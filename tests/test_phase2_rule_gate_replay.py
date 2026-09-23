import copy
import json

import pytest

from research import paper_result_views as views
from research import phase2_rule_gate_replay as replay


@pytest.fixture
def dataset() -> dict[str, object]:
    return {
        "contract_version": replay.CONTRACT_VERSION,
        "dataset_id": "synthetic-seven-arm-contract",
        "tables": [
            {
                "uid": "p-typo",
                "family": "typo",
                "layer": "proposal_train",
                "observations": [
                    {"observed": "Revnue", "gold_target": "Revenue"},
                    {"observed": "Amount", "gold_target": "Amount"},
                ],
            },
            {
                "uid": "p-collision",
                "family": "collision",
                "layer": "proposal_train",
                "observations": [
                    {"observed": "acct", "gold_target": "Accounts Receivable"},
                    {"observed": "turnover", "gold_target": "Revenue"},
                ],
            },
            {
                "uid": "p-noise",
                "family": "noise",
                "layer": "proposal_train",
                "observations": [
                    {"observed": "mystery", "gold_target": "Unknown"},
                ],
            },
            {
                "uid": "g-typo",
                "family": "typo",
                "layer": "gate_validation",
                "observations": [
                    {"observed": "Revnue", "gold_target": "Revenue"},
                    {"observed": "acct", "gold_target": "Accounts Receivable"},
                ],
            },
            {
                "uid": "g-collision",
                "family": "collision",
                "layer": "gate_validation",
                "observations": [
                    {"observed": "turnover", "gold_target": "Sales"},
                ],
            },
        ],
        "candidates": [
            {
                "candidate_id": "c-revenue",
                "source_uid": "p-typo",
                "synonym": "Revnue",
                "target": "Revenue",
                "confidence": "high",
            },
            {
                "candidate_id": "c-wrong-mystery",
                "source_uid": "p-noise",
                "synonym": "mystery",
                "target": "Revenue",
                "confidence": "high",
            },
            {
                "candidate_id": "c-acct",
                "source_uid": "p-collision",
                "synonym": "acct",
                "target": "Accounts Receivable",
                "confidence": "low",
            },
            {
                "candidate_id": "c-turnover",
                "source_uid": "p-collision",
                "synonym": "turnover",
                "target": "Revenue",
                "confidence": "high",
            },
            {
                "candidate_id": "c-second-wrong-mystery",
                "source_uid": "p-noise",
                "synonym": "mystery",
                "target": "Amount",
                "confidence": None,
            },
        ],
        "initial_rules": {},
    }


@pytest.fixture
def config() -> dict[str, object]:
    return {
        "contract_version": replay.CONTRACT_VERSION,
        "min_source_gain": 0.1,
        "max_collateral_loss": 0.0,
        "max_gate_loss": 0.5,
        "rollback_budget": 0.1,
        "confidence_policy": {
            "high": "accept",
            "medium": "reject",
            "low": "reject",
            "missing": "unmeasurable",
        },
        "cost_proxy": {
            "source": 1.0,
            "collateral": 1.0,
            "gate": 2.0,
            "snapshot": 0.5,
        },
    }


def test_replay_is_deterministic_aggregate_only_and_has_seven_arms(dataset, config):
    first = replay.run_replay(dataset, config)
    second = replay.run_replay(dataset, config)

    assert first == second
    assert tuple(first["arms"]) == replay.ARMS
    assert first["meta"]["endpoint_calls"] == 0
    assert first["meta"]["paper_result"] is False
    assert first["meta"]["training_authorized"] is False
    assert len({arm["processed_order_sha256"] for arm in first["arms"].values()}) == 1
    rendered = json.dumps(first, ensure_ascii=False)
    for private_value in ("Revnue", "mystery", "p-typo", "g-collision"):
        assert private_value not in rendered


def test_state_divergence_forces_per_arm_score_recomputation(dataset, config):
    report = replay.run_replay(dataset, config)
    no_gate = report["arms"]["no_gate"]["events"][-1]
    fixed = report["arms"]["fixed_dual_gate"]["events"][-1]

    assert no_gate["step"] == fixed["step"] == 5
    assert no_gate["source_gain"] == 1.0
    assert fixed["source_gain"] == -1.0
    assert no_gate["accepted"] is True
    assert fixed["accepted"] is False


def test_confidence_missing_is_unmeasurable_not_a_surrogate_score(dataset, config):
    report = replay.run_replay(dataset, config)
    event = report["arms"]["confidence_only"]["events"][-1]

    assert event["decision"] == "unmeasurable"
    assert event["accepted"] is False
    assert event["retained_after_step"] is False


def test_rollback_restores_best_independent_validation_snapshot(dataset, config):
    report = replay.run_replay(dataset, config)
    enhanced = report["arms"]["independent_gate_validation"]
    rollback = report["arms"]["rollback_versioning"]
    turnover_event = rollback["events"][3]

    assert enhanced["events"][3]["accepted"] is True
    assert turnover_event["accepted"] is True
    assert turnover_event["rolled_back"] is True
    assert turnover_event["retained_after_step"] is False
    assert rollback["metrics"]["rollbacks"] == 1
    assert rollback["metrics"]["gate_utility"] > enhanced["metrics"]["gate_utility"]


@pytest.mark.parametrize("forbidden", ["gain", "collateral", "accepted", "split"])
def test_candidate_contract_rejects_recorded_outcomes(dataset, config, forbidden):
    bad = copy.deepcopy(dataset)
    bad["candidates"][0][forbidden] = 1

    with pytest.raises(ValueError, match="unknown candidate 0 fields"):
        replay.run_replay(bad, config)


@pytest.mark.parametrize("layer", ["sealed_test", "future_replay"])
def test_replay_refuses_sealed_and_future_layers(dataset, config, layer):
    bad = copy.deepcopy(dataset)
    bad["tables"][0]["layer"] = layer

    with pytest.raises(ValueError, match="forbidden or unknown data layer"):
        replay.run_replay(bad, config)


def test_candidate_sources_cannot_come_from_gate_validation(dataset, config):
    bad = copy.deepcopy(dataset)
    bad["candidates"][0]["source_uid"] = "g-typo"

    with pytest.raises(ValueError, match="source_uid must belong to proposal_train"):
        replay.run_replay(bad, config)


def test_paper_views_are_stable_watermarked_interfaces(dataset, config):
    report = replay.run_replay(dataset, config)
    first = views.build_phase2_views(report)
    second = views.build_phase2_views(report)

    assert first == second
    assert len(first["table_2_gate_baselines"]["rows"]) == 7
    assert len(first["figure_4_rule_dynamics"]["series"]) == 7 * 5
    assert first["manifest"]["paper_result"] is False
    assert first["manifest"]["watermark"] == "NOT_FOR_PAPER_UNTIL_INDEPENDENT_GB10_ACCEPTANCE"


def test_paper_view_rejects_self_promoted_report(dataset, config):
    report = replay.run_replay(dataset, config)
    report["meta"]["paper_result"] = True

    with pytest.raises(ValueError, match="only accepts unpromoted reports"):
        views.build_phase2_views(report)


def test_report_writer_refuses_overwrite(tmp_path):
    output = tmp_path / "report.json"
    replay._write_new(output, {"first": True})

    with pytest.raises(ValueError, match="refusing to overwrite"):
        replay._write_new(output, {"second": True})
