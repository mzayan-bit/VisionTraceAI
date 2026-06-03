"""
VisionTraceAI — Redis Connection Tests.

Comprehensive test suite for the Redis connection manager, covering:
  - Connection lifecycle (connect / close / reconnect)
  - Health checks
  - Data operations (SET / GET / DELETE / EXISTS)
  - Connection pool management
  - Error handling and edge cases
  - Context manager protocol

All tests use a real Redis instance via Docker.  The test database (DB 15)
is flushed before each test to guarantee isolation.
"""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest
import redis as redis_lib

from backend.storage.redis_client import (
    RedisClient,
    RedisConnectionError,
    RedisHealthCheckError,
    _RedisConfig,
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
def client(redis_config: _RedisConfig, redis_available: bool) -> RedisClient:
    """Yield a connected RedisClient on DB 15, flushed before the test."""
    if not redis_available:
        pytest.skip("Redis is not running — skipping integration test")
    c = RedisClient(config=redis_config)
    c.connect()
    c.flushdb()  # start each test with clean state
    yield c  # type: ignore[misc]
    if c.is_connected:
        c.flushdb()
        c.close()


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════


class TestConfig:
    """Tests for ``_RedisConfig`` environment-variable loading."""

    def test_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = _RedisConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 6379
        assert cfg.db == 0
        assert cfg.password is None
        assert cfg.url is None
        assert cfg.max_connections == 20
        assert cfg.socket_timeout == 5.0

    def test_override_host_port(self) -> None:
        with patch.dict(os.environ, {
            "REDIS_HOST": "redis.internal",
            "REDIS_PORT": "6380",
            "REDIS_DB": "3",
        }, clear=True):
            cfg = _RedisConfig()
        assert cfg.host == "redis.internal"
        assert cfg.port == 6380
        assert cfg.db == 3

    def test_url_takes_precedence(self) -> None:
        with patch.dict(os.environ, {
            "REDIS_URL": "redis://secret:pass@myhost:6399/2",
        }, clear=True):
            cfg = _RedisConfig()
        assert cfg.url == "redis://secret:pass@myhost:6399/2"

    def test_display_url_redacts_password(self) -> None:
        with patch.dict(os.environ, {
            "REDIS_URL": "redis://user:supersecret@host:6379/0",
        }, clear=True):
            cfg = _RedisConfig()
        assert "supersecret" not in cfg.display_url
        assert "***" in cfg.display_url

    def test_retry_on_timeout_parsing(self) -> None:
        for val in ("true", "1", "yes", "True", "YES"):
            with patch.dict(os.environ, {"REDIS_RETRY_ON_TIMEOUT": val}, clear=True):
                assert _RedisConfig().retry_on_timeout is True

        for val in ("false", "0", "no"):
            with patch.dict(os.environ, {"REDIS_RETRY_ON_TIMEOUT": val}, clear=True):
                assert _RedisConfig().retry_on_timeout is False

    def test_repr(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cfg = _RedisConfig()
        r = repr(cfg)
        assert "localhost" in r
        assert "6379" in r


# ═══════════════════════════════════════════════════════════════════════════
# Connection Lifecycle
# ═══════════════════════════════════════════════════════════════════════════


class TestConnection:
    """Tests for connect / close / reconnect."""

    def test_connect_success(self, client: RedisClient) -> None:
        assert client.is_connected is True
        assert client.client is not None

    def test_close(self, client: RedisClient) -> None:
        client.close()
        assert client.is_connected is False
        assert client.client is None
        assert client.pool is None

    def test_double_close_is_safe(self, client: RedisClient) -> None:
        client.close()
        client.close()  # should not raise
        assert client.is_connected is False

    def test_reconnect(self, client: RedisClient) -> None:
        # set a key, reconnect, verify key is still there
        client.set("persist_key", "persist_val")
        client.reconnect()
        assert client.is_connected is True
        assert client.get("persist_key") == "persist_val"

    def test_connect_bad_host(self) -> None:
        with patch.dict(os.environ, {
            "REDIS_HOST": "nonexistent.invalid",
            "REDIS_PORT": "6379",
            "REDIS_MAX_RETRIES": "1",
            "REDIS_RETRY_DELAY": "0.01",
            "REDIS_SOCKET_TIMEOUT": "0.5",
            "REDIS_SOCKET_CONNECT_TIMEOUT": "0.5",
        }, clear=True):
            bad = RedisClient()
            with pytest.raises(RedisConnectionError):
                bad.connect()

    def test_ensure_client_when_disconnected(self) -> None:
        c = RedisClient()
        with pytest.raises(RedisConnectionError, match="Not connected"):
            c._ensure_client()

    def test_context_manager(
        self, redis_config: _RedisConfig, redis_available: bool,
    ) -> None:
        if not redis_available:
            pytest.skip("Redis not running")
        with RedisClient(config=redis_config) as c:
            assert c.is_connected is True
            c.set("ctx_key", "ctx_val")
            assert c.get("ctx_key") == "ctx_val"
        assert c.is_connected is False


# ═══════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════


class TestHealthCheck:
    """Tests for the health_check method."""

    def test_health_check_passes(self, client: RedisClient) -> None:
        result = client.health_check()
        assert result["status"] == "healthy"
        assert result["ping"] is True
        assert "redis_version" in result
        assert result["uptime_seconds"] >= 0
        assert result["connected_clients"] >= 1
        assert "used_memory_human" in result

    def test_health_check_keys(self, client: RedisClient) -> None:
        result = client.health_check()
        expected = {
            "status", "ping", "redis_version", "uptime_seconds",
            "connected_clients", "used_memory_human", "host", "port", "db",
        }
        assert expected.issubset(result.keys())

    def test_health_check_fails_when_disconnected(self) -> None:
        c = RedisClient()
        with pytest.raises(RedisConnectionError):
            c.health_check()


# ═══════════════════════════════════════════════════════════════════════════
# Data Operations
# ═══════════════════════════════════════════════════════════════════════════


class TestDataOperations:
    """Tests for SET / GET / DELETE / EXISTS / keys."""

    def test_set_and_get(self, client: RedisClient) -> None:
        assert client.set("key1", "value1") is True
        assert client.get("key1") == "value1"

    def test_get_nonexistent_returns_none(self, client: RedisClient) -> None:
        assert client.get("does_not_exist") is None

    def test_set_with_ttl(self, client: RedisClient) -> None:
        client.set("ttl_key", "ttl_val", ttl=1)
        assert client.get("ttl_key") == "ttl_val"
        time.sleep(1.5)
        assert client.get("ttl_key") is None

    def test_delete_single(self, client: RedisClient) -> None:
        client.set("del_key", "del_val")
        removed = client.delete("del_key")
        assert removed == 1
        assert client.get("del_key") is None

    def test_delete_multiple(self, client: RedisClient) -> None:
        client.set("a", "1")
        client.set("b", "2")
        client.set("c", "3")
        removed = client.delete("a", "b", "c")
        assert removed == 3

    def test_delete_nonexistent(self, client: RedisClient) -> None:
        assert client.delete("ghost") == 0

    def test_exists(self, client: RedisClient) -> None:
        client.set("ex", "val")
        assert client.exists("ex") is True
        assert client.exists("nope") is False

    def test_keys_pattern(self, client: RedisClient) -> None:
        client.set("track:1:frame:0", "a")
        client.set("track:1:frame:1", "b")
        client.set("track:2:frame:0", "c")
        matched = client.keys("track:1:*")
        assert len(matched) == 2

    def test_flushdb_and_dbsize(self, client: RedisClient) -> None:
        client.set("k1", "v1")
        client.set("k2", "v2")
        assert client.dbsize() >= 2
        client.flushdb()
        assert client.dbsize() == 0

    def test_overwrite_key(self, client: RedisClient) -> None:
        client.set("ow", "first")
        client.set("ow", "second")
        assert client.get("ow") == "second"


# ═══════════════════════════════════════════════════════════════════════════
# Connection Pool
# ═══════════════════════════════════════════════════════════════════════════


class TestConnectionPool:
    """Tests for pool_info and pooling behaviour."""

    def test_pool_info_connected(self, client: RedisClient) -> None:
        info = client.pool_info()
        assert "max_connections" in info
        assert info["max_connections"] == 5  # from fixture config

    def test_pool_info_disconnected(self) -> None:
        c = RedisClient()
        info = c.pool_info()
        assert info == {"status": "no_pool"}

    def test_repr_connected(self, client: RedisClient) -> None:
        r = repr(client)
        assert "connected" in r

    def test_repr_disconnected(self) -> None:
        c = RedisClient()
        r = repr(c)
        assert "disconnected" in r
