from collections import Counter
import json
from pathlib import Path
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
