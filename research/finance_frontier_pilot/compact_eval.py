"""Evaluate compact ODA adapters on matched calibration or official financial reasoning panels."""

import argparse
import hashlib
import json
from math import isclose, isfinite
from pathlib import Path
import re
from statistics import median
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
DEPTH_ALIASES = {'balanced': 'oda-compact-balanced', 'multi_only': 'oda-compact-multi-only'}
TATQA_EXPANSION_ALIASES = {'canonical': ALIASES['canonical'],
                           'annotated_scale': 'oda-compact-annotated-scale',
                           'execution_aligned': 'oda-compact-execution-aligned'}
TATQA_EXPANSION_PINS = {
    'panel/manifest.json': 'be7a3cbf21a09afe88ad6c75dc4323c5d4a01f0e30ef01c86aba04dcbe8670c8',
    'panel/calibration/public.jsonl': 'f6478c5ca6e127b557bb8fbe1c54e567d53f052bb7b221f0beb882b11add464d',
}
DATASET = 'finqa'
ACTION = 'contract_compile'
ADAPTER_FILES = ('adapter_config.json', 'adapter_model.safetensors')
MANAGED_RESCUE_FEATURES = ('question_chars', 'question_digits', 'question_percent', 'question_years',
                           'table_rows', 'table_cells', 'evidence_chars', 'program_chars', 'operations',
                           'scale_none', 'scale_thousand', 'scale_million', 'scale_billion', 'scale_percent',
                           'ambiguous_literals', 'explicit_conflicts')


def read(path):
    return json.loads(path.read_bytes())


def inspect_server(benchmark, container):
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
    return frozen, image, argv, mounts


def serving_profiles(benchmark, compact, container, *, dataset=DATASET, depth_control=False):
    _, image, argv, mounts = inspect_server(benchmark, container)
    common = {'base_checkpoint': REVISION, 'image': image, 'argv': argv, 'mounts': mounts}
    profiles = {'base': {**common, 'model': BASE_MODEL, 'checkpoint': REVISION}}
    loras = [json.loads(argument) for argument in argv[argv.index('--lora-modules') + 1:]]
    by_name = {entry['name']: entry for entry in loras}
    aliases = DEPTH_ALIASES if depth_control else {arm: ALIASES[arm] for arm in ('canonical', 'teacher')}
    if len(loras) != 2 or by_name.keys() != set(aliases.values()):
        raise ValueError('Expected exactly the two frozen static LoRA aliases')
    if depth_control:
        updates, status = 134, 'TRAINED_FINQA_DEPTH_CONTROL'
    elif dataset == 'tatqa':
        updates, status = 78, 'TRAINED_TATQA_COMPACT_PROGRAM_DEVELOPMENT'
    else:
        updates, status = 67, 'TRAINED_COMPACT_PROGRAM_DEVELOPMENT'
    for arm, alias in aliases.items():
        destination = f'/adapters/{arm}'
        path = compact / arm / arm
        expected = {'Source': str(path.resolve()), 'Destination': destination, 'RW': False}
        if expected not in mounts or by_name[alias] != {'name': alias, 'path': destination, 'base_model_name': BASE_MODEL}:
            raise ValueError(f'{alias}: adapter mount or model identity differs')
        result_path = compact / arm / 'RESULT.json'
        result = read(result_path)
        if (result['status'] != status or result['optimizer_updates'] != updates
                or result['arms'].keys() != {arm} or result['arms'][arm]['updates'] != updates):
            raise ValueError(f'{alias}: expected one completed training pass with {updates} updates')
        artifacts = {name: digest_file(path / name) for name in ADAPTER_FILES}
        if any(result['arms'][arm]['adapter_files'].get(name) != digest for name, digest in artifacts.items()):
            raise ValueError(f'{alias}: adapter files differ from the training receipt')
        identity = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()
        profiles[arm] = {**common, 'model': alias, 'checkpoint': identity, 'adapter_files': artifacts,
                         'training_result_sha256': digest_file(result_path)}
    return profiles


def timed_compact_profile(benchmark, container, dataset):
    """Bind the matched timing server to the two evaluated compact checkpoints."""
    development = benchmark / 'compact_program_development_v1'
    adapters = {'finqa': ('balanced', DEPTH_ALIASES['balanced'], development / 'finqa_depth_control'),
                'tatqa': ('canonical', ALIASES['canonical'], development / 'tatqa_aligned')}
    arm, alias, directory = adapters[dataset]
    frozen, image, argv, mounts = inspect_server(benchmark, container)
    prefix = frozen['argv'] + ['--enable-lora', '--max-lora-rank', '8', '--lora-dtype', 'bfloat16',
                              '--max-loras', '1', '--max-cpu-loras', '2', '--lora-modules']
    expected_loras = [{'name': model, 'path': f'/adapters/{name}', 'base_model_name': BASE_MODEL}
                      for name, model, _ in adapters.values()]
    if argv[:len(prefix)] != prefix or [json.loads(entry) for entry in argv[len(prefix):]] != expected_loras:
        raise ValueError('Matched timing requires the two frozen compact aliases and serving flags')
    expected_mounts = [
        *frozen['mounts'],
        *({'Source': str((root / name / name).resolve()), 'Destination': f'/adapters/{name}', 'RW': False}
          for name, _, root in adapters.values()),
    ]
    if sorted(expected_mounts, key=lambda item: item['Destination']) != mounts:
        raise ValueError('Matched timing requires the frozen base and read-only compact adapter mounts')
    profile_path = directory / f'{arm}_serving_profile.json'
    previous = read(profile_path)
    artifacts = {name: digest_file(directory / arm / arm / name) for name in ADAPTER_FILES}
    checkpoint = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()
    if (previous['model'], previous['base_checkpoint'], previous['checkpoint'], previous['adapter_files']) != (
            alias, REVISION, checkpoint, artifacts):
        raise ValueError('Timed compact adapter differs from the evaluated checkpoint')
    return {'model': alias, 'checkpoint': checkpoint, 'base_checkpoint': REVISION,
            'image': image, 'argv': argv, 'mounts': mounts, 'adapter_files': artifacts,
            'evaluated_serving_profile_sha256': digest_file(profile_path)}


def collect_and_verify(benchmark, namespace, path, profile, panel, public, gold, panel_identity, metric_dir,
                       *, dataset=DATASET, check_conflicts=False, measure_wall=False, capture_features=False):
    freeze(path, profile)
    timing = ['--workers', '1', '--measure-wall'] if measure_wall else ['--workers', '8']
    subprocess.run([sys.executable, '-B', '-u', str(Path(__file__).with_name('benchmark_actions.py')),
                    '--panel', str(panel), '--dataset', dataset, '--run-dir', str(benchmark), '--namespace', namespace,
                    '--base', BASE, '--model', profile['model'], '--checkpoint', profile['checkpoint'],
                    '--serving-profile', str(path), '--metric-dir', str(metric_dir), '--actions', ACTION,
                    '--disable-thinking', *timing, '--context', '16384', '--temperature', '.6',
                    '--solve-output', '4096', '--verify-output', '4096', '--probe-output', '4096'], check=True)
    return verify_collection(benchmark / namespace, path, profile, public, gold, panel_identity, metric_dir,
                             dataset=dataset, check_conflicts=check_conflicts, capture_features=capture_features)


