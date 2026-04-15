"""
Tests for 1Password secrets retrieval
"""

import subprocess
from unittest.mock import patch

import pytest

from sync.io.op.secrets import get_secret


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the get_secret cache before each test."""
    get_secret.cache_clear()
    yield
    get_secret.cache_clear()


def test_get_secret_success():
    """Verify get_secret returns secret from op CLI."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="my_secret\n", stderr=""
        )

        secret = get_secret("TestItem", "password")

        assert secret == "my_secret"
        mock_run.assert_called_once_with(
            ["op", "read", "op://Scripts/TestItem/password"],
            capture_output=True,
            text=True,
            check=True,
        )


def test_get_secret_strips_whitespace():
    """Verify get_secret strips leading/trailing whitespace."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="  secret_with_spaces  \n", stderr=""
        )

        secret = get_secret("TestItem", "field")

        assert secret == "secret_with_spaces"


def test_get_secret_caches_results():
    """Verify get_secret caches to avoid repeated subprocess calls."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="cached_secret\n", stderr=""
        )

        # Call three times with same args
        secret1 = get_secret("TestItem", "password")
        secret2 = get_secret("TestItem", "password")
        secret3 = get_secret("TestItem", "password")

        assert secret1 == secret2 == secret3 == "cached_secret"
        # Should only call subprocess once due to @lru_cache
        assert mock_run.call_count == 1


def test_get_secret_different_args_not_cached():
    """Verify get_secret only caches per unique (item, field) combination."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="secret1\n", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="secret2\n", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="secret3\n", stderr=""),
        ]

        # Different combinations should each trigger subprocess
        s1 = get_secret("Item1", "password")
        s2 = get_secret("Item2", "password")
        s3 = get_secret("Item1", "username")

        assert s1 == "secret1"
        assert s2 == "secret2"
        assert s3 == "secret3"
        assert mock_run.call_count == 3


def test_get_secret_cli_not_installed():
    """Verify helpful error when op CLI not installed."""
    with patch("subprocess.run", side_effect=FileNotFoundError("op not found")):
        with pytest.raises(
            FileNotFoundError, match="1Password CLI.*not found.*Install it"
        ) as exc_info:
            get_secret("TestItem", "password")

        # Verify original exception is chained
        assert exc_info.value.__cause__ is not None


def test_get_secret_cli_error_with_stderr():
    """Verify helpful error when op CLI fails with stderr."""
    error = subprocess.CalledProcessError(
        returncode=1, cmd=["op", "read", "..."], stderr="[ERROR] item not found\n"
    )

    with patch("subprocess.run", side_effect=error):
        with pytest.raises(
            RuntimeError,
            match="Failed to read secret 'password' from 1Password item 'TestItem'.*item not found",
        ) as exc_info:
            get_secret("TestItem", "password")

        # Verify original exception is chained
        assert exc_info.value.__cause__ is not None


def test_get_secret_cli_error_without_stderr():
    """Verify we handle op CLI errors even when stderr is empty."""
    error = subprocess.CalledProcessError(returncode=1, cmd=["op", "read", "..."], stderr="")

    with patch("subprocess.run", side_effect=error):
        with pytest.raises(
            RuntimeError, match="Failed to read secret.*no error output"
        ) as exc_info:
            get_secret("TestItem", "password")

        # Verify original exception is chained
        assert exc_info.value.__cause__ is not None


def test_get_secret_cli_error_stderr_none():
    """Verify we handle op CLI errors when stderr is None."""
    error = subprocess.CalledProcessError(returncode=1, cmd=["op", "read", "..."], stderr=None)

    with patch("subprocess.run", side_effect=error):
        with pytest.raises(RuntimeError, match="Failed to read secret.*no error output"):
            get_secret("TestItem", "password")


def test_get_secret_builds_correct_reference():
    """Verify get_secret builds the correct 1Password reference syntax."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="secret\n", stderr=""
        )

        get_secret("MyService", "api_key")

        # Verify the reference follows op://VAULT/ITEM/FIELD format
        call_args = mock_run.call_args[0][0]
        assert call_args == ["op", "read", "op://Scripts/MyService/api_key"]
