#!/usr/bin/env bash
# Remote autonomous supervisor for the client-M1 loop chain.
# Waits for already-running A (schema) and B (ocr) loops to finish, then
# launches C (LLM header mapping) after A, and D (multi-agent delegation)
# after B and C. Runs detached via nohup; does NOT depend on any live session.
set -uo pipefail
source ~/.bashrc 2>/dev/null
export PATH="$HOME/.npm-global/bin:$PATH"
PROJ="$HOME/wzh/projects/agents_final_tech"
EXP="$PROJ/docs/experiments"
LOG=/tmp/supervisor.log
{ echo; echo "===== supervisor start $(date '+%m-%d %T') pid=$$ ====="; } > "$LOG"
log() { echo "[$(date '+%m-%d %T')] $*" | tee -a "$LOG"; }

# wait for a glob marker; if a tmux session name is given, fail early when it
# dies without producing the marker (loop crashed).
wait_for() {
  local pat="$1" to="$2" tm="${3:-}"
  local dl=$(( SECONDS + to ))
  while [ $SECONDS -lt $dl ]; do
    ls $pat >/dev/null 2>&1 && return 0
    if [ -n "$tm" ] && ! tmux has-session -t "$tm" 2>/dev/null; then
      sleep 15; ls $pat >/dev/null 2>&1 && return 0; return 1
    fi
    sleep 20
  done
  return 1
}
launch() {
  local name="$1" loop="$2"
  log "LAUNCH $name ($loop)"
  tmux kill-session -t "$name" 2>/dev/null
  tmux new-session -d -s "$name" "cd $PROJ && source ~/.bashrc && cat $loop | codex exec --dangerously-bypass-approvals-and-sandbox > /tmp/codex_$name.log 2>&1"
}

C_LAUNCHED=0
log "waiting A (schema_reconcile, tmux codex-m1-schema)"
if wait_for "$EXP/*_m1_schema_reconcile.md" 4200 codex-m1-schema; then
  log "A done -> launch C"
  launch codex-m1-llmap scripts/loop_m1_header_mapping_llm.md
  C_LAUNCHED=1
else
  log "A timeout/crash -> skip C"
fi

log "waiting B (ocr_fallback, tmux codex-m1-ocr) [C runs in parallel if launched]"
wait_for "$EXP/*_m1_ocr_fallback.md" 5400 codex-m1-ocr || log "B timeout/crash (continue)"

if [ "$C_LAUNCHED" = 1 ]; then
  log "waiting C (header_mapping_llm, tmux codex-m1-llmap)"
  wait_for "$EXP/*_m1_header_mapping_llm.md" 5400 codex-m1-llmap || log "C timeout/crash (continue)"
fi

if ls "$EXP"/*_m1_ocr_fallback.md >/dev/null 2>&1 && ls "$EXP"/*_m1_header_mapping_llm.md >/dev/null 2>&1; then
  log "B+C done -> launch D"
  launch codex-m1-multi scripts/loop_m1_multiagent_delegation.md
  wait_for "$EXP/*_m1_multiagent_delegation.md" 5400 codex-m1-multi || log "D timeout/crash"
else
  log "B or C marker missing -> skip D"
fi
log "===== supervisor chain finished $(date '+%m-%d %T') ====="
