"""Logging configuration for youtube-sync."""

import json
import logging
import sys
from pathlib import Path

import structlog
from structlog.stdlib import BoundLogger

from rich.console import Console
from rich.traceback import install as install_rich_traceback


def setup_logging(verbose: bool = False, job_name: str | None = None) -> None:
    """
    Configure structured logging with Rich console + JSON file output.

    Args:
        verbose: If True, show DEBUG logs. If False, show INFO+ logs.
        job_name: Optional job name for per-job log files (e.g., "sync_subs")

    Usage:
        setup_logging(verbose=True, job_name="sync_subs")
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

    # Configure root logger level (no handlers yet)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Configure structlog to use stdlib logging backend (so file handlers work)
    structlog.configure(
        processors=[
            # Add contextvars to all log entries
            structlog.contextvars.merge_contextvars,
            # Add log level to event dict
            structlog.processors.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add timestamp (ISO format for files, will be reformatted for console)
            structlog.processors.TimeStamper(fmt="iso", utc=False),
            # Format stack info
            structlog.processors.StackInfoRenderer(),
            # This must be last: sends to stdlib logging
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        # Use stdlib logging as backend
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # Use dict for context
        context_class=dict,
        # Cache logger instances
        cache_logger_on_first_use=True,
    )

    # Setup file logging handlers
    _setup_file_logging(log_level, job_name)

    # Configure console handler with Rich formatting
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                # Re-add timestamp in short format for console
                structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
                # Render to console with Rich styling
                structlog.dev.ConsoleRenderer(
                    colors=console.is_terminal,
                ),
            ],
            foreign_pre_chain=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso", utc=False),
            ],
        )
    )

    # Add console handler to root logger
    root_logger.addHandler(console_handler)

    # Silence noisy third-party libraries via stdlib logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)


def _setup_file_logging(log_level: int, job_name: str | None) -> None:
    """
    Setup JSON file logging with separate files for different log levels.

    Files created in .logs/:
    - {job_name}.jsonl - All logs for this specific job
    - errors.jsonl - All ERROR+ logs from any job
    - warnings.jsonl - Only WARNING logs (not ERROR) from any job
    """
    # Create logs directory
    logs_dir = Path(".logs")
    logs_dir.mkdir(exist_ok=True)

    # Get root logger for file handlers
    root_logger = logging.getLogger()

    # JSON formatter using structlog's stdlib integration
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=False),
        ],
    )

    # Handler 1: Per-job log file (if job_name provided)
    if job_name:
        job_handler = logging.FileHandler(logs_dir / f"{job_name}.jsonl", mode="a")
        job_handler.setLevel(log_level)
        job_handler.setFormatter(json_formatter)
        root_logger.addHandler(job_handler)

    # Handler 2: Errors file (ERROR and CRITICAL only)
    error_handler = logging.FileHandler(logs_dir / "errors.jsonl", mode="a")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)

    # Handler 3: Warnings file (WARNING only, not ERROR+)
    class WarningOnlyFilter(logging.Filter):
        """Only allow WARNING level (not ERROR or CRITICAL)."""
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == logging.WARNING

    warning_handler = logging.FileHandler(logs_dir / "warnings.jsonl", mode="a")
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(WarningOnlyFilter())
    warning_handler.setFormatter(json_formatter)
    root_logger.addHandler(warning_handler)


def get_logger(name: str) -> BoundLogger:
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
