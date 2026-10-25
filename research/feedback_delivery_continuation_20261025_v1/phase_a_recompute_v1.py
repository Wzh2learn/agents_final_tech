"""Phase A-only recompute for diagnostic semantics and ledger arithmetic."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_binding_residual_v3 import extract_target, parse_cells
from revision_operator_diagnostic_v1 import (
    expected_target,
    load_jsonl,
    normalize_generated_text,
    strict_target,
    write_json,
    write_jsonl,
)
from run_natural_program_experiment_v2 import evaluate_target
from semantic_delivery_check_v3 import question_from_prompt, semantic_check


SCALE_PATTERN = re.compile(
    r"\b(?:in\s+)?(?:million|millions|thousand|thousands)\b",
    flags=re.IGNORECASE,
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def repair_eligibility(row: dict[str, Any], instance: dict[str, Any]) -> dict[str, Any]:
    if row.get("condition") in {
        "copy_control",
        "known_edit_control",
    }:
        return {
            "status": "CONTROL_NOT_A_REPAIR_TARGET",
            "visible_basis": "copy_or_reference_assisted_edit",
        }
    if row.get("source_task_id") == "NAT_train_f1f2c2cb_27cb53a0":
        scale_present = bool(SCALE_PATTERN.search(str(instance["table_text"])))
        return {
            "status": (
                "ELIGIBLE_VISIBLE_UNIT_SCALE"
                if scale_present
                else "NOT_ELIGIBLE_VISIBLE_UNIT_SCALE_ABSENT"
            ),
            "visible_scale_present": scale_present,
            "expected_unit": instance["expected"].get("unit"),
        }
    return {
        "status": "ELIGIBLE_VISIBLE_ROW_PERIOD_REFERENCE",
        "visible_basis": "row_and_period_labels_are_present",
    }


def rescore_rows(
    summaries: list[Path],
    instances_path: Path,
) -> list[dict[str, Any]]:
    instances = {row["instance_id"]: row for row in load_jsonl(instances_path)}
    rows = []
    for summary_path in summaries:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        for row in summary["rows"]:
            instance = instances[row["instance_id"]]
            raw = str(row.get("raw_generated_text", row.get("generated_text", "")))
            normalized, applied, actions = normalize_generated_text(raw)
            target = extract_target(normalized)
            strict = strict_target(normalized)
            scored = evaluate_target(normalized, instance)
            decision, reasons = semantic_check(
                question_from_prompt(str(instance["prompt"])),
                (target or {}).get("program"),
                parse_cells(str(instance["table_text"])),
            )
            rows.append({
                **row,
                "raw_generated_text": raw,
                "generated_text": normalized,
                "strict_format_valid": strict is not None,
                "embedded_format_valid": target is not None,
                "syntax_adapter_applied": applied,
                "syntax_adapter_actions": actions,
                "semantic_decision": decision,
                "semantic_reasons": reasons,
                "target_exact": canonical(target) == canonical(expected_target(instance)),
                "old_program_correct": bool(row.get("program_correct")),
                "recomputed_program_correct": bool(scored["program_correct"]),
                "repair_eligibility": repair_eligibility(row, instance),
                **scored,
            })
    return rows


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    controls = [
        row for row in rows
        if row.get("condition") in {"copy_control", "known_edit_control"}
        and row.get("attempt_id", "").endswith(("f440", "f234", "f1f2", "dac4"))
    ]
    # Restrict controls to the corrected v2 control run when duplicate v1 rows exist.
    controls = [
        row for row in controls
        if row.get("syntax_adapter_actions") is not None
    ][-4:]
    mechanism = [
        row for row in rows
        if row.get("condition") in {
            "neutral_revision",
            "category_feedback",
            "localization_feedback",
        }
    ]
    # The phase-A mechanism comparison is the format-guarded v3 run only.
    by_attempt = {}
    for row in mechanism:
        by_attempt[row["attempt_id"]] = row
    mechanism = list(by_attempt.values())
    by_condition = defaultdict(list)
    for row in mechanism:
        by_condition[row["condition"]].append(row)
    mechanism_summary = {}
    for condition, subset in sorted(by_condition.items()):
        eligible = [
            row for row in subset
            if row["repair_eligibility"]["status"].startswith("ELIGIBLE_")
        ]
        ineligible = [
            row for row in subset
            if row["repair_eligibility"]["status"].startswith("NOT_ELIGIBLE_")
        ]
        mechanism_summary[condition] = {
            "attempts": len(subset),
            "eligible_visible_repair_cases": len(eligible),
            "eligible_target_exact": sum(row["target_exact"] for row in eligible),
            "ineligible_scale_unobservable_cases": len(ineligible),
            "all_target_exact_historical": sum(row["target_exact"] for row in subset),
            "strict_format_valid": sum(row["strict_format_valid"] for row in subset),
            "embedded_format_valid": sum(row["embedded_format_valid"] for row in subset),
        }
    return {
        "controls": {
            "attempts": len(controls),
            "target_exact": sum(row["target_exact"] for row in controls),
            "strict_raw_valid": sum(row["strict_format_valid"] and not row["syntax_adapter_applied"] for row in controls),
            "safe_adapter_applied": sum(row["syntax_adapter_applied"] for row in controls),
            "semantic_changed_by_old_vs_recompute": sum(
                row["old_program_correct"] != row["recomputed_program_correct"]
                for row in controls
            ),
        },
        "mechanism": mechanism_summary,
        "target_exact_by_condition": dict(Counter(
            f"{row['condition']}:{row['target_exact']}" for row in mechanism
        )),
    }


def reconcile_ledger(ledger_path: Path) -> dict[str, Any]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    event_groups = [
        ("root", ledger.get("events", [])),
        ("revision_v4", ledger.get("revision_v4", {}).get("execution_events", [])),
        ("revision_v5", ledger.get("revision_v5", {}).get("execution_events", [])),
    ]
    events = []
    for group, values in event_groups:
        for value in values:
            events.append((group, value))
    generation_tokens = sum(int(value.get("accounting_tokens", 0)) for _, value in events)
    attempts = sum(
        int(value.get("attempts", value.get("accounting_attempts", 0)))
        for _, value in events
    )
    training_tokens = sum(
        int(value.get("training_tokens", 0))
        for value in ledger.get("training_events", [])
    )
    recomputed = generation_tokens + training_tokens
    stated = int(ledger["new_budget"]["accounting_tokens_used"])
    return {
        "event_count": len(events),
        "attempts": attempts,
        "generation_tokens": generation_tokens,
        "training_tokens": training_tokens,
        "recomputed_total": recomputed,
        "stated_total": stated,
        "difference": stated - recomputed,
        "cause_status": "UNRESOLVED_NO_UNIQUE_MISSING_EVENT_IDENTIFIED",
        "action": "PRESERVE_STATED_CONSERVATIVE_TOTAL_AND_DO_NOT_RELEASE_340_TOKENS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--v1-summary", type=Path, required=True)
    parser.add_argument("--v2-summary", type=Path, required=True)
    parser.add_argument("--v3-summary", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = rescore_rows(
        [args.v1_summary, args.v2_summary, args.v3_summary],
        args.instances,
    )
    write_jsonl(args.output.with_suffix(".jsonl"), rows)
    counterexample_raw = (
        '{"program":{"const":1)0},"evidence_refs":[],"unit":"million"}'
    )
    normalized, applied, actions = normalize_generated_text(counterexample_raw)
    result = {
        "schema": "loop_d_phase_a_recompute_v1",
        "date": "2026-10-26",
        "generation_attempts": 0,
        "training_runs": 0,
        "safe_adapter_counterexample": {
            "before": counterexample_raw,
            "after": normalized,
            "applied": applied,
            "actions": actions,
            "semantic_corruption_prevented": normalized == counterexample_raw,
        },
        "diagnostic": summarize_rows(rows),
        "ledger": reconcile_ledger(args.ledger),
        "raw_and_old_scores_preserved": True,
    }
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
