"""VisionTraceAI — Streaming module for Kafka event publishing."""

from backend.streaming.kafka_producer import TrackingEventProducer

__all__ = ["TrackingEventProducer"]
