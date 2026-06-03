"""
VisionTraceAI — Redis Connection Manager.

Production-grade Redis client with connection pooling, automatic reconnect,
health checks, and environment-driven configuration.  Serves as the temporal
data backbone for trajectory storage, caching, and pub/sub messaging.

Usage::

    from backend.storage.redis_client import RedisClient

    client = RedisClient()
    client.connect()
    assert client.health_check()["status"] == "healthy"

    # Store / retrieve data
    client.set("track:42:frame:100", '{"x": 10, "y": 20}', ttl=3600)
    data = client.get("track:42:frame:100")

    client.close()

Environment variables (all optional — sensible defaults provided):

    REDIS_HOST          default: localhost
    REDIS_PORT          default: 6379
    REDIS_DB            default: 0
    REDIS_PASSWORD      default: (none)
    REDIS_URL           default: (none — overrides host/port/db if set)
    REDIS_MAX_CONNECTIONS    default: 20
    REDIS_SOCKET_TIMEOUT     default: 5.0
    REDIS_RETRY_ON_TIMEOUT   default: true
    REDIS_MAX_RETRIES        default: 3
    REDIS_RETRY_DELAY        default: 1.0
"""

from __future__ import annotations

import os
import time
from typing import Any

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import (
    ConnectionError as RedisConnError,
    TimeoutError as RedisTimeoutError,
)
from redis.retry import Retry

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class RedisConnectionError(Exception):
    """Raised when a connection to Redis cannot be established."""


