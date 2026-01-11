"""
Pushover API client
https://pushover.net/api
"""

from functools import lru_cache

import httpx

from youtube_sync.io.op.secrets import get_secret
from youtube_sync.io.pushover.models import PushoverResponse

API_BASE = "https://api.pushover.net/1"


class PushoverClient:
    """Client for Pushover notification API."""

    def __init__(self, app_token: str, user_key: str):
        self._client = httpx.Client(base_url=API_BASE)
        self._app_token = app_token
        self._user_key = user_key

    def send_message(
        self,
        message: str,
        *,
        title: str | None = None,
        html: bool = False,
    ) -> PushoverResponse:
        """Send a push notification."""
        payload = {
            "token": self._app_token,
            "user": self._user_key,
            "message": message,
        }

        if title:
            payload["title"] = title

        if html:
            payload["html"] = 1

        response = self._client.post("/messages.json", data=payload)
        response.raise_for_status()
        return PushoverResponse.model_validate(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@lru_cache
def create_client() -> PushoverClient:
    """Create a Pushover client with credentials from 1Password."""
    app_token = get_secret("Pushover", "app: scripts repo")
    user_key = get_secret("Pushover", "user key")
    return PushoverClient(app_token, user_key)
