"""Fit and replay BudgetVerify routes from same-checkpoint OpenCode receipts.

This adaptation follows section 3.2 with local DSL features and a declared
lambda grid. Generator confidence and explicit evidence fields are unavailable.
The generator's executed answer and operand mentions supply observable proxies.
https://arxiv.org/html/2609.33052v1#S3
"""

import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path
import re
from time import perf_counter

import numpy as np

from benchmark_actions import action_cost, digest_file, observable
from benchmark_panels import identity_keys
from grounding import NUMBER_SPAN, YEAR
from run_pilot import PUBLIC_FIELDS, load_lines, write_json
from scoring import OPERATION


TIERS = ('low', 'mid', 'high')
SPLITS = ('fit', 'calibration', 'eval')
LAMBDAS = (0, .001, .002, .003, .005, .0075, .01, .015, .02, .025, .03, .04, .05,
           .06, .08, .10, .125, .15, .20, .25, .30, .40, .50, .65, .80, 1.0)
GBM_GRID = ({'max_depth': 1, 'n_estimators': 50}, {'max_depth': 2, 'n_estimators': 50},
            {'max_depth': 2, 'n_estimators': 100}, {'max_depth': 3, 'n_estimators': 100})
OPERATIONS = OPERATION.split('|')
PERIOD = re.compile(rf'{YEAR.pattern}|\bQ[1-4]\b', re.I)
CUES = {
    'percent': r'%|\bpercent(?:age)?\b', 'currency': r'[$€£]|\b(?:dollars?|USD|EUR|GBP)\b',
    'calculation': r'\b(?:increase|decrease|growth|difference|change|ratio|margin|sum|average)\b',
    'comparison': r'\b(?:higher|lower|greater|less|largest|smallest|compare|versus)\b',
    'finance': r'\b(?:revenue|income|expense|assets|cash|debt|equity|profit|loss)\b',
    'ratio': r'\b(?:ratio|portion|share|of total|percentage of)\b',
    'margin': r'\bmargin\b', 'lookup': r'\b(?:what was|how much was|amount of)\b',
    'signed_change': r'\b(?:decline|decrease|fell|change)\b',
}


def features(public, draft):
    """Read public text and Low's parsed answer before invoking any verifier."""
    question = public['question']
    table = public['table']
    serialized = '\n'.join([*public['pre_text'], *(' | '.join(map(str, row)) for row in table),
                            *public['post_text']])
    cue = {name: int(bool(re.search(pattern, question, re.I))) for name, pattern in CUES.items()}
    question_periods = len({match.group().casefold() for match in PERIOD.finditer(question)})
    number_count = len(NUMBER_SPAN.findall(serialized))
    steps = re.findall(rf'\b({OPERATION})\s*\(', draft['program'] or '')
    evidence = observable(public, draft)
    bindings = evidence['bindings']
    execution = evidence['execution']
    answer = execution.get('terminal_execution_answer') if execution['status'] == 'executed' else None
    numeric = int(type(answer) in (int, float))
    scale = draft['scale']
    located = sum(bool(item['match_count']) for item in bindings)
    return {
        'question_words': len(question.split()), 'question_chars': len(question),
        'question_numbers': len(NUMBER_SPAN.findall(question)), 'question_periods': question_periods,
        **cue,
        'context_chars': len(serialized), 'context_words': len(serialized.split()),
        'context_numbers': number_count, 'context_number_density': number_count / max(len(serialized.split()), 1),
        'context_periods': len({match.group().casefold() for match in PERIOD.finditer(serialized)}),
        'table_rows': len(table), 'table_columns': max(map(len, table), default=0),
        'formula_present': int(bool(draft['program'])), 'step_count': len(steps),
        **{f'operation_{operation}': steps.count(operation) for operation in OPERATIONS},
        **{f'unit_{unit}': int(scale == unit) for unit in ('percent', 'thousand', 'million', 'billion')},
        'answer_numeric': numeric, 'answer_yes_no': int(answer in ('yes', 'no')),
        'number_of_bound_literals': len(bindings), 'context_mentions': located,
        'unlocated_operands': len(bindings) - located,
        'executable': int(execution['status'] == 'executed'),
        'calc_question_no_formula': int(cue['calculation'] and not draft['program']),
        'multi_period_numeric': int(question_periods >= 2 and numeric),
        'explicit_scale_missing': int(scale is None),
        'percent_question_nonpercent_scale': int(cue['percent'] and scale != 'percent'),
        'ratio_question_percent_scale': int(cue['ratio'] and scale == 'percent'),
    }


