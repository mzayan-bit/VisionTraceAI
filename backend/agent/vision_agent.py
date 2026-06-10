"""
VisionTraceAI — LangGraph Vision Agent (v2 — Bulletproof Rewrite).

A stateful ReAct agent that uses custom tools to query the Global Scene Memory
(Qdrant for visual embeddings, Redis for temporal trajectories) and answers
complex visual and temporal user queries via an LLM.

Architecture
────────────
  ┌─────────┐    tools_condition    ┌───────┐
  │  agent  │ ───────────────────►  │ tools │
  │ (LLM)   │ ◄──────────────────── │       │
  └────┬────┘                       └───────┘
       │  END (no tool call)
       ▼
    response

Error‑handling philosophy: **never crash, always respond**.
Every layer (LLM init, tool execution, graph invocation) is wrapped in
try/except so the user always receives a readable string — even if the
entire backend is on fire.
"""

from __future__ import annotations

import json
import os
import re
import time
import traceback
from typing import Annotated, Any, Dict, List, TypedDict

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  0.  LLM PROVIDER INITIALIZATION  (Google → OpenAI → Mock)          ║
# ╚═══════════════════════════════════════════════════════════════════════╝

_LLM_PROVIDER: str = "none"
_LLM_ERROR_MSG: str = ""

def _get_llm():
    """
    Attempt to create an LLM in priority order:
      1. Google  (GOOGLE_API_KEY  → gemini-2.5-flash)
      2. OpenAI  (OPENAI_API_KEY  → gpt-4o-mini)
      3. None    → returns None; caller must handle gracefully.

    A fresh instance is returned each call so that env‑var hot‑reloads
    are picked up without restarting the server.
    """
    global _LLM_PROVIDER, _LLM_ERROR_MSG

    # ── 1. Google Gemini ────────────────────────────────────────────────
    google_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.2,
                max_retries=2,
                timeout=30,
            )
            _LLM_PROVIDER = "google/gemini-2.5-flash"
            _LLM_ERROR_MSG = ""
            logger.info("LLM initialised", extra={"provider": _LLM_PROVIDER})
            return llm
        except Exception as exc:
            _LLM_ERROR_MSG = f"Google LLM init failed: {exc}"
            logger.warning(_LLM_ERROR_MSG)

    # ── 2. OpenAI ───────────────────────────────────────────────────────
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                max_retries=2,
                request_timeout=30,
            )
            _LLM_PROVIDER = "openai/gpt-4o-mini"
            _LLM_ERROR_MSG = ""
            logger.info("LLM initialised", extra={"provider": _LLM_PROVIDER})
            return llm
        except Exception as exc:
            _LLM_ERROR_MSG = f"OpenAI LLM init failed: {exc}"
            logger.warning(_LLM_ERROR_MSG)

    # ── 3. No key at all ────────────────────────────────────────────────
    _LLM_PROVIDER = "none"
    _LLM_ERROR_MSG = (
        "System Configuration Error: No LLM API key found. "
        "Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file."
    )
    logger.error(_LLM_ERROR_MSG)
    return None


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  1.  MEMORY MANAGER  (lazy singleton)                               ║
# ╚═══════════════════════════════════════════════════════════════════════╝

_memory_manager = None


def _get_memory_manager():
    """Return a connected MemoryManager, or None on failure."""
    global _memory_manager
    if _memory_manager is not None:
        return _memory_manager
    try:
        from backend.storage.memory_manager import MemoryManager

        mm = MemoryManager()
        mm.connect()
        _memory_manager = mm
        logger.info("MemoryManager connected successfully")
        return mm
    except Exception as exc:
        logger.error("MemoryManager connection failed", extra={"error": str(exc)})
        return None


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  2.  CUSTOM TOOLS  (bulletproof)                                    ║
# ╚═══════════════════════════════════════════════════════════════════════╝

