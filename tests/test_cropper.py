"""
Integration tests for VisionTraceAI Cropper service.

Run with:
    pytest tests/test_cropper.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.models.tracking import BoundingBox, TrackResult
from app.pipelines.cropper import PersonCropPipeline


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "crops"


@pytest.fixture
def cropper(temp_output_dir: Path) -> PersonCropPipeline:
    return PersonCropPipeline(output_dir=temp_output_dir, blur_threshold=10.0)


class TestCropperOperations:
    """Test the PersonCropPipeline logic."""

    def test_valid_crop(self, cropper: PersonCropPipeline, temp_output_dir: Path) -> None:
        # Create a sharp random image (high variance)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        track = TrackResult(
            track_id=1,
            confidence=0.95,
            bbox=BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=300.0)
        )
        
        meta = cropper.process_track(frame, track, camera_id="test_cam", frame_number=5, timestamp=0.5)
        
        assert meta is not None
        assert meta.track_id == 1
        assert meta.camera_id == "test_cam"
        
        # Verify saved crop
        crop_path = Path(meta.crop_path)
        assert crop_path.exists()
        
        saved_img = cv2.imread(str(crop_path))
        assert saved_img is not None
        assert saved_img.shape == (224, 224, 3)  # TARGET_SIZE
        
        # Verify metadata JSON
        meta_json_path = temp_output_dir / "test_cam" / "track_1" / "crop_metadata.json"
        assert meta_json_path.exists()
        
        with open(meta_json_path, "r") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["camera_id"] == "test_cam"

    def test_reject_zero_size(self, cropper: PersonCropPipeline) -> None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Bbox with 0 width/height
        track = TrackResult(
            track_id=2,
            confidence=0.9,
            bbox=BoundingBox(x1=100.0, y1=100.0, x2=100.0, y2=100.0)
        )
        
        meta = cropper.process_track(frame, track, camera_id="cam_2", frame_number=1, timestamp=0.1)
        
        assert meta is None
        assert cropper.rejected_invalid_coords == 1  # Fails invalid_coords because x2 <= x1

    def test_reject_out_of_bounds(self, cropper: PersonCropPipeline) -> None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Completely outside frame
        track = TrackResult(
            track_id=3,
            confidence=0.9,
            bbox=BoundingBox(x1=700.0, y1=500.0, x2=800.0, y2=600.0)
        )
        
        meta = cropper.process_track(frame, track, camera_id="cam_3", frame_number=1, timestamp=0.1)
        
        assert meta is None
        assert cropper.rejected_invalid_coords == 1

    def test_reject_blurry(self, cropper: PersonCropPipeline) -> None:
        # Create a completely blank (uniform) image. Variance = 0
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        track = TrackResult(
            track_id=4,
            confidence=0.9,
            bbox=BoundingBox(x1=100.0, y1=100.0, x2=200.0, y2=300.0)
        )
        
        meta = cropper.process_track(frame, track, camera_id="cam_4", frame_number=1, timestamp=0.1)
        
        assert meta is None
        assert cropper.rejected_blur == 1
