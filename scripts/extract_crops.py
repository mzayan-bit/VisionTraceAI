#!/usr/bin/env python3
"""
VisionTraceAI — Crop Extraction Script.

Runs the tracking engine and extracts person crops to data/crops/
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
from app.core.tracker import VisionTracker
from app.pipelines.cropper import PersonCropPipeline
from app.utils.logger import get_logger

logger = get_logger("scripts.extract_crops")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract person crops from video")
    parser.add_argument("video_path", type=str, help="Path to input video file")
    parser.add_argument("--camera-id", type=str, default="cam_1", help="Camera ID to simulate")
    parser.add_argument("--blur-threshold", type=float, default=50.0, help="Laplacian blur threshold")
    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        logger.error(f"Input video not found: {video_path}")
        return 1

    logger.info("Starting crop extraction", extra={"video": str(video_path)})

    tracker = VisionTracker()
    cropper = PersonCropPipeline(blur_threshold=args.blur_threshold)
    
    try:
        tracker.initialize_model()
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error("Could not open video")
            return 1
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            timestamp = frame_number / fps if fps > 0 else 0.0
            
            # 1. Track
            frame_res, _ = tracker.track_frame(frame, frame_number, timestamp)
            
            # 2. Extract crops
            for track in frame_res.tracks:
                cropper.process_track(
                    frame=frame,
                    track=track,
                    camera_id=args.camera_id,
                    frame_number=frame_number,
                    timestamp=timestamp
                )
                
            frame_number += 1
            if frame_number % 30 == 0:
                logger.debug(f"Processed {frame_number} frames")
                
    except Exception as exc:
        logger.error("Crop extraction failed", extra={"error": str(exc)})
        return 1
    finally:
        if 'cap' in locals():
            cap.release()
        tracker.shutdown()
        cropper.log_statistics()

    return 0

if __name__ == "__main__":
    sys.exit(main())
