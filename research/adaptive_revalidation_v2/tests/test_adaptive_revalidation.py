"""Contract tests for the DEV_ONLY adaptive-revalidation thin environment."""
from __future__ import annotations

import inspect
import json
from dataclasses import replace
from pathlib import Path
from typing import Dict

import pytest

from research.adaptive_revalidation_v2.environment import (
    QueryBudgetExceeded,
    ThinEnvironment,
)
from research.adaptive_revalidation_v2.fixtures import (
    CHECKER_GRAPH,
    DEV_ONLY_STATUS,
    PUBLIC_TOOL_NAMES,
    load_fixture_document,
    load_frozen_scenarios,
)
from research.adaptive_revalidation_v2.metrics import (
    aggregate_metrics,
    evaluate_action,
    execute_action,
)
from research.adaptive_revalidation_v2.model import (
    ActiveEdge,
    DependencyEvidence,
    EvidenceBundle,
    ExecutionGraph,
    FinalAction,
    NodeDefinition,
    Operation,
    OutputAction,
    PolicyKind,
    PolicySpec,
    RepairDecision,
    canonical_json,
)
from research.adaptive_revalidation_v2.policies import make_policy
from research.adaptive_revalidation_v2.receipt import (
    REQUIRED_METRICS,
    build_receipt,
    verify_receipt,
    write_receipt,
)
from research.adaptive_revalidation_v2.repairer import FixedRepairer
from research.adaptive_revalidation_v2.runner import (
    DEFAULT_POLICY_SPECS,
    experiment_as_dict,
    run_episode,
    run_experiment,
)


def _fixture_by_id() -> Dict[str, object]:
    return {fixture.scenario_id: fixture for fixture in load_frozen_scenarios()}


def _action(decisions: Dict[str, RepairDecision]) -> FinalAction:
    return FinalAction(
        tuple(
            OutputAction(output_id=output_id, decision=decision)
            for output_id, decision in decisions.items()
        )
    )


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
        assert scenario.changed_source_nodes()


