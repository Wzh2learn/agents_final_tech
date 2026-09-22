#!/usr/bin/env bash
# Canonical foreground launcher for the M1/M2 HTTP application.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

if [ -z "${PYTHON_BIN:-}" ] && [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
else
    PYTHON_BIN="${PYTHON_BIN:-python}"
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python executable not found: $PYTHON_BIN" >&2
    exit 1
fi

dotenv_value() {
    "$PYTHON_BIN" -c 'from dotenv import dotenv_values; import sys; print(dotenv_values(".env").get(sys.argv[1], ""))' "$1"
}
if [ -f ".env" ]; then
    PGDATABASE_URL="${PGDATABASE_URL:-$(dotenv_value PGDATABASE_URL)}"
    M1_HOST="${M1_HOST:-$(dotenv_value M1_HOST)}"
    M1_PORT="${M1_PORT:-$(dotenv_value M1_PORT)}"
    M1_WORKERS="${M1_WORKERS:-$(dotenv_value M1_WORKERS)}"
fi

export PGDATABASE_URL="${PGDATABASE_URL:-postgresql://postgres:postgres@127.0.0.1:15432/vector_db}"
M1_HOST="${M1_HOST:-0.0.0.0}"
M1_PORT="${M1_PORT:-5050}"
M1_WORKERS="${M1_WORKERS:-2}"
export M1_HOST M1_PORT M1_WORKERS

if ! [[ "$M1_PORT" =~ ^[0-9]+$ ]] || [ "$M1_PORT" -lt 1 ] || [ "$M1_PORT" -gt 65535 ]; then
    echo "ERROR: M1_PORT must be an integer between 1 and 65535." >&2
    exit 2
fi
if ! [[ "$M1_WORKERS" =~ ^[0-9]+$ ]] || [ "$M1_WORKERS" -lt 1 ]; then
    echo "ERROR: M1_WORKERS must be a positive integer." >&2
    exit 2
fi

CHECK_HOST="$M1_HOST"
[ "$CHECK_HOST" = "0.0.0.0" ] && CHECK_HOST="127.0.0.1"
if "$PYTHON_BIN" -c 'import socket, sys; sock = socket.socket(); sock.settimeout(0.2); sys.exit(0 if sock.connect_ex((sys.argv[1], int(sys.argv[2]))) == 0 else 1)' "$CHECK_HOST" "$M1_PORT"; then
    echo "ERROR: Port $M1_PORT is already in use. Stop the owning service explicitly or set M1_PORT to a free port." >&2
    exit 2
fi

export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
echo "Starting M1/M2 on ${M1_HOST}:${M1_PORT} with ${M1_WORKERS} workers"
echo "Press Ctrl+C to stop the development server."
exec "$PYTHON_BIN" -m uvicorn main:app --host "$M1_HOST" --port "$M1_PORT" --workers "$M1_WORKERS"
