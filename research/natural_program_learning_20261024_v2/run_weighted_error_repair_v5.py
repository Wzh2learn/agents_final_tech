"""Retry natural-error feedback with task diversity preserved."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from run_natural_error_repair_v4 import (
    build_confirm_instances,
    corrected_target,
    load_jsonl,
    paired_metrics,
    sha256_file,
    write_json,
    write_jsonl,
)
from run_natural_program_experiment_v2 import generate_and_score_batch, train_arm, target_text


def weighted_rows(
    tasks: list[dict[str, Any]],
    corrected: dict[str, Any],
    wrong_ids: set[str],
    arm: str,
) -> list[dict[str, Any]]:
    rng = random.Random(20261024)
    wrong = [task for task in tasks if task["task_id"] in wrong_ids]
    rows: list[dict[str, Any]] = []
    if arm == "weighted_error_repair_sft":
        for task in wrong:
            for _ in range(16):
                rows.append({
                    "row_id": f"{task['task_id']}::{arm}::{len(rows)}",
                    "task_id": task["task_id"],
                    "table_uid": task["table_uid"],
                    "target": corrected[task["task_id"]],
                    "text": task["prompt"] + "\n" + target_text(corrected[task["task_id"]]),
                })
        filler = tasks[:]
        rng.shuffle(filler)
        filler_index = 0
        while len(rows) < 256:
            task = filler[filler_index % len(filler)]
            filler_index += 1
            rows.append({
                "row_id": f"{task['task_id']}::{arm}::{len(rows)}",
                "task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "target": corrected[task["task_id"]],
                "text": task["prompt"] + "\n" + target_text(corrected[task["task_id"]]),
            })
    else:
        filler = tasks[:]
        rng.shuffle(filler)
        while len(rows) < 256:
            task = filler[len(rows) % len(filler)]
            rows.append({
                "row_id": f"{task['task_id']}::{arm}::{len(rows)}",
                "task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "target": corrected[task["task_id"]],
                "text": task["prompt"] + "\n" + target_text(corrected[task["task_id"]]),
            })
    return rows[:256]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--baseline-results", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    tasks = load_jsonl(args.tasks)
    error_pool = tasks[:48]
    confirm_tasks = tasks[72:96]
    corrected = {}
    eligible_error = []
    eligible_confirm = []
    for task in error_pool:
        target = corrected_target(task)
        if target is not None:
            corrected[task["task_id"]] = target
            eligible_error.append(task)
    for task in confirm_tasks:
        target = corrected_target(task)
        if target is not None:
            corrected[task["task_id"]] = target
            eligible_confirm.append(task)
    baseline = load_jsonl(args.baseline_results)
    wrong_ids = {row["source_task_id"] for row in baseline if not row["program_correct"]}
    wrong_ids &= {task["task_id"] for task in eligible_error}
    if len(wrong_ids) < 8 or len(eligible_confirm) < 24:
        raise ValueError(f"insufficient_diverse_inputs:{len(wrong_ids)}:{len(eligible_confirm)}")
    args.run_root.mkdir(parents=True, exist_ok=False)
    confirm_instances = build_confirm_instances(eligible_confirm[:24])
    write_jsonl(args.run_root / "weighted_confirmation_instances_v5.jsonl", confirm_instances)
    training_receipts = {
        arm: train_arm(
            arm,
            weighted_rows(eligible_error, corrected, wrong_ids, arm),
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
        )
        for arm in ("weighted_error_repair_sft", "uniform_mixed_control_sft")
    }
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = []
    generation_receipts = {}
    for arm in ("ordinary_answer_execution_sft", "weighted_error_repair_sft", "uniform_mixed_control_sft"):
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
            with (args.run_root / "weighted_confirmation_results_v5.partial.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
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
    write_jsonl(args.run_root / "weighted_confirmation_results_v5.jsonl", rows)
    write_json(args.run_root / "WEIGHTED_ERROR_REPAIR_SUMMARY_V5.json", {
        "schema": "weighted_error_repair_summary_v5",
        "identity": "DIVERSITY_PRESERVING_NATURAL_ERROR_FEEDBACK_WITH_UNIFORM_CONTROL",
        "error_pool_tasks": len(eligible_error),
        "natural_error_tasks": len(wrong_ids),
        "confirmation_tasks": 24,
        "training": training_receipts,
        "generation": generation_receipts,
        "metrics": paired_metrics(rows),
        "new_judge_calls": 0,
        "results_sha256": sha256_file(args.run_root / "weighted_confirmation_results_v5.jsonl"),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