def index_rows(rows, dataset, label):
    selected = [row for row in rows if row['dataset'] == dataset]
    indexed = {row['id']: row for row in selected}
    if not indexed or len(indexed) != len(selected):
        raise ValueError(f'{label}: expected nonempty unique {dataset} question IDs')
    return indexed


def replay_high(run, row, gold, run_digest, actions, receipts, metric_dir):
    """Choose High from the same bound receipts with the final-answer decoder enabled."""
    from benchmark_actions import collect_case
    from diagnose import read_replay_call

    replayed_calls = {}

    def call(name, actor, prompt):
        if name not in replayed_calls:
            receipt = read_replay_call(run, row, name, actor, prompt, run_digest, receipts[name])
            replayed_calls[name] = (actor, prompt, receipt)
        expected_actor, expected_prompt, receipt = replayed_calls[name]
        if (actor, prompt) != (expected_actor, expected_prompt):
            raise ValueError(f'{run}: High decoder changed a recorded request for {row["id"]}')
        return receipt

    original = collect_case(row, gold, ['high'], call, metric_dir)
    for tier, candidate in original.items():
        cost = action_cost([replayed_calls[name][2] for name in candidate['calls']])
        if actions[tier] != {**candidate, 'cost': cost}:
            raise ValueError(f'{run}: original {tier} result or cost differs for {row["id"]}')
    corrected = collect_case(row, gold, ['high'], call, metric_dir, decode_verifier_answer=True)['high']
    if corrected['calls'] != original['high']['calls']:
        raise ValueError(f'{run}: High decoder changed the charged calls for {row["id"]}')
    return corrected


