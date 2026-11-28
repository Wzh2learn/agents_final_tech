#!/usr/bin/env bash
# Serve a verified joint checkpoint on the established, single research GPU lease.
set -euo pipefail
umask 077

study=$(cd "${1:?study directory}" && pwd -P)
panel=$(cd "${2:?public and reference panel directory}" && pwd -P)
label=${3:?new run label}
shift 3
[[ $study == "$HOME/wzh/research_evidence/"* && $label =~ ^[a-z][a-z0-9_]+$ ]]
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
driver="$repo/research/finance_frontier_pilot"
lease_repo="$HOME/wzh/projects/agents_final_tech"
python="$lease_repo/venv/bin/python"
original_train="$study/training/run"
train="$original_train"
plan_arm=
preference_arm=
case ${1:-} in
    --scale-adapter)
        shift
        train="$study/training/scale_4000_v1/run"
        for flag in "$@"; do
            case $flag in
                --joint-timing|--live-teacher|--pl*)
                    echo 'The 4000-row adapter supports unplanned native compact evaluation only.' >&2
                    exit 2
                    ;;
            esac
        done
        ;;
    --hard-adapter)
        shift
        train="$study/training/hard_adapt_v1/run"
        ;;
    --planning-adapter)
        plan_arm=${2:?plain or planned}
        [[ $plan_arm == plain || $plan_arm == planned ]]
        shift 2
        train="$study/training/planning_v1/$plan_arm/run"
        ;;
    --joint-preference-adapter)
        preference_arm=${2:-}
        if [[ $preference_arm != control && $preference_arm != preference ]]; then
            echo '--joint-preference-adapter requires control or preference.' >&2
            exit 2
        fi
        shift 2
        train="$study/training/semantic_joint_preference_run_v1/$preference_arm/run"
        ;;
esac
restore_status="$train/restore_teacher/status"
if [[ -n $plan_arm ]]; then
    restore_status="$study/training/planning_v1/restore_teacher/status"
    for flag in "$@"; do
        if [[ $flag == --planned ]]; then
            echo 'The planning adapter determines the prompt format.' >&2
            exit 2
        fi
    done
elif [[ -n $preference_arm ]]; then
    restore_status="$study/training/semantic_joint_preference_run_v1/restore_teacher/status"
    preference_options_start=1
    case ${1:-} in
        --joint-timing|--live-teacher) preference_options_start=2 ;;
    esac
    for flag in "${@:preference_options_start}"; do
        case $flag in
            --joint-timing|--live-teacher|--pl*)
                echo 'Use unplanned evaluation and place any timing mode immediately after the preference arm.' >&2
                exit 2
                ;;
        esac
    done
fi
if [[ $train != "$original_train" && -z $preference_arm ]]; then
    case ${1:-} in
        --joint-timing|--live-teacher)
            echo 'Continuation adapters use the compact evaluation mode.' >&2
            exit 2
            ;;
    esac
fi
model="$HOME/wzh/models/hf/ODA-Fin-RL-8B-948c22ea"
metric="$HOME/wzh/research_evidence/agent_learning_20261030/tools/tatqa/870accc41953dcde885aabeb963d94aabdc0fbc3"
out="$study/serving/$label"
image=sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f
alias=oda-compact-joint
base=http://127.0.0.1:18157/v1
export PYTHONPATH="$driver:$repo:$repo/src" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

