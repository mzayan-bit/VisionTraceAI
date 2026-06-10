"""
VisionTraceAI — Global Scene Memory Manager.

Handles dual-database ingestion:
1. Qdrant for visual embeddings (semantic search).
2. Redis for temporal logs and spatial trajectories.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

import redis
from backend.storage.redis_client import RedisClient
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config.settings import get_settings
from app.utils.logger import get_logger
from backend.streaming.feature_engine import FeatureEngine

logger = get_logger(__name__)


class MemoryManager:
    """Manages global scene memory across Redis and Qdrant."""

    def __init__(self):
        self.settings = get_settings()
        
        # Redis Connection
        self.redis_client: RedisClient | None = None
        
        # Qdrant Connection
        self.qdrant_client: QdrantClient | None = None
        self.collection_name = "person_tracks"
        self.vector_size = 768  # Native output size of google/siglip-base-patch16-224
        
        # Lazy loaded Text Encoder for semantic searches
        self.feature_engine = None

    def init_redis(self) -> None:
        """Initialize connection to local Redis."""
        try:
            self.redis_client = RedisClient()
            self.redis_client.connect()
            logger.info("Redis initialized successfully for Global Scene Memory.")
        except Exception as e:
            logger.error("Failed to connect to Redis", extra={"error": str(e)})
            raise RuntimeError(f"Redis connection failed: {e}")

    def init_qdrant(self) -> None:
        """Initialize connection to Qdrant and create the collection."""
        try:
            self.qdrant_client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                timeout=10
            )
            
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
            else:
                logger.info(f"Qdrant collection '{self.collection_name}' already exists.")
                
        except Exception as e:
            logger.error("Failed to initialize Qdrant", extra={"error": str(e)})
            raise RuntimeError(f"Qdrant initialization failed: {e}")

    def connect(self) -> None:
        """Helper to initialize both databases."""
        self.init_redis()
        self.init_qdrant()

    def upsert_track_data(self, track_dict: Dict[str, Any]) -> None:
        """
        Ingest dictionary from feature engine into Qdrant and Redis.
        
        Expected dictionary format:
        {
            "track_id": int,
            "timestamp": float,
            "camera_id": str,
            "siglip_embedding": List[float],
            "detected_color": str,
            "bbox": dict (optional spatial coords)
        }
        """
        if self.redis_client is None or self.qdrant_client is None:
            self.connect()
            
        track_id = track_dict.get("track_id")
        if track_id is None:
            logger.warning("Upsert failed: track_dict missing 'track_id'")
            return
            
        camera_id = track_dict.get("camera_id", "unknown")
        timestamp = track_dict.get("timestamp", 0.0)
        embedding = track_dict.get("siglip_embedding")
        detected_color = track_dict.get("detected_color", "unknown")
        bbox = track_dict.get("bbox", {})
        
        try:
            # 1. Upsert into Qdrant
            if embedding:
                # Generate a stable UUID based on track ID and camera
                point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{camera_id}_{track_id}"))
                
                payload = {
                    "track_id": track_id,
                    "camera_id": camera_id,
                    "detected_color": detected_color,
                    "last_seen": timestamp
                }
                
                if self.qdrant_client:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=[
                            qmodels.PointStruct(
                                id=point_id,
                                vector=embedding,
                                payload=payload
                            )
                        ]
                    )
                
            # 2. Append trajectory to Redis List
            redis_key = f"trajectory:{camera_id}:{track_id}"
            trajectory_point = {
                "timestamp": timestamp,
                "bbox": bbox,
                "detected_color": detected_color
            }
            
            if self.redis_client and self.redis_client._ensure_client():
                client = self.redis_client._ensure_client()
                client.rpush(redis_key, json.dumps(trajectory_point))
                client.ltrim(redis_key, -1000, -1)
            
        except Exception as e:
            logger.error("Error upserting track data", extra={"error": str(e), "track_id": track_id})

    def search_similar_appearance(self, text_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Takes a text string (e.g., "person wearing white shirt"), computes vector, 
        and searches Qdrant for matching tracks.
        """
        if self.qdrant_client is None:
            self.connect()
            
        if self.feature_engine is None:
            self.feature_engine = FeatureEngine()
            self.feature_engine.initialize()
            
        try:
            # We construct a dummy batch of prompts and get the embedding
            # Since FeatureEngine is optimized for image processing in the current code,
            # we access the tokenizer/model directly or rely on a standard text encoder
            
            # Let's cleanly encode text using transformers directly here to ensure
            # it matches the requirement specifically.
            import torch
            with torch.no_grad():
                if self.feature_engine and self.feature_engine.processor and self.feature_engine.model:
                    inputs = self.feature_engine.processor(text=[text_query], padding="max_length", return_tensors="pt")
                    inputs = {k: v.to(self.feature_engine.device) for k, v in inputs.items()}
                    
                    features = self.feature_engine.model.get_text_features(**inputs)
                    if hasattr(features, "pooler_output"):
                        features = features.pooler_output
                    elif hasattr(features, "text_embeds"):
                        features = features.text_embeds
                        
                    norm = features.norm(p=2, dim=-1, keepdim=True)
                    vector = features.div(norm)[0].cpu().numpy().tolist()
                else:
                    return []
                
            # Query Qdrant
            if self.qdrant_client:
                search_results = self.qdrant_client.query_points(
                    collection_name=self.collection_name,
                    query=vector,
                    limit=limit
                ).points
            else:
                search_results = []
            
            # Format output
            results = []
            for hit in search_results:
                results.append({
                    "track_id": hit.payload.get("track_id"),
                    "camera_id": hit.payload.get("camera_id"),
                    "detected_color": hit.payload.get("detected_color"),
                    "score": hit.score
                })
                
            return results
            
        except Exception as e:
            logger.error("Error during semantic search", extra={"error": str(e)}, exc_info=True)
            return []
