#!/usr/bin/env python3
"""
VisionTraceAI — Video Indexing Script.

Runs the complete Semantic Memory Pipeline:
1. Tracks individuals in a video.
2. Extracts their crops.
3. Generates SigLIP embeddings.
4. Stores everything into Qdrant.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2

from app.core.tracker import VisionTracker
from app.pipelines.cropper import PersonCropPipeline
from app.pipelines.vector_pipeline import SemanticMemoryPipeline
from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService
from app.utils.logger import get_logger

logger = get_logger("scripts.index_video")


def main() -> int:
    parser = argparse.ArgumentParser(description="Index video crops into semantic memory")
    parser.add_argument("video_path", type=str, help="Path to input video file")
    parser.add_argument("--camera-id", type=str, default="cam_1", help="Camera ID")
    parser.add_argument("--blur-threshold", type=float, default=50.0, help="Blur threshold")
    parser.add_argument("--batch-size", type=int, default=16, help="Vector insertion batch size")
    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        logger.error(f"Input video not found: {video_path}")
        return 1

    print("=" * 60)
    print(f"  🎬 VisionTraceAI — Semantic Indexing: {video_path.name}")
    print("=" * 60)

    # Initialize services
    tracker = VisionTracker()
    cropper = PersonCropPipeline(blur_threshold=args.blur_threshold)
    qdrant = QdrantService()
    embedder = SigLIPEmbeddingService()
    
    try:
        print("\n  [1/4] Initializing Models...")
        tracker.initialize_model()
        
        # Connect locally if docker is running, else use memory for testing
        try:
            qdrant.connect()
            qdrant.health_check()
        except Exception:
            logger.warning("Local Qdrant not available, falling back to memory storage")
            qdrant.connect_memory()
            
        qdrant.create_collection()
        embedder.initialize()
        
        pipeline = SemanticMemoryPipeline(qdrant=qdrant, embedder=embedder)
        
        print("\n  [2/4] Processing Video Frames...")
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = 0
        total_crops = 0
        
        pending_crops = []
        
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            timestamp = frame_number / fps if fps > 0 else 0.0
            
            # Track
            frame_res, _ = tracker.track_frame(frame, frame_number, timestamp)
            
            # Extract crops
            for track in frame_res.tracks:
                meta = cropper.process_track(
                    frame=frame,
                    track=track,
                    camera_id=args.camera_id,
                    frame_number=frame_number,
                    timestamp=timestamp
                )
                if meta:
                    pending_crops.append(meta)
                    total_crops += 1
            
            # Batch ingest
            if len(pending_crops) >= args.batch_size:
                pipeline.ingest_crops_batch(pending_crops)
                pending_crops.clear()
                
            frame_number += 1
            if frame_number % 30 == 0:
                print(f"        Processed {frame_number} frames...", end="\r")
                
        # Ingest remaining
        if pending_crops:
            pipeline.ingest_crops_batch(pending_crops)
            
        total_time = time.time() - start_time
        
        print("\n  [3/4] Vector Storage Complete")
        
        stats = qdrant.get_collection_stats()
        vector_count = stats.get("vectors_count", 0) or stats.get("points_count", 0)
        
        print("\n  [4/4] Indexing Summary:")
        print(f"        Frames Processed : {frame_number}")
        print(f"        Total Crops Found: {total_crops}")
        print(f"        Vectors Stored   : {vector_count}")
        print(f"        Processing Time  : {total_time:.2f}s")
        print("=" * 60)
        
    except Exception as exc:
        logger.error("Indexing failed", extra={"error": str(exc)})
        return 1
    finally:
        if 'cap' in locals():
            cap.release()
        tracker.shutdown()
        embedder.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
