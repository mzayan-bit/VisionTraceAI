"""
VisionTraceAI — FastAPI Core Backend.
"""

import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from backend.agent.executor import VisionAgentExecutor
from app.utils.logger import get_logger
from api.websocket import ws_router

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
    intent: Dict[str, Any]
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