def verify_collection(directory, path, profile, public, gold, panel_identity, metric_dir,
                      *, dataset=DATASET, check_conflicts=False, disable_thinking=True, capture_features=False):
    namespace = directory.name
    reports = {row['id']: row['report'] for row in public}
    run, indexed, provenance = read_paired_run(directory, panel_identity, reports, dataset, ACTION)
    expected = {'enable_thinking': False} if disable_thinking else None
    if (run['model'] != profile['model'] or run['checkpoint'] != profile['checkpoint']
            or run['serve_sha256'] != digest_file(path) or run.get('chat_template_kwargs') != expected):
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

        scored = collect_case(row, gold[dataset, ident], [ACTION], call, metric_dir)
        cost = action_cost(seen)
        if entry['actions'] != {name: {**result, 'cost': cost} for name, result in scored.items()}:
            raise ValueError(f'{namespace}: replayed score or usage differs for {ident}')
        result = scored[ACTION]
        usage = seen[0]['usage'] or {}
        decision = {'id': ident, 'strict': result['strict'], 'executable': result['executable'],
                    'selected': profile['model'], 'queried': [profile['model']], **cost,
                    'known_input_tokens': usage.get('input', 0), 'known_output_tokens': usage.get('output', 0)}
        if check_conflicts or capture_features:
            bindings = ground(row, result['submission']['program']) if result['executable'] else []
            decision['explicit_conflict'] = any(binding['explicit_conflicts'] for binding in bindings)
            decision['ambiguous_literals'] = sum(len(binding['candidates']) > 1 for binding in bindings)
            if capture_features:
                decision['public_features'] = managed_rescue_features(row, result['submission'], decision)
        decisions.append(decision)
    evidence = {'namespace': namespace, 'files': provenance, 'collection': read(directory / 'collection.json')}
    if run.get('timing_protocol') == 'fresh_serial_action_until_execution_v1':
        times = []
        for entry in indexed.values():
            timing = entry['online_wall']
            seconds = timing['seconds']
            if timing['action'] != ACTION or not isfinite(seconds) or seconds <= 0:
                raise ValueError(f'{namespace}: invalid measured wall time for {entry["id"]}')
            times.append(seconds)
        evidence['serial_action_wall_seconds'] = {'n': len(times), 'median': median(times), 'sum': sum(times)}
    return decisions, evidence


def recovery_and_harm(candidate, baseline):
    pairs = [(a, b) for a, b in zip(candidate, baseline, strict=True)]
    if any(a['id'] != b['id'] for a, b in pairs):
        raise ValueError('Comparison decisions must align by question ID')
    outcomes = [(a['strict'] and a['executable'], b['strict'] and b['executable']) for a, b in pairs]
    return {'recoveries': sum(new and not old for new, old in outcomes),
            'harms': sum(old and not new for new, old in outcomes)}


def managed_rescue_features(row, submission, observed):
    """Fixed, label-free features available immediately after local execution."""
    question = row['question'].casefold()
    program = submission.get('program') or ''
    scale = submission.get('scale') or ''
    values = (len(question), sum(char.isdigit() for char in question),
              int('%' in question or 'percent' in question), len(re.findall(r'\b(?:19|20)\d{2}\b', question)),
              len(row['table']), sum(len(line) for line in row['table']),
              sum(len(text) for key in ('pre_text', 'post_text') for text in row[key]),
              len(program), program.count('('), *(int(scale == name) for name in ('', 'thousand', 'million', 'billion', 'percent')),
              observed['ambiguous_literals'], int(observed['explicit_conflict']))
    if len(values) != len(MANAGED_RESCUE_FEATURES):
        raise ValueError('Unexpected managed-rescue public feature length')
    return values


def prepend(local, managed, *, forward_conflicts=False, forward_ids=()):
    decisions = []
    for first in local:
        if (first['executable'] and first['id'] not in forward_ids
                and not (forward_conflicts and first['explicit_conflict'])):
            decisions.append(first)
            continue
        peer = managed[first['id']]
        decisions.append({**peer, 'queried': [*first['queried'], *peer['queried']],
                          **{key: first[key] + peer[key]
                             for key in ('known_tokens', 'unknown_usage_calls', 'summed_call_seconds')}})
    return decisions


def indexed_outcomes(decisions):
    from frontier_report import Outcome

    return {item['id']: Outcome(int(item['strict']), item['known_tokens'], item['unknown_usage_calls'],
                               len(item['queried']), item['summed_call_seconds'], item['executable'])
            for item in decisions}


def run(benchmark, container, metric_dir, *, dataset=DATASET):
    compact = benchmark / 'compact_program_development_v1'
    namespace_prefix = 'oda_compact'
    dataset_name = 'FinQA'
    if dataset == 'tatqa':
        compact /= 'tatqa_aligned'
        namespace_prefix = 'oda_compact_tatqa'
        dataset_name = 'TAT-QA'
    panel = benchmark / 'panel' / 'calibration'
    public, gold, panel_identity = read_panel(panel, dataset)
    if len(public) != 48:
        raise ValueError(f'Expected the fixed 48 {dataset_name} calibration questions')
    profiles = serving_profiles(benchmark, compact, container, dataset=dataset)
    ledger = benchmark / 'official_frontiers_v1' / 'campus_ledger.json'
    old = [benchmark / 'oda_calibration_v1', *(benchmark / f'campus_calibration_{model}_v1'
                                               for model in (campus.QWEN_MODEL, campus.MODEL))]
    pool = read_pool(panel, dataset, old, representation='compiled', metric_dir=metric_dir, campus_rows=read(ledger))
    managed = realized(NonexecutionCascade((2, 1)), pool)
    by_id = {decision['id']: decision for decision in managed}
    if len(managed) != 48 or by_id.keys() != {row['id'] for row in public}:
        raise ValueError('Managed calibration does not cover the fixed local panel')
    managed = [by_id[row['id']] for row in public]

    wait_service(BASE, BASE_MODEL, 300)
    for model in (ALIASES['canonical'], ALIASES['teacher']):
        wait_service(BASE, model, 30)
    report = {'scope': f'Matched {dataset_name} development comparison. Local arms are native calls. '
                       'The managed cascade and appended handoffs replay existing receipts without new calls.',
              'panel': panel_identity, 'managed_ledger_sha256': digest_file(ledger),
              'managed_only': summarize(managed), 'arms': {}}
    for arm, profile in profiles.items():
        local, provenance = collect_and_verify(benchmark, f'{namespace_prefix}_{arm}_calibration_v1',
                                               compact / f'{arm}_serving_profile.json', profile,
                                               panel, public, gold, panel_identity, metric_dir, dataset=dataset)
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


