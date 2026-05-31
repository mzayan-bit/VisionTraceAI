"""
Integration tests for VisionTraceAI Qdrant service.

Uses Qdrant's in-memory mode — no running server required.

Run with:
    pytest tests/test_qdrant.py -v
"""

from __future__ import annotations

import uuid

import pytest

from app.services.database import (
    QdrantConnectionError,
    QdrantService,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_COLLECTION = f"test_visiontrace_{uuid.uuid4().hex[:8]}"
TEST_VECTOR_SIZE = 1152


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def qdrant() -> QdrantService:
    """Return a QdrantService connected via in-memory backend."""
    svc = QdrantService()
    svc.connect_memory()
    return svc


@pytest.fixture(autouse=True, scope="module")
def _cleanup(qdrant: QdrantService) -> None:  # type: ignore[misc]
    """Ensure the test collection is removed after all tests."""
    yield  # type: ignore[misc]
    if qdrant.collection_exists(TEST_COLLECTION):
        qdrant.delete_collection(TEST_COLLECTION)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

class TestConnection:
    """Connection and health check tests."""

    def test_connect_success(self, qdrant: QdrantService) -> None:
        assert qdrant.client is not None

    def test_health_check(self, qdrant: QdrantService) -> None:
        health = qdrant.health_check()
        assert health["status"] == "healthy"
        assert isinstance(health["collections_count"], int)
        assert isinstance(health["collection_names"], list)

    def test_connect_bad_host(self) -> None:
        svc = QdrantService(host="nonexistent-host-12345", port=9999)
        with pytest.raises(QdrantConnectionError):
            svc.connect()


# ---------------------------------------------------------------------------
# Collection CRUD
# ---------------------------------------------------------------------------

class TestCollections:
    """Collection creation, existence, stats, and deletion."""

    def test_create_collection(self, qdrant: QdrantService) -> None:
        created = qdrant.create_collection(
            name=TEST_COLLECTION,
            vector_size=TEST_VECTOR_SIZE,
        )
        assert created is True

    def test_collection_exists(self, qdrant: QdrantService) -> None:
        assert qdrant.collection_exists(TEST_COLLECTION) is True

    def test_collection_not_exists(self, qdrant: QdrantService) -> None:
        assert qdrant.collection_exists("nonexistent_collection_xyz") is False

    def test_create_skip_if_exists(self, qdrant: QdrantService) -> None:
        created = qdrant.create_collection(
            name=TEST_COLLECTION,
            vector_size=TEST_VECTOR_SIZE,
            skip_if_exists=True,
        )
        assert created is False  # already exists

    def test_collection_stats(self, qdrant: QdrantService) -> None:
        stats = qdrant.get_collection_stats(TEST_COLLECTION)
        assert stats["collection_name"] == TEST_COLLECTION
        assert stats["vector_size"] == TEST_VECTOR_SIZE
        assert stats["status"] == "green"

    def test_list_collections(self, qdrant: QdrantService) -> None:
        names = qdrant.list_collections()
        assert TEST_COLLECTION in names


# ---------------------------------------------------------------------------
# Vector Operations
# ---------------------------------------------------------------------------

class TestVectorOperations:
    """Insert and search operations."""

    def test_insert_vector(self, qdrant: QdrantService) -> None:
        vector = [0.1] * TEST_VECTOR_SIZE
        payload = {"label": "person", "camera_id": "cam_01", "test": True}
        point_id = qdrant.insert_vector(
            vector=vector,
            payload=payload,
            collection_name=TEST_COLLECTION,
        )
        assert point_id is not None
        assert isinstance(point_id, str)

    def test_insert_batch(self, qdrant: QdrantService) -> None:
        vectors = [
            [0.2] * TEST_VECTOR_SIZE,
            [0.3] * TEST_VECTOR_SIZE,
            [0.4] * TEST_VECTOR_SIZE,
        ]
        payloads = [
            {"label": "car", "camera_id": "cam_02"},
            {"label": "truck", "camera_id": "cam_02"},
            {"label": "bicycle", "camera_id": "cam_03"},
        ]
        ids = qdrant.insert_batch(
            vectors=vectors,
            payloads=payloads,
            collection_name=TEST_COLLECTION,
        )
        assert len(ids) == 3

    def test_search_vector(self, qdrant: QdrantService) -> None:
        query = [0.1] * TEST_VECTOR_SIZE
        results = qdrant.search(
            query_vector=query,
            top_k=5,
            collection_name=TEST_COLLECTION,
        )
        assert len(results) > 0
        assert "id" in results[0]
        assert "score" in results[0]
        assert "payload" in results[0]

    def test_search_returns_sorted_by_score(self, qdrant: QdrantService) -> None:
        query = [0.15] * TEST_VECTOR_SIZE
        results = qdrant.search(
            query_vector=query,
            top_k=5,
            collection_name=TEST_COLLECTION,
        )
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_stats_after_inserts(self, qdrant: QdrantService) -> None:
        stats = qdrant.get_collection_stats(TEST_COLLECTION)
        # 1 single insert + 3 batch = 4
        assert stats["points_count"] >= 4


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

class TestCleanup:
    """Deletion tests — run last."""

    def test_delete_collection(self, qdrant: QdrantService) -> None:
        deleted = qdrant.delete_collection(TEST_COLLECTION)
        assert deleted is True

    def test_delete_nonexistent(self, qdrant: QdrantService) -> None:
        deleted = qdrant.delete_collection("nonexistent_col_abc")
        assert deleted is False

    def test_collection_gone(self, qdrant: QdrantService) -> None:
        assert qdrant.collection_exists(TEST_COLLECTION) is False
