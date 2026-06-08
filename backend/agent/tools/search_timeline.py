"""
VisionTraceAI — Semantic Timeline Search Tool.

LangChain tool for filtering tracks by temporal descriptions.
"""

import re
from typing import List, Optional, Tuple

from langchain_core.tools import tool

from backend.storage.memory_layer import MemoryLayer
from pathlib import Path


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
_memory: MemoryLayer | None = None

def get_memory_layer() -> MemoryLayer:
    """Get or initialize the MemoryLayer singleton."""
    global _memory
    if _memory is None:
        _memory = MemoryLayer()
    return _memory


@tool
def search_timeline(query: str) -> List[dict]:
    """
    Timeline search tool for querying events by time.
    
    Filters tracks based on temporal descriptions like 'after 8pm' or 'between 5-6pm'.
    
    Args:
        query: Natural language time query.
        
    Returns:
        List of entity dictionaries that were observed during the specified time period.
    """
    start_time, end_time = parse_time_query(query)
    
    memory = get_memory_layer()
    entities = memory.query_scene(start_time, end_time)
            
    return [
        {
            "track_id": e.track_id,
            "camera_id": e.camera_id,
            "timestamp": e.last_seen,
            "trajectory_points": len(e.trajectory),
            "crop_url": f"http://localhost:8000/crops/{Path(e.semantic_description.get('crop_path', '')).relative_to('data/crops').as_posix()}" if e.semantic_description.get('crop_path') else e.semantic_description.get('crop_url'),
        }
        for e in entities
    ]
