#!/usr/bin/env bash
set -uo pipefail
PROJECT_DIR="$HOME/wzh/projects/agents_final_tech"
DASH="/tmp/graph_dashboard.txt"
HIST="/tmp/graph_dashboard_history.log"
INTERVAL="${LOOP_D_INTERVAL:-600}"
while true; do
  {
    echo "===== LOOP D DASHBOARD $(date '+%Y-%m-%d %H:%M:%S %Z') ====="
    bash "$PROJECT_DIR/scripts/graph/loop_d_monitor.sh" 2>/dev/null || echo "[monitor error]"
    echo "----- Loop B verify-report -----"
    cat "$PROJECT_DIR/logs/graph/verify-report.json" 2>/dev/null || echo "[no verify-report yet]"
    echo "----- tmux graph sessions -----"
    tmux list-sessions 2>/dev/null | grep -E "graph-loop" || echo "[no graph sessions]"
  } > "$DASH" 2>&1
  echo "[$(date '+%m-%d %H:%M:%S')] heartbeat" >> "$HIST"
  sleep "$INTERVAL"
done