def tatqa_expansion_inputs(benchmark, compact):
    """Bind both panels and training inputs to the pre-existing source snapshot."""
    from cohorts import read_source, table_signature

    for relative, digest in TATQA_EXPANSION_PINS.items():
        if digest_file(compact / relative) != digest:
            raise ValueError(f'Frozen TAT-QA expansion input changed: {relative}')
    manifest_path = compact / 'panel' / 'manifest.json'
    manifest = read(manifest_path)
    source = manifest['train']
    if (manifest['schema'] != 'tatqa-compact-source-expansion-v1'
            or source['sha256'] != '2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69'
            or manifest['scoring_n'] != 96
            or manifest['train_counts'] != {'single': 128, 'single_changed': 16,
                                            'multi': 128, 'multi_changed': 73}):
        raise ValueError('Unexpected frozen TAT-QA source-expansion manifest')
    candidates, observed_source = read_source('tatqa', Path(source['path']), upstream={
        'tatqa': (source['split'], source['url'], source['sha256'], source['source_questions'])})
    if observed_source != source:
        raise ValueError('The TAT-QA training source differs from the frozen manifest')
    source_rows = {row['id']: (row, {k: v for k, v in reference.items() if k != 'question'})
                   for row, reference, _ in candidates}
    panels = {name: read_panel(compact / 'panel' / name, 'tatqa') for name in ('fit', 'calibration')}
    for name, expected in (('fit', 256), ('calibration', 96)):
        public, gold, _ = panels[name]
        if len(public) != expected:
            raise ValueError(f'Expected {expected} frozen {name} questions')
        if any(row['id'] not in source_rows or source_rows[row['id']] != (row, gold['tatqa', row['id']])
               for row in public):
            raise ValueError(f'{name}: public inputs or references differ from the pinned source')
    fit, calibration = (panels[name][0] for name in ('fit', 'calibration'))
    if ({r['id'] for r in fit} & {r['id'] for r in calibration}
            or {r['report'] for r in fit} & {r['report'] for r in calibration}
            or {table_signature(r['table']) for r in fit} & {table_signature(r['table']) for r in calibration}):
        raise ValueError('Training and calibration sources must be disjoint')

    targets = compact / 'targets.jsonl'
    if digest_file(targets) != manifest['targets_sha256']:
        raise ValueError('Prepared training targets differ from the frozen manifest')
    target_rows = [json.loads(line) for line in targets.read_text(encoding='utf-8').splitlines() if line.strip()]
    target_ids = {row['id']: row['report'] for row in target_rows}
    if len(target_rows) != 256 or len(target_ids) != 256 or target_ids != {r['id']: r['report'] for r in fit}:
        raise ValueError('Training target identities differ from the frozen fit panel')
    if set(manifest['old_public_exclusion']) != {'fit', 'calibration', 'eval'}:
        raise ValueError('The frozen old-panel exclusions are incomplete')
    for name, digest in manifest['old_public_exclusion'].items():
        if digest_file(benchmark / 'panel' / name / 'public.jsonl') != digest:
            raise ValueError(f'Old public exclusion changed: {name}')
    plans, data_rows = {}, {}
    for arm in ('annotated_scale', 'execution_aligned'):
        plan = read(compact / arm / 'PLAN.json')
        if (plan['arms'] != [arm] or plan['updates_per_arm'] != 256
                or plan['terminal_status'] != 'TRAINED_TATQA_COMPACT_SOURCE_EXPANSION'
                or digest_file(compact / arm / 'DATA.json') != plan['data_sha256']):
            raise ValueError(f'{arm}: frozen training plan or data differs')
        data = read(compact / arm / 'DATA.json')
        if data['verified_target_carrier'] != manifest['targets_sha256'] or len(data['rows']) != 256:
            raise ValueError(f'{arm}: training data is not bound to the frozen targets')
        data_rows[arm] = data['rows']
        plans[arm] = plan
    matched = ('model_path', 'seed', 'updates_per_arm', 'schedule', 'learning_rate',
               'rank', 'alpha', 'completion_logits_only')
    if any(plans['annotated_scale'][key] != plans['execution_aligned'][key] for key in matched):
        raise ValueError('Expansion arms must use the same training schedule and model settings')
    for a, b in zip(data_rows['annotated_scale'], data_rows['execution_aligned'], strict=True):
        if (a['prompt_token_count'] != b['prompt_token_count']
                or a['input_ids'][:a['prompt_token_count']] != b['input_ids'][:b['prompt_token_count']]):
            raise ValueError('Expansion training prompts differ across arms')
    identity = {'manifest_sha256': digest_file(manifest_path), 'source_sha256': source['sha256'],
                'targets_sha256': digest_file(targets), 'panels': {name: p[2] for name, p in panels.items()},
                'plans': {arm: digest_file(compact / arm / 'PLAN.json') for arm in plans},
                'data': {arm: digest_file(compact / arm / 'DATA.json') for arm in plans}}
    return panels['calibration'], identity


def tatqa_expansion_profiles(benchmark, compact, container):
    """Verify the three static adapters share exactly one frozen BF16 server."""
    frozen, image, argv, mounts = inspect_server(benchmark, container)
    prefix = frozen['argv'] + ['--enable-lora', '--max-lora-rank', '8', '--lora-dtype', 'bfloat16',
                              '--max-loras', '1', '--max-cpu-loras', '3', '--lora-modules']
    if argv[:len(prefix)] != prefix:
        raise ValueError('Expected the frozen BF16 ODA server with three static adapters')
    loras = [json.loads(argument) for argument in argv[len(prefix):]]
    by_name = {entry['name']: entry for entry in loras}
    if len(loras) != 3 or by_name.keys() != set(TATQA_EXPANSION_ALIASES.values()):
        raise ValueError('Expected exactly the three TAT-QA expansion adapter aliases')
    profiles = {}
    for arm, alias in TATQA_EXPANSION_ALIASES.items():
        root = compact.parent / arm if arm == 'canonical' else compact / arm
        path = root / arm
        destination = f'/adapters/{arm}'
        if ({'Source': str(path.resolve()), 'Destination': destination, 'RW': False} not in mounts
                or by_name[alias] != {'name': alias, 'path': destination, 'base_model_name': BASE_MODEL}):
            raise ValueError(f'{alias}: adapter mount or model identity differs')
        receipt = root / 'RESULT.json'
        result = read(receipt)
        updates, status = ((78, 'TRAINED_TATQA_COMPACT_PROGRAM_DEVELOPMENT') if arm == 'canonical'
                           else (256, 'TRAINED_TATQA_COMPACT_SOURCE_EXPANSION'))
        if (result['status'] != status or result['optimizer_updates'] != updates
                or result['arms'].keys() != {arm} or result['arms'][arm]['updates'] != updates):
            raise ValueError(f'{alias}: incomplete or unexpected training result')
        artifacts = {name: digest_file(path / name) for name in ADAPTER_FILES}
        if any(result['arms'][arm]['adapter_files'].get(name) != digest for name, digest in artifacts.items()):
            raise ValueError(f'{alias}: adapter files differ from its training receipt')
        identity = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()
        profiles[arm] = {'base_checkpoint': REVISION, 'image': image, 'argv': argv, 'mounts': mounts,
                         'model': alias, 'checkpoint': identity, 'adapter_files': artifacts,
                         'training_result_sha256': digest_file(receipt)}
    return profiles