def test_actor_input_excludes_hidden_or_derived_state() -> None:
    fixture = _fixture_by_id()["value_cancellation_exact"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    assert set(actor_input.as_dict()) == {
        "changes",
        "node_ids",
        "output_ids",
        "query_budget",
        "scenario_id",
    }
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
    assert tuple(inspect.signature(FixedRepairer.repair).parameters) == ("self", "bundle")


def test_public_tools_return_only_documented_evidence_fields() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    actor_input = fixture.actor_input(CHECKER_GRAPH)
    environment = ThinEnvironment(fixture, actor_input)
    assert environment.public_tool_names == PUBLIC_TOOL_NAMES

    dependency = environment.inspect_dependency("price")
    assert set(dependency.as_dict()) == {
        "cost",
        "kind",
        "node_id",
        "observed_dependencies",
        "query_index",
        "reachable_outputs",
        "result_key",
    }
    assert dependency.reachable_outputs == CHECKER_GRAPH.output_ids

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

    test = environment.run_target_test("total")
    assert set(test.as_dict()) == {
        "cost",
        "kind",
        "output_id",
        "passed",
        "query_index",
        "result_key",
    }
    assert test.as_dict() == {
        "cost": 1,
        "kind": "target_test",
        "output_id": "total",
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

    valid_evidence = environment.inspect_dependency("unused")
    with pytest.raises(ValueError, match="EVIDENCE_QUERY_INDEX_NOT_SEQUENTIAL"):
        EvidenceBundle(
            actor_input,
            (
                DependencyEvidence(
                    node_id="unused",
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

    dependency_environment = ThinEnvironment(fixture, actor_input)
    dependency_bundle = EvidenceBundle(
        actor_input,
        (
            dependency_environment.inspect_change(actor_input.changes[0].change_id),
            dependency_environment.inspect_dependency("fee"),
        ),
    )
    dependency_action = FixedRepairer().repair(dependency_bundle)

    test_environment = ThinEnvironment(fixture, actor_input)
    test_bundle = EvidenceBundle(
        actor_input,
        tuple(
            test_environment.run_target_test(output_id)
            for output_id in CHECKER_GRAPH.output_ids
        ),
    )
    test_action = FixedRepairer().repair(test_bundle)

    assert dependency_action.as_dict() == {
        "audit": "recompute",
        "margin": "recompute",
        "total": "recompute",
    }
    assert test_action.as_dict() == dependency_action.as_dict()


def test_missing_and_noisy_edges_have_opposite_failure_modes() -> None:
    fixtures = _fixture_by_id()
    missing = fixtures["missing_edge_breaking"]
    missing_input = missing.actor_input(CHECKER_GRAPH)
    missing_environment = ThinEnvironment(missing, missing_input)
    missing_bundle = EvidenceBundle(
        missing_input,
        (
            missing_environment.inspect_change(missing_input.changes[0].change_id),
            missing_environment.inspect_dependency("price"),
        ),
    )
    missing_action = FixedRepairer().repair(missing_bundle)
    missing_metrics = evaluate_action(missing, missing_action, missing_bundle)
    assert missing_action.as_dict() == {
        "audit": "keep",
        "margin": "keep",
        "total": "keep",
    }
    assert missing_metrics.missed_invalidation == 3
    assert missing_metrics.repair_loss > 0.0

    noisy = fixtures["noisy_edge_benign"]
    noisy_input = noisy.actor_input(CHECKER_GRAPH)
    noisy_environment = ThinEnvironment(noisy, noisy_input)
    noisy_bundle = EvidenceBundle(
        noisy_input,
        (
            noisy_environment.inspect_change(noisy_input.changes[0].change_id),
            noisy_environment.inspect_dependency("unused"),
        ),
    )
    noisy_action = FixedRepairer().repair(noisy_bundle)
    noisy_metrics = evaluate_action(noisy, noisy_action, noisy_bundle)
    assert noisy_action.as_dict() == {
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
                for output_id in CHECKER_GRAPH.output_ids
            ),
        )
        action = FixedRepairer().repair(bundle)
        metrics = evaluate_action(fixture, action, bundle)
        assert action.as_dict() == {
            "audit": "keep",
            "margin": "keep",
            "total": "keep",
        }
        assert metrics.missed_invalidation == 0
        assert metrics.over_invalidation == 0
        assert metrics.repair_loss == 0.0

    partial = fixtures["partial_breaking_bonus"]
    partial_input = partial.actor_input(CHECKER_GRAPH)
    partial_environment = ThinEnvironment(partial, partial_input)
    partial_bundle = EvidenceBundle(
        partial_input,
        (
            partial_environment.inspect_change(partial_input.changes[0].change_id),
            partial_environment.inspect_dependency("bonus"),
        ),
    )
    partial_action = FixedRepairer().repair(partial_bundle)
    partial_metrics = evaluate_action(partial, partial_action, partial_bundle)
    assert partial_action.as_dict() == {
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
    assert set(cancellation.changed_source_nodes()) == {"fee", "price"}

    inactive = fixtures["inactive_branch_change"]
    inactive_trace = CHECKER_GRAPH.full_trace(
        inactive.before_source_values,
        inactive.post_source_values,
    )
    assert ActiveEdge("bonus", "audit") not in inactive_trace.after.active_edges
    assert inactive_trace.changed_outputs == ()


def test_required_policies_are_deterministic_and_bounded() -> None:
    fixtures = load_frozen_scenarios()
    assert [spec.policy_kind for spec in DEFAULT_POLICY_SPECS] == [
        PolicyKind.NO_CHECK,
        PolicyKind.RANDOM_CHECK,
        PolicyKind.UNIT_COST_GREEDY,
        PolicyKind.TWO_STEP_LOOKAHEAD,
        PolicyKind.FULL_RECOMPUTE,
    ]
    for fixture in fixtures:
        for spec in DEFAULT_POLICY_SPECS:
            first = run_episode(fixture, spec, FixedRepairer())
            second = run_episode(fixture, spec, FixedRepairer())
            assert canonical_json(first.as_dict()) == canonical_json(second.as_dict())
            assert first.metrics.query_cost <= fixture.query_budget
            if spec.policy_kind is not PolicyKind.FULL_RECOMPUTE:
                assert first.decision_source == "fixed_repairer_replay"
                keys = [
                    (record.kind.value, record.node_id if hasattr(record, "node_id") else record.output_id)
                    for record in first.evidence.records
                ]
                assert len(keys) == len(set(keys))
            else:
                assert first.decision_source == "full_recompute_override"
                assert first.metrics.query_cost == 0
                assert first.action.as_dict() == {
                    "audit": "recompute",
                    "margin": "recompute",
                    "total": "recompute",
                }


def test_information_gain_policies_replay_fully_within_budget() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    for policy_kind in (
        PolicyKind.UNIT_COST_GREEDY,
        PolicyKind.TWO_STEP_LOOKAHEAD,
    ):
        result = run_episode(fixture, PolicySpec(policy_kind), FixedRepairer())
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
        FixedRepairer(),
    )
    assert no_check.action.as_dict() == {
        "audit": "abstain",
        "margin": "abstain",
        "total": "abstain",
    }
    assert no_check.metrics.completion == 0.0
    assert no_check.metrics.abstention == 1.0
    assert no_check.metrics.final_action_loss == 0.5

    breaking = fixtures["breaking_change"]
    partial_action = _action(
        {
            "total": RepairDecision.RECOMPUTE,
            "margin": RepairDecision.KEEP,
            "audit": RepairDecision.KEEP,
        }
    )
    empty_bundle = EvidenceBundle(breaking.actor_input(CHECKER_GRAPH), ())
    partial_metrics = evaluate_action(breaking, partial_action, empty_bundle)
    assert partial_metrics.missed_invalidation == 2
    assert partial_metrics.regression_rate == pytest.approx(2 / 3)
    assert partial_metrics.completion == 1.0
    assert partial_metrics.repair_loss > 0.0

    near = fixtures["near_additive_residual"]
    keep_all = _action(
        {
            "total": RepairDecision.KEEP,
            "margin": RepairDecision.KEEP,
            "audit": RepairDecision.KEEP,
        }
    )
    near_metrics = evaluate_action(
        near,
        keep_all,
        EvidenceBundle(near.actor_input(CHECKER_GRAPH), ()),
    )
    assert near_metrics.repair_loss > 0.0
    assert near_metrics.repair_loss < partial_metrics.repair_loss


def test_full_recompute_and_aggregate_metrics_are_not_all_or_nothing() -> None:
    result = run_experiment(load_frozen_scenarios(), DEFAULT_POLICY_SPECS)
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
            "query_trace",
            "scenario_family",
            "scenario_id",
        }
        lowered = canonical_json(episode).lower()
        assert "gold" not in lowered
        assert "hidden_checker_graph" not in lowered
        assert "hidden_trace" not in lowered

    records = {
        record["scenario_id"]: record
        for record in serialized["evaluator_only_upper_bounds"]["records"]
    }
    inactive = records["inactive_branch_change"]
    assert inactive["hidden_oracle_graph"]["outputs"] == ["audit"]
    assert inactive["hidden_full_trace"]["outputs"] == []
    assert inactive["minimal_value_change"]["outputs"] == []


def test_receipt_is_source_hash_bound_deterministic_and_tamper_detecting(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    arguments = {
        "test_command": "python -m pytest research/adaptive_revalidation_v2/tests -q",
        "test_exit_code": 0,
        "test_passed": 17,
        "test_failed": 0,
        "test_skipped": 0,
    }
    first = build_receipt(root, **arguments)
    second = build_receipt(root, **arguments)
    assert canonical_json(first) == canonical_json(second)
    assert first["status"] == DEV_ONLY_STATUS
    assert first["claims"]["model_calls"] == 0
    assert first["claims"]["network_calls"] == 0
    assert "model.py" in first["source_hashes"]
    assert "policies.py" in first["source_hashes"]
    assert "tests/test_adaptive_revalidation.py" in first["source_hashes"]
    assert "fixtures/scenarios.json" in first["source_hashes"]

    receipt_path = tmp_path / "result_receipt.json"
    write_receipt(receipt_path, first)
    verification = verify_receipt(receipt_path, root)
    assert verification["status"] == "PASS"
    assert verification["policy_episodes"] == 45

    tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
    tampered["source_hashes"]["model.py"] = "0" * 64
    tampered_path = tmp_path / "tampered_receipt.json"
    write_receipt(tampered_path, tampered)
    with pytest.raises(ValueError, match="RECEIPT_SOURCE_HASH_MISMATCH"):
        verify_receipt(tampered_path, root)


def test_execute_action_keeps_cached_values_for_abstain() -> None:
    fixture = _fixture_by_id()["breaking_change"]
    action = _action(
        {
            "total": RepairDecision.ABSTAIN,
            "margin": RepairDecision.RECOMPUTE,
            "audit": RepairDecision.KEEP,
        }
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
