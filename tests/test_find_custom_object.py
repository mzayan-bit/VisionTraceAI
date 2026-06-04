"""
Tests for the find_custom_object agent tool.
"""

from unittest.mock import ANY, MagicMock, patch
import numpy as np

import pytest

from backend.agent.tools.find_custom_object import find_custom_object

@pytest.fixture
def mock_detector():
    """Mock the OpenVocabDetector to avoid downloading transformer models."""
    with patch("backend.agent.tools.find_custom_object.get_detector") as mock_get:
        mock_instance = MagicMock()
        mock_get.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_cv2():
    """Mock OpenCV video capture to simulate video frame reading."""
    with patch("backend.agent.tools.find_custom_object.cv2") as mock_cv2_module:
        mock_cap = MagicMock()
        
        # Simulate video properties
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30.0  # 30 fps
        
        # We will simulate 2 valid frames to keep the test deterministic and fast
        def read_side_effect():
            read_side_effect.call_count += 1
            if read_side_effect.call_count <= 2:
                # Return a dummy BGR frame
                return True, np.zeros((480, 640, 3), dtype=np.uint8)
            return False, None
        read_side_effect.call_count = 0
        
        mock_cap.read.side_effect = read_side_effect
        mock_cv2_module.VideoCapture.return_value = mock_cap
        mock_cv2_module.COLOR_BGR2RGB = 4
        # Just pass through the frame for color conversion
        mock_cv2_module.cvtColor.side_effect = lambda f, code: f
        
        yield mock_cv2_module

def test_find_custom_object_tool(mock_detector, mock_cv2):
    """Test that the tool correctly extracts frames and processes prompts."""
    # Setup dummy detections returned by the mocked DINO
    mock_detector.detect.return_value = [
        {
            "label": "fire extinguisher",
            "confidence": 0.85,
            "bbox": {"x1": 10.0, "y1": 20.0, "x2": 100.0, "y2": 200.0}
        }
    ]

    prompts = [
        "fire extinguisher",
        "exit sign",
        "red bag on floor"
    ]
    
    for prompt in prompts:
        # Reset the frame reading state for each prompt execution
        mock_cv2.VideoCapture().read.side_effect.call_count = 0
        
        # LangChain tools use invoke
        results = find_custom_object.invoke({
            "video_path": "dummy_video.mp4",
            "prompt": prompt,
            "sample_rate": 1  # Process every frame for the test
        })
        
        # Since we simulate 2 frames, and sample rate is 1, we get 2 frames processed.
        # So we should get 2 detections.
        assert len(results) == 2
        
        # Verify first detection
        assert results[0]["label"] == "fire extinguisher"
        assert results[0]["frame_index"] == 0
        assert results[0]["timestamp_sec"] == 0.0
        assert "bbox" in results[0]
        
        # Verify second detection
        assert results[1]["frame_index"] == 1
        assert results[1]["timestamp_sec"] == 1.0 / 30.0
        
        # Verify the underlying detector was called correctly
        mock_detector.detect.assert_called_with(ANY, prompt, box_threshold=0.3)
