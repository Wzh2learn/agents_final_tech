"""Versioned correction and recompute for the first finance method experiment."""

from __future__ import annotations

import argparse
import ast
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
    parse_task_contract,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def file_hash(path: Path) -> str:
    """Return SHA-256 for one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_answer(value: Any) -> float | None:
    """Accept only literal numeric answers for direct-answer scoring."""
    return float(value) if type(value) in (int, float) else None


def legacy_formula_value(value: Any) -> float | None:
    """Evaluate a legacy numeric formula for historical lineage only."""
    try:
        node = ast.parse(str(value), mode="eval")
    except (SyntaxError, ValueError):
        return None

    def visit(item: ast.AST) -> float:
        if isinstance(item, ast.Expression):
            return visit(item.body)
        if isinstance(item, ast.Constant) and type(item.value) in (int, float):
            return float(item.value)
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, (ast.UAdd, ast.USub)):
            operand = visit(item.operand)
            return operand if isinstance(item.op, ast.UAdd) else -operand
        if isinstance(item, ast.BinOp):
            left = visit(item.left)
            right = visit(item.right)
            if isinstance(item.op, ast.Add):
                return left + right
            if isinstance(item.op, ast.Sub):
                return left - right
            if isinstance(item.op, ast.Mult):
                return left * right
            if isinstance(item.op, ast.Div):
                return left / right
        raise ValueError("unsupported_formula")

    try:
        result = visit(node)
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def close(left: float, right: float) -> bool:
    """Compare finite numeric results."""
    return math.isclose(left, right, rel_tol=1e-6, abs_tol=1e-6)


def score_instance(
    generation: dict[str, Any],
    instance: dict[str, Any],
) -> dict[str, Any]:
    """Score direct, visible-program, current-table tool and legacy metrics."""
    target = extract_legacy_target(generation["generated_text"])
    expected = instance["expected"]
    question = instance["question"]
    table_text = instance["table_text"]
    contract = parse_task_contract(question)
    direct_value = numeric_answer(target.get("answer")) if target else None
    direct_correct = direct_value is not None and close(direct_value, float(expected["answer"]))
    legacy_formula = legacy_formula_value(target.get("formula")) if target else None
    legacy_formula_correct = legacy_formula is not None and close(
        legacy_formula,
        float(expected["answer"]),
    )
    features = deployable_features(question, table_text, target or {})
    tool_value = None
    if target:
        try:
            tool_value = execute_program(question, table_text, target)
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            tool_value = None
    tool_correct = tool_value is not None and close(tool_value, float(expected["answer"]))
    program_correct = all_deployable_checks_pass(features)
    return {
        "instance_id": generation["instance_id"],
        "source_task_id": generation["source_task_id"],
        "table_uid": generation["table_uid"],
        "slice": generation["slice"],
        "variant": generation["variant"],
        "operator": contract.operator,
        "reference_unit": expected["unit"],
        "requested_unit": contract.requested_unit,
        "expected_answer": float(expected["answer"]),
        "direct_value": direct_value,
        "direct_correct": direct_correct,
        "legacy_formula_value": legacy_formula,
        "legacy_formula_correct": legacy_formula_correct,
        "tool_value": tool_value,
        "tool_result_correct": tool_correct,
        "visible_program_correct": program_correct,
        "deployable_features": features,
    }


def pair_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute task-equal paired outcomes without mixing answer and tool values."""
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["source_task_id"]][row["variant"]] = row
    direct_pairs = 0
    tool_pairs = 0
    legacy_mixed_pairs = 0
    task_rows: list[dict[str, Any]] = []
    for task_id, variants in sorted(grouped.items()):
        if set(variants) != {"original", "relevant_change", "irrelevant_change"}:
            raise ValueError(f"incomplete_variants:{task_id}")
        original = variants["original"]
        irrelevant = variants["irrelevant_change"]
        relevant = variants["relevant_change"]
        direct_invariant = (
            original["direct_value"] is not None
            and irrelevant["direct_value"] is not None
            and close(original["direct_value"], irrelevant["direct_value"])
        )
        direct_pair = (
            direct_invariant
            and original["direct_correct"]
            and relevant["direct_correct"]
            and irrelevant["direct_correct"]
        )
        tool_invariant = (
            original["tool_value"] is not None
            and irrelevant["tool_value"] is not None
            and close(original["tool_value"], irrelevant["tool_value"])
        )
        tool_pair = (
            tool_invariant
            and original["visible_program_correct"]
            and relevant["visible_program_correct"]
            and irrelevant["visible_program_correct"]
            and original["tool_result_correct"]
            and relevant["tool_result_correct"]
            and irrelevant["tool_result_correct"]
        )
        legacy_formula_all = all(
            variants[name]["legacy_formula_correct"]
            for name in ("original", "relevant_change", "irrelevant_change")
        )
        legacy_mixed_pair = legacy_formula_all and direct_invariant
        direct_pairs += int(direct_pair)
        tool_pairs += int(tool_pair)
        legacy_mixed_pairs += int(legacy_mixed_pair)
        task_rows.append(
            {
                "source_task_id": task_id,
                "table_uid": original["table_uid"],
                "operator": original["operator"],
                "direct_pair": direct_pair,
                "tool_pair": tool_pair,
                "legacy_mixed_pair": legacy_mixed_pair,
            }
        )
    count = len(task_rows)
    by_cluster: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in task_rows:
        by_cluster[row["table_uid"]].append(row)
    return {
        "paired_tasks": count,
        "table_clusters": len(by_cluster),
        "direct_pair_count": direct_pairs,
        "direct_pair_rate_task_equal": direct_pairs / count if count else None,
        "direct_pair_rate_table_cluster_equal": (
            sum(
                statistics_mean([float(row["direct_pair"]) for row in cluster_rows])
                for cluster_rows in by_cluster.values()
            )
            / len(by_cluster)
            if by_cluster
            else None
        ),
        "tool_pair_count": tool_pairs,
        "tool_pair_rate_task_equal": tool_pairs / count if count else None,
        "tool_pair_rate_table_cluster_equal": (
            sum(
                statistics_mean([float(row["tool_pair"]) for row in cluster_rows])
                for cluster_rows in by_cluster.values()
            )
            / len(by_cluster)
            if by_cluster
            else None
        ),
        "legacy_mixed_pair_count": legacy_mixed_pairs,
        "legacy_mixed_pair_rate_task_equal": legacy_mixed_pairs / count if count else None,
        "task_rows": task_rows,
    }


