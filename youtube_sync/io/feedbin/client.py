"""
Feedbin API client
https://github.com/feedbin/feedbin-api
"""

from functools import lru_cache

import httpx

from youtube_sync.io.feedbin.models import FeedbinSubscription
from youtube_sync.io.op.secrets import get_secret

API_BASE = "https://api.feedbin.com/v2"


class FeedbinClient:
    """Client for Feedbin API operations."""

    def __init__(self, username: str, password: str):
        self._client = httpx.Client(
            base_url=API_BASE,
            auth=(username, password),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    def list_subscriptions(self) -> list[FeedbinSubscription]:
        """Get all subscriptions."""
        response = self._client.get("/subscriptions.json")
        response.raise_for_status()
        return [FeedbinSubscription.model_validate(item) for item in response.json()]

    def create_subscription(self, feed_url: str) -> FeedbinSubscription:
        """Create a new subscription."""
        response = self._client.post("/subscriptions.json", json={"feed_url": feed_url})
        response.raise_for_status()
        return FeedbinSubscription.model_validate(response.json())

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@lru_cache
def create_client() -> FeedbinClient:
    """Create a Feedbin client with credentials from 1Password."""
    username = get_secret("Feedbin", "username")
    password = get_secret("Feedbin", "password")
    return FeedbinClient(username, password)
