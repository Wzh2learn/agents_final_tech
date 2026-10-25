"""Fail-closed deterministic applier for B1 restricted local edits."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "b1_local_patch_v1"
PATCH_KEYS = {"schema", "candidate_sha256", "target_sha256", "operations"}
OPERATION_KEYS = {"op", "path", "expected", "value"}
CANDIDATE_KEYS = {"program", "evidence_refs", "unit"}
REF_RE = re.compile(r"^R\d+:C\d+$")
EVIDENCE_INDEX_RE = re.compile(r"^/evidence_refs/(\d+)$")
ALLOWED_PATHS = {
    "/program/left/ref",
    "/program/right/ref",
}
MAX_OPERATIONS = 8


class PatchError(ValueError):
    """Raised whenever a patch cannot be applied without guessing."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def evaluate_semantic_acceptance(
    candidate: Any,
    structural_target: Any,
    *,
    execution_equal: bool,
    visible_evidence_valid: bool,
    unit_valid: bool,
    role_period_valid: bool,
) -> dict[str, Any]:
    """Evaluate semantic acceptance separately from structural target identity."""
    structural_identity = candidate == structural_target
    all_semantic_inputs_valid = all([
        execution_equal,
        visible_evidence_valid,
        unit_valid,
        role_period_valid,
    ])
    if not all_semantic_inputs_valid:
        return {
            "accepted": False,
            "decision": "REJECTED_OR_UNRESOLVED",
            "structural_identity": structural_identity,
            "legal_equivalence_accepted": False,
        }
    return {
        "accepted": True,
        "decision": (
            "ACCEPTED_STRUCTURAL_EXACT"
            if structural_identity
            else "ACCEPTED_LEGAL_EQUIVALENCE"
        ),
        "structural_identity": structural_identity,
        "legal_equivalence_accepted": not structural_identity,
    }


def _require_exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PatchError(f"{label}_must_be_object")
    actual = set(value)
    if actual != keys:
        raise PatchError(
            f"{label}_keys_mismatch:"
            f"missing={sorted(keys - actual)}:extra={sorted(actual - keys)}"
        )
    return value


def _json_value_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return type(left) is type(right) and left == right
    return type(left) is type(right) and left == right


def _path_parts(path: Any) -> list[str]:
    if not isinstance(path, str) or not path.startswith("/"):
        raise PatchError("operation_path_must_be_absolute_json_pointer")
    if "\\" in path or any(part == ".." for part in path.split("/")[1:]):
        raise PatchError("operation_path_traversal_rejected")
    return path.split("/")[1:]


def _read_pointer(container: Any, parts: list[str]) -> Any:
    current = container
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                raise PatchError("operation_path_parent_missing")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit() or int(part) >= len(current):
                raise PatchError("operation_list_index_invalid")
            current = current[int(part)]
        else:
            raise PatchError("operation_path_parent_not_container")
    return current


def _write_pointer(container: Any, parts: list[str], value: Any) -> None:
    current = container
    for part in parts[:-1]:
        if isinstance(current, dict):
            if part not in current:
                raise PatchError("operation_path_parent_missing")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit() or int(part) >= len(current):
                raise PatchError("operation_list_index_invalid")
            current = current[int(part)]
        else:
            raise PatchError("operation_path_parent_not_container")
    final = parts[-1]
    if isinstance(current, dict):
        if final not in current:
            raise PatchError("operation_target_missing")
        current[final] = value
    elif isinstance(current, list):
        if not final.isdigit() or int(final) >= len(current):
            raise PatchError("operation_list_index_invalid")
        current[int(final)] = value
    else:
        raise PatchError("operation_target_parent_not_container")


def _validate_allowed_value(path: str, value: Any, allowed_refs: set[str]) -> None:
    if path.endswith("/ref"):
        if not isinstance(value, str) or value not in allowed_refs:
            raise PatchError("operation_value_reference_not_visible")
        return
    match = EVIDENCE_INDEX_RE.fullmatch(path)
    if match:
        if not isinstance(value, str) or value not in allowed_refs:
            raise PatchError("operation_value_reference_not_visible")
        return
    raise PatchError("operation_path_not_allowed")


def _validate_candidate(candidate: Any, allowed_refs: set[str]) -> dict[str, Any]:
    _require_exact_keys(candidate, CANDIDATE_KEYS, "candidate")
    if not isinstance(candidate["program"], dict):
        raise PatchError("candidate_program_must_be_object")
    if not isinstance(candidate["evidence_refs"], list):
        raise PatchError("candidate_evidence_refs_must_be_list")
    if any(not isinstance(item, str) for item in candidate["evidence_refs"]):
        raise PatchError("candidate_evidence_refs_must_be_strings")
    if not isinstance(candidate["unit"], str):
        raise PatchError("candidate_unit_must_be_string")
    if any(item not in allowed_refs for item in candidate["evidence_refs"]):
        raise PatchError("candidate_reference_not_visible")
    program_refs = _program_refs(candidate["program"])
    if any(ref not in allowed_refs for ref in program_refs):
        raise PatchError("candidate_reference_not_visible")
    if len(candidate["evidence_refs"]) != len(set(candidate["evidence_refs"])):
        raise PatchError("candidate_evidence_refs_must_be_unique")
    if program_refs != candidate["evidence_refs"]:
        raise PatchError("candidate_program_evidence_refs_mismatch")
    return candidate