@tool
def search_person_by_visual_attributes(description: str) -> str:
    """
    Searches the Qdrant visual‑embedding database for people matching a
    text description of their appearance or clothing (e.g. "person in a
    red jacket", "woman with white shirt").

    Args:
        description: Free‑text appearance description.

    Returns:
        A human‑readable summary of matching track IDs and scores, or
        an informative message if no results are found.
    """
    print(f"  🔧 TOOL CALLED: search_person_by_visual_attributes(\"{description}\")")
    logger.info("Tool invoked: search_person_by_visual_attributes", extra={"description": description})

    mm = _get_memory_manager()
    if mm is None:
        msg = "Database Status: Unable to connect to the visual memory database (Qdrant). Please ensure Docker containers are running."
        print(f"  ⚠️  TOOL RESULT: {msg}")
        return msg

    try:
        results = mm.search_similar_appearance(description, limit=5)
    except Exception as exc:
        msg = f"Database Error: Qdrant query failed — {exc}"
        logger.error(msg, exc_info=True)
        print(f"  ❌ TOOL ERROR: {msg}")
        return msg

    if not results:
        msg = f"No visual matches found in the Qdrant database for: '{description}'."
        print(f"  ℹ️  TOOL RESULT: {msg}")
        return msg

    lines = []
    for r in results:
        lines.append(
            f"  • Track ID {r.get('track_id')}"
            f"  |  Camera: {r.get('camera_id', 'unknown')}"
            f"  |  Dominant Color: {r.get('detected_color', 'unknown')}"
            f"  |  Similarity: {r.get('score', 0):.3f}"
        )
    output = f"Found {len(results)} visual matches:\n" + "\n".join(lines)
    print(f"  ✅ TOOL RESULT (snippet): {output[:200]}")
    logger.info("Tool executed successfully", extra={"tool": "search_person_by_visual_attributes", "matches": len(results)})
    return output


@tool
def get_temporal_trajectory(track_id: int) -> str:
    """
    Retrieves the movement trajectory (timestamps + bounding boxes) for a
    specific tracked person from the Redis temporal database.

    Args:
        track_id: The integer Track ID to look up (e.g. 5).

    Returns:
        A human‑readable timeline of where the person was seen, or an
        informative message if no data exists.
    """
    print(f"  🔧 TOOL CALLED: get_temporal_trajectory(track_id={track_id})")
    logger.info("Tool invoked: get_temporal_trajectory", extra={"track_id": track_id})

    mm = _get_memory_manager()
    if mm is None:
        msg = "Database Status: Unable to connect to the temporal database (Redis). Please ensure Docker containers are running."
        print(f"  ⚠️  TOOL RESULT: {msg}")
        return msg

    try:
        # Ensure Redis is initialised
        if mm.redis_client is None:
            mm.init_redis()

        client = mm.redis_client._ensure_client()
    except Exception as exc:
        msg = f"Database Status: Redis connection failed — {exc}"
        logger.error(msg, exc_info=True)
        print(f"  ❌ TOOL ERROR: {msg}")
        return msg

    try:
        # Scan across all cameras for this track
        keys = client.keys(f"trajectory:*:{track_id}")

        if not keys:
            msg = (
                f"Database Status: Track ID {track_id} was found in visual embeddings, "
                f"but no temporal trajectory logs exist in Redis for this person yet."
            )
            print(f"  ℹ️  TOOL RESULT: {msg}")
            return msg

        history_lines = []
        for key in keys:
            raw_entries = client.lrange(key, -10, -1)  # last 10 entries
            key_str = key if isinstance(key, str) else key.decode("utf-8")
            camera_id = key_str.split(":")[1] if ":" in key_str else "unknown"
            for entry in raw_entries:
                try:
                    data = json.loads(entry)
                    ts = data.get("timestamp", "?")
                    bbox = data.get("bbox", {})
                    color = data.get("detected_color", "unknown")
                    history_lines.append(
                        f"  • t={ts}s  |  Camera: {camera_id}"
                        f"  |  Color: {color}"
                        f"  |  BBox: x1={bbox.get('x1','?')}, y1={bbox.get('y1','?')}, x2={bbox.get('x2','?')}, y2={bbox.get('y2','?')}"
                    )
                except json.JSONDecodeError:
                    continue

        if not history_lines:
            msg = f"Track ID {track_id}: trajectory keys exist but contained no parseable data."
            print(f"  ℹ️  TOOL RESULT: {msg}")
            return msg

        output = f"Trajectory for Track ID {track_id} ({len(history_lines)} recent points):\n" + "\n".join(history_lines)
        print(f"  ✅ TOOL RESULT (snippet): {output[:300]}")
        logger.info("Tool executed successfully", extra={"tool": "get_temporal_trajectory", "points": len(history_lines)})
        return output

    except Exception as exc:
        msg = f"Redis query error for Track ID {track_id}: {exc}"
        logger.error(msg, exc_info=True)
        print(f"  ❌ TOOL ERROR: {msg}")
        return msg


