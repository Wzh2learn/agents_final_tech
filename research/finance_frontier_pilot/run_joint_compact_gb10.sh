#!/usr/bin/env bash
# Serve a verified joint checkpoint on the established, single research GPU lease.
set -euo pipefail
umask 077

study=$(cd "${1:?study directory}" && pwd -P)
panel=$(cd "${2:?public and reference panel directory}" && pwd -P)
label=${3:?new run label}
shift 3
[[ $study == "$HOME/wzh/research_evidence/"* && $label =~ ^[a-z][a-z0-9_]+$ ]]
repo="$HOME/wzh/projects/agents_final_tech"
driver="$repo/research/finance_frontier_pilot"
python="$repo/venv/bin/python"
train="$study/training/run"
adapter="$train/adapter_3000"
model="$HOME/wzh/models/hf/ODA-Fin-RL-8B-948c22ea"
metric="$HOME/wzh/research_evidence/agent_learning_20261030/tools/tatqa/870accc41953dcde885aabeb963d94aabdc0fbc3"
out="$study/serving/$label"
image=sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f
alias=oda-compact-joint
base=http://127.0.0.1:18157/v1
export PYTHONPATH="$driver:$repo:$repo/src" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
test -s "$panel/public.jsonl"
test -s "$panel/references.jsonl"
test -s "$metric/tatqa_metric.py"
for ((attempt=0; attempt<15; attempt++)); do
    [[ ! -s $study/training/supervisor/exit ]] || break
    sleep 1
done
grep -Fxq 0 "$study/training/supervisor/exit"
grep -Fxq ready "$train/restore_teacher/status"
"$python" -B - "$train" "$adapter" "$model" <<'PY'
from pathlib import Path
import json
import sys
from benchmark_actions import digest_file

train, adapter, model = map(Path, sys.argv[1:])
result = json.loads((train / 'RESULT.json').read_text())
plan = json.loads((train / 'PLAN.json').read_text())
matches = [item for item in result['adapters'] if item['examples'] == 3000]
if (result['status'] != 'TRAINED_ODA_JOINT_COMPACT' or result['examples'] != 3000
        or result['plan_sha256'] != digest_file(train / 'PLAN.json') or len(matches) != 1
        or Path(matches[0]['directory']).resolve() != adapter.resolve()
        or Path(plan['model_path']).resolve() != model.resolve()):
    raise ValueError('Expected the finalized 3,000-example joint artifact')
artifacts = matches[0]['artifacts']
if set(artifacts) != {'adapter_config.json', 'adapter_model.safetensors'} or any(
        digest_file(adapter / name) != checksum for name, checksum in artifacts.items()):
    raise ValueError('Adapter files differ from the training receipt')
PY

