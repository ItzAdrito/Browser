"""Structured logging configuration for PyBrowser."""

from __future__ import annotations

import logging
import os
import sys
from typing import Final

_DEFAULT_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)
_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def setup_root_logger() -> None:
    """Initialize root logger with standard formatting."""
    log_level_name = os.getenv("PYBROWSER_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt=_DEFAULT_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance for a given module name.

    Args:
        name: Name of the calling module, typically __name__.

    Returns:
        Configured logger instance.
    """
    setup_root_logger()
    return logging.getLogger(name)
