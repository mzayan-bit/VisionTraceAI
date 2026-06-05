"""
VisionTraceAI — Kafka Producer Smoke Test.

Sends synthetic tracking events to the ``video-stream-topic`` to validate
that the Kafka broker is running and the producer is functioning correctly.

Usage::

    # 1. Start Kafka
    docker compose -f docker/docker-compose.kafka.yml up -d

    # 2. Run this script
    uv run python scripts/test_kafka_producer.py
"""

import os
import sys
import time
import random

# Ensure the root of the project is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.streaming.kafka_producer import (
    TrackingEventProducer,
    KafkaConnectionError,
)


# ---------------------------------------------------------------------------
# Synthetic data generators
# ---------------------------------------------------------------------------
def _random_bbox() -> dict:
    """Generate a random bounding box."""
    x1 = random.randint(50, 500)
    y1 = random.randint(50, 400)
    w = random.randint(40, 150)
    h = random.randint(80, 250)
    return {"x1": x1, "y1": y1, "x2": x1 + w, "y2": y1 + h}


def _generate_dummy_events(num_frames: int = 30, tracks_per_frame: int = 3) -> list:
    """Generate a batch of synthetic tracking events."""
    cameras = ["cam_lobby", "cam_gate", "cam_parking"]
    events = []
    for frame_id in range(num_frames):
        timestamp = frame_id / 25.0  # 25 FPS
        for _ in range(tracks_per_frame):
            events.append({
                "frame_id": frame_id,
                "track_id": random.randint(1, 20),
                "bbox": _random_bbox(),
                "camera_id": random.choice(cameras),
                "timestamp": round(timestamp, 4),
                "confidence": round(random.uniform(0.6, 0.99), 3),
            })
    return events


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    num_frames = 30
    tracks_per_frame = 3
    total_events = num_frames * tracks_per_frame

    print("═" * 60)
    print("📡 VisionTraceAI — Kafka Producer Smoke Test")
    print("═" * 60)
    print(f"  Target Topic  : video-stream-topic")
    print(f"  Broker        : localhost:9092")
    print(f"  Frames        : {num_frames}")
    print(f"  Tracks/Frame  : {tracks_per_frame}")
    print(f"  Total Events  : {total_events}")
    print("─" * 60)

    # ── Connect ──────────────────────────────────────────────────────
    print("\n[1/4] Connecting to Kafka broker...")
    producer = TrackingEventProducer()
    try:
        producer.connect()
        print("      ✅ Connected successfully")
    except KafkaConnectionError as exc:
        print(f"      ❌ Connection failed: {exc}")
        print("\n  Make sure Kafka is running:")
        print("    docker compose -f docker/docker-compose.kafka.yml up -d")
        return

    # ── Generate events ──────────────────────────────────────────────
    print("\n[2/4] Generating synthetic tracking events...")
    events = _generate_dummy_events(num_frames, tracks_per_frame)
    print(f"      ✅ Generated {len(events)} events")

    # ── Publish ──────────────────────────────────────────────────────
    print("\n[3/4] Publishing events to Kafka...")
    start = time.time()
    sent = producer.publish_batch(events)
    elapsed = time.time() - start
    print(f"      ✅ Queued {sent} events in {elapsed:.3f}s")

    # ── Flush ────────────────────────────────────────────────────────
    print("\n[4/4] Flushing and verifying delivery...")
    remaining = producer.flush(timeout=10.0)
    if remaining == 0:
        print(f"      ✅ All {sent} messages delivered successfully")
    else:
        print(f"      ⚠️  {remaining} messages still pending after flush")

    # ── Summary ──────────────────────────────────────────────────────
    throughput = sent / elapsed if elapsed > 0 else 0
    print("\n" + "─" * 60)
    print("  📊 Results")
    print(f"     Messages Sent   : {producer.messages_sent}")
    print(f"     Publish Time    : {elapsed:.3f}s")
    print(f"     Throughput      : {throughput:,.0f} events/sec")
    print(f"     Pending         : {remaining}")
    print("─" * 60)

    # ── Verify topic exists by listing topics ────────────────────────
    try:
        from confluent_kafka import Consumer
        consumer = Consumer({
            "bootstrap.servers": "localhost:9092",
            "group.id": "visiontrace-test-verify",
            "auto.offset.reset": "earliest",
        })
        metadata = consumer.list_topics(timeout=5)
        topics = list(metadata.topics.keys())
        consumer.close()

        print("\n  📋 Kafka Topics:")
        for t in sorted(topics):
            marker = "  ← target" if t == "video-stream-topic" else ""
            print(f"     • {t}{marker}")
    except Exception:
        pass

    producer.close()
    print("\n✅ Kafka producer smoke test complete!")
    print("═" * 60)


if __name__ == "__main__":
    main()
