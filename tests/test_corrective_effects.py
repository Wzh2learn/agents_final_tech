"""Behavioral checks for source-effect transfer, not empirical task results."""
import importlib.util
from pathlib import Path
import sys

import pytest

PATH = Path(__file__).parents[1] / 'research/agent_frontier_portfolio_20261029/corrective_skill_policy.py'
spec = importlib.util.spec_from_file_location('corrective_effects_under_test', PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def fitted(include_joint=True):
    policy = module.CorrectiveEffects()
    initial = dict(forward=True, reverse=False, decline=False, dispatch=False, scalar=True)
    for steps, repairs in [((), ()), (('decline',), ('decline', 'dispatch')),
                           (('reverse',), ('reverse',)),
                           (('decline', 'reverse'), ('decline', 'dispatch', 'reverse'))]:
        if len(steps) == 2 and not include_joint:
            continue
        after = dict(initial)
        after.update({k: True for k in repairs})
        policy.update('source-a', initial, steps, after, execution_valid=True)
    return policy, initial


def test_new_progress_vectors_choose_different_executed_subsets():
    policy, initial = fitted()
    joint = policy.choose(initial, initial, source_group='new-task', heldout=True)
    assert joint['steps'] == ('decline', 'reverse')
    current = dict(initial, reverse=True)
    assert policy.choose(current, current, source_group='new-task')['steps'] == ('decline',)
    current = dict(initial, decline=True, dispatch=True)
    assert policy.choose(current, current, source_group='new-task')['steps'] == ('reverse',)
    assert len(policy.training_sources) == 1


def test_no_unobserved_joint_effect_is_invented_from_single_steps():
    policy, initial = fitted(include_joint=False)
    assert policy.choose(initial, initial, source_group='new-task') is None


def test_observed_regression_blocks_a_plan_even_when_target_would_pass():
    policy = module.CorrectiveEffects()
    policy.update('source', dict(target=False, preserved=True), ('edit',),
                  dict(target=True, preserved=False), execution_valid=True)
    assert policy.choose(dict(target=False, preserved=True), ['target'], source_group='new') is None


def test_conflicting_effects_or_unknown_behavior_fall_back():
    policy, initial = fitted()
    policy.update('source-b', initial, ('decline',), initial, execution_valid=True)
    current = dict(initial, reverse=True)
    # Joint is still an independently observed valid alternative.
    assert policy.choose(current, current, source_group='new')['steps'] == ('decline', 'reverse')
    current['unknown_requirement'] = False
    assert policy.choose(current, current, source_group='new') is None


def test_terminal_and_provenance_are_separate_from_learning():
    policy, initial = fitted()
    with pytest.raises(ValueError, match='source group'):
        policy.choose(initial, initial, source_group='source-a', heldout=True)
    terminal = policy.choose(dict.fromkeys(initial, True), initial, source_group='new')
    assert terminal['terminal'] and terminal['steps'] == ()


def test_invalid_execution_and_changed_empty_intervention_do_not_train():
    policy = module.CorrectiveEffects()
    assert not policy.update('source', {'x': False}, ('edit',), {'x': True}, execution_valid=False)
    assert not policy.rows
    with pytest.raises(ValueError, match='empty intervention'):
        policy.update('source', {'x': False}, (), {'x': True}, execution_valid=True)
    with pytest.raises(ValueError, match='booleans'):
        policy.update('source', {'x': False}, ('edit',), {'x': 1}, execution_valid=True)


def test_contract_guards_preserve_unknowns_and_match_strong_positive_only_rule():
    learner = module.ContractGuards(('distinct', 'lazy'))
    for x, y in [((False, False), {'native': False, 'legacy': None}),
                 ((True, False), {'native': True, 'legacy': False}),
                 ((True, True), {'native': True, 'legacy': True})]:
        learner.update(dict(zip(learner.features, x)), y)
    unseen = {'distinct': False, 'lazy': True}
    assert learner.predict(unseen, ('native', 'legacy')) is False
    assert learner.positive_only(unseen, ('native', 'legacy')) is False
    # Collapsing all outcomes loses which native constraint failed. This is a
    # hypothesis comparison, not an observed execution label for the new row.
    scalar = module.ContractGuards(learner.features)
    for x, y in learner.rows:
        scalar.update(x, {'joint': module.joint_outcome(y.values())})
    assert scalar.predict(unseen, ('joint',)) is True
    assert module.joint_outcome([True, None]) is None
    assert module.joint_outcome([False, None]) is False


def test_guard_ambiguity_conflicts_and_feedback_update_do_not_invent_certainty():
    learner = module.ContractGuards(('a', 'b'))
    learner.update({'a': False, 'b': False}, {'ok': False})
    learner.update({'a': True, 'b': True}, {'ok': True})
    assert learner.predict({'a': True, 'b': False}, ('ok',)) is None
    learner.update({'a': True, 'b': False}, {'ok': False})
    assert learner.guards('ok') == ((('b', True),),)
    assert learner.predict({'a': None, 'b': True}, ('ok',)) is True
    assert learner.predict({'a': True, 'b': None}, ('ok',)) is None
    learner.update({'a': True, 'b': True}, {'ok': False})
    assert learner.guards('ok') == ()
    assert learner.predict({'a': True, 'b': True}, ('ok',)) is None
    assert learner.predict({'a': True, 'b': True}, ('unobserved',)) is None
    with pytest.raises(ValueError):
        learner.update({'a': True, 'b': 1}, {'ok': True})
    with pytest.raises(ValueError):
        learner.update({'a': True, 'b': False, 'source_id': 'leak'}, {'ok': True})
