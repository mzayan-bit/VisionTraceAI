"""
VisionTraceAI — Ultra-Low Latency WebSocket Streaming API.

Pipeline: Kafka -> FastAPI Consumer -> Frame Annotator -> WebSocket -> React
"""

import asyncio
import json
import threading
import time
from typing import Any

from confluent_kafka import Consumer
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.logger import get_logger
from backend.streaming.color_engine import ColorEngine
from backend.storage.redis_client import RedisClient

logger = get_logger(__name__)

color_engine = ColorEngine()
redis_client = RedisClient()
try:
    redis_client.connect()
except Exception:
    pass

ws_router = APIRouter()

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "video-stream-topic"
BUFFER_SIZE = 3  # Max frames in queue
TARGET_FPS = 30
FRAME_INTERVAL = 1.0 / TARGET_FPS


class ConnectionManager:
    """Manages WebSocket connections and frame buffering."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.queues: dict[WebSocket, asyncio.Queue] = {}
        self.loop = asyncio.get_event_loop()
        self.frame_count = 0
        self.last_fps_time = time.time()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new connection and initialize its frame buffer."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.queues[websocket] = asyncio.Queue(maxsize=BUFFER_SIZE)
        logger.info("WebSocket connected", extra={"clients": len(self.active_connections)})

        asyncio.create_task(self._send_loop(websocket))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.queues:
            del self.queues[websocket]
        logger.info("WebSocket disconnected", extra={"clients": len(self.active_connections)})

    async def _send_loop(self, websocket: WebSocket) -> None:
        """Continuously drain the queue and send to the WebSocket with FPS control."""
        queue = self.queues.get(websocket)
        if not queue:
            return

        try:
            while websocket in self.active_connections:
                start_time = time.time()

                message = await queue.get()

                # Check latency for drop-frame logic (>200ms)
                latency_ms = message.get("latency_ms", 0)
                if latency_ms > 200:
                    logger.debug("Dropping frame due to high latency", extra={"latency_ms": latency_ms})
                    queue.task_done()
                    continue

                await websocket.send_json(message)
                queue.task_done()

                # FPS control
                elapsed = time.time() - start_time
                sleep_time = FRAME_INTERVAL - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as exc:
            logger.error("Error in websocket send loop", extra={"error": str(exc)})
            self.disconnect(websocket)

    def broadcast_sync(self, message: dict[str, Any]) -> None:
        if not self.active_connections:
            return

        message["ws_server_time"] = time.time()
        produced_at = message.get("produced_at")
        
        # Calculate latency
        latency_ms = 0
        if produced_at:
            latency_ms = round((message["ws_server_time"] - produced_at) * 1000, 2)
            message["latency_ms"] = latency_ms

        # Calculate FPS
        self.frame_count += 1
        now = time.time()
        if now - self.last_fps_time >= 1.0:
            current_fps = self.frame_count / (now - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = now
            
            # Push metrics to Redis
            if redis_client.is_connected:
                try:
                    redis_client.set("metrics:system_fps", str(round(current_fps, 1)), ttl=60)
                    redis_client.set("metrics:pipeline_latency", str(latency_ms), ttl=60)
                except Exception:
                    pass

        # Optional: Frame Annotator logic if needed (e.g., drawing on the frame)
        # Assuming the frame is already base64 encoded by the producer.
        # Format payload: { frame: base64, detections: [], track_ids: [], latency_ms: X, fps: 30 }

        track_id = message.get("track_id")
        color = None
        if track_id is not None:
            color = color_engine.get_track_color(track_id)

        payload = {
            "frame": message.get("frame", ""),
            "detections": [message.get("bbox")] if message.get("bbox") else [],
            "track_ids": [track_id] if track_id is not None else [],
            "colors": [color] if color is not None else [],
            "latency_ms": message["latency_ms"],
            "fps": TARGET_FPS,
            # include other metadata for React App
            "track_id": track_id,
            "bbox": message.get("bbox"),
            "camera_id": message.get("camera_id"),
            "color": color,
        }

        for ws in list(self.active_connections):
            q = self.queues.get(ws)
            if q:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                try:
                    self.loop.call_soon_threadsafe(q.put_nowait, payload)
                except Exception as exc:
                    logger.error("Failed to enqueue frame", extra={"error": str(exc)})

    def broadcast_agent_event(self, track_id: int | None, action: str, raw_results: list | None = None) -> None:
        """Push an out-of-band agent intelligence event to the frontend."""
        if not self.active_connections:
            return

        payload = {
            "event_type": "agent_response",
            "track_id": track_id,
            "action": action,
            "timestamp": time.time(),
            "raw_results": raw_results or []
        }

        for ws in list(self.active_connections):
            q = self.queues.get(ws)
            if q:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                try:
                    self.loop.call_soon_threadsafe(q.put_nowait, payload)
                except Exception as exc:
                    logger.error("Failed to enqueue agent event", extra={"error": str(exc)})


manager = ConnectionManager()
kafka_thread: threading.Thread | None = None
stop_event = threading.Event()


def kafka_bridge_worker() -> None:
    logger.info("Starting Kafka to WebSocket bridge thread")

    try:
        consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": "visiontrace-ws-bridge-v2",
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        })
        consumer.subscribe([KAFKA_TOPIC])

        while not stop_event.is_set():
            msg = consumer.poll(timeout=0.1)

            if msg is None:
                continue
            if msg.error():
                logger.error("Kafka bridge poll error", extra={"error": msg.error().str()})
                continue

            try:
                payload = json.loads(msg.value().decode('utf-8'))
                if manager.active_connections:
                    manager.broadcast_sync(payload)
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from Kafka bridge")

    except Exception as exc:
        logger.error("Kafka bridge thread crashed", extra={"error": str(exc)})
    finally:
        try:
            consumer.close()
        except Exception:
            pass
        logger.info("Kafka bridge thread stopped")


def start_kafka_bridge() -> None:
    global kafka_thread
    if kafka_thread is None or not kafka_thread.is_alive():
        stop_event.clear()
        kafka_thread = threading.Thread(target=kafka_bridge_worker, daemon=True)
        kafka_thread.start()


@ws_router.websocket("/video")
async def websocket_endpoint(websocket: WebSocket):
    """
    Ultra-low latency WebSocket streaming API for annotated CV video.
    """
    start_kafka_bridge()
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
