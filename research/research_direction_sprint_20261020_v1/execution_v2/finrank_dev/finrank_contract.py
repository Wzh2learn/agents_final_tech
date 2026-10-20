#!/usr/bin/env python3
"""Deterministic FinRank evidence tool contract and development scoring."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
EXECUTION_V2 = PACKAGE.parent
SPRINT_ROOT = EXECUTION_V2.parent
PROJECT_ROOT = SPRINT_ROOT.parent.parent
EXECUTION_V1 = SPRINT_ROOT / "execution_v1"
SOURCE_DRAFT = EXECUTION_V1 / "experience_scope" / "SCOPE_TASK_DRAFT.json"
ADJUDICATION = (
    EXECUTION_V1
    / "ai_semantic_adjudication_v1"
    / "ADJUDICATION.json"
)
SHARED_LEDGER = EXECUTION_V1 / "RESEARCH_GENERATION_LEDGER.json"
RUNTIME_SOURCE = (
    PROJECT_ROOT
    / "research"
    / "tatqa_wp0_2026"
    / "history_collection_execution_v1"
    / "RUNTIME_IDENTITY_SNAPSHOT.json"
)

FIRST_SEVEN = (
    "ESD_001",
    "ESD_002",
    "ESD_003",
    "ESD_004",
    "ESD_006",
    "ESD_010",
    "ESD_012",
)
REQUEST_TOKEN_RESERVE = 10240
REQUEST_CAP = 192
TOKEN_CAP = 2_000_000

PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["experience_actions", "evidence_candidate_ids"],
    "properties": {
        "experience_actions": {
            "type": "array",
            "maxItems": 0,
            "items": {
                "type": "object",
                "required": ["experience_id", "decision"],
                "properties": {
                    "experience_id": {"type": "string"},
                    "decision": {"enum": ["APPLY", "SKIP", "ABSTAIN"]},
                },
                "additionalProperties": False,
            },
        },
        "evidence_candidate_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "uniqueItems": True,
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

LOOKUP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["candidate_ids"],
    "properties": {
        "candidate_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "uniqueItems": True,
            "items": {"type": "string"},
        }
    },
    "additionalProperties": False,
}

LOOKUP_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["tool_status", "evidence"],
    "properties": {
        "tool_status": {"enum": ["OK", "INVALID_ARGUMENT"]},
        "error": {"type": ["string", "null"]},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "candidate_id",
                    "text",
                    "page_number",
                    "visible_source_scope",
                ],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "text": {"type": "string"},
                    "page_number": {"type": ["string", "null"]},
                    "visible_source_scope": {"type": "object"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

CONSUME_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["answer_status", "facts", "used_candidate_ids"],
    "properties": {
        "answer_status": {"enum": ["ANSWER", "UNKNOWN", "REFUSE"]},
        "facts": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "required": ["label", "value", "unit", "period"],
                "properties": {
                    "label": {"type": "string", "minLength": 1, "maxLength": 160},
                    "value": {"type": ["number", "string"]},
                    "unit": {"type": ["string", "null"]},
                    "period": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
        },
        "used_candidate_ids": {
            "type": "array",
            "maxItems": 8,
            "uniqueItems": True,
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

ALL_SCHEMAS = {
    "plan": PLAN_SCHEMA,
    "evidence_lookup_input": LOOKUP_SCHEMA,
    "evidence_lookup_output": LOOKUP_OUTPUT_SCHEMA,
    "consume": CONSUME_SCHEMA,
}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def strict_json_object(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise ValueError("model_content_must_be_string")
    if len(text.encode("utf-8")) > 65536:
        raise ValueError("model_content_too_large")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model_json_invalid:{exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("model_json_must_be_object")
    return value


def normalize_text(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).split())


def normalized_tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalize_text(value).lower()))


def parse_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
        return result if math.isfinite(result) else None
    text = normalize_text(value).replace(",", "")
    text = re.sub(r"[−–—－]", "-", text)
    negative_parentheses = text.startswith("(") and text.endswith(")")
    if negative_parentheses:
        text = text[1:-1]
    match = re.fullmatch(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    result = float(text)
    return -result if negative_parentheses and result > 0 else result


def exact_keys(
    value: Any,
    expected: set[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}_must_be_object")
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{label}_keys_invalid missing={sorted(expected - actual)} "
            f"unknown={sorted(actual - expected)}"
        )
    return value


def validate_plan(value: Any) -> dict[str, Any]:
    value = exact_keys(
        value,
        {"experience_actions", "evidence_candidate_ids"},
        "plan",
    )
    if value["experience_actions"] != []:
        raise ValueError("history_actions_require_history_card")
    ids = value["evidence_candidate_ids"]
    if not isinstance(ids, list) or not 1 <= len(ids) <= 8:
        raise ValueError("plan_candidate_count_invalid")
    if any(not isinstance(item, str) or not item for item in ids):
        raise ValueError("plan_candidate_id_invalid")
    if len(ids) != len(set(ids)):
        raise ValueError("plan_duplicate_candidate_id")
    return value


def validate_consume(value: Any) -> dict[str, Any]:
    value = exact_keys(
        value,
        {"answer_status", "facts", "used_candidate_ids"},
        "consume",
    )
    status = value["answer_status"]
    if status not in {"ANSWER", "UNKNOWN", "REFUSE"}:
        raise ValueError("consume_status_invalid")
    facts = value["facts"]
    used = value["used_candidate_ids"]
    if not isinstance(facts, list) or len(facts) > 8:
        raise ValueError("consume_facts_invalid")
    if not isinstance(used, list) or len(used) > 8:
        raise ValueError("consume_used_ids_invalid")
    if any(not isinstance(item, str) or not item for item in used):
        raise ValueError("consume_used_id_invalid")
    if len(used) != len(set(used)):
        raise ValueError("consume_duplicate_used_id")
    for fact in facts:
        fact = exact_keys(
            fact,
            {"label", "value", "unit", "period"},
            "consume_fact",
        )
        if not isinstance(fact["label"], str) or not fact["label"].strip():
            raise ValueError("consume_fact_label_invalid")
        if isinstance(fact["value"], bool) or not isinstance(
            fact["value"], (int, float, str)
        ):
            raise ValueError("consume_fact_value_invalid")
        for key in ("unit", "period"):
            if fact[key] is not None and not isinstance(fact[key], str):
                raise ValueError(f"consume_fact_{key}_invalid")
    if status != "ANSWER" and facts:
        raise ValueError("non_answer_facts_must_be_empty")
    if status == "ANSWER" and not facts:
        raise ValueError("answer_requires_facts")
    if status == "ANSWER" and not used:
        raise ValueError("answer_requires_used_candidate_ids")
    return value


def validate_consumed_evidence(
    consume: dict[str, Any],
    tool_result: dict[str, Any],
) -> None:
    returned_ids = {
        item["candidate_id"]
        for item in tool_result.get("evidence", [])
        if isinstance(item, dict)
    }
    absent = sorted(set(consume["used_candidate_ids"]) - returned_ids)
    if absent:
        raise ValueError(f"consume_cites_absent_evidence:{absent}")


def evidence_lookup(
    task: dict[str, Any],
    arguments: Any,
    all_tasks: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    try:
        arguments = exact_keys(arguments, {"candidate_ids"}, "lookup_input")
        ids = arguments["candidate_ids"]
        if not isinstance(ids, list) or not 1 <= len(ids) <= 8:
            raise ValueError("lookup_count_out_of_range")
        if any(not isinstance(item, str) or not item for item in ids):
            raise ValueError("lookup_candidate_id_invalid")
        if len(ids) != len(set(ids)):
            raise ValueError("lookup_duplicate_candidate_id")
        candidates = {
            item["candidate_id"]: item for item in task["actor_view"]["candidates"]
        }
        global_ids = {
            item["candidate_id"]
            for other in all_tasks.values()
            for item in other["actor_view"]["candidates"]
        }
        for candidate_id in ids:
            if candidate_id not in candidates:
                code = (
                    "cross_task_candidate_id"
                    if candidate_id in global_ids
                    else "unknown_candidate_id"
                )
                raise ValueError(code)
        evidence = [
            {
                "candidate_id": candidate_id,
                "text": candidates[candidate_id]["text"],
                "page_number": candidates[candidate_id].get("page_number"),
                "visible_source_scope": candidates[candidate_id][
                    "visible_source_scope"
                ],
            }
            for candidate_id in ids
        ]
        return {"tool_status": "OK", "evidence": evidence}
    except ValueError as exc:
        return {
            "tool_status": "INVALID_ARGUMENT",
            "evidence": [],
            "error": str(exc),
        }


def evidence_sufficiency(
    selected: list[str],
    reference: dict[str, Any],
) -> dict[str, Any]:
    selected_set = set(selected)
    minimal_sets = {
        tuple(sorted(items))
        for items in reference["minimal_sufficient_sets"]
    }
    sufficient_sets = sorted(
        [list(items) for items in minimal_sets if set(items) <= selected_set],
        key=lambda items: (len(items), items),
    )
    allowed = set(reference["optional_redundant"])
    for items in reference["minimal_sufficient_sets"]:
        allowed.update(items)
    return {
        "sufficient": bool(sufficient_sets),
        "matched_minimal_sets": sufficient_sets,
        "scope_precision": selected_set <= allowed,
        "unsupported_selected_ids": sorted(selected_set - allowed),
        "optional_redundant_used": sorted(
            selected_set & set(reference["optional_redundant"])
        ),
    }


def _unit_matches(actual: Any, expected: str) -> bool:
    if expected == "NONE":
        return actual in (None, "", "none", "dimensionless")
    actual_text = normalize_text(actual).lower()
    actual_tokens = normalized_tokens(actual)
    expected_tokens = normalized_tokens(expected)
    if "percent" in expected_tokens or "%" in normalize_text(expected):
        return actual_text in {"%", "percent", "percentage"} or bool(
            {"percent", "percentage"} & actual_tokens
        )
    if "billion" in expected_tokens:
        return "billion" in actual_tokens
    if "million" in expected_tokens:
        return "million" in actual_tokens
    return bool(expected_tokens & actual_tokens)


def _period_matches(actual: Any, expected: str) -> bool:
    if expected == "NONE":
        return True
    actual_text = normalize_text(actual).lower()
    expected_tokens = normalized_tokens(expected)
    if expected == "FY2024":
        return "2024" in actual_text and not re.search(
            r"(three months|march 31|q1)", actual_text
        )
    if expected == "2024-12-31":
        return "2024" in actual_text
    if expected == "2022-2024":
        return all(year in actual_text for year in ("2022", "2023", "2024"))
    return bool(expected_tokens & normalized_tokens(actual_text))


def _label_matches(actual: Any, patterns: list[str]) -> bool:
    actual_tokens = normalized_tokens(actual)
    return any(
        normalized_tokens(pattern) <= actual_tokens
        or normalize_text(pattern).lower() in normalize_text(actual).lower()
        for pattern in patterns
    )


def _fact_value_matches(
    fact: dict[str, Any],
    atom: dict[str, Any],
) -> bool:
    actual = parse_number(fact["value"])
    expected = atom["value"]
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return actual is not None and math.isclose(
            actual,
            float(expected),
            rel_tol=0,
            abs_tol=float(atom.get("tolerance", 1e-6)),
        )
    actual_text = normalize_text(fact["value"]).lower()
    expected_text = normalize_text(expected).lower()
    expected_tokens = normalized_tokens(expected_text)
    actual_tokens = normalized_tokens(actual_text)
    return (
        expected_text in actual_text
        or expected_tokens <= actual_tokens
        or bool(atom.get("value_synonyms")) and any(
            normalize_text(synonym).lower() in actual_text
            for synonym in atom["value_synonyms"]
        )
    )


def answer_reference_match(
    consume: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    if consume["answer_status"] != "ANSWER":
        return {
            "match": False,
            "matched_atoms": [],
            "missing_atoms": [
                atom["name"] for atom in reference["answer_atoms"]
            ],
        }
    matches: list[str] = []
    missing: list[str] = []
    for atom in reference["answer_atoms"]:
        found = any(
            _label_matches(fact["label"], atom["label_patterns"])
            and _fact_value_matches(fact, atom)
            and _unit_matches(fact["unit"], atom.get("unit", "NONE"))
            and _period_matches(fact["period"], atom.get("period", "NONE"))
            for fact in consume["facts"]
        )
        (matches if found else missing).append(atom["name"])
    return {
        "match": not missing,
        "matched_atoms": matches,
        "missing_atoms": missing,
    }


def _numeric_values_in_text(text: str) -> list[float]:
    values: list[float] = []
    for raw in re.findall(r"(?<![A-Za-z0-9])\(?-?\d[\d,]*(?:\.\d+)?\)?", text):
        parsed = parse_number(raw)
        if parsed is not None:
            values.append(parsed)
    return values


def _literal_fact_supported(fact: dict[str, Any], evidence_text: str) -> bool:
    number = parse_number(fact["value"])
    if number is not None:
        return any(
            math.isclose(
                number,
                value,
                rel_tol=0,
                abs_tol=0.011,
            )
            for value in _numeric_values_in_text(evidence_text)
        )
    fact_text = normalize_text(fact["value"]).lower()
    evidence_normalized = normalize_text(evidence_text).lower()
    return bool(fact_text) and fact_text in evidence_normalized


def _matching_reference_atom(
    fact: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any] | None:
    atoms = list(reference.get("answer_atoms", [])) + list(
        reference.get("operand_facts", [])
    )
    for atom in atoms:
        if (
            _label_matches(fact["label"], atom["label_patterns"])
            and _fact_value_matches(fact, atom)
            and _unit_matches(fact["unit"], atom.get("unit", "NONE"))
            and _period_matches(fact["period"], atom.get("period", "NONE"))
        ):
            return atom
    return None


def _explicit_derivation_supported(
    fact: dict[str, Any],
    atom: dict[str, Any],
    derivation: dict[str, Any],
    evidence_text: str,
    reference: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    operand_atoms = derivation.get("operand_atoms")
    operand_values = derivation.get("operand_values")
    formula = derivation.get("formula")
    operator = derivation.get("operator")
    if (
        derivation.get("target_atom") != atom["name"]
        or not isinstance(operand_atoms, list)
        or not operand_atoms
        or not isinstance(operand_values, dict)
        or set(operand_atoms) != set(operand_values)
        or not isinstance(formula, str)
        or not formula.strip()
        or not isinstance(operator, str)
    ):
        return False, {
            "target_atom": atom["name"],
            "reason": "derivation_contract_invalid",
        }
    reference_atoms = {
        item["name"]: item
        for item in list(reference.get("answer_atoms", []))
        + list(reference.get("operand_facts", []))
    }
    evidence_values = _numeric_values_in_text(evidence_text)
    resolved: dict[str, float] = {}
    for operand_atom in operand_atoms:
        expected = operand_values[operand_atom]
        reference_atom = reference_atoms.get(operand_atom)
        if (
            reference_atom is None
            or parse_number(reference_atom.get("value")) is None
            or not math.isclose(
                parse_number(expected),
                parse_number(reference_atom.get("value")),
                rel_tol=0,
                abs_tol=1e-9,
            )
        ):
            return False, {
                "target_atom": atom["name"],
                "reason": "operand_atom_contract_invalid",
                "operand_atom": operand_atom,
            }
        expected_number = parse_number(expected)
        if not any(
            math.isclose(
                expected_number,
                value,
                rel_tol=0,
                abs_tol=0.011,
            )
            for value in evidence_values
        ):
            return False, {
                "target_atom": atom["name"],
                "reason": "operand_value_absent_from_returned_evidence",
                "operand_atom": operand_atom,
                "operand_value": expected,
            }
        resolved[operand_atom] = expected_number
    values = [resolved[item] for item in operand_atoms]
    if operator == "SUBTRACT" and len(values) == 2:
        calculated = values[0] - values[1]
    elif (
        operator == "MARGIN_PERCENT_FROM_REVENUE_AND_COST"
        and len(values) == 2
        and values[0] != 0
    ):
        calculated = (values[0] - values[1]) / values[0] * 100
    else:
        return False, {
            "target_atom": atom["name"],
            "reason": "derivation_operator_invalid",
            "operator": operator,
        }
    target = parse_number(fact["value"])
    supported = target is not None and math.isclose(
        target,
        calculated,
        rel_tol=0,
        abs_tol=max(float(atom.get("tolerance", 1e-6)), 0.011),
    )
    return supported, {
        "target_atom": atom["name"],
        "operator": operator,
        "formula": formula,
        "operand_values": resolved,
        "calculated": calculated,
        "target": target,
    }


def answer_tool_consistency(
    consume: dict[str, Any],
    tool_result: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    returned_ids = {
        item["candidate_id"]
        for item in tool_result.get("evidence", [])
        if isinstance(item, dict)
    }
    cited_absent = sorted(set(consume["used_candidate_ids"]) - returned_ids)
    evidence_text = "\n".join(
        str(item.get("text", ""))
        for item in tool_result.get("evidence", [])
        if isinstance(item, dict)
    )
    derivations = {
        item["target_atom"]: item
        for item in reference.get("derivations", [])
    }
    unsupported_facts: list[dict[str, Any]] = []
    unsupported_values: list[Any] = []
    derivation_checks: list[dict[str, Any]] = []
    for fact in consume["facts"]:
        atom = _matching_reference_atom(fact, reference)
        derivation = (
            derivations.get(atom["name"]) if atom is not None else None
        )
        if derivation is not None:
            supported, detail = _explicit_derivation_supported(
                fact,
                atom,
                derivation,
                evidence_text,
                reference,
            )
            mode = "EXPLICIT_REFERENCE_DERIVATION"
            derivation_checks.append(detail)
        else:
            supported = _literal_fact_supported(fact, evidence_text)
            mode = "LITERAL_EVIDENCE"
            detail = {"fact_label": fact["label"], "value": fact["value"]}
        if not supported:
            unsupported_facts.append(
                {
                    "label": fact["label"],
                    "value": fact["value"],
                    "mode": mode,
                    "detail": detail,
                }
            )
            if parse_number(fact["value"]) is not None:
                unsupported_values.append(fact["value"])
    return {
        "consistent": not cited_absent and not unsupported_facts,
        "cited_absent_ids": cited_absent,
        "unsupported_numeric_values": unsupported_values,
        "unsupported_facts": unsupported_facts,
        "derivation_checks": derivation_checks,
    }


def classify_result(
    task_id: str,
    plan: dict[str, Any],
    tool_result: dict[str, Any],
    consume: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    plan_valid = isinstance(plan, dict) and not plan.get("error")
    tool_success = tool_result.get("tool_status") == "OK"
    consume_valid = isinstance(consume, dict) and not consume.get("error")
    sufficiency = evidence_sufficiency(
        consume.get("used_candidate_ids", []) if consume_valid else [],
        reference,
    )
    reference_match = (
        answer_reference_match(consume, reference) if consume_valid else {
            "match": False,
            "matched_atoms": [],
            "missing_atoms": [item["name"] for item in reference["answer_atoms"]],
        }
    )
    consistency = answer_tool_consistency(consume, tool_result, reference)
    success = (
        plan_valid
        and tool_success
        and consume_valid
        and sufficiency["sufficient"]
        and sufficiency["scope_precision"]
        and reference_match["match"]
        and consistency["consistent"]
    )
    return {
        "task_id": task_id,
        "source_cluster_id": reference["source_cluster_id"],
        "plan_contract_valid": plan_valid,
        "tool_execution_success": tool_success,
        "consume_contract_valid": consume_valid,
        "evidence_sufficiency": sufficiency,
        "answer_reference_match": reference_match,
        "answer_tool_consistency": consistency,
        "outcome": "SUCCESS" if success else "NON_SUCCESS",
        "error_class": (
            None
            if success
            else (
                "ENGINEERING_SCHEMA_OR_TOOL"
                if not (plan_valid and tool_success and consume_valid)
                else "SEMANTIC_SELECTION_OR_ANSWER"
            )
        ),
        "plan": plan,
        "tool_result": tool_result,
        "consume": consume,
    }


def render_messages(
    stage: str,
    task: dict[str, Any],
    tool_result: dict[str, Any] | None,
) -> list[dict[str, str]]:
    schemas_json = json.dumps(ALL_SCHEMAS, ensure_ascii=False, sort_keys=True)
    task_json = json.dumps(
        {
            "task_id": task["task_id"],
            "instruction": task["actor_view"]["instruction"],
            "question": task["actor_view"]["question"],
            "question_scope": task["actor_view"]["question_scope"],
            "plan_time_visibility": "FULL_VISIBLE_CANDIDATES_AT_PLAN",
            "candidate_visibility_sha256": candidate_visibility_sha256(task),
            "candidates": plan_visible_candidates(task),
            "experience_context": None,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    common = (
        "You are an evidence-selection and answer actor. Return one JSON object "
        "only. The complete schemas are authoritative and shown here verbatim: "
        f"{schemas_json}. All candidate records in the task are visible before "
        "planning. evidence_lookup still returns the selected original records "
        "and consume must rely on that actual return. Never infer hidden "
        "passage IDs, reference answers, adjudication notes or future labels. "
        "Return minified JSON only, with no whitespace outside string values. "
        "Do not pretty-print, indent, use Markdown fences, or add commentary."
    )
    if stage == "plan":
        user = (
            f"{common}\nTASK_AND_VISIBLE_EVIDENCE={task_json}\n"
            "Choose candidate IDs for evidence_lookup. No history card is "
            "present, so experience_actions must be []. Return the object "
            "described by schema key `plan` directly, without a `plan` wrapper. "
            "Its top-level keys must be exactly `experience_actions` and "
            "`evidence_candidate_ids`."
        )
    elif stage == "consume":
        if tool_result is None:
            raise ValueError("consume_requires_tool_result")
        tool_json = json.dumps(tool_result, ensure_ascii=False, sort_keys=True)
        user = (
            f"{common}\nTASK_AND_VISIBLE_EVIDENCE={task_json}\n"
            f"ACTUAL_TOOL_RESULT={tool_json}\n"
            "Consume only evidence present in ACTUAL_TOOL_RESULT. Cite only "
            "returned candidate IDs. Return the object described by schema key "
            "`consume` directly, without a `consume` wrapper. Its top-level keys "
            "must be exactly `answer_status`, `facts`, and "
            "`used_candidate_ids`. If evidence is insufficient, return UNKNOWN "
            "with facts []."
        )
    else:
        raise ValueError("stage_invalid")
    return [
        {
            "role": "system",
            "content": (
                "Follow the visible JSON contract exactly. Do not reveal or "
                "invent hidden evaluation material. Output raw minified JSON "
                "only, with no whitespace outside string values. Do not "
                "pretty-print, indent, use Markdown fences, or add commentary."
            ),
        },
        {"role": "user", "content": user},
    ]


def request_payload(
    runtime_identity: dict[str, Any],
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    identity = runtime_identity["identity"]
    return {
        "model": identity["model"]["model_id"],
        "messages": messages,
        "chat_template_kwargs": identity["chat_template_kwargs"],
        **identity["generation"],
    }


def parse_chat_response(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("status_code") != 200:
        raise ValueError("chat_http_status_invalid")
    body = strict_json_object(response["body_text"])
    choices = body.get("choices")
    usage = body.get("usage")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("chat_choices_invalid")
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("chat_message_invalid")
    if not isinstance(usage, dict):
        raise ValueError("chat_usage_invalid")
    total = usage.get("total_tokens")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError("chat_usage_total_invalid")
    return {"content": message["content"], "usage": usage}


class HttpChatAdapter:
    def __init__(self, base_url: str, timeout_seconds: int):
        if not base_url.startswith(("http://127.0.0.1:", "http://localhost:")):
            raise ValueError("base_url_must_be_local")
        self.url = base_url.rstrip("/") + "/v1/chat/completions"
        self.timeout_seconds = timeout_seconds

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                raw = response.read(65537)
                result = {
                    "status_code": int(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "body_text": raw.decode("utf-8"),
                }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"adapter_request_failed:{type(exc).__name__}") from exc
        if len(raw) > 65536:
            raise RuntimeError("adapter_response_too_large")
        if not result["content_type"].startswith("application/json"):
            raise RuntimeError("adapter_response_content_type_invalid")
        return result


class ImmutableRawStore:
    def __init__(self, root: Path):
        self.root = root
        if root.exists():
            raise FileExistsError(f"raw_root_already_exists:{root}")
        root.mkdir(parents=True)

    def begin_request(
        self,
        logical_id: str,
        payload: dict[str, Any],
    ) -> tuple[str, Path]:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", logical_id)[:120]
        request_id = f"{safe}_{sha256_text(payload)[:12]}"
        request_root = self.root / request_id
        request_root.mkdir()
        write_json(request_root / "request.json", payload)
        return request_id, request_root

    @staticmethod
    def persist_response(request_root: Path, response: dict[str, Any]) -> None:
        path = request_root / "response.json"
        if path.exists():
            raise FileExistsError(f"response_already_exists:{path}")
        write_json(path, response)

    @staticmethod
    def mark_crash(request_root: Path, error: str) -> None:
        path = request_root / "crash.json"
        if path.exists():
            raise FileExistsError(f"crash_already_exists:{path}")
        write_json(path, {"error": error, "at_utc": utc_now()})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SharedGenerationLedger:
    """Two-phase request accounting with a process lock."""

    def __init__(self, path: Path):
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")

    def _locked(self):
        class Context:
            def __enter__(self_inner):
                deadline = time.monotonic() + 20
                while True:
                    try:
                        self_inner.fd = os.open(
                            self.lock_path,
                            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                        )
                        os.write(self_inner.fd, str(os.getpid()).encode("ascii"))
                        return self_inner
                    except FileExistsError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("shared_ledger_lock_timeout")
                        time.sleep(0.05)

            def __exit__(self_inner, exc_type, exc, traceback):
                os.close(self_inner.fd)
                self.lock_path.unlink(missing_ok=True)

        return Context()

    def reserve(
        self,
        run_id: str,
        request_key: str,
        payload_sha256: str,
    ) -> str:
        with self._locked():
            ledger = load_object(self.path)
            budget = ledger["new_generation_budget"]
            if budget["requests_used"] + 1 > budget["request_cap"]:
                raise PermissionError("shared_request_cap_exceeded")
            if (
                budget["accounting_tokens_used"] + REQUEST_TOKEN_RESERVE
                > budget["token_cap"]
            ):
                raise PermissionError("shared_token_cap_exceeded")
            record_id = f"{run_id}:{request_key}:{sha256_text(utc_now())[:10]}"
            record = {
                "record_id": record_id,
                "run_id": run_id,
                "request_key": request_key,
                "payload_sha256": payload_sha256,
                "status": "STARTED",
                "started_at_utc": utc_now(),
                "accounting_tokens": REQUEST_TOKEN_RESERVE,
                "usage_total_tokens": None,
            }
            budget["requests_used"] += 1
            budget["accounting_tokens_used"] += REQUEST_TOKEN_RESERVE
            ledger.setdefault("request_records", []).append(record)
            write_json(self.path, ledger)
            return record_id

    def settle(
        self,
        record_id: str,
        status: str,
        usage_total_tokens: int | None,
        error: str | None = None,
    ) -> None:
        if usage_total_tokens is not None and usage_total_tokens < 0:
            raise ValueError("usage_total_tokens_invalid")
        with self._locked():
            ledger = load_object(self.path)
            records = ledger.get("request_records", [])
            matches = [item for item in records if item["record_id"] == record_id]
            if len(matches) != 1:
                raise ValueError("ledger_record_not_found")
            record = matches[0]
            if record["status"] != "STARTED":
                raise ValueError("ledger_record_already_settled")
            old_tokens = int(record["accounting_tokens"])
            new_tokens = (
                usage_total_tokens
                if status == "OK" and usage_total_tokens is not None
                else REQUEST_TOKEN_RESERVE
            )
            record["status"] = status
            record["settled_at_utc"] = utc_now()
            record["usage_total_tokens"] = usage_total_tokens
            record["accounting_tokens"] = new_tokens
            record["error"] = error
            budget = ledger["new_generation_budget"]
            budget["accounting_tokens_used"] += new_tokens - old_tokens
            write_json(self.path, ledger)


def validate_reference_separation(
    actor_task: dict[str, Any],
    messages: list[dict[str, str]],
) -> None:
    banned_keys = {
        "reference",
        "canonical_answer",
        "answer_atoms",
        "minimal_sufficient_sets",
        "optional_redundant",
        "anchors",
        "note",
        "repair",
        "source_passage_ids",
        "hidden_reference",
    }

    def scan(value: Any) -> None:
        if isinstance(value, dict):
            unknown = banned_keys & set(value)
            if unknown:
                raise ValueError(f"reference_key_leak:{sorted(unknown)}")
            for item in value.values():
                scan(item)
        elif isinstance(value, list):
            for item in value:
                scan(item)

    scan(actor_task)
    scan(messages)
    prompt = json.dumps(messages, ensure_ascii=False)
    for token in ("minimal_sufficient_sets", "canonical_answer", "hidden_reference"):
        if token in prompt:
            raise ValueError(f"reference_token_leak:{token}")


def strong_rule_plan(task: dict[str, Any]) -> dict[str, Any]:
    question_tokens = normalized_tokens(task["actor_view"]["question"])
    question_tokens -= {
        "what",
        "were",
        "was",
        "the",
        "and",
        "for",
        "in",
        "of",
        "to",
        "how",
        "which",
        "does",
        "during",
        "year",
        "ended",
    }
    target_ticker = task["actor_view"]["question_scope"]["entity"]["target_ticker"]
    requested_years = {
        str(item)
        for item in task["actor_view"]["question_scope"]["requested_period"][
            "explicit_years"
        ]
    }
    scored: list[tuple[float, str, bool]] = []
    visible_candidates = plan_visible_candidates(task)
    if sha256_text(visible_candidates) != candidate_visibility_sha256(task):
        raise RuntimeError("strong_rule_visibility_fingerprint_mismatch")
    for candidate in visible_candidates:
        text = candidate["text"]
        text_tokens = normalized_tokens(text)
        lexical = len(question_tokens & text_tokens) / max(len(question_tokens), 1)
        entity = 1.0 if candidate["visible_source_scope"]["ticker"] == target_ticker else -0.8
        text_years = set(re.findall(r"\b20\d{2}\b", text))
        content_period_conflict = (
            bool(requested_years)
            and bool(text_years)
            and not requested_years & text_years
        )
        period = 0.35 if requested_years & text_years else -0.25
        metadata_only = (
            -0.75
            if content_period_conflict
            and str(candidate["visible_source_scope"].get("year")) in requested_years
            else 0
        )
        if content_period_conflict:
            period = -1.0
        table_metric = 0.1 if "|" in text else 0
        score = 1.0 * lexical + entity + period + metadata_only + table_metric
        scored.append(
            (score, candidate["candidate_id"], content_period_conflict)
        )
    eligible = [item for item in scored if not item[2]]
    if not eligible:
        eligible = scored
    eligible.sort(key=lambda item: (-item[0], item[1]))
    selected = [
        candidate_id
        for score, candidate_id, _ in eligible[:2]
        if score > 0.25
    ]
    if not selected:
        selected = [eligible[0][1]]
    return {
        "experience_actions": [],
        "evidence_candidate_ids": selected,
    }


def plan_visible_candidates(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Return exactly the candidate evidence visible to B0 and strong rule."""
    visible: list[dict[str, Any]] = []
    for candidate in task["actor_view"]["candidates"]:
        visible.append(
            {
                "candidate_id": candidate["candidate_id"],
                "text": candidate["text"],
                "page_number": candidate["page_number"],
                "visible_source_scope": candidate["visible_source_scope"],
            }
        )
    return visible


