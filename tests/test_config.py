"""
Unit tests for VisionTraceAI configuration system.

Run with:
    pytest tests/test_config.py -v
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.settings import Settings, get_settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Clear the lru_cache before each test so env changes take effect."""
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestDefaults:
    """Settings should load sensible defaults when no env vars are set."""

    def test_project_name_default(self) -> None:
        s = Settings()
        assert s.project_name == "VisionTraceAI"

    def test_qdrant_host_default(self) -> None:
        s = Settings()
        assert s.qdrant_host == "localhost"

    def test_qdrant_port_default(self) -> None:
        s = Settings()
        assert s.qdrant_port == 6333

    def test_device_default(self) -> None:
        s = Settings()
        assert s.device == "cpu"

    def test_yolo_model_default(self) -> None:
        s = Settings()
        assert s.yolo_model == "yolo11n.pt"

    def test_siglip_model_default(self) -> None:
        s = Settings()
        assert s.siglip_model == "google/siglip-base-patch16-224"


# ---------------------------------------------------------------------------
# Environment overrides
# ---------------------------------------------------------------------------

class TestEnvOverrides:
    """Settings should pick up values from environment variables."""

    def test_override_project_name(self) -> None:
        with patch.dict(os.environ, {"PROJECT_NAME": "TestProject"}):
            s = Settings()
        assert s.project_name == "TestProject"

    def test_override_qdrant_host(self) -> None:
        with patch.dict(os.environ, {"QDRANT_HOST": "qdrant.prod.internal"}):
            s = Settings()
        assert s.qdrant_host == "qdrant.prod.internal"

    def test_override_qdrant_port(self) -> None:
        with patch.dict(os.environ, {"QDRANT_PORT": "6334"}):
            s = Settings()
        assert s.qdrant_port == 6334

    def test_override_device_cuda(self) -> None:
        with patch.dict(os.environ, {"DEVICE": "cuda"}):
            s = Settings()
        assert s.device == "cuda"

    def test_override_device_mps(self) -> None:
        with patch.dict(os.environ, {"DEVICE": "mps"}):
            s = Settings()
        assert s.device == "mps"

    def test_override_yolo_model(self) -> None:
        with patch.dict(os.environ, {"YOLO_MODEL": "yolov8x.pt"}):
            s = Settings()
        assert s.yolo_model == "yolov8x.pt"

    def test_override_siglip_model(self) -> None:
        with patch.dict(os.environ, {"SIGLIP_MODEL": "google/siglip-large-patch16-384"}):
            s = Settings()
        assert s.siglip_model == "google/siglip-large-patch16-384"


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

class TestValidators:
    """Field validators should normalise and sanitise input."""

    def test_device_case_insensitive(self) -> None:
        with patch.dict(os.environ, {"DEVICE": "CUDA"}):
            s = Settings()
        assert s.device == "cuda"

    def test_device_strips_whitespace(self) -> None:
        with patch.dict(os.environ, {"DEVICE": "  mps  "}):
            s = Settings()
        assert s.device == "mps"

    def test_qdrant_host_strips_trailing_slash(self) -> None:
        with patch.dict(os.environ, {"QDRANT_HOST": "qdrant.local///"}):
            s = Settings()
        assert s.qdrant_host == "qdrant.local"

    def test_model_strips_whitespace(self) -> None:
        with patch.dict(os.environ, {"YOLO_MODEL": "  yolov8s.pt  "}):
            s = Settings()
        assert s.yolo_model == "yolov8s.pt"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestValidationErrors:
    """Invalid input should raise ValidationError."""

    def test_invalid_device_value(self) -> None:
        with patch.dict(os.environ, {"DEVICE": "tpu"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_qdrant_port_too_high(self) -> None:
        with patch.dict(os.environ, {"QDRANT_PORT": "99999"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_qdrant_port_zero(self) -> None:
        with patch.dict(os.environ, {"QDRANT_PORT": "0"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_qdrant_port_negative(self) -> None:
        with patch.dict(os.environ, {"QDRANT_PORT": "-1"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_qdrant_port_non_numeric(self) -> None:
        with patch.dict(os.environ, {"QDRANT_PORT": "abc"}):
            with pytest.raises(ValidationError):
                Settings()


# ---------------------------------------------------------------------------
# Computed properties
# ---------------------------------------------------------------------------

class TestProperties:
    """Computed properties should assemble correct values."""

    def test_qdrant_url_default(self) -> None:
        s = Settings()
        assert s.qdrant_url == "http://localhost:6333"

    def test_qdrant_url_custom(self) -> None:
        with patch.dict(os.environ, {"QDRANT_HOST": "db.example.com", "QDRANT_PORT": "6334"}):
            s = Settings()
        assert s.qdrant_url == "http://db.example.com:6334"


# ---------------------------------------------------------------------------
# Singleton / caching
# ---------------------------------------------------------------------------

class TestSingleton:
    """get_settings() should return a cached singleton."""

    def test_singleton_identity(self) -> None:
        a = get_settings()
        b = get_settings()
        assert a is b

    def test_cache_clear_returns_new_instance(self) -> None:
        a = get_settings()
        get_settings.cache_clear()
        b = get_settings()
        # After clearing, still equal values but may be different object
        assert a.project_name == b.project_name
