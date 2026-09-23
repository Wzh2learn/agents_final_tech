import hashlib
import json
from pathlib import Path
import socket
import sys

import pytest

from research import phase1a_learnability_baselines as probe


def _stable_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_stable_bytes(value))


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(_stable_bytes(row) for row in rows))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(
    sample_id: str,
    uid: str,
    observed_header: str,
    candidate_target: str | None,
    confidence: str | None,
    gold_action: str,
    gold_target: str | None,
    family: str,
) -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "uid": uid,
        "observed_header": observed_header,
        "canonical_fields": ["Revenue", "Amount"],
        "candidate_target": candidate_target,
        "confidence": confidence,
        "gold_action": gold_action,
        "gold_target": gold_target,
        "family": family,
    }


@pytest.fixture
def accepted_probe(tmp_path: Path) -> dict[str, Path]:
    package = tmp_path / "private-package"
    view = package / "artifacts" / "learnability_view.jsonl"
    manifest_path = package / "phase1a_manifest.json"
    precheck_path = tmp_path / "phase1a-precheck.json"
    receipt_path = tmp_path / "phase1a-independent-acceptance.json"
    config_path = tmp_path / "phase1a-prereg.json"

    train = [
        _case("t-map-1", "uid-t1", "Revenue", "Revenue", "high", "map_to", "Revenue", "exact"),
        _case("t-map-2", "uid-t2", "Amount", "Amount", "high", "map_to", "Amount", "exact"),
        _case("t-skip-1", "uid-t3", "Mystery", "Revenue", "low", "skip", None, "noise"),
        _case("t-skip-2", "uid-t4", "Unknown", "Amount", "low", "skip", None, "noise"),
        _case("t-hold-1", "uid-t5", "Ambiguous", "Revenue", "medium", "hold", None, "ambiguous"),
        _case("t-hold-2", "uid-t6", "Unclear", "Amount", "medium", "hold", None, "ambiguous"),
    ]
    dev = [
        _case("d-map-1", "uid-d1", "Revenue", "Revenue", "high", "map_to", "Revenue", "exact"),
        _case("d-map-2", "uid-d2", "Revnue", "Revenue", "high", "map_to", "Revenue", "typo"),
        _case("d-skip-1", "uid-d3", "Unknown", "Amount", "low", "skip", None, "noise"),
        _case("d-skip-2", "uid-d4", "Misleading", "Amount", "high", "skip", None, "collision"),
        _case("d-hold-1", "uid-d5", "Ambiguous", "Revenue", "medium", "hold", None, "ambiguous"),
        _case("d-hold-2", "uid-d6", "Unclear", "Amount", "medium", "hold", None, "ambiguous"),
    ]
    _write_jsonl(view, train + dev)

    def refs(rows: list[dict[str, object]]) -> list[dict[str, str]]:
        return [
            {"sample_id": str(row["sample_id"]), "uid": str(row["uid"])}
            for row in rows
        ]

    manifest = {
        "contract_version": "phase1a-data-package-v1",
        "package_id": "synthetic-learnability-fixture",
        "artifacts": [],
        "bindings": {},
        "layers": {
            "proposal_train": {"train": refs(train), "dev": refs(dev)},
            "gate_validation": [{"sample_id": "gate-secret", "uid": "uid-gate"}],
            "sealed_test": [{"sample_id": "sealed-secret", "uid": "uid-sealed"}],
            "future_replay": [{"sample_id": "future-secret", "uid": "uid-future"}],
        },
    }
    _write_json(manifest_path, manifest)
    manifest_sha = _sha256(manifest_path)

    precheck = {
        "status": "READY_FOR_INDEPENDENT_ACCEPTANCE",
        "meta": {
            "contract_version": "phase1a-data-package-v1",
            "endpoint_calls": 0,
            "socket_attempts": 0,
        },
        "hashes": {"manifest_sha256": manifest_sha},
        "gates": {
            gate: {"status": "PASS", "errors": []}
            for gate in (
                "artifact_integrity",
                "layer_isolation",
                "independent_correctness",
                "licence_permission",
                "confidence_provenance",
                "analysis_plan",
                "parser_contract",
            )
        },
    }
    _write_json(precheck_path, precheck)

    receipt = {
        "contract_version": "phase1a-independent-acceptance-v1",
        "status": "ACCEPTED_FOR_PHASE1A_LEARNABILITY",
        "scope": "proposal_train_only",
        "approved_by": "acceptance-lead",
        "approved_at": "2026-09-23T10:00:00Z",
        "package_manifest_sha256": manifest_sha,
        "precheck_report_sha256": _sha256(precheck_path),
        "learnability_view": {
            "path": "artifacts/learnability_view.jsonl",
            "bytes": view.stat().st_size,
            "sha256": _sha256(view),
        },
        "manual_reviews": {
            "licence_authority": {"status": "PASS", "reviewer_id": "reviewer-licence"},
            "label_independence": {"status": "PASS", "reviewer_id": "reviewer-labels"},
            "analysis_and_parser_provenance": {
                "status": "PASS",
                "reviewer_id": "reviewer-provenance",
            },
        },
    }
    _write_json(receipt_path, receipt)

    config = {
        "contract_version": "phase1a-learnability-probe-v1",
        "lexical_threshold": 0.8,
        "confidence_policy": {
            "high": "map_to",
            "medium": "hold",
            "low": "skip",
            "missing": "unmeasurable",
        },
        "classifier": {
            "epochs": 160,
            "learning_rate": 0.2,
            "l2": 0.01,
        },
        "bootstrap": {"samples": 200, "seed": 20260923},
        "decision_policy": {
            "min_dev_uids": 4,
            "min_action_macro_f1": 0.75,
            "max_harmful_action_rate": 0.2,
            "min_valid_action_coverage": 0.2,
            "min_classifier_macro_f1_gain": 0.05,
        },
    }
    _write_json(config_path, config)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["preregistered_config_sha256"] = _sha256(config_path)
    _write_json(receipt_path, receipt)
    return {
        "package": package,
        "manifest": manifest_path,
        "view": view,
        "precheck": precheck_path,
        "receipt": receipt_path,
        "config": config_path,
    }


