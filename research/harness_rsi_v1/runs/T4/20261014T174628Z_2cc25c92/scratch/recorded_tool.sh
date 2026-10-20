#!/usr/bin/env bash
set -uo pipefail

if [[ $# -lt 2 ]]; then
  printf 'usage: %s LABEL COMMAND [ARG ...]\n' "$0" >&2
  exit 64
fi

run_dir="$(cd "$(dirname "$0")/.." && pwd)"
scratch_dir="$run_dir/scratch"
output_dir="$scratch_dir/tool_outputs"
events_file="$run_dir/events.jsonl"
label="$1"
shift
request_id="$(date -u +%Y%m%dT%H%M%S.%NZ)_$$_${RANDOM}"
output_file="$output_dir/${request_id}_$(printf '%s' "$label" | tr -cs 'A-Za-z0-9_.-' '_').log"
started_at="$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)"

python3 - "$events_file" "$request_id" "$label" "$started_at" "$@" <<'PY'
import json
import sys

path, request_id, label, started_at, *argv = sys.argv[1:]
event = {
    "event": "tool_request",
    "request_id": request_id,
    "label": label,
    "argv": argv,
    "started_at": started_at,
    "write_scope": "run",
    "network": False,
}
with open(path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
PY

mkdir -p "$output_dir"
set +e
"$@" >"$output_file" 2>&1
exit_code=$?
set -e
finished_at="$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)"
output_sha256="$(sha256sum "$output_file" | awk '{print $1}')"
output_bytes="$(wc -c <"$output_file" | tr -d ' ')"

python3 - "$events_file" "$request_id" "$label" "$finished_at" "$exit_code" "$output_sha256" "$output_bytes" "$output_file" <<'PY'
import json
import sys

path, request_id, label, finished_at, exit_code, output_sha256, output_bytes, output_file = sys.argv[1:]
event = {
    "event": "tool_response",
    "request_id": request_id,
    "label": label,
    "finished_at": finished_at,
    "exit_code": int(exit_code),
    "output_sha256": output_sha256,
    "output_bytes": int(output_bytes),
    "output_file": output_file,
}
with open(path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
PY

cat "$output_file"
exit "$exit_code"
