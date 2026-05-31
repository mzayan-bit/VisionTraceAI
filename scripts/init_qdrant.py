#!/usr/bin/env python3
"""
VisionTraceAI — Qdrant Initialization Script.

Connects to Qdrant, creates the default collection if missing,
verifies it, and prints diagnostics.

Usage:
    uv run python scripts/init_qdrant.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import get_settings  # noqa: E402
from app.services.database import QdrantService, QdrantServiceError  # noqa: E402


def main() -> int:
    settings = get_settings()

    print("=" * 60)
    print("  🔍 VisionTraceAI — Qdrant Initialization")
    print("=" * 60)
    print(f"  Host       : {settings.qdrant_host}")
    print(f"  Port       : {settings.qdrant_port}")
    print(f"  Collection : {settings.qdrant_collection_name}")
    print(f"  Vector Size: {QdrantService.DEFAULT_VECTOR_SIZE}")
    print(f"  Distance   : {QdrantService.DEFAULT_DISTANCE.value}")
    print("─" * 60)

    qdrant = QdrantService()

    # 1. Connect
    print("\n  [1/4] Connecting to Qdrant...")
    try:
        qdrant.connect()
        print("        ✅  Connected successfully")
    except QdrantServiceError as exc:
        print(f"        ❌  Connection failed: {exc}")
        return 1

    # 2. Create collection
    print("\n  [2/4] Creating collection...")
    try:
        created = qdrant.create_collection(skip_if_exists=True)
        if created:
            print(f"        ✅  Collection '{settings.qdrant_collection_name}' created")
        else:
            print(f"        ⏭️   Collection '{settings.qdrant_collection_name}' already exists")
    except QdrantServiceError as exc:
        print(f"        ❌  Creation failed: {exc}")
        return 1

    # 3. Verify
    print("\n  [3/4] Verifying collection...")
    try:
        exists = qdrant.collection_exists()
        if exists:
            print(f"        ✅  Collection '{settings.qdrant_collection_name}' verified")
        else:
            print(f"        ❌  Collection not found after creation!")
            return 1
    except QdrantServiceError as exc:
        print(f"        ❌  Verification failed: {exc}")
        return 1

    # 4. Print diagnostics
    print("\n  [4/4] Collection diagnostics:")
    try:
        stats = qdrant.get_collection_stats()
        print(f"        Name         : {stats['collection_name']}")
        print(f"        Status       : {stats['status']}")
        print(f"        Vector Size  : {stats['vector_size']}")
        print(f"        Points Count : {stats['points_count']}")
        print(f"        Segments     : {stats['segments_count']}")
    except QdrantServiceError as exc:
        print(f"        ❌  Diagnostics failed: {exc}")
        return 1

    print("\n" + "=" * 60)
    print("  ✅  Qdrant initialization complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