joint_timing_batches() (
    local mode=$1
    shift
    local tabfm_deps="$HOME/wzh/external_research_sources/finance_frontier/budgetverify-tabfm-deps-v1"
    cd "$repo"
    PYTHONPATH="$tabfm_deps:$PYTHONPATH" "$python" -B - "$mode" "$driver" "$base" "$metric" "$out" \
        "${cid:-000000000000}" "$@" <<'PY'
from pathlib import Path
import subprocess
import sys

mode, driver, base, metric, output, container, *arguments = sys.argv[1:]
groups = [[]]
for token in arguments:
    if token == '--next-joint-timing':
        groups.append([])
    else:
        groups[-1].append(token)
if len(groups) < 2 or not all(groups):
    raise SystemExit('Separate two or more nonempty timing argument groups with --next-joint-timing.')

script = str(Path(driver) / 'live_policy_timing.py')
profile = str(Path(output) / 'serving_profile.json')
common = ['--stage', 'eval', '--base', base, '--compare-baselines', '--compact-container', container,
          '--joint-serving-profile', profile, '--metric-dir', metric]

if mode == 'check':
    sys.path.insert(0, driver)
    import live_policy_timing as timing

    def check(args, benchmark, ledger_root):
        if args.joint_gate is None or not args.joint_gate.is_file():
            raise SystemExit('Each timing group requires an existing --joint-gate file.')
        if not args.tabfm_checkpoint.exists():
            raise SystemExit('Each timing group requires an existing --tabfm-checkpoint.')

    # Reuse the driver's normal CLI validation without entering the live runner.
    timing.run = check
    for index, group in enumerate(groups, 1):
        if set(group) & {'-h', '--help'}:
            raise SystemExit(f'Timing group {index} must contain driver arguments.')
        sys.argv = [script, *group, *common]
        try:
            timing.main()
        except SystemExit as error:
            print(f'Invalid timing argument group {index}.', file=sys.stderr)
            if error.code == 0:
                raise SystemExit(2) from None
            raise
else:
    for index, group in enumerate(groups, 1):
        with (Path(output) / f'eval_{index:02d}.log').open('x', encoding='utf-8') as log:
            result = subprocess.run([sys.executable, '-B', '-u', script, *group, *common],
                                    stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise SystemExit(result.returncode if result.returncode > 0 else 128 - result.returncode)
PY
)

joint_batch=0
if [[ ${1:-} == --joint-timing ]]; then
    # A separator opts in; an ordinary timing invocation keeps its original log and command.
    for flag in "${@:2}"; do
        if [[ $flag == --next-joint-timing ]]; then
            joint_batch=1
            joint_timing_batches check "${@:2}"
            break
        fi
    done
fi

test -s "$panel/public.jsonl"
test -s "$panel/references.jsonl"
test -s "$metric/tatqa_metric.py"
for ((attempt=0; attempt<15; attempt++)); do
    [[ ! -s $study/training/supervisor/exit ]] || break
    sleep 1
done
grep -Fxq 0 "$study/training/supervisor/exit"
grep -Fxq ready "$restore_status"
adapter=$("$python" -B - "$original_train" "$train" "$model" "$plan_arm" "$preference_arm" <<'PY'
from pathlib import Path
import json
import sys
from benchmark_actions import digest_file
from compact_consensus import OPERAND_PLAN_INSTRUCTION

original, train, model = map(Path, sys.argv[1:4])
plan_arm, preference_arm = sys.argv[4:6]


def adapter_from_receipt(directory, status, examples):
    result = json.loads((directory / 'RESULT.json').read_text())
    matches = [item for item in result['adapters'] if item['examples'] == examples]
    adapter = directory / f'adapter_{examples:04d}'
    if (result['status'] != status or result['examples'] != examples
            or result['plan_sha256'] != digest_file(directory / 'PLAN.json') or len(matches) != 1
            or Path(matches[0]['directory']).resolve() != adapter.resolve()):
        raise ValueError(f'Expected the finalized {examples}-example adapter in {directory}')
    artifacts = matches[0]['artifacts']
    if set(artifacts) != {'adapter_config.json', 'adapter_model.safetensors'} or any(
            digest_file(adapter / name) != checksum for name, checksum in artifacts.items()):
        raise ValueError('Adapter files differ from the training receipt')
    return adapter, artifacts


plan = json.loads((original / 'PLAN.json').read_text())
if Path(plan['model_path']).resolve() != model.resolve():
    raise ValueError('Expected the pinned ODA base for the joint adapter')
adapter, original_artifacts = adapter_from_receipt(original, 'TRAINED_ODA_JOINT_COMPACT', 3000)
if train == original.parent / 'scale_4000_v1/run':
    manifest_path = original.parents[1] / 'data/joint_scale_4000_v1/manifest.json'
    if digest_file(manifest_path) != '2da43151f271556174bfbddc2f25cdadfd7bbcb04b0fa139c24abec522c5ed78':
        raise ValueError('Expected the frozen 4000-row source manifest')
    manifest = json.loads(manifest_path.read_text())
    scale_plan = json.loads((train / 'PLAN.json').read_text())
    result = json.loads((train / 'RESULT.json').read_text())
    targets = manifest_path.with_name('targets_4000.jsonl')
    target_sha = manifest['target_sha256'][targets.name]
    if (manifest['status'] != 'CPU_FROZEN' or manifest['combined_count'] != 4000
            or scale_plan['schema'] != 'oda-joint-compact-train-v1' or scale_plan['examples'] != 4000
            or manifest['original_fit_sha256'] != plan['targets_sha256']
            or scale_plan['script_sha256'] != plan['script_sha256']
            or scale_plan['thinking'] is not False or scale_plan['optimizer_updates'] != 1000
            or result['optimizer_updates'] != 1000 or result['trainable_parameters'] != 3833856
            or Path(scale_plan['model_path']).resolve() != model.resolve()
            or scale_plan['model_files'] != plan['model_files']
            or any(digest_file(model / name) != checksum for name, checksum in plan['model_files'].items())
            or Path(scale_plan['targets']).resolve() != targets
            or digest_file(targets) != target_sha or scale_plan['targets_sha256'] != target_sha):
        raise ValueError('The finalized 4000-row training plan or source differs')
    adapter, _ = adapter_from_receipt(train, 'TRAINED_ODA_JOINT_COMPACT', 4000)
elif train != original:
    continuation = json.loads((train / 'PLAN.json').read_text())
    if continuation['warm_adapter'] != original_artifacts or continuation['model_files'] != plan['model_files']:
        raise ValueError('Continuation must inherit the exact joint adapter and pinned ODA base')
    if plan_arm:
        planned = plan_arm == 'planned'
        result = json.loads((train / 'RESULT.json').read_text())
        if (continuation['schema'] != 'oda-joint-compact-operand-planning-v1'
                or continuation['arm'] != plan_arm or continuation['planned'] is not planned
                or continuation['plan_prompt_suffix'] != (OPERAND_PLAN_INSTRUCTION if planned else '')
                or result['arm'] != plan_arm or result['planned'] is not planned
                or continuation['examples'] != 384):
            raise ValueError('Planning arm, prompt format or matched row count differs')
        status = 'TRAINED_ODA_JOINT_COMPACT_OPERAND_PLAN'
    elif preference_arm:
        result = json.loads((train / 'RESULT.json').read_text())
        if (continuation['schema'] != 'oda-joint-compact-joint-preference-v1'
                or continuation['examples'] != 256 or continuation['optimizer_updates'] != 64
                or result['optimizer_updates'] != continuation['optimizer_updates']
                or any(receipt['arm'] != preference_arm or receipt['planned'] is not False
                       for receipt in (continuation, result))):
            raise ValueError('Joint preference arm, prompt format or matched training plan differs')
        status = 'TRAINED_ODA_JOINT_COMPACT_JOINT_PREFERENCE'
    else:
        if continuation['schema'] != 'oda-joint-compact-hard-v1':
            raise ValueError('Expected hard-example continuation')
        status = 'TRAINED_ODA_JOINT_COMPACT_HARD'
    adapter, _ = adapter_from_receipt(train, status, continuation['examples'])
print(adapter)
PY
)

lock="$HOME/wzh/.gpu_lock"
guard=$(lslocks -rn -o PID,PATH | awk -v lock="$lock" '$2==lock{print $1}')
[[ $guard =~ ^[1-9][0-9]+$ && $(readlink -f "/proc/$guard/cwd") = "$lease_repo" ]]
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
        (
            cd "$lease_repo" || exit 1
            export PYTHONPATH="$lease_repo/research/finance_frontier_pilot:$lease_repo:$lease_repo/src"
            nohup setsid "$python" -u -B "$out/restore_teacher/restore.py" \
                </dev/null >"$out/restore.log" 2>&1 &
            printf '%s\n' "$!" >"$out/restore.pid"
        )
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
if ((joint_batch)); then
    joint_timing_batches run "${@:2}"
elif [[ ${1:-} == --joint-timing ]]; then
    shift
    tabfm_deps="$HOME/wzh/external_research_sources/finance_frontier/budgetverify-tabfm-deps-v1"
    PYTHONPATH="$tabfm_deps:$PYTHONPATH" "$python" -B -u "$driver/live_policy_timing.py" --stage eval --base "$base" --compare-baselines \
        --compact-container "$cid" \
        --joint-serving-profile "$out/serving_profile.json" --metric-dir "$metric" "$@" >"$out/eval.log" 2>&1
elif [[ ${1:-} == --live-teacher ]]; then
    shift
    profile_digest=$(sha256sum "$out/serving_profile.json" | cut -d ' ' -f 1)
    "$python" -B -u "$driver/live_compact_teacher.py" --live --panel "$panel" --output "$out/live" \
        --base "$base" --serving-profile "$out/serving_profile.json" --serving-profile-sha256 "$profile_digest" \
        --metric-dir "$metric" "$@" >"$out/eval.log" 2>&1
else
    if [[ $plan_arm == planned ]]; then set -- --planned "$@"; fi
    "$python" -B -u "$driver/compact_consensus.py" --panel "$panel" --output "$out/measurements" \
        --base "$base" --model "$alias" --serving-profile "$out/serving_profile.json" \
        --metric-dir "$metric" --measure-exclusive-engine "$@" >"$out/eval.log" 2>&1
fi
