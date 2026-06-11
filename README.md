<p align="center">
  <h1 align="center">🔍 VisionTraceAI</h1>
  <p align="center">
    <strong>Production-Grade AI Surveillance, Streaming Analytics & Agentic Workflow Dashboard</strong>
  </p>
  <p align="center">
    <a href="https://github.com/mzayan-bit/VisionTraceAI/actions"><img src="https://img.shields.io/github/actions/workflow/status/mzayan-bit/VisionTraceAI/ci.yml?branch=main&style=flat-square" alt="CI"></a>
    <a href="https://github.com/mzayan-bit/VisionTraceAI/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
    <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/react-18-blue?style=flat-square&logo=react&logoColor=white" alt="React">
    <img src="https://img.shields.io/badge/kafka-streaming-red?style=flat-square&logo=apachekafka&logoColor=white" alt="Kafka">
    <img src="https://img.shields.io/badge/qdrant-vector%20DB-purple?style=flat-square" alt="Qdrant">
  </p>
</p>

---

## 📋 Overview

**VisionTraceAI** is a highly scalable, enterprise-grade AI surveillance platform. It bridges the gap between state-of-the-art computer vision models (YOLOv11, SigLIP, FastReID) and modern web-based operational dashboards. 

It is built around an event-driven Kafka architecture, a LangGraph-powered AI Supervisor Agent, and a React/Vite frontend designed for real-time video analytics, zero-shot global searching, and multi-camera re-identification.

### 🌟 Key Capabilities

| Capability | Technology Stack | Description |
|---|---|---|
| 🎯 **High-Speed Object Tracking** | `YOLOv11m`, `ByteTrack`, `OpenCV` | Real-time object detection and kinematics tracking with Apple Silicon (MPS) & CUDA acceleration. |
| 🧠 **Semantic Vector Search** | `SigLIP`, `Qdrant` | Extracts 768-dimensional visual embeddings allowing you to search "person wearing a red hoodie" across all cameras. |
| 📡 **Real-Time Streaming** | `Apache Kafka`, `WebSockets` | Decoupled event streaming for publishing live bounding boxes and insights to the dashboard. |
| 🗄️ **Global Scene Memory** | `Redis` | Caches short-term trajectory data and active tracks for ultra-fast in-memory retrieval. |
| 🤖 **Agentic Workflows** | `LangGraph`, `LLMs` | Autonomous AI Supervisor that can execute complex user commands via custom tools (`find_custom_object.py`, `search_timeline.py`). |
| 👤 **Identity Re-Identification** | `FastReID` | Persistent tracking and matching of identities across different camera feeds and occlusions. |

---

## 🖥️ The Frontend Dashboard

The frontend is a world-class React/Vite application packed with over 15 distinct functional screens to give security operators absolute control over the surveillance data.

### Core Modules
* **Live Monitoring & Multi-Camera Grid**: View real-time processed streams and manage camera fleets natively in the browser.
* **Playback Center**: A custom HTML5 video playback engine built to handle processed `H.264 (avc1)` video exports complete with overlay metrics.
* **Global Search**: Instantly query historical events using natural language text prompts.
* **Agent Command Center**: An interactive chat interface communicating directly with the backend LangGraph AI supervisor to autonomously investigate footage.
* **Analytics & Heatmaps**: Visualize physical security metrics, traffic flows, spatial mappings, and generate comprehensive PDF audit reports.

---

## ⚙️ Backend Architecture

The Python backend is engineered for maximum throughput and modularity.

### 1. Vision Engine (`app/core/tracker.py`)
Handles the heavy lifting of reading frames, skipping non-essential frames for speed optimization, evaluating the YOLO neural network, and processing kinematics.
* **Performance**: Optimized to skip SigLIP extraction redundancies by caching `embedded_track_ids`.

### 2. Streaming Layer (`backend/streaming/`)
* **Kafka Producers**: The tracker publishes every single detected bounding box and action classification to a Kafka topic.
* **Kafka Consumers**: A background pipeline consumes the Kafka feed, routes crops through the `FeatureEngine` and `ColorEngine`, and writes the semantic metadata into the databases.

### 3. Agentic Layer (`backend/agent/`)
Implements a stateful AI workflow using `LangGraph`.
* **Supervisor**: Delegates tasks.
* **Tools**: Executes strict Python tools (like searching the timeline or cross-camera matching) on behalf of the user query.

---

## 🏗️ Project Structure

```text
VisionTraceAI/
├── frontend/               # React + Vite UI Application
│   ├── src/
│   │   ├── components/     # UI Building Blocks (VideoPlayer, ErrorBoundary, etc.)
│   │   ├── screens/        # 15+ Core Dashboard Views
│   │   ├── layout/         # Shell, Sidebar, and Drawers
│   │   └── themes/         # CSS design tokens
│
├── api/                    # FastAPI Server
│   ├── main.py             # REST Endpoints (Upload/Download)
│   ├── websocket.py        # Real-time connection management
│   └── websocket_stream.py # Kafka-to-WebSocket bridge
│
├── app/                    # Vision Operations
│   ├── core/               # Tracker and Kinematics Engine
│   └── pipelines/          # Cropping and Vector routing
│
├── backend/                # Heavy AI & Data Pipelines
│   ├── agent/              # LangGraph Supervisor & Executor
│   ├── reid/               # FastReID identity management
│   ├── search/             # NLP routing and translation
│   ├── storage/            # Redis & Qdrant adapters
│   └── streaming/          # Kafka Event pipelines & Feature Engines (SigLIP)
│
├── docker/                 # Infra Configurations (Zookeeper, Kafka, Redis, Qdrant)
├── scripts/                # CLI Utilities and Benchmarking Tools
└── tests/                  # Massive Pytest Suite covering the entire architecture
```

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python 3.11+** with `uv` package manager.
* **Node.js v18+** with `npm`.
* **Docker Desktop** (for Kafka, Redis, and Qdrant).

### 1. Boot Infrastructure

```bash
git clone https://github.com/mzayan-bit/VisionTraceAI.git
cd VisionTraceAI

# Spin up Zookeeper, Kafka, Redis, and Qdrant
docker compose up -d
```

### 2. Configure & Start Backend

```bash
# Setup virtual environment
uv venv --python 3.11
source .venv/bin/activate
uv sync

# Configure environment variables
cp .env.example .env
```
> **CRITICAL**: If you are on an Apple Silicon Mac, edit your `.env` file and set `DEVICE=mps` to enable Metal Performance Shaders. For NVIDIA GPUs, use `DEVICE=cuda`. This provides a massive 10x-20x speedup for video processing!

```bash
# Start the background Kafka streaming pipeline
uv run python -c "from backend.streaming.kafka_consumer import StreamingPipeline; pipeline = StreamingPipeline(); pipeline.start()" &

# Start the FastAPI web server
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend Dashboard

Open a fresh terminal window:

```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` in your browser.

---

## 🎬 How to Process a Video

1. Open the **Live Monitoring** screen in the Dashboard.
2. Click **Upload Video** and select your `.mp4` file.
3. The video is sent to the FastAPI server, which saves it to `data/videos/` and spawns a background tracking process.
4. *Note: On your very first upload, the system will automatically download the `yolo11m-pose.pt` weights (~40MB). This may take 30-40 seconds.*
5. The tracker analyzes the video, calculates kinematics, and generates SigLIP embeddings for global search.
6. Once processing completes, navigate to the **Playback Center** to seamlessly view the resulting H.264 video with all overlay metrics natively in your browser!

---

## 🧪 Testing & Validation

VisionTraceAI includes a comprehensive `pytest` suite ensuring rock-solid stability across ML pipelines, storage adapters, and streaming brokers.

```bash
# Run the entire test suite
pytest

# Test the LangGraph agent specifically
pytest tests/test_langgraph_workflow.py -v
```

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