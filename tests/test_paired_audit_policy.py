"""Synthetic mathematical controls, not native Agent experiment results."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'))
from paired_audit_policy import AuditOption, PairedPosterior, select_audit


def test_uniform_sample_value_matches_independent_rational_enumeration():
    # Order: both pass, WITH only, WITHOUT only, neither passes.
    outcomes = ((1, 1), (1, 0), (0, 1), (0, 0))
    posterior = PairedPosterior()
    expected = Fraction(0)
    for observed, (with_ok, without_ok) in enumerate(outcomes):
        counts = [1, 1, 1, 1]
        counts[observed] += 1
        with_value = Fraction(counts[0] + counts[1], 5)
        without_value = Fraction(counts[0] + counts[2], 5)
        expected += Fraction(1, 4) * max(with_value, without_value)
        assert posterior.observe(bool(with_ok), bool(without_ok)).alpha == tuple(counts)
    assert expected - Fraction(1, 2) == Fraction(1, 20)
    assert posterior.sample_value() == pytest.approx(float(Fraction(1, 20)))
    assert posterior.alpha == (1, 1, 1, 1), 'prospective scoring must not add observations'


def test_sample_value_and_tie_choice_match_rational_grid():
    for counts in product(range(1, 4), repeat=4):
        total = sum(counts)
        for with_cost, without_cost in ((0, 0), (1, 0), (0, 1), (1, 2)):
            with_value = Fraction(counts[0] + counts[1], total) - Fraction(with_cost, 4)
            without_value = Fraction(counts[0] + counts[2], total) - Fraction(without_cost, 4)
            future = Fraction(0)
            for index in range(4):
                updated = list(counts)
                updated[index] += 1
                values = (Fraction(updated[0] + updated[1], total + 1) - Fraction(with_cost, 4),
                          Fraction(updated[0] + updated[2], total + 1) - Fraction(without_cost, 4))
                future += Fraction(counts[index], total) * max(values)
            posterior = PairedPosterior(counts)
            quotes = dict(with_cost=with_cost, without_cost=without_cost, cost_weight=.25)
            assert posterior.sample_value(**quotes) == pytest.approx(
                float(future - max(with_value, without_value)), abs=1e-13)
            expected = 'WITH' if with_value > without_value else 'WITHOUT'
            assert posterior.preferred(**quotes) == expected, (counts, quotes)


def test_shared_probability_cancels_before_exact_cost_tie_comparison():
    posterior = PairedPosterior((1, 6, 3, 2))
    assert Fraction(6 - 3, 12) - Fraction(1, 4) == 0
    assert posterior.preferred(with_cost=1, cost_weight=.25) == 'WITHOUT'


def test_no_changed_decision_has_exactly_zero_information_value():
    posterior = PairedPosterior((1, 1, 2, 5))
    assert all(posterior.observe(*o).preferred() == 'WITHOUT'
               for o in ((True, True), (True, False), (False, True), (False, False)))
    assert posterior.sample_value() == 0


def test_shared_failure_is_not_evidence_that_skill_caused_failure():
    helped = PairedPosterior().observe(True, False)
    shared_failure = helped.observe(False, False)
    assert helped.preferred() == shared_failure.preferred() == 'WITH'
    assert shared_failure.alpha == (1, 2, 1, 2)
    harmed = PairedPosterior().observe(False, True)
    assert harmed.preferred() == 'WITHOUT'


def test_horizon_and_paid_acquisition_change_the_decision():
    posterior = PairedPosterior()
    short = AuditOption('short', posterior, expected_uses=1, audit_cost=2)
    long = AuditOption('long', posterior, expected_uses=10, audit_cost=2)
    assert select_audit([short], remaining_budget=2, cost_weight=.1) is None
    selected = select_audit([long], remaining_budget=2, cost_weight=.1)
    assert selected is not None and selected.audit_id == 'long'
    assert selected.expected_net_gain == pytest.approx(.3)
    assert select_audit([long], remaining_budget=1, cost_weight=.1) is None
    assert select_audit([AuditOption('zero', posterior, 0, 2)], remaining_budget=2,
                        cost_weight=.1) is None


def test_audit_cannot_change_a_dominant_choice_so_it_is_not_bought():
    posterior = PairedPosterior((1, 20, 1, 1))
    assert posterior.preferred() == 'WITH'
    assert posterior.sample_value() == pytest.approx(0, abs=1e-14)
    assert select_audit([AuditOption('dominant', posterior, 10000, 1)],
                        remaining_budget=100, cost_weight=.1) is None


def test_execution_costs_are_included_and_ties_abstain():
    posterior = PairedPosterior()
    assert posterior.preferred() == 'WITHOUT'
    assert posterior.preferred(with_cost=2, without_cost=0, cost_weight=.1) == 'WITHOUT'
    assert posterior.preferred(with_cost=0, without_cost=2, cost_weight=.1) == 'WITH'


@pytest.mark.parametrize('bad', [None, 1, 0, 'false'])
def test_missing_or_non_boolean_task_outcomes_are_rejected(bad):
    with pytest.raises(ValueError, match='boolean'):
        PairedPosterior().observe(bad, True)


@pytest.mark.parametrize('bad', [None, -1, float('inf'), float('nan'), True])
def test_unknown_or_invalid_cost_is_not_treated_as_free(bad):
    with pytest.raises(ValueError):
        AuditOption('bad', PairedPosterior(), 1, bad)


def test_audit_ids_are_unique_and_ties_are_deterministic():
    p = PairedPosterior()
    a = AuditOption('a', p, 10, 1)
    b = AuditOption('b', p, 10, 1)
    assert select_audit([b, a], remaining_budget=1, cost_weight=.1).audit_id == 'a'
    with pytest.raises(ValueError, match='duplicate'):
        select_audit([a, a], remaining_budget=2, cost_weight=.1)


def test_paid_two_step_reference_can_escape_the_myopic_lock():
    # An initially helpful pair creates a one-observation dead zone.
    posterior = PairedPosterior((1, 2, 1, 1))
    option = AuditOption('learn', posterior, expected_uses=1, audit_cost=1)
    assert select_audit([option], remaining_budget=2, cost_weight=.002) is None
    selected = select_audit([option], remaining_budget=2, cost_weight=.002, max_audits=2)
    assert selected is not None
    # Buy once; only if WITHOUT alone succeeds (probability 1/5), buy again.
    expected = Fraction(1, 105) - Fraction(1, 500) * Fraction(6, 5)
    assert selected.expected_net_gain == pytest.approx(float(expected))
    assert select_audit([option], remaining_budget=1, cost_weight=.002,
                        max_audits=2) is None, 'lookahead must pay both audits'


@pytest.mark.parametrize('depth', [-1, 3, True])
def test_lookahead_is_a_bounded_reference_not_an_unbounded_search(depth):
    with pytest.raises(ValueError, match='max_audits'):
        select_audit([], remaining_budget=1, cost_weight=.1, max_audits=depth)