def run_tatqa_expansion(benchmark, container, metric_dir):
    from paired_tradeoff import paired_tradeoff

    compact = benchmark / 'compact_program_development_v1' / 'tatqa_aligned' / 'source_expansion_v1'
    panel = compact / 'panel' / 'calibration'
    (public, gold, panel_identity), source_identity = tatqa_expansion_inputs(benchmark, compact)
    profiles = tatqa_expansion_profiles(benchmark, compact, container)
    reports = {row['id']: row['report'] for row in public}
    wait_service(BASE, BASE_MODEL, 300)
    for alias in TATQA_EXPANSION_ALIASES.values():
        wait_service(BASE, alias, 30)
    report = {'scope': 'Matched TAT-QA TRAIN calibration: three fresh native adapter collections. '
                       'This is a development comparison, not an official DEV confirmation.',
              'panel': panel_identity, 'source_identity': source_identity, 'arms': {}}
    decisions = {}
    for arm, profile in profiles.items():
        profile = {**profile, 'source_identity': source_identity}
        local, provenance = collect_and_verify(
            benchmark, f'oda_compact_tatqa_expansion_{arm}_calibration_v1',
            compact / f'{arm}_serving_profile.json', profile, panel, public, gold,
            panel_identity, metric_dir, dataset='tatqa')
        decisions[arm] = local
        report['arms'][arm] = {'native': {**summarize(local), **{
            key: sum(item[key] for item in local) for key in ('known_input_tokens', 'known_output_tokens')}},
            'provenance': provenance}
        print(json.dumps({'arm': arm, **report['arms'][arm]}), flush=True)
    if tatqa_expansion_inputs(benchmark, compact)[1] != source_identity:
        raise ValueError('Frozen TAT-QA inputs changed during collection')
    if tatqa_expansion_profiles(benchmark, compact, container) != profiles:
        raise ValueError('The serving image, mounts, adapters or receipts changed during collection')
    aligned = decisions['execution_aligned']
    report['contrasts'] = {}
    for arm in ('annotated_scale', 'canonical'):
        report['contrasts'][arm] = {
            'recovery_and_harm': recovery_and_harm(aligned, decisions[arm]),
            'paired_tradeoff': paired_tradeoff(indexed_outcomes(aligned), indexed_outcomes(decisions[arm]),
                                               reports.keys(), reports, require_execution=True)}
    freeze(compact / 'calibration_summary.json', report)
    print(json.dumps({'contrasts': report['contrasts']}), flush=True)


def run_depth(benchmark, container, metric_dir):
    """Compare matched training depths on new source pairs and the original calibration panel."""
    from cohorts import table_signature
    from diagnose import paired_effect
    from paired_tradeoff import paired_tradeoff

    compact = benchmark / 'compact_program_development_v1' / 'finqa_depth_control'
    preparation_path = compact / 'summary.json'
    preparation = read(preparation_path)
    paths = {name: compact / 'panel' / name for name in ('single', 'multi')}
    paths['retention'] = benchmark / 'panel' / 'calibration'
    panels = {name: read_panel(path, DATASET) for name, path in paths.items()}
    if any(len(public) != 48 for public, _, _ in panels.values()):
        raise ValueError('Each depth-control panel requires its fixed 48 FinQA questions')
    if ({name: panels[name][2] for name in ('single', 'multi')} != preparation['calibration_panel_sha256']
            or panels['retention'][2]['public.jsonl'] != preparation['public_panel_sha256']['calibration']):
        raise ValueError('Depth-control panels differ from the prepared experiment')

    single = panels['single'][0]
    multi = {row['report']: row for row in panels['multi'][0]}
    if len(multi) != 48 or multi.keys() != {row['report'] for row in single}:
        raise ValueError('Single and multi panels do not match by distinct source report')
    pairs = [[row['id'], multi[row['report']]['id']] for row in single]
    pair_digest = hashlib.sha256(json.dumps(pairs, separators=(',', ':')).encode()).hexdigest()
    if (pair_digest != preparation['new_calibration_pair_ids_sha256'] or any(
            row['id'] == multi[row['report']]['id']
            or table_signature(row['table']) != table_signature(multi[row['report']]['table']) for row in single)):
        raise ValueError('Depth-control question pairs do not match the frozen source tables')

    profiles = serving_profiles(benchmark, compact, container, depth_control=True)
    wait_service(BASE, BASE_MODEL, 300)
    for alias in DEPTH_ALIASES.values():
        wait_service(BASE, alias, 30)
    report = {'scope': 'FinQA TRAIN development control. One native call per question and adapter. '
                       'The new depth panels match by source report and table; retention is the original panel.',
              'preparation_sha256': digest_file(preparation_path), 'pair_ids_sha256': pair_digest, 'panels': {}}
    source_effects = {}
    for name, path in paths.items():
        public, gold, panel_identity = panels[name]
        reports = {row['id']: row['report'] for row in public}
        decisions = {}
        entry = {'panel': panel_identity, 'arms': {}}
        for arm in DEPTH_ALIASES:
            local, provenance = collect_and_verify(
                benchmark, f'oda_compact_depth_{arm}_{name}_calibration_v1',
                compact / f'{arm}_serving_profile.json', profiles[arm], path, public, gold, panel_identity, metric_dir)
            decisions[arm] = local
            entry['arms'][arm] = {'native': {**summarize(local), **{
                key: sum(item[key] for item in local) for key in ('known_input_tokens', 'known_output_tokens')}},
                'provenance': provenance}
        balanced, multi_only = (decisions[arm] for arm in DEPTH_ALIASES)
        entry['balanced_vs_multi_only'] = recovery_and_harm(balanced, multi_only)
        entry['paired_tradeoff'] = paired_tradeoff(indexed_outcomes(balanced), indexed_outcomes(multi_only),
                                                   reports.keys(), reports, require_execution=True)
        if name != 'retention':
            source_effects[name] = {reports[first['id']]: int(first['strict'] and first['executable'])
                                    - int(second['strict'] and second['executable'])
                                    for first, second in zip(balanced, multi_only, strict=True)}
        report['panels'][name] = entry
        print(json.dumps({'panel': name, **entry}), flush=True)

    draws = 10000
    examples = [(report_id, {depth: {'delta': source_effects[depth][report_id]} for depth in ('single', 'multi')})
                for report_id in sorted(multi)]
    interaction = paired_effect(examples, (('single', 'delta'), ('multi', 'delta')), draws)
    report['depth_interaction'] = {'contrast': '(balanced - multi_only) on single minus multi, '
                                              'using strict and executable success',
                                   'draws': draws, **{key: interaction[key] for key in (
                                       'n', 'reports', 'net_pp', 'paired_cluster_percentile_95_pp')}}
    freeze(compact / 'calibration_summary.json', report)
    print(json.dumps({'depth_interaction': report['depth_interaction']}), flush=True)


def official_archive(benchmark, public, panel_identity, *, dataset=DATASET):
    """Rebuild the archived official policies so the new comparison uses identical question IDs."""
    from frontier_report import (ODA_METHODS, budget_items, car_items, cascade_items, matched,
                                 selected_action, shared_budgetverify_inputs)
    from run_pilot import load_lines

    root = benchmark / 'official_frontiers_v1'
    archive_path = root / f'{dataset}_frontier.json'
    archive = read(archive_path)
    if (archive['dataset'], archive['n'], archive['panel']) != (dataset, len(public), panel_identity):
        raise ValueError('Archived official frontiers differ from the current panel')
    oda_run = benchmark / 'oda_eval_v1'
    provenance = {name: digest_file(oda_run / name) for name in ('run.json', 'outcomes.jsonl')}
    if provenance != archive['oda']:
        raise ValueError('Archived ODA receipt digests differ')
    car = benchmark / 'car_oda_4096_v1' / dataset / 'eval'
    sources = {name: root / f'{dataset}_{name}.json'
               for name in ('budgetverify_gbm', 'budgetverify_tabfm', 'cascade_raw', 'cascade_compiled')}
    sources['car'] = car / 'outcomes.jsonl'
    if {name: digest_file(path) for name, path in sources.items()} != archive['input_sha256']:
        raise ValueError('Archived official policy input digests differ')
    oda = matched(load_lines(oda_run / 'outcomes.jsonl'), public, 'ODA', dataset)
    draft = {action: {ident: selected_action(row, action) for ident, row in oda.items()} for action in ODA_METHODS}
    policies = {f'oda/{action}': items for action, items in draft.items()}
    policies.update({name: items for name, (items, _) in car_items(
        car, oda, public, dataset, panel_identity, provenance['outcomes.jsonl']).items()})
    gbm, tabfm = (read(sources[f'budgetverify_{name}']) for name in ('gbm', 'tabfm'))
    if shared_budgetverify_inputs(gbm, tabfm) != archive['budgetverify_inputs']:
        raise ValueError('Archived BudgetVerify inputs differ')
    for name, record, method in (('gbm', gbm, 'GBM'), ('tabfm', tabfm, 'TabFM-1.0.0-PyTorch')):
        tiers = budget_items(record, oda, public, dataset, provenance, method)
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