def _refresh_view_binding(paths: dict[str, Path]) -> None:
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt["learnability_view"]["bytes"] = paths["view"].stat().st_size
    receipt["learnability_view"]["sha256"] = _sha256(paths["view"])
    _write_json(paths["receipt"], receipt)


def _refresh_config_binding(paths: dict[str, Path]) -> None:
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    receipt["preregistered_config_sha256"] = _sha256(paths["config"])
    _write_json(paths["receipt"], receipt)


def _run(paths: dict[str, Path]) -> dict[str, object]:
    return probe.run_probe(
        package_root=paths["package"],
        precheck_report=paths["precheck"],
        acceptance_receipt=paths["receipt"],
        config_path=paths["config"],
    )


def test_probe_is_deterministic_aggregate_only_and_has_five_baselines(
    accepted_probe: dict[str, Path],
) -> None:
    first = _run(accepted_probe)
    second = _run(accepted_probe)

    assert first == second
    assert set(first["baselines"]) == {
        "always_skip",
        "deterministic_matcher",
        "lexical_fuzzy",
        "confidence_only",
        "simple_classifier",
    }
    assert first["meta"]["endpoint_calls"] == 0
    assert first["meta"]["socket_attempts"] == 0
    assert first["meta"]["evidence_level"] == "DEVELOPMENT_ONLY"
    assert len(first["hashes"]["implementation_sha256"]) == 64
    assert first["decision"] in {
        "SIMPLE_SUFFICIENT",
        "LEARNABILITY_SIGNAL",
        "NO_CLEAR_SIGNAL",
        "PILOT_ONLY",
    }
    assert first["decision"] != "DATA_GO"
    rendered = json.dumps(first, ensure_ascii=False)
    for private_value in ("Revnue", "Misleading", "uid-d1", "d-map-1"):
        assert private_value not in rendered


