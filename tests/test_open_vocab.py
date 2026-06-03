import pytest
import numpy as np
from PIL import Image

from backend.open_vocab.open_vocab import OpenVocabDetector, OpenVocabDetectorError

def test_open_vocab_init():
    detector = OpenVocabDetector(device="cpu")
    assert detector.model_id == "IDEA-Research/grounding-dino-tiny"
    assert str(detector.device) == "cpu"

def test_detect_without_loading_model_raises_error():
    detector = OpenVocabDetector()
    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    with pytest.raises(OpenVocabDetectorError, match="Model not loaded"):
        detector.detect(dummy_image, "car")

def test_detect_with_mock_model():
    detector = OpenVocabDetector()
    detector.load_model(mock_for_testing=True)
    
    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
    prompts = ["red fire extinguisher", "chair", "laptop"]
    
    # Run inference
    detections = detector.detect(dummy_image, prompts, box_threshold=0.3)
    
    # We expect 4 mock words from the split: "red", "fire", "extinguisher", "chair", "laptop"
    # Wait, the prompt becomes "red fire extinguisher . chair . laptop ."
    # Then split() -> ["red", "fire", "extinguisher", "chair", "laptop"]
    # Their confidences are 0.9, 0.8, 0.7, 0.6, 0.5
    assert len(detections) == 5
    
    # Check that extracting works and confidences are populated
    labels = [d["label"] for d in detections]
    assert "red" in labels
    assert "laptop" in labels
    
    for d in detections:
        assert "confidence" in d
        assert "bbox" in d
        bbox = d["bbox"]
        assert "x1" in bbox and "y1" in bbox and "x2" in bbox and "y2" in bbox

def test_detect_confidence_filtering():
    detector = OpenVocabDetector()
    detector.load_model(mock_for_testing=True)
    
    dummy_image = Image.new("RGB", (200, 200))
    # mock yields confidences 0.9, 0.8, 0.7
    prompts = ["a", "b", "c"]
    
    # High threshold should filter out "c"
    detections = detector.detect(dummy_image, prompts, box_threshold=0.75)
    
    assert len(detections) == 2
    labels = [d["label"] for d in detections]
    assert "a" in labels
    assert "b" in labels
    assert "c" not in labels
