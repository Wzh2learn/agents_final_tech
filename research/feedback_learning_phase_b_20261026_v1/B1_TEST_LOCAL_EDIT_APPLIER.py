"""Focused deterministic tests for the B1 remediation package."""

from __future__ import annotations

import copy
import json
import math
import re
import sys
import unittest
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from B1_LOCAL_EDIT_APPLIER import (  # noqa: E402
    PatchError,
    apply_patch,
    canonical_sha256,
    evaluate_semantic_acceptance,
)


REGISTERED_SUBCASES = 27
ALLOWED_REFS = {"R1:C1", "R1:C2", "R2:C1", "R2:C2"}
VISIBLE_UNIT_VOCABULARY = {"crore", "million", "percent", "reported", "thousand"}


class raises:
    def __init__(self, exception_type: type[BaseException], match: str | None = None) -> None:
        self.exception_type = exception_type
        self.match = match
        self.exception: BaseException | None = None

    def __enter__(self) -> "raises":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        if exc_type is None:
            raise AssertionError(f"{self.exception_type.__name__} was not raised")
        if not issubclass(exc_type, self.exception_type):
            return False
        if self.match is not None and not re.search(self.match, str(exc)):
            raise AssertionError(f"{exc!r} does not match {self.match!r}")
        self.exception = exc
        return True


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def base_candidate() -> dict[str, Any]:
    return {
        "program": {
            "left": {"ref": "R1:C1"},
            "op": "sub",
            "right": {"ref": "R1:C2"},
        },
        "evidence_refs": ["R1:C1", "R1:C2"],
        "unit": "million",
    }


