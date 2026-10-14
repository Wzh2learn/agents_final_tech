#!/usr/bin/env bash
set -euo pipefail

run_root="$(cd "$(dirname "$0")/.." && pwd)"
repo_root="$(git rev-parse --show-toplevel)"
out_dir="$run_root/scratch/tool_outputs"
events="$run_root/events.jsonl"
mkdir -p "$out_dir"
: > "$events"

emit_event() {
  local phase="$1" event_id="$2" adapter="$3" case_id="$4" log_path="$5" pass="$6" rc="${7:-}"
  python3 - "$events" "$phase" "$event_id" "$adapter" "$case_id" "$log_path" "$pass" "$rc" <<'PY'
import json, sys
from datetime import datetime, timezone
path, phase, event_id, adapter, case_id, log_path, replay_pass, rc = sys.argv[1:]
record = {
    "event_id": event_id,
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "phase": phase,
    "task_id": "T4",
    "run_id": "20261014T184810Z_c9dcfe0e",
    "adapter": adapter,
    "case_id": case_id,
    "replay_pass": int(replay_pass),
    "log_path": log_path,
}
if rc != "":
    record["exit_code"] = int(rc)
with open(path, "a", encoding="utf-8") as stream:
    stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

run_logged() {
  local replay_pass="$1" case_id="$2" kind="$3" adapter="$4"
  shift 4
  local stamp uuid nonce log_path log_absolute event_id rc
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  uuid="$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')"
  nonce="$$"
  log_path="scratch/tool_outputs/${stamp}_${uuid}_${nonce}_pass${replay_pass}_${case_id}_${kind}.log"
  log_absolute="$run_root/$log_path"
  event_id="${case_id}_${kind}_pass${replay_pass}"
  emit_event "request" "$event_id" "$adapter" "$case_id" "$log_path" "$replay_pass"
  {
    printf 'command=%q' "$run_root/$adapter"
    local argument
    for argument in "$@"; do printf ' %q' "$argument"; done
    printf '\n'
    printf 'observed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%NZ)"
    set +e
    "$run_root/$adapter" "$@"
    rc=$?
    set -e
    printf 'adapter_exit_code=%s\n' "$rc"
  } > "$log_absolute" 2>&1
  emit_event "response" "$event_id" "$adapter" "$case_id" "$log_path" "$replay_pass" "$rc"
  printf '%s rc=%s log=%s\n' "$case_id" "$rc" "$log_path"
}

for replay_pass in 1 2; do
  run_logged "$replay_pass" T1-INC-01 dispatch adapters/dispatch_precheck_adapter.sh \
    --watcher "$run_root/fixtures/dispatch/watcher.sh" --tick-marker "$run_root/fixtures/dispatch/missing_tick.json"
  run_logged "$replay_pass" T1-INC-02 dispatch adapters/dispatch_precheck_adapter.sh \
    --watcher "$run_root/fixtures/dispatch/watcher.sh" --tick-marker "$run_root/fixtures/dispatch/tick_prose.txt"
  run_logged "$replay_pass" T1-INC-07 summary adapters/summary_guard_check_adapter.sh \
    check "$run_root/fixtures/summary/offline_proxy_match.md"
  run_logged "$replay_pass" T1-INC-09 summary adapters/summary_guard_check_adapter.sh \
    check "$run_root/fixtures/summary/stale_manifest_match.md"
  run_logged "$replay_pass" T1-INC-09 frozen adapters/frozen_hash_check_adapter.sh \
    "$run_root/fixtures/frozen/stale.md5"
  run_logged "$replay_pass" T1-INC-11 dispatch adapters/dispatch_precheck_adapter.sh \
    --watcher "$run_root/fixtures/dispatch/watcher.sh" --tick-marker "$run_root/fixtures/dispatch/missing_tick.json"
  run_logged "$replay_pass" T1-INC-12 summary_derive adapters/summary_guard_derive_check_adapter.sh \
    "$run_root/fixtures/summary/effect_match.md"
  run_logged "$replay_pass" T1-INC-13 summary_derive adapters/summary_guard_derive_check_adapter.sh \
    "$run_root/fixtures/summary/effect_match.md"
  run_logged "$replay_pass" T1-INC-14 summary adapters/summary_guard_check_adapter.sh \
    check "$run_root/fixtures/summary/usage_no_block.md"
  run_logged "$replay_pass" T1-CTRL-01 summary adapters/summary_guard_check_adapter.sh \
    check "$run_root/fixtures/summary/negative_result_match.md"
  run_logged "$replay_pass" T1-CTRL-02 summary adapters/summary_guard_check_adapter.sh \
    check "$run_root/fixtures/summary/measurement_object_match.md"
done

python3 - "$events" "$run_root" <<'PY'
import json, pathlib, sys
events_path, run_root = map(pathlib.Path, sys.argv[1:])
records = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
requests = [record for record in records if record["phase"] == "request"]
responses = [record for record in records if record["phase"] == "response"]
assert len(requests) == 22, len(requests)
assert len(responses) == 22, len(responses)
for record in responses:
    assert (run_root / record["log_path"]).is_file(), record["log_path"]
print("replay_events=22 request=22 response=22")
PY
