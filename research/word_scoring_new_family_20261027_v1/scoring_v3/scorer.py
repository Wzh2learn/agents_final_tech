"""Zero-model Scoring V3 paired-control implementation.

V2 remains the immutable baseline.  V3 imports its structural helpers and
replaces only the two ambiguous evidence rules plus numeric agreement for a
one-element numeric span.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from research.adaptive_mechanism_20261027_v1.scoring_v2 import scorer as v2


ROLE_REFERENCE_RE = re.compile(r"^TABLE:R\d+$")
ALL_REFERENCE_RE = re.compile(r"^(?:P[1-9]\d*|TABLE:C\d+|TABLE:R\d+(?::C\d+)?)$")


def _is_valid_reference(value: str) -> bool:
    return bool(ALL_REFERENCE_RE.fullmatch(value))


def _support(expected: str, observed: str) -> str:
    if expected == observed:
        return "exact"
    expected_row = re.fullmatch(r"TABLE:R(\d+)(?::C\d+)?", expected)
    observed_row = re.fullmatch(r"TABLE:R(\d+)(?::C\d+)?", observed)
    expected_role_only = bool(re.fullmatch(r"TABLE:R\d+", expected))
    observed_role_only = bool(re.fullmatch(r"TABLE:R\d+", observed))
    if (
        expected_row
        and observed_row
        and expected_row.group(1) == observed_row.group(1)
        and (expected_role_only or observed_role_only)
    ):
        return "role"
    if expected.startswith("TABLE:R") and observed.startswith("TABLE:C"):
        expected_column = expected.rsplit(":", 1)[-1]
        observed_column = observed.rsplit(":", 1)[-1]
        if expected_column == observed_column:
            return "broad"
    if expected.startswith("TABLE:R") and observed.startswith("TABLE:R"):
        expected_column = expected.rsplit(":", 1)[-1]
        observed_column = observed.rsplit(":", 1)[-1]
        if expected_column == observed_column:
            return "broad"
    return "none"


def _validate_observed_refs(
    observed_refs: list[str], visible: v2.VisibleContext
) -> dict[str, Any] | None:
    for ref in observed_refs:
        if not _is_valid_reference(ref):
            return {"status": "FAIL", "reason": "invalid_reference", "observed": ref}
        if ref.startswith("P"):
            index = int(ref[1:])
            if index not in visible.paragraphs:
                return {"status": "FAIL", "reason": "out_of_range_reference", "observed": ref}
        elif ROLE_REFERENCE_RE.fullmatch(ref):
            row_index = int(ref[7:])
            if row_index not in visible.table.rows:
                return {"status": "FAIL", "reason": "nonexistent_reference", "observed": ref}
        elif ":R" in ref:
            match = re.fullmatch(r"TABLE:R(\d+):C(\d+)", ref)
            assert match
            row_index, column_index = map(int, match.groups())
            if row_index not in visible.table.rows or column_index not in visible.table.rows[row_index]:
                return {"status": "FAIL", "reason": "nonexistent_reference", "observed": ref}
        else:
            column_index = int(ref.split(":C", 1)[1])
            if column_index not in visible.table.columns:
                return {"status": "FAIL", "reason": "nonexistent_reference", "observed": ref}
    return None


def _required_supports(requirement: dict[str, Any], observed_refs: list[str]) -> str:
    accepted = requirement.get("accepted_citations") or [requirement["citation"]]
    statuses = [
        _support(str(expected), observed)
        for expected in accepted
        for observed in observed_refs
    ]
    if requirement.get("binding_mode") == "role_period":
        exact = [
            observed
            for expected in accepted
            for observed in observed_refs
            if str(expected) == observed
        ]
        if exact:
            return "exact"
        if any(status in {"role", "broad"} for status in statuses):
            return "broad"
        return "none"
    if "exact" in statuses or "role" in statuses:
        return "exact"
    if "broad" in statuses:
        return "broad"
    return "none"


def evidence_layer_v3(
    payload: dict[str, Any],
    reference: dict[str, Any],
    visible: v2.VisibleContext,
    reconstruction: dict[str, Any],
) -> dict[str, Any]:
    if payload.get("unknown"):
        if not reconstruction["reconstructible"]:
            return {"status": "REASONABLE_UNKNOWN", "reason": reconstruction["reason"]}
        return {"status": "FAIL", "reason": "unsupported_unknown_visible_evidence"}

    observed_refs = list(payload["evidence_refs"])
    invalid = _validate_observed_refs(observed_refs, visible)
    if invalid is not None:
        return invalid

    explicit_requirements = reference.get("required_evidence")
    if explicit_requirements:
        support: dict[str, str] = {}
        for requirement in explicit_requirements:
            operand = str(requirement["operand_id"])
            support[operand] = _required_supports(requirement, observed_refs)
        if any(status == "none" for status in support.values()):
            return {
                "status": "FAIL",
                "reason": "required_evidence_operand_mismatch",
                "support": support,
            }
        if any(status == "broad" for status in support.values()):
            return {
                "status": "PENDING_ADJUDICATION",
                "reason": "broad_evidence_not_role_bound",
                "support": support,
            }
        return {
            "status": "PASS",
            "reason": "each_required_operand_exactly_supported",
            "support": support,
        }

    role_only = [ref for ref in observed_refs if ROLE_REFERENCE_RE.fullmatch(ref)]
    if role_only and not reference.get("independent_role_reference"):
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": "role_reference_cannot_distinguish_rows",
            "observed": observed_refs,
        }

    if not reconstruction["reconstructible"]:
        if not observed_refs:
            return {"status": "FAIL", "reason": "evidence_refs_missing"}
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": "legal_semantic_reference_not_reconstructible",
            "observed": observed_refs,
        }

    expected_refs = reconstruction["refs"]
    if not expected_refs:
        if reference["source_requirement"] in {"paragraph", "both"} and reconstruction.get(
            "missing_raw_orders"
        ):
            return {
                "status": "PENDING_ADJUDICATION",
                "reason": "required_scale_context_not_visible",
                "missing_raw_orders": reconstruction["missing_raw_orders"],
            }
        return {"status": "PENDING_ADJUDICATION", "reason": "semantic_reference_unavailable"}

    support = {}
    for expected in expected_refs:
        statuses = [_support(expected, observed) for observed in observed_refs]
        if "exact" in statuses or "role" in statuses:
            support[expected] = "exact"
        elif "broad" in statuses:
            support[expected] = "broad"
        else:
            support[expected] = "none"
    if any(status == "none" for status in support.values()):
        return {
            "status": "FAIL",
            "reason": "semantic_reference_mismatch",
            "expected": sorted(expected_refs),
            "observed": observed_refs,
            "support": support,
        }
    if any(status == "broad" for status in support.values()):
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": "complete_evidence_contract_requires_exact_role_binding",
            "expected": sorted(expected_refs),
            "observed": observed_refs,
            "support": support,
        }
    return {
        "status": "PASS",
        "reason": "every_required_evidence_item_exactly_supported",
        "expected": sorted(expected_refs),
        "observed": observed_refs,
        "support": support,
    }


def numeric_layer_v3(payload: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    answer_type = reference["answer_type"]
    answer = payload["answer"]
    observed_number = payload["numeric_value"]
    singular_numeric_expected = (
        answer_type in {"arithmetic", "count"}
        or (answer_type == "span" and v2.parse_decimal(reference["answer"]) is not None)
        or (
            answer_type == "span"
            and isinstance(answer, list)
            and len(answer) == 1
            and v2.parse_decimal(answer[0]) is not None
        )
    )
    if not singular_numeric_expected:
        return {"status": "PASS", "reason": "numeric_value_not_applicable"}

    if (
        answer_type == "span"
        and isinstance(answer, list)
        and len(answer) == 1
        and v2.parse_decimal(answer[0]) is not None
    ):
        expected_number = v2.parse_decimal(answer[0])
        expected_source = "one_element_answer_list"
    else:
        expected_number = v2.parse_decimal(reference["answer"])
        expected_source = "reference_answer"
    if expected_number is None or observed_number is None or not v2.numeric_close(
        observed_number, expected_number
    ):
        return {
            "status": "FAIL",
            "reason": "numeric_value_mismatch_or_missing",
            "expected": str(expected_number) if expected_number is not None else reference["answer"],
            "expected_source": expected_source,
            "observed": observed_number,
        }
    return {
        "status": "PASS",
        "reason": f"signed_numeric_value_matches_{expected_source}",
        "expected": str(expected_number),
        "expected_source": expected_source,
        "observed": observed_number,
    }


def strict_layer_v3(response_text: str, reference: dict[str, Any]) -> dict[str, Any]:
    result = v2.strict_layer(response_text, reference)
    if result["reason"] == "invalid_evidence_reference_syntax" and isinstance(
        result["parsed"], dict
    ):
        refs = result["parsed"].get("evidence_refs")
        if isinstance(refs, list) and all(
            isinstance(item, str) and _is_valid_reference(item) for item in refs
        ):
            return {
                "status": "PASS",
                "reason": "strict_contract_satisfied_with_v3_role_references",
                "parsed": result["parsed"],
            }
    return result


def final_status_v3(layers: dict[str, dict[str, Any]], payload: dict[str, Any], reconstruction: dict[str, Any]) -> dict[str, Any]:
    if layers["strict"]["status"] == "STRICT_FAIL":
        return {"status": "STRICT_FAIL", "reason": layers["strict"]["reason"]}
    if payload.get("unknown"):
        if reconstruction.get("missing_raw_orders") or not reconstruction["reconstructible"]:
            return {"status": "REASONABLE_UNKNOWN", "reason": "required_evidence_not_visible"}
        return {"status": "REJECT", "reason": "unsupported_unknown"}
    failing = [
        name
        for name in ("answer", "numeric_unit", "evidence")
        if layers[name]["status"] == "FAIL"
    ]
    if failing:
        return {
            "status": "REJECT",
            "reason": ";".join(f"{name}:{layers[name]['reason']}" for name in failing),
        }
    pending = [
        name
        for name, layer in layers.items()
        if layer["status"] in {"PENDING_ADJUDICATION", "REASONABLE_UNKNOWN"}
    ]
    if pending:
        return {
            "status": "PENDING_ADJUDICATION",
            "reason": ";".join(f"{name}:{layers[name]['reason']}" for name in pending),
        }
    return {"status": "ACCEPT", "reason": "all_five_layers_pass"}


def score_response(
    response_text: str,
    reference: dict[str, Any],
    visible: v2.VisibleContext,
) -> dict[str, Any]:
    strict = strict_layer_v3(response_text, reference)
    if strict["parsed"] is None:
        layers = {
            "strict": strict,
            "answer": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
            "numeric_unit": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
            "evidence": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
            "final_delivery": {"status": "STRICT_FAIL", "reason": "unavailable_after_strict_failure"},
        }
        return {
            "status": "STRICT_FAIL",
            "scoring_version": "V3",
            "layers": layers,
            "expected_reference_reconstruction": None,
        }

    payload = strict["parsed"]
    reconstruction = v2.reconstruct_expected_refs(reference, visible)
    answer = v2.answer_layer(payload, reference)
    unit = v2.unit_layer(payload, reference, visible)
    numeric = numeric_layer_v3(payload, reference)
    if numeric["status"] == "FAIL" or unit["status"] == "FAIL":
        numeric_unit = {
            "status": "FAIL",
            "reason": ";".join(
                item["reason"] for item in (numeric, unit) if item["status"] == "FAIL"
            ),
            "numeric": numeric,
            "unit": unit,
        }
    elif unit["status"] == "PENDING_ADJUDICATION":
        numeric_unit = {
            "status": "PENDING_ADJUDICATION",
            "reason": unit["reason"],
            "numeric": numeric,
            "unit": unit,
        }
    else:
        numeric_unit = {
            "status": "PASS",
            "reason": ";".join(item["reason"] for item in (numeric, unit)),
            "numeric": numeric,
            "unit": unit,
        }
    evidence = evidence_layer_v3(payload, reference, visible, reconstruction)
    layers = {
        "strict": strict,
        "answer": answer,
        "numeric_unit": numeric_unit,
        "evidence": evidence,
    }
    final = final_status_v3(layers, payload, reconstruction)
    layers["final_delivery"] = final
    return {
        "status": final["status"],
        "scoring_version": "V3",
        "layers": layers,
        "expected_reference_reconstruction": {
            **reconstruction,
            "refs": sorted(reconstruction["refs"])
            if isinstance(reconstruction.get("refs"), set)
            else reconstruction.get("refs"),
        },
    }


def load_source_records(path: Path) -> dict[str, dict[str, Any]]:
    return v2.load_source_records(path)


ARMS = v2.ARMS
