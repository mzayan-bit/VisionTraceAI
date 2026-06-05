"""
VisionTraceAI — WebSocket Streaming Endpoint.

Bridges the Kafka video-stream-topic to WebSocket clients.
Features:
- Auto reconnect handling (client-side reconnect supported by clean disconnect logic)
- Frame buffering (per-client asyncio Queue)
- Latency tracking (server ingestion timestamp vs message timestamp)
- Frame drop handling (drops oldest frames if buffer fills up)
"""

import asyncio
import json
import threading
import time
from typing import Any, Dict, List

from confluent_kafka import Consumer
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.logger import get_logger

logger = get_logger(__name__)

ws_router = APIRouter()

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "video-stream-topic"
BUFFER_SIZE = 60  # Approx 2 seconds of 30FPS frames per client before dropping


class ConnectionManager:
    """Manages WebSocket connections and frame buffering."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.queues: Dict[WebSocket, asyncio.Queue] = {}
        self.loop = asyncio.get_event_loop()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new connection and initialize its frame buffer."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.queues[websocket] = asyncio.Queue(maxsize=BUFFER_SIZE)
        logger.info("WebSocket connected", extra={"clients": len(self.active_connections)})
        
        # Start the queue consumer task for this websocket
        asyncio.create_task(self._send_loop(websocket))

    def disconnect(self, websocket: WebSocket) -> None:
        """Clean up resources on disconnect."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.queues:
            del self.queues[websocket]
        logger.info("WebSocket disconnected", extra={"clients": len(self.active_connections)})

    async def _send_loop(self, websocket: WebSocket) -> None:
        """Continuously drain the queue and send to the WebSocket."""
        queue = self.queues.get(websocket)
        if not queue:
            return
            
        try:
            while websocket in self.active_connections:
                message = await queue.get()
                await websocket.send_json(message)
                queue.task_done()
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as exc:
            logger.error("Error in websocket send loop", extra={"error": str(exc)})
            self.disconnect(websocket)

    def broadcast_sync(self, message: Dict[str, Any]) -> None:
        """Thread-safe broadcast called from the Kafka polling thread."""
        if not self.active_connections:
            return
            
        # Add latency tracking metadata
        message["ws_server_time"] = time.time()
        
        # Calculate latency from original producer
        produced_at = message.get("produced_at")
        if produced_at:
            message["latency_ms"] = round((message["ws_server_time"] - produced_at) * 1000, 2)
            
        # Push to each client's queue in a thread-safe manner
        for ws in list(self.active_connections):
            q = self.queues.get(ws)
            if q:
                # Frame drop handling: if full, remove oldest frame
                if q.full():
                    try:
                        q.get_nowait()
                        logger.debug("Buffer full, dropping old frame for client")
                    except asyncio.QueueEmpty:
                        pass
                
                try:
                    self.loop.call_soon_threadsafe(q.put_nowait, message)
                except Exception as exc:
                    logger.error("Failed to enqueue frame", extra={"error": str(exc)})


manager = ConnectionManager()
kafka_thread: threading.Thread | None = None
stop_event = threading.Event()


def kafka_bridge_worker() -> None:
    """Background thread that polls Kafka and pushes to the WebSocket manager."""
    logger.info("Starting Kafka to WebSocket bridge thread")
    
    try:
        consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": "visiontrace-ws-bridge",
            "auto.offset.reset": "latest",  # We only care about live stream
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
                # We only broadcast if there are active clients to save CPU
                if manager.active_connections:
                    manager.broadcast_sync(payload)
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from Kafka bridge")
                
    except Exception as exc:
        logger.error("Kafka bridge thread crashed", extra={"error": str(exc)})
    finally:
        try:
            consumer.close()
        except:
            pass
        logger.info("Kafka bridge thread stopped")


def start_kafka_bridge() -> None:
    """Start the background Kafka listener if not already running."""
    global kafka_thread
    if kafka_thread is None or not kafka_thread.is_alive():
        stop_event.clear()
        kafka_thread = threading.Thread(target=kafka_bridge_worker, daemon=True)
        kafka_thread.start()


@ws_router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video tracking annotations.
    Streams: frame_id, track_id, bbox, confidence, camera_id, and latency metrics.
    """
    # Ensure Kafka bridge is running
    start_kafka_bridge()
    
    await manager.connect(websocket)
    try:
        # Keep connection alive and handle client-side ping/messages if any
        while True:
            # We don't expect messages from client, but we wait to detect disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
