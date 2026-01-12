"""Pushover authentication management."""

from dataclasses import dataclass

from youtube_sync.io.op.secrets import get_secret


@dataclass
class PushoverAuth:
    """
    Credentials for Pushover API authentication.

    Pushover requires an application token and user key for authentication.
    """

    app_token: str
    user_key: str


def create_auth_from_1password() -> PushoverAuth:
    """Create PushoverAuth using credentials from 1Password."""
    app_token = get_secret("Pushover", "app: scripts repo")
    user_key = get_secret("Pushover", "user key")
    return PushoverAuth(app_token=app_token, user_key=user_key)
