#!/usr/bin/env python3
"""Zero-model answer-type ablations for the first-batch diagnostic.

The only actor feature added here is a deterministic type inference from the
question text. Reference answer_type is used after output solely by the scorer.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from research.adaptive_mechanism_20261027_v1.diagnostics import (  # noqa: E402
    visible_typed_baseline as vtb,
)
from research.adaptive_mechanism_20261027_v1.scoring_v2 import scorer as sc  # noqa: E402


OUT_ROOT = Path(__file__).resolve().parent / "results"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def infer_answer_type_from_question(question: str) -> str:
    q = question.casefold()
    if re.search(r"\bhow many\b", q):
        return "count"
    if "components factored" in q or re.search(r"\bwhat services\b", q):
        return "multi-span"
    if " respectively" in q and " and " in q:
        return "multi-span"
    if "units used" in q or "unit used" in q:
        return "span"
    if "average" in q or "mean" in q or "percentage change" in q:
        return "arithmetic"
    if re.search(r"\bchange\b", q):
        return "arithmetic"
    if re.search(r"\bwhat (?:is|was|are|were)\b", q):
        return "span"
    return "unknown"


def build_cases():
    raw_rows = read_jsonl(vtb.DEFAULT_RAW)
    annotated = {row["call_id"]: row for row in read_jsonl(vtb.DEFAULT_ANNOTATED)}
    references = json.loads(vtb.DEFAULT_REFERENCE.read_text(encoding="utf-8"))["rows"]
    uid_by_hash = {
        hashlib.sha256(row["question_uid"].encode("utf-8")).hexdigest(): row["question_uid"]
        for row in references
    }
    ref_by_uid = {row["question_uid"]: row for row in references}
    sources = sc.load_source_records(vtb.DEFAULT_SOURCE)
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row["question_uid_sha256"], row["arm"])].append(row)
    cases = []
    for (uid_hash, arm), attempts in sorted(grouped.items()):
        raw = max(attempts, key=lambda item: int(item["call_number"]))
        uid = uid_by_hash[uid_hash]
        reference = ref_by_uid[uid]
        selected_orders = raw.get(
            "selected_paragraph_orders",
            annotated[raw["call_id"]]["selected_paragraph_orders"],
        )
        visible = sc.load_visible_context(
            sources[reference["table_uid"]], reference, selected_orders
        )
        cases.append((uid, arm, reference, visible))
    return cases


def run_variant(cases, mode: str):
    rows = []
    for uid, arm, reference, visible in cases:
        if mode == "oracle":
            actor_type = reference["answer_type"]
            type_source = "reference.answer_type"
        elif mode == "answer_type_free":
            actor_type = ""
            type_source = "blank"
        elif mode == "question_only":
            actor_type = infer_answer_type_from_question(reference["question"])
            type_source = "question_text"
        else:
            raise ValueError(mode)
        response_text = vtb.answer_from_visible(
            reference["question"], actor_type, visible
        )
        score = sc.score_response(response_text, reference, visible)
        rows.append(
            {
                "question_uid": uid,
                "question": reference["question"],
                "arm": arm,
                "reference_answer_type": reference["answer_type"],
                "actor_answer_type": actor_type,
                "actor_type_source": type_source,
                "response": json.loads(response_text),
                "score_status": score["status"],
                "score_layers": score["layers"],
            }
        )
    return rows


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    cases = build_cases()
    variants = {
        mode: run_variant(cases, mode)
        for mode in ("oracle", "answer_type_free", "question_only")
    }
    summary = {
        "schema": "question_only_answer_type_ablation_v1",
        "status": "COMPLETE_ZERO_MODEL",
        "model_calls": 0,
        "training_runs": 0,
        "generation_records_created": 0,
        "review_identity": (
            "D zero-model ablation; not human gold, not a model run and not "
            "new-source validation"
        ),
        "question_only_rule_boundary": (
            "The actor type is inferred only from question text. The scorer may "
            "use reference metadata after output. This is an exposed development "
            "heuristic and is not a general answer-type oracle replacement."
        ),
        "variants": {},
        "source_hashes": {
            "raw": sha256(vtb.DEFAULT_RAW),
            "annotated": sha256(vtb.DEFAULT_ANNOTATED),
            "reference": sha256(vtb.DEFAULT_REFERENCE),
            "source": sha256(vtb.DEFAULT_SOURCE),
        },
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for mode, rows in variants.items():
        counts = dict(sorted(Counter(row["score_status"] for row in rows).items()))
        summary["variants"][mode] = {
            "status_counts": counts,
            "rows_path": str((OUT_ROOT / f"{mode.upper()}_ROWS.jsonl").relative_to(REPO_ROOT)),
        }
        (OUT_ROOT / f"{mode.upper()}_ROWS.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
    summary["question_only_status_counts"] = summary["variants"]["question_only"]["status_counts"]
    summary["answer_type_free_status_counts"] = summary["variants"]["answer_type_free"]["status_counts"]
    summary["oracle_status_counts"] = summary["variants"]["oracle"]["status_counts"]
    write_json(OUT_ROOT / "QUESTION_ONLY_ABLATION.json", summary)
    print(json.dumps(summary["variants"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
