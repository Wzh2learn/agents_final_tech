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
    lines(panel / 'references.jsonl', [dict(row, gold={'program': program}) for row, program in zip(
        public, ('add(1, 2)', 'add(1, 2), multiply(#0, 2)'), strict=True)])
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
        actions = {name: {'strict': known and name in ('free', 'dsl_fallback', 'contract_compile', 'compiled_fallback'),
                          'executable': known and 'free' not in used,
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
                        'repair_receipt': relative, 'strict': relative is not None, 'executable': relative is not None,
                        'cost': action_cost(charged)})
    lines(car / 'outcomes.jsonl', repairs)

    for path, method in ((args.budgetverify_gbm, 'GBM'), (args.budgetverify_tabfm, 'TabFM-1.0.0-PyTorch')):
        order = list(reversed(ids))
        labels = {'low': [0, 0], 'mid': [0, 0], 'high': [0, 1]}
        executed = {'low': [False, True], 'mid': [False, True], 'high': [True, True]}
        fixed = {}
        for tier, stricts in labels.items():
            items = [outcome(strict, oda_points[ident]['actions'][tier]['cost'], executable=flag)
                     for ident, strict, flag in zip(order, stricts, executed[tier], strict=True)]
            fixed[tier] = {'all': summarize(items), 'tiers_in_eval_order': [tier] * len(ids)}
        inputs = {split: {name: sha256(f'{split}/{name}'.encode()).hexdigest() for name in provenance}
                  for split in ('fit', 'calibration')}
        write(path, {'dataset': 'finqa', 'method': method, 'inputs': {**inputs, 'eval': provenance},
                     'eval_ids': order, 'eval_strict_by_tier': labels, 'eval_executable_by_tier': executed, 'fixed': fixed,
                     'verifier_replay': {'eval': {}}, 'policies': [
                         {'lambda': .1, 'calibration_frontier': True, 'config': {'constant': 'high'}, 'eval': fixed['high'],
                          'calibration': {'normalized_token_cost': 1.8, 'accuracy': .6, 'total_tokens': 180}},
                         {'lambda': .2, 'calibration_frontier': False, 'calibration': {}},
                         {'lambda': .3, 'calibration_frontier': True, 'config': {'constant': 'mid'}, 'eval': fixed['mid'],
                          'calibration': {'normalized_token_cost': 2.2, 'accuracy': .9, 'total_tokens': 220}},
                     ]})

    def reported(items):
        stats = summarize([outcome(row['strict'], {**row, 'calls': len(row['queried'])},
                                   executable=row.get('executable')) for row in items])
        return {'items': items, 'all': {**stats, 'strict': stats['correct'], 'tokens': stats['total_tokens']}}

    for representation, path in (('raw', args.cascade_raw), ('compiled', args.cascade_compiled)):
        arm = 'low' if representation == 'raw' else 'contract_compile'
        single = [{'id': ident, 'selected': 'oda-8b', 'queried': ['oda-8b'],
                   'executable': row['actions'][arm]['executable'],
                   'strict': row['actions'][arm]['strict'], **row['actions'][arm]['cost']}
                  for ident, row in oda_points.items()]
        policies = {'always_oda-8b': reported(single)}
        for model in ('qwen-27b', 'deepseek'):
            policies[f'always_{model}'] = reported([
                {'id': ident, 'selected': model, 'queried': [model],
                 'strict': model == 'qwen-27b', 'executable': True, **action_cost([call(40, 3)])} for ident in ids])
        policies['cascade_routing_1.5'] = {**policies['always_qwen-27b'], 'target_mean_tokens': 15}
        if representation == 'compiled':
            policies[CONTRACT_CASCADE] = reported([
                single[0], {'id': 'unknown', 'selected': 'qwen-27b',
                            'queried': ['oda-8b', 'oda-8b-free', 'qwen-27b'], 'strict': 1, 'executable': True,
                            **action_cost([call(10, 1), call(None, 2), call(40, 3)])},
            ])
            policies['nonexecution_8b_qwen_deepseek'] = reported([
                single[0], {'id': 'unknown', 'selected': 'qwen-27b', 'queried': ['oda-8b', 'qwen-27b'],
                            'strict': 1, 'executable': True, **action_cost([call(10, 1), call(40, 3)])},
            ])
            policies['nonexecution_deepseek_qwen'] = policies['always_deepseek']
            policies['nonexecution_qwen_deepseek'] = policies['always_qwen-27b']
            policies['nonexecution_8b_deepseek_qwen'] = policies['nonexecution_8b_qwen_deepseek']
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
    assert set(report['budgetverify_inputs']) == {'fit', 'calibration', 'eval'}
    assert report['budgetverify_inputs']['eval'] == report['oda']
    chain = 'cascade/compiled/contract_8b_free_qwen_deepseek'
    measured = full['policies'][chain]
    assert (full['n'], measured['correct'], measured['known_tokens']) == (2, 2, 60)
    assert measured['total_tokens'] is None and measured['unknown_usage_calls'] == 1
    assert measured['known_tokens_are_lower_bound'] and measured['mean_serial_call_seconds'] == 3.5
    assert 'token_frontier' not in full and (shared['n'], shared['excluded_n']) == (1, 1)
    assert shared['policies'][chain]['total_tokens'] == 10
    assert not shared['policies'][chain]['known_tokens_are_lower_bound']
    assert all(point['unknown_usage_calls'] == 0 and point['n'] == 1 for point in shared['policies'].values())
    assert 'oda/low' not in shared['token_frontier'] and 'oda/free' in shared['token_frontier']
    assert 'budgetverify/gbm/lambda_0.2' not in full['policies']
    assert strata['detected_overlap']['policies']['budgetverify/gbm/lambda_0.1']['correct'] == 1
    assert strata['no_detected_overlap']['n'] == 1
    assert report['timing']['online_policy_wall_seconds'] is None
    assert report['timing']['acquisition_wall']['oda']['collection_wall_seconds_this_pass'] == 58
    assert f'{chain}\t2\t2\t1.000000\tunknown\t60\t1' in render_table(report)
    assert measured['executable'] == measured['strict_and_executable'] == 2
    compiler = report['paired_compiler_effect']['by_stratum']['all']
    for metric in ('strict', 'strict_and_executable'):
        effect = compiler['oda-8b'][metric]
        assert (effect['n'], effect['raw_correct'], effect['compiled_correct'], effect['gains']) == (2, 0, 1, 1)
        assert effect['paired_cluster_percentile_95_pp'] == [0, 100]
        assert compiler['qwen-27b'][metric]['losses'] == 0
    shared_rescue = report['paired_compiler_effect']['strict_rescue_overlap_by_stratum']['all']
    assert shared_rescue == {'n': 2, 'rescued_by_model_count': [1, 1, 0, 0],
                             'rescued_by_only': {'oda-8b': 1, 'qwen-27b': 0, 'deepseek': 0},
                             'all_raw_wrong': 0, 'all_raw_wrong_rescued': 0}
    assert strata['reference_depth/single']['n'] == strata['reference_depth/multi']['n'] == 1
    by_depth = report['paired_compiler_effect']['by_stratum']
    assert by_depth['reference_depth/single']['oda-8b']['strict']['gains'] == 1
    assert by_depth['reference_depth/multi']['oda-8b']['strict']['gains'] == 0
    free = full['policies']['oda/free']
    assert (free['correct'], free['executable'], free['strict_and_executable']) == (1, 0, 0)
    assert full['policies']['budgetverify/gbm/fixed_high']['executable'] == 2
    executable = strata['common_complete_usage_and_execution']
    assert (executable['n'], executable['excluded_n']) == (1, 1)
    assert 'oda/contract_compile' in executable['executable_correct_token_frontier']
    header, *policy_rows = (line.split('\t') for line in render_table(report).splitlines())
    assert header[12:16] == ['executable', 'strict_and_executable', 'execution_known_n', 'execution_unknown_n']
    table = {row[0]: dict(zip(header, row, strict=True)) for row in policy_rows}
    assert table[chain]['common_complete_execution_n'] == '2'
    assert table[chain]['common_complete_execution_correct'] == '2'
    assert table[chain]['common_complete_usage_and_execution_n'] == '1'
    paired = report['paired_strict_evaluation']
    contrast = paired['by_stratum']['all']['cascade/compiled/nonexecution_deepseek_qwen']
    assert paired['flagship'] == chain and contrast['gains'] == 2
    assert contrast['paired_cluster_percentile_95_pp'] == [100.0, 100.0]
    assert paired['by_stratum']['no_detected_overlap']['oda/compiled_fallback']['net_pp'] == 100
    assert 'paired_cluster_percentile_95_pp' not in paired['by_stratum']['all']['oda/low']
    tradeoff = report['paired_tradeoff_evaluation']
    assert tradeoff['proposed'] == chain and tradeoff['unavailable_anchors'] == []
    assert 'budgetverify/tabfm/lambda_0.1' in tradeoff['anchors']
    assert 'budgetverify/tabfm/lambda_0.3' not in tradeoff['anchors']
    assert 'budgetverify/gbm/lambda_0.1' in tradeoff['anchors']
    assert 'budgetverify/gbm/lambda_0.3' not in tradeoff['anchors']
    assert 'cascade/compiled/cascade_routing_1.5' in tradeoff['anchors']
    assert 'cascade/raw/cascade_routing_1.5' in tradeoff['anchors']
    assert 'cascade/compiled/nonexecution_qwen_deepseek' in tradeoff['anchors']
    assert 'cascade/compiled/nonexecution_8b_deepseek_qwen' in tradeoff['anchors']
    deepseek = tradeoff['by_stratum']['all']['cascade/compiled/always_deepseek']
    assert deepseek['tokens']['n'] == deepseek['tokens']['excluded_n'] == 1
    assert deepseek['tokens']['interval_95'] is None
    assert deepseek['serial_call_seconds']['n'] == 2
    assert deepseek['serial_call_seconds']['strict_delta_pp'] == 100
    executable = tradeoff['strict_and_executable_by_stratum']['all']['cascade/compiled/always_deepseek']
    assert executable['serial_call_seconds']['strict_and_executable_delta_pp'] == 100


