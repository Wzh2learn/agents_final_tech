#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
target="$repo_root/scripts/graph/hooks/summary_recompute_guard.py"

if [[ "${1:-}" != "check" ]]; then
  printf 'summary_guard_check_adapter supports only the existing check entrypoint\n' >&2
  exit 64
fi
shift

for argument in "$@"; do
  if [[ "$argument" == "--staged" ]]; then
    printf 'summary_guard_check_adapter forbids --staged because T4 may not alter the git index\n' >&2
    exit 64
  fi
done

exec python3 "$target" check "$@"
