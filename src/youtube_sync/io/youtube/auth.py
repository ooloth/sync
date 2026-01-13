"""
YouTube OAuth authentication management

Handles OAuth token lifecycle following RFC 9700 security best practices:
- Short-lived access tokens cached locally (~1 hour)
- Long-lived refresh tokens stored securely in 1Password
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from youtube_sync.io.op.secrets import get_secret
from youtube_sync.logging import get_logger

log = get_logger(__name__)

API_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def _get_tokens_file() -> Path:
    """Get the path to the OAuth access token cache file."""
    # Allow override via environment variable, otherwise use project .secrets/
    tokens_path = os.getenv("YOUTUBE_TOKENS_FILE")
    if tokens_path:
        return Path(tokens_path)

    # Default to .secrets/ in project root
    # If running as installed package, fall back to user's home directory
    try:
        # Try to find project root via git
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        project_root = Path(result.stdout.strip())
        return project_root / ".secrets" / "oauth_access_token.json"
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to user's home directory if not in git repo
        return Path.home() / ".youtube_sync" / "oauth_access_token.json"


def _fetch_new_oauth_tokens(client_config: dict, scopes: list[str]) -> Credentials:
    """
    Fetches new Google Cloud OAuth tokens using client configuration.

    OAuth client: https://console.cloud.google.com/apis/credentials?project=michael-uloth
    """
    log.info("fetching new OAuth tokens via browser flow")

    try:
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        credentials = flow.run_local_server()
        log.info("successfully obtained new OAuth tokens")
        return credentials
    except Exception as e:
        log.error("unexpected error while fetching new OAuth tokens", error=str(e))
        raise


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

    log.debug("caching access token", tokens_file=str(tokens_file))
    with open(tokens_file, "w") as file:
        json.dump(token_data, file, indent=2)
    log.debug("access token cached")


@dataclass
class YouTubeAuth:
    """
    OAuth credential provider for YouTube API.

    Manages the OAuth token lifecycle using a hybrid security approach:
    - Fast path: Cached access tokens from disk (~1 hour validity)
    - Refresh path: Use refresh token from 1Password to get new access token
    - Full OAuth: Browser flow when refresh token is invalid/expired

    Storage Strategy:
    1. Disk cache (.secrets/oauth_access_token.json):
       - ONLY contains: access token + expiry
       - Fast path when access token still valid (~1 hour window)
       - Per RFC 9700: short-lived tokens can be cached

    2. 1Password:
       - oauth_client_secrets.json: OAuth app credentials
       - oauth_refresh_token: Long-lived refresh token (the key credential)
       - Only updated on full OAuth flow (rare - when refresh token expires/revoked)
    """

    client_config: dict
    tokens_file: Path
    scopes: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = API_SCOPES

    def get_credentials(self) -> Credentials:
        """
        Get valid OAuth credentials, refreshing or re-authenticating as needed.

        Flow:
        1. Try disk cache - if access token valid, use it (fast!)
        2. If not, fetch client config + refresh token from 1Password
        3. Use refresh token to get new access token
        4. Cache ONLY the access token to disk for next run
        5. If refresh fails (bad refresh token), do full OAuth and update 1Password
        """
        credentials: Credentials | None = None

        # Try disk cache first (fast path - only if access token still valid)
        log.debug("checking for cached access token", tokens_file=str(self.tokens_file))
        if self.tokens_file.exists():
            credentials = self._load_cached_credentials()
            if credentials and credentials.valid:
                log.debug("using cached access token", status="valid")
                return credentials
            if credentials:
                log.debug("cached access token expired", status="expired")

        # Access token expired or missing - need to refresh using refresh token
        log.debug("fetching refresh token from 1Password")
        try:
            refresh_token = get_secret("YouTube API", "oauth_refresh_token")
            log.debug("loaded refresh token from 1Password")

            # Build credentials with refresh token
            credentials = Credentials(
                token=None,  # Will be populated by refresh
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_config["installed"]["client_id"],
                client_secret=self.client_config["installed"]["client_secret"],
                scopes=self.scopes,
            )
        except Exception as e:
            log.warning("error loading refresh token from 1Password", error=str(e))
            return self._do_full_oauth_flow()

        # Use refresh token to get new access token
        try:
            log.debug("using refresh token to get new access token")
            credentials.refresh(Request())
            log.debug("access token refreshed successfully")
        except Exception as e:
            log.error("refresh token invalid or expired", error=str(e))
            return self._do_full_oauth_flow()

        # Cache ONLY access token to disk (no refresh token, no client secrets)
        _cache_access_token(credentials, self.tokens_file)

        return credentials

    def _load_cached_credentials(self) -> Credentials | None:
        """Load credentials from disk cache."""
        try:
            log.debug("loading cached access token", tokens_file=str(self.tokens_file))
            with open(self.tokens_file) as f:
                token_data = json.load(f)

            # Reconstruct credentials from minimal cached data
            expiry = (
                datetime.fromisoformat(token_data["expiry"]) if token_data.get("expiry") else None
            )
            return Credentials(
                token=token_data["token"],
                expiry=expiry,
            )
        except Exception as e:
            log.warning("error loading cached access token", error=str(e))
            return None

    def _do_full_oauth_flow(self) -> Credentials:
        """Perform full OAuth browser flow and prompt user to update 1Password."""
        log.info("starting new OAuth browser flow")
        credentials = _fetch_new_oauth_tokens(self.client_config, self.scopes)

        log.warning(
            "manual step required: please update 'YouTube API' -> 'oauth_refresh_token' in 1Password",
            new_refresh_token=credentials.refresh_token,
        )

        # Cache and return
        _cache_access_token(credentials, self.tokens_file)
        return credentials


def create_auth_from_1password() -> YouTubeAuth:
    """Create YouTubeAuth using secrets from 1Password."""
    # Get client secrets JSON from 1Password
    client_secrets_json = get_secret("YouTube API", "oauth_client_secrets.json")
    client_config = json.loads(client_secrets_json)

    # Get tokens file path
    tokens_file = _get_tokens_file()

    return YouTubeAuth(
        client_config=client_config,
        tokens_file=tokens_file,
    )
