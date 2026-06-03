"""
VisionTraceAI — Production Tracking Engine.

Uses YOLO11 and ByteTrack for persistent multi-object tracking.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from ultralytics import YOLO

from app.config.settings import get_settings
from app.models.tracking import BoundingBox, FrameResult, TrackResult, VideoResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VisionTracker:
    """YOLO11 + ByteTrack powered tracking engine."""

    def __init__(self, trajectory_store=None, camera_id: str = "camera_1") -> None:
        self.settings = get_settings()
        self.model: YOLO | None = None
        self.device = self.settings.device
        self.model_path = self.settings.yolo_model
        
        self.trajectory_store = trajectory_store
        self.camera_id = camera_id

    def initialize_model(self) -> None:
        """Load the YOLO model."""
        logger.info("Loading YOLO model", extra={"model_path": self.model_path, "device": self.device})
        try:
            self.model = YOLO(self.model_path)
            # Attempt to send to configured device if ultralytics supports explicit to() for it
            # YOLO internally handles device, but we can set it
            self.model.to(self.device)
            logger.info("YOLO model loaded successfully")
        except Exception as exc:
            logger.error("Failed to load YOLO model", extra={"error": str(exc)})
            raise RuntimeError(f"Model initialization failed: {exc}") from exc

    def track_frame(self, frame: np.ndarray, frame_number: int, timestamp: float) -> tuple[FrameResult, np.ndarray]:
        """Track objects in a single frame.
        
        Returns:
            Tuple of FrameResult and the annotated frame.
        """
        if self.model is None:
            raise RuntimeError("Model not initialized. Call initialize_model() first.")

        # classes=0 (person only), tracker="bytetrack.yaml", persist=True
        results = self.model.track(
            frame,
            classes=[0],
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
            device=self.device
        )
        
        result = results[0]
        tracks = []
        
        if result.boxes is not None and result.boxes.id is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            track_ids = result.boxes.id.int().cpu().numpy()
            confidences = result.boxes.conf.cpu().numpy()
            
            for box, track_id, conf in zip(boxes, track_ids, confidences):
                bbox_obj = BoundingBox(
                    x1=float(box[0]),
                    y1=float(box[1]),
                    x2=float(box[2]),
                    y2=float(box[3])
                )
                
                # Create TrackResult
                track_res = TrackResult(
                    track_id=int(track_id),
                    confidence=float(conf),
                    bbox=bbox_obj
                )
                tracks.append(track_res)
                
                # Write to Redis if a store was provided
                if self.trajectory_store is not None:
                    try:
                        self.trajectory_store.save_track(
                            track_id=int(track_id),
                            camera_id=self.camera_id,
                            timestamp=timestamp,
                            bbox={
                                "x1": bbox_obj.x1,
                                "y1": bbox_obj.y1,
                                "x2": bbox_obj.x2,
                                "y2": bbox_obj.y2,
                            }
                        )
                    except Exception as exc:
                        logger.error("Failed to write track to Redis", extra={"track_id": track_id, "error": str(exc)})
                
        annotated_frame = result.plot()
        
        frame_result = FrameResult(
            frame_number=frame_number,
            timestamp=timestamp,
            tracks=tracks
        )
        
        return frame_result, annotated_frame

    def track_video(self, video_path: str | Path, output_path: str | Path | None = None) -> VideoResult:
        """Process a full video and optionally save the annotated output."""
        import cv2
        
        video_path = str(video_path)
        logger.info("Video tracking started", extra={"video": video_path})
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        out = None
        if output_path is not None:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
        frame_results = []
        frame_number = 0
        total_tracks = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                timestamp = frame_number / fps if fps > 0 else 0.0
                
                frame_res, annotated_frame = self.track_frame(frame, frame_number, timestamp)
                frame_results.append(frame_res)
                total_tracks += len(frame_res.tracks)
                
                if out is not None:
                    out.write(annotated_frame)
                    
                frame_number += 1
                
                if frame_number % 30 == 0:
                    logger.debug("Processed frames", extra={"frame": frame_number, "total": total_frames})
                    
        finally:
            cap.release()
            if out is not None:
                out.release()
                
        processing_time = time.time() - start_time
        process_fps = frame_number / processing_time if processing_time > 0 else 0.0
        
        logger.info(
            "Video completed",
            extra={
                "video": video_path,
                "frames": frame_number,
                "tracks_detected": total_tracks,
                "processing_time": round(processing_time, 2),
                "processing_speed_fps": round(process_fps, 2)
            }
        )
        
        return VideoResult(
            video_path=video_path,
            total_frames=frame_number,
            fps=fps,
            processing_time_sec=processing_time,
            frames=frame_results
        )

    def shutdown(self) -> None:
        """Clean up resources."""
        self.model = None
        logger.info("VisionTracker shut down")
