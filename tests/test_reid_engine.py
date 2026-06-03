"""
Tests for the FastReID Engine.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
from PIL import Image

from backend.reid.reid_engine import ReIDEngine, ReIDEngineError


@pytest.fixture
def engine() -> ReIDEngine:
    e = ReIDEngine()
    # We use the mock mode for unit testing to avoid requiring actual FastReID weights
    e.load_model(mock_for_testing=True)
    return e


class TestReIDEngine:
    def test_initialization(self) -> None:
        """Test engine can be initialized with default devices."""
        e = ReIDEngine()
        assert e.device.type in ["cpu", "cuda", "mps"]
        assert e.model is None

    def test_load_mock_model(self, engine: ReIDEngine) -> None:
        """Test mock model loading populates the model."""
        assert engine.model is not None
        assert isinstance(engine.model, torch.nn.Module)
        
    def test_extract_embedding_numpy(self, engine: ReIDEngine) -> None:
        """Test extraction from a NumPy array."""
        image = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)
        embedding = engine.extract_embedding(image)
        
        # ResNet18 raw features dimension is 512
        assert embedding.shape == (512,)
        # Check L2 normalization
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-4)

    def test_extract_embedding_pil(self, engine: ReIDEngine) -> None:
        """Test extraction from a PIL Image."""
        image_np = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)
        image_pil = Image.fromarray(image_np)
        
        embedding = engine.extract_embedding(image_pil)
        assert embedding.shape == (512,)

    def test_uninitialized_raises(self) -> None:
        """Extracting before loading raises an error."""
        e = ReIDEngine()
        image = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)
        with pytest.raises(ReIDEngineError, match="Model not loaded"):
            e.extract_embedding(image)
