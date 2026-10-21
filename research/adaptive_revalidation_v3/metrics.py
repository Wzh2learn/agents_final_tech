"""Evaluator-only partial-success action and repair metrics."""
from __future__ import annotations

from typing import Dict, Mapping, Sequence, Set, Union

from .actor import (
    EvidenceBundle,
    FinalAction,
    OutputAction,
    OutputId,
    RepairDecision,
    rounded,
)
from .fixtures import CHECKER_GRAPH, ActorIdentityMap, ScenarioFixture
from .model import EpisodeMetrics, ExecutionGraph


def _dependency_closure_size(
    graph: ExecutionGraph,
    output_id: OutputId,
) -> int:
    dependencies = {
        node_id: definition.dependencies
        for node_id, definition in graph.definitions.items()
    }
    reached: Set[str] = {output_id}
    pending = [output_id]
    while pending:
        node_id = pending.pop()
        for dependency in dependencies[node_id]:
            if dependency not in reached:
                reached.add(dependency)
                pending.append(dependency)
    return len(reached)


def semantic_action(
    action: FinalAction,
    identity: ActorIdentityMap,
) -> Dict[OutputId, RepairDecision]:
    """Map one opaque action to evaluator-only semantic output names."""
    actor_outputs = set(identity.actor_outputs)
    if {item.output_id for item in action.outputs} != actor_outputs:
        raise ValueError("ACTION_OUTPUT_SET_MISMATCH")
    return {
        identity.semantic_output(item.output_id): item.decision
        for item in action.outputs
    }


def execute_action(
    fixture: ScenarioFixture,
    action: FinalAction,
    graph: ExecutionGraph = CHECKER_GRAPH,
) -> Dict[OutputId, float]:
    """Apply keep/recompute/abstain semantics to the before-success cache."""
    identity = fixture.identity_map(graph)
    decisions = semantic_action(action, identity)
    trace = graph.full_trace(fixture.before_source_values, fixture.post_source_values)
    before = trace.before.value_map()
    after = trace.after.value_map()
    final_values: Dict[OutputId, float] = {}
    for output_id in graph.output_ids:
        decision = decisions[output_id]
        if decision is RepairDecision.RECOMPUTE:
            final_values[output_id] = after[output_id]
        else:
            final_values[output_id] = before[output_id]
    return final_values


def evaluate_action(
    fixture: ScenarioFixture,
    action: FinalAction,
    evidence: EvidenceBundle,
    graph: ExecutionGraph = CHECKER_GRAPH,
) -> EpisodeMetrics:
    """Compute all required metrics without collapsing success to one score."""
    identity = fixture.identity_map(graph)
    output_ids = graph.output_ids
    decisions = semantic_action(action, identity)
    if evidence.actor_input.output_ids != identity.actor_outputs:
        raise ValueError("EVIDENCE_OUTPUT_SET_MISMATCH")

    trace = graph.full_trace(fixture.before_source_values, fixture.post_source_values)
    before = trace.before.value_map()
    after = trace.after.value_map()
    final_values = execute_action(fixture, action, graph)
    gold: Set[OutputId] = set(trace.changed_outputs)

    action_cost = 0.0
    missed = 0
    over = 0
    regressions = 0
    committed = 0
    abstentions = 0
    repair_squared_error = 0.0
    recomputation_cost = 0

    for output_id in output_ids:
        decision = decisions[output_id]
        optimal = RepairDecision.RECOMPUTE if output_id in gold else RepairDecision.KEEP
        if decision is RepairDecision.ABSTAIN:
            action_cost += 0.5
            abstentions += 1
        else:
            committed += 1
            if decision is not optimal:
                action_cost += 1.0

        if output_id in gold and decision is not RepairDecision.RECOMPUTE:
            missed += 1
        if output_id not in gold and decision is RepairDecision.RECOMPUTE:
            over += 1
        if decision is RepairDecision.RECOMPUTE:
            recomputation_cost += _dependency_closure_size(graph, output_id)

        error = final_values[output_id] - after[output_id]
        if abs(error) > 1e-12:
            regressions += 1
        scale = max(1.0, abs(before[output_id]), abs(after[output_id]))
        repair_squared_error += (error / scale) ** 2

    count = len(output_ids)
    return EpisodeMetrics(
        final_action_loss=action_cost / count,
        repair_loss=repair_squared_error / count,
        query_cost=evidence.query_cost,
        recomputation_cost=recomputation_cost,
        missed_invalidation=missed,
        over_invalidation=over,
        regression_rate=regressions / count,
        completion=committed / count,
        abstention=abstentions / count,
    )


def aggregate_metrics(
    metrics: Sequence[EpisodeMetrics],
) -> Mapping[str, Union[float, int]]:
    """Aggregate normalized losses/rates as means and costs/counts as sums."""
    if not metrics:
        raise ValueError("NO_EPISODE_METRICS")
    count = len(metrics)
    summed = {
        "query_cost": sum(item.query_cost for item in metrics),
        "recomputation_cost": sum(item.recomputation_cost for item in metrics),
        "missed_invalidation": sum(item.missed_invalidation for item in metrics),
        "over_invalidation": sum(item.over_invalidation for item in metrics),
    }
    means = {
        "final_action_loss": sum(item.final_action_loss for item in metrics) / count,
        "repair_loss": sum(item.repair_loss for item in metrics) / count,
        "regression_rate": sum(item.regression_rate for item in metrics) / count,
        "completion": sum(item.completion for item in metrics) / count,
        "abstention": sum(item.abstention for item in metrics) / count,
    }
    return {
        "abstention": rounded(means["abstention"]),
        "completion": rounded(means["completion"]),
        "final_action_loss": rounded(means["final_action_loss"]),
        "missed_invalidation": summed["missed_invalidation"],
        "over_invalidation": summed["over_invalidation"],
        "query_cost": summed["query_cost"],
        "recomputation_cost": summed["recomputation_cost"],
        "regression_rate": rounded(means["regression_rate"]),
        "repair_loss": rounded(means["repair_loss"]),
    }


def optimal_action(
    fixture: ScenarioFixture,
    graph: ExecutionGraph = CHECKER_GRAPH,
) -> FinalAction:
    """Return evaluator-derived minimal actions using opaque output IDs."""
    identity = fixture.identity_map(graph)
    trace = graph.full_trace(fixture.before_source_values, fixture.post_source_values)
    gold: Set[OutputId] = set(trace.changed_outputs)
    return FinalAction(
        tuple(
            OutputAction(
                output_id=identity.actor_output(output_id),
                decision=(
                    RepairDecision.RECOMPUTE
                    if output_id in gold
                    else RepairDecision.KEEP
                ),
            )
            for output_id in graph.output_ids
        )
    )