@pytest.mark.parametrize('split', ['fit', 'calibration'])
def test_matched_report_rejects_budgetverify_source_mismatch(matched_runs, split):
    from frontier_report import build_report

    path = matched_runs.budgetverify_tabfm
    report = json.loads(path.read_text(encoding='utf-8'))
    report['inputs'][split]['outcomes.jsonl'] = sha256(b'another training receipt').hexdigest()
    path.write_text(json.dumps(report), encoding='utf-8')
    with pytest.raises(ValueError, match='identical fit, calibration and eval receipts'):
        build_report(matched_runs)


def test_shared_budgetverify_compiler_updates_answers_without_changing_routes_or_cost(matched_runs):
    from frontier_report import build_report

    flags = {'low': {'strict': [False, True], 'executable': [False, True]},
             'mid': {'strict': [False, True], 'executable': [False, True]},
             'high': {'strict': [True, True], 'executable': [True, True]}}
    for path in (matched_runs.budgetverify_gbm, matched_runs.budgetverify_tabfm):
        record = json.loads(path.read_text(encoding='utf-8'))
        record['eval_public_compiler_by_tier'] = flags
        path.write_text(json.dumps(record), encoding='utf-8')
    report = build_report(matched_runs)
    stats = report['strata']['all']['policies']
    native = 'budgetverify/tabfm/lambda_0.1'
    compiled = 'budgetverify_compiled/tabfm/lambda_0.1'
    assert (stats[native]['correct'], stats[compiled]['correct']) == (1, 2)
    for key in ('calls', 'total_tokens', 'known_tokens', 'mean_serial_call_seconds'):
        assert stats[native][key] == stats[compiled][key]
    assert stats[compiled]['strict_and_executable'] == 2
    assert compiled in report['paired_tradeoff_evaluation']['anchors']
    assert 'budgetverify_compiled/gbm/lambda_0.1' in report['paired_tradeoff_evaluation']['anchors']
    assert 'budgetverify_compiled/tabfm/lambda_0.3' not in report['paired_tradeoff_evaluation']['anchors']
    assert compiled in report['paired_strict_evaluation']['by_stratum']['all']