def statistics_mean(values: list[float]) -> float:
    """Return a finite mean or zero."""
    return sum(values) / len(values) if values else 0.0


def aggregate_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate corrected metrics by model and slice."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["target_model_arm"], row["slice"])].append(row)
    metrics: dict[str, Any] = {}
    for (arm, slice_name), subset in sorted(grouped.items()):
        operators = Counter(row["operator"] for row in subset)
        units = Counter(row["reference_unit"] for row in subset)
        item_metrics = {
            "items": len(subset),
            "operators": dict(operators),
            "reference_units": dict(units),
            "direct_correct_instances": sum(row["direct_correct"] for row in subset),
            "legacy_formula_correct_instances": sum(
                row["legacy_formula_correct"] for row in subset
            ),
            "visible_program_correct_instances": sum(
                row["visible_program_correct"] for row in subset
            ),
            "tool_result_correct_instances": sum(
                row["tool_result_correct"] for row in subset
            ),
        }
        if slice_name != "dev":
            item_metrics["paired"] = pair_metrics(subset)
        metrics.setdefault(arm, {})[slice_name] = item_metrics
    return metrics


def task_composition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize task type, units and numeric-scale composition by slice."""
    output: dict[str, Any] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["slice"], row["source_task_id"])
        if key in seen:
            continue
        seen.add(key)
        answer = abs(float(row["expected_answer"]))
        scale = (
            "zero"
            if answer == 0
            else "<1"
            if answer < 1
            else "1-100"
            if answer < 100
            else "100-10000"
            if answer < 10000
            else ">=10000"
        )
        bucket = output.setdefault(
            row["slice"],
            {
                "tasks": 0,
                "operators": Counter(),
                "reference_units": Counter(),
                "numeric_scale": Counter(),
            },
        )
        bucket["tasks"] += 1
        bucket["operators"][row["operator"]] += 1
        bucket["reference_units"][row["reference_unit"]] += 1
        bucket["numeric_scale"][scale] += 1
    for bucket in output.values():
        for name in ("operators", "reference_units", "numeric_scale"):
            bucket[name] = dict(bucket[name])
    return output


def rebuild_training_summary(run_root: Path) -> dict[str, Any]:
    """Rebuild all six training arms from immutable per-arm receipts."""
    receipts: dict[str, Any] = {}
    for receipt_path in sorted((run_root / "training").glob("*/training_receipt.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipts[str(receipt["arm"])] = receipt
    return {
        "schema": "financial_feedback_training_summary_v2",
        "date": "2026-10-24",
        "identity": "DERIVED_AGGREGATE_FROM_SIX_IMMUTABLE_ARM_RECEIPTS",
        "arms": receipts,
        "totals": {
            "arms": len(receipts),
            "rows": sum(receipt["rows"] for receipt in receipts.values()),
            "prompt_tokens": sum(receipt["prompt_tokens"] for receipt in receipts.values()),
            "completion_tokens": sum(
                receipt["completion_tokens"] for receipt in receipts.values()
            ),
            "accounting_tokens": sum(
                receipt["prompt_tokens"] + receipt["completion_tokens"]
                for receipt in receipts.values()
            ),
            "gpu_seconds": sum(
                receipt["train_runtime_seconds"] for receipt in receipts.values()
            ),
        },
    }


def main() -> int:
    """Write corrected metrics and aggregate training receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--metrics-output", type=Path, required=True)
    parser.add_argument("--training-output", type=Path, required=True)
    args = parser.parse_args()
    rows = load_jsonl(args.run_root / "generation_results.jsonl")
    instances = {
        row["instance_id"]: row
        for row in load_jsonl(args.run_root / "evaluation_instances.jsonl")
    }
    scored = [
        {**score_instance(row, instances[row["instance_id"]]), "target_model_arm": row["model_arm"]}
        for row in rows
    ]
    training_summary = rebuild_training_summary(args.run_root)
    output = {
        "schema": "financial_feedback_corrected_metrics_v2",
        "date": "2026-10-24",
        "evidence_identity": "POST_HOC_CORRECTED_RECOMPUTE_NOT_PREREGISTERED_DEPLOYMENT_SUCCESS",
        "raw_sha256": file_hash(args.run_root / "generation_results.jsonl"),
        "evaluation_instances_sha256": file_hash(
            args.run_root / "evaluation_instances.jsonl"
        ),
        "strict_delivery_note": "No legacy output satisfies the strict v2 deployment contract; recovered legacy targets remain diagnostics.",
        "task_composition": task_composition(scored),
        "metrics": aggregate_metrics(scored),
        "training_totals": training_summary["totals"],
        "new_model_calls": 0,
        "new_training_runs": 0,
        "new_judge_calls": 0,
    }
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.training_output.parent.mkdir(parents=True, exist_ok=True)
    args.training_output.write_text(
        json.dumps(training_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"metrics_output": str(args.metrics_output), "training_output": str(args.training_output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

