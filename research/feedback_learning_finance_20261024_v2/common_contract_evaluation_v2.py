"""Evaluate a transparent row/period solver and legacy checkpoints under one tool contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from deployable_tool_contract_v2 import (
    all_deployable_checks_pass,
    deployable_features,
    execute_program,
    extract_legacy_target,
    extract_visible_table_from_prompt,
    normalize_label,
    parse_task_contract,
    parse_visible_table,
    period_label_matches,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def file_hash(path: Path) -> str:
    """Hash a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float) -> bool:
    """Compare finite results."""
    return math.isclose(left, right, rel_tol=1e-6, abs_tol=1e-6)


def transparent_candidate(question: str, table_text: str) -> dict[str, Any]:
    """Solve the explicit row/period template without model or hidden reference."""
    contract = parse_task_contract(question)
    cells = parse_visible_table(table_text)
    row_ids = sorted(
        {
            cell.row_id
            for cell in cells.values()
            if normalize_label(cell.row_label) == normalize_label(contract.scope)
        }
    )
    if len(row_ids) != 1:
        raise ValueError("scope_not_unique")
    row_id = row_ids[0]
    row_cells = [cell for cell in cells.values() if cell.row_id == row_id]
    prior = [cell for cell in row_cells if period_label_matches(contract.prior_period, cell.column_label)]
    current = [cell for cell in row_cells if period_label_matches(contract.current_period, cell.column_label)]
    if len(prior) != 1 or len(current) != 1:
        raise ValueError("period_operands_not_unique")
    return {
        "operator": contract.operator,
        "requested_unit": contract.requested_unit,
        "evidence_refs": [prior[0].ref, current[0].ref],
    }


def classify_failure(features: dict[str, Any]) -> str:
    """Return the first visible failure stage for a candidate."""
    if not features["contract_parseable"]:
        return "task_contract_parse"
    if not features["candidate_parseable"]:
        return "candidate_parse"
    if not features["refs_unique"]:
        return "duplicate_refs"
    if not features["refs_valid"]:
        return "evidence_ref_binding"
    if not features["scope_match"]:
        return "scope_binding"
    if not features["period_match"]:
        return "period_binding"
    if not features["operator_match"]:
        return "operator_selection"
    if not features["unit_match"]:
        return "unit_contract"
    if not features["tool_executable"]:
        return "tool_execution"
    return "none"


def evaluate_candidate(
    instance: dict[str, Any],
    candidate: dict[str, Any],
    failure_override: str | None = None,
) -> dict[str, Any]:
    """Score one candidate using visible contract and hidden reference only at the end."""
    question = instance["question"]
    table_text = extract_visible_table_from_prompt(instance["prompt"])
    features = deployable_features(question, table_text, candidate)
    tool_value = None
    try:
        tool_value = execute_program(question, table_text, candidate)
    except (ValueError, TypeError, KeyError, ZeroDivisionError):
        tool_value = None
    expected = float(instance["expected"]["answer"])
    tool_correct = tool_value is not None and close(tool_value, expected)
    deployment_correct = all_deployable_checks_pass(features) and tool_correct
    return {
        "instance_id": instance["instance_id"],
        "source_task_id": instance["source_task_id"],
        "table_uid": instance["table_uid"],
        "slice": instance["slice"],
        "variant": instance["variant"],
        "operator": parse_task_contract(question).operator,
        "tool_value": tool_value,
        "expected": expected,
        "tool_correct": tool_correct,
        "deployment_correct": deployment_correct,
        "failure": failure_override or classify_failure(features),
        "features": features,
    }


def paired_from_rows(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Compute three-variant paired success from deployment/tool rows."""
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["source_task_id"]][row["variant"]] = row
    successes = 0
    task_rows = []
    for task_id, variants in sorted(grouped.items()):
        if set(variants) != {"original", "relevant_change", "irrelevant_change"}:
            continue
        success = all(bool(variants[name][key]) for name in variants)
        successes += int(success)
        task_rows.append(
            {
                "source_task_id": task_id,
                "table_uid": variants["original"]["table_uid"],
                "success": success,
            }
        )
    return {
        "paired_tasks": len(task_rows),
        "success_count": successes,
        "success_rate_task_equal": successes / len(task_rows) if task_rows else 0.0,
        "task_rows": task_rows,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize failure and paired outcomes by slice."""
    output: dict[str, Any] = {}
    for slice_name in sorted({row["slice"] for row in rows}):
        subset = [row for row in rows if row["slice"] == slice_name]
        output[slice_name] = {
            "instances": len(subset),
            "tool_correct_instances": sum(row["tool_correct"] for row in subset),
            "deployment_correct_instances": sum(
                row["deployment_correct"] for row in subset
            ),
            "failure_counts": dict(Counter(row["failure"] for row in subset)),
            "paired_tool": paired_from_rows(subset, "tool_correct"),
            "paired_deployment": paired_from_rows(subset, "deployment_correct"),
        }
    return output


def main() -> int:
    """Run transparent and legacy-checkpoint contract evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    instances = {
        row["instance_id"]: row
        for row in load_jsonl(args.run_root / "evaluation_instances.jsonl")
    }
    generations = load_jsonl(args.run_root / "generation_results.jsonl")
    baseline_rows = []
    for instance in instances.values():
        table_text = extract_visible_table_from_prompt(instance["prompt"])
        try:
            candidate = transparent_candidate(instance["question"], table_text)
            baseline_rows.append(evaluate_candidate(instance, candidate))
        except ValueError as exc:
            baseline_rows.append(
                evaluate_candidate(
                    instance,
                    {},
                    failure_override=f"transparent_{exc}",
                )
            )
    model_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for generation in generations:
        instance = instances[generation["instance_id"]]
        target = extract_legacy_target(generation["generated_text"])
        candidate = target or {}
        scored = evaluate_candidate(instance, candidate)
        scored["model_arm"] = generation["model_arm"]
        model_rows[generation["model_arm"]].append(scored)
    output = {
        "schema": "common_tool_contract_evaluation_v2",
        "date": "2026-10-24",
        "identity": "VISIBLE_INPUT_DEPLOYMENT_REPLAY_WITH_HIDDEN_REFERENCE_FINAL_SCORING_ONLY",
        "source_hashes": {
            "evaluation_instances": file_hash(args.run_root / "evaluation_instances.jsonl"),
            "generation_results": file_hash(args.run_root / "generation_results.jsonl"),
        },
        "transparent_row_year_calculator": summarize(baseline_rows),
        "legacy_checkpoint_adapter": {
            arm: summarize(rows) for arm, rows in sorted(model_rows.items())
        },
        "new_model_calls": 0,
        "new_training_runs": 0,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "baseline": output["transparent_row_year_calculator"],
        "models": {
            arm: {
                slice_name: {
                    "deployment": metrics["deployment_correct_instances"],
                    "tool": metrics["tool_correct_instances"],
                    "paired_deployment": metrics["paired_deployment"]["success_rate_task_equal"],
                }
                for slice_name, metrics in slices.items()
            }
            for arm, slices in output["legacy_checkpoint_adapter"].items()
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

