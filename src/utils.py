"""Utility functions for LuzidSettings"""

import logging
import os
import sys
from typing import Optional
from datetime import datetime


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the application-wide logger.

    Creates a console handler with a readable timestamp format.
    Safe to call multiple times — handlers are only attached once.

    Args:
        log_level: stdlib logging level constant (default INFO).

    Returns:
        The configured ``LuzidSettings`` logger instance.
    """
    logger = logging.getLogger("LuzidSettings")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        ))
        logger.addHandler(handler)

    return logger


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Return a bracketed HH:MM:SS timestamp string.

    Args:
        dt: Datetime to format.  Defaults to ``datetime.now()``.

    Returns:
        String like ``[14:32:07]``.
    """
    return (dt or datetime.now()).strftime("[%H:%M:%S]")


def truncate_string(text: str, max_length: int = 80) -> str:
    """
    Truncate *text* to *max_length* characters, appending ``…`` if cut.

    Args:
        text:       Input string.
        max_length: Maximum allowed length (must be >= 4).

    Returns:
        Original string if short enough, otherwise a truncated copy.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def get_resource_path(relative_path: str) -> str:
    """
    Resolve a path to a bundled resource so it works both when running
    from source and when packaged with PyInstaller / Nuitka.

    PyInstaller sets ``sys._MEIPASS`` to the temp extraction directory;
    for normal execution we resolve relative to the project root
    (two levels above this file: ``src/utils.py`` → project root).

    Args:
        relative_path: Path relative to the project root, e.g.
                       ``"assets/logo.png"``.

    Returns:
        Absolute filesystem path.
    """
    base = getattr(sys, "_MEIPASS", None) or _project_root()
    return os.path.join(base, relative_path)


def _project_root() -> str:
    """Return the absolute path of the project root directory."""
    # src/utils.py  →  src/  →  project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
