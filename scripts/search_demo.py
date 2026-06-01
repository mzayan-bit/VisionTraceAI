#!/usr/bin/env python3
"""
VisionTraceAI — Interactive Search Console (Week 1 MVP Demo).

Provides a REPL-style CLI for querying the semantic memory:

    uv run python scripts/search_demo.py

Features:
    - Interactive text queries
    - Special commands:  /track <id>, /camera <id>, /top <k> <query>, /save, /quit
    - Automatic JSON export to data/outputs/search_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.search_engine import VisionSearchEngine
from app.utils.logger import get_logger

logger = get_logger("scripts.search_demo")

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║               🔍 VisionTraceAI Search Console               ║
║                      Week 1 MVP Demo                         ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:                                                   ║
║    <text>            Semantic search (e.g. "blue hoodie")    ║
║    /track <id>       Lookup by track ID                      ║
║    /camera <id>      Lookup by camera ID                     ║
║    /top <k> <query>  Return top-K results                    ║
║    /save             Save last results to JSON               ║
║    /help             Show this help                          ║
║    /quit             Exit                                    ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
  Available commands:

    <text>              Free-form semantic search.
                        Example: person wearing a red jacket

    /track <id>         Retrieve all indexed crops for a track ID.
                        Example: /track 17

    /camera <id>        Retrieve all indexed crops for a camera.
                        Example: /camera cam_1

    /top <k> <query>    Return exactly k results for a query.
                        Example: /top 3 person with backpack

    /save               Save the most recent results to
                        data/outputs/search_results.json

    /help               Show this help message.

    /quit               Exit the search console.
"""


def run_interactive(engine: VisionSearchEngine) -> None:
    """Main REPL loop."""
    print(BANNER)

    last_results = []
    last_query = ""

    while True:
        try:
            raw = input("\n  Enter query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not raw:
            continue

        # ── Slash commands ───────────────────────────────────────────
        if raw.lower() in ("/quit", "/exit", "/q"):
            print("  Goodbye!")
            break

        if raw.lower() in ("/help", "/h"):
            print(HELP_TEXT)
            continue

        if raw.lower() == "/save":
            if not last_results:
                print("  ⚠  No results to save. Run a search first.")
                continue
            path = engine.save_results(last_results, last_query)
            print(f"  💾 Saved {len(last_results)} results → {path}")
            continue

        if raw.lower().startswith("/track "):
            try:
                track_id = int(raw.split(None, 1)[1])
            except (ValueError, IndexError):
                print("  ⚠  Usage: /track <integer_id>")
                continue
            last_query = f"track:{track_id}"
            last_results = engine.search_by_track(track_id)
            _display(last_results, last_query, engine)
            continue

        if raw.lower().startswith("/camera "):
            try:
                camera_id = raw.split(None, 1)[1]
            except IndexError:
                print("  ⚠  Usage: /camera <camera_id>")
                continue
            last_query = f"camera:{camera_id}"
            last_results = engine.search_by_camera(camera_id)
            _display(last_results, last_query, engine)
            continue

        if raw.lower().startswith("/top "):
            parts = raw.split(None, 2)
            if len(parts) < 3:
                print("  ⚠  Usage: /top <k> <query>")
                continue
            try:
                k = int(parts[1])
            except ValueError:
                print("  ⚠  <k> must be an integer")
                continue
            query = parts[2]
            last_query = query
            last_results = engine.search_top_k(query, k=k)
            _display(last_results, last_query, engine)
            continue

        # ── Default: semantic search ─────────────────────────────────
        last_query = raw
        last_results = engine.search(raw)
        _display(last_results, last_query, engine)


def _display(
    results: list,
    query: str,
    engine: VisionSearchEngine,
) -> None:
    """Pretty-print search results to the terminal."""
    print(f"\n  📋 Results for: \"{query}\"\n")
    print(engine.format_results(results))
    print(f"\n  Total: {len(results)} match(es)")


def run_batch(engine: VisionSearchEngine, queries: list[str]) -> None:
    """Non-interactive batch mode — run a list of queries and print."""
    for q in queries:
        print(f"\n{'═' * 60}")
        print(f"  Query: \"{q}\"")
        print(f"{'═' * 60}")
        results = engine.search(q)
        print(engine.format_results(results))
        print(f"  Total: {len(results)} match(es)")
        engine.save_results(results, q)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="VisionTraceAI — Interactive Search Console"
    )
    parser.add_argument(
        "--batch",
        nargs="*",
        help='Run non-interactively with given queries (e.g. --batch "blue hoodie" "red jacket")',
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Use in-memory Qdrant (no server required)",
    )
    args = parser.parse_args()

    engine = VisionSearchEngine()

    try:
        print("  ⏳ Initializing search engine...")
        engine.initialize(use_memory=args.memory)
        print("  ✅ Search engine ready!\n")

        if args.batch is not None:
            run_batch(engine, args.batch)
        else:
            run_interactive(engine)

    except Exception as exc:
        logger.error("Search demo failed", extra={"error": str(exc)})
        print(f"\n  ❌ Error: {exc}")
        return 1
    finally:
        engine.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
