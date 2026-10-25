"""Build the deterministic, visibility-honest B1 remediation package."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
NATURAL_HELPER_DIR = ROOT / "research/natural_program_learning_20261024_v2"
sys.path.insert(0, str(NATURAL_HELPER_DIR))

from B1_LOCAL_EDIT_APPLIER import (  # noqa: E402
    apply_patch,
    canonical_json,
    canonical_sha256,
    evaluate_semantic_acceptance,
)
from analyze_binding_residual_v3 import (  # noqa: E402
    extract_target,
    parse_cells,
    program_value,
    refs_in_program,
)
from semantic_delivery_check_v3 import (  # noqa: E402
    question_from_prompt,
    semantic_check,
)


AUTHORITY_COMMIT = "caa18102bdbbcfe99a889bcf82a125dcc20fdcca"
AUTHORITY_PATH = "docs/research/LOOP_D_RESEARCH_PROMPT.md"
AUTHORITY_BLOB = "c7053b678ce4c67f38656f73932991632107b4fe"
AUTHORITY_LF_SHA256 = "3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7"
SUPERSEDED_WINDOWS_SHA256 = "c23ec144fe778d1ea8b36ab35def58a13b59d9682f1da4adf6005c2ea378e922"
INSTANCE_PATH = Path("/home/testuser/wzh/research_runs/weighted_error_repair_v5/weighted_confirmation_instances_v5.jsonl")
RESULT_PATH = Path("/home/testuser/wzh/research_runs/weighted_error_repair_v5/weighted_confirmation_results_v5.jsonl")
SOURCE_POOL_PATH = Path("/home/testuser/wzh/research_runs/natural_program_finance_20261024_v2/natural_tasks_source_disjoint_v4.jsonl")
SOURCE_DISJOINT_RESULTS_PATH = Path("/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/source_disjoint_results_v4.jsonl")
EXPOSURE_MANIFEST_PATH = ROOT / "research/feedback_delivery_continuation_20261025_v1/EXPOSURE_UNION_SOURCES_V1.json"
CHECKPOINT_PATH = Path("/home/testuser/wzh/research_runs/natural_program_finance_20261024_v2/training/ordinary_answer_execution_sft/final_adapter")

VISIBLE_UNIT_VOCABULARY = {"crore", "million", "percent", "reported", "thousand"}
UNRESOLVED_RULES = {
    "NAT_train_2e038152_274875b0::original": "TOTAL_ROW_LABEL_NOT_VISIBLE",
    "NAT_train_2e038152_274875b0::relevant_change": "TOTAL_ROW_LABEL_NOT_VISIBLE",
    "NAT_train_2e038152_274875b0::irrelevant_change": "TOTAL_ROW_AND_PERIOD_LABELS_NOT_VISIBLE",
    "NAT_train_d45efeed_e84d4bd3::irrelevant_change": "PERIOD_HEADER_NOT_VISIBLE",
    "NAT_train_b74eaf04_caa15292::relevant_change": "UNIT_SCALE_NOT_VISIBLE",
    "NAT_train_04e7f446_538c6915::original": "COMPARISON_DIRECTION_NOT_VISIBLE",
    "NAT_train_04e7f446_538c6915::relevant_change": "COMPARISON_DIRECTION_NOT_VISIBLE",
    "NAT_train_04e7f446_538c6915::irrelevant_change": "COMPARISON_DIRECTION_NOT_VISIBLE",
    "NAT_train_819641fb_108cfcb0::original": "COMPARISON_DIRECTION_NOT_VISIBLE",
    "NAT_train_819641fb_108cfcb0::relevant_change": "COMPARISON_DIRECTION_NOT_VISIBLE",
    "NAT_train_819641fb_108cfcb0::irrelevant_change": "COMPARISON_DIRECTION_NOT_VISIBLE",
}
ROW_ROLE_FAMILIES = {
    "NAT_train_b74eaf04_caa15292",
    "NAT_train_bdeeb701_c6f0281e",
}
ROW_PERIOD_ROLE_FAMILIES = {"NAT_train_dac4e923_dccd9dbf"}
SIGN_REVERSAL_FAMILIES = {
    "NAT_train_04e7f446_538c6915",
    "NAT_train_819641fb_108cfcb0",
}
EVIDENCE_REQUIREMENTS = {
    "NAT_train_b74eaf04_caa15292": ("ROW_ROLE_MISBINDING", ["others, allowances", "ceo", "coo"]),
    "NAT_train_bdeeb701_c6f0281e": ("ROW_ROLE_MISBINDING", ["consumer cyber safety", "enterprise security"]),
    "NAT_train_dac4e923_dccd9dbf": ("ROW_AND_PERIOD_ROLE_MISBINDING", ["amer", "emea", "2018"]),
}
PANEL_SEED = "phaseb-b2-development-panel-v1:20261026:"
SET_BINDING_MECHANISM = "VISIBLE_SET_BINDING_REBINDING"
SET_BINDING_PATHS = {
    "/program/left/ref",
    "/program/right/ref",
    "/evidence_refs/<nonnegative-index>",
}
CORRECT_PRESERVATION_DIRECTION = {
    "status": "PRE_REGISTERED",
    "preserve": [
        "unchanged_references",
        "operator",
        "order",
        "unit",
    ],
    "originally_correct_family_rule": (
        "E must not damage an originally correct family; preserve its complete "
        "reference set, operator, order and unit with a no-op set-binding target"
    ),
    "unit_component_training_target": False,
    "direction_component_training_target": False,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def git_bytes(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def authority_binding() -> dict[str, Any]:
    commit_tree_blob = git_bytes("rev-parse", f"{AUTHORITY_COMMIT}:{AUTHORITY_PATH}").decode().strip()
    blob_bytes = git_bytes("cat-file", "blob", AUTHORITY_BLOB)
    lf_bytes = blob_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    observed_lf_sha256 = hashlib.sha256(lf_bytes).hexdigest()
    binding_ok = (
        commit_tree_blob == AUTHORITY_BLOB
        and observed_lf_sha256 == AUTHORITY_LF_SHA256
        and len(blob_bytes) == 21673
    )
    return {
        "schema": "b1_authority_binding_correction_v1",
        "status": "PASS" if binding_ok else "FAIL",
        "canonical_identity": {
            "git_commit": AUTHORITY_COMMIT,
            "path": AUTHORITY_PATH,
            "git_blob": AUTHORITY_BLOB,
            "byte_size": len(blob_bytes),
            "gb10_lf_sha256": observed_lf_sha256,
            "identity_match": binding_ok,
        },
        "superseded_noncanonical_identity": {
            "sha256": SUPERSEDED_WINDOWS_SHA256,
            "source": "earlier A task cards and budget-ledger Windows-byte value",
            "canonical_for_remote_execution": False,
            "action": "reference only; never use as the Git authority digest",
        },
        "verification": {
            "commit_path_blob_matches_declared_blob": commit_tree_blob == AUTHORITY_BLOB,
            "blob_lf_sha256_matches_declared_gb10_sha256": observed_lf_sha256 == AUTHORITY_LF_SHA256,
            "blob_byte_size": len(blob_bytes),
            "carriage_returns_in_blob": blob_bytes.count(b"\r"),
        },
    }


def strict_json_outcome(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"valid": False, "error": str(exc), "value": None}
    return {
        "valid": isinstance(value, dict),
        "error": None if isinstance(value, dict) else "top_level_not_object",
        "value": value if isinstance(value, dict) else None,
    }


def visible_unit_values(prompt: str) -> list[str]:
    lowered = prompt.lower()
    return sorted(
        unit
        for unit in VISIBLE_UNIT_VOCABULARY
        if re.search(rf"\b{re.escape(unit)}\b", lowered)
    )


def target_for_audit(instance: dict[str, Any]) -> dict[str, Any]:
    expected = instance["expected"]
    return {
        "program": copy.deepcopy(expected["program"]),
        "evidence_refs": copy.deepcopy(expected["evidence_refs"]),
        "unit": expected["unit"],
    }


def materialize_set_binding_target(
    candidate: dict[str, Any],
    reference_target: dict[str, Any],
    cells: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Materialize the reference-derived unordered set into O's fixed slot skeleton."""
    desired_refs = list(dict.fromkeys(refs_in_program(reference_target["program"])))
    current_refs = refs_in_program(candidate["program"])
    if len(desired_refs) != len(current_refs):
        raise RuntimeError("set_binding_cardinality_mismatch")
    if len(set(desired_refs)) != len(desired_refs):
        raise RuntimeError("set_binding_reference_not_unique")

    target = copy.deepcopy(candidate)
    slot_paths = ("/program/left/ref", "/program/right/ref")
    assigned: dict[str, str] = {}
    unmatched_slots: list[str] = []
    for path in slot_paths:
        current_ref = target["program"][path.split("/")[-2]][path.split("/")[-1]]
        if current_ref in desired_refs and current_ref not in assigned.values():
            assigned[path] = current_ref
        else:
            unmatched_slots.append(path)
    unmatched_desired = [
        ref for ref in desired_refs
        if ref not in assigned.values()
    ]

    def slot_column(path: str) -> str:
        ref = target["program"][path.split("/")[-2]][path.split("/")[-1]]
        return ref.split(":")[-1]

    def desired_column(ref: str) -> str:
        return ref.split(":")[-1]

    for ref in sorted(unmatched_desired, key=desired_column):
        matching_paths = [
            path for path in unmatched_slots
            if desired_column(ref) == slot_column(path)
        ]
        competing_refs = [
            other for other in unmatched_desired
            if other != ref and desired_column(other) == desired_column(ref)
        ]
        if len(matching_paths) == 1 and not competing_refs:
            assigned[matching_paths[0]] = ref
            unmatched_slots.remove(matching_paths[0])
            unmatched_desired.remove(ref)

    for path, ref in zip(
        unmatched_slots,
        sorted(unmatched_desired),
        strict=True,
    ):
        assigned[path] = ref

    if set(assigned) != set(slot_paths) or set(assigned.values()) != set(desired_refs):
        raise RuntimeError("set_binding_materialization_failed")
    for path, ref in assigned.items():
        _, node, field = path.strip("/").split("/")
        target["program"][node][field] = ref
    target["evidence_refs"] = [
        target["program"]["left"]["ref"],
        target["program"]["right"]["ref"],
    ]
    if cells is not None and any(ref not in cells for ref in target["evidence_refs"]):
        raise RuntimeError("set_binding_target_ref_not_visible")
    return target


