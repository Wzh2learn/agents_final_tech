#!/usr/bin/env bash
# PreToolUse guard for Bash commands.
# Blocks irreversible git operations: force push and commit --amend.
# The hook receives Claude-style JSON on stdin and exits 2 to block.
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
  echo "[git-commit-guard] guard degraded: python3/python unavailable; passing through" >&2
  exit 0
fi

CMD=$(printf '%s' "$INPUT" | parse_command || true)
if [ -n "$INPUT" ] && [ -z "$CMD" ]; then
  echo "[git-commit-guard] guard degraded: JSON parse returned empty; passing through" >&2
  exit 0
fi

SAFE=$(printf '%s' "$CMD" | tr '\r\n' '  ' | cut -c1-240)

if printf '%s' "$CMD" | grep -qE '(^|[;&|]|[[:space:]])git[[:space:]]+((-C|--git-dir|--work-tree)[[:space:]]+[^[:space:]]+[[:space:]]+)*push\b[^;&|\n]*([[:space:]](--force|--force-with-lease|-f)([[:space:]]|$))'; then
  echo "[git-commit-guard] block: force push is not authorized" >&2
  echo "Command: $SAFE" >&2
  echo "Use a normal push or obtain explicit authorization for a force operation." >&2
  exit 2
fi

if printf '%s' "$CMD" | grep -qE '(^|[;&|]|[[:space:]])git[[:space:]]+((-C|--git-dir|--work-tree)[[:space:]]+[^[:space:]]+[[:space:]]+)*commit\b[^;&|\n]*([[:space:]]--amend)([[:space:]]|$)'; then
  echo "[git-commit-guard] block: git commit --amend is not authorized" >&2
  echo "Command: $SAFE" >&2
  echo "Create a new commit or obtain explicit authorization for amend." >&2
  exit 2
fi

exit 0
