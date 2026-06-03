"""
VisionTraceAI — Identity Manager.

Manages cross-camera identity mappings using Redis.
Provides capabilities to merge, split, and track ownership of global identities.
"""

from __future__ import annotations

import uuid
from typing import Any

from backend.storage.redis_client import RedisClient, RedisConnectionError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _track_mapping_key(camera_id: str, track_id: int) -> str:
    """Key for looking up the global person ID for a specific track."""
    return f"IdentityMapping:{camera_id}:{track_id}"


def _global_identity_key(global_id: str) -> str:
    """Key for looking up all tracks owned by a global person ID."""
    return f"GlobalIdentity:{global_id}"


class IdentityManager:
    """
    Manages global person identities across multiple cameras.
    Backed by Redis for fast access and persistence.
    """

    def __init__(self, redis_client: RedisClient | None = None) -> None:
        self.redis = redis_client or RedisClient()
        self._owns_client = redis_client is None
        logger.info("IdentityManager initialised")

    def connect(self) -> None:
        """Connect the underlying Redis client (if we own it)."""
        if self._owns_client:
            self.redis.connect()

    def close(self) -> None:
        """Close the underlying Redis client (if we own it)."""
        if self._owns_client:
            self.redis.close()

    def __enter__(self) -> IdentityManager:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def generate_global_id(self) -> str:
        """Generate a new unique global person ID."""
        return f"global_{uuid.uuid4().hex[:8]}"

    def get_global_id(self, camera_id: str, track_id: int) -> str | None:
        """Get the global person ID for a given camera track."""
        client = self.redis._ensure_client()
        result = client.get(_track_mapping_key(camera_id, track_id))
        if result is None:
            return None
        return result.decode("utf-8") if isinstance(result, bytes) else str(result)

    def get_tracks_for_global_id(self, global_id: str) -> list[dict[str, Any]]:
        """Retrieve all tracks owned by a global ID.
        
        Returns:
            A list of dicts: [{'camera_id': '...', 'track_id': ...}]
        """
        client = self.redis._ensure_client()
        members = client.smembers(_global_identity_key(global_id))
        tracks = []
        for member in members:
            mem_str = member.decode("utf-8") if isinstance(member, bytes) else str(member)
            cam_id, trk_id_str = mem_str.rsplit(":", 1)
            tracks.append({"camera_id": cam_id, "track_id": int(trk_id_str)})
        return tracks

    def assign_track(self, camera_id: str, track_id: int, global_id: str) -> None:
        """Assign a track to a global ID."""
        client = self.redis._ensure_client()
        mapping_key = _track_mapping_key(camera_id, track_id)
        global_key = _global_identity_key(global_id)
        track_str = f"{camera_id}:{track_id}"
        
        # Check if already assigned
        existing_global = self.get_global_id(camera_id, track_id)
        
        pipe = client.pipeline(transaction=True)
        if existing_global and existing_global != global_id:
            # Remove from old global ID
            pipe.srem(_global_identity_key(existing_global), track_str)
            
        pipe.set(mapping_key, global_id)
        pipe.sadd(global_key, track_str)
        pipe.execute()
        
        logger.info(
            "Track assigned to global identity",
            extra={"camera_id": camera_id, "track_id": track_id, "global_id": global_id}
        )

    def merge_identities(self, camera1: str, track1: int, camera2: str, track2: int) -> str:
        """Merge two tracks into the same global identity.
        
        If neither has a global ID, a new one is created.
        If one has a global ID, the other is assigned to it.
        If both have different global IDs, the second is merged into the first.
        
        Returns:
            The resulting global_person_id.
        """
        id1 = self.get_global_id(camera1, track1)
        id2 = self.get_global_id(camera2, track2)
        
        if id1 and id2 and id1 != id2:
            # Merge id2 into id1
            tracks2 = self.get_tracks_for_global_id(id2)
            for t in tracks2:
                self.assign_track(t["camera_id"], t["track_id"], id1)
            final_id = id1
        elif id1:
            self.assign_track(camera2, track2, id1)
            final_id = id1
        elif id2:
            self.assign_track(camera1, track1, id2)
            final_id = id2
        else:
            final_id = self.generate_global_id()
            self.assign_track(camera1, track1, final_id)
            self.assign_track(camera2, track2, final_id)
            
        logger.info(
            "Identities merged",
            extra={
                "track1": f"{camera1}:{track1}",
                "track2": f"{camera2}:{track2}",
                "global_id": final_id
            }
        )
        return final_id

    def split_identity(self, camera_id: str, track_id: int) -> str:
        """Remove a track from its current global ID and assign it a new one.
        
        Returns:
            The new global_person_id for the track.
        """
        existing_global = self.get_global_id(camera_id, track_id)
        new_global = self.generate_global_id()
        
        if existing_global:
            client = self.redis._ensure_client()
            track_str = f"{camera_id}:{track_id}"
            client.srem(_global_identity_key(existing_global), track_str)
            logger.info(
                "Track split from identity",
                extra={"camera_id": camera_id, "track_id": track_id, "old_global_id": existing_global}
            )
            
        self.assign_track(camera_id, track_id, new_global)
        return new_global


def _run_validation() -> None:
    """Standalone validation of identity management."""
    print("═" * 50)
    print("🔍 VisionTraceAI — Identity Manager Validation")
    print("═" * 50)
    
    manager = IdentityManager()
    try:
        manager.connect()
        print("✅ Redis Connected")
        
        # Test Case 1: Merge
        print("\nTesting: Identity Merge (Camera1: Track 15 + Camera2: Track 82)")
        global_id = manager.merge_identities("Camera1", 15, "Camera2", 82)
        
        id1 = manager.get_global_id("Camera1", 15)
        id2 = manager.get_global_id("Camera2", 82)
        
        assert id1 == id2 == global_id, "Merge failed: IDs do not match"
        print(f"✅ Merge Successful! Global ID: {global_id}")
        
        # Test Case 2: Track ownership
        tracks = manager.get_tracks_for_global_id(global_id)
        assert len(tracks) == 2, "Expected 2 tracks owned by global ID"
        print("✅ Track ownership verified")
        
        # Test Case 3: Split
        print("\nTesting: Identity Split (Splitting Camera2: Track 82)")
        new_id = manager.split_identity("Camera2", 82)
        
        id1_after = manager.get_global_id("Camera1", 15)
        id2_after = manager.get_global_id("Camera2", 82)
        
        assert id1_after == global_id, "Track 15 should retain old ID"
        assert id2_after == new_id, "Track 82 should have new ID"
        assert id1_after != id2_after, "IDs should now be different"
        print(f"✅ Split Successful! New Global ID for Track 82: {new_id}")
        
    except Exception as exc:
        print(f"❌ Validation failed: {exc}")
        raise SystemExit(1)
    finally:
        manager.close()
        print("\n" + "═" * 50)


if __name__ == "__main__":
    _run_validation()
