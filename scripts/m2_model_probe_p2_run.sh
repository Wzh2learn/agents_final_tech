#!/usr/bin/env bash
# P2 基准闸门一键执行 (模型升级专项, 2026-08-16)。
# 前提: :8006 vLLM 探针已 READY (scripts/vllm_probe_serve.sh)。
# 生产 :5050/:8004 不触碰; 全部走探针端点。
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
PY=./venv/bin/python
EP="${PROBE_ENDPOINT:-http://127.0.0.1:8006/v1/chat/completions}"
MODEL="${PROBE_MODEL:-qwen38-27b-fp8}"
EVAL_DIR=logs/graph/eval
OLD_EP=http://127.0.0.1:8004/v1/chat/completions
OLD_MODEL=Qwen3.6-35B-A3B-Q4_K_M.gguf

echo "== [0/7] 端点健康预检 =="
curl -s -o /dev/null -w "probe /v1/models %{http_code}\n" --max-time 5 "${EP%/chat/completions}/models" || true
curl -s -o /dev/null -w "probe /v1/health %{http_code}\n" --max-time 5 "${EP%/chat/completions}/health" || true
curl -s -o /dev/null -w "probe /health %{http_code}\n" --max-time 5 "http://$(echo ${EP#*//} | cut -d/ -f1)/health" || true

echo "== [1/7] thinking 控制验证 =="
$PY scripts/m2_model_probe_benchmark.py --mode thinking-probe \
    --endpoint "$EP" --model "$MODEL"

echo "== [2/7] 三档思考矩阵 (固定 10 题) =="
$PY scripts/m2_model_probe_benchmark.py --mode matrix \
    --endpoint "$EP" --model "$MODEL"

echo "== [3/7] 确定性 16 题 (探针直连路, thinking off) =="
$PY scripts/m2_model_probe_benchmark.py --mode deterministic \
    --endpoint "$EP" --model "$MODEL" \
    --report "$EVAL_DIR/model_probe_deterministic.json"

echo "== [4/7] 并发 3 流 =="
$PY scripts/m2_model_probe_benchmark.py --mode concurrency \
    --endpoint "$EP" --model "$MODEL"

echo "== [5/7] judge: 旧模型交叉评 (基线可比口径) =="
M2_JUDGE_ENDPOINT="$OLD_EP" M2_JUDGE_MODEL="$OLD_MODEL" \
  $PY scripts/m2_eval_judge.py \
  --input "$EVAL_DIR/model_probe_deterministic.json" \
  --report "$EVAL_DIR/model_probe_judge_by_old.json" || echo "[warn] old-judge rc=$?"

echo "== [6/7] judge: 候选模型自评 =="
M2_JUDGE_ENDPOINT="$EP" M2_JUDGE_MODEL="$MODEL" \
  $PY scripts/m2_eval_judge.py \
  --input "$EVAL_DIR/model_probe_deterministic.json" \
  --report "$EVAL_DIR/model_probe_judge_by_new.json" || echo "[warn] new-judge rc=$?"

echo "== [7/7] 视觉对比 (WaveFax 传真 + 嘉合 PDF 首页) =="
$PY scripts/m2_model_probe_benchmark.py --mode vision \
    --endpoint "$EP" --model "$MODEL" \
    --image /tmp/vllm_probe_vis/wavefax_p1-1.png \
    --compare-endpoint "$OLD_EP" --compare-model "$OLD_MODEL" \
    --report "$EVAL_DIR/model_probe_vision_wavefax.json"
$PY scripts/m2_model_probe_benchmark.py --mode vision \
    --endpoint "$EP" --model "$MODEL" \
    --image /tmp/vllm_probe_vis/jiahe_p1-1.png \
    --report "$EVAL_DIR/model_probe_vision_jiahe.json"

echo "P2_RUN_DONE"