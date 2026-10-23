"""Apply contract-level corrections to auxiliary G2 semantic verdicts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def corrected_category(row: dict[str, Any], verdict: dict[str, Any]) -> tuple[str, list[str]]:
    record = row["answer_record"]
    decision = record.get("decision")
    answer = record.get("answer")
    reasons = []
    category = verdict["primary_category"]
    if verdict.get("response_contract_status") != "VALID":
        category = "INTERFACE_FORMAT_FAILURE"
        reasons.append("INVALID_RESPONSE_CONTRACT")
    elif decision == "ANSWER" and not str(answer or "").strip():
        category = "INTERFACE_FORMAT_FAILURE"
        reasons.append("ANSWER_DECISION_WITHOUT_ANSWER")
    elif decision in {"CLARIFY", "UNKNOWN"} and category == "GROUNDED_TASK_COMPLETION":
        category = "REASONABLE_UNKNOWN_OR_CLARIFICATION"
        reasons.append(f"{decision}_IS_NOT_TASK_COMPLETION")
    return category, reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-results", type=Path, required=True)
    parser.add_argument("--fixed-state-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    judge = load(args.judge_results)
    fixed = load(args.fixed_state_results)
    source_by_key = {
        (row["uid"], row["representation"], row["question_kind"]): row
        for row in fixed["rows"]
    }
    rows = []
    for verdict_row in judge["rows"]:
        key = (
            verdict_row["uid"],
            verdict_row["representation"],
            verdict_row["question_kind"],
        )
        source = source_by_key[key]
        raw_verdict = verdict_row["verdict"]
        category, reasons = corrected_category(source, raw_verdict)
        validated = dict(raw_verdict)
        validated["primary_category"] = category
        validated["reasonable_abstention"] = (
            category == "REASONABLE_UNKNOWN_OR_CLARIFICATION"
        )
        validated["unnecessary_refusal"] = (
            category == "UNNECESSARY_REFUSAL_DESPITE_SUFFICIENT_EVIDENCE"
        )
        rows.append({
            **{key: verdict_row[key] for key in (
                "uid", "representation", "question_kind", "response_code"
            )},
            "raw_judge_verdict": raw_verdict,
            "validated_verdict": validated,
            "validation_reasons": reasons,
        })
    summary = {}
    for representation in ("plain_fact_bundle", "evidence_decision_bundle"):
        group = [row for row in rows if row["representation"] == representation]
        fact = [row for row in group if row["question_kind"] == "fact"]
        action = [row for row in group if row["question_kind"] == "action"]
        summary[representation] = {
            "primary_counts": dict(Counter(
                row["validated_verdict"]["primary_category"] for row in group
            )),
            "fact_primary_counts": dict(Counter(
                row["validated_verdict"]["primary_category"] for row in fact
            )),
            "action_primary_counts": dict(Counter(
                row["validated_verdict"]["primary_category"] for row in action
            )),
            "fact_completion": sum(
                row["validated_verdict"]["primary_category"] == "GROUNDED_TASK_COMPLETION"
                for row in fact
            ),
            "action_completion": sum(
                row["validated_verdict"]["primary_category"] == "GROUNDED_TASK_COMPLETION"
                for row in action
            ),
            "corrections": dict(Counter(
                reason for row in group for reason in row["validation_reasons"]
            )),
        }
    output = {
        "schema": "g2_semantic_judge_validated_v5",
        "date": "2026-10-23",
        "evidence_identity": "CONTRACT_LEVEL_VALIDATION_OVER_AUXILIARY_LLM_JUDGE",
        "validation_rule": (
            "CLARIFY/UNKNOWN are reasonable abstention rather than task completion; "
            "ANSWER without text and invalid contracts are interface failures."
        ),
        "summary_by_representation": summary,
        "rows": rows,
        "nonclaims": [
            "This correction does not turn the auxiliary judge into human gold.",
            "Raw judge verdicts remain unchanged for audit.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
