"""
VisionTraceAI — Feature Engine.

Generates dense semantic embeddings and zero-shot attribute classifications
(e.g., clothing color) from cropped images of tracked people.
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from PIL import Image
from transformers import AutoModel, AutoProcessor

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FeatureEngine:
    """Extracts embeddings and attributes using SigLIP."""

    def __init__(self, model_name: str = "google/siglip-base-patch16-224"):
        self.settings = get_settings()
        self.model_name = model_name
        
        # Determine device
        if self.settings.device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
        elif self.settings.device == "mps" and not torch.backends.mps.is_available():
            self.device = "cpu"
        else:
            self.device = self.settings.device

        self.processor = None
        self.model = None

        # Predefined prompts for zero-shot color classification
        self.color_prompts = [
            "person wearing red",
            "person wearing blue",
            "person wearing white",
            "person wearing black",
            "person wearing green",
            "person wearing yellow",
            "person wearing gray",
            "person wearing pink",
            "person wearing purple",
            "person wearing brown"
        ]
        
        # We extract just the color name for the final output
        self.color_names = [prompt.split(" ")[-1] for prompt in self.color_prompts]
        self.text_embeddings = None

    def initialize(self) -> None:
        """Loads model and precomputes text embeddings."""
        logger.info("Initializing FeatureEngine", extra={"model": self.model_name, "device": self.device})
        try:
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Precompute text embeddings for colors
            with torch.no_grad():
                inputs = self.processor(text=self.color_prompts, padding="max_length", return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                features = self.model.get_text_features(**inputs)
                if hasattr(features, "pooler_output"):
                    features = features.pooler_output
                elif hasattr(features, "text_embeds"):
                    features = features.text_embeds
                    
                # L2 normalize
                norm = features.norm(p=2, dim=-1, keepdim=True)
                self.text_embeddings = features.div(norm)
                
            logger.info("FeatureEngine initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize FeatureEngine", extra={"error": str(e)})
            raise RuntimeError(f"FeatureEngine init failed: {e}")

    def extract_features(self, cropped_image_array: np.ndarray | Image.Image) -> Optional[List[float]]:
        """
        Extracts a dense semantic embedding for the cropped image.
        Returns a list of floats representing the 768-dim SigLIP embedding.
        """
        if self.model is None:
            self.initialize()
            
        try:
            if isinstance(cropped_image_array, np.ndarray):
                # Ensure the crop is valid and not empty
                if cropped_image_array.size == 0 or cropped_image_array.shape[0] < 10 or cropped_image_array.shape[1] < 10:
                    return None
                image = Image.fromarray(cropped_image_array)
            else:
                image = cropped_image_array

            with torch.no_grad():
                inputs = self.processor(images=[image], return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                features = self.model.get_image_features(**inputs)
                if hasattr(features, "pooler_output"):
                    features = features.pooler_output
                elif hasattr(features, "image_embeds"):
                    features = features.image_embeds
                    
                # L2 Normalize
                norm = features.norm(p=2, dim=-1, keepdim=True)
                normalized_features = features.div(norm)
                
            return normalized_features[0].cpu().numpy().tolist()
            
        except Exception as e:
            logger.error("Failed to extract features", extra={"error": str(e)})
            return None

    def classify_color(self, cropped_image_array: np.ndarray | Image.Image) -> Optional[str]:
        """
        Performs zero-shot classification to detect dominant clothing color.
        """
        if self.model is None:
            self.initialize()
            
        try:
            if isinstance(cropped_image_array, np.ndarray):
                if cropped_image_array.size == 0 or cropped_image_array.shape[0] < 10 or cropped_image_array.shape[1] < 10:
                    return None
                image = Image.fromarray(cropped_image_array)
            else:
                image = cropped_image_array

            with torch.no_grad():
                inputs = self.processor(images=[image], return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                image_features = self.model.get_image_features(**inputs)
                if hasattr(image_features, "pooler_output"):
                    image_features = image_features.pooler_output
                elif hasattr(image_features, "image_embeds"):
                    image_features = image_features.image_embeds
                    
                # L2 Normalize
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                
                # Dot product similarity
                similarity = (image_features @ self.text_embeddings.T).squeeze(0)
                best_idx = similarity.argmax().item()
                
            return self.color_names[best_idx]
            
        except Exception as e:
            logger.error("Failed to classify color", extra={"error": str(e)})
            return None

    def process_crop(self, track_id: int, timestamp: float, camera_id: str, cropped_image_array: np.ndarray | Image.Image) -> Optional[Dict[str, Any]]:
        """
        Main pipeline function that processes a crop and returns a dictionary
        containing the embedding and detected attributes.
        """
        if isinstance(cropped_image_array, np.ndarray) and (cropped_image_array.size == 0 or cropped_image_array.shape[0] < 10 or cropped_image_array.shape[1] < 10):
            return None

        # To optimize real-time performance, we can extract features and compute similarity directly
        # rather than calling both methods and running the image through the model twice.
        
        if self.model is None:
            self.initialize()
            
        try:
            if isinstance(cropped_image_array, np.ndarray):
                image = Image.fromarray(cropped_image_array)
            else:
                image = cropped_image_array

            with torch.no_grad():
                inputs = self.processor(images=[image], return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                features = self.model.get_image_features(**inputs)
                if hasattr(features, "pooler_output"):
                    features = features.pooler_output
                elif hasattr(features, "image_embeds"):
                    features = features.image_embeds
                    
                # L2 Normalize
                norm = features.norm(p=2, dim=-1, keepdim=True)
                normalized_features = features.div(norm)
                
                # Classification
                similarity = (normalized_features @ self.text_embeddings.T).squeeze(0)
                best_idx = similarity.argmax().item()
                detected_color = self.color_names[best_idx]
                
            embedding_list = normalized_features[0].cpu().numpy().tolist()
            
            return {
                "track_id": track_id,
                "timestamp": timestamp,
                "camera_id": camera_id,
                "siglip_embedding": embedding_list,
                "detected_color": detected_color
            }
            
        except Exception as e:
            logger.error("Failed to process crop", extra={"error": str(e)})
            return None
