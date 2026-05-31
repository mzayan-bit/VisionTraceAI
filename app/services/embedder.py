"""
VisionTraceAI — SigLIP Semantic Embedding Engine.

Provides normalized, 768-dimensional semantic embeddings for images
and text using the SigLIP vision-language model.
"""

from __future__ import annotations

import time
from typing import Any, List

import numpy as np
import torch
from PIL import Image
from transformers import AutoModel, AutoProcessor

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SigLIPEmbeddingService:
    """Production-grade SigLIP embedding engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = self.settings.siglip_model
        
        # Determine actual device fallback (mps/cuda/cpu)
        if self.settings.device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
            logger.warning("CUDA requested but not available. Falling back to CPU.")
        elif self.settings.device == "mps" and not torch.backends.mps.is_available():
            self.device = "cpu"
            logger.warning("MPS requested but not available. Falling back to CPU.")
        else:
            self.device = self.settings.device

        self.processor: Any | None = None
        self.model: Any | None = None

    def initialize(self) -> None:
        """Load the SigLIP processor and model into memory."""
        start_time = time.time()
        logger.info("Initializing SigLIP model", extra={"model": self.model_name, "device": self.device})
        
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            elapsed = time.time() - start_time
            logger.info("SigLIP model loaded successfully", extra={"load_time_sec": round(elapsed, 2)})
        except Exception as exc:
            logger.error("Failed to load SigLIP model", extra={"error": str(exc)})
            raise RuntimeError(f"SigLIP initialization failed: {exc}") from exc

    def _ensure_initialized(self) -> None:
        if self.model is None or self.processor is None:
            raise RuntimeError("SigLIP service is not initialized. Call initialize() first.")

    def normalize_embedding(self, vector: np.ndarray | torch.Tensor) -> np.ndarray:
        """L2 normalize an embedding vector to shape (..., 768) float32."""
        if isinstance(vector, torch.Tensor):
            vector = vector.detach().cpu().numpy()
            
        vector = np.array(vector, dtype=np.float32)
        
        # Handle 1D or 2D arrays
        if vector.ndim == 1:
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
        else:
            norm = np.linalg.norm(vector, axis=-1, keepdims=True)
            # Avoid division by zero
            norm[norm == 0] = 1.0
            vector = vector / norm
            
        return vector

    def encode_image(self, image: Image.Image | np.ndarray) -> np.ndarray:
        """Generate normalized embedding for a single image."""
        return self.encode_images([image])[0]

    def encode_images(self, images: List[Image.Image | np.ndarray]) -> np.ndarray:
        """Generate normalized embeddings for a batch of images."""
        self._ensure_initialized()
        start_time = time.time()
        
        # Convert numpy arrays to PIL images if needed
        pil_images = []
        for img in images:
            if isinstance(img, np.ndarray):
                # Ensure correct format (assume RGB)
                if img.dtype != np.uint8:
                    img = img.astype(np.uint8)
                pil_images.append(Image.fromarray(img))
            else:
                pil_images.append(img)
                
        try:
            with torch.no_grad():
                inputs = self.processor(images=pil_images, return_tensors="pt")
                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                features = self.model.get_image_features(**inputs)
                if hasattr(features, "pooler_output"):
                    features = features.pooler_output
                elif hasattr(features, "image_embeds"):
                    features = features.image_embeds
                
            embeddings = self.normalize_embedding(features)
            
            elapsed = time.time() - start_time
            logger.info(
                "Batch image embedding generated",
                extra={"batch_size": len(images), "latency_sec": round(elapsed, 3)}
            )
            return embeddings
            
        except Exception as exc:
            logger.error("Failed to encode images", extra={"error": str(exc)})
            raise RuntimeError(f"Image encoding failed: {exc}") from exc

    def encode_text(self, text: str) -> np.ndarray:
        """Generate normalized embedding for a single text query."""
        return self.encode_texts([text])[0]

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Generate normalized embeddings for a batch of text queries."""
        self._ensure_initialized()
        start_time = time.time()
        
        try:
            with torch.no_grad():
                inputs = self.processor(text=texts, padding="max_length", return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                features = self.model.get_text_features(**inputs)
                if hasattr(features, "pooler_output"):
                    features = features.pooler_output
                elif hasattr(features, "text_embeds"):
                    features = features.text_embeds
                
            embeddings = self.normalize_embedding(features)
            
            elapsed = time.time() - start_time
            logger.info(
                "Batch text embedding generated",
                extra={"batch_size": len(texts), "latency_sec": round(elapsed, 3)}
            )
            return embeddings
            
        except Exception as exc:
            logger.error("Failed to encode texts", extra={"error": str(exc)})
            raise RuntimeError(f"Text encoding failed: {exc}") from exc

    def health_check(self) -> dict[str, Any]:
        """Verify the service is running and model is loaded."""
        status = "healthy" if self.model is not None else "uninitialized"
        return {
            "status": status,
            "device": self.device,
            "model": self.model_name
        }

    def shutdown(self) -> None:
        """Release resources."""
        self.model = None
        self.processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            # torch.mps.empty_cache() is available in newer PyTorch versions
            if hasattr(torch, 'mps') and hasattr(torch.mps, 'empty_cache'):
                torch.mps.empty_cache()
        logger.info("SigLIP embedding service shut down")
