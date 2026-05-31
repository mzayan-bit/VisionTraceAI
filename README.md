<p align="center">
  <h1 align="center">🔍 VisionTraceAI</h1>
  <p align="center">
    <strong>Production-Grade AI-Powered Surveillance & Video Analytics Platform</strong>
  </p>
  <p align="center">
    <a href="https://github.com/mzayan-bit/VisionTraceAI/actions"><img src="https://img.shields.io/github/actions/workflow/status/mzayan-bit/VisionTraceAI/ci.yml?branch=main&style=flat-square" alt="CI"></a>
    <a href="https://github.com/mzayan-bit/VisionTraceAI/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
    <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/package%20manager-uv-blueviolet?style=flat-square" alt="uv">
  </p>
</p>

---

## 📋 Overview

**VisionTraceAI** is an enterprise-grade AI surveillance system designed for real-time video analytics. It provides end-to-end pipelines for object detection, multi-object tracking, re-identification, and anomaly detection across multiple camera feeds.

### Key Capabilities

| Capability              | Description                                                  |
|------------------------|--------------------------------------------------------------|
| 🎯 Object Detection    | Real-time detection with state-of-the-art deep learning models |
| 🔄 Multi-Object Tracking | Persistent identity tracking across frames and cameras       |
| 🧠 Anomaly Detection   | Behavioral anomaly detection and alerting                    |
| 📹 Multi-Stream        | Concurrent processing of multiple RTSP/video streams         |
| 📊 Analytics Dashboard | Real-time metrics, heatmaps, and event logging               |
| 🐳 Containerized       | Production-ready Docker deployment                           |

---

## 🏗️ Project Structure

```
VisionTraceAI/
│
├── app/                    # Main application package
│   ├── core/               # Core logic, base classes, exceptions
│   ├── services/           # Business logic services
│   ├── pipelines/          # ML/AI processing pipelines
│   ├── models/             # Data models, schemas, ORM
│   ├── utils/              # Shared utilities and helpers
│   └── config/             # Configuration management
│
├── scripts/                # Utility & automation scripts
├── tests/                  # Test suite (pytest)
├── docs/                   # Project documentation
├── docker/                 # Dockerfiles & compose configs
├── notebooks/              # Jupyter notebooks for exploration
│
├── data/
│   ├── videos/             # Input video files
│   ├── crops/              # Extracted object crops
│   └── outputs/            # Processing outputs
│
├── .env.example            # Environment variable template
├── pyproject.toml          # Project metadata & dependencies
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11+
- **uv** package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker** (for Qdrant)
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/mzayan-bit/VisionTraceAI.git
cd VisionTraceAI

# Create virtual environment and install dependencies
uv venv --python 3.11
source .venv/bin/activate
uv sync

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings
```

### Development Setup

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy app/
```

---

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker compose -f docker/docker-compose.yml up --build
```

---

## 🗄️ Qdrant Vector Database

VisionTraceAI uses [Qdrant](https://qdrant.tech/) as the semantic memory backend for storing and searching embedding vectors.

### Setup

```bash
# 1. Start the Qdrant container
docker compose -f docker/docker-compose.qdrant.yml up -d

# 2. Initialize the default collection
uv run python scripts/init_qdrant.py

# 3. Verify with health check
uv run python scripts/check_qdrant.py
```

### Expected Output — Initialization

```
  🔍 VisionTraceAI — Qdrant Initialization
  ════════════════════════════════════════
  [1/4] Connecting to Qdrant...
        ✅  Connected successfully
  [2/4] Creating collection...
        ✅  Collection 'visiontrace_embeddings' created
  [3/4] Verifying collection...
        ✅  Collection 'visiontrace_embeddings' verified
  [4/4] Collection diagnostics:
        Name         : visiontrace_embeddings
        Status       : green
        Vector Size  : 1152
        Vectors Count: 0
```

### Expected Output — Health Check

```
  🔍 VisionTraceAI — Qdrant Health Check
  ════════════════════════════════════════
  [1/3] Testing connection...
        ✅  Connected to localhost:6333
  [2/3] Running health check...
        Status           : healthy
        Collections Count: 1
  [3/3] Listing collections:
        1. visiontrace_embeddings
           Status : green
           Vectors: 0
           Dim    : 1152
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `localhost` | Qdrant server hostname |
| `QDRANT_PORT` | `6333` | Qdrant HTTP API port |
| `QDRANT_COLLECTION_NAME` | `visiontrace_embeddings` | Default collection name |

### Collection Details

| Property | Value |
|----------|-------|
| Collection Name | `visiontrace_embeddings` |
| Vector Size | 1152 (SigLIP embeddings) |
| Distance Metric | Cosine |
| Persistent Storage | Docker volume `qdrant_data` |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test module
pytest tests/test_core.py -v
```

---

## 📖 Documentation

Documentation is located in the `docs/` directory. To build and serve locally:

```bash
uv sync --extra docs
mkdocs serve
```

---

## 🗺️ Roadmap

| Stage | Description                     | Status         |
|-------|---------------------------------|----------------|
| 1     | Project Bootstrap               | ✅ Complete     |
| 2     | Configuration System            | ✅ Complete     |
| 3     | Enterprise Logging              | ✅ Complete     |
| 4     | Qdrant Infrastructure           | ✅ Complete     |
| 5     | Detection & Tracking Pipelines  | 🔲 Planned     |
| 6     | API & Dashboard                 | 🔲 Planned     |
| 7     | Deployment & Monitoring         | 🔲 Planned     |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ by the <strong>VisionTraceAI</strong> team
</p>
