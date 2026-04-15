"""
This is the module where concrete implementations are chosen and glued together, connecting abstractions (ports) to
implementations (adapters).

It address three distinct needs in the "shell" layer at startup and shutdown:
  1. Choose implementations (Postgres vs SQLite, Kafka vs in-memory publisher, etc)
  2. Create them in the right order (config → DB connection → repo → use case deps)
  3. Control lifecycle (open connections, close connections, hooks for startup/shutdown)

It:
  1. Instantiates long-lived adapter dependencies
  2. Passes them into use cases / handlers as a struct-like object graph
  3. Loads config
  4. Manages lifecycle (startup/shutdown)

It’s a manually-built object graph:
  1. A struct-like object
  2. Holding long-lived dependencies
  3. Created once at startup
  4. Passed around implicitly (or imported)

This file is intentionally boring.
It:
  1. defines the shape of the runtime
  2. documents what the service depends on
  3. does not choose implementations
  4. does not do IO

"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Context:
    """
    Context is the runtime dependency graph for this service.

    It contains concrete implementations of the ports required by the core.
    Entry points receive an AppContext and pass its members into use cases.
    """

    # Ports rather than adapters at this level (for typing)
    # users: UserRepo
    # events: EventPublisher


def create_dev_context() -> Context:
    # dev-friendly default; can be overridden with env vars
    # db_path = os.getenv("DEV_SQLITE_PATH", "./.local/dev.sqlite3")

    # conn = sqlite3.connect(db_path, check_same_thread=False)
    # users = SqliteUserRepo(conn)

    # In dev, using an in-memory publisher keeps things simple.
    # Swap to a real broker adapter when you want end-to-end event flow locally.
    # events = InMemoryPublisher()

    return Context()
    # return AppContext(users=users, events=events)


def create_prod_context() -> Context:
    """
    Example usage in shell/entrypoints/http/register_user_handler.py:

    from shell.composition.prod import create_context
    from core.app.register_user import register_user, RegisterUserCommand

    ctx = create_context()

    def handle_http_request(payload: dict):
        cmd = RegisterUserCommand(email=payload["email"])
        return register_user(cmd, users=ctx.users, events=ctx.events)
    """
    # conn = sqlite3.connect("/var/db/users.sqlite", check_same_thread=False)

    # users = SqliteUserRepo(conn)
    # events = KafkaPublisher(brokers=["kafka:9092"])

    # Adapters rather than ports now
    return Context()
    # return AppContext(users=users, events=events)


def create_unit_test_context() -> Context:
    """
    Use this for:
        •	core use-case tests
        •	domain tests
        •	“handler calls use case correctly” tests (without real IO)

    Example unit test:
        def test_register_user_creates_new_user(unit_ctx):
            from core.app.register_user import register_user, RegisterUserCommand

            result = register_user(
                RegisterUserCommand(email="a@example.com"),
                users=unit_ctx.users,
                events=unit_ctx.events,
            )

            assert result.created is True
            assert unit_ctx.events.published  # in-memory publisher
    """
    return Context()
    # return AppContext(users=InMemoryUserRepo(), events=InMemoryPublisher())


def create_integration_test_context() -> Context:
    """
    Use this for:
        •	repository integration tests (queries, constraints, transactions)
        •	migrations / schema bootstrapping
        •	adapter behavior tests

    Example integration test:
        import pytest

        @pytest.mark.integration
        def test_user_is_persisted(integration_ctx):
            from core.app.register_user import register_user, RegisterUserCommand

            register_user(
                RegisterUserCommand(email="b@example.com"),
                users=integration_ctx.users,
                events=integration_ctx.events,
            )

            user = integration_ctx.users.get_by_email("b@example.com")
            assert user is not None
    """
    # in-memory sqlite: "real adapter", ephemeral database
    # conn = sqlite3.connect(":memory:", check_same_thread=False)
    # users = SqliteUserRepo(conn)

    # Often still in-memory for events unless you specifically want broker integration.
    # events = InMemoryPublisher()

    return Context()
    # return AppContext(users=users, events=events)


def create_e2e_test_context() -> Context:
    """
    Use this for:
        •	a small number of “real system” tests
        •	verifying wiring across actual infrastructure

    Example end-to-end test:
        import pytest

        @pytest.mark.e2e
        def test_real_event_is_published(e2e_ctx):
            from core.app.register_user import register_user, RegisterUserCommand

            register_user(
                RegisterUserCommand(email="c@example.com"),
                users=e2e_ctx.users,
                events=e2e_ctx.events,
            )

            # assertion depends on real infra; often "no exception" is enough
    """
    # users = PostgresUserRepo(dsn=os.environ["TEST_POSTGRES_DSN"])
    # events = KafkaPublisher(brokers=os.environ["TEST_KAFKA_BROKERS"].split(","))

    return Context()
    # return AppContext(users=users, events=events)
