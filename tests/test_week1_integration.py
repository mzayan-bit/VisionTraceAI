"""
Week 1 Integration Tests — VisionTraceAI.

End-to-end tests validating the complete pipeline:
    Tracker → Cropper → Embedder → Qdrant → SearchEngine

Run with::

    pytest tests/test_week1_integration.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from app.core.tracker import VisionTracker
from app.models.search import SearchResult
from app.models.tracking import BoundingBox, CropMetadata, FrameResult, TrackResult
from app.pipelines.cropper import PersonCropPipeline
from app.pipelines.vector_pipeline import SemanticMemoryPipeline
from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService
from app.services.search_engine import VisionSearchEngine


# ── Shared Fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def tracker() -> VisionTracker:
    t = VisionTracker()
    t.initialize_model()
    yield t
    t.shutdown()


@pytest.fixture(scope="module")
def embedder() -> SigLIPEmbeddingService:
    e = SigLIPEmbeddingService()
    e.initialize()
    yield e
    e.shutdown()


@pytest.fixture(scope="module")
def search_engine() -> VisionSearchEngine:
    engine = VisionSearchEngine()
    engine.initialize(use_memory=True)
    yield engine
    engine.shutdown()


@pytest.fixture
def dummy_frame() -> np.ndarray:
    """Create a synthetic BGR frame."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def dummy_crop(tmp_path: Path) -> Path:
    img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    p = tmp_path / "integ_crop.jpg"
    img.save(p)
    return p


@pytest.fixture
def seeded_engine(search_engine: VisionSearchEngine, dummy_crop: Path) -> VisionSearchEngine:
    """Search engine with a few crops already ingested."""
    pipeline = search_engine._ensure_ready()
    for i in range(5):
        meta = CropMetadata(
            camera_id="cam_integ",
            track_id=i,
            frame_number=i * 10,
            timestamp=i * 0.5,
            crop_path=str(dummy_crop),
            bbox=BoundingBox(x1=0, y1=0, x2=50, y2=100),
        )
        pipeline.ingest_crop(meta)
    return search_engine


# ── Integration Tests ────────────────────────────────────────────────────


class TestTrackerIntegration:
    """Tracker produces valid FrameResult objects."""

    def test_tracker_returns_frame_result(
        self, tracker: VisionTracker, dummy_frame: np.ndarray
    ) -> None:
        res, annotated = tracker.track_frame(dummy_frame, 0, 0.0)
        assert isinstance(res, FrameResult)
        assert isinstance(annotated, np.ndarray)

    def test_tracker_frame_has_valid_schema(
        self, tracker: VisionTracker, dummy_frame: np.ndarray
    ) -> None:
        res, _ = tracker.track_frame(dummy_frame, 1, 0.033)
        assert res.frame_number == 1
        assert res.timestamp == pytest.approx(0.033)
        assert isinstance(res.tracks, list)


class TestCropperIntegration:
    """Cropper processes tracker output correctly."""

    def test_cropper_accepts_valid_track(self, tmp_path: Path) -> None:
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        track = TrackResult(
            track_id=1,
            confidence=0.9,
            bbox=BoundingBox(x1=10, y1=10, x2=200, y2=400),
        )
        cropper = PersonCropPipeline(output_dir=tmp_path, blur_threshold=0.0)
        meta = cropper.process_track(frame, track, "cam_test", 0, 0.0)
        assert meta is not None
        assert Path(meta.crop_path).exists()

    def test_crop_metadata_serialisable(self, tmp_path: Path) -> None:
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        track = TrackResult(
            track_id=2,
            confidence=0.85,
            bbox=BoundingBox(x1=20, y1=20, x2=300, y2=450),
        )
        cropper = PersonCropPipeline(output_dir=tmp_path, blur_threshold=0.0)
        meta = cropper.process_track(frame, track, "cam_test", 5, 0.5)
        assert meta is not None
        d = meta.model_dump()
        assert isinstance(json.dumps(d), str)


class TestEmbedderIntegration:
    """Embedder generates correct-dimension normalised vectors."""

    def test_image_embedding_shape(
        self, embedder: SigLIPEmbeddingService, dummy_crop: Path
    ) -> None:
        img = Image.open(dummy_crop).convert("RGB")
        vec = embedder.encode_image(img)
        assert vec.shape == (768,)
        assert vec.dtype == np.float32

    def test_text_embedding_shape(self, embedder: SigLIPEmbeddingService) -> None:
        vec = embedder.encode_text("person wearing a hat")
        assert vec.shape == (768,)
        assert vec.dtype == np.float32


class TestQdrantIntegration:
    """Qdrant stores and retrieves vectors correctly."""

    def test_insert_and_search(self) -> None:
        qdrant = QdrantService()
        qdrant.connect_memory()
        qdrant.create_collection()

        vec = np.random.rand(768).astype(np.float32).tolist()
        qdrant.insert_vector(vector=vec, payload={"track_id": 99, "camera_id": "cam_q"})

        results = qdrant.search(query_vector=vec, top_k=1)
        assert len(results) == 1
        assert results[0]["payload"]["track_id"] == 99


class TestSearchEngineIntegration:
    """Full pipeline search works end-to-end."""

    def test_text_search_returns_results(
        self, seeded_engine: VisionSearchEngine
    ) -> None:
        results = seeded_engine.search("person", limit=5)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_track_filter_returns_correct_id(
        self, seeded_engine: VisionSearchEngine
    ) -> None:
        results = seeded_engine.search_by_track(track_id=0)
        assert all(r.track_id == 0 for r in results)

    def test_camera_filter_returns_correct_id(
        self, seeded_engine: VisionSearchEngine
    ) -> None:
        results = seeded_engine.search_by_camera(camera_id="cam_integ")
        assert all(r.camera_id == "cam_integ" for r in results)

    def test_save_results_produces_json(
        self, seeded_engine: VisionSearchEngine, tmp_path: Path
    ) -> None:
        results = seeded_engine.search("person", limit=3)
        out = seeded_engine.save_results(results, "person", tmp_path / "out.json")
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["total_results"] == len(results)

    def test_payload_integrity(
        self, seeded_engine: VisionSearchEngine
    ) -> None:
        results = seeded_engine.search("person", limit=1)
        assert len(results) >= 1
        r = results[0]
        assert r.camera_id == "cam_integ"
        assert isinstance(r.payload, dict)
        assert "embedding_model" in r.payload
        assert "created_at" in r.payload
