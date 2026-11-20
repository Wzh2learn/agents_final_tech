"""Separate delivery failures from scoring contrasts in the frozen pilot receipts."""

import argparse
from collections import Counter, defaultdict
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--receipts-only', action='store_true')
    args = parser.parse_args()
    public = [json.loads(line) for line in (args.root / 'panel/public.jsonl').read_text(encoding='utf-8').splitlines()]
    result = {'receipts': receipt_counts(args.root, public)}
    if not args.receipts_only:
        result['cluster_bootstrap_draws'] = 10000
        outcomes = read(args.root / 'outcomes.json')
        result['contrasts'] = contrasts(public, outcomes, result['cluster_bootstrap_draws'])
        result['teacher_recovery_sensitivity'] = teacher_recovery_sensitivity(args.root, public, outcomes)
        result['representation_fallback'] = representation_fallback(args.root, public, outcomes)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