def test_metrics_include_required_risk_coverage_and_uid_intervals(
    accepted_probe: dict[str, Path],
) -> None:
    report = _run(accepted_probe)
    metrics = report["baselines"]["lexical_fuzzy"]["dev"]

    assert set(metrics) >= {
        "action_macro_f1",
        "correct_map_to_recall",
        "hold_recall",
        "harmful_action_rate",
        "map_to_risk",
        "valid_action_coverage",
        "evaluated_samples",
        "evaluated_uids",
        "uid_cluster_intervals",
        "worst_family",
    }
    assert set(metrics["uid_cluster_intervals"]) == {
        "action_macro_f1",
        "harmful_action_rate",
        "valid_action_coverage",
    }


def test_missing_confidence_is_unmeasurable_not_filled(
    accepted_probe: dict[str, Path],
) -> None:
    rows = [
        json.loads(line)
        for line in accepted_probe["view"].read_text(encoding="utf-8").splitlines()
    ]
    next(row for row in rows if row["sample_id"] == "d-hold-1")["confidence"] = None
    _write_jsonl(accepted_probe["view"], rows)
    _refresh_view_binding(accepted_probe)

    report = _run(accepted_probe)
    confidence = report["baselines"]["confidence_only"]["dev"]

    assert confidence["evaluated_samples"] == 5
    assert confidence["excluded_unmeasurable"] == 1
    assert confidence["scope"] == "confidence_measurable_subset"
    assert confidence["comparable_to_full_dev"] is False


@pytest.mark.parametrize("forbidden", ["gain", "collateral", "accepted", "split", "partition"])
def test_case_contract_rejects_post_outcome_and_split_fields(
    accepted_probe: dict[str, Path],
    forbidden: str,
) -> None:
    rows = [
        json.loads(line)
        for line in accepted_probe["view"].read_text(encoding="utf-8").splitlines()
    ]
    rows[0][forbidden] = 1
    _write_jsonl(accepted_probe["view"], rows)
    _refresh_view_binding(accepted_probe)

    with pytest.raises(ValueError, match="unknown case fields"):
        _run(accepted_probe)


def test_classifier_features_ignore_labels_identity_and_family() -> None:
    row = _case(
        "sample-a",
        "uid-a",
        "Revnue",
        "Revenue",
        "high",
        "map_to",
        "Revenue",
        "typo",
    )
    before = probe._features(row)
    row.update({
        "sample_id": "sample-b",
        "uid": "uid-b",
        "gold_action": "skip",
        "gold_target": None,
        "family": "collision",
    })
    assert probe._features(row) == before


def test_view_cannot_include_gate_validation_or_sealed_samples(
    accepted_probe: dict[str, Path],
) -> None:
    rows = [
        json.loads(line)
        for line in accepted_probe["view"].read_text(encoding="utf-8").splitlines()
    ]
    rows.append(_case(
        "sealed-secret",
        "uid-sealed",
        "must-not-be-read",
        "Revenue",
        "high",
        "map_to",
        "Revenue",
        "sealed",
    ))
    _write_jsonl(accepted_probe["view"], rows)
    _refresh_view_binding(accepted_probe)

    with pytest.raises(ValueError, match="proposal_train sample set"):
        _run(accepted_probe)


def test_view_must_cover_every_proposal_train_sample(
    accepted_probe: dict[str, Path],
) -> None:
    rows = [
        json.loads(line)
        for line in accepted_probe["view"].read_text(encoding="utf-8").splitlines()
    ][1:]
    _write_jsonl(accepted_probe["view"], rows)
    _refresh_view_binding(accepted_probe)

    with pytest.raises(ValueError, match="proposal_train sample set"):
        _run(accepted_probe)