def compact_policies(arm, native, managed):
    return {f'{arm}_native': native, f'{arm}_nonexecution_then_managed': prepend(native, managed),
            f'{arm}_conflict_or_nonexecution_then_managed': prepend(native, managed, forward_conflicts=True)}


def replay_official_canonical(benchmark, compact, public, gold, panel_identity, metric_dir, ledger_digest, managed,
                              *, dataset=DATASET):
    summary_path = compact / f'official_{dataset}_summary.json'
    saved = read(summary_path)
    if saved['panel'] != panel_identity or saved['managed_ledger_sha256'] != ledger_digest:
        raise ValueError('Canonical official summary differs in panel or managed ledger')
    profile_path = compact / 'canonical_serving_profile.json'
    profile = read(profile_path)
    if profile['model'] != ALIASES['canonical'] or profile['base_checkpoint'] != REVISION:
        raise ValueError('Canonical archive uses a different serving identity')
    namespace = ('oda_compact_canonical_tatqa_dev_v1' if dataset == 'tatqa'
                 else 'oda_compact_canonical_finqa_test_v1')
    native, provenance = verify_collection(benchmark / namespace, profile_path, profile, public, gold,
                                           panel_identity, metric_dir, dataset=dataset, check_conflicts=True)
    if provenance != saved['provenance']:
        raise ValueError('Canonical native receipt provenance differs from the published official summary')
    policies = compact_policies('canonical', native, managed)
    fields = ('n', 'strict', 'executable', 'strict_and_executable', 'known_tokens', 'unknown_usage_calls')
    for name, items in policies.items():
        measured = summarize(items)
        if any(measured[key] != saved['policies'][name][key] for key in fields):
            raise ValueError(f'{name}: replayed outcomes differ from the canonical official summary')
    return {name: indexed_outcomes(items) for name, items in policies.items()}, digest_file(summary_path)


def run_official(benchmark, container, metric_dir, *, depth_control=False, dataset=DATASET, source_expansion=False):
    from frontier_report import frontier, summarize as summarize_outcomes
    from paired_tradeoff import paired_tradeoff

    original = benchmark / 'compact_program_development_v1'
    compact = original / 'finqa_depth_control' if depth_control else original
    arm = 'balanced' if depth_control else 'canonical'
    calibration = ('oda_compact_depth_balanced_single_calibration_v1' if depth_control
                   else 'oda_compact_canonical_calibration_v1')
    namespace = f'oda_compact_{arm}_finqa_test_v1'
    panel_name, expected_n, archived_n = 'FinQA test', 1147, 1132
    if source_expansion and (dataset != 'tatqa' or depth_control):
        raise ValueError('Source expansion requires the TAT-QA official panel')
    if dataset == 'tatqa':
        if depth_control:
            raise ValueError('The depth-control official comparison requires FinQA')
        compact = original / 'tatqa_aligned'
        calibration = 'oda_compact_tatqa_canonical_calibration_v1'
        namespace = 'oda_compact_canonical_tatqa_dev_v1'
        panel_name, expected_n, archived_n = 'TAT-QA development arithmetic', 718, 711
        if source_expansion:
            compact /= 'source_expansion_v1'
            arm = 'execution_aligned'
            calibration = 'oda_compact_tatqa_expansion_execution_aligned_calibration_v1'
            namespace = 'oda_compact_tatqa_expansion_execution_aligned_dev_v1'
    panel = benchmark / 'panel' / 'eval'
    public, gold, panel_identity = read_panel(panel, dataset)
    if len(public) != expected_n:
        raise ValueError(f'Expected the complete {expected_n:,}-question official {panel_name} panel')
    reports = {row['id']: row['report'] for row in public}
    root, archive_digest, archived, archive_ids = official_archive(benchmark, reports, panel_identity, dataset=dataset)
    if len(archive_ids) != archived_n:
        raise ValueError(f'Expected the archived {archived_n:,}-question complete-usage and execution cohort')
    ledger = root / 'campus_ledger.json'
    ledger_digest = digest_file(ledger)
    runs = [benchmark / 'oda_eval_v1', *(benchmark / f'campus_eval_{model}_v1'
                                        for model in (campus.QWEN_MODEL, campus.MODEL))]
    pool = read_pool(panel, dataset, runs, representation='compiled', metric_dir=metric_dir, campus_rows=read(ledger))
    managed_arms = {
        'always_qwen-27b': realized(None, pool, initial=1),
        'always_deepseek': realized(None, pool, initial=2),
        'nonexecution_deepseek_qwen': realized(NonexecutionCascade((2, 1)), pool),
    }

    for name, decisions in managed_arms.items():
        expected = archived[f'cascade/compiled/{name}']
        actual = indexed_outcomes(decisions)
        if (len(decisions) != expected_n or actual.keys() != expected.keys() or any(
                actual[ident]._replace(serial_seconds=expected[ident].serial_seconds) != expected[ident]
                or not isclose(actual[ident].serial_seconds, expected[ident].serial_seconds, abs_tol=1e-8)
                for ident in expected)):
            raise ValueError(f'{name}: independently replayed managed decisions differ from the official archive')
    managed = managed_arms['nonexecution_deepseek_qwen']
    by_id = {item['id']: item for item in managed}
    managed = [by_id[ident] for ident in reports]

    canonical_policies, canonical_digest = {}, None
    if depth_control or source_expansion:
        canonical_root = original / 'tatqa_aligned' if source_expansion else original
        canonical_policies, canonical_digest = replay_official_canonical(
            benchmark, canonical_root, public, gold, panel_identity, metric_dir, ledger_digest, by_id,
            dataset=dataset)
    if source_expansion:
        (_, _, calibration_identity), source_identity = tatqa_expansion_inputs(benchmark, compact)
        profiles = tatqa_expansion_profiles(benchmark, compact, container)
        profile = {**profiles[arm], 'source_identity': source_identity}
        calibration_summary = compact / 'calibration_summary.json'
        saved = read(calibration_summary)
        if saved['panel'] != calibration_identity or saved['source_identity'] != source_identity:
            raise ValueError('Expansion calibration does not match the frozen source and panel')
    else:
        profile = serving_profiles(benchmark, compact, container, dataset=dataset, depth_control=depth_control)[arm]
    profile_path = compact / f'{arm}_serving_profile.json'
    if read(profile_path) != profile:
        raise ValueError(f'Official inference requires the exact {arm} calibration serving profile')
    calibrated = read(benchmark / calibration / 'run.json')
    if (calibrated['opencode_sha256'] != digest_file(Path.home() / '.opencode/bin/opencode')
            or calibrated['checkpoint'] != profile['checkpoint'] or calibrated['serve_sha256'] != digest_file(profile_path)):
        raise ValueError(f'Official inference requires the same OpenCode and adapter as {arm} calibration')
    if source_expansion and saved['arms'][arm]['provenance']['files']['run.json'] != digest_file(benchmark / calibration / 'run.json'):
        raise ValueError('Expansion calibration receipt differs from its frozen summary')
    wait_service(BASE, profile['model'], 300)
    native, provenance = collect_and_verify(benchmark, namespace, profile_path, profile, panel, public, gold,
                                            panel_identity, metric_dir, dataset=dataset, check_conflicts=True)
    candidates = compact_policies(arm, native, by_id)
    native_name, base_gate, conflict_gate = candidates
    indexed = {name: indexed_outcomes(items) for name, items in candidates.items()}
    compact_policies_by_id = {**canonical_policies, **indexed}
    ids = [ident for ident in archive_ids
           if all(not items[ident].unknown_usage_calls for items in compact_policies_by_id.values())]
    if not ids:
        raise ValueError('No complete official cost comparisons remain after adding the compact policies')
    points = {name: summarize_outcomes([items[ident] for ident in ids])
              for name, items in {**archived, **compact_policies_by_id}.items()}
    comparator = {**indexed, 'managed_only': indexed_outcomes(managed)}
    contrasts = {}
    for name, baselines in ((native_name, ('managed_only',)), (base_gate, (native_name, 'managed_only')),
                            (conflict_gate, (native_name, base_gate, 'managed_only'))):
        contrasts[name] = {baseline: paired_tradeoff(indexed[name], comparator[baseline], reports.keys(), reports,
                                                     require_execution=True) for baseline in baselines}
    if depth_control or source_expansion:
        for name in candidates:
            previous = name.replace(f'{arm}_', 'canonical_', 1)
            contrasts[name][previous] = paired_tradeoff(indexed[name], canonical_policies[previous],
                                                        reports.keys(), reports, require_execution=True)
            if source_expansion and previous != 'canonical_native':
                contrasts[name]['canonical_native'] = paired_tradeoff(
                    indexed[name], canonical_policies['canonical_native'], reports.keys(), reports,
                    require_execution=True)
    report = {'scope': f'Frozen {arm} adapter on the complete official {panel_name}. Local generation uses '
                       'native calls and replays the existing managed-only paths when the fixed gate fires.',
              'panel': panel_identity, 'archive_sha256': archive_digest,
              'managed_ledger_sha256': ledger_digest, 'provenance': provenance,
              'fixed_gate': 'Escalate on nonexecution or a public grounding explicit conflict.',
              'native_explicit_conflicts': sum(item['explicit_conflict'] for item in native),
              'native_known_input_tokens': sum(item['known_input_tokens'] for item in native),
              'native_known_output_tokens': sum(item['known_output_tokens'] for item in native),
              'policies': {name: {**summarize(items), f'vs_{arm}_native': recovery_and_harm(items, native),
                                  'vs_managed_only': recovery_and_harm(items, managed)}
                           for name, items in candidates.items()},
              'managed': {name: summarize(items) for name, items in managed_arms.items()},
              'paired_tradeoff': contrasts,
              'common_complete_usage_and_execution': {
                  'archived_n': len(archive_ids), 'n': len(ids), 'policies': points,
                  'executable_correct_token_frontier': frontier(points, 'total_tokens', 'strict_and_executable')}}
    if canonical_digest is not None:
        report['canonical_official_summary_sha256'] = canonical_digest
    if source_expansion:
        if (tatqa_expansion_inputs(benchmark, compact)[1] != source_identity
                or tatqa_expansion_profiles(benchmark, compact, container) != profiles):
            raise ValueError('Expansion inputs or serving profile changed during collection')
        report['source_identity'] = source_identity
        report['calibration_summary_sha256'] = digest_file(calibration_summary)
        baseline = canonical_policies['canonical_native']
        for name, items in candidates.items():
            outcomes = indexed[name]
            report['policies'][name]['vs_canonical_native'] = {
                'recoveries': sum(bool(outcomes[i].strict and outcomes[i].executable)
                                  and not bool(baseline[i].strict and baseline[i].executable) for i in reports),
                'harms': sum(bool(baseline[i].strict and baseline[i].executable)
                             and not bool(outcomes[i].strict and outcomes[i].executable) for i in reports)}
    freeze(compact / f'official_{dataset}_summary.json', report)
    print(json.dumps({'policies': report['policies'], 'common_complete_n': len(ids),
                      'token_frontier': report['common_complete_usage_and_execution']['executable_correct_token_frontier']}),
          flush=True)


