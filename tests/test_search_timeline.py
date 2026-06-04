"""
Tests for the search_timeline agent tool.
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.agent.tools.search_timeline import parse_time_query, search_timeline


def test_parse_time_query_after():
    """Test parsing 'after 8pm' style queries."""
    start, end = parse_time_query("after 8pm")
    assert start == 20 * 3600.0
    assert end is None

    start, end = parse_time_query("after 9am")
    assert start == 9 * 3600.0
    assert end is None


def test_parse_time_query_between():
    """Test parsing 'between X-Ypm' style queries."""
    start, end = parse_time_query("between 5-6pm")
    assert start == 17 * 3600.0
    assert end == 18 * 3600.0

    start, end = parse_time_query("between 8-10am")
    assert start == 8 * 3600.0
    assert end == 10 * 3600.0


@pytest.fixture
def mock_store():
    """Mock the TrajectoryStore to prevent network calls to Redis."""
    with patch("backend.agent.tools.search_timeline.get_trajectory_store") as mock_get:
        mock_instance = MagicMock()
        mock_get.return_value = mock_instance
        yield mock_instance


def test_search_timeline_tool(mock_store):
    """Test that the tool correctly filters tracks based on trajectory logs."""
    # Mock track IDs in the global index
    mock_store.get_all_track_ids.return_value = [1, 2, 3]
    
    # Mock trajectory returns
    # Track 1 has observations between 5-6pm (17.5 hours * 3600 = 63000s)
    # Track 2 has no observations during this time
    # Track 3 has observations between 5-6pm
    def mock_get_trajectory(track_id, start_time, end_time):
        if track_id in (1, 3):
            return [{"timestamp": 17.5 * 3600}]
        return []
        
    mock_store.get_trajectory.side_effect = mock_get_trajectory
    
    # Execute LangChain tool
    results = search_timeline.invoke({"query": "between 5-6pm"})
    
    # Verify that only track 1 and 3 are returned
    assert results == [1, 3]
    
    # Verify the underlying store was called correctly for all tracks
    assert mock_store.get_trajectory.call_count == 3
