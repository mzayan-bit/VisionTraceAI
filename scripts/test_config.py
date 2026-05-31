#!/usr/bin/env python3
"""
Quick smoke-test for VisionTraceAI configuration loading.

Run from project root:
    python scripts/test_config.py
    # or
    uv run scripts/test_config.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import Settings, get_settings  # noqa: E402


def main() -> int:
    """Load settings, print summary, and run basic assertions."""
    print("=" * 60)
    print("  VisionTraceAI — Configuration Smoke Test")
    print("=" * 60)

    # 1. Load settings
    settings = get_settings()
    settings.print_summary()

    # 2. Run assertions
    checks: list[tuple[str, bool]] = [
        ("project_name is non-empty", bool(settings.project_name)),
        ("qdrant_host is non-empty", bool(settings.qdrant_host)),
        ("qdrant_port in valid range", 1 <= settings.qdrant_port <= 65535),
        ("device is valid", settings.device in {"cpu", "cuda", "mps"}),
        ("yolo_model is non-empty", bool(settings.yolo_model)),
        ("siglip_model is non-empty", bool(settings.siglip_model)),
        ("qdrant_url starts with http", settings.qdrant_url.startswith("http")),
        ("singleton returns same instance", get_settings() is settings),
    ]

    passed = 0
    failed = 0
    for label, result in checks:
        icon = "✅" if result else "❌"
        print(f"  {icon}  {label}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