def report_recovery_fit(student, teacher, reports):
    from benchmark_panels import priority
    from paired_tradeoff import paired_tradeoff

    if [item['id'] for item in student] != [item['id'] for item in teacher]:
        raise ValueError('Expected the same ordered recovery questions for both models')
    peers = {item['id']: item for item in teacher}
    executable = [item for item in student if item['executable']]
    ambiguous = {item['id'] for item in executable if item['ambiguous_literals']}
    conflict = {item['id'] for item in executable if item['explicit_conflict']}
    k = len(ambiguous)
    ranked = sorted(executable, key=lambda item: (not item['explicit_conflict'],
                    priority(DATASET, 'recovery-gate-tie', item['id'])))
    arms = {
        'nonexecution': prepend(student, peers),
        'explicit_conflict': prepend(student, peers, forward_ids=conflict),
        'same_k_conflict_first': prepend(student, peers, forward_ids={item['id'] for item in ranked[:k]}),
        'ambiguous_literal': prepend(student, peers, forward_ids=ambiguous),
        'always_qwen': teacher,
    }
    base = arms['nonexecution']
    probability = k / len(executable) if executable else 0.0
    recoverable = endangered = 0
    for local in executable:
        remote = peers[local['id']]
        correct = remote['strict'] and remote['executable']
        recoverable += not local['strict'] and correct
        endangered += local['strict'] and not correct
    random = {'expected_recoveries': probability * recoverable, 'expected_harms': probability * endangered,
              'expected_correct': summarize(base)['strict_and_executable'] + probability * (recoverable - endangered),
              'expected_known_tokens': sum(item['known_tokens'] for item in base) + probability * sum(
                  peers[item['id']]['known_tokens'] for item in executable),
              'expected_unknown_usage_calls': sum(item['unknown_usage_calls'] for item in base) + probability * sum(
                  peers[item['id']]['unknown_usage_calls'] for item in executable)}
    candidate = indexed_outcomes(arms['ambiguous_literal'])
    contrasts = {name: paired_tradeoff(candidate, indexed_outcomes(arms[name]), reports, reports,
                                      require_execution=True)
                 for name in ('nonexecution', 'same_k_conflict_first', 'always_qwen')}
    return {'n_executable': len(executable), 'k': k, 'explicit_conflict': len(conflict),
            'student': summarize(student),
            'policies': {name: {**summarize(items), 'vs_nonexecution': recovery_and_harm(items, base)}
                         for name, items in arms.items()},
            'same_k_random': random, 'paired_ambiguity_contrasts': contrasts}


