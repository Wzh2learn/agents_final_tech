#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


RESULT_SCHEMA = "harness_rsi_r_evaluator_result_v1"
DIRECTIONS = {"R"}
DECISIONS = {"ALLOW_WITHIN_SCOPE", "BLOCK", "REVIEW_REQUIRED"}
EXPECTED_CATEGORIES = DECISIONS
HASH_DOMAINS = {"sha256_file", "git_blob_id"}
DIMENSIONS = ("execution_integrity", "measurement_validity", "claim_boundary")
STATUS_RANK = {"FAIL": 4, "REVIEW_REQUIRED": 3, "PASS": 2, "NOT_EVALUATED": 1}
FAMILIES = (
    "真实调用边界",
    "证据身份",
    "完整性与预算",
    "数据与统计",
    "测量对象",
    "交付与权限",
)
ARTIFACT_LEVELS = {
    "synthetic_challenge",
    "real_incident",
    "control_exemplar",
    "unverified_inference",
}
CONTROL_CLASSES = {"BLOCK_SIGNATURE", "LEGAL_ALLOW", "FAIL_CLOSED", "REVIEW_SIGNATURE"}
SOURCE_ORIGINS = {"synthetic_challenge", "t1_v3_accepted_case_set"}
T1_ALLOW_PREFIXES = (
    "research/harness_rsi_v1/runs/T1/20261014T141004Z_2647a7e1/",
    "research/harness_rsi_v1/reviews/T1I-03/",
)
LEGAL_ASSERTIONS = {
    "REAL_INTERFACE_CONTRACT_VERIFIED",
    "HASH_DOMAINS_EXPLICIT_AND_PINNED",
    "FAILURES_COUNTED_AND_RECORDS_PRESERVED",
    "FROZEN_SPLIT_AND_EXCLUSION_APPLIED",
    "DOWNSTREAM_MEASUREMENT_RECOMPUTED",
    "NEGATIVE_RESULT_STOPPED_AND_PENDING_REVIEW",
}
DEFECT_ASSERTIONS = {
    "NON_JSON_NOT_PERSISTED": "execution_integrity",
    "STRUCTURED_OUTPUT_ENFORCEMENT_MISSING": "execution_integrity",
    "IMPORT_REGISTRATION_MISSING": "execution_integrity",
    "CALL_ARGUMENT_ORDER_ERROR": "execution_integrity",
    "RAW_NORMALIZED_MIXED": "execution_integrity",
    "STALE_RECEIPT_CURRENT_CODE": "execution_integrity",
    "MANIFEST_NOT_REPINNED": "execution_integrity",
    "REQUEST_BUDGET_EXCEEDED": "execution_integrity",
    "RAW_RECORD_OVERWRITTEN": "execution_integrity",
    "EVIDENCE_SILENTLY_EXCLUDED": "execution_integrity",
    "SPLIT_LEAKAGE": "measurement_validity",
    "DENOMINATOR_DRIFT": "measurement_validity",
    "SILENT_EXCLUSION": "measurement_validity",
    "DOWNSTREAM_MEASUREMENT_NOT_RECOMPUTED": "measurement_validity",
    "REVIEW_BRIEF_NOT_INJECTED": "claim_boundary",
    "PARTIAL_PASS_ELEVATED": "claim_boundary",
    "AUDIT_SOURCE_MISSING": "claim_boundary",
    "STOP_IGNORED": "claim_boundary",
}
REVIEW_ASSERTIONS = {
    "HASH_DOMAIN_DRIFT_REVIEWED": ("execution_integrity", "claim_boundary"),
    "ENGINEERING_FAILURE_PENDING_SCIENCE": (
        "execution_integrity",
        "measurement_validity",
        "claim_boundary",
    ),
    "USAGE_METERING_UNRESOLVED": ("execution_integrity",),
    "PROXY_NOT_REAL_OBJECT": ("measurement_validity", "claim_boundary"),
    "SCIENTIFIC_STATUS_WORDING_REVIEW": ("claim_boundary",),
}
ASSERTION_FAMILY = {
    "REAL_INTERFACE_CONTRACT_VERIFIED": "真实调用边界",
    "NON_JSON_NOT_PERSISTED": "真实调用边界",
    "STRUCTURED_OUTPUT_ENFORCEMENT_MISSING": "真实调用边界",
    "IMPORT_REGISTRATION_MISSING": "真实调用边界",
    "CALL_ARGUMENT_ORDER_ERROR": "真实调用边界",
    "HASH_DOMAINS_EXPLICIT_AND_PINNED": "证据身份",
    "RAW_NORMALIZED_MIXED": "证据身份",
    "STALE_RECEIPT_CURRENT_CODE": "证据身份",
    "MANIFEST_NOT_REPINNED": "证据身份",
    "HASH_DOMAIN_DRIFT_REVIEWED": "证据身份",
    "FAILURES_COUNTED_AND_RECORDS_PRESERVED": "完整性与预算",
    "REQUEST_BUDGET_EXCEEDED": "完整性与预算",
    "RAW_RECORD_OVERWRITTEN": "完整性与预算",
    "EVIDENCE_SILENTLY_EXCLUDED": "完整性与预算",
    "ENGINEERING_FAILURE_PENDING_SCIENCE": "完整性与预算",
    "USAGE_METERING_UNRESOLVED": "完整性与预算",
    "FROZEN_SPLIT_AND_EXCLUSION_APPLIED": "数据与统计",
    "SPLIT_LEAKAGE": "数据与统计",
    "DENOMINATOR_DRIFT": "数据与统计",
    "SILENT_EXCLUSION": "数据与统计",
    "DOWNSTREAM_MEASUREMENT_RECOMPUTED": "测量对象",
    "DOWNSTREAM_MEASUREMENT_NOT_RECOMPUTED": "测量对象",
    "PROXY_NOT_REAL_OBJECT": "测量对象",
    "NEGATIVE_RESULT_STOPPED_AND_PENDING_REVIEW": "交付与权限",
    "REVIEW_BRIEF_NOT_INJECTED": "交付与权限",
    "PARTIAL_PASS_ELEVATED": "交付与权限",
    "AUDIT_SOURCE_MISSING": "交付与权限",
    "STOP_IGNORED": "交付与权限",
    "SCIENTIFIC_STATUS_WORDING_REVIEW": "交付与权限",
}


