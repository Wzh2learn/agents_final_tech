"""Engineering controls for selection; fixtures are not scientific evidence."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/decision_probes.py'
spec = importlib.util.spec_from_file_location('decision_probes', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
STATE = 'a' * 64


def raw_plan():
    return {'state_sha256': STATE,
            'actions': [{'id': 'A', 'change': 'repair implementation'}, {'id': 'B', 'change': 'repair caller'}],
            'hypotheses': [{'id': 'H1', 'premise': 'first cause', 'action_id': 'A', 'weight': .45},
                           {'id': 'H2', 'premise': 'second cause, same repair', 'action_id': 'A', 'weight': .45},
                           {'id': 'H3', 'premise': 'caller violates contract', 'action_id': 'B', 'weight': .1}],
            'probes': [{'id': 'diagnostic', 'role': 'api_shape', 'python': 'print("probe")', 'cost': 1,
                        'predictions': {'H1': 'x', 'H2': 'y', 'H3': 'x'}},
                       {'id': 'decision', 'role': 'public_reproduction', 'python': 'print("probe")', 'cost': 1,
                        'predictions': {'H1': 'x', 'H2': 'x', 'H3': 'y'}}]}


def test_information_and_repair_action_can_choose_different_probes():
    plan = m.parse_plan(json.dumps(raw_plan()), STATE)
    assert m.select_probe(plan)['selected'] == 'decision'
    assert m.select_probe(plan, 'hypothesis_entropy')['selected'] == 'diagnostic'


def test_skip_when_uncertainty_does_not_change_repair_action():
    value = raw_plan()
    for item in value['hypotheses']:
        item['action_id'] = 'A'
    plan = m.parse_plan(json.dumps(value), STATE)
    assert m.select_probe(plan)['selected'] is None
    assert m.select_probe(plan, 'hypothesis_entropy')['selected'] is not None


def test_unknown_actual_outcome_does_not_manufacture_certainty():
    plan = m.parse_plan(json.dumps(raw_plan()), STATE)
    update = m.update_from_observation(plan, 'decision', 'not predicted')
    assert update['status'] == 'UNPREDICTED_OBSERVATION'
    assert update['hypotheses'] == plan['hypotheses']


@pytest.mark.parametrize('change', ['state', 'weight', 'prediction', 'python'])
def test_invalid_plans_rejected(change):
    value = raw_plan()
    if change == 'state': value['state_sha256'] = 'b' * 64
    if change == 'weight': value['hypotheses'][0]['weight'] = float('nan')
    if change == 'prediction': value['probes'][0]['predictions'].pop('H1')
    if change == 'python': value['probes'][0]['python'] = 'def invalid:'
    with pytest.raises((ValueError, SyntaxError)):
        m.parse_plan(json.dumps(value), STATE)
