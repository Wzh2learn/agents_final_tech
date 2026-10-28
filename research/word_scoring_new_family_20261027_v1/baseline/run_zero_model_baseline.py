#!/usr/bin/env python3
"""Run the frozen question-only typed baseline before any model output."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from research.adaptive_mechanism_20261027_v1.d_integration.question_only_ablation import (  # noqa: E402
    infer_answer_type_from_question,
)
from research.adaptive_mechanism_20261027_v1.diagnostics.visible_typed_baseline import (  # noqa: E402
    answer_from_visible,
)
from research.adaptive_mechanism_20261027_v1.scoring_v2.scorer import (  # noqa: E402
    load_visible_context,
)
from research.word_scoring_new_family_20261027_v1.scoring_v3.scorer import (  # noqa: E402
    score_response,
)


OUT = Path(__file__).resolve().parent / "results"
PANEL = OUT.parent.parent / "exposure/PANEL_FREEZE.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for reference in panel["references"]:
        visible = load_visible_context(
            {"paragraphs": reference["paragraphs"]},
            reference,
            [item["order"] for item in reference["paragraphs"]],
        )
        actor_type = infer_answer_type_from_question(reference["question"])
        response_text = answer_from_visible(
            reference["question"], actor_type, visible
        )
        score = score_response(response_text, reference, visible)
        rows.append(
            {
                "schema": "word_new_family_question_only_baseline_row_v1",
                "question_uid": reference["question_uid"],
                "family_id": reference["family_id"],
                "arm": "question_only_typed_baseline",
                "question": reference["question"],
                "reference_answer_type": reference["answer_type"],
                "actor_answer_type": actor_type,
                "actor_type_source": "frozen_question_text_rule",
                "visible_paragraph_orders": [
                    item["order"] for item in reference["paragraphs"]
                ],
                "response": json.loads(response_text),
                "score": score,
                "model_calls": 0,
            }
        )
    counts = Counter(row["score"]["status"] for row in rows)
    applicable = sum(
        row["response"].get("unknown") is False for row in rows
    )
    payload = {
        "schema": "word_new_family_zero_model_baseline_v1",
        "status": "COMPLETE_ZERO_MODEL_BASELINE",
        "model_calls": 0,
        "training_runs": 0,
        "generation_records_created": 0,
        "rows": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "applicable_non_unknown": applicable,
        "failure_or_abstention": len(rows) - applicable,
        "baseline_identity": (
            "Frozen question-only answer-type rule plus visible typed reduction "
            "and shared calculator; no model, gold answer input or UID branch."
        ),
        "source_hashes": {
            "panel_freeze": sha256(PANEL),
            "scoring_v3": sha256(
                OUT.parent.parent / "scoring_v3/scorer.py"
            ),
            "typed_baseline": sha256(
                ROOT
                / "research/adaptive_mechanism_20261027_v1/diagnostics/"
                "visible_typed_baseline.py"
            ),
            "question_only_rule": sha256(
                ROOT
                / "research/adaptive_mechanism_20261027_v1/d_integration/"
                "question_only_ablation.py"
            ),
        },
        "per_uid": [
            {
                "question_uid": row["question_uid"],
                "family_id": row["family_id"],
                "status": row["score"]["status"],
                "applicable": row["response"].get("unknown") is False,
                "answer_reason": row["score"]["layers"]["answer"].get("reason"),
                "evidence_reason": row["score"]["layers"]["evidence"].get("reason"),
            }
            for row in rows
        ],
        "claim_boundary": (
            "Zero-model applicability/failure diagnostic on the frozen same-source "
            "new-table panel; not accuracy, method gain or confirmation."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ZERO_MODEL_BASELINE_ROWS.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    (OUT / "ZERO_MODEL_BASELINE.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "rows": payload["rows"],
                "status_counts": payload["status_counts"],
                "applicable": applicable,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
