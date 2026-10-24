"""Run a frozen same-source new-family confirmation for two existing adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from build_natural_tasks_v2 import natural_rule_candidate
from natural_variant_measurement_v3 import extract_prompt_table
from run_natural_program_experiment_v2 import (
    generate_and_score_batch,
    make_variants,
    stable_hash,
    training_rows,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def corrected_variants(task: dict[str, Any]) -> list[dict[str, Any]]:
    variants = []
    for variant in make_variants(task):
        variant = dict(variant)
        variant["table_text"] = extract_prompt_table(variant["prompt"])
        variants.append(variant)
    return variants


def select_tasks(
    tasks: list[dict[str, Any]],
    prior_instances_path: Path,
) -> list[dict[str, Any]]:
    training_ids = {
        row["task_id"] for row in training_rows(tasks, "ordinary_answer_execution_sft")
    }
    prior_table_ids = {
        row["table_uid"] for row in load_jsonl(prior_instances_path)
    }
    candidates = [
        task for task in tasks
        if task["split"] == "train"
        and task["task_id"] not in training_ids
        and task["table_uid"] not in prior_table_ids
    ]
    candidates.sort(key=lambda task: stable_hash(task["task_id"]))
    selected = []
    seen_tables = set()
    for task in candidates:
        if task["table_uid"] in seen_tables:
            continue
        selected.append(task)
        seen_tables.add(task["table_uid"])
        if len(selected) == 24:
            break
    if len(selected) != 24:
        raise ValueError(f"insufficient_unseen_families:{len(selected)}")
    return selected


def build_instances(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for task in tasks:
        for variant in corrected_variants(task):
            selected.append({
                "instance_id": f"{task['task_id']}::{variant['variant']}",
                "source_task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "slice": "confirmation",
                "variant": variant["variant"],
                "prompt": variant["prompt"],
                "expected": variant["expected"],
                "table_text": variant["table_text"],
            })
    return selected


def bootstrap_difference(rows: list[dict[str, Any]], key: str, repetitions: int = 5000) -> dict[str, Any]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["source_task_id"]][row["model_arm"]] = row
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for task_id, arms in grouped.items():
        if set(arms) != {"ordinary_answer_execution_sft", "visible_program_filter_sft"}:
            continue
        left = arms["ordinary_answer_execution_sft"]
        right = arms["visible_program_filter_sft"]
        by_cluster[left["table_uid"]].append(float(left[key]) - float(right[key]))
    clusters = sorted(by_cluster)
    observed = sum(sum(values) / len(values) for values in by_cluster.values()) / len(clusters)
    rng = random.Random(20261024)
    samples = []
    for _ in range(repetitions):
        chosen = [rng.choice(clusters) for _ in clusters]
        samples.append(sum(
            sum(by_cluster[cluster]) / len(by_cluster[cluster])
            for cluster in chosen
        ) / len(chosen))
    samples.sort()
    return {
        "metric": key,
        "ordinary_minus_visible": observed,
        "ci95": [samples[int(0.025 * repetitions)], samples[int(0.975 * repetitions)]],
        "table_clusters": len(clusters),
    }


def analyze(rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    task_rows: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        task_rows[(row["model_arm"], row["source_task_id"])][row["variant"]] = row
    metrics = {}
    paired_rows = []
    for (arm, task_id), variants in sorted(task_rows.items()):
        if {"original", "relevant_change", "irrelevant_change"} - set(variants):
            continue
        item = {
            "model_arm": arm,
            "source_task_id": task_id,
            "table_uid": variants["original"]["table_uid"],
            "original_correct": bool(variants["original"]["program_correct"]),
            "relevant_adaptation": bool(
                variants["original"]["program_correct"]
                and variants["relevant_change"]["program_correct"]
            ),
            "irrelevant_invariance": bool(
                variants["original"]["program_correct"]
                and variants["irrelevant_change"]["program_correct"]
            ),
            "paired_all_three": bool(all(
                variants[name]["program_correct"]
                for name in ("original", "relevant_change", "irrelevant_change")
            )),
        }
        paired_rows.append(item)
    for arm in sorted({row["model_arm"] for row in paired_rows}):
        subset = [row for row in paired_rows if row["model_arm"] == arm]
        metrics[arm] = {
            "tasks": len(subset),
            **{
                f"{key}_rate": sum(float(row[key]) for row in subset) / len(subset)
                for key in ("original_correct", "relevant_adaptation", "irrelevant_invariance", "paired_all_three")
            },
        }
    comparison = {
        key: bootstrap_difference(paired_rows, key)
        for key in ("original_correct", "relevant_adaptation", "irrelevant_invariance", "paired_all_three")
    }
    return {
        "metrics": metrics,
        "ordinary_minus_visible": comparison,
        "transparent_baseline": {
            "tasks": len(baseline_rows),
            "solved": sum(bool(row["solved"]) for row in baseline_rows),
            "accuracy": sum(bool(row["solved"]) for row in baseline_rows) / len(baseline_rows),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--prior-instances", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("status") != "FROZEN_BEFORE_CONFIRMATION":
        raise ValueError("protocol_not_frozen")
    tasks = load_jsonl(args.tasks)
    selected = select_tasks(tasks, args.prior_instances)
    instances = build_instances(selected)
    args.run_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.run_root / "confirmation_instances_v3.jsonl", instances)
    baseline_rows = []
    for task in selected:
        candidate = natural_rule_candidate(task)
        baseline_rows.append({
            "task_id": task["task_id"],
            "table_uid": task["table_uid"],
            "solved": bool(candidate) and abs(float(candidate["answer"]) - float(task["expected"]["answer"])) < 1e-6,
        })
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = []
    receipts = {}
    for arm in protocol["models"]:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        model = PeftModel.from_pretrained(model, args.adapter_root / arm / "final_adapter")
        model.eval()
        started = time.time()
        arm_rows = []
        for start in range(0, len(instances), 16):
            batch = generate_and_score_batch(model, tokenizer, instances[start:start + 16], 256)
            for row in batch:
                row["model_arm"] = arm
                arm_rows.append(row)
                rows.append(row)
            with (args.run_root / "confirmation_results_v3.partial.jsonl").open(
                "a", encoding="utf-8", newline="\n"
            ) as handle:
                for row in batch:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            print(f"{arm}: {len(arm_rows)}/{len(instances)}", flush=True)
        receipts[arm] = {
            "attempts": len(arm_rows),
            "prompt_tokens": sum(row["prompt_tokens"] for row in arm_rows),
            "completion_tokens": sum(row["completion_tokens"] for row in arm_rows),
            "wall_seconds": time.time() - started,
        }
        del model
        torch.cuda.empty_cache()
    write_jsonl(args.run_root / "confirmation_results_v3.jsonl", rows)
    summary = analyze(rows, baseline_rows)
    write_json(args.run_root / "CONFIRMATION_SUMMARY_V3.json", {
        "schema": "natural_tatqa_confirmation_summary_v3",
        "identity": "FROZEN_SAME_SOURCE_NEW_TABLE_FAMILY_CONFIRMATION",
        "protocol_sha256": sha256_file(args.protocol),
        "instances": len(instances),
        "accounting_attempts": sum(item["attempts"] for item in receipts.values()),
        "prompt_tokens": sum(item["prompt_tokens"] for item in receipts.values()),
        "completion_tokens": sum(item["completion_tokens"] for item in receipts.values()),
        "models": receipts,
        "new_training_runs": 0,
        "new_judge_calls": 0,
        **summary,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
