#!/usr/bin/env bash
# Restart the OpenCode sidecar (:4096) so it reloads opencode.json + skills/.
#
# Background (2026-08-09): opencode serve does NOT hot-reload config; a
# sidecar started before an opencode.json/skills change silently serves the
# stale agent prompts for days. After ANY change to opencode.json or skills/,
# run this script before eval/rehearsal.
#
# Usage: bash scripts/restart_opencode_sidecar.sh
set -uo pipefail

PORT=4096
TMUX_SESSION="opencode-serve"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE="http://127.0.0.1:$PORT"

echo "[sidecar] killing existing opencode serve (if any)"
pkill -9 -f "opencode serve" 2>/dev/null
sleep 2

if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  tmux new-session -d -s "$TMUX_SESSION"
fi
tmux send-keys -t "$TMUX_SESSION" "cd $REPO_DIR && set -a && source .env && set +a && bash scripts/run_opencode_gb10.sh serve" Enter

echo "[sidecar] waiting for health"
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health" 2>/dev/null)
  if [ "$code" = "200" ]; then
    echo "[sidecar] health 200 after ~$((i * 2))s"
    break
  fi
  sleep 2
done
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health" 2>/dev/null)
if [ "$code" != "200" ]; then
  echo "[sidecar] FAIL: health=$code"
  exit 1
fi

echo "[sidecar] verifying skill load"
SKILLS=$(curl -s "$BASE/skill" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d if isinstance(d, list) else d.get('skills') or []
names = sorted((s.get('name') or '') for s in items)
print(len(names), ','.join(n for n in names if n in ('m2-rag-playbook', 'm1-gap-triage', 'graph-loop-rules')))
")
COUNT=$(echo "$SKILLS" | cut -d" " -f1)
FOUND=$(echo "$SKILLS" | cut -d" " -f2)
echo "[sidecar] skills loaded: $COUNT | key skills present: $FOUND"
if [ "$COUNT" -lt 10 ]; then
  echo "[sidecar] FAIL: unexpectedly few skills loaded"
  exit 1
fi
# --- warm-up ask (latency fix a, 2026-08-12): 预热 sidecar+模型 prefill, 冷启 43s→~23s ---
echo "[sidecar] warm-up ask (latency fix a; 真实检索题以预热 jinrong-rag MCP + embedding)"
WARM_T0=$(date +%s)
WARM_SID=$(curl -s -m 15 -X POST "$BASE/session" -H "Content-Type: application/json" -d "{}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
if [ -n "${WARM_SID:-}" ]; then
  curl -s -m 240 -X POST "$BASE/session/$WARM_SID/message" -H "Content-Type: application/json" \
    -d '{"parts":[{"type":"text","text":"嘉兴民安的总资产是多少？/no_think"}],"agent":"m2-qa"}' > /tmp/sidecar_warmup_reply.json 2>&1 \
    && echo "[sidecar] warm-up reply received" \
    || echo "[sidecar] warm-up ask 失败 (不阻塞, 首问会冷一些)"
  curl -s -m 10 -X DELETE "$BASE/session/$WARM_SID" > /dev/null 2>&1
  echo "[sidecar] warm-up 耗时 $(( $(date +%s) - WARM_T0 ))s"
else
  echo "[sidecar] warm-up 跳过 (session 创建失败)"
fi

echo "[sidecar] PASS: sidecar restarted with fresh config"
