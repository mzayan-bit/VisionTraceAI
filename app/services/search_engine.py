"""
VisionTraceAI — Vision Search Engine.

High-level search facade providing natural language querying, track-based
lookups, camera filtering, and ranked result formatting on top of the
Semantic Memory Pipeline.

Usage::

    from app.services.search_engine import VisionSearchEngine

    engine = VisionSearchEngine()
    engine.initialize()
    results = engine.search("person wearing a blue hoodie")
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

import numpy as np

from app.models.search import SearchResult
from app.pipelines.vector_pipeline import SemanticMemoryPipeline
from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VisionSearchEngine:
    """Week-1 MVP search engine for the VisionTraceAI platform.

    Wraps :class:`SemanticMemoryPipeline` with additional convenience
    methods for ranked querying, payload-based filtering, and structured
    result formatting.

    Attributes:
        qdrant: The underlying Qdrant vector-database service.
        embedder: The SigLIP embedding service.
        pipeline: The semantic memory pipeline used for vector operations.
    """

    def __init__(
        self,
        qdrant: QdrantService | None = None,
        embedder: SigLIPEmbeddingService | None = None,
    ) -> None:
        self.qdrant = qdrant or QdrantService()
        self.embedder = embedder or SigLIPEmbeddingService()
        self.pipeline: SemanticMemoryPipeline | None = None
        self._initialized = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    def initialize(self, use_memory: bool = False) -> None:
        """Boot every subsystem (Qdrant + SigLIP).

        Args:
            use_memory: If ``True``, use an in-memory Qdrant instance
                instead of connecting to a running server.  Useful for
                demos and tests.
        """
        logger.info("Initializing VisionSearchEngine")
        start = time.time()

        # Qdrant
        if use_memory:
            self.qdrant.connect_memory()
        else:
            try:
                self.qdrant.connect()
                self.qdrant.health_check()
            except Exception:
                logger.warning(
                    "Qdrant server not available — falling back to in-memory"
                )
                self.qdrant.connect_memory()

        self.qdrant.create_collection()

        # SigLIP
        self.embedder.initialize()

        # Pipeline
        self.pipeline = SemanticMemoryPipeline(
            qdrant=self.qdrant, embedder=self.embedder
        )
        self._initialized = True

        elapsed = time.time() - start
        logger.info(
            "VisionSearchEngine ready",
            extra={"init_time_sec": round(elapsed, 2)},
        )

    def shutdown(self) -> None:
        """Release all resources."""
        self.embedder.shutdown()
        self._initialized = False
        logger.info("VisionSearchEngine shut down")

    def _ensure_ready(self) -> SemanticMemoryPipeline:
        if not self._initialized or self.pipeline is None:
            raise RuntimeError(
                "VisionSearchEngine is not initialised. Call initialize() first."
            )
        return self.pipeline

    # ── Core Search Methods ──────────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Run a natural-language semantic search.

        Args:
            query: Free-form text description (e.g. ``"person in red jacket"``).
            limit: Maximum number of results.

        Returns:
            Ranked list of :class:`SearchResult`, highest similarity first.
        """
        pipeline = self._ensure_ready()

        logger.info("Executing search", extra={"query": query, "limit": limit})
        start = time.time()

        results = pipeline.search_by_text(query, limit=limit)

        # Results from Qdrant already come sorted by score descending, but
        # we enforce the guarantee here.
        results.sort(key=lambda r: r.score, reverse=True)

        elapsed = time.time() - start
        logger.info(
            "Search completed",
            extra={
                "query": query,
                "results_count": len(results),
                "latency_sec": round(elapsed, 3),
            },
        )
        return results

    def search_top_k(self, query: str, k: int = 5) -> List[SearchResult]:
        """Convenience wrapper that returns exactly *k* results."""
        return self.search(query, limit=k)

    def search_person(self, description: str, limit: int = 10) -> List[SearchResult]:
        """Search for a person matching a text description.

        Prepends *"a photo of "* to the description to improve SigLIP
        zero-shot retrieval quality.
        """
        augmented = f"a photo of {description}"
        return self.search(augmented, limit=limit)

    def search_by_image(self, image_path: str | Path, limit: int = 10) -> List[SearchResult]:
        """Search for visually similar crops given an image path."""
        pipeline = self._ensure_ready()
        results = pipeline.search_similar_person(image_path, limit=limit)
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    # ── Payload-Based Filters ────────────────────────────────────────────

    def search_by_track(self, track_id: int, limit: int = 50) -> List[SearchResult]:
        """Retrieve all indexed crops for a given *track_id*.

        Uses Qdrant's ``scroll`` API with a payload filter so that no
        query vector is required.
        """
        pipeline = self._ensure_ready()
        client = self.qdrant._ensure_client()

        from qdrant_client.http import models as qmodels

        results, _next = client.scroll(
            collection_name=self.qdrant.collection_name,
            scroll_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="track_id",
                        match=qmodels.MatchValue(value=track_id),
                    )
                ]
            ),
            limit=limit,
            with_vectors=False,
            with_payload=True,
        )

        parsed: List[SearchResult] = []
        for point in results:
            payload = point.payload or {}
            parsed.append(
                SearchResult(
                    score=1.0,  # exact match — no cosine involved
                    track_id=payload.get("track_id", track_id),
                    camera_id=payload.get("camera_id", "unknown"),
                    crop_path=payload.get("crop_path", ""),
                    timestamp=payload.get("timestamp", 0.0),
                    payload=payload,
                )
            )

        logger.info(
            "Track search completed",
            extra={"track_id": track_id, "results": len(parsed)},
        )
        return parsed

    def search_by_camera(self, camera_id: str, limit: int = 50) -> List[SearchResult]:
        """Retrieve all indexed crops for a given *camera_id*."""
        pipeline = self._ensure_ready()
        client = self.qdrant._ensure_client()

        from qdrant_client.http import models as qmodels

        results, _next = client.scroll(
            collection_name=self.qdrant.collection_name,
            scroll_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="camera_id",
                        match=qmodels.MatchValue(value=camera_id),
                    )
                ]
            ),
            limit=limit,
            with_vectors=False,
            with_payload=True,
        )

        parsed: List[SearchResult] = []
        for point in results:
            payload = point.payload or {}
            parsed.append(
                SearchResult(
                    score=1.0,
                    track_id=payload.get("track_id", -1),
                    camera_id=payload.get("camera_id", camera_id),
                    crop_path=payload.get("crop_path", ""),
                    timestamp=payload.get("timestamp", 0.0),
                    payload=payload,
                )
            )

        logger.info(
            "Camera search completed",
            extra={"camera_id": camera_id, "results": len(parsed)},
        )
        return parsed

    # ── Formatting Helpers ───────────────────────────────────────────────

    @staticmethod
    def format_results(results: List[SearchResult]) -> str:
        """Produce a human-readable table from a list of search results."""
        if not results:
            return "  No results found."

        lines = [
            f"  {'#':<4} {'Track':<10} {'Camera':<12} {'Timestamp':<12} {'Similarity':<12} {'Crop Path'}",
            f"  {'─'*4} {'─'*10} {'─'*12} {'─'*12} {'─'*12} {'─'*30}",
        ]
        for i, r in enumerate(results, 1):
            ts = f"{r.timestamp:.2f}s"
            sim = f"{r.score:.4f}"
            lines.append(
                f"  {i:<4} {r.track_id:<10} {r.camera_id:<12} {ts:<12} {sim:<12} {r.crop_path}"
            )
        return "\n".join(lines)

    @staticmethod
    def results_to_dict(results: List[SearchResult]) -> List[dict[str, Any]]:
        """Serialise results to plain dicts (JSON-safe)."""
        return [r.model_dump() for r in results]

    def save_results(
        self,
        results: List[SearchResult],
        query: str,
        output_path: str | Path | None = None,
    ) -> Path:
        """Write search results to a JSON file.

        Args:
            results: The search results to persist.
            query: The original query string.
            output_path: Destination file. Defaults to
                ``data/outputs/search_results.json``.

        Returns:
            The path to the written file.
        """
        if output_path is None:
            output_path = Path("data/outputs/search_results.json")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "query": query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_results": len(results),
            "results": self.results_to_dict(results),
        }
        output_path.write_text(json.dumps(payload, indent=2, default=str))
        logger.info("Search results saved", extra={"path": str(output_path)})
        return output_path
