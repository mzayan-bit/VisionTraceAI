"""Services module — business logic and domain services."""

from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService


def __getattr__(name: str):  # noqa: N807
    """Lazy-load VisionSearchEngine to avoid a circular import."""
    if name == "VisionSearchEngine":
        from app.services.search_engine import VisionSearchEngine
        return VisionSearchEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["QdrantService", "SigLIPEmbeddingService", "VisionSearchEngine"]
