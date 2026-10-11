#!/bin/bash
# ============================================================
# Graph Engineering - Orchestrator
# ============================================================
# 管理 Loop B，并显示 A/C 的人工派发入口。
#
# 用法:
#   bash scripts/graph/graph_orchestrator.sh start   # 启动 B 并显示 A/C 入口，须授权
#   bash scripts/graph/graph_orchestrator.sh stop    # 停止匹配的 tmux 会话，须授权
#   bash scripts/graph/graph_orchestrator.sh status  # 访问服务探测状态，非零调用
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

start_loop_a() {
  cat <<'EOF_LOOPA'
[Loop A] 当前派发入口是 scripts/graph/loop_ac_launcher.sh。
  本 orchestrator 只管理 Loop B，不自动启动 A/C。
  先运行 launcher preflight，再用 start a <task-id> <prompt-file> 启动 detached task。
  规则与任务授权仍由 AGENTS.md、memory/STATE.md、memory/THREADS.md 和任务卡决定。
  执行约束: scripts/graph/loop_a_exec_constraints.md。
  任务合同: templates/task_card_template.md。
  执行面: docs/governance/2026-09-07_execution_plane_boundary.md。
EOF_LOOPA
}

start_loop_c() {
  cat <<'EOF_LOOPC'
[Loop C] 当前派发入口是 scripts/graph/loop_ac_launcher.sh。
  本 orchestrator 只管理 Loop B，不自动启动 A/C。
  先运行 launcher preflight，再用 start c <task-id> <prompt-file> 启动 detached task。
  Loop C 保持独立只读审计；模型、服务、数据库和真实样本解析须按任务卡授权。
  审计约束: scripts/graph/loop_c_audit_prompt.md。
  任务合同: templates/task_card_template.md。
  执行面: docs/governance/2026-09-07_execution_plane_boundary.md。
EOF_LOOPC
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
  if tmux has-session -t graph-loop-b 2>/dev/null; then
    echo "  graph-loop-b: RUNNING"
  else
    echo "  graph-loop-b: STOPPED"
  fi
  ac_sessions=$(tmux ls 2>/dev/null | grep -E '^loop-(a|c)-' || true)
  if [[ -n "$ac_sessions" ]]; then
    echo "$ac_sessions" | sed 's/^/  /'
  else
    echo "  Loop A/C detached tasks: none"
  fi
  echo

  # Model services
  echo "--- Model services ---"
  for port in 8004 8006; do
    local health
    health=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$port/health" 2>/dev/null || echo "000")
    echo "  :$port -> HTTP $health"
  done
  echo "  :8005 -> RETIRED (2026-08-17, Qwen3-14B 退位)" 
  echo

  # App service
  echo "--- App service ---"
  local app_health
  app_health=$(curl -s -o /dev/null -w '%{http_code}' "${M1_API_BASE:-http://127.0.0.1:5050}/health" 2>/dev/null || echo "000")
  echo "  ${M1_API_BASE:-http://127.0.0.1:5050} -> HTTP $app_health"
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

  # 72B download probe removed 2026-08-04 (model evaluated, rejected and deleted 2026-08-03)
}

# ---- Logs ----
show_logs() {
  echo "=== Loop B (last 20 lines) ==="
  tail -20 "$LOG_DIR/loop_b.log" 2>/dev/null || echo "  No log"
  echo
  echo "=== Loop A/C ==="
  echo "  Use: bash scripts/graph/loop_ac_launcher.sh logs <task-id> <a|c> [lines]"
}

# ---- Stop ----
stop_all() {
  if tmux has-session -t graph-loop-b 2>/dev/null; then
    tmux kill-session -t graph-loop-b
    echo "[graph-loop-b] Stopped"
  fi
  echo "Loop A/C tasks are managed by loop_ac_launcher.sh stop <task-id> <a|c>"
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
    echo "Loop B 启动步骤已返回，未核验健康；A/C 仅显示派发入口，未启动。status 会访问真实服务，须另有授权。"
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
