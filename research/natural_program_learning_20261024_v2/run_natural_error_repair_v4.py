"""Natural-error-targeted feedback SFT with a cost-matched random control."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from natural_variant_measurement_v3 import extract_prompt_table
from analyze_binding_residual_v3 import parse_cells
from run_natural_program_experiment_v2 import (
    generate_and_score_batch,
    make_variants,
    program_refs,
    target_text,
    train_arm,
)
from source_role_contract_v3 import classify_average_denominator


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def corrected_target(task: dict[str, Any]) -> dict[str, Any] | None:
    program = deepcopy(task["target"]["program"])
    question = str(task["question"])
    cells = parse_cells(str(task["table_text"]))
    unresolved = False

    def visit(node: Any) -> None:
        nonlocal unresolved
        if not isinstance(node, dict):
            return
        if node.get("op") == "div" and isinstance(node.get("right"), dict):
            right = node["right"]
            ref = right.get("ref")
            cell = cells.get(str(ref))
            label = classify_average_denominator(question, right, cell, node.get("left"))
            if label == "STRUCTURAL_CONSTANT_MISBOUND":
                node["right"] = {"const": float(cell["value"])}
            elif label == "UNRESOLVED_REFERENCE_QUESTION_MISMATCH":
                unresolved = True
        visit(node.get("left"))
        visit(node.get("right"))

    visit(program)
    if unresolved:
        return None
    return {
        "program": program,
        "evidence_refs": program_refs(program),
        "unit": task["target"]["unit"],
    }


def make_original_instance(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "instance_id": f"{task['task_id']}::original",
        "source_task_id": task["task_id"],
        "table_uid": task["table_uid"],
        "slice": "error_pool",
        "variant": "original",
        "prompt": task["prompt"],
        "expected": task["expected"],
        "table_text": task["table_text"],
    }


def build_confirm_instances(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for task in tasks:
        for variant in make_variants(task):
            output.append({
                "instance_id": f"{task['task_id']}::{variant['variant']}",
                "source_task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "slice": "error_repair_confirmation",
                "variant": variant["variant"],
                "prompt": variant["prompt"],
                "expected": variant["expected"],
                "table_text": extract_prompt_table(variant["prompt"]),
            })
    return output


def paired_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(row["model_arm"], row["source_task_id"])][row["variant"]] = row
    metrics = {}
    for arm in sorted({key[0] for key in grouped}):
        items = []
        for (row_arm, _task), variants in grouped.items():
            if row_arm != arm or {"original", "relevant_change", "irrelevant_change"} - set(variants):
                continue
            items.append({
                "original": bool(variants["original"]["program_correct"]),
                "relevant": bool(variants["original"]["program_correct"] and variants["relevant_change"]["program_correct"]),
                "irrelevant": bool(variants["original"]["program_correct"] and variants["irrelevant_change"]["program_correct"]),
                "paired": bool(all(variants[name]["program_correct"] for name in ("original", "relevant_change", "irrelevant_change"))),
            })
        metrics[arm] = {
            "tasks": len(items),
            **{f"{key}_rate": sum(item[key] for item in items) / len(items) for key in ("original", "relevant", "irrelevant", "paired")},
        }
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    tasks = load_jsonl(args.tasks)
    if len(tasks) < 72:
        raise ValueError("not_enough_source_disjoint_tasks")
    corrected = {}
    eligible = []
    for task in tasks:
        target = corrected_target(task)
        if target is not None:
            corrected[task["task_id"]] = target
            eligible.append(task)
    error_pool = eligible[:48]
    confirm_tasks = eligible[48:72]
    if len(confirm_tasks) < 24:
        raise ValueError("not_enough_corrected_confirmation_tasks")
    args.run_root.mkdir(parents=True, exist_ok=False)
    error_instances = [make_original_instance(task) for task in error_pool]
    write_jsonl(args.run_root / "error_pool_instances_v4.jsonl", error_instances)
    confirm_instances = build_confirm_instances(confirm_tasks)
    write_jsonl(args.run_root / "error_repair_confirmation_instances_v4.jsonl", confirm_instances)
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model = PeftModel.from_pretrained(
        model,
        args.adapter_root / "ordinary_answer_execution_sft" / "final_adapter",
    )
    model.eval()
    baseline_rows = []
    for start in range(0, len(error_instances), 16):
        batch = generate_and_score_batch(model, tokenizer, error_instances[start:start + 16], 256)
        baseline_rows.extend(batch)
        with (args.run_root / "error_pool_baseline_v4.partial.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            for row in batch:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    write_jsonl(args.run_root / "error_pool_baseline_v4.jsonl", baseline_rows)
    wrong_ids = {
        row["source_task_id"] for row in baseline_rows if not row["program_correct"]
    }
    if len(wrong_ids) < 8:
        raise ValueError(f"too_few_natural_errors:{len(wrong_ids)}")
    wrong_tasks = [task for task in error_pool if task["task_id"] in wrong_ids]
    rng = random.Random(20261024)
    control_tasks = rng.sample(error_pool, min(len(error_pool), len(wrong_tasks)))
    def rows_for(tasks: list[dict[str, Any]], arm: str) -> list[dict[str, Any]]:
        rows = []
        index = 0
        while len(rows) < 256:
            task = tasks[index % len(tasks)]
            rows.append({
                "row_id": f"{task['task_id']}::{arm}::{len(rows)}",
                "task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "target": corrected[task["task_id"]],
                "text": task["prompt"] + "\n" + target_text(corrected[task["task_id"]]),
            })
            index += 1
        return rows
    training_receipts = {
        "natural_error_repair_sft": train_arm(
            "natural_error_repair_sft",
            rows_for(wrong_tasks, "natural_error_repair_sft"),
            args.run_root,
            {
                "model_path_gb10": str(args.model_path),
                "max_steps_per_arm": 256,
                "max_length": 1536,
                "learning_rate": 0.0001,
                "lora_r": 16,
                "lora_alpha": 32,
                "target_modules": ["q_proj", "v_proj"],
                "seed": 20261024,
            },
        ),
        "random_additional_sft": train_arm(
            "random_additional_sft",
            rows_for(control_tasks, "random_additional_sft"),
            args.run_root,
            {
                "model_path_gb10": str(args.model_path),
                "max_steps_per_arm": 256,
                "max_length": 1536,
                "learning_rate": 0.0001,
                "lora_r": 16,
                "lora_alpha": 32,
                "target_modules": ["q_proj", "v_proj"],
                "seed": 20261024,
            },
        ),
    }
    del model
    torch.cuda.empty_cache()
    rows = []
    generation_receipts = {}
    for arm in ("ordinary_answer_execution_sft", "natural_error_repair_sft", "random_additional_sft"):
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        adapter = (
            args.adapter_root / arm / "final_adapter"
            if arm == "ordinary_answer_execution_sft"
            else args.run_root / "training" / arm / "final_adapter"
        )
        model = PeftModel.from_pretrained(model, adapter)
        model.eval()
        started = time.time()
        arm_rows = []
        for start in range(0, len(confirm_instances), 16):
            batch = generate_and_score_batch(model, tokenizer, confirm_instances[start:start + 16], 256)
            for row in batch:
                row["model_arm"] = arm
                arm_rows.append(row)
                rows.append(row)
            with (args.run_root / "error_repair_confirmation_v4.partial.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                for row in batch:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        generation_receipts[arm] = {
            "attempts": len(arm_rows),
            "prompt_tokens": sum(row["prompt_tokens"] for row in arm_rows),
            "completion_tokens": sum(row["completion_tokens"] for row in arm_rows),
            "wall_seconds": time.time() - started,
        }
        del model
        torch.cuda.empty_cache()
    write_jsonl(args.run_root / "error_repair_confirmation_results_v4.jsonl", rows)
    write_json(args.run_root / "NATURAL_ERROR_REPAIR_SUMMARY_V4.json", {
        "schema": "natural_error_repair_summary_v4",
        "identity": "NATURAL_ERROR_TARGETED_FEEDBACK_SFT_WITH_RANDOM_CONTROL",
        "error_pool_tasks": len(error_pool),
        "natural_error_tasks": len(wrong_ids),
        "confirmation_tasks": len(confirm_tasks),
        "training": training_receipts,
        "generation": generation_receipts,
        "metrics": paired_metrics(rows),
        "new_judge_calls": 0,
        "results_sha256": sha256_file(args.run_root / "error_repair_confirmation_results_v4.jsonl"),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
