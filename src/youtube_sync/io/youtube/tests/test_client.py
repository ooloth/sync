"""
Tests for YouTube Data API client
"""

import datetime
from unittest.mock import Mock, patch

import pytest
from inline_snapshot import snapshot
from pydantic_core import TzInfo

from youtube_sync.io.youtube import YouTubeAuth, YouTubeClient, YouTubeSubscription, create_client


@pytest.fixture
def mock_credentials():
    """Mock Google OAuth2 credentials."""
    creds = Mock()
    creds.token = "mock_access_token"
    creds.valid = True
    return creds


@pytest.fixture
def mock_youtube_resource():
    """Mock YouTube API resource."""
    return Mock()


def test_client_initializes_youtube_resource(mock_credentials, mock_youtube_resource):
    """Verify YouTubeClient initializes the YouTube API resource correctly."""
    with patch(
        "youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource
    ) as mock_build:
        client = YouTubeClient(mock_credentials)

        mock_build.assert_called_once_with(
            credentials=mock_credentials,
            serviceName="youtube",
            version="v3",
        )
        assert client._youtube == mock_youtube_resource


def test_list_subscriptions_handles_single_page(mock_credentials, mock_youtube_resource):
    """Verify list_subscriptions handles a single page of results."""
    # Mock API response
    mock_response = {
        "items": [
            {
                "kind": "youtube#subscription",
                "etag": "test_etag_123",
                "id": "sub123",
                "snippet": {
                    "publishedAt": "2024-01-15T12:00:00Z",
                    "title": "Test Channel",
                    "description": "A test channel",
                    "channelId": "UCuser123",
                    "resourceId": {
                        "kind": "youtube#channel",
                        "channelId": "UC123",
                    },
                    "thumbnails": {
                        "default": {
                            "url": "https://example.com/thumb.jpg",
                            "width": 88,
                            "height": 88,
                        }
                    },
                },
                "contentDetails": {
                    "totalItemCount": 42,
                    "newItemCount": 5,
                    "activityType": "all",
                },
            }
        ]
    }

    # Set up mock chain: youtube.subscriptions().list().execute()
    mock_subs_resource = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = mock_response
    mock_subs_resource.list.return_value = mock_request
    mock_subs_resource.list_next.return_value = None  # No next page
    mock_youtube_resource.subscriptions.return_value = mock_subs_resource

    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        client = YouTubeClient(mock_credentials)
        subs = client.list_subscriptions()

    assert len(subs) == 1
    assert isinstance(subs[0], YouTubeSubscription)
    # Use snapshot for the subscription object to ensure complete validation
    assert subs[0].model_dump() == snapshot(
        {
            "kind": "youtube#subscription",
            "etag": "test_etag_123",
            "id": "sub123",
            "snippet": {
                "published_at": datetime.datetime(2024, 1, 15, 12, 0, tzinfo=TzInfo(0)),
                "title": "Test Channel",
                "description": "A test channel",
                "channel_id": "UCuser123",
                "resource_id": {"kind": "youtube#channel", "channel_id": "UC123"},
                "thumbnails": {
                    "default": {"url": "https://example.com/thumb.jpg", "width": 88, "height": 88},
                    "medium": None,
                    "high": None,
                },
                "channel_title": None,
            },
            "content_details": {
                "total_item_count": 42,
                "new_item_count": 5,
                "activity_type": "all",
            },
        }
    )


