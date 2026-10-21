"""Bounded deterministic query policies for the thin environment."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import itertools
import math
from typing import Dict, Iterable, List, Protocol, Sequence, Tuple

from .actor import (
    ActorInput,
    ChangeEvidence,
    DependencyEvidence,
    Evidence,
    EvidenceBundle,
    EvidenceKind,
    FinalAction,
    OutputAction,
    PolicyDecision,
    PolicyKind,
    PolicySpec,
    QueryTraceEntry,
    RepairDecision,
    TargetTestEvidence,
)


class PublicTools(Protocol):
    """Complete actor-facing query capability: exactly three call methods."""

    def inspect_dependency(self, node_id: str) -> DependencyEvidence:
        """Inspect one actor-visible dependency record."""

    def inspect_change(self, change_id: str) -> ChangeEvidence:
        """Inspect one actor-identified source change."""

    def run_target_test(self, output_id: str) -> TargetTestEvidence:
        """Run one actor-identified target test."""


class QueryTool(str, Enum):
    """Public query names used by policy choice records."""

    INSPECT_DEPENDENCY = "inspect_dependency"
    INSPECT_CHANGE = "inspect_change"
    RUN_TARGET_TEST = "run_target_test"


PUBLIC_TOOL_NAMES = tuple(tool.value for tool in QueryTool)


@dataclass(frozen=True)
class QueryChoice:
    """One possible public query."""

    tool: QueryTool
    target: str

    @property
    def key(self) -> str:
        """Return a stable query key."""
        return f"{self.tool.value}:{self.target}"

    def execute(self, tools: PublicTools, query_index: int) -> Evidence:
        """Execute one query and require the matching evidence variant."""
        if self.tool is QueryTool.INSPECT_DEPENDENCY:
            evidence = tools.inspect_dependency(self.target)
            if not isinstance(evidence, DependencyEvidence):
                raise TypeError("DEPENDENCY_TOOL_EVIDENCE_TYPE_MISMATCH")
        elif self.tool is QueryTool.INSPECT_CHANGE:
            evidence = tools.inspect_change(self.target)
            if not isinstance(evidence, ChangeEvidence):
                raise TypeError("CHANGE_TOOL_EVIDENCE_TYPE_MISMATCH")
        elif self.tool is QueryTool.RUN_TARGET_TEST:
            evidence = tools.run_target_test(self.target)
            if not isinstance(evidence, TargetTestEvidence):
                raise TypeError("TARGET_TEST_EVIDENCE_TYPE_MISMATCH")
        else:
            raise ValueError("UNSUPPORTED_QUERY_TOOL", self.tool)
        if evidence.query_index != query_index:
            raise ValueError("QUERY_INDEX_MISMATCH")
        return evidence


def candidate_queries(actor_input: ActorInput) -> Tuple[QueryChoice, ...]:
    """Return every legal query in stable tool and target order."""
    dependencies = tuple(
        QueryChoice(QueryTool.INSPECT_DEPENDENCY, node_id)
        for node_id in actor_input.node_ids
    )
    changes = tuple(
        QueryChoice(QueryTool.INSPECT_CHANGE, change.change_id)
        for change in actor_input.changes
    )
    tests = tuple(
        QueryChoice(QueryTool.RUN_TARGET_TEST, output_id)
        for output_id in actor_input.output_ids
    )
    return dependencies + changes + tests


def _stable_seed(actor_input: ActorInput, seed: int) -> int:
    digest = hashlib.sha256(
        f"{actor_input.scenario_id}:{seed}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def _deterministic_shuffle(
    values: Sequence[QueryChoice],
    actor_input: ActorInput,
    seed: int,
) -> Tuple[QueryChoice, ...]:
    items = list(values)
    state = _stable_seed(actor_input, seed)
    for index in range(len(items) - 1, 0, -1):
        state = (6364136223846793005 * state + 1442695040888963407) % (2**64)
        swap_index = state % (index + 1)
        items[index], items[swap_index] = items[swap_index], items[index]
    return tuple(items)


class _ImpactPosterior:
    """Actor-visible binary-output hypothesis distribution for query scoring."""

    def __init__(self, actor_input: ActorInput) -> None:
        self._actor_input = actor_input
        hypotheses = tuple(
            itertools.product((False, True), repeat=len(actor_input.output_ids))
        )
        self._hypotheses: Tuple[Tuple[bool, ...], ...] = hypotheses
        self._weights: Dict[Tuple[bool, ...], float] = {
            hypothesis: 1.0 / len(hypotheses) for hypothesis in hypotheses
        }

    def copy(self) -> "_ImpactPosterior":
        """Return an independent copy for hypothetical lookahead."""
        clone = _ImpactPosterior(self._actor_input)
        clone._weights = dict(self._weights)
        return clone

    @staticmethod
    def _entropy(probabilities: Iterable[float]) -> float:
        entropy = 0.0
        for probability in probabilities:
            if probability > 0.0:
                entropy -= probability * math.log2(probability)
        return entropy

    def entropy(self) -> float:
        """Return current binary hypothesis entropy."""
        return self._entropy(self._weights.values())

    def _likelihood(
        self,
        choice: QueryChoice,
        hypothesis: Tuple[bool, ...],
        outcome: str,
    ) -> float:
        any_impact = any(hypothesis)
        if choice.tool is QueryTool.RUN_TARGET_TEST:
            output_index = self._actor_input.output_ids.index(choice.target)
            needs_repair = hypothesis[output_index]
            if outcome == "fail":
                return 0.97 if needs_repair else 0.02
            return 0.03 if needs_repair else 0.98
        if choice.tool is QueryTool.INSPECT_CHANGE:
            if outcome == "delta":
                return 0.85 if any_impact else 0.25
            return 0.15 if any_impact else 0.75
        changed_nodes = {change.node_id for change in self._actor_input.changes}
        if choice.target in changed_nodes:
            reach_probability = 0.88 if any_impact else 0.15
        else:
            reach_probability = 0.35 if any_impact else 0.08
        return reach_probability if outcome == "reach" else 1.0 - reach_probability

    @staticmethod
    def _outcomes(choice: QueryChoice) -> Tuple[str, ...]:
        if choice.tool is QueryTool.RUN_TARGET_TEST:
            return ("fail", "pass")
        if choice.tool is QueryTool.INSPECT_CHANGE:
            return ("delta", "no_delta")
        return ("reach", "no_reach")

    def outcome_probability(self, choice: QueryChoice, outcome: str) -> float:
        """Return actor-model probability for one hypothetical query outcome."""
        probability = 0.0
        for hypothesis, weight in self._weights.items():
            probability += weight * self._likelihood(choice, hypothesis, outcome)
        return probability

    def condition(
        self,
        choice: QueryChoice,
        outcome: str,
    ) -> Tuple[float, "_ImpactPosterior"]:
        """Return outcome probability and a conditioned posterior copy."""
        unnormalized: Dict[Tuple[bool, ...], float] = {}
        outcome_probability = 0.0
        for hypothesis, weight in self._weights.items():
            likelihood = self._likelihood(choice, hypothesis, outcome)
            updated = weight * likelihood
            unnormalized[hypothesis] = updated
            outcome_probability += updated
        if outcome_probability <= 0.0:
            raise ValueError("ZERO_PROBABILITY_EVIDENCE_OUTCOME")
        posterior = self.copy()
        posterior._weights = {
            hypothesis: weight / outcome_probability
            for hypothesis, weight in unnormalized.items()
        }
        return outcome_probability, posterior

    def update(self, choice: QueryChoice, outcome: str) -> None:
        """Condition this posterior in place on an observed query outcome."""
        _, posterior = self.condition(choice, outcome)
        self._weights = posterior._weights

    def information_gain(self, choice: QueryChoice) -> float:
        """Return expected one-query entropy reduction in bits."""
        current_entropy = self.entropy()
        expected_entropy = 0.0
        for outcome in self._outcomes(choice):
            probability, posterior = self.condition(choice, outcome)
            expected_entropy += probability * posterior.entropy()
        return max(0.0, current_entropy - expected_entropy)


def _two_step_score(
    posterior: _ImpactPosterior,
    first: QueryChoice,
    remaining: Sequence[QueryChoice],
) -> float:
    first_gain = posterior.information_gain(first)
    expected_second_gain = 0.0
    for outcome in posterior._outcomes(first):
        probability, conditioned = posterior.condition(first, outcome)
        best_second = max(
            (conditioned.information_gain(second) for second in remaining),
            default=0.0,
        )
        expected_second_gain += probability * best_second
    return first_gain + expected_second_gain


class QueryPolicy:
    """Base interface for bounded query policies."""

    def __init__(self, policy_kind: PolicyKind, name: str) -> None:
        self.policy_kind = policy_kind
        self.name = name

    def run(self, actor_input: ActorInput, tools: PublicTools) -> PolicyDecision:
        """Return evidence and either fixed-repair input or a baseline override."""
        raise NotImplementedError


class NoCheckingPolicy(QueryPolicy):
    """Issue no checks and leave all output decisions to evidence replay."""

    def __init__(self) -> None:
        super().__init__(PolicyKind.NO_CHECK, PolicyKind.NO_CHECK.value)

    def run(self, actor_input: ActorInput, tools: PublicTools) -> PolicyDecision:
        """Return an empty evidence bundle."""
        return PolicyDecision(
            evidence=EvidenceBundle(actor_input, ()),
            action_override=None,
            query_trace=(),
        )


class RandomCheckingPolicy(QueryPolicy):
    """Sample public queries without replacement with a deterministic seed."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        super().__init__(
            PolicyKind.RANDOM_CHECK,
            f"{PolicyKind.RANDOM_CHECK.value}_seed_{seed}",
        )

    def run(self, actor_input: ActorInput, tools: PublicTools) -> PolicyDecision:
        """Execute a bounded deterministic random query sequence."""
        ordered = _deterministic_shuffle(
            candidate_queries(actor_input),
            actor_input,
            self.seed,
        )
        records: List[Evidence] = []
        trace: List[QueryTraceEntry] = []
        for choice in ordered[: actor_input.query_budget]:
            evidence = choice.execute(tools, len(records))
            records.append(evidence)
            trace.append(
                QueryTraceEntry(
                    query_key=choice.key,
                    result_key=evidence.result_key,
                    information_gain=0.0,
                )
            )
        return PolicyDecision(
            evidence=EvidenceBundle(actor_input, tuple(records)),
            action_override=None,
            query_trace=tuple(trace),
        )


