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
benchmark_split=${5:-fit}
compact_dataset=${6:-finqa}
case $benchmark_split in
    fit|calibration|eval|timing|short-calibration|compact-train|compact-calibration|compact-official-finqa|compact-depth-train|compact-depth-calibration|compact-depth-official-finqa) ;;
    *) echo 'Unknown financial benchmark mode.' >&2; exit 2 ;;
esac
if [[ $compact_dataset != finqa && ( $compact_dataset != tatqa ||
      ( $benchmark_split != compact-train && $benchmark_split != compact-calibration ) ) ]]; then
    echo 'Use FinQA or TAT-QA with compact training and calibration.' >&2
    exit 2
fi
work=$root
model_dir=$HOME/wzh/models/hf/ODA-Fin-RL-8B-948c22ea
image=sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f
args=(--root "$root" --metric-dir "$metric_dir"
      --rule-dir "$private/tatqa_correction_v1")
export PYTHONPATH="$repo/research/agent_frontier_portfolio_20261029:$repo"

car_collect () {
    local stage=$1 dataset=$2 drafts=$3 output=$4
    shift 4
    if [[ -e $output/outcomes.jsonl ]]; then
        test -s "$output/outcomes.jsonl"
        test -s "$output/run.json"
        return
    fi
    "$car_python" -u "$car_adapter" collect "$stage" --dataset "$dataset" --panel-root "$work/panel" \
        --drafts "$drafts" --output "$output" --base http://127.0.0.1:18157/v1 \
        --serving-profile "$work/oda_serving_profile.json" --metric-dir "$metric_dir" \
        --workers 4 --repair-output 4096 "$@"
}

car_run () {
    local dataset output fit_policy
    for dataset in finqa tatqa; do
        output="$car_root/$dataset"
        if [[ $benchmark_split == calibration ]]; then
            fit_policy="$output/fit_policy.json"
            car_collect fit "$dataset" "$car_fit_drafts" "$output/fit"
            "$car_python" -u "$car_adapter" fit --dataset "$dataset" --panel-root "$work/panel" \
                --collection "$output/fit" --output "$fit_policy"
            car_collect calibration "$dataset" "$work/oda_calibration_v1" "$output/calibration" --policy "$fit_policy"
            "$car_python" -u "$car_adapter" freeze --dataset "$dataset" --panel-root "$work/panel" \
                --collection "$output/calibration" --policy "$fit_policy" --output "$output/frozen_policy.json"
        else
            car_collect eval "$dataset" "$work/oda_eval_v1" "$output/eval" --policy "$output/frozen_policy.json"
        fi
    done
}

