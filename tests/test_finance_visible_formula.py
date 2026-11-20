from pathlib import Path

import pytest


@pytest.fixture
def recover(monkeypatch):
    pilot = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(pilot))
    from visible_formula import recover_formula

    return recover_formula


def public(*numbers):
    return {'dataset': 'finqa', 'id': 'example/0', 'report': 'example', 'question': 'What is the difference?',
            'table': [['Metric', 'Amount'], *[[f'Measure {name}', number] for name, number
                                            in zip('abcdefgh', numbers)]],
            'pre_text': [], 'post_text': []}


def test_free_formula_preserves_the_reported_value_and_handles_leading_decimals(recover):
    free, candidate, counts = recover(public('.5', '.6'), 'Calculation: .5 + .6 = 1.1\nFinal answer: 1.1')
    assert free['answer'] == 1.1 and free['program'] is None
    assert candidate['program'] == 'add(0.5, 0.6)'
    assert counts['grounded_equal_programs'] == 1


@pytest.mark.parametrize(('numbers', 'worked_answer', 'grounded'), [
    (('11', '7'), '11 - 7 = 4\nFinal answer: 5', 0),
    (('11', '7', '11'), '11 - 7 = 4\nFinal answer: 4', 0),
    (('11', '7', '14', '10'), '11 - 7 = 4\n14 - 10 = 4\nFinal answer: 4', 2),
])
def test_free_formula_rejects_mismatch_ambiguous_sources_and_multiple_programs(recover, numbers, worked_answer, grounded):
    _, candidate, counts = recover(public(*numbers), worked_answer)
    assert candidate is None
    assert counts['grounded_equal_programs'] == grounded
