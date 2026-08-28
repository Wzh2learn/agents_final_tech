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

# ---- Loop A: Execution Layer (一次性派活模式, 2026-08-04 更新) ----
start_loop_a() {
  cat <<'EOF_LOOPA'
[Loop A] Loop A 为一次性派活 (codex exec), 非常驻进程。派活方式:
  1) 任务写入 /tmp/task.md (目标/步骤/约束/验收标准)
  2) tmux new-session -d -s loop-a-taskN "cd $PROJ && source ~/.bashrc && \
       cat scripts/graph/loop_a_exec_constraints.md /tmp/task.md | \
       codex exec --profile loopa-exec --dangerously-bypass-approvals-and-sandbox 2>&1 | tee -a logs/graph/loop_a.log"
     (PROJ=~/wzh/projects/agents_final_tech)
  模型路由 (2026-08-27, 按任务性质双档路由; profile 单文件在仓外不入 git):
    - 执行卡(默认) --profile loopa-exec  = qwen3.8-flash / Token_Plan / medium
      适用: 明确卡面的确定性执行 (脚本修补/工件整理/实验流水/数据复算)
    - 诊断卡 --profile loopa-diag = deepseek-v4-flash-0731 / Token_Plan_Chat / xhigh
      适用: 根因诊断/归因分析/设计稿/任何需深度推理的任务
    - profile 文件: ~/.codex/loopa-exec.config.toml 与 ~/.codex/loopa-diag.config.toml
      (勿写 config.toml [profiles.X] legacy 块, codex 0.145 报错)
详见 docs/17 §8 与 memory/CORE.md「分发通道」。
EOF_LOOPA
}

# ---- Loop C: Quality Audit (Claude Code + qwen3.8-max, 2026-08-04 更新) ----
start_loop_c() {
  cat <<'EOF_LOOPC'
[Loop C] Loop C 载体为 Claude Code (qwen3.8-max, Anthropic 兼容端点), 非常驻进程。派活方式:
  cd $PROJ && claude --bare -p "$(cat scripts/graph/loop_c_audit_prompt.md)" > docs/experiments/<audit_report>.md
必须用 --bare: oh-my-claudecode 插件 bridge 在非交互派发下挂死（08-29 根因坐实, 探针 --bare 9s 正常）。
详见 docs/17 §6 与 memory/CORE.md「分发通道」。
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
