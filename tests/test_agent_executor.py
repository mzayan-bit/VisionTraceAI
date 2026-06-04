"""
Tests for the agent executor and result formatter.
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.agent.executor import VisionAgentExecutor, format_final_answer


def test_format_final_answer_timeline():
    """Verify formatting of timeline tool outputs."""
    tool_outputs = [{"tool": "search_timeline", "result": [10, 20, 30]}]
    answer = format_final_answer(tool_outputs)
    assert "Found 3 active tracks" in answer


def test_format_final_answer_visuals():
    """Verify formatting of visual search outputs."""
    tool_outputs = [{
        "tool": "search_visuals", 
        "result": [
            {"track_id": 42, "camera_id": "cam_01", "confidence_score": 0.95}
        ]
    }]
    answer = format_final_answer(tool_outputs)
    assert "Identified 1 visual matches" in answer
    assert "Track 42" in answer
    assert "cam_01" in answer
    assert "0.95" in answer


def test_format_final_answer_custom_object():
    """Verify formatting of custom object detections."""
    tool_outputs = [{
        "tool": "find_custom_object",
        "result": [
            {"label": "fire extinguisher", "frame_index": 150, "confidence": 0.88}
        ]
    }]
    answer = format_final_answer(tool_outputs)
    assert "Detected 1 instances" in answer
    assert "fire extinguisher" in answer
    assert "frame 150" in answer


@patch("backend.agent.executor.app")
def test_executor_end_to_end(mock_app):
    """Verify the executor correctly orchestrates the graph and formats results."""
    # Setup mock graph return state
    mock_app.invoke.return_value = {
        "parsed_intent": {"selected_tool": "search_visuals"},
        "tool_outputs": [{
            "tool": "search_visuals",
            "result": [{"track_id": 99, "camera_id": "cam_test", "confidence_score": 0.99}]
        }]
    }

    executor = VisionAgentExecutor()
    response = executor.execute("find the person with red backpack")

    # Verify input passing
    mock_app.invoke.assert_called_once()
    passed_state = mock_app.invoke.call_args[0][0]
    assert passed_state["user_query"] == "find the person with red backpack"

    # Verify output structure
    assert response["query"] == "find the person with red backpack"
    assert response["intent"]["selected_tool"] == "search_visuals"
    assert "Track 99" in response["final_answer"]
    assert len(response["raw_results"]) == 1
