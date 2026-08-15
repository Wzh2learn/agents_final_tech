#!/usr/bin/env bash
# vLLM GB10 探针启动脚本 (模型升级专项 P1, 2026-08-15)
# 独立探针端口 :8006, 不触碰生产 :8004/:8005。
# 内存预算: 机器 121GB 统一内存, llama.cpp 生产模型常驻 ~30GB+,
#   gpu-memory-utilization 默认 0.35 (~44GB); 只许调低不许调高。
# 用法:
#   bash scripts/vllm_probe_serve.sh            # 前台运行 (Ctrl-C 停)
#   PORT=8006 GMEM=0.35 MAXLEN=32768 bash scripts/vllm_probe_serve.sh
set -euo pipefail

IMAGE="${VLLM_IMAGE:-dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1}"
MODEL_DIR="${MODEL_DIR:-$HOME/wzh/models/hf/Qwen3.8-27B-FP8}"
PORT="${PORT:-8006}"
GMEM="${GMEM:-0.27}"
MAXLEN="${MAXLEN:-32768}"
SERVED_NAME="${SERVED_NAME:-qwen38-27b-fp8}"
MAXSEQS="${MAXSEQS:-32}"

if [[ ! -f "$MODEL_DIR/config.json" ]]; then
  echo "model dir not ready: $MODEL_DIR" >&2
  exit 1
fi

exec docker run --rm --name vllm-probe \
  --device nvidia.com/gpu=all \
  --ipc host \
  -p "$PORT:8000" \
  -v "$MODEL_DIR:/models/Qwen3.8-27B-FP8:ro" \
  -v "$HOME/wzh/vllm_cache:/root/.cache/vllm" \
  "$IMAGE" \
  vllm serve /models/Qwen3.8-27B-FP8 \
  --served-model-name "$SERVED_NAME" \
  --gpu-memory-utilization "$GMEM" \
  --max-num-seqs "$MAXSEQS" \
  --max-model-len "$MAXLEN" \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --limit-mm-per-prompt '{"image":2}' \
  --trust-remote-code