# Tool registry
tools = [search_person_by_visual_attributes, get_temporal_trajectory]


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  3.  LANGGRAPH STATE + NODES                                        ║
# ╚═══════════════════════════════════════════════════════════════════════╝

SYSTEM_PROMPT = (
    "You are VisionTraceAI, an intelligent video surveillance analysis agent.\n\n"
    "You have access to two tools:\n"
    "1. search_person_by_visual_attributes — searches the Qdrant vector database "
    "for people matching a visual description.\n"
    "2. get_temporal_trajectory — retrieves movement history from Redis for a "
    "specific Track ID.\n\n"
    "Guidelines:\n"
    "- Always use your tools to look up real data before answering.\n"
    "- Provide clear, human‑readable summaries. Never expose raw JSON.\n"
    "- If a tool returns no results, say so honestly.\n"
    "- When reporting matches, mention the Track ID, dominant clothing color, "
    "and confidence score.\n"
    "- Keep answers concise (2‑4 sentences)."
)


class AgentState(TypedDict):
    """State flowing through the LangGraph agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    current_active_tracks: List[str]


def call_model(state: AgentState) -> dict:
    """
    The 'agent' node: invoke the LLM to either call a tool or produce a
    final response.  Includes full error handling around LLM invocation.
    """
    messages = state["messages"]

    # ── Prepend system prompt ───────────────────────────────────────────
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    print(f"\n{'='*60}")
    print(f"  🧠 AGENT NODE — Processing {len(messages)} messages")
    print(f"  📨 Latest user query: {messages[-1].content[:100] if messages else 'N/A'}")
    print(f"{'='*60}")

    # ── Get LLM ─────────────────────────────────────────────────────────
    llm = _get_llm()
    if llm is None:
        error_response = AIMessage(content=_LLM_ERROR_MSG)
        print(f"  ❌ NO LLM AVAILABLE: {_LLM_ERROR_MSG}")
        return {"messages": [error_response]}

    # ── Bind tools & invoke ─────────────────────────────────────────────
    try:
        llm_with_tools = llm.bind_tools(tools)
        print(f"  🤖 Calling LLM ({_LLM_PROVIDER}) with {len(tools)} tools bound...")
        response = llm_with_tools.invoke(messages)

        # Log what the LLM decided
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                print(f"  🔨 LLM decided to call tool: {tc.get('name', '?')} with args: {tc.get('args', {})}")
        else:
            content_preview = _extract_text(response.content)[:150]
            print(f"  💬 LLM final answer: {content_preview}")

        return {"messages": [response]}

    except Exception as exc:
        error_text = f"LLM invocation error ({_LLM_PROVIDER}): {exc}"
        logger.error(error_text, exc_info=True)
        print(f"  ❌ LLM ERROR: {error_text}")

        # Return a graceful fallback so the graph terminates cleanly
        fallback = AIMessage(
            content=(
                "I encountered an error while processing your query. "
                "This may be a temporary rate limit or network issue. "
                "Please try again in a few seconds."
            )
        )
        return {"messages": [fallback]}


# Pre‑built tool executor node from LangGraph
tool_node = ToolNode(tools)


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  4.  COMPILE THE GRAPH                                              ║
# ╚═══════════════════════════════════════════════════════════════════════╝

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

vision_agent = workflow.compile()


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  5.  HELPER UTILITIES                                               ║
# ╚═══════════════════════════════════════════════════════════════════════╝

def _extract_text(content: Any) -> str:
    """
    Safely extract a plain string from LLM response content.

    Gemini ≥ 3.x returns content as a List[dict] with
    ``{"type": "text", "text": "..."}`` entries.  Older models return
    a plain ``str``.  This function normalises both.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts)
    return str(content)


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  6.  PUBLIC API  — run_vision_agent()                               ║
# ╚═══════════════════════════════════════════════════════════════════════╝