class RedisHealthCheckError(Exception):
    """Raised when a Redis health check fails."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
class _RedisConfig:
    """Reads Redis configuration from environment variables.

    Supports both individual host/port/db variables and a single
    ``REDIS_URL`` connection string.  When ``REDIS_URL`` is set it
    takes precedence over the individual fields.
    """

    def __init__(self) -> None:
        # Connection parameters
        self.host: str = os.getenv("REDIS_HOST", "localhost")
        self.port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.db: int = int(os.getenv("REDIS_DB", "0"))
        self.password: str | None = os.getenv("REDIS_PASSWORD")
        self.url: str | None = os.getenv("REDIS_URL")

        # Pool & timeout
        self.max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
        self.socket_timeout: float = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0"))
        self.socket_connect_timeout: float = float(
            os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5.0")
        )
        self.retry_on_timeout: bool = os.getenv(
            "REDIS_RETRY_ON_TIMEOUT", "true"
        ).lower() in {"true", "1", "yes"}

        # Reconnect
        self.max_retries: int = int(os.getenv("REDIS_MAX_RETRIES", "3"))
        self.retry_delay: float = float(os.getenv("REDIS_RETRY_DELAY", "1.0"))

    @property
    def display_url(self) -> str:
        """Human-readable connection string (password redacted)."""
        if self.url:
            # Redact password in URL for display
            import re

            return re.sub(r"://[^:]+:([^@]+)@", r"://***:***@", self.url)
        pw = ":***" if self.password else ""
        return f"redis://{self.host}{pw}@{self.host}:{self.port}/{self.db}"

    def __repr__(self) -> str:
        return (
            f"RedisConfig(host={self.host!r}, port={self.port}, db={self.db}, "
            f"max_connections={self.max_connections}, "
            f"socket_timeout={self.socket_timeout})"
        )


# ---------------------------------------------------------------------------
# Redis Client
# ---------------------------------------------------------------------------
class RedisClient:
    """Production-grade Redis connection manager.

    Features:
        * **Connection pooling** — reuses connections via
          ``redis.ConnectionPool``.
        * **Automatic reconnect** — exponential-backoff retry on transient
          failures (configurable).
        * **Health check** — ``PING`` + ``INFO server`` for detailed status.
        * **Environment-driven** — all tunables read from env vars / ``.env``.
        * **Graceful shutdown** — ``close()`` releases pool resources.

    Attributes:
        config: Loaded ``_RedisConfig`` instance.
        client: Underlying ``redis.Redis`` instance (``None`` until connected).
        pool: ``redis.ConnectionPool`` backing the client.
    """

    def __init__(self, config: _RedisConfig | None = None) -> None:
        self.config = config or _RedisConfig()
        self.client: redis.Redis | None = None  # type: ignore[type-arg]
        self.pool: redis.ConnectionPool | None = None
        self._connected: bool = False

        logger.info(
            "RedisClient initialised",
            extra={
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.db,
                "max_connections": self.config.max_connections,
            },
        )

    # ── Connection ───────────────────────────────────────────────────────

    def connect(self) -> None:
        """Establish a pooled connection to Redis.

        Creates a ``ConnectionPool`` and issues a ``PING`` to verify the
        server is reachable.  On failure, retries up to
        ``config.max_retries`` times with exponential back-off.

        Raises:
            RedisConnectionError: If all retry attempts are exhausted.
        """
        cfg = self.config

        logger.info(
            "Connecting to Redis",
            extra={"url": cfg.display_url, "max_retries": cfg.max_retries},
        )

        retry = Retry(ExponentialBackoff(), retries=cfg.max_retries)

        last_exc: Exception | None = None
        for attempt in range(1, cfg.max_retries + 1):
            try:
                if cfg.url:
                    self.pool = redis.ConnectionPool.from_url(
                        cfg.url,
                        max_connections=cfg.max_connections,
                        socket_timeout=cfg.socket_timeout,
                        socket_connect_timeout=cfg.socket_connect_timeout,
                        retry_on_timeout=cfg.retry_on_timeout,
                        retry=retry,
                        health_check_interval=30,
                    )
                else:
                    self.pool = redis.ConnectionPool(
                        host=cfg.host,
                        port=cfg.port,
                        db=cfg.db,
                        password=cfg.password,
                        max_connections=cfg.max_connections,
                        socket_timeout=cfg.socket_timeout,
                        socket_connect_timeout=cfg.socket_connect_timeout,
                        retry_on_timeout=cfg.retry_on_timeout,
                        retry=retry,
                        health_check_interval=30,
                        decode_responses=True,
                    )

                self.client = redis.Redis(connection_pool=self.pool)
                self.client.ping()
                self._connected = True

                logger.info(
                    "Redis connection established",
                    extra={"attempt": attempt, "url": cfg.display_url},
                )
                return

            except (RedisConnError, RedisTimeoutError, OSError) as exc:
                last_exc = exc
                wait = cfg.retry_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Redis connection attempt failed, retrying",
                    extra={
                        "attempt": attempt,
                        "max_retries": cfg.max_retries,
                        "wait_seconds": wait,
                        "error": str(exc),
                    },
                )
                if attempt < cfg.max_retries:
                    time.sleep(wait)

        # All retries exhausted
        self.client = None
        self.pool = None
        self._connected = False
        msg = f"Cannot connect to Redis at {cfg.display_url} after {cfg.max_retries} attempts"
        logger.error(msg, extra={"error": str(last_exc)})
        raise RedisConnectionError(f"{msg} — {last_exc}")

    def reconnect(self) -> None:
        """Close the current connection (if any) and reconnect.

        Safe to call even if not currently connected.
        """
        logger.info("Reconnecting to Redis")
        self.close()
        self.connect()

    # ── Health Check ─────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Run a health check against the Redis server.

        Performs ``PING`` and fetches ``INFO server`` for version and
        uptime data.

        Returns:
            Dictionary with ``status``, ``ping``, ``redis_version``,
            ``uptime_seconds``, ``connected_clients``, ``used_memory_human``.

        Raises:
            RedisHealthCheckError: If the health check fails.
        """
        client = self._ensure_client()
        try:
            ping_ok = client.ping()
            info = client.info(section="server")
            memory_info = client.info(section="memory")
            clients_info = client.info(section="clients")

            result: dict[str, Any] = {
                "status": "healthy" if ping_ok else "unhealthy",
                "ping": ping_ok,
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", -1),
                "connected_clients": clients_info.get("connected_clients", -1),
                "used_memory_human": memory_info.get("used_memory_human", "unknown"),
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.db,
            }

            logger.info("Redis health check passed", extra=result)
            return result

        except Exception as exc:
            logger.error("Redis health check failed", extra={"error": str(exc)})
            raise RedisHealthCheckError(f"Health check failed — {exc}") from exc

    # ── Data Operations ──────────────────────────────────────────────────

    def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        """Set a key-value pair, optionally with a TTL in seconds."""
        client = self._ensure_client()
        try:
            result = client.set(key, value, ex=ttl)
            return bool(result)
        except Exception as exc:
            logger.error("Redis SET failed", extra={"key": key, "error": str(exc)})
            raise

    def get(self, key: str) -> str | None:
        """Get a value by key.  Returns ``None`` if the key does not exist."""
        client = self._ensure_client()
        try:
            return client.get(key)  # type: ignore[return-value]
        except Exception as exc:
            logger.error("Redis GET failed", extra={"key": key, "error": str(exc)})
            raise

    def delete(self, *keys: str) -> int:
        """Delete one or more keys.  Returns the number of keys removed."""
        client = self._ensure_client()
        try:
            return client.delete(*keys)  # type: ignore[return-value]
        except Exception as exc:
            logger.error("Redis DELETE failed", extra={"keys": keys, "error": str(exc)})
            raise

    def exists(self, key: str) -> bool:
        """Check whether a key exists."""
        client = self._ensure_client()
        return bool(client.exists(key))

    def keys(self, pattern: str = "*") -> list[str]:
        """Return all keys matching *pattern* (use with care in production)."""
        client = self._ensure_client()
        return client.keys(pattern)  # type: ignore[return-value]

    def flushdb(self) -> None:
        """Flush the current database.  **Destructive** — use only in tests."""
        client = self._ensure_client()
        client.flushdb()
        logger.warning("Redis database flushed", extra={"db": self.config.db})

    def dbsize(self) -> int:
        """Return the number of keys in the current database."""
        client = self._ensure_client()
        return client.dbsize()  # type: ignore[return-value]

    # ── Connection Info ──────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the client is connected and responsive."""
        if not self._connected or self.client is None:
            return False
        try:
            return bool(self.client.ping())
        except Exception:
            self._connected = False
            return False

    def pool_info(self) -> dict[str, Any]:
        """Return connection pool statistics."""
        if self.pool is None:
            return {"status": "no_pool"}

        return {
            "max_connections": self.pool.max_connections,
            "current_connections": len(self.pool._in_use_connections),
            "available_connections": len(self.pool._available_connections),
        }

    # ── Lifecycle ────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the Redis connection and release pool resources."""
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

        if self.pool is not None:
            try:
                self.pool.disconnect()
            except Exception:
                pass
            self.pool = None

        self._connected = False
        logger.info("Redis connection closed")

    # ── Internals ────────────────────────────────────────────────────────

    def _ensure_client(self) -> redis.Redis:  # type: ignore[type-arg]
        """Return the connected client or raise."""
        if self.client is None or not self._connected:
            raise RedisConnectionError(
                "Not connected to Redis. Call connect() first."
            )
        return self.client

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"RedisClient({self.config.display_url}, {status})"

    def __enter__(self) -> RedisClient:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Standalone smoke test
