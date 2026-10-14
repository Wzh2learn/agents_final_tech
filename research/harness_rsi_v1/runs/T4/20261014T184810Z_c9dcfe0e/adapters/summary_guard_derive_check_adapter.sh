#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'usage: %s MATCHING_BASE_MD\n' "$0" >&2
  exit 64
fi

base_md="$1"
if [[ "$base_md" != /* ]]; then
  printf 'matching base path must be absolute\n' >&2
  exit 64
fi

repo_root="$(git rev-parse --show-toplevel)"
run_root="$(cd "$(dirname "$0")/.." && pwd)"
derive="$run_root/fixtures/summary/derive_case_mismatch.py"
target="$repo_root/scripts/graph/hooks/summary_recompute_guard.py"
derived="$(mktemp "${TMPDIR:-/tmp}/t4-v2-summary-mismatch.XXXXXX.md")"
trap 'rm -f -- "$derived"' EXIT

printf 'derived_md_path=%s\n' "$derived"
python3 "$derive" "$base_md" "$derived"
printf 'derived_md_sha256=%s\n' "$(sha256sum -- "$derived" | awk '{print $1}')"
printf 'guard_command=python3 %s check %s\n' "$target" "$derived"
set +e
python3 "$target" check "$derived"
rc=$?
set -e
printf 'guard_rc=%s\n' "$rc"
rm -f -- "$derived"
if [[ $rc -ne 1 ]]; then
  printf 'expected guard rc=1 for runtime-derived mismatch, observed rc=%s\n' "$rc" >&2
  exit 70
fi
printf 'derived_md_removed=true\n'
exit 0