def read_split(panel, run, dataset, *, decode_verifier_answer=False, metric_dir=None):
    public_path = panel / 'public.jsonl'
    reference_path = panel / 'references.jsonl'
    contract_path = run / 'run.json'
    outcomes_path = run / 'outcomes.jsonl'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    if (contract['schema'] != 'finance-benchmark-actions-v1' or not set(TIERS) <= set(contract['actions'])
            or contract['dataset'] not in (None, dataset)):
        raise ValueError(f'{run}: expected a matching three-tier action run')
    if contract['panel'] != {p.name: digest_file(p) for p in (public_path, reference_path)}:
        raise ValueError(f'{run}: action run and panel bytes disagree')
    if decode_verifier_answer:
        from benchmark_actions import read_panel

        if dataset == 'tatqa' and metric_dir is None:
            raise ValueError('TAT-QA verifier replay requires the official metric directory')
        rows, gold, _ = read_panel(panel, dataset)
        public = {row['id']: row for row in rows}
        run_digest = digest_file(contract_path)
        decoder_stats = Counter(questions=0, comparison_changed=0, selection_changed=0,
                                old_high_correct=0, new_high_correct=0, recovered=0, harmed=0)
    else:
        public = index_rows(load_lines(public_path), dataset, str(panel))
    outcomes = index_rows(load_lines(outcomes_path), dataset, str(run))
    if public.keys() != outcomes.keys() or any(outcomes[k]['report'] != r['report'] for k, r in public.items()):
        raise ValueError(f'{run}: action receipts must cover eligible panel IDs and reports exactly once')
    if any(set(row) != {'dataset', 'id', 'report', *PUBLIC_FIELDS} for row in public.values()):
        raise ValueError(f'{panel}: invalid public-only schema')
    design, correct, costs = [], [], []
    feature_seconds = 0.0
    required_calls = (['low'], ['low', 'mid'], ['low', 'high_solve', 'high_compare'])
    for ident, row in public.items():
        actions = outcomes[ident]['actions']
        receipts = outcomes[ident]['calls']
        started = perf_counter()
        design.append(features(row, actions['low']['submission']))
        feature_seconds += perf_counter() - started
        tier_costs = []
        for tier, names in zip(TIERS, required_calls):
            recorded = actions[tier]
            if recorded['calls'] != names or type(recorded['strict']) is not bool:
                raise ValueError(f'{run}: invalid {tier} action for {ident}')
            cost = action_cost([receipts[name] for name in names])
            if cost != recorded['cost']:
                raise ValueError(f'{run}: invalid {tier} cost for {ident}')
            tier_costs.append(cost)
        costs.append(tier_costs)
        labels = [int(actions[tier]['strict']) for tier in TIERS]
        if decode_verifier_answer:
            original = actions['high']
            adjusted = replay_high(run, row, gold[dataset, ident], run_digest, actions, receipts, metric_dir)
            before, after = original['strict'], adjusted['strict']
            labels[-1] = int(after)
            decoder_stats.update(questions=1, comparison_changed=original['comparison'] != adjusted['comparison'],
                                 selection_changed=original['decision'] != adjusted['decision'],
                                 old_high_correct=before, new_high_correct=after,
                                 recovered=after and not before, harmed=before and not after)
        correct.append(labels)
    profile = {key: value for key, value in contract.items()
               if key not in ('namespace', 'panel', 'dataset', 'actions')}
    split = {'ids': list(public), 'source_keys': {key for row in public.values() for key in identity_keys(row)},
             'provenance': {p.name: digest_file(p) for p in (contract_path, outcomes_path)},
             'profile': profile, 'features': np.array([list(row.values()) for row in design], dtype=float),
             'feature_names': list(design[0]), 'feature_seconds': feature_seconds,
             'correct': np.array(correct), 'costs': costs,
             'tokens': np.array([[cost['total_tokens'] for cost in row] for row in costs], dtype=float)}
    if decode_verifier_answer:
        split['verifier_replay'] = {'decoder': 'exact_keep_or_use_new_final_answer_v1', **decoder_stats}
    return split


def exposure_labels(path, dataset, eval_ids):
    if not path.is_file():
        return {}
    rows = index_rows(json.loads(path.read_text(encoding='utf-8')), dataset, str(path))
    if set(rows) != set(eval_ids):
        raise ValueError('Evaluation exposure membership must cover the evaluation IDs exactly')
    return {ident: rows[ident]['exposure'] for ident in eval_ids}


def oracle_labels(correct, tokens, penalty, mean_low_cost):
    utility = correct - penalty * tokens / mean_low_cost
    best_utility = utility.max(axis=1, keepdims=True)
    # Prefer lower realized cost on utility ties, then the cheaper nominal tier.
    return np.where(utility == best_utility, tokens, np.inf).argmin(axis=1)


def route_stats(split, routes, indices):
    low = split['correct'][indices, 0]
    chosen = split['correct'][indices, routes[indices]]
    records = [split['costs'][i][routes[i]] for i in indices]
    unknown = sum(row['unknown_usage_calls'] for row in records)
    known = sum(row['known_tokens'] for row in records)
    low_tokens = split['tokens'][indices, 0]
    return {
        'n': len(indices), 'accuracy': float(chosen.mean()), 'correct': int(chosen.sum()),
        'recovered': int(((low == 0) & (chosen == 1)).sum()),
        'harmed': int(((low == 1) & (chosen == 0)).sum()),
        'selected': dict(Counter(TIERS[route] for route in routes[indices])),
        'calls': sum(row['calls'] for row in records), 'known_tokens': known,
        'unknown_usage_calls': unknown, 'total_tokens': None if unknown else known,
        'normalized_token_cost': known / float(low_tokens.sum())
        if not unknown and np.isfinite(low_tokens).all() and low_tokens.sum() > 0 else None,
        'summed_call_seconds': sum(row['summed_call_seconds'] for row in records),
    }


