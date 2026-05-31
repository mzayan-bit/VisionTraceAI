"""
VisionTraceAI — Tracking Data Models.

Defines Pydantic schemas for object tracking results.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates in [x1, y1, x2, y2] format."""
    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.width / 2, self.y1 + self.height / 2)


class TrackResult(BaseModel):
    """Result for a single tracked object in a frame."""
    track_id: int = Field(..., description="Persistent tracking ID")
    confidence: float = Field(..., description="Detection confidence score")
    bbox: BoundingBox = Field(..., description="Bounding box of the object")


class FrameResult(BaseModel):
    """Collection of track results for a single frame."""
    frame_number: int = Field(..., description="Frame sequence number")
    timestamp: float = Field(..., description="Timestamp in seconds from video start")
    tracks: list[TrackResult] = Field(default_factory=list, description="List of tracked objects")


class VideoResult(BaseModel):
    """Complete tracking results for a video."""
    video_path: str = Field(..., description="Path or identifier of the source video")
    total_frames: int = Field(..., description="Total number of frames processed")
    fps: float = Field(..., description="Frames per second of the source video")
    processing_time_sec: float = Field(..., description="Total processing time in seconds")
    frames: list[FrameResult] = Field(default_factory=list, description="Frame-by-frame tracking results")
