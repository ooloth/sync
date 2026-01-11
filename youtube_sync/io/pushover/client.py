"""
Docs:
- https://pushover-complete.readthedocs.io/en/stable/api.html
- https://pushover.net/api
"""

import os

from common.logs import log
from common.secrets import get_secret
from pushover_complete import PushoverAPI  # type: ignore[import-untyped]

OP_ITEM = "Pushover"
OP_FIELD_APP_TOKEN = "app: scripts repo"
OP_FIELD_USER_KEY = "user key"

_client: PushoverAPI | None = None


def get_client() -> PushoverAPI:
    """Return a reusable pushover client."""
    global _client

    if _client is None:
        _client = PushoverAPI(get_secret(OP_ITEM, OP_FIELD_APP_TOKEN))

    return _client


def send_notification(*, title: str, html: str, dry_run: bool = False) -> None:
    """
    Send a notification with the given subject and HTML content.

    Args:
        title (str): The subject of the notification.
        html (str): The HTML content of the notification.
        dry_run (bool): If True, the notification will not be sent. Defaults to False.

    Raises:
        Exception: If there is an error sending the notification, it will be logged.
    """
    dry_run = os.getenv("DRY_RUN") == "true" or dry_run

    try:
        client = get_client()

        if dry_run:
            log.info(f"🌵 Skipping '{title}' email (dry run)")
            return

        client.send_message(
            user=get_secret(OP_ITEM, OP_FIELD_USER_KEY),
            title=title,
            message=html,
            html=True,
        )
        log.info("✅ Notification sent successfully.")
    except Exception:
        log.error(
            f"🚨 There was a problem sending the '{title}' notification.", exc_info=True
        )
