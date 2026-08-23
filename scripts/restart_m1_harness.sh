#!/bin/bash
# :5050 M1/M2 harness 重启 SOP (2026-08-23 代码窗定型; 回滚=原参数重起)
# 窗前存档: logs/graph/eval/m1_harness_window_archive_20260823.txt
# env 基线: PGDATABASE_URL / OPENCODE_ASK_TIMEOUT / M2_OPENCODE_ROUTE /
#           LOCAL_EMBEDDING_MODEL_PATH / LOCAL_EMBEDDING_DEVICE / PYTHONPATH
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)/src"
export PGDATABASE_URL="${PGDATABASE_URL:-postgresql://postgres:postgres@127.0.0.1:15432/vector_db}"
export OPENCODE_ASK_TIMEOUT="${OPENCODE_ASK_TIMEOUT:-45}"
export M2_OPENCODE_ROUTE="${M2_OPENCODE_ROUTE:-on}"
export LOCAL_EMBEDDING_MODEL_PATH="${LOCAL_EMBEDDING_MODEL_PATH:-/home/testuser/wzh/models/hf/qwen3-embedding-0.6b}"
export LOCAL_EMBEDDING_DEVICE="${LOCAL_EMBEDDING_DEVICE:-cpu}"
pkill -f "uvicorn main:app.*5050" 2>/dev/null || true
sleep 2
nohup ./venv/bin/python ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2 \
    > logs/m1_service.log 2>&1 &
echo "launched PID $!"
