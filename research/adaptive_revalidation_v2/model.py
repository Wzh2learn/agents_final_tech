"""Typed core model for the adaptive-revalidation thin environment."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import math
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union


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
    """Round metrics for stable receipts without hiding meaningful changes."""
    return round(float(value), 12)


class Operation(str, Enum):
    """Executable operation vocabulary used by the fixture DAG."""

    SOURCE = "source"
    ADD = "add"
    MULTIPLY = "multiply"
    COPY = "copy"
    SUBTRACT = "subtract"
    SELECT = "select"


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
class NodeDefinition:
    """One executable node in the hidden checker graph."""

    node_id: NodeId
    operation: Operation
    dependencies: Tuple[NodeId, ...]
    parameter: float = 1.0

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("NODE_ID_EMPTY")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("DUPLICATE_NODE_DEPENDENCY")
        if self.operation is Operation.SOURCE and self.dependencies:
            raise ValueError("SOURCE_HAS_DEPENDENCIES")
        if self.operation in (Operation.ADD, Operation.MULTIPLY) and not self.dependencies:
            raise ValueError("REDUCTION_REQUIRES_DEPENDENCIES")
        if self.operation is Operation.COPY and len(self.dependencies) != 1:
            raise ValueError("COPY_REQUIRES_ONE_DEPENDENCY")
        if self.operation is Operation.SUBTRACT and len(self.dependencies) != 2:
            raise ValueError("SUBTRACT_REQUIRES_TWO_DEPENDENCIES")
        if self.operation is Operation.SELECT and len(self.dependencies) != 3:
            raise ValueError("SELECT_REQUIRES_THREE_DEPENDENCIES")


@dataclass(frozen=True)
class ActiveEdge:
    """Evaluator-only active dependency edge in one execution trace."""

    source: NodeId
    target: NodeId


@dataclass(frozen=True)
class EvaluationResult:
    """Evaluator-only values and dynamic trace for one source state."""

    values: Tuple[Tuple[NodeId, Value], ...]
    active_edges: Tuple[ActiveEdge, ...]

    def value_map(self) -> Dict[NodeId, Value]:
        """Return a copied node-to-value mapping."""
        return dict(self.values)


@dataclass(frozen=True)
class FullTrace:
    """Evaluator-only before/after execution trace used for upper bounds."""

    before: EvaluationResult
    after: EvaluationResult
    changed_nodes: Tuple[NodeId, ...]
    changed_outputs: Tuple[OutputId, ...]


class ExecutionGraph:
    """Deterministic DAG evaluator with explicit active-edge tracing."""

    def __init__(self, definitions: Sequence[NodeDefinition], output_ids: Sequence[OutputId]):
        by_id = {definition.node_id: definition for definition in definitions}
        if len(by_id) != len(definitions):
            raise ValueError("DUPLICATE_NODE_ID")
        if not 8 <= len(definitions) <= 12:
            raise ValueError("EXECUTABLE_NODE_COUNT_OUT_OF_BOUNDS")
        if not 2 <= len(output_ids) <= 4:
            raise ValueError("OUTPUT_COUNT_OUT_OF_BOUNDS")
        if len(set(output_ids)) != len(output_ids):
            raise ValueError("DUPLICATE_OUTPUT_ID")
        unknown_outputs = sorted(set(output_ids) - set(by_id))
        if unknown_outputs:
            raise ValueError("UNKNOWN_OUTPUT_NODE")
        for definition in definitions:
            unknown = sorted(set(definition.dependencies) - set(by_id))
            if unknown:
                raise ValueError("UNKNOWN_NODE_DEPENDENCY", definition.node_id, unknown)
        self._definitions: Mapping[NodeId, NodeDefinition] = dict(by_id)
        self._output_ids: Tuple[OutputId, ...] = tuple(output_ids)
        self._topological_order: Tuple[NodeId, ...] = self._sort_topologically()

    @property
    def output_ids(self) -> Tuple[OutputId, ...]:
        """Return the frozen output identifiers."""
        return self._output_ids

    @property
    def node_ids(self) -> Tuple[NodeId, ...]:
        """Return executable node identifiers in deterministic graph order."""
        return tuple(definition.node_id for definition in self._definitions.values())

    @property
    def topological_order(self) -> Tuple[NodeId, ...]:
        """Return the deterministic topological node order."""
        return self._topological_order

    @property
    def definitions(self) -> Mapping[NodeId, NodeDefinition]:
        """Return the hidden checker graph definitions."""
        return dict(self._definitions)

    def _sort_topologically(self) -> Tuple[NodeId, ...]:
        visited: Dict[NodeId, int] = {}
        order: list[NodeId] = []

        def visit(node_id: NodeId) -> None:
            state = visited.get(node_id, 0)
            if state == 1:
                raise ValueError("CYCLIC_NODE_GRAPH")
            if state == 2:
                return
            visited[node_id] = 1
            for dependency in self._definitions[node_id].dependencies:
                visit(dependency)
            visited[node_id] = 2
            order.append(node_id)

        for node_id in sorted(self._definitions):
            visit(node_id)
        return tuple(order)

    def evaluate(self, source_values: Mapping[NodeId, Value]) -> EvaluationResult:
        """Evaluate all executable nodes and record active edges."""
        source_ids = {
            node_id
            for node_id, definition in self._definitions.items()
            if definition.operation is Operation.SOURCE
        }
        missing = sorted(source_ids - set(source_values))
        unexpected = sorted(set(source_values) - source_ids)
        if missing or unexpected:
            raise ValueError("SOURCE_VALUE_KEYS_MISMATCH", missing, unexpected)

        values: Dict[NodeId, Value] = {}
        active_edges: list[ActiveEdge] = []
        for node_id in self._topological_order:
            definition = self._definitions[node_id]
            operation = definition.operation
            if operation is Operation.SOURCE:
                values[node_id] = float(source_values[node_id])
                continue
            dependencies = definition.dependencies
            if operation is Operation.ADD:
                values[node_id] = sum(float(values[item]) for item in dependencies)
                active_edges.extend(ActiveEdge(item, node_id) for item in dependencies)
            elif operation is Operation.MULTIPLY:
                product = float(definition.parameter)
                for item in dependencies:
                    product *= float(values[item])
                values[node_id] = product
                active_edges.extend(ActiveEdge(item, node_id) for item in dependencies)
            elif operation is Operation.COPY:
                values[node_id] = float(values[dependencies[0]])
                active_edges.append(ActiveEdge(dependencies[0], node_id))
            elif operation is Operation.SUBTRACT:
                values[node_id] = float(values[dependencies[0]]) - float(values[dependencies[1]])
                active_edges.extend(ActiveEdge(item, node_id) for item in dependencies)
            elif operation is Operation.SELECT:
                guard, when_true, when_false = dependencies
                selected = when_true if abs(float(values[guard])) > 1e-12 else when_false
                values[node_id] = float(values[selected])
                active_edges.append(ActiveEdge(guard, node_id))
                active_edges.append(ActiveEdge(selected, node_id))
            else:
                raise ValueError("UNSUPPORTED_OPERATION", operation)

        ordered_values = tuple(
            (node_id, float(values[node_id])) for node_id in self._topological_order
        )
        ordered_edges = tuple(
            sorted(set(active_edges), key=lambda edge: (edge.source, edge.target))
        )
        return EvaluationResult(ordered_values, ordered_edges)

    def full_trace(
        self,
        before_source_values: Mapping[NodeId, Value],
        after_source_values: Mapping[NodeId, Value],
    ) -> FullTrace:
        """Compute evaluator-only before/after values, changes, and active edges."""
        before = self.evaluate(before_source_values)
        after = self.evaluate(after_source_values)
        before_values = before.value_map()
        after_values = after.value_map()
        changed_nodes = tuple(
            node_id
            for node_id in self._topological_order
            if not math.isclose(before_values[node_id], after_values[node_id], abs_tol=1e-12)
        )
        changed_outputs = tuple(
            output_id for output_id in self._output_ids if output_id in changed_nodes
        )
        return FullTrace(before, after, changed_nodes, changed_outputs)

    def static_outputs_from(self, changed_nodes: Iterable[NodeId]) -> Tuple[OutputId, ...]:
        """Return output nodes statically reachable from changed nodes."""
        reachable = set(changed_nodes)
        pending = list(reachable)
        while pending:
            node_id = pending.pop()
            for target, definition in self._definitions.items():
                if node_id in definition.dependencies and target not in reachable:
                    reachable.add(target)
                    pending.append(target)
        return tuple(output_id for output_id in self._output_ids if output_id in reachable)

    def dynamic_outputs_from(
        self,
        trace: FullTrace,
        changed_nodes: Iterable[NodeId],
    ) -> Tuple[OutputId, ...]:
        """Return outputs with an active post-change path from a changed node."""
        parents: Dict[NodeId, set[NodeId]] = {
            node_id: set() for node_id in self._definitions
        }
        for edge in trace.after.active_edges:
            parents[edge.target].add(edge.source)
        reachable = set(changed_nodes)
        pending = list(reachable)
        while pending:
            node_id = pending.pop()
            for target, sources in parents.items():
                if node_id in sources and target not in reachable:
                    reachable.add(target)
                    pending.append(target)
        return tuple(output_id for output_id in self._output_ids if output_id in reachable)


@dataclass(frozen=True)
class ChangeSummary:
    """Actor-visible identifier for a source change, with no state values."""

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
    """The complete policy input; hidden evaluator state is deliberately absent."""

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
        if set(self.output_ids) - set(self.node_ids):
            raise ValueError("ACTOR_OUTPUT_NOT_IN_NODE_CATALOG")
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
    """Response from ``inspect_dependency`` using the visible fixture graph."""

    node_id: NodeId
    observed_dependencies: Tuple[NodeId, ...]
    reachable_outputs: Tuple[OutputId, ...]
    query_index: int
    cost: int = 1
    kind: EvidenceKind = EvidenceKind.DEPENDENCY

    @property
    def result_key(self) -> str:
        """Return the discrete outcome used by Bayesian query scoring."""
        return "reach" if self.reachable_outputs else "no_reach"

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
        """Return the discrete outcome used by Bayesian query scoring."""
        return "delta" if abs(self.delta) > 1e-12 else "no_delta"

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
    """Response from ``run_target_test`` without exposing observed values."""

    output_id: OutputId
    passed: bool
    query_index: int
    cost: int = 1
    kind: EvidenceKind = EvidenceKind.TARGET_TEST

    @property
    def result_key(self) -> str:
        """Return the discrete outcome used by Bayesian query scoring."""
        return "pass" if self.passed else "fail"

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
        query_keys = [
            (record.kind.value, getattr(record, "node_id", getattr(record, "output_id", "")))
            for record in self.records
        ]
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
    """Output of a query policy before or instead of fixed repairer replay."""

    evidence: EvidenceBundle
    action_override: Optional[FinalAction]
    query_trace: Tuple[QueryTraceEntry, ...]


@dataclass(frozen=True)
class EpisodeMetrics:
    """Required partial-success metrics for one scenario-policy episode."""

    final_action_loss: float
    repair_loss: float
    query_cost: int
    recomputation_cost: int
    missed_invalidation: int
    over_invalidation: int
    regression_rate: float
    completion: float
    abstention: float

    def as_dict(self) -> Dict[str, Union[float, int]]:
        """Return stable metric names and values."""
        return {
            "abstention": rounded(self.abstention),
            "completion": rounded(self.completion),
            "final_action_loss": rounded(self.final_action_loss),
            "missed_invalidation": self.missed_invalidation,
            "over_invalidation": self.over_invalidation,
            "query_cost": self.query_cost,
            "recomputation_cost": self.recomputation_cost,
            "regression_rate": rounded(self.regression_rate),
            "repair_loss": rounded(self.repair_loss),
        }


@dataclass(frozen=True)
class EpisodeResult:
    """Serializable policy result for one deterministic fixture."""

    scenario_id: ScenarioId
    scenario_family: str
    policy: str
    policy_kind: PolicyKind
    decision_source: str
    action: FinalAction
    evidence: EvidenceBundle
    query_trace: Tuple[QueryTraceEntry, ...]
    metrics: EpisodeMetrics

    def as_dict(self) -> Dict[str, Any]:
        """Return the stable episode representation."""
        return {
            "action": self.action.as_dict(),
            "decision_source": self.decision_source,
            "evidence": self.evidence.as_dict(),
            "metrics": self.metrics.as_dict(),
            "policy": self.policy,
            "policy_kind": self.policy_kind.value,
            "query_trace": [entry.as_dict() for entry in self.query_trace],
            "scenario_family": self.scenario_family,
            "scenario_id": self.scenario_id,
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


@dataclass(frozen=True)
class ExperimentResult:
    """All policy episodes plus evaluator-only upper-bound records."""

    episodes: Tuple[EpisodeResult, ...]
    upper_bounds: Tuple[Mapping[str, Any], ...]
