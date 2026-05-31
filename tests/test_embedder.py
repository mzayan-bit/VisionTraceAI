"""
Integration tests for VisionTraceAI SigLIP Embedding service.

Run with:
    pytest tests/test_embedder.py -v
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
from PIL import Image

from app.services.embedder import SigLIPEmbeddingService


@pytest.fixture(scope="module")
def embedder() -> SigLIPEmbeddingService:
    """Fixture providing an initialized SigLIP service."""
    service = SigLIPEmbeddingService()
    service.initialize()
    yield service
    service.shutdown()


class TestSigLIPInitialization:
    """Test service initialization and device handling."""

    def test_initialization(self, embedder: SigLIPEmbeddingService) -> None:
        """Test model and processor load successfully."""
        assert embedder.model is not None
        assert embedder.processor is not None
        assert "siglip-base" in embedder.model_name.lower()

    def test_uninitialized_raises(self) -> None:
        """Test methods raise errors if used before initialize()."""
        uninit = SigLIPEmbeddingService()
        with pytest.raises(RuntimeError, match="not initialized"):
            uninit.encode_text("test")

    def test_health_check(self, embedder: SigLIPEmbeddingService) -> None:
        """Test the health check output."""
        health = embedder.health_check()
        assert health["status"] == "healthy"
        assert health["model"] == embedder.model_name
        assert health["device"] == embedder.device


class TestEmbeddings:
    """Test image, text, and batch embeddings."""

    @pytest.fixture
    def dummy_image(self) -> Image.Image:
        """Return a random 224x224 RGB image."""
        arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        return Image.fromarray(arr)

    def test_encode_text_shape_and_type(self, embedder: SigLIPEmbeddingService) -> None:
        """Test basic text encoding."""
        emb = embedder.encode_text("A photo of a person")
        assert isinstance(emb, np.ndarray)
        assert emb.dtype == np.float32
        assert emb.shape == (768,)

    def test_encode_image_shape_and_type(self, embedder: SigLIPEmbeddingService, dummy_image: Image.Image) -> None:
        """Test basic image encoding."""
        emb = embedder.encode_image(dummy_image)
        assert isinstance(emb, np.ndarray)
        assert emb.dtype == np.float32
        assert emb.shape == (768,)

    def test_encode_image_numpy_array(self, embedder: SigLIPEmbeddingService) -> None:
        """Test image encoding passing a numpy array instead of PIL."""
        arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        emb = embedder.encode_image(arr)
        assert emb.shape == (768,)

    def test_batch_texts(self, embedder: SigLIPEmbeddingService) -> None:
        """Test encoding multiple texts at once."""
        texts = ["hello", "world", "vision"]
        embs = embedder.encode_texts(texts)
        assert isinstance(embs, np.ndarray)
        assert embs.shape == (3, 768)

    def test_batch_images(self, embedder: SigLIPEmbeddingService, dummy_image: Image.Image) -> None:
        """Test encoding multiple images at once."""
        images = [dummy_image, dummy_image]
        embs = embedder.encode_images(images)
        assert embs.shape == (2, 768)


class TestNormalization:
    """Test embedding normalization logic."""

    def test_text_normalization(self, embedder: SigLIPEmbeddingService) -> None:
        """Test that text embeddings are L2 normalized."""
        emb = embedder.encode_text("normalize me")
        norm = np.linalg.norm(emb)
        np.testing.assert_almost_equal(norm, 1.0, decimal=5)

    def test_image_normalization(self, embedder: SigLIPEmbeddingService) -> None:
        """Test that image embeddings are L2 normalized."""
        arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        emb = embedder.encode_image(arr)
        norm = np.linalg.norm(emb)
        np.testing.assert_almost_equal(norm, 1.0, decimal=5)

    def test_manual_normalization_1d(self, embedder: SigLIPEmbeddingService) -> None:
        """Test the normalization function directly on a 1D tensor."""
        vector = torch.tensor([3.0, 4.0])
        normed = embedder.normalize_embedding(vector)
        # 3-4-5 triangle, so should be 0.6, 0.8
        np.testing.assert_almost_equal(normed[0], 0.6, decimal=5)
        np.testing.assert_almost_equal(normed[1], 0.8, decimal=5)

    def test_manual_normalization_2d(self, embedder: SigLIPEmbeddingService) -> None:
        """Test the normalization function directly on a 2D batch."""
        vector = np.array([[3.0, 4.0], [0.0, -5.0]])
        normed = embedder.normalize_embedding(vector)
        np.testing.assert_almost_equal(normed[0, 0], 0.6, decimal=5)
        np.testing.assert_almost_equal(normed[1, 1], -1.0, decimal=5)
