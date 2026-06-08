"""
VisionTraceAI — Unified Memory Abstraction Layer.

This module provides a unified interface for the agent to interact with both
Redis (spatial/trajectory memory) and Qdrant (semantic/appearance memory),
abstracting away raw database queries into 'Entity' objects.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.storage.trajectory_store import TrajectoryStore, TrackNotFoundError
from app.services.database import QdrantService, QdrantServiceError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Entity(BaseModel):
    """
    Unified representation of a tracked person/object across the system.
    """
    track_id: int
    camera_id: str
    first_seen: float
    last_seen: float
    total_observations: int
    embedding_id: Optional[str] = None
    trajectory: List[Dict[str, Any]] = Field(default_factory=list)
    semantic_description: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0


class MemoryLayer:
    """
    Unified Memory Layer combining TrajectoryStore and QdrantService.
    """
    def __init__(self):
        self.trajectory_store = TrajectoryStore()
        self.qdrant_service = QdrantService()
        self._connected = False

    def connect(self):
        if not self._connected:
            self.trajectory_store.connect()
            self.qdrant_service.connect()
            self._connected = True

    def close(self):
        if self._connected:
            self.trajectory_store.close()
            self._connected = False

    def get_entity(self, track_id: int) -> Optional[Entity]:
        """Fetch a complete Entity by its track_id."""
        self.connect()
        try:
            meta = self.trajectory_store.get_track(track_id)
            trajectory = self.trajectory_store.get_trajectory(track_id)
            
            embedding_id = meta.get("embedding_id")
            semantic_description = {}
            
            # If there's an embedding ID, we might want to fetch payload from Qdrant,
            # but Qdrant's primary purpose is search. However, the payload is often 
            # stored during indexing. We can do a point lookup if needed, but for now 
            # we rely on the trajectory crops if available.
            
            # Extract basic semantic info from the most recent trajectory observation if needed
            if trajectory:
                latest = trajectory[-1]
                if "crop_url" in latest:
                    semantic_description["crop_url"] = latest["crop_url"]
                
            return Entity(
                track_id=int(meta["track_id"]),
                camera_id=meta["camera_id"],
                first_seen=float(meta["first_seen"]),
                last_seen=float(meta["last_seen"]),
                total_observations=int(meta["total_observations"]),
                embedding_id=embedding_id,
                trajectory=trajectory,
                semantic_description=semantic_description
            )
        except TrackNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error fetching entity {track_id}", extra={"error": str(e)})
            return None

    def query_scene(self, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Entity]:
        """
        Query Episodic Memory for all entities active within a time range.
        Currently, scans recent tracks and filters by time if provided.
        """
        self.connect()
        entities = []
        try:
            # We fetch recent tracks and filter
            recent_tracks = self.trajectory_store.get_recent_tracks(limit=100)
            
            for track in recent_tracks:
                first = float(track.get("first_seen", 0))
                last = float(track.get("last_seen", 0))
                
                # Check overlap
                if start_time is not None and last < start_time:
                    continue
                if end_time is not None and first > end_time:
                    continue
                    
                entity = self.get_entity(int(track["track_id"]))
                if entity:
                    entities.append(entity)
                    
            return entities
        except Exception as e:
            logger.error("Error querying scene", extra={"error": str(e)})
            return []

    def find_similar(self, query_vector: List[float], top_k: int = 5) -> List[Entity]:
        """
        Query Identity Memory (Qdrant) and return hydrated Entities.
        """
        self.connect()
        entities = []
        try:
            results = self.qdrant_service.search(query_vector=query_vector, top_k=top_k)
            
            for res in results:
                payload = res.get("payload", {})
                track_id = payload.get("track_id")
                score = res.get("score", 0.0)
                
                if track_id is not None:
                    entity = self.get_entity(int(track_id))
                    if entity:
                        entity.confidence_score = score
                        # Enrich semantic description with Qdrant payload
                        entity.semantic_description.update(payload)
                        entities.append(entity)
                        
            return entities
        except Exception as e:
            logger.error("Error finding similar entities", extra={"error": str(e)})
            return []
