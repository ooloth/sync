import pytest


@pytest.mark.integration
def test_user_is_persisted(integration_ctx):
    from core.app.register_user import RegisterUserCommand, register_user

    register_user(
        RegisterUserCommand(email="b@example.com"),
        users=integration_ctx.users,
        events=integration_ctx.events,
    )

    user = integration_ctx.users.get_by_email("b@example.com")
    assert user is not None