def predict_factory(checkpoint):
    if checkpoint is None:
        from sklearn.ensemble import GradientBoostingClassifier

        return 'GBM', GBM_GRID, lambda config: GradientBoostingClassifier(
            **config, min_samples_leaf=3, random_state=17)

    from tabfm import TabFMClassifier, tabfm_v1_0_0_pytorch

    model = tabfm_v1_0_0_pytorch.load(model_type='classification', device='cpu', checkpoint_path=str(checkpoint))
    return 'TabFM-1.0.0-PyTorch', ({'n_estimators': 1}, {'n_estimators': 2}), lambda config: TabFMClassifier(
        model=model, random_state=17, **config)


def fit_on_training(fit, calibration, penalty, mean_low_cost, configure, candidates):
    usable_fit = np.isfinite(fit['tokens']).all(axis=1)
    usable_cal = np.isfinite(calibration['tokens']).all(axis=1)
    labels = oracle_labels(fit['correct'][usable_fit], fit['tokens'][usable_fit], penalty, mean_low_cost)
    counts = dict(Counter(TIERS[label] for label in labels))
    if len(counts) == 1:
        label = int(labels[0])
        return lambda values: np.full(len(values), label), {'constant': TIERS[label]}, counts

    indices = np.flatnonzero(usable_cal)
    best = None
    for config in candidates:
        clf = configure(config)
        clf.fit(fit['features'][usable_fit], labels)
        predicted = clf.predict(calibration['features'][usable_cal]).astype(int)
        realized_cost = float(calibration['tokens'][indices, predicted].mean())
        realized_correct = float(calibration['correct'][indices, predicted].mean())
        utility = realized_correct - penalty * realized_cost / mean_low_cost
        key = (utility, -realized_cost)
        if best is None or key > best[0]:
            best = key, clf, config
    return best[1].predict, best[2], counts


def pareto_indices(points):
    return [i for i, (cost, accuracy) in enumerate(points)
            if not any(c <= cost and a >= accuracy and (c < cost or a > accuracy) for c, a in points)]


def fit_policies(fit, calibration, checkpoint):
    """Fit every policy and select the calibration frontier before evaluation."""
    masks = [np.isfinite(split['tokens']).all(axis=1) for split in (fit, calibration)]
    if not all(mask.any() for mask in masks):
        raise ValueError('Fit and calibration require some complete three-tier token costs')
    mean_low_cost = float(fit['tokens'][masks[0], 0].mean())
    if mean_low_cost <= 0:
        raise ValueError('Mean Low token cost on fit must be positive')
    name, candidates, configure = predict_factory(checkpoint)
    cal_idx = np.flatnonzero(masks[1])
    policies = []
    for penalty in LAMBDAS:
        predict, config, counts = fit_on_training(fit, calibration, penalty, mean_low_cost, configure, candidates)
        cal_routes = np.zeros(len(calibration['ids']), dtype=int)
        cal_routes[cal_idx] = predict(calibration['features'][cal_idx]).astype(int)
        policies.append((predict, {'lambda': penalty, 'config': config, 'fit_oracle_labels': counts,
                                   'calibration': route_stats(calibration, cal_routes, cal_idx)}))
    frontier = set(pareto_indices([(point['calibration']['total_tokens'], point['calibration']['accuracy'])
                                   for _, point in policies]))
    for index, (_, point) in enumerate(policies):
        point['calibration_frontier'] = index in frontier
    summary = {
        'method': name, 'feature_names': fit['feature_names'],
        'fit_rows': len(masks[0]), 'complete_fit_rows': int(masks[0].sum()),
        'calibration_rows': len(masks[1]), 'complete_calibration_rows': int(masks[1].sum()),
        'mean_fit_low_tokens': mean_low_cost,
    }
    return summary, policies


