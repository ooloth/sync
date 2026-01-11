"""
Feedbin API response models

Parse at I/O boundary per architecture rules.
https://github.com/feedbin/feedbin-api
"""

from pydantic import BaseModel, HttpUrl


class FeedbinSubscription(BaseModel):
    """Feedbin subscription response"""

    id: int
    feed_id: int
    title: str
    feed_url: HttpUrl
    site_url: HttpUrl | None = None
    created_at: str  # ISO datetime string

    # Other fields exist in the API but we don't need them yet:
    # - groups: list of tag names
    # - last_downloaded_at: datetime
