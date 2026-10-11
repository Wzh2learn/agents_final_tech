#!/usr/bin/env bash
# Detached, observable launcher for one-shot Loop A / Loop C tasks on GB10.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-}"
RUN_ROOT="${LOOP_RUN_ROOT:-}"
CODEX_BIN="${CODEX_BIN:-$HOME/.npm-global/bin/codex}"
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.npm-global/bin/claude}"
source "$SCRIPT_DIR/agent_env.sh"
PROJECT_DIR="${PROJECT_DIR:-$AGENT_PROJECT_ROOT}"
RUN_ROOT="${RUN_ROOT:-$AGENT_RUNTIME_ROOT}"

usage() {
  cat >&2 <<'EOF'
Usage:
  loop_ac_launcher.sh preflight [--smoke]
  loop_ac_launcher.sh start <a|c> <task-id> <prompt-file> [timeout-seconds]
  loop_ac_launcher.sh status <task-id> [a|c]
  loop_ac_launcher.sh logs <task-id> <a|c> [lines]
  loop_ac_launcher.sh stop <task-id> <a|c>

The launcher never prints credentials. It runs commands in detached tmux,
uses an outer timeout, and writes status JSON under LOOP_RUN_ROOT.
EOF
}

die() { echo "ERROR: $*" >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }
valid_id() { [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$ ]]; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

write_status() {
  local file="$1" status="$2" task="$3" role="$4" rc="${5:-}" note="${6:-}"
  printf '{"task_id":"%s","role":"%s","status":"%s","rc":"%s","updated_utc":"%s","note":"%s"}\n' \
    "$task" "$role" "$status" "$rc" "$(now)" "$note" > "$file"
}

preflight() {
  local smoke="${1:-}"
  need bash
  need tmux
  need timeout
  [[ -x "$CODEX_BIN" ]] || die "codex binary not executable: $CODEX_BIN"
  [[ -x "$CLAUDE_BIN" ]] || die "claude binary not executable: $CLAUDE_BIN"
  agent_env_validate || die "agent runtime configuration is incomplete"
  [[ -f "$HOME/.codex/loopa-exec.config.toml" ]] || die "missing Loop A profile"
  
  
  agent_env_load_codex_api || die "Codex API environment is incomplete"
  echo "preflight: binaries/config present; credentials not read"
  if [[ "$smoke" == "--smoke" ]]; then
    local root="$RUN_ROOT/preflight-$(date +%Y%m%d-%H%M%S)"
    local codex_rc=0 claude_rc=0
    mkdir -p "$root"
    set +e
    printf '%s\n' 'Reply exactly OK' | timeout --signal=TERM --kill-after=15s 180 \
      "$CODEX_BIN" exec --ephemeral --skip-git-repo-check -C /tmp \
      -p loopa-exec --json > "$root/codex.jsonl" 2> "$root/codex.err"
    codex_rc=$?
    timeout --signal=TERM --kill-after=15s 180 \
      "$CLAUDE_BIN" -p 'Reply exactly OK' --no-session-persistence \
      --output-format text > "$root/claude.txt" 2> "$root/claude.err"
    claude_rc=$?
    set -e
    echo "preflight smoke artifacts=$root codex_rc=$codex_rc claude_rc=$claude_rc"
    if [[ $codex_rc -eq 0 ]] && grep -q '"type":"turn.completed"' "$root/codex.jsonl" \
      && [[ $claude_rc -eq 0 ]] && grep -q '^OK$' "$root/claude.txt"; then
      echo "preflight smoke: PASS"
      return 0
    fi
    echo "preflight smoke: FAIL; inspect $root/codex.err and $root/claude.err" >&2
    return 1
  fi
}

