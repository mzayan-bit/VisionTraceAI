"""
VisionTraceAI — FastReID Engine.

Wrapper around the FastReID library for person re-identification.
Handles model initialization, image preprocessing, embedding extraction,
and vector normalization (L2). Automatically falls back to CPU if
CUDA/MPS is unavailable.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image

try:
    from fastreid.config import get_cfg
    from fastreid.modeling.meta_arch import build_model
    from fastreid.utils.checkpoint import Checkpointer
    HAS_FASTREID = True
except ImportError:
    HAS_FASTREID = False

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReIDEngineError(Exception):
    """Base exception for ReID engine failures."""


class ReIDEngine:
    """Person Re-Identification embedding extractor using FastReID.

    Attributes:
        config_path: Path to the FastReID YAML configuration file.
        weights_path: Path to the pre-trained PyTorch weights.
        device: Target computation device ('cpu', 'cuda', 'mps').
        model: The initialized PyTorch model.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        weights_path: str | Path | None = None,
        device: str | None = None,
    ) -> None:
        if not HAS_FASTREID:
            raise ReIDEngineError("fastreid package is not installed.")

        self.config_path = str(config_path) if config_path else ""
        self.weights_path = str(weights_path) if weights_path else ""
        
        # 1. Determine Device (GPU with CPU fallback)
        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.model: torch.nn.Module | None = None
        
        # 2. Setup standard image transforms for ReID
        self.transform = T.Compose([
            T.Resize((256, 128)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        logger.info(
            "ReIDEngine initialized",
            extra={"device": str(self.device), "config": self.config_path}
        )

    def load_model(self, mock_for_testing: bool = False) -> None:
        """Load the FastReID configuration and model weights.

        Args:
            mock_for_testing: If True, loads a dummy ResNet50 model instead
                of requiring a valid FastReID config and weights file.
        """
        if mock_for_testing:
            logger.info("Loading mock ReID model for testing")
            import torchvision.models as models
            self.model = models.resnet18(weights=None)
            self.model.fc = torch.nn.Identity()  # Output raw features (512-d)
            self.model.eval()
            self.model.to(self.device)
            return

        if not self.config_path:
            raise ReIDEngineError("config_path is required to load FastReID model.")

        try:
            logger.info("Loading FastReID configuration")
            cfg = get_cfg()
            cfg.merge_from_file(self.config_path)
            cfg.MODEL.BACKBONE.PRETRAIN = False
            cfg.MODEL.DEVICE = str(self.device)
            
            logger.info("Building FastReID model")
            self.model = build_model(cfg)
            self.model.eval()

            if self.weights_path and Path(self.weights_path).exists():
                logger.info(f"Loading weights from {self.weights_path}")
                Checkpointer(self.model).load(self.weights_path)
            else:
                logger.warning("No weights path provided or file not found; using initialized weights.")

            self.model.to(self.device)
            logger.info("FastReID model loaded successfully")

        except Exception as exc:
            logger.error("Failed to load ReID model", extra={"error": str(exc)})
            raise ReIDEngineError(f"Model loading failed: {exc}") from exc

    def extract_embedding(self, image: np.ndarray | Image.Image) -> np.ndarray:
        """Extract and normalize the appearance embedding for a given image.

        Args:
            image: A cropped person image as a NumPy array (H, W, C) in RGB
                   or a PIL Image.

        Returns:
            A 1D numpy array representing the normalized embedding vector.
        """
        if self.model is None:
            raise ReIDEngineError("Model not loaded. Call load_model() first.")

        # Ensure image is PIL format for torchvision transforms
        if isinstance(image, np.ndarray):
            # OpenCV provides BGR, ensure RGB conversion if needed before this,
            # but assume RGB inputs here.
            pil_image = Image.fromarray(image)
        elif isinstance(image, Image.Image):
            pil_image = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Preprocess
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)  # type: ignore

        # Forward pass
        with torch.no_grad():
            features = self.model(input_tensor)
            
            # FastReID might return a tuple during eval, or a raw tensor
            if isinstance(features, tuple) or isinstance(features, list):
                features = features[0]
                
            # L2 Normalization (critical for cosine similarity)
            norm_features = F.normalize(features, p=2, dim=1)
            
        embedding = norm_features.cpu().numpy().flatten()
        return embedding


def _run_smoke_test() -> None:
    """Standalone smoke test to generate embedding and print shape."""
    print("═" * 50)
    print("🔍 VisionTraceAI — FastReID Validation")
    print("═" * 50)
    
    try:
        engine = ReIDEngine()
        engine.load_model(mock_for_testing=True)
        
        # Create a dummy image (e.g., 256x128 RGB crop)
        dummy_image = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)
        
        embedding = engine.extract_embedding(dummy_image)
        
        print("✅ Model loaded successfully (Mock/ResNet18)")
        print(f"✅ Generated embedding of shape: {embedding.shape}")
        print(f"✅ Embedding vector (first 5 elements): {embedding[:5]}")
        print(f"✅ L2 Norm (should be ~1.0): {np.linalg.norm(embedding):.4f}")
        print("═" * 50)
        
    except Exception as exc:
        print(f"❌ ReID engine validation failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    _run_smoke_test()
