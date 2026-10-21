"""Public query surface for the bounded thin environment."""
from __future__ import annotations

from typing import Mapping, Protocol, Tuple

from .fixtures import CHECKER_GRAPH, PUBLIC_TOOL_NAMES, ScenarioFixture
from .model import (
    ActorInput,
    ChangeEvidence,
    DependencyEvidence,
    ExecutionGraph,
    OutputId,
    TargetTestEvidence,
)


class PublicTools(Protocol):
    """The complete actor-facing query contract."""

    def inspect_dependency(self, node_id: str) -> DependencyEvidence:
        """Inspect the independently authored visible dependency record."""

    def inspect_change(self, change_id: str) -> ChangeEvidence:
        """Inspect one actor-identified source change."""

    def run_target_test(self, output_id: str) -> TargetTestEvidence:
        """Run one target test against the post-change state."""


class QueryBudgetExceeded(ValueError):
    """Raised when a policy exceeds its actor-visible query budget."""


class ThinEnvironment:
    """Deterministic environment implementing exactly the three public tools."""

    def __init__(
        self,
        fixture: ScenarioFixture,
        actor_input: ActorInput,
        graph: ExecutionGraph = CHECKER_GRAPH,
    ) -> None:
        fixture.validate(graph)
        if actor_input != fixture.actor_input(graph):
            raise ValueError("ACTOR_INPUT_FIXTURE_MISMATCH")
        self._fixture = fixture
        self._actor_input = actor_input
        self._graph = graph
        self._query_count = 0
        self._trace = graph.full_trace(
            fixture.before_source_values,
            fixture.post_source_values,
        )

    @property
    def public_tool_names(self) -> Tuple[str, ...]:
        """Return the public tool names as a stable tuple."""
        return PUBLIC_TOOL_NAMES

    @property
    def query_count(self) -> int:
        """Return the number of public queries consumed."""
        return self._query_count

    @property
    def remaining_queries(self) -> int:
        """Return the remaining actor-visible unit query budget."""
        return self._actor_input.query_budget - self._query_count

    def _consume_query(self) -> int:
        if self._query_count >= self._actor_input.query_budget:
            raise QueryBudgetExceeded(
                f"query budget {self._actor_input.query_budget} exhausted"
            )
        query_index = self._query_count
        self._query_count += 1
        return query_index

    def _visible_reachable_outputs(self, node_id: str) -> Tuple[OutputId, ...]:
        dependencies: Mapping[str, Tuple[str, ...]] = self._fixture.visible_dependencies
        reachable = {node_id}
        pending = [node_id]
        while pending:
            current = pending.pop()
            for target in dependencies[current]:
                if target not in reachable:
                    reachable.add(target)
                    pending.append(target)
        return tuple(
            output_id for output_id in self._graph.output_ids if output_id in reachable
        )

    def inspect_dependency(self, node_id: str) -> DependencyEvidence:
        """Return only the authored visible dependency evidence for one node."""
        if node_id not in self._fixture.visible_dependencies:
            raise KeyError(node_id)
        query_index = self._consume_query()
        return DependencyEvidence(
            node_id=node_id,
            observed_dependencies=self._fixture.visible_dependencies[node_id],
            reachable_outputs=self._visible_reachable_outputs(node_id),
            query_index=query_index,
        )

    def inspect_change(self, change_id: str) -> ChangeEvidence:
        """Return public before/after source values for one identified change."""
        summary = next(
            (change for change in self._actor_input.changes if change.change_id == change_id),
            None,
        )
        if summary is None:
            raise KeyError(change_id)
        node_id = summary.node_id
        before_value = float(self._fixture.before_source_values[node_id])
        after_value = float(self._fixture.post_source_values[node_id])
        query_index = self._consume_query()
        return ChangeEvidence(
            change_id=change_id,
            node_id=node_id,
            change_kind=summary.change_kind,
            before_value=before_value,
            after_value=after_value,
            delta=after_value - before_value,
            query_index=query_index,
        )

    def run_target_test(self, output_id: str) -> TargetTestEvidence:
        """Return pass/fail only; no observed or expected values are exposed."""
        if output_id not in self._graph.output_ids:
            raise KeyError(output_id)
        query_index = self._consume_query()
        passed = output_id not in self._trace.changed_outputs
        return TargetTestEvidence(
            output_id=output_id,
            passed=passed,
            query_index=query_index,
        )