start_task() {
  local role="$1" task="$2" prompt_file="$3" timeout_s="${4:-}"
  valid_id "$task" || die "invalid task id"
  [[ "$role" == "a" || "$role" == "c" ]] || die "role must be a or c"
  [[ -f "$prompt_file" ]] || die "prompt file not found: $prompt_file"
  [[ -n "$timeout_s" ]] || timeout_s="$([[ "$role" == a ]] && echo 14400 || echo 7200)"
  [[ "$timeout_s" =~ ^[0-9]+$ ]] || die "timeout must be integer seconds"
  local run="$RUN_ROOT/$task"
  local session="loop-${role}-${task}"
  local log="$run/${role}.log"
  local status="$run/${role}.status.json"
  local runner="$run/${role}.run.sh"
  mkdir -p "$run"
  if tmux has-session -t "$session" 2>/dev/null; then
    die "session already running: $session"
  fi
  write_status "$status" queued "$task" "$role" "" "queued"
  if [[ "$role" == "a" ]]; then
    cat > "$runner" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$LOOP_PROJECT_DIR"
source "$HOME/.bashrc"
source "$LOOP_PROJECT_DIR/scripts/graph/agent_env.sh"; agent_env_load_codex_api
export PATH="$HOME/.npm-global/bin:$PATH"
printf '%s\n' "[loop-a] start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOOP_LOG"
set +e
rc=1
for attempt in 1 2; do
  attempt_log="$LOOP_LOG.attempt-$attempt"
  cat "$LOOP_PROMPT" | timeout --signal=TERM --kill-after=30s "$LOOP_TIMEOUT" \
    "$LOOP_CODEX_BIN" exec --ephemeral --dangerously-bypass-approvals-and-sandbox \
    -C "$LOOP_PROJECT_DIR" -p loopa-exec --json > "$attempt_log" 2>&1
  rc=$?
  cat "$attempt_log" >> "$LOOP_LOG"
  [[ $rc -eq 0 ]] && break
  if [[ $attempt -eq 1 ]] && grep -q '429 Too Many Requests' "$attempt_log"; then
    printf '%s\n' '[loop-a] bounded retry after HTTP 429' >> "$LOOP_LOG"
    sleep 20
    continue
  fi
  break
done
set -e
printf '{"task_id":"%s","role":"%s","status":"%s","rc":"%s","updated_utc":"%s","log":"%s"}\n' \
  "$LOOP_TASK" "a" "$([[ $rc -eq 0 ]] && echo done || echo failed)" "$rc" \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$LOOP_LOG" > "$LOOP_STATUS"
exit $rc
EOF
  else
    cat > "$runner" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$LOOP_PROJECT_DIR"
source "$HOME/.bashrc"
source "$LOOP_PROJECT_DIR/scripts/graph/agent_env.sh"
export PATH="$HOME/.npm-global/bin:$PATH"
printf '%s\n' "[loop-c] start $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOOP_LOG"
set +e
prompt=$(cat "$LOOP_PROMPT")
timeout --signal=TERM --kill-after=30s "$LOOP_TIMEOUT" \
  "$LOOP_CLAUDE_BIN" -p "$prompt" --no-session-persistence --output-format text \
  >> "$LOOP_LOG" 2>&1
rc=$?
set -e
printf '{"task_id":"%s","role":"%s","status":"%s","rc":"%s","updated_utc":"%s","log":"%s"}\n' \
  "$LOOP_TASK" "c" "$([[ $rc -eq 0 ]] && echo done || echo failed)" "$rc" \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$LOOP_LOG" > "$LOOP_STATUS"
exit $rc
EOF
  fi
  chmod 700 "$runner"
  write_status "$status" running "$task" "$role" "" "started"
  if [[ "$role" == "a" ]]; then
    if ! tmux new-session -d -s "$session" \
      "LOOP_PROJECT_DIR='$PROJECT_DIR' LOOP_CODEX_BIN='$CODEX_BIN' LOOP_TIMEOUT='$timeout_s' LOOP_TASK='$task' LOOP_PROMPT='$prompt_file' LOOP_LOG='$log' LOOP_STATUS='$status' bash '$runner'"; then
      write_status "$status" failed "$task" "$role" "125" "tmux-launch-failed"
      die "tmux launch failed: $session"
    fi
  else
    if ! tmux new-session -d -s "$session" \
      "LOOP_PROJECT_DIR='$PROJECT_DIR' LOOP_CLAUDE_BIN='$CLAUDE_BIN' LOOP_TIMEOUT='$timeout_s' LOOP_TASK='$task' LOOP_PROMPT='$prompt_file' LOOP_LOG='$log' LOOP_STATUS='$status' bash '$runner'"; then
      write_status "$status" failed "$task" "$role" "125" "tmux-launch-failed"
      die "tmux launch failed: $session"
    fi
  fi
  echo "started session=$session run=$run timeout=${timeout_s}s"
}
show_status() {
  local task="$1" role="${2:-}"
  valid_id "$task" || die "invalid task id"
  if [[ -n "$role" ]]; then
    [[ "$role" == "a" || "$role" == "c" ]] || die "role must be a or c"
    cat "$RUN_ROOT/$task/$role.status.json" 2>/dev/null || echo '{"status":"missing"}'
    tmux has-session -t "loop-${role}-${task}" 2>/dev/null && echo '{"tmux":"running"}' || echo '{"tmux":"stopped"}'
  else
    show_status "$task" a
    show_status "$task" c
  fi
}

show_logs() {
  local task="$1" role="$2" lines="${3:-40}"
  valid_id "$task" || die "invalid task id"
  [[ "$role" == "a" || "$role" == "c" ]] || die "role must be a or c"
  tail -n "$lines" "$RUN_ROOT/$task/$role.log" 2>/dev/null || echo "no log"
}

stop_task() {
  local task="$1" role="$2"
  valid_id "$task" || die "invalid task id"
  [[ "$role" == "a" || "$role" == "c" ]] || die "role must be a or c"
  if tmux has-session -t "loop-${role}-${task}" 2>/dev/null; then
    tmux kill-session -t "loop-${role}-${task}"
    write_status "$RUN_ROOT/$task/$role.status.json" stopped "$task" "$role" "" "stopped-by-user"
    echo "stopped loop-${role}-${task}"
  else
    echo "not running"
  fi
}

case "${1:-}" in
  preflight) preflight "${2:-}" ;;
  start) [[ $# -ge 4 ]] || { usage; exit 2; }; start_task "$2" "$3" "$4" "${5:-}" ;;
  status) [[ $# -ge 2 ]] || { usage; exit 2; }; show_status "$2" "${3:-}" ;;
  logs) [[ $# -ge 3 ]] || { usage; exit 2; }; show_logs "$2" "$3" "${4:-40}" ;;
  stop) [[ $# -eq 3 ]] || { usage; exit 2; }; stop_task "$2" "$3" ;;
  *) usage; exit 2 ;;
esac