def make_operations(
    candidate: dict[str, Any],
    target: dict[str, Any],
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for path, target_value in (
        ("/program/left/ref", target["program"].get("left", {}).get("ref")),
        ("/program/right/ref", target["program"].get("right", {}).get("ref")),
    ):
        if target_value is None:
            continue
        current: Any = candidate
        for part in path.strip("/").split("/"):
            current = current[part]
        if current != target_value:
            operations.append({
                "op": "replace",
                "path": path,
                "expected": copy.deepcopy(current),
                "value": copy.deepcopy(target_value),
            })
    for index, value in enumerate(target["evidence_refs"]):
        current = candidate["evidence_refs"][index]
        if current != value:
            operations.append({
                "op": "replace",
                "path": f"/evidence_refs/{index}",
                "expected": copy.deepcopy(current),
                "value": copy.deepcopy(value),
            })
    return operations


def classify_case(
    instance: dict[str, Any],
    result: dict[str, Any],
    candidate: dict[str, Any],
    reference_target: dict[str, Any],
) -> tuple[str, str, str]:
    instance_id = instance["instance_id"]
    unit_mismatch = candidate["unit"] != reference_target["unit"]
    if unit_mismatch:
        if result["program_correct"]:
            return (
                "CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL",
                "LABEL_UNRESOLVED",
                "UNIT_SCALE_NOT_VISIBLE",
            )
        return "UNRESOLVED", "NATURAL_ERROR_UNRESOLVED", "UNIT_SCALE_NOT_VISIBLE"
    if result["program_correct"]:
        return "CORRECT_NO_OP", "CORRECT_NO_OP", "NO_OP"
    if instance_id in UNRESOLVED_RULES:
        family = instance["source_task_id"]
        if family in SIGN_REVERSAL_FAMILIES:
            error_type = "OPERAND_ORDER_SIGN_REVERSAL"
        elif family == "NAT_train_b74eaf04_caa15292":
            error_type = "UNIT_SCALE_NOT_VISIBLE"
        elif family == "NAT_train_2e038152_274875b0":
            error_type = UNRESOLVED_RULES[instance_id]
        else:
            error_type = UNRESOLVED_RULES[instance_id]
        return "UNRESOLVED", "NATURAL_ERROR_UNRESOLVED", error_type
    family = instance["source_task_id"]
    if family in ROW_ROLE_FAMILIES:
        return "ELIGIBLE", "NATURAL_ERROR_ELIGIBLE", "ROW_ROLE_MISBINDING"
    if family in ROW_PERIOD_ROLE_FAMILIES:
        return (
            "ELIGIBLE",
            "NATURAL_ERROR_ELIGIBLE",
            "ROW_AND_PERIOD_ROLE_MISBINDING",
        )
    raise RuntimeError(f"unclassified_natural_error:{instance_id}")


def cell_snapshot(
    refs: list[str],
    cells: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "ref": ref,
            "row_label": cells.get(ref, {}).get("row_label"),
            "column_label": cells.get(ref, {}).get("column_label"),
            "period_labels": cells.get(ref, {}).get("period_labels"),
            "unit_labels": cells.get(ref, {}).get("unit_labels"),
            "value": cells.get(ref, {}).get("value"),
        }
        for ref in refs
    ]