def run_vision_agent(query: str, history: List[Dict[str, str]] | None = None) -> dict:
    """
    Top‑level convenience function called by the FastAPI endpoint.

    Returns a dict matching the ``ChatResponse`` schema::

        {
            "query":        str,
            "intent":       dict,
            "final_answer": str,   # always a plain string
            "raw_results":  list,
            "system_health": float  # 0.0 – 1.0
        }
    """
    logger.info("Agent received query", extra={"query": query})
    print(f"\n{'#'*60}")
    print(f"  🚀 VISION AGENT START")
    print(f"  📝 Query: {query}")
    print(f"{'#'*60}")

    start = time.time()

    # ── Build message list ──────────────────────────────────────────────
    langchain_messages: List[BaseMessage] = []
    if history:
        for msg in history:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if role == "assistant":
                langchain_messages.append(AIMessage(content=text))
            else:
                langchain_messages.append(HumanMessage(content=text))
    langchain_messages.append(HumanMessage(content=query))

    initial_state: AgentState = {
        "messages": langchain_messages,
        "current_active_tracks": [],
    }

    # ── Invoke graph with top‑level safety net ──────────────────────────
    try:
        result = vision_agent.invoke(initial_state)
        final_answer = _extract_text(result["messages"][-1].content)

        # ── Extract intent for UI highlighting ──────────────────────────
        intent: Dict[str, Any] = {}
        for msg in result["messages"]:
            if msg.type == "tool":
                matches = re.findall(r"Track ID[:\s]*(\d+)", msg.content)
                if matches:
                    intent["target_id"] = int(matches[0])
                    intent["type"] = "track"
                    break

        elapsed = time.time() - start
        print(f"\n{'='*60}")
        print(f"  ✅ AGENT COMPLETE in {elapsed:.1f}s")
        print(f"  📤 Answer: {final_answer[:200]}")
        print(f"{'='*60}\n")
        logger.info("Agent completed", extra={"elapsed_sec": round(elapsed, 2), "answer_length": len(final_answer)})

        return {
            "query": query,
            "intent": intent,
            "final_answer": final_answer,
            "raw_results": [],
            "system_health": 1.0,
        }

    except Exception as exc:
        elapsed = time.time() - start
        error_detail = traceback.format_exc()
        logger.error("Agent invocation failed", extra={"error": str(exc), "traceback": error_detail})
        print(f"\n{'='*60}")
        print(f"  ❌ AGENT FAILED in {elapsed:.1f}s")
        print(f"  Error: {exc}")
        print(f"  Traceback:\n{error_detail}")
        print(f"{'='*60}\n")

        return {
            "query": query,
            "intent": {},
            "final_answer": (
                "I'm sorry, I encountered an internal error while processing your request. "
                f"Error detail: {exc}. "
                "Please try again in a moment, or check the server terminal for full logs."
            ),
            "raw_results": [],
            "system_health": 0.5,
        }


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  7.  STANDALONE TEST RUNNER                                         ║
# ╚═══════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    """
    Run this file directly to test the agent end‑to‑end from the terminal:

        uv run python -m backend.agent.vision_agent

    No web server required.  Exercises both tools with real data.
    """
    border = "═" * 60

    print(f"\n  ╔{border}╗")
    print(f"  ║  🧪 VisionTraceAI — Agent Standalone Test Suite{' ' * 11}║")
    print(f"  ╚{border}╝\n")

    print(f"  LLM Provider : {_LLM_PROVIDER or 'checking...'}")
    test_llm = _get_llm()
    print(f"  LLM Provider : {_LLM_PROVIDER}")
    if _LLM_ERROR_MSG:
        print(f"  ⚠️  LLM Warning: {_LLM_ERROR_MSG}")
    print()

    test_queries = [
        "Find a person wearing a white shirt",
        "Where did Track ID 5 go?",
        "How many people are wearing blue?",
        "Show the trajectory of Track ID 1",
    ]

    for i, q in enumerate(test_queries, 1):
        print(f"\n  ┌{'─'*58}┐")
        print(f"  │  Test {i}/{len(test_queries)}: {q:<48} │")
        print(f"  └{'─'*58}┘")

        result = run_vision_agent(q)

        print(f"\n  📋 Result:")
        print(f"     Query:        {result['query']}")
        print(f"     Intent:       {result['intent']}")
        print(f"     Health:       {result['system_health']}")
        print(f"     Answer:       {result['final_answer'][:300]}")
        print(f"  {'─'*60}")

    print(f"\n  ╔{border}╗")
    print(f"  ║  ✅  All {len(test_queries)} test queries completed.{' ' * 27}║")
    print(f"  ╚{border}╝\n")