def independent_table_values(table_text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for row_match in re.finditer(r"^(R\d+) \[(.*?)\] (.*)$", table_text, flags=re.MULTILINE):
        row_id, _, body = row_match.groups()
        for cell_match in re.finditer(r"(C\d+)=([^|]+)", body):
            column_id, raw_value = cell_match.groups()
            text = raw_value.strip().replace(",", "").replace("$", "")
            negative = text.startswith("(") and text.endswith(")")
            text = text.strip("()").rstrip("%")
            try:
                value = float(text)
            except ValueError:
                continue
            values[f"{row_id}:{column_id}"] = -value if negative else value
    return values


def independent_program_value(program: dict[str, Any], cells: dict[str, float]) -> float:
    if "ref" in program:
        return cells[str(program["ref"])]
    if "const" in program:
        return float(program["const"])
    left = independent_program_value(program["left"], cells)
    right = independent_program_value(program["right"], cells)
    if program["op"] == "add":
        return left + right
    if program["op"] == "sub":
        return left - right
    if program["op"] == "mul":
        return left * right
    if program["op"] == "div":
        return left / right
    raise AssertionError(f"unsupported operation: {program['op']}")


def base_patch(candidate: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    for path, target_value in (
        ("/program/left/ref", target["program"]["left"].get("ref")),
        ("/program/right/ref", target["program"]["right"].get("ref")),
    ):
        if target_value is not None:
            current = candidate
            for part in path.strip("/").split("/"):
                current = current[part]
            if current != target_value:
                operations.append({
                    "op": "replace",
                    "path": path,
                    "expected": current,
                    "value": target_value,
                })
    for index, value in enumerate(target["evidence_refs"]):
        current = candidate["evidence_refs"][index]
        if current != value:
            operations.append({
                "op": "replace",
                "path": f"/evidence_refs/{index}",
                "expected": current,
                "value": value,
            })
    return {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(target),
        "operations": operations,
    }


def _all_generated_patches_reproduce_exact_legal_targets() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    assert len(trajectories) == 72
    applied = 0
    for trajectory in trajectories:
        patch = trajectory["correction"]["e_patch"]
        if patch is None:
            assert trajectory["correction"]["set_binding_component"][
                "training_target"
            ] is False
            assert trajectory["correction"]["r_target"] is None
            assert trajectory["verification"]["overall"] == "UNRESOLVED"
            continue
        candidate = trajectory["o_output"]["parsed_candidate"]
        patched = apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=set(trajectory["visible_input"]["allowed_evidence_refs"]),
        )
        component = trajectory["correction"]["set_binding_component"]
        assert set(patched["evidence_refs"]) == set(component["desired_reference_set"])
        assert patched["program"]["op"] == candidate["program"]["op"]
        assert patched["unit"] == candidate["unit"]
        assert set(patched["program"]) == set(candidate["program"])
        assert set(patched["program"]["left"]) == set(candidate["program"]["left"])
        assert set(patched["program"]["right"]) == set(candidate["program"]["right"])
        assert canonical_sha256(patched) == patch["target_sha256"]
        assert trajectory["verification"]["patch"]["hidden_reference_fallback"] is False
        if trajectory["error"]["natural_error_status"] != "NATURAL_ERROR_ELIGIBLE":
            cells = independent_table_values(trajectory["visible_input"]["table_text"])
            observed = independent_program_value(patched["program"], cells)
            expected_answer = trajectory["verification"]["execution"][
                "frozen_expected_answer_for_audit"
            ]
            assert math.isclose(
                observed,
                float(expected_answer),
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
        assert trajectory["verification"]["strict_json"]["valid"] is True
        assert trajectory["verification"]["embedded_json"]["valid"] is True
        applied += 1
    assert applied == 61


def _taxonomy_demonstrates_two_visible_types() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    eligible = [
        row for row in trajectories
        if row["error"]["natural_error_status"] == "NATURAL_ERROR_ELIGIBLE"
    ]
    counts = Counter(row["error"]["error_type"] for row in eligible)
    assert counts == {
        "ROW_ROLE_MISBINDING": 3,
        "ROW_AND_PERIOD_ROLE_MISBINDING": 2,
    }
    assert all(row["error"]["visible_evidence_test"]["status"] == "PASS" for row in eligible)
    assert all(
        row["error"]["visible_evidence_test"]["correction_operator"]["unit_edits_allowed"] is False
        for row in eligible
    )
    taxonomy = load_json(HERE / "B1_ERROR_TYPE_TAXONOMY.json")
    assert taxonomy["status"] == (
        "ONE_VISIBLE_SET_BINDING_MECHANISM_TWO_OBSERVED_SUBTYPES"
    )
    unresolved_types = {item["error_type"]: item for item in taxonomy["unresolved_types"]}
    assert unresolved_types["OPERAND_ORDER_SIGN_REVERSAL"]["status"] == "UNRESOLVED"
    sign_rows = [
        row for row in trajectories
        if row["error"]["error_type"] == "OPERAND_ORDER_SIGN_REVERSAL"
    ]
    assert len(sign_rows) == 6
    assert all(row["error"]["unresolved_reason"] == "COMPARISON_DIRECTION_NOT_VISIBLE" for row in sign_rows)
    assert all(row["correction"]["e_patch"] is None for row in sign_rows)
    assert taxonomy["explicitly_absent_types"][0]["natural_occurrence_count"] == 0


def _eligible_corrections_are_split_into_set_binding_and_direction() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    eligible = [
        row for row in trajectories
        if row["error"]["natural_error_status"] == "NATURAL_ERROR_ELIGIBLE"
    ]
    assert len(eligible) == 5
    for row in eligible:
        correction = row["correction"]
        assert set(correction) >= {"set_binding_component", "direction_component"}
        assert correction["set_binding_component"]["status"] == "QUALIFIED"
        assert correction["direction_component"]["operator_source"] == "O_CANDIDATE"
        assert correction["direction_component"]["training_target"] is False
        assert correction["r_target"]["schema"] == "b1_set_binding_training_target_v2"
        assert set(correction["r_target"]) == {"schema", "set_binding_component"}
        assert all(
            operation["path"] in {
                "/program/left/ref",
                "/program/right/ref",
                "/evidence_refs/0",
                "/evidence_refs/1",
            }
            for operation in correction["e_patch"]["operations"]
        )
    taxonomy = load_json(HERE / "B1_ERROR_TYPE_TAXONOMY.json")
    assert taxonomy["registered_mechanism"]["mechanism"] == "VISIBLE_SET_BINDING_REBINDING"
    assert taxonomy["registered_mechanism"]["source_family_count"] == 3
    assert taxonomy["registered_mechanism"]["subtype_source_family_counts"] == {
        "ROW_ROLE_MISBINDING": 2,
        "ROW_AND_PERIOD_ROLE_MISBINDING": 1,
    }


def _correct_preservation_direction_is_pre_registered() -> None:
    taxonomy = load_json(HERE / "B1_ERROR_TYPE_TAXONOMY.json")
    mechanism = taxonomy["registered_mechanism"]
    direction = mechanism["correct_preservation_direction"]
    assert direction["status"] == "PRE_REGISTERED"
    assert set(direction["preserve"]) == {
        "unchanged_references",
        "operator",
        "order",
        "unit",
    }
    assert direction["originally_correct_family_rule"].startswith("E must not damage")
    assert mechanism["unit_component"]["training_target"] is False
    assert mechanism["direction_component"]["training_target"] is False
    for row in load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl"):
        direction = row["correction"]["direction_component"]
        assert direction["status"] in {
            "FROZEN_TO_O_CANDIDATE",
            "UNRESOLVED",
        }
        assert direction["operator"] == row["o_output"]["parsed_candidate"]["program"]["op"]
        assert direction["training_target"] is False
        assert direction["reference_direction_inference"] is False
        if row["correction"]["r_target"] is not None:
            assert set(row["correction"]["r_target"]) == {
                "schema",
                "set_binding_component",
            }
        if row["o_output"]["frozen_scoring_fields"]["program_correct"]:
            assert row["correction"]["set_binding_component"]["status"] == (
                "PRESERVE_ORIGINAL"
            )
            assert row["correction"]["e_patch"]["operations"] == []
            assert row["correction"]["direction_component"]["training_target"] is False


def _all_unit_mismatches_are_unresolved_and_no_patch_edits_unit() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    unit_mismatches = [
        row for row in trajectories
        if row["o_output"]["parsed_candidate"]["unit"]
        != row["correction"]["frozen_reference_target_for_audit"]["unit"]
    ]
    unit_only = [
        row for row in unit_mismatches
        if row["o_output"]["frozen_scoring_fields"]["program_correct"]
    ]
    assert len(unit_mismatches) == 17
    assert len(unit_only) == 16
    assert all(row["correction"]["unit_correction_status"] == "UNRESOLVED" for row in unit_mismatches)
    assert all(row["error"]["unit_field_status"] == "UNRESOLVED" for row in unit_mismatches)
    assert all(
        operation["path"] != "/unit"
        for row in trajectories
        if row["correction"]["e_patch"] is not None
        for operation in row["correction"]["e_patch"]["operations"]
    )


def _allowed_units_are_lexical_visible_only() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    distributions: Counter[tuple[str, ...]] = Counter()
    for row in trajectories:
        prompt = row["visible_input"]["prompt"].lower()
        lexical = tuple(sorted(
            unit
            for unit in VISIBLE_UNIT_VOCABULARY
            if re.search(rf"\b{re.escape(unit)}\b", prompt)
        ))
        recorded = tuple(row["visible_input"]["allowed_answer_units"])
        assert recorded == lexical
        assert set(recorded) <= VISIBLE_UNIT_VOCABULARY
        distributions[recorded] += 1
    assert distributions[()] == 63
    assert distributions[("percent",)] == 3
    assert distributions[("reported",)] == 6


def _reference_only_edit_instructions_and_feedback_diff() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    for row in trajectories:
        identity = row["label_reference_identity"]
        diff = identity["r_e_feedback_content_diff"]
        assert diff["identical"] is True
        assert diff["differences"] == []
        assert diff["R"] == diff["E"]
        assert identity["deployment_feedback"]["minimal_edit_instruction"] is None
        if row["correction"]["e_patch"] is None:
            assert identity["training_reference"]["minimal_edit_instruction"] is None
            assert identity["teacher_reference"]["minimal_edit_instruction"] is None
        else:
            instruction = identity["training_reference"]["minimal_edit_instruction"]
            assert instruction
            assert instruction == identity["teacher_reference"]["minimal_edit_instruction"]
            assert "unit" in instruction


def _structural_identity_is_separate_from_semantic_acceptance() -> None:
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    overall = Counter(row["verification"]["overall"] for row in trajectories)
    assert overall == {"PASS": 30, "UNRESOLVED": 42}
    for row in trajectories:
        structural = row["verification"]["structural_identity"]
        semantic = row["verification"]["semantic"]
        assert structural["semantic_gold_equated_by_target_sha256"] is False
        assert structural["definition"].startswith("canonical equality")
        assert semantic["definition"].startswith("separate executable acceptance")
        if row["correction"]["e_patch"] is not None:
            assert structural["patch_target_exact"] is True
            assert semantic["decision"] in {
                "ACCEPTED_STRUCTURAL_EXACT",
                "SET_BINDING_ACCEPTED_DIRECTION_UNRESOLVED",
                "UNRESOLVED",
            }
    manifest = load_json(HERE / "B1_SUPERVISION_MANIFEST.json")
    assert manifest["target_semantics"]["target_exact_is_not_semantic_gold"] is True


def _semantic_acceptance_allows_executable_legal_equivalence() -> None:
    structural_target = {
        "program": {
            "left": {"ref": "R1:C1"},
            "op": "add",
            "right": {"ref": "R1:C2"},
        },
        "evidence_refs": ["R1:C1", "R1:C2"],
        "unit": "million",
    }
    equivalent = {
        "program": {
            "left": {"ref": "R1:C2"},
            "op": "add",
            "right": {"ref": "R1:C1"},
        },
        "evidence_refs": ["R1:C1", "R1:C2"],
        "unit": "million",
    }
    accepted = evaluate_semantic_acceptance(
        equivalent,
        structural_target,
        execution_equal=True,
        visible_evidence_valid=True,
        unit_valid=True,
        role_period_valid=True,
    )
    assert accepted["decision"] == "ACCEPTED_LEGAL_EQUIVALENCE"
    assert accepted["structural_identity"] is False
    assert accepted["legal_equivalence_accepted"] is True
    rejected = evaluate_semantic_acceptance(
        equivalent,
        structural_target,
        execution_equal=True,
        visible_evidence_valid=True,
        unit_valid=False,
        role_period_valid=True,
    )
    assert rejected["accepted"] is False


def _authority_binding_is_canonical_and_passing() -> None:
    authority = load_json(HERE / "B1_AUTHORITY_BINDING_CORRECTION.json")
    canonical = authority["canonical_identity"]
    assert authority["status"] == "PASS"
    assert canonical["git_commit"] == "caa18102bdbbcfe99a889bcf82a125dcc20fdcca"
    assert canonical["git_blob"] == "c7053b678ce4c67f38656f73932991632107b4fe"
    assert canonical["gb10_lf_sha256"] == "3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7"
    assert authority["superseded_noncanonical_identity"]["canonical_for_remote_execution"] is False


def _manifest_has_parity_and_closed_conditions() -> None:
    manifest = load_json(HERE / "B1_SUPERVISION_MANIFEST.json")
    assert manifest["overall_gate_status"] == (
        "REMEDIATION3_COMPLETE_PENDING_C_REAUDIT3"
    )
    assert manifest["b2_training_authorized"] is False
    assert manifest["exposure"]["selected_source_role"] == "EXPOSED_DEVELOPMENT_SUPERVISION"
    assert manifest["exposure"]["confirmation_claim"] == "NONE"
    arms = manifest["deployment_input_contract"]["arms"]
    assert arms["R"]["inputs"] == arms["E"]["inputs"]
    assert arms["R"]["feedback_input"] == arms["E"]["feedback_input"]
    assert manifest["deployment_input_contract"]["minimal_edit_instruction_in_deployment_feedback"] is False
    preflight = load_json(HERE / "B1_PREFLIGHT_DRAFT.json")
    assert all(
        preflight["checks"][f"C_{index}_{name}"] == "CLOSED"
        for index, name in [
            (1, "taxonomy_visible_set_binding_mechanism"),
            (2, "unit_corrections_unresolved_and_unit_paths_forbidden"),
            (3, "visible_only_units_and_reference_only_edit_instructions"),
            (4, "structural_identity_separate_from_semantic_acceptance"),
            (5, "authority_binding_corrected"),
            (6, "exact_12_family_damage_panel_and_denominator"),
        ]
    )


def _remediation3_discloses_sign_reversal_and_sole_estimand() -> None:
    report = (HERE / "B1_REPORT.md").read_text(encoding="utf-8")
    manifest = load_json(HERE / "B1_SUPERVISION_MANIFEST.json")
    disclosure = manifest["materialized_target_disclosure"]
    estimand = manifest["qualified_estimand"]
    rule = manifest["resolved_operating_rules"]["OPERAND_ORDER_SIGN_REVERSAL"]

    assert disclosure["sign_reversed_eligible_source_family_count"] == 2
    assert disclosure["sign_reversed_eligible_row_count"] == 3
    assert disclosure["eligible_row_count"] == 5
    families = disclosure["families"]
    assert families["NAT_train_bdeeb701_c6f0281e"][
        "sign_reversed_eligible_row_count"
    ] == 1
    assert families["NAT_train_b74eaf04_caa15292"][
        "sign_reversed_eligible_row_count"
    ] == 2
    assert all(
        family["materialized_target_executes_to_reference_answer"] is False
        for family in families.values()
    )
    assert estimand == {
        "definition": "correct visible cell set with operator, order and unit preserved",
        "is_answer_correctness": False,
        "name": "SET_BINDING_SET_ACCURACY",
        "score_against_reference_answer": "NEVER",
    }
    assert rule["set_difference"] == "CAN_YIELD_ELIGIBLE_SET_BINDING_COMPONENT"
    assert rule["order_only_difference"] == "UNRESOLVED_NO_TRAINING_TARGET"
    assert rule["between_A_and_B_phrase_alone_is_discriminator"] is False
    assert "do not execute to that answer" in report
    assert "must never be scored against the reference answer" in report
    assert "alone is not the discriminator" in report


def _development_panel_is_exact_12_families_with_7_correct() -> None:
    panel = load_json(HERE / "B2_DEVELOPMENT_PANEL_DRAFT.json")
    trajectories = load_jsonl(HERE / "B1_CORRECTION_TRAJECTORIES.jsonl")
    by_id = {
        row["source_identity"]["instance_id"]: row
        for row in trajectories
    }
    assert panel["status"] == "PROPOSED_NOT_FROZEN"
    assert panel["family_count"] == 12
    assert panel["trajectory_count"] == 36
    assert panel["originally_correct_family_denominator"]["count"] == 7
    assert panel["originally_correct_family_denominator"]["denominator"] == 12
    assert panel["originally_wrong_family_count"] == 5
    assert panel["set_binding_mechanism"]["mechanism"] == (
        "VISIBLE_SET_BINDING_REBINDING"
    )
    assert panel["set_binding_mechanism"]["independent_mechanism_count"] == 1
    assert panel["set_binding_mechanism"]["source_family_count"] == 3
    assert panel["set_binding_mechanism"]["trajectory_count"] == 5
    assert panel["set_binding_mechanism"]["subtype_source_family_counts"] == {
        "ROW_ROLE_MISBINDING": 2,
        "ROW_AND_PERIOD_ROLE_MISBINDING": 1,
    }
    assert panel["correct_preservation_direction"]["status"] == "PRE_REGISTERED"
    families = panel["families"]
    assert len(families) == 12
    assert len({item["source_task_id"] for item in families}) == 12
    assert len({item["source_cluster_id"] for item in families}) == 12
    assert sum(item["originally_correct_on_original_variant"] for item in families) == 7
    for item in families:
        assert len(item["variants"]) == 3
        assert len(item["trajectory_ids"]) == 3
        for trajectory_id in item["trajectory_ids"]:
            row = by_id[trajectory_id]
            assert row["source_identity"]["source_task_id"] == item["source_task_id"]
            assert row["source_identity"]["source_cluster_id"] == item["source_cluster_id"]


def _noop_patch_is_exact_identity() -> None:
    candidate = base_candidate()
    patch = {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(candidate),
        "operations": [],
    }
    assert apply_patch(
        candidate,
        patch,
        allowed_evidence_refs=ALLOWED_REFS,
    ) == candidate


def _patch_does_not_mutate_candidate() -> None:
    candidate = base_candidate()
    original = copy.deepcopy(candidate)
    target = copy.deepcopy(candidate)
    target["program"]["left"]["ref"] = "R2:C1"
    target["evidence_refs"][0] = "R2:C1"
    apply_patch(
        candidate,
        base_patch(candidate, target),
        allowed_evidence_refs=ALLOWED_REFS,
    )
    assert candidate == original


def _candidate_hash_mismatch_is_rejected() -> None:
    candidate = base_candidate()
    patch = base_patch(candidate, candidate)
    patch["candidate_sha256"] = "0" * 64
    with raises(PatchError, match="candidate_sha256_mismatch"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _expected_value_mismatch_is_rejected() -> None:
    candidate = base_candidate()
    target = copy.deepcopy(candidate)
    target["program"]["left"]["ref"] = "R2:C1"
    target["evidence_refs"][0] = "R2:C1"
    patch = base_patch(candidate, target)
    patch["operations"][0]["expected"] = "R9:C9"
    with raises(PatchError, match="operation_expected_value_mismatch"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _illegal_path_is_rejected() -> None:
    candidate = base_candidate()
    patch = {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(candidate),
        "operations": [{
            "op": "replace",
            "path": "/program",
            "expected": candidate["program"],
            "value": {"ref": "R2:C1"},
        }],
    }
    with raises(PatchError, match="operation_path_not_allowed"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _invisible_reference_is_rejected() -> None:
    candidate = base_candidate()
    target = copy.deepcopy(candidate)
    target["program"]["left"]["ref"] = "R9:C9"
    target["evidence_refs"][0] = "R9:C9"
    with raises(PatchError, match="operation_value_reference_not_visible"):
        apply_patch(
            candidate,
            base_patch(candidate, target),
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _target_hash_mismatch_is_rejected() -> None:
    candidate = base_candidate()
    target = copy.deepcopy(candidate)
    target["program"]["left"]["ref"] = "R2:C1"
    target["evidence_refs"][0] = "R2:C1"
    patch = base_patch(candidate, target)
    patch["target_sha256"] = "0" * 64
    with raises(PatchError, match="target_sha256_mismatch"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _duplicate_path_is_rejected() -> None:
    candidate = base_candidate()
    target = copy.deepcopy(candidate)
    target["program"]["left"]["ref"] = "R2:C1"
    target["evidence_refs"][0] = "R2:C1"
    patch = base_patch(candidate, target)
    patch["operations"].append(copy.deepcopy(patch["operations"][0]))
    with raises(PatchError, match="operation_duplicate_path"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _unknown_patch_key_is_rejected() -> None:
    candidate = base_candidate()
    patch = {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(candidate),
        "operations": [],
        "reference_program": {"ref": "R2:C1"},
    }
    with raises(PatchError, match="patch_keys_mismatch"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _unit_path_is_forbidden_even_when_lexically_visible() -> None:
    candidate = base_candidate()
    patch = {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(candidate),
        "operations": [{
            "op": "replace",
            "path": "/unit",
            "expected": "million",
            "value": "percent",
        }],
    }
    with raises(PatchError, match="operation_path_not_allowed"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _operator_and_order_paths_are_forbidden_for_set_binding_patches() -> None:
    candidate = base_candidate()
    for path, value in (
        ("/program/op", "add"),
        ("/program/left/const", 1),
        ("/program/right/const", 2),
    ):
        patch = {
            "schema": "b1_local_patch_v1",
            "candidate_sha256": canonical_sha256(candidate),
            "target_sha256": canonical_sha256(candidate),
            "operations": [{
                "op": "replace",
                "path": path,
                "expected": "sub" if path == "/program/op" else {"ref": "R1:C1"},
                "value": value,
            }],
        }
        with raises(PatchError, match="operation_path_not_allowed"):
            apply_patch(
                candidate,
                patch,
                allowed_evidence_refs=ALLOWED_REFS,
            )


def _non_string_candidate_unit_is_rejected() -> None:
    candidate = base_candidate()
    candidate["unit"] = 1
    patch = base_patch(candidate, candidate)
    with raises(PatchError, match="candidate_unit_must_be_string"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _deep_operand_shape_is_out_of_scope_and_fails_closed() -> None:
    candidate = base_candidate()
    patch = {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(candidate),
        "operations": [{
            "op": "replace",
            "path": "/program/left/left/ref",
            "expected": "R1:C1",
            "value": "R2:C1",
        }],
    }
    with raises(PatchError, match="operation_path_not_allowed"):
        apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=ALLOWED_REFS,
        )


def _receipt_is_remediation_scoped_and_zero_budget() -> None:
    receipt = load_json(HERE / "B1_QUALIFICATION_RECEIPT.json")
    assert receipt["status"] == "A_REMEDIATION3_COMPLETE_PENDING_C_REAUDIT3"
    assert receipt["tests"]["status"] in {"PENDING", "PASS"}
    assert receipt["immutable_inputs_modified"] is False
    assert receipt["training_runs"] == 0


class TestB1LocalEditApplier(unittest.TestCase):
    def test_all_registered_cases(self) -> None:
        cases = [
            _all_generated_patches_reproduce_exact_legal_targets,
            _taxonomy_demonstrates_two_visible_types,
            _eligible_corrections_are_split_into_set_binding_and_direction,
            _correct_preservation_direction_is_pre_registered,
            _all_unit_mismatches_are_unresolved_and_no_patch_edits_unit,
            _allowed_units_are_lexical_visible_only,
            _reference_only_edit_instructions_and_feedback_diff,
            _structural_identity_is_separate_from_semantic_acceptance,
            _semantic_acceptance_allows_executable_legal_equivalence,
            _authority_binding_is_canonical_and_passing,
            _manifest_has_parity_and_closed_conditions,
            _remediation3_discloses_sign_reversal_and_sole_estimand,
            _development_panel_is_exact_12_families_with_7_correct,
            _noop_patch_is_exact_identity,
            _patch_does_not_mutate_candidate,
            _candidate_hash_mismatch_is_rejected,
            _expected_value_mismatch_is_rejected,
            _illegal_path_is_rejected,
            _invisible_reference_is_rejected,
            _target_hash_mismatch_is_rejected,
            _duplicate_path_is_rejected,
            _unknown_patch_key_is_rejected,
            _unit_path_is_forbidden_even_when_lexically_visible,
            _operator_and_order_paths_are_forbidden_for_set_binding_patches,
            _non_string_candidate_unit_is_rejected,
            _deep_operand_shape_is_out_of_scope_and_fails_closed,
            _receipt_is_remediation_scoped_and_zero_budget,
        ]
        assert len(cases) == REGISTERED_SUBCASES
        for case in cases:
            with self.subTest(case=case.__name__):
                case()


if __name__ == "__main__":
    unittest.main()
