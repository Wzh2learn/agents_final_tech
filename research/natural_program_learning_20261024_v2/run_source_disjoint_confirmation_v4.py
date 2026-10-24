"""Evaluate existing adapters on a source-role-disjoint confirmation pool."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from natural_variant_measurement_v3 import extract_prompt_table
from run_natural_program_experiment_v2 import generate_and_score_batch, make_variants


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


def build_instances(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for task in tasks[:24]:
        for variant in make_variants(task):
            prompt_table = extract_prompt_table(variant["prompt"])
            selected.append({
                "instance_id": f"{task['task_id']}::{variant['variant']}",
                "source_task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "slice": "source_disjoint_confirmation_v4",
                "variant": variant["variant"],
                "prompt": variant["prompt"],
                "expected": variant["expected"],
                "table_text": prompt_table,
            })
    return selected


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_arm"], row["slice"], row["variant"])].append(row)
    output = {}
    for (arm, slice_name, variant), subset in sorted(grouped.items()):
        output.setdefault(arm, {}).setdefault(slice_name, {})[variant] = {
            "instances": len(subset),
            "program_correct": sum(bool(row["program_correct"]) for row in subset),
            "interface_valid": sum(bool(row["interface_valid"]) for row in subset),
            "refs_valid": sum(bool(row["refs_valid"]) for row in subset),
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    tasks = load_jsonl(args.tasks)
    if len(tasks) < 24:
        raise ValueError("not_enough_source_disjoint_tasks")
    instances = build_instances(tasks)
    args.run_root.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.run_root / "source_disjoint_instances_v4.jsonl", instances)
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = []
    receipts = {}
    for arm in ("ordinary_answer_execution_sft", "visible_program_filter_sft"):
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
            with (args.run_root / "source_disjoint_results_v4.partial.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
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
    write_jsonl(args.run_root / "source_disjoint_results_v4.jsonl", rows)
    summary = summarize(rows)
    write_json(args.run_root / "SOURCE_DISJOINT_SUMMARY_V4.json", {
        "schema": "source_disjoint_confirmation_summary_v4",
        "identity": "SOURCE_ROLE_DISJOINT_NEW_FAMILY_CONFIRMATION",
        "tasks": len(tasks),
        "instances": len(instances),
        "accounting_attempts": sum(item["attempts"] for item in receipts.values()),
        "prompt_tokens": sum(item["prompt_tokens"] for item in receipts.values()),
        "completion_tokens": sum(item["completion_tokens"] for item in receipts.values()),
        "models": receipts,
        "results_sha256": sha256_file(args.run_root / "source_disjoint_results_v4.jsonl"),
        "summary": summary,
        "new_judge_calls": 0,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
