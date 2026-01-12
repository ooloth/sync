"""
YouTube Data API client
https://developers.google.com/youtube/v3/docs
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from result import Err, Ok, Result

from youtube_sync.io.youtube.auth import YouTubeAuth, create_auth_from_1password
from youtube_sync.io.youtube.models import YouTubeSubscription

# Type-only import: google-api-python-client-stubs provides accurate types generated from
# Google's API discovery documents, but these types exist only in .pyi stub files and cannot
# be imported at runtime. We use TYPE_CHECKING to get proper type safety (method signatures,
# parameter validation) during type checking while keeping runtime imports clean.
if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource


class YouTubeClient:
    """
    Client for YouTube Data API operations.

    Usage patterns:
    1. Via factory (recommended for scripts):
        client = create_client()
        subs = client.list_subscriptions()

    2. As context manager (auto-cleanup):
        with YouTubeClient(...) as client:
            subs = client.list_subscriptions()

    3. Manual cleanup (for long-running apps):
        client = YouTubeClient(...)
        try:
            subs = client.list_subscriptions()
        finally:
            client.close()
    """

    def __init__(self, credentials: Credentials):
        self._youtube: YouTubeResource = build(  # type: ignore[assignment]
            credentials=credentials,
            serviceName="youtube",
            version="v3",
        )

    def list_subscriptions(self) -> Result[list[YouTubeSubscription], str]:
        """
        Get all YouTube channel subscriptions.

        Returns:
            Ok with list of subscription resources, or Err with error message
        """
        try:
            subscriptions = []
            subs_resource = self._youtube.subscriptions()

            request = subs_resource.list(
                part="snippet,contentDetails",
                mine=True,
                maxResults=50,
            )

            while request is not None:
                response = request.execute()
                items = response.get("items", [])
                subscriptions.extend([YouTubeSubscription.model_validate(item) for item in items])
                request = subs_resource.list_next(request, response)

            return Ok(subscriptions)
        except Exception as e:
            return Err(f"Failed to list YouTube subscriptions: {e}")

    def close(self) -> None:
        """
        Close the YouTube API client and release connections.

        Not strictly necessary for short-lived scripts (Python cleans up on exit),
        but good practice for tests and long-running applications.
        """
        self._youtube.close()

    def __enter__(self):
        """Enable 'with' statement usage. Returns self for use in the with block."""
        return self

    def __exit__(self, *args):
        """Called when exiting 'with' block. Ensures cleanup even if exceptions occur."""
        self.close()


@lru_cache
def create_client(auth: YouTubeAuth | None = None) -> YouTubeClient:
    """
    Create a YouTube client with OAuth credentials.

    Args:
        auth: Optional YouTubeAuth instance. If None, creates one using 1Password secrets.

    Returns:
        Configured YouTubeClient ready for API calls
    """
    if auth is None:
        auth = create_auth_from_1password()

    credentials = auth.get_credentials()
    return YouTubeClient(credentials)
