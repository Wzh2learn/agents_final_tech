#!/bin/bash
# ============================================================
# Graph Engineering - Orchestrator
# ============================================================
# 启动和管理所有 Graph Loop 的 tmux 会话。
#
# 用法:
#   bash scripts/graph/graph_orchestrator.sh start   # 启动所有 Loop
#   bash scripts/graph/graph_orchestrator.sh stop    # 停止所有 Loop
#   bash scripts/graph/graph_orchestrator.sh status  # 查看状态
#   bash scripts/graph/graph_orchestrator.sh logs    # 查看最近日志
# ============================================================

set -euo pipefail

PROJECT_DIR="$HOME/wzh/projects/agents_final_tech"
GRAPH_DIR="$PROJECT_DIR/scripts/graph"
LOG_DIR="$PROJECT_DIR/logs/graph"
CODEX_BIN="${CODEX_BIN:-codex}"

mkdir -p "$LOG_DIR"

# ---- Loop B: Independent Verification (pure script) ----
start_loop_b() {
  if tmux has-session -t graph-loop-b 2>/dev/null; then
    echo "[Loop B] Already running"
    return
  fi
  echo "[Loop B] Starting verification guardian..."
  tmux new-session -d -s graph-loop-b \
    "bash $GRAPH_DIR/loop_b_verify.sh --daemon 2>&1 | tee -a $LOG_DIR/loop_b.log"
  echo "[Loop B] Started (tmux: graph-loop-b)"
}

# ---- Loop A: Execution Layer (Codex CLI) ----
start_loop_a() {
  if tmux has-session -t graph-loop-a 2>/dev/null; then
    echo "[Loop A] Already running"
    return
  fi
  echo "[Loop A] Starting execution agent..."
  tmux new-session -d -s graph-loop-a \
    "cd $PROJECT_DIR && $CODEX_BIN --full-auto \
      -q 'Read scripts/graph/loop_a_exec_constraints.md and docs/17_Graph_Engineering_多层Loop设计.md first. You are Loop A. Follow all constraints. Current task: continue M1 development per priority list. Check logs/graph/verify-report.json before starting.' \
      2>&1 | tee -a $LOG_DIR/loop_a.log"
  echo "[Loop A] Started (tmux: graph-loop-a)"
}

# ---- Loop C: Quality Audit (Codex CLI on :8005) ----
start_loop_c() {
  if tmux has-session -t graph-loop-c 2>/dev/null; then
    echo "[Loop C] Already running"
    return
  fi
  echo "[Loop C] Starting quality audit agent..."
  tmux new-session -d -s graph-loop-c \
    "cd $PROJECT_DIR && $CODEX_BIN --full-auto \
      -q 'Read scripts/graph/loop_c_audit_prompt.md first. You are Loop C. Execute a full audit cycle now. Write report to docs/experiments/.' \
      2>&1 | tee -a $LOG_DIR/loop_c.log"
  echo "[Loop C] Started (tmux: graph-loop-c)"
}

# ---- Status ----
show_status() {
  echo "=========================================="
  echo "Graph Engineering - Status Report"
  echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "=========================================="
  echo

  # tmux sessions
  echo "--- tmux sessions ---"
  for loop in graph-loop-a graph-loop-b graph-loop-c; do
    if tmux has-session -t "$loop" 2>/dev/null; then
      echo "  $loop: RUNNING"
    else
      echo "  $loop: STOPPED"
    fi
  done
  echo

  # Model services
  echo "--- Model services ---"
  for port in 8004 8005; do
    local health
    health=$(curl -s "http://127.0.0.1:$port/health" 2>/dev/null | grep -o '"ok"' || echo "DOWN")
    echo "  :$port -> $health"
  done
  echo

  # App service
  echo "--- App service ---"
  local app_health
  app_health=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:5000/health" 2>/dev/null || echo "000")
  echo "  :5000 -> HTTP $app_health"
  echo

  # Latest verify report
  echo "--- Latest Loop B report ---"
  if [[ -f "$LOG_DIR/verify-report.json" ]]; then
    cat "$LOG_DIR/verify-report.json"
  else
    echo "  No report yet"
  fi
  echo

  # Latest audit report
  echo "--- Latest Loop C audit ---"
  local latest_audit
  latest_audit=$(ls -t "$PROJECT_DIR/docs/experiments/"*audit* 2>/dev/null | head -1)
  if [[ -n "$latest_audit" ]]; then
    echo "  File: $latest_audit"
    head -5 "$latest_audit"
  else
    echo "  No audit report yet"
  fi
  echo

  # Git state
  echo "--- Git state ---"
  cd "$PROJECT_DIR"
  echo "  HEAD: $(git rev-parse --short HEAD) ($(git log --oneline -1 | cut -d' ' -f2-))"
  echo "  Branch: $(git branch --show-current)"
  echo "  Dirty: $(git status --porcelain | wc -l) files"
  echo

  # Memory
  echo "--- Memory ---"
  free -h | head -2
  echo

  # Download progress
  echo "--- 72B Download ---"
  if tmux has-session -t download-72b 2>/dev/null; then
    tmux capture-pane -t download-72b -p 2>/dev/null | tail -2
  else
    local f="$HOME/wzh/models/gguf/qwen3-72b/Qwen3-72B-Instruct.Q4_K_M.gguf"
    if [[ -f "$f" ]]; then
      echo "  Downloaded: $(ls -lh "$f" | awk '{print $5}')"
    else
      echo "  Not started or session ended"
    fi
  fi
}

# ---- Logs ----
show_logs() {
  echo "=== Loop B (last 20 lines) ==="
  tail -20 "$LOG_DIR/loop_b.log" 2>/dev/null || echo "  No log"
  echo
  echo "=== Loop A (last 10 lines) ==="
  tail -10 "$LOG_DIR/loop_a.log" 2>/dev/null || echo "  No log"
  echo
  echo "=== Loop C (last 10 lines) ==="
  tail -10 "$LOG_DIR/loop_c.log" 2>/dev/null || echo "  No log"
}

# ---- Stop ----
stop_all() {
  for loop in graph-loop-a graph-loop-b graph-loop-c; do
    if tmux has-session -t "$loop" 2>/dev/null; then
      tmux kill-session -t "$loop"
      echo "[${loop}] Stopped"
    fi
  done
}

# ---- Entry Point ----
case "${1:-status}" in
  start)
    echo "Starting Graph Engineering loops..."
    start_loop_b
    sleep 2
    start_loop_a
    sleep 2
    start_loop_c
    echo
    echo "All loops started. Use 'status' to monitor."
    ;;
  stop)
    stop_all
    ;;
  status)
    show_status
    ;;
  logs)
    show_logs
    ;;
  *)
    echo "Usage: $0 {start|stop|status|logs}"
    exit 1
    ;;
esac
