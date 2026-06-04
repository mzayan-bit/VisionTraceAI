"""
VisionTraceAI — Open Vocabulary Object Search Tool.

LangChain tool for finding custom objects in video streams using Grounding DINO.
"""

from typing import Any, Dict, List
import cv2
import numpy as np

from langchain_core.tools import tool
from backend.open_vocab.open_vocab import OpenVocabDetector

# Singleton instance
_detector: OpenVocabDetector | None = None

def get_detector() -> OpenVocabDetector:
    """Initialize and retrieve the OpenVocabDetector singleton."""
    global _detector
    if _detector is None:
        _detector = OpenVocabDetector()
        # In a real environment, this loads the model. We can mock it during testing.
        _detector.load_model(mock_for_testing=False)
    return _detector

@tool
def find_custom_object(video_path: str, prompt: str, sample_rate: int = 30) -> List[Dict[str, Any]]:
    """
    Search for a custom object in a video using open vocabulary detection (Grounding DINO).
    
    This performs frame sampling and inference to find specific text prompts in the visual data.
    
    Args:
        video_path: Path to the video file to analyze.
        prompt: Natural language text prompt to search for (e.g., 'fire extinguisher', 'exit sign', 'red bag on floor').
        sample_rate: Analyze every Nth frame (default 30).
        
    Returns:
        List of detections, each containing frame_index, timestamp_sec, confidence, and bbox locations.
    """
    detector = get_detector()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return [{"error": f"Could not open video {video_path}"}]
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
        
    results = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx % sample_rate == 0:
            # OpenCV loads frames as BGR, DINO expects RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Grounding DINO inference with confidence filtering built-in
            detections = detector.detect(rgb_frame, prompt, box_threshold=0.3)
            
            for det in detections:
                results.append({
                    "frame_index": frame_idx,
                    "timestamp_sec": float(frame_idx) / float(fps),
                    "label": det["label"],
                    "confidence": det["confidence"],
                    "bbox": det["bbox"]
                })
                
        frame_idx += 1
        
    cap.release()
    return results
