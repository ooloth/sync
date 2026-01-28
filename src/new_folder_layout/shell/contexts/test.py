import os
import sqlite3

from shell.adapters.db.user_repo_inmemory import InMemoryUserRepo
from shell.adapters.db.user_repo_postgres import PostgresUserRepo  # hypothetical
from shell.adapters.db.user_repo_sqlite import SqliteUserRepo
from shell.adapters.event_bus.publisher_inmem import InMemoryPublisher
from shell.adapters.event_bus.publisher_kafka import KafkaPublisher  # hypothetical
from shell.contexts.base import AppContext


def create_unit_context() -> AppContext:
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
    return AppContext(users=InMemoryUserRepo(), events=InMemoryPublisher())


def create_integration_context() -> AppContext:
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
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    users = SqliteUserRepo(conn)

    # Often still in-memory for events unless you specifically want broker integration.
    events = InMemoryPublisher()

    return AppContext(users=users, events=events)


def create_e2e_context() -> AppContext:
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
    users = PostgresUserRepo(dsn=os.environ["TEST_POSTGRES_DSN"])
    events = KafkaPublisher(brokers=os.environ["TEST_KAFKA_BROKERS"].split(","))

    return AppContext(users=users, events=events)