def test_view_hash_and_safe_relative_path_are_mandatory(
    accepted_probe: dict[str, Path],
) -> None:
    receipt = json.loads(accepted_probe["receipt"].read_text(encoding="utf-8"))
    receipt["learnability_view"]["sha256"] = "0" * 64
    _write_json(accepted_probe["receipt"], receipt)
    with pytest.raises(ValueError, match="view SHA-256"):
        _run(accepted_probe)

    receipt["learnability_view"]["sha256"] = _sha256(accepted_probe["view"])
    receipt["learnability_view"]["path"] = "../outside.jsonl"
    _write_json(accepted_probe["receipt"], receipt)
    with pytest.raises(ValueError, match="safe package-relative"):
        _run(accepted_probe)


def test_independent_acceptance_receipt_is_fail_closed(
    accepted_probe: dict[str, Path],
) -> None:
    receipt = json.loads(accepted_probe["receipt"].read_text(encoding="utf-8"))
    receipt["status"] = "DRAFT"
    _write_json(accepted_probe["receipt"], receipt)
    with pytest.raises(ValueError, match="not accepted"):
        _run(accepted_probe)


def test_precheck_requires_the_complete_seven_gate_set(
    accepted_probe: dict[str, Path],
) -> None:
    precheck = json.loads(accepted_probe["precheck"].read_text(encoding="utf-8"))
    precheck["gates"].pop("parser_contract")
    _write_json(accepted_probe["precheck"], precheck)
    with pytest.raises(ValueError, match="gate set"):
        _run(accepted_probe)


def test_acceptance_receipt_binds_preregistered_config(
    accepted_probe: dict[str, Path],
) -> None:
    config = json.loads(accepted_probe["config"].read_text(encoding="utf-8"))
    config["lexical_threshold"] = 0.9
    _write_json(accepted_probe["config"], config)
    with pytest.raises(ValueError, match="preregistered-config SHA-256"):
        _run(accepted_probe)


def test_manual_reviewers_must_be_distinct(
    accepted_probe: dict[str, Path],
) -> None:
    receipt = json.loads(accepted_probe["receipt"].read_text(encoding="utf-8"))
    for review in receipt["manual_reviews"].values():
        review["reviewer_id"] = "same-reviewer"
    _write_json(accepted_probe["receipt"], receipt)
    with pytest.raises(ValueError, match="distinct reviewers"):
        _run(accepted_probe)


def test_preregistration_rejects_invalid_thresholds_and_unknown_fields(
    accepted_probe: dict[str, Path],
) -> None:
    config = json.loads(accepted_probe["config"].read_text(encoding="utf-8"))
    config["lexical_threshold"] = 1.1
    _write_json(accepted_probe["config"], config)
    with pytest.raises(ValueError, match="lexical_threshold"):
        _run(accepted_probe)

    config["lexical_threshold"] = 0.8
    config["test_optimized_threshold"] = 0.9
    _write_json(accepted_probe["config"], config)
    with pytest.raises(ValueError, match="unknown config fields"):
        _run(accepted_probe)


