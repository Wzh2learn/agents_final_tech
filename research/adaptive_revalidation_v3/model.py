"""Evaluator-only graph and result model for adaptive-revalidation V3.

Actor-safe DTOs live in :mod:`actor`; this module is never imported by the
policy process.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple, Union

from .actor import (
    EvidenceBundle,
    FinalAction,
    PolicyKind,
    QueryTraceEntry,
    Value,
    canonical_json,
    canonical_json_bytes,
    rounded,
)


NodeId = str
OutputId = str
ScenarioId = str


class Operation(str, Enum):
    """Executable operation vocabulary used by the fixture DAG."""

    SOURCE = "source"
    ADD = "add"
    MULTIPLY = "multiply"
    COPY = "copy"
    SUBTRACT = "subtract"
    SELECT = "select"


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
    query_budget: int
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
            "query_budget": self.query_budget,
            "query_trace": [entry.as_dict() for entry in self.query_trace],
            "scenario_family": self.scenario_family,
            "scenario_id": self.scenario_id,
        }


@dataclass(frozen=True)
class ExperimentResult:
    """All policy episodes plus evaluator-only upper-bound records."""

    episodes: Tuple[EpisodeResult, ...]
    upper_bounds: Tuple[Mapping[str, Any], ...]
