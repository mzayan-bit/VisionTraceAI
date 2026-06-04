"""
Tests for the Agent State Schema.
"""

from typing import get_type_hints

from backend.agent.graph.state import AgentState

def test_agent_state_schema():
    """Verify that the AgentState schema has all the required fields and type hints."""
    hints = get_type_hints(AgentState, include_extras=True)
    
    expected_keys = {
        "user_query",
        "parsed_intent",
        "tool_outputs",
        "track_ids",
        "final_answer",
        "conversation_memory"
    }
    
    for key in expected_keys:
        assert key in hints, f"Missing required state key: {key}"

def test_agent_state_instantiation():
    """Verify that a valid AgentState dictionary can be instantiated correctly."""
    state: AgentState = {
        "user_query": "find the red bag",
        "parsed_intent": {"target": "red bag", "action": "find"},
        "tool_outputs": [{"status": "success"}],
        "track_ids": [42],
        "final_answer": "I found track 42.",
        "conversation_memory": [{"role": "user", "content": "find the red bag"}]
    }
    
    # Assert fields are accessible and retain their expected values
    assert state["user_query"] == "find the red bag"
    assert state["parsed_intent"]["target"] == "red bag"
    assert state["track_ids"] == [42]
    assert state["final_answer"] == "I found track 42."
