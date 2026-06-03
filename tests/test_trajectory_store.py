"""
VisionTraceAI — Trajectory Store Tests.

Comprehensive test suite for the temporal trajectory store, covering:
  - Track CRUD operations (save, get, update, delete)
  - Trajectory observation ordering and retrieval
  - Camera and global index management
  - Recent-tracks queries
  - Time-range filtered trajectory queries
  - Bulk operations and statistics
  - Edge cases and error handling

All tests use a real Redis instance on DB 15, flushed between tests.
"""

from __future__ import annotations

import json
import os
import time
from unittest.mock import patch

import pytest
import redis as redis_lib

from backend.storage.redis_client import RedisClient, _RedisConfig
from backend.storage.trajectory_store import (
    TrajectoryStore,
    TrackNotFoundError,
    TrajectoryStoreError,
    _track_key,
    _trajectory_key,
    _camera_key,
    _INDEX_KEY,
)

# ---------------------------------------------------------------------------
# Use DB 15 for testing to avoid colliding with development data (DB 0)
# ---------------------------------------------------------------------------
TEST_DB = 15


@pytest.fixture()
def redis_config() -> _RedisConfig:
    """Return a config pointing at the local Redis, test database."""
    with patch.dict(os.environ, {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_DB": str(TEST_DB),
        "REDIS_MAX_CONNECTIONS": "5",
        "REDIS_SOCKET_TIMEOUT": "3.0",
        "REDIS_MAX_RETRIES": "2",
        "REDIS_RETRY_DELAY": "0.1",
    }, clear=False):
        return _RedisConfig()


@pytest.fixture()
def redis_available() -> bool:
    """Return True if a local Redis instance is reachable."""
    try:
        r = redis_lib.Redis(host="localhost", port=6379, db=TEST_DB, socket_timeout=2)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


@pytest.fixture()
def redis_client(redis_config: _RedisConfig, redis_available: bool) -> RedisClient:
    """Yield a connected RedisClient on DB 15, flushed before the test."""
    if not redis_available:
        pytest.skip("Redis is not running — skipping integration test")
    c = RedisClient(config=redis_config)
    c.connect()
    c.flushdb()
    yield c  # type: ignore[misc]
    if c.is_connected:
        c.flushdb()
        c.close()


@pytest.fixture()
def store(redis_client: RedisClient) -> TrajectoryStore:
    """Yield a TrajectoryStore backed by the test Redis client."""
    s = TrajectoryStore(redis_client=redis_client)
    yield s  # type: ignore[misc]


