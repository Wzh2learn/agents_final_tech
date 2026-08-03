#!/bin/bash
# ============================================================
# Graph Engineering - Loop D: Strategic Monitor
# ============================================================
# 给指挥层 (用户 + 本机 Codex) 用的快速状态检查。
# 可从本机通过 SSH 调用:
#   ssh jinrong-dev "bash ~/wzh/projects/agents_final_tech/scripts/graph/loop_d_monitor.sh"
#
# 输出: 一份简洁的战略级状态摘要, 供 Loop D 决策用。
# ============================================================

set -euo pipefail

PROJECT_DIR="$HOME/wzh/projects/agents_final_tech"
LOG_DIR="$PROJECT_DIR/logs/graph"

echo "============================================"
echo "  GRAPH ENGINEERING - LOOP D STRATEGIC VIEW"
echo "  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "============================================"
echo

# 1. Overall health
echo "[1] SYSTEM HEALTH"

m8004=$(curl -s http://127.0.0.1:8004/health 2>/dev/null | grep -c ok || echo 0)
m8005=$(curl -s http://127.0.0.1:8005/health 2>/dev/null | grep -c ok || echo 0)
app=$(curl -s -o /dev/null -w '%{http_code}' "${M1_API_BASE:-http://127.0.0.1:5050}/health" 2>/dev/null || echo 000)

[[ "$m8004" -ge 1 ]] && echo "  :8004 main model    [OK]" || echo "  :8004 main model    [DOWN]"
[[ "$m8005" -ge 1 ]] && echo "  :8005 aux model     [OK]" || echo "  :8005 aux model     [DOWN] (non-critical)"
[[ "$app" == "200" ]] && echo "  :5000 FastAPI       [OK]" || echo "  :5000 FastAPI       [DOWN: $app]"
echo

# 2. Loop status
echo "[2] LOOP STATUS"
for loop in graph-loop-a graph-loop-b graph-loop-c; do
  if tmux has-session -t "$loop" 2>/dev/null; then
    echo "  $loop  [RUNNING]"
  else
    echo "  $loop  [STOPPED]"
  fi
done
legacy=$(tmux ls 2>/dev/null | grep -v graph-loop | grep -v download | grep -v coding-jinrong | wc -l)
[[ "$legacy" -gt 0 ]] && echo "  (legacy tmux sessions: $legacy)"
echo

# 3. Loop B verdict
echo "[3] LOOP B VERDICT (independent verification)"
if [[ -f "$LOG_DIR/verify-report.json" ]]; then
  overall=$(python3 -c "import json; print(json.load(open('$LOG_DIR/verify-report.json'))['overall'])" 2>/dev/null || echo "PARSE_ERROR")
  ts=$(python3 -c "import json; print(json.load(open('$LOG_DIR/verify-report.json'))['timestamp'])" 2>/dev/null || echo "?")
  echo "  Result: $overall  (at $ts)"
  if [[ "$overall" == "FAIL" ]]; then
    echo "  >>> ACTION NEEDED: Loop A should halt and fix <<<"
  fi
else
  echo "  No report yet (Loop B may not have run)"
fi
echo

# 4. Loop C latest audit
echo "[4] LOOP C AUDIT (quality review)"
latest_audit=$(ls -t "$PROJECT_DIR/docs/experiments/"*audit* 2>/dev/null | head -1)
if [[ -n "$latest_audit" ]]; then
  echo "  Latest: $(basename "$latest_audit")"
  verdict=$(grep -iE 'ACCEPTED|REJECTED|CONDITIONAL' "$latest_audit" | head -1 || echo "  (verdict not found)")
  echo "  Verdict: $verdict"
else
  echo "  No audit report yet"
fi
echo

# 5. Git progress
echo "[5] GIT PROGRESS"
cd "$PROJECT_DIR"
echo "  HEAD: $(git log --oneline -1)"
echo "  Last 5 commits:"
git log --oneline -5 | sed 's/^/    /'
dirty=$(git status --porcelain | wc -l)
echo "  Uncommitted changes: $dirty files"
git fetch origin main --quiet 2>/dev/null || true
behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
echo "  vs origin/main: +$ahead / -$behind"
echo

# 6. Frozen node integrity
echo "[6] FROZEN NODES"
frozen_file="$PROJECT_DIR/scripts/graph/frozen_hashes.txt"
if [[ -f "$frozen_file" ]]; then
  violations=0
  while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    expected=$(echo "$line" | awk '{print $1}')
    fpath=$(echo "$line" | awk '{print $2}')
    [[ "$fpath" != /* ]] && fpath="$PROJECT_DIR/$fpath"
    if [[ -f "$fpath" ]]; then
      actual=$(md5sum "$fpath" | awk '{print $1}')
      [[ "$actual" != "$expected" ]] && { echo "  TAMPERED: $fpath"; violations=$((violations+1)); }
    else
      echo "  MISSING: $fpath"; violations=$((violations+1))
    fi
  done < "$frozen_file"
  [[ "$violations" -eq 0 ]] && echo "  All frozen nodes intact [OK]"
else
  echo "  No frozen hash file found"
fi
echo

# 7. Resources
echo "[7] RESOURCES"
mem_used=$(free -g | awk '/Mem:/{print $3}')
mem_total=$(free -g | awk '/Mem:/{print $2}')
echo "  Memory: ${mem_used}GB / ${mem_total}GB"
disk_used=$(df -h /home | awk 'NR==2{print $3}')
disk_total=$(df -h /home | awk 'NR==2{print $2}')
echo "  Disk: $disk_used / $disk_total"
echo

# 8. Pending items
echo "[8] PENDING"
if tmux has-session -t download-72b 2>/dev/null; then
  progress=$(tmux capture-pane -t download-72b -p 2>/dev/null | grep -oP '\d+%' | tail -1 || echo "?")
  echo "  Qwen3-72B download: $progress"
else
  f="$HOME/wzh/models/gguf/qwen3-72b/Qwen3-72B-Instruct.Q4_K_M.gguf"
  [[ -f "$f" ]] && echo "  Qwen3-72B: DOWNLOADED ($(du -h "$f" | cut -f1))" || echo "  Qwen3-72B: not found"
fi
echo "  Codex CLI + GLM 5.2: FAILED (pending investigation)"
echo "  TAT-DQA: FROZEN"
echo
echo "============================================"
echo "  End of strategic view"
echo "============================================"
