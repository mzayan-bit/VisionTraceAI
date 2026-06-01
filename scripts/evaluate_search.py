#!/usr/bin/env python3
"""
VisionTraceAI — Search Quality Evaluation.

Runs a suite of predefined evaluation queries and records the top-10
matches for each. Outputs a structured JSON report.

Usage::

    uv run python scripts/evaluate_search.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image

from app.models.tracking import BoundingBox, CropMetadata
from app.services.search_engine import VisionSearchEngine
from app.utils.logger import get_logger

logger = get_logger("scripts.evaluate_search")

OUTPUT_PATH = Path("data/outputs/search_evaluation.json")

EVAL_QUERIES = [
    "person wearing backpack",
    "person in white shirt",
    "person wearing dark clothes",
    "person walking",
    "person facing camera",
]


def seed_engine(engine: VisionSearchEngine, n: int = 30) -> int:
    """Insert synthetic crops into the engine for evaluation."""
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    pipeline = engine._ensure_ready()
    count = 0

    for i in range(n):
        img = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )
        p = tmp / f"eval_crop_{i}.jpg"
        img.save(p)
        meta = CropMetadata(
            camera_id=f"cam_{i % 3 + 1}",
            track_id=i,
            frame_number=i * 10,
            timestamp=i * 0.33,
            crop_path=str(p),
            bbox=BoundingBox(x1=10, y1=10, x2=200, y2=400),
        )
        try:
            pipeline.ingest_crop(meta)
            count += 1
        except Exception as exc:
            logger.warning(f"Seed failed for crop {i}: {exc}")

    return count


def main() -> int:
    print("=" * 64)
    print("  🔬 VisionTraceAI — Search Quality Evaluation")
    print("=" * 64)

    engine = VisionSearchEngine()
    engine.initialize(use_memory=True)

    print("\n  [1/3] Seeding evaluation corpus...")
    n_seeded = seed_engine(engine)
    print(f"        ✅ {n_seeded} vectors indexed")

    print("\n  [2/3] Running evaluation queries...")
    report = {
        "total_queries": len(EVAL_QUERIES),
        "vectors_in_collection": n_seeded,
        "queries": [],
    }

    for query in EVAL_QUERIES:
        t0 = time.perf_counter()
        results = engine.search(query, limit=10)
        latency = time.perf_counter() - t0

        entry = {
            "query": query,
            "latency_ms": round(latency * 1000, 2),
            "num_results": len(results),
            "top_scores": [round(r.score, 4) for r in results[:5]],
            "results": [
                {
                    "rank": i + 1,
                    "score": round(r.score, 4),
                    "track_id": r.track_id,
                    "camera_id": r.camera_id,
                    "timestamp": r.timestamp,
                    "crop_path": r.crop_path,
                }
                for i, r in enumerate(results)
            ],
        }
        report["queries"].append(entry)

        print(f"\n    Query: \"{query}\"")
        print(f"    Results: {len(results)} | Latency: {latency * 1000:.1f}ms")
        if results:
            print(f"    Top Score: {results[0].score:.4f} | Track: {results[0].track_id}")

    print("\n  [3/3] Saving evaluation report...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"        💾 Saved → {OUTPUT_PATH}")

    engine.shutdown()
    print("\n" + "=" * 64)
    print("  ✅ Search evaluation complete")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
