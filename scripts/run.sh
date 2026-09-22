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

# Refuse to replace an existing listener.  This launcher is safe to run in a
# shared development environment and never terminates another process.
if python -c 'import socket, sys; sock = socket.socket(); sock.settimeout(0.2); sys.exit(0 if sock.connect_ex(("127.0.0.1", 5050)) == 0 else 1)'; then
    echo "ERROR: Port 5050 is already in use. Stop the owning service explicitly or choose another launcher configuration." >&2
    exit 2
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

echo "  M1/M2 UI:    http://localhost:5050/m1"
echo "  API docs:    http://localhost:5050/docs"
echo "  Health:      http://localhost:5050/health"
echo "  Press Ctrl+C to stop the development server."

exec python -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2
