"""
VisionTraceAI — FastAPI Core Backend.
"""

import time
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import shutil
from pathlib import Path
import subprocess

from api.websocket_stream import ws_router, manager
from app.config.settings import get_settings
from app.utils.logger import get_logger
from backend.agent.executor import VisionAgentExecutor

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    description="VisionTraceAI Production API",
    version="0.1.0",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register WebSocket routes
app.include_router(ws_router, prefix="/ws")

# Initialize the LangGraph agent executor lazily
agent_executor: VisionAgentExecutor | None = None

def get_agent_executor() -> VisionAgentExecutor:
    global agent_executor
    if agent_executor is None:
        logger.info("Initializing VisionAgentExecutor...")
        agent_executor = VisionAgentExecutor()
    return agent_executor


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str = Field(..., description="User's natural language query")


class ChatResponse(BaseModel):
    query: str
    intent: dict[str, Any]
    final_answer: str
    raw_results: list[Any]
    processing_time_sec: float


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=app.version,
        timestamp=time.time(),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Process a natural language query through the LangGraph reasoning agent.
    """
    logger.info("Received chat query", extra={"query": request.query})

    start_time = time.time()
    try:
        executor = get_agent_executor()
        # The executor.execute call is synchronous, so it will block the thread.
        # In a high-concurrency production env, we could use `run_in_threadpool`.
        result = executor.execute(request.query)

        elapsed = time.time() - start_time
        logger.info("Chat query processed", extra={"elapsed_sec": elapsed})
        
        # Broadcast the agent event via WebSocket
        intent = result.get("intent", {})
        track_id = intent.get("target_id")
        action = "highlight" if intent.get("type") == "track" else "search"
        
        try:
            manager.broadcast_agent_event(track_id=track_id, action=action, raw_results=result.get("raw_results", []))
        except Exception as e:
            logger.error("Failed to broadcast agent event", extra={"error": str(e)})

        return ChatResponse(
            query=result.get("query", request.query),
            intent=result.get("intent", {}),
            final_answer=result.get("final_answer", ""),
            raw_results=result.get("raw_results", []),
            processing_time_sec=elapsed,
        )
    except Exception as exc:
        logger.error("Error processing chat query", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


def run_tracker_background(video_path: Path):
    """Run the tracking script as a background subprocess."""
    try:
        logger.info("Starting background tracker", extra={"video": str(video_path)})
        subprocess.Popen(["uv", "run", "python", "scripts/run_tracker.py", str(video_path)])
    except Exception as exc:
        logger.error("Failed to start background tracker", extra={"error": str(exc)})


@app.post("/upload-video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Upload a video file and start tracking it in the background.
    """
    try:
        videos_dir = Path("data/videos")
        videos_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = videos_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info("Video uploaded successfully", extra={"uploaded_file": file.filename})
        
        # Start tracking in background
        background_tasks.add_task(run_tracker_background, file_path)
        
        return {
            "status": "success",
            "message": f"Video {file.filename} uploaded and tracking started.",
            "filename": file.filename
        }
    except Exception as exc:
        logger.error("Error uploading video", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))
