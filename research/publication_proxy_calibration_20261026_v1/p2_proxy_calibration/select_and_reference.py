#!/usr/bin/env python3
"""Select a pre-output P2 development panel and build its review chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SEED = 20261026
PANEL_LIMIT = 12
PANEL_STRATUM = ("source_requirement", "answer_type", "proxy_disagreement")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_rank(uid: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{uid}".encode()).hexdigest()


def render_table(table: list[list[str]]) -> str:
    header = "columns: " + " | ".join(f"C{i}={cell}" for i, cell in enumerate(table[0]))
    rows = [header]
    for index, row in enumerate(table[1:], start=1):
        label = row[0] if row else ""
        body = " | ".join(f"C{i}={cell}" for i, cell in enumerate(row))
        rows.append(f"R{index} [{label}] {body}")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row-results", type=Path, required=True)
    parser.add_argument("--raw-dev", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.row_results.read_text(encoding="utf-8"))["row_results"]
    source = json.loads(args.raw_dev.read_text(encoding="utf-8"))
    qualification = json.loads(args.qualification.read_text(encoding="utf-8"))

    by_uid = {record["table"]["uid"]: record for record in source}
    selected: list[dict[str, Any]] = []
    strata: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("offline_reference_only", {}).get("reference_status") != "QUALIFIED":
            continue
        table_only = row["deployable_actions"]["frontiers"]["table_only"]["semantic_reference_potential_offline"]
        always = row["deployable_actions"]["frontiers"]["always_expand"]["semantic_reference_potential_offline"]
        source_need = row["offline_reference_only"]["reference_classification"]["source_requirement"]
        proxy_disagreement = "disagree" if table_only != always else "agree"
        strata[(source_need, row["answer_type"], proxy_disagreement)].append(row)

    # Freeze one hash-ranked item per nonempty stratum, then fill remaining
    # capacity in lexicographic stratum order. No model output is read.
    ordered_strata = sorted(strata)
    for stratum in ordered_strata:
        candidates = sorted(strata[stratum], key=lambda row: stable_rank(row["question_uid"], SEED))
        if candidates:
            selected.append({"row": candidates[0], "stratum": stratum})
    for stratum in ordered_strata:
        candidates = sorted(strata[stratum], key=lambda row: stable_rank(row["question_uid"], SEED))
        for row in candidates[1:]:
            if len(selected) >= PANEL_LIMIT:
                break
            selected.append({"row": row, "stratum": stratum})
        if len(selected) >= PANEL_LIMIT:
            break
    selected = selected[:PANEL_LIMIT]

    references = []
    for item in selected:
        row = item["row"]
        record = by_uid[row["table_uid"]]
        questions = next(q for q in record["questions"] if q["uid"] == row["question_uid"])
        paragraph_by_order = {str(p["order"]): p for p in record["paragraphs"]}
        required_orders = [str(order) for order in row["offline_reference_only"]["required_paragraph_orders"]]
        references.append(
            {
                "question_uid": row["question_uid"],
                "table_uid": row["table_uid"],
                "question": row["question"],
                "table_text": render_table(record["table"]["table"]),
                "paragraphs": [
                    {
                        "order": order,
                        "uid": paragraph_by_order.get(order, {}).get("uid"),
                        "text": paragraph_by_order.get(order, {}).get("text"),
                    }
                    for order in required_orders
                ],
                "role": row["offline_reference_only"]["reference_classification"]["target_source"],
                "unit": row["offline_reference_only"]["reference_scale"],
                "program": questions.get("derivation", ""),
                "answer": row["offline_reference_only"]["reference_answer"],
                "source_requirement": row["offline_reference_only"]["reference_classification"]["source_requirement"],
                "answer_type": row["answer_type"],
                "proxy_disagreement": item["stratum"][2],
                "review_identity": "publication_proxy_calibration_a_20261026 automated AI review; not human gold or a complete semantic oracle",
            }
        )

    selection = {
        "schema": "p2_development_selection_v1",
        "task_id": "publication-proxy-calibration-a-20261026",
        "seed": SEED,
        "panel_limit": PANEL_LIMIT,
        "stratification_rule": list(PANEL_STRATUM),
        "selection_order": "one hash-ranked item per nonempty stratum, then fill by lexicographic stratum and UID hash",
        "source_row_count": len(rows),
        "source_qualified_count": sum(
            row.get("offline_reference_only", {}).get("reference_status") == "QUALIFIED" for row in rows
        ),
        "excluded_count": len(rows) - sum(
            row.get("offline_reference_only", {}).get("reference_status") == "QUALIFIED" for row in rows
        ),
        "exclusion_reason": "P2 qualification excludes the frozen NOT_MODEL_READY ambiguous direction/scale item before model output",
        "replacements": [],
        "selected_count": len(selected),
        "selected_uids": [item["row"]["question_uid"] for item in selected],
        "stratum_counts": {
            "|".join(key): len(value) for key, value in sorted(strata.items())
        },
        "denominator_preserved": {
            "screen": 507,
            "future_evaluation": 506,
            "source": qualification["reference_completeness"],
        },
        "model_output_viewed": False,
        "generation_status": "STOPPED_BEFORE_GENERATION",
        "source_sha256": {
            "row_results": sha256_file(args.row_results),
            "raw_dev": sha256_file(args.raw_dev),
            "qualification": sha256_file(args.qualification),
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "P2_SELECTION_RECEIPT.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "P2_REFERENCE_CHAIN.json").write_text(
        json.dumps(
            {
                "schema": "p2_question_table_role_unit_program_answer_chain_v1",
                "review_identity": "publication_proxy_calibration_a_20261026 automated AI review; not human gold or a complete semantic oracle",
                "rows": references,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(selection, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
