"""
Tests for Pushover API client
"""

import httpx
import pytest
from inline_snapshot import snapshot
from pytest_httpx import HTTPXMock

from youtube_sync.io.pushover.client import PushoverClient
from youtube_sync.io.pushover.models import PushoverResponse


def test_send_message_basic(httpx_mock: HTTPXMock):
    """Verify we can send a basic text message."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        json={
            "status": 1,
            "request": "abc123-def456-ghi789",
        },
    )

    client = PushoverClient(app_token="test_app", user_key="test_user")
    response = client.send_message("Test message")

    assert response == snapshot(
        PushoverResponse(
            status=1,
            request="abc123-def456-ghi789",
            errors=None,
        )
    )


def test_send_message_with_title(httpx_mock: HTTPXMock):
    """Verify we can send a message with a title."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        json={
            "status": 1,
            "request": "xyz789",
        },
    )

    client = PushoverClient(app_token="test_app", user_key="test_user")
    response = client.send_message("Message body", title="Test Title")

    assert response.status == 1

    # Verify title was sent in payload
    request = httpx_mock.get_request()
    assert isinstance(request, httpx.Request)
    assert b"title=Test+Title" in request.content


def test_send_message_with_html(httpx_mock: HTTPXMock):
    """Verify we can send HTML-formatted messages."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        json={
            "status": 1,
            "request": "html123",
        },
    )

    client = PushoverClient(app_token="test_app", user_key="test_user")
    response = client.send_message("<b>Bold text</b>", html=True)

    assert response.status == 1

    # Verify html flag was sent
    request = httpx_mock.get_request()
    assert isinstance(request, httpx.Request)
    assert b"html=1" in request.content


def test_send_message_sends_correct_payload(httpx_mock: HTTPXMock):
    """Verify send_message sends the expected form data."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        json={
            "status": 1,
            "request": "req123",
        },
    )

    client = PushoverClient(app_token="my_app_token", user_key="my_user_key")
    client.send_message("Hello world", title="Greeting", html=True)

    request = httpx_mock.get_request()
    assert isinstance(request, httpx.Request)
    assert request.method == "POST"

    # Verify all required fields in form data
    content = request.content.decode("utf-8")
    assert "token=my_app_token" in content
    assert "user=my_user_key" in content
    assert "message=Hello+world" in content
    assert "title=Greeting" in content
    assert "html=1" in content


def test_send_message_parses_response(httpx_mock: HTTPXMock):
    """Verify we parse Pushover response correctly."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        json={
            "status": 1,
            "request": "unique-request-id-12345",
        },
    )

    client = PushoverClient(app_token="test_app", user_key="test_user")
    response = client.send_message("Test")

    assert response == snapshot(
        PushoverResponse(
            status=1,
            request="unique-request-id-12345",
            errors=None,
        )
    )


def test_send_message_handles_error_response(httpx_mock: HTTPXMock):
    """Verify we parse error responses with errors field."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        json={
            "status": 0,
            "request": "error-request-id",
            "errors": ["user identifier is invalid", "application token is invalid"],
        },
    )

    client = PushoverClient(app_token="bad_token", user_key="bad_user")
    response = client.send_message("Test")

    assert response == snapshot(
        PushoverResponse(
            status=0,
            request="error-request-id",
            errors=["user identifier is invalid", "application token is invalid"],
        )
    )


def test_client_raises_on_http_error(httpx_mock: HTTPXMock):
    """Verify client raises exception on HTTP errors."""
    httpx_mock.add_response(
        url="https://api.pushover.net/1/messages.json",
        status_code=400,
        json={
            "status": 0,
            "errors": ["application token is invalid"],
        },
    )

    client = PushoverClient(app_token="invalid", user_key="test_user")

    with pytest.raises(Exception):  # httpx.HTTPStatusError
        client.send_message("Test")


def test_client_context_manager():
    """Verify client works as context manager."""
    with PushoverClient(app_token="test_app", user_key="test_user") as client:
        assert client._client is not None
        assert not client._client.is_closed

    # Client should be closed after context exit
    assert client._client.is_closed
