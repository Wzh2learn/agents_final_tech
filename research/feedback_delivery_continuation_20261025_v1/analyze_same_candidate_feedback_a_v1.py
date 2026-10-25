"""Rebuild Experiment A summary from preserved raw generation output."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from same_candidate_feedback_a_v1 import (
    CONDITIONS,
    build_summary,
    enrich_row,
    load_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--frozen-results", type=Path, required=True)
    parser.add_argument("--raw-results", type=Path, required=True)
    parser.add_argument("--neutral-results", type=Path)
    parser.add_argument("--failed-neutral-results", type=Path)
    parser.add_argument("--oracle-results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    frozen = [
        row for row in load_jsonl(args.frozen_results)
        if row.get("model_arm") == "ordinary_answer_execution_sft"
    ]
    raw = load_jsonl(args.raw_results)
    for row in raw:
        if row.get("condition") == "ordinary_retry":
            row["condition"] = "deterministic_rerun_control"
            row["slice"] = "deterministic_rerun_control_after_identity_correction"
    neutral = load_jsonl(args.neutral_results) if args.neutral_results else []
    failed_neutral = load_jsonl(args.failed_neutral_results) if args.failed_neutral_results else []
    oracle = load_jsonl(args.oracle_results) if args.oracle_results else []
    for row in failed_neutral:
        row["condition"] = "neutral_revision_interface_failure_v2"
        row["slice"] = "preserved_neutral_revision_interface_failure_v2"
    if (
        len(frozen) != 72
        or len(raw) != 216
        or len(neutral) not in {0, 72}
        or len(failed_neutral) not in {0, 72}
        or len(oracle) not in {0, 72}
    ):
        raise ValueError(
            f"unexpected_counts:{len(frozen)}:{len(raw)}:{len(neutral)}:{len(failed_neutral)}:{len(oracle)}"
        )
    raw.extend(neutral)
    raw.extend(failed_neutral)
    raw.extend(oracle)

    frozen_rows = [
        enrich_row(
            {**row, "condition": "original_frozen"},
            instances[row["instance_id"]],
            "original_frozen",
        )
        for row in frozen
    ]
    enriched = [
        enrich_row(row, instances[str(row["base_instance_id"])], str(row["condition"]))
        for row in raw
    ]

    receipts = {}
    grouped = defaultdict(list)
    for row in enriched:
        grouped[row["condition"]].append(row)
    for condition in CONDITIONS:
        rows = grouped[condition]
        if not rows:
            continue
        receipts[condition] = {
            "attempts": len(rows),
            "prompt_tokens": sum(int(row["prompt_tokens"]) for row in rows),
            "completion_tokens": sum(int(row["completion_tokens"]) for row in rows),
            "wall_seconds_from_per_item_latency": sum(
                float(row.get("latency_ms", 0.0)) for row in rows
            ) / 1000.0,
            "max_new_tokens": 256,
        }

    summary = build_summary(frozen_rows + enriched, receipts)
    summary["new_accounting_attempts"] = len(enriched)
    summary["new_accounting_tokens"] = sum(
        int(row["prompt_tokens"]) + int(row["completion_tokens"])
        for row in enriched
    )
    summary["input_sha256"] = {
        "instances": sha256_file(args.instances),
        "frozen_results": sha256_file(args.frozen_results),
        "raw_results": sha256_file(args.raw_results),
        "neutral_results": sha256_file(args.neutral_results) if args.neutral_results else None,
        "failed_neutral_results": (
            sha256_file(args.failed_neutral_results)
            if args.failed_neutral_results else None
        ),
        "oracle_results": sha256_file(args.oracle_results) if args.oracle_results else None,
    }
    output_rows = args.output.with_suffix(".jsonl")
    write_jsonl(output_rows, enriched)
    summary["output_sha256"] = sha256_file(output_rows)
    write_json(args.output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
