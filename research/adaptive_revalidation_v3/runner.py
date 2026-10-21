"""Deterministic evaluator orchestration for isolated policy replay."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .actor import (
    Evidence,
    EvidenceBundle,
    FinalAction,
    OutputAction,
    PolicyKind,
    PolicySpec,
    RepairDecision,
    rounded,
)
from .environment import ThinEnvironment
from .fixtures import (
    CHECKER_GRAPH,
    DEV_ONLY_STATUS,
    PUBLIC_TOOL_NAMES,
    ActorIdentityMap,
    ScenarioFixture,
    load_frozen_scenarios,
)
from .metrics import aggregate_metrics, evaluate_action
from .model import EpisodeMetrics, EpisodeResult, ExperimentResult, ExecutionGraph
from .policy_rpc import execute_policy_batch
from .repairer import FixedRepairer


DEFAULT_POLICY_SPECS: Tuple[PolicySpec, ...] = (
    PolicySpec(PolicyKind.NO_CHECK),
    PolicySpec(PolicyKind.RANDOM_CHECK, seed=20261021),
    PolicySpec(PolicyKind.UNIT_COST_GREEDY),
    PolicySpec(PolicyKind.TWO_STEP_LOOKAHEAD),
    PolicySpec(PolicyKind.FULL_RECOMPUTE),
)


def _action_for_recompute(
    identity: ActorIdentityMap,
    semantic_outputs: Sequence[str],
) -> FinalAction:
    selected = set(semantic_outputs)
    return FinalAction(
        tuple(
            OutputAction(
                output_id=identity.actor_output(output_id),
                decision=(
                    RepairDecision.RECOMPUTE
                    if output_id in selected
                    else RepairDecision.KEEP
                ),
            )
            for output_id in identity.semantic_outputs
        )
    )


def _upper_bound_record(
    fixture: ScenarioFixture,
    graph: ExecutionGraph,
) -> Mapping[str, Any]:
    identity = fixture.identity_map(graph)
    trace = graph.full_trace(fixture.before_source_values, fixture.post_source_values)
    changed_sources = fixture.changed_source_nodes(graph)
    oracle_graph_outputs = graph.static_outputs_from(changed_sources)
    full_trace_outputs = graph.dynamic_outputs_from(trace, changed_sources)
    gold_outputs = trace.changed_outputs

    bounds: Dict[str, Any] = {
        "scenario_id": identity.actor_scenario_id,
        "scenario_family": fixture.family,
        "visibility": "evaluator_only",
        "policy_eligible": False,
    }
    for bound_name, semantic_outputs in (
        ("hidden_oracle_graph", oracle_graph_outputs),
        ("hidden_full_trace", full_trace_outputs),
        ("minimal_value_change", gold_outputs),
    ):
        action = _action_for_recompute(identity, semantic_outputs)
        evidence = EvidenceBundle(identity.actor_input(fixture.query_budget), ())
        metrics = evaluate_action(fixture, action, evidence, graph)
        bounds[bound_name] = {
            "action": action.as_dict(),
            "outputs": [
                identity.actor_output(output_id) for output_id in semantic_outputs
            ],
            "semantic_outputs": list(semantic_outputs),
            "metrics": metrics.as_dict(),
        }
    return bounds


def _validated_decision(
    fixture: ScenarioFixture,
    policy_spec: PolicySpec,
    decision: Any,
    observed_records: Sequence[Evidence],
    graph: ExecutionGraph,
    query_budget: int,
) -> Any:
    actor_input = fixture.actor_input(graph, query_budget)
    if decision.evidence.actor_input != actor_input:
        raise ValueError("POLICY_ACTOR_INPUT_MISMATCH")
    if [record.as_dict() for record in decision.evidence.records] != [
        record.as_dict() for record in observed_records
    ]:
        raise ValueError("POLICY_EVIDENCE_NOT_TOOL_GROUNDED")
    if decision.evidence.query_cost > actor_input.query_budget:
        raise ValueError("POLICY_QUERY_BUDGET_EXCEEDED")
    expected_trace_count = len(decision.evidence.records)
    if len(decision.query_trace) != expected_trace_count:
        raise ValueError("POLICY_QUERY_TRACE_COUNT_MISMATCH")
    if policy_spec.policy_kind is PolicyKind.FULL_RECOMPUTE:
        if decision.action_override is None:
            raise ValueError("FULL_RECOMPUTE_OVERRIDE_MISSING")
        action_outputs = {item.output_id for item in decision.action_override.outputs}
        if action_outputs != set(actor_input.output_ids) or any(
            item.decision is not RepairDecision.RECOMPUTE
            for item in decision.action_override.outputs
        ):
            raise ValueError("FULL_RECOMPUTE_OVERRIDE_INVALID")
        if decision.evidence.records or decision.query_trace:
            raise ValueError("FULL_RECOMPUTE_QUERIES_FORBIDDEN")
    elif decision.action_override is not None:
        raise ValueError("POLICY_ACTION_OVERRIDE_FORBIDDEN")
    return decision


def run_episode(
    fixture: ScenarioFixture,
    policy_spec: PolicySpec,
    graph: ExecutionGraph = CHECKER_GRAPH,
    query_budget: Optional[int] = None,
) -> EpisodeResult:
    """Run one policy in a spawned process and replay the internal fixed repairer."""
    experiment = run_experiment(
        (fixture,),
        (policy_spec,),
        graph=graph,
        budgets=(fixture.query_budget if query_budget is None else query_budget,),
    )
    if len(experiment.episodes) != 1:
        raise ValueError("RUN_EPISODE_RESULT_COUNT_MISMATCH")
    return experiment.episodes[0]


def run_experiment(
    scenarios: Sequence[ScenarioFixture],
    policy_specs: Sequence[PolicySpec] = DEFAULT_POLICY_SPECS,
    graph: ExecutionGraph = CHECKER_GRAPH,
    budgets: Optional[Sequence[int]] = None,
) -> ExperimentResult:
    """Run scenario-policy-budget episodes through one isolated policy batch."""
    if not scenarios:
        raise ValueError("NO_SCENARIOS")
    if not policy_specs:
        raise ValueError("NO_POLICY_SPECS")
    budget_values = (
        (scenarios[0].query_budget,) if budgets is None else tuple(budgets)
    )
    if not budget_values:
        raise ValueError("NO_QUERY_BUDGETS")
    if any(not 0 <= budget <= 9 for budget in budget_values):
        raise ValueError("QUERY_BUDGET_OUTSIDE_SWEEP")

    repairer = FixedRepairer()
    task_inputs: List[Tuple[Any, PolicySpec]] = []
    task_contexts: List[Tuple[ScenarioFixture, ThinEnvironment, int]] = []
    task_specs: List[PolicySpec] = []
    for budget in budget_values:
        for fixture in scenarios:
            fixture.validate(graph)
            actor_input = fixture.actor_input(graph, budget)
            for policy_spec in policy_specs:
                environment = ThinEnvironment(fixture, actor_input, graph)
                task_inputs.append((actor_input, policy_spec))
                task_contexts.append((fixture, environment, budget))
                task_specs.append(policy_spec)

    observed_records: List[List[Evidence]] = [[] for _ in task_inputs]

    def tool_handler(index: int, tool: str, target: str) -> Evidence:
        if tool not in PUBLIC_TOOL_NAMES:
            raise ValueError("NON_PUBLIC_TOOL")
        _, environment, _ = task_contexts[index]
        evidence = getattr(environment, tool)(target)
        observed_records[index].append(evidence)
        return evidence

    decisions, process_info = execute_policy_batch(task_inputs, tool_handler)
    if process_info.policy_pid == process_info.evaluator_pid:
        raise ValueError("POLICY_PROCESS_BOUNDARY_MISSING")

    episodes: List[EpisodeResult] = []
    for (fixture, _, budget), policy_spec, decision, records in zip(
        task_contexts,
        task_specs,
        decisions,
        observed_records,
    ):
        validated = _validated_decision(
            fixture,
            policy_spec,
            decision,
            records,
            graph,
            budget,
        )
        if validated.action_override is None:
            action = repairer.repair(validated.evidence)
            decision_source = "fixed_repairer_replay"
        else:
            action = validated.action_override
            decision_source = "full_recompute_override"
        metrics = evaluate_action(fixture, action, validated.evidence, graph)
        actor_input = validated.evidence.actor_input
        episodes.append(
            EpisodeResult(
                scenario_id=actor_input.scenario_id,
                scenario_family=fixture.family,
                query_budget=budget,
                policy=policy_spec.name,
                policy_kind=policy_spec.policy_kind,
                decision_source=decision_source,
                action=action,
                evidence=validated.evidence,
                query_trace=validated.query_trace,
                metrics=metrics,
            )
        )
    upper_bounds = tuple(_upper_bound_record(fixture, graph) for fixture in scenarios)
    return ExperimentResult(tuple(episodes), upper_bounds)


def run_budget_sweep(
    scenarios: Optional[Sequence[ScenarioFixture]] = None,
    policy_specs: Sequence[PolicySpec] = DEFAULT_POLICY_SPECS,
    graph: ExecutionGraph = CHECKER_GRAPH,
) -> ExperimentResult:
    """Run the fixed 0-9 query-budget sweep without semantic sampling."""
    frozen = load_frozen_scenarios() if scenarios is None else scenarios
    return run_experiment(frozen, policy_specs, graph=graph, budgets=tuple(range(10)))


def _aggregate_by_budget(
    experiment: ExperimentResult,
) -> Mapping[str, Mapping[str, Mapping[str, Union[float, int]]]]:
    grouped: Dict[int, Dict[str, List[EpisodeMetrics]]] = defaultdict(lambda: defaultdict(list))
    for episode in experiment.episodes:
        grouped[episode.query_budget][episode.policy].append(episode.metrics)
    return {
        str(budget): {
            policy: dict(aggregate_metrics(metrics))
            for policy, metrics in sorted(by_policy.items())
        }
        for budget, by_policy in sorted(grouped.items())
    }


def compute_cost_action_loss_frontier(
    experiment: ExperimentResult,
) -> Mapping[str, Any]:
    """Compute aggregate query-cost/final-action-loss Pareto points."""
    grouped: Dict[Tuple[int, str, str], List[EpisodeMetrics]] = defaultdict(list)
    for episode in experiment.episodes:
        grouped[
            (episode.query_budget, episode.policy, episode.policy_kind.value)
        ].append(episode.metrics)
    points: List[Dict[str, Any]] = []
    for (budget, policy, policy_kind), metrics in sorted(grouped.items()):
        aggregate = aggregate_metrics(metrics)
        points.append(
            {
                "episodes": len(metrics),
                "mean_final_action_loss": aggregate["final_action_loss"],
                "mean_query_cost": rounded(
                    sum(item.query_cost for item in metrics) / len(metrics)
                ),
                "policy": policy,
                "policy_kind": policy_kind,
                "query_budget": budget,
            }
        )
    frontier = []
    for candidate in points:
        dominated = any(
            other["mean_query_cost"] <= candidate["mean_query_cost"]
            and other["mean_final_action_loss"] <= candidate["mean_final_action_loss"]
            and (
                other["mean_query_cost"] < candidate["mean_query_cost"]
                or other["mean_final_action_loss"] < candidate["mean_final_action_loss"]
            )
            for other in points
        )
        if not dominated:
            frontier.append(dict(candidate))
    return {
        "dominance_rule": "minimize_mean_query_cost_and_mean_final_action_loss",
        "frontier": frontier,
        "points": points,
    }


def compare_paired_policies(experiment: ExperimentResult) -> Mapping[str, Any]:
    """Compare greedy and two-step at matched budget, scenario, and query cost."""
    pairs: Dict[Tuple[int, str], Dict[PolicyKind, EpisodeMetrics]] = defaultdict(dict)
    for episode in experiment.episodes:
        if episode.policy_kind in {
            PolicyKind.UNIT_COST_GREEDY,
            PolicyKind.TWO_STEP_LOOKAHEAD,
        }:
            pairs[(episode.query_budget, episode.scenario_id)][
                episode.policy_kind
            ] = episode.metrics
    benefits: List[float] = []
    repair_benefits: List[float] = []
    matched_query_costs = set()
    query_cost_mismatches = 0
    incomplete_pairs = 0
    positive_pairs = 0
    negative_pairs = 0
    for by_kind in pairs.values():
        greedy = by_kind.get(PolicyKind.UNIT_COST_GREEDY)
        two_step = by_kind.get(PolicyKind.TWO_STEP_LOOKAHEAD)
        if greedy is None or two_step is None:
            incomplete_pairs += 1
            continue
        if greedy.query_cost != two_step.query_cost:
            query_cost_mismatches += 1
            continue
        benefit = greedy.final_action_loss - two_step.final_action_loss
        repair_benefit = greedy.repair_loss - two_step.repair_loss
        benefits.append(benefit)
        repair_benefits.append(repair_benefit)
        matched_query_costs.add(greedy.query_cost)
        if benefit > 1e-12:
            positive_pairs += 1
        elif benefit < -1e-12:
            negative_pairs += 1
    mean_benefit = rounded(sum(benefits) / len(benefits)) if benefits else 0.0
    mean_repair_benefit = (
        rounded(sum(repair_benefits) / len(repair_benefits))
        if repair_benefits
        else 0.0
    )
    return {
        "greedy_sufficient": positive_pairs == 0,
        "incomplete_pairs": incomplete_pairs,
        "matched_pairs": len(benefits),
        "matched_query_costs": sorted(matched_query_costs),
        "mean_final_action_loss_benefit_two_step": mean_benefit,
        "mean_repair_loss_benefit_two_step": mean_repair_benefit,
        "negative_pairs_two_step": negative_pairs,
        "positive_pairs_two_step": positive_pairs,
        "query_cost_mismatches": query_cost_mismatches,
        "two_step_adds_paired_benefit": positive_pairs > 0 or mean_benefit > 1e-12,
    }


def experiment_as_dict(experiment: ExperimentResult) -> Mapping[str, Any]:
    """Return policy results, budget analysis, and evaluator-only upper bounds."""
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
    budgets = sorted({episode.query_budget for episode in experiment.episodes})
    families = {episode.scenario_family for episode in experiment.episodes}
    return {
        "budgets": budgets,
        "budget_policy_aggregate": _aggregate_by_budget(experiment),
        "capability_boundary": {
            "actor_input_encoding": "canonical_json",
            "policy_execution": "spawned_process_rpc",
            "policy_public_tools": list(PUBLIC_TOOL_NAMES),
            "forbidden_policy_objects": [
                "ThinEnvironment",
                "ScenarioFixture",
                "ExecutionGraph",
                "FullTrace",
                "source_values",
                "Gold",
                "evaluator_exports",
            ],
        },
        "cost_action_loss_frontier": compute_cost_action_loss_frontier(experiment),
        "evidence_boundary": DEV_ONLY_STATUS,
        "evaluator_only_upper_bounds": {
            "policy_eligible": False,
            "records": [dict(record) for record in experiment.upper_bounds],
        },
        "family_count": len(families),
        "paired_policy_comparison": compare_paired_policies(experiment),
        "policy_aggregate": aggregates,
        "policy_results": [episode.as_dict() for episode in experiment.episodes],
        "semantic_label_policy": {
            "actor_input_uses_semantic_labels": False,
            "sampling": "frozen_fixture_order_and_numeric_budget",
            "scoring": "numeric_metrics_without_family_labels",
        },
    }
