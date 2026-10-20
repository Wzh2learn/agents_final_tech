#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/home/testuser/wzh/projects/agents_final_tech/research/tatqa_wp0_2026/history_collection_execution_v1
RUN_ROOT=/home/testuser/wzh/collection_runs/AUTH-20261019-2000-CST-54REQ-5a389f0e
START_EPOCH=$(date -u -d '2026-10-19T12:00:00Z' +%s)
END_EPOCH=$(date -u -d '2026-10-19T13:30:00Z' +%s)
PRECHECK_EPOCH=$((START_EPOCH - 90))
SERVICE_PID=2642808
EXPECTED_BUNDLE=5a389f0ee0cdb6b1522fa4a291b8f95b413f59021b5ef0b8a5503d86b4f4b85c
EXPECTED_MODEL=4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d
EXPECTED_SERVER=037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d
MODEL=/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf
SERVER=/home/testuser/.lmstudio/llmster/0.0.14-2/.bundle/bin/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server

now_epoch() { date -u +%s; }

while (( $(now_epoch) < PRECHECK_EPOCH )); do
  sleep 15
done

if [[ -e "$RUN_ROOT" ]]; then
  echo "FATAL: run root already exists; refusing reopen" >&2
  exit 91
fi
if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
  echo "FATAL: bound service PID is no longer alive" >&2
  exit 92
fi
SERVICE_ARGS=$(ps -p "$SERVICE_PID" -o args=)
if [[ "$SERVICE_ARGS" != *"$MODEL"* || "$SERVICE_ARGS" != *"$SERVER"* ]]; then
  echo "FATAL: service identity drift" >&2
  exit 93
fi
if [[ "$(sha256sum "$ROOT/PRE_COLLECTION_EXECUTION_BUNDLE.json" | awk '{print $1}')" != "$EXPECTED_BUNDLE" ]]; then
  echo "FATAL: bundle identity drift" >&2
  exit 94
fi
if [[ "$(sha256sum "$MODEL" | awk '{print $1}')" != "$EXPECTED_MODEL" ]]; then
  echo "FATAL: model identity drift" >&2
  exit 95
fi
if [[ "$(sha256sum "$SERVER" | awk '{print $1}')" != "$EXPECTED_SERVER" ]]; then
  echo "FATAL: server identity drift" >&2
  exit 96
fi
(cd "$ROOT" && python3 collection_runner.py preflight --root . --bundle PRE_COLLECTION_EXECUTION_BUNDLE.json)

while (( $(now_epoch) < START_EPOCH )); do
  sleep 1
done
if (( $(now_epoch) >= END_EPOCH )); then
  echo "FATAL: window expired before execution" >&2
  exit 97
fi

mkdir -p "$RUN_ROOT"
cd "$ROOT"
python3 collection_runner.py execute \
  --root . \
  --bundle PRE_COLLECTION_EXECUTION_BUNDLE.json \
  --authorization EXECUTION_AUTHORIZATION.json \
  --raw-root "$RUN_ROOT"
