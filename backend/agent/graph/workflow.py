"""
VisionTraceAI — Agent LangGraph Workflow.

Constructs the execution graph routing user queries through the appropriate reasoning
and search nodes.
"""

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from backend.agent.graph.state import AgentState
from backend.agent.graph.supervisor import supervisor_node
from backend.agent.tools.find_custom_object import find_custom_object
from backend.agent.tools.search_timeline import search_timeline
from backend.agent.tools.search_visuals import search_visuals


def execute_with_self_healing(tool_callable, kwargs: dict, tool_name: str):
    """
    Self-healing wrapper for tool execution.
    Retries once on failure, then silently degrades by returning empty results.
    Returns: (results, diagnostic_logs_list, health_score_delta)
    """
    try:
        results = tool_callable.invoke(kwargs)
        return results, [], 0.0
    except Exception as e:
        try:
            results = tool_callable.invoke(kwargs)
            log = {"tool": tool_name, "error": str(e), "status": "retried_success"}
            return results, [log], -0.1
        except Exception as e2:
            log = {"tool": tool_name, "error": str(e2), "status": "failed"}
            return [], [log], -0.3


def timeline_node(state: AgentState) -> Dict[str, Any]:
    """Execute timeline search based on the query."""
    results, logs, health_delta = execute_with_self_healing(
        search_timeline, {"query": state["user_query"]}, "search_timeline"
    )
    
    track_ids = [r["track_id"] for r in results] if results else []
    
    return {
        "track_ids": track_ids,
        "tool_outputs": [{"tool": "search_timeline", "result": results}],
        "diagnostic_logs": logs,
        "system_health": max(0.0, state.get("system_health", 1.0) + health_delta)
    }


def search_visuals_node(state: AgentState) -> Dict[str, Any]:
    """Execute visual semantic search and optionally filter by timeline tracks."""
    results, logs, health_delta = execute_with_self_healing(
        search_visuals, {"query": state["user_query"]}, "search_visuals"
    )
    
    # If the timeline node executed first, it will have populated track_ids
    # We intersect the visual search results with the temporal track_ids
    if state.get("track_ids"):
        valid_tracks = set(state["track_ids"])
        results = [r for r in results if r.get("track_id") in valid_tracks]
        
    return {
        "tool_outputs": [{"tool": "search_visuals", "result": results}],
        "diagnostic_logs": logs,
        "system_health": max(0.0, state.get("system_health", 1.0) + health_delta),
        "final_answer": f"Found {len(results)} matching visual tracks."
    }


def custom_object_node(state: AgentState) -> Dict[str, Any]:
    """Execute Grounding DINO search for unknown/custom objects."""
    # Hardcode sample video path for the MVP implementation
    results, logs, health_delta = execute_with_self_healing(
        find_custom_object, 
        {"video_path": "data/videos/sample.mp4", "prompt": state["user_query"]}, 
        "find_custom_object"
    )
    
    return {
        "tool_outputs": [{"tool": "find_custom_object", "result": results}],
        "diagnostic_logs": logs,
        "system_health": max(0.0, state.get("system_health", 1.0) + health_delta),
        "final_answer": f"Found {len(results)} custom object detections."
    }


def route_query(state: AgentState) -> str:
    """Determine the next node based on the deterministic tool_chain."""
    tool_chain = state.get("parsed_intent", {}).get("tool_chain", [])
    if not tool_chain:
        return END
        
    first_tool = tool_chain[0]
    if first_tool == "search_timeline":
        return "timeline_node"
    elif first_tool == "search_visuals":
        return "search_visuals_node"
    elif first_tool == "find_custom_object":
        return "custom_object_node"
        
    return END


def route_after_timeline(state: AgentState) -> str:
    """Follow the tool_chain after a timeline search."""
    tool_chain = state.get("parsed_intent", {}).get("tool_chain", [])
    if "search_visuals" in tool_chain:
        return "search_visuals_node"
    return END


# ── Graph Construction ──────────────────────────────────────────────────

workflow = StateGraph(AgentState)  # type: ignore

# Add Nodes
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("timeline_node", timeline_node)
workflow.add_node("search_visuals_node", search_visuals_node)
workflow.add_node("custom_object_node", custom_object_node)

# Add Edges
workflow.set_entry_point("supervisor_node")

# Conditional routing from supervisor
workflow.add_conditional_edges("supervisor_node", route_query)

# Strictly follow the tool_chain after timeline
workflow.add_conditional_edges("timeline_node", route_after_timeline)

# Terminal edges
workflow.add_edge("search_visuals_node", END)
workflow.add_edge("custom_object_node", END)

# Compile graph
app = workflow.compile()
