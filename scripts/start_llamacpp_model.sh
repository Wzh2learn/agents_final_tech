#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <model_gguf_path> <port> <log_path> [ctx_size]" >&2
  exit 2
fi

MODEL_PATH="$1"
PORT="$2"
LOG_PATH="$3"
CTX_SIZE="${4:-${LLAMA_CTX_SIZE:-16384}}"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server}"

if [[ ! -x "$LLAMA_SERVER" ]]; then
  echo "llama-server not found or not executable: $LLAMA_SERVER" >&2
  exit 1
fi

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "model file not found: $MODEL_PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$LOG_PATH")"
nohup "$LLAMA_SERVER" \
  -m "$MODEL_PATH" \
  --host 127.0.0.1 \
  --port "$PORT" \
  -c "$CTX_SIZE" \
  -ngl 999 \
  > "$LOG_PATH" 2>&1 < /dev/null &

PID="$!"
echo "started llama.cpp server"
echo "pid: $PID"
echo "base_url: http://127.0.0.1:$PORT/v1"
echo "log: $LOG_PATH"
