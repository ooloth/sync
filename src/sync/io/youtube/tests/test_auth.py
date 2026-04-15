"""
Tests for YouTube OAuth authentication
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from google.oauth2.credentials import Credentials

from sync.io.youtube import YouTubeAuth, create_auth_from_1password
from sync.io.youtube.auth import (
    API_SCOPES,
    _cache_access_token,
    _fetch_new_oauth_tokens,
    _get_tokens_file,
)


@pytest.fixture
def mock_client_config():
    """Mock OAuth client configuration."""
    return {
        "installed": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


@pytest.fixture
def mock_credentials():
    """Mock valid Google OAuth2 credentials."""
    expiry = datetime.now() + timedelta(hours=1)
    creds = Mock(spec=Credentials)
    creds.token = "mock_access_token"
    creds.expiry = expiry
    creds.valid = True
    creds.refresh_token = "mock_refresh_token"
    return creds


@pytest.fixture
def mock_expired_credentials():
    """Mock expired Google OAuth2 credentials."""
    expiry = datetime.now() - timedelta(hours=1)
    creds = Mock(spec=Credentials)
    creds.token = "expired_token"
    creds.expiry = expiry
    creds.valid = False
    creds.refresh_token = "mock_refresh_token"
    return creds


def test_get_tokens_file_uses_env_var(monkeypatch, tmp_path):
    """Verify _get_tokens_file respects YOUTUBE_TOKENS_FILE env var."""
    custom_path = tmp_path / "custom_tokens.json"
    monkeypatch.setenv("YOUTUBE_TOKENS_FILE", str(custom_path))

    result = _get_tokens_file()

    assert result == custom_path


def test_get_tokens_file_uses_git_root(tmp_path, monkeypatch):
    """Verify _get_tokens_file finds git root when no env var set."""
    # Mock git command to return tmp_path as project root
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(stdout=f"{tmp_path}\n", returncode=0)

        result = _get_tokens_file()

        assert result == tmp_path / ".secrets" / "oauth_access_token.json"
        mock_run.assert_called_once()


def test_get_tokens_file_falls_back_to_home(monkeypatch, tmp_path):
    """Verify _get_tokens_file falls back to home directory when not in git repo."""
    import subprocess

    # Mock git command to fail (not in git repo)
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = _get_tokens_file()

            assert result == tmp_path / ".sync" / "oauth_access_token.json"


def test_fetch_new_oauth_tokens_success(mock_client_config, mock_credentials):
    """Verify _fetch_new_oauth_tokens successfully obtains tokens via browser flow."""
    with patch("sync.io.youtube.auth.InstalledAppFlow.from_client_config") as mock_flow_class:
        mock_flow = Mock()
        mock_flow.run_local_server.return_value = mock_credentials
        mock_flow_class.return_value = mock_flow

        result = _fetch_new_oauth_tokens(mock_client_config, API_SCOPES)

        mock_flow_class.assert_called_once_with(mock_client_config, API_SCOPES)
        mock_flow.run_local_server.assert_called_once()
        assert result == mock_credentials


def test_fetch_new_oauth_tokens_propagates_errors(mock_client_config):
    """Verify _fetch_new_oauth_tokens propagates errors from OAuth flow."""
    with patch("sync.io.youtube.auth.InstalledAppFlow.from_client_config") as mock_flow_class:
        mock_flow = Mock()
        mock_flow.run_local_server.side_effect = Exception("OAuth failed")
        mock_flow_class.return_value = mock_flow

        with pytest.raises(Exception, match="OAuth failed"):
            _fetch_new_oauth_tokens(mock_client_config, API_SCOPES)


def test_cache_access_token_creates_file(tmp_path, mock_credentials):
    """Verify _cache_access_token creates cache file with minimal token data."""
    tokens_file = tmp_path / "tokens.json"

    _cache_access_token(mock_credentials, tokens_file)

    assert tokens_file.exists()
    cached_data = json.loads(tokens_file.read_text())
    assert cached_data["token"] == "mock_access_token"
    assert "expiry" in cached_data
    # Verify refresh token is NOT cached (security best practice)
    assert "refresh_token" not in cached_data


def test_cache_access_token_creates_parent_dirs(tmp_path, mock_credentials):
    """Verify _cache_access_token creates parent directories if needed."""
    tokens_file = tmp_path / "nested" / "path" / "tokens.json"

    _cache_access_token(mock_credentials, tokens_file)

    assert tokens_file.exists()
    assert tokens_file.parent.exists()


def test_youtube_auth_get_credentials_uses_valid_cache(
    tmp_path, mock_client_config, mock_credentials
):
    """Verify YouTubeAuth uses cached access token when still valid."""
    # Create cache file with valid token
    tokens_file = tmp_path / "tokens.json"
    tokens_file.write_text(
        json.dumps(
            {
                "token": "cached_valid_token",
                "expiry": (datetime.now() + timedelta(hours=1)).isoformat(),
            }
        )
    )

    auth = YouTubeAuth(client_config=mock_client_config, tokens_file=tokens_file)

    # Mock Credentials constructor to track what gets created
    with patch("sync.io.youtube.auth.Credentials") as mock_creds_class:
        mock_creds_instance = Mock(spec=Credentials)
        mock_creds_instance.valid = True
        mock_creds_instance.token = "cached_valid_token"
        mock_creds_class.return_value = mock_creds_instance

        result = auth.get_credentials()

        assert result.valid
        # Should not try to refresh or do full OAuth
        mock_creds_instance.refresh.assert_not_called()


def test_youtube_auth_refreshes_expired_token(tmp_path, mock_client_config, mock_credentials):
    """Verify YouTubeAuth refreshes expired access token using refresh token."""
    # Create cache file with expired token
    tokens_file = tmp_path / "tokens.json"
    tokens_file.write_text(
        json.dumps(
            {
                "token": "expired_token",
                "expiry": (datetime.now() - timedelta(hours=1)).isoformat(),
            }
        )
    )

    auth = YouTubeAuth(client_config=mock_client_config, tokens_file=tokens_file)

    with (
        patch("sync.io.youtube.auth.get_secret", return_value="test_refresh_token"),
        patch("sync.io.youtube.auth.Credentials") as mock_creds_class,
        patch("sync.io.youtube.auth._cache_access_token") as mock_cache,
    ):
        # First call returns expired creds, second call returns refresh creds
        expired_creds = Mock(spec=Credentials)
        expired_creds.valid = False
        expired_creds.token = "expired_token"

        refresh_creds = Mock(spec=Credentials)
        refresh_creds.valid = True
        refresh_creds.token = "new_access_token"
        refresh_creds.expiry = datetime.now() + timedelta(hours=1)

        mock_creds_class.side_effect = [expired_creds, refresh_creds]

        result = auth.get_credentials()

        # Should return the refreshed credentials
        assert result == refresh_creds
        # Should have called refresh
        refresh_creds.refresh.assert_called_once()
        # Should have cached the new token
        mock_cache.assert_called_once_with(refresh_creds, tokens_file)


def test_youtube_auth_handles_missing_cache(tmp_path, mock_client_config):
    """Verify YouTubeAuth handles missing cache file gracefully."""
    tokens_file = tmp_path / "nonexistent.json"
    auth = YouTubeAuth(client_config=mock_client_config, tokens_file=tokens_file)

    with (
        patch("sync.io.youtube.auth.get_secret", return_value="test_refresh_token"),
        patch("sync.io.youtube.auth.Credentials") as mock_creds_class,
        patch("sync.io.youtube.auth._cache_access_token"),
    ):
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        mock_creds.token = "new_token"
        mock_creds.expiry = datetime.now() + timedelta(hours=1)
        mock_creds_class.return_value = mock_creds

        result = auth.get_credentials()

        # Should return valid credentials
        assert result.valid
        # Should have attempted to get refresh token from 1Password
        mock_creds.refresh.assert_called_once()


def test_youtube_auth_handles_refresh_token_error(tmp_path, mock_client_config, mock_credentials):
    """Verify YouTubeAuth falls back to full OAuth when refresh fails."""
    tokens_file = tmp_path / "tokens.json"
    auth = YouTubeAuth(client_config=mock_client_config, tokens_file=tokens_file)

    with (
        patch("sync.io.youtube.auth.get_secret", side_effect=Exception("1Password error")),
        patch(
            "sync.io.youtube.auth._fetch_new_oauth_tokens", return_value=mock_credentials
        ) as mock_oauth,
        patch("sync.io.youtube.auth._cache_access_token") as mock_cache,
    ):
        result = auth.get_credentials()

        # Should return the credentials from OAuth
        assert result == mock_credentials
        # Should have fallen back to full OAuth flow
        mock_oauth.assert_called_once_with(mock_client_config, API_SCOPES)
        mock_cache.assert_called_once()


def test_youtube_auth_handles_invalid_refresh_token(tmp_path, mock_client_config, mock_credentials):
    """Verify YouTubeAuth falls back to full OAuth when refresh token is invalid."""
    tokens_file = tmp_path / "tokens.json"
    auth = YouTubeAuth(client_config=mock_client_config, tokens_file=tokens_file)

    with (
        patch("sync.io.youtube.auth.get_secret", return_value="invalid_refresh_token"),
        patch("sync.io.youtube.auth.Credentials") as mock_creds_class,
        patch(
            "sync.io.youtube.auth._fetch_new_oauth_tokens", return_value=mock_credentials
        ) as mock_oauth,
        patch("sync.io.youtube.auth._cache_access_token") as mock_cache,
    ):
        refresh_creds = Mock(spec=Credentials)
        refresh_creds.refresh.side_effect = Exception("Invalid refresh token")
        mock_creds_class.return_value = refresh_creds

        result = auth.get_credentials()

        # Should return the credentials from OAuth
        assert result == mock_credentials
        # Should have fallen back to full OAuth flow
        mock_oauth.assert_called_once()
        mock_cache.assert_called_once()


def test_youtube_auth_uses_custom_scopes(tmp_path, mock_client_config):
    """Verify YouTubeAuth respects custom scopes."""
    tokens_file = tmp_path / "tokens.json"
    custom_scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    auth = YouTubeAuth(
        client_config=mock_client_config, tokens_file=tokens_file, scopes=custom_scopes
    )

    assert auth.scopes == custom_scopes


def test_youtube_auth_defaults_to_api_scopes(tmp_path, mock_client_config):
    """Verify YouTubeAuth uses API_SCOPES by default."""
    tokens_file = tmp_path / "tokens.json"
    auth = YouTubeAuth(client_config=mock_client_config, tokens_file=tokens_file)

    assert auth.scopes == API_SCOPES


def test_create_auth_from_1password(mock_client_config):
    """Verify create_auth_from_1password retrieves config from 1Password."""
    with (
        patch("sync.io.youtube.auth.get_secret", return_value=json.dumps(mock_client_config)),
        patch("sync.io.youtube.auth._get_tokens_file", return_value=Path("/tmp/tokens.json")),
    ):
        auth = create_auth_from_1password()

        assert isinstance(auth, YouTubeAuth)
        assert auth.client_config == mock_client_config
        assert auth.tokens_file == Path("/tmp/tokens.json")
