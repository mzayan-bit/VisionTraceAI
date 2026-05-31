"""
Unit tests for VisionTraceAI logging system.

Run with:
    pytest tests/test_logging.py -v
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from app.utils.logger import (
    LOG_DIR,
    LOG_FILE,
    ERROR_LOG_FILE,
    ROOT_LOGGER_NAME,
    _StructuredFileFormatter,
    get_logger,
    setup_logging,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_logging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect logs to a temp directory and reset state for each test."""
    import app.utils.logger as _mod

    # Reset initialisation flag
    monkeypatch.setattr(_mod, "_initialised", False)

    # Redirect log paths to temp
    monkeypatch.setattr(_mod, "LOG_DIR", tmp_path)
    monkeypatch.setattr(_mod, "LOG_FILE", tmp_path / "visiontrace.log")
    monkeypatch.setattr(_mod, "ERROR_LOG_FILE", tmp_path / "visiontrace.error.log")

    # Remove all handlers from root logger
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.handlers.clear()

    yield

    # Cleanup after test
    root.handlers.clear()


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

class TestGetLogger:
    """get_logger should return properly namespaced loggers."""

    def test_returns_logger(self) -> None:
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_namespaced_under_root(self) -> None:
        logger = get_logger("app.core.engine")
        assert logger.name == f"{ROOT_LOGGER_NAME}.app.core.engine"

    def test_does_not_double_prefix(self) -> None:
        logger = get_logger(f"{ROOT_LOGGER_NAME}.already.prefixed")
        assert logger.name == f"{ROOT_LOGGER_NAME}.already.prefixed"

    def test_auto_initialises(self) -> None:
        import app.utils.logger as _mod
        assert _mod._initialised is False
        get_logger("auto_init_test")
        assert _mod._initialised is True


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

class TestSetup:
    """setup_logging should be idempotent and create handlers."""

    def test_creates_handlers(self) -> None:
        setup_logging()
        root = logging.getLogger(ROOT_LOGGER_NAME)
        # Console + file + error_file = 3 handlers
        assert len(root.handlers) == 3

    def test_idempotent(self) -> None:
        setup_logging()
        setup_logging()
        setup_logging()
        root = logging.getLogger(ROOT_LOGGER_NAME)
        assert len(root.handlers) == 3  # still only 3

    def test_accepts_string_level(self) -> None:
        setup_logging("DEBUG")
        root = logging.getLogger(ROOT_LOGGER_NAME)
        assert root.level == logging.DEBUG

    def test_accepts_int_level(self) -> None:
        setup_logging(logging.WARNING)
        root = logging.getLogger(ROOT_LOGGER_NAME)
        assert root.level == logging.WARNING


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------

class TestFileOutput:
    """Log messages should be written to rotating log files."""

    def test_log_file_created(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        logger = get_logger("test.file")
        logger.info("test message")
        # Flush handlers
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        assert _mod.LOG_FILE.exists()

    def test_log_file_contains_message(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        logger = get_logger("test.content")
        logger.info("hello_marker_12345")
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        content = _mod.LOG_FILE.read_text()
        assert "hello_marker_12345" in content

    def test_error_log_captures_errors(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        logger = get_logger("test.errors")
        logger.error("error_marker_67890")
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        content = _mod.ERROR_LOG_FILE.read_text()
        assert "error_marker_67890" in content

    def test_error_log_excludes_info(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        logger = get_logger("test.filter")
        logger.info("info_only_marker")
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        if _mod.ERROR_LOG_FILE.exists():
            content = _mod.ERROR_LOG_FILE.read_text()
            assert "info_only_marker" not in content


# ---------------------------------------------------------------------------
# Structured formatting
# ---------------------------------------------------------------------------

class TestStructuredFormat:
    """Structured formatter should append extra fields as key=value pairs."""

    def test_extras_appended(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        logger = get_logger("test.extras")
        logger.info("processing", extra={"pipeline": "detect", "fps": 30})
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        content = _mod.LOG_FILE.read_text()
        assert "pipeline=detect" in content
        assert "fps=30" in content

    def test_no_extras_no_pipe(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        logger = get_logger("test.no_extras")
        logger.info("plain_message_no_extras")
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        content = _mod.LOG_FILE.read_text()
        # The line should not end with an extra " | " after the message
        for line in content.splitlines():
            if "plain_message_no_extras" in line:
                assert not line.rstrip().endswith("|")
                break

    def test_formatter_class_directly(self) -> None:
        formatter = _StructuredFileFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.custom_key = "custom_val"  # type: ignore[attr-defined]
        output = formatter.format(record)
        assert "custom_key=custom_val" in output


# ---------------------------------------------------------------------------
# Log directory
# ---------------------------------------------------------------------------

class TestLogDirectory:
    """The logs/ directory should be created automatically."""

    def test_log_dir_created(self, tmp_path: Path) -> None:
        import app.utils.logger as _mod
        import shutil

        target = tmp_path / "nested" / "logs"
        _mod.LOG_DIR = target
        _mod.LOG_FILE = target / "visiontrace.log"
        _mod.ERROR_LOG_FILE = target / "visiontrace.error.log"
        _mod._initialised = False

        root = logging.getLogger(ROOT_LOGGER_NAME)
        root.handlers.clear()

        setup_logging()
        assert target.is_dir()
