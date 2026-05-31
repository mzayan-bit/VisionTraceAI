#!/usr/bin/env python3
"""
Smoke-test for VisionTraceAI logging system.

Run from project root:
    uv run python scripts/test_logging.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.logger import LOG_DIR, LOG_FILE, ERROR_LOG_FILE, get_logger  # noqa: E402


def main() -> int:
    print("=" * 60)
    print("  VisionTraceAI — Logging Smoke Test")
    print("=" * 60)

    logger = get_logger("scripts.test_logging")

    # Emit at every level
    logger.debug("Debug message — verbose diagnostics")
    logger.info("Info message — normal operation", extra={"component": "smoke_test"})
    logger.warning("Warning message — something to watch", extra={"threshold": 0.85})
    logger.error("Error message — something failed", extra={"error_code": 5001})
    logger.critical("Critical message — system-level failure")

    print()

    # Verify
    checks: list[tuple[str, bool]] = [
        ("logs/ directory exists", LOG_DIR.is_dir()),
        ("visiontrace.log exists", LOG_FILE.is_file()),
        ("visiontrace.error.log exists", ERROR_LOG_FILE.is_file()),
        ("visiontrace.log is non-empty", LOG_FILE.stat().st_size > 0),
        ("visiontrace.error.log is non-empty", ERROR_LOG_FILE.stat().st_size > 0),
    ]

    # Check file contents
    log_content = LOG_FILE.read_text()
    error_content = ERROR_LOG_FILE.read_text()

    checks.extend([
        ("main log contains INFO", "INFO" in log_content),
        ("main log contains WARNING", "WARN" in log_content or "WARNING" in log_content),
        ("main log contains ERROR", "ERROR" in log_content),
        ("main log contains CRITICAL", "CRITICAL" in log_content or "CRIT" in log_content),
        ("main log has structured extras", "component=smoke_test" in log_content),
        ("error log contains ERROR", "ERROR" in error_content),
        ("error log contains CRITICAL", "CRITICAL" in error_content or "CRIT" in error_content),
        ("error log does NOT contain INFO", "| INFO" not in error_content),
    ])

    passed = failed = 0
    for label, result in checks:
        icon = "✅" if result else "❌"
        print(f"  {icon}  {label}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n  Results: {passed} passed, {failed} failed, {passed + failed} total")

    # Show file contents
    print("\n" + "─" * 60)
    print("  📄 visiontrace.log (last 10 lines):")
    print("─" * 60)
    for line in log_content.strip().splitlines()[-10:]:
        print(f"    {line}")

    print("\n" + "─" * 60)
    print("  📄 visiontrace.error.log:")
    print("─" * 60)
    for line in error_content.strip().splitlines()[-10:]:
        print(f"    {line}")

    print("\n" + "=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
