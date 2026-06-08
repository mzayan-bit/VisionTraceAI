"""
VisionTraceAI — Semantic Visual Search Tool.

LangChain tool for the agent to semantically search visual data.
"""

from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool

from app.services.search_engine import VisionSearchEngine

# Singleton instance to avoid reloading models on every tool call
_search_engine: VisionSearchEngine | None = None

def get_search_engine() -> VisionSearchEngine:
    """Get or initialize the search engine singleton."""
    global _search_engine
    if _search_engine is None:
        _search_engine = VisionSearchEngine()
        # Fallback to memory if Qdrant isn't running
        _search_engine.initialize()
    return _search_engine

@tool
def search_visuals(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Semantic visual search tool.
    
    Searches the vector database for visual crops matching the provided natural language text query 
    (e.g., 'person in green shirt', 'red backpack', 'walking person').
    Internally, this creates a SigLIP embedding of the text, normalizes it, and queries Qdrant.
    
    Args:
        query: A text description of the person or object to find.
        limit: Maximum number of results to return.
        
    Returns:
        A list of matching records containing track_ids, confidence scores, and camera_id metadata.
    """
    engine = get_search_engine()
    results = engine.search(query, limit=limit)
    
    # Return structured dicts with the required fields
    return [
        {
            "track_id": r.track_id,
            "confidence_score": r.score,
            "camera_id": r.camera_id,
            "timestamp": r.timestamp,
            "crop_url": f"http://localhost:8000/crops/{Path(r.crop_path).relative_to('data/crops').as_posix()}" if r.crop_path else None,
        }
        for r in results
    ]
