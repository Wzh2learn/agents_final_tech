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

    _write_jsonl(artifacts / "source_tables.jsonl", [
        {"uid": uid, "headers": ["alias", "amount"]}
        for uid in ("train-1", "dev-1", "gate-1", "test-1", "future-1")
    ])
    _write_json(artifacts / "schema.json", {
        "canonical_fields": ["Revenue", "Amount"],
    })
    _write_json(artifacts / "injection_map.json", {
        uid: [{"col": 0, "canonical": "Revenue", "family": "alias_variant"}]
        for uid in ("train-1", "dev-1", "gate-1", "test-1", "future-1")
    })

    samples = [
        ("sample-train", "train-1", "map_to", "Revenue"),
        ("sample-dev", "dev-1", "skip", None),
        ("sample-gate", "gate-1", "hold", None),
        ("sample-test", "test-1", "map_to", "Amount"),
        ("sample-future", "future-1", "skip", None),
    ]
    _write_jsonl(artifacts / "labels.jsonl", [
        {
            "sample_id": sample_id,
            "uid": uid,
            "col": 0,
            "gold_action": action,
            "gold_target": target,
            "reviewers": [
                {"reviewer_id": "reviewer-a", "action": action, "target": target},
                {"reviewer_id": "reviewer-b", "action": action, "target": target},
            ],
            "adjudication": None,
        }
        for sample_id, uid, action, target in samples
    ])
    def sample(sample_id: str, uid: str) -> dict[str, str]:
        return {"sample_id": sample_id, "uid": uid}

    layers = {
        "proposal_train": {
            "train": [sample("sample-train", "train-1")],
            "dev": [sample("sample-dev", "dev-1")],
        },
        "gate_validation": [sample("sample-gate", "gate-1")],
        "sealed_test": [sample("sample-test", "test-1")],
        "future_replay": [sample("sample-future", "future-1")],
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
    _write_json(artifacts / "analysis_plan.json", {
        "status": "approved",
        "approved_by": "research-owner",
        "approved_at": "2026-09-23T00:00:00Z",
        "cluster_unit": "uid",
        "alpha": 0.05,
        "power": 0.8,
        "noninferiority_margin": 0.02,
        "primary_metrics": ["action_macro_f1", "harmful_action_rate"],
        "layer_manifest_sha256": _stable_hash(layers),
    })

    artifact_specs = [
        ("source-tables", "source_tables", artifacts / "source_tables.jsonl"),
        ("schema", "schema", artifacts / "schema.json"),
        ("injection-map", "injection_map", artifacts / "injection_map.json"),
        ("labels", "label_ledger", artifacts / "labels.jsonl"),
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
        "package_id": "fixture-package-v1",
        "artifacts": manifest_artifacts,
        "layers": layers,
        "bindings": {
            "label_ledger": "labels",
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
    assert first["status"] != "DATA_GO"
    assert "not DATA_GO" in first["release_boundary"]


@pytest.mark.parametrize(
    ("mutation", "gate", "error"),
    [
        ("hash", "artifact_integrity", "sha256_mismatch"),
        ("overlap", "layer_isolation", "uid_cross_partition"),
        ("missing_label", "independent_correctness", "missing_label"),
        ("one_reviewer", "independent_correctness", "insufficient_independent_reviewers"),
        ("licence", "licence_permission", "missing_permitted_use"),
        ("licence_hash", "licence_permission", "licence_artifact_hash_mismatch"),
        ("confidence", "confidence_provenance", "invalid_missing_policy"),
        ("analysis", "analysis_plan", "analysis_plan_not_approved"),
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
    elif mutation == "overlap":
        manifest["layers"]["sealed_test"][0]["uid"] = "train-1"
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
    elif mutation in {"analysis", "analysis_layers"}:
        path = package / artifacts["analysis-plan"]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "analysis":
            value["status"] = "draft"
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
    _save_manifest(package, manifest)

    report = contract.validate_package(package)
    errors = report["gates"]["independent_correctness"]["errors"]
    assert report["status"] == "DATA_NO_GO"
    assert "missing_adjudication" in {item["code"] for item in errors}


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
        '{"contract_version":"phase1a-data-package-v1",',
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


def test_cli_returns_two_and_writes_report_for_no_go_package(
    package: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(package)
    manifest["layers"]["future_replay"] = []
    _save_manifest(package, manifest)
    output = tmp_path / "phase1a-no-go.json"
    monkeypatch.setattr(sys, "argv", [
        "phase1a_data_contract.py",
        "--package-root", str(package),
        "--output", str(output),
    ])

    assert contract.main() == 2
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "DATA_NO_GO"
    assert report["gates"]["layer_isolation"]["status"] == "FAIL"
    assert report["meta"]["endpoint_calls"] == 0
    assert report["meta"]["socket_attempts"] == 0
