"""
Pushover API response models

Parse at I/O boundary per architecture rules.
https://pushover.net/api
"""

from pydantic import BaseModel


class PushoverResponse(BaseModel):
    """Response from Pushover message API"""

    status: int  # 1 = success, 0 = error
    request: str  # Unique request ID
    errors: list[str] | None = None  # Only present on error
