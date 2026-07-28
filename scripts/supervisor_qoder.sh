#!/usr/bin/env bash
# v2 supervisor: backstop D if old supervisor skips it, then run Qoder recon.
# Independent of supervisor_m1.sh; mutually-exclusive with it on D (no double-launch).
set -uo pipefail
source ~/.bashrc 2>/dev/null
export PATH="$HOME/.npm-global/bin:$PATH"
PROJ="$HOME/wzh/projects/agents_final_tech"
EXP="$PROJ/docs/experiments"
LOG=/tmp/supervisor_qoder.log
{ echo; echo "===== supervisor_qoder start $(date '+%m-%d %T') pid=$$ ====="; } > "$LOG"
log() { echo "[$(date '+%m-%d %T')] $*" | tee -a "$LOG"; }
has() { ls $1 >/dev/null 2>&1; }
tmux_has() { tmux has-session -t "$1" 2>/dev/null; }
wait_for() {
  local pat="$1" to="$2" tm="${3:-}" dl=$(( SECONDS + to ))
  while [ $SECONDS -lt $dl ]; do
    has "$pat" && return 0
    if [ -n "$tm" ] && ! tmux_has "$tm"; then sleep 15; has "$pat" && return 0; return 1; fi
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

log "wait C (header_mapping_llm)"
wait_for "$EXP/*_m1_header_mapping_llm.md" 5400 codex-m1-llmap || log "C timeout/crash (continue; qoder recon independent)"

log "settle B (ocr_fallback): marker or ocr tmux gone or 6000s"
B_OK=0
dl=$(( SECONDS + 6000 ))
while [ $SECONDS -lt $dl ]; do
  if has "$EXP/*_m1_ocr_fallback.md"; then B_OK=1; break; fi
  if ! tmux_has codex-m1-ocr; then sleep 15; has "$EXP/*_m1_ocr_fallback.md" && B_OK=1; break; fi
  sleep 20
done
log "B_OK=$B_OK"

D_DONE=0; has "$EXP/*_m1_multiagent_delegation.md" && D_DONE=1
if [ $D_DONE = 1 ]; then
  log "D already done"
elif tmux_has codex-m1-multi; then
  log "D running; v2 waits only"
else
  if [ $B_OK = 1 ]; then
    log "B ok, D not running: give old supervisor 120s to start D, else v2 backstops"
    for i in $(seq 1 8); do
      sleep 15
      tmux_has codex-m1-multi && break
      has "$EXP/*_m1_multiagent_delegation.md" && break
    done
    if ! tmux_has codex-m1-multi && ! has "$EXP/*_m1_multiagent_delegation.md"; then
      log "old supervisor did not start D -> v2 backstops D"
      launch codex-m1-multi scripts/loop_m1_multiagent_delegation.md
    fi
  else
    log "B failed and D not started -> v2 launches D"
    launch codex-m1-multi scripts/loop_m1_multiagent_delegation.md
  fi
fi

log "wait D"
wait_for "$EXP/*_m1_multiagent_delegation.md" 5400 codex-m1-multi || log "D timeout/crash (continue to qoder recon anyway)"

log "launch Qoder recon"
launch codex-qoder-recon /tmp/loop_qoder_recon.md
wait_for "$EXP/*_qoder_recon.md" 3600 codex-qoder-recon || log "qoder recon timeout/crash"
log "===== supervisor_qoder finished $(date '+%m-%d %T') ====="
