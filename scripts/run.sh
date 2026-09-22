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

# Canonical local runtime values. Explicitly exported values win; otherwise
# read the same .env file as the application before applying development defaults.
dotenv_value() {
    python -c 'from dotenv import dotenv_values; import sys; print(dotenv_values(".env").get(sys.argv[1], ""))' "$1"
}
if [ -f ".env" ]; then
    PGDATABASE_URL="${PGDATABASE_URL:-$(dotenv_value PGDATABASE_URL)}"
    M1_PORT="${M1_PORT:-$(dotenv_value M1_PORT)}"
fi
export PGDATABASE_URL="${PGDATABASE_URL:-postgresql://postgres:postgres@127.0.0.1:15432/vector_db}"
M1_PORT="${M1_PORT:-5050}"
if ! [[ "$M1_PORT" =~ ^[0-9]+$ ]] || [ "$M1_PORT" -lt 1 ] || [ "$M1_PORT" -gt 65535 ]; then
    echo "ERROR: M1_PORT must be an integer between 1 and 65535." >&2
    exit 2
fi

# Refuse to replace an existing listener.  This launcher is safe to run in a
# shared development environment and never terminates another process.
if python -c 'import socket, sys; sock = socket.socket(); sock.settimeout(0.2); sys.exit(0 if sock.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)' "$M1_PORT"; then
    echo "ERROR: Port $M1_PORT is already in use. Stop the owning service explicitly or set M1_PORT to a free port." >&2
    exit 2
fi

# Check PGVector
echo "[2/4] Checking PostgreSQL + PGVector..."
if ! docker ps --format '{{.Names}}' | grep -q pgvector; then
    echo "  Starting PGVector container..."
    docker run -d --name pgvector \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=vector_db \
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
echo "[4/4] Starting M1/M2 harness on :${M1_PORT}..."
export PYTHONPATH=src

echo "  M1/M2 UI:    http://localhost:${M1_PORT}/m1"
echo "  API docs:    http://localhost:${M1_PORT}/docs"
echo "  Health:      http://localhost:${M1_PORT}/health"
echo "  Press Ctrl+C to stop the development server."

exec python -m uvicorn main:app --host 0.0.0.0 --port "$M1_PORT" --workers 2
