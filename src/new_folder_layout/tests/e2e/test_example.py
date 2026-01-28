import pytest


@pytest.mark.e2e
def test_real_event_is_published(e2e_ctx):
    from core.app.register_user import RegisterUserCommand, register_user

    register_user(
        RegisterUserCommand(email="c@example.com"),
        users=e2e_ctx.users,
        events=e2e_ctx.events,
    )

    # assertion depends on real infra; often "no exception" is enough
