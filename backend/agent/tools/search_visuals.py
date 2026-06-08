"""
VisionTraceAI — Semantic Visual Search Tool.

LangChain tool for the agent to semantically search visual data.
"""

from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool

from backend.storage.memory_layer import MemoryLayer
from app.services.embedder import SigLIPEmbeddingService

_memory_layer: MemoryLayer | None = None
_embedder: SigLIPEmbeddingService | None = None

def get_memory_subsystems():
    global _memory_layer, _embedder
    if _memory_layer is None:
        _memory_layer = MemoryLayer()
        _embedder = SigLIPEmbeddingService()
        _embedder.initialize()
    return _memory_layer, _embedder

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
    memory, embedder = get_memory_subsystems()
    
    # 1. Embed the text query into a vector
    augmented_query = f"a photo of {query}"
    vector_batch = embedder.encode_text([augmented_query])
    query_vector = vector_batch[0].tolist()
    
    # 2. Query Identity Memory (Qdrant -> Redis)
    entities = memory.find_similar(query_vector, top_k=limit)
    
    # Return structured dicts mapped from Entities
    return [
        {
            "track_id": e.track_id,
            "confidence_score": e.confidence_score,
            "camera_id": e.camera_id,
            "timestamp": e.last_seen,
            "crop_url": f"http://localhost:8000/crops/{Path(e.semantic_description.get('crop_path', '')).relative_to('data/crops').as_posix()}" if e.semantic_description.get('crop_path') else e.semantic_description.get('crop_url'),
            "trajectory_points": len(e.trajectory)
        }
        for e in entities
    ]
