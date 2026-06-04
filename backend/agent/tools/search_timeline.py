"""
VisionTraceAI — Semantic Timeline Search Tool.

LangChain tool for filtering tracks by temporal descriptions.
"""

import re
from typing import List, Optional, Tuple

from langchain_core.tools import tool

from backend.storage.trajectory_store import TrajectoryStore


def parse_time_query(query: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse a natural language time query into start and end seconds.
    
    Handles simple formats like "after 8pm", "between 5-6pm".
    Assumes standard 24-hour daily cycle mapped to seconds.
    """
    query = query.lower()
    start_time = None
    end_time = None
    
    # "between 5-6pm"
    match_between = re.search(r"between (\d+)-(\d+)(am|pm)", query)
    if match_between:
        h1 = int(match_between.group(1))
        h2 = int(match_between.group(2))
        is_pm = match_between.group(3) == "pm"
        
        if is_pm:
            if h1 < 12: h1 += 12
            if h2 < 12: h2 += 12
            
        start_time = float(h1 * 3600)
        end_time = float(h2 * 3600)
        return start_time, end_time
        
    # "after 8pm"
    match_after = re.search(r"after (\d+)(am|pm)", query)
    if match_after:
        hour = int(match_after.group(1))
        is_pm = match_after.group(2) == "pm"
        if is_pm and hour < 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
        start_time = float(hour * 3600)
        
    return start_time, end_time


# Singleton store instance
_store: TrajectoryStore | None = None

def get_trajectory_store() -> TrajectoryStore:
    """Get or initialize the TrajectoryStore singleton."""
    global _store
    if _store is None:
        _store = TrajectoryStore()
    return _store


@tool
def search_timeline(query: str) -> List[int]:
    """
    Timeline search tool for querying events by time.
    
    Filters tracks based on temporal descriptions like 'after 8pm' or 'between 5-6pm'.
    
    Args:
        query: Natural language time query.
        
    Returns:
        List of track IDs that were observed during the specified time period.
    """
    start_time, end_time = parse_time_query(query)
    
    store = get_trajectory_store()
    
    # Ensure connection to Redis
    try:
        store.connect()
    except Exception:
        pass
        
    try:
        all_track_ids = store.get_all_track_ids()
    except Exception:
        all_track_ids = []
        
    filtered_track_ids = []
    
    for track_id in all_track_ids:
        try:
            # Query trajectory logs to see if track was active within the bounds
            trajectory = store.get_trajectory(track_id, start_time, end_time)
            if trajectory:
                filtered_track_ids.append(track_id)
        except Exception:
            continue
            
    return filtered_track_ids
