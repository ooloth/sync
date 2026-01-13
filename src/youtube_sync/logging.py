"""Logging configuration for youtube-sync."""

import logging
import sys

import structlog
from structlog.typing import FilteringBoundLogger


def setup_logging(verbose: bool = False) -> None:
    """
    Configure structured logging with excellent console output.

    Args:
        verbose: If True, show DEBUG logs. If False, show INFO+ logs.

    Usage:
        setup_logging(verbose=True)
        log = get_logger(__name__)
        log.debug("detailed message", key="value")
        log.info("important event", count=42)
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Configure structlog for beautiful console output
    structlog.configure(
        processors=[
            # Add contextvars to all log entries
            structlog.contextvars.merge_contextvars,
            # Add log level to event dict
            structlog.processors.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Format exceptions nicely
            structlog.processors.ExceptionRenderer(),
            # Render to console with colors and pretty formatting
            structlog.dev.ConsoleRenderer(
                colors=sys.stderr.isatty(),  # Only use colors if terminal
            ),
        ],
        # Wrapper for filtering by level
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        # Use dict for context
        context_class=dict,
        # Print to stderr
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        # Cache logger instances
        cache_logger_on_first_use=True,
    )

    # Silence noisy third-party libraries via stdlib logging
    # (structlog can still integrate with stdlib loggers if needed)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger for the given module.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        A structlog logger instance

    Usage:
        log = get_logger(__name__)
        log.info("user logged in", user_id=123, method="oauth")
    """
    return structlog.get_logger(name)
