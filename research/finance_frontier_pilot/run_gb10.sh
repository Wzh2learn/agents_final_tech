#!/usr/bin/env bash
# Rotate the existing research-only 27B service and the ODA BF16 service on one GPU lease.
set -euo pipefail

root=$(cd "$1" && pwd)
repo=${PILOT_REPO:-$HOME/wzh/projects/agents_final_tech}
private=$HOME/wzh/research_evidence/agent_learning_20261030
metric_dir=$private/tools/tatqa/870accc41953dcde885aabeb963d94aabdc0fbc3
python=$HOME/wzh/venvs/docling_probe/bin/python
guard_pid=$2
old_restore=$3
benchmark=${4:-}
work=$root
model_dir=$HOME/wzh/models/hf/ODA-Fin-RL-8B-948c22ea
image=sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f
args=(--root "$root" --metric-dir "$metric_dir"
      --rule-dir "$private/tatqa_correction_v1")
export PYTHONPATH="$repo/research/agent_frontier_portfolio_20261029:$repo"

cd "$root"
test -r panel/manifest.json
test -s smoke/teacher/call.json
"$python" -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["text"] and r["usage"] and not r["exit_code"]' smoke/teacher/call.json
[[ $(stat -c %s "$model_dir/model-00003-of-00004.safetensors") = 4999853856 ]]
[[ $(readlink -f "/proc/$guard_pid/cwd") = "$repo" ]]
tr '\0' '\n' <"/proc/$guard_pid/cmdline" | grep -Fxq "$old_restore"
if [[ -n $benchmark ]]; then
    work=$(cd "$benchmark" && pwd)
    [[ $work == "$HOME/wzh/research_evidence/finance_frontier_benchmark_"* ]]
    test -s "$work/panel/fit/public.jsonl"
    test -s "$work/panel/fit/references.jsonl"
    if [[ ! -s $root/summary.json || ! -s $root/outcomes.json ]]; then
        echo 'Wait for the full teacher probe to finish before launching the benchmark.' >&2
        exit 1
    fi
    "$python" - "$root/outcomes.json" <<'PY'
import json, sys
with open(sys.argv[1]) as source:
    rows = json.load(source)
assert len(rows) == 400 and sum('teacher' in row for row in rows) == 220
PY
fi
lslocks -rn -o PID,PATH | awk -v guard="$guard_pid" -v lock="$HOME/wzh/.gpu_lock" \
    '$1==guard && $2==lock {owner=1} END {exit !owner}'
