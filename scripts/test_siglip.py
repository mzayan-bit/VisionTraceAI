#!/usr/bin/env python3
"""
VisionTraceAI — SigLIP Test & Benchmark Script.

Loads the SigLIP semantic embedding engine and runs benchmark tests
to report dimension, L2 norm, and latencies for text/image pairs.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.embedder import SigLIPEmbeddingService
from app.utils.logger import get_logger

logger = get_logger("scripts.test_siglip")


def main() -> int:
    print("=" * 60)
    print("  🧠 VisionTraceAI — SigLIP Embedding Test")
    print("=" * 60)

    try:
        service = SigLIPEmbeddingService()
        
        # 1. Initialization and Load Time
        print("\n  [1/4] Loading SigLIP Model...")
        t0 = time.time()
        service.initialize()
        load_time = time.time() - t0
        print(f"        ✅  Loaded in {load_time:.2f}s")
        print(f"        Device: {service.device}")
        
        # 2. Text Embedding
        print("\n  [2/4] Testing Text Embedding...")
        sample_text = "person wearing blue hoodie"
        print(f"        Query: '{sample_text}'")
        
        t0 = time.time()
        text_emb = service.encode_text(sample_text)
        text_time = time.time() - t0
        
        dim = text_emb.shape[0]
        norm = np.linalg.norm(text_emb)
        
        print(f"        ✅  Latency: {text_time*1000:.1f}ms")
        print(f"        Dimension: {dim}")
        print(f"        L2 Norm  : {norm:.4f}")
        
        # 3. Image Embedding
        print("\n  [3/4] Testing Image Embedding...")
        # Create a dummy image mimicking a person crop (224x224 RGB)
        dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        
        t0 = time.time()
        img_emb = service.encode_image(dummy_img)
        img_time = time.time() - t0
        
        dim_img = img_emb.shape[0]
        norm_img = np.linalg.norm(img_emb)
        
        print(f"        ✅  Latency: {img_time*1000:.1f}ms")
        print(f"        Dimension: {dim_img}")
        print(f"        L2 Norm  : {norm_img:.4f}")
        
        # 4. Batch Processing
        print("\n  [4/4] Testing Batch Processing...")
        batch_size = 4
        batch_texts = ["query " + str(i) for i in range(batch_size)]
        
        t0 = time.time()
        batch_emb = service.encode_texts(batch_texts)
        batch_time = time.time() - t0
        
        print(f"        ✅  Batch Size: {batch_size}")
        print(f"        Latency   : {batch_time*1000:.1f}ms ({(batch_time/batch_size)*1000:.1f}ms/item)")
        print(f"        Shape     : {batch_emb.shape}")
        
        print("\n" + "=" * 60)
        print("  ✅  All SigLIP tests passed!")
        print("=" * 60)
        
    except Exception as exc:
        logger.error("SigLIP test failed", extra={"error": str(exc)})
        print(f"\n        ❌  Test failed: {exc}")
        return 1
    finally:
        if 'service' in locals():
            service.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
