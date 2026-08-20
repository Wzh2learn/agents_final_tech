#!/usr/bin/env bash
# vLLM GB10 探针启动脚本 (模型升级专项 P1, 2026-08-15)
# 独立探针端口 :8006, 不触碰生产 :8004/:8005。
# 内存预算: 机器 121GB 统一内存, llama.cpp 生产模型常驻 ~30GB+,
#   gpu-memory-utilization 默认 0.30 (~39GB); 只许调低不许调高
#   (0.27 差 0.44GiB 失败; 0.35 为理论上限无余量, 勿用)。
#   [08-21 窗口 v3 用户授权覆写] DSpark 规格需 KV ≥4.6GiB, GMEM 0.30 预算仅
#   3.0-3.1G (08-20/21 五连败 2.13-3.08G; 探针 08-19 偶得 5.96G 为贴边侥幸),
#   提至 0.34 (上限 41.35G; 探针峰值实测 37.07G, 余量 4.2G)。覆写仅适用于
#   用户批准窗口; 此后 GMEM 上调一律需用户窗口批准 + 内存算术, 默认仍只降不升。
# 用法:
#   bash scripts/vllm_probe_serve.sh            # 前台运行 (Ctrl-C 停)
#   PORT=8006 GMEM=0.30 MAXLEN=32768 bash scripts/vllm_probe_serve.sh
#   换模型 (如 35B-A3B 探针): MODEL_DIR + SERVED_NAME + PORT 覆写,
#   容器内路径固定 /models/model, 无需改脚本。
# DSpark 投机解码探针 (2026-08-19, Track 1 Route V):
#   CONTAINER_NAME=vllm-dspark-v PORT=8007 \
#   DRAFTER_DIR=$HOME/wzh/models/hf/Qwen3.8-27B-DSpark-vLLM \
#   CHAT_TEMPLATE=$HOME/wzh/vllm_cache/qwen38_think_off_default.jinja \
#   bash scripts/vllm_probe_serve.sh
#   DRAFTER_K=7 / DRAFTER_SAMPLE=probabilistic 可覆写。README 结论:
#   probabilistic 比 greedy 快 ~23%, k 不可缩减 —— 详见
#   docs/experiments/2026-08-19_dspark_drafter_ledger.md
set -euo pipefail

IMAGE="${VLLM_IMAGE:-dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1}"
MODEL_DIR="${MODEL_DIR:-$HOME/wzh/models/hf/Qwen3.8-27B-FP8}"
PORT="${PORT:-8006}"
GMEM="${GMEM:-0.30}"
MAXLEN="${MAXLEN:-32768}"
SERVED_NAME="${SERVED_NAME:-qwen38-27b-fp8}"
MAXSEQS="${MAXSEQS:-32}"
CONTAINER_NAME="${CONTAINER_NAME:-vllm-probe}"
# FM7 (2026-08-17): APC was OFF in this build (prefix_cache_queries=0):
# every call re-prefilled ~15-19k tokens -> 45-85s agent turns.
# --enable-prefix-caching restores cross-call/session prefix reuse.
# FM6 (2026-08-17): Qwen3.8 emits tool calls as XML tags; hermes parser
# misses them (tool_calls=null, answer swallowed into content). Use qwen3_xml.
TOOL_PARSER="${TOOL_PARSER:-qwen3_xml}"
# CHAT_TEMPLATE: 自定义 jinja 模板路径 (可选); 用于服务器级思考默认值改造,
# 例: ~/wzh/vllm_cache/qwen38_think_off_default.jinja (默认 thinking off)
CHAT_TEMPLATE="${CHAT_TEMPLATE:-}"
# KV_CACHE_MEMORY (可选, 08-21 窗口 v3): 显式钉死 KV 预算 (字节), 绕过 GMEM
#   预算自动切分的 profiling 噪声轮盘 (vllm#48140 同族 MemFree 口径问题)。
#   例: KV_CACHE_MEMORY=6442450944 (6.0 GiB, DSpark 硬门槛 4.6G 留余量)。
KV_CACHE_MEMORY="${KV_CACHE_MEMORY:-}"

if [[ ! -f "$MODEL_DIR/config.json" ]]; then
  echo "model dir not ready: $MODEL_DIR" >&2
  exit 1
fi

TEMPLATE_MOUNT=()
TEMPLATE_VLLM=()
if [[ -n "$CHAT_TEMPLATE" ]]; then
  TEMPLATE_MOUNT=(-v "$CHAT_TEMPLATE:/models/chat_template_custom.jinja:ro")
  TEMPLATE_VLLM=(--chat-template /models/chat_template_custom.jinja)
fi

# DSpark drafter (可选, 2026-08-19): 设置后挂载 /models/drafter 并追加 --speculative-config
DRAFTER_MOUNT=()
DRAFTER_VLLM=()
KV_VLLM=()
if [[ -n "$KV_CACHE_MEMORY" ]]; then
  KV_VLLM=(--kv-cache-memory "$KV_CACHE_MEMORY")
fi
if [[ -n "${DRAFTER_DIR:-}" ]]; then
  if [[ ! -f "$DRAFTER_DIR/model.safetensors" ]]; then
    echo "drafter dir not ready: $DRAFTER_DIR" >&2
    exit 1
  fi
  DRAFTER_MOUNT=(-v "$DRAFTER_DIR:/models/drafter:ro")
  DRAFTER_VLLM=(--speculative-config "{\"method\":\"dspark\",\"model\":\"/models/drafter\",\"num_speculative_tokens\":${DRAFTER_K:-7},\"draft_sample_method\":\"${DRAFTER_SAMPLE:-probabilistic}\"}")
fi

exec docker run --rm --name "$CONTAINER_NAME" \
  --device nvidia.com/gpu=all \
  --ipc host \
  -p "$PORT:8000" \
  -v "$MODEL_DIR:/models/model:ro" \
  -v "$HOME/wzh/vllm_cache:/root/.cache/vllm" \
  "${TEMPLATE_MOUNT[@]}" \
  "${DRAFTER_MOUNT[@]}" \
  "$IMAGE" \
  vllm serve /models/model \
  --served-model-name "$SERVED_NAME" \
  --gpu-memory-utilization "$GMEM" \
  --max-num-seqs "$MAXSEQS" \
  --max-model-len "$MAXLEN" \
  --enable-prefix-caching \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser "$TOOL_PARSER" \
  --limit-mm-per-prompt '{"image":2}' \
  "${TEMPLATE_VLLM[@]}" \
  "${KV_VLLM[@]}" \
  "${DRAFTER_VLLM[@]}" \
  --trust-remote-code