def test_combined_classifier_and_bootstrap_work_is_bounded(
    accepted_probe: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = json.loads(accepted_probe["config"].read_text(encoding="utf-8"))
    config["classifier"]["epochs"] = 10_000
    _write_json(accepted_probe["config"], config)
    _refresh_config_binding(accepted_probe)
    monkeypatch.setattr(probe, "MAX_CLASSIFIER_WORK", 10_000)
    with pytest.raises(ValueError, match="classifier work budget"):
        _run(accepted_probe)

    config["classifier"]["epochs"] = 160
    config["bootstrap"]["samples"] = 10_000
    _write_json(accepted_probe["config"], config)
    _refresh_config_binding(accepted_probe)
    monkeypatch.setattr(probe, "MAX_CLASSIFIER_WORK", 5_000_000)
    monkeypatch.setattr(probe, "MAX_BOOTSTRAP_WORK", 10_000)
    with pytest.raises(ValueError, match="bootstrap work budget"):
        _run(accepted_probe)


def test_decision_gate_prefers_nonlearned_simple_sufficiency() -> None:
    policy = {
        "min_dev_uids": 4,
        "min_action_macro_f1": 0.75,
        "max_harmful_action_rate": 0.1,
        "min_valid_action_coverage": 0.2,
        "min_classifier_macro_f1_gain": 0.05,
    }
    metrics = {
        "deterministic_matcher": {
            "action_macro_f1": 0.8,
            "harmful_action_rate": 0.0,
            "valid_action_coverage": 0.3,
        },
        "lexical_fuzzy": {
            "action_macro_f1": 0.7,
            "harmful_action_rate": 0.0,
            "valid_action_coverage": 0.3,
        },
        "confidence_only": {
            "action_macro_f1": 0.7,
            "harmful_action_rate": 0.0,
            "valid_action_coverage": 0.3,
        },
        "simple_classifier": {
            "action_macro_f1": 0.83,
            "harmful_action_rate": 0.0,
            "valid_action_coverage": 0.4,
        },
    }
    assert probe.decide_probe(6, metrics, policy)["status"] == "SIMPLE_SUFFICIENT"


def test_decision_gate_keeps_residual_signal_when_nonlearned_also_passes() -> None:
    policy = {
        "min_dev_uids": 4,
        "min_action_macro_f1": 0.75,
        "max_harmful_action_rate": 0.1,
        "min_valid_action_coverage": 0.2,
        "min_classifier_macro_f1_gain": 0.05,
    }
    metrics = {
        name: {
            "action_macro_f1": score,
            "harmful_action_rate": 0.0,
            "valid_action_coverage": 0.3,
        }
        for name, score in (
            ("deterministic_matcher", 0.8),
            ("lexical_fuzzy", 0.7),
            ("confidence_only", 0.7),
            ("simple_classifier", 0.9),
        )
    }
    assert probe.decide_probe(6, metrics, policy)["status"] == "LEARNABILITY_SIGNAL"


def test_decision_gate_can_report_learnability_without_training_permission() -> None:
    policy = {
        "min_dev_uids": 4,
        "min_action_macro_f1": 0.75,
        "max_harmful_action_rate": 0.1,
        "min_valid_action_coverage": 0.2,
        "min_classifier_macro_f1_gain": 0.05,
    }
    metrics = {
        name: {
            "action_macro_f1": 0.5,
            "harmful_action_rate": 0.0,
            "valid_action_coverage": 0.2,
        }
        for name in ("deterministic_matcher", "lexical_fuzzy", "confidence_only")
    }
    metrics["simple_classifier"] = {
        "action_macro_f1": 0.8,
        "harmful_action_rate": 0.05,
        "valid_action_coverage": 0.3,
    }
    decision = probe.decide_probe(6, metrics, policy)
    assert decision["status"] == "LEARNABILITY_SIGNAL"
    assert decision["training_authorized"] is False


def test_cli_refuses_overwrite_and_keeps_report_outside_repo(
    accepted_probe: dict[str, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "probe-report.json"
    argv = [
        "phase1a_learnability_baselines.py",
        "--package-root",
        str(accepted_probe["package"]),
        "--precheck-report",
        str(accepted_probe["precheck"]),
        "--acceptance-receipt",
        str(accepted_probe["receipt"]),
        "--config",
        str(accepted_probe["config"]),
        "--output",
        str(output),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    assert probe.main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["decision"] != "DATA_GO"

    before = output.read_bytes()
    with pytest.raises(SystemExit):
        probe.main()
    assert output.read_bytes() == before


def test_probe_restores_socket_functions(accepted_probe: dict[str, Path]) -> None:
    original = socket.create_connection
    _run(accepted_probe)
    assert socket.create_connection is original
