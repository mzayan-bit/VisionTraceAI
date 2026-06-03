#!/usr/bin/env python3
"""
VisionTraceAI — Run Tracker Script.

Runs the YOLO11 + ByteTrack tracking engine on a video.

Usage:
    uv run python scripts/run_tracker.py <path_to_video>
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.tracker import VisionTracker
from app.utils.logger import get_logger

logger = get_logger("scripts.run_tracker")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VisionTraceAI tracking engine on a video")
    parser.add_argument("video_path", type=str, help="Path to input video file")
    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        logger.error(f"Input video not found: {video_path}")
        return 1

    # Define outputs
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    annotated_video_path = output_dir / f"annotated_{video_path.name}"
    json_output_path = output_dir / f"tracking_{video_path.stem}.json"

    logger.info("Starting tracking script", extra={
        "input": str(video_path),
        "output_video": str(annotated_video_path),
        "output_json": str(json_output_path)
    })

    from backend.storage.trajectory_store import TrajectoryStore
    
    store = TrajectoryStore()
    store.connect()
    
    # Example hardcoded camera id for the script
    camera_id = "test_camera_1"
    
    tracker = VisionTracker(trajectory_store=store, camera_id=camera_id)
    try:
        tracker.initialize_model()
        result = tracker.track_video(video_path, annotated_video_path)
        
        # Save JSON
        with open(json_output_path, "w") as f:
            f.write(result.model_dump_json(indent=2))
            
        logger.info("Tracking results saved to JSON", extra={"json_path": str(json_output_path)})
        
    except Exception as exc:
        logger.error("Tracking failed", extra={"error": str(exc)})
        return 1
    finally:
        tracker.shutdown()
        store.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
