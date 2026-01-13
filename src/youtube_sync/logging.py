"""Logging configuration for youtube-sync."""

import logging
import sys

import structlog
from structlog.typing import FilteringBoundLogger

from rich.console import Console
from rich.traceback import install as install_rich_traceback


def setup_logging(verbose: bool = False) -> None:
    """
    Configure structured logging with Rich for beautiful console output.

    Args:
        verbose: If True, show DEBUG logs. If False, show INFO+ logs.

    Usage:
        setup_logging(verbose=True)
        log = get_logger(__name__)
        log.debug("detailed message", key="value")
        log.info("important event", count=42)
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Install rich traceback handler for prettier exceptions
    install_rich_traceback(
        show_locals=True,  # Show local variables in tracebacks
        suppress=[structlog],  # Don't show structlog internals
    )

    # Create Rich console for output
    console = Console(stderr=True, force_terminal=sys.stderr.isatty())

    # Configure structlog with Rich integration
    structlog.configure(
        processors=[
            # Add contextvars to all log entries
            structlog.contextvars.merge_contextvars,
            # Add log level to event dict
            structlog.processors.add_log_level,
            # Add timestamp (short format: HH:MM:SS)
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
            # Format stack info
            structlog.processors.StackInfoRenderer(),
            # Render to console with styling (Rich handles exceptions automatically)
            structlog.dev.ConsoleRenderer(
                colors=console.is_terminal,
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

    # Integrate stdlib logging with structlog
    # This makes all logging.getLogger() calls flow through structlog processors
    structlog.stdlib.recreate_defaults(log_level=log_level)

    # Silence noisy third-party libraries via stdlib logging
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
