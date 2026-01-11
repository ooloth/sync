"""
YouTube Data API client
https://developers.google.com/youtube/v3/docs
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from youtube_sync.io.op.secrets import get_secret
from youtube_sync.io.youtube.models import YouTubeSubscription

# Type-only import: google-api-python-client-stubs provides accurate types generated from
# Google's API discovery documents, but these types exist only in .pyi stub files and cannot
# be imported at runtime. We use TYPE_CHECKING to get proper type safety (method signatures,
# parameter validation) during type checking while keeping runtime imports clean.
if TYPE_CHECKING:
    from googleapiclient._apis.youtube.v3 import YouTubeResource

API_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def _get_tokens_file() -> Path:
    """Get the path to the OAuth tokens file."""
    # Allow override via environment variable, otherwise use project default
    tokens_path = os.getenv("YOUTUBE_TOKENS_FILE")
    if tokens_path:
        return Path(tokens_path)
    return Path.home() / ".config" / "youtube-sync" / "oauth_tokens.json"


def _fetch_new_oauth_tokens(client_config: dict, scopes: list[str] = API_SCOPES) -> Credentials:
    """
    Fetches new Google Cloud OAuth tokens using client configuration.

    OAuth client: https://console.cloud.google.com/apis/credentials?project=michael-uloth
    """
    print("🥁 Fetching new tokens...")

    try:
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        credentials = flow.run_local_server()
        return credentials
    except Exception as e:
        print(f"😱 Unexpected error while fetching new OAuth tokens: {e}")
        raise


def _generate_oauth_credentials(client_config: dict, tokens_file: Path) -> Credentials:
    """
    Generates OAuth credentials from a saved, refreshed or new access token.
    """
    credentials: Credentials | None = None

    print("🥁 Checking for saved tokens...")

    if tokens_file.exists():
        print("👍 Saved tokens found")
        try:
            print(f'🥁 Loading saved tokens from "{tokens_file}"...')
            credentials = Credentials.from_authorized_user_file(str(tokens_file), API_SCOPES)
        except Exception as e:
            print(f"😱 Error loading tokens: {e}")
            credentials = _fetch_new_oauth_tokens(client_config)
    else:
        print("👎 No saved tokens found")
        credentials = _fetch_new_oauth_tokens(client_config)

    if not credentials.valid:
        if credentials.expired and credentials.refresh_token:
            try:
                print("🥁 Refreshing expired access token...")
                credentials.refresh(Request())
            except Exception as e:
                print(f"😱 Error refreshing token: {e}")
                credentials = _fetch_new_oauth_tokens(client_config)
        else:
            credentials = _fetch_new_oauth_tokens(client_config)

        # Ensure parent directory exists
        tokens_file.parent.mkdir(parents=True, exist_ok=True)

        print(f'🥁 Saving updated tokens to "{tokens_file}"...')
        with open(tokens_file, "w") as file:
            file.write(credentials.to_json())

    return credentials


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

    def list_subscriptions(self) -> list[YouTubeSubscription]:
        """
        Get all YouTube channel subscriptions.

        Returns:
            List of subscription resources with channel details
        """
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

        return subscriptions

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
def create_client() -> YouTubeClient:
    """Create a YouTube client with credentials from 1Password."""
    # Get client secrets JSON from 1Password
    client_secrets_json = get_secret("YouTube API", "oauth_client_secrets.json")
    client_config = json.loads(client_secrets_json)

    # Get tokens file path
    tokens_file = _get_tokens_file()

    # Generate credentials
    credentials = _generate_oauth_credentials(client_config, tokens_file)

    return YouTubeClient(credentials)
