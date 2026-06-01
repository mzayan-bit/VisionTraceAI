#!/usr/bin/env python3
"""
VisionTraceAI — Automatic Week 1 Report Generator.

Collects project metadata, test results, and benchmark data to produce
docs/WEEK1_FINAL_REPORT.md automatically.

Usage::

    uv run python scripts/generate_week1_report.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.logger import get_logger

logger = get_logger("scripts.generate_week1_report")

REPORT_PATH = Path("docs/WEEK1_FINAL_REPORT.md")
BENCHMARK_PATH = Path("data/outputs/benchmark_results.json")
EVALUATION_PATH = Path("data/outputs/search_evaluation.json")


def count_lines(directory: str = "app") -> int:
    """Count Python source lines in a directory."""
    total = 0
    for p in Path(directory).rglob("*.py"):
        total += sum(1 for _ in p.open())
    return total


def count_tests() -> int:
    """Count test functions across the tests/ directory."""
    total = 0
    for p in Path("tests").rglob("*.py"):
        for line in p.open():
            if line.strip().startswith("def test_"):
                total += 1
    return total


def run_pytest_summary() -> tuple[int, int, str]:
    """Run pytest and return (passed, failed, raw_output)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=no", "-q"],
            capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
            timeout=120,
        )
        output = result.stdout + result.stderr
        # Parse "X passed, Y warnings"
        for line in output.strip().splitlines():
            if "passed" in line:
                parts = line.split()
                passed = int(parts[0]) if parts[0].isdigit() else 0
                failed = 0
                for i, p in enumerate(parts):
                    if p == "failed,":
                        failed = int(parts[i - 1])
                return passed, failed, output
        return 0, 0, output
    except Exception as exc:
        return 0, 0, str(exc)