old_container=$(docker inspect --format '{{.Id}}' research-qwen27b-current)
metrics=$(curl -fsS http://127.0.0.1:8006/metrics)
if ! awk '/^vllm:num_requests_(running|waiting)\{/{n++; if ($NF != 0) b++} END {exit (n<2 || b)}' <<<"$metrics"; then
    echo 'Wait for the current 27B requests to drain.' >&2
    exit 1
fi
mkdir -p "$work/restore_teacher"
if [[ ! -f "$work/restore_teacher/restore.py" ]]; then
    cp "$old_restore" "$work/restore_teacher/restore.py"
fi

cd "$work"
cid=
watcher=
stop_oda () {
    if [[ -n $watcher ]]; then
        kill "$watcher" 2>/dev/null || true
        wait "$watcher" 2>/dev/null || true
        watcher=
    fi
    if [[ -n $cid ]]; then
        docker logs "$cid" >"oda_service.$cid.log" 2>&1 || true
        if ! docker stop --time 15 "$cid" >/dev/null; then
            [[ $(docker inspect --format '{{.State.Running}}' "$cid" 2>/dev/null) = false ]] || return 1
        fi
        cid=
    fi
    flock -u 9
}
restore () {
    stop_oda || return 1
    if [[ $(docker inspect --format '{{.State.Running}}' research-qwen27b-current 2>/dev/null) == true ]]; then
        return 0
    fi
    if kill -0 "$guard_pid" 2>/dev/null && [[ -r /proc/$guard_pid/cmdline ]] &&
        tr '\0' '\n' <"/proc/$guard_pid/cmdline" | grep -Fxq "$old_restore"; then
        echo 'Previous 27B guard is still present. Check the guard before another restore.' >&2
        return 1
    fi
    (cd "$repo" && nohup setsid "$repo/venv/bin/python" -u -B "$work/restore_teacher/restore.py" \
        >"$work/restore_teacher/supervisor.log" 2>&1 9>&- </dev/null &)
}
exec 9<> "$HOME/wzh/.gpu_lock"
trap restore EXIT
trap 'exit 130' INT TERM
kill -TERM "$guard_pid"
flock -w 100 9
running=$(docker ps -q --no-trunc)
if grep -Fxq "$old_container" <<<"$running"; then
    echo 'Previous 27B container still running after acquiring lease.' >&2
    exit 1
fi
awk '/^MemAvailable:/{if ($2<50331648) exit 1; print}' /proc/meminfo
cid=$(docker run -d --name "finance-frontier-oda-v1-$$" --pull never --network host --ipc host \
    --device nvidia.com/gpu=all -v "$model_dir:/models/oda:ro" \
    -v "$HOME/wzh/vllm_cache:/root/.cache/vllm" -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
    "$image" vllm serve /models/oda --host 127.0.0.1 --port 18157 --served-model-name oda-fin-rl-8b \
    --dtype bfloat16 --gpu-memory-utilization 0.23 --kv-cache-memory 5368709120 --max-model-len 16384 \
    --max-num-seqs 12 --max-num-batched-tokens 12288 --enable-prefix-caching --enforce-eager \
    --reasoning-parser qwen3)
echo "$cid" >oda_container_id
(
    while sleep 5; do
        if ! awk '/^MemAvailable:/{exit ($2<33554432)}' /proc/meminfo; then
            echo 'ODA stopped below the 32 GiB RAM reserve.' >&2
            docker stop --time 10 "$cid" >/dev/null
            exit 1
        fi
    done
) &
watcher=$!
if [[ -n $benchmark ]]; then
    "$python" - "$cid" "$model_dir" <<'PY'
import json, subprocess, sys
from pathlib import Path

container = json.loads(subprocess.check_output(['docker', 'inspect', sys.argv[1]]))[0]
model = Path(sys.argv[2])
metadata = json.loads((model / 'DOWNLOAD_STATUS.json').read_text())
assert metadata['status'] == 'ready'
assert metadata['revision'] == '948c22ea48f9bf93e5747f4211657fcad9cb0295'
profile = {'model': 'oda-fin-rl-8b', 'checkpoint': metadata['revision'],
           'image': container['Image'], 'argv': container['Config']['Cmd'],
           'mounts': [{k: item[k] for k in ('Source', 'Destination', 'RW')} for item in container['Mounts']]}
target = Path('oda_serving_profile.json')
if target.exists():
    if json.loads(target.read_text()) != profile:
        raise ValueError('ODA serving profile differs from the frozen benchmark profile')
else:
    with target.open('x') as out:
        json.dump(profile, out, indent=2)
        out.write('\n')
PY
    PYTHONPATH="$repo/research/finance_frontier_pilot:$PYTHONPATH" "$python" -c \
        'from run_pilot import wait_service; wait_service("http://127.0.0.1:18157/v1", "oda-fin-rl-8b", 300)'
    "$python" -u "$repo/research/finance_frontier_pilot/benchmark_actions.py" \
        --panel "$work/panel/fit" --run-dir "$work" --namespace oda_fit_v1 \
        --base http://127.0.0.1:18157/v1 --model oda-fin-rl-8b \
        --checkpoint 948c22ea48f9bf93e5747f4211657fcad9cb0295 \
        --serving-profile "$work/oda_serving_profile.json" --metric-dir "$metric_dir" \
        --actions low free dsl_fallback contract_compile compiled_fallback mid high independent car_probe \
        --workers 8 --context 16384 --solve-output 4096 --verify-output 4096 --probe-output 4096 --temperature .6
    exit 0
fi
"$python" -u run_pilot.py "${args[@]}" --phase oda --smoke
"$python" -u run_pilot.py "${args[@]}" --phase oda
stop_oda
if [[ -r legacy_heads.py && ! -f legacy_heads.json ]]; then
    "$repo/venv/bin/python" -u -B legacy_heads.py --root "$root" >legacy_heads.log 2>&1 || \
        echo 'Legacy head replay failed. See legacy_heads.log.' >&2
fi
restore
trap - EXIT
"$python" -u run_pilot.py "${args[@]}" --phase teacher
