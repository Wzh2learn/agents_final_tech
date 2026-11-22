"""Separate delivery failures from scoring contrasts in the frozen pilot receipts."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from random import Random


METRICS = {
    'official_free_minus_dsl_pp': (('free', 'strict'), ('dsl', 'strict')),
    'normalization_minus_dsl_pp': (('dsl', 'norm'), ('dsl', 'strict')),
    'normalization_minus_public_rule_pp': (('dsl', 'norm'), ('dsl', 'rule')),
    'free_minus_dsl_after_normalization_pp': (('free', 'norm'), ('dsl', 'norm')),
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def receipt_counts(root, public):
    counts = defaultdict(Counter)
    for index, row in enumerate(public):
        dataset = row['dataset']
        case = root / 'calls' / dataset / f'{index:03d}'
        for arm in ('free', 'dsl', 'reverse', 'teacher'):
            path = case / arm / 'call.json'
            if not path.is_file():
                continue
            call = read(path)
            measured = counts[dataset, arm]
            reached_cap = 'length' in call['finish']
            delivered = bool(call['text'].strip())
            infrastructure_error = bool(call['exit_code'] or call['errors'])
            measured.update({
                'completed_receipts': 1,
                'delivered_text': delivered,
                'output_cap': reached_cap,
                'no_text_at_cap': reached_cap and not delivered,
                'no_text_other': not reached_cap and not delivered,
                'execution_error': infrastructure_error,
                'no_usage': call['usage'] is None,
            })
    return {dataset: {arm: dict(counts[dataset, arm]) for arm in ('free', 'dsl', 'reverse', 'teacher')}
            for dataset in ('finqa', 'tatqa')}


def paired_effect(examples, columns, draws):
    left, right = columns
    groups = defaultdict(list)
    for report, row in examples:
        groups[report].append(int(row[left[0]][left[1]]) - int(row[right[0]][right[1]]))
    differences = [delta for values in groups.values() for delta in values]
    clusters = [(sum(values), len(values)) for values in groups.values()]
    rng = Random(20261119)
    estimates = []
    for _ in range(draws):
        selected = rng.choices(clusters, k=len(clusters))
        numerator = sum(delta for delta, _ in selected)
        denominator = sum(size for _, size in selected)
        estimates.append(100 * numerator / denominator)
    estimates.sort()
    return {'n': len(differences), 'reports': len(clusters),
            'gains': differences.count(1), 'losses': differences.count(-1),
            'net_pp': 100 * sum(differences) / len(differences),
            'paired_cluster_percentile_95_pp': [estimates[int(.025 * (draws - 1))],
                                                estimates[int(.975 * (draws - 1))]]}


def grounding_lift(examples):
    from grounding import parse_verifier
    from run_pilot import rank_auc

    covered = []
    for _, row in examples:
        if row.get('reverse_risk') is None:
            continue
        rules = parse_verifier(None, row['grounding']['bindings'])['risk_score']
        covered.append((row, rules))
    wrong = [(row, rules) for row, rules in covered if not row['dsl']['strict'] and row.get('teacher')]
    panels = {'error_detection': (covered, [not row['dsl']['strict'] for row, _ in covered]),
              'teacher_recovery': (wrong, [row['teacher']['strict'] for row, _ in wrong])}
    return {name: {'n': len(pairs), 'positives': sum(labels),
                   'rules_auc': rank_auc([rules for _, rules in pairs], labels),
                   'rules_and_verifier_auc': rank_auc([row['reverse_risk'] for row, _ in pairs], labels)}
            for name, (pairs, labels) in panels.items()}


def recovery_panel(examples, signals):
    from run_pilot import rank_auc

    def auc(rows, signal):
        labels = [case['recovered'] for case in rows]
        return {'n': len(rows), 'positives': sum(labels),
                'auc': rank_auc([case['scores'][signal] for case in rows], labels)}

    common = [case for case in examples if all(case['scores'][signal] is not None for signal in signals)]
    return {
        'n': len(examples),
        'recovered': sum(case['recovered'] for case in examples),
        'covered': {signal: auc([case for case in examples if case['scores'][signal] is not None], signal)
                    for signal in signals},
        'common': {signal: auc(common, signal) for signal in signals},
    }


def representation_fallback(root, public, outcomes):
    """Replay two public failure gates with each requested generation charged."""
    indexed = {(row['dataset'], row['id']): row for row in outcomes}
    paired = defaultdict(Counter)
    policies = defaultdict(lambda: defaultdict(Counter))
    for idx, example in enumerate(public):
        dataset = example['dataset']
        row = indexed[dataset, example['id']]
        free, dsl = row['free'], row['dsl']
        path = root / 'calls' / dataset / f'{idx:03d}'
        missing_free = free['normalized_answer'] is None
        failed_dsl = not dsl['executable']
        paired[dataset][f'free_{int(free["strict"])}_dsl_{int(dsl["strict"])}'] += 1
        usage = {arm: read(path / arm / 'call.json')['usage'] for arm in ('free', 'dsl')}
        for key, result, arms in (
            ('free', free, ('free',)),
            ('dsl', dsl, ('dsl',)),
            ('free_then_dsl_on_missing', dsl if missing_free else free,
             ('free', 'dsl') if missing_free else ('free',)),
            ('dsl_then_free_on_nonexecution', free if failed_dsl else dsl,
             ('dsl', 'free') if failed_dsl else ('dsl',)),
        ):
            counts = policies[dataset][key]
            counts['strict_correct'] += int(result['strict'])
            for arm in arms:
                tokens = usage[arm]
                counts['calls'] += 1
                counts['unknown_usage'] += tokens is None
                if tokens is not None:
                    counts['known_tokens'] += tokens.get('total') or tokens['input'] + tokens['output']
    return {
        'scope': 'Post-hoc replay of completed paired calls. No online cascade timing is estimated.',
        'datasets': {dataset: {'n': sum(counts.values()), 'paired_correctness': dict(counts),
                               'policies': policies[dataset]} for dataset, counts in paired.items()},
    }


def finqa_teacher_ratio_replay(root, public, outcomes):
    from run_pilot import load_lines
    from scoring import finqa_ratio_rule, score

    indexed = {(row['dataset'], row['id']): row for row in outcomes}
    gold = {row['id']: row['gold'] for row in load_lines(root / 'panel/references.jsonl')
            if row['dataset'] == 'finqa'}
    first, teacher = Counter(), defaultdict(Counter)
    remaining = []
    signals = ('initial_nonexecution', 'reverse_risk', 'representation_disagreement', 'legacy_risk', 'legacy_value')

    def amended(example, original):
        submission = finqa_ratio_rule(example, original, original['execution'])
        if submission is None:
            return original['strict'], False
        return score(example, submission, gold=gold[example['id']])['strict'], True

    for idx, example in enumerate(public):
        if example['dataset'] != 'finqa':
            continue
        row = indexed['finqa', example['id']]
        original = row['dsl']
        local, applied = amended(example, original)
        first.update({'n': 1, 'strict': original['strict'], 'factor_normalized': original['norm'],
                      'rule': local, 'rule_applied': applied, 'recovered': local and not original['strict'],
                      'harmed': original['strict'] and not local})
        if row.get('teacher') is None:
            continue
        call = read(root / 'calls/finqa' / f'{idx:03d}' / 'teacher/call.json')
        delivered = bool(call['text'].strip()) and not (call['exit_code'] or call['errors'])
        corrected, rule = amended(example, row['teacher']) if delivered else (False, False)
        subset = 'local_rule_recovered' if local else 'remaining_after_local_rule'
        if not local:
            scores = {signal: row.get(signal) for signal in signals}
            scores['initial_nonexecution'] = int(not original['executable'])
            remaining.append({'scores': scores, 'recovered': corrected})
        for scope in ('all_first_pass_errors', subset):
            teacher[scope].update({'attempted': 1, 'delivered': delivered,
                                   'strict': delivered and row['teacher']['strict'],
                                   'factor_normalized': delivered and row['teacher']['norm'],
                                   'rule': corrected, 'rule_applied': rule})
    return {'scope': 'Post-hoc same-rule replay, with teacher called only on original strict misses.',
            'local': first, 'teacher': teacher, 'remaining_after_local_rule': first['n'] - first['rule'],
            'remaining_without_teacher': first['n'] - first['rule'] - teacher['remaining_after_local_rule']['attempted'],
            'remaining_recovery_auc_after_teacher_rule': recovery_panel(remaining, signals)}


def teacher_recovery_sensitivity(root, public, outcomes):
    """Keep failed teacher attempts in the end-to-end panel, then condition on delivery."""
    indexed = {(row['dataset'], row['id']): row for row in outcomes}
    cases = defaultdict(list)
    wrong = Counter()
    signals = ('reverse_risk', 'representation_disagreement', 'legacy_risk', 'legacy_value')
    for idx, public_row in enumerate(public):
        dataset = public_row['dataset']
        wrong.setdefault(dataset, 0)
        row = indexed[dataset, public_row['id']]
        if row['dsl']['strict']:
            continue
        wrong[dataset] += 1
        path = root / 'calls' / dataset / f'{idx:03d}' / 'teacher/call.json'
        teacher = row.get('teacher')
        if path.is_file() != (teacher is not None):
            raise ValueError(f'teacher receipt/outcome mismatch for {dataset}:{idx}')
        if teacher is None:
            continue
        receipt = read(path)
        call_error = bool(receipt['exit_code'] or receipt['errors'])
        error_text = json.dumps(receipt['errors']).casefold()
        timed_out = receipt['exit_code'] == 124 or 'timed out' in error_text or 'timeouterror' in error_text
        has_text = bool(receipt['text'].strip())
        delivered = has_text and not call_error
        scores = {signal: row.get(signal) for signal in signals}
        scores['initial_nonexecution'] = int(not row['dsl']['executable'])
        cases[dataset].append({
            'scores': scores,
            'recovered': delivered and bool(teacher['strict']),
            'recorded_strict': bool(teacher['strict']),
            'call_error': call_error,
            'timeout': timed_out,
            'has_text': has_text,
            'delivered': delivered,
            'executable': delivered and bool(teacher['executable']),
        })
    result = {}
    for dataset in sorted(wrong):
        attempts = cases[dataset]
        active = ('initial_nonexecution', *(signal for signal in signals
                                              if any(case['scores'][signal] is not None for case in attempts)))
        result[dataset] = {
            'all_initial_strict_errors': wrong[dataset],
            'unattempted_errors': wrong[dataset] - len(attempts),
            'call_errors': sum(case['call_error'] for case in attempts),
            'timeouts': sum(case['timeout'] for case in attempts),
            'no_final_text': sum(not case['has_text'] for case in attempts),
            'recorded_strict_matches': sum(case['recorded_strict'] for case in attempts),
            'all_attempted': recovery_panel(attempts, active),
            'delivered_without_call_error': recovery_panel([case for case in attempts if case['delivered']], active),
            'executable_teacher': recovery_panel([case for case in attempts if case['executable']], active),
        }
    return {
        'outcome': 'Teacher official match with delivered text, zero exit status and no recorded call error.',
        'conditioning': 'All attempted retains call failures and nonexecutable replies. The other panels require delivery without call error or additionally a teacher program that executes.',
        'auc_direction': 'Larger scores predict teacher recovery. Initial nonexecution is 1 for an initial DSL program that did not execute.',
        'datasets': result,
    }


def contrasts(public, outcomes, draws):
    reports = {(row['dataset'], row['id']): row['report'] for row in public}
    if set(reports) != {(row['dataset'], row['id']) for row in outcomes} or len(reports) != len(outcomes):
        raise ValueError('completed outcomes and frozen panel differ')
    data = defaultdict(list)
    for row in outcomes:
        data[row['dataset']].append((reports[row['dataset'], row['id']], row))
    results = {}
    for dataset, examples in data.items():
        comparisons = {name: paired_effect(examples, columns, draws) for name, columns in METRICS.items()}
        dsl_errors = [row for _, row in examples if not row['dsl']['strict']]
        known_teacher = [row for row in dsl_errors if row.get('teacher') is not None]
        executable_errors = [row for row in known_teacher if row['dsl']['executable']]
        teacher_recovery = {'all_strict_errors': len(dsl_errors), 'attempted_errors': len(known_teacher),
                            'recovered_errors': sum(row['teacher']['strict'] for row in known_teacher),
                            'attempted_executable_errors': len(executable_errors),
                            'recovered_executable_errors': sum(row['teacher']['strict'] for row in executable_errors)}
        results[dataset] = {'comparisons': comparisons, 'teacher_recovery': teacher_recovery,
                            'grounding_paired_auc': grounding_lift(examples)}
    return results


def read_paired_run(directory, panel_digest, reports, dataset, action):
    from benchmark_actions import digest_file
    from run_pilot import load_lines

    contract_path = directory / 'run.json'
    contract = read(contract_path)
    if (contract['schema'] != 'finance-benchmark-actions-v1'
            or contract['dataset'] not in (None, dataset)
            or action not in contract['actions']
            or contract['panel'] != panel_digest):
        raise ValueError(f'{directory}: action run does not match the frozen panel')

    outcomes_path = directory / 'outcomes.jsonl'
    completed = load_lines(outcomes_path)
    selected = [row for row in completed if row['dataset'] == dataset]
    indexed = {row['id']: row for row in selected}
    if (len(indexed) != len(selected) or indexed.keys() != reports.keys()
            or any(row['report'] != reports[ident] for ident, row in indexed.items())
            or (contract['dataset'] == dataset and len(selected) != len(completed))):
        raise ValueError(f'{directory}: completed outcomes must cover frozen IDs and reports exactly once')

    profile = {key: value for key, value in contract.items()
               if key not in ('namespace', 'panel', 'dataset', 'actions')}
    required = {'model', 'checkpoint', 'endpoint', 'serve_sha256', 'opencode_sha256',
                'seed', 'context', 'output', 'temperature'}
    if not required <= profile.keys() or 'solve' not in profile['output']:
        raise ValueError(f'{directory}: incomplete serving profile')
    return profile, indexed, {path.name: digest_file(path) for path in (contract_path, outcomes_path)}


def read_replay_call(directory, row, name, actor, prompt, run_digest, metadata):
    from run_pilot import call_fields_from_raw

    case = sha256(row['id'].encode('utf-8')).hexdigest()[:24]
    relative = Path('calls') / row['dataset'] / case / name
    expected_request = {'prompt_sha256': sha256(prompt.encode('utf-8')).hexdigest(),
                        'run_contract': run_digest, 'actor': actor}
    target = directory / relative
    if (metadata['path'] != (relative / 'call.json').as_posix()
            or read(target / 'request.json') != expected_request
            or (target / 'prompt.txt').read_bytes() != (prompt + '\n').encode('utf-8')):
        raise ValueError(f'{target}: recorded prompt or request differs from the frozen arm')
    receipt = read(target / 'call.json')
    replayed = call_fields_from_raw((target / 'raw.jsonl').read_bytes())
    if (any(receipt[key] != value for key, value in replayed.items())
            or any(metadata[key] != receipt[key]
                   for key in ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors'))):
        raise ValueError(f'{target}: raw events, call receipt or recorded usage disagree')
    return receipt


def compare_nested(panel: Path, flat_run: Path, nested_run: Path, dataset: str,
                   metric_dir: Path | None = None) -> dict:
    """Rescore two matched one-call representations from frozen local receipts."""
    from benchmark_actions import action_cost, collect_case, deliver, read_panel

    if flat_run.resolve() == nested_run.resolve():
        raise ValueError('Flat and nested receipts require separate run directories')
    if dataset == 'tatqa' and metric_dir is None:
        raise ValueError('TAT-QA requires the official metric directory')
    public, gold, panel_digest = read_panel(panel, dataset)
    reports = {row['id']: row['report'] for row in public}
    specs = ((flat_run, 'contract_compile', 'low'), (nested_run, 'nested_compile', 'nested_compile'))
    runs = [read_paired_run(run, panel_digest, reports, dataset, action) for run, action, _ in specs]
    if runs[0][0] != runs[1][0]:
        raise ValueError('Flat and nested serving profiles differ')

    summaries = defaultdict(Counter)
    paired = []
    for row in public:
        outcomes = {}
        for (run, action, expected_call), (_, indexed, provenance) in zip(specs, runs):
            saved = indexed[row['id']]
            receipts = {}

            def call(name, actor, prompt):
                if name != expected_call or actor != 'solve' or receipts:
                    raise ValueError(f'{run}: unexpected call plan for {row["id"]}')
                receipts[name] = read_replay_call(run, row, name, actor, prompt,
                                                  provenance['run.json'], saved['calls'][name])
                return receipts[name]

            replayed = collect_case(row, gold[dataset, row['id']], [action], call, metric_dir)
            receipt = receipts[expected_call]
            for arm, output in replayed.items():
                if output['calls'] != [expected_call]:
                    raise ValueError(f'{run}: {arm} must charge only its single solve call')
                cost = action_cost([receipt])
                if saved['actions'][arm] != {**output, 'cost': cost}:
                    raise ValueError(f'{run}: recorded score or cost differs for {row["id"]} {arm}')
                summaries[arm].update(n=1, strict_correct=output['strict'], executable=output['executable'],
                                      delivered=bool(deliver(receipt).strip()),
                                      call_errors=bool(receipt['exit_code'] or receipt['errors']),
                                      output_cap='length' in receipt['finish'],
                                      known_tokens=cost['known_tokens'], unknown_usage_calls=cost['unknown_usage_calls'],
                                      summed_call_seconds=cost['summed_call_seconds'])
            outcomes.update(replayed)
        paired.append((row['report'], outcomes))

    draws = 10000
    return {
        'scope': 'One solve attempt per representation. Raw and compiled share the flat receipt. '
                 'Elapsed values sum per-question call duration, without estimating batch wall time.',
        'dataset': dataset, 'panel': panel_digest, 'profile': runs[0][0],
        'provenance': {'flat': runs[0][2], 'nested': runs[1][2]},
        'arms': summaries, 'cluster_bootstrap_draws': draws,
        'comparisons': {
            f'nested_minus_{baseline}': paired_effect(paired, (('nested_compile', 'strict'), (baseline, 'strict')), draws)
            for baseline in ('low', 'contract_compile')
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--receipts-only', action='store_true')
    parser.add_argument('--compare-nested', type=Path, nargs=2, metavar=('FLAT_RUN', 'NESTED_RUN'),
                        help='Compare completed runs on the frozen panel directory given by --root')
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'))
    parser.add_argument('--metric-dir', type=Path)
    args = parser.parse_args()
    if args.compare_nested:
        if args.receipts_only or args.dataset is None or (args.dataset == 'tatqa' and args.metric_dir is None):
            parser.error('nested comparison requires --dataset, --metric-dir for tatqa, and scoring enabled')
        result = compare_nested(args.root, *args.compare_nested, args.dataset, args.metric_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return
    if args.dataset or args.metric_dir:
        parser.error('--dataset and --metric-dir apply only to nested comparison')
    public = [json.loads(line) for line in (args.root / 'panel/public.jsonl').read_text(encoding='utf-8').splitlines()]
    result = {'receipts': receipt_counts(args.root, public)}
    if not args.receipts_only:
        result['cluster_bootstrap_draws'] = 10000
        outcomes = read(args.root / 'outcomes.json')
        result['contrasts'] = contrasts(public, outcomes, result['cluster_bootstrap_draws'])
        result['teacher_recovery_sensitivity'] = teacher_recovery_sensitivity(args.root, public, outcomes)
        result['representation_fallback'] = representation_fallback(args.root, public, outcomes)
        result['finqa_teacher_ratio_replay'] = finqa_teacher_ratio_replay(args.root, public, outcomes)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