class _AdaptiveInformationPolicy(QueryPolicy):
    """Shared deterministic information-gain query loop."""

    def __init__(self, policy_kind: PolicyKind, lookahead_steps: int) -> None:
        self.lookahead_steps = lookahead_steps
        super().__init__(policy_kind, policy_kind.value)

    def _select(
        self,
        posterior: _ImpactPosterior,
        remaining: Sequence[QueryChoice],
    ) -> Tuple[QueryChoice, float]:
        if self.lookahead_steps == 1:
            scores = [posterior.information_gain(choice) for choice in remaining]
            selected_index = max(
                range(len(remaining)),
                key=lambda index: (scores[index], -index),
            )
            return remaining[selected_index], scores[selected_index]
        scores = [
            _two_step_score(posterior, choice, remaining[:index] + remaining[index + 1 :])
            for index, choice in enumerate(remaining)
        ]
        selected_index = max(
            range(len(remaining)),
            key=lambda index: (scores[index], -index),
        )
        selected = remaining[selected_index]
        return selected, posterior.information_gain(selected)

    def run(self, actor_input: ActorInput, tools: PublicTools) -> PolicyDecision:
        """Execute unit-cost information-gain queries within the fixed budget."""
        posterior = _ImpactPosterior(actor_input)
        remaining = list(candidate_queries(actor_input))
        records: List[Evidence] = []
        trace: List[QueryTraceEntry] = []
        while remaining and len(records) < actor_input.query_budget:
            choice, information_gain = self._select(posterior, tuple(remaining))
            evidence = choice.execute(tools, len(records))
            records.append(evidence)
            trace.append(
                QueryTraceEntry(
                    query_key=choice.key,
                    result_key=evidence.result_key,
                    information_gain=information_gain,
                )
            )
            posterior.update(choice, evidence.result_key)
            remaining = [
                candidate for candidate in remaining if candidate.key != choice.key
            ]
        return PolicyDecision(
            evidence=EvidenceBundle(actor_input, tuple(records)),
            action_override=None,
            query_trace=tuple(trace),
        )


