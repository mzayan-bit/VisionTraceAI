"""
Tests for tracking to Redis logger integration.

Verifies that VisionTracker successfully logs detected tracks to the TrajectoryStore.
"""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock

from app.core.tracker import VisionTracker
from backend.storage.trajectory_store import TrajectoryStore
from app.models.tracking import BoundingBox, FrameResult, TrackResult

class TestTrackingLogger:
    def test_vision_tracker_logs_to_redis(self) -> None:
        """Verify that VisionTracker calls save_track on the provided store."""
        
        # 1. Create a mock store
        mock_store = MagicMock(spec=TrajectoryStore)
        
        # 2. Initialize tracker with the mock store
        tracker = VisionTracker(trajectory_store=mock_store, camera_id="test_cam")
        
        # 3. We'll mock the internal YOLO model so we don't have to load actual weights
        #    and we can easily simulate a detection.
        tracker.model = MagicMock()
        
        # Mock the result structure returned by YOLO
        mock_result = MagicMock()
        # Create a mock for boxes
        mock_boxes = MagicMock()
        # Return numpy arrays for xyxy, id, conf
        mock_xyxy = MagicMock()
        mock_xyxy.cpu.return_value.numpy.return_value = np.array([[10, 20, 30, 40]])
        mock_boxes.xyxy = mock_xyxy
        
        mock_id = MagicMock()
        mock_id.int.return_value.cpu.return_value.numpy.return_value = np.array([42])
        mock_boxes.id = mock_id
        
        mock_conf = MagicMock()
        mock_conf.cpu.return_value.numpy.return_value = np.array([0.95])
        mock_boxes.conf = mock_conf
        
        mock_result.boxes = mock_boxes
        mock_result.plot.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # YOLO model.track returns a list of results
        tracker.model.track.return_value = [mock_result]
        
        # 4. Process a blank frame (the model is mocked anyway)
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_res, _ = tracker.track_frame(blank_frame, frame_number=1, timestamp=0.5)
        
        # 5. Assert frame_res contains the track
        assert len(frame_res.tracks) == 1
        assert frame_res.tracks[0].track_id == 42
        assert frame_res.tracks[0].confidence == 0.95
        
        # 6. Verify that save_track was called on the mock store
        mock_store.save_track.assert_called_once_with(
            track_id=42,
            camera_id="test_cam",
            timestamp=0.5,
            bbox={'x1': 10.0, 'y1': 20.0, 'x2': 30.0, 'y2': 40.0}
        )