timing_run () {
    local dataset namespace
    local sources="$HOME/wzh/external_research_sources/finance_frontier"
    local driver="$repo/research/finance_frontier_pilot"
    export PYTHONPATH="$sources/budgetverify-tabfm-deps-v1:$driver:$PYTHONPATH"
    for dataset in finqa tatqa; do
        namespace="matched_live_policy_${dataset}_v2"
        printf '%s starting isolated matched official timing for %s\n' "$(date -Is)" "$dataset"
        "$repo/venv/bin/python" -B -u "$driver/live_policy_timing.py" \
            --benchmark "$work" --namespace "$namespace" --stage eval --dataset "$dataset" \
            --cases 18 --max-posts 180 --token-cap 2000000 --metric-dir "$metric_dir" \
            --compare-baselines --upstream "$sources/cascade-routing" --author-deps "$sources/cascade-router-deps" \
            --tabfm-checkpoint "$HOME/wzh/models/hf/tabfm-1.0.0-pytorch"
        "$repo/venv/bin/python" -B - "$work/$namespace/collection.json" <<'PY'
import json
from pathlib import Path
import sys

record = json.loads(Path(sys.argv[1]).read_bytes())
if record['complete_paired_questions'] != record['planned_questions'] or record['planned_questions'] != 18:
    raise SystemExit('Matched online timing stopped with an incomplete block')
PY
    done
}

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
    compact="$work/compact_program_development_v1"
    compact_arms=(canonical teacher)
    if [[ $compact_dataset == tatqa ]]; then
        compact="$compact/tatqa_aligned"
    elif [[ $benchmark_split == compact-depth-* ]]; then
        compact="$compact/finqa_depth_control"
        compact_arms=(balanced multi_only)
    fi
    run_car=0
    if [[ $benchmark_split == timing ]]; then
        test -n "${BUPT_API_KEY:-}"
        test "$(wc -l < "$work/oda_eval_v1/outcomes.jsonl")" -eq 1865
        for dataset in finqa tatqa; do
            test -s "$work/car_oda_4096_v1/$dataset/frozen_policy.json"
            test -s "$work/car_oda_4096_v1/$dataset/eval/outcomes.jsonl"
            test ! -e "$work/matched_live_policy_${dataset}_v2"
        done
    fi
    if [[ ( $benchmark_split == calibration || $benchmark_split == eval ) && -e $work/compare_car.enabled ]]; then
        if [[ ! -f $work/compare_car.enabled || -s $work/compare_car.enabled ]]; then
            echo 'CAR opt-in requires an empty compare_car.enabled file in the benchmark directory.' >&2
            exit 2
        fi
        run_car=1
        car_fit_drafts="$work/reconciled_fit_v1/oda_fit_v1"
        car_root="$work/car_oda_4096_v1"
        car_python="$repo/venv/bin/python"
        car_adapter="$repo/research/finance_frontier_pilot/car_adapter.py"
        "$car_python" -c 'import numpy, sklearn'
        if [[ $benchmark_split == calibration && ! -e $car_fit_drafts/outcomes.jsonl ]]; then
            test -s "$work/oda_fit_v1/outcomes.jsonl"
            test -s "$work/oda_nested_fit_finqa_v1/outcomes.jsonl"
            (cd "$work" && PYTHONPATH="$repo/research/finance_frontier_pilot:$PYTHONPATH" \
                "$car_python" -u "$work/oda_startup_repair_v1/publish_reconciled.py" "$work" --metric-dir "$metric_dir")
        fi
        test -s "$car_fit_drafts/run.json"
        test -s "$car_fit_drafts/outcomes.jsonl"
        if [[ $benchmark_split == eval ]]; then
            "$car_python" - "$car_root" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

for dataset in ('finqa', 'tatqa'):
    root = Path(sys.argv[1]) / dataset
    policy = json.loads((root / 'frozen_policy.json').read_text(encoding='utf-8'))
    if (policy['schema'], policy['stage'], policy['dataset'], policy['repair_output']) != (
        'finance-car-v1', 'frozen', dataset, 4096
    ):
        raise ValueError(f'{dataset}: a matching frozen CAR policy is required for evaluation')
    for stage in ('fit', 'calibration'):
        with (root / stage / 'outcomes.jsonl').open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        if policy[f'{stage}_outcomes_sha256'] != digest:
            raise ValueError(f'{dataset}: {stage} outcomes differ from the frozen CAR policy')
