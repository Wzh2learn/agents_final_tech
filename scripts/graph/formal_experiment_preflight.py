#!/usr/bin/env python3
"""Fail-closed formal experiment preflight validator."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_METADATA = ("split_role", "stage", "cluster_id", "report_cluster")
REQUIRED_POPULATION_FIELDS = (
    "candidate_injections",
    "retained_injections",
    "samples",
    "groups",
)
REQUIRED_QUALIFICATION_FIELDS = (
    "runtime_bindings_pass",
    "runtime_bindings_total",
    "evaluation_trace_rows_match",
    "evaluation_trace_rows_total",
    "report_clusters",
    "missing_metadata",
    "silent_defaults",
    "empty_set_bypasses",
    "identity_drift",
    "split_drift",
    "scientific_outputs",
    "previous_invalid_run_drift",
)
REQUIRED_RUNTIME_METADATA_POLICY = {
    "missing": "RAISE",
    "null": "RAISE",
    "empty": "RAISE",
    "silent_defaults": "FORBIDDEN",
}
REQUIRED_PREFLIGHT_STATUS = "END_TO_END_PREFLIGHT_PASS_CANDIDATE_PENDING_LOOP_C"
REQUIRED_VERIFICATION_LEVEL = "END_TO_END_PREFLIGHT_PASS"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(report: dict[str, Any], code: str, message: str) -> None:
    report["status"] = "FAIL"
    report.setdefault("failures", []).append({"code": code, "message": message})


def resolve_path(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, (str, Path)) or not str(raw):
        return None
    path = Path(raw)
    return path if path.is_absolute() else root / path


def get_path(
    root: Path,
    manifest: dict[str, Any],
    field: str,
    report: dict[str, Any],
) -> Path | None:
    if field not in manifest:
        fail(report, "MANIFEST_PATH_MISSING", field)
        return None
    path = resolve_path(root, manifest[field])
    if path is None:
        fail(report, "MANIFEST_PATH_INVALID", field)
        return None
    return path


def check_hash_bindings(
    root: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> None:
    required_raw = manifest.get("required_authority_paths")
    if not isinstance(required_raw, list) or not required_raw:
        fail(report, "REQUIRED_AUTHORITY_PATHS_EMPTY", "required_authority_paths must be nonempty")
        required: set[Path] = set()
    else:
        required_paths = [resolve_path(root, item) for item in required_raw]
        if any(path is None for path in required_paths):
            fail(report, "REQUIRED_AUTHORITY_PATH_INVALID", repr(required_raw))
            required = set()
        else:
            required = {path.resolve() for path in required_paths if path is not None}

    bindings = manifest.get("hash_bindings")
    if not isinstance(bindings, list):
        fail(report, "HASH_BINDINGS_MISSING", "hash_bindings must be a list")
        return
    if not bindings:
        fail(report, "HASH_BINDINGS_EMPTY", "hash_bindings must not be empty")
        report["hash_bindings_checked"] = 0
        fail(report, "ZERO_CHECKED_BINDINGS", "zero hash bindings were verified")
        return

    checked = 0
    bound_paths: set[Path] = set()
    for item in bindings:
        if not isinstance(item, dict) or not {"path", "sha256"} <= item.keys():
            fail(report, "HASH_BINDING_INVALID", f"invalid binding: {item!r}")
            continue
        path = resolve_path(root, item["path"])
        expected_hash = item["sha256"]
        if path is None or not isinstance(expected_hash, str) or not expected_hash:
            fail(report, "HASH_BINDING_INVALID", f"invalid binding: {item!r}")
            continue
        bound_paths.add(path.resolve())
        if not path.is_file():
            fail(report, "AUTHORITY_FILE_MISSING", str(path))
            continue
        actual = sha256_file(path)
        if actual != expected_hash:
            fail(report, "AUTHORITY_HASH_MISMATCH", f"{path}: {actual} != {expected_hash}")
            continue
        checked += 1

    report["hash_bindings_checked"] = checked
    report["required_authority_paths_checked"] = len(required & bound_paths)
    for path in sorted(required - bound_paths):
        fail(report, "REQUIRED_AUTHORITY_ARTIFACT_MISSING", str(path))
    if checked == 0:
        fail(report, "ZERO_CHECKED_BINDINGS", "zero hash bindings were verified")
    if checked != len(bindings):
        fail(
            report,
            "HASH_BINDINGS_NOT_FULLY_CHECKED",
            f"checked={checked} total={len(bindings)}",
        )


def check_runtime_contract(
    root: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> None:
    required_raw = manifest.get("required_metadata")
    if not isinstance(required_raw, list) or tuple(required_raw) != REQUIRED_METADATA:
        fail(report, "METADATA_CONTRACT_CHANGED", f"required_metadata={required_raw!r}")
    policy = manifest.get("runtime_metadata_policy")
    if not isinstance(policy, dict):
        fail(report, "MISSING_RUNTIME_METADATA_POLICY", "manifest runtime_metadata_policy missing")
    elif policy != REQUIRED_RUNTIME_METADATA_POLICY:
        fail(report, "RUNTIME_METADATA_POLICY_MISMATCH", repr(policy))

    interface_path = get_path(root, manifest, "runtime_interface_json", report)
    if interface_path is None:
        return
    if not interface_path.is_file():
        fail(report, "RUNTIME_INTERFACE_MISSING", str(interface_path))
        return
    interface = load_json(interface_path)
    metadata = interface.get("runtime_metadata")
    if not isinstance(metadata, dict):
        fail(report, "RUNTIME_METADATA_MISSING", "runtime_metadata object missing")
        return
    field_specs = metadata["fields"] if "fields" in metadata else metadata
    if not isinstance(field_specs, dict):
        fail(report, "REQUIRED_METADATA_SPEC_INVALID", "runtime metadata fields invalid")
        return

    for field in REQUIRED_METADATA:
        if field not in field_specs:
            fail(report, "REQUIRED_METADATA_MISSING", field)
            continue
        spec = field_specs[field]
        if not isinstance(spec, dict):
            fail(report, "REQUIRED_METADATA_SPEC_INVALID", field)
            continue
        if spec.get("required") is not True:
            fail(report, "REQUIRED_METADATA_NOT_REQUIRED", field)
        if spec.get("null_allowed") is not False:
            fail(report, "REQUIRED_METADATA_NULL_POLICY", field)
        if spec.get("empty_allowed") is not False:
            fail(report, "REQUIRED_METADATA_EMPTY_POLICY", field)
        if not isinstance(spec.get("type"), str) or "nonempty" not in spec["type"]:
            fail(report, "REQUIRED_METADATA_TYPE_POLICY", field)

    top_missing_policy = interface.get("missing_metadata_policy")
    nested_missing_policy = metadata.get("missing_value_behavior")
    policy_present = (
        top_missing_policy in {"RAISE", "FAIL_CLOSED"}
        or (
            isinstance(nested_missing_policy, str)
            and ("fail-closed" in nested_missing_policy.lower()
                 or "raise" in nested_missing_policy.lower())
        )
    )
    top_silent_policy = interface.get("silent_defaults")
    nested_silent_policy = metadata.get("silent_default_policy")
    silent_policy_present = (
        top_silent_policy == []
        or (
            isinstance(nested_silent_policy, str)
            and "forbidden" in nested_silent_policy.lower()
        )
    )
    if not policy_present or not silent_policy_present:
        fail(report, "MISSING_RUNTIME_METADATA_POLICY", "interface runtime policy missing")
    if top_silent_policy not in (None, []):
        fail(report, "SILENT_DEFAULTS_PRESENT", repr(top_silent_policy))

    source_path = get_path(root, manifest, "runtime_interface_source", report)
    if source_path is None:
        return
    if not source_path.is_file():
        fail(report, "RUNTIME_SOURCE_MISSING", str(source_path))
        return
    source = source_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        fail(report, "RUNTIME_SOURCE_SYNTAX_ERROR", str(exc))
        return
    required_fields = set(REQUIRED_METADATA)

    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp):
            for operand in node.values:
                if (
                    isinstance(operand, ast.Call)
                    and isinstance(operand.func, ast.Attribute)
                    and operand.func.attr == "get"
                    and len(operand.args) == 1
                    and isinstance(operand.args[0], ast.Constant)
                    and operand.args[0].value in required_fields
                ):
                    fail(
                        report,
                        "SILENT_DEFAULT_SOURCE",
                        f"{operand.args[0].value} uses an or-fallback",
                    )
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "get":
            field = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
            has_positional_default = len(node.args) > 1
            has_keyword_default = any(keyword.arg == "default" for keyword in node.keywords)
            if field in required_fields and (has_positional_default or has_keyword_default):
                fail(report, "SILENT_DEFAULT_SOURCE", f"{field} uses a get default")
        elif node.func.attr == "setdefault":
            field = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
            if field in required_fields and len(node.args) >= 2:
                fail(report, "SILENT_DEFAULT_SOURCE", f"{field} uses setdefault")

    report["required_metadata"] = list(REQUIRED_METADATA)
    report["runtime_metadata_policy"] = REQUIRED_RUNTIME_METADATA_POLICY.copy()


def split_population_counts(split: dict[str, Any]) -> dict[str, int]:
    counts = split.get("counts")
    if isinstance(counts, dict) and {"samples", "groups"} <= counts.keys():
        return counts
    allocation = split.get("allocation")
    allocation_counts = allocation.get("counts") if isinstance(allocation, dict) else None
    if not isinstance(allocation_counts, dict):
        return {}
    samples = 0
    groups = 0
    for stage_counts in allocation_counts.values():
        if not isinstance(stage_counts, dict):
            return {}
        evaluation = stage_counts.get("evaluation")
        if not isinstance(evaluation, dict) or not {"samples", "groups"} <= evaluation.keys():
            return {}
        samples += evaluation["samples"]
        groups += evaluation["groups"]
    return {"samples": samples, "groups": groups}


def check_population(
    root: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> None:
    expected = manifest.get("expected_population")
    if not isinstance(expected, dict):
        fail(report, "EXPECTED_POPULATION_EMPTY", "expected_population must be an object")
        expected = {}
    elif not expected:
        fail(report, "EXPECTED_POPULATION_EMPTY", "expected_population must not be empty")
    missing = [field for field in REQUIRED_POPULATION_FIELDS if field not in expected]
    if missing:
        fail(report, "EXPECTED_POPULATION_INCOMPLETE", repr(missing))

    sample_path = get_path(root, manifest, "sample_manifest", report)
    split_path = get_path(root, manifest, "split_manifest", report)
    if sample_path is None or split_path is None:
        return
    for name, path in (("sample_manifest", sample_path), ("split_manifest", split_path)):
        if not path.is_file():
            fail(report, "POPULATION_FILE_MISSING", f"{name}: {path}")
            return
    sample = load_json(sample_path)
    split = load_json(split_path)
    sample_counts = sample.get("counts")
    split_counts = split_population_counts(split)
    if not isinstance(sample_counts, dict):
        fail(report, "SAMPLE_COUNTS_MISSING", str(sample_path))
        sample_counts = {}
    if not split_counts:
        fail(report, "SPLIT_COUNTS_MISSING", str(split_path))

    for key in ("candidate_injections", "retained_injections"):
        if key in expected and sample_counts.get(key) != expected[key]:
            fail(
                report,
                "SAMPLE_COUNT_MISMATCH",
                f"{key}: {sample_counts.get(key)} != {expected[key]}",
            )
    for key in ("samples", "groups"):
        if key in expected and split_counts.get(key) != expected[key]:
            fail(
                report,
                "SPLIT_COUNT_MISMATCH",
                f"{key}: {split_counts.get(key)} != {expected[key]}",
            )
    report["population_checked"] = True


def check_qualification(
    root: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> None:
    expected = manifest.get("expected_qualification")
    if not isinstance(expected, dict):
        fail(report, "EXPECTED_QUALIFICATION_EMPTY", "expected_qualification must be an object")
        expected = {}
    elif not expected:
        fail(report, "EXPECTED_QUALIFICATION_EMPTY", "expected_qualification must not be empty")
    missing = [field for field in REQUIRED_QUALIFICATION_FIELDS if field not in expected]
    if missing:
        fail(report, "EXPECTED_QUALIFICATION_INCOMPLETE", repr(missing))

    path = get_path(root, manifest, "qualification_summary", report)
    if path is None:
        return
    if not path.is_file():
        fail(report, "QUALIFICATION_SUMMARY_MISSING", str(path))
        return
    summary = load_json(path)
    if not isinstance(summary, dict):
        fail(report, "QUALIFICATION_SUMMARY_INVALID", str(path))
        return
    actual = summary["qualification"] if isinstance(summary.get("qualification"), dict) else summary
    for key in REQUIRED_QUALIFICATION_FIELDS:
        if key not in actual:
            fail(report, "QUALIFICATION_FIELD_MISSING", key)
        elif key in expected and actual[key] != expected[key]:
            fail(
                report,
                "QUALIFICATION_MISMATCH",
                f"{key}: {actual[key]} != {expected[key]}",
            )
    report["qualification_checked"] = True


def check_previous_runs(
    root: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> None:
    runs = manifest.get("previous_invalid_runs")
    if not isinstance(runs, list):
        fail(report, "PREVIOUS_INVALID_RUNS_MISSING", "previous_invalid_runs must be a list")
        return
    if not runs:
        fail(report, "PREVIOUS_INVALID_RUNS_EMPTY", "previous_invalid_runs must not be empty")
        report["previous_runs_checked"] = 0
        return
    checked = 0
    for item in runs:
        if not isinstance(item, dict) or not {"path", "sha256"} <= item.keys():
            fail(report, "PREVIOUS_RUN_BINDING_INVALID", repr(item))
            continue
        path = resolve_path(root, item["path"])
        if path is None:
            fail(report, "PREVIOUS_RUN_BINDING_INVALID", repr(item))
            continue
        if not path.is_file():
            fail(report, "PREVIOUS_RUN_MISSING", str(path))
            continue
        actual = sha256_file(path)
        if actual != item["sha256"]:
            fail(report, "PREVIOUS_RUN_DRIFT", f"{path}: {actual} != {item['sha256']}")
            continue
        checked += 1
    report["previous_runs_checked"] = checked
    report["previous_invalid_run_drift"] = len(runs) - checked


def check_zero_outputs(
    root: Path,
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> None:
    outputs = manifest.get("scientific_output_paths")
    if not isinstance(outputs, list):
        fail(report, "SCIENTIFIC_OUTPUT_PATHS_MISSING", "scientific_output_paths must be a list")
        return
    if not outputs:
        fail(report, "SCIENTIFIC_OUTPUT_PATHS_EMPTY", "scientific_output_paths must not be empty")
        report["scientific_output_paths_checked"] = 0
        report["scientific_outputs"] = 0
        return
    existing: list[str] = []
    for raw in outputs:
        path = resolve_path(root, raw)
        if path is None:
            fail(report, "SCIENTIFIC_OUTPUT_PATH_INVALID", repr(raw))
            continue
        if path.exists():
            existing.append(str(path))
            fail(report, "SCIENTIFIC_OUTPUT_EXISTS", str(path))
    report["scientific_output_paths_checked"] = len(outputs)
    report["scientific_outputs"] = len(existing)


def validate(root: Path, manifest_path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "PASS",
        "failures": [],
        "manifest": str(manifest_path),
    }
    manifest = load_json(manifest_path)
    if manifest.get("status") != REQUIRED_PREFLIGHT_STATUS:
        fail(report, "PREFLIGHT_STATUS", f"must be {REQUIRED_PREFLIGHT_STATUS}")
    if manifest.get("verification_level") != REQUIRED_VERIFICATION_LEVEL:
        fail(report, "VERIFICATION_LEVEL", f"must be {REQUIRED_VERIFICATION_LEVEL}")
    check_hash_bindings(root, manifest, report)
    check_runtime_contract(root, manifest, report)
    check_population(root, manifest, report)
    check_qualification(root, manifest, report)
    check_previous_runs(root, manifest, report)
    check_zero_outputs(root, manifest, report)
    if report["failures"]:
        report["status"] = "FAIL"
    report["empty_set_bypasses"] = 0 if report["status"] == "PASS" else len(
        [
            item
            for item in report["failures"]
            if item["code"].endswith("_EMPTY")
        ]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a formal experiment preflight manifest")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        report = validate(args.root.resolve(), args.manifest.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {
            "status": "FAIL",
            "failures": [{"code": "PREFLIGHT_INPUT_ERROR", "message": str(exc)}],
        }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
