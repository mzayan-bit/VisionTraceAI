"""
VisionTraceAI — Semantic Memory Pipeline.

Connects the Crop Pipeline, SigLIP, and Qdrant to form a complete
vector semantic memory layer for the surveillance system.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

import numpy as np
from PIL import Image

from app.models.search import SearchResult
from app.models.tracking import CropMetadata
from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SemanticMemoryPipeline:
    """Manages ingestion and retrieval of semantic embeddings into Qdrant."""

    def __init__(self, qdrant: QdrantService, embedder: SigLIPEmbeddingService) -> None:
        self.qdrant = qdrant
        self.embedder = embedder

    def generate_point_id(self, meta: CropMetadata) -> str:
        """Create a deterministic ID based on camera, track, and frame."""
        raw_id = f"{meta.camera_id}_{meta.track_id}_{meta.frame_number}_{meta.timestamp}"
        return hashlib.md5(raw_id.encode("utf-8")).hexdigest()

    def create_payload(self, meta: CropMetadata) -> dict[str, Any]:
        """Convert crop metadata into a Qdrant-compatible payload."""
        return {
            "camera_id": meta.camera_id,
            "track_id": meta.track_id,
            "frame_number": meta.frame_number,
            "timestamp": meta.timestamp,
            "crop_path": str(meta.crop_path),
            "bbox": {
                "x1": meta.bbox.x1,
                "y1": meta.bbox.y1,
                "x2": meta.bbox.x2,
                "y2": meta.bbox.y2,
            },
            "embedding_model": self.embedder.model_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def ingest_crop(self, meta: CropMetadata) -> str:
        """Load crop, embed it, and store in Qdrant. Returns point ID."""
        crop_path = Path(meta.crop_path)
        if not crop_path.exists():
            raise FileNotFoundError(f"Crop image not found: {crop_path}")
            
        # Load image
        img = Image.open(crop_path).convert("RGB")
        
        # Embed
        vector = self.embedder.encode_image(img)
        
        # Prepare payload
        payload = self.create_payload(meta)
        point_id = self.generate_point_id(meta)
        
        # Store in Qdrant
        self.qdrant.insert_vector(
            point_id=point_id,
            vector=vector.tolist(),
            payload=payload
        )
        
        logger.debug("Ingested crop into Qdrant", extra={"point_id": point_id})
        return point_id

    def ingest_crops_batch(self, metas: List[CropMetadata]) -> List[str]:
        """Batch ingest crops into Qdrant."""
        if not metas:
            return []
            
        images = []
        valid_metas = []
        
        for meta in metas:
            crop_path = Path(meta.crop_path)
            if crop_path.exists():
                images.append(Image.open(crop_path).convert("RGB"))
                valid_metas.append(meta)
            else:
                logger.warning(f"Crop missing, skipping: {crop_path}")
                
        if not valid_metas:
            return []
            
        vectors = self.embedder.encode_images(images)
        
        ids = []
        payloads = []
        vectors_list = []
        
        for i, meta in enumerate(valid_metas):
            ids.append(self.generate_point_id(meta))
            payloads.append(self.create_payload(meta))
            vectors_list.append(vectors[i].tolist())
            
        self.qdrant.insert_batch(
            point_ids=ids,
            vectors=vectors_list,
            payloads=payloads
        )
        
        logger.info(f"Batch ingested {len(ids)} crops into Qdrant")
        return ids

    def _parse_search_results(self, qdrant_results: List[dict[str, Any]]) -> List[SearchResult]:
        """Convert Qdrant result dicts into SearchResult models."""
        results = []
        for point in qdrant_results:
            payload = point.get("payload", {})
            
            res = SearchResult(
                score=point.get("score", 0.0),
                track_id=payload.get("track_id", -1),
                camera_id=payload.get("camera_id", "unknown"),
                crop_path=payload.get("crop_path", ""),
                timestamp=payload.get("timestamp", 0.0),
                payload=payload
            )
            results.append(res)
        return results

    def search_by_text(self, query: str, limit: int = 5) -> List[SearchResult]:
        """Search for crops matching a semantic text description."""
        vector = self.embedder.encode_text(query)
        matches = self.qdrant.search(query_vector=vector.tolist(), top_k=limit)
        return self._parse_search_results(matches)

    def search_by_embedding(self, vector: List[float] | np.ndarray, limit: int = 5) -> List[SearchResult]:
        """Search using a raw vector embedding."""
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        matches = self.qdrant.search(query_vector=vector, top_k=limit)
        return self._parse_search_results(matches)

    def search_similar_person(self, crop_path: str | Path, limit: int = 5) -> List[SearchResult]:
        """Find matching individuals based on an image crop."""
        path = Path(crop_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
            
        img = Image.open(path).convert("RGB")
        vector = self.embedder.encode_image(img)
        matches = self.qdrant.search(query_vector=vector.tolist(), top_k=limit)
        return self._parse_search_results(matches)
