"""
VisionTraceAI — Crop Extraction Pipeline.

Extracts, validates, resizes, and saves individual tracking crops
for downstream processing (e.g., SigLIP embeddings).
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from typing import Any

from app.models.tracking import CropMetadata, TrackResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PersonCropPipeline:
    """Extracts, validates, and saves person crops from tracked frames."""

    TARGET_SIZE = (224, 224)

    def __init__(self, output_dir: str | Path = "data/crops", blur_threshold: float = 100.0) -> None:
        """
        Args:
            output_dir: Base directory to save crops.
            blur_threshold: Minimum Laplacian variance. Lower means more blur tolerated.
        """
        self.output_dir = Path(output_dir)
        self.blur_threshold = blur_threshold
        
        # Statistics
        self.total_processed = 0
        self.saved_crops = 0
        self.rejected_zero_size = 0
        self.rejected_invalid_coords = 0
        self.rejected_blur = 0

    def is_valid_bbox(self, bbox: Any, frame_shape: tuple[int, ...]) -> bool:
        """Validate bounding box coordinates against frame dimensions."""
        h, w = frame_shape[:2]
        
        if bbox.x2 <= bbox.x1 or bbox.y2 <= bbox.y1:
            return False
            
        if bbox.x1 >= w or bbox.y1 >= h or bbox.x2 <= 0 or bbox.y2 <= 0:
            return False
                
        return True

    def calculate_blur(self, image: np.ndarray) -> float:
        """Calculate the blur metric using Laplacian variance."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def process_track(
        self,
        frame: np.ndarray,
        track: TrackResult,
        camera_id: str,
        frame_number: int,
        timestamp: float
    ) -> CropMetadata | None:
        """Extract and save a crop for a single track."""
        self.total_processed += 1
        
        if not self.is_valid_bbox(track.bbox, frame.shape):
            self.rejected_invalid_coords += 1
            logger.debug("Rejected crop: invalid coordinates", extra={"track_id": track.track_id})
            return None

        # Clamp coordinates to frame
        h, w = frame.shape[:2]
        x1 = max(0, int(track.bbox.x1))
        y1 = max(0, int(track.bbox.y1))
        x2 = min(w, int(track.bbox.x2))
        y2 = min(h, int(track.bbox.y2))
        
        crop = frame[y1:y2, x1:x2]
        
        if crop.size == 0:
            self.rejected_zero_size += 1
            logger.debug("Rejected crop: zero size", extra={"track_id": track.track_id})
            return None
            
        # Blur detection
        variance = self.calculate_blur(crop)
        if variance < self.blur_threshold:
            self.rejected_blur += 1
            logger.debug("Rejected crop: too blurry", extra={"track_id": track.track_id, "variance": variance})
            return None
            
        # Resize to Target Size (224x224 RGB compatible layout)
        resized_crop = cv2.resize(crop, self.TARGET_SIZE)
        
        # Build path: data/crops/{camera_id}/track_{track_id}/
        track_dir = self.output_dir / camera_id / f"track_{track.track_id}"
        track_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"track_{track.track_id}_frame_{frame_number:05d}.jpg"
        crop_path = track_dir / filename
        
        # Save image
        cv2.imwrite(str(crop_path), resized_crop)
        
        # Create metadata
        metadata = CropMetadata(
            camera_id=camera_id,
            track_id=track.track_id,
            frame_number=frame_number,
            timestamp=timestamp,
            crop_path=str(crop_path),
            bbox=track.bbox
        )
        
        # Manage track-level crop_metadata.json
        track_meta_path = track_dir / "crop_metadata.json"
        
        track_data = []
        if track_meta_path.exists():
            try:
                with open(track_meta_path, "r") as f:
                    track_data = json.load(f)
            except json.JSONDecodeError:
                pass
                
        track_data.append(metadata.model_dump())
        with open(track_meta_path, "w") as f:
            json.dump(track_data, f, indent=2)
        
        self.saved_crops += 1
        return metadata

    def log_statistics(self) -> None:
        """Log pipeline statistics."""
        logger.info(
            "Crop Pipeline Statistics",
            extra={
                "total_processed": self.total_processed,
                "saved_crops": self.saved_crops,
                "rejected_zero_size": self.rejected_zero_size,
                "rejected_invalid_coords": self.rejected_invalid_coords,
                "rejected_blur": self.rejected_blur,
            }
        )
