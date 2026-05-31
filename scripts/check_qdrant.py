#!/usr/bin/env python3
"""
VisionTraceAI — Qdrant Health Check Script.

Displays connection status, collection count, and collection names.

Usage:
    uv run python scripts/check_qdrant.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.database import QdrantService, QdrantServiceError  # noqa: E402


def main() -> int:
    print("=" * 60)
    print("  🔍 VisionTraceAI — Qdrant Health Check")
    print("=" * 60)

    qdrant = QdrantService()

    # 1. Connection
    print("\n  [1/3] Testing connection...")
    try:
        qdrant.connect()
        print(f"        ✅  Connected to {qdrant.host}:{qdrant.port}")
    except QdrantServiceError as exc:
        print(f"        ❌  Connection failed: {exc}")
        return 1

    # 2. Health check
    print("\n  [2/3] Running health check...")
    try:
        health = qdrant.health_check()
        print(f"        Status           : {health['status']}")
        print(f"        Collections Count: {health['collections_count']}")
    except QdrantServiceError as exc:
        print(f"        ❌  Health check failed: {exc}")
        return 1

    # 3. Collection listing
    print("\n  [3/3] Listing collections:")
    try:
        names = qdrant.list_collections()
        if names:
            for i, name in enumerate(names, 1):
                stats = qdrant.get_collection_stats(name)
                print(f"        {i}. {name}")
                print(f"           Status : {stats['status']}")
                print(f"           Vectors: {stats['vectors_count']}")
                print(f"           Dim    : {stats['vector_size']}")
        else:
            print("        (no collections)")
    except QdrantServiceError as exc:
        print(f"        ❌  Listing failed: {exc}")
        return 1

    print("\n" + "=" * 60)
    print("  ✅  Health check passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
