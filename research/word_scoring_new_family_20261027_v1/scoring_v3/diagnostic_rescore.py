"""Rescore persisted D/T/M outputs with interface and Scoring V3 separation."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from research.adaptive_mechanism_20261027_v1.persistent_budget.shared_tools import (
    safe_calculate,
)
from research.adaptive_mechanism_20261027_v1.scoring_v2 import scorer as v2
from research.word_scoring_new_family_20261027_v1.scoring_v3 import scorer as v3


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RAW_PATH = ROOT / "generation" / "results" / "RAW_RESPONSES.jsonl"
RAW_RECEIPT_PATH = ROOT / "generation" / "results" / "RAW_EXTRACTION_RECEIPT.json"
GENERATION_RECEIPT_PATH = ROOT / "generation" / "GENERATION_RECEIPT.json"
INTERFACE_FAULT_PATH = ROOT / "generation" / "INTERFACE_FAULT_RECEIPT.json"
PANEL_PATH = ROOT / "exposure" / "PANEL_FREEZE.json"
BASELINE_PATH = ROOT / "baseline" / "results" / "ZERO_MODEL_BASELINE.json"
BASELINE_ROWS_PATH = (
    ROOT / "baseline" / "results" / "ZERO_MODEL_BASELINE_ROWS.jsonl"
)
FREEZE_PATH = ROOT / "mechanism" / "MECHANISM_FREEZE.json"
ROWS_PATH = ROOT / "scoring_v3" / "results" / "DIAGNOSTIC_ROWS.jsonl"
SUMMARY_PATH = ROOT / "scoring_v3" / "results" / "DIAGNOSTIC_SUMMARY.json"
FAMILY_PATH = ROOT / "scoring_v3" / "results" / "PER_FAMILY_SUMMARY.json"
INTERFACE_PATH = ROOT / "scoring_v3" / "results" / "INTERFACE_NORMALIZATION_RECEIPT.json"
COMPARISON_PATH = ROOT / "scoring_v3" / "results" / "MECHANISM_COMPARISON.md"
FINAL_KEYS = {
    "answer",
    "numeric_value",
    "unit",
    "evidence_refs",
    "unknown",
    "clarification",
}
TYPED_KEYS = {
    "answer_type",
    "answer",
    "operands",
    "program",
    "operation",
    "unit",
    "evidence_refs",
    "unknown",
    "clarification",
}
ALLOWED_ANSWER_TYPES = {"arithmetic", "count", "multi-span", "span", "other"}
ALLOWED_OPERATIONS = {
    "add",
    "subtract",
    "multiply",
    "divide",
    "percent_change",
    "mean",
    "compare",
    "count",
    "none",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def extract_json_objects(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for match in re.finditer(r"\{", text):
        depth = 0
        in_string = False
        escaped = False
        for index in range(match.start(), len(text)):
            character = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[match.start() : index + 1])
                    except json.JSONDecodeError:
                        pass
                    else:
                        if isinstance(value, dict):
                            objects.append(value)
                    break
    return objects


def visible_context(reference: dict[str, Any]) -> v2.VisibleContext:
    return v2.VisibleContext(
        paragraphs={
            index: {
                "raw_order": str(item["order"]),
                "text": str(item["text"]),
                "uid": str(item["uid"]),
            }
            for index, item in enumerate(reference["paragraphs"], start=1)
        },
        raw_orders={str(item["order"]) for item in reference["paragraphs"]},
        table=v2.parse_table(reference["table_text"]),
    )


def parse_single_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        number = v2.parse_decimal(value)
        return float(number) if number is not None else None
    if isinstance(value, list) and len(value) == 1:
        return parse_single_number(value[0])
    return None


def count_numeric_value(answer: Any) -> float | None:
    if isinstance(answer, list):
        return float(len(answer))
    number = parse_single_number(answer)
    return number


def normalize_typed(
    payload: dict[str, Any],
    arm: str,
    reference: dict[str, Any],
    visible: v2.VisibleContext,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    expected_keys = TYPED_KEYS | ({"bindings"} if arm == "M" else set())
    if set(payload) != expected_keys:
        return None, {
            "status": "FAIL",
            "reason": "typed_key_contract_mismatch",
            "observed_keys": sorted(payload),
            "expected_keys": sorted(expected_keys),
        }
    if payload.get("answer_type") not in ALLOWED_ANSWER_TYPES:
        return None, {"status": "FAIL", "reason": "invalid_answer_type"}
    if payload.get("operation") not in ALLOWED_OPERATIONS:
        return None, {"status": "FAIL", "reason": "invalid_operation"}
    if not isinstance(payload.get("operands"), list):
        return None, {"status": "FAIL", "reason": "operands_not_list"}
    if not isinstance(payload.get("evidence_refs"), list):
        return None, {"status": "FAIL", "reason": "evidence_refs_not_list"}
    if not isinstance(payload.get("unknown"), bool):
        return None, {"status": "FAIL", "reason": "unknown_not_boolean"}
    evidence_refs = [item for item in payload["evidence_refs"] if isinstance(item, str)]
    invalid_refs = v3._validate_observed_refs(evidence_refs, visible)
    if invalid_refs:
        return None, {"status": "FAIL", **invalid_refs}
    if arm == "M":
        binding = validate_bindings(
            payload.get("bindings"), evidence_refs, reference, visible
        )
        if binding["status"] != "PASS":
            return None, binding
    if payload.get("unknown"):
        final = {
            "answer": "UNKNOWN",
            "numeric_value": None,
            "unit": "UNKNOWN",
            "evidence_refs": [],
            "unknown": True,
            "clarification": str(payload.get("clarification") or ""),
        }
        return final, {
            "status": "PASS",
            "reason": "typed_unknown_normalized",
            "binding": binding if arm == "M" else None,
        }
    operation = payload["operation"]
    numeric_value = None
    if operation in {
        "add",
        "subtract",
        "multiply",
        "divide",
        "percent_change",
        "mean",
    }:
        program = str(payload.get("program") or "")
        try:
            numeric_value = float(safe_calculate(program))
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as exc:
            return None, {
                "status": "FAIL",
                "reason": "shared_calculator_rejected_program",
                "error": type(exc).__name__,
            }
    elif operation == "count":
        numeric_value = count_numeric_value(payload.get("answer"))
    elif reference["answer_type"] == "span":
        numeric_value = parse_single_number(payload.get("answer"))
    final = {
        "answer": payload["answer"],
        "numeric_value": numeric_value,
        "unit": str(payload.get("unit") or ""),
        "evidence_refs": evidence_refs,
        "unknown": False,
        "clarification": str(payload.get("clarification") or ""),
    }
    return final, {
        "status": "PASS",
        "reason": "typed_envelope_normalized_with_shared_calculator",
        "calculator_executed": operation
        in {"add", "subtract", "multiply", "divide", "percent_change", "mean"},
        "binding": binding if arm == "M" else None,
    }


def validate_bindings(
    bindings: Any,
    evidence_refs: list[str],
    reference: dict[str, Any],
    visible: v2.VisibleContext,
) -> dict[str, Any]:
    if not isinstance(bindings, list) or not bindings:
        return {"status": "FAIL", "reason": "bindings_missing"}
    if len(bindings) < len(set(evidence_refs)):
        return {"status": "FAIL", "reason": "binding_count_below_evidence_count"}
    visible_text = (
        reference["question"]
        + "\n"
        + reference["table_text"]
        + "\n"
        + "\n".join(item["text"] for item in reference["paragraphs"])
    ).casefold()
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            return {"status": "FAIL", "reason": "binding_not_object"}
        if set(binding) != {"evidence_ref", "row", "period", "role", "unit"}:
            return {"status": "FAIL", "reason": "binding_key_contract_mismatch"}
        ref = binding["evidence_ref"]
        if ref not in evidence_refs or ref in seen:
            return {"status": "FAIL", "reason": "binding_evidence_ref_mismatch"}
        seen.add(ref)
        row_match = re.fullmatch(r"TABLE:R(\d+)(?::C\d+)?", ref)
        if row_match:
            expected_row = int(row_match.group(1))
            if binding["row"] != expected_row:
                return {
                    "status": "FAIL",
                    "reason": "binding_row_mismatch",
                    "observed": binding["row"],
                    "expected": expected_row,
                }
        elif binding["row"] is not None:
            return {"status": "FAIL", "reason": "paragraph_binding_has_row"}
        for field in ("period", "role", "unit"):
            value = binding[field]
            if value is not None and str(value).casefold() not in visible_text:
                return {
                    "status": "FAIL",
                    "reason": f"binding_{field}_not_visible",
                    "observed": value,
                }
    if seen != set(evidence_refs):
        return {"status": "FAIL", "reason": "binding_coverage_incomplete"}
    return {"status": "PASS", "reason": "all_bindings_visible_and_consistent"}


def canonical_formula(program: Any) -> str | None:
    if not isinstance(program, str) or not program.strip():
        return None
    cleaned = program.replace(",", "").replace("$", "").strip()
    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError:
        return None

    def visit(node: ast.AST) -> str:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            return "N"
        if isinstance(node, ast.BinOp):
            return f"({visit(node.left)}{operator_symbol(node.op)}{visit(node.right)})"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            prefix = "-" if isinstance(node.op, ast.USub) else "+"
            return f"({prefix}{visit(node.operand)})"
        return "?"

    return visit(tree)


def operator_symbol(operator: ast.AST) -> str:
    return {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.Pow: "**",
    }.get(type(operator), "?")


def alternative_explanations(
    row: dict[str, Any],
    raw_score: dict[str, Any],
    semantic_score: dict[str, Any],
    interface: dict[str, Any],
    reference: dict[str, Any],
) -> list[str]:
    explanations: list[str] = []
    usage = row["usage"]
    if usage["output_tokens"] >= 512 and interface["candidate_found"] is False:
        explanations.append("output_budget_exhausted_before_contract")
    if interface["candidate_found"] and not interface["raw_strict_pass"]:
        explanations.append("non_contract_reasoning_prefix_before_json")
    if interface["status"] != "PASS":
        explanations.append(interface["reason"])
    layers = semantic_score.get("layers", {})
    if layers.get("numeric_unit", {}).get("status") == "FAIL":
        unit = layers["numeric_unit"].get("unit", {})
        if unit.get("status") == "FAIL" and "unit" in unit.get("reason", ""):
            explanations.append("reference_unit_conflict")
        explanations.append("numeric_or_unit_mismatch")
    if layers.get("evidence", {}).get("status") == "FAIL":
        explanations.append("visible_citation_support_mismatch")
    if layers.get("answer", {}).get("status") == "FAIL":
        explanations.append("answer_text_or_set_mismatch")
    if raw_score.get("status") == "STRICT_FAIL":
        explanations.append("raw_strict_format_failure")
    if reference.get("unit") in {"percent", "thousand"} and reference.get(
        "answer_type"
    ) in {"span", "multi-span", "count"}:
        explanations.append("frozen_reference_unit_may_conflict_with_visible_semantics")
    return sorted(set(explanations))


def category_flags(
    baseline_status: str,
    raw_score: dict[str, Any],
    semantic_score: dict[str, Any],
    interface: dict[str, Any],
    reconstruction: dict[str, Any] | None,
    payload: dict[str, Any] | None,
) -> dict[str, bool]:
    semantic_status = semantic_score.get("status")
    return {
        "complete_delivery": bool(
            interface["status"] == "PASS" and raw_score.get("status") != "STRICT_FAIL"
        ),
        "correct_repair": bool(
            baseline_status != "ACCEPT" and semantic_status == "ACCEPT"
        ),
        "damage": bool(
            baseline_status == "ACCEPT" and semantic_status != "ACCEPT"
        ),
        "strict_failure": bool(
            raw_score.get("status") == "STRICT_FAIL"
            or interface["status"] != "PASS"
        ),
        "reasonable_unknown": semantic_status == "REASONABLE_UNKNOWN",
        "unnecessary_refusal": bool(
            payload is not None
            and payload.get("unknown")
            and bool(reconstruction and reconstruction.get("reconstructible"))
        ),
        "pending": semantic_status == "PENDING_ADJUDICATION",
    }


def main() -> int:
    raw_rows = load_jsonl(RAW_PATH)
    panel = json.loads(PANEL_PATH.read_text(encoding="utf-8"))
    references = {row["question_uid"]: row for row in panel["references"]}
    baseline_rows = load_jsonl(BASELINE_ROWS_PATH)
    baselines = {row["question_uid"]: row for row in baseline_rows}
    raw_receipt = json.loads(RAW_RECEIPT_PATH.read_text(encoding="utf-8"))
    generation_receipt = json.loads(
        GENERATION_RECEIPT_PATH.read_text(encoding="utf-8")
    )
    fault_receipt = json.loads(INTERFACE_FAULT_PATH.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    output_rows = []
    interface_rows = []
    for row in raw_rows:
        reference = references[row["question_uid"]]
        visible = visible_context(reference)
        raw_score = v3.score_response(row["response_text"], reference, visible)
        objects = extract_json_objects(row["response_text"])
        arm = row["arm"]
        candidate = None
        candidate_kind = None
        if arm == "D":
            for item in objects:
                if set(item) == FINAL_KEYS:
                    candidate = item
                    candidate_kind = "direct_final"
                    break
        else:
            for item in objects:
                if set(item) == TYPED_KEYS | ({"bindings"} if arm == "M" else set()):
                    candidate = item
                    candidate_kind = "typed_envelope"
                    break
        final_payload = None
        interface = {
            "status": "FAIL",
            "reason": "no_complete_contract_candidate",
            "candidate_found": candidate is not None,
            "candidate_kind": candidate_kind,
            "raw_strict_pass": raw_score.get("status") != "STRICT_FAIL",
            "binding_validation": None,
            "calculator_executed": False,
        }
        if candidate is not None:
            if arm == "D":
                final_payload = candidate
                interface.update(
                    {
                        "status": "PASS",
                        "reason": "direct_final_contract_extracted",
                    }
                )
            else:
                final_payload, normalization = normalize_typed(
                    candidate, arm, reference, visible
                )
                interface.update(
                    {
                        "status": normalization["status"],
                        "reason": normalization["reason"],
                        "binding_validation": normalization.get("binding"),
                        "calculator_executed": normalization.get(
                            "calculator_executed", False
                        ),
                    }
                )
        if final_payload is None:
            semantic_score = raw_score
            semantic_text = row["response_text"]
        else:
            semantic_text = json.dumps(
                final_payload, ensure_ascii=False, sort_keys=True
            )
            semantic_score = v3.score_response(
                semantic_text, reference, visible
            )
        reconstruction = v2.reconstruct_expected_refs(reference, visible)
        numeric_status = semantic_score.get("layers", {}).get(
            "numeric_unit", {}
        ).get("numeric", {}).get("status", "UNAVAILABLE")
        evidence_status = semantic_score.get("layers", {}).get(
            "evidence", {}
        ).get("status", "UNAVAILABLE")
        if reference["answer_type"] != "arithmetic":
            formula_status = "NOT_APPLICABLE"
        elif arm == "D":
            formula_status = "NO_EXPLICIT_FORMULA"
        elif interface["status"] != "PASS":
            formula_status = "UNAVAILABLE_INTERFACE_FAILURE"
        else:
            expected_formula = canonical_formula(reference.get("program"))
            observed_formula = canonical_formula(candidate.get("program"))
            formula_status = (
                "PASS"
                if expected_formula is not None
                and observed_formula == expected_formula
                else "FAIL"
            )
        baseline = baselines[row["question_uid"]]
        baseline_status = baseline["score"]["status"]
        flags = category_flags(
            baseline_status,
            raw_score,
            semantic_score,
            interface,
            reconstruction,
            final_payload,
        )
        explanations = alternative_explanations(
            row, raw_score, semantic_score, interface, reference
        )
        output_row = {
            "schema": "word_new_family_diagnostic_row_v1",
            "physical_attempt_id": row["physical_attempt_id"],
            "logical_call_id": row["logical_call_id"],
            "arm": arm,
            "family_id": row["family_id"],
            "question_uid": row["question_uid"],
            "reference_answer_type": reference["answer_type"],
            "task_signature": panel["selection"]["task_signatures"].get(
                row["question_uid"]
            )
            if isinstance(panel.get("selection", {}).get("task_signatures"), dict)
            else reference.get("task_signature"),
            "baseline_status": baseline_status,
            "raw_strict_score": raw_score,
            "interface": interface,
            "semantic_score": semantic_score,
            "normalized_payload": final_payload,
            "numeric_correct": numeric_status == "PASS",
            "formula_status": formula_status,
            "visible_citation_support": {
                "PASS": "EXACT",
                "PENDING_ADJUDICATION": "BROAD_PENDING",
                "FAIL": "NONE_OR_MISMATCH",
            }.get(evidence_status, "UNAVAILABLE"),
            "categories": flags,
            "alternative_explanations": explanations,
            "usage": row["usage"],
        }
        output_rows.append(output_row)
        interface_rows.append(
            {
                "logical_call_id": row["logical_call_id"],
                "arm": arm,
                "question_uid": row["question_uid"],
                "status": interface["status"],
                "reason": interface["reason"],
                "candidate_found": interface["candidate_found"],
                "raw_strict_pass": interface["raw_strict_pass"],
                "calculator_executed": interface["calculator_executed"],
                "binding_validation": interface["binding_validation"],
            }
        )
    ROWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ROWS_PATH.open("w", encoding="utf-8") as handle:
        for row in output_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in output_rows:
        by_arm[row["arm"]].append(row)
    arm_summary = {}
    for arm, rows in sorted(by_arm.items()):
        arm_summary[arm] = {
            "rows": len(rows),
            "complete_delivery": sum(
                row["categories"]["complete_delivery"] for row in rows
            ),
            "correct_repair": sum(
                row["categories"]["correct_repair"] for row in rows
            ),
            "damage": sum(row["categories"]["damage"] for row in rows),
            "strict_failure": sum(
                row["categories"]["strict_failure"] for row in rows
            ),
            "reasonable_unknown": sum(
                row["categories"]["reasonable_unknown"] for row in rows
            ),
            "unnecessary_refusal": sum(
                row["categories"]["unnecessary_refusal"] for row in rows
            ),
            "pending": sum(row["categories"]["pending"] for row in rows),
            "semantic_status_counts": dict(
                Counter(row["semantic_score"]["status"] for row in rows)
            ),
            "numeric_correct": sum(row["numeric_correct"] for row in rows),
            "formula_status_counts": dict(
                Counter(row["formula_status"] for row in rows)
            ),
            "citation_support_counts": dict(
                Counter(row["visible_citation_support"] for row in rows)
            ),
            "interface_status_counts": dict(
                Counter(row["interface"]["status"] for row in rows)
            ),
            "raw_strict_status_counts": dict(
                Counter(row["raw_strict_score"]["status"] for row in rows)
            ),
            "persisted_input_tokens": sum(
                row["usage"]["input_tokens"] for row in rows
            ),
            "persisted_output_tokens": sum(
                row["usage"]["output_tokens"] for row in rows
            ),
        }
    family_rows = []
    for family_id in [reference["family_id"] for reference in panel["references"]]:
        rows = [row for row in output_rows if row["family_id"] == family_id]
        arm_rows = {row["arm"]: row for row in rows}
        t_signature = signature(arm_rows.get("T"))
        m_signature = signature(arm_rows.get("M"))
        family_rows.append(
            {
                "family_id": family_id,
                "question_uid": rows[0]["question_uid"],
                "task_signature": rows[0]["task_signature"],
                "arms": {arm: signature(row) for arm, row in sorted(arm_rows.items())},
                "T_matches_M": t_signature == m_signature,
                "M_repair_beyond_T": bool(
                    arm_rows.get("T")
                    and arm_rows.get("M")
                    and m_repair(arm_rows["T"], arm_rows["M"])
                ),
                "alternative_explanations": sorted(
                    {
                        explanation
                        for row in rows
                        for explanation in row["alternative_explanations"]
                    }
                ),
            }
        )
    write_json(FAMILY_PATH, {"families": family_rows})
    t_m_match = all(row["T_matches_M"] for row in family_rows)
    m_repairs = [row["family_id"] for row in family_rows if row["M_repair_beyond_T"]]
    persisted_tokens = raw_receipt["actual_input_plus_output_tokens"]
    uncertain_tokens = fault_receipt["consumed_token_upper_bound"]
    summary = {
        "schema": "word_new_family_diagnostic_summary_v1",
        "status": "COMPLETE_RESCORE_NO_MODEL_CALL",
        "source_identity_label": panel["source_identity_label"],
        "claim_boundary": panel["claim_boundary"],
        "rows": len(output_rows),
        "families": len(family_rows),
        "arm_summary": arm_summary,
        "T_matches_M_all_families": t_m_match,
        "M_stop_decision": (
            "STOP_M_NO_DIFFERENTIAL_MECHANISM"
            if t_m_match and not m_repairs
            else "M_DIFFERENCE_REQUIRES_REVIEW"
        ),
        "M_repair_families": m_repairs,
        "confirmation_card_prepared": bool(m_repairs),
        "confirmation_run": False,
        "all_arms_fail": all(
            arm_summary[arm]["semantic_status_counts"].get("ACCEPT", 0) == 0
            for arm in ("D", "T", "M")
        ),
        "adapter_training": "NOT_RUN",
        "cost": {
            "physical_reservations": generation_receipt["primary_attempts_completed"]
            + fault_receipt["fault_count"],
            "persisted_raw_attempts": raw_receipt["raw_rows"],
            "real_model_generate_calls": fault_receipt[
                "real_model_generate_calls"
            ]
            + raw_receipt["raw_rows"],
            "preserved_pre_raw_failures": fault_receipt["fault_count"],
            "persisted_actual_input_tokens": raw_receipt["actual_input_tokens"],
            "persisted_actual_output_tokens": raw_receipt["actual_output_tokens"],
            "persisted_actual_input_plus_output_tokens": persisted_tokens,
            "uncertain_consumed_input_plus_output_tokens": uncertain_tokens,
            "ledger_consumed_input_plus_output_tokens": persisted_tokens
            + uncertain_tokens,
            "token_cap": 240000,
            "reserve_attempts_used": generation_receipt["reserve_attempts_used"],
            "reserve_attempts_available": generation_receipt[
                "reserve_attempts_available"
            ],
            "retries_with_persisted_raw": generation_receipt["bounded_retries"],
            "generation_wall_seconds_last_process": generation_receipt[
                "wall_seconds_this_process"
            ],
            "external_harness_calls": 0,
            "service_or_endpoint_calls": 0,
            "judge_calls": 0,
            "paid_api_calls": 0,
            "production_calls": 0,
            "training_runs": 0,
        },
        "unknowns": [
            "Historical base-model pretraining exposure is unauditable.",
            "One discarded model response has unknown actual token usage; its reservation upper bound is consumed.",
            "DOCX/PDF visual acceptance and Loop C acceptance are outside A.",
            "Frozen reference units may conflict with visible semantics for several non-arithmetic rows.",
        ],
        "source_hashes": {
            str(path.relative_to(REPO)): sha256(path)
            for path in [
                RAW_PATH,
                RAW_RECEIPT_PATH,
                GENERATION_RECEIPT_PATH,
                INTERFACE_FAULT_PATH,
                PANEL_PATH,
                BASELINE_PATH,
                BASELINE_ROWS_PATH,
                FREEZE_PATH,
                Path(v3.__file__),
                Path(v2.__file__),
            ]
        },
    }
    write_json(SUMMARY_PATH, summary)
    interface_receipt = {
        "schema": "word_new_family_interface_normalization_receipt_v1",
        "status": "COMPLETE",
        "model_loaded": False,
        "rows": len(interface_rows),
        "status_counts": dict(
            Counter(row["status"] for row in interface_rows)
        ),
        "raw_strict_pass_count": sum(
            row["raw_strict_pass"] for row in interface_rows
        ),
        "calculator_executions": sum(
            row["calculator_executed"] for row in interface_rows
        ),
        "binding_validations_passed": sum(
            bool(row["binding_validation"])
            and row["binding_validation"].get("status") == "PASS"
            for row in interface_rows
        ),
        "rows_detail": interface_rows,
        "source_hashes": {
            str(ROWS_PATH.relative_to(REPO)): sha256(ROWS_PATH),
        },
    }
    write_json(INTERFACE_PATH, interface_receipt)
    COMPARISON_PATH.write_text(
        "# Mechanism Comparison\n\n"
        + f"- T matches M on every frozen UID/family vector: `{t_m_match}`.\n"
        + f"- M repair families beyond T: `{m_repairs or 'none'}`.\n"
        + f"- Stop decision: `{summary['M_stop_decision']}`.\n"
        + "- Formatting-only or abstention-only differences are not counted as repairs.\n"
        + "- Confirmation was not run; no adapter was trained.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "rows": len(output_rows),
                "arm_summary": arm_summary,
                "T_matches_M": t_m_match,
                "M_stop_decision": summary["M_stop_decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def signature(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "complete_delivery": row["categories"]["complete_delivery"],
        "semantic_status": row["semantic_score"]["status"],
        "numeric_correct": row["numeric_correct"],
        "formula_status": row["formula_status"],
        "visible_citation_support": row["visible_citation_support"],
        "interface_status": row["interface"]["status"],
    }


def m_repair(t_row: dict[str, Any], m_row: dict[str, Any]) -> bool:
    if not m_row["categories"]["complete_delivery"]:
        return False
    if m_row["semantic_score"]["status"] == "REASONABLE_UNKNOWN":
        return False
    t_status = t_row["semantic_score"]["status"]
    m_status = m_row["semantic_score"]["status"]
    status_improvement = (
        m_status == "ACCEPT"
        and t_status in {"REJECT", "STRICT_FAIL", "PENDING_ADJUDICATION"}
    )
    evidence_improvement = (
        m_row["visible_citation_support"] == "EXACT"
        and t_row["visible_citation_support"] != "EXACT"
    )
    numeric_improvement = m_row["numeric_correct"] and not t_row["numeric_correct"]
    return bool(
        status_improvement
        and (evidence_improvement or numeric_improvement)
        and m_row["formula_status"] != "UNAVAILABLE_INTERFACE_FAILURE"
    )


if __name__ == "__main__":
    raise SystemExit(main())
