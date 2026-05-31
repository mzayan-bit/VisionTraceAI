"""
VisionTraceAI — Qdrant Vector Database Service.

Production-grade integration layer for the Qdrant vector database,
serving as the semantic memory backend for the surveillance system.

Usage::

    from app.services.database import QdrantService

    qdrant = QdrantService()
    qdrant.connect()
    qdrant.create_collection("visiontrace_embeddings", vector_size=1152)
    results = qdrant.search("visiontrace_embeddings", query_vector=[...], top_k=5)
"""

from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import (
    ResponseHandlingException,
    UnexpectedResponse,
)

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QdrantServiceError(Exception):
    """Base exception for Qdrant service errors."""


class QdrantConnectionError(QdrantServiceError):
    """Raised when a connection to Qdrant cannot be established."""


class QdrantCollectionError(QdrantServiceError):
    """Raised on collection-level operation failures."""


class QdrantService:
    """Production-grade Qdrant vector database service.

    Manages connections, collections, and vector operations against a
    Qdrant instance. All configuration is read from the centralised
    settings system.

    Attributes:
        host: Qdrant server hostname.
        port: Qdrant server port.
        collection_name: Default collection name.
        client: Underlying ``QdrantClient`` instance (``None`` until connected).
    """

    # Default vector configuration for SigLIP embeddings
    DEFAULT_VECTOR_SIZE: int = 1152
    DEFAULT_DISTANCE: qmodels.Distance = qmodels.Distance.COSINE

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        collection_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.collection_name = collection_name or settings.qdrant_collection_name
        self.client: QdrantClient | None = None

        logger.info(
            "QdrantService initialised",
            extra={"host": self.host, "port": self.port, "collection": self.collection_name},
        )

    # ── Connection ───────────────────────────────────────────────────────

    def connect(self) -> None:
        """Establish a connection to the Qdrant server.

        Raises:
            QdrantConnectionError: If the connection cannot be established.
        """
        logger.info("Connecting to Qdrant", extra={"host": self.host, "port": self.port})
        try:
            self.client = QdrantClient(host=self.host, port=self.port, timeout=10)
            # Verify the connection with a lightweight call
            self.client.get_collections()
            logger.info("Qdrant connection established successfully")
        except (ResponseHandlingException, Exception) as exc:
            self.client = None
            logger.error("Failed to connect to Qdrant", extra={"error": str(exc)})
            raise QdrantConnectionError(
                f"Cannot connect to Qdrant at {self.host}:{self.port} — {exc}"
            ) from exc

    def connect_memory(self) -> None:
        """Connect using an in-memory Qdrant instance (for testing).

        This creates a local, ephemeral Qdrant database that requires
        no running server. Ideal for unit tests and CI pipelines.
        """
        logger.info("Connecting to in-memory Qdrant instance")
        self.client = QdrantClient(":memory:")
        logger.info("In-memory Qdrant connection established")

    def _ensure_client(self) -> QdrantClient:
        """Return the connected client or raise."""
        if self.client is None:
            raise QdrantConnectionError(
                "Not connected to Qdrant. Call connect() first."
            )
        return self.client

    # ── Health ───────────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Run a health check against the Qdrant server.

        Returns:
            Dictionary with ``status``, ``version``, and ``collections_count``.

        Raises:
            QdrantConnectionError: If the server is unreachable.
        """
        client = self._ensure_client()
        try:
            collections = client.get_collections().collections
            logger.info(
                "Health check passed",
                extra={"collections_count": len(collections)},
            )
            return {
                "status": "healthy",
                "host": self.host,
                "port": self.port,
                "collections_count": len(collections),
                "collection_names": [c.name for c in collections],
            }
        except Exception as exc:
            logger.error("Health check failed", extra={"error": str(exc)})
            raise QdrantConnectionError(f"Health check failed — {exc}") from exc

    # ── Collection Operations ────────────────────────────────────────────

    def collection_exists(self, name: str | None = None) -> bool:
        """Check whether a collection exists.

        Args:
            name: Collection name. Defaults to ``self.collection_name``.
        """
        client = self._ensure_client()
        name = name or self.collection_name
        try:
            exists = client.collection_exists(name)
            logger.debug("Collection existence check", extra={"collection": name, "exists": exists})
            return exists
        except Exception as exc:
            logger.error("Collection existence check failed", extra={"collection": name, "error": str(exc)})
            raise QdrantCollectionError(f"Cannot check collection '{name}' — {exc}") from exc

    def create_collection(
        self,
        name: str | None = None,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        distance: qmodels.Distance = DEFAULT_DISTANCE,
        *,
        skip_if_exists: bool = True,
    ) -> bool:
        """Create a new vector collection.

        Args:
            name: Collection name. Defaults to ``self.collection_name``.
            vector_size: Dimensionality of vectors (default 1152 for SigLIP).
            distance: Distance metric (default COSINE).
            skip_if_exists: If ``True``, silently skip when the collection
                already exists.

        Returns:
            ``True`` if the collection was created, ``False`` if it already existed.

        Raises:
            QdrantCollectionError: On creation failure.
        """
        client = self._ensure_client()
        name = name or self.collection_name

        if skip_if_exists and self.collection_exists(name):
            logger.info("Collection already exists, skipping creation", extra={"collection": name})
            return False

        logger.info(
            "Creating collection",
            extra={"collection": name, "vector_size": vector_size, "distance": distance.value},
        )
        try:
            client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=distance,
                ),
            )
            logger.info("Collection created successfully", extra={"collection": name})
            return True
        except (UnexpectedResponse, Exception) as exc:
            logger.error("Failed to create collection", extra={"collection": name, "error": str(exc)})
            raise QdrantCollectionError(f"Cannot create collection '{name}' — {exc}") from exc

    def delete_collection(self, name: str | None = None) -> bool:
        """Delete a collection.

        Args:
            name: Collection name. Defaults to ``self.collection_name``.

        Returns:
            ``True`` if deleted, ``False`` if it did not exist.

        Raises:
            QdrantCollectionError: On deletion failure.
        """
        client = self._ensure_client()
        name = name or self.collection_name

        if not self.collection_exists(name):
            logger.info("Collection does not exist, nothing to delete", extra={"collection": name})
            return False

        logger.info("Deleting collection", extra={"collection": name})
        try:
            client.delete_collection(collection_name=name)
            logger.info("Collection deleted", extra={"collection": name})
            return True
        except Exception as exc:
            logger.error("Failed to delete collection", extra={"collection": name, "error": str(exc)})
            raise QdrantCollectionError(f"Cannot delete collection '{name}' — {exc}") from exc

    def get_collection_stats(self, name: str | None = None) -> dict[str, Any]:
        """Retrieve statistics for a collection.

        Returns:
            Dictionary with ``name``, ``vectors_count``, ``points_count``,
            ``status``, and ``vector_size``.
        """
        client = self._ensure_client()
        name = name or self.collection_name
        try:
            info = client.get_collection(collection_name=name)
            stats = {
                "collection_name": name,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "segments_count": info.segments_count,
                "status": info.status.value if info.status else "unknown",
                "vector_size": info.config.params.vectors.size  # type: ignore[union-attr]
                if info.config and info.config.params
                else None,
            }
            logger.info("Collection stats retrieved", extra=stats)
            return stats
        except Exception as exc:
            logger.error("Failed to get collection stats", extra={"collection": name, "error": str(exc)})
            raise QdrantCollectionError(f"Cannot get stats for '{name}' — {exc}") from exc

    def list_collections(self) -> list[str]:
        """List all collection names on the Qdrant server."""
        client = self._ensure_client()
        try:
            collections = client.get_collections().collections
            names = [c.name for c in collections]
            logger.info("Listed collections", extra={"count": len(names)})
            return names
        except Exception as exc:
            logger.error("Failed to list collections", extra={"error": str(exc)})
            raise QdrantServiceError(f"Cannot list collections — {exc}") from exc

    # ── Vector Operations ────────────────────────────────────────────────

    def insert_vector(
        self,
        vector: list[float],
        payload: dict[str, Any] | None = None,
        point_id: str | None = None,
        collection_name: str | None = None,
    ) -> str:
        """Insert a single vector into a collection.

        Args:
            vector: The embedding vector.
            payload: Optional metadata dictionary.
            point_id: Optional point UUID. Auto-generated if omitted.
            collection_name: Target collection. Defaults to ``self.collection_name``.

        Returns:
            The point ID (string UUID).
        """
        client = self._ensure_client()
        collection_name = collection_name or self.collection_name
        point_id = point_id or str(uuid.uuid4())

        logger.debug(
            "Inserting vector",
            extra={"collection": collection_name, "point_id": point_id, "dim": len(vector)},
        )
        try:
            client.upsert(
                collection_name=collection_name,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload or {},
                    )
                ],
            )
            logger.info(
                "Vector inserted",
                extra={"collection": collection_name, "point_id": point_id},
            )
            return point_id
        except Exception as exc:
            logger.error("Failed to insert vector", extra={"point_id": point_id, "error": str(exc)})
            raise QdrantServiceError(f"Insert failed for point '{point_id}' — {exc}") from exc

    def insert_batch(
        self,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]] | None = None,
        point_ids: list[str] | None = None,
        collection_name: str | None = None,
    ) -> list[str]:
        """Insert a batch of vectors into a collection.

        Args:
            vectors: List of embedding vectors.
            payloads: Optional list of metadata dicts (one per vector).
            point_ids: Optional list of UUIDs. Auto-generated if omitted.
            collection_name: Target collection.

        Returns:
            List of point IDs.
        """
        client = self._ensure_client()
        collection_name = collection_name or self.collection_name
        count = len(vectors)

        if point_ids is None:
            point_ids = [str(uuid.uuid4()) for _ in range(count)]
        if payloads is None:
            payloads = [{} for _ in range(count)]

        if len(point_ids) != count or len(payloads) != count:
            raise ValueError(
                f"Length mismatch: {count} vectors, {len(point_ids)} IDs, {len(payloads)} payloads"
            )

        logger.info(
            "Inserting batch",
            extra={"collection": collection_name, "batch_size": count},
        )
        try:
            points = [
                qmodels.PointStruct(id=pid, vector=vec, payload=pl)
                for pid, vec, pl in zip(point_ids, vectors, payloads)
            ]
            client.upsert(collection_name=collection_name, points=points)
            logger.info(
                "Batch inserted successfully",
                extra={"collection": collection_name, "count": count},
            )
            return point_ids
        except Exception as exc:
            logger.error("Batch insert failed", extra={"batch_size": count, "error": str(exc)})
            raise QdrantServiceError(f"Batch insert failed — {exc}") from exc

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        collection_name: str | None = None,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search for the nearest vectors in a collection.

        Args:
            query_vector: The query embedding.
            top_k: Number of results to return.
            collection_name: Target collection.
            score_threshold: Optional minimum score filter.

        Returns:
            List of dicts with ``id``, ``score``, and ``payload``.
        """
        client = self._ensure_client()
        collection_name = collection_name or self.collection_name

        logger.debug(
            "Searching vectors",
            extra={"collection": collection_name, "top_k": top_k, "dim": len(query_vector)},
        )
        try:
            results = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
            )
            formatted = [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results.points
            ]
            logger.info(
                "Search completed",
                extra={"collection": collection_name, "results_count": len(formatted)},
            )
            return formatted
        except Exception as exc:
            logger.error("Search failed", extra={"collection": collection_name, "error": str(exc)})
            raise QdrantServiceError(f"Search failed on '{collection_name}' — {exc}") from exc
