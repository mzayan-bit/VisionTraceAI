"""
VisionTraceAI — Production Tracking Engine.

Uses YOLO11 and ByteTrack for persistent multi-object tracking.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import cv2
from ultralytics import YOLO

from app.config.settings import get_settings
from app.models.tracking import BoundingBox, FrameResult, TrackResult, VideoResult
from app.utils.logger import get_logger
from backend.storage.redis_client import RedisClient

logger = get_logger(__name__)


class VisionTracker:
    """YOLO11 + ByteTrack powered tracking engine."""

    def __init__(self, trajectory_store=None, camera_id: str = "camera_1", kafka_producer=None) -> None:
        self.settings = get_settings()
        self.model: YOLO | None = None
        self.device = self.settings.device
        self.model_path = self.settings.yolo_model
        
        self.trajectory_store = trajectory_store
        self.kafka_producer = kafka_producer
        self.camera_id = camera_id
        
        self.redis_client = RedisClient()
        if not self.redis_client.is_connected:
            try:
                self.redis_client.connect()
            except Exception:
                pass
                
        self.last_metric_check = 0.0
        self.system_fps = 30.0
        self.system_latency = 0.0
        self.scale_cooldown_until = 0.0

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

    def track_frame(self, frame: np.ndarray, frame_number: int, timestamp: float, imgsz: int = 640) -> tuple[FrameResult, np.ndarray]:
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
            device=self.device,
            imgsz=imgsz,
            conf=0.10,
            iou=0.45
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
                
                bbox_dict = {
                    "x1": bbox_obj.x1,
                    "y1": bbox_obj.y1,
                    "x2": bbox_obj.x2,
                    "y2": bbox_obj.y2,
                }
                
                # Write to Redis if a store was provided
                if self.trajectory_store is not None:
                    try:
                        self.trajectory_store.save_track(
                            track_id=int(track_id),
                            camera_id=self.camera_id,
                            timestamp=timestamp,
                            bbox=bbox_dict,
                        )
                    except Exception as exc:
                        logger.error("Failed to write track to Redis", extra={"track_id": track_id, "error": str(exc)})
                
                # Publish to Kafka if a producer was provided
                if self.kafka_producer is not None:
                    try:
                        self.kafka_producer.publish_track_event(
                            frame_id=frame_number,
                            track_id=int(track_id),
                            bbox=bbox_dict,
                            camera_id=self.camera_id,
                            timestamp=timestamp,
                            confidence=float(conf),
                            frame=frame,
                        )
                    except Exception as exc:
                        logger.error("Failed to publish track to Kafka", extra={"track_id": track_id, "error": str(exc)})
                
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
                    
                # Auto-scaling logic check
                now = time.time()
                if now - self.last_metric_check > 1.0:
                    self.last_metric_check = now
                    if self.redis_client.is_connected:
                        try:
                            fps_str = self.redis_client.get("metrics:system_fps")
                            if fps_str:
                                self.system_fps = float(fps_str)
                            lat_str = self.redis_client.get("metrics:pipeline_latency")
                            if lat_str:
                                self.system_latency = float(lat_str)
                        except Exception:
                            pass

                # If FPS < 20, skip odd frames
                if self.system_fps < 20.0 and now > self.scale_cooldown_until:
                    if frame_number % 2 != 0:
                        frame_number += 1
                        continue

                # If latency > 300, use lower resolution
                current_imgsz = 640
                if self.system_latency > 300.0 and now > self.scale_cooldown_until:
                    current_imgsz = 320
                    
                timestamp = frame_number / fps if fps > 0 else 0.0
                
                frame_res, annotated_frame = self.track_frame(frame, frame_number, timestamp, imgsz=current_imgsz)
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
        # Flush any pending Kafka messages before shutting down
        if self.kafka_producer is not None:
            try:
                self.kafka_producer.flush(timeout=5.0)
            except Exception as exc:
                logger.error("Failed to flush Kafka producer on shutdown", extra={"error": str(exc)})
        self.model = None
        logger.info("VisionTracker shut down")
