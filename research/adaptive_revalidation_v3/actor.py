"""Actor-safe DTOs and serialization for the V3 capability boundary.

This module is intentionally free of graph, fixture, trace, and evaluator
classes.  Policy processes import only this module and ``policies``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union


NodeId = str
OutputId = str
ScenarioId = str
Value = float


def canonical_json(value: Any) -> str:
    """Return deterministic, non-finite-free JSON."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Encode :func:`canonical_json` as UTF-8 bytes."""
    return canonical_json(value).encode("utf-8")


def rounded(value: float) -> float:
    """Round serialized metrics for stable receipts."""
    return round(float(value), 12)


class RepairDecision(str, Enum):
    """Commitment made by a policy or the fixed repairer for one output."""

    KEEP = "keep"
    RECOMPUTE = "recompute"
    ABSTAIN = "abstain"


class EvidenceKind(str, Enum):
    """Public query evidence variants."""

    DEPENDENCY = "dependency"
    CHANGE = "change"
    TARGET_TEST = "target_test"


class PolicyKind(str, Enum):
    """Required bounded policy families."""

    NO_CHECK = "no_check"
    RANDOM_CHECK = "random_check"
    UNIT_COST_GREEDY = "unit_cost_greedy"
    TWO_STEP_LOOKAHEAD = "two_step_lookahead"
    FULL_RECOMPUTE = "full_recompute"


@dataclass(frozen=True)
class ChangeSummary:
    """Actor-visible identifier for one source change, with no state values."""

    change_id: str
    node_id: NodeId
    change_kind: str

    def __post_init__(self) -> None:
        if not self.change_id or not self.node_id or not self.change_kind:
            raise ValueError("CHANGE_SUMMARY_FIELD_EMPTY")

    def as_dict(self) -> Dict[str, str]:
        """Return the actor-visible serializable form."""
        return {
            "change_id": self.change_id,
            "change_kind": self.change_kind,
            "node_id": self.node_id,
        }


@dataclass(frozen=True)
class ActorInput:
    """Complete policy input; evaluator state is deliberately absent."""

    scenario_id: ScenarioId
    node_ids: Tuple[NodeId, ...]
    output_ids: Tuple[OutputId, ...]
    changes: Tuple[ChangeSummary, ...]
    query_budget: int

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("SCENARIO_ID_EMPTY")
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("DUPLICATE_ACTOR_NODE_ID")
        if len(set(self.output_ids)) != len(self.output_ids):
            raise ValueError("DUPLICATE_ACTOR_OUTPUT_ID")
        if not self.node_ids:
            raise ValueError("ACTOR_NODE_CATALOG_EMPTY")
        if not self.output_ids:
            raise ValueError("ACTOR_OUTPUT_CATALOG_EMPTY")
        change_ids = [change.change_id for change in self.changes]
        if len(set(change_ids)) != len(change_ids):
            raise ValueError("DUPLICATE_CHANGE_ID")
        if {change.node_id for change in self.changes} - set(self.node_ids):
            raise ValueError("ACTOR_CHANGE_NODE_UNKNOWN")
        if self.query_budget < 0:
            raise ValueError("NEGATIVE_QUERY_BUDGET")

    def as_dict(self) -> Dict[str, Any]:
        """Return only actor-visible fields."""
        return {
            "changes": [change.as_dict() for change in self.changes],
            "node_ids": list(self.node_ids),
            "output_ids": list(self.output_ids),
            "query_budget": self.query_budget,
            "scenario_id": self.scenario_id,
        }


@dataclass(frozen=True)
class DependencyEvidence:
    """Response from ``inspect_dependency`` using visible dependency records."""

    node_id: NodeId
    observed_dependencies: Tuple[NodeId, ...]
    reachable_outputs: Tuple[OutputId, ...]
    query_index: int
    cost: int = 1
    kind: EvidenceKind = EvidenceKind.DEPENDENCY

    @property
    def result_key(self) -> str:
        """Return the discrete outcome used by policy scoring."""
        return "reach" if self.reachable_outputs else "no_reach"

    @property
    def query_key(self) -> str:
        """Return a stable evidence query key."""
        return f"{self.kind.value}:{self.node_id}"

    def as_dict(self) -> Dict[str, Any]:
        """Return the public evidence payload."""
        return {
            "cost": self.cost,
            "kind": self.kind.value,
            "node_id": self.node_id,
            "observed_dependencies": list(self.observed_dependencies),
            "query_index": self.query_index,
            "reachable_outputs": list(self.reachable_outputs),
            "result_key": self.result_key,
        }


