"""Offline precheck for a private Phase 1a data-supplement package.

The checker turns the repository's DATA_NO_GO supplement list into a deterministic
contract.  It never releases data for training: a fully passing package is only
``READY_FOR_INDEPENDENT_ACCEPTANCE`` and still needs human/GB10 acceptance.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import socket
from typing import Any


REPO = Path(__file__).resolve().parents[1]
CONTRACT_VERSION = "phase1a-data-package-v1"
READY = "READY_FOR_INDEPENDENT_ACCEPTANCE"
NO_GO = "DATA_NO_GO"

REQUIRED_ROLES = {
    "source_tables",
    "schema",
    "injection_map",
    "label_ledger",
    "licence_record",
    "confidence_manifest",
    "analysis_plan",
    "parser_contract_receipt",
}
REQUIRED_BINDINGS = {
    "label_ledger": ("independent_correctness", "label_ledger"),
    "licence_record": ("licence_permission", "licence_record"),
    "confidence_manifest": ("confidence_provenance", "confidence_manifest"),
    "analysis_plan": ("analysis_plan", "analysis_plan"),
    "parser_contract_receipt": ("parser_contract", "parser_contract_receipt"),
}
PARTITIONS = (
    "proposal_train.train",
    "proposal_train.dev",
    "gate_validation",
    "sealed_test",
    "future_replay",
)
VALID_ACTIONS = {"map_to", "skip", "hold"}
REQUIRED_USES = {"training", "tuning", "evaluation", "rule_acceptance"}
REQUIRED_PRIMARY_METRICS = {"action_macro_f1", "harmful_action_rate"}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")


def _stable_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_object(value: object) -> str:
    return _sha256_bytes(_stable_json(value).encode("utf-8"))


def _strict_json(raw: bytes) -> Any:
    def invalid(value: str) -> None:
        raise ValueError(f"invalid JSON constant: {value}")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(raw, parse_constant=invalid, object_pairs_hook=unique)


def _iso8601(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


@contextmanager
def offline_guard():
    """Block common socket entry points and expose the attempted-call counter."""

    attempts = [0]

    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        attempts[0] += 1
        raise RuntimeError("network access forbidden during Phase 1a package precheck")

    targets = [
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "sendto"),
        (socket, "create_connection"),
        (socket, "getaddrinfo"),
    ]
    originals = [(obj, name, getattr(obj, name)) for obj, name in targets]
    try:
        for obj, name in targets:
            setattr(obj, name, forbidden)
        yield attempts
    finally:
        for obj, name, original in originals:
            setattr(obj, name, original)


def _new_gates() -> dict[str, dict[str, object]]:
    return {
        name: {"status": "PASS", "errors": []}
        for name in (
            "artifact_integrity",
            "layer_isolation",
            "independent_correctness",
            "licence_permission",
            "confidence_provenance",
            "analysis_plan",
            "parser_contract",
        )
    }


def _fail(
    gates: dict[str, dict[str, object]],
    gate: str,
    code: str,
    **details: object,
) -> None:
    gates[gate]["status"] = "FAIL"
    error = {"code": code}
    error.update(details)
    errors = gates[gate]["errors"]
    assert isinstance(errors, list)
    if error not in errors:
        errors.append(error)


def _base_report(gates: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        "status": NO_GO,
        "meta": {
            "phase": "precheck",
            "endpoint_calls": 0,
            "socket_attempts": 0,
            "contract_version": CONTRACT_VERSION,
        },
        "gates": gates,
        "counts": {"artifacts": 0, "samples": 0, "uids": 0, "labels": 0},
        "hashes": {},
        "manual_review_required": [
            "confirm licence authority and permitted-use record authenticity",
            "confirm reviewer identity, independence, and adjudication provenance",
            "confirm analysis-plan approval and parser-receipt execution provenance",
        ],
        "release_boundary": (
            "Mechanical PASS is not DATA_GO, training permission, a paper result, "
            "or GB10 independent acceptance."
        ),
    }


def _resolve_inside(root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    return resolved if resolved.is_relative_to(root) else None


def _load_bound_json(
    artifact_id: str | None,
    expected_role: str,
    artifact_index: dict[str, dict[str, object]],
    artifact_bytes: dict[str, bytes],
    gates: dict[str, dict[str, object]],
    gate: str,
) -> dict[str, object] | None:
    artifact = artifact_index.get(artifact_id or "")
    if not artifact or artifact.get("role") != expected_role:
        _fail(gates, gate, "missing_or_mismatched_binding")
        return None
    raw = artifact_bytes.get(artifact_id or "")
    if raw is None:
        _fail(gates, gate, "bound_artifact_unavailable")
        return None
    try:
        value = _strict_json(raw)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _fail(gates, gate, "invalid_bound_json")
        return None
    if not isinstance(value, dict):
        _fail(gates, gate, "bound_json_object_required")
        return None
    return value


def _valid_choice(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    action = value.get("action")
    target = value.get("target")
    if action not in VALID_ACTIONS:
        return False
    if action == "map_to":
        return isinstance(target, str) and bool(target)
    return target is None


def _partition_rows(manifest: dict[str, object]) -> dict[str, object]:
    layers = manifest.get("layers")
    if not isinstance(layers, dict):
        return {}
    proposal = layers.get("proposal_train")
    if not isinstance(proposal, dict):
        proposal = {}
    return {
        "proposal_train.train": proposal.get("train"),
        "proposal_train.dev": proposal.get("dev"),
        "gate_validation": layers.get("gate_validation"),
        "sealed_test": layers.get("sealed_test"),
        "future_replay": layers.get("future_replay"),
    }


def _validate_package(package_root: Path, manifest_path: Path) -> dict[str, object]:
    gates = _new_gates()
    report = _base_report(gates)

    if not package_root.is_dir() or not manifest_path.is_file():
        _fail(gates, "artifact_integrity", "missing_package_or_manifest")
        return report
    try:
        manifest_raw = manifest_path.read_bytes()
        manifest = _strict_json(manifest_raw)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _fail(gates, "artifact_integrity", "invalid_manifest_json")
        return report
    if not isinstance(manifest, dict):
        _fail(gates, "artifact_integrity", "manifest_object_required")
        return report

    report["hashes"] = {"manifest_sha256": _sha256_bytes(manifest_raw)}
    if manifest.get("contract_version") != CONTRACT_VERSION:
        _fail(gates, "artifact_integrity", "unsupported_contract_version")
    if not isinstance(manifest.get("package_id"), str) or not manifest["package_id"]:
        _fail(gates, "artifact_integrity", "missing_package_id")

    artifacts = manifest.get("artifacts")
    artifact_index: dict[str, dict[str, object]] = {}
    artifact_bytes: dict[str, bytes] = {}
    actual_hashes: dict[str, str] = {}
    declared_roles: set[str] = set()
    if not isinstance(artifacts, list):
        _fail(gates, "artifact_integrity", "artifact_list_required")
        artifacts = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            _fail(gates, "artifact_integrity", "invalid_artifact_entry", index=index)
            continue
        artifact_id = artifact.get("id")
        role = artifact.get("role")
        if not isinstance(artifact_id, str) or not artifact_id:
            _fail(gates, "artifact_integrity", "invalid_artifact_id", index=index)
            continue
        if artifact_id in artifact_index:
            _fail(gates, "artifact_integrity", "duplicate_artifact_id", artifact_id=artifact_id)
            continue
        artifact_index[artifact_id] = artifact
        if not isinstance(role, str) or not role:
            _fail(gates, "artifact_integrity", "invalid_artifact_role", artifact_id=artifact_id)
        else:
            declared_roles.add(role)

        path = _resolve_inside(package_root, artifact.get("path"))
        if path is None:
            _fail(gates, "artifact_integrity", "unsafe_artifact_path", artifact_id=artifact_id)
            continue
        if not path.is_file():
            _fail(gates, "artifact_integrity", "missing_artifact", artifact_id=artifact_id)
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            _fail(gates, "artifact_integrity", "unreadable_artifact", artifact_id=artifact_id)
            continue
        actual = _sha256_bytes(raw)
        artifact_bytes[artifact_id] = raw
        actual_hashes[artifact_id] = actual
        if not raw:
            _fail(gates, "artifact_integrity", "empty_artifact", artifact_id=artifact_id)
        if artifact.get("bytes") != len(raw):
            _fail(gates, "artifact_integrity", "byte_count_mismatch", artifact_id=artifact_id)
        declared_hash = artifact.get("sha256")
        if not isinstance(declared_hash, str) or not SHA256_RE.fullmatch(declared_hash):
            _fail(gates, "artifact_integrity", "invalid_sha256", artifact_id=artifact_id)
        elif declared_hash != actual:
            _fail(gates, "artifact_integrity", "sha256_mismatch", artifact_id=artifact_id)

    for role in sorted(REQUIRED_ROLES - declared_roles):
        _fail(gates, "artifact_integrity", "missing_required_role", role=role)
    report["counts"]["artifacts"] = len(artifact_index)
    report["hashes"]["artifact_manifest_sha256"] = _sha256_bytes(
        _stable_json(dict(sorted(actual_hashes.items()))).encode("utf-8")
    )

    partitions = _partition_rows(manifest)
    samples: dict[str, tuple[str, str]] = {}
    uid_partitions: dict[str, set[str]] = {}
    partition_counts: dict[str, dict[str, int]] = {}
    for partition in PARTITIONS:
        rows = partitions.get(partition)
        if not isinstance(rows, list) or not rows:
            _fail(gates, "layer_isolation", "missing_or_empty_partition", partition=partition)
            continue
        partition_uids: set[str] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                _fail(gates, "layer_isolation", "invalid_sample_entry", partition=partition, index=index)
                continue
            sample_id, uid = row.get("sample_id"), row.get("uid")
            if not isinstance(sample_id, str) or not sample_id or not isinstance(uid, str) or not uid:
                _fail(gates, "layer_isolation", "invalid_sample_identity", partition=partition, index=index)
                continue
            if sample_id in samples:
                _fail(gates, "layer_isolation", "duplicate_sample_id", partition=partition)
                continue
            samples[sample_id] = (uid, partition)
            partition_uids.add(uid)
            uid_partitions.setdefault(uid, set()).add(partition)
        partition_counts[partition] = {"samples": len(rows), "uids": len(partition_uids)}
    for partitions_for_uid in uid_partitions.values():
        if len(partitions_for_uid) > 1:
            _fail(
                gates,
                "layer_isolation",
                "uid_cross_partition",
                partitions=sorted(partitions_for_uid),
            )
    report["counts"].update({
        "samples": len(samples),
        "uids": len(uid_partitions),
        "partitions": partition_counts,
    })

    bindings = manifest.get("bindings")
    if not isinstance(bindings, dict):
        bindings = {}
    for binding, (gate, expected_role) in REQUIRED_BINDINGS.items():
        artifact = artifact_index.get(bindings.get(binding, ""))
        if not artifact or artifact.get("role") != expected_role:
            _fail(gates, gate, "missing_or_mismatched_binding")

    label_id = bindings.get("label_ledger") if isinstance(bindings.get("label_ledger"), str) else None
    labels_raw = artifact_bytes.get(label_id or "")
    labels: dict[str, dict[str, object]] = {}
    if labels_raw is None:
        _fail(gates, "independent_correctness", "bound_artifact_unavailable")
    else:
        for index, line in enumerate(labels_raw.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = _strict_json(line)
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                _fail(gates, "independent_correctness", "invalid_label_json", line=index)
                continue
            if not isinstance(row, dict):
                _fail(gates, "independent_correctness", "label_object_required", line=index)
                continue
            sample_id = row.get("sample_id")
            if not isinstance(sample_id, str) or not sample_id:
                _fail(gates, "independent_correctness", "invalid_label_sample_id", line=index)
                continue
            if sample_id in labels:
                _fail(gates, "independent_correctness", "duplicate_label", line=index)
                continue
            labels[sample_id] = row
            sample = samples.get(sample_id)
            if sample is None:
                _fail(gates, "independent_correctness", "extra_label", line=index)
                continue
            if row.get("uid") != sample[0] or type(row.get("col")) is not int or row["col"] < 0:
                _fail(gates, "independent_correctness", "label_identity_mismatch", line=index)
            gold = {"action": row.get("gold_action"), "target": row.get("gold_target")}
            if not _valid_choice(gold):
                _fail(gates, "independent_correctness", "invalid_gold_action", line=index)
                continue
            reviewers = row.get("reviewers")
            if not isinstance(reviewers, list):
                reviewers = []
            reviewer_ids = {
                review.get("reviewer_id")
                for review in reviewers
                if isinstance(review, dict) and isinstance(review.get("reviewer_id"), str)
                and review["reviewer_id"]
            }
            if len(reviewer_ids) < 2:
                _fail(
                    gates,
                    "independent_correctness",
                    "insufficient_independent_reviewers",
                    line=index,
                )
                continue
            if any(not _valid_choice(review) for review in reviewers):
                _fail(gates, "independent_correctness", "invalid_reviewer_label", line=index)
                continue
            choices = {(review["action"], review.get("target")) for review in reviewers}
            if len(choices) == 1:
                if next(iter(choices)) != (gold["action"], gold["target"]):
                    _fail(gates, "independent_correctness", "gold_review_mismatch", line=index)
            else:
                adjudication = row.get("adjudication")
                if not isinstance(adjudication, dict):
                    _fail(gates, "independent_correctness", "missing_adjudication", line=index)
                    continue
                adjudicator = adjudication.get("adjudicator_id")
                if (not isinstance(adjudicator, str) or not adjudicator
                        or adjudicator in reviewer_ids or not _valid_choice(adjudication)):
                    _fail(gates, "independent_correctness", "invalid_adjudication", line=index)
                elif (adjudication["action"], adjudication.get("target")) != (
                    gold["action"], gold["target"]
                ):
                    _fail(gates, "independent_correctness", "gold_adjudication_mismatch", line=index)
    for sample_id in sorted(set(samples) - set(labels)):
        del sample_id
        _fail(gates, "independent_correctness", "missing_label")
    report["counts"]["labels"] = len(labels)

    licence = _load_bound_json(
        bindings.get("licence_record") if isinstance(bindings.get("licence_record"), str) else None,
        "licence_record",
        artifact_index,
        artifact_bytes,
        gates,
        "licence_permission",
    )
    if licence is not None:
        if licence.get("status") != "accepted":
            _fail(gates, "licence_permission", "licence_not_accepted")
        if not isinstance(licence.get("accepted_by"), str) or not licence["accepted_by"]:
            _fail(gates, "licence_permission", "missing_acceptance_owner")
        if not _iso8601(licence.get("accepted_at")):
            _fail(gates, "licence_permission", "invalid_acceptance_time")
        uses = licence.get("permitted_uses")
        use_set = set(uses) if isinstance(uses, list) and all(isinstance(x, str) for x in uses) else set()
        for use in sorted(REQUIRED_USES - use_set):
            _fail(gates, "licence_permission", "missing_permitted_use", use=use)
        covered = licence.get("covered_artifact_sha256")
        if not isinstance(covered, dict):
            covered = {}
        licensed_inputs = {
            artifact_id: actual_hashes.get(artifact_id)
            for artifact_id, artifact in artifact_index.items()
            if artifact.get("role") in {
                "source_tables", "schema", "injection_map", "label_ledger"
            }
        }
        for artifact_id, actual_hash in sorted(licensed_inputs.items()):
            if actual_hash is None or covered.get(artifact_id) != actual_hash:
                _fail(
                    gates,
                    "licence_permission",
                    "licence_artifact_hash_mismatch",
                    artifact_id=artifact_id,
                )

    confidence = _load_bound_json(
        bindings.get("confidence_manifest") if isinstance(bindings.get("confidence_manifest"), str) else None,
        "confidence_manifest",
        artifact_index,
        artifact_bytes,
        gates,
        "confidence_provenance",
    )
    if confidence is not None:
        if not isinstance(confidence.get("field"), str) or not confidence["field"]:
            _fail(gates, "confidence_provenance", "missing_confidence_field")
        if not isinstance(confidence.get("source"), str) or not confidence["source"]:
            _fail(gates, "confidence_provenance", "missing_confidence_source")
        if confidence.get("missing_policy") != "unmeasurable":
            _fail(gates, "confidence_provenance", "invalid_missing_policy")
        if confidence.get("gain_collateral_substitution") is not False:
            _fail(gates, "confidence_provenance", "gain_collateral_substitution_forbidden")
        values = confidence.get("allowed_values")
        if (
            not isinstance(values, list)
            or not all(isinstance(value, str) for value in values)
            or set(values) != {"low", "medium", "high"}
        ):
            _fail(gates, "confidence_provenance", "invalid_confidence_vocabulary")

    analysis = _load_bound_json(
        bindings.get("analysis_plan") if isinstance(bindings.get("analysis_plan"), str) else None,
        "analysis_plan",
        artifact_index,
        artifact_bytes,
        gates,
        "analysis_plan",
    )
    if analysis is not None:
        if analysis.get("status") != "approved":
            _fail(gates, "analysis_plan", "analysis_plan_not_approved")
        if not isinstance(analysis.get("approved_by"), str) or not analysis["approved_by"]:
            _fail(gates, "analysis_plan", "missing_analysis_owner")
        if not _iso8601(analysis.get("approved_at")):
            _fail(gates, "analysis_plan", "invalid_analysis_approval_time")
        if analysis.get("cluster_unit") != "uid":
            _fail(gates, "analysis_plan", "invalid_cluster_unit")
        for key in ("alpha", "power"):
            value = analysis.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value < 1:
                _fail(gates, "analysis_plan", f"invalid_{key}")
        margin = analysis.get("noninferiority_margin")
        if type(margin) not in (int, float) or not math.isfinite(margin) or not 0 <= margin < 1:
            _fail(gates, "analysis_plan", "invalid_noninferiority_margin")
        metrics = analysis.get("primary_metrics")
        metric_set = set(metrics) if isinstance(metrics, list) and all(isinstance(x, str) for x in metrics) else set()
        for metric in sorted(REQUIRED_PRIMARY_METRICS - metric_set):
            _fail(gates, "analysis_plan", "missing_primary_metric", metric=metric)
        if analysis.get("layer_manifest_sha256") != _digest_object(manifest.get("layers")):
            _fail(gates, "analysis_plan", "layer_manifest_hash_mismatch")

    receipt = _load_bound_json(
        bindings.get("parser_contract_receipt")
        if isinstance(bindings.get("parser_contract_receipt"), str) else None,
        "parser_contract_receipt",
        artifact_index,
        artifact_bytes,
        gates,
        "parser_contract",
    )
    if receipt is not None:
        if receipt.get("status") != "PASS":
            _fail(gates, "parser_contract", "parser_contract_not_passed")
        if not isinstance(receipt.get("checker"), str) or not receipt["checker"]:
            _fail(gates, "parser_contract", "missing_parser_checker")
        if not isinstance(receipt.get("commit"), str) or not COMMIT_RE.fullmatch(receipt["commit"]):
            _fail(gates, "parser_contract", "invalid_parser_commit")
        if not _iso8601(receipt.get("executed_at")):
            _fail(gates, "parser_contract", "invalid_parser_execution_time")
        receipt_hashes = receipt.get("input_sha256")
        if not isinstance(receipt_hashes, dict):
            receipt_hashes = {}
        required_inputs = {
            artifact_id: actual_hashes.get(artifact_id)
            for artifact_id, artifact in artifact_index.items()
            if artifact.get("role") in {"source_tables", "schema", "injection_map"}
        }
        for artifact_id, actual_hash in sorted(required_inputs.items()):
            if actual_hash is None or receipt_hashes.get(artifact_id) != actual_hash:
                _fail(
                    gates,
                    "parser_contract",
                    "parser_input_hash_mismatch",
                    artifact_id=artifact_id,
                )

    if all(gate["status"] == "PASS" for gate in gates.values()):
        report["status"] = READY
    return report


def validate_package(
    package_root: Path | str,
    manifest_path: Path | str = "phase1a_manifest.json",
) -> dict[str, object]:
    root = Path(package_root).resolve()
    manifest = Path(manifest_path)
    if not manifest.is_absolute():
        manifest = (root / manifest).resolve()
    if not manifest.is_relative_to(root):
        gates = _new_gates()
        report = _base_report(gates)
        _fail(gates, "artifact_integrity", "unsafe_manifest_path")
        return report
    with offline_guard() as attempts:
        report = _validate_package(root, manifest)
        report["meta"]["socket_attempts"] = attempts[0]
        if attempts[0]:
            raise RuntimeError("network attempted during Phase 1a package precheck")
        return report


def _valid_output_path(output: Path, package_root: Path) -> bool:
    output = output.resolve()
    if output.is_relative_to(package_root):
        return False
    if output.is_relative_to(REPO) and not output.is_relative_to(REPO / "data"):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Precheck a private Phase 1a data package without network or training",
    )
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("phase1a_manifest.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.package_root.resolve()
    output = args.output.resolve()
    if output.exists():
        parser.error("output already exists; use a new path")
    if not _valid_output_path(output, root):
        parser.error("output must be outside the package and tracked repository paths")
    report = validate_package(root, args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(_stable_json(report) + "\n")
    summary = {
        "status": report["status"],
        "gates": {name: value["status"] for name, value in report["gates"].items()},
        "counts": report["counts"],
        "manifest_sha256": report["hashes"].get("manifest_sha256"),
        "report_sha256": _sha256_bytes(output.read_bytes()),
        "endpoint_calls": 0,
        "socket_attempts": report["meta"]["socket_attempts"],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == READY else 2


if __name__ == "__main__":
    raise SystemExit(main())