class FailClosed(Exception):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


def find_repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("repository root not found")


def resolve_case_path(path: str, base: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        raise FailClosed("FC_PATH_OUTSIDE_ALLOWLIST", "absolute paths are forbidden")
    return (base / candidate).resolve()


def ensure_within(path: Path, root: Path) -> None:
    path.relative_to(root)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_id(repository_root: Path, relative_path: str) -> str:
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative_path],
        cwd=repository_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if tracked.returncode != 0:
        raise FailClosed(
            "FC_HASH_BINDING_MISMATCH",
            f"tracked repository evidence not found at HEAD: {relative_path}",
        )
    result = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative_path}"],
        cwd=repository_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise FailClosed(
            "FC_HASH_BINDING_MISMATCH",
            f"cannot resolve canonical HEAD blob id: {relative_path}",
        )
    return result.stdout.strip()


def verify_hash(
    item: dict[str, Any],
    path: Path,
    repository_root: Path,
    repository_relative: str | None,
) -> None:
    domain = item.get("hash_domain")
    declared = item.get("sha256")
    if domain not in HASH_DOMAINS:
        raise FailClosed("FC_UNSUPPORTED_HASH_DOMAIN", f"unsupported hash domain: {domain!r}")
    if not isinstance(declared, str) or not declared:
        raise FailClosed("FC_MISSING_REQUIRED_FIELD", "sha256 must be a non-empty string")
    if not path.is_file():
        raise FailClosed("FC_HASH_BINDING_MISMATCH", f"artifact is not a regular file: {item.get('path')}")
    if domain == "sha256_file":
        actual = sha256_file(path)
    else:
        if repository_relative is None:
            raise FailClosed("FC_HASH_BINDING_MISMATCH", "git evidence has no repository-relative path")
        actual = git_blob_id(repository_root, repository_relative)
    if actual != declared:
        raise FailClosed(
            "FC_HASH_BINDING_MISMATCH",
            f"declared hash does not match current canonical value for {item.get('path')}",
        )


def validate_required(bundle: dict[str, Any]) -> None:
    required = (
        "schema",
        "bundle_id",
        "direction",
        "case_kind",
        "failure_family",
        "expected_category",
        "candidate_artifact",
        "independent_evidence",
        "candidate_writable_paths",
        "source",
    )
    missing = [field for field in required if field not in bundle]
    if missing:
        raise FailClosed("FC_MISSING_REQUIRED_FIELD", f"missing required fields: {', '.join(missing)}")
    if bundle.get("direction") not in DIRECTIONS:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "direction must be R")
    if bundle.get("failure_family") not in FAMILIES:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "unknown failure family")
    if bundle.get("expected_category") not in EXPECTED_CATEGORIES:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "invalid frozen expected_category")
    if not isinstance(bundle.get("bundle_id"), str) or not bundle["bundle_id"]:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "bundle_id must be non-empty")
    case_kind = bundle.get("case_kind")
    if not isinstance(case_kind, dict):
        raise FailClosed("FC_MISSING_REQUIRED_FIELD", "case_kind must be an object")
    if case_kind.get("artifact_level") not in ARTIFACT_LEVELS:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "invalid artifact_level")
    if case_kind.get("control_class") not in CONTROL_CLASSES:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "invalid control_class")
    source = bundle.get("source")
    if not isinstance(source, dict) or source.get("origin") not in SOURCE_ORIGINS:
        raise FailClosed("FC_INVALID_ENUM_VALUE", "invalid source origin")
    if not isinstance(source.get("case_reference"), str) or not source["case_reference"]:
        raise FailClosed("FC_MISSING_REQUIRED_FIELD", "source.case_reference must be non-empty")


