"""Evaluate compact ODA adapters on matched FinQA calibration or official test."""

import argparse
import hashlib
import json
from math import isclose
from pathlib import Path
import re
import subprocess
import sys

from benchmark_actions import action_cost, collect_case, digest_file, freeze, read_panel
from cascade_benchmark import NonexecutionCascade, read_pool, realized, summarize
from diagnose import read_paired_run, read_replay_call
from grounding import ground
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


def collect_and_verify(benchmark, namespace, path, profile, panel, public, gold, panel_identity, metric_dir,
                       *, check_conflicts=False):
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
        decision = {'id': ident, 'strict': result['strict'], 'executable': result['executable'],
                    'selected': profile['model'], 'queried': [profile['model']], **cost,
                    'known_input_tokens': usage.get('input', 0), 'known_output_tokens': usage.get('output', 0)}
        if check_conflicts:
            decision['explicit_conflict'] = bool(result['executable'] and any(
                binding['explicit_conflicts'] for binding in ground(row, result['submission']['program'])))
        decisions.append(decision)
    return decisions, {'namespace': namespace, 'files': provenance, 'collection': read(directory / 'collection.json')}


def recovery_and_harm(candidate, baseline):
    pairs = [(a, b) for a, b in zip(candidate, baseline, strict=True)]
    if any(a['id'] != b['id'] for a, b in pairs):
        raise ValueError('Comparison decisions must align by question ID')
    outcomes = [(a['strict'] and a['executable'], b['strict'] and b['executable']) for a, b in pairs]
    return {'recoveries': sum(new and not old for new, old in outcomes),
            'harms': sum(old and not new for new, old in outcomes)}


def prepend(local, managed, *, forward_conflicts=False):
    decisions = []
    for first in local:
        if first['executable'] and not (forward_conflicts and first['explicit_conflict']):
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
        local, provenance = collect_and_verify(benchmark, f'oda_compact_{arm}_calibration_v1',
                                               compact / f'{arm}_serving_profile.json', profile,
                                               panel, public, gold, panel_identity, metric_dir)
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


def official_archive(benchmark, public, panel_identity):
    """Rebuild the archived official policies so the new comparison uses identical question IDs."""
    from frontier_report import (ODA_METHODS, budget_items, car_items, cascade_items, matched,
                                 selected_action, shared_budgetverify_inputs)
    from run_pilot import load_lines

    root = benchmark / 'official_frontiers_v1'
    archive_path = root / 'finqa_frontier.json'
    archive = read(archive_path)
    if (archive['dataset'], archive['n'], archive['panel']) != (DATASET, len(public), panel_identity):
        raise ValueError('Archived official frontiers differ from the current panel')
    oda_run = benchmark / 'oda_eval_v1'
    provenance = {name: digest_file(oda_run / name) for name in ('run.json', 'outcomes.jsonl')}
    if provenance != archive['oda']:
        raise ValueError('Archived ODA receipt digests differ')
    car = benchmark / 'car_oda_4096_v1' / DATASET / 'eval'
    sources = {name: root / f'finqa_{name}.json'
               for name in ('budgetverify_gbm', 'budgetverify_tabfm', 'cascade_raw', 'cascade_compiled')}
    sources['car'] = car / 'outcomes.jsonl'
    if {name: digest_file(path) for name, path in sources.items()} != archive['input_sha256']:
        raise ValueError('Archived official policy input digests differ')
    oda = matched(load_lines(oda_run / 'outcomes.jsonl'), public, 'ODA', DATASET)
    draft = {action: {ident: selected_action(row, action) for ident, row in oda.items()} for action in ODA_METHODS}
    policies = {f'oda/{action}': items for action, items in draft.items()}
    policies.update({name: items for name, (items, _) in car_items(
        car, oda, public, DATASET, panel_identity, provenance['outcomes.jsonl']).items()})
    gbm, tabfm = (read(sources[f'budgetverify_{name}']) for name in ('gbm', 'tabfm'))
    if shared_budgetverify_inputs(gbm, tabfm) != archive['budgetverify_inputs']:
        raise ValueError('Archived BudgetVerify inputs differ')
    for name, record, method in (('gbm', gbm, 'GBM'), ('tabfm', tabfm, 'TabFM-1.0.0-PyTorch')):
        tiers = budget_items(record, oda, public, DATASET, provenance, method)
        for prefix, tier in zip(('budgetverify', 'budgetverify_compiled'), tiers, strict=True):
            policies.update({f'{prefix}/{name}/{key}': items for key, (items, _) in tier.items()})
    for representation in ('raw', 'compiled'):
        record = read(sources[f'cascade_{representation}'])
        policies.update({f'cascade/{representation}/{name}': items
                         for name, (items, _) in cascade_items(record, draft, public).items()})
    if policies.keys() != archive['policy_metadata'].keys():
        raise ValueError('Archived official policy names differ')
    ids = [ident for ident in public if all(
        not items[ident].unknown_usage_calls and items[ident].executable is not None for items in policies.values())]
    archived = archive['strata']['common_complete_usage_and_execution']
    if len(ids) != archived['n'] or any(
            (sum(items[ident].strict and items[ident].executable for ident in ids),
             sum(items[ident].known_tokens for ident in ids))
            != (archived['policies'][name]['strict_and_executable'], archived['policies'][name]['known_tokens'])
            for name, items in policies.items()):
        raise ValueError('Rebuilt official cohort differs from the archived published points')
    return root, digest_file(archive_path), policies, ids


