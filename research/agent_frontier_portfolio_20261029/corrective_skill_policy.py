"""Development prototype: learn conditional preferences over executable repairs.

This is a small pairwise learner, not an empirical claim or a novel loss.
Training labels describe complete segments plus continuation, never first actions.
Only pre-decision public conditions are model features. Snapshot/source identifiers
are admission metadata and are deliberately absent from the feature map.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


CONDITIONS = frozenset({"feedback_kind", "call_arity", "return_arity", "operation_kind", "public_check_kind"})
FEEDBACK_CONDITIONS = frozenset({"feedback_kind", "public_check_kind"})


@dataclass(frozen=True)
class Context:
    snapshot: str
    source_group: str
    conditions: tuple[tuple[str, str], ...]

    def __post_init__(self):
        keys = [k for k, _ in self.conditions]
        if not self.snapshot or not self.source_group or len(keys) != len(set(keys)):
            raise ValueError("missing provenance or duplicate condition")
        if not set(keys) <= CONDITIONS or any(not isinstance(v, str) or len(v) > 80 for _, v in self.conditions):
            raise ValueError("only admitted pre-decision observable conditions are allowed")


@dataclass(frozen=True)
class Segment:
    identifier: str
    family: str
    # Each entry is a concrete native Bash command with its workspace directory.
    commands: tuple[tuple[str, str], ...]
    exit_condition: str

    def __post_init__(self):
        if not self.identifier or not self.family or not self.commands or not self.exit_condition:
            raise ValueError("a segment needs concrete executable steps and an exit condition")
        for command, workdir in self.commands:
            if not command.strip() or workdir != "/workspace":
                raise ValueError("unbound command or workspace")


@dataclass(frozen=True)
class FamilyProposal:
    """Rank-equivalent alternatives, not a certificate of equal behavior.

    The caller binds and executes one member, then checks its actual outcome.
    Snapshot identity is an execution guard, never a prediction feature.
    """

    snapshot: str
    family: str
    alternatives: tuple[Segment, ...]
    score: float

    def select(self, identifier, *, snapshot):
        if snapshot != self.snapshot:
            raise ValueError("proposal does not bind the current snapshot")
        for segment in self.alternatives:
            if segment.identifier == identifier:
                return segment
        raise ValueError("selected segment is outside the proposal")


@dataclass(frozen=True)
class Outcome:
    snapshot: str
    model: str
    continuation: str
    budget: str
    execution_valid: bool
    target_success: bool
    regression_preserved: bool
    total_tokens: int | None

    def __post_init__(self):
        if not all((self.snapshot, self.model, self.continuation, self.budget)):
            raise ValueError("missing outcome provenance")
        if self.total_tokens is not None and (type(self.total_tokens) is not int or self.total_tokens < 0):
            raise ValueError("cost must be a nonnegative token count or unknown")

    @property
    def full_success(self):
        return self.target_success and self.regression_preserved


def preference(context, a, b):
    """Return +1/-1/None, with success ahead of cost; no common-failure label."""
    if a.snapshot != context.snapshot or b.snapshot != context.snapshot:
        raise ValueError("outcomes are not from the same admitted pre-correction snapshot")
    if (a.model, a.continuation, a.budget) != (b.model, b.continuation, b.budget):
        raise ValueError("paired outcomes must share model, continuation policy and budget")
    if not a.execution_valid or not b.execution_valid:
        return None
    if a.full_success != b.full_success:
        return 1 if a.full_success else -1
    if not a.full_success:
        return None
    if a.total_tokens is None or b.total_tokens is None or a.total_tokens == b.total_tokens:
        return None
    if min(a.total_tokens, b.total_tokens) < 0:
        raise ValueError("negative cost")
    return 1 if a.total_tokens < b.total_tokens else -1


def features(context, segment, *, use_feedback=True, use_environment=True):
    """Interactions permit opposite segment preferences under the same feedback."""
    f = {("family", segment.family): 1.0}
    conditions = dict(context.conditions)
    feedback = [(k,v) for k,v in conditions.items() if k in FEEDBACK_CONDITIONS] if use_feedback else []
    for key,value in feedback:
        f[("feedback",key,value,segment.family)] = 1.0
    if use_environment:
        for key, value in context.conditions:
            if key in FEEDBACK_CONDITIONS:
                continue
            f[("environment", key, value, segment.family)] = 1.0
            for fk,fv in feedback:
                f[("joint",fk,fv,key,value,segment.family)] = 1.0
    return f


class ConditionalRepairPolicy:
    """Sparse logistic preference updates; the actor still executes the segment.

    Formed segments and feedback are shared with comparison methods. This class
    neither generates extra candidates nor reads any deployment grading labels.
    """

    def __init__(self, *, learning_rate=.2, regularization=.001, use_feedback=True, use_environment=True):
        if learning_rate <= 0 or regularization < 0:
            raise ValueError("invalid optimizer settings")
        self.learning_rate, self.regularization = learning_rate, regularization
        self.use_feedback, self.use_environment = use_feedback, use_environment
        self.weights = {}
        self.training_sources = set()
        self.supported_contexts = set()
        self.trained_families = set()
        self.updates = 0

    def _features(self, context, segment):
        return features(context, segment, use_feedback=self.use_feedback, use_environment=self.use_environment)

    def score(self, context, segment):
        return sum(self.weights.get(k, 0.) * v for k, v in self._features(context, segment).items())

    def _support_key(self, context):
        return tuple(sorted((k,v) for k,v in context.conditions
            if (self.use_feedback if k in FEEDBACK_CONDITIONS else self.use_environment)))

    def update(self, context, a, b, outcome_a, outcome_b):
        label = preference(context, outcome_a, outcome_b)
        if label is None:
            return False
        fa, fb = self._features(context, a), self._features(context, b)
        delta = {k: label * (fa.get(k, 0.) - fb.get(k, 0.)) for k in fa.keys() | fb.keys()}
        if not any(delta.values()):
            return False
        margin = max(-60., min(60., sum(self.weights.get(k, 0.) * v for k, v in delta.items())))
        gradient = 1. / (1. + math.exp(margin))
        for k in self.weights:
            self.weights[k] *= 1. - self.learning_rate * self.regularization
        for k, v in delta.items():
            if v:
                self.weights[k] = self.weights.get(k,0.) + self.learning_rate * gradient * v
        self.training_sources.add(context.source_group)
        self.supported_contexts.add(self._support_key(context))
        self.trained_families.update((a.family,b.family))
        self.updates += 1
        return True

    def choose(self, context, candidates, *, heldout=False):
        if heldout and context.source_group in self.training_sources:
            raise ValueError("source group already used to fit the policy")
        candidates = tuple(candidates)
        if (not candidates or self.updates == 0 or self._support_key(context) not in self.supported_contexts
                or any(s.family not in self.trained_families for s in candidates)):
            return None  # Ordinary correction fallback, not free candidate execution.
        scored = [(self.score(context, s), s) for s in candidates]
        scored.sort(key=lambda pair: (-pair[0], pair[1].identifier))
        if len(scored) > 1 and abs(scored[0][0] - scored[1][0]) < 1e-12:
            return None
        return scored[0][1]

    def propose(self, context, candidates, *, heldout=False):
        """Select a family while preserving its concrete execution alternatives.

        This reuses the scalar reference's support, provenance and family scores.
        A tie across different families still falls back to ordinary correction.
        Presentation order within a family does not imply an outcome preference.
        """
        grouped = {}
        identifiers = set()
        for segment in candidates:
            if segment.identifier in identifiers:
                raise ValueError("ambiguous segment identifier")
            identifiers.add(segment.identifier)
            grouped.setdefault(segment.family, []).append(segment)
        representatives = [members[0] for members in grouped.values()]
        selected = self.choose(context, representatives, heldout=heldout)
        if selected is None:
            return None
        alternatives = tuple(sorted(grouped[selected.family], key=lambda s: s.identifier))
        return FamilyProposal(context.snapshot, selected.family, alternatives, self.score(context, selected))