def direction_component(
    candidate: dict[str, Any],
    *,
    status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    component = {
        "status": status,
        "operator": copy.deepcopy(candidate["program"]["op"]),
        "operator_source": "O_CANDIDATE",
        "operand_order": [
            candidate["program"]["left"].get("ref"),
            candidate["program"]["right"].get("ref"),
        ],
        "operand_order_source": "O_CANDIDATE_SLOT_SKELETON",
        "reference_direction_inference": False,
        "training_target": False,
        "patch_paths_allowed": [],
    }
    if reason is not None:
        component["unresolved_reason"] = reason
    return component


def set_binding_component(
    *,
    status: str,
    desired_reference_set: list[str] | None,
    operations: list[dict[str, Any]],
    label_sha256: str | None,
    training_target: bool,
    reference_role: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "desired_reference_set": (
            sorted(desired_reference_set)
            if desired_reference_set is not None
            else None
        ),
        "operations": copy.deepcopy(operations),
        "set_binding_label_sha256": label_sha256,
        "training_target": training_target,
        "reference_role": reference_role,
        "unit_component_training_target": False,
        "direction_component_training_target": False,
    }


def visible_evidence_test(
    instance: dict[str, Any],
    candidate: dict[str, Any],
    reference_target: dict[str, Any],
    cells: dict[str, dict[str, Any]],
    error_type: str,
) -> dict[str, Any]:
    requirement = EVIDENCE_REQUIREMENTS.get(instance["source_task_id"])
    if requirement is None or requirement[0] != error_type:
        raise RuntimeError(f"missing_visible_evidence_requirement:{instance['instance_id']}")
    registered_type, required_tokens = requirement
    prompt = instance["prompt"].lower()
    question = question_from_prompt(instance["prompt"]).lower()
    candidate_refs = refs_in_program(candidate["program"])
    target_refs = refs_in_program(reference_target["program"])
    all_refs_visible = all(ref in cells for ref in candidate_refs + target_refs)
    tokens_in_question = all(token in question for token in required_tokens)
    tokens_in_deployment_input = all(token in prompt for token in required_tokens)
    structural_only_difference = candidate["unit"] == reference_target["unit"]
    if error_type in {"ROW_ROLE_MISBINDING", "ROW_AND_PERIOD_ROLE_MISBINDING"}:
        mechanism = (
            "replace only reference-valued operand paths and corresponding "
            "evidence_refs entries with the visible requested unordered set binding"
        )
        if error_type == "ROW_AND_PERIOD_ROLE_MISBINDING":
            mechanism = (
                "replace only reference-valued operand paths and corresponding "
                "evidence_refs entries with the visible requested row-and-period set binding"
            )
    else:
        raise RuntimeError(f"visible_evidence_test_not_set_binding:{error_type}")
    passed = all([
        registered_type == error_type,
        tokens_in_question,
        tokens_in_deployment_input,
        all_refs_visible,
        structural_only_difference,
    ])
    return {
        "schema": "b1_visible_evidence_test_v2",
        "error_type": error_type,
        "mechanism": SET_BINDING_MECHANISM,
        "status": "PASS" if passed else "FAIL",
        "required_visible_tokens": required_tokens,
        "tokens_present_in_question": tokens_in_question,
        "tokens_present_in_deployment_input": tokens_in_deployment_input,
        "candidate_and_target_refs_visible": all_refs_visible,
        "candidate_refs": candidate_refs,
        "target_refs": target_refs,
        "structural_only_difference": structural_only_difference,
        "set_binding_sufficiency_test": passed,
        "direction_derivability_test": {
            "required": False,
            "status": "EXCLUDED_FROM_SET_BINDING_TARGET",
            "derived_from_gold": False,
            "reason": (
                "operator and subtraction-order direction are frozen to O or "
                "marked UNRESOLVED; no direction is inferred from the reference"
            ),
        },
        "correction_operator": {
            "mechanism_id": SET_BINDING_MECHANISM,
            "subtype": error_type,
            "name": "VISIBLE_SET_BINDING_REF_REBIND",
            "mechanism": mechanism,
            "legal_paths": sorted(SET_BINDING_PATHS),
            "unit_edits_allowed": False,
            "operator_edits_allowed": False,
            "direction_edits_allowed": False,
        },
        "reference_role": "REFERENCE_DERIVED_UNORDERED_SET_LABEL",
        "hidden_reference_used_for_set_label": True,
        "hidden_reference_used_for_direction": False,
    }


def reference_only_edit_instruction(
    patch: dict[str, Any] | None,
    candidate_unit: str,
    unresolved_reason: str | None,
) -> str | None:
    if patch is None:
        return None
    if not patch["operations"]:
        return (
            "No structural edit is required. Preserve the candidate program, evidence_refs, "
            f"and unit `{candidate_unit}` exactly."
        )
    clauses = []
    for operation in patch["operations"]:
        clauses.append(
            f"at `{operation['path']}`, replace `{json.dumps(operation['expected'], sort_keys=True)}` "
            f"with `{json.dumps(operation['value'], sort_keys=True)}`"
        )
    suffix = f" Do not edit unit `{candidate_unit}`."
    if unresolved_reason is not None:
        suffix += f" Preserve this unresolved label status: {unresolved_reason}."
    return "; ".join(clauses) + "." + suffix


def feedback_content_diff(trajectory_id: str) -> dict[str, Any]:
    content = {
        "schema": "b1_neutral_deployment_feedback_v1",
        "trajectory_id": trajectory_id,
        "instruction": (
            "Revise the candidate using only the visible question and table. "
            "Do not use hidden references, gold programs, or development edit instructions."
        ),
    }
    content_json = canonical_json(content)
    content_sha256 = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
    return {
        "R": copy.deepcopy(content),
        "E": copy.deepcopy(content),
        "content_sha256": content_sha256,
        "differences": [],
        "identical": True,
        "minimal_edit_instruction_in_deployment_feedback": False,
    }


def build_trajectory(
    instance: dict[str, Any],
    result: dict[str, Any],
    *,
    instance_line: int,
    result_line: int,
) -> dict[str, Any]:
    candidate = extract_target(result["generated_text"])
    if candidate is None:
        raise RuntimeError(f"embedded_target_missing:{instance['instance_id']}")
    strict_outcome = strict_json_outcome(result["generated_text"])
    embedded_outcome = {
        "valid": True,
        "method": "json_decoder_raw_decode_from_first_valid_object",
        "value": candidate,
    }
    cells = parse_cells(instance["table_text"])
    question = question_from_prompt(instance["prompt"])
    try:
        semantic_decision, semantic_reasons = semantic_check(question, candidate["program"], cells)
    except Exception as exc:
        semantic_decision = "TOOL_ERROR"
        semantic_reasons = [f"{type(exc).__name__}:{exc}"]
    reference_target = target_for_audit(instance)
    eligibility_status, natural_error_status, error_type = classify_case(
        instance,
        result,
        candidate,
        reference_target,
    )
    unit_mismatch = candidate["unit"] != reference_target["unit"]
    visible_refs = sorted(cells)
    visible_units = visible_unit_values(instance["prompt"])
    set_binding_target = None
    if eligibility_status == "ELIGIBLE":
        set_binding_target = materialize_set_binding_target(
            candidate,
            reference_target,
            cells,
        )
    elif eligibility_status in {
        "CORRECT_NO_OP",
        "CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL",
    }:
        set_binding_target = materialize_set_binding_target(
            candidate,
            candidate,
            cells,
        )
    question_hash = hashlib.sha256(instance["prompt"].encode("utf-8")).hexdigest()
    table_hash = hashlib.sha256(instance["table_text"].encode("utf-8")).hexdigest()

    execution_before = None
    try:
        execution_before = program_value(candidate["program"], cells)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        execution_before = {"error": f"{type(exc).__name__}:{exc}"}
    execution_target = None
    try:
        execution_target = program_value(reference_target["program"], cells)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        execution_target = {"error": f"{type(exc).__name__}:{exc}"}
    target_executable = isinstance(execution_target, (int, float))
    target_answer_match = (
        target_executable
        and math.isclose(
            float(execution_target),
            float(instance["expected"]["answer"]),
            rel_tol=1e-9,
            abs_tol=1e-9,
        )
    )
    patched_semantic_decision = semantic_decision
    patched_semantic_reasons = semantic_reasons

    evidence_test = None
    if eligibility_status == "ELIGIBLE":
        evidence_test = visible_evidence_test(
            instance,
            candidate,
            reference_target,
            cells,
            error_type,
        )
        if evidence_test["status"] != "PASS":
            raise RuntimeError(f"visible_evidence_test_failed:{instance['instance_id']}")

    patch = None
    r_target = None
    execution_after = None
    set_binding_status = "UNRESOLVED"
    set_binding_training_target = False
    set_binding_reference_role = "AUDIT_ONLY_UNRESOLVED"
    desired_reference_set: list[str] | None = None
    direction_status = "FROZEN_TO_O_CANDIDATE"
    direction_reason = None
    if eligibility_status == "ELIGIBLE":
        set_binding_status = "QUALIFIED"
        set_binding_training_target = True
        set_binding_reference_role = "REFERENCE_DERIVED_UNORDERED_SET_LABEL"
        desired_reference_set = refs_in_program(reference_target["program"])
    elif eligibility_status in {
        "CORRECT_NO_OP",
        "CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL",
    }:
        set_binding_status = "PRESERVE_ORIGINAL"
        set_binding_training_target = True
        set_binding_reference_role = "O_CANDIDATE_PRESERVATION"
        desired_reference_set = refs_in_program(candidate["program"])
    elif error_type == "OPERAND_ORDER_SIGN_REVERSAL":
        set_binding_status = "SET_PRESERVED_DIRECTION_UNRESOLVED"
        set_binding_reference_role = "AUDIT_ONLY_SET_PRESERVED"
        desired_reference_set = refs_in_program(candidate["program"])
        direction_status = "UNRESOLVED"
        direction_reason = "COMPARISON_DIRECTION_NOT_VISIBLE"

    patch_verification: dict[str, Any] = {
        "status": "NOT_APPLICABLE",
        "applied": False,
        "hidden_reference_fallback": False,
        "unit_edited": False,
        "operator_edited": False,
        "direction_edited": False,
    }
    operations: list[dict[str, Any]] = []
    if set_binding_target is not None:
        operations = make_operations(candidate, set_binding_target)
        patch = {
            "schema": "b1_local_patch_v1",
            "candidate_sha256": canonical_sha256(candidate),
            "target_sha256": canonical_sha256(set_binding_target),
            "operations": operations,
        }
        patched = apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=set(visible_refs),
        )
        execution_after = program_value(patched["program"], cells)
        try:
            patched_semantic_decision, patched_semantic_reasons = semantic_check(
                question,
                patched["program"],
                cells,
            )
        except Exception as exc:
            patched_semantic_decision = "TOOL_ERROR"
            patched_semantic_reasons = [f"{type(exc).__name__}:{exc}"]
        if (
            patched != set_binding_target
            or canonical_sha256(patched) != patch["target_sha256"]
        ):
            raise RuntimeError(f"patch_target_mismatch:{instance['instance_id']}")
        set_binding_exact = (
            set(patched["evidence_refs"]) == set(desired_reference_set or [])
            and patched["program"]["op"] == candidate["program"]["op"]
            and patched["unit"] == candidate["unit"]
            and set(patched["program"]) == set(candidate["program"])
            and set(patched["program"]["left"]) == set(candidate["program"]["left"])
            and set(patched["program"]["right"]) == set(candidate["program"]["right"])
        )
        if not set_binding_exact:
            raise RuntimeError(f"set_binding_preservation_failed:{instance['instance_id']}")
        patch_verification = {
            "status": "PASS",
            "applied": True,
            "candidate_sha256_verified": True,
            "target_sha256_verified": True,
            "set_binding_target_exact": True,
            "hidden_reference_fallback": False,
            "unit_edited": False,
            "operator_edited": False,
            "direction_edited": False,
        }
    else:
        patch_verification["status"] = "UNRESOLVED_NO_PATCH"

    set_binding = set_binding_component(
        status=set_binding_status,
        desired_reference_set=desired_reference_set,
        operations=operations,
        label_sha256=(
            canonical_sha256({
                "desired_reference_set": sorted(desired_reference_set or []),
                "operations": operations,
            })
            if desired_reference_set is not None
            else None
        ),
        training_target=set_binding_training_target,
        reference_role=set_binding_reference_role,
    )
    direction = direction_component(
        candidate,
        status=direction_status,
        reason=direction_reason,
    )
    if patch is not None:
        r_target = {
            "schema": "b1_set_binding_training_target_v2",
            "set_binding_component": copy.deepcopy(set_binding),
        }

    if eligibility_status == "CORRECT_NO_OP":
        overall = "PASS" if semantic_decision == "VALID" else "UNRESOLVED"
    elif eligibility_status == "CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL":
        overall = "UNRESOLVED"
    elif eligibility_status == "ELIGIBLE":
        overall = (
            "PASS"
            if patch_verification["status"] == "PASS"
            and set_binding_exact
            else "FAIL"
        )
    else:
        overall = "UNRESOLVED"
    if overall == "FAIL":
        raise RuntimeError(f"verification_failed:{instance['instance_id']}")

    minimal_instruction = reference_only_edit_instruction(
        patch,
        candidate["unit"],
        error_type if overall == "UNRESOLVED" else None,
    )
    trajectory_id = instance["instance_id"]
    feedback_diff = feedback_content_diff(trajectory_id)
    semantic_acceptance = evaluate_semantic_acceptance(
        set_binding_target if set_binding_target is not None else candidate,
        reference_target,
        execution_equal=(
            False
            if eligibility_status == "ELIGIBLE"
            else target_answer_match
        ),
        visible_evidence_valid=all(
            ref in cells
            for ref in refs_in_program(
                (set_binding_target or candidate)["program"]
            )
        ),
        unit_valid=not unit_mismatch,
        role_period_valid=(
            patched_semantic_decision == "VALID"
            if patch is not None
            else semantic_decision == "VALID"
        ),
    )
    evidence = {
        "observed_from": "frozen_ordinary_output",
        "generated_program_refs": refs_in_program(candidate["program"]),
        "frozen_reference_program_refs_for_audit": refs_in_program(reference_target["program"]),
        "generated_unit": candidate["unit"],
        "frozen_reference_unit_for_audit": reference_target["unit"],
        "generated_value": execution_before,
        "frozen_reference_value_for_audit": execution_target,
        "question": question,
        "generated_reference_cells": cell_snapshot(refs_in_program(candidate["program"]), cells),
        "frozen_reference_cells_for_audit": cell_snapshot(refs_in_program(reference_target["program"]), cells),
        "semantic_reasons": semantic_reasons,
    }

    return {
        "schema": "b1_correction_trajectory_v3",
        "task_id": "phaseb-b1-remediation2-a-20261026",
        "goal_id": "FEEDBACK_LEARNING_PHASE_B_20261026",
        "source_identity": {
            "instance_id": instance["instance_id"],
            "source_task_id": instance["source_task_id"],
            "source_cluster_id": instance["table_uid"],
            "table_uid": instance["table_uid"],
            "variant": instance["variant"],
            "instance_file": str(INSTANCE_PATH),
            "instance_line": instance_line,
            "instance_sha256": sha256_file(INSTANCE_PATH),
            "result_file": str(RESULT_PATH),
            "result_line": result_line,
            "result_sha256": sha256_file(RESULT_PATH),
            "model_arm": result["model_arm"],
        },
        "visible_input": {
            "prompt": instance["prompt"],
            "visible_input_sha256": question_hash,
            "table_text": instance["table_text"],
            "table_sha256": table_hash,
            "allowed_evidence_refs": visible_refs,
            "allowed_answer_units": visible_units,
            "allowed_answer_units_rule": "lexical unit-vocabulary strings literally present in the deployment prompt; no gold-scale inference",
            "contains_hidden_scale_claim": False,
        },
        "o_output": {
            "raw_generated_text": result["generated_text"],
            "parsed_candidate": copy.deepcopy(candidate),
            "frozen_scoring_fields": {
                "interface_valid": result["interface_valid"],
                "refs_valid": result["refs_valid"],
                "program_executable": result["program_executable"],
                "program_correct": result["program_correct"],
                "failure": result["failure"],
            },
        },
        "error": {
            "natural_error_status": natural_error_status,
            "eligibility_status": eligibility_status,
            "error_type": None if natural_error_status == "CORRECT_NO_OP" else error_type,
            "unresolved_reason": UNRESOLVED_RULES.get(instance["instance_id"]),
            "unit_field_status": "UNRESOLVED" if unit_mismatch else "NOT_DIFFERENT_FROM_CANDIDATE",
            "evidence": evidence,
            "visible_evidence_test": evidence_test,
        },
        "correction": {
            "set_binding_component": set_binding,
            "direction_component": direction,
            "correction_target_status": set_binding_status,
            "frozen_reference_target_for_audit": copy.deepcopy(reference_target),
            "frozen_reference_target_qualification": (
                "AUDIT_ONLY_NOT_A_TRAINING_TARGET"
            ),
            "r_target": r_target,
            "e_patch": patch,
            "unit_correction_status": "UNRESOLVED" if unit_mismatch else "NOT_APPLICABLE",
        },
        "verification": {
            "strict_json": strict_outcome,
            "embedded_json": embedded_outcome,
            "structural_identity": {
                "definition": (
                    "canonical equality to the materialized unordered set-binding "
                    "target while preserving O operator, slot skeleton and unit"
                ),
                "patch_target_exact": (
                    patch is not None
                    and set_binding_target is not None
                    and canonical_sha256(set_binding_target) == patch["target_sha256"]
                ),
                "semantic_gold_equated_by_target_sha256": False,
                "full_reference_target_is_training_target": False,
            },
            "semantic": {
                "definition": (
                    "separate executable acceptance requiring valid evidence, unit, role and "
                    "period semantics; structural identity alone is insufficient"
                ),
                "candidate_decision": semantic_decision,
                "patched_decision": patched_semantic_decision,
                "decision": (
                    "SET_BINDING_ACCEPTED_DIRECTION_UNRESOLVED"
                    if eligibility_status == "ELIGIBLE"
                    else "ACCEPTED_STRUCTURAL_EXACT"
                    if overall == "PASS"
                    else "UNRESOLVED"
                ),
                "legal_equivalence_accepted": False,
                "policy_implementation": "B1_LOCAL_EDIT_APPLIER.evaluate_semantic_acceptance",
                "dataset_reference_acceptance": semantic_acceptance,
                "eligible_direction_gold_claim": False,
                "candidate_reasons": semantic_reasons,
                "patched_reasons": patched_semantic_reasons if overall != "PASS" else [],
            },
            "execution": {
                "o_before": execution_before,
                "reference_target_for_audit": execution_target,
                "patched_after": execution_after,
                "frozen_expected_answer_for_audit": instance["expected"]["answer"],
                "reference_target_executes_to_frozen_expected": target_answer_match,
                "eligible_set_binding_target_answer_claim": (
                    False if eligibility_status == "ELIGIBLE" else None
                ),
            },
            "patch": patch_verification,
            "overall": overall,
        },
        "label_reference_identity": {
            "training_reference": {
                "origin": "EXISTING_DETERMINISTIC_TASK_REFERENCE",
                "role": "FROZEN_SET_BINDING_ONLY_TRAINING_TARGET",
                "minimal_edit_instruction": minimal_instruction,
                "unit_action": "PRESERVE_CANDIDATE",
                "direction_action": "PRESERVE_O_OR_UNRESOLVED",
                "unit_training_target": False,
                "direction_training_target": False,
            },
            "teacher_reference": {
                "origin": "FROZEN_DEVELOPMENT_REFERENCE",
                "role": "REFERENCE_ONLY_SET_BINDING_EDIT_INSTRUCTION",
                "minimal_edit_instruction": minimal_instruction,
                "unit_action": "PRESERVE_CANDIDATE",
                "direction_action": "PRESERVE_O_OR_UNRESOLVED",
                "unit_training_target": False,
                "direction_training_target": False,
            },
            "deployment_feedback": {
                "origin": "NEUTRAL_VISIBLE_INPUT_ONLY",
                "role": "DEPLOYMENT_FEEDBACK",
                "minimal_edit_instruction": None,
                "reference_program_input": False,
            },
            "confirmation_gold": None,
            "feedback_learning_claim": "NOT_QUALIFIED",
            "human_gold": False,
            "r_e_feedback_content_diff": feedback_diff,
        },
        "exposure": {
            "role": "EXPOSED_DEVELOPMENT_SUPERVISION",
            "source_identity_boundary": "task_id/question_uid/table_uid only; report/company identity unavailable",
            "eligible_for_current_confirmation": False,
            "reason": "source identity belongs to the current exposure union",
        },
    }


