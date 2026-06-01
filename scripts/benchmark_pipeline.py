#!/usr/bin/env python3
"""
VisionTraceAI — End-to-End Pipeline Benchmark.

Measures latency and throughput of every pipeline stage:
  1. YOLO11 tracking
  2. Crop extraction
  3. SigLIP embedding
  4. Qdrant insertion
  5. Search latency

Usage::

    uv run python scripts/benchmark_pipeline.py data/videos/sample.mp4
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from PIL import Image

from app.core.tracker import VisionTracker
from app.pipelines.cropper import PersonCropPipeline
from app.pipelines.vector_pipeline import SemanticMemoryPipeline
from app.services.database import QdrantService
from app.services.embedder import SigLIPEmbeddingService
from app.services.search_engine import VisionSearchEngine
from app.utils.logger import get_logger

logger = get_logger("scripts.benchmark_pipeline")

OUTPUT_PATH = Path("data/outputs/benchmark_results.json")


def _fmt_ms(seconds: float) -> str:
    return f"{seconds * 1000:.1f}ms"


def benchmark_tracking(video_path: str) -> dict:
    """Benchmark YOLO11 + ByteTrack tracking."""
    tracker = VisionTracker()
    tracker.initialize_model()

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    tracemalloc.start()
    start = time.time()
    frame_times = []
    tracks_detected = 0
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ts = frame_num / fps if fps > 0 else 0.0
        t0 = time.perf_counter()
        res, _ = tracker.track_frame(frame, frame_num, ts)
        frame_times.append(time.perf_counter() - t0)
        tracks_detected += len(res.tracks)
        frame_num += 1

    elapsed = time.time() - start
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cap.release()
    tracker.shutdown()

    avg_ms = (sum(frame_times) / len(frame_times) * 1000) if frame_times else 0
    process_fps = frame_num / elapsed if elapsed > 0 else 0

    return {
        "stage": "YOLO11 + ByteTrack Tracking",
        "total_frames": frame_num,
        "total_time_sec": round(elapsed, 3),
        "avg_ms_per_frame": round(avg_ms, 2),
        "processing_fps": round(process_fps, 2),
        "tracks_detected": tracks_detected,
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
    }


def benchmark_cropping(video_path: str) -> dict:
    """Benchmark crop extraction pipeline."""
    tracker = VisionTracker()
    tracker.initialize_model()
    cropper = PersonCropPipeline(blur_threshold=50.0)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_num = 0
    crop_times = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ts = frame_num / fps if fps > 0 else 0.0
        res, _ = tracker.track_frame(frame, frame_num, ts)
        for track in res.tracks:
            t0 = time.perf_counter()
            cropper.process_track(frame, track, "cam_bench", frame_num, ts)
            crop_times.append(time.perf_counter() - t0)
        frame_num += 1

    cap.release()
    tracker.shutdown()

    avg_ms = (sum(crop_times) / len(crop_times) * 1000) if crop_times else 0
    return {
        "stage": "Crop Extraction",
        "total_crops_processed": len(crop_times),
        "saved_crops": cropper.saved_crops,
        "rejected_crops": cropper.rejected_zero_size + cropper.rejected_invalid_coords + cropper.rejected_blur,
        "avg_ms_per_crop": round(avg_ms, 2),
        "total_time_ms": round(sum(crop_times) * 1000, 2),
    }


def benchmark_embedding() -> dict:
    """Benchmark SigLIP embedding generation."""
    embedder = SigLIPEmbeddingService()
    embedder.initialize()

    # Generate synthetic test images
    test_images = [
        Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        for _ in range(10)
    ]
    test_texts = [
        "person wearing backpack",
        "person in white shirt",
        "person walking",
        "person facing camera",
        "person wearing dark clothes",
    ]

    # Image embedding benchmark
    img_times = []
    for img in test_images:
        t0 = time.perf_counter()
        embedder.encode_image(img)
        img_times.append(time.perf_counter() - t0)

    # Text embedding benchmark
    txt_times = []
    for txt in test_texts:
        t0 = time.perf_counter()
        embedder.encode_text(txt)
        txt_times.append(time.perf_counter() - t0)

    # Batch benchmark
    t0 = time.perf_counter()
    embedder.encode_images(test_images)
    batch_img_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    embedder.encode_texts(test_texts)
    batch_txt_time = time.perf_counter() - t0

    embedder.shutdown()

    return {
        "stage": "SigLIP Embedding",
        "single_image_avg_ms": round(sum(img_times) / len(img_times) * 1000, 2),
        "single_text_avg_ms": round(sum(txt_times) / len(txt_times) * 1000, 2),
        "batch_images_10_ms": round(batch_img_time * 1000, 2),
        "batch_texts_5_ms": round(batch_txt_time * 1000, 2),
        "image_throughput_per_sec": round(len(test_images) / batch_img_time, 2),
        "text_throughput_per_sec": round(len(test_texts) / batch_txt_time, 2),
    }


def benchmark_qdrant() -> dict:
    """Benchmark Qdrant insertion and search."""
    qdrant = QdrantService()
    qdrant.connect_memory()
    qdrant.create_collection()

    dim = 768
    n_vectors = 100

    # Insertion benchmark
    vectors = [np.random.rand(dim).astype(np.float32).tolist() for _ in range(n_vectors)]
    payloads = [{"track_id": i, "camera_id": "cam_bench"} for i in range(n_vectors)]

    t0 = time.perf_counter()
    qdrant.insert_batch(vectors=vectors, payloads=payloads)
    insert_time = time.perf_counter() - t0

    # Search benchmark
    search_times = []
    for _ in range(20):
        q = np.random.rand(dim).astype(np.float32).tolist()
        t0 = time.perf_counter()
        qdrant.search(query_vector=q, top_k=10)
        search_times.append(time.perf_counter() - t0)

    avg_search_ms = sum(search_times) / len(search_times) * 1000

    return {
        "stage": "Qdrant Vector DB",
        "vectors_inserted": n_vectors,
        "batch_insert_ms": round(insert_time * 1000, 2),
        "avg_insert_per_vector_ms": round(insert_time / n_vectors * 1000, 3),
        "avg_search_ms": round(avg_search_ms, 2),
        "search_throughput_per_sec": round(1000 / avg_search_ms, 2) if avg_search_ms > 0 else 0,
    }


def benchmark_search() -> dict:
    """Benchmark end-to-end search latency."""
    engine = VisionSearchEngine()
    engine.initialize(use_memory=True)

    # Seed with dummy data
    from app.models.tracking import BoundingBox, CropMetadata
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    for i in range(20):
        img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        p = tmp / f"crop_{i}.jpg"
        img.save(p)
        meta = CropMetadata(
            camera_id="cam_bench", track_id=i, frame_number=i * 10,
            timestamp=i * 0.5, crop_path=str(p),
            bbox=BoundingBox(x1=0, y1=0, x2=50, y2=100),
        )
        engine.pipeline.ingest_crop(meta)

    queries = [
        "person wearing backpack",
        "person in white shirt",
        "person walking",
        "person facing camera",
        "person wearing dark clothes",
    ]

    search_times = []
    for q in queries:
        t0 = time.perf_counter()
        engine.search(q, limit=10)
        search_times.append(time.perf_counter() - t0)

    engine.shutdown()

    avg_ms = sum(search_times) / len(search_times) * 1000
    return {
        "stage": "End-to-End Search",
        "queries_run": len(queries),
        "avg_search_latency_ms": round(avg_ms, 2),
        "min_search_latency_ms": round(min(search_times) * 1000, 2),
        "max_search_latency_ms": round(max(search_times) * 1000, 2),
        "total_search_time_ms": round(sum(search_times) * 1000, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VisionTraceAI — Pipeline Benchmark")
    parser.add_argument("video_path", nargs="?", default="data/videos/sample.mp4",
                        help="Path to input video")
    args = parser.parse_args()

    print("=" * 64)
    print("  ⚡ VisionTraceAI — End-to-End Pipeline Benchmark")
    print("=" * 64)

    results = {}

    stages = [
        ("Tracking", lambda: benchmark_tracking(args.video_path)),
        ("Cropping", lambda: benchmark_cropping(args.video_path)),
        ("Embedding", benchmark_embedding),
        ("Qdrant", benchmark_qdrant),
        ("Search", benchmark_search),
    ]

    for name, fn in stages:
        print(f"\n  [{name}] Running...")
        try:
            data = fn()
            results[name.lower()] = data
            for k, v in data.items():
                if k == "stage":
                    print(f"    📊 {v}")
                else:
                    print(f"       {k:<30} {v}")
        except Exception as exc:
            print(f"    ❌ Failed: {exc}")
            results[name.lower()] = {"stage": name, "error": str(exc)}

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2, default=str))

    print(f"\n  💾 Results saved → {OUTPUT_PATH}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
