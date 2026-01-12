"""
Tests for Feedbin API client
"""

import base64
import json

import httpx
import pytest
from inline_snapshot import snapshot
from pydantic import HttpUrl
from pytest_httpx import HTTPXMock

from youtube_sync.io.feedbin import FeedbinClient, FeedbinSubscription


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

    client = FeedbinClient(username="test", password="test")
    subs = client.list_subscriptions()

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

    client = FeedbinClient(username="test", password="test")
    subs = client.list_subscriptions()

    assert subs == []


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

    client = FeedbinClient(username="test", password="test")
    subs = client.list_subscriptions()

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

    client = FeedbinClient(username="test", password="test")
    sub = client.create_subscription("https://example.com/feed.xml")

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

    client = FeedbinClient(username="test", password="test")
    client.create_subscription("https://example.com/feed.xml")

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

    client = FeedbinClient(username="myuser", password="mypass")
    client.list_subscriptions()

    request = httpx_mock.get_request()
    assert isinstance(request, httpx.Request)

    # httpx encodes basic auth as base64
    expected_auth = base64.b64encode(b"myuser:mypass").decode("ascii")
    assert request.headers["Authorization"] == f"Basic {expected_auth}"


def test_client_raises_on_http_error(httpx_mock: HTTPXMock):
    """Verify client raises exception on HTTP errors."""
    httpx_mock.add_response(
        url="https://api.feedbin.com/v2/subscriptions.json",
        status_code=401,
        json={"error": "Unauthorized"},
    )

    client = FeedbinClient(username="wrong", password="wrong")

    with pytest.raises(Exception):  # httpx.HTTPStatusError
        client.list_subscriptions()


def test_client_context_manager():
    """Verify client works as context manager."""
    with FeedbinClient(username="test", password="test") as client:
        assert client._client is not None
        assert not client._client.is_closed

    # Client should be closed after context exit
    assert client._client.is_closed
