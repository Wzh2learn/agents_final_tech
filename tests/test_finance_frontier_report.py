from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def matched_runs(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    from benchmark_actions import action_cost, digest_file
    from frontier_report import CONTRACT_CASCADE, outcome, summarize

    panel, oda, car = (tmp_path / name for name in ('panel', 'oda', 'car'))
    for path in (panel, oda, car):
        path.mkdir()
    args = SimpleNamespace(panel=panel, oda_run=oda, car_run=car, dataset='finqa',
                           **{key: tmp_path / f'{key}.json' for key in (
                               'budgetverify_gbm', 'budgetverify_tabfm', 'cascade_raw', 'cascade_compiled')})
    ids = ('known', 'unknown')

    def write(path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def lines(path, values):
        path.write_text(''.join(json.dumps(value) + '\n' for value in values), encoding='utf-8')

    public = [{'dataset': 'finqa', 'id': ident, 'report': ident} for ident in ids]
    lines(panel / 'public.jsonl', public)
    lines(panel / 'references.jsonl', [dict(row, gold={}) for row in public])
    write(panel / 'exposure.json', [
        {'dataset': 'finqa', 'id': 'known', 'exposure': 'pilot_question'},
        {'dataset': 'finqa', 'id': 'unknown', 'exposure': 'no_pilot_or_reserved_context_detected'},
    ])
    panel_digest = {name: digest_file(panel / name) for name in ('public.jsonl', 'references.jsonl')}
    write(oda / 'run.json', {'schema': 'finance-benchmark-actions-v1', 'dataset': None, 'panel': panel_digest})
    write(oda / 'collection.json', {'collection_wall_seconds_this_pass': 58})

    def call(tokens, elapsed):
        return {'usage': None if tokens is None else {'total': tokens}, 'elapsed_seconds': elapsed}

    oda_points = {}
    for row in public:
        known = row['id'] == 'known'
        calls = {'low': call(10, 1), 'free': call(7 if known else None, 2), 'mid': call(4, 1),
                 'car_probe': call(5, 1), 'high_solve': call(6, 2), 'high_compare': call(2, 1)}
        selected = {'low': ['low'], 'free': ['free'], 'dsl_fallback': ['low', 'free'],
                    'contract_compile': ['low'], 'compiled_fallback': ['low'] if known else ['low', 'free'],
                    'mid': ['low', 'mid'], 'high': ['low', 'high_solve', 'high_compare']}
        actions = {name: {'strict': known and name in ('contract_compile', 'compiled_fallback'),
                          'calls': used, 'cost': action_cost([calls[key] for key in used])}
                   for name, used in selected.items()}
        oda_points[row['id']] = dict(row, actions=actions, calls=calls)
    lines(oda / 'outcomes.jsonl', oda_points.values())
    provenance = {name: digest_file(oda / name) for name in ('run.json', 'outcomes.jsonl')}
    write(car / 'run.json', {'schema': 'finance-car-collection-v1', 'stage': 'eval', 'dataset': 'finqa',
                             'panel': panel_digest, 'draft_collection': provenance['outcomes.jsonl'], 'policy': 'frozen'})
    write(car / 'collection.json', {'collection_wall_seconds': 24})
    repairs = []
    for row in oda_points.values():
        ident = row['id']
        relative = f'calls/{sha256(ident.encode()).hexdigest()[:24]}/call.json' if ident == 'known' else None
        charged = [row['calls'][name] for name in ('low', 'car_probe')]
        if relative:
            path = car / relative
            path.parent.mkdir(parents=True)
            charged.append(call(3, 2))
            write(path, charged[-1])
        repairs.append({k: row[k] for k in ('dataset', 'id', 'report')} |
                       {'draft_correct': False, 'attempted_repair': relative is not None,
                        'repair_receipt': relative, 'strict': relative is not None, 'cost': action_cost(charged)})
    lines(car / 'outcomes.jsonl', repairs)

    for path, method in ((args.budgetverify_gbm, 'GBM'), (args.budgetverify_tabfm, 'TabFM-1.0.0-PyTorch')):
        order = list(reversed(ids))
        labels = {'low': [0, 0], 'mid': [0, 0], 'high': [0, 1]}
        fixed = {}
        for tier, stricts in labels.items():
            items = [outcome(strict, oda_points[ident]['actions'][tier]['cost'])
                     for ident, strict in zip(order, stricts, strict=True)]
            fixed[tier] = {'all': summarize(items), 'tiers_in_eval_order': [tier] * len(ids)}
        write(path, {'dataset': 'finqa', 'method': method, 'inputs': {'eval': provenance},
                     'eval_ids': order, 'eval_strict_by_tier': labels, 'fixed': fixed,
                     'verifier_replay': {'eval': {}}, 'policies': [
                         {'lambda': .1, 'calibration_frontier': True, 'config': {'constant': 'high'}, 'eval': fixed['high']},
                         {'lambda': .2, 'calibration_frontier': False},
                     ]})

    def reported(items):
        stats = summarize([outcome(row['strict'], {**row, 'calls': len(row['queried'])}) for row in items])
        return {'items': items, 'all': {**stats, 'strict': stats['correct'], 'tokens': stats['total_tokens']}}

    for representation, path in (('raw', args.cascade_raw), ('compiled', args.cascade_compiled)):
        arm = 'low' if representation == 'raw' else 'contract_compile'
        single = [{'id': ident, 'selected': 'oda-8b', 'queried': ['oda-8b'],
                   'strict': row['actions'][arm]['strict'], **row['actions'][arm]['cost']}
                  for ident, row in oda_points.items()]
        policies = {'always_oda-8b': reported(single)}
        for model in ('qwen-27b', 'deepseek'):
            policies[f'always_{model}'] = reported([
                {'id': ident, 'selected': model, 'queried': [model],
                 'strict': model == 'qwen-27b', **action_cost([call(40, 3)])} for ident in ids])
        if representation == 'compiled':
            policies[CONTRACT_CASCADE] = reported([
                single[0], {'id': 'unknown', 'selected': 'qwen-27b',
                            'queried': ['oda-8b', 'oda-8b-free', 'qwen-27b'], 'strict': 1,
                            **action_cost([call(10, 1), call(None, 2), call(40, 3)])},
            ])
            policies['nonexecution_8b_qwen_deepseek'] = reported([
                single[0], {'id': 'unknown', 'selected': 'qwen-27b', 'queried': ['oda-8b', 'qwen-27b'],
                            'strict': 1, **action_cost([call(10, 1), call(40, 3)])},
            ])
            policies['nonexecution_deepseek_qwen'] = policies['always_deepseek']
        write(path, {'dataset': 'finqa', 'representation': representation, 'policies': policies,
                     'profiles': [], 'author_revision': 'pinned',
                     'campus_ledger_sha256': 'shared', 'matched_input_sha256': {'eval': 'matched'}})
    return args


def test_matched_report_keeps_cost_uncertainty_and_calibration_choice(matched_runs):
    from frontier_report import build_report, render_table

    report = build_report(matched_runs)
    strata = report['strata']
    full = strata['all']
    shared = strata['common_complete_usage']
    chain = 'cascade/compiled/contract_8b_free_qwen_deepseek'
    measured = full['policies'][chain]
    assert (full['n'], measured['correct'], measured['known_tokens']) == (2, 2, 60)
    assert measured['total_tokens'] is None and measured['unknown_usage_calls'] == 1
    assert measured['known_tokens_are_lower_bound'] and measured['mean_serial_call_seconds'] == 3.5
    assert 'token_frontier' not in full and (shared['n'], shared['excluded_n']) == (1, 1)
    assert shared['policies'][chain]['total_tokens'] == 10
    assert not shared['policies'][chain]['known_tokens_are_lower_bound']
    assert all(point['unknown_usage_calls'] == 0 and point['n'] == 1 for point in shared['policies'].values())
    assert 'oda/low' not in shared['token_frontier'] and 'oda/contract_compile' in shared['token_frontier']
    assert 'budgetverify/gbm/lambda_0.2' not in full['policies']
    assert strata['detected_overlap']['policies']['budgetverify/gbm/lambda_0.1']['correct'] == 1
    assert strata['no_detected_overlap']['n'] == 1
    assert report['timing']['online_policy_wall_seconds'] is None
    assert report['timing']['acquisition_wall']['oda']['collection_wall_seconds_this_pass'] == 58
    assert f'{chain}\t2\t2\t1.000000\tunknown\t60\t1' in render_table(report)
    paired = report['paired_strict_evaluation']
    contrast = paired['by_stratum']['all']['cascade/compiled/nonexecution_deepseek_qwen']
    assert paired['flagship'] == chain and contrast['gains'] == 2
    assert contrast['paired_cluster_percentile_95_pp'] == [100.0, 100.0]
    assert paired['by_stratum']['no_detected_overlap']['oda/compiled_fallback']['net_pp'] == 100
    assert 'paired_cluster_percentile_95_pp' not in paired['by_stratum']['all']['oda/low']


def test_matched_report_rejects_duplicate_ids(matched_runs):
    from frontier_report import build_report

    path = matched_runs.oda_run / 'outcomes.jsonl'
    first = path.read_text(encoding='utf-8').splitlines()[0]
    path.write_text(first + '\n' + first + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='ODA: expected exactly one row'):
        build_report(matched_runs)


def test_paired_intervals_resample_report_clusters_and_retain_harms(matched_runs):
    from frontier_report import FLAGSHIP, INTERVAL_ANCHORS, Outcome, paired_evaluation

    reports = {'a': 'first', 'b': 'first', 'c': 'second', 'd': 'second'}

    def policy(correctness):
        return ({ident: Outcome(strict, 23, 0, 1, 1.0)
                 for ident, strict in zip(reports, correctness, strict=True)}, {})

    main, comparator = policy([1, 0, 1, 0]), policy([0, 1, 0, 0])
    policies = {FLAGSHIP: main, **dict.fromkeys(INTERVAL_ANCHORS, comparator), 'descriptive': comparator}
    paired = paired_evaluation(policies, reports, {'all': list(reports), 'no_detected_overlap': ['b']})['by_stratum']
    assert paired['all']['car'] == {'n': 4, 'clusters': 2, 'gains': 2, 'harms': 1, 'net_pp': 25,
                                    'paired_cluster_percentile_95_pp': [0.0, 50.0]}
    assert paired['no_detected_overlap']['car']['paired_cluster_percentile_95_pp'] == [-100.0, -100.0]
    assert 'paired_cluster_percentile_95_pp' not in paired['all']['descriptive']


def test_ratio_sensitivity_is_separate_from_matched_frontiers(matched_runs):
    from frontier_report import CONTRACT_CASCADE, build_report

    path = matched_runs.cascade_compiled
    compiled = json.loads(path.read_text(encoding='utf-8'))
    before = build_report(matched_runs)
    assert 'literal_ratio_sensitivity' not in before
    full = dict(n=2, baseline_correct=2, guarded_correct=1, gains=0, harms=1, changed_values=1)
    subgroup = dict(full, n=1, baseline_correct=1, guarded_correct=0)
    compiled['literal_ratio_sensitivity'] = {
        'rule': 'guard explicit percent literals',
        'policies': {CONTRACT_CASCADE: {'no_detected_overlap': subgroup, 'all': full}},
    }
    path.write_text(json.dumps(compiled), encoding='utf-8')
    report = build_report(matched_runs)
    measured = report['literal_ratio_sensitivity']['policies'][CONTRACT_CASCADE]
    assert measured == {'all': full, 'no_detected_overlap': subgroup}
    assert report['strata'] == before['strata']
    assert report['paired_strict_evaluation'] == before['paired_strict_evaluation']

    subgroup.update(n=2, baseline_correct=2, guarded_correct=1)
    path.write_text(json.dumps(compiled), encoding='utf-8')
    with pytest.raises(ValueError, match='counts differ from matched outcomes'):
        build_report(matched_runs)
