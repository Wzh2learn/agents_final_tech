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
        result['contrasts'] = contrasts(public, read(args.root / 'outcomes.json'), result['cluster_bootstrap_draws'])
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
