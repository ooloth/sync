"""
Tests for Feedbin API client
"""

import base64
import json

import httpx
from inline_snapshot import snapshot
from pydantic import HttpUrl
from pytest_httpx import HTTPXMock
from result import Err, Ok

from youtube_sync.io.feedbin import FeedbinAuth, FeedbinClient, FeedbinSubscription


def test_list_subscriptions_parses_response(httpx_mock: HTTPXMock):
    """Verify we parse Feedbin subscription responses correctly."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        json=[
            {
                "id": 123,
                "feed_id": 456,
                "title": "YouTube - TestChannel",
                "feed_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC123",
                "site_url": "https://www.youtube.com/channel/UC123",
                "created_at": "2024-01-15T12:00:00.000000Z",
            }
        ],
    )

    client = FeedbinClient(FeedbinAuth("test", "test"))
    result = client.list_subscriptions()

    assert isinstance(result, Ok)
    subs = result.ok_value
    assert len(subs) == 1
    assert subs[0] == snapshot(
        FeedbinSubscription(
            id=123,
            feed_id=456,
            title="YouTube - TestChannel",
            feed_url=HttpUrl("https://www.youtube.com/feeds/videos.xml?channel_id=UC123"),
            site_url=HttpUrl("https://www.youtube.com/channel/UC123"),
            created_at="2024-01-15T12:00:00.000000Z",
        )
    )


def test_list_subscriptions_handles_empty_list(httpx_mock: HTTPXMock):
    """Verify we handle an empty subscription list."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        json=[],
    )

    client = FeedbinClient(FeedbinAuth("test", "test"))
    result = client.list_subscriptions()

    assert isinstance(result, Ok)
    assert result.ok_value == []


def test_list_subscriptions_handles_null_site_url(httpx_mock: HTTPXMock):
    """Verify we handle subscriptions without site_url."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        json=[
            {
                "id": 123,
                "feed_id": 456,
                "title": "Test Feed",
                "feed_url": "https://example.com/feed.xml",
                "site_url": None,
                "created_at": "2024-01-15T12:00:00.000000Z",
            }
        ],
    )

    client = FeedbinClient(FeedbinAuth("test", "test"))
    result = client.list_subscriptions()

    assert isinstance(result, Ok)
    subs = result.ok_value
    assert len(subs) == 1
    assert subs[0] == snapshot(
        FeedbinSubscription(
            id=123,
            feed_id=456,
            title="Test Feed",
            feed_url=HttpUrl("https://example.com/feed.xml"),
            site_url=None,
            created_at="2024-01-15T12:00:00.000000Z",
        )
    )


def test_create_subscription_returns_parsed_model(httpx_mock: HTTPXMock):
    """Verify create returns parsed subscription."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        json={
            "id": 789,
            "feed_id": 999,
            "title": "New Channel",
            "feed_url": "https://example.com/feed.xml",
            "site_url": None,
            "created_at": "2024-01-15T13:00:00.000000Z",
        },
    )

    client = FeedbinClient(FeedbinAuth("test", "test"))
    result = client.create_subscription("https://example.com/feed.xml")

    assert isinstance(result, Ok)
    sub = result.ok_value
    assert sub == snapshot(
        FeedbinSubscription(
            id=789,
            feed_id=999,
            title="New Channel",
            feed_url=HttpUrl("https://example.com/feed.xml"),
            site_url=None,
            created_at="2024-01-15T13:00:00.000000Z",
        )
    )


def test_create_subscription_sends_correct_payload(httpx_mock: HTTPXMock):
    """Verify create sends the expected JSON payload."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        json={
            "id": 1,
            "feed_id": 1,
            "title": "Test",
            "feed_url": "https://example.com/feed.xml",
            "site_url": None,
            "created_at": "2024-01-15T13:00:00.000000Z",
        },
    )

    client = FeedbinClient(FeedbinAuth("test", "test"))
    result = client.create_subscription("https://example.com/feed.xml")
    assert isinstance(result, Ok)

    request = httpx_mock.get_request()

    assert isinstance(request, httpx.Request)
    assert request.method == "POST"
    assert request.headers["Content-Type"] == "application/json; charset=utf-8"

    # httpx uses read() for streaming bodies, so we need to check the sent data
    assert json.loads(request.content) == {"feed_url": "https://example.com/feed.xml"}


def test_client_sets_auth_header(httpx_mock: HTTPXMock):
    """Verify client sends basic auth credentials."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        json=[],
    )

    client = FeedbinClient(FeedbinAuth("myuser", "mypass"))
    result = client.list_subscriptions()
    assert isinstance(result, Ok)

    request = httpx_mock.get_request()
    assert isinstance(request, httpx.Request)

    # httpx encodes basic auth as base64
    expected_auth = base64.b64encode(b"myuser:mypass").decode("ascii")
    assert request.headers["Authorization"] == f"Basic {expected_auth}"


def test_client_returns_err_on_http_error(httpx_mock: HTTPXMock):
    """Verify client returns Err on HTTP errors."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        status_code=401,
        json={"error": "Unauthorized"},
    )

    client = FeedbinClient(FeedbinAuth("wrong", "wrong"))
    result = client.list_subscriptions()

    assert isinstance(result, Err)
    assert "Failed to list Feedbin subscriptions" in result.err_value


def test_client_context_manager():
    """Verify client works as context manager."""
    with FeedbinClient(FeedbinAuth("test", "test")) as client:
        assert client._client is not None
        assert not client._client.is_closed

    # Client should be closed after context exit
    assert client._client.is_closed
