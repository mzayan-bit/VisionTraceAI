"""
VisionTraceAI — Enterprise-Grade Logging System.

Provides structured, rotating log output to both console and file.

Usage::

    from app.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Pipeline started", extra={"pipeline": "detection", "fps": 30})
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

from app.config.settings import PROJECT_ROOT

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOG_DIR: Final[Path] = PROJECT_ROOT / "logs"
LOG_FILE: Final[Path] = LOG_DIR / "visiontrace.log"
ERROR_LOG_FILE: Final[Path] = LOG_DIR / "visiontrace.error.log"

MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB per file
BACKUP_COUNT: Final[int] = 5              # keep 5 rotated copies

DEFAULT_LEVEL: Final[str] = "INFO"
ROOT_LOGGER_NAME: Final[str] = "visiontrace"

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
CONSOLE_FORMAT: Final[str] = (
    "\033[90m%(asctime)s\033[0m "
    "%(levelname_colored)s "
    "\033[36m%(name)s\033[0m"
    "\033[90m:\033[0m %(message)s"
)

FILE_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)

DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Mapping of log levels to ANSI-colored labels
_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG:    "\033[34m DEBUG  \033[0m",  # blue
    logging.INFO:     "\033[32m INFO   \033[0m",  # green
    logging.WARNING:  "\033[33m WARN   \033[0m",  # yellow
    logging.ERROR:    "\033[31m ERROR  \033[0m",  # red
    logging.CRITICAL: "\033[1;31m CRIT   \033[0m",  # bold red
}


class _ColoredFormatter(logging.Formatter):
    """Formatter that injects a ``levelname_colored`` field for console output."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        record.levelname_colored = _LEVEL_COLORS.get(record.levelno, record.levelname)  # type: ignore[attr-defined]
        return super().format(record)


class _StructuredFileFormatter(logging.Formatter):
    """File formatter that appends ``extra`` fields as key=value pairs.

    Any keys passed via ``extra={...}`` on the log call are appended to
    the message, giving structured context without requiring a JSON library.

    Example output::

        2026-05-31 18:00:00 | INFO     | app.pipelines.detect | run:42 | Detection started | model=yolov8n fps=30
    """

    # Standard LogRecord attributes to exclude from extras output
    _BUILTIN_ATTRS: frozenset[str] = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()) | {
        "message",
        "asctime",
        "levelname_colored",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        base = super().format(record)
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self._BUILTIN_ATTRS and not k.startswith("_")
        }
        if extras:
            pairs = " ".join(f"{k}={v}" for k, v in extras.items())
            return f"{base} | {pairs}"
        return base


# ---------------------------------------------------------------------------
# Setup (idempotent)
# ---------------------------------------------------------------------------
_initialised: bool = False


def _ensure_log_dir() -> None:
    """Create the logs directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(level: str | int = DEFAULT_LEVEL) -> None:
    """Configure the root ``visiontrace`` logger.

    This is idempotent — calling it multiple times is safe and has no
    additional effect after the first call.

    Args:
        level: Minimum log level (name or int). Defaults to ``INFO``.
    """
    global _initialised  # noqa: PLW0603
    if _initialised:
        return

    _ensure_log_dir()

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.setLevel(level)
    root.propagate = False

    # ── Console handler ──────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(_ColoredFormatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(console)

    # ── Rotating file handler (all levels) ───────────────────────────
    file_handler = RotatingFileHandler(
        filename=str(LOG_FILE),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_StructuredFileFormatter(FILE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(file_handler)

    # ── Rotating error-only file handler ─────────────────────────────
    error_handler = RotatingFileHandler(
        filename=str(ERROR_LOG_FILE),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(_StructuredFileFormatter(FILE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(error_handler)

    _initialised = True
    root.debug("Logging system initialised (level=%s)", logging.getLevelName(level))


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``visiontrace`` namespace.

    Automatically calls :func:`setup_logging` on first use so callers
    never need to worry about initialisation order.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    setup_logging()

    # Nest under root namespace: "app.core.engine" → "visiontrace.app.core.engine"
    if name.startswith(ROOT_LOGGER_NAME):
        qualified = name
    else:
        qualified = f"{ROOT_LOGGER_NAME}.{name}"

    return logging.getLogger(qualified)