# ---------------------------------------------------------------------------
def _run_smoke_test() -> None:
    """Quick smoke test when run directly: ``python backend/storage/redis_client.py``."""
    border = "═" * 56
    print(f"\n  ╔{border}╗")
    print(f"  ║  🔍 VisionTraceAI — Redis Connection Test{' ' * 12}║")
    print(f"  ╚{border}╝\n")

    client = RedisClient()
    try:
        print("  [1/5] Connecting to Redis...")
        client.connect()
        print("        ✅  Connected successfully\n")

        print("  [2/5] Running health check...")
        health = client.health_check()
        print(f"        Status         : {health['status']}")
        print(f"        Redis Version  : {health['redis_version']}")
        print(f"        Uptime         : {health['uptime_seconds']}s")
        print(f"        Clients        : {health['connected_clients']}")
        print(f"        Memory         : {health['used_memory_human']}\n")

        print("  [3/5] Testing SET/GET...")
        client.set("visiontrace:test:ping", "pong", ttl=60)
        val = client.get("visiontrace:test:ping")
        assert val == "pong", f"Expected 'pong', got {val!r}"
        print(f"        ✅  SET/GET verified (value={val!r})\n")

        print("  [4/5] Connection pool stats...")
        pool = client.pool_info()
        print(f"        Max connections : {pool['max_connections']}")
        print(f"        In use          : {pool['current_connections']}")
        print(f"        Available       : {pool['available_connections']}\n")

        print("  [5/5] Cleanup...")
        client.delete("visiontrace:test:ping")
        print("        ✅  Test key removed\n")

        print("  ════════════════════════════════════════════")
        print("  ✅  All checks passed — Redis is operational")
        print("  ════════════════════════════════════════════\n")

    except RedisConnectionError as exc:
        print(f"\n  ❌  Connection failed: {exc}")
        print("      Make sure Redis is running:")
        print("      docker compose -f docker/docker-compose.redis.yml up -d\n")
        raise SystemExit(1)
    finally:
        client.close()


if __name__ == "__main__":
    _run_smoke_test()
