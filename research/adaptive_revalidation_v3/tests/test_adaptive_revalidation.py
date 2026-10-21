"""Contract tests for isolated, opaque adaptive-revalidation V3 replay."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
from typing import Dict

import pytest

from research.adaptive_revalidation_v3 import DEV_ONLY_STATUS
from research.adaptive_revalidation_v3.actor import (
    DependencyEvidence,
    EvidenceBundle,
    FinalAction,
    OutputAction,
    PolicyDecision,
    PolicyKind,
    PolicySpec,
    RepairDecision,
    canonical_json,
)
from research.adaptive_revalidation_v3.environment import (
    QueryBudgetExceeded,
    ThinEnvironment,
)
from research.adaptive_revalidation_v3.fixtures import (
    CHECKER_GRAPH,
    PUBLIC_TOOL_NAMES,
    load_fixture_document,
    load_frozen_scenarios,
)
from research.adaptive_revalidation_v3.metrics import (
    aggregate_metrics,
    evaluate_action,
    execute_action,
)
from research.adaptive_revalidation_v3.model import (
    ActiveEdge,
    ExecutionGraph,
    NodeDefinition,
    Operation,
)
from research.adaptive_revalidation_v3.policies import (
    candidate_queries,
    make_policy,
    _deterministic_shuffle,
)
from research.adaptive_revalidation_v3.policy_rpc import (
    RpcProtocolError,
    _run_protocol,
    _send,
    run_introspection_probe,
)
from research.adaptive_revalidation_v3.receipt import (
    REQUIRED_METRICS,
    build_receipt,
    recompute_result_payload,
    verify_receipt,
    write_receipt,
)
from research.adaptive_revalidation_v3.repairer import FixedRepairer
from research.adaptive_revalidation_v3.runner import (
    DEFAULT_POLICY_SPECS,
    _validated_decision,
    compare_paired_policies,
    compute_cost_action_loss_frontier,
    experiment_as_dict,
    run_budget_sweep,
    run_episode,
    run_experiment,
)


def _fixture_by_id() -> Dict[str, object]:
    return {fixture.scenario_id: fixture for fixture in load_frozen_scenarios()}


def _actor_action(fixture: object, semantic_decisions: Dict[str, RepairDecision]) -> FinalAction:
    identity = fixture.identity_map(CHECKER_GRAPH)
    return FinalAction(
        tuple(
            OutputAction(identity.actor_output(output_id), decision)
            for output_id, decision in semantic_decisions.items()
        )
    )


def _semantic_action_dict(fixture: object, action: FinalAction) -> Dict[str, str]:
    identity = fixture.identity_map(CHECKER_GRAPH)
    return {
        identity.semantic_output(item.output_id): item.decision.value
        for item in action.outputs
    }


def _forged_batch_result_worker(control: object, result: object) -> None:
    _send(
        control,
        {
            "policy_pid": os.getpid(),
            "results": [],
            "type": "batch_result",
        },
    )
    control.close()
    result.close()


def _forged_tool_call_on_result_worker(control: object, result: object) -> None:
    _send(
        result,
        {
            "episode_index": 0,
            "target": "forged",
            "tool": "inspect_dependency",
            "type": "tool_call",
        },
    )
    control.close()
    result.close()


def test_environment_and_frozen_fixture_contracts() -> None:
    scenarios = load_frozen_scenarios()
    assert len(CHECKER_GRAPH.node_ids) == 12
    assert len(CHECKER_GRAPH.output_ids) == 3
    assert PUBLIC_TOOL_NAMES == (
        "inspect_dependency",
        "inspect_change",
        "run_target_test",
    )
    assert {
        scenario.family for scenario in scenarios
    } == {
        "breaking",
        "benign",
        "inactive_branch",
        "multiple_evidence",
        "value_cancellation",
        "near_additive",
        "partial_breaking",
        "missing_edge",
        "noisy_edge",
    }
    for scenario in scenarios:
        trace = CHECKER_GRAPH.full_trace(
            scenario.before_source_values,
            scenario.post_source_values,
        )
        before = trace.before.value_map()
        for output_id, expected in scenario.before_success_snapshot.items():
            assert before[output_id] == expected
        assert scenario.changed_source_nodes(CHECKER_GRAPH)


def test_actor_ids_are_opaque_stable_and_hidden_label_invariant() -> None:
    fixture = _fixture_by_id()["value_cancellation_exact"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    serialized = canonical_json(actor_input.as_dict())
    assert set(actor_input.as_dict()) == {
        "changes",
        "node_ids",
        "output_ids",
        "query_budget",
        "scenario_id",
    }
    assert re.fullmatch(r"S[0-9a-f]{12}", actor_input.scenario_id)
    assert all(re.fullmatch(r"N[0-9a-f]{12}", item) for item in actor_input.node_ids)
    assert all(re.fullmatch(r"O[0-9a-f]{12}", item) for item in actor_input.output_ids)
    assert all(re.fullmatch(r"C[0-9a-f]{12}", item.change_id) for item in actor_input.changes)
    assert set(actor_input.node_ids).isdisjoint(CHECKER_GRAPH.node_ids)
    assert set(actor_input.output_ids).isdisjoint(CHECKER_GRAPH.output_ids)

    mutated = replace(
        fixture,
        scenario_id="hidden_gold_label",
        family="hidden_gold_label",
        description="hidden_gold_label",
        before_success_snapshot={
            "audit": 999.0,
            "margin": 999.0,
            "total": 999.0,
        },
    )
    assert canonical_json(mutated.actor_input(CHECKER_GRAPH).as_dict()) == serialized
    assert mutated.identity_map(CHECKER_GRAPH).actor_nodes == actor_input.node_ids
    assert mutated.identity_map(CHECKER_GRAPH).actor_outputs == actor_input.output_ids


def test_policy_randomness_is_seeded_without_semantic_labels() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    base = fixture.actor_input(CHECKER_GRAPH)
    mutated = replace(
        fixture,
        scenario_id="semantic_gold_change",
        family="semantic_gold_change",
        description="semantic_gold_change",
    ).actor_input(CHECKER_GRAPH)
    base_order = _deterministic_shuffle(candidate_queries(base), base, 20261021)
    mutated_order = _deterministic_shuffle(candidate_queries(mutated), mutated, 20261021)
    assert [item.key for item in base_order] == [item.key for item in mutated_order]


def test_actor_input_excludes_hidden_or_derived_state() -> None:
    fixture = _fixture_by_id()["value_cancellation_exact"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    serialized = canonical_json(actor_input.as_dict()).lower()
    for forbidden in (
        "gold",
        "hidden",
        "trace",
        "oracle",
        "before_value",
        "after_value",
        "delta",
        "visible_dependencies",
        "before_success_snapshot",
        "post_source_values",
    ):
        assert forbidden not in serialized
    assert set(actor_input.__dataclass_fields__) == set(actor_input.as_dict())
    assert tuple(
        __import__("inspect").signature(FixedRepairer.repair).parameters
    ) == ("self", "bundle")


def test_public_tools_return_only_documented_evidence_fields() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    identity = fixture.identity_map(CHECKER_GRAPH)
    environment = ThinEnvironment(fixture, actor_input)
    assert environment.public_tool_names == PUBLIC_TOOL_NAMES

    dependency = environment.inspect_dependency(identity.actor_node("price"))
    assert set(dependency.as_dict()) == {
        "cost",
        "kind",
        "node_id",
        "observed_dependencies",
        "query_index",
        "reachable_outputs",
        "result_key",
    }
    assert set(dependency.reachable_outputs) == set(actor_input.output_ids)

    change = environment.inspect_change(actor_input.changes[0].change_id)
    assert set(change.as_dict()) == {
        "after_value",
        "before_value",
        "change_id",
        "change_kind",
        "cost",
        "delta",
        "kind",
        "node_id",
        "query_index",
        "result_key",
    }
    assert change.result_key == "delta"

    test = environment.run_target_test(identity.actor_output("total"))
    assert test.as_dict() == {
        "cost": 1,
        "kind": "target_test",
        "output_id": identity.actor_output("total"),
        "passed": False,
        "query_index": 2,
        "result_key": "fail",
    }


def test_query_budget_is_enforced() -> None:
    fixture = _fixture_by_id()["benign_change"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    environment = ThinEnvironment(fixture, actor_input)
    for node_id in actor_input.node_ids[: actor_input.query_budget]:
        environment.inspect_dependency(node_id)
    assert environment.remaining_queries == 0
    with pytest.raises(QueryBudgetExceeded):
        environment.inspect_dependency(actor_input.node_ids[actor_input.query_budget])


def test_invalid_targets_evidence_order_and_fixture_status_fail_closed(
    tmp_path: Path,
) -> None:
    fixture = _fixture_by_id()["benign_change"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    environment = ThinEnvironment(fixture, actor_input)
    for call in (
        lambda: environment.inspect_dependency("missing_node"),
        lambda: environment.inspect_change("missing_change"),
        lambda: environment.run_target_test("missing_output"),
    ):
        with pytest.raises(KeyError):
            call()
    assert environment.query_count == 0

    valid_evidence = environment.inspect_dependency(actor_input.node_ids[0])
    with pytest.raises(ValueError, match="EVIDENCE_QUERY_INDEX_NOT_SEQUENTIAL"):
        EvidenceBundle(
            actor_input,
            (
                DependencyEvidence(
                    node_id=actor_input.node_ids[0],
                    observed_dependencies=(),
                    reachable_outputs=(),
                    query_index=1,
                ),
            ),
        )
    with pytest.raises(ValueError, match="DUPLICATE_EVIDENCE_QUERY"):
        EvidenceBundle(
            actor_input,
            (valid_evidence, replace(valid_evidence, query_index=1)),
        )

    source = Path(__file__).resolve().parents[1] / "fixtures" / "scenarios.json"
    document = json.loads(source.read_text(encoding="utf-8"))
    document["status"] = "NOT_DEV_ONLY"
    invalid_fixture = tmp_path / "invalid_scenarios.json"
    invalid_fixture.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="FIXTURE_STATUS_MISMATCH"):
        load_fixture_document(invalid_fixture)


def test_policy_process_and_client_have_strict_actor_capability_surface() -> None:
    probe, info = run_introspection_probe()
    assert info.policy_pid != info.evaluator_pid
    assert probe["public_names"] == sorted(PUBLIC_TOOL_NAMES)
    assert probe["client_slots"] == []
    assert probe["client_private_attributes"] == []
    assert probe["client_connection_attribute_error"] == "AttributeError"
    assert probe["client_vars"] is None
    assert probe["client_vars_error"] == "TypeError"
    assert probe["client_class_module"] == "research.adaptive_revalidation_v3.policy_rpc"
    assert "ThinEnvironment" not in probe["client_repr"]
    assert not any(
        name.endswith((".environment", ".fixtures", ".model", ".metrics", ".runner", ".receipt"))
        for name in probe["loaded_modules"]
    )
    globals_text = canonical_json(probe["method_global_names"]).lower()
    for forbidden in (
        "thinenvironment",
        "scenariofixture",
        "executiongraph",
        "fulltrace",
        "checker_graph",
        "before_source_values",
        "post_source_values",
        "gold",
    ):
        assert forbidden not in globals_text


def test_rpc_protocol_rejects_forged_result_and_tool_messages() -> None:
    with pytest.raises(RpcProtocolError, match="UNEXPECTED_CONTROL_MESSAGE"):
        _run_protocol(_forged_batch_result_worker, ())
    with pytest.raises(RpcProtocolError, match="UNEXPECTED_RESULT_MESSAGE"):
        _run_protocol(_forged_tool_call_on_result_worker, ())


def test_full_recompute_override_requires_every_output_to_recompute() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    empty_evidence = EvidenceBundle(actor_input, ())
    spec = PolicySpec(PolicyKind.FULL_RECOMPUTE)

    partial = PolicyDecision(
        empty_evidence,
        FinalAction(
            (
                OutputAction(actor_input.output_ids[0], RepairDecision.RECOMPUTE),
                OutputAction(actor_input.output_ids[1], RepairDecision.KEEP),
                OutputAction(actor_input.output_ids[2], RepairDecision.ABSTAIN),
            )
        ),
        (),
    )
    with pytest.raises(ValueError, match="FULL_RECOMPUTE_OVERRIDE_INVALID"):
        _validated_decision(
            fixture,
            spec,
            partial,
            (),
            CHECKER_GRAPH,
            actor_input.query_budget,
        )

    missing = PolicyDecision(
        empty_evidence,
        FinalAction(
            (
                OutputAction(actor_input.output_ids[0], RepairDecision.RECOMPUTE),
                OutputAction(actor_input.output_ids[1], RepairDecision.RECOMPUTE),
            )
        ),
        (),
    )
    with pytest.raises(ValueError, match="FULL_RECOMPUTE_OVERRIDE_INVALID"):
        _validated_decision(
            fixture,
            spec,
            missing,
            (),
            CHECKER_GRAPH,
            actor_input.query_budget,
        )

    forged_non_baseline = PolicyDecision(
        empty_evidence,
        FinalAction(
            tuple(
                OutputAction(output_id, RepairDecision.RECOMPUTE)
                for output_id in actor_input.output_ids
            )
        ),
        (),
    )
    with pytest.raises(ValueError, match="POLICY_ACTION_OVERRIDE_FORBIDDEN"):
        _validated_decision(
            fixture,
            PolicySpec(PolicyKind.UNIT_COST_GREEDY),
            forged_non_baseline,
            (),
            CHECKER_GRAPH,
            actor_input.query_budget,
        )


def test_package_exports_do_not_expose_evaluator_objects() -> None:
    import research.adaptive_revalidation_v3 as package

    assert package.__all__ == ["DEV_ONLY_STATUS"]
    assert not any(
        hasattr(package, name)
        for name in (
            "ThinEnvironment",
            "ScenarioFixture",
            "ExecutionGraph",
            "FullTrace",
            "CHECKER_GRAPH",
        )
    )


def test_invalid_graph_shapes_fail_closed() -> None:
    with pytest.raises(ValueError, match="EXECUTABLE_NODE_COUNT_OUT_OF_BOUNDS"):
        ExecutionGraph(
            tuple(NodeDefinition(f"n{index}", Operation.SOURCE, ()) for index in range(7)),
            ("n0", "n1"),
        )
    with pytest.raises(ValueError, match="CYCLIC_NODE_GRAPH"):
        ExecutionGraph(
            (
                NodeDefinition("a", Operation.COPY, ("b",)),
                NodeDefinition("b", Operation.COPY, ("a",)),
                NodeDefinition("n0", Operation.SOURCE, ()),
                NodeDefinition("n1", Operation.SOURCE, ()),
                NodeDefinition("n2", Operation.SOURCE, ()),
                NodeDefinition("n3", Operation.SOURCE, ()),
                NodeDefinition("n4", Operation.SOURCE, ()),
                NodeDefinition("n5", Operation.SOURCE, ()),
            ),
            ("a", "b"),
        )


def test_fixed_repairer_accepts_multiple_valid_evidence_sets() -> None:
    fixture = _fixture_by_id()["multiple_supporting_evidence"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    identity = fixture.identity_map(CHECKER_GRAPH)

    dependency_environment = ThinEnvironment(fixture, actor_input)
    dependency_bundle = EvidenceBundle(
        actor_input,
        (
            dependency_environment.inspect_change(actor_input.changes[0].change_id),
            dependency_environment.inspect_dependency(identity.actor_node("fee")),
        ),
    )
    dependency_action = FixedRepairer().repair(dependency_bundle)

    test_environment = ThinEnvironment(fixture, actor_input)
    test_bundle = EvidenceBundle(
        actor_input,
        tuple(
            test_environment.run_target_test(output_id)
            for output_id in actor_input.output_ids
        ),
    )
    test_action = FixedRepairer().repair(test_bundle)
    expected = _semantic_action_dict(
        fixture,
        _actor_action(
            fixture,
            {
                "audit": RepairDecision.RECOMPUTE,
                "margin": RepairDecision.RECOMPUTE,
                "total": RepairDecision.RECOMPUTE,
            },
        ),
    )
    assert _semantic_action_dict(fixture, dependency_action) == expected
    assert _semantic_action_dict(fixture, test_action) == expected


def test_missing_and_noisy_edges_have_opposite_failure_modes() -> None:
    fixtures = _fixture_by_id()
    missing = fixtures["missing_edge_breaking"]
    missing_input = missing.actor_input(CHECKER_GRAPH)
    missing_identity = missing.identity_map(CHECKER_GRAPH)
    missing_environment = ThinEnvironment(missing, missing_input)
    missing_bundle = EvidenceBundle(
        missing_input,
        (
            missing_environment.inspect_change(missing_input.changes[0].change_id),
            missing_environment.inspect_dependency(missing_identity.actor_node("price")),
        ),
    )
    missing_action = FixedRepairer().repair(missing_bundle)
    missing_metrics = evaluate_action(missing, missing_action, missing_bundle)
    assert _semantic_action_dict(missing, missing_action) == {
        "audit": "keep",
        "margin": "keep",
        "total": "keep",
    }
    assert missing_metrics.missed_invalidation == 3
    assert missing_metrics.repair_loss > 0.0

    noisy = fixtures["noisy_edge_benign"]
    noisy_input = noisy.actor_input(CHECKER_GRAPH)
    noisy_identity = noisy.identity_map(CHECKER_GRAPH)
    noisy_environment = ThinEnvironment(noisy, noisy_input)
    noisy_bundle = EvidenceBundle(
        noisy_input,
        (
            noisy_environment.inspect_change(noisy_input.changes[0].change_id),
            noisy_environment.inspect_dependency(noisy_identity.actor_node("unused")),
        ),
    )
    noisy_action = FixedRepairer().repair(noisy_bundle)
    noisy_metrics = evaluate_action(noisy, noisy_action, noisy_bundle)
    assert _semantic_action_dict(noisy, noisy_action) == {
        "audit": "keep",
        "margin": "keep",
        "total": "recompute",
    }
    assert noisy_metrics.over_invalidation == 1
    assert noisy_metrics.repair_loss == 0.0


def test_cancellation_inactive_branch_and_partial_impact_stay_partial() -> None:
    fixtures = _fixture_by_id()
    for scenario_id in ("value_cancellation_exact", "inactive_branch_change"):
        fixture = fixtures[scenario_id]
        actor_input = fixture.actor_input(CHECKER_GRAPH)
        environment = ThinEnvironment(fixture, actor_input)
        bundle = EvidenceBundle(
            actor_input,
            tuple(
                environment.run_target_test(output_id)
                for output_id in actor_input.output_ids
            ),
        )
        action = FixedRepairer().repair(bundle)
        metrics = evaluate_action(fixture, action, bundle)
        assert _semantic_action_dict(fixture, action) == {
            "audit": "keep",
            "margin": "keep",
            "total": "keep",
        }
        assert metrics.missed_invalidation == 0
        assert metrics.over_invalidation == 0
        assert metrics.repair_loss == 0.0

    partial = fixtures["partial_breaking_bonus"]
    partial_input = partial.actor_input(CHECKER_GRAPH)
    partial_identity = partial.identity_map(CHECKER_GRAPH)
    partial_environment = ThinEnvironment(partial, partial_input)
    partial_bundle = EvidenceBundle(
        partial_input,
        (
            partial_environment.inspect_change(partial_input.changes[0].change_id),
            partial_environment.inspect_dependency(partial_identity.actor_node("bonus")),
        ),
    )
    partial_action = FixedRepairer().repair(partial_bundle)
    partial_metrics = evaluate_action(partial, partial_action, partial_bundle)
    assert _semantic_action_dict(partial, partial_action) == {
        "audit": "recompute",
        "margin": "keep",
        "total": "keep",
    }
    assert partial_metrics.final_action_loss == 0.0
    assert partial_metrics.repair_loss == 0.0


def test_value_cancellation_and_inactive_trace_are_evaluator_separated() -> None:
    fixtures = _fixture_by_id()
    cancellation = fixtures["value_cancellation_exact"]
    cancellation_trace = CHECKER_GRAPH.full_trace(
        cancellation.before_source_values,
        cancellation.post_source_values,
    )
    assert set(cancellation_trace.changed_nodes) == {"fee", "price"}
    assert "base" not in cancellation_trace.changed_nodes
    assert set(cancellation.changed_source_nodes(CHECKER_GRAPH)) == {"fee", "price"}

    inactive = fixtures["inactive_branch_change"]
    inactive_trace = CHECKER_GRAPH.full_trace(
        inactive.before_source_values,
        inactive.post_source_values,
    )
    assert ActiveEdge("bonus", "audit") not in inactive_trace.after.active_edges
    assert inactive_trace.changed_outputs == ()


def test_required_policies_are_deterministic_bounded_and_process_isolated() -> None:
    assert [spec.policy_kind for spec in DEFAULT_POLICY_SPECS] == [
        PolicyKind.NO_CHECK,
        PolicyKind.RANDOM_CHECK,
        PolicyKind.UNIT_COST_GREEDY,
        PolicyKind.TWO_STEP_LOOKAHEAD,
        PolicyKind.FULL_RECOMPUTE,
    ]
    first = run_budget_sweep()
    second = run_budget_sweep()
    assert canonical_json(experiment_as_dict(first)) == canonical_json(
        experiment_as_dict(second)
    )
    assert len(first.episodes) == 450
    assert {episode.query_budget for episode in first.episodes} == set(range(10))
    for episode in first.episodes:
        assert episode.metrics.query_cost <= episode.query_budget
        if episode.policy_kind is not PolicyKind.FULL_RECOMPUTE:
            assert episode.decision_source == "fixed_repairer_replay"
        else:
            assert episode.decision_source == "full_recompute_override"
            assert episode.metrics.query_cost == 0


def test_budget_sweep_identifies_frontier_and_paired_benefit() -> None:
    result = experiment_as_dict(run_budget_sweep())
    assert result["budgets"] == list(range(10))
    assert result["family_count"] == 9
    frontier = compute_cost_action_loss_frontier(run_experiment(load_frozen_scenarios()))
    assert frontier["dominance_rule"].startswith("minimize_mean_query_cost")
    assert frontier["frontier"]
    paired = compare_paired_policies(run_budget_sweep())
    assert paired["matched_pairs"] == 90
    assert paired["query_cost_mismatches"] == 0
    assert paired["incomplete_pairs"] == 0
    assert isinstance(paired["greedy_sufficient"], bool)
    assert isinstance(paired["two_step_adds_paired_benefit"], bool)
    assert result["cost_action_loss_frontier"]["frontier"]


def test_information_gain_policies_replay_fully_within_budget() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    for policy_kind in (
        PolicyKind.UNIT_COST_GREEDY,
        PolicyKind.TWO_STEP_LOOKAHEAD,
    ):
        result = run_episode(fixture, PolicySpec(policy_kind))
        assert result.metrics.query_cost == fixture.query_budget
        assert len(result.query_trace) == fixture.query_budget
        assert all(entry.information_gain >= 0.0 for entry in result.query_trace)
        assert result.metrics.missed_invalidation == 0
        assert result.metrics.over_invalidation == 0
        assert result.metrics.repair_loss == 0.0


def test_no_check_abstains_and_metrics_preserve_partial_success() -> None:
    fixtures = _fixture_by_id()
    no_check = run_episode(
        fixtures["breaking_change"],
        PolicySpec(PolicyKind.NO_CHECK),
    )
    assert set(no_check.action.as_dict().values()) == {"abstain"}
    assert set(no_check.action.as_dict()) == set(
        no_check.evidence.actor_input.output_ids
    )
    assert no_check.metrics.completion == 0.0
    assert no_check.metrics.abstention == 1.0
    assert no_check.metrics.final_action_loss == 0.5

    breaking = fixtures["breaking_change"]
    partial_action = _actor_action(
        breaking,
        {
            "total": RepairDecision.RECOMPUTE,
            "margin": RepairDecision.KEEP,
            "audit": RepairDecision.KEEP,
        },
    )
    empty_bundle = EvidenceBundle(breaking.actor_input(CHECKER_GRAPH), ())
    partial_metrics = evaluate_action(breaking, partial_action, empty_bundle)
    assert partial_metrics.missed_invalidation == 2
    assert partial_metrics.regression_rate == pytest.approx(2 / 3)
    assert partial_metrics.completion == 1.0
    assert partial_metrics.repair_loss > 0.0

    near = fixtures["near_additive_residual"]
    keep_all = _actor_action(
        near,
        {
            "total": RepairDecision.KEEP,
            "margin": RepairDecision.KEEP,
            "audit": RepairDecision.KEEP,
        },
    )
    near_metrics = evaluate_action(
        near,
        keep_all,
        EvidenceBundle(near.actor_input(CHECKER_GRAPH), ()),
    )
    assert near_metrics.repair_loss > 0.0
    assert near_metrics.repair_loss < partial_metrics.repair_loss


def test_full_recompute_and_aggregate_metrics_are_not_all_or_nothing() -> None:
    result = run_experiment(load_frozen_scenarios())
    aggregate = experiment_as_dict(result)["policy_aggregate"]
    full = aggregate["full_recompute"]["metrics"]
    assert full["repair_loss"] == 0.0
    assert full["over_invalidation"] > 0
    assert full["completion"] == 1.0
    assert set(full) == REQUIRED_METRICS

    metrics = [episode.metrics for episode in result.episodes[:3]]
    summarized = aggregate_metrics(metrics)
    assert summarized["query_cost"] == sum(item.query_cost for item in metrics)
    assert 0.0 <= summarized["final_action_loss"] <= 1.0


def test_oracle_graph_and_trace_are_only_upper_bounds() -> None:
    serialized = experiment_as_dict(run_experiment(load_frozen_scenarios()))
    assert serialized["evaluator_only_upper_bounds"]["policy_eligible"] is False
    for episode in serialized["policy_results"]:
        assert set(episode) == {
            "action",
            "decision_source",
            "evidence",
            "metrics",
            "policy",
            "policy_kind",
            "query_budget",
            "query_trace",
            "scenario_family",
            "scenario_id",
        }
        actor_input = episode["evidence"]["actor_input"]
        lowered = canonical_json(actor_input).lower()
        assert "gold" not in lowered
        assert "hidden_checker_graph" not in lowered
        assert "hidden_trace" not in lowered

    records = {
        record["scenario_id"]: record
        for record in serialized["evaluator_only_upper_bounds"]["records"]
    }
    inactive = next(
        record
        for record in records.values()
        if record["scenario_family"] == "inactive_branch"
    )
    assert inactive["hidden_oracle_graph"]["semantic_outputs"] == ["audit"]
    assert inactive["hidden_full_trace"]["semantic_outputs"] == []
    assert inactive["minimal_value_change"]["semantic_outputs"] == []


def test_receipt_is_replay_bound_deterministic_and_tamper_detecting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path(__file__).resolve().parents[1]
    arguments = {
        "test_command": "python -m pytest research/adaptive_revalidation_v3/tests -q",
        "test_exit_code": 0,
        "test_passed": 24,
        "test_failed": 0,
        "test_skipped": 0,
    }
    first = build_receipt(root, **arguments)
    receipt_path = tmp_path / "result_receipt.json"
    write_receipt(receipt_path, first)
    verification = verify_receipt(receipt_path, root)
    assert verification["status"] == "PASS"
    assert verification["policy_episodes"] == 450
    assert first["status"] == DEV_ONLY_STATUS
    assert first["zero_call_accounting"] == {
        "database_calls": 0,
        "judge_calls": 0,
        "model_calls": 0,
        "network_calls": 0,
        "training_calls": 0,
    }

    expected = {section: first[section] for section in (
        "budget_policy_aggregate",
        "budgets",
        "capability_boundary",
        "cost_action_loss_frontier",
        "evidence_boundary",
        "evaluator_only_upper_bounds",
        "family_count",
        "paired_policy_comparison",
        "policy_aggregate",
        "policy_results",
        "semantic_label_policy",
    )}
    monkeypatch.setattr(
        "research.adaptive_revalidation_v3.receipt.recompute_result_payload",
        lambda: expected,
    )

    def expect_failure(payload: Dict[str, object], match: str) -> None:
        tampered_path = tmp_path / f"{match}.json"
        write_receipt(tampered_path, payload)
        with pytest.raises(ValueError, match=match):
            verify_receipt(tampered_path, root)

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["policy_results"][0]["metrics"]["query_cost"] += 1
    expect_failure(tampered, "RECEIPT_RESULT_PAYLOAD_TAMPERING")

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["policy_aggregate"]["no_check"]["metrics"]["final_action_loss"] = -1.0
    expect_failure(tampered, "RECEIPT_RESULT_PAYLOAD_TAMPERING")

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["replay_hashes"]["policy_results"] = "0" * 64
    expect_failure(tampered, "RECEIPT_REPLAY_HASH_MISMATCH")

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["result_payload_sha256"] = "0" * 64
    expect_failure(tampered, "RECEIPT_RESULT_HASH_MISMATCH")
    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["serialized_replay_sha256"] = "0" * 64
    expect_failure(tampered, "RECEIPT_SERIALIZED_REPLAY_HASH_MISMATCH")

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["source_hashes"]["model.py"] = "0" * 64
    expect_failure(tampered, "RECEIPT_SOURCE_HASH_MISMATCH")

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["test_summary"]["status"] = "FAIL"
    expect_failure(tampered, "RECEIPT_TEST_STATUS_INCONSISTENT")

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["zero_call_accounting"]["model_calls"] = 1
    expect_failure(tampered, "RECEIPT_ZERO_CALL_ACCOUNTING_NONZERO")


def test_execute_action_keeps_cached_values_for_abstain() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    action = _actor_action(
        fixture,
        {
            "total": RepairDecision.ABSTAIN,
            "margin": RepairDecision.RECOMPUTE,
            "audit": RepairDecision.KEEP,
        },
    )
    final_values = execute_action(fixture, action)
    trace = CHECKER_GRAPH.full_trace(
        fixture.before_source_values,
        fixture.post_source_values,
    )
    before = trace.before.value_map()
    after = trace.after.value_map()
    assert final_values["total"] == before["total"]
    assert final_values["margin"] == after["margin"]
    assert final_values["audit"] == before["audit"]
