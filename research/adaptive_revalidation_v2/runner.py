"""Deterministic experiment replay across policies and frozen scenarios."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Tuple, Union

from .environment import ThinEnvironment
from .fixtures import CHECKER_GRAPH, DEV_ONLY_STATUS, ScenarioFixture, load_frozen_scenarios
from .metrics import aggregate_metrics, evaluate_action, optimal_action
from .model import (
    EpisodeMetrics,
    EpisodeResult,
    EvidenceBundle,
    ExperimentResult,
    ExecutionGraph,
    FinalAction,
    OutputAction,
    PolicyKind,
    PolicySpec,
    RepairDecision,
)
from .policies import make_policy
from .repairer import FixedRepairer


DEFAULT_POLICY_SPECS: Tuple[PolicySpec, ...] = (
    PolicySpec(PolicyKind.NO_CHECK),
    PolicySpec(PolicyKind.RANDOM_CHECK, seed=20261021),
    PolicySpec(PolicyKind.UNIT_COST_GREEDY),
    PolicySpec(PolicyKind.TWO_STEP_LOOKAHEAD),
    PolicySpec(PolicyKind.FULL_RECOMPUTE),
)


def _action_for_recompute(
    graph: ExecutionGraph,
    recompute_outputs: Sequence[str],
) -> FinalAction:
    selected = set(recompute_outputs)
    return FinalAction(
        tuple(
            OutputAction(
                output_id=output_id,
                decision=(
                    RepairDecision.RECOMPUTE
                    if output_id in selected
                    else RepairDecision.KEEP
                ),
            )
            for output_id in graph.output_ids
        )
    )


def run_episode(
    fixture: ScenarioFixture,
    policy_spec: PolicySpec,
    repairer: FixedRepairer,
    graph: ExecutionGraph = CHECKER_GRAPH,
) -> EpisodeResult:
    """Run one bounded policy episode through the fixed repairer boundary."""
    actor_input = fixture.actor_input(graph)
    environment = ThinEnvironment(fixture, actor_input, graph)
    policy = make_policy(policy_spec)
    decision = policy.run(actor_input, environment)
    if decision.action_override is None:
        action = repairer.repair(decision.evidence)
        decision_source = "fixed_repairer_replay"
    else:
        action = decision.action_override
        decision_source = "full_recompute_override"
    metrics = evaluate_action(fixture, action, decision.evidence, graph)
    return EpisodeResult(
        scenario_id=fixture.scenario_id,
        scenario_family=fixture.family,
        policy=policy_spec.name,
        policy_kind=policy_spec.policy_kind,
        decision_source=decision_source,
        action=action,
        evidence=decision.evidence,
        query_trace=decision.query_trace,
        metrics=metrics,
    )


def _upper_bound_record(
    fixture: ScenarioFixture,
    graph: ExecutionGraph,
) -> Mapping[str, Any]:
    trace = graph.full_trace(fixture.before_source_values, fixture.post_source_values)
    changed_sources = fixture.changed_source_nodes()
    oracle_graph_outputs = graph.static_outputs_from(changed_sources)
    full_trace_outputs = graph.dynamic_outputs_from(trace, changed_sources)
    gold_outputs = trace.changed_outputs

    bounds: Dict[str, Any] = {
        "scenario_id": fixture.scenario_id,
        "scenario_family": fixture.family,
        "visibility": "evaluator_only",
        "policy_eligible": False,
    }
    for bound_name, outputs in (
        ("hidden_oracle_graph", oracle_graph_outputs),
        ("hidden_full_trace", full_trace_outputs),
        ("minimal_value_change", gold_outputs),
    ):
        action = _action_for_recompute(graph, outputs)
        evidence = EvidenceBundle(fixture.actor_input(graph), ())
        metrics = evaluate_action(fixture, action, evidence, graph)
        bounds[bound_name] = {
            "action": action.as_dict(),
            "outputs": list(outputs),
            "metrics": metrics.as_dict(),
        }
    return bounds


def run_experiment(
    scenarios: Sequence[ScenarioFixture],
    policy_specs: Sequence[PolicySpec] = DEFAULT_POLICY_SPECS,
    graph: ExecutionGraph = CHECKER_GRAPH,
) -> ExperimentResult:
    """Run every scenario-policy pair with one immutable repairer implementation."""
    if not scenarios:
        raise ValueError("NO_SCENARIOS")
    if not policy_specs:
        raise ValueError("NO_POLICY_SPECS")
    repairer = FixedRepairer()
    episodes: List[EpisodeResult] = []
    for fixture in scenarios:
        fixture.validate(graph)
        for policy_spec in policy_specs:
            episodes.append(run_episode(fixture, policy_spec, repairer, graph))
    upper_bounds = tuple(_upper_bound_record(fixture, graph) for fixture in scenarios)
    return ExperimentResult(tuple(episodes), upper_bounds)


def experiment_as_dict(experiment: ExperimentResult) -> Mapping[str, Any]:
    """Return policy results and evaluator-only upper bounds in separate sections."""
    grouped: Dict[str, List[EpisodeMetrics]] = defaultdict(list)
    policy_metadata: Dict[str, str] = {}
    for episode in experiment.episodes:
        grouped[episode.policy].append(episode.metrics)
        policy_metadata[episode.policy] = episode.policy_kind.value
    aggregates = {
        policy: {
            "policy_kind": policy_metadata[policy],
            "metrics": dict(aggregate_metrics(metrics)),
        }
        for policy, metrics in sorted(grouped.items())
    }
    return {
        "evidence_boundary": DEV_ONLY_STATUS,
        "policy_aggregate": aggregates,
        "policy_results": [episode.as_dict() for episode in experiment.episodes],
        "evaluator_only_upper_bounds": {
            "policy_eligible": False,
            "records": [dict(record) for record in experiment.upper_bounds],
        },
    }
