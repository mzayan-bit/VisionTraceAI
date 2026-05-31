"""
Integration tests for VisionTraceAI Tracker service.

Run with:
    pytest tests/test_tracker.py -v
"""

from __future__ import annotations

import numpy as np
import pytest

from app.core.tracker import VisionTracker
from app.models.tracking import BoundingBox, FrameResult, TrackResult


@pytest.fixture(scope="module")
def tracker() -> VisionTracker:
    """Return an initialized VisionTracker."""
    t = VisionTracker()
    t.initialize_model()
    yield t
    t.shutdown()


class TestTrackerInitialization:
    """Test model loading and initialization."""

    def test_initialization(self, tracker: VisionTracker) -> None:
        assert tracker.model is not None
        assert "yolo11n.pt" in str(tracker.model_path)

    def test_uninitialized_raises(self) -> None:
        t = VisionTracker()
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError, match="Model not initialized"):
            t.track_frame(dummy_frame, 0, 0.0)


class TestTrackingOperations:
    """Test tracking on mock frames."""

    def test_tracking_output_schema_and_bbox(self, tracker: VisionTracker) -> None:
        # Create a blank frame where YOLO will likely find nothing
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        res, ann = tracker.track_frame(blank_frame, frame_number=1, timestamp=0.5)
        
        # Schema validation
        assert isinstance(res, FrameResult)
        assert res.frame_number == 1
        assert res.timestamp == 0.5
        assert isinstance(res.tracks, list)
        assert isinstance(ann, np.ndarray)
        
        # Validation for bbox if anything is detected
        for track in res.tracks:
            assert isinstance(track, TrackResult)
            assert isinstance(track.track_id, int)
            assert isinstance(track.confidence, float)
            assert isinstance(track.bbox, BoundingBox)
            # bbox coordinates validation
            assert track.bbox.x2 >= track.bbox.x1
            assert track.bbox.y2 >= track.bbox.y1

