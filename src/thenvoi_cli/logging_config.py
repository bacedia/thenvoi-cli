"""Logging configuration for thenvoi-cli."""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.logging import RichHandler

if TYPE_CHECKING:
    pass


class SanitizingFilter(logging.Filter):
    """Filter to sanitize sensitive data from log records."""

    # Patterns to redact
    PATTERNS = [
        (re.compile(r"sk-[a-zA-Z0-9_-]{20,}"), "[REDACTED_API_KEY]"),
        (re.compile(r"api_key[=:]\s*['\"]?[\w-]+['\"]?", re.I), "api_key=[REDACTED]"),
        (re.compile(r"password[=:]\s*['\"]?[\w-]+['\"]?", re.I), "password=[REDACTED]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize the log record message."""
        msg = str(record.msg)
        for pattern, replacement in self.PATTERNS:
            msg = pattern.sub(replacement, msg)
        record.msg = msg
        return True


def setup_logging(
    verbosity: int = 0,
    log_file: str | None = None,
    no_color: bool | None = None,
) -> logging.Logger:
    """Configure logging for the CLI.

    Args:
        verbosity: Verbosity level (-1=quiet, 0=normal, 1=verbose, 2=debug).
        log_file: Optional path to log file.
        no_color: Disable colors. If None, checks NO_COLOR env var.

    Returns:
        Configured logger instance.
    """
    # Determine color setting
    if no_color is None:
        no_color = os.getenv("NO_COLOR") is not None

    # Map verbosity to log level
    levels = {
        -1: logging.ERROR,
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    level = levels.get(verbosity, logging.INFO)

    # Create logger
    logger = logging.getLogger("thenvoi_cli")
    logger.setLevel(level)
    logger.handlers.clear()

    # Add sanitizing filter
    logger.addFilter(SanitizingFilter())

    # Console handler
    if not no_color and sys.stderr.isatty():
        console = Console(stderr=True)
        handler: logging.Handler = RichHandler(
            console=console,
            show_time=verbosity >= 2,
            show_path=verbosity >= 2,
            rich_tracebacks=True,
            tracebacks_show_locals=verbosity >= 2,
        )
    else:
        handler = logging.StreamHandler(sys.stderr)
        fmt = "%(levelname)s: %(message)s"
        if verbosity >= 2:
            fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    handler.setLevel(level)
    logger.addHandler(handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        file_handler.addFilter(SanitizingFilter())
        logger.addHandler(file_handler)

    # Also configure SDK loggers
    for sdk_logger_name in ["thenvoi", "thenvoi.platform", "thenvoi.runtime"]:
        sdk_logger = logging.getLogger(sdk_logger_name)
        sdk_logger.setLevel(level)
        sdk_logger.handlers.clear()
        sdk_logger.addHandler(handler)
        sdk_logger.addFilter(SanitizingFilter())

    return logger


def get_logger() -> logging.Logger:
    """Get the CLI logger instance."""
    return logging.getLogger("thenvoi_cli")
