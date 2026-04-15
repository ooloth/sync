"""
Pushover API client
https://pushover.net/api
"""

from functools import lru_cache

import httpx
from result import Err, Ok, Result

from sync.errors import ErrorMessage
from sync.io.pushover.auth import PushoverAuth, create_auth_from_1password
from sync.io.pushover.models import PushoverResponse

API_BASE = "https://api.pushover.net/1"


class PushoverClient:
    """
    Client for Pushover notification API.

    Usage patterns:
    1. Via factory (recommended for scripts):
        client = create_client()
        client.send_message("Hello")

    2. As context manager (auto-cleanup):
        with PushoverClient(...) as client:
            client.send_message("Hello")

    3. Manual cleanup (for long-running apps):
        client = PushoverClient(...)
        try:
            client.send_message("Hello")
        finally:
            client.close()
    """

    def __init__(self, auth: PushoverAuth):
        self._client = httpx.Client(base_url=API_BASE)
        self._app_token = auth.app_token
        self._user_key = auth.user_key

    def send_message(
        self,
        message: str,
        *,
        title: str | None = None,
        html: bool = False,
    ) -> Result[PushoverResponse, ErrorMessage]:
        """
        Send a push notification.

        Args:
            message: The message body
            title: Optional message title
            html: Whether to enable HTML formatting

        Returns:
            Ok with the response, or Err with error message
        """
        try:
            payload = {
                "token": self._app_token,
                "user": self._user_key,
                "message": message,
            }

            if title:
                payload["title"] = title

            if html:
                payload["html"] = "1"

            response = self._client.post("/messages.json", data=payload)
            response.raise_for_status()
            pushover_response = PushoverResponse.model_validate(response.json())
            return Ok(pushover_response)
        except Exception as e:
            return Err(f"Failed to send Pushover message: {e}")

    def close(self) -> None:
        """
        Close the HTTP client and release connections.

        Not strictly necessary for short-lived scripts (Python cleans up on exit),
        but good practice for tests and long-running applications.
        """
        self._client.close()

    def __enter__(self):
        """Enable 'with' statement usage. Returns self for use in the with block."""
        return self

    def __exit__(self, *args):
        """Called when exiting 'with' block. Ensures cleanup even if exceptions occur."""
        self.close()


@lru_cache
def create_client(auth: PushoverAuth | None = None) -> PushoverClient:
    """
    Create a Pushover client with credentials.

    Args:
        auth: Optional PushoverAuth instance. If None, creates one using 1Password credentials.

    Returns:
        Configured PushoverClient ready for sending notifications
    """
    if auth is None:
        auth = create_auth_from_1password()
    return PushoverClient(auth)