def validate_path(
    item: dict[str, Any],
    path_base: Path,
    repository_root: Path,
    source_origin: str,
) -> tuple[Path, str | None]:
    relative_path = item.get("path")
    if not isinstance(relative_path, str) or not relative_path:
        raise FailClosed("FC_MISSING_REQUIRED_FIELD", "path must be a non-empty string")
    normalized = Path(relative_path).as_posix()
    if ".." in Path(relative_path).parts:
        raise FailClosed("FC_PATH_OUTSIDE_ALLOWLIST", "parent traversal is forbidden")
    if source_origin == "synthetic_challenge":
        if not normalized.startswith("artifacts/"):
            raise FailClosed("FC_PATH_OUTSIDE_ALLOWLIST", "synthetic path is outside artifacts/")
        resolved = resolve_case_path(relative_path, path_base)
        fixture_root = (path_base / "artifacts").resolve()
        ensure_within(resolved, fixture_root)
        return resolved, None
    if not normalized.startswith(T1_ALLOW_PREFIXES):
        raise FailClosed("FC_PATH_OUTSIDE_ALLOWLIST", "T1 path is outside the accepted T1 allowlist")
    resolved = (repository_root / normalized).resolve()
    allowed_roots = tuple((repository_root / prefix).resolve() for prefix in T1_ALLOW_PREFIXES)
    if not any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots):
        raise FailClosed("FC_PATH_OUTSIDE_ALLOWLIST", "T1 path escaped the allowlist")
    return resolved, normalized


def combine_status(current: str, new_status: str) -> str:
    if STATUS_RANK[new_status] > STATUS_RANK[current]:
        return new_status
    return current


