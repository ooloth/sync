"""Logging configuration for youtube-sync."""

import logging
import sys


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging based on verbosity level.

    Args:
        verbose: If True, show DEBUG logs. If False, only show WARNING+.

    Usage:
        setup_logging(verbose=True)
        logger = logging.getLogger(__name__)
        logger.debug("This will be shown")
    """
    level = logging.DEBUG if verbose else logging.WARNING

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
        force=True,  # Override any existing configuration
    )

    # Silence noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
