#!/usr/bin/env python3
"""Build evidence-grounded error cards for the immutable first-batch panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
HISTORICAL_ROOT = (
    REPOSITORY_ROOT
    / "research"
    / "publication_proxy_calibration_20261026_v1"
)
DEFAULT_RAW = HISTORICAL_ROOT / "raw/runs/compliant_primary/P2_GENERATIONS.raw.jsonl"
DEFAULT_ANNOTATED = (
    HISTORICAL_ROOT / "raw/runs/compliant_primary/P2_GENERATIONS.annotated.jsonl"
)
DEFAULT_REFERENCE = (
    HISTORICAL_ROOT / "p2_proxy_calibration/receipts/P2_REFERENCE_CHAIN.json"
)
SCORING_ROOT = (
    REPOSITORY_ROOT
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "scoring_v2"
    / "results"
)
OUTPUT_ROOT = Path(__file__).resolve().parent / "results"
ARMS = ("table_top3", "table_top5", "table_all")

DIAGNOSES = {
    "01de2123-400f-4411-98d9-cd3f9f1e4136": (
        "The visible paragraph supplies 2019=4.3 and 2018=19.6 million, but each "
        "arm instead returns the table's 3.1 row change: wrong row binding and "
        "wrong typed operation."
    ),
    "5e67e832-44c4-4284-96d3-75b81cd1ac26": (
        "The two payroll values are numerically correct, but numeric_value is an "
        "array under a scalar contract and the evidence is column-broad rather "
        "than row-bound."
    ),
    "7e942684-fe9e-4ded-a3e9-2f3a5aa707fe": (
        "The question asks for enumerated services, while every arm returns fee "
        "categories; paragraph and column references therefore do not support the "
        "requested fact."
    ),
    "8a3fb2be-150b-410f-a6d5-f3a3dd1fdba3": (
        "All arms return 2,991 rather than the 2018-minus-2017 diluted-share "
        "difference 3,251, indicating period/operation binding failure; references "
        "are only column-broad."
    ),
    "9e3493de-9a29-4db8-ad06-52dc6ff1fdaf": (
        "All arms enumerate fee-table categories but never count the seven "
        "paragraph services; the required visible paragraph is absent from the "
        "top3/top5 contexts."
    ),
    "ad42fe3e-38cd-446f-a313-b9a50f5e6937": (
        "All arms expose the two trade-receivable operands but omit the mean "
        "reduction and scalar numeric_value, so correct operands do not constitute "
        "complete delivery."
    ),
    "cb4abf04-9551-46e2-8a32-46672e284167": (
        "All arms return 302%, the raw total rather than (302-148)/148=104.05%; "
        "the operation and direction are wrong and references are column-broad."
    ),
    "e14c60c4-3460-42eb-8d21-c29abdbce3a8": (
        "All arms find First/Second/Fourth but omit the count 3 and cite "
        "nonexistent columns C6/C8 instead of the visible quarter columns."
    ),
    "f37d1be3-b3fe-487f-bd05-253c20f55eb2": (
        "All arms answer 'dollars' although the visible paragraph states "
        "'(in thousands)'; the citation is visible but the unit is wrong."
    ),
    "7a1f65b6-25e2-48e2-a3cc-baddc688545e": (
        "The Canada value is correct, but USD/$ is used instead of the visible "
        "thousand scale and TABLE:C1 is not row-bound; top3 also lacks the scale "
        "paragraph."
    ),
    "a75bb0b1-4fb1-405c-b2f1-1df4ee3cc9be": (
        "All arms add 'At end of the period' as a component even though it is the "
        "result row, and duplicate column-broad citations do not bind each span."
    ),
    "fcb5e3fa-fb0c-4cce-a86c-229ac3734bd2": (
        "The value and thousand scale are correct, but TABLE:C4 is column-broad "
        "rather than row-bound to Total Electronic Components."
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def layer_reasons(row: dict[str, Any]) -> dict[str, str]:
    return {
        layer: str(details.get("reason", ""))
        for layer, details in row["scoring_v2_layers"].items()
    }


def derive_labels(row: dict[str, Any]) -> dict[str, list[str]]:
    reasons = layer_reasons(row)
    joined = " ".join(reasons.values()).casefold()
    labels: dict[str, list[str]] = defaultdict(list)

    def add(label: str, basis: str) -> None:
        if basis not in labels[label]:
            labels[label].append(basis)

    if row["scoring_v2_status"] == "STRICT_FAIL" or "invalid_" in joined:
        add("format", reasons["strict"] or reasons["final_delivery"])
    if any(
        token in reasons["evidence"].casefold()
        for token in (
            "mismatch",
            "missing",
            "nonexistent",
            "out_of_range",
            "invalid_reference",
            "not_reconstructible",
        )
    ):
        add("reference_defect", reasons["evidence"])
    if "not_reconstructible" in reasons["evidence"].casefold() or "missing" in reasons[
        "evidence"
    ].casefold():
        add("visible_information_insufficient", reasons["evidence"])
    if any(
        token in reasons["answer"].casefold()
        for token in ("mismatch", "set_mismatch", "incomplete")
    ):
        add("fact_entity_row_period_binding", reasons["answer"])
    if any(
        token in reasons["answer"].casefold()
        for token in ("not_complete_or_reduced", "numeric_answer_mismatch")
    ):
        add("operation_reduction", reasons["answer"])
    if any(
        token in reasons["numeric_unit"].casefold()
        for token in ("direction", "unit_or_scale", "unit_mismatch")
    ):
        add("unit_direction", reasons["numeric_unit"])
    if any(
        token in reasons["evidence"].casefold()
        for token in ("mismatch", "broad", "nonexistent", "out_of_range")
    ):
        add("citation_support", reasons["evidence"])
    return dict(sorted(labels.items()))


def markdown_card(card: dict[str, Any]) -> str:
    lines = [
        f"## {card['question_uid']} — {card['control_role']}",
        "",
        f"- Question: {card['question']}",
        f"- Answer type / source: `{card['answer_type']}` / `{card['source_requirement']}`",
        f"- Diagnosis: {card['diagnosis']}",
        f"- Labels: {', '.join(card['labels'])}",
        "",
        "| Arm | Call | Historical | V2 | Failed/pending layers |",
        "|---|---:|---|---|---|",
    ]
    for arm in ARMS:
        raw = card["immutable_final_raw_by_arm"][arm]
        outcome = card["post_v2_residual_by_arm"][arm]
        failed = ", ".join(
            f"{layer}:{details.get('reason', '')}"
            for layer, details in raw["scoring_v2_layers"].items()
            if details.get("status") in {"FAIL", "PENDING_ADJUDICATION", "STRICT_FAIL"}
        )
        lines.append(
            f"| {arm} | {raw['call_number']} | "
            f"{raw['historical_semantic_outcome']} | {outcome} | {failed or 'none'} |"
        )
    lines.extend(
        [
            "",
            "Visible context:",
            "",
            "```text",
            card["visible_context_text"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--annotated", type=Path, default=DEFAULT_ANNOTATED)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--scoring-rows", type=Path, default=SCORING_ROOT / "FIRST_BATCH_ROWS_V2.jsonl")
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    scoring_rows = read_jsonl(args.scoring_rows)
    raw_rows = read_jsonl(args.raw)
    raw_by_call = {row["call_id"]: row for row in raw_rows}
    references = json.loads(args.reference.read_text(encoding="utf-8"))["rows"]
    reference_by_uid = {row["question_uid"]: row for row in references}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scoring_rows:
        grouped[row["question_uid"]].append(row)

    cards: list[dict[str, Any]] = []
    for uid in sorted(grouped):
        arm_rows = {row["arm"]: row for row in grouped[uid]}
        historical = {
            arm: arm_rows[arm]["historical_semantic_outcome"] for arm in ARMS
        }
        control_role = (
            "old_shared_reject"
            if all(value == "REJECT" for value in historical.values())
            else "non_shared_control"
        )
        reference = reference_by_uid[uid]
        raw_final: dict[str, Any] = {}
        for arm in ARMS:
            scoring_row = arm_rows[arm]
            immutable = raw_by_call[scoring_row["call_id"]]
            try:
                parsed_response: Any = json.loads(immutable["complete_response"])
            except json.JSONDecodeError:
                parsed_response = immutable["complete_response"]
            raw_final[arm] = {
                "call_id": immutable["call_id"],
                "call_number": immutable["call_number"],
                "retry_attempt": immutable["retry_attempt"],
                "complete_response": immutable["complete_response"],
                "parsed_response": parsed_response,
                "strict_parse_outcome_historical": immutable["strict_parse_outcome"],
                "historical_semantic_outcome": scoring_row["historical_semantic_outcome"],
                "historical_semantic_reason": scoring_row["historical_semantic_reason"],
                "scoring_v2_status": scoring_row["scoring_v2_status"],
                "scoring_v2_layers": scoring_row["scoring_v2_layers"],
                "selected_paragraph_orders": scoring_row["visible_paragraph_orders"],
            }
        labels: dict[str, list[str]] = defaultdict(list)
        for arm in ARMS:
            for label, bases in derive_labels(arm_rows[arm]).items():
                for basis in bases:
                    if basis not in labels[label]:
                        labels[label].append(basis)
        paragraphs = "\n".join(
            f"P{index}: {item['text']}"
            for index, item in sorted(
                {
                    index: item
                    for row in scoring_rows
                    if row["question_uid"] == uid
                    for index, item in _visible_paragraph_map(row, reference).items()
                }.items()
            )
        )
        visible_text = (
            paragraphs
            + "\n\nTABLE\n"
            + reference["table_text"]
        )
        cards.append(
            {
                "schema": "adaptive_mechanism_error_card_v1",
                "question_uid": uid,
                "control_role": control_role,
                "question": reference["question"],
                "answer_type": reference["answer_type"],
                "source_requirement": reference["source_requirement"],
                "diagnosis": DIAGNOSES[uid],
                "labels": sorted(labels),
                "label_basis_by_arm": {
                    arm: derive_labels(arm_rows[arm]) for arm in ARMS
                },
                "post_v2_residual_by_arm": {
                    arm: arm_rows[arm]["scoring_v2_status"] for arm in ARMS
                },
                "historical_by_arm": historical,
                "immutable_final_raw_by_arm": raw_final,
                "visible_paragraph_orders_by_arm": {
                    arm: arm_rows[arm]["visible_paragraph_orders"] for arm in ARMS
                },
                "visible_context_text": visible_text,
                "evidence_boundary": (
                    "Card labels are derived from immutable raw responses, visible "
                    "context and scoring-layer observations; model self-labels are "
                    "not used as diagnoses."
                ),
            }
        )

    if len(cards) != 12:
        raise SystemExit(f"expected_12_error_cards:{len(cards)}")
    if sum(card["control_role"] == "old_shared_reject" for card in cards) != 9:
        raise SystemExit("expected_9_old_shared_reject_cards")
    if sum(card["control_role"] == "non_shared_control" for card in cards) != 3:
        raise SystemExit("expected_3_non_shared_control_cards")

    payload = {
        "schema": "adaptive_mechanism_error_card_set_v1",
        "status": "COMPLETE_12_EVIDENCE_GROUNDED_CARDS",
        "review_identity": (
            "AI/automatic diagnostic labeling from immutable first-batch evidence; "
            "not model self-report and not human gold"
        ),
        "model_calls": 0,
        "old_shared_reject_uid_count": 9,
        "non_shared_control_uid_count": 3,
        "source_hashes": {
            "raw_jsonl": sha256(args.raw),
            "annotated_jsonl": sha256(args.annotated),
            "reference_chain": sha256(args.reference),
            "scoring_v2_rows": sha256(args.scoring_rows),
        },
        "cards": cards,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "ERROR_CARDS.json", payload)
    markdown = [
        "# Error Cards",
        "",
        payload["review_identity"],
        "",
        "Nine old shared REJECT UIDs and three non-shared controls; each card uses "
        "the real question, immutable final-attempt raw response and visible context.",
        "",
    ]
    markdown.extend(markdown_card(card) for card in cards)
    (args.output / "ERROR_CARDS.md").write_text(
        "\n".join(markdown),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "cards": len(cards),
                "model_calls": 0,
                "output": str(args.output / "ERROR_CARDS.json"),
            },
            sort_keys=True,
        )
    )
    return 0


def _visible_paragraph_map(
    scoring_row: dict[str, Any],
    reference: dict[str, Any],
) -> dict[int, dict[str, str]]:
    selected = set(str(item) for item in scoring_row["visible_paragraph_orders"])
    paragraphs = sorted(
        (
            item
            for item in reference["paragraphs"]
            if str(item["order"]) in selected
        ),
        key=lambda item: int(item["order"]),
    )
    return {
        index: {
            "raw_order": str(item["order"]),
            "text": str(item["text"]),
            "uid": str(item["uid"]),
        }
        for index, item in enumerate(paragraphs, start=1)
    }


if __name__ == "__main__":
    raise SystemExit(main())
