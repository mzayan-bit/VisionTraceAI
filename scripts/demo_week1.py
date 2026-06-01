#!/usr/bin/env python3
"""
VisionTraceAI — Week 1 MVP Demo.

Interactive menu-driven demo showcasing every capability of the Week 1 MVP.

Usage::

    uv run python scripts/demo_week1.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.search_engine import VisionSearchEngine
from app.utils.logger import get_logger

logger = get_logger("scripts.demo_week1")

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║           🔍 VisionTraceAI — Week 1 MVP Demo                ║
║                  Production MVP Showcase                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   1  Process Video        (Track + Crop + Embed + Store)     ║
║   2  Search Person        (Natural language query)           ║
║   3  Search Track         (By track ID)                      ║
║   4  Search Camera        (By camera ID)                     ║
║   5  Run Benchmarks       (Pipeline performance)             ║
║   6  Generate Report      (Week 1 final report)              ║
║   7  Exit                                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def _run_script(script: str, args: list[str] | None = None) -> None:
    """Run a project script via subprocess."""
    cmd = [sys.executable, f"scripts/{script}"]
    if args:
        cmd.extend(args)
    subprocess.run(cmd, cwd=str(Path(__file__).resolve().parents[1]))


def action_process_video() -> None:
    """Process a video through the full pipeline."""
    path = input("  Enter video path [data/videos/sample.mp4]: ").strip()
    if not path:
        path = "data/videos/sample.mp4"
    cam = input("  Enter camera ID [cam_1]: ").strip() or "cam_1"
    _run_script("index_video.py", [path, "--camera-id", cam])


def action_search_person(engine: VisionSearchEngine | None) -> VisionSearchEngine | None:
    """Search by natural language description."""
    if engine is None:
        print("  ⏳ Initializing search engine...")
        engine = VisionSearchEngine()
        engine.initialize()
        print("  ✅ Ready!\n")

    query = input("  Enter description: ").strip()
    if not query:
        print("  ⚠  No query provided.")
        return engine

    results = engine.search_person(query, limit=10)
    print(f"\n  📋 Results for: \"{query}\"\n")
    print(engine.format_results(results))
    print(f"\n  Total: {len(results)} match(es)")
    return engine


def action_search_track(engine: VisionSearchEngine | None) -> VisionSearchEngine | None:
    """Search by track ID."""
    if engine is None:
        print("  ⏳ Initializing search engine...")
        engine = VisionSearchEngine()
        engine.initialize()
        print("  ✅ Ready!\n")

    raw = input("  Enter track ID: ").strip()
    try:
        track_id = int(raw)
    except ValueError:
        print("  ⚠  Track ID must be an integer.")
        return engine

    results = engine.search_by_track(track_id)
    print(f"\n  📋 Results for Track {track_id}\n")
    print(engine.format_results(results))
    print(f"\n  Total: {len(results)} match(es)")
    return engine


def action_search_camera(engine: VisionSearchEngine | None) -> VisionSearchEngine | None:
    """Search by camera ID."""
    if engine is None:
        print("  ⏳ Initializing search engine...")
        engine = VisionSearchEngine()
        engine.initialize()
        print("  ✅ Ready!\n")

    camera_id = input("  Enter camera ID: ").strip()
    if not camera_id:
        print("  ⚠  No camera ID provided.")
        return engine

    results = engine.search_by_camera(camera_id)
    print(f"\n  📋 Results for Camera {camera_id}\n")
    print(engine.format_results(results))
    print(f"\n  Total: {len(results)} match(es)")
    return engine


def action_benchmarks() -> None:
    """Run the pipeline benchmark."""
    _run_script("benchmark_pipeline.py")


def action_report() -> None:
    """Generate the Week 1 report."""
    _run_script("generate_week1_report.py")


def main() -> int:
    engine: VisionSearchEngine | None = None

    while True:
        print(BANNER)
        choice = input("  Select option [1-7]: ").strip()

        if choice == "1":
            action_process_video()
        elif choice == "2":
            engine = action_search_person(engine)
        elif choice == "3":
            engine = action_search_track(engine)
        elif choice == "4":
            engine = action_search_camera(engine)
        elif choice == "5":
            action_benchmarks()
        elif choice == "6":
            action_report()
        elif choice == "7":
            if engine:
                engine.shutdown()
            print("  Goodbye!")
            break
        else:
            print("  ⚠  Invalid option. Choose 1-7.")

        input("\n  Press Enter to continue...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
