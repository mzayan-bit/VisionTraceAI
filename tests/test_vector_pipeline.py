"""
Integration tests for VisionTraceAI Semantic Memory Pipeline.

Run with:
    pytest tests/test_vector_pipeline.py -v
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.models.tracking import BoundingBox, CropMetadata
from app.pipelines.vector_pipeline import SemanticMemoryPipeline
from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService


@pytest.fixture(scope="module")
def qdrant() -> QdrantService:
    service = QdrantService()
    service.connect_memory()
    service.create_collection()
    return service


@pytest.fixture(scope="module")
def embedder() -> SigLIPEmbeddingService:
    service = SigLIPEmbeddingService()
    service.initialize()
    yield service
    service.shutdown()


@pytest.fixture
def pipeline(qdrant: QdrantService, embedder: SigLIPEmbeddingService) -> SemanticMemoryPipeline:
    # Clear memory collection before each test
    qdrant.connect_memory()
    qdrant.create_collection()
    return SemanticMemoryPipeline(qdrant=qdrant, embedder=embedder)


@pytest.fixture
def dummy_crop(tmp_path: Path) -> Path:
    """Creates a temporary dummy crop image."""
    img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    path = tmp_path / "dummy_crop.jpg"
    img.save(path)
    return path


class TestSemanticMemoryPipeline:
    """Test full semantic ingestion and retrieval."""

    def test_generate_point_id(self, pipeline: SemanticMemoryPipeline, dummy_crop: Path) -> None:
        meta = CropMetadata(
            camera_id="cam_test",
            track_id=1,
            frame_number=10,
            timestamp=0.5,
            crop_path=str(dummy_crop),
            bbox=BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
        )
        pid1 = pipeline.generate_point_id(meta)
        pid2 = pipeline.generate_point_id(meta)
        assert pid1 == pid2  # Deterministic
        assert len(pid1) == 32  # md5 hash length

    def test_ingest_crop(self, pipeline: SemanticMemoryPipeline, dummy_crop: Path) -> None:
        meta = CropMetadata(
            camera_id="cam_test",
            track_id=1,
            frame_number=10,
            timestamp=0.5,
            crop_path=str(dummy_crop),
            bbox=BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
        )
        
        point_id = pipeline.ingest_crop(meta)
        assert point_id is not None
        
        # Verify it's in Qdrant
        stats = pipeline.qdrant.get_collection_stats()
        count = stats.get("vectors_count", 0) or stats.get("points_count", 0)
        assert count == 1

    def test_ingest_batch(self, pipeline: SemanticMemoryPipeline, dummy_crop: Path) -> None:
        metas = [
            CropMetadata(
                camera_id="cam_batch",
                track_id=i,
                frame_number=i*10,
                timestamp=i*0.5,
                crop_path=str(dummy_crop),
                bbox=BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
            )
            for i in range(3)
        ]
        
        ids = pipeline.ingest_crops_batch(metas)
        assert len(ids) == 3
        
        stats = pipeline.qdrant.get_collection_stats()
        count = stats.get("vectors_count", 0) or stats.get("points_count", 0)
        assert count == 3

    def test_search_by_text(self, pipeline: SemanticMemoryPipeline, dummy_crop: Path) -> None:
        # Ingest one
        meta = CropMetadata(
            camera_id="cam_search",
            track_id=99,
            frame_number=1,
            timestamp=0.1,
            crop_path=str(dummy_crop),
            bbox=BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
        )
        pipeline.ingest_crop(meta)
        
        # Search
        results = pipeline.search_by_text("person in an image", limit=5)
        
        assert len(results) == 1
        res = results[0]
        assert res.camera_id == "cam_search"
        assert res.track_id == 99
        assert res.payload["camera_id"] == "cam_search"

    def test_search_by_embedding(self, pipeline: SemanticMemoryPipeline, dummy_crop: Path) -> None:
        meta = CropMetadata(
            camera_id="cam_embed",
            track_id=42,
            frame_number=1,
            timestamp=0.1,
            crop_path=str(dummy_crop),
            bbox=BoundingBox(x1=0.0, y1=0.0, x2=10.0, y2=10.0)
        )
        pipeline.ingest_crop(meta)
        
        # Search using dummy vector
        dummy_vector = np.random.rand(768).astype(np.float32)
        # Normalize
        dummy_vector = dummy_vector / np.linalg.norm(dummy_vector)
        
        results = pipeline.search_by_embedding(dummy_vector, limit=1)
        assert len(results) == 1
        assert results[0].track_id == 42
