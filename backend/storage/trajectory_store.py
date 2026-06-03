"""
VisionTraceAI — Temporal Trajectory Store.

Persists and retrieves person movement histories in Redis.  Each track's
metadata is stored as a Redis Hash, its ordered sequence of observations
(trajectory) as a Sorted Set keyed by timestamp, and per-camera indices
are maintained automatically for fast cross-camera lookups.

Redis key schema
================

``Track:{track_id}``
    Hash — static metadata for the track (camera_id, first_seen, last_seen,
    total_observations, embedding_id, status).

``Trajectory:{track_id}``
    Sorted Set — each member is a JSON-encoded observation dict, scored by
    its ``timestamp`` so the set is always in chronological order.

``Camera:{camera_id}``
    Set — contains all ``track_id`` values observed on this camera,
    enabling fast "list all tracks for camera X" queries.

``TrackIndex``
    Set — global index of all active track IDs.

Usage::

    from backend.storage.trajectory_store import TrajectoryStore

    store = TrajectoryStore()
    store.connect()

    store.save_track(
        track_id=42,
        camera_id="cam_1",
        timestamp=12.5,
        bbox={"x1": 100, "y1": 200, "x2": 300, "y2": 500},
        embedding_id="qdrant-point-uuid",
    )

    track = store.get_track(42)
    history = store.get_trajectory(42)

    store.close()
"""

from __future__ import annotations

import json
import time as _time
from typing import Any

from backend.storage.redis_client import RedisClient, RedisConnectionError
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class TrajectoryStoreError(Exception):
    """Base exception for trajectory store operations."""


class TrackNotFoundError(TrajectoryStoreError):
    """Raised when a requested track does not exist."""


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------
def _track_key(track_id: int) -> str:
    return f"Track:{track_id}"


def _trajectory_key(track_id: int) -> str:
    return f"Trajectory:{track_id}"


def _camera_key(camera_id: str) -> str:
    return f"Camera:{camera_id}"


_INDEX_KEY = "TrackIndex"


