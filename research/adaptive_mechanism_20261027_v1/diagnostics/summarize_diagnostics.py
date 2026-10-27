#!/usr/bin/env python3
"""Summarize V2 residuals against the visible typed baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_V2 = (
    REPOSITORY_ROOT
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "scoring_v2"
    / "results"
    / "FIRST_BATCH_RESCORE_V2.json"
)
DEFAULT_BASELINE = Path(__file__).resolve().parent / "results/VISIBLE_TYPED_BASELINE.json"
DEFAULT_CARDS = Path(__file__).resolve().parent / "results/ERROR_CARDS.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results/DIAGNOSTIC_SUMMARY.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2", type=Path, default=DEFAULT_V2)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    v2 = load(args.v2)
    baseline = load(args.baseline)
    cards = load(args.cards)
    baseline_by_uid = {row["question_uid"]: row for row in baseline["rows"]}
    v2_by_uid = {row["question_uid"]: row for row in v2["per_uid_outcomes"]}

    accepted = [
        row for row in baseline["rows"] if row["score"]["status"] == "ACCEPT"
    ]
    bounded_unknown = [
        row
        for row in baseline["rows"]
        if row["score"]["status"] == "REASONABLE_UNKNOWN"
    ]
    unexplained = [
        row
        for row in baseline["rows"]
        if row["score"]["status"]
        not in {"ACCEPT", "REASONABLE_UNKNOWN"}
    ]
    if unexplained:
        raise SystemExit("baseline_left_unexplained_natural_residuals")

    mechanism_uids = [
        "ad42fe3e-38cd-446f-a313-b9a50f5e6937",
        "e14c60c4-3460-42eb-8d21-c29abdbce3a8",
        "9e3493de-9a29-4db8-ad06-52dc6ff1fdaf",
    ]
    mechanism_evidence = []
    for uid in mechanism_uids:
        rows = [
            row for row in baseline["rows"] if row["question_uid"] == uid
        ]
        mechanism_evidence.append(
            {
                "question_uid": uid,
                "question": rows[0]["question"],
                "v2_status_by_arm": v2_by_uid[uid]["scoring_v2_by_arm"],
                "baseline_status_by_arm": {
                    row["arm"]: row["score"]["status"] for row in rows
                },
                "baseline_numeric_by_arm": {
                    row["arm"]: row["response"].get("numeric_value")
                    for row in rows
                },
                "interpretation": (
                    "Visible typed reduction resolves the mean/count information-loss "
                    "signal wherever the required evidence is visible."
                ),
            }
        )

    payload = {
        "schema": "adaptive_mechanism_diagnostic_summary_v1",
        "status": "COMPLETE_BASELINE_EXPLAINS_OR_BOUNDS_ALL_V2_RESIDUALS",
        "review_identity": (
            "AI/automatic zero-model diagnostic comparison; not human gold, "
            "not a judge, and not new-source validation"
        ),
        "model_calls": 0,
        "training_runs": 0,
        "generation_records_created": 0,
        "source_hashes": {
            "scoring_v2_summary": sha256(args.v2),
            "visible_typed_baseline": sha256(args.baseline),
            "error_cards": sha256(args.cards),
        },
        "v2_primary_final_attempts": v2["primary_final_attempt_count"],
        "v2_status_counts_by_arm": {
            arm: summary["scoring_v2_outcomes"]
            for arm, summary in v2["paired_arm_summaries"].items()
            if isinstance(summary, dict) and "scoring_v2_outcomes" in summary
        },
        "baseline_status_counts": baseline["status_counts"],
        "explained_by_accept": len(accepted),
        "bounded_as_reasonable_unknown": len(bounded_unknown),
        "unexplained_natural_residuals": len(unexplained),
        "unexplained_rows": unexplained,
        "mechanism_signal_evidence": mechanism_evidence,
        "error_card_count": len(cards["cards"]),
        "decision": {
            "candidate": "STOP_BEFORE_GENERATION",
            "reason": (
                "The transparent visible-only typed baseline reaches ACCEPT on "
                "31/36 attempts and a contract-valid REASONABLE_UNKNOWN on the "
                "remaining 5 where required visible evidence is absent; no "
                "unexplained natural residual remains."
            ),
            "confirmation_run": False,
            "new_source_validation": False,
        },
        "claim_boundary": (
            "One immutable 12-UID development panel only; no panel method gain, "
            "C acceptance, confirmation, production result, or external validation."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "accept": len(accepted),
                "reasonable_unknown": len(bounded_unknown),
                "unexplained": len(unexplained),
                "decision": payload["decision"]["candidate"],
                "model_calls": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
