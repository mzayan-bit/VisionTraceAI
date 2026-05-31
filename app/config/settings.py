"""
VisionTraceAI — Centralized Configuration Management.

Uses pydantic-settings to load, validate, and expose typed configuration
from environment variables and .env files.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Resolve project root (two levels up from this file: app/config/settings.py)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file.

    All values have sensible defaults for local development.
    Override them via environment variables or a ``.env`` file at the
    project root.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Project ──────────────────────────────────────────────────────────
    project_name: str = Field(
        default="VisionTraceAI",
        description="Display name of the project.",
    )

    # ── Qdrant Vector DB ─────────────────────────────────────────────────
    qdrant_host: str = Field(
        default="localhost",
        description="Hostname or IP of the Qdrant vector database.",
    )
    qdrant_port: int = Field(
        default=6333,
        ge=1,
        le=65535,
        description="Port of the Qdrant gRPC/HTTP API.",
    )
    qdrant_collection_name: str = Field(
        default="visiontrace_embeddings",
        description="Default Qdrant collection name for storing embeddings.",
    )

    # ── Device ───────────────────────────────────────────────────────────
    device: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description="Compute device for model inference.",
    )

    # ── AI Models ────────────────────────────────────────────────────────
    yolo_model: str = Field(
        default="yolo11n.pt",
        description="YOLO model variant or path to weights file.",
    )
    siglip_model: str = Field(
        default="google/siglip-base-patch16-224",
        description="SigLIP model identifier (HuggingFace hub ID or local path).",
    )

    # ── Validators ───────────────────────────────────────────────────────
    @field_validator("device", mode="before")
    @classmethod
    def _normalise_device(cls, v: str) -> str:
        """Accept mixed-case device strings like 'CUDA' or 'Cpu'."""
        return v.strip().lower()

    @field_validator("qdrant_host", mode="before")
    @classmethod
    def _strip_host(cls, v: str) -> str:
        """Strip whitespace and trailing slashes from host."""
        return v.strip().rstrip("/")

    @field_validator("yolo_model", "siglip_model", mode="before")
    @classmethod
    def _strip_model(cls, v: str) -> str:
        """Strip whitespace from model identifiers."""
        return v.strip()

    # ── Convenience ──────────────────────────────────────────────────────
    @property
    def qdrant_url(self) -> str:
        """Full Qdrant HTTP URL assembled from host + port."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    def print_summary(self, file: object = sys.stdout) -> None:
        """Print a human-readable configuration summary."""
        border = "─" * 52
        print(f"\n┌{border}┐", file=file)  # noqa: T201
        print(f"│  🔍  {self.project_name} — Configuration Summary", file=file)  # noqa: T201
        print(f"├{border}┤", file=file)  # noqa: T201
        print(f"│  Project Name  : {self.project_name}", file=file)  # noqa: T201
        print(f"│  Device        : {self.device}", file=file)  # noqa: T201
        print(f"│  YOLO Model    : {self.yolo_model}", file=file)  # noqa: T201
        print(f"│  SigLIP Model  : {self.siglip_model}", file=file)  # noqa: T201
        print(f"│  Qdrant Host   : {self.qdrant_host}", file=file)  # noqa: T201
        print(f"│  Qdrant Port   : {self.qdrant_port}", file=file)  # noqa: T201
        print(f"│  Qdrant Coll.  : {self.qdrant_collection_name}", file=file)  # noqa: T201
        print(f"│  Qdrant URL    : {self.qdrant_url}", file=file)  # noqa: T201
        print(f"└{border}┘\n", file=file)  # noqa: T201


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, validated ``Settings`` singleton.

    Subsequent calls return the same instance without re-reading the
    environment, making this safe to call from hot paths.
    """
    return Settings()
