"""Centralized logging bootstrap for the application.

This module configures logging consistently across the project. It is intended to be
invoked once at application startup. Tests typically do not need to call this; they can
rely on Python's default logging configuration unless a particular test requires it.

Design goals (docs/plan.md, docs/tasks.md Task 2):
- Single place to define formatters, levels, and module filters.
- Minimal, predictable formatting suitable for both developer console and CI logs.
- Avoid duplicate handlers if setup is called multiple times.
"""
from __future__ import annotations

from typing import Optional, Union
import logging

# Default log format: timestamp, level, logger name, message.
_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_DEFAULT_DATEFMT = "%H:%M:%S"


def _coerce_level(level: Union[int, str, None]) -> int:
    """Convert a level name or integer to a logging level int.

    Accepts standard level names (case-insensitive) or integers. Falls back to INFO.
    """
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        lvl = level.upper()
        return getattr(logging, lvl, logging.INFO)
    return logging.INFO


def setup_logging(level: Union[int, str, None] = None, *, fmt: Optional[str] = None, datefmt: Optional[str] = None) -> None:
    """Initialize root logging configuration for the app.

    - Sets a StreamHandler on the root logger if none present.
    - Applies formatter with time, level, name, and message.
    - Establishes sensible default levels and quiets noisy third-party loggers.

    This function is idempotent: calling it multiple times will not attach duplicate
    handlers.
    """
    root = logging.getLogger()

    # Only attach our handler if there are no handlers already (idempotent behavior).
    if not root.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt or _DEFAULT_FORMAT, datefmt or _DEFAULT_DATEFMT)
        handler.setFormatter(formatter)
        root.addHandler(handler)

    # Set overall level.
    root.setLevel(_coerce_level(level))

    # Quiet some verbose third-party modules by default.
    logging.getLogger("PySide6").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Project package loggers can inherit root level; ensure a consistent default.
    for name in (
        "core",
        "controllers",
        "ui",
    ):
        logging.getLogger(name).setLevel(root.level)


__all__ = ["setup_logging"]



def format_context(**ctx: object) -> str:
    """Format a context dict into a compact ``key=value`` sequence.

    Only non-None values are included. Example: "frame=12 object=lamp op=copy".
    """
    parts = [f"{k}={v}" for k, v in ctx.items() if v is not None]
    return " ".join(parts)


def log_with_context(logger: logging.Logger, level: int, msg: str, **ctx: object) -> None:
    """Log a message and append a serialized context segment.

    This is a lightweight approach that avoids custom formatters while keeping
    contextual information (frame index, object/puppet names, operation type)
    close to the message for easier grepping in CI logs.
    """
    if ctx:
        msg = f"{msg} | ctx={format_context(**ctx)}"
    logger.log(level, msg)