lock="$HOME/wzh/.gpu_lock"
guard=$(lslocks -rn -o PID,PATH | awk -v lock="$lock" '$2==lock{print $1}')
[[ $guard =~ ^[1-9][0-9]+$ && $(readlink -f "/proc/$guard/cwd") = "$repo" ]]
mapfile -d '' -t guard_command <"/proc/$guard/cmdline"
[[ ${#guard_command[@]} == 4 && ${guard_command[0]} = "$python" && ${guard_command[1]} = -u && ${guard_command[2]} = -B ]]
restore_script=$(realpath -- "${guard_command[3]}")
[[ $restore_script == "$HOME/wzh/research_evidence/"*/restore_teacher/restore.py && -s $restore_script ]]
teacher=$(docker inspect --format '{{.Id}}' research-qwen27b-current)
metrics=$(curl -fsS --max-time 8 http://127.0.0.1:8006/metrics)
awk '/^vllm:num_requests_(running|waiting)\{/{n++; if ($NF!=0) live++} END {exit (n<2 || live)}' <<<"$metrics"
docker image inspect "$image" >/dev/null
mkdir -p "$study/serving"
mkdir "$out"
mkdir "$out/restore_teacher"
cp -- "$restore_script" "$out/restore_teacher/restore.py"
cmp -s "$restore_script" "$out/restore_teacher/restore.py"
cd "$repo"

cid=
compact_name="finance-compact-joint-$$"
launched=
watcher=
cleanup() {
    rc=$?
    trap - EXIT INT TERM
    set +e
    if [[ -n $watcher ]]; then
        kill "$watcher" 2>/dev/null
        wait "$watcher" 2>/dev/null
    fi
    if [[ -n $launched ]]; then
        docker logs "${cid:-$compact_name}" >"$out/vllm.log" 2>&1
        "$python" -B - "${cid:-$compact_name}" "$out/stop.json" <<'PY'
from pathlib import Path
import sys
from scripts.graph.research_gpu_guard import stop_owned
stop_owned(sys.argv[1], {'status': 'STOPPED_COMPACT'}, Path(sys.argv[2]), 5)
PY
    fi
    flock -u 9
    exec 9>&-
    if [[ $(docker inspect --format '{{.State.Running}}' research-qwen27b-current 2>/dev/null) != true ]]; then
        if kill -0 "$guard" 2>/dev/null && [[ -r /proc/$guard/cmdline ]] &&
                tr '\0' '\n' <"/proc/$guard/cmdline" | grep -Fxq "$restore_script"; then
            echo 'Original research guard still exists; restoration requires reconciliation.' >&2
            exit 1
        fi
        nohup setsid "$python" -u -B "$out/restore_teacher/restore.py" \
            </dev/null >"$out/restore.log" 2>&1 &
        printf '%s\n' "$!" >"$out/restore.pid"
    fi
    for ((attempt=0; attempt<120; attempt++)); do
        if ready=$(curl -fsS --max-time 3 http://127.0.0.1:8006/v1/models 2>/dev/null) &&
                [[ $ready == *qwen38-27b-fp8* ]] &&
                lslocks -rn -o PID,PATH | awk -v lock="$lock" '$2==lock{held=1} END{exit !held}'; then
            printf 'ready\n' >"$out/restore.status"
            exit "$rc"
        fi
        sleep 5
    done
    printf 'not-ready\n' >"$out/restore.status"
    exit 1
}
exec 9<>"$lock"
trap cleanup EXIT
trap 'exit 130' INT TERM
kill -TERM "$guard"
flock -w 100 9
[[ $(docker inspect --format '{{.State.Running}}' "$teacher" 2>/dev/null || true) != true ]]
awk '/^MemAvailable:/{if ($2<50331648) exit 1; print}' /proc/meminfo

launched=1
cid=$(docker run -d --name "$compact_name" --pull never --network host --ipc host \
    --device nvidia.com/gpu=all -v "$model:/models/oda:ro" -v "$adapter:/adapters/joint:ro" \
    -v "$HOME/wzh/vllm_cache:/root/.cache/vllm" -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
    "$image" vllm serve /models/oda --host 127.0.0.1 --port 18157 --served-model-name oda-fin-rl-8b \
    --dtype bfloat16 --gpu-memory-utilization 0.23 --kv-cache-memory 5368709120 --max-model-len 16384 \
    --max-num-seqs 12 --max-num-batched-tokens 12288 --enable-prefix-caching --enforce-eager --reasoning-parser qwen3 \
    --enable-lora --max-lora-rank 8 --lora-dtype bfloat16 --max-loras 1 --max-cpu-loras 1 \
    --lora-modules '{"name":"oda-compact-joint","path":"/adapters/joint","base_model_name":"oda-fin-rl-8b"}')
printf '%s\n' "$cid" >"$out/container.id"
(
    while sleep 5; do
        if ! awk '/^MemAvailable:/{exit ($2<33554432)}' /proc/meminfo; then
            echo 'Compact serving stopped below the 32 GiB RAM reserve.' >&2
            docker stop --time 10 "$cid" >/dev/null
            exit 1
        fi
    done
) &
watcher=$!

"$python" -B - "$cid" "$adapter" "$train" "$out" "$base" "$alias" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
from benchmark_actions import digest_file, freeze
from run_pilot import wait_service

container, adapter, train, out, base, alias = sys.argv[1:]
template = '\n'.join('{{json .' + field + '}}' for field in ('Image', 'Config.Cmd', 'Mounts'))
image, argv, mounts = map(json.loads, subprocess.check_output(
    ['docker', 'inspect', '--format', template, container], text=True).splitlines())
freeze(Path(out) / 'serving_profile.json', {
    'model': alias, 'image': image, 'argv': argv,
    'mounts': [{k: entry[k] for k in ('Source', 'Destination', 'RW')}
               for entry in sorted(mounts, key=lambda entry: entry['Destination'])],
    'adapter_files': {name: digest_file(Path(adapter) / name)
                      for name in ('adapter_config.json', 'adapter_model.safetensors')},
    'training_result_sha256': digest_file(Path(train) / 'RESULT.json'),
})
wait_service(base, alias, 360)
PY
"$python" -B -u "$driver/compact_consensus.py" --panel "$panel" --output "$out/measurements" \
    --base "$base" --model "$alias" --serving-profile "$out/serving_profile.json" \
    --metric-dir "$metric" --measure-exclusive-engine "$@" >"$out/eval.log" 2>&1