def _program_refs(program: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(program, dict) and "ref" in program:
        refs.append(str(program["ref"]))
    elif isinstance(program, dict) and "op" in program:
        refs.extend(_program_refs(program.get("left")))
        refs.extend(_program_refs(program.get("right")))
    return list(dict.fromkeys(refs))


def _validate_program_shape(program: Any) -> None:
    if not isinstance(program, dict):
        raise PatchError("patched_program_must_be_object")
    if "ref" in program:
        if set(program) != {"ref"} or not isinstance(program["ref"], str) or not REF_RE.fullmatch(program["ref"]):
            raise PatchError("patched_program_ref_node_invalid")
        return
    if "const" in program:
        if (
            set(program) != {"const"}
            or isinstance(program["const"], bool)
            or not isinstance(program["const"], (int, float))
        ):
            raise PatchError("patched_program_const_node_invalid")
        return
    if set(program) != {"op", "left", "right"} or program.get("op") not in {"add", "sub", "mul", "div"}:
        raise PatchError("patched_program_operator_node_invalid")
    _validate_program_shape(program.get("left"))
    _validate_program_shape(program.get("right"))


def apply_patch(
    candidate: Any,
    patch: Any,
    *,
    allowed_evidence_refs: set[str],
) -> dict[str, Any]:
    """Apply one strict patch and return the exact patched candidate."""
    if not isinstance(candidate, dict):
        raise PatchError("candidate_must_be_object")
    if not allowed_evidence_refs or any(not REF_RE.fullmatch(ref) for ref in allowed_evidence_refs):
        raise PatchError("allowed_evidence_refs_invalid")
    original_unit = copy.deepcopy(candidate["unit"])
    candidate = copy.deepcopy(candidate)
    _validate_candidate(candidate, allowed_evidence_refs)
    _require_exact_keys(patch, PATCH_KEYS, "patch")
    if patch["schema"] != SCHEMA:
        raise PatchError("patch_schema_mismatch")
    if not isinstance(patch["candidate_sha256"], str) or canonical_sha256(candidate) != patch["candidate_sha256"]:
        raise PatchError("candidate_sha256_mismatch")
    if not isinstance(patch["target_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", patch["target_sha256"]):
        raise PatchError("target_sha256_invalid")
    operations = patch["operations"]
    if not isinstance(operations, list) or len(operations) > MAX_OPERATIONS:
        raise PatchError("operations_invalid_or_too_long")
    seen_paths: set[str] = set()
    for operation in operations:
        _require_exact_keys(operation, OPERATION_KEYS, "operation")
        if operation["op"] != "replace":
            raise PatchError("operation_op_must_be_replace")
        path = operation["path"]
        parts = _path_parts(path)
        match = EVIDENCE_INDEX_RE.fullmatch(path)
        if path not in ALLOWED_PATHS and not match:
            raise PatchError("operation_path_not_allowed")
        if path in seen_paths:
            raise PatchError("operation_duplicate_path")
        seen_paths.add(path)
        current = _read_pointer(candidate, parts)
        if not _json_value_equal(current, operation["expected"]):
            raise PatchError("operation_expected_value_mismatch")
        _validate_allowed_value(path, operation["value"], allowed_evidence_refs)
        _write_pointer(candidate, parts, copy.deepcopy(operation["value"]))
    _require_exact_keys(candidate, CANDIDATE_KEYS, "patched_candidate")
    if not isinstance(candidate["program"], dict):
        raise PatchError("patched_program_must_be_object")
    _validate_program_shape(candidate["program"])
    program_refs = _program_refs(candidate["program"])
    evidence_refs = candidate["evidence_refs"]
    if any(not isinstance(item, str) or item not in allowed_evidence_refs for item in evidence_refs):
        raise PatchError("patched_evidence_reference_not_visible")
    if len(evidence_refs) != len(set(evidence_refs)) or program_refs != evidence_refs:
        raise PatchError("patched_program_evidence_refs_mismatch")
    if candidate["unit"] != original_unit:
        raise PatchError("candidate_unit_mutated")
    if canonical_sha256(candidate) != patch["target_sha256"]:
        raise PatchError("target_sha256_mismatch")
    return candidate


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--allowed-refs", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = apply_patch(
            _load_json(args.candidate),
            _load_json(args.patch),
            allowed_evidence_refs=set(_load_json(args.allowed_refs)),
        )
    except (PatchError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
