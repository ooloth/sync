"""
YouTube Data API models
https://developers.google.com/youtube/v3/docs/subscriptions
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThumbnailDetails(BaseModel):
    """Thumbnail image details."""

    url: str
    width: int | None = None
    height: int | None = None


class Thumbnails(BaseModel):
    """Collection of thumbnail images at different resolutions."""

    default: ThumbnailDetails | None = None
    medium: ThumbnailDetails | None = None
    high: ThumbnailDetails | None = None


class ResourceId(BaseModel):
    """Identifies the resource (channel) being subscribed to."""

    kind: str
    channel_id: str = Field(alias="channelId")


class SubscriptionSnippet(BaseModel):
    """Basic subscription details."""

    published_at: datetime = Field(alias="publishedAt")
    title: str
    description: str
    channel_id: str = Field(alias="channelId")  # Subscriber's channel ID
    resource_id: ResourceId = Field(alias="resourceId")  # Subscribed channel
    thumbnails: Thumbnails
    channel_title: str | None = Field(None, alias="channelTitle")  # Subscribed channel name


class ContentDetails(BaseModel):
    """Subscription statistics."""

    total_item_count: int = Field(alias="totalItemCount")
    new_item_count: int = Field(alias="newItemCount")
    activity_type: str = Field(alias="activityType")


class YouTubeSubscription(BaseModel):
    """YouTube subscription resource."""

    model_config = ConfigDict(populate_by_name=True)

    kind: str
    etag: str
    id: str
    snippet: SubscriptionSnippet
    content_details: ContentDetails | None = Field(None, alias="contentDetails")