PY
        fi
    fi
    panel_split=$benchmark_split
    if [[ $benchmark_split == timing ]]; then
        panel_split=eval
    elif [[ $benchmark_split == short-calibration ]]; then
        panel_split=calibration
        test -s "$work/oda_calibration_v1/outcomes.jsonl"
        test ! -e "$work/oda_short_calibration_v1/outcomes.jsonl"
    elif [[ $benchmark_split == compact-train || $benchmark_split == compact-depth-train ]]; then
        panel_split=fit
        for arm in "${compact_arms[@]}"; do
            test -s "$compact/$arm/PLAN.json"
            test ! -e "$compact/$arm/LIVE.json"
        done
    elif [[ $benchmark_split == compact-calibration || $benchmark_split == compact-depth-calibration ||
            $benchmark_split == compact*-official-finqa ]]; then
        panel_split=calibration
        if [[ $benchmark_split == compact*-official-finqa ]]; then
            panel_split=eval
        fi
        for arm in "${compact_arms[@]}"; do
            test -s "$compact/$arm/RESULT.json"
            test -s "$compact/$arm/$arm/adapter_config.json"
            test -s "$compact/$arm/$arm/adapter_model.safetensors"
        done
    fi
    test -s "$work/panel/$panel_split/public.jsonl"
    test -s "$work/panel/$panel_split/references.jsonl"
    if [[ -e $work/oda_${benchmark_split}_v1/outcomes.jsonl && $run_car == 0 ]]; then
        echo 'Existing finalized outcomes are inputs to downstream baselines. Preserve them before any explicit repair.' >&2
        exit 1
    fi
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
elif [[ $benchmark_split == timing || $benchmark_split == short-calibration || $benchmark_split == compact-* ]]; then
    echo 'This mode requires the benchmark directory.' >&2
    exit 2
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
trainer=
stop_oda () {
    if [[ -n $watcher ]]; then
        kill "$watcher" 2>/dev/null || true
        wait "$watcher" 2>/dev/null || true
        watcher=
    fi
    if [[ -n $trainer ]]; then
        kill -TERM "$trainer" 2>/dev/null || true
        wait "$trainer" 2>/dev/null || true
        trainer=
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
    # Replace the background shell so it cannot hold an entry lock while its child serves.
    (
        cd "$repo"
        exec nohup setsid "$repo/venv/bin/python" -B -c '
import os
import sys

os.closerange(3, os.sysconf("SC_OPEN_MAX"))
os.execv(sys.executable, [sys.executable, "-u", "-B", sys.argv[1]])
' "$work/restore_teacher/restore.py" \
            >"$work/restore_teacher/supervisor.log" 2>&1 9>&- </dev/null
    ) &
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
if [[ $benchmark_split == compact-train || $benchmark_split == compact-depth-train ]]; then
    flock -u 9  # The trainer acquires this same lease before loading weights.
    for arm in "${compact_arms[@]}"; do
        "$repo/venv/bin/python" -B -u -c \
            'from finqa_learning import train, sha; from pathlib import Path; import sys; root=Path(sys.argv[1]); train(sha(root / "PLAN.json"), root)' \
            "$compact/$arm" &
        trainer=$!
        (
            while sleep 5; do
                if ! awk '/^MemAvailable:/{exit ($2<33554432)}' /proc/meminfo; then
                    echo 'Compact-program training stopped below the 32 GiB RAM reserve.' >&2
                    kill -TERM "$trainer" 2>/dev/null || true
                    exit 1
                fi
            done
        ) &
        watcher=$!
        wait "$trainer"
        trainer=
        kill "$watcher" 2>/dev/null || true
        wait "$watcher" 2>/dev/null || true
        watcher=
    done
    exit 0
fi
lora_mount=()
lora_options=()
if [[ $benchmark_split == compact-calibration || $benchmark_split == compact-depth-calibration ||
      $benchmark_split == compact*-official-finqa ]]; then
    lora_options=(--enable-lora --max-lora-rank 8 --lora-dtype bfloat16 --max-loras 1 --max-cpu-loras 2
                  --lora-modules)
    for arm in "${compact_arms[@]}"; do
        lora_mount+=(-v "$compact/$arm/$arm:/adapters/$arm:ro")
        lora_options+=("{\"name\":\"oda-compact-${arm//_/-}\",\"path\":\"/adapters/$arm\",\"base_model_name\":\"oda-fin-rl-8b\"}")
    done
fi
cid=$(docker run -d --name "finance-frontier-oda-v1-$$" --pull never --network host --ipc host \
    --device nvidia.com/gpu=all -v "$model_dir:/models/oda:ro" \
    -v "$HOME/wzh/vllm_cache:/root/.cache/vllm" "${lora_mount[@]}" -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
    "$image" vllm serve /models/oda --host 127.0.0.1 --port 18157 --served-model-name oda-fin-rl-8b \
    --dtype bfloat16 --gpu-memory-utilization 0.23 --kv-cache-memory 5368709120 --max-model-len 16384 \
    --max-num-seqs 12 --max-num-batched-tokens 12288 --enable-prefix-caching --enforce-eager \
    --reasoning-parser qwen3 "${lora_options[@]}")
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
if [[ $benchmark_split == compact-calibration || $benchmark_split == compact-depth-calibration ||
      $benchmark_split == compact*-official-finqa ]]; then
    stage=calibration
    dataset_args=()
    if [[ $compact_dataset == tatqa ]]; then
        dataset_args=(--dataset tatqa)
    fi
    if [[ $benchmark_split == compact-official-finqa ]]; then
        stage=official-finqa
    elif [[ $benchmark_split == compact-depth-official-finqa ]]; then
        stage=official-finqa-depth
    elif [[ $benchmark_split == compact-depth-calibration ]]; then
        stage=depth-calibration
    fi
    "$repo/venv/bin/python" -B -u "$repo/research/finance_frontier_pilot/compact_eval.py" \
        --benchmark "$work" --container "$cid" --metric-dir "$metric_dir" --stage "$stage" "${dataset_args[@]}"
    exit 0
fi
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
    def comparable(record):
        mounts = sorted(record['mounts'], key=lambda item: (item['Destination'], item['Source'], item['RW']))
        return {**record, 'mounts': mounts}

    # Docker may enumerate the same mounts in a different order on each inspect.
    if comparable(json.loads(target.read_text())) != comparable(profile):
        raise ValueError('ODA serving profile differs from the frozen benchmark profile')
else:
    with target.open('x') as out:
        json.dump(profile, out, indent=2)
        out.write('\n')
PY
    PYTHONPATH="$repo/research/finance_frontier_pilot:$PYTHONPATH" "$python" -c \
        'from run_pilot import wait_service; wait_service("http://127.0.0.1:18157/v1", "oda-fin-rl-8b", 300)'
    if [[ $benchmark_split == timing ]]; then
        timing_run
        exit 0
    fi
    if [[ $benchmark_split == short-calibration ]]; then
        "$python" -u "$repo/research/finance_frontier_pilot/benchmark_actions.py" \
            --panel "$work/panel/calibration" --run-dir "$work" --namespace oda_short_calibration_v1 \
            --base http://127.0.0.1:18157/v1 --model oda-fin-rl-8b \
            --checkpoint 948c22ea48f9bf93e5747f4211657fcad9cb0295 \
            --serving-profile "$work/oda_serving_profile.json" --metric-dir "$metric_dir" \
            --actions contract_compile --disable-thinking --workers 8 --context 16384 \
            --solve-output 4096 --verify-output 4096 --probe-output 4096 --temperature .6
        exit 0
    fi
    if [[ ! -e $work/oda_${benchmark_split}_v1/outcomes.jsonl ]]; then
        schedule=()
        if [[ $benchmark_split == eval ]]; then
            schedule=(--prioritize-direct)
        fi
        "$python" -u "$repo/research/finance_frontier_pilot/benchmark_actions.py" \
            --panel "$work/panel/$benchmark_split" --run-dir "$work" --namespace "oda_${benchmark_split}_v1" \
            --base http://127.0.0.1:18157/v1 --model oda-fin-rl-8b \
            --checkpoint 948c22ea48f9bf93e5747f4211657fcad9cb0295 \
            --serving-profile "$work/oda_serving_profile.json" --metric-dir "$metric_dir" \
            --actions low free dsl_fallback contract_compile compiled_fallback mid high independent car_probe \
            --workers 8 --context 16384 --solve-output 4096 --verify-output 4096 --probe-output 4096 --temperature .6 \
            "${schedule[@]}"
    fi
    if [[ $run_car == 1 ]]; then
        car_run
    fi
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