def test_list_subscriptions_handles_pagination(mock_credentials, mock_youtube_resource):
    """Verify list_subscriptions handles multiple pages correctly."""
    # Mock first page
    page1 = {
        "items": [
            {
                "kind": "youtube#subscription",
                "etag": "etag1",
                "id": "sub1",
                "snippet": {
                    "publishedAt": "2024-01-01T12:00:00Z",
                    "title": "Channel 1",
                    "description": "First channel",
                    "channelId": "UCuser1",
                    "resourceId": {"kind": "youtube#channel", "channelId": "UC1"},
                    "thumbnails": {"default": {"url": "https://example.com/1.jpg"}},
                },
                "contentDetails": {"totalItemCount": 10, "newItemCount": 1, "activityType": "all"},
            }
        ]
    }

    # Mock second page
    page2 = {
        "items": [
            {
                "kind": "youtube#subscription",
                "etag": "etag2",
                "id": "sub2",
                "snippet": {
                    "publishedAt": "2024-01-02T12:00:00Z",
                    "title": "Channel 2",
                    "description": "Second channel",
                    "channelId": "UCuser2",
                    "resourceId": {"kind": "youtube#channel", "channelId": "UC2"},
                    "thumbnails": {"default": {"url": "https://example.com/2.jpg"}},
                },
                "contentDetails": {"totalItemCount": 20, "newItemCount": 2, "activityType": "all"},
            }
        ]
    }

    # Set up mock chain with pagination
    mock_subs_resource = Mock()
    mock_request1 = Mock()
    mock_request2 = Mock()
    mock_request1.execute.return_value = page1
    mock_request2.execute.return_value = page2

    mock_subs_resource.list.return_value = mock_request1
    mock_subs_resource.list_next.side_effect = [mock_request2, None]  # Second page, then done
    mock_youtube_resource.subscriptions.return_value = mock_subs_resource

    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        client = YouTubeClient(mock_credentials)
        subs = client.list_subscriptions()

    assert len(subs) == 2
    # Use snapshots for dict representation to avoid Pydantic aliasing issues
    assert subs[0].model_dump() == snapshot(
        {
            "kind": "youtube#subscription",
            "etag": "etag1",
            "id": "sub1",
            "snippet": {
                "published_at": datetime.datetime(2024, 1, 1, 12, 0, tzinfo=TzInfo(0)),
                "title": "Channel 1",
                "description": "First channel",
                "channel_id": "UCuser1",
                "resource_id": {"kind": "youtube#channel", "channel_id": "UC1"},
                "thumbnails": {
                    "default": {"url": "https://example.com/1.jpg", "width": None, "height": None},
                    "medium": None,
                    "high": None,
                },
                "channel_title": None,
            },
            "content_details": {
                "total_item_count": 10,
                "new_item_count": 1,
                "activity_type": "all",
            },
        }
    )
    assert subs[1].model_dump() == snapshot(
        {
            "kind": "youtube#subscription",
            "etag": "etag2",
            "id": "sub2",
            "snippet": {
                "published_at": datetime.datetime(2024, 1, 2, 12, 0, tzinfo=TzInfo(0)),
                "title": "Channel 2",
                "description": "Second channel",
                "channel_id": "UCuser2",
                "resource_id": {"kind": "youtube#channel", "channel_id": "UC2"},
                "thumbnails": {
                    "default": {"url": "https://example.com/2.jpg", "width": None, "height": None},
                    "medium": None,
                    "high": None,
                },
                "channel_title": None,
            },
            "content_details": {
                "total_item_count": 20,
                "new_item_count": 2,
                "activity_type": "all",
            },
        }
    )


def test_list_subscriptions_handles_empty_response(mock_credentials, mock_youtube_resource):
    """Verify list_subscriptions handles empty results gracefully."""
    mock_response = {"items": []}

    mock_subs_resource = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = mock_response
    mock_subs_resource.list.return_value = mock_request
    mock_subs_resource.list_next.return_value = None
    mock_youtube_resource.subscriptions.return_value = mock_subs_resource

    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        client = YouTubeClient(mock_credentials)
        subs = client.list_subscriptions()

    assert len(subs) == 0


def test_list_subscriptions_requests_correct_parameters(mock_credentials, mock_youtube_resource):
    """Verify list_subscriptions requests the correct API parameters."""
    mock_response = {"items": []}

    mock_subs_resource = Mock()
    mock_request = Mock()
    mock_request.execute.return_value = mock_response
    mock_subs_resource.list.return_value = mock_request
    mock_subs_resource.list_next.return_value = None
    mock_youtube_resource.subscriptions.return_value = mock_subs_resource

    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        client = YouTubeClient(mock_credentials)
        client.list_subscriptions()

    mock_subs_resource.list.assert_called_once_with(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50,
    )


def test_client_close(mock_credentials, mock_youtube_resource):
    """Verify close() cleans up the YouTube resource."""
    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        client = YouTubeClient(mock_credentials)
        client.close()

    mock_youtube_resource.close.assert_called_once()


def test_client_context_manager(mock_credentials, mock_youtube_resource):
    """Verify client works as context manager and auto-closes."""
    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        with YouTubeClient(mock_credentials) as client:
            assert client._youtube == mock_youtube_resource

    mock_youtube_resource.close.assert_called_once()


def test_create_client_with_provided_auth(mock_credentials, mock_youtube_resource):
    """Verify create_client uses provided auth instance."""
    mock_auth = Mock(spec=YouTubeAuth)
    mock_auth.get_credentials.return_value = mock_credentials

    with patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource):
        client = create_client(auth=mock_auth)

    mock_auth.get_credentials.assert_called_once()
    assert isinstance(client, YouTubeClient)


def test_create_client_without_auth_uses_1password(mock_credentials, mock_youtube_resource):
    """Verify create_client creates auth from 1Password when auth not provided."""
    with (
        patch("youtube_sync.io.youtube.client.create_auth_from_1password") as mock_create_auth,
        patch("youtube_sync.io.youtube.client.build", return_value=mock_youtube_resource),
    ):
        mock_auth = Mock(spec=YouTubeAuth)
        mock_auth.get_credentials.return_value = mock_credentials
        mock_create_auth.return_value = mock_auth

        client = create_client()

    mock_create_auth.assert_called_once()
    mock_auth.get_credentials.assert_called_once()
    assert isinstance(client, YouTubeClient)