@dataclass(frozen=True)
class ChangeEvidence:
    """Response from ``inspect_change`` with public source values."""

    change_id: str
    node_id: NodeId
    change_kind: str
    before_value: Value
    after_value: Value
    delta: Value
    query_index: int
    cost: int = 1
    kind: EvidenceKind = EvidenceKind.CHANGE

    @property
    def result_key(self) -> str:
        """Return the discrete outcome used by policy scoring."""
        return "delta" if abs(self.delta) > 1e-12 else "no_delta"

    @property
    def query_key(self) -> str:
        """Return a stable evidence query key."""
        return f"{self.kind.value}:{self.change_id}"

    def as_dict(self) -> Dict[str, Any]:
        """Return the public evidence payload."""
        return {
            "after_value": rounded(self.after_value),
            "before_value": rounded(self.before_value),
            "change_id": self.change_id,
            "change_kind": self.change_kind,
            "cost": self.cost,
            "delta": rounded(self.delta),
            "kind": self.kind.value,
            "node_id": self.node_id,
            "query_index": self.query_index,
            "result_key": self.result_key,
        }


@dataclass(frozen=True)
class TargetTestEvidence:
    """Response from ``run_target_test`` without observed values."""

    output_id: OutputId
    passed: bool
    query_index: int
    cost: int = 1
    kind: EvidenceKind = EvidenceKind.TARGET_TEST

    @property
    def result_key(self) -> str:
        """Return the discrete outcome used by policy scoring."""
        return "pass" if self.passed else "fail"

    @property
    def query_key(self) -> str:
        """Return a stable evidence query key."""
        return f"{self.kind.value}:{self.output_id}"

    def as_dict(self) -> Dict[str, Any]:
        """Return the public evidence payload."""
        return {
            "cost": self.cost,
            "kind": self.kind.value,
            "output_id": self.output_id,
            "passed": self.passed,
            "query_index": self.query_index,
            "result_key": self.result_key,
        }


Evidence = Union[DependencyEvidence, ChangeEvidence, TargetTestEvidence]


@dataclass(frozen=True)
class EvidenceBundle:
    """Ordered policy evidence plus the actor-visible policy context."""

    actor_input: ActorInput
    records: Tuple[Evidence, ...]

    def __post_init__(self) -> None:
        indices = [record.query_index for record in self.records]
        if indices != list(range(len(indices))):
            raise ValueError("EVIDENCE_QUERY_INDEX_NOT_SEQUENTIAL")
        query_keys = [record.query_key for record in self.records]
        if len(set(query_keys)) != len(query_keys):
            raise ValueError("DUPLICATE_EVIDENCE_QUERY")

    @property
    def query_cost(self) -> int:
        """Return the total unit query cost."""
        return sum(record.cost for record in self.records)

    def as_dict(self) -> Dict[str, Any]:
        """Return actor context and public query evidence only."""
        return {
            "actor_input": self.actor_input.as_dict(),
            "records": [record.as_dict() for record in self.records],
        }


@dataclass(frozen=True)
class QueryTraceEntry:
    """Policy-only audit entry; never passed to the fixed repairer."""

    query_key: str
    result_key: str
    information_gain: float

    def as_dict(self) -> Dict[str, Any]:
        """Return the stable trace representation."""
        return {
            "information_gain": rounded(self.information_gain),
            "query_key": self.query_key,
            "result_key": self.result_key,
        }


@dataclass(frozen=True)
class OutputAction:
    """One output-level final action."""

    output_id: OutputId
    decision: RepairDecision

    def as_dict(self) -> Dict[str, str]:
        """Return the stable action representation."""
        return {"decision": self.decision.value, "output_id": self.output_id}


@dataclass(frozen=True)
class FinalAction:
    """Complete output-level action, including explicit abstentions."""

    outputs: Tuple[OutputAction, ...]

    def __post_init__(self) -> None:
        if len({item.output_id for item in self.outputs}) != len(self.outputs):
            raise ValueError("DUPLICATE_FINAL_ACTION_OUTPUT")

    def decision_for(self, output_id: OutputId) -> RepairDecision:
        """Return the decision for one output."""
        for item in self.outputs:
            if item.output_id == output_id:
                return item.decision
        raise KeyError(output_id)

    def as_dict(self) -> Dict[str, str]:
        """Return a mapping representation sorted by output identifier."""
        return {
            item.output_id: item.decision.value
            for item in sorted(self.outputs, key=lambda entry: entry.output_id)
        }