def run_official(benchmark, container, metric_dir):
    from frontier_report import Outcome, frontier, summarize as summarize_outcomes
    from paired_tradeoff import paired_tradeoff

    compact = benchmark / 'compact_program_development_v1'
    panel = benchmark / 'panel' / 'eval'
    public, gold, panel_identity = read_panel(panel, DATASET)
    if len(public) != 1147:
        raise ValueError('Expected the complete 1,147-question official FinQA test panel')
    reports = {row['id']: row['report'] for row in public}
    root, archive_digest, archived, archive_ids = official_archive(benchmark, reports, panel_identity)
    ledger = root / 'campus_ledger.json'
    runs = [benchmark / 'oda_eval_v1', *(benchmark / f'campus_eval_{model}_v1'
                                        for model in (campus.QWEN_MODEL, campus.MODEL))]
    pool = read_pool(panel, DATASET, runs, representation='compiled', metric_dir=metric_dir, campus_rows=read(ledger))
    managed_arms = {
        'always_qwen-27b': realized(None, pool, initial=1),
        'always_deepseek': realized(None, pool, initial=2),
        'nonexecution_deepseek_qwen': realized(NonexecutionCascade((2, 1)), pool),
    }

    def indexed_outcomes(decisions):
        return {item['id']: Outcome(int(item['strict']), item['known_tokens'], item['unknown_usage_calls'],
                                   len(item['queried']), item['summed_call_seconds'], item['executable'])
                for item in decisions}

    for name, decisions in managed_arms.items():
        expected = archived[f'cascade/compiled/{name}']
        actual = indexed_outcomes(decisions)
        if (len(decisions) != 1147 or actual.keys() != expected.keys() or any(
                actual[ident]._replace(serial_seconds=expected[ident].serial_seconds) != expected[ident]
                or not isclose(actual[ident].serial_seconds, expected[ident].serial_seconds, abs_tol=1e-8)
                for ident in expected)):
            raise ValueError(f'{name}: independently replayed managed decisions differ from the official archive')
    managed = managed_arms['nonexecution_deepseek_qwen']
    by_id = {item['id']: item for item in managed}
    managed = [by_id[ident] for ident in reports]

    profile = serving_profiles(benchmark, compact, container)['canonical']
    profile_path = compact / 'canonical_serving_profile.json'
    if read(profile_path) != profile:
        raise ValueError('Official inference requires the exact canonical calibration serving profile')
    calibrated = read(benchmark / 'oda_compact_canonical_calibration_v1' / 'run.json')
    if (calibrated['opencode_sha256'] != digest_file(Path.home() / '.opencode/bin/opencode')
            or calibrated['checkpoint'] != profile['checkpoint'] or calibrated['serve_sha256'] != digest_file(profile_path)):
        raise ValueError('Official inference requires the same OpenCode and adapter as canonical calibration')
    wait_service(BASE, ALIASES['canonical'], 300)
    native, provenance = collect_and_verify(benchmark, 'oda_compact_canonical_finqa_test_v1', profile_path,
                                            profile, panel, public, gold, panel_identity, metric_dir,
                                            check_conflicts=True)
    native_name = 'canonical_native'
    base_gate = 'canonical_nonexecution_then_managed'
    conflict_gate = 'canonical_conflict_or_nonexecution_then_managed'
    candidates = {native_name: native, base_gate: prepend(native, by_id),
                  conflict_gate: prepend(native, by_id, forward_conflicts=True)}
    indexed = {name: indexed_outcomes(items) for name, items in candidates.items()}
    ids = [ident for ident in archive_ids if all(not items[ident].unknown_usage_calls for items in indexed.values())]
    if not ids:
        raise ValueError('No complete official cost comparisons remain after adding the compact policies')
    points = {name: summarize_outcomes([items[ident] for ident in ids])
              for name, items in {**archived, **indexed}.items()}
    comparator = {**indexed, 'managed_only': indexed_outcomes(managed)}
    contrasts = {}
    for name, baselines in ((native_name, ('managed_only',)), (base_gate, (native_name, 'managed_only')),
                            (conflict_gate, (native_name, base_gate, 'managed_only'))):
        contrasts[name] = {baseline: paired_tradeoff(indexed[name], comparator[baseline], reports.keys(), reports,
                                                     require_execution=True) for baseline in baselines}
    report = {'scope': 'Frozen canonical adapter on the complete official FinQA test. Local generation uses '
                       'native calls and replays the existing managed-only paths when the fixed gate fires.',
              'panel': panel_identity, 'archive_sha256': archive_digest,
              'managed_ledger_sha256': digest_file(ledger), 'provenance': provenance,
              'fixed_gate': 'Escalate on nonexecution or a public grounding explicit conflict.',
              'native_explicit_conflicts': sum(item['explicit_conflict'] for item in native),
              'native_known_input_tokens': sum(item['known_input_tokens'] for item in native),
              'native_known_output_tokens': sum(item['known_output_tokens'] for item in native),
              'policies': {name: {**summarize(items), 'vs_canonical_native': recovery_and_harm(items, native),
                                  'vs_managed_only': recovery_and_harm(items, managed)}
                           for name, items in candidates.items()},
              'managed': {name: summarize(items) for name, items in managed_arms.items()},
              'paired_tradeoff': contrasts,
              'common_complete_usage_and_execution': {
                  'archived_n': len(archive_ids), 'n': len(ids), 'policies': points,
                  'executable_correct_token_frontier': frontier(points, 'total_tokens', 'strict_and_executable')}}
    freeze(compact / 'official_finqa_summary.json', report)
    print(json.dumps({'policies': report['policies'], 'common_complete_n': len(ids),
                      'token_frontier': report['common_complete_usage_and_execution']['executable_correct_token_frontier']}),
          flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--container', required=True)
    parser.add_argument('--metric-dir', type=Path, required=True)
    parser.add_argument('--stage', choices=('calibration', 'official-finqa'), default='calibration')
    args = parser.parse_args()
    if re.fullmatch(r'[0-9a-f]{12,64}', args.container) is None:
        parser.error('--container must be a Docker container ID')
    entry = run_official if args.stage == 'official-finqa' else run
    entry(args.benchmark.resolve(), args.container, args.metric_dir.resolve())


if __name__ == '__main__':
    main()
