"""Train and confirm cost-matched evidence-stability supervision."""

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
    program_refs,
    stable_hash,
    target_text,
    train_arm,
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
    output = []
    for variant in make_variants(task):
        variant = dict(variant)
        variant["table_text"] = extract_prompt_table(variant["prompt"])
        output.append(variant)
    return output


def selected_variant(task: dict[str, Any]) -> dict[str, Any]:
    variants = {
        variant["variant"]: variant
        for variant in corrected_variants(task)
    }
    preferred = (
        "relevant_change"
        if int(stable_hash(task["task_id"] + "::paired_variant")[:8], 16) % 2 == 0
        else "irrelevant_change"
    )
    if preferred in variants:
        return variants[preferred]
    for name in ("irrelevant_change", "relevant_change"):
        if name in variants:
            return variants[name]
    raise ValueError(f"no_counterfactual_variant:{task['task_id']}")


def build_training_rows(tasks: list[dict[str, Any]], arm: str) -> list[dict[str, Any]]:
    train_tasks = [task for task in tasks if task["split"] == "train"]
    train_tasks = sorted(train_tasks, key=lambda task: stable_hash(task["task_id"]))[:512]
    rows = []
    for task in train_tasks:
        target = target_text(task["target"])
        if arm == "duplicate_original_control_sft":
            prompts = [task["prompt"], task["prompt"]]
        elif arm == "paired_variant_stability_sft":
            variant = selected_variant(task)
            prompts = [task["prompt"], variant["prompt"]]
        else:
            raise ValueError(f"unknown_arm:{arm}")
        for index, prompt in enumerate(prompts):
            rows.append({
                "row_id": f"{task['task_id']}::{arm}::{index}",
                "task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "target": task["target"],
                "text": prompt + "\n" + target,
            })
    return rows


def select_confirmation_tasks(
    tasks: list[dict[str, Any]],
    prior_instances: Path,
    first_confirmation_instances: Path,
) -> list[dict[str, Any]]:
    training_ids = {
        row["task_id"] for row in training_rows(tasks, "ordinary_answer_execution_sft")
    }
    excluded_tables = {
        row["table_uid"]
        for path in (prior_instances, first_confirmation_instances)
        for row in load_jsonl(path)
    }
    candidates = [
        task for task in tasks
        if task["split"] == "train"
        and task["task_id"] not in training_ids
        and task["table_uid"] not in excluded_tables
    ]
    candidates.sort(key=lambda task: stable_hash(task["task_id"]))
    selected = []
    seen = set()
    for task in candidates:
        if task["table_uid"] in seen:
            continue
        selected.append(task)
        seen.add(task["table_uid"])
        if len(selected) == 24:
            break
    if len(selected) != 24:
        raise ValueError(f"insufficient_confirmation_tasks:{len(selected)}")
    return selected


def build_instances(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for task in tasks:
        for variant in corrected_variants(task):
            output.append({
                "instance_id": f"{task['task_id']}::{variant['variant']}",
                "source_task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "slice": "stability_confirmation",
                "variant": variant["variant"],
                "prompt": variant["prompt"],
                "expected": variant["expected"],
                "table_text": variant["table_text"],
            })
    return output


def paired_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(row["model_arm"], row["source_task_id"])][row["variant"]] = row
    output = []
    for (arm, task_id), variants in sorted(grouped.items()):
        if {"original", "relevant_change", "irrelevant_change"} - set(variants):
            continue
        original_refs = set(program_refs(variants["original"].get("parsed_program") or {}))
        relevant_refs = set(program_refs(variants["relevant_change"].get("parsed_program") or {}))
        irrelevant_refs = set(program_refs(variants["irrelevant_change"].get("parsed_program") or {}))
        output.append({
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
            "reference_stability": bool(
                original_refs
                and original_refs == relevant_refs == irrelevant_refs
            ),
        })
    return output


def bootstrap_difference(
    rows: list[dict[str, Any]],
    left_arm: str,
    right_arm: str,
    key: str,
    repetitions: int = 5000,
) -> dict[str, Any]:
    left = {row["source_task_id"]: row for row in rows if row["model_arm"] == left_arm}
    right = {row["source_task_id"]: row for row in rows if row["model_arm"] == right_arm}
    common = sorted(set(left) & set(right))
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for task_id in common:
        by_cluster[left[task_id]["table_uid"]].append(
            float(left[task_id][key]) - float(right[task_id][key])
        )
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
        "left": left_arm,
        "right": right_arm,
        "metric": key,
        "difference": observed,
        "ci95": [samples[int(0.025 * repetitions)], samples[int(0.975 * repetitions)]],
        "table_clusters": len(clusters),
    }


