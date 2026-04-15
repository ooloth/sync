"""Feedbin authentication management."""

from dataclasses import dataclass

from sync.io.op.secrets import get_secret


@dataclass
class FeedbinAuth:
    """
    Credentials for Feedbin API authentication.

    Feedbin uses HTTP Basic Authentication with username and password.
    """

    username: str
    password: str


def create_auth_from_1password() -> FeedbinAuth:
    """Create FeedbinAuth using credentials from 1Password."""
    username = get_secret("Feedbin API", "username")
    password = get_secret("Feedbin API", "password")
    return FeedbinAuth(username=username, password=password)
