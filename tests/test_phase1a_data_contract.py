import copy
import hashlib
import json
from pathlib import Path
import socket
import sys

import pytest

from research import phase1a_data_contract as contract


def _stable_bytes(value: object) -> bytes:
    return (json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ) + "\n").encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_stable_bytes(value))


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(_stable_bytes(row) for row in rows))


def _artifact(path: Path, artifact_id: str, role: str) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "id": artifact_id,
        "role": role,
        "path": path.relative_to(path.parents[1]).as_posix(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(value: object) -> str:
    return hashlib.sha256(_stable_bytes(value).rstrip(b"\n")).hexdigest()


@pytest.fixture
def package(tmp_path: Path) -> Path:
    root = tmp_path / "phase1a-package"
    artifacts = root / "artifacts"

    lineage_specs = {
        name: {
            "dataset_id": "fixture-finance",
            "dataset_revision": "rev-2026-09-23",
            "source_split": source_split,
            "independence_cluster": (
                "cluster-proposal" if name in {"train", "dev"} else f"cluster-{name}"
            ),
            "lineage_root_id": f"report-{name}",
            "transformation_parent_id": None,
        }
        for name, source_split in (
            ("train", "train"),
            ("dev", "train"),
            ("gate", "validation"),
            ("test", "test"),
            ("future", "future-2027q1"),
        )
    }
    uids = {
        name: contract.lineage_uid(
            str(spec["dataset_id"]),
            str(spec["dataset_revision"]),
            str(spec["lineage_root_id"]),
        )
        for name, spec in lineage_specs.items()
    }

    _write_jsonl(artifacts / "source_tables.jsonl", [
        {"uid": uid, "headers": ["alias", "amount"]}
        for uid in uids.values()
    ])
    _write_json(artifacts / "schema.json", {
        "canonical_fields": ["Revenue", "Amount"],
    })
    _write_json(artifacts / "injection_map.json", {
        uid: [{"col": 0, "canonical": "Revenue", "family": "alias_variant"}]
        for uid in uids.values()
    })

    samples = [
        ("sample-train", uids["train"], "map_to", "Revenue"),
        ("sample-dev", uids["dev"], "skip", None),
        ("sample-gate", uids["gate"], "hold", None),
        ("sample-test", uids["test"], "map_to", "Amount"),
        ("sample-future", uids["future"], "skip", None),
    ]
    _write_jsonl(artifacts / "labels.jsonl", [
        {
            "sample_id": sample_id,
            "uid": uid,
            "col": 0,
            "gold_action": action,
            "gold_target": target,
            "quality_grade": "Q3",
            "reviewers": [
                {"reviewer_id": "reviewer-a", "action": action, "target": target},
                {"reviewer_id": "reviewer-b", "action": action, "target": target},
            ],
            "adjudication": None,
        }
        for sample_id, uid, action, target in samples
    ])
    def sample(sample_id: str, name: str) -> dict[str, object]:
        return {"sample_id": sample_id, "uid": uids[name], **lineage_specs[name]}

    layers = {
        "proposal_train": {
            "train": [sample("sample-train", "train")],
            "dev": [sample("sample-dev", "dev")],
        },
        "gate_validation": [sample("sample-gate", "gate")],
        "sealed_test": [sample("sample-test", "test")],
        "future_replay": [sample("sample-future", "future")],
    }
    covered_hashes = {
        "source-tables": _file_hash(artifacts / "source_tables.jsonl"),
        "schema": _file_hash(artifacts / "schema.json"),
        "injection-map": _file_hash(artifacts / "injection_map.json"),
        "labels": _file_hash(artifacts / "labels.jsonl"),
    }
    _write_json(artifacts / "licence.json", {
        "status": "accepted",
        "accepted_by": "data-owner",
        "accepted_at": "2026-09-23T00:00:00Z",
        "permitted_uses": ["training", "tuning", "evaluation", "rule_acceptance"],
        "covered_artifact_sha256": covered_hashes,
    })
    _write_json(artifacts / "confidence.json", {
        "field": "confidence",
        "source": "pre_verification_teacher_output",
        "allowed_values": ["low", "medium", "high"],
        "missing_policy": "unmeasurable",
        "gain_collateral_substitution": False,
    })
    _write_json(artifacts / "features.json", {
        "contract_version": contract.FEATURE_LEDGER_VERSION,
        "source_tables_sha256": _file_hash(artifacts / "source_tables.jsonl"),
        "schema_sha256": _file_hash(artifacts / "schema.json"),
        "confidence_manifest_sha256": _file_hash(artifacts / "confidence.json"),
        "rows": [
            {
                "sample_id": "sample-train",
                "uid": uids["train"],
                "observed_header": "alias",
                "canonical_fields": ["Revenue", "Amount"],
                "candidate_target": "Revenue",
                "confidence": "high",
                "family": "alias_variant",
            },
            {
                "sample_id": "sample-dev",
                "uid": uids["dev"],
                "observed_header": "amount",
                "canonical_fields": ["Revenue", "Amount"],
                "candidate_target": "Amount",
                "confidence": "medium",
                "family": "alias_variant",
            },
        ],
    })
    licence = json.loads((artifacts / "licence.json").read_text(encoding="utf-8"))
    licence["covered_artifact_sha256"]["features"] = _file_hash(artifacts / "features.json")
    _write_json(artifacts / "licence.json", licence)
    _write_json(artifacts / "analysis_plan.json", {
        "status": "approved",
        "approved_by": "research-owner",
        "approved_at": "2026-09-23T00:00:00Z",
        "cluster_unit": "lineage_uid",
        "significance_level": 0.05,
        "target_power": 0.8,
        "risk_limit": 0.1,
        "noninferiority_margins": {
            "delta_quality": 0.02,
            "delta_harm": 0.02,
            "delta_retention": 0.02,
        },
        "primary_metrics": ["action_macro_f1", "harmful_map_rate"],
        "threshold_selection": "proposal_dev_only",
        "seed_uid_aggregation": "fixed_seed_pair_then_uid_cluster_bootstrap",
        "holm_families": contract.REQUIRED_HOLM_FAMILIES,
        "one_sided_p_value_methods": {
            "H2a_quality_noninferiority": "paired_uid_sign_flip_on_seed_mean_difference",
            "H2b_safety_noninferiority": "paired_uid_sign_flip_on_seed_mean_difference",
            "H2c_risk_constrained_coverage": "paired_uid_sign_flip_on_seed_mean_difference",
            "H3a_cluster_any_harm": "exact_mcnemar",
            "H3a_valid_rule_retention": "paired_cluster_sign_flip_noninferiority",
        },
        "holm_adjustment": "step_down_adjusted_p_and_simultaneous_one_sided_ci",
        "minimum_uid_by_role_family": {"proposal_train.dev/*": 2},
        "minimum_uid_by_action": {"skip": 2, "hold": 2, "map_to": 2},
        "mde_by_confirmatory_contrast": {
            "H2a_quality_noninferiority": 0.05,
            "H2b_safety_noninferiority": 0.03,
            "H2c_risk_constrained_coverage": 0.05,
            "H3a_cluster_any_harm": 0.05,
            "H3a_valid_rule_retention": 0.05,
        },
        "layer_manifest_sha256": _stable_hash(layers),
    })

    artifact_specs = [
        ("source-tables", "source_tables", artifacts / "source_tables.jsonl"),
        ("schema", "schema", artifacts / "schema.json"),
        ("injection-map", "injection_map", artifacts / "injection_map.json"),
        ("labels", "label_ledger", artifacts / "labels.jsonl"),
        ("features", "learnability_feature_ledger", artifacts / "features.json"),
        ("licence", "licence_record", artifacts / "licence.json"),
        ("confidence", "confidence_manifest", artifacts / "confidence.json"),
        ("analysis-plan", "analysis_plan", artifacts / "analysis_plan.json"),
    ]
    manifest_artifacts = [_artifact(path, artifact_id, role)
                          for artifact_id, role, path in artifact_specs]
    hashes = {item["id"]: item["sha256"] for item in manifest_artifacts}
    _write_json(artifacts / "parser_receipt.json", {
        "status": "PASS",
        "checker": "phase1a-parser-contract-v1",
        "commit": "0123456789abcdef0123456789abcdef01234567",
        "executed_at": "2026-09-23T00:00:00Z",
        "input_sha256": {
            "source-tables": hashes["source-tables"],
            "schema": hashes["schema"],
            "injection-map": hashes["injection-map"],
        },
    })
    manifest_artifacts.append(_artifact(
        artifacts / "parser_receipt.json", "parser-receipt", "parser_contract_receipt"))

    _write_json(root / "phase1a_manifest.json", {
        "contract_version": contract.CONTRACT_VERSION,
        "package_id": "fixture-package-v2",
        "artifacts": manifest_artifacts,
        "layers": layers,
        "bindings": {
            "label_ledger": "labels",
            "learnability_feature_ledger": "features",
            "licence_record": "licence",
            "confidence_manifest": "confidence",
            "analysis_plan": "analysis-plan",
            "parser_contract_receipt": "parser-receipt",
        },
    })
    return root


def _manifest(package: Path) -> dict[str, object]:
    return json.loads((package / "phase1a_manifest.json").read_text(encoding="utf-8"))


def _save_manifest(package: Path, value: dict[str, object]) -> None:
    _write_json(package / "phase1a_manifest.json", value)


def test_complete_package_is_ready_for_independent_acceptance(package: Path) -> None:
    first = contract.validate_package(package)
    second = contract.validate_package(package)

    assert first == second
    assert first["status"] == "READY_FOR_INDEPENDENT_ACCEPTANCE"
    assert first["meta"] == {
        "phase": "precheck",
        "endpoint_calls": 0,
        "socket_attempts": 0,
        "contract_version": contract.CONTRACT_VERSION,
    }
    assert set(first["gates"]) == {
        "artifact_integrity",
        "layer_isolation",
        "independent_correctness",
        "licence_permission",
        "confidence_provenance",
        "analysis_plan",
        "parser_contract",
    }
    assert all(gate["status"] == "PASS" for gate in first["gates"].values())
    assert first["counts"]["samples"] == 5
    assert first["counts"]["uids"] == 5
    assert first["counts"]["labels"] == 5
    assert first["label_quality"] == {
        "rows_with_valid_reviewer_sets": 5,
        "raw_action_agreement": 1.0,
        "raw_action_target_agreement": 1.0,
        "pooled_pairwise_action_kappa": 1.0,
        "target_agreement_on_joint_map_to_pairs": 1.0,
        "conflict_rate": 0.0,
        "adjudication_rate_given_conflict": None,
    }
    assert first["status"] != "DATA_GO"
    assert "not DATA_GO" in first["release_boundary"]


@pytest.mark.parametrize(
    ("mutation", "gate", "error"),
    [
        ("hash", "artifact_integrity", "sha256_mismatch"),
        ("feature_ledger_source_hash", "artifact_integrity", "feature_ledger_source_hash_mismatch"),
        ("overlap", "layer_isolation", "uid_cross_partition"),
        ("missing_label", "independent_correctness", "missing_label"),
        ("one_reviewer", "independent_correctness", "insufficient_independent_reviewers"),
        ("licence", "licence_permission", "missing_permitted_use"),
        ("licence_hash", "licence_permission", "licence_artifact_hash_mismatch"),
        ("confidence", "confidence_provenance", "invalid_missing_policy"),
        ("analysis", "analysis_plan", "analysis_plan_not_approved"),
        ("analysis_action_minimum", "analysis_plan", "invalid_minimum_uid_by_action"),
        ("analysis_layers", "analysis_plan", "layer_manifest_hash_mismatch"),
        ("parser", "parser_contract", "parser_input_hash_mismatch"),
    ],
)
def test_gate_failures_never_release_data(
    package: Path,
    mutation: str,
    gate: str,
    error: str,
) -> None:
    manifest = _manifest(package)
    artifacts = {item["id"]: item for item in manifest["artifacts"]}

    if mutation == "hash":
        artifacts["schema"]["sha256"] = "0" * 64
    elif mutation == "feature_ledger_source_hash":
        path = package / artifacts["features"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["schema_sha256"] = "b" * 64
        _write_json(path, value)
        artifacts["features"].update(
            _artifact(path, "features", "learnability_feature_ledger"))
        licence_path = package / artifacts["licence"]["path"]
        licence = json.loads(licence_path.read_text(encoding="utf-8"))
        licence["covered_artifact_sha256"]["features"] = _file_hash(path)
        _write_json(licence_path, licence)
        artifacts["licence"].update(_artifact(licence_path, "licence", "licence_record"))
    elif mutation == "overlap":
        manifest["layers"]["sealed_test"][0]["uid"] = manifest["layers"]["proposal_train"]["train"][0]["uid"]
    elif mutation in {"missing_label", "one_reviewer"}:
        path = package / artifacts["labels"]["path"]
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if mutation == "missing_label":
            rows.pop()
        else:
            rows[0]["reviewers"].pop()
        _write_jsonl(path, rows)
        artifacts["labels"].update(_artifact(path, "labels", "label_ledger"))
    elif mutation in {"licence", "licence_hash"}:
        path = package / artifacts["licence"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "licence":
            value["permitted_uses"].remove("training")
        else:
            value["covered_artifact_sha256"]["schema"] = "e" * 64
        _write_json(path, value)
        artifacts["licence"].update(_artifact(path, "licence", "licence_record"))
    elif mutation == "confidence":
        path = package / artifacts["confidence"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["missing_policy"] = "fill_zero"
        _write_json(path, value)
        artifacts["confidence"].update(_artifact(path, "confidence", "confidence_manifest"))
    elif mutation in {"analysis", "analysis_action_minimum", "analysis_layers"}:
        path = package / artifacts["analysis-plan"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "analysis":
            value["status"] = "draft"
        elif mutation == "analysis_action_minimum":
            value["minimum_uid_by_action"]["hold"] = 1
        else:
            value["layer_manifest_sha256"] = "d" * 64
        _write_json(path, value)
        artifacts["analysis-plan"].update(_artifact(path, "analysis-plan", "analysis_plan"))
    elif mutation == "parser":
        path = package / artifacts["parser-receipt"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        value["input_sha256"]["schema"] = "f" * 64
        _write_json(path, value)
        artifacts["parser-receipt"].update(_artifact(
            path, "parser-receipt", "parser_contract_receipt"))

    _save_manifest(package, manifest)
    report = contract.validate_package(package)
    assert report["status"] == "DATA_NO_GO"
    assert report["gates"][gate]["status"] == "FAIL"
    assert error in {item["code"] for item in report["gates"][gate]["errors"]}
    assert report["status"] != "DATA_GO"


def test_path_escape_is_rejected_without_reading_outside_package(
    package: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "private.json"
    outside.write_text('{"secret":"must-not-be-read"}', encoding="utf-8")
    manifest = _manifest(package)
    manifest["artifacts"][0]["path"] = "../private.json"
    _save_manifest(package, manifest)

    report = contract.validate_package(package)
    assert report["status"] == "DATA_NO_GO"
    errors = report["gates"]["artifact_integrity"]["errors"]
    assert {item["code"] for item in errors} == {"unsafe_artifact_path"}
    assert "secret" not in json.dumps(report)


def test_duplicate_role_cannot_bypass_feature_ledger_hash_binding(
    package: Path,
) -> None:
    import shutil

    manifest = _manifest(package)
    schema_entry = next(a for a in manifest["artifacts"] if a["id"] == "schema")
    schema_path = package / schema_entry["path"]
    dup_path = schema_path.parent / "schema_copy.json"
    shutil.copy(schema_path, dup_path)
    manifest["artifacts"].append(_artifact(dup_path, "schema-copy", "schema"))

    feat_entry = next(a for a in manifest["artifacts"] if a["id"] == "features")
    feat_path = package / feat_entry["path"]
    features = json.loads(feat_path.read_text(encoding="utf-8"))
    features["schema_sha256"] = "e" * 64
    _write_json(feat_path, features)
    feat_entry.update(_artifact(feat_path, "features", "learnability_feature_ledger"))

    # Cover every duplicate in licence and parser receipt so only the role
    # duplication itself can fail the package.
    lic_entry = next(a for a in manifest["artifacts"] if a["id"] == "licence")
    lic_path = package / lic_entry["path"]
    licence = json.loads(lic_path.read_text(encoding="utf-8"))
    licence["covered_artifact_sha256"]["schema-copy"] = _file_hash(dup_path)
    licence["covered_artifact_sha256"]["features"] = _file_hash(feat_path)
    _write_json(lic_path, licence)
    lic_entry.update(_artifact(lic_path, "licence", "licence_record"))

    receipt_entry = next(a for a in manifest["artifacts"] if a["id"] == "parser-receipt")
    receipt_path = package / receipt_entry["path"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["input_sha256"]["schema-copy"] = _file_hash(dup_path)
    _write_json(receipt_path, receipt)
    receipt_entry.update(
        _artifact(receipt_path, "parser-receipt", "parser_contract_receipt"))

    _save_manifest(package, manifest)
    report = contract.validate_package(package)
    assert report["status"] == "DATA_NO_GO"
    codes = {item["code"] for item in report["gates"]["artifact_integrity"]["errors"]}
    assert "duplicate_role_artifact" in codes
    assert "feature_ledger_source_hash_mismatch" not in codes


def test_disagreement_requires_adjudication(package: Path) -> None:
    manifest = _manifest(package)
    artifact = next(item for item in manifest["artifacts"] if item["id"] == "labels")
    path = package / artifact["path"]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["reviewers"][1] = {
        "reviewer_id": "reviewer-b",
        "action": "hold",
        "target": None,
    }
    _write_jsonl(path, rows)
    artifact.update(_artifact(path, "labels", "label_ledger"))
    licence_artifact = next(
        item for item in manifest["artifacts"] if item["id"] == "licence"
    )
    licence_path = package / licence_artifact["path"]
    licence = json.loads(licence_path.read_text(encoding="utf-8"))
    licence["covered_artifact_sha256"]["labels"] = _file_hash(path)
    _write_json(licence_path, licence)
    licence_artifact.update(_artifact(licence_path, "licence", "licence_record"))
    _save_manifest(package, manifest)

    report = contract.validate_package(package)
    errors = report["gates"]["independent_correctness"]["errors"]
    assert report["status"] == "DATA_NO_GO"
    assert "missing_adjudication" in {item["code"] for item in errors}


def test_label_quality_reports_conflict_and_adjudication_rates(package: Path) -> None:
    manifest = _manifest(package)
    artifact = next(item for item in manifest["artifacts"] if item["id"] == "labels")
    path = package / artifact["path"]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["reviewers"][1] = {
        "reviewer_id": "reviewer-b",
        "action": "hold",
        "target": None,
    }
    rows[0]["adjudication"] = {
        "adjudicator_id": "reviewer-c",
        "action": rows[0]["gold_action"],
        "target": rows[0]["gold_target"],
    }
    _write_jsonl(path, rows)
    artifact.update(_artifact(path, "labels", "label_ledger"))
    licence_artifact = next(
        item for item in manifest["artifacts"] if item["id"] == "licence"
    )
    licence_path = package / licence_artifact["path"]
    licence = json.loads(licence_path.read_text(encoding="utf-8"))
    licence["covered_artifact_sha256"]["labels"] = _file_hash(path)
    _write_json(licence_path, licence)
    licence_artifact.update(_artifact(licence_path, "licence", "licence_record"))
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    assert report["status"] == "READY_FOR_INDEPENDENT_ACCEPTANCE"
    assert report["label_quality"]["conflict_rate"] == 0.2
    assert report["label_quality"]["adjudication_rate_given_conflict"] == 1.0
    assert report["label_quality"]["raw_action_agreement"] == 0.8


def test_unhashable_confidence_vocabulary_is_rejected_without_crashing(
    package: Path,
) -> None:
    manifest = _manifest(package)
    artifact = next(
        item for item in manifest["artifacts"] if item["id"] == "confidence"
    )
    path = package / artifact["path"]
    value = json.loads(path.read_text(encoding="utf-8"))
    value["allowed_values"] = ["low", ["medium"], "high"]
    _write_json(path, value)
    artifact.update(_artifact(path, "confidence", "confidence_manifest"))
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    assert report["status"] == "DATA_NO_GO"
    errors = report["gates"]["confidence_provenance"]["errors"]
    assert "invalid_confidence_vocabulary" in {item["code"] for item in errors}


def test_empty_bound_artifact_is_rejected_without_crashing(package: Path) -> None:
    manifest = _manifest(package)
    artifact = next(
        item for item in manifest["artifacts"] if item["id"] == "confidence"
    )
    path = package / artifact["path"]
    path.write_bytes(b"")
    artifact.update(_artifact(path, "confidence", "confidence_manifest"))
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    assert report["status"] == "DATA_NO_GO"
    integrity_errors = report["gates"]["artifact_integrity"]["errors"]
    confidence_errors = report["gates"]["confidence_provenance"]["errors"]
    assert "empty_artifact" in {item["code"] for item in integrity_errors}
    assert "invalid_bound_json" in {item["code"] for item in confidence_errors}


def test_malformed_manifest_is_rejected_without_crashing(tmp_path: Path) -> None:
    package = tmp_path / "phase1a-package"
    package.mkdir()
    (package / "phase1a_manifest.json").write_text(
        '{"contract_version":"phase1a-data-package-v2",',
        encoding="utf-8",
    )

    report = contract.validate_package(package)

    assert report["status"] == "DATA_NO_GO"
    errors = report["gates"]["artifact_integrity"]["errors"]
    assert "invalid_manifest_json" in {item["code"] for item in errors}


def test_offline_guard_blocks_and_restores_sockets() -> None:
    original = socket.create_connection
    with contract.offline_guard() as attempts:
        with pytest.raises(RuntimeError, match="network"):
            socket.create_connection(("invalid.example", 443))
        assert attempts == [1]
    assert socket.create_connection is original


def test_cli_writes_deterministic_private_report_without_overwrite(
    package: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "phase1a-precheck.json"
    monkeypatch.setattr(sys, "argv", [
        "phase1a_data_contract.py",
        "--package-root", str(package),
        "--output", str(output),
    ])
    assert contract.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "READY_FOR_INDEPENDENT_ACCEPTANCE"
    assert report["meta"]["endpoint_calls"] == 0
    assert report["meta"]["socket_attempts"] == 0

    before = output.read_bytes()
    with pytest.raises(SystemExit):
        contract.main()
    assert output.read_bytes() == before


def _refresh_analysis_layer_hash(package: Path, manifest: dict[str, object]) -> None:
    artifact = next(item for item in manifest["artifacts"] if item["id"] == "analysis-plan")
    path = package / artifact["path"]
    value = json.loads(path.read_text(encoding="utf-8"))
    value["layer_manifest_sha256"] = _stable_hash(manifest["layers"])
    _write_json(path, value)
    artifact.update(_artifact(path, "analysis-plan", "analysis_plan"))


def test_empty_future_replay_is_ready_with_hash_bound_protocol(
    package: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(package)
    manifest["layers"]["future_replay"] = []
    artifacts = {item["id"]: item for item in manifest["artifacts"]}
    labels_path = package / artifacts["labels"]["path"]
    labels = [
        json.loads(line)
        for line in labels_path.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["sample_id"] != "sample-future"
    ]
    _write_jsonl(labels_path, labels)
    artifacts["labels"].update(_artifact(labels_path, "labels", "label_ledger"))
    licence_path = package / artifacts["licence"]["path"]
    licence = json.loads(licence_path.read_text(encoding="utf-8"))
    licence["covered_artifact_sha256"]["labels"] = _file_hash(labels_path)
    _write_json(licence_path, licence)
    artifacts["licence"].update(_artifact(licence_path, "licence", "licence_record"))
    protocol_path = package / "artifacts" / "future_replay_protocol.json"
    _write_json(protocol_path, {
        "contract_version": "future-replay-acquisition-v1",
        "status": "HASH_BOUND_PROTOCOL",
        "cycle_id": "cycle-2026-09-paper-1",
        "freeze_receipt_sha256": "a" * 64,
        "approved_by": "research-owner",
        "approved_at": "2026-09-23T00:00:00Z",
        "acquire_after": "2026-10-23T00:00:00Z",
        "source_constraints": "new source lineage roots acquired after system freeze",
        "partition_rule": "assign before content inspection; never tune on this cycle",
        "contamination_policy": "never_return_to_current_cycle",
    })
    manifest["artifacts"].append(_artifact(
        protocol_path, "future-protocol", "future_replay_protocol"))
    manifest["bindings"]["future_replay_protocol"] = "future-protocol"
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)
    output = tmp_path / "phase1a-ready-without-future.json"
    monkeypatch.setattr(sys, "argv", [
        "phase1a_data_contract.py",
        "--package-root", str(package),
        "--output", str(output),
    ])

    assert contract.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "READY_FOR_INDEPENDENT_ACCEPTANCE"
    assert report["gates"]["layer_isolation"]["status"] == "PASS"
    assert report["evidence_limits"] == ["LONGITUDINAL_EVIDENCE_UNAVAILABLE"]
    assert report["meta"]["endpoint_calls"] == 0
    assert report["meta"]["socket_attempts"] == 0


def test_empty_future_replay_without_protocol_is_no_go(package: Path) -> None:
    manifest = _manifest(package)
    manifest["layers"]["future_replay"] = []
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    assert report["status"] == "DATA_NO_GO"
    errors = report["gates"]["layer_isolation"]["errors"]
    assert "missing_or_mismatched_binding" in {item["code"] for item in errors}
    assert report["evidence_limits"] == ["LONGITUDINAL_EVIDENCE_UNAVAILABLE"]


def test_arbitrary_uid_rename_is_rejected(package: Path) -> None:
    manifest = _manifest(package)
    manifest["layers"]["sealed_test"][0]["uid"] = "renamed-to-hide-lineage"
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    errors = report["gates"]["layer_isolation"]["errors"]
    assert report["status"] == "DATA_NO_GO"
    assert "lineage_uid_mismatch" in {item["code"] for item in errors}


def test_transformation_parent_must_exist_and_share_full_lineage(package: Path) -> None:
    manifest = _manifest(package)
    child = manifest["layers"]["proposal_train"]["dev"][0]
    child["transformation_parent_id"] = "sample-train"
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    errors = report["gates"]["layer_isolation"]["errors"]
    assert report["status"] == "DATA_NO_GO"
    assert "transformation_parent_cross_lineage" in {
        item["code"] for item in errors
    }

    manifest = _manifest(package)
    child = manifest["layers"]["proposal_train"]["dev"][0]
    child["transformation_parent_id"] = "missing-parent"
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)

    report = contract.validate_package(package)
    errors = report["gates"]["layer_isolation"]["errors"]
    assert "missing_transformation_parent" in {item["code"] for item in errors}


def test_independence_cluster_can_span_proposal_train_and_dev(package: Path) -> None:
    report = contract.validate_package(package)

    assert report["status"] == "READY_FOR_INDEPENDENT_ACCEPTANCE"
    assert report["gates"]["layer_isolation"]["status"] == "PASS"


def test_independence_cluster_cannot_cross_role_layers_after_uid_rename(package: Path) -> None:
    manifest = _manifest(package)
    train = manifest["layers"]["proposal_train"]["train"][0]
    sealed = manifest["layers"]["sealed_test"][0]
    sealed["independence_cluster"] = train["independence_cluster"]
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    errors = report["gates"]["layer_isolation"]["errors"]
    assert report["status"] == "DATA_NO_GO"
    assert "independence_cluster_cross_role_layer" in {
        item["code"] for item in errors
    }


@pytest.mark.parametrize(
    ("approved_at", "acquire_after"),
    [
        ("2026-10-23T00:00:00Z", "2026-09-23T00:00:00Z"),
        ("2026-09-23T00:00:00Z", "2026-09-23T00:00:00Z"),
    ],
)
def test_future_replay_acquisition_must_be_after_freeze(
    package: Path,
    approved_at: str,
    acquire_after: str,
) -> None:
    manifest = _manifest(package)
    manifest["layers"]["future_replay"] = []
    protocol_path = package / "artifacts" / "future_replay_protocol.json"
    _write_json(protocol_path, {
        "contract_version": "future-replay-acquisition-v1",
        "status": "HASH_BOUND_PROTOCOL",
        "cycle_id": "cycle-2026-09-paper-1",
        "freeze_receipt_sha256": "a" * 64,
        "approved_by": "research-owner",
        "approved_at": approved_at,
        "acquire_after": acquire_after,
        "source_constraints": "new source lineage roots acquired after system freeze",
        "partition_rule": "assign before content inspection; never tune on this cycle",
        "contamination_policy": "never_return_to_current_cycle",
    })
    manifest["artifacts"].append(_artifact(
        protocol_path, "future-protocol", "future_replay_protocol"))
    manifest["bindings"]["future_replay_protocol"] = "future-protocol"
    _refresh_analysis_layer_hash(package, manifest)
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    assert report["status"] == "DATA_NO_GO"
    errors = report["gates"]["layer_isolation"]["errors"]
    assert "future_acquisition_not_after_freeze" in {
        item["code"] for item in errors
    }


def test_non_q3_label_is_rejected(package: Path) -> None:
    manifest = _manifest(package)
    artifact = next(item for item in manifest["artifacts"] if item["id"] == "labels")
    path = package / artifact["path"]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[0]["quality_grade"] = "Q1"
    _write_jsonl(path, rows)
    artifact.update(_artifact(path, "labels", "label_ledger"))
    _save_manifest(package, manifest)

    report = contract.validate_package(package)

    errors = report["gates"]["independent_correctness"]["errors"]
    assert report["status"] == "DATA_NO_GO"
    assert "label_not_q3" in {item["code"] for item in errors}