def analyze(rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    tasks = paired_rows(rows)
    metrics = {}
    for arm in sorted({row["model_arm"] for row in tasks}):
        subset = [row for row in tasks if row["model_arm"] == arm]
        metrics[arm] = {
            "tasks": len(subset),
            **{
                f"{key}_rate": sum(float(row[key]) for row in subset) / len(subset)
                for key in (
                    "original_correct",
                    "relevant_adaptation",
                    "irrelevant_invariance",
                    "paired_all_three",
                    "reference_stability",
                )
            },
        }
    comparisons = {}
    for right in ("duplicate_original_control_sft", "ordinary_answer_execution_sft"):
        comparisons[right] = {
            key: bootstrap_difference(tasks, "paired_variant_stability_sft", right, key)
            for key in ("paired_all_three", "reference_stability", "relevant_adaptation", "irrelevant_invariance")
        }
    return {
        "metrics": metrics,
        "paired_minus_comparators": comparisons,
        "transparent_baseline": {
            "tasks": len(baseline_rows),
            "solved": sum(bool(row["solved"]) for row in baseline_rows),
            "accuracy": sum(bool(row["solved"]) for row in baseline_rows) / len(baseline_rows),
        },
    }


def add_parsed_program(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    import re
    decoder = json.JSONDecoder()
    output = []
    for row in rows:
        parsed = None
        for match in re.finditer(r"\{", str(row.get("generated_text", ""))):
            try:
                value, _ = decoder.raw_decode(str(row["generated_text"])[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and "program" in value:
                parsed = value["program"]
                break
        output.append({**row, "parsed_program": parsed})
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--prior-instances", type=Path, required=True)
    parser.add_argument("--first-confirmation-instances", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("status") != "FROZEN_BEFORE_PAIRED_STABILITY_TRAINING":
        raise ValueError("protocol_not_frozen")
    tasks = load_jsonl(args.tasks)
    args.run_root.mkdir(parents=True, exist_ok=False)
    training_receipts = {
        arm: train_arm(
            arm,
            build_training_rows(tasks, arm),
            args.run_root,
            protocol["training"] | {
                "model_path_gb10": str(args.model_path),
                "max_steps_per_arm": protocol["training"]["max_steps_per_arm"],
                "max_length": 1536,
                "learning_rate": 0.0001,
                "lora_r": 16,
                "lora_alpha": 32,
                "target_modules": ["q_proj", "v_proj"],
                "seed": 20261024,
            },
        )
        for arm in ("duplicate_original_control_sft", "paired_variant_stability_sft")
    }
    write_json(args.run_root / "PAIRED_STABILITY_TRAINING_V3.json", training_receipts)
    selected = select_confirmation_tasks(
        tasks,
        args.prior_instances,
        args.first_confirmation_instances,
    )
    instances = build_instances(selected)
    write_jsonl(args.run_root / "stability_confirmation_instances_v3.jsonl", instances)
    baseline_rows = []
    for task in selected:
        candidate = natural_rule_candidate(task)
        baseline_rows.append({
            "task_id": task["task_id"],
            "solved": bool(candidate) and abs(float(candidate["answer"]) - float(task["expected"]["answer"])) < 1e-6,
        })
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = []
    generation_receipts = {}
    for arm in protocol["confirmation"]["models"]:
        model = AutoModelForCausalLM.from_pretrained(
            args.model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        if arm != "ordinary_answer_execution_sft":
            model = PeftModel.from_pretrained(model, args.run_root / "training" / arm / "final_adapter")
        else:
            model = PeftModel.from_pretrained(
                model,
                args.run_root.parent / "natural_program_finance_20261024_v2" / "training" / arm / "final_adapter",
            )
        model.eval()
        started = time.time()
        arm_rows = []
        for start in range(0, len(instances), 16):
            batch = generate_and_score_batch(model, tokenizer, instances[start:start + 16], 256)
            for row in batch:
                row["model_arm"] = arm
                arm_rows.append(row)
                rows.append(row)
            with (args.run_root / "stability_confirmation_results_v3.partial.jsonl").open(
                "a", encoding="utf-8", newline="\n"
            ) as handle:
                for row in batch:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            print(f"{arm}: {len(arm_rows)}/{len(instances)}", flush=True)
        generation_receipts[arm] = {
            "attempts": len(arm_rows),
            "prompt_tokens": sum(row["prompt_tokens"] for row in arm_rows),
            "completion_tokens": sum(row["completion_tokens"] for row in arm_rows),
            "wall_seconds": time.time() - started,
        }
        del model
        torch.cuda.empty_cache()
    rows = add_parsed_program(rows)
    write_jsonl(args.run_root / "stability_confirmation_results_v3.jsonl", rows)
    summary = analyze(rows, baseline_rows)
    write_json(args.run_root / "PAIRED_STABILITY_CONFIRMATION_V3.json", {
        "schema": "natural_tatqa_paired_stability_confirmation_v3",
        "identity": "FROZEN_SAME_SOURCE_NEW_FAMILY_CONFIRMATION",
        "protocol_sha256": sha256_file(args.protocol),
        "training": training_receipts,
        "generation": generation_receipts,
        "accounting_attempts": sum(item["attempts"] for item in generation_receipts.values()),
        "prompt_tokens": sum(item["prompt_tokens"] for item in generation_receipts.values()),
        "completion_tokens": sum(item["completion_tokens"] for item in generation_receipts.values()),
        "new_judge_calls": 0,
        **summary,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
