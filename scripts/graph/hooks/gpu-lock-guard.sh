#!/usr/bin/env bash
# PreToolUse guard for GPU-heavy commands.
# Training-like commands require a verifiable free lock; unknown lock state blocks.
set -u

INPUT=$(cat)

parse_command() {
  local py
  for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
      "$py" -c 'import json, sys; d=json.load(sys.stdin); print(d.get("tool_input", {}).get("command", ""))' 2>/dev/null
      return 0
    fi
  done
  return 1
}

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "[gpu-lock-guard] block: parser unavailable; GPU-heavy command state cannot be verified" >&2
  exit 2
fi

CMD=$(printf '%s' "$INPUT" | parse_command || true)
if [ -n "$INPUT" ] && [ -z "$CMD" ]; then
  echo "[gpu-lock-guard] block: command JSON could not be parsed" >&2
  exit 2
fi

CMD_SAFE=$(printf '%s' "$CMD" | tr '\r\n' '  ' | cut -c1-200)

strip_prefix() {
  local s n
  s=$(printf '%s' "$1" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
  while :; do
    n=$(printf '%s' "$s" | sed -E 's/^[[:space:]]*(nohup[[:space:]]+|[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)//')
    [ "$n" = "$s" ] && break
    s="$n"
  done
  printf '%s\n' "$s"
}

CMD_JUDGE=$(printf '%s\n' "$CMD" | awk '
  skip { if ($0 == term) skip = 0; next }
  {
    if (match($0, /<<-?[ \t]*["'"'"']?[A-Za-z_][A-Za-z0-9_]*/)) {
      t = substr($0, RSTART, RLENGTH)
      sub(/^<<-?[ \t]*/, "", t)
      gsub(/["'"'"']/, "", t)
      term = t
      skip = 1
    }
    print
  }')

READ_ONLY='^(cat|echo|printf|sed|tee|cp|mv|ln|mkdir|touch|chmod|diff|wc|grep|rg|find|ls|head|tail|jq|sleep|ps|nvidia-smi|date|stat|du|df|file|top|free|git)([[:space:]]|$)'
TRAIN_PATTERN='(^|[[:space:]/])(torchrun|deepspeed)([[:space:]]|$)|accelerate[[:space:]]+launch|(^|[[:space:]/])(train|finetune|sft|dpo)[A-Za-z0-9_.-]*\.(py|sh)([[:space:]]|$)|qlora|checkpoint-filtered'

IS_TRAIN=0
while IFS= read -r SEG; do
  SEG=$(strip_prefix "$SEG")
  [ -z "$SEG" ] && continue
  printf '%s' "$SEG" | grep -qE "$READ_ONLY" && continue
  if printf '%s' "$SEG" | grep -qE "$TRAIN_PATTERN"; then
    IS_TRAIN=1
    break
  fi
done < <(printf '%s\n' "$CMD_JUDGE" | awk '{gsub(/\|\||&&|;|\|/, "\n"); print}')

if [ "$IS_TRAIN" -eq 0 ]; then
  exit 0
fi

if ! command -v flock >/dev/null 2>&1; then
  echo "[gpu-lock-guard] block: flock unavailable; GPU lock cannot be verified" >&2
  echo "Command: $CMD_SAFE" >&2
  exit 2
fi

GPU_LOCK_FILE="${GPU_LOCK_FILE:-$HOME/wzh/.gpu_lock}"
if [ -d "$GPU_LOCK_FILE" ] || { [ -e "$GPU_LOCK_FILE" ] && [ ! -f "$GPU_LOCK_FILE" ]; }; then
  echo "[gpu-lock-guard] block: GPU lock path is not a regular file" >&2
  echo "Command: $CMD_SAFE" >&2
  echo "Lock: $GPU_LOCK_FILE" >&2
  exit 2
fi
if ! flock -n "$GPU_LOCK_FILE" true 2>/dev/null; then
  echo "[gpu-lock-guard] block: GPU lock is held or cannot be verified" >&2
  echo "Command: $CMD_SAFE" >&2
  echo "Lock: $GPU_LOCK_FILE" >&2
  echo "Wait for release or provide a valid GPU_LOCK_FILE; do not bypass this guard." >&2
  exit 2
fi

exit 0