class UnitCostGreedyPolicy(_AdaptiveInformationPolicy):
    """Choose each query by unit-cost one-step expected information gain."""

    def __init__(self) -> None:
        super().__init__(PolicyKind.UNIT_COST_GREEDY, lookahead_steps=1)


class TwoStepLookaheadPolicy(_AdaptiveInformationPolicy):
    """Choose each query using expected best-next-query information gain."""

    def __init__(self) -> None:
        super().__init__(PolicyKind.TWO_STEP_LOOKAHEAD, lookahead_steps=2)


class FullRecomputePolicy(QueryPolicy):
    """Baseline that recomputes every output without issuing public queries."""

    def __init__(self) -> None:
        super().__init__(PolicyKind.FULL_RECOMPUTE, PolicyKind.FULL_RECOMPUTE.value)

    def run(self, actor_input: ActorInput, tools: PublicTools) -> PolicyDecision:
        """Return a direct all-output recompute action."""
        action = FinalAction(
            tuple(
                OutputAction(output_id, RepairDecision.RECOMPUTE)
                for output_id in actor_input.output_ids
            )
        )
        return PolicyDecision(
            evidence=EvidenceBundle(actor_input, ()),
            action_override=action,
            query_trace=(),
        )


def make_policy(spec: PolicySpec) -> QueryPolicy:
    """Construct one required policy from reproducible parameters."""
    if spec.policy_kind is PolicyKind.NO_CHECK:
        return NoCheckingPolicy()
    if spec.policy_kind is PolicyKind.RANDOM_CHECK:
        return RandomCheckingPolicy(spec.seed)
    if spec.policy_kind is PolicyKind.UNIT_COST_GREEDY:
        return UnitCostGreedyPolicy()
    if spec.policy_kind is PolicyKind.TWO_STEP_LOOKAHEAD:
        return TwoStepLookaheadPolicy()
    if spec.policy_kind is PolicyKind.FULL_RECOMPUTE:
        return FullRecomputePolicy()
    raise ValueError("UNSUPPORTED_POLICY_KIND", spec.policy_kind)
