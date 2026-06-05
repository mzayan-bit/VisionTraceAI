"""
Tests for the FastAPI backbone endpoints.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@patch("api.main.get_agent_executor")
def test_chat_endpoint_success(mock_get_executor):
    """Test the /chat endpoint with a mocked agent executor."""
    # Setup mock executor
    mock_executor = mock_get_executor.return_value
    mock_executor.execute.return_value = {
        "query": "Find the person in a red shirt",
        "intent": {"selected_tool": "search_visuals", "reasoning_trace": "Looking for red shirt"},
        "final_answer": "Found 1 match.",
        "raw_results": [{"confidence_score": 0.95, "camera_id": "cam_1"}],
    }
    
    # Send request
    payload = {"query": "Find the person in a red shirt"}
    response = client.post("/chat", json=payload)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["final_answer"] == "Found 1 match."
    assert "processing_time_sec" in data
    assert len(data["raw_results"]) == 1


@patch("api.main.get_agent_executor")
def test_chat_endpoint_error(mock_get_executor):
    """Test the /chat endpoint when the executor raises an exception."""
    # Setup mock executor to raise exception
    mock_executor = mock_get_executor.return_value
    mock_executor.execute.side_effect = Exception("Agent execution failed")
    
    # Send request
    payload = {"query": "Find the person in a red shirt"}
    response = client.post("/chat", json=payload)
    
    # Assertions
    assert response.status_code == 500
    assert response.json()["detail"] == "Agent execution failed"
