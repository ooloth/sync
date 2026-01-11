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
from googleapiclient.discovery import build

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
    """Get the path to the OAuth access token cache file."""
    # Allow override via environment variable, otherwise use project .secrets/
    tokens_path = os.getenv("YOUTUBE_TOKENS_FILE")
    if tokens_path:
        return Path(tokens_path)
    # Project root is 5 levels up from this file: src/youtube_sync/io/youtube/client.py
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / ".secrets" / "oauth_access_token.json"


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
    Generates OAuth credentials using a hybrid approach for security and performance.

    OAuth Token Lifecycle:
    - access_token: Short-lived (~1 hour), used for API requests
    - refresh_token: Long-lived (months/years), used to get new access tokens

    Storage Strategy:
    1. Disk cache (.secrets/oauth_access_token.json):
       - ONLY contains: access token + expiry
       - Fast path when access token still valid (~1 hour window)
       - Per RFC 9700: short-lived tokens can be cached, long-lived credentials stay secure

    2. 1Password:
       - oauth_client_secrets.json: OAuth app credentials (client_id, client_secret)
       - oauth_refresh_token: Long-lived refresh token (the key credential)
       - Only updated on full OAuth flow (rare - when refresh token expires/revoked)

    Flow:
    1. Try disk cache - if access token valid, use it (fast!)
    2. If not, fetch client config + refresh token from 1Password
    3. Use refresh token to get new access token
    4. Cache ONLY the access token to disk for next run
    5. If refresh fails (bad refresh token), do full OAuth and update 1Password
    """
    credentials: Credentials | None = None

    # Try disk cache first (fast path - only if access token still valid)
    print("🥁 Checking for cached access token...")
    if tokens_file.exists():
        try:
            print(f'🥁 Loading cached access token from "{tokens_file}"...')
            with open(tokens_file) as f:
                token_data = json.load(f)

            # Reconstruct credentials from minimal cached data
            from datetime import datetime

            expiry = datetime.fromisoformat(token_data["expiry"])
            credentials = Credentials(
                token=token_data["token"],
                expiry=expiry,
            )

            if credentials.valid:
                print("✅ Cached access token is still valid")
                return credentials
            print("⏰ Cached access token expired")
        except Exception as e:
            print(f"⚠️  Error loading cached access token: {e}")

    # Access token expired or missing - need to refresh using refresh token
    print("🥁 Fetching refresh token from 1Password...")
    try:
        refresh_token = get_secret("YouTube API", "oauth_refresh_token")
        print("✅ Loaded refresh token from 1Password")

        # Build credentials with refresh token
        credentials = Credentials(
            token=None,  # Will be populated by refresh
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_config["installed"]["client_id"],
            client_secret=client_config["installed"]["client_secret"],
            scopes=API_SCOPES,
        )
    except Exception as e:
        print(f"⚠️  Error loading refresh token from 1Password: {e}")
        print("🥁 Starting OAuth flow...")
        credentials = _fetch_new_oauth_tokens(client_config)
        print("⚠️  Manual step: Please update 'YouTube API' -> 'oauth_refresh_token' in 1Password")
        print(f"   New refresh token: {credentials.refresh_token}")
        # Cache and return
        _cache_access_token(credentials, tokens_file)
        return credentials

    # Use refresh token to get new access token
    try:
        print("🥁 Using refresh token to get new access token...")
        credentials.refresh(Request())
        print("✅ Access token refreshed successfully")
    except Exception as e:
        print(f"😱 Refresh token invalid or expired: {e}")
        print("🥁 Starting new OAuth flow...")
        credentials = _fetch_new_oauth_tokens(client_config)
        print("⚠️  Manual step: Please update 'YouTube API' -> 'oauth_refresh_token' in 1Password")
        print(f"   New refresh token: {credentials.refresh_token}")

    # Cache ONLY access token to disk (no refresh token, no client secrets)
    _cache_access_token(credentials, tokens_file)

    return credentials


def _cache_access_token(credentials: Credentials, tokens_file: Path) -> None:
    """
    Cache only the access token to disk, following OAuth 2.0 security best practices (RFC 9700).

    Cached: access token + expiry (short-lived, ~1hr)
    Not cached: refresh_token, client_id, client_secret (long-lived credentials stay in 1Password)
    """
    tokens_file.parent.mkdir(parents=True, exist_ok=True)

    # Minimal token data - only what's needed for the fast path
    token_data = {
        "token": credentials.token,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }

    print(f'🥁 Caching access token to "{tokens_file}"...')
    with open(tokens_file, "w") as file:
        json.dump(token_data, file, indent=2)
    print("✅ Access token cached (refresh token stays in 1Password)")


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