def test_matched_report_rejects_duplicate_ids(matched_runs):
    from frontier_report import build_report

    path = matched_runs.oda_run / 'outcomes.jsonl'
    first = path.read_text(encoding='utf-8').splitlines()[0]
    path.write_text(first + '\n' + first + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='ODA: expected exactly one row'):
        build_report(matched_runs)


def test_compiler_effect_requires_same_model_call(matched_runs):
    from frontier_report import Outcome, paired_compiler_effect

    raw = ({'use': Outcome(0, 50, 0, 1, 1, False)}, {})
    compiled = ({'use': Outcome(1, 51, 0, 1, 1, True)}, {})
    with pytest.raises(ValueError, match='same-call compiler comparison has different recorded charges'):
        paired_compiler_effect({'cascade/raw/always_oda-8b': raw, 'cascade/compiled/always_oda-8b': compiled},
                               {'use': 'report'}, {'all': ['use']})


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


def test_paired_executable_tradeoff_distinguishes_free_answers_and_unknown_flags(matched_runs):
    from frontier_report import Outcome
    from paired_tradeoff import paired_tradeoff

    reports = {'free': 'report-a', 'executed': 'report-b', 'unknown': 'report-c'}
    proposed = {
        'free': Outcome(1, 5, 0, 1, 1.0, False),
        'executed': Outcome(1, 0, 1, 1, 1.0, True),
        'unknown': Outcome(1, 5, 0, 1, 1.0, None),
    }
    comparator = dict.fromkeys(reports, Outcome(1, 10, 0, 1, 2.0, True))
    strict = paired_tradeoff(proposed, comparator, reports, reports, draws=300)
    joint = paired_tradeoff(proposed, comparator, reports, reports, draws=300, require_execution=True)
    assert strict['serial_call_seconds']['strict_delta_pp'] == 0
    seconds = joint['serial_call_seconds']
    assert (seconds['n'], seconds['excluded_n'], seconds['strict_and_executable_delta_pp']) == (2, 1, -50)
    assert seconds['interval_95']['strict_and_executable_delta_pp'] == [-100, 0]
    tokens = joint['tokens']
    assert (tokens['n'], tokens['excluded_n'], tokens['strict_and_executable_delta_pp']) == (1, 2, -100)
    assert tokens['mean_token_delta'] == -5


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


