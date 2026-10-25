"""Rescore preserved revision diagnostic rows with the common syntax adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_binding_residual_v3 import extract_target, parse_cells
from revision_operator_diagnostic_v1 import (
    expected_target,
    load_jsonl,
    normalize_generated_text,
    summarize,
    write_json,
    write_jsonl,
)
from run_natural_program_experiment_v2 import evaluate_target
from semantic_delivery_check_v3 import question_from_prompt, semantic_check


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--exposure-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    rescored = []
    for row in load_jsonl(args.rows):
        instance = instances[row["instance_id"]]
        raw = str(row.get("raw_generated_text", row.get("generated_text", "")))
        normalized, applied, actions = normalize_generated_text(raw)
        target = extract_target(normalized)
        scored = evaluate_target(normalized, instance)
        decision, reasons = semantic_check(
            question_from_prompt(str(instance["prompt"])),
            (target or {}).get("program"),
            parse_cells(str(instance["table_text"])),
        )
        rescored.append({
            **row,
            "generated_text": normalized,
            "raw_generated_text": raw,
            "raw_format_valid": extract_target(raw) is not None,
            "syntax_adapter_applied": applied,
            "syntax_adapter_actions": actions,
            "format_valid": target is not None,
            "semantic_decision": decision,
            "semantic_reasons": reasons,
            "target_exact": canonical(target) == canonical(expected_target(instance)),
            **scored,
        })
    exposure = json.loads(args.exposure_receipt.read_text(encoding="utf-8"))
    summary = summarize(rescored, exposure)
    summary["identity"] = "RESCORED_WITH_COMMON_SYNTAX_ADAPTER"
    write_jsonl(args.output.with_suffix(".jsonl"), rescored)
    write_json(args.output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
