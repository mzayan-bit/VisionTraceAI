import json
import random
import numpy as np
from typing import Any

from app.utils.logger import get_logger
from backend.storage.redis_client import RedisClient

logger = get_logger(__name__)

# Predefined premium colors
COLORS = [
    '#3b82f6', # blue
    '#10b981', # green
    '#f59e0b', # yellow
    '#ef4444', # red
    '#8b5cf6', # purple
    '#ec4899', # pink
    '#06b6d4', # cyan
]

class ColorEngine:
    """Manages identity color assignment based on ReID embeddings."""
    
    def __init__(self, redis_client: RedisClient | None = None):
        self.redis = redis_client or RedisClient()
        if not self.redis.is_connected:
            try:
                self.redis.connect()
            except Exception as e:
                logger.warning(f"ColorEngine Redis connection failed: {e}")

    def assign_identity(self, track_id: int, reid_emb: np.ndarray | list[float], camera_source: str) -> dict[str, Any]:
        """Match embedding to existing identities or create new one, then assign a color."""
        if not self.redis.is_connected:
            return self._assign_random_color(track_id, camera_source)

        if isinstance(reid_emb, np.ndarray):
            emb_vec = reid_emb.flatten()
        else:
            emb_vec = np.array(reid_emb)
            
        # Normalize the embedding for cosine similarity
        norm = np.linalg.norm(emb_vec)
        if norm > 0:
            emb_vec = emb_vec / norm

        # 1. Fetch existing identities
        identity_keys = self.redis.keys("identity:emb:*")
        best_match_id = None
        best_score = -1.0
        
        for key in identity_keys:
            try:
                data = self.redis.get(key)
                if data:
                    stored_emb = np.array(json.loads(data))
                    score = float(np.dot(emb_vec, stored_emb))
                    if score > best_score:
                        best_score = score
                        best_match_id = key.split(":")[-1]
            except Exception:
                continue

        # 2. Check threshold (0.85)
        if best_match_id and best_score > 0.85:
            identity_id = best_match_id
            confidence = best_score
            logger.info(f"Matched track {track_id} to identity {identity_id} (score: {best_score:.2f})")
        else:
            identity_id = f"id_{track_id}_{random.randint(1000, 9999)}"
            confidence = 1.0
            # Store new embedding
            self.redis.set(f"identity:emb:{identity_id}", json.dumps(emb_vec.tolist()), ttl=86400)
            logger.info(f"Created new identity {identity_id} for track {track_id}")

        # 3. Assign Color
        color_key = f"identity:color:{identity_id}"
        color = self.redis.get(color_key)
        if not color:
            color = random.choice(COLORS)
            self.redis.set(color_key, color, ttl=86400)

        # 4. Cache track_id mapping for the WebSocket stream
        mapping = {
            "color": color,
            "confidence": confidence,
            "camera_source": camera_source,
            "identity_id": identity_id
        }
        self.redis.set(f"track_color:{track_id}", json.dumps(mapping), ttl=3600)
        
        return mapping

    def _assign_random_color(self, track_id: int, camera_source: str) -> dict[str, Any]:
        """Fallback if Redis is unavailable."""
        color = COLORS[track_id % len(COLORS)]
        return {
            "color": color,
            "confidence": 0.0,
            "camera_source": camera_source,
            "identity_id": f"fallback_{track_id}"
        }

    def get_track_color(self, track_id: int) -> str | None:
        """Fetch assigned color for a track_id from Redis."""
        if not self.redis.is_connected:
            return COLORS[track_id % len(COLORS)]
            
        data = self.redis.get(f"track_color:{track_id}")
        if data:
            try:
                mapping = json.loads(data)
                return mapping.get("color")
            except Exception:
                pass
        return None
