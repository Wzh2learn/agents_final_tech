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
echo "[4/4] Starting M1/M2 harness through the canonical launcher..."
exec ./serve.sh
