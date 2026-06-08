#!/bin/bash
# VisionTraceAI - Production Auto-Restart Supervisor

echo "Starting VisionTraceAI Production Supervisor..."

# Function to run a command and restart it if it crashes
supervise() {
    local cmd="$1"
    local name="$2"
    
    while true; do
        echo "[$(date)] Starting $name..."
        eval "$cmd"
        echo "[$(date)] $name crashed or exited with code $?. Restarting in 5 seconds..."
        sleep 5
    done
}

# 1. Start FastAPI Backend (Port 8000)
supervise "uv run uvicorn api.main:app --host 0.0.0.0 --port 8000" "FastAPI Backend" &

# 2. Start Kafka Consumer Pipeline
supervise "uv run python -c \"from backend.streaming.kafka_consumer import StreamingPipelineConsumer; c = StreamingPipelineConsumer(); c.run()\"" "Kafka Consumer" &

# 3. Start React Frontend (or serve built production files)
# For this script we use the dev server to keep it simple, but in true prod we'd serve the build directory
supervise "cd frontend && npm run dev -- --host" "React Frontend" &

echo "All services supervised. Press Ctrl+C to exit all."

# Wait for all background jobs to finish (which is never, due to the while loop)
wait
