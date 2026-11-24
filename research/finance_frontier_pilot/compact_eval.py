"""Run and verify matched FinQA calibration with the base and two compact LoRAs."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from benchmark_actions import action_cost, collect_case, digest_file, freeze, read_panel
from cascade_benchmark import NonexecutionCascade, read_pool, realized, summarize
from diagnose import read_paired_run, read_replay_call
from run_pilot import wait_service
from school_benchmark import campus


BASE = 'http://127.0.0.1:18157/v1'
BASE_MODEL = 'oda-fin-rl-8b'
REVISION = '948c22ea48f9bf93e5747f4211657fcad9cb0295'
ALIASES = {'base': BASE_MODEL, 'canonical': 'oda-compact-canonical', 'teacher': 'oda-compact-teacher'}
DATASET = 'finqa'
ACTION = 'contract_compile'
ADAPTER_FILES = ('adapter_config.json', 'adapter_model.safetensors')


def read(path):
    return json.loads(path.read_bytes())


def serving_profiles(benchmark, compact, container):
    # Ask Docker for these fields alone. Full inspect can contain environment variables.
    keys = ('Image', 'Config.Cmd', 'Mounts', 'State.Running')
    template = '\n'.join('{{json .' + key + '}}' for key in keys)
    output = subprocess.check_output(['docker', 'inspect', '--type', 'container', '--format', template, container],
                                     text=True, timeout=15)
    image, argv, mounts, running = map(json.loads, output.splitlines())
    frozen = read(benchmark / 'oda_serving_profile.json')
    mounts = [{key: mount[key] for key in ('Source', 'Destination', 'RW')}
              for mount in sorted(mounts, key=lambda item: item['Destination'])]
    if (not running or frozen['model'] != BASE_MODEL or frozen['checkpoint'] != REVISION or image != frozen['image']
            or argv[:len(frozen['argv'])] != frozen['argv'] or any(mount not in mounts for mount in frozen['mounts'])):
        raise ValueError('Compact evaluation requires the frozen BF16 ODA image, flags, and base mounts')

    common = {'base_checkpoint': REVISION, 'image': image, 'argv': argv, 'mounts': mounts}
    profiles = {'base': {**common, 'model': BASE_MODEL, 'checkpoint': REVISION}}
    loras = [json.loads(argument) for argument in argv[argv.index('--lora-modules') + 1:]]
    by_name = {entry['name']: entry for entry in loras}
    if len(loras) != 2 or by_name.keys() != {ALIASES['canonical'], ALIASES['teacher']}:
        raise ValueError('Expected exactly the two frozen static LoRA aliases')
    for arm in ('canonical', 'teacher'):
        alias, destination = ALIASES[arm], f'/adapters/{arm}'
        path = compact / arm / arm
        expected = {'Source': str(path.resolve()), 'Destination': destination, 'RW': False}
        if expected not in mounts or by_name[alias] != {'name': alias, 'path': destination, 'base_model_name': BASE_MODEL}:
            raise ValueError(f'{alias}: adapter mount or model identity differs')
        result_path = compact / arm / 'RESULT.json'
        result = read(result_path)
        if (result['status'] != 'TRAINED_COMPACT_PROGRAM_DEVELOPMENT' or result['optimizer_updates'] != 67
                or result['arms'].keys() != {arm} or result['arms'][arm]['updates'] != 67):
            raise ValueError(f'{alias}: expected one completed training pass with 67 updates')
        artifacts = {name: digest_file(path / name) for name in ADAPTER_FILES}
        if any(result['arms'][arm]['adapter_files'].get(name) != digest for name, digest in artifacts.items()):
            raise ValueError(f'{alias}: adapter files differ from the training receipt')
        identity = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()
        profiles[arm] = {**common, 'model': alias, 'checkpoint': identity, 'adapter_files': artifacts,
                         'training_result_sha256': digest_file(result_path)}
    return profiles


def collect_and_verify(benchmark, compact, arm, profile, panel, public, gold, panel_identity, metric_dir):
    namespace = f'oda_compact_{arm}_calibration_v1'
    path = compact / f'{arm}_serving_profile.json'
    freeze(path, profile)
    subprocess.run([sys.executable, '-B', '-u', str(Path(__file__).with_name('benchmark_actions.py')),
                    '--panel', str(panel), '--dataset', DATASET, '--run-dir', str(benchmark), '--namespace', namespace,
                    '--base', BASE, '--model', profile['model'], '--checkpoint', profile['checkpoint'],
                    '--serving-profile', str(path), '--metric-dir', str(metric_dir), '--actions', ACTION,
                    '--disable-thinking', '--workers', '8', '--context', '16384', '--temperature', '.6',
                    '--solve-output', '4096', '--verify-output', '4096', '--probe-output', '4096'], check=True)

    directory = benchmark / namespace
    reports = {row['id']: row['report'] for row in public}
    run, indexed, provenance = read_paired_run(directory, panel_identity, reports, DATASET, ACTION)
    if (run['model'] != profile['model'] or run['checkpoint'] != profile['checkpoint']
            or run['serve_sha256'] != digest_file(path) or run['chat_template_kwargs'] != {'enable_thinking': False}):
        raise ValueError(f'{namespace}: unexpected local serving contract')
    decisions = []
    for row in public:
        ident = row['id']
        entry = indexed[ident]
        seen = []

        def call(name, actor, prompt):
            if (name, actor) != ('low', 'solve') or seen:
                raise ValueError(f'{namespace}: expected one native solve for {ident}')
            receipt = read_replay_call(directory, row, name, actor, prompt, provenance['run.json'], entry['calls'][name])
            seen.append(receipt)
            return receipt

        scored = collect_case(row, gold[DATASET, ident], [ACTION], call, metric_dir)
        cost = action_cost(seen)
        if entry['actions'] != {name: {**result, 'cost': cost} for name, result in scored.items()}:
            raise ValueError(f'{namespace}: replayed score or usage differs for {ident}')
        result = scored[ACTION]
        usage = seen[0]['usage'] or {}
        decisions.append({'id': ident, 'strict': result['strict'], 'executable': result['executable'],
                          'selected': profile['model'], 'queried': [profile['model']], **cost,
                          'known_input_tokens': usage.get('input', 0), 'known_output_tokens': usage.get('output', 0)})
    return decisions, {'namespace': namespace, 'files': provenance, 'collection': read(directory / 'collection.json')}


def recovery_and_harm(candidate, baseline):
    pairs = [(a, b) for a, b in zip(candidate, baseline, strict=True)]
    if any(a['id'] != b['id'] for a, b in pairs):
        raise ValueError('Comparison decisions must align by question ID')
    outcomes = [(a['strict'] and a['executable'], b['strict'] and b['executable']) for a, b in pairs]
    return {'recoveries': sum(new and not old for new, old in outcomes),
            'harms': sum(old and not new for new, old in outcomes)}


def prepend(local, managed):
    decisions = []
    for first in local:
        if first['executable']:
            decisions.append(first)
            continue
        peer = managed[first['id']]
        decisions.append({**peer, 'queried': [*first['queried'], *peer['queried']],
                          **{key: first[key] + peer[key]
                             for key in ('known_tokens', 'unknown_usage_calls', 'summed_call_seconds')}})
    return decisions


def run(benchmark, container, metric_dir):
    compact = benchmark / 'compact_program_development_v1'
    panel = benchmark / 'panel' / 'calibration'
    public, gold, panel_identity = read_panel(panel, DATASET)
    if len(public) != 48:
        raise ValueError('Expected the fixed 48 FinQA calibration questions')
    profiles = serving_profiles(benchmark, compact, container)
    ledger = benchmark / 'official_frontiers_v1' / 'campus_ledger.json'
    old = [benchmark / 'oda_calibration_v1', *(benchmark / f'campus_calibration_{model}_v1'
                                               for model in (campus.QWEN_MODEL, campus.MODEL))]
    pool = read_pool(panel, DATASET, old, representation='compiled', metric_dir=metric_dir, campus_rows=read(ledger))
    managed = realized(NonexecutionCascade((2, 1)), pool)
    by_id = {decision['id']: decision for decision in managed}
    if len(managed) != 48 or by_id.keys() != {row['id'] for row in public}:
        raise ValueError('Managed calibration does not cover the fixed local panel')
    managed = [by_id[row['id']] for row in public]

    wait_service(BASE, BASE_MODEL, 300)
    for model in (ALIASES['canonical'], ALIASES['teacher']):
        wait_service(BASE, model, 30)
    report = {'scope': 'Matched FinQA development comparison. Local arms are native calls. '
                       'The managed cascade and appended handoffs replay existing receipts without new calls.',
              'panel': panel_identity, 'managed_ledger_sha256': digest_file(ledger),
              'managed_only': summarize(managed), 'arms': {}}
    for arm, profile in profiles.items():
        local, provenance = collect_and_verify(benchmark, compact, arm, profile, panel, public, gold,
                                               panel_identity, metric_dir)
        if arm == 'base':
            baseline = local
        cascade = prepend(local, by_id)
        entry = {'native': {**summarize(local),
                            **{key: sum(item[key] for item in local)
                               for key in ('known_input_tokens', 'known_output_tokens')}},
                 'native_vs_base': recovery_and_harm(local, baseline),
                 'local_then_managed_replay': summarize(cascade),
                 'cascade_vs_managed_only': recovery_and_harm(cascade, managed), 'provenance': provenance}
        report['arms'][arm] = entry
        print(json.dumps({'arm': arm, **entry}), flush=True)
    freeze(compact / 'calibration_summary.json', report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--container', required=True)
    parser.add_argument('--metric-dir', type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r'[0-9a-f]{12,64}', args.container) is None:
        parser.error('--container must be a Docker container ID')
    run(args.benchmark.resolve(), args.container, args.metric_dir.resolve())


if __name__ == '__main__':
    main()
