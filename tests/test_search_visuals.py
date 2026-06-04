"""
Tests for the search_visuals agent tool.
"""

from unittest.mock import MagicMock, patch

import pytest
from app.models.search import SearchResult

from backend.agent.tools.search_visuals import search_visuals


@pytest.fixture
def mock_search_engine():
    """Mock the VisionSearchEngine to prevent network calls to Qdrant/SigLIP."""
    with patch("backend.agent.tools.search_visuals.get_search_engine") as mock_get:
        mock_engine = MagicMock()
        mock_get.return_value = mock_engine
        yield mock_engine


def test_search_visuals_tool(mock_search_engine):
    """Test that the tool correctly wraps the search engine and formats results."""
    # Setup mock results
    mock_result_1 = SearchResult(
        score=0.95,
        track_id=10,
        camera_id="cam_01",
        crop_path="/fake/path/1.jpg",
        timestamp=123.45,
        payload={}
    )
    mock_search_engine.search.return_value = [mock_result_1]

    # Test the tool queries requested by the user
    queries = [
        "person in green shirt",
        "red backpack",
        "walking person"
    ]
    
    for query in queries:
        # LangChain tools use .invoke()
        results = search_visuals.invoke({"query": query, "limit": 5})
        
        # Verify the underlying engine was called correctly
        mock_search_engine.search.assert_called_with(query, limit=5)
        
        # Verify output formatting matches the required specification
        assert len(results) == 1
        assert results[0]["track_id"] == 10
        assert results[0]["confidence_score"] == 0.95
        assert results[0]["camera_id"] == "cam_01"
        assert results[0]["timestamp"] == 123.45