def apply_assertions(
    bundle: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    statuses = {dimension: "NOT_EVALUATED" for dimension in DIMENSIONS}
    reasons: list[dict[str, Any]] = []
    family = bundle["failure_family"]
    for record in evidence:
        assertions = record.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            raise FailClosed("FC_EMPTY_EVIDENCE_SET", f"empty assertions for {record.get('evidence_id')}")
        for assertion in assertions:
            if assertion not in ASSERTION_FAMILY:
                raise FailClosed("FC_UNKNOWN_ASSERTION_SIGNATURE", f"unknown assertion: {assertion}")
            if ASSERTION_FAMILY[assertion] != family:
                raise FailClosed(
                    "FC_SIGNATURE_FAMILY_MISMATCH",
                    f"assertion {assertion} is not valid for family {family}",
                )
            if assertion in LEGAL_ASSERTIONS:
                for dimension in DIMENSIONS:
                    statuses[dimension] = combine_status(statuses[dimension], "PASS")
            elif assertion in DEFECT_ASSERTIONS:
                dimension = DEFECT_ASSERTIONS[assertion]
                statuses[dimension] = combine_status(statuses[dimension], "FAIL")
            elif assertion in REVIEW_ASSERTIONS:
                for dimension in REVIEW_ASSERTIONS[assertion]:
                    statuses[dimension] = combine_status(statuses[dimension], "REVIEW_REQUIRED")
            reasons.append(
                {
                    "evidence_id": record.get("evidence_id"),
                    "assertion": assertion,
                    "family": family,
                }
            )
    return statuses, reasons


def decision_from_statuses(statuses: dict[str, str]) -> str:
    if any(statuses[dimension] == "FAIL" for dimension in DIMENSIONS):
        return "BLOCK"
    if any(statuses[dimension] != "PASS" for dimension in DIMENSIONS):
        return "REVIEW_REQUIRED"
    return "ALLOW_WITHIN_SCOPE"


def evaluate_bundle(bundle: dict[str, Any], case_path: Path) -> dict[str, Any]:
    try:
        if not isinstance(bundle, dict):
            raise FailClosed("FC_INPUT_NOT_JSON_OBJECT", "case bundle must be a JSON object")
        validate_required(bundle)
        source_origin = bundle["source"]["origin"]
        candidate_artifact = bundle["candidate_artifact"]
        if not isinstance(candidate_artifact, dict):
            raise FailClosed("FC_MISSING_REQUIRED_FIELD", "candidate_artifact must be an object")
        if bundle["candidate_writable_paths"] != [candidate_artifact.get("path")]:
            raise FailClosed(
                "FC_CANDIDATE_OWNERSHIP_VIOLATION",
                "candidate_writable_paths must contain exactly the candidate artifact path",
            )
        evidence = bundle["independent_evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise FailClosed("FC_EMPTY_EVIDENCE_SET", "independent_evidence must be a non-empty array")
        repository_root = find_repository_root()
        path_base = case_path.resolve().parent
        candidate_path, candidate_repo_path = validate_path(
            candidate_artifact,
            path_base,
            repository_root,
            source_origin,
        )
        verify_hash(candidate_artifact, candidate_path, repository_root, candidate_repo_path)
        required_evidence_fields = {
            "evidence_id",
            "path",
            "hash_domain",
            "sha256",
            "assertions",
            "provenance",
        }
        for record in evidence:
            if not isinstance(record, dict):
                raise FailClosed("FC_MISSING_REQUIRED_FIELD", "evidence records must be objects")
            missing = sorted(required_evidence_fields - set(record))
            if missing:
                raise FailClosed(
                    "FC_MISSING_REQUIRED_FIELD",
                    f"evidence missing fields: {', '.join(missing)}",
                )
            if record.get("provenance") not in {"synthetic_challenge", "accepted_t1_v3"}:
                raise FailClosed("FC_CANDIDATE_OWNERSHIP_VIOLATION", "untrusted evidence provenance")
            evidence_path, evidence_repo_path = validate_path(
                record,
                path_base,
                repository_root,
                source_origin,
            )
            verify_hash(record, evidence_path, repository_root, evidence_repo_path)
        statuses, reasons = apply_assertions(bundle, evidence)
        decision = decision_from_statuses(statuses)
        return {
            "schema": RESULT_SCHEMA,
            "bundle_id": bundle["bundle_id"],
            "direction": "R",
            "decision": decision,
            "dimensions": statuses,
            "reasons": reasons,
            "fail_closed_code": None,
            "validated_evidence_count": len(evidence),
            "candidate_artifact_content_policy": "hash_only_no_candidate_scoring_code_or_labels_read",
            "expected_category_for_qualification_only": bundle["expected_category"],
        }
    except FailClosed as error:
        bundle_id = bundle.get("bundle_id", "UNRESOLVED") if isinstance(bundle, dict) else "UNRESOLVED"
        return {
            "schema": RESULT_SCHEMA,
            "bundle_id": bundle_id,
            "direction": "R",
            "decision": "REVIEW_REQUIRED",
            "dimensions": {dimension: "NOT_EVALUATED" for dimension in DIMENSIONS},
            "reasons": [{"fail_closed_reason": error.reason}],
            "fail_closed_code": error.code,
            "validated_evidence_count": 0,
            "candidate_artifact_content_policy": "hash_only_no_candidate_scoring_code_or_labels_read",
            "expected_category_for_qualification_only": bundle.get("expected_category", "UNRESOLVED"),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    case_path = Path(args.case)
    try:
        with case_path.open("r", encoding="utf-8") as handle:
            bundle = json.load(handle)
    except (OSError, json.JSONDecodeError):
        result = {
            "schema": RESULT_SCHEMA,
            "bundle_id": "UNRESOLVED",
            "direction": "R",
            "decision": "REVIEW_REQUIRED",
            "dimensions": {dimension: "NOT_EVALUATED" for dimension in DIMENSIONS},
            "reasons": [{"fail_closed_reason": "case bundle is not readable valid JSON"}],
            "fail_closed_code": "FC_INPUT_NOT_JSON_OBJECT",
            "validated_evidence_count": 0,
            "candidate_artifact_content_policy": "hash_only_no_candidate_scoring_code_or_labels_read",
            "expected_category_for_qualification_only": "UNRESOLVED",
        }
        serialized = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.out == "-":
            sys.stdout.write(serialized)
        else:
            Path(args.out).write_text(serialized, encoding="utf-8")
        return 3
    result = evaluate_bundle(bundle, case_path)
    serialized = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out == "-":
        sys.stdout.write(serialized)
    else:
        Path(args.out).write_text(serialized, encoding="utf-8")
    return 3 if result["fail_closed_code"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