# ---------------------------------------------------------------------------
# Trajectory Store
# ---------------------------------------------------------------------------
class TrajectoryStore:
    """Temporal trajectory store backed by Redis.

    Provides a high-level API for persisting, updating, and querying
    person movement histories.  Internally it uses:

    - **Hashes** for track metadata.
    - **Sorted Sets** (scored by timestamp) for trajectory observations.
    - **Sets** for per-camera and global track indices.

    Attributes:
        redis: Underlying :class:`RedisClient` instance.
        default_ttl: Optional TTL (seconds) applied to track keys.
    """

    def __init__(
        self,
        redis_client: RedisClient | None = None,
        default_ttl: int | None = None,
    ) -> None:
        self.redis = redis_client or RedisClient()
        self.default_ttl = default_ttl
        self._owns_client = redis_client is None

        logger.info(
            "TrajectoryStore initialised",
            extra={"default_ttl": default_ttl},
        )

    # ── Lifecycle ────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Connect the underlying Redis client (if we own it)."""
        if self._owns_client:
            self.redis.connect()

    def close(self) -> None:
        """Close the underlying Redis client (if we own it)."""
        if self._owns_client:
            self.redis.close()

    def __enter__(self) -> TrajectoryStore:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ── Write Operations ─────────────────────────────────────────────────

    def save_track(
        self,
        track_id: int,
        camera_id: str,
        timestamp: float,
        bbox: dict[str, float],
        embedding_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new track and record its first observation.

        If the track already exists, this behaves like :meth:`update_track`
        — it appends a new observation and refreshes metadata.

        Args:
            track_id: Persistent tracking ID from the detector/tracker.
            camera_id: Source camera identifier.
            timestamp: Observation time (seconds from video start).
            bbox: Bounding box dict with keys ``x1, y1, x2, y2``.
            embedding_id: Optional Qdrant point UUID for this crop.

        Returns:
            Dictionary echo of the stored track metadata.
        """
        client = self.redis._ensure_client()
        tk = _track_key(track_id)
        trk = _trajectory_key(track_id)
        ck = _camera_key(camera_id)

        pipe = client.pipeline(transaction=True)

        # -- Track metadata hash ----------------------------------------
        existing = client.exists(tk)
        now_iso = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())

        if not existing:
            # Brand-new track
            meta = {
                "track_id": str(track_id),
                "camera_id": camera_id,
                "first_seen": str(timestamp),
                "last_seen": str(timestamp),
                "total_observations": "1",
                "embedding_id": embedding_id or "",
                "status": "active",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            pipe.hset(tk, mapping=meta)
        else:
            # Update existing track
            pipe.hset(tk, mapping={
                "last_seen": str(timestamp),
                "updated_at": now_iso,
            })
            pipe.hincrby(tk, "total_observations", 1)
            if embedding_id:
                pipe.hset(tk, "embedding_id", embedding_id)

        # -- Trajectory sorted set (score = timestamp) ------------------
        observation = json.dumps({
            "track_id": track_id,
            "camera_id": camera_id,
            "timestamp": timestamp,
            "bbox": bbox,
            "embedding_id": embedding_id or "",
            "recorded_at": now_iso,
        })
        pipe.zadd(trk, {observation: timestamp})

        # -- Camera index -----------------------------------------------
        pipe.sadd(ck, str(track_id))

        # -- Global index -----------------------------------------------
        pipe.sadd(_INDEX_KEY, str(track_id))

        # -- Optional TTL -----------------------------------------------
        if self.default_ttl:
            pipe.expire(tk, self.default_ttl)
            pipe.expire(trk, self.default_ttl)

        pipe.execute()

        logger.info(
            "Track saved",
            extra={
                "track_id": track_id,
                "camera_id": camera_id,
                "timestamp": timestamp,
                "is_new": not existing,
            },
        )

        return self.get_track(track_id)

    def update_track(
        self,
        track_id: int,
        camera_id: str,
        timestamp: float,
        bbox: dict[str, float],
        embedding_id: str | None = None,
    ) -> dict[str, Any]:
        """Append a new observation to an existing track.

        This is an alias that delegates to :meth:`save_track` — the
        save method is upsert-safe, so it handles both new and existing
        tracks identically.

        Raises:
            TrackNotFoundError: If the track does not exist and you want
                strict-update semantics, check :meth:`track_exists` first.
        """
        return self.save_track(
            track_id=track_id,
            camera_id=camera_id,
            timestamp=timestamp,
            bbox=bbox,
            embedding_id=embedding_id,
        )

    # ── Read Operations ──────────────────────────────────────────────────

    def get_track(self, track_id: int) -> dict[str, Any]:
        """Retrieve metadata for a single track.

        Returns:
            Dictionary with track metadata fields.

        Raises:
            TrackNotFoundError: If the track does not exist.
        """
        client = self.redis._ensure_client()
        tk = _track_key(track_id)

        data = client.hgetall(tk)
        if not data:
            raise TrackNotFoundError(f"Track {track_id} not found")

        return dict(data)

    def track_exists(self, track_id: int) -> bool:
        """Check whether a track exists."""
        client = self.redis._ensure_client()
        return bool(client.exists(_track_key(track_id)))

    def get_trajectory(
        self,
        track_id: int,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve the ordered observation history for a track.

        Args:
            track_id: Target track ID.
            start_time: Optional lower timestamp bound (inclusive).
            end_time: Optional upper timestamp bound (inclusive).

        Returns:
            List of observation dicts in chronological order.

        Raises:
            TrackNotFoundError: If the track does not exist.
        """
        client = self.redis._ensure_client()
        trk = _trajectory_key(track_id)

        if not client.exists(trk):
            raise TrackNotFoundError(f"Trajectory for track {track_id} not found")

        lo = start_time if start_time is not None else "-inf"
        hi = end_time if end_time is not None else "+inf"

        raw = client.zrangebyscore(trk, lo, hi)  # type: ignore[arg-type]
        return [json.loads(entry) for entry in raw]

    def get_trajectory_count(self, track_id: int) -> int:
        """Return the number of observations in a track's trajectory."""
        client = self.redis._ensure_client()
        return client.zcard(_trajectory_key(track_id))  # type: ignore[return-value]

    def delete_track(self, track_id: int) -> bool:
        """Delete a track, its trajectory, and remove from indices.

        Returns:
            ``True`` if the track existed and was deleted, ``False`` otherwise.
        """
        client = self.redis._ensure_client()
        tk = _track_key(track_id)

        if not client.exists(tk):
            logger.info("Track not found for deletion", extra={"track_id": track_id})
            return False

        # Read camera_id before deleting so we can clean the camera index
        camera_id = client.hget(tk, "camera_id")

        pipe = client.pipeline(transaction=True)
        pipe.delete(tk)
        pipe.delete(_trajectory_key(track_id))
        if camera_id:
            pipe.srem(_camera_key(camera_id), str(track_id))  # type: ignore[arg-type]
        pipe.srem(_INDEX_KEY, str(track_id))
        pipe.execute()

        logger.info("Track deleted", extra={"track_id": track_id})
        return True

    # ── Query Operations ─────────────────────────────────────────────────

    def get_recent_tracks(
        self,
        limit: int = 20,
        camera_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve the most recently updated tracks.

        Args:
            limit: Maximum number of tracks to return.
            camera_id: If provided, restrict to tracks from this camera.

        Returns:
            List of track metadata dicts, sorted by ``last_seen`` descending.
        """
        client = self.redis._ensure_client()

        if camera_id:
            track_ids = client.smembers(_camera_key(camera_id))
        else:
            track_ids = client.smembers(_INDEX_KEY)

        if not track_ids:
            return []

        # Fetch metadata for each track
        tracks: list[dict[str, Any]] = []
        for tid in track_ids:
            data = client.hgetall(_track_key(int(tid)))  # type: ignore[arg-type]
            if data:
                tracks.append(dict(data))

        # Sort by last_seen descending
        tracks.sort(key=lambda t: float(t.get("last_seen", 0)), reverse=True)
        return tracks[:limit]

    def get_tracks_by_camera(self, camera_id: str) -> list[dict[str, Any]]:
        """Retrieve all track metadata for a given camera.

        Args:
            camera_id: Camera identifier.

        Returns:
            List of track metadata dicts.
        """
        client = self.redis._ensure_client()
        track_ids = client.smembers(_camera_key(camera_id))

        if not track_ids:
            return []

        tracks: list[dict[str, Any]] = []
        for tid in track_ids:
            data = client.hgetall(_track_key(int(tid)))  # type: ignore[arg-type]
            if data:
                tracks.append(dict(data))

        return tracks

    def get_all_track_ids(self) -> list[int]:
        """Return all track IDs in the global index."""
        client = self.redis._ensure_client()
        raw = client.smembers(_INDEX_KEY)
        return sorted(int(tid) for tid in raw)  # type: ignore[arg-type]

    def get_camera_ids(self) -> list[str]:
        """Return all camera IDs that have at least one track."""
        client = self.redis._ensure_client()
        keys = client.keys("Camera:*")
        return sorted(k.split(":", 1)[1] for k in keys)  # type: ignore[union-attr]

    # ── Stats ────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Return aggregate statistics about the trajectory store."""
        client = self.redis._ensure_client()
        total_tracks = client.scard(_INDEX_KEY)
        camera_ids = self.get_camera_ids()

        return {
            "total_tracks": total_tracks,
            "total_cameras": len(camera_ids),
            "camera_ids": camera_ids,
        }

    # ── Bulk ─────────────────────────────────────────────────────────────

    def flush_all_tracks(self) -> int:
        """Delete ALL tracks, trajectories, and indices.

        **Destructive** — intended for tests and reset workflows only.

        Returns:
            Number of track IDs that were removed.
        """
        track_ids = self.get_all_track_ids()
        if not track_ids:
            return 0

        for tid in track_ids:
            self.delete_track(tid)

        logger.warning(
            "All tracks flushed",
            extra={"count": len(track_ids)},
        )
        return len(track_ids)


# ---------------------------------------------------------------------------
# Standalone validation
# ---------------------------------------------------------------------------
def _run_validation() -> None:
    """Store 100 sample trajectories, retrieve them, verify correctness."""
    import random

    border = "═" * 56
    print(f"\n  ╔{border}╗")
    print(f"  ║  🔍 VisionTraceAI — Trajectory Store Validation{' ' * 5}║")
    print(f"  ╚{border}╝\n")

    store = TrajectoryStore()
    try:
        print("  [1/6] Connecting to Redis...")
        store.connect()
        print("        ✅  Connected\n")

        # Clean slate
        store.flush_all_tracks()

        print("  [2/6] Storing 100 sample trajectories...")
        cameras = ["cam_1", "cam_2", "cam_3"]
        t_start = _time.time()

        for track_id in range(1, 101):
            cam = random.choice(cameras)
            # Each track gets 5 observations
            for obs in range(5):
                ts = track_id * 1.0 + obs * 0.2
                store.save_track(
                    track_id=track_id,
                    camera_id=cam,
                    timestamp=ts,
                    bbox={
                        "x1": random.uniform(0, 500),
                        "y1": random.uniform(0, 500),
                        "x2": random.uniform(500, 1000),
                        "y2": random.uniform(500, 1000),
                    },
                    embedding_id=f"emb-{track_id}-{obs}",
                )

        elapsed = (_time.time() - t_start) * 1000
        print(f"        ✅  500 observations stored in {elapsed:.1f}ms\n")

        print("  [3/6] Verifying track count...")
        all_ids = store.get_all_track_ids()
        assert len(all_ids) == 100, f"Expected 100 tracks, got {len(all_ids)}"
        print(f"        ✅  {len(all_ids)} tracks confirmed\n")

        print("  [4/6] Retrieving and verifying trajectories...")
        errors = 0
        for tid in range(1, 101):
            meta = store.get_track(tid)
            assert meta["track_id"] == str(tid)
            assert int(meta["total_observations"]) == 5

            traj = store.get_trajectory(tid)
            assert len(traj) == 5, f"Track {tid}: expected 5 obs, got {len(traj)}"

            # Verify chronological ordering
            timestamps = [o["timestamp"] for o in traj]
            assert timestamps == sorted(timestamps), f"Track {tid} not sorted"

        print(f"        ✅  All 100 trajectories verified (5 obs each)\n")

        print("  [5/6] Stats...")
        s = store.stats()
        print(f"        Total tracks  : {s['total_tracks']}")
        print(f"        Total cameras : {s['total_cameras']}")
        print(f"        Camera IDs    : {', '.join(s['camera_ids'])}\n")

        print("  [6/6] Recent tracks query...")
        recent = store.get_recent_tracks(limit=5)
        print(f"        Top 5 by last_seen:")
        for r in recent:
            print(f"          Track {r['track_id']:>3}  cam={r['camera_id']}  "
                  f"last_seen={r['last_seen']}s  obs={r['total_observations']}")

        print(f"\n  {'═' * 52}")
        print(f"  ✅  Validation passed — 100 tracks, 500 observations")
        print(f"  {'═' * 52}\n")

        # Cleanup
        store.flush_all_tracks()

    except RedisConnectionError as exc:
        print(f"\n  ❌  Connection failed: {exc}")
        print("      Make sure Redis is running:")
        print("      docker compose -f docker/docker-compose.redis.yml up -d\n")
        raise SystemExit(1)
    finally:
        store.close()


if __name__ == "__main__":
    _run_validation()
