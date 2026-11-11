"""Bounded expected sample information for paid paired utility audits.

This is a classical EVSI reference prototype, not an official SkillApt
implementation or evidence of a new effective Agent method. Four Dirichlet
categories represent paired task outcomes: both succeed, WITH only, WITHOUT
only, neither succeeds. The caller must supply matched, independently scored
task pairs and deduplicate task/source groups before updating.

Predictions assume a shared outcome distribution within the declared scope.
Execution-cost quotes are fixed during prospective enumeration; they are not
inferred from unseen outcomes. Zero execution quotes mean a success-only
calculation, not free execution. Forecast reuse counts must not use future
answers. Acquisition cost and the remaining budget use the same explicit unit.
This module neither spends a runtime budget nor executes tools or models.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Iterable


def _nonnegative(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{name} must be a finite nonnegative number')
    try:
        value = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f'{name} is outside the finite numeric range') from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{name} must be a finite nonnegative number')
    return value


def _audit_depth(value: int) -> int:
    if type(value) is not int or not 0 <= value <= 2:
        raise ValueError('max_audits must be an integer from 0 to 2')
    return value


@dataclass(frozen=True)
class PairedPosterior:
    alpha: tuple[float, float, float, float] = (1, 1, 1, 1)

    def __post_init__(self):
        if not isinstance(self.alpha, (tuple, list)) or len(self.alpha) != 4:
            raise ValueError('alpha needs four positive joint-outcome counts')
        values = tuple(_nonnegative('alpha', x) for x in self.alpha)
        if min(values) <= 0 or not math.isfinite(sum(values)):
            raise ValueError('alpha counts and their sum must be positive and finite')
        object.__setattr__(self, 'alpha', values)

    @property
    def probabilities(self) -> tuple[float, ...]:
        total = sum(self.alpha)
        return tuple(x / total for x in self.alpha)

    def observe(self, with_success: bool, without_success: bool) -> PairedPosterior:
        if type(with_success) is not bool or type(without_success) is not bool:
            raise ValueError('paired native task outcomes must both be boolean')
        index = {(True, True): 0, (True, False): 1,
                 (False, True): 2, (False, False): 3}[with_success, without_success]
        values = list(self.alpha)
        values[index] += 1
        return PairedPosterior(tuple(values))

    def utilities(self, *, with_cost: float = 0, without_cost: float = 0,
                  cost_weight: float = 0) -> tuple[float, float]:
        weight = _nonnegative('cost_weight', cost_weight)
        with_cost = _nonnegative('with_cost', with_cost)
        without_cost = _nonnegative('without_cost', without_cost)
        both, helped, harmed, _ = self.probabilities
        values = (both + helped - weight * with_cost,
                  both + harmed - weight * without_cost)
        if not all(math.isfinite(x) for x in values):
            raise ValueError('weighted execution costs exceed finite range')
        return values

    def preferred(self, **quotes: float) -> str:
        self.utilities(**quotes)  # Validate all quotes before cancelling common terms.
        advantage = (self.alpha[1] - self.alpha[2]) / sum(self.alpha)
        advantage -= quotes.get('cost_weight', 0) * (
            quotes.get('with_cost', 0) - quotes.get('without_cost', 0))
        return 'WITH' if advantage > 0 else 'WITHOUT'

    def sample_value(self, **quotes: float) -> float:
        current = max(self.utilities(**quotes))
        outcomes = ((True, True), (True, False), (False, True), (False, False))
        updated = [self.observe(*outcome) for outcome in outcomes]
        # A fixed optimal action has zero sample value by total expectation.
        # Avoid charging an audit on a positive floating-point cancellation residue.
        if all(p.preferred(**quotes) == self.preferred(**quotes) for p in updated):
            return 0.0
        prospective = math.fsum(prob * max(p.utilities(**quotes))
                                for prob, p in zip(self.probabilities, updated))
        value = prospective - current
        if value < -1e-12:
            raise ArithmeticError('sample value violated the nonnegative information bound')
        return max(0.0, value)


@dataclass(frozen=True)
class AuditOption:
    audit_id: str
    posterior: PairedPosterior
    expected_uses: float
    audit_cost: float
    with_cost: float = 0
    without_cost: float = 0

    def __post_init__(self):
        if not isinstance(self.audit_id, str) or not self.audit_id.strip():
            raise ValueError('audit_id must be a nonempty string')
        if not isinstance(self.posterior, PairedPosterior):
            raise ValueError('posterior must contain paired evidence')
        for field in ('expected_uses', 'audit_cost', 'with_cost', 'without_cost'):
            object.__setattr__(self, field, _nonnegative(field, getattr(self, field)))
        if self.audit_cost <= 0:
            raise ValueError('a newly purchased audit must have positive quoted cost')

    def net_gain(self, cost_weight: float) -> float:
        weight = _nonnegative('cost_weight', cost_weight)
        gain = self.expected_uses * self.posterior.sample_value(
            with_cost=self.with_cost, without_cost=self.without_cost, cost_weight=weight)
        gain -= weight * self.audit_cost
        if not math.isfinite(gain):
            raise ValueError('audit gain exceeds finite numeric range')
        return gain

    def plan_gain(self, *, cost_weight: float, remaining_budget: float,
                  max_audits: int = 2) -> float:
        """Value of stopping or buying up to two paid samples of this scope.

        This classical finite-horizon reference is not a joint planner across
        scopes. Each possible second audit pays its cost and must fit the
        remaining budget. Hypothetical observations never update live evidence.
        """
        depth = _audit_depth(max_audits)
        budget = _nonnegative('remaining_budget', remaining_budget)
        weight = _nonnegative('cost_weight', cost_weight)
        quotes = dict(with_cost=self.with_cost, without_cost=self.without_cost,
                      cost_weight=weight)
        outcomes = ((True, True), (True, False), (False, True), (False, False))

        def value(posterior: PairedPosterior, left: int, funds: float) -> float:
            if left == 0 or funds < self.audit_cost or self.expected_uses == 0:
                return 0.0
            improvement = self.expected_uses * posterior.sample_value(**quotes)
            improvement -= weight * self.audit_cost
            if left > 1:
                improvement += math.fsum(prob * value(posterior.observe(*outcome),
                                                       left - 1, funds - self.audit_cost)
                                         for prob, outcome in zip(posterior.probabilities, outcomes))
            if not math.isfinite(improvement):
                raise ValueError('audit plan exceeds finite numeric range')
            return max(0.0, improvement)

        return value(self.posterior, depth, budget)


@dataclass(frozen=True)
class AuditDecision:
    audit_id: str
    expected_net_gain: float
    quoted_cost: float


def select_audit(options: Iterable[AuditOption], *, remaining_budget: float,
                 cost_weight: float, max_audits: int = 1) -> AuditDecision | None:
    """Select at most one positive-value affordable audit; never execute it.

    The default is myopic; max_audits=2 provides the bounded reference for
    complementary evidence. Physical POST/token/time caps remain the execution
    controller's job. A quoted cost is for the first acquisition, not free data.
    """
    budget = _nonnegative('remaining_budget', remaining_budget)
    weight = _nonnegative('cost_weight', cost_weight)
    depth = _audit_depth(max_audits)
    seen = set()
    scored = []
    for option in options:
        if not isinstance(option, AuditOption):
            raise ValueError('each option must be an AuditOption')
        if option.audit_id in seen:
            raise ValueError('duplicate audit_id')
        seen.add(option.audit_id)
        if option.audit_cost > budget:
            continue
        gain = option.plan_gain(cost_weight=weight, remaining_budget=budget,
                                max_audits=depth)
        if gain > 0:
            scored.append(AuditDecision(option.audit_id, gain, option.audit_cost))
    if not scored:
        return None
    return min(scored, key=lambda x: (-x.expected_net_gain, x.quoted_cost, x.audit_id))