def candidate_visibility_sha256(task: dict[str, Any]) -> str:
    return sha256_text(plan_visible_candidates(task))


def deterministic_consume(
    task: dict[str, Any],
    tool_result: dict[str, Any],
) -> dict[str, Any]:
    """Extractive visible-rule consumption; no hidden reference is read."""
    if tool_result.get("tool_status") != "OK":
        return {
            "answer_status": "UNKNOWN",
            "facts": [],
            "used_candidate_ids": [],
        }
    question_tokens = normalized_tokens(task["actor_view"]["question"])
    question_tokens -= {"what", "were", "was", "the", "and", "for", "in", "of", "to"}
    facts: list[dict[str, Any]] = []
    used: list[str] = []
    for item in tool_result["evidence"]:
        text = item["text"]
        lines = [line.strip() for line in text.splitlines() if "|" in line]
        candidates: list[tuple[float, dict[str, Any]]] = []
        for line in lines:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            label = next((cell for cell in cells if re.search(r"[A-Za-z]{3}", cell)), "")
            numbers = [
                parse_number(cell)
                for cell in cells
                if parse_number(cell) is not None
            ]
            if not label or not numbers:
                continue
            overlap = len(question_tokens & normalized_tokens(label))
            value = numbers[-1] if len(numbers) > 1 else numbers[0]
            fact = {
                "label": label,
                "value": value,
                "unit": None,
                "period": None,
            }
            candidates.append((float(overlap), fact))
        candidates.sort(key=lambda pair: -pair[0])
        for _, fact in candidates[:2]:
            facts.append(fact)
            if item["candidate_id"] not in used:
                used.append(item["candidate_id"])
    if not facts:
        return {
            "answer_status": "UNKNOWN",
            "facts": [],
            "used_candidate_ids": [item["candidate_id"] for item in tool_result["evidence"]],
        }
    return {
        "answer_status": "ANSWER",
        "facts": facts[:4],
        "used_candidate_ids": used[:4],
    }


def verify_bundle(bundle_path: Path) -> dict[str, Any]:
    bundle = load_object(bundle_path)
    if bundle.get("schema") != "finrank_c3_b0_v4_bundle_v2":
        raise ValueError("bundle_schema_invalid")
    for name, expected in bundle["artifacts"].items():
        path = PACKAGE / name
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"bundle_artifact_mismatch:{name}")
    return bundle
