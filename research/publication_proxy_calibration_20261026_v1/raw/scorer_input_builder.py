"""Build scorer inputs strictly after an actor response has been produced."""

from __future__ import annotations

from typing import Any

from .contracts import canonical_json, sha256_bytes
from .strict_parser import ParsedResponse


def evidence_visible(
    reference: dict[str, Any],
    selected_paragraph_orders: set[str],
) -> bool:
    if reference["source_requirement"] == "table":
        return True
    required = {str(item["order"]) for item in reference.get("paragraphs", [])}
    return bool(required) and required <= selected_paragraph_orders


def build_scorer_input(
    response: ParsedResponse,
    reference: dict[str, Any],
    selected_paragraph_orders: set[str],
) -> dict[str, Any]:
    visible = evidence_visible(reference, selected_paragraph_orders)
    return {
        "schema": "p2_post_generation_scorer_input_v1",
        "question_uid": reference["question_uid"],
        "table_uid": reference["table_uid"],
        "question": reference["question"],
        "response": response.to_dict(),
        "frozen_reference_chain": {
            "answer": reference["answer"],
            "answer_type": reference["answer_type"],
            "unit": reference["unit"],
            "program": reference["program"],
            "paragraphs": reference["paragraphs"],
            "source_requirement": reference["source_requirement"],
            "review_identity": reference["review_identity"],
        },
        "selected_paragraph_orders": sorted(selected_paragraph_orders),
        "required_evidence_visible": visible,
        "scorer_input_sha256": sha256_bytes(canonical_json(response.to_dict())),
    }

