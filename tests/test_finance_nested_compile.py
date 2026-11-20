from pathlib import Path

import pytest


@pytest.fixture
def pilot(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    from benchmark_actions import collect_case
    from run_pilot import paired_prompt
    from table_scope_replay import nested_contract

    return collect_case, paired_prompt, nested_contract


@pytest.fixture
def report():
    return {
        'dataset': 'finqa', 'id': 'test', 'report': 'report',
        'question': 'What is the difference?',
        'pre_text': [], 'post_text': [],
        'table': [['', '2022', '2023'], ['Revenue', '2', '3']],
    }


def test_one_call_uses_same_scoring_as_compiled_flat(pilot, report):
    collect_case, paired_prompt, _ = pilot
    flat = 'add(10, 5), subtract(2, 3), divide(#0, #1)'
    replies = {'low': flat, 'nested_compile': 'divide(add(10, 5), subtract(2, 3))'}
    calls = []

    def call(action, actor, prompt):
        assert actor == 'solve'
        assert prompt == paired_prompt(report, 'dsl' if action == 'low' else 'nested')
        calls.append(action)
        return {'text': f'Final program: {replies[action]}', 'exit_code': 0, 'errors': [], 'finish': ['stop']}

    gold = {'exe_ans': -15.0}
    result = collect_case(report, gold, ['nested_compile'], call, None)
    assert calls == ['nested_compile']
    assert set(result) == {'nested_compile'}
    nested = result['nested_compile']
    assert nested['strict'] and nested['executable']
    assert nested['calls'] == ['nested_compile']
    assert nested['submission']['program'] == flat

    calls.clear()
    flat_action = collect_case(report, gold, ['contract_compile'], call, None)['contract_compile']
    assert calls == ['low']
    assert flat_action['strict'] and flat_action['submission'] == nested['submission']


def test_nested_keeps_scale_and_applies_shared_repairs(pilot, report):
    _, _, compile_reply = pilot
    projected, prediction, decision, cells = compile_reply(
        dict(report, dataset='tatqa'),
        'Final program: add(table_sum("Revenue", "2022", "2023"), 1)\nScale: million',
        stopped=True,
    )
    assert prediction['scale'] == 'million'
    assert decision == 'nested_table_scope'
    assert projected['table'][-1][1:] == ['2', '3']
    assert [entry['column'] for entry in cells] == [1, 2]
    assert prediction['program'].endswith('add(#0, 1)')

    _, prediction, decision, _ = compile_reply(
        dict(report, question='What percentage of the total?'),
        'Final program: multiply(divide(10, 20), const_100)', stopped=True,
    )
    assert decision == 'nested_finqa_ratio'
    assert prediction['program'] == 'divide(10, 20)'

    _, prediction, _, _ = compile_reply(
        dict(report, dataset='tatqa'),
        'Scale: million\n{"program": "add(1, 2)"}', stopped=True,
    )
    assert prediction['scale'] == 'million'


@pytest.mark.parametrize('reply', [
    'Final program: add(1, 2)\nFinal program: add(3, 4)',
    'Final program: add(1, 2)\n{"program": "add(3, 4)"}',
    '{"program": "add(3, 4)"}\nFinal program: add(1, 2)',
    '{\n  "program": "add(3, 4)"\n}\nFinal program: add(1, 2)',
    'Scale: million\n{"program": "add(1, 2)", "scale": "percent"}',
    'Final program: add(1, 2)\nScale: percent\nScale: million',
    'Final program: add(1, 2), subtract(#0, 3)',
    'Final program: divide(#0, 2)',
    'Final program: sum(1, 2)',
    'Final program: ' + 'add(1, ' * 130 + '2' + ')' * 130,
])
def test_rejects_invalid_or_ambiguous_declarations(pilot, report, reply):
    _, _, compile_reply = pilot
    _, prediction, decision, cells = compile_reply(report, reply, stopped=True)
    assert decision == 'nested_rejected'
    assert prediction['program'] is None
    assert cells == []
