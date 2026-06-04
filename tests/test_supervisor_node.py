"""
Tests for the reasoning supervisor node.
"""

from unittest.mock import patch

import pytest
from langchain_core.runnables import RunnableLambda

from backend.agent.graph.state import AgentState
from backend.agent.graph.supervisor import IntentClassification, supervisor_node


@pytest.fixture
def mock_agent_state() -> AgentState:
    """Fixture to provide a dummy initial agent state."""
    return {
        "user_query": "mock query",
        "parsed_intent": {},
        "tool_outputs": [],
        "track_ids": [],
        "final_answer": "",
        "conversation_memory": []
    }


@patch("backend.agent.graph.supervisor.ChatOpenAI")
def test_supervisor_node_routes_to_timeline(mock_chat_openai, mock_agent_state):
    """Test that the supervisor parses timeline queries."""
    mock_agent_state["user_query"] = "between 5 and 6pm"
    
    # Setup mock LLM structured output using RunnableLambda
    mock_structured_llm = RunnableLambda(
        lambda x: IntentClassification(
            reasoning_trace="The user mentioned a specific time range.",
            selected_tool="search_timeline"
        )
    )
    mock_chat_openai.return_value.with_structured_output.return_value = mock_structured_llm

    # Execute node
    result = supervisor_node(mock_agent_state)
    
    # Validate parsed intent update
    assert "parsed_intent" in result
    assert result["parsed_intent"]["selected_tool"] == "search_timeline"
    assert "reasoning_trace" in result["parsed_intent"]


@patch("backend.agent.graph.supervisor.ChatOpenAI")
def test_supervisor_node_routes_to_visuals(mock_chat_openai, mock_agent_state):
    """Test that the supervisor parses visual queries."""
    mock_agent_state["user_query"] = "person in a green shirt"
    
    mock_structured_llm = RunnableLambda(
        lambda x: IntentClassification(
            reasoning_trace="The user is looking for a visual appearance trait.",
            selected_tool="search_visuals"
        )
    )
    mock_chat_openai.return_value.with_structured_output.return_value = mock_structured_llm

    result = supervisor_node(mock_agent_state)
    
    assert result["parsed_intent"]["selected_tool"] == "search_visuals"


@patch("backend.agent.graph.supervisor.ChatOpenAI")
def test_supervisor_node_routes_to_custom_object(mock_chat_openai, mock_agent_state):
    """Test that the supervisor parses open vocabulary queries."""
    mock_agent_state["user_query"] = "find the fire extinguisher"
    
    mock_structured_llm = RunnableLambda(
        lambda x: IntentClassification(
            reasoning_trace="The user is looking for an unknown/custom object.",
            selected_tool="find_custom_object"
        )
    )
    mock_chat_openai.return_value.with_structured_output.return_value = mock_structured_llm

    result = supervisor_node(mock_agent_state)
    
    assert result["parsed_intent"]["selected_tool"] == "find_custom_object"