def evaluate_policies(summary, policies, evaluation, exposure):
    """Apply previously calibrated policies without refitting or reselecting."""
    eval_indices = np.arange(len(evaluation['ids']))
    groups = {group: np.array([i for i, ident in enumerate(evaluation['ids']) if exposure.get(ident) == group])
              for group in sorted(set(exposure.values()))}

    def eval_route(routes):
        return {'all': route_stats(evaluation, routes, eval_indices),
                'by_exposure': {name: route_stats(evaluation, routes, group) for name, group in groups.items()},
                'tiers_in_eval_order': [TIERS[route] for route in routes]}

    scored = []
    for predict, point in policies:
        started = perf_counter()
        chosen = predict(evaluation['features']).astype(int)
        measured = {'prediction_batch_seconds': perf_counter() - started, **eval_route(chosen)}
        scored.append({**point, 'eval': measured})
    return {
        **summary, 'eval_ids': evaluation['ids'],
        'eval_strict_by_tier': {tier: evaluation['correct'][:, index].tolist()
                                for index, tier in enumerate(TIERS)},
        'eval_feature_seconds': evaluation['feature_seconds'],
        'fixed': {tier: eval_route(np.full(len(eval_indices), route)) for route, tier in enumerate(TIERS)},
        'policies': scored,
    }


def evaluate(fit, calibration, evaluation, exposure, checkpoint):
    summary, policies = fit_policies(fit, calibration, checkpoint)
    return evaluate_policies(summary, policies, evaluation, exposure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, required=True)
    for name in SPLITS:
        parser.add_argument(f'--{name}-run', type=Path, required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decode-verifier-answer', action='store_true',
                        help='Replay High with exact KEEP/USE_NEW from the final answer')
    parser.add_argument('--metric-dir', type=Path, help='Official TAT-QA metric checkout for verifier replay')
    parser.add_argument('--tabfm-checkpoint', type=Path, help='Local TabFM checkpoint with classification subdir')
    args = parser.parse_args()
    if args.tabfm_checkpoint is not None and not args.tabfm_checkpoint.exists():
        parser.error('TabFM checkpoint must already exist locally')
    if args.output.exists():
        parser.error('Use a new results file')
    if args.decode_verifier_answer and args.dataset == 'tatqa' and args.metric_dir is None:
        parser.error('TAT-QA verifier replay requires --metric-dir')

    def read_part(part):
        return read_split(args.panel / part, getattr(args, f'{part}_run'), args.dataset,
                          decode_verifier_answer=args.decode_verifier_answer, metric_dir=args.metric_dir)

    fit, cal = read_part('fit'), read_part('calibration')
    seen = set(fit['source_keys'])

    def check_split(split):
        if split['profile'] != fit['profile'] or split['feature_names'] != fit['feature_names']:
            raise ValueError('All splits must use the same checkpoint, serving, and features')
        if seen & split['source_keys']:
            raise ValueError('Question, report, filing, or table overlaps across splits')
        seen.update(split['source_keys'])

    check_split(cal)
    summary, policies = fit_policies(fit, cal, args.tabfm_checkpoint)
    evaluation = read_part('eval')
    check_split(evaluation)
    splits = fit, cal, evaluation
    exposure = exposure_labels(args.panel / 'eval/exposure.json', args.dataset, evaluation['ids'])
    result = evaluate_policies(summary, policies, evaluation, exposure)
    result.update(dataset=args.dataset, run_profile=fit['profile'],
                  inputs={name: split['provenance'] for name, split in zip(SPLITS, splits)},
                  classifier_package_version=version('tabfm' if args.tabfm_checkpoint else 'scikit-learn'),
                  adaptation={'oracle_cost_scale': 'mean Low tokens on complete-cost fit rows',
                              'lambda_grid': 'predeclared 26-point adaptation',
                              'unknown_costs': 'Complete-cost rows for fit/calibration. Full eval with unknown totals retained.',
                              'timing': 'Replayed model-call sums, feature time, and batched router time reported separately.',
                              'features': 'Question, context and Low DSL only. No confidence or explicit evidence fields.',
                              'tabfm_checkpoint': str(args.tabfm_checkpoint) if args.tabfm_checkpoint else None})
    if args.decode_verifier_answer:
        result['verifier_replay'] = {name: split['verifier_replay'] for name, split in zip(SPLITS, splits)}
    write_json(args.output, result)


if __name__ == '__main__':
    main()
