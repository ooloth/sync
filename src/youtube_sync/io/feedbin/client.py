"""
Feedbin API client
https://github.com/feedbin/feedbin-api
"""

from functools import lru_cache

import httpx
from result import Err, Ok, Result

from youtube_sync.io.feedbin.auth import FeedbinAuth, create_auth_from_1password
from youtube_sync.io.feedbin.models import FeedbinSubscription
from youtube_sync.types import ErrorMessage

API_BASE = "https://api.feedbin.com/v2"


class FeedbinClient:
    """
    Client for Feedbin API operations.

    Usage patterns:
    1. Via factory (recommended for scripts):
        client = create_client()
        subs = client.list_subscriptions()

    2. As context manager (auto-cleanup):
        with FeedbinClient(...) as client:
            subs = client.list_subscriptions()

    3. Manual cleanup (for long-running apps):
        client = FeedbinClient(...)
        try:
            subs = client.list_subscriptions()
        finally:
            client.close()
    """

    def __init__(self, auth: FeedbinAuth):
        self._client = httpx.Client(
            base_url=API_BASE,
            auth=(auth.username, auth.password),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    def list_subscriptions(self) -> Result[list[FeedbinSubscription], ErrorMessage]:
        """
        Get all subscriptions.

        Returns:
            Ok with list of subscriptions, or Err with error message
        """
        try:
            response = self._client.get("/subscriptions.json")
            response.raise_for_status()
            subscriptions = [FeedbinSubscription.model_validate(item) for item in response.json()]
            return Ok(subscriptions)
        except Exception as e:
            return Err(f"Failed to list Feedbin subscriptions: {e}")

    def create_subscription(self, feed_url: str) -> Result[FeedbinSubscription, ErrorMessage]:
        """
        Create a new subscription.

        Args:
            feed_url: The URL of the feed to subscribe to

        Returns:
            Ok with the created subscription, or Err with error message
        """
        try:
            response = self._client.post("/subscriptions.json", json={"feed_url": feed_url})
            response.raise_for_status()
            subscription = FeedbinSubscription.model_validate(response.json())
            return Ok(subscription)
        except Exception as e:
            return Err(f"Failed to create Feedbin subscription: {e}")

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
def create_client(auth: FeedbinAuth | None = None) -> FeedbinClient:
    """
    Create a Feedbin client with credentials.

    Args:
        auth: Optional FeedbinAuth instance. If None, creates one using 1Password credentials.

    Returns:
        Configured FeedbinClient ready for API calls
    """
    if auth is None:
        auth = create_auth_from_1password()
    return FeedbinClient(auth)
