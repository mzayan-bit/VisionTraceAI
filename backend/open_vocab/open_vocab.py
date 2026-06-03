"""
VisionTraceAI — Open Vocabulary Detection.

Uses Grounding DINO via Hugging Face Transformers for zero-shot text-prompted 
object detection in video frames.
"""

from __future__ import annotations

import logging
from typing import Any, List, Dict, Union

import numpy as np
import torch
from PIL import Image

try:
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenVocabDetectorError(Exception):
    """Base exception for open vocabulary detector failures."""


class OpenVocabDetector:
    """Zero-shot object detection using Grounding DINO.
    
    Attributes:
        model_id: HuggingFace model hub ID.
        device: Computation device.
    """
    
    def __init__(
        self, 
        model_id: str = "IDEA-Research/grounding-dino-tiny",
        device: str | None = None
    ) -> None:
        if not HAS_TRANSFORMERS:
            raise OpenVocabDetectorError("transformers package is not installed.")
            
        self.model_id = model_id
        
        # Determine Device
        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
            
        self.processor = None
        self.model = None
        
        logger.info(
            "OpenVocabDetector initialized",
            extra={"model_id": self.model_id, "device": str(self.device)}
        )

    def load_model(self, mock_for_testing: bool = False) -> None:
        """Load the Grounding DINO model and processor."""
        if mock_for_testing:
            logger.info("Loading mock OpenVocab model for testing")
            self.processor = "mock_processor"
            self.model = "mock_model"
            return
            
        logger.info(f"Loading Grounding DINO model: {self.model_id}")
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            self.model = AutoModelForZeroShotObjectDetection.from_pretrained(self.model_id).to(self.device)
            self.model.eval()
            logger.info("Grounding DINO model loaded successfully")
        except Exception as exc:
            logger.error("Failed to load Grounding DINO", extra={"error": str(exc)})
            raise OpenVocabDetectorError(f"Model loading failed: {exc}") from exc

    def detect(
        self, 
        image: Union[np.ndarray, Image.Image], 
        prompts: Union[str, List[str]], 
        box_threshold: float = 0.3,
        text_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Perform open vocabulary detection based on text prompts.
        
        Args:
            image: Image as a numpy array or PIL Image.
            prompts: A single string or list of strings to detect.
            box_threshold: Confidence threshold for bounding boxes.
            text_threshold: Confidence threshold for text alignment.
            
        Returns:
            List of detected objects with label, confidence, and bbox coordinates.
        """
        if self.model is None or self.processor is None:
            raise OpenVocabDetectorError("Model not loaded. Call load_model() first.")
            
        # Convert image to PIL if it's a numpy array
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        elif isinstance(image, Image.Image):
            pil_image = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
            
        # Format text prompts. Grounding DINO expects lowercase phrases separated by periods.
        if isinstance(prompts, list):
            text_prompt = " . ".join(prompts).lower() + " ."
        else:
            text_prompt = prompts.lower()
            if not text_prompt.endswith("."):
                text_prompt += " ."
                
        # Handle mock inference for testing
        if self.model == "mock_model":
            return self._mock_inference(pil_image, text_prompt, box_threshold)

        # Preprocess inputs
        inputs = self.processor(images=pil_image, text=text_prompt, return_tensors="pt").to(self.device)
        
        # Forward pass (frame inference)
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Bbox extraction
        width, height = pil_image.size
        target_sizes = [torch.tensor([height, width])]
        
        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            target_sizes=target_sizes
        )[0]
        
        # Confidence filtering and formatting
        detections = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            confidence = score.item()
            if confidence >= box_threshold:
                detections.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": {
                        "x1": float(box[0].item()),
                        "y1": float(box[1].item()),
                        "x2": float(box[2].item()),
                        "y2": float(box[3].item())
                    }
                })
                
        return detections

    def _mock_inference(self, image: Image.Image, text_prompt: str, threshold: float) -> List[Dict[str, Any]]:
        """Return dummy detections for unit tests."""
        # Simple mock matching
        detections = []
        words = text_prompt.replace(".", "").split()
        for i, word in enumerate(words):
            detections.append({
                "label": word,
                "confidence": 0.9 - (i * 0.1),  # mock confidence
                "bbox": {
                    "x1": 10.0 + i * 10,
                    "y1": 20.0 + i * 10,
                    "x2": 100.0 + i * 10,
                    "y2": 200.0 + i * 10
                }
            })
        # Filter by threshold
        return [d for d in detections if d["confidence"] >= threshold]


def _run_smoke_test() -> None:
    """Standalone validation for Open Vocab Detector."""
    print("═" * 50)
    print("🔍 VisionTraceAI — OpenVocab Validation")
    print("═" * 50)
    
    try:
        detector = OpenVocabDetector()
        detector.load_model(mock_for_testing=True)
        
        # Create a dummy image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Prompts to verify
        prompts = ["red fire extinguisher", "chair", "laptop"]
        print(f"Testing prompts: {prompts}")
        
        detections = detector.detect(dummy_image, prompts, box_threshold=0.3)
        
        print(f"✅ Extracted {len(detections)} bounding boxes.")
        for d in detections:
            bbox = d['bbox']
            print(f"  - [{d['label']}] (conf: {d['confidence']:.2f}) -> bbox: {bbox['x1']:.1f}, {bbox['y1']:.1f}, {bbox['x2']:.1f}, {bbox['y2']:.1f}")
            
        print("═" * 50)
        
    except Exception as exc:
        print(f"❌ OpenVocab validation failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    _run_smoke_test()
