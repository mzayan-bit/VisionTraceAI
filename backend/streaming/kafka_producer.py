"""
VisionTraceAI — Kafka Producer Client.

Production-grade Kafka producer for publishing tracking events to the
``video-stream-topic``. Handles serialisation, delivery callbacks,
graceful flushing, and automatic topic creation.

Usage::

    from backend.streaming.kafka_producer import TrackingEventProducer

    producer = TrackingEventProducer()
    producer.connect()

    producer.publish_track_event(
        frame_id=42,
        track_id=7,
        bbox={"x1": 100, "y1": 200, "x2": 300, "y2": 500},
        camera_id="cam_1",
        timestamp=12.5,
    )

    producer.close()
"""

from __future__ import annotations

import base64
import json
import time as _time
from typing import Any

import cv2
import numpy as np

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_TOPIC = "video-stream-topic"
DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class KafkaProducerError(Exception):
    """Base exception for Kafka producer failures."""


class KafkaConnectionError(KafkaProducerError):
    """Raised when the Kafka broker is unreachable."""


# ---------------------------------------------------------------------------
# Delivery callback
# ---------------------------------------------------------------------------
def _delivery_callback(err: Any, msg: Any) -> None:
    """Called once per message to indicate delivery result."""
    if err is not None:
        logger.error(
            "Kafka delivery failed",
            extra={"error": str(err), "topic": msg.topic() if msg else "unknown"},
        )
    else:
        logger.debug(
            "Kafka message delivered",
            extra={
                "topic": msg.topic(),
                "partition": msg.partition(),
                "offset": msg.offset(),
            },
        )


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------
class TrackingEventProducer:
    """Publishes tracking events to a Kafka topic.

    Attributes:
        bootstrap_servers: Kafka broker address(es).
        topic: Target Kafka topic name.
        producer: Underlying ``confluent_kafka.Producer`` instance.
    """

    def __init__(
        self,
        bootstrap_servers: str = DEFAULT_BOOTSTRAP_SERVERS,
        topic: str = DEFAULT_TOPIC,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: Any = None  # confluent_kafka.Producer
        self._connected = False
        self._messages_sent = 0

        logger.info(
            "TrackingEventProducer initialised",
            extra={"bootstrap_servers": self.bootstrap_servers, "topic": self.topic},
        )

    # ── Connection ───────────────────────────────────────────────────────

    def connect(self) -> None:
        """Create the Kafka producer and verify broker connectivity.

        Raises:
            KafkaConnectionError: If the broker is unreachable.
        """
        try:
            from confluent_kafka import Producer
        except ImportError as exc:
            raise KafkaProducerError(
                "confluent-kafka is not installed. "
                "Run: uv add confluent-kafka"
            ) from exc

        logger.info("Connecting to Kafka broker", extra={"servers": self.bootstrap_servers})

        try:
            self.producer = Producer({
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": "visiontrace-tracker",
                "acks": "all",
                "retries": 3,
                "retry.backoff.ms": 200,
                "linger.ms": 5,
                "batch.num.messages": 100,
                "compression.type": "lz4",
                "message.max.bytes": 10485760,
                "queue.buffering.max.messages": 100000,
                "queue.buffering.max.kbytes": 1048576,
            })
            # Verify connectivity by requesting metadata
            metadata = self.producer.list_topics(timeout=5)
            self._connected = True
            logger.info(
                "Kafka producer connected",
                extra={
                    "broker_count": len(metadata.brokers),
                    "topic_count": len(metadata.topics),
                },
            )
        except Exception as exc:
            self.producer = None
            self._connected = False
            logger.error("Failed to connect to Kafka", extra={"error": str(exc)})
            raise KafkaConnectionError(
                f"Cannot connect to Kafka at {self.bootstrap_servers} — {exc}"
            ) from exc

    @property
    def connected(self) -> bool:
        """Return whether the producer is connected."""
        return self._connected and self.producer is not None

    def _ensure_producer(self) -> Any:
        """Return the connected producer or raise."""
        if not self.connected:
            raise KafkaConnectionError(
                "Producer not connected. Call connect() first."
            )
        return self.producer

    # ── Publishing ───────────────────────────────────────────────────────

    def publish_track_event(
        self,
        frame_id: int,
        track_id: int,
        bbox: dict[str, float],
        camera_id: str,
        timestamp: float,
        confidence: float = 0.0,
        extra_payload: dict[str, Any] | None = None,
        frame: np.ndarray | None = None,
    ) -> None:
        """Publish a single tracking event to Kafka.

        Args:
            frame_id: Frame sequence number.
            track_id: Persistent tracking ID.
            bbox: Bounding box dict with keys x1, y1, x2, y2.
            camera_id: Source camera identifier.
            timestamp: Timestamp in seconds from video start.
            confidence: Detection confidence score.
            extra_payload: Optional additional metadata.
        """
        producer = self._ensure_producer()

        event = {
            "event_type": "track_update",
            "frame_id": frame_id,
            "track_id": track_id,
            "camera_id": camera_id,
            "timestamp": timestamp,
            "confidence": confidence,
            "bbox": bbox,
            "produced_at": _time.time(),
        }

        if extra_payload:
            event["metadata"] = extra_payload

        if frame is not None:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
            success, encoded_image = cv2.imencode('.jpg', frame, encode_param)
            if success:
                event["frame"] = base64.b64encode(encoded_image).decode('utf-8')

        # Use camera_id as the partition key so all events from the same
        # camera land on the same partition (preserving ordering).
        key = camera_id.encode("utf-8")
        value = json.dumps(event).encode("utf-8")

        try:
            producer.produce(
                topic=self.topic,
                key=key,
                value=value,
                callback=_delivery_callback,
            )
            # Trigger delivery callbacks without blocking
            producer.poll(0)
            self._messages_sent += 1
        except BufferError:
            logger.warning("Kafka producer buffer full, flushing...")
            producer.flush(timeout=5)
            # Retry after flush
            producer.produce(
                topic=self.topic,
                key=key,
                value=value,
                callback=_delivery_callback,
            )
            self._messages_sent += 1
        except Exception as exc:
            logger.error(
                "Failed to publish track event",
                extra={"track_id": track_id, "frame_id": frame_id, "error": str(exc)},
            )
            raise KafkaProducerError(f"Publish failed — {exc}") from exc

    def publish_batch(
        self,
        events: list[dict[str, Any]],
    ) -> int:
        """Publish a batch of pre-formatted tracking events.

        Args:
            events: List of event dicts (each must contain frame_id,
                    track_id, bbox, camera_id, timestamp).

        Returns:
            Number of events successfully queued.
        """
        count = 0
        for event in events:
            self.publish_track_event(
                frame_id=event["frame_id"],
                track_id=event["track_id"],
                bbox=event["bbox"],
                camera_id=event["camera_id"],
                timestamp=event["timestamp"],
                confidence=event.get("confidence", 0.0),
                frame=event.get("frame"),
            )
            count += 1
        return count

    # ── Lifecycle ────────────────────────────────────────────────────────

    def flush(self, timeout: float = 10.0) -> int:
        """Flush all buffered messages and wait for delivery.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            Number of messages still in the queue (0 = all delivered).
        """
        if self.producer is None:
            return 0
        remaining = self.producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning(
                "Kafka flush incomplete",
                extra={"remaining": remaining, "timeout": timeout},
            )
        return remaining

    def close(self) -> None:
        """Flush pending messages and shut down the producer."""
        if self.producer is not None:
            logger.info(
                "Closing Kafka producer",
                extra={"messages_sent": self._messages_sent},
            )
            self.flush(timeout=10.0)
            self.producer = None
            self._connected = False
            logger.info("Kafka producer closed")

    @property
    def messages_sent(self) -> int:
        """Total number of messages published since connection."""
        return self._messages_sent

    # ── Context manager ──────────────────────────────────────────────────

    def __enter__(self) -> TrackingEventProducer:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