def taxonomy_artifact(trajectories: list[dict[str, Any]]) -> dict[str, Any]:
    eligible_rows = [
        row for row in trajectories
        if row["error"]["natural_error_status"] == "NATURAL_ERROR_ELIGIBLE"
    ]
    eligible = Counter(row["error"]["error_type"] for row in eligible_rows)
    families_by_subtype = {
        subtype: sorted({
            row["source_identity"]["source_task_id"]
            for row in eligible_rows
            if row["error"]["error_type"] == subtype
        })
        for subtype in (
            "ROW_ROLE_MISBINDING",
            "ROW_AND_PERIOD_ROLE_MISBINDING",
        )
    }
    all_eligible_families = sorted({
        row["source_identity"]["source_task_id"] for row in eligible_rows
    })
    mechanism = {
        "mechanism": SET_BINDING_MECHANISM,
        "status": "ONE_MECHANISM_TWO_OBSERVED_SUBTYPES",
        "independent_mechanism_count": 1,
        "independent_subtype_mechanism_claim": False,
        "source_family_count": len(all_eligible_families),
        "trajectory_count": len(eligible_rows),
        "source_families": all_eligible_families,
        "subtype_source_family_counts": {
            subtype: len(families_by_subtype[subtype])
            for subtype in families_by_subtype
        },
        "subtype_trajectory_counts": dict(sorted(eligible.items())),
        "subtype_counts": {
            subtype: {
                "source_family_count": len(families_by_subtype[subtype]),
                "trajectory_count": eligible[subtype],
                "source_families": families_by_subtype[subtype],
            }
            for subtype in (
                "ROW_ROLE_MISBINDING",
                "ROW_AND_PERIOD_ROLE_MISBINDING",
            )
        },
        "visible_evidence_sufficiency_test": (
            "required role/period tokens occur literally in question and deployment "
            "input; candidate and reference-derived set members are visible cells; "
            "unit is unchanged; direction derivability is explicitly excluded"
        ),
        "correction_operator": {
            "name": "VISIBLE_SET_BINDING_REF_REBIND",
            "legal_paths": sorted(SET_BINDING_PATHS),
            "operator_edits_allowed": False,
            "direction_edits_allowed": False,
            "unit_edits_allowed": False,
        },
        "set_binding_component": {
            "training_target": True,
            "reference_role": "REFERENCE_DERIVED_UNORDERED_SET_LABEL",
        },
        "direction_component": {
            "training_target": False,
            "eligible_status": "FROZEN_TO_O_CANDIDATE",
            "sign_reversal_status": "UNRESOLVED",
            "gold_inference_allowed": False,
        },
        "unit_component": {
            "training_target": False,
            "all_unit_corrections": "UNRESOLVED",
        },
        "correct_preservation_direction": copy.deepcopy(
            CORRECT_PRESERVATION_DIRECTION
        ),
    }
    return {
        "schema": "b1_error_type_taxonomy_v2",
        "status": "ONE_VISIBLE_SET_BINDING_MECHANISM_TWO_OBSERVED_SUBTYPES",
        "registered_mechanism": mechanism,
        "registered_types": [
            {
                "error_type": "ROW_ROLE_MISBINDING",
                "mechanism": SET_BINDING_MECHANISM,
                "independent_mechanism": False,
                "source_family_count": len(
                    families_by_subtype["ROW_ROLE_MISBINDING"]
                ),
                "source_families": families_by_subtype["ROW_ROLE_MISBINDING"],
                "eligible_trajectory_count": eligible["ROW_ROLE_MISBINDING"],
                "visible_evidence_sufficiency_test": (
                    "question and table literally contain the requested role tokens; "
                    "reference-derived set members are visible; direction excluded"
                ),
                "correction_operator": "VISIBLE_SET_BINDING_REF_REBIND",
                "legal_paths": sorted(SET_BINDING_PATHS),
                "unit_edits_allowed": False,
                "operator_edits_allowed": False,
                "direction_edits_allowed": False,
            },
            {
                "error_type": "ROW_AND_PERIOD_ROLE_MISBINDING",
                "mechanism": SET_BINDING_MECHANISM,
                "independent_mechanism": False,
                "source_family_count": len(
                    families_by_subtype["ROW_AND_PERIOD_ROLE_MISBINDING"]
                ),
                "source_families": families_by_subtype[
                    "ROW_AND_PERIOD_ROLE_MISBINDING"
                ],
                "eligible_trajectory_count": eligible["ROW_AND_PERIOD_ROLE_MISBINDING"],
                "visible_evidence_sufficiency_test": (
                    "question and table literally contain the requested row roles and period; "
                    "reference-derived set members are visible; direction excluded"
                ),
                "correction_operator": "VISIBLE_SET_BINDING_REF_REBIND",
                "legal_paths": sorted(SET_BINDING_PATHS),
                "unit_edits_allowed": False,
                "operator_edits_allowed": False,
                "direction_edits_allowed": False,
            },
        ],
        "unresolved_types": [
            {
                "error_type": "OPERAND_ORDER_SIGN_REVERSAL",
                "status": "UNRESOLVED",
                "correction_operator": None,
                "reason": (
                    "the visible phrase uses unordered 'between A and B' wording; the "
                    "subtraction direction is not uniquely derivable without the "
                    "reference; operator and order remain frozen to O and are not "
                    "training targets"
                ),
            },
            {
                "error_type": "UNIT_SCALE_NOT_VISIBLE",
                "status": "UNRESOLVED",
                "correction_operator": None,
                "reason": "gold scale is not a deployment-visible answer-unit label",
            },
            {
                "error_type": "TOTAL_ROW_LABEL_NOT_VISIBLE",
                "status": "UNRESOLVED",
                "correction_operator": None,
            },
            {
                "error_type": "TOTAL_ROW_AND_PERIOD_LABELS_NOT_VISIBLE",
                "status": "UNRESOLVED",
                "correction_operator": None,
            },
            {
                "error_type": "PERIOD_HEADER_NOT_VISIBLE",
                "status": "UNRESOLVED",
                "correction_operator": None,
            },
        ],
        "explicitly_absent_types": [
            {
                "error_type": "WRONG_OPERATOR",
                "natural_occurrence_count": 0,
                "status": "NOT_QUALIFIED",
                "reason": "no natural program.op difference occurs in the 72 B1 trajectories",
            }
        ],
    }