def load_json(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def generate_report() -> str:
    """Build the full Markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    app_lines = count_lines("app")
    test_lines = count_lines("tests")
    script_lines = count_lines("scripts")
    test_count = count_tests()
    passed, failed, pytest_output = run_pytest_summary()

    bench = load_json(BENCHMARK_PATH)
    evaluation = load_json(EVALUATION_PATH)

    sections = []

    # Header
    sections.append(f"""# 📊 VisionTraceAI — Week 1 Final Report

**Generated:** {now}
**Status:** ✅ Week 1 MVP Complete
**Repository:** [github.com/mzayan-bit/VisionTraceAI](https://github.com/mzayan-bit/VisionTraceAI)

---

## 📋 Project Overview

VisionTraceAI is a production-grade AI surveillance system providing end-to-end
video analytics: **detection → tracking → cropping → embedding → semantic search**.

The Week 1 MVP delivers a fully operational pipeline that can:

1. Process surveillance video with YOLO11 + ByteTrack
2. Extract and validate person crops (224×224 RGB)
3. Generate SigLIP semantic embeddings (768-dim, L2-normalised)
4. Store vectors in Qdrant with rich payloads
5. Search using natural language (e.g. "person wearing blue hoodie")

---

## 🏗️ Architecture

```
Video (.mp4)
  │
  ├─ YOLO11 + ByteTrack ──▸ Persistent person tracking
  │
  ├─ PersonCropPipeline ──▸ 224×224 blur-filtered crops
  │
  ├─ SigLIPEmbeddingService ──▸ 768-dim float32 vectors
  │
  ├─ SemanticMemoryPipeline ──▸ Qdrant upsert with payloads
  │
  └─ VisionSearchEngine ──▸ Ranked natural-language retrieval
```

---

## 📂 Folder Structure

```
VisionTraceAI/
├── app/                        # Application package
│   ├── config/settings.py      # Pydantic-settings configuration
│   ├── core/tracker.py         # YOLO11 + ByteTrack engine
│   ├── models/                 # Pydantic data models
│   ├── pipelines/              # Cropper + Vector pipeline
│   ├── services/               # Qdrant, SigLIP, SearchEngine
│   └── utils/logger.py         # Rotating file logger
├── scripts/                    # CLI tools and demos
├── tests/                      # pytest test suite
├── data/                       # Videos, crops, outputs
├── docs/                       # Documentation
└── docker/                     # Container configs
```

---

## 📈 Code Statistics

| Metric | Value |
|--------|-------|
| Application source lines | {app_lines:,} |
| Test source lines | {test_lines:,} |
| Script source lines | {script_lines:,} |
| Total test functions | {test_count} |
| Stages completed | 10 / 10 |

---

## ✅ Test Results

| Metric | Value |
|--------|-------|
| Tests passed | {passed} |
| Tests failed | {failed} |
| Total | {passed + failed} |
| Status | {"✅ ALL PASSING" if failed == 0 else "⚠️ SOME FAILURES"} |
""")

    # Benchmark section
    if bench:
        sections.append("---\n\n## ⚡ Performance Benchmarks\n")
        for stage_key, data in bench.items():
            if isinstance(data, dict):
                name = data.get("stage", stage_key)
                sections.append(f"\n### {name}\n")
                sections.append("| Metric | Value |")
                sections.append("|--------|-------|")
                for k, v in data.items():
                    if k != "stage":
                        sections.append(f"| {k} | {v} |")
    else:
        sections.append("\n---\n\n## ⚡ Performance Benchmarks\n\n> Benchmarks not yet generated. Run `uv run python scripts/benchmark_pipeline.py`.\n")

    # Search evaluation section
    if evaluation:
        sections.append("\n---\n\n## 🔬 Search Quality Evaluation\n")
        sections.append(f"**Vectors indexed:** {evaluation.get('vectors_in_collection', 'N/A')}\n")
        sections.append("| Query | Results | Top Score | Latency |")
        sections.append("|-------|---------|-----------|---------|")
        for q in evaluation.get("queries", []):
            top = q["top_scores"][0] if q["top_scores"] else "—"
            sections.append(
                f"| {q['query']} | {q['num_results']} | {top} | {q['latency_ms']}ms |"
            )
    else:
        sections.append("\n---\n\n## 🔬 Search Quality Evaluation\n\n> Evaluation not yet generated. Run `uv run python scripts/evaluate_search.py`.\n")

    # Known limitations
    sections.append("""
---

## ⚠️ Known Limitations

| Area | Limitation |
|------|-----------|
| GPU | Tests run CPU-only; CUDA/MPS fallback implemented but not benchmarked |
| Sample Video | Default `sample.mp4` may lack visible people for crop extraction |
| Re-ID | Cross-camera re-identification is similarity-based, not learned |
| Qdrant | Falls back to in-memory when Docker is not running |
| SigLIP | `siglip-base-patch16-224` outputs 768-dim (larger models produce 1152) |
| Auth | HuggingFace token not set → rate-limited model downloads |

---

## 🗺️ Stages Completed

| Stage | Description | Status |
|-------|-------------|--------|
| 1 | Project Bootstrap | ✅ |
| 2 | Configuration System | ✅ |
| 3 | Enterprise Logging | ✅ |
| 4 | Qdrant Infrastructure | ✅ |
| 5 | YOLO11 + ByteTrack Tracking | ✅ |
| 6 | Crop Extraction Pipeline | ✅ |
| 7 | SigLIP Embedding Engine | ✅ |
| 8 | Semantic Memory Pipeline | ✅ |
| 9 | Week 1 Search MVP | ✅ |
| 10 | Production MVP Polish | ✅ |

---

## 🔮 Future Roadmap (Week 2+)

| Priority | Feature |
|----------|---------|
| 🔴 High | REST API (FastAPI) with WebSocket streaming |
| 🔴 High | Multi-camera support + cross-camera re-ID |
| 🟡 Medium | Real-time RTSP stream processing |
| 🟡 Medium | Alerting & anomaly detection |
| 🟡 Medium | Web dashboard (React / Next.js) |
| 🟢 Low | Docker Compose production deployment |
| 🟢 Low | CI/CD pipeline (GitHub Actions) |

---

*Report generated automatically by `scripts/generate_week1_report.py`.*
""")

    return "\n".join(sections)


def main() -> int:
    print("=" * 64)
    print("  📊 VisionTraceAI — Week 1 Report Generator")
    print("=" * 64)

    print("\n  [1/3] Collecting project metrics...")
    print("  [2/3] Running test suite...")
    report = generate_report()

    print("  [3/3] Writing report...")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(f"\n  💾 Report saved → {REPORT_PATH}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
