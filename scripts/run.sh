#!/bin/bash
# One-click startup script for M1/M2 system
set -e

echo "=== M1/M2 Financial Statement System ==="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.11+"
    exit 1
fi

# Check venv
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# Check PGVector
echo "[2/4] Checking PostgreSQL + PGVector..."
if ! docker ps --format '{{.Names}}' | grep -q pgvector; then
    echo "  Starting PGVector container..."
    docker run -d --name pgvector \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=m1_statements \
        -p 15432:5432 \
        pgvector/pgvector:pg16 2>/dev/null || {
        echo "  WARNING: Docker not available. Ensure PostgreSQL with pgvector is running on :15432"
    }
    sleep 3
else
    echo "  PGVector container already running."
fi

# Check model services
echo "[3/4] Checking model services..."
if curl -s http://127.0.0.1:8004/health >/dev/null 2>&1; then
    echo "  :8004 (35B + vision) OK"
else
    echo "  WARNING: :8004 not responding. LLM features will be unavailable."
fi

# Start M1 harness
echo "[4/4] Starting M1/M2 harness on :5050..."
export PYTHONPATH=src
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:15432/m1_statements}"

# Kill existing if running
pkill -f "uvicorn main:app.*5050" 2>/dev/null || true
sleep 1

nohup python -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2 \
    > logs/m1_service.log 2>&1 &
echo "  PID: $!"

sleep 2
if curl -s http://127.0.0.1:5050/health | grep -q ok; then
    echo ""
    echo "=== System Ready ==="
    echo "  M1/M2 UI:    http://localhost:5050/m1"
    echo "  API docs:    http://localhost:5050/docs"
    echo "  Health:      http://localhost:5050/health"
    echo ""
else
    echo "  WARNING: Service may still be starting. Check logs/m1_service.log"
fi