def run_tatqa_managed_train(benchmark, container, metric_dir):
    """Fit two public-feature selectors on old TRAIN; replay matched managed receipts."""
    import numpy as np
    from benchmark_panels import priority
    from cohorts import table_signature
    from paired_tradeoff import paired_tradeoff
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    compact = benchmark / 'compact_program_development_v1' / 'tatqa_aligned' / 'source_expansion_v1'
    (_, _, expansion_panel), source_identity = tatqa_expansion_inputs(benchmark, compact)
    profiles = tatqa_expansion_profiles(benchmark, compact, container)
    profile = {**profiles['execution_aligned'], 'source_identity': source_identity}
    profile_path = compact / 'execution_aligned_serving_profile.json'
    calibration = benchmark / 'oda_compact_tatqa_expansion_execution_aligned_calibration_v1' / 'run.json'
    saved = read(compact / 'calibration_summary.json')
    calibrated = read(calibration)
    if (read(profile_path) != profile or saved['source_identity'] != source_identity
            or saved['panel'] != expansion_panel
            or saved['arms']['execution_aligned']['provenance']['files']['run.json'] != digest_file(calibration)
            or calibrated['opencode_sha256'] != digest_file(Path.home() / '.opencode/bin/opencode')
            or calibrated['checkpoint'] != profile['checkpoint']
            or calibrated['serve_sha256'] != digest_file(profile_path)):
        raise ValueError('Managed TRAIN probe requires the matched expansion calibration profile and OpenCode')
    panels = {name: read_panel(benchmark / 'panel' / name, 'tatqa') for name in ('fit', 'calibration')}
    if len(panels['fit'][0]) != 96 or len(panels['calibration'][0]) != 48:
        raise ValueError('Expected the fixed 96 fit and 48 calibration TAT-QA questions')
    fit, check = (panels[name][0] for name in ('fit', 'calibration'))
    if ({r['id'] for r in fit} & {r['id'] for r in check}
            or {r['report'] for r in fit} & {r['report'] for r in check}
            or {table_signature(r['table']) for r in fit} & {table_signature(r['table']) for r in check}):
        raise ValueError('Managed TRAIN fit and calibration sources must be disjoint')
    ledger = benchmark / 'official_frontiers_v1' / 'campus_ledger.json'
    old_runs = {}
    for name in panels:
        old_local = benchmark / ('reconciled_fit_v1/oda_fit_v1' if name == 'fit' else 'oda_calibration_v1')
        old_runs[name] = [old_local, *(benchmark / f'campus_{name}_{model}_v1'
                                       for model in (campus.QWEN_MODEL, campus.MODEL))]
    old_digests = {name: [{file: digest_file(path / file) for file in ('run.json', 'outcomes.jsonl')}
                          for path in paths] for name, paths in old_runs.items()}
    contract = {'schema': 'tatqa-expansion-managed-train-v1', 'dataset': 'tatqa',
                'script_sha256': digest_file(Path(__file__)),
                'panels': {name: panel[2] for name, panel in panels.items()},
                'source_identity': source_identity, 'serving_profile_sha256': digest_file(profile_path),
                'calibration_sha256': digest_file(calibration), 'campus_ledger_sha256': digest_file(ledger),
                'managed_and_old_local_runs': old_digests,
                'features': list(MANAGED_RESCUE_FEATURES), 'estimator': 'StandardScaler + Ridge(alpha=4)',
                'targets': {'gain': 'C(deepseek)-C(local)', 'risk': '1-C(local)'},
                'training_scope': 'Only locally executable fit states; C means strict and executable.',
                'selection': 'Top 12 executable local states by score; fixed source-hash tie break.',
                'fallback': 'Nonexecution uses the archived DeepSeek then Qwen route; selected executable '
                            'states use one archived DeepSeek response only.'}
    contract_path = compact / 'managed_train_rescue_contract.json'
    freeze(contract_path, contract)
    ledger_rows = read(ledger)
    runs, pools, provenance = {}, {}, {}
    for name in panels:
        pools[name] = read_pool(benchmark / 'panel' / name, 'tatqa', old_runs[name], representation='compiled',
                                metric_dir=metric_dir, campus_rows=ledger_rows)
    wait_service(BASE, profile['model'], 300)
    for name, (public, gold, panel_identity) in panels.items():
        namespace = f'oda_compact_tatqa_expansion_managed_{name}_v1'
        runs[name], provenance[name] = collect_and_verify(
            benchmark, namespace, profile_path, profile, benchmark / 'panel' / name, public, gold,
            panel_identity, metric_dir, dataset='tatqa', capture_features=True)
    if (tatqa_expansion_inputs(benchmark, compact)[1] != source_identity
            or tatqa_expansion_profiles(benchmark, compact, container) != profiles
            or digest_file(ledger) != contract['campus_ledger_sha256']
            or {name: [{file: digest_file(path / file) for file in ('run.json', 'outcomes.jsonl')}
                       for path in paths] for name, paths in old_runs.items()} != old_digests):
        raise ValueError('Frozen expansion or managed source changed during collection')

    teacher_fit = {item['id']: item for item in realized(None, pools['fit'], initial=2)}
    fit_local = [item for item in runs['fit'] if item['executable']]
    if len(fit_local) < 2 or set(teacher_fit) != {r['id'] for r in fit}:
        raise ValueError('Insufficient matched executable fit states')
    x = np.asarray([item['public_features'] for item in fit_local], dtype=float)
    current = np.asarray([int(item['strict'] and item['executable']) for item in fit_local])
    teacher = np.asarray([int(teacher_fit[item['id']]['strict'] and teacher_fit[item['id']]['executable'])
                          for item in fit_local])
    models = {name: make_pipeline(StandardScaler(), Ridge(alpha=4)).fit(x, target)
              for name, target in (('gain', teacher - current), ('risk', 1 - current))}
    public, _, panel_identity = panels['calibration']
    reports = {row['id']: row['report'] for row in public}
    local = runs['calibration']
    eligible = [item for item in local if item['executable']]
    if len(eligible) < 12:
        raise ValueError('Fewer than twelve executable calibration states; no top-12 comparison')
    matrix = np.asarray([item['public_features'] for item in eligible], dtype=float)
    teacher_rows = realized(None, pools['calibration'], initial=2)
    teacher_by_id = {item['id']: item for item in teacher_rows}
    managed_rows = realized(NonexecutionCascade((2, 1)), pools['calibration'])
    managed = {item['id']: item for item in managed_rows}
    if teacher_by_id.keys() != reports.keys() or managed.keys() != reports.keys():
        raise ValueError('Matched managed receipts must cover every calibration question')
    baseline = prepend(local, managed)
    p = lambda ident: priority('tatqa', 'managed-rescue-tie-v1', ident)
    selected = {}
    for name, model in models.items():
        scores = model.predict(matrix)
        selected[name] = {item['id'] for _, item in sorted(
            zip(scores, eligible, strict=True), key=lambda pair: (-pair[0], p(pair[1]['id'])))[:12]}
    selected['conflict_first'] = {item['id'] for item in sorted(
        eligible, key=lambda item: (not item['explicit_conflict'], p(item['id'])))[:12]}

    policies = {'nonexecution': baseline, 'direct_deepseek': teacher_rows}
    for name, ids in selected.items():
        redirected = prepend(local, teacher_by_id, forward_ids=ids)
        policies[name] = [redirect if item['id'] in ids else original
                          for item, redirect, original in zip(local, redirected, baseline, strict=True)]
    report_policies = {name: {**summarize(items), 'vs_nonexecution': recovery_and_harm(items, baseline),
                              'vs_direct_deepseek': recovery_and_harm(items, teacher_rows)}
                       for name, items in policies.items()}
    contrasts = {name: {other: paired_tradeoff(indexed_outcomes(policies[name]), indexed_outcomes(policies[other]),
                                                reports.keys(), reports, require_execution=True)
                        for other in ('nonexecution', 'direct_deepseek')}
                 for name in selected}
    for other in ('risk', 'conflict_first'):
        contrasts['gain'][other] = paired_tradeoff(indexed_outcomes(policies['gain']), indexed_outcomes(policies[other]),
                                                   reports.keys(), reports, require_execution=True)
    probability = 12 / len(eligible)
    base_summary = summarize(baseline)
    recovered = sum(not item['strict'] and teacher_by_id[item['id']]['strict']
                    and teacher_by_id[item['id']]['executable'] for item in eligible)
    harmed = sum(item['strict'] and not (teacher_by_id[item['id']]['strict']
                                        and teacher_by_id[item['id']]['executable']) for item in eligible)
    unknown = base_summary['unknown_usage_calls'] + probability * sum(
        teacher_by_id[item['id']]['unknown_usage_calls'] for item in eligible)
    uniform = {'n': len(local), 'k': 12, 'eligible': len(eligible),
               'expected_recoveries': probability * recovered, 'expected_harms': probability * harmed,
               'expected_strict_and_executable': base_summary['strict_and_executable'] + probability * (recovered - harmed),
               'expected_known_tokens': base_summary['known_tokens'] + probability * sum(
                   teacher_by_id[item['id']]['known_tokens'] for item in eligible),
               'expected_unknown_usage_calls': unknown,
               'expected_total_tokens': None if unknown else base_summary['known_tokens'] + probability * sum(
                   teacher_by_id[item['id']]['known_tokens'] for item in eligible)}
    gain_result, direct_result = report_policies['gain'], report_policies['direct_deepseek']
    transition = gain_result['vs_nonexecution']
    net = transition['recoveries'] - transition['harms']
    if not gain_result['unknown_usage_calls'] and gain_result['known_tokens'] <= direct_result['known_tokens']:
        cost_compatible = True  # Direct known tokens are a lower bound even with unknown usage.
    elif not gain_result['unknown_usage_calls'] and not direct_result['unknown_usage_calls']:
        cost_compatible = False
    else:
        cost_compatible = None
    verdict = {'net_recoveries_vs_nonexecution': net, 'required_net_recoveries': 7,
               'cost_compatible_with_direct_deepseek': cost_compatible,
               'meets_joint_condition': False if net < 7 or cost_compatible is False else
                                        True if cost_compatible is True else None,
               'cost_scope': 'Known recorded tokens only; unknown usage prevents treating a lower bound as a total.'}
    report = {'scope': 'Frozen TRAIN fit/calibration development; managed calls replayed, no new campus calls.',
              'contract_sha256': digest_file(contract_path), 'panel': panel_identity,
              'local_provenance': provenance, 'fit_executable_n': len(fit_local),
              'fit_target_counts': {'gain_positive': int(sum(teacher > current)),
                                    'gain_negative': int(sum(teacher < current)), 'local_incorrect': int(sum(1 - current))},
              'models': {name: {'mean': model[0].mean_.tolist(), 'scale': model[0].scale_.tolist(),
                                'coefficient': model[1].coef_.tolist(), 'intercept': float(model[1].intercept_)}
                         for name, model in models.items()},
              'selected_ids': {name: sorted(ids) for name, ids in selected.items()},
              'policies': report_policies, 'paired_tradeoff': contrasts, 'uniform_k12': uniform,
              'seven_net_cost_verdict': verdict}
    freeze(compact / 'managed_train_rescue_summary.json', report)
    print(json.dumps({'policies': report_policies, 'uniform_k12': uniform}), flush=True)


def collect_recovery_fit(benchmark, container, metric_dir):
    development = benchmark / 'compact_program_development_v1'
    recovery = development / 'finqa_recovery_pairs'
    panel = recovery / 'panel' / 'fit'
    public, gold, identity = read_panel(panel, DATASET)
    manifest = read(recovery / 'manifest.json')
    if (manifest['schema'] != 'finqa-train-recovery-pairs-v1'
            or manifest['panels']['fit']['sha256'] != identity
            or manifest['panels']['fit']['n'] != len(public) or len(public) != 96):
        raise ValueError('Expected the frozen FinQA recovery fit panel')
    teacher_profile = recovery / 'local_qwen27b_serving_profile.json'
    teacher, teacher_provenance = verify_collection(
        benchmark / 'qwen27b_local_finqa_recovery_fit_v1', teacher_profile, read(teacher_profile),
        public, gold, identity, metric_dir, disable_thinking=False,
    )
    compact = development / 'finqa_depth_control'
    profile = serving_profiles(benchmark, compact, container, depth_control=True)['balanced']
    profile_path = compact / 'balanced_serving_profile.json'
    calibration = read(benchmark / 'oda_compact_depth_balanced_single_calibration_v1' / 'run.json')
    if (read(profile_path) != profile or calibration['serve_sha256'] != digest_file(profile_path)
            or calibration['opencode_sha256'] != digest_file(Path.home() / '.opencode/bin/opencode')):
        raise ValueError('Recovery fit requires the balanced FinQA calibration model and OpenCode')
    wait_service(BASE, profile['model'], 300)
    decisions, provenance = collect_and_verify(
        benchmark, 'oda_compact_balanced_finqa_recovery_fit_v1', profile_path, profile,
        panel, public, gold, identity, metric_dir, check_conflicts=True, measure_wall=True,
    )
    reports = {row['id']: row['report'] for row in public}
    report = report_recovery_fit(decisions, teacher, reports)
    report.update(panel=identity, student_provenance=provenance, teacher_provenance=teacher_provenance)
    freeze(recovery / 'fit_summary.json', report)
    print(json.dumps(report), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--container', required=True)
    parser.add_argument('--metric-dir', type=Path, required=True)
    parser.add_argument('--stage', choices=('calibration', 'official-finqa', 'official-tatqa',
                                           'depth-calibration', 'official-finqa-depth', 'recovery-fit',
                                           'tatqa-expansion-calibration', 'official-tatqa-expansion',
                                           'tatqa-expansion-managed-train'),
                        default='calibration')
    parser.add_argument('--dataset', choices=(DATASET, 'tatqa'), default=DATASET)
    args = parser.parse_args()
    if re.fullmatch(r'[0-9a-f]{12,64}', args.container) is None:
        parser.error('--container must be a Docker container ID')
    benchmark, metric = args.benchmark.resolve(), args.metric_dir.resolve()
    if args.stage == 'calibration':
        run(benchmark, args.container, metric, dataset=args.dataset)
    else:
        expected = 'tatqa' if args.stage in ('official-tatqa', 'tatqa-expansion-calibration',
                                             'official-tatqa-expansion', 'tatqa-expansion-managed-train') else DATASET
        if args.dataset != expected:
            parser.error(f'--stage {args.stage} requires --dataset {expected}')
        if args.stage == 'depth-calibration':
            run_depth(benchmark, args.container, metric)
        elif args.stage == 'tatqa-expansion-calibration':
            run_tatqa_expansion(benchmark, args.container, metric)
        elif args.stage == 'tatqa-expansion-managed-train':
            run_tatqa_managed_train(benchmark, args.container, metric)
        elif args.stage == 'recovery-fit':
            collect_recovery_fit(benchmark, args.container, metric)
        else:
            run_official(benchmark, args.container, metric, dataset=args.dataset,
                         depth_control=args.stage == 'official-finqa-depth',
                         source_expansion=args.stage == 'official-tatqa-expansion')


if __name__ == '__main__':
    main()