def test_missing_legacy_execution_flags_stay_unknown(matched_runs):
    from frontier_report import build_report

    budget_path = matched_runs.budgetverify_gbm
    budget = json.loads(budget_path.read_text(encoding='utf-8'))
    budget.pop('eval_executable_by_tier')
    records = [*budget['fixed'].values(), budget['policies'][0]['eval']]
    for record in records:
        for key in ('executable', 'strict_and_executable'):
            record['all'].pop(key)
    budget_path.write_text(json.dumps(budget), encoding='utf-8')

    cascade_path = matched_runs.cascade_raw
    cascade = json.loads(cascade_path.read_text(encoding='utf-8'))
    for policy in cascade['policies'].values():
        for key in ('executable', 'strict_and_executable'):
            policy['all'].pop(key)
        for item in policy['items']:
            item.pop('executable')
    cascade_path.write_text(json.dumps(cascade), encoding='utf-8')

    report = build_report(matched_runs)
    full = report['strata']['all']['policies']
    high = full['budgetverify/gbm/fixed_high']
    assert high['correct'] == 1 and high['executable'] is None and high['strict_and_executable'] is None
    assert high['execution_unknown_n'] == 2
    assert full['budgetverify/gbm/fixed_low']['executable'] == 1
    assert full['cascade/raw/always_oda-8b']['executable'] == 1
    assert full['cascade/raw/always_qwen-27b']['executable'] is None
    assert report['strata']['common_complete_usage']['n'] == 1
    assert report['strata']['common_complete_usage_and_execution']['n'] == 0
    assert not report['strata']['common_complete_execution']['executable_correct_serial_call_time_frontier']


def test_executable_time_frontier_keeps_unknown_usage_on_the_shared_cohort(matched_runs):
    from frontier_report import Outcome, matched_frontiers

    ids = ['complete', 'unknown_usage', 'unknown_execution']
    policies = {
        'numeric_only': ({ident: Outcome(1, 5, 0, 1, 1.0, False) for ident in ids}, {}),
        'program': ({'complete': Outcome(1, 10, 0, 1, 2.0, True),
                     'unknown_usage': Outcome(1, 0, 1, 1, 2.0, True),
                     'unknown_execution': Outcome(1, 10, 0, 1, 2.0, None)}, {}),
    }
    cohorts, result = matched_frontiers(policies, {'all': ids})
    assert result['all']['serial_call_time_frontier'] == ['numeric_only']
    assert cohorts['common_complete_execution'] == ['complete', 'unknown_usage']
    assert cohorts['common_complete_usage_and_execution'] == ['complete']
    time = result['common_complete_execution']
    assert time['n'] == 2 and time['excluded_n'] == 1
    assert time['policies']['program']['strict_and_executable'] == 2
    assert time['executable_correct_serial_call_time_frontier'] == ['numeric_only', 'program']


def test_rejects_cascade_flag_that_disagrees_with_selected_program(matched_runs):
    from frontier_report import CONTRACT_CASCADE, build_report

    path = matched_runs.cascade_compiled
    report = json.loads(path.read_text(encoding='utf-8'))
    report['policies'][CONTRACT_CASCADE]['items'][0]['executable'] = False
    path.write_text(json.dumps(report), encoding='utf-8')
    with pytest.raises(ValueError, match='execution flag differs from its matched source'):
        build_report(matched_runs)
