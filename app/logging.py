"""Structured logging configuration for Roxstar AI Voice Room Assistant."""

from __future__ import annotations

import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """Configure structured console logging suitable for development.

    Args:
        level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Format handler to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger instance.

    Args:
        name: Name of the logger module. Defaults to 'roxstar_assistant'.

    Returns:
        A standard logging.Logger instance.
    """
    return logging.getLogger(name or "roxstar_assistant")
