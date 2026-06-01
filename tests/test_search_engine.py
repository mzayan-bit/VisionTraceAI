"""
Tests for VisionTraceAI VisionSearchEngine (Stage 9 — Week 1 MVP).

Run with::

    pytest tests/test_search_engine.py -v
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Generator

import numpy as np
import pytest
from PIL import Image

from app.models.search import SearchResult
from app.models.tracking import BoundingBox, CropMetadata
from app.services.search_engine import VisionSearchEngine


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine() -> Generator[VisionSearchEngine, None, None]:
    eng = VisionSearchEngine()
    eng.initialize(use_memory=True)
    yield eng
    eng.shutdown()


@pytest.fixture
def dummy_crop(tmp_path: Path) -> Path:
    """Create a temporary dummy crop image."""
    img = Image.fromarray(
        np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    )
    path = tmp_path / "dummy_crop.jpg"
    img.save(path)
    return path


def _seed_engine(engine: VisionSearchEngine, crop_path: Path, n: int = 5) -> None:
    """Insert *n* synthetic crops into the engine's Qdrant collection."""
    pipeline = engine._ensure_ready()
    for i in range(n):
        meta = CropMetadata(
            camera_id="cam_test",
            track_id=i,
            frame_number=i * 10,
            timestamp=i * 0.5,
            crop_path=str(crop_path),
            bbox=BoundingBox(x1=0, y1=0, x2=50, y2=100),
        )
        pipeline.ingest_crop(meta)


# ── Test Classes ─────────────────────────────────────────────────────────


class TestSearchEngineLifecycle:
    """Verify init / shutdown semantics."""

    def test_is_initialised(self, engine: VisionSearchEngine) -> None:
        assert engine._initialized is True

    def test_pipeline_exists(self, engine: VisionSearchEngine) -> None:
        assert engine.pipeline is not None

    def test_uninitialised_raises(self) -> None:
        eng = VisionSearchEngine()
        with pytest.raises(RuntimeError, match="not initialised"):
            eng.search("anything")


class TestSearchQueries:
    """Validate semantic text search."""

    def test_search_returns_list(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        _seed_engine(engine, dummy_crop, n=3)
        results = engine.search("person", limit=10)
        assert isinstance(results, list)

    def test_search_result_type(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        _seed_engine(engine, dummy_crop, n=1)
        results = engine.search("person walking")
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_top_k_limits(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        _seed_engine(engine, dummy_crop, n=5)
        results = engine.search_top_k("person", k=2)
        assert len(results) <= 2

    def test_search_person_augments_query(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        """search_person should still return valid results."""
        _seed_engine(engine, dummy_crop, n=2)
        results = engine.search_person("wearing a red jacket")
        assert isinstance(results, list)

    def test_empty_collection_returns_empty(self) -> None:
        eng = VisionSearchEngine()
        eng.initialize(use_memory=True)
        try:
            results = eng.search("something that does not exist")
            assert results == []
        finally:
            eng.shutdown()


class TestResultRanking:
    """Ensure results come back sorted by descending cosine similarity."""

    def test_sorted_descending(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        _seed_engine(engine, dummy_crop, n=5)
        results = engine.search("person standing")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestPayloadFilters:
    """Validate track_id and camera_id filtering."""

    def test_search_by_track(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        _seed_engine(engine, dummy_crop, n=5)
        results = engine.search_by_track(track_id=0)
        assert all(r.track_id == 0 for r in results)

    def test_search_by_camera(
        self, engine: VisionSearchEngine, dummy_crop: Path
    ) -> None:
        _seed_engine(engine, dummy_crop, n=3)
        results = engine.search_by_camera(camera_id="cam_test")
        assert all(r.camera_id == "cam_test" for r in results)

    def test_search_by_track_nonexistent(
        self, engine: VisionSearchEngine
    ) -> None:
        results = engine.search_by_track(track_id=999999)
        assert results == []


class TestResultFormatting:
    """Validate formatting and serialisation helpers."""

    def test_format_results_empty(self) -> None:
        text = VisionSearchEngine.format_results([])
        assert "No results" in text

    def test_format_results_nonempty(self) -> None:
        dummy = SearchResult(
            score=0.91,
            track_id=7,
            camera_id="cam_1",
            crop_path="/tmp/crop.jpg",
            timestamp=3.5,
            payload={},
        )
        text = VisionSearchEngine.format_results([dummy])
        assert "cam_1" in text
        assert "0.91" in text

    def test_results_to_dict(self) -> None:
        dummy = SearchResult(
            score=0.5,
            track_id=1,
            camera_id="cam_x",
            crop_path="/tmp/c.jpg",
            timestamp=1.0,
            payload={"a": 1},
        )
        dicts = VisionSearchEngine.results_to_dict([dummy])
        assert isinstance(dicts, list)
        assert dicts[0]["track_id"] == 1

    def test_save_results(self, engine: VisionSearchEngine, tmp_path: Path) -> None:
        dummy = SearchResult(
            score=0.75,
            track_id=2,
            camera_id="cam_2",
            crop_path="/tmp/c.jpg",
            timestamp=2.0,
            payload={},
        )
        out = engine.save_results(
            [dummy], query="test query", output_path=tmp_path / "out.json"
        )
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["query"] == "test query"
        assert data["total_results"] == 1
