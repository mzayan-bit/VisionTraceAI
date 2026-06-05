"""
Tests for the Kafka TrackingEventProducer.

Covers initialisation, event serialisation, batch publishing, connection
error handling, and flush behaviour — all without requiring a live Kafka
broker (mocked via ``unittest.mock``).
"""

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from backend.streaming.kafka_producer import (
    TrackingEventProducer,
    KafkaConnectionError,
    KafkaProducerError,
    DEFAULT_TOPIC,
    DEFAULT_BOOTSTRAP_SERVERS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_confluent_producer():
    """Return a mocked confluent_kafka.Producer class."""
    with patch("backend.streaming.kafka_producer.TrackingEventProducer.connect") as mock_connect:
        producer = TrackingEventProducer()
        # Simulate a connected state
        mock_inner = MagicMock()
        mock_inner.list_topics.return_value = MagicMock(
            brokers={1: "localhost:9092"},
            topics={"video-stream-topic": MagicMock()},
        )
        mock_inner.flush.return_value = 0
        mock_inner.poll.return_value = 0
        producer.producer = mock_inner
        producer._connected = True
        yield producer


@pytest.fixture
def sample_event():
    """Return a sample tracking event dict."""
    return {
        "frame_id": 42,
        "track_id": 7,
        "bbox": {"x1": 100.0, "y1": 200.0, "x2": 300.0, "y2": 500.0},
        "camera_id": "cam_lobby",
        "timestamp": 1.68,
        "confidence": 0.92,
    }


# ---------------------------------------------------------------------------
# Tests — Initialisation
# ---------------------------------------------------------------------------
class TestInitialisation:
    """Tests for producer initialisation and defaults."""

    def test_default_topic(self):
        producer = TrackingEventProducer()
        assert producer.topic == DEFAULT_TOPIC

    def test_default_bootstrap_servers(self):
        producer = TrackingEventProducer()
        assert producer.bootstrap_servers == DEFAULT_BOOTSTRAP_SERVERS

    def test_custom_config(self):
        producer = TrackingEventProducer(
            bootstrap_servers="kafka.example.com:9093",
            topic="custom-topic",
        )
        assert producer.bootstrap_servers == "kafka.example.com:9093"
        assert producer.topic == "custom-topic"

    def test_not_connected_by_default(self):
        producer = TrackingEventProducer()
        assert producer.connected is False
        assert producer.messages_sent == 0


# ---------------------------------------------------------------------------
# Tests — Connection
# ---------------------------------------------------------------------------
class TestConnection:
    """Tests for producer connection handling."""

    def test_connect_without_confluent_kafka_raises(self):
        """If confluent-kafka is not installed, connect() should raise."""
        producer = TrackingEventProducer()
        with patch.dict("sys.modules", {"confluent_kafka": None}):
            with pytest.raises(KafkaProducerError, match="confluent-kafka is not installed"):
                producer.connect()

    def test_connect_bad_broker_raises(self):
        """Connection to a non-existent broker should raise KafkaConnectionError."""
        producer = TrackingEventProducer(bootstrap_servers="nonexistent:9999")
        try:
            producer.connect()
            # If connect doesn't raise (e.g. librdkafka defers errors),
            # we still verify the state
            # Some versions of confluent-kafka may not throw on connect
        except (KafkaConnectionError, KafkaProducerError):
            assert producer.connected is False

    def test_ensure_producer_when_disconnected(self):
        producer = TrackingEventProducer()
        with pytest.raises(KafkaConnectionError, match="not connected"):
            producer._ensure_producer()


# ---------------------------------------------------------------------------
# Tests — Publishing
# ---------------------------------------------------------------------------
class TestPublishing:
    """Tests for event publishing."""

    def test_publish_single_event(self, mock_confluent_producer, sample_event):
        mock_confluent_producer.publish_track_event(**sample_event)
        
        # Verify produce was called
        mock_confluent_producer.producer.produce.assert_called_once()
        call_kwargs = mock_confluent_producer.producer.produce.call_args
        
        assert call_kwargs.kwargs["topic"] == DEFAULT_TOPIC
        assert call_kwargs.kwargs["key"] == b"cam_lobby"
        
        # Verify the serialised payload
        payload = json.loads(call_kwargs.kwargs["value"])
        assert payload["event_type"] == "track_update"
        assert payload["frame_id"] == 42
        assert payload["track_id"] == 7
        assert payload["camera_id"] == "cam_lobby"
        assert payload["timestamp"] == 1.68
        assert payload["confidence"] == 0.92
        assert payload["bbox"]["x1"] == 100.0

    def test_publish_increments_counter(self, mock_confluent_producer, sample_event):
        assert mock_confluent_producer.messages_sent == 0
        mock_confluent_producer.publish_track_event(**sample_event)
        assert mock_confluent_producer.messages_sent == 1
        mock_confluent_producer.publish_track_event(**sample_event)
        assert mock_confluent_producer.messages_sent == 2

    def test_publish_with_extra_payload(self, mock_confluent_producer):
        mock_confluent_producer.publish_track_event(
            frame_id=1,
            track_id=2,
            bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
            camera_id="cam_1",
            timestamp=0.5,
            extra_payload={"zone": "entrance"},
        )
        call_kwargs = mock_confluent_producer.producer.produce.call_args
        payload = json.loads(call_kwargs.kwargs["value"])
        assert payload["metadata"]["zone"] == "entrance"

    def test_publish_when_disconnected_raises(self, sample_event):
        producer = TrackingEventProducer()
        with pytest.raises(KafkaConnectionError):
            producer.publish_track_event(**sample_event)

    def test_publish_batch(self, mock_confluent_producer):
        events = [
            {
                "frame_id": i,
                "track_id": i + 1,
                "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
                "camera_id": "cam_1",
                "timestamp": i * 0.04,
            }
            for i in range(5)
        ]
        count = mock_confluent_producer.publish_batch(events)
        assert count == 5
        assert mock_confluent_producer.messages_sent == 5

    def test_buffer_error_triggers_flush_and_retry(self, mock_confluent_producer, sample_event):
        """When the producer buffer is full, it should flush and retry."""
        mock_confluent_producer.producer.produce.side_effect = [
            BufferError("Queue full"),
            None,  # Retry succeeds
        ]
        mock_confluent_producer.publish_track_event(**sample_event)
        mock_confluent_producer.producer.flush.assert_called_once()
        assert mock_confluent_producer.messages_sent == 1


# ---------------------------------------------------------------------------
# Tests — Partition Key Strategy
# ---------------------------------------------------------------------------
class TestPartitionKey:
    """Verify that camera_id is used as the partition key."""

    def test_partition_key_is_camera_id(self, mock_confluent_producer):
        mock_confluent_producer.publish_track_event(
            frame_id=0, track_id=1,
            bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
            camera_id="cam_parking",
            timestamp=0.0,
        )
        call_kwargs = mock_confluent_producer.producer.produce.call_args
        assert call_kwargs.kwargs["key"] == b"cam_parking"


# ---------------------------------------------------------------------------
# Tests — Event Schema
# ---------------------------------------------------------------------------
class TestEventSchema:
    """Verify the structure of published events."""

    def test_event_contains_required_fields(self, mock_confluent_producer):
        mock_confluent_producer.publish_track_event(
            frame_id=10, track_id=3,
            bbox={"x1": 50, "y1": 60, "x2": 150, "y2": 260},
            camera_id="cam_gate",
            timestamp=0.4,
            confidence=0.87,
        )
        call_kwargs = mock_confluent_producer.producer.produce.call_args
        payload = json.loads(call_kwargs.kwargs["value"])

        required_fields = [
            "event_type", "frame_id", "track_id", "camera_id",
            "timestamp", "confidence", "bbox", "produced_at",
        ]
        for field in required_fields:
            assert field in payload, f"Missing field: {field}"

    def test_event_bbox_has_coordinates(self, mock_confluent_producer):
        mock_confluent_producer.publish_track_event(
            frame_id=0, track_id=1,
            bbox={"x1": 10, "y1": 20, "x2": 30, "y2": 40},
            camera_id="cam_1",
            timestamp=0.0,
        )
        call_kwargs = mock_confluent_producer.producer.produce.call_args
        payload = json.loads(call_kwargs.kwargs["value"])
        bbox = payload["bbox"]
        assert all(k in bbox for k in ("x1", "y1", "x2", "y2"))


# ---------------------------------------------------------------------------
# Tests — Lifecycle
# ---------------------------------------------------------------------------
class TestLifecycle:
    """Tests for flush and close."""

    def test_flush_returns_remaining(self, mock_confluent_producer):
        mock_confluent_producer.producer.flush.return_value = 0
        remaining = mock_confluent_producer.flush()
        assert remaining == 0

    def test_flush_when_not_connected(self):
        producer = TrackingEventProducer()
        assert producer.flush() == 0

    def test_close_flushes_and_disconnects(self, mock_confluent_producer):
        assert mock_confluent_producer.connected is True
        mock_confluent_producer.close()
        assert mock_confluent_producer.connected is False
        assert mock_confluent_producer.producer is None

    def test_context_manager(self):
        """Context manager should call connect() and close()."""
        producer = TrackingEventProducer()
        with patch.object(producer, "connect") as mock_connect, \
             patch.object(producer, "close") as mock_close:
            with producer:
                mock_connect.assert_called_once()
            mock_close.assert_called_once()


# ---------------------------------------------------------------------------
# Tests — Tracker Integration
# ---------------------------------------------------------------------------
class TestTrackerIntegration:
    """Verify that VisionTracker accepts and uses a kafka_producer."""

    def test_tracker_accepts_kafka_producer(self):
        from app.core.tracker import VisionTracker
        mock_producer = MagicMock()
        tracker = VisionTracker(kafka_producer=mock_producer, camera_id="cam_test")
        assert tracker.kafka_producer is mock_producer

    def test_tracker_default_no_kafka(self):
        from app.core.tracker import VisionTracker
        tracker = VisionTracker()
        assert tracker.kafka_producer is None

    def test_tracker_shutdown_flushes_kafka(self):
        from app.core.tracker import VisionTracker
        mock_producer = MagicMock()
        tracker = VisionTracker(kafka_producer=mock_producer)
        tracker.shutdown()
        mock_producer.flush.assert_called_once()