@dataclass(frozen=True)
class PolicyDecision:
    """Output of a query policy before fixed-repairer replay."""

    evidence: EvidenceBundle
    action_override: Optional[FinalAction]
    query_trace: Tuple[QueryTraceEntry, ...]

    def as_dict(self) -> Dict[str, Any]:
        """Return the serialized actor-safe decision."""
        return {
            "action_override": (
                None if self.action_override is None else self.action_override.as_dict()
            ),
            "evidence": self.evidence.as_dict(),
            "query_trace": [entry.as_dict() for entry in self.query_trace],
        }


@dataclass(frozen=True)
class PolicySpec:
    """Reproducible policy construction parameters."""

    policy_kind: PolicyKind
    seed: int = 0

    @property
    def name(self) -> str:
        """Return the stable policy display name."""
        if self.policy_kind is PolicyKind.RANDOM_CHECK:
            return f"{self.policy_kind.value}_seed_{self.seed}"
        return self.policy_kind.value

    def as_dict(self) -> Dict[str, Any]:
        """Return the serialized policy specification."""
        return {"policy_kind": self.policy_kind.value, "seed": self.seed}


def evidence_from_dict(raw: Mapping[str, Any]) -> Evidence:
    kind = EvidenceKind(str(raw["kind"]))
    if kind is EvidenceKind.DEPENDENCY:
        return DependencyEvidence(
            node_id=str(raw["node_id"]),
            observed_dependencies=tuple(str(v) for v in raw["observed_dependencies"]),
            reachable_outputs=tuple(str(v) for v in raw["reachable_outputs"]),
            query_index=int(raw["query_index"]),
            cost=int(raw["cost"]),
        )
    if kind is EvidenceKind.CHANGE:
        return ChangeEvidence(
            change_id=str(raw["change_id"]),
            node_id=str(raw["node_id"]),
            change_kind=str(raw["change_kind"]),
            before_value=float(raw["before_value"]),
            after_value=float(raw["after_value"]),
            delta=float(raw["delta"]),
            query_index=int(raw["query_index"]),
            cost=int(raw["cost"]),
        )
    return TargetTestEvidence(
        output_id=str(raw["output_id"]),
        passed=bool(raw["passed"]),
        query_index=int(raw["query_index"]),
        cost=int(raw["cost"]),
    )


def actor_input_from_dict(raw: Mapping[str, Any]) -> ActorInput:
    """Deserialize and validate one actor input."""
    return ActorInput(
        scenario_id=str(raw["scenario_id"]),
        node_ids=tuple(str(v) for v in raw["node_ids"]),
        output_ids=tuple(str(v) for v in raw["output_ids"]),
        changes=tuple(
            ChangeSummary(
                change_id=str(item["change_id"]),
                node_id=str(item["node_id"]),
                change_kind=str(item["change_kind"]),
            )
            for item in raw["changes"]
        ),
        query_budget=int(raw["query_budget"]),
    )


def final_action_from_dict(raw: Mapping[str, Any]) -> FinalAction:
    """Deserialize one complete actor action."""
    return FinalAction(
        tuple(
            OutputAction(str(output_id), RepairDecision(str(decision)))
            for output_id, decision in raw.items()
        )
    )


def policy_decision_from_dict(raw: Mapping[str, Any]) -> PolicyDecision:
    """Deserialize one policy decision from the RPC payload."""
    actor_input = actor_input_from_dict(raw["evidence"]["actor_input"])
    records = tuple(evidence_from_dict(item) for item in raw["evidence"]["records"])
    action_override = raw["action_override"]
    return PolicyDecision(
        evidence=EvidenceBundle(actor_input, records),
        action_override=(
            None if action_override is None else final_action_from_dict(action_override)
        ),
        query_trace=tuple(
            QueryTraceEntry(
                query_key=str(item["query_key"]),
                result_key=str(item["result_key"]),
                information_gain=float(item["information_gain"]),
            )
            for item in raw["query_trace"]
        ),
    )


def policy_spec_from_dict(raw: Mapping[str, Any]) -> PolicySpec:
    """Deserialize one policy specification."""
    return PolicySpec(
        policy_kind=PolicyKind(str(raw["policy_kind"])),
        seed=int(raw["seed"]),
    )
