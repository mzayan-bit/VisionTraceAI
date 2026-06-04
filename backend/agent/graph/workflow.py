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


def timeline_node(state: AgentState) -> Dict[str, Any]:
    """Execute timeline search based on the query."""
    results = search_timeline.invoke({"query": state["user_query"]})
    
    return {
        "track_ids": results,
        "tool_outputs": [{"tool": "search_timeline", "result": results}]
    }


def search_visuals_node(state: AgentState) -> Dict[str, Any]:
    """Execute visual semantic search and optionally filter by timeline tracks."""
    results = search_visuals.invoke({"query": state["user_query"]})
    
    # If the timeline node executed first, it will have populated track_ids
    # We intersect the visual search results with the temporal track_ids
    if state.get("track_ids"):
        valid_tracks = set(state["track_ids"])
        results = [r for r in results if r.get("track_id") in valid_tracks]
        
    return {
        "tool_outputs": [{"tool": "search_visuals", "result": results}],
        "final_answer": f"Found {len(results)} matching visual tracks."
    }


def custom_object_node(state: AgentState) -> Dict[str, Any]:
    """Execute Grounding DINO search for unknown/custom objects."""
    # Hardcode sample video path for the MVP implementation
    results = find_custom_object.invoke({
        "video_path": "data/videos/sample.mp4",
        "prompt": state["user_query"]
    })
    
    return {
        "tool_outputs": [{"tool": "find_custom_object", "result": results}],
        "final_answer": f"Found {len(results)} custom object detections."
    }


def route_query(state: AgentState) -> str:
    """Determine the next node based on the supervisor's parsed intent."""
    tool = state.get("parsed_intent", {}).get("selected_tool", "none")
    
    if tool == "search_timeline":
        return "timeline_node"
    elif tool == "search_visuals":
        return "search_visuals_node"
    elif tool == "find_custom_object":
        return "custom_object_node"
    else:
        # Fallback for hybrid or unknown tools
        return "search_visuals_node"


# ── Graph Construction ──────────────────────────────────────────────────

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("timeline_node", timeline_node)
workflow.add_node("search_visuals_node", search_visuals_node)
workflow.add_node("custom_object_node", custom_object_node)

# Add Edges
workflow.set_entry_point("supervisor_node")

# Conditional routing from supervisor
workflow.add_conditional_edges("supervisor_node", route_query)

# Linear flow: time queries filter tracks, then pass to visual search
workflow.add_edge("timeline_node", "search_visuals_node")

# Terminal edges
workflow.add_edge("search_visuals_node", END)
workflow.add_edge("custom_object_node", END)

# Compile graph
app = workflow.compile()
