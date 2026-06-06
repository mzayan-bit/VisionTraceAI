"""
Tests for the LangGraph execution pipeline.
"""

import os
# Set dummy API key to prevent ChatOpenAI initialization errors during test graph compilation
os.environ["OPENAI_API_KEY"] = "dummy-key-for-tests"

from unittest.mock import MagicMock, patch

import pytest

from backend.agent.graph.state import AgentState
from backend.agent.graph.workflow import app, route_query


def test_route_query():
    """Verify conditional edge routing logic."""
    state_timeline: AgentState = {"parsed_intent": {"selected_tool": "search_timeline"}}  # type: ignore
    assert route_query(state_timeline) == "timeline_node"

    state_visuals: AgentState = {"parsed_intent": {"selected_tool": "search_visuals"}}  # type: ignore
    assert route_query(state_visuals) == "search_visuals_node"

    state_custom: AgentState = {"parsed_intent": {"selected_tool": "find_custom_object"}}  # type: ignore
    assert route_query(state_custom) == "custom_object_node"

    state_fallback: AgentState = {"parsed_intent": {"selected_tool": "hybrid_search"}}  # type: ignore
    assert route_query(state_fallback) == "search_visuals_node"


@patch("backend.agent.graph.supervisor.ChatGoogleGenerativeAI")
@patch("backend.agent.graph.workflow.search_timeline")
@patch("backend.agent.graph.workflow.search_visuals")
def test_timeline_to_visual_flow(mock_visuals, mock_timeline, mock_chat_openai):
    """Test the execution sequence: supervisor -> timeline -> visual search."""
    
    from langchain_core.runnables import RunnableLambda
    from backend.agent.graph.supervisor import IntentClassification
    
    # 1. Mock LLM to output timeline intent
    mock_structured_llm = RunnableLambda(
        lambda x: IntentClassification(
            reasoning_trace="Time query",
            selected_tool="search_timeline"
        )
    )
    mock_chat_openai.return_value.with_structured_output.return_value = mock_structured_llm

    # 2. Mock Timeline Tool to return track ID [42]
    mock_timeline.invoke.return_value = [42]

    # 3. Mock Visual Search Tool to return un-filtered results
    # One matching track 42, one non-matching track 99
    mock_visuals.invoke.return_value = [
        {"track_id": 42, "score": 0.9},
        {"track_id": 99, "score": 0.8}
    ]

    # Execute workflow
    initial_state = {
        "user_query": "red bag after 8pm",
        "parsed_intent": {},
        "tool_outputs": [],
        "track_ids": [],
        "final_answer": "",
        "conversation_memory": []
    }
    
    result = app.invoke(initial_state)

    # Validate correct tools were called
    mock_timeline.invoke.assert_called_once_with({"query": "red bag after 8pm"})
    mock_visuals.invoke.assert_called_once_with({"query": "red bag after 8pm"})

    # Validate state mutations
    assert result["parsed_intent"]["selected_tool"] == "search_timeline"
    assert result["track_ids"] == [42]
    
    # Validate the visual node correctly filtered out track 99
    tool_outputs = result["tool_outputs"]
    
    # Tool outputs use operator.add, so there are two outputs appended
    timeline_out = next(t for t in tool_outputs if t["tool"] == "search_timeline")
    assert timeline_out["result"] == [42]
    
    visual_out = next(t for t in tool_outputs if t["tool"] == "search_visuals")
    assert len(visual_out["result"]) == 1
    assert visual_out["result"][0]["track_id"] == 42


@patch("backend.agent.graph.supervisor.ChatGoogleGenerativeAI")
@patch("backend.agent.graph.workflow.find_custom_object")
def test_custom_object_flow(mock_custom, mock_chat_openai):
    """Test the execution sequence: supervisor -> custom object -> END."""
    
    from langchain_core.runnables import RunnableLambda
    from backend.agent.graph.supervisor import IntentClassification
    
    mock_structured_llm = RunnableLambda(
        lambda x: IntentClassification(
            reasoning_trace="Object query",
            selected_tool="find_custom_object"
        )
    )
    mock_chat_openai.return_value.with_structured_output.return_value = mock_structured_llm

    mock_custom.invoke.return_value = [{"label": "fire extinguisher", "frame_index": 5}]

    initial_state = {
        "user_query": "find fire extinguisher",
        "parsed_intent": {},
        "tool_outputs": [],
        "track_ids": [],
        "final_answer": "",
        "conversation_memory": []
    }
    
    result = app.invoke(initial_state)

    mock_custom.invoke.assert_called_once_with({
        "video_path": "data/videos/sample.mp4",
        "prompt": "find fire extinguisher"
    })

    assert result["parsed_intent"]["selected_tool"] == "find_custom_object"
    assert "Found 1 custom object detections." in result["final_answer"]