# Helper
def _sample_bbox(offset: float = 0) -> dict[str, float]:
    return {
        "x1": 100.0 + offset,
        "y1": 200.0 + offset,
        "x2": 300.0 + offset,
        "y2": 500.0 + offset,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Key Helpers
# ═══════════════════════════════════════════════════════════════════════════


class TestKeyHelpers:
    """Tests for the Redis key formatting functions."""

    def test_track_key(self) -> None:
        assert _track_key(42) == "Track:42"

    def test_trajectory_key(self) -> None:
        assert _trajectory_key(7) == "Trajectory:7"

    def test_camera_key(self) -> None:
        assert _camera_key("cam_1") == "Camera:cam_1"

    def test_index_key(self) -> None:
        assert _INDEX_KEY == "TrackIndex"


# ═══════════════════════════════════════════════════════════════════════════
# save_track
# ═══════════════════════════════════════════════════════════════════════════


class TestSaveTrack:
    """Tests for creating new tracks."""

    def test_save_new_track(self, store: TrajectoryStore) -> None:
        result = store.save_track(
            track_id=1,
            camera_id="cam_1",
            timestamp=10.5,
            bbox=_sample_bbox(),
            embedding_id="emb-001",
        )
        assert result["track_id"] == "1"
        assert result["camera_id"] == "cam_1"
        assert result["first_seen"] == "10.5"
        assert result["last_seen"] == "10.5"
        assert result["total_observations"] == "1"
        assert result["embedding_id"] == "emb-001"
        assert result["status"] == "active"

    def test_save_without_embedding(self, store: TrajectoryStore) -> None:
        result = store.save_track(
            track_id=2,
            camera_id="cam_2",
            timestamp=5.0,
            bbox=_sample_bbox(),
        )
        assert result["embedding_id"] == ""

    def test_save_creates_trajectory(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        traj = store.get_trajectory(1)
        assert len(traj) == 1
        assert traj[0]["track_id"] == 1
        assert traj[0]["timestamp"] == 10.0

    def test_save_adds_to_camera_index(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        tracks = store.get_tracks_by_camera("cam_1")
        assert any(t["track_id"] == "1" for t in tracks)

    def test_save_adds_to_global_index(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        all_ids = store.get_all_track_ids()
        assert 1 in all_ids

    def test_save_duplicate_is_upsert(self, store: TrajectoryStore) -> None:
        """Saving the same track_id twice should add observations, not
        overwrite the track."""
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        store.save_track(1, "cam_1", 11.0, _sample_bbox(10))
        meta = store.get_track(1)
        assert meta["first_seen"] == "10.0"
        assert meta["last_seen"] == "11.0"
        assert int(meta["total_observations"]) == 2


# ═══════════════════════════════════════════════════════════════════════════
# update_track
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdateTrack:
    """Tests for appending observations to existing tracks."""

    def test_update_appends_observation(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        store.update_track(1, "cam_1", 12.0, _sample_bbox(5))
        store.update_track(1, "cam_1", 14.0, _sample_bbox(10))

        traj = store.get_trajectory(1)
        assert len(traj) == 3
        assert [o["timestamp"] for o in traj] == [10.0, 12.0, 14.0]

    def test_update_increments_observations(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        for i in range(4):
            store.update_track(1, "cam_1", 2.0 + i, _sample_bbox(i))
        meta = store.get_track(1)
        assert int(meta["total_observations"]) == 5

    def test_update_refreshes_last_seen(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.update_track(1, "cam_1", 99.0, _sample_bbox())
        meta = store.get_track(1)
        assert meta["last_seen"] == "99.0"

    def test_update_overwrites_embedding_id(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox(), embedding_id="old")
        store.update_track(1, "cam_1", 2.0, _sample_bbox(), embedding_id="new")
        meta = store.get_track(1)
        assert meta["embedding_id"] == "new"


# ═══════════════════════════════════════════════════════════════════════════
# get_track
# ═══════════════════════════════════════════════════════════════════════════


class TestGetTrack:
    """Tests for retrieving track metadata."""

    def test_get_existing_track(self, store: TrajectoryStore) -> None:
        store.save_track(42, "cam_2", 5.0, _sample_bbox(), "emb-42")
        meta = store.get_track(42)
        assert meta["track_id"] == "42"
        assert meta["camera_id"] == "cam_2"

    def test_get_nonexistent_raises(self, store: TrajectoryStore) -> None:
        with pytest.raises(TrackNotFoundError):
            store.get_track(9999)

    def test_track_exists_true(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        assert store.track_exists(1) is True

    def test_track_exists_false(self, store: TrajectoryStore) -> None:
        assert store.track_exists(9999) is False


# ═══════════════════════════════════════════════════════════════════════════
# get_trajectory
# ═══════════════════════════════════════════════════════════════════════════


class TestGetTrajectory:
    """Tests for trajectory observation retrieval."""

    def test_trajectory_order(self, store: TrajectoryStore) -> None:
        """Observations must always be returned in chronological order."""
        # Insert out of order
        store.save_track(1, "cam_1", 30.0, _sample_bbox())
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        store.save_track(1, "cam_1", 20.0, _sample_bbox())

        traj = store.get_trajectory(1)
        timestamps = [o["timestamp"] for o in traj]
        assert timestamps == [10.0, 20.0, 30.0]

    def test_trajectory_time_range(self, store: TrajectoryStore) -> None:
        for t in range(10):
            store.save_track(1, "cam_1", float(t), _sample_bbox(t))

        # Only get observations between t=3 and t=7
        traj = store.get_trajectory(1, start_time=3.0, end_time=7.0)
        timestamps = [o["timestamp"] for o in traj]
        assert timestamps == [3.0, 4.0, 5.0, 6.0, 7.0]

    def test_trajectory_start_only(self, store: TrajectoryStore) -> None:
        for t in range(5):
            store.save_track(1, "cam_1", float(t), _sample_bbox())

        traj = store.get_trajectory(1, start_time=3.0)
        assert len(traj) == 2  # t=3, t=4

    def test_trajectory_end_only(self, store: TrajectoryStore) -> None:
        for t in range(5):
            store.save_track(1, "cam_1", float(t), _sample_bbox())

        traj = store.get_trajectory(1, end_time=2.0)
        assert len(traj) == 3  # t=0, t=1, t=2

    def test_trajectory_count(self, store: TrajectoryStore) -> None:
        for t in range(7):
            store.save_track(1, "cam_1", float(t), _sample_bbox())
        assert store.get_trajectory_count(1) == 7

    def test_trajectory_nonexistent_raises(self, store: TrajectoryStore) -> None:
        with pytest.raises(TrackNotFoundError):
            store.get_trajectory(9999)

    def test_trajectory_bbox_preserved(self, store: TrajectoryStore) -> None:
        bbox = {"x1": 10.5, "y1": 20.5, "x2": 30.5, "y2": 40.5}
        store.save_track(1, "cam_1", 1.0, bbox)
        traj = store.get_trajectory(1)
        assert traj[0]["bbox"] == bbox


# ═══════════════════════════════════════════════════════════════════════════
# delete_track
# ═══════════════════════════════════════════════════════════════════════════


class TestDeleteTrack:
    """Tests for track deletion."""

    def test_delete_existing(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        assert store.delete_track(1) is True
        assert store.track_exists(1) is False

    def test_delete_removes_trajectory(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.save_track(1, "cam_1", 2.0, _sample_bbox())
        store.delete_track(1)
        assert store.get_trajectory_count(1) == 0

    def test_delete_removes_from_camera_index(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.delete_track(1)
        tracks = store.get_tracks_by_camera("cam_1")
        assert not any(t["track_id"] == "1" for t in tracks)

    def test_delete_removes_from_global_index(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.delete_track(1)
        assert 1 not in store.get_all_track_ids()

    def test_delete_nonexistent_returns_false(self, store: TrajectoryStore) -> None:
        assert store.delete_track(9999) is False


# ═══════════════════════════════════════════════════════════════════════════
# get_recent_tracks
# ═══════════════════════════════════════════════════════════════════════════


class TestGetRecentTracks:
    """Tests for the recent-tracks query."""

    def test_recent_tracks_sorted_desc(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        store.save_track(2, "cam_1", 30.0, _sample_bbox())
        store.save_track(3, "cam_1", 20.0, _sample_bbox())

        recent = store.get_recent_tracks(limit=10)
        last_seen_values = [float(t["last_seen"]) for t in recent]
        assert last_seen_values == sorted(last_seen_values, reverse=True)

    def test_recent_tracks_limit(self, store: TrajectoryStore) -> None:
        for i in range(10):
            store.save_track(i, "cam_1", float(i), _sample_bbox())
        recent = store.get_recent_tracks(limit=3)
        assert len(recent) == 3

    def test_recent_tracks_by_camera(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 10.0, _sample_bbox())
        store.save_track(2, "cam_2", 20.0, _sample_bbox())
        store.save_track(3, "cam_1", 30.0, _sample_bbox())

        recent = store.get_recent_tracks(camera_id="cam_1")
        assert len(recent) == 2
        assert all(t["camera_id"] == "cam_1" for t in recent)

    def test_recent_tracks_empty(self, store: TrajectoryStore) -> None:
        recent = store.get_recent_tracks()
        assert recent == []


# ═══════════════════════════════════════════════════════════════════════════
# Camera / Index Operations
# ═══════════════════════════════════════════════════════════════════════════


class TestCameraAndIndexOps:
    """Tests for camera and global index queries."""

    def test_get_tracks_by_camera(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.save_track(2, "cam_1", 2.0, _sample_bbox())
        store.save_track(3, "cam_2", 3.0, _sample_bbox())

        cam1 = store.get_tracks_by_camera("cam_1")
        assert len(cam1) == 2

    def test_get_tracks_by_camera_empty(self, store: TrajectoryStore) -> None:
        assert store.get_tracks_by_camera("nonexistent") == []

    def test_get_all_track_ids(self, store: TrajectoryStore) -> None:
        for i in [5, 2, 8, 1]:
            store.save_track(i, "cam_1", float(i), _sample_bbox())
        ids = store.get_all_track_ids()
        assert ids == [1, 2, 5, 8]  # sorted

    def test_get_camera_ids(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.save_track(2, "cam_3", 2.0, _sample_bbox())
        store.save_track(3, "cam_2", 3.0, _sample_bbox())

        cams = store.get_camera_ids()
        assert cams == ["cam_1", "cam_2", "cam_3"]  # sorted


# ═══════════════════════════════════════════════════════════════════════════
# Stats & Bulk
# ═══════════════════════════════════════════════════════════════════════════


class TestStatsAndBulk:
    """Tests for stats and flush_all_tracks."""

    def test_stats(self, store: TrajectoryStore) -> None:
        store.save_track(1, "cam_1", 1.0, _sample_bbox())
        store.save_track(2, "cam_2", 2.0, _sample_bbox())

        s = store.stats()
        assert s["total_tracks"] == 2
        assert s["total_cameras"] == 2

    def test_flush_all_tracks(self, store: TrajectoryStore) -> None:
        for i in range(5):
            store.save_track(i, "cam_1", float(i), _sample_bbox())

        removed = store.flush_all_tracks()
        assert removed == 5
        assert store.get_all_track_ids() == []

    def test_flush_empty_store(self, store: TrajectoryStore) -> None:
        assert store.flush_all_tracks() == 0


# ═══════════════════════════════════════════════════════════════════════════
# Bulk Ingestion (100 trajectories)
# ═══════════════════════════════════════════════════════════════════════════


class TestBulkIngestion:
    """Validates storing and retrieving 100 sample trajectories."""

    def test_100_trajectories(self, store: TrajectoryStore) -> None:
        import random
        random.seed(42)

        cameras = ["cam_1", "cam_2", "cam_3"]

        # Store 100 tracks, each with 5 observations
        for tid in range(1, 101):
            cam = cameras[tid % len(cameras)]
            for obs in range(5):
                ts = tid * 1.0 + obs * 0.2
                store.save_track(
                    track_id=tid,
                    camera_id=cam,
                    timestamp=ts,
                    bbox={
                        "x1": random.uniform(0, 500),
                        "y1": random.uniform(0, 500),
                        "x2": random.uniform(500, 1000),
                        "y2": random.uniform(500, 1000),
                    },
                    embedding_id=f"emb-{tid}-{obs}",
                )

        # Verify count
        all_ids = store.get_all_track_ids()
        assert len(all_ids) == 100

        # Verify each track
        for tid in range(1, 101):
            meta = store.get_track(tid)
            assert meta["track_id"] == str(tid)
            assert int(meta["total_observations"]) == 5

            traj = store.get_trajectory(tid)
            assert len(traj) == 5

            # Chronological order
            timestamps = [o["timestamp"] for o in traj]
            assert timestamps == sorted(timestamps)

        # Verify camera distribution
        stats = store.stats()
        assert stats["total_tracks"] == 100
        assert stats["total_cameras"] == 3

        # Recent tracks
        recent = store.get_recent_tracks(limit=5)
        assert len(recent) == 5
        last_seens = [float(t["last_seen"]) for t in recent]
        assert last_seens == sorted(last_seens, reverse=True)
