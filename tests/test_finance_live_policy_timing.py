from collections import Counter
from contextlib import nullcontext
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def timing(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    import live_policy_timing

    return live_policy_timing


@pytest.fixture
def question():
    return {'dataset': 'finqa', 'id': 'train-item', 'report': 'train-report', 'question': 'What is the total?',
            'pre_text': [], 'post_text': [], 'table': [['Row', '2023'], ['Revenue', '3']]}


def call_receipt(reply, elapsed=1, tokens=12):
    return {'text': reply, 'elapsed_seconds': elapsed, 'usage': None if tokens is None else {'total': tokens},
            'finish': ['stop'], 'errors': [], 'exit_code': 0}


def test_fixed_policies_use_numeric_and_execution_gates(timing, question):
    qwen, deepseek = timing.MANAGED
    replies = {'low': 'invalid', 'free': 'Final answer: 3', qwen: 'invalid',
               deepseek: 'Final program: add(1, 2)'}
    calls = []

    def call(name, role, prompt):
        assert role == 'solve' and question['question'] in prompt
        calls.append(name)
        return call_receipt(replies[name])

    action, _ = timing.select_policy(question, 'contract', call)
    assert calls == ['low', 'free'] and action['selected_stage'] == 'free_oda'
    calls.clear()
    replies['free'] = 'missing'
    action, _ = timing.select_policy(question, 'contract', call)
    assert calls == ['low', 'free', qwen, deepseek] and action['selected_model'] == deepseek
    calls.clear()
    replies.update({qwen: 'Final program: add(1, 2)', deepseek: 'invalid'})
    action, _ = timing.select_policy(question, 'ds-first', call)
    assert calls == [deepseek, qwen] and action['selected_model'] == qwen
    calls.clear()
    action, _ = timing.select_policy(question, 'qwen-first', call)
    assert calls == [qwen] and action['selected_model'] == qwen
    calls.clear()
    replies.update({qwen: 'invalid', deepseek: 'Final program: add(1, 2)'})
    action, _ = timing.select_policy(question, 'qwen-first', call)
    assert calls == [qwen, deepseek] and action['selected_model'] == deepseek


def test_train_order_seed_balances_six_permutations(timing, question):
    rows = [dict(question, id=str(index)) for index in range(6)]
    cases = timing.frozen_cases(rows, 6)
    assert cases == timing.frozen_cases(list(reversed(rows)), 6)
    assert len({order for _, order in cases}) == 6


@pytest.mark.parametrize('dataset,count', [('finqa', 1147), ('tatqa', 718)])
def test_full_panel_requires_complete_official_request(timing, dataset, count):
    args = SimpleNamespace(dataset=dataset, cases=count, stage='eval', offset=0,
                           compare_baselines=True, compact_container='a' * 12)
    timing.validate_full_panel_request(args)
    for key, value in [('cases', count - 1), ('offset', 1), ('stage', 'fit'),
                       ('compare_baselines', False), ('compact_container', None)]:
        changed = SimpleNamespace(**{**vars(args), key: value})
        with pytest.raises(ValueError, match='full-panel'):
            timing.validate_full_panel_request(changed)


def test_stratified_panel_requires_24_official_paired_questions(timing):
    args = SimpleNamespace(dataset='tatqa', cases=24, stage='eval', offset=0,
                           compare_baselines=True, compact_container='a' * 12)
    timing.validate_stratified_panel_request(args)
    for key, value in [('cases', 23), ('offset', 1), ('stage', 'fit'),
                       ('compare_baselines', False), ('compact_container', None)]:
        changed = SimpleNamespace(**{**vars(args), key: value})
        with pytest.raises(ValueError, match='stratified-panel'):
            timing.validate_stratified_panel_request(changed)


@pytest.mark.parametrize('dataset', ['finqa', 'tatqa'])
def test_stratified_sample_is_stable_and_preserves_depth_and_length(timing, question, dataset):
    rows = [dict(question, dataset=dataset, id=str(i), pre_text=['x' * i]) for i in range(100)]
    references = {
        'finqa': ('program', ('add(1, 2)', 'add(1, 2), divide(#0, 2)')),
        'tatqa': ('derivation', ('(-1,200.5) − 93%', '(1,200.5 − 93) ÷ 2 × 100%')),
    }
    field, (single, multi) = references[dataset]
    gold = {(dataset, row['id']): {field: single if i < 36 else multi} for i, row in enumerate(rows)}
    if dataset == 'tatqa':
        gold[dataset, '98'] = {field: 'implicit arithmetic'}
        gold[dataset, '99'] = {field: ''}

    cases, sampling = timing.stratified_cases(rows, gold, dataset)
    assert timing.stratified_cases(list(reversed(rows)), gold, dataset) == (cases, sampling)
    assert len(cases) == len(sampling['stratum_by_id']) == sampling['sample_n'] == 24
    assert sampling['population_n'] == 100
    assert {row['id'] for row, _ in cases} == set(sampling['stratum_by_id'])
    strata = sampling['strata']
    assert {key: strata[key]['population_n'] for key in ('single-short', 'single-long')} == {
        'single-short': 18, 'single-long': 18}
    assert strata['multi-short']['population_n'] == strata['multi-long']['population_n'] == (
        31 if dataset == 'tatqa' else 32)
    if dataset == 'tatqa':
        assert strata['unknown-short'] == strata['unknown-long'] == {'population_n': 1, 'sample_n': 1}
    observed = Counter(sampling['stratum_by_id'].values())
    assert observed == {key: value['sample_n'] for key, value in strata.items()}
    assert all(observed.values())
    expected_policies = set(timing.MATCHED_POLICIES + timing.COMPACT_POLICIES)
    for position in range(len(expected_policies)):
        assert {order[position] for _, order in cases[:len(expected_policies)]} == expected_policies


@pytest.mark.parametrize('dataset,count', [('finqa', 1147), ('tatqa', 718)])
def test_full_panel_binds_selected_rows_and_references_to_official_source(timing, monkeypatch, tmp_path,
                                                                        dataset, count):
    import cohorts

    source = {'path': str(tmp_path / 'official.json'), 'sha256': 'official'}
    (tmp_path / 'panel').mkdir()
    (tmp_path / 'panel' / 'manifest.json').write_text(
        json.dumps({'datasets': {dataset: {'eval': source}}}), encoding='utf-8')
    official = [({'dataset': dataset, 'id': str(i), 'question': f'question {i}'},
                 {'answer': i, 'question': 'not a reference field'}, 'arithmetic') for i in range(count)]
    monkeypatch.setattr(cohorts, 'read_source', lambda actual, path: (official, source))
    public = [row for row, _, _ in official]
    gold = {(dataset, row['id']): {'answer': reference['answer']} for row, reference, _ in official}
    assert timing.validate_official_panel(tmp_path, dataset, public, gold) == source
    with pytest.raises(ValueError, match='official source'):
        timing.validate_official_panel(tmp_path, dataset, public[:-1], gold)
    altered = list(public)
    altered[0] = {**altered[0], 'question': 'a changed prompt'}
    with pytest.raises(ValueError, match='official source'):
        timing.validate_official_panel(tmp_path, dataset, altered, gold)
    altered_gold = dict(gold)
    altered_gold[dataset, public[0]['id']] = {'answer': -1}
    with pytest.raises(ValueError, match='official source'):
        timing.validate_official_panel(tmp_path, dataset, public, altered_gold)
    with pytest.raises(ValueError, match='official source'):
        timing.validate_official_panel(tmp_path, dataset, [public[0], *public[1:-1], public[0]], gold)


@pytest.mark.parametrize('full_panel', [False, True])
def test_v4_alone_selects_expanded_timing_profile(timing, monkeypatch, tmp_path, full_panel):
    class ProfileReached(Exception):
        pass

    calls = []
    def profile(*args, **kwargs):
        calls.append((args, kwargs))
        raise ProfileReached

    monkeypatch.setitem(sys.modules, 'compact_eval',
                        SimpleNamespace(BASE='http://127.0.0.1:18157/v1', timed_compact_profile=profile))
    serve = tmp_path / 'oda_serving_profile.json'
    serve.write_text(json.dumps({'model': timing.ODA, 'checkpoint': timing.ODA_CHECKPOINT}), encoding='utf-8')
    args = SimpleNamespace(dataset='finqa', stage='eval', cases=1147, offset=0, compare_baselines=True,
                           compact_container='a' * 12, full_panel=full_panel, serving_profile=serve,
                           base='http://127.0.0.1:18157/v1')
    if full_panel:
        monkeypatch.setattr(timing, 'read_panel', lambda *_: (['panel'], {'gold': 1}, {'sha': 'digest'}))
        monkeypatch.setattr(timing, 'validate_official_panel', lambda *args: {'sha256': 'official'})
    with pytest.raises(ProfileReached):
        timing.run(args, tmp_path, tmp_path / 'ledger')
    assert calls == [((tmp_path, 'a' * 12, 'finqa'), {'expanded': True} if full_panel else {})]


@pytest.mark.parametrize('stratified', [False, True])
def test_official_timing_contract_declares_planned_panel_and_eleven_policies(timing, monkeypatch, tmp_path,
                                                                            question, stratified):
    serve = tmp_path / 'oda_serving_profile.json'
    serve.write_text(json.dumps({'model': timing.ODA, 'checkpoint': timing.ODA_CHECKPOINT}), encoding='utf-8')
    args = SimpleNamespace(dataset='finqa', stage='eval', cases=24 if stratified else 1147, offset=0,
                           compare_baselines=True, compact_container='a' * 12, full_panel=not stratified,
                           stratified_panel=stratified, serving_profile=serve,
                           base='http://127.0.0.1:18157/v1', qwen_api_profile=None, deepseek_api_profile=None,
                           prior_charged_tokens=0, max_posts=1, token_cap=100, namespace='full',
                           opencode=tmp_path / 'opencode', metric_dir=None)
    rows = [dict(question, id=str(i), pre_text=['x' * (i % 20)]) for i in range(1147)]
    gold = {('finqa', row['id']): {'program': 'add(1, 2)' if i % 2 else 'add(1, 2), divide(#0, 2)'}
            for i, row in enumerate(rows)}
    monkeypatch.setattr(timing, 'read_panel', lambda *_: (rows, gold, {'public.jsonl': 'panel'}))
    monkeypatch.setattr(timing, 'validate_official_panel', lambda *args: {'sha256': 'official'})
    monkeypatch.setattr(timing, 'digest_file', lambda *_: 'digest')
    monkeypatch.setenv('BUPT_API_KEY', 'test-only')
    monkeypatch.setitem(sys.modules, 'compact_eval', SimpleNamespace(
        BASE=args.base, timed_compact_profile=lambda *a, **kw: {
            'base_checkpoint': timing.ODA_CHECKPOINT, 'model': 'compact', 'checkpoint': 'adapter'}))
    monkeypatch.setitem(sys.modules, 'live_local_baselines', SimpleNamespace(
        load_local_baselines=lambda *a: ({'car': None, 'budgetverify': None}, {})))
    monkeypatch.setitem(sys.modules, 'live_author_cascade', SimpleNamespace(
        load_isolated_author_cascade=lambda *a: nullcontext((None, {}))))
    budget = SimpleNamespace(rows=[], close=lambda: None)
    monkeypatch.setattr(timing.school.campus, 'BatchBudget', lambda *_: budget)
    monkeypatch.setattr(timing.school, 'charged', lambda *_: (0, 0))
    monkeypatch.setattr(timing.school, 'has_gateway_capacity', lambda *_: True)
    monkeypatch.setattr(timing.school, 'read_profile', lambda path, _: ({}, {'model_id': path.stem}))
    monkeypatch.setattr(timing, 'OpenCode', lambda *a, **kw: SimpleNamespace(initialize_session_store=lambda: None))
    monkeypatch.setattr(timing, 'wait_service', lambda *a: None)
    collected = []
    monkeypatch.setattr(timing, 'collect_cases', lambda args, root, cases, *rest: collected.extend(cases))
    ledger = tmp_path / 'ledger'
    ledger.mkdir()
    timing.run(args, tmp_path, ledger)
    contract = json.loads((tmp_path / 'full' / 'run.json').read_text(encoding='utf-8'))
    assert contract['schema'] == ('finance-live-policy-timing-stratified-v1' if stratified
                                  else 'finance-live-policy-timing-v4')
    assert contract['full_official_panel'] is (not stratified) and contract['case_offset'] == 0
    assert contract['official_source'] == {'sha256': 'official'}
    assert len(contract['case_order']) == len(collected) == args.cases
    assert all(set(order) == set(timing.MATCHED_POLICIES + timing.COMPACT_POLICIES)
               for _, order in collected)
    if stratified:
        selected, sampling = timing.stratified_cases(rows, gold, 'finqa')
        assert contract['stratified_sampling'] == sampling
        assert selected == collected
    else:
        assert 'collection.json' in contract['full_panel_completion']


def test_matched_block_balances_positions_and_keeps_shard_order(timing, question):
    policies = timing.MATCHED_POLICIES
    n = len(policies)
    assert n == 9 and {'qwen-first', 'ds-first'} <= set(policies)
    rows = [dict(question, id=str(index)) for index in range(2 * n)]
    all_cases = timing.frozen_cases(rows, len(rows), policies)
    for position in range(n):
        assert {order[position] for _, order in all_cases[:n]} == set(policies)
    adjacent = Counter(pair for _, sequence in all_cases for pair in zip(sequence, sequence[1:]))
    assert len(adjacent) == n * (n - 1)
    assert set(adjacent.values()) == {2}
    assert timing.frozen_cases(rows, n, policies, offset=n) == all_cases[n:]


def test_direct_compiled_uses_only_the_named_model(timing, question):
    calls = []

    def call(name, role, prompt):
        calls.append((name, role))
        return call_receipt('Final program: add(1, 2)')

    selected, _ = timing.select_policy(question, 'qwen-direct', call)
    assert calls == [(timing.MANAGED[0], 'solve')]
    assert selected['selected_model'] == timing.MANAGED[0]
    assert selected['calls'] == [timing.MANAGED[0]]


def test_compact_dispatch_escalates_only_nonexecution(timing, question):
    calls = []
    replies = {'compact': 'Final program: add(1, 2)', timing.MANAGED[1]: 'invalid',
               timing.MANAGED[0]: 'Final program: add(1, 2)'}

    def call(name, role, prompt):
        calls.append((name, role))
        return call_receipt(replies[name])

    result, _ = timing.select_compact_policy(question, 'compact-fallback', call, 'compact-model')
    assert calls == [('compact', 'compact_fallback')]
    assert result['selected_model'] == 'compact-model' and result['calls'] == ['compact']
    replies['compact'] = 'not a program'
    calls.clear()
    result, _ = timing.select_compact_policy(question, 'compact-direct', call, 'compact-model')
    assert calls == [('compact', 'compact_direct')] and result['calls'] == ['compact']
    calls.clear()
    result, _ = timing.select_compact_policy(question, 'compact-fallback', call, 'compact-model')
    assert calls == [('compact', 'compact_fallback'), (timing.MANAGED[1], 'solve'),
                     (timing.MANAGED[0], 'solve')]
    assert result['selected_model'] == timing.MANAGED[0]
    assert result['calls'] == ['compact', timing.MANAGED[1], timing.MANAGED[0]]


def test_comparator_time_includes_probe_and_repair_roles(timing, question, monkeypatch, tmp_path):
    clock = [0.0]
    dispatched = []

    def local(actor, prompt, target, run_digest):
        dispatched.append(actor)
        clock[0] += 2
        return call_receipt('Final program: add(1, 2)', elapsed=1)

    def selector(row, call):
        for role in ('solve', 'probe', 'repair'):
            call(role, role, 'fixture prompt')
        return {'submission': {'arm': 'dsl', 'program': 'add(1, 2)', 'scale': '', 'answer': None,
                               'parse_mode': 'declared'}, 'calls': ['solve', 'probe', 'repair']}, row

    monkeypatch.setattr(timing, 'recorded_call', local)
    monkeypatch.setattr(timing, 'monotonic', lambda: clock[0])
    selectors = {'car': selector}
    roles = {role: role for role in ('solve', 'probe', 'repair')}
    args = SimpleNamespace(metric_dir=None)
    budget = SimpleNamespace(rows=[])
    timing.collect_cases(args, tmp_path, [(question, ('car',))], {('finqa', question['id']): {'exe_ans': 3}},
                         roles, {}, budget, 'fixture', 'digest', selectors)

    assert dispatched == ['solve', 'probe', 'repair']
    summary = json.loads((tmp_path / 'collection.json').read_text(encoding='utf-8'))
    car = summary['complete_pair_policies']['car']
    assert (car['mean_wall_seconds'], car['cost']['summed_call_seconds'], car['strict_and_executable']) == (6, 3, 1)


def test_wall_counts_fresh_routes_and_excludes_grading(timing, question, monkeypatch, tmp_path):
    qwen, deepseek = timing.MANAGED
    clock = [0.0]
    seen = set()
    actual_grading = timing.grade_case
    budget = SimpleNamespace(rows=[])
    args = SimpleNamespace(opencode=Path('fixture-opencode'), metric_dir=None)

    def local(_actor, _prompt, target, _digest):
        assert target not in seen
        seen.add(target)
        clock[0] += 1
        return call_receipt('Final program: add(1, 2)')

    def campus(target, _opencode, _digest, _prompt, *, key, budget, profile, gateway):
        assert target not in seen and gateway['model_id'] == deepseek and key == 'fixture'
        seen.add(target)
        clock[0] += 5
        budget.rows.append({'state': 'complete', 'usage': {'total_tokens': 40}})
        return {**call_receipt('Final program: add(1, 2)', elapsed=4, tokens=40), 'provider_posts': 1}

    def grade(*args, **kwargs):
        clock[0] += 100
        return actual_grading(*args, **kwargs)

    monkeypatch.setattr(timing, 'recorded_call', local)
    monkeypatch.setattr(timing.school, 'has_gateway_capacity', lambda _: True, raising=False)
    monkeypatch.setattr(timing.school, 'fresh_managed_call', campus, raising=False)
    monkeypatch.setattr(timing, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(timing, 'grade_case', grade)
    profiles = {model: ({}, {'model_id': model}) for model in (qwen, deepseek)}
    timing.collect_cases(args, tmp_path, [(question, timing.POLICIES)],
                         {('finqa', question['id']): {'exe_ans': 3}}, {'solve': None},
                         profiles, budget, 'fixture', 'digest')
    outcome = json.loads((tmp_path / 'outcomes.jsonl').read_text(encoding='utf-8'))
    assert outcome['complete_pair']
    policies = outcome['policies']
    assert [policies[name]['wall_seconds'] for name in timing.POLICIES] == [1, 1, 5]
    assert policies['ds-first']['cost']['summed_call_seconds'] == 4
    assert all(item['result']['strict'] for item in policies.values())
    summary = json.loads((tmp_path / 'collection.json').read_text(encoding='utf-8'))
    assert summary['campus_debit_including_unknown'] == 40 and summary['collection_wall_seconds'] == 307
    assert summary['complete_pair_policies']['ds-first']['median_wall_seconds'] == 5
    assert summary['complete_pair_policies']['ds-first']['p90_wall_seconds'] == 5
    assert summary['all_attempt_cost']['known_tokens'] == 64
    assert summary['strict_wall_frontier'] == ['contract', 'oda-local']
    assert summary['strict_and_executable_wall_frontier'] == ['contract', 'oda-local']
    paired = summary['paired_online_wall']['comparisons']['ds-first']
    assert (paired['strict']['n'], paired['strict']['mean_online_wall_seconds_delta']) == (1, -4)
    assert paired['strict']['strict_delta_pp'] == paired['strict_and_executable']['strict_and_executable_delta_pp'] == 0


def test_budget_stop_preserves_costs_and_excludes_incomplete_pair(timing, question, monkeypatch, tmp_path):
    args = SimpleNamespace(opencode=Path('fixture-opencode'), metric_dir=None)
    budget = SimpleNamespace(rows=[])
    profiles = {model: ({}, {}) for model in timing.MANAGED}
    monkeypatch.setattr(timing, 'recorded_call', lambda *_: call_receipt('invalid', tokens=None))
    monkeypatch.setattr(timing.school, 'has_gateway_capacity', lambda _: False)

    timing.collect_cases(args, tmp_path, [(question, timing.POLICIES)],
                         {('finqa', question['id']): {'exe_ans': 3}}, {'solve': None},
                         profiles, budget, 'fixture', 'digest')
    outcome = json.loads((tmp_path / 'outcomes.jsonl').read_text(encoding='utf-8'))
    assert not outcome['complete_pair']
    assert outcome['policies']['contract']['status'] == 'incomplete_budget'
    summary = json.loads((tmp_path / 'collection.json').read_text(encoding='utf-8'))
    assert summary['complete_paired_questions'] == 0 and summary['stop_reason'] == 'gateway_budget'
    assert summary['all_attempt_cost']['calls'] == summary['all_attempt_cost']['unknown_usage_calls'] == 4
    assert summary['all_attempt_cost']['total_tokens'] is None
    assert all(not row['n'] for row in summary['complete_pair_policies'].values())
    paired = summary['paired_online_wall']['comparisons']['ds-first']['strict']
    assert paired['n'] == 0 and paired['mean_online_wall_seconds_delta'] is None


def test_full_panel_early_budget_stop_is_not_reported_as_completed(timing, question, monkeypatch, tmp_path):
    args = SimpleNamespace(opencode=Path('fixture-opencode'), metric_dir=None)
    budget = SimpleNamespace(rows=[])
    profiles = {model: ({}, {}) for model in timing.MANAGED}
    monkeypatch.setattr(timing.school, 'has_gateway_capacity', lambda _: False)

    def dispatch(row, call):
        call(timing.MANAGED[0], 'solve', 'fixture prompt')
        raise AssertionError('budget stop must interrupt before return')

    policies = timing.MATCHED_POLICIES + timing.COMPACT_POLICIES
    selectors = {name: dispatch for name in policies}
    rows = [dict(question, id=str(index)) for index in range(1147)]
    cases = timing.frozen_cases(rows, len(rows), policies)
    timing.collect_cases(args, tmp_path, cases, {}, {'solve': None}, profiles,
                         budget, 'fixture', 'digest', selectors)
    outcome = json.loads((tmp_path / 'outcomes.jsonl').read_text(encoding='utf-8'))
    summary = json.loads((tmp_path / 'collection.json').read_text(encoding='utf-8'))
    assert not outcome['complete_pair']
    assert summary['planned_questions'] == 1147 and summary['complete_paired_questions'] == 0
    assert summary['stop_reason'] == 'gateway_budget'
    assert set(summary['complete_pair_policies']) == set(policies)
    assert all(item['n'] == 0 for item in summary['complete_pair_policies'].values())
