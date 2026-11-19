#!/usr/bin/env bash
# Rotate the existing research-only 27B service and the ODA BF16 service on one GPU lease.
set -euo pipefail

root=$(cd "$1" && pwd)
repo=${PILOT_REPO:-$HOME/wzh/projects/agents_final_tech}
private=$HOME/wzh/research_evidence/agent_learning_20261030
python=$HOME/wzh/venvs/docling_probe/bin/python
guard_pid=$2
old_restore=$3
model_dir=$HOME/wzh/models/hf/ODA-Fin-RL-8B-948c22ea
image=734134467dc5
args=(--root "$root" --metric-dir "$private/tools/tatqa/870accc41953dcde885aabeb963d94aabdc0fbc3"
      --rule-dir "$private/tatqa_correction_v1")
export PYTHONPATH="$repo/research/agent_frontier_portfolio_20261029:$repo"

cd "$root"
test -r panel/manifest.json
test -s smoke/teacher/call.json
"$python" -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["text"] and r["usage"] and not r["exit_code"]' smoke/teacher/call.json
[[ $(stat -c %s "$model_dir/model-00003-of-00004.safetensors") = 4999853856 ]]
[[ $(readlink -f "/proc/$guard_pid/cwd") = "$repo" ]]
tr '\0' '\n' <"/proc/$guard_pid/cmdline" | grep -Fxq "$old_restore"
metrics=$(curl -fsS http://127.0.0.1:8006/metrics)
if ! awk '/^vllm:num_requests_(running|waiting)\{/{n++; if ($NF != 0) b++} END {exit (n<2 || b)}' <<<"$metrics"; then
    echo 'Wait for the current 27B requests to drain.' >&2
    exit 1
fi
mkdir -p restore_teacher
if [[ ! -f restore_teacher/restore.py ]]; then
    cp "$old_restore" restore_teacher/restore.py
fi
kill -TERM "$guard_pid"

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
    (cd "$repo" && nohup setsid "$repo/venv/bin/python" -u -B "$root/restore_teacher/restore.py" \
        >"$root/restore_teacher/supervisor.log" 2>&1 </dev/null &)
}
exec 9<> "$HOME/wzh/.gpu_lock"
flock -w 100 9
trap restore EXIT
trap 'exit 130' INT TERM
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