def build_development_panel(
    trajectories: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trajectories:
        grouped[row["source_identity"]["source_task_id"]].append(row)
    original_wrong: list[dict[str, Any]] = []
    original_correct: list[dict[str, Any]] = []
    for source_task_id, rows in grouped.items():
        original = next(row for row in rows if row["source_identity"]["variant"] == "original")
        item = {
            "source_task_id": source_task_id,
            "source_cluster_id": original["source_identity"]["source_cluster_id"],
            "table_uid": original["source_identity"]["table_uid"],
            "originally_correct_on_original_variant": original["o_output"]["frozen_scoring_fields"]["program_correct"],
        }
        if item["originally_correct_on_original_variant"]:
            original_correct.append(item)
        else:
            original_wrong.append(item)
    if len(original_wrong) != 5 or len(original_correct) != 19:
        raise RuntimeError("unexpected_original_family_denominator")

    for item in original_correct:
        item["selection_sha256"] = hashlib.sha256(
            (PANEL_SEED + item["source_task_id"]).encode("utf-8")
        ).hexdigest()
    selected_correct = sorted(original_correct, key=lambda item: item["selection_sha256"])[:7]
    selected_wrong = sorted(original_wrong, key=lambda item: item["source_task_id"])
    selected = []
    for stratum, items in (
        ("ALL_ORIGINAL_WRONG_FAMILIES", selected_wrong),
        ("SEVEN_LOWEST_SHA256_OF_19_ORIGINAL_CORRECT_FAMILIES", selected_correct),
    ):
        for item in items:
            item = copy.deepcopy(item)
            item["selection_stratum"] = stratum
            rows = grouped[item["source_task_id"]]
            item["variants"] = sorted(row["source_identity"]["variant"] for row in rows)
            item["trajectory_ids"] = sorted(row["source_identity"]["instance_id"] for row in rows)
            item["trajectory_sha256"] = {
                row["source_identity"]["variant"]: hashlib.sha256(
                    canonical_json(row).encode("utf-8")
                ).hexdigest()
                for row in rows
            }
            selected.append(item)
    if len(selected) != 12:
        raise RuntimeError("development_panel_not_12_families")
    selected_trajectory_ids = {trajectory_id for item in selected for trajectory_id in item["trajectory_ids"]}
    unit_unresolved = sum(
        row["correction"]["unit_correction_status"] == "UNRESOLVED"
        for row in trajectories
        if row["source_identity"]["instance_id"] in selected_trajectory_ids
    )
    eligible_rows = [
        row for row in trajectories
        if row["error"]["natural_error_status"] == "NATURAL_ERROR_ELIGIBLE"
    ]
    eligible_families = {
        row["source_identity"]["source_task_id"] for row in eligible_rows
    }
    subtype_families = {
        subtype: {
            row["source_identity"]["source_task_id"]
            for row in eligible_rows
            if row["error"]["error_type"] == subtype
        }
        for subtype in (
            "ROW_ROLE_MISBINDING",
            "ROW_AND_PERIOD_ROLE_MISBINDING",
        )
    }
    subtype_trajectories = Counter(
        row["error"]["error_type"] for row in eligible_rows
    )
    return {
        "schema": "b2_development_panel_draft_v2",
        "status": "PROPOSED_NOT_FROZEN",
        "training_authorized": False,
        "authority_prerequisite": "D must freeze this exact panel after C accepts the B1 remediation",
        "source_population": {
            "trajectory_count": len(trajectories),
            "source_family_count": len(grouped),
            "variants_per_family": 3,
            "variant_independence": "REPEATED_MEASURES_WITHIN_SOURCE_FAMILY",
        },
        "selection_rule": [
            "include all five source families whose original variant is not program-correct",
            "from the 19 originally-correct families, sort by SHA-256(PANEL_SEED + source_task_id) and include the first seven",
        ],
        "panel_seed": PANEL_SEED,
        "family_count": 12,
        "trajectory_count": 36,
        "originally_correct_family_denominator": {
            "count": 7,
            "denominator": 12,
            "fraction": "7/12",
            "criterion": "o_output.frozen_scoring_fields.program_correct on the original variant",
        },
        "originally_wrong_family_count": 5,
        "set_binding_mechanism": {
            "mechanism": SET_BINDING_MECHANISM,
            "source_family_count": len(eligible_families),
            "trajectory_count": len(eligible_rows),
            "subtype_source_family_counts": {
                subtype: len(families)
                for subtype, families in subtype_families.items()
            },
            "subtype_trajectory_counts": dict(sorted(subtype_trajectories.items())),
            "independent_mechanism_count": 1,
        },
        "correct_preservation_direction": copy.deepcopy(
            CORRECT_PRESERVATION_DIRECTION
        ),
        "unit_unresolved_trajectory_count": unit_unresolved,
        "development_only": True,
        "source_role": "EXPOSED_DEVELOPMENT_SUPERVISION",
        "confirmation_claim": "NONE",
        "families": selected,
    }


def build_source_pool_candidate() -> dict[str, Any]:
    pool = load_jsonl(SOURCE_POOL_PATH)
    used_results = load_jsonl(SOURCE_DISJOINT_RESULTS_PATH)
    used_ids = sorted({row["source_task_id"] for row in used_results})
    candidate_tasks = [task for task in pool if task["task_id"] not in used_ids][:24]
    if len(candidate_tasks) != 24:
        raise RuntimeError("future_confirmation_candidate_pool_too_small")
    return {
        "status": "RESERVED_CANDIDATE_NOT_CURRENTLY_EXPOSURE_CLEAN",
        "boundary": "same-dataset source-isolated only; report/company independence is unavailable",
        "source_pool_path": str(SOURCE_POOL_PATH),
        "source_pool_sha256": sha256_file(SOURCE_POOL_PATH),
        "historical_source_disjoint_results_path": str(SOURCE_DISJOINT_RESULTS_PATH),
        "historical_source_disjoint_results_sha256": sha256_file(SOURCE_DISJOINT_RESULTS_PATH),
        "task_count": len(candidate_tasks),
        "task_ids": [task["task_id"] for task in candidate_tasks],
        "table_uids": [task["table_uid"] for task in candidate_tasks],
        "blocking_condition": "the entire current source-disjoint pool is already named in the exposure-union manifest",
        "minimum_next_action": "D must freeze a reserved split and C must independently recompute a new pre-generation union before any confirmation generation",
    }


def main() -> int:
    instances = load_jsonl(INSTANCE_PATH)
    results = load_jsonl(RESULT_PATH)
    instance_lines = {row["instance_id"]: index for index, row in enumerate(instances, start=1)}
    ordinary = [
        row for row in results
        if row["model_arm"] == "ordinary_answer_execution_sft"
    ]
    result_lines = {
        row["instance_id"]: index
        for index, row in enumerate(results, start=1)
        if row["model_arm"] == "ordinary_answer_execution_sft"
    }
    if len(instances) != 72 or len(ordinary) != 72:
        raise RuntimeError("unexpected_frozen_dataset_shape")
    trajectories = [
        build_trajectory(
            instance,
            result,
            instance_line=instance_lines[instance["instance_id"]],
            result_line=result_lines[instance["instance_id"]],
        )
        for instance, result in zip(instances, ordinary, strict=True)
    ]
    write_jsonl(OUT_DIR / "B1_CORRECTION_TRAJECTORIES.jsonl", trajectories)

    authority = authority_binding()
    write_json(OUT_DIR / "B1_AUTHORITY_BINDING_CORRECTION.json", authority)
    taxonomy = taxonomy_artifact(trajectories)
    write_json(OUT_DIR / "B1_ERROR_TYPE_TAXONOMY.json", taxonomy)
    panel = build_development_panel(trajectories)
    write_json(OUT_DIR / "B2_DEVELOPMENT_PANEL_DRAFT.json", panel)

    natural_status = Counter(row["error"]["natural_error_status"] for row in trajectories)
    eligibility = Counter(row["error"]["eligibility_status"] for row in trajectories)
    error_types = Counter(
        row["error"]["error_type"]
        for row in trajectories
        if row["error"]["natural_error_status"] == "NATURAL_ERROR_ELIGIBLE"
    )
    overall = Counter(row["verification"]["overall"] for row in trajectories)
    unit_mismatches = sum(
        row["correction"]["unit_correction_status"] == "UNRESOLVED"
        for row in trajectories
    )
    unit_only = sum(
        row["error"]["unit_field_status"] == "UNRESOLVED"
        and row["o_output"]["frozen_scoring_fields"]["program_correct"]
        for row in trajectories
    )
    patch_pass = sum(row["verification"]["patch"]["status"] == "PASS" for row in trajectories)
    taxonomy_pass = sum(
        row["error"]["visible_evidence_test"]["status"] == "PASS"
        for row in trajectories
        if row["error"]["visible_evidence_test"] is not None
    )
    scientific_status = (
        "REMEDIATED_WITH_LIMITATIONS"
        if authority["status"] == "PASS"
        and len(error_types) == 2
        and taxonomy_pass == 5
        and unit_mismatches > 0
        and all(
            row["correction"]["unit_correction_status"] == "UNRESOLVED"
            for row in trajectories
            if row["error"]["unit_field_status"] == "UNRESOLVED"
        )
        else "QUALIFICATION_FAILED"
    )

    contract = {
        "schema": "b1_local_patch_contract_v3",
        "status": "IMPLEMENTED_AND_DETERMINISTICALLY_VERIFIED",
        "representation": (
            "restricted set-binding replace operations, not JSON Patch RFC 6902"
        ),
        "mechanism": SET_BINDING_MECHANISM,
        "patch_keys": ["schema", "candidate_sha256", "target_sha256", "operations"],
        "operation_keys": ["op", "path", "expected", "value"],
        "operation": "replace only",
        "max_operations": 8,
        "candidate_keys": ["program", "evidence_refs", "unit"],
        "allowed_paths": sorted(SET_BINDING_PATHS),
        "forbidden_paths": [
            "/program/op",
            "/program/left/const",
            "/program/right/const",
            "/unit",
        ],
        "direction_policy": {
            "operator_source": "O_CANDIDATE",
            "operand_order_source": "O_CANDIDATE_SLOT_SKELETON",
            "sign_reversal_direction": "UNRESOLVED",
            "gold_direction_inference": False,
            "direction_patch_paths_allowed": [],
            "direction_training_target": False,
        },
        "correct_preservation_direction": copy.deepcopy(
            CORRECT_PRESERVATION_DIRECTION
        ),
        "unit_policy": {
            "candidate_unit_is_immutable": True,
            "all_unit_field_corrections": "UNRESOLVED",
            "unit_mismatch_trajectory_count": unit_mismatches,
            "unit_only_mismatch_trajectory_count": unit_only,
            "allowed_answer_units_rule": (
                "lexical unit-vocabulary strings literally present in the deployment prompt; "
                "never constructed from expected.unit or question.scale"
            ),
        },
        "target_semantics": {
            "target_exact": (
                "canonical structural identity to the materialized unordered "
                "set-binding target only"
            ),
            "target_exact_is_not_semantic_gold": True,
            "full_reference_program_is_training_target": False,
            "semantic_acceptance": (
                "separate executable acceptance requiring valid visible evidence, unit, role, "
                "and period semantics; eligible direction remains unresolved and is "
                "never inferred from gold"
            ),
            "semantic_acceptance_implementation": "B1_LOCAL_EDIT_APPLIER.evaluate_semantic_acceptance",
        },
        "expressiveness_bound": {
            "operand_depth": 1,
            "deeper_operands_fail_closed": True,
            "out_of_scope_b1_trajectory_count": 0,
        },
        "fail_closed_checks": [
            "exact top-level and operation keys",
            "canonical candidate SHA-256",
            "exact expected current value",
            "reference values must occur in the runtime-visible reference set",
            "restricted binary arithmetic program shape",
            "program refs equal evidence_refs",
            "candidate unit remains byte-identical",
            "operator and O slot skeleton remain byte-identical",
            "final canonical set-binding-target SHA-256",
            "operator, const and direction paths fail closed",
            "no duplicate or disallowed paths",
            "no silent reference fallback",
        ],
        "canonicalization": {
            "json": "UTF-8",
            "sort_keys": True,
            "separators": [",", ":"],
            "allow_nan": False,
        },
        "implementation": "B1_LOCAL_EDIT_APPLIER.py",
        "tests": "B1_TEST_LOCAL_EDIT_APPLIER.py",
    }
    write_json(OUT_DIR / "B1_LOCAL_PATCH_CONTRACT.json", contract)

    manifest = {
        "schema": "b1_supervision_manifest_v3",
        "task_id": "phaseb-b1-remediation2-a-20261026",
        "goal_id": "FEEDBACK_LEARNING_PHASE_B_20261026",
        "authority": authority["canonical_identity"] | {
            "status": authority["status"],
            "superseded_windows_sha256": SUPERSEDED_WINDOWS_SHA256,
            "correction_artifact": "B1_AUTHORITY_BINDING_CORRECTION.json",
        },
        "scientific_qualification": {
            "status": scientific_status,
            "trajectory_count": len(trajectories),
            "natural_status_counts": dict(sorted(natural_status.items())),
            "eligibility_counts": dict(sorted(eligibility.items())),
            "eligible_natural_error_count": natural_status["NATURAL_ERROR_ELIGIBLE"],
            "eligible_error_types": dict(sorted(error_types.items())),
            "registered_mechanism": {
                "mechanism": SET_BINDING_MECHANISM,
                "independent_mechanism_count": 1,
                "source_family_count": len({
                    row["source_identity"]["source_task_id"]
                    for row in trajectories
                    if row["error"]["natural_error_status"] == "NATURAL_ERROR_ELIGIBLE"
                }),
                "trajectory_count": natural_status["NATURAL_ERROR_ELIGIBLE"],
                "subtype_source_family_counts": taxonomy["registered_mechanism"][
                    "subtype_source_family_counts"
                ],
                "subtype_trajectory_counts": taxonomy["registered_mechanism"][
                    "subtype_trajectory_counts"
                ],
            },
            "visible_evidence_test_pass": taxonomy_pass,
            "verification_overall": dict(sorted(overall.items())),
            "strict_json_valid": sum(row["verification"]["strict_json"]["valid"] for row in trajectories),
            "embedded_json_valid": sum(row["verification"]["embedded_json"]["valid"] for row in trajectories),
            "patch_verification_pass": patch_pass,
            "unit_mismatch_trajectory_count": unit_mismatches,
            "unit_only_mismatch_trajectory_count": unit_only,
            "unit_corrections_unresolved": unit_mismatches,
            "feedback_learning_status": "NOT_QUALIFIED",
            "supervision_mode": (
                "REFERENCE_DERIVED_VISIBLE_SET_BINDING_REVISION_SUPERVISION"
            ),
            "set_binding_component_training_target": True,
            "direction_component_training_target": False,
            "unit_component_training_target": False,
        },
        "error_taxonomy": {
            "artifact": "B1_ERROR_TYPE_TAXONOMY.json",
            "sha256": sha256_file(OUT_DIR / "B1_ERROR_TYPE_TAXONOMY.json"),
            "registered_mechanism_count": 1,
            "registered_observed_subtype_count": 2,
            "registered_visible_error_type_count": 2,
            "natural_wrong_operator_count": 0,
            "correct_preservation_direction": copy.deepcopy(
                CORRECT_PRESERVATION_DIRECTION
            ),
        },
        "sources": {
            "instances": {
                "path": str(INSTANCE_PATH),
                "sha256": sha256_file(INSTANCE_PATH),
                "role": "frozen_visible_inputs_and_reference_targets",
            },
            "results": {
                "path": str(RESULT_PATH),
                "sha256": sha256_file(RESULT_PATH),
                "role": "frozen_multi-arm outputs; only ordinary_answer_execution_sft is O",
            },
            "ordinary_checkpoint": {
                "path": str(CHECKPOINT_PATH),
                "exists": CHECKPOINT_PATH.exists(),
                "role": "frozen ordinary checkpoint; not modified or loaded",
            },
            "semantic_execution_helpers": {
                "analyze_binding_residual_v3.py": sha256_file(NATURAL_HELPER_DIR / "analyze_binding_residual_v3.py"),
                "semantic_delivery_check_v3.py": sha256_file(NATURAL_HELPER_DIR / "semantic_delivery_check_v3.py"),
                "natural_program_contract_v2.py": sha256_file(
                    ROOT / "research/feedback_learning_finance_20261024_v2/natural_program_contract_v2.py"
                ),
            },
        },
        "exposure": {
            "manifest_path": str(EXPOSURE_MANIFEST_PATH),
            "manifest_sha256": sha256_file(EXPOSURE_MANIFEST_PATH),
            "selected_source_role": "EXPOSED_DEVELOPMENT_SUPERVISION",
            "selected_overlap_count": len({
                row["source_identity"]["source_task_id"] for row in trajectories
            } | {
                row["source_identity"]["table_uid"] for row in trajectories
            }),
            "confirmation_claim": "NONE",
            "identity_boundary": "task_id/question_uid/table_uid only; report/company identity unavailable",
            "future_candidate": build_source_pool_candidate(),
        },
        "label_roles": {
            "training_reference": (
                "frozen set-binding-only target; operator, order and unit excluded"
            ),
            "teacher_reference": (
                "reference-only set-binding minimal edit instruction; operator, "
                "order and unit excluded"
            ),
            "deployment_feedback": "neutral visible-input-only content identical for R and E",
            "confirmation_gold": None,
            "human_gold": False,
            "feedback_derived_fields": [],
            "unit_training_target": False,
            "direction_training_target": False,
        },
        "deployment_input_contract": {
            "arms": {
                "R": {
                    "inputs": [
                        "question_prompt",
                        "visible_table",
                        "O_candidate_object",
                        "runtime_visible_ref_set",
                        "runtime_visible_unit_set",
                        "neutral_visible_input_feedback",
                    ],
                    "output": (
                        "set-binding-only training target; operator, order and "
                        "unit are not targets"
                    ),
                    "feedback_input": "neutral_visible_input_feedback",
                },
                "E": {
                    "inputs": [
                        "question_prompt",
                        "visible_table",
                        "O_candidate_object",
                        "runtime_visible_ref_set",
                        "runtime_visible_unit_set",
                        "neutral_visible_input_feedback",
                    ],
                    "output": "restricted set-binding-only patch",
                    "feedback_input": "neutral_visible_input_feedback",
                    "postprocess": "deterministic B1_LOCAL_EDIT_APPLIER with no fallback",
                },
            },
            "information_parity": (
                "R and E receive identical visible inputs and identical neutral feedback; "
                "per-trajectory diff is empty"
            ),
            "per_trajectory_diff_field": "label_reference_identity.r_e_feedback_content_diff",
            "reference_only_edit_instruction_fields": [
                "label_reference_identity.training_reference.minimal_edit_instruction",
                "label_reference_identity.teacher_reference.minimal_edit_instruction",
            ],
            "minimal_edit_instruction_in_deployment_feedback": False,
            "strict_json_requirement": "O must parse as one strict whole JSON object before patch application",
            "embedded_json_fallback": False,
            "reference_program_input": False,
            "patch_failure_action": "REJECT_AND_RECORD; never substitute a reference program",
        },
        "target_semantics": contract["target_semantics"],
        "development_panel": {
            "artifact": "B2_DEVELOPMENT_PANEL_DRAFT.json",
            "sha256": sha256_file(OUT_DIR / "B2_DEVELOPMENT_PANEL_DRAFT.json"),
            "family_count": panel["family_count"],
            "originally_correct_family_denominator": panel["originally_correct_family_denominator"],
            "status": panel["status"],
        },
        "overall_gate_status": "REMEDIATION2_COMPLETE_PENDING_C_REAUDIT",
        "b2_training_authorized": False,
        "blocking_risks": [
            "all current trajectories are exposed development supervision",
            (
                "no actual feedback-derived field exists; only reference-derived "
                "visible set-binding revision supervision is qualified"
            ),
            "Loop C re-audit has not accepted the remediation",
            "D has not frozen the proposed 12-family development panel",
        ],
    }
    write_json(OUT_DIR / "B1_SUPERVISION_MANIFEST.json", manifest)

    preflight = {
        "schema": "b1_remediation2_preflight_v1",
        "status": "READY_FOR_C_REAUDIT2_NOT_READY_FOR_B2_TRAINING",
        "ready_for_c_preaudit": True,
        "ready_for_b2_training": False,
        "checks": {
            "C_1_taxonomy_visible_set_binding_mechanism": "CLOSED",
            "C_2_unit_corrections_unresolved_and_unit_paths_forbidden": "CLOSED",
            "C_3_visible_only_units_and_reference_only_edit_instructions": "CLOSED",
            "C_4_structural_identity_separate_from_semantic_acceptance": "CLOSED",
            "C_5_authority_binding_corrected": "CLOSED",
            "C_6_exact_12_family_damage_panel_and_denominator": "CLOSED",
            "loop_c_reaudit": "PENDING",
            "d_panel_freeze": "PENDING",
        },
        "budget_release": {
            "generation_attempts": 0,
            "generation_tokens": 0,
            "training_runs": 0,
            "training_tokens": 0,
        },
    }
    write_json(OUT_DIR / "B1_PREFLIGHT_DRAFT.json", preflight)

    receipt = {
        "schema": "b1_remediation2_receipt_a_v1",
        "task_id": "phaseb-b1-remediation2-a-20261026",
        "status": "A_REMEDIATION2_COMPLETE_PENDING_C_REAUDIT",
        "scientific_content_status": scientific_status,
        "authority_identity_status": authority["status"],
        "counts": {
            "trajectories": len(trajectories),
            "natural_status": dict(sorted(natural_status.items())),
            "eligibility": dict(sorted(eligibility.items())),
            "eligible_natural_errors": natural_status["NATURAL_ERROR_ELIGIBLE"],
            "eligible_error_types": dict(sorted(error_types.items())),
            "visible_evidence_test_pass": taxonomy_pass,
            "unit_mismatch_trajectories": unit_mismatches,
            "unit_only_mismatch_trajectories": unit_only,
            "patch_verification_pass": patch_pass,
            "verification_overall": dict(sorted(overall.items())),
        },
        "model_generation_attempts": 0,
        "training_runs": 0,
        "model_or_judge_calls": 0,
        "tests": {
            "status": "PENDING",
            "command": None,
            "exit_code": None,
            "output": None,
            "output_sha256": None,
        },
        "artifacts": {},
        "immutable_inputs_modified": False,
        "budget_ledger_modified": False,
        "next_action": (
            "C independently re-audits the narrowed set-binding contract; "
            "D freezes the proposed panel; do not train B2"
        ),
    }
    write_json(OUT_DIR / "B1_QUALIFICATION_RECEIPT.json", receipt)

    print(json.dumps({
        "status": receipt["status"],
        "scientific_content_status": scientific_status,
        "authority": authority["status"],
        "trajectories": len(trajectories),
        "eligible_error_types": dict(sorted(error_types.items())),
        "visible_evidence_test_pass": taxonomy_pass,
        "unit_mismatch_trajectories": unit_mismatches,
        "verification": dict(sorted(overall.items())),
        "panel_family_count": panel["family_count"],
        "originally_correct_family_denominator": panel["originally_correct_family_denominator"]["fraction"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
