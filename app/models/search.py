"""
VisionTraceAI — Search Data Models.

Defines Pydantic schemas for semantic search results.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Result from a vector similarity search."""
    score: float = Field(..., description="Cosine similarity score")
    track_id: int = Field(..., description="Persistent tracking ID")
    camera_id: str = Field(..., description="Source camera identifier")
    crop_path: str = Field(..., description="Path to the saved crop image")
    timestamp: float = Field(..., description="Timestamp in seconds from video start")
    payload: dict[str, Any] = Field(default_factory=dict, description="Full Qdrant payload")
