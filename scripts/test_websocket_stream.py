"""
VisionTraceAI — WebSocket Stream Test Script.

Validates the real-time WebSocket connection to the FastAPI server.
Automatically connects to ws://localhost:8000/ws/stream and tracks metrics:
- Connection stability
- Message throughput
- Frame latency
"""

import asyncio
import json
import statistics
import sys
import time

import websockets


async def test_stream(duration_sec: int = 15):
    """Connect to the WebSocket endpoint and gather statistics for `duration_sec` seconds."""
    uri = "ws://localhost:8000/ws/stream"
    print("═" * 60)
    print(f"📡 Connecting to WebSocket Stream: {uri}")
    print("═" * 60)
    
    latencies = []
    messages_received = 0
    start_time = time.time()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully! Listening for frames...\n")
            
            while True:
                # Calculate elapsed time
                elapsed = time.time() - start_time
                if elapsed > duration_sec:
                    break
                    
                # Await message with a short timeout to handle idle streams
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    messages_received += 1
                    
                    # Extract latency
                    latency = data.get("latency_ms")
                    if latency is not None:
                        latencies.append(latency)
                        
                    # Print snapshot every 50 messages
                    if messages_received % 50 == 0:
                        cam = data.get("camera_id", "unknown")
                        track = data.get("track_id", "unknown")
                        print(f"[{elapsed:.1f}s] Received {messages_received} frames... Last: Cam={cam}, Track={track}, Latency={latency}ms")
                        
                except asyncio.TimeoutError:
                    continue
                    
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the FastAPI server running?")
        print("   Start it with: uv run uvicorn api.main:app --reload")
        sys.exit(1)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"⚠️ Connection closed unexpectedly: {e}")
        
    # --- Summary ---
    print("\n" + "─" * 60)
    print("📊 Stream Summary")
    print("─" * 60)
    print(f"Duration        : {time.time() - start_time:.1f} sec")
    print(f"Total Frames    : {messages_received}")
    
    if messages_received > 0:
        fps = messages_received / (time.time() - start_time)
        print(f"Throughput      : {fps:.1f} events/sec")
    
    if latencies:
        print(f"Avg Latency     : {statistics.mean(latencies):.1f} ms")
        print(f"Min Latency     : {min(latencies):.1f} ms")
        print(f"Max Latency     : {max(latencies):.1f} ms")
    else:
        print("Latency Data    : None recorded")
    print("═" * 60)


if __name__ == "__main__":
    try:
        # Default test duration is 15 seconds
        asyncio.run(test_stream(15))
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
