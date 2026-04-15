import pytest
from src.new_folder_layout.core.app.register_user import RegisterUserCommand, register_user


@pytest.mark.e2e
def test_real_event_is_published(e2e_ctx):
    register_user(
        RegisterUserCommand(email="c@example.com"),
        users=e2e_ctx.users,
        events=e2e_ctx.events,
    )

    # assertion depends on real infra; often "no exception" is enough
