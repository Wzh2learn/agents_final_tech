"""Replay fixed-model delivery on the prior V4/V5 error-pool families.

The historical filename says confirmation, but source-identity review showed
that the selected tasks were reused error-pool tasks and are development only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from analyze_binding_residual_v3 import extract_target, parse_cells
from run_natural_program_experiment_v2 import generate_and_score_batch, make_variants
from same_candidate_feedback_a_v1 import (
    binding_relation,
    is_unknown_or_clarify,
    load_jsonl,
    localization_feedback,
    revision_prompt,
    sha256_file,
    task_level_metrics,
    write_json,
    write_jsonl,
)
from semantic_delivery_check_v3 import question_from_prompt, semantic_check


def build_instances(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for task in tasks[24:48]:
        for variant in make_variants(task):
            selected.append({
                "instance_id": f"{task['task_id']}::{variant['variant']}",
                "source_task_id": task["task_id"],
                "table_uid": task["table_uid"],
                "slice": "delivery_confirmation_c_v1",
                "variant": variant["variant"],
                "prompt": variant["prompt"],
                "expected": deepcopy(variant["expected"]),
                "table_text": variant["prompt"].split("\n\nQuestion:", 1)[0].split("Table:\n", 1)[-1],
            })
    return selected


def semantic_state(instance: dict[str, Any], generated: str) -> tuple[str, list[str]]:
    target = extract_target(generated)
    cells = parse_cells(str(instance["table_text"]))
    return semantic_check(
        question_from_prompt(str(instance["prompt"])),
        (target or {}).get("program"),
        cells,
    )


def policy_metrics(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    outcomes = []
    for row in rows:
        original = row["original"]
        retry = row["ordinary_retry"]
        revision = row["localization_feedback"]
        if policy == "always_accept_original":
            selected = original
        elif policy == "semantic_gate_original":
            selected = original if original["semantic_decision"] == "VALID" else None
        elif policy == "always_accept_ordinary_retry":
            selected = retry
        elif policy == "always_accept_localization_revision":
            selected = revision
        elif policy == "semantic_gate_localization_revision":
            selected = revision if revision["semantic_decision"] == "VALID" else None
        elif policy == "bounded_repair_original_if_valid_else_verified_revision":
            if original["semantic_decision"] == "VALID":
                selected = original
            elif revision["semantic_decision"] == "VALID":
                selected = revision
            else:
                selected = None
        else:
            raise ValueError(policy)
        outcomes.append(selected)
    accepted = [row for row in outcomes if row is not None]
    correct = sum(bool(row["program_correct"]) for row in accepted)
    wrong = len(accepted) - correct
    return {
        "items": len(rows),
        "delivered": len(accepted),
        "correct_delivery": correct,
        "wrong_delivery": wrong,
        "abstention": len(rows) - len(accepted),
        "correct_coverage": correct / len(rows) if rows else 0.0,
        "delivery_coverage": len(accepted) / len(rows) if rows else 0.0,
        "conditional_wrong_rate": wrong / len(accepted) if accepted else None,
    }


def condition_metrics(rows: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    subset = [row[condition] for row in rows]
    return {
        "items": len(subset),
        "numeric_correct": sum(bool(row["program_correct"]) for row in subset),
        "wrong": sum(not bool(row["program_correct"]) for row in subset),
        "interface_valid": sum(bool(row["interface_valid"]) for row in subset),
        "program_executable": sum(bool(row["program_executable"]) for row in subset),
        "exact_reference_set": sum(bool(row["binding_relation"]["exact"]) for row in subset),
        "unknown_or_clarify": sum(bool(row["unknown_or_clarify"]) for row in subset),
        "semantic_valid": sum(row["semantic_decision"] == "VALID" for row in subset),
        "semantic_unresolved": sum(row["semantic_decision"] == "UNRESOLVED" for row in subset),
        "semantic_invalid": sum(row["semantic_decision"] == "INVALID" for row in subset),
        "prompt_tokens": sum(int(row["prompt_tokens"]) for row in subset),
        "completion_tokens": sum(int(row["completion_tokens"]) for row in subset),
        "wall_seconds": sum(float(row["latency_ms"]) for row in subset) / 1000.0,
    }


def transitions(rows: list[dict[str, Any]], condition: str) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        before = bool(row["original"]["program_correct"])
        after = bool(row[condition]["program_correct"])
        counts[("correct" if before else "wrong") + "_to_" + ("correct" if after else "wrong")] += 1
    return dict(counts)


def paired_family_differences(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for condition in ("original", "ordinary_retry", "localization_feedback"):
            grouped[row["source_task_id"]][condition].append(row[condition])
    output = {}
    for condition in ("ordinary_retry", "localization_feedback"):
        diffs = []
        for task_rows in grouped.values():
            before = sum(bool(row["program_correct"]) for row in task_rows["original"])
            after = sum(bool(row["program_correct"]) for row in task_rows[condition])
            diffs.append(after - before)
        output[condition] = {
            "families": len(diffs),
            "family_score_differences": diffs,
            "mean_difference": sum(diffs) / len(diffs) if diffs else 0.0,
            "improved_families": sum(value > 0 for value in diffs),
            "degraded_families": sum(value < 0 for value in diffs),
            "unchanged_families": sum(value == 0 for value in diffs),
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    actual_hash = hashlib.sha256(args.tasks.read_bytes()).hexdigest()
    if actual_hash != protocol["source_file_sha256"]:
        raise ValueError(f"source_hash_mismatch:{actual_hash}")
    tasks = load_jsonl(args.tasks)
    instances = build_instances(tasks)
    if len(instances) != 72 or len({row["source_task_id"] for row in instances}) != 24:
        raise ValueError("unexpected_confirmation_shape")
    args.run_root.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.run_root / "delivery_confirmation_instances_c_v1.jsonl", instances)

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

    def generate(selected: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
        rows = []
        started = time.time()
        for start in range(0, len(selected), args.batch_size):
            batch = selected[start : start + args.batch_size]
            output = generate_and_score_batch(model, tokenizer, batch, args.max_new_tokens)
            rows.extend(output)
            with (args.run_root / f"{name}.partial.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                for row in output:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            print(f"{name}: {len(rows)}/{len(selected)}", flush=True)
        write_jsonl(args.run_root / f"{name}.jsonl", rows)
        return rows

    original_rows = generate(instances, "original_results_c_v1")
    original_by_id = {row["instance_id"]: row for row in original_rows}
    retry_instances = []
    localization_instances = []
    for instance in instances:
        previous = str(original_by_id[instance["instance_id"]]["generated_text"])
        retry_instances.append({
            **deepcopy(instance),
            "instance_id": f"{instance['instance_id']}::ordinary_retry",
            "base_instance_id": instance["instance_id"],
            "condition": "ordinary_retry",
            "prompt": revision_prompt(instance, previous, "ordinary_retry"),
        })
        localization_instances.append({
            **deepcopy(instance),
            "instance_id": f"{instance['instance_id']}::localization_feedback",
            "base_instance_id": instance["instance_id"],
            "condition": "localization_feedback",
            "prompt": revision_prompt(instance, previous, "localization_feedback"),
        })
    retry_rows = generate(retry_instances, "ordinary_retry_results_c_v1")
    localization_rows = generate(localization_instances, "localization_results_c_v1")

    by_condition = {
        "original": {row["instance_id"]: row for row in original_rows},
        "ordinary_retry": {row["base_instance_id"]: row for row in retry_rows},
        "localization_feedback": {row["base_instance_id"]: row for row in localization_rows},
    }
    paired = []
    for instance in instances:
        item = {"source_task_id": instance["source_task_id"], "variant": instance["variant"]}
        for condition, mapping in by_condition.items():
            row = mapping[instance["instance_id"]]
            decision, reasons = semantic_state(instance, str(row["generated_text"]))
            item[condition] = {
                **row,
                "semantic_decision": decision,
                "semantic_reasons": reasons,
                "binding_relation": binding_relation(str(row["generated_text"]), instance["expected"]),
                "unknown_or_clarify": is_unknown_or_clarify(
                    str(row["generated_text"]),
                    extract_target(str(row["generated_text"])),
                ),
            }
        paired.append(item)

    policies = (
        "always_accept_original",
        "semantic_gate_original",
        "always_accept_ordinary_retry",
        "always_accept_localization_revision",
        "semantic_gate_localization_revision",
        "bounded_repair_original_if_valid_else_verified_revision",
    )
    summary = {
        "schema": "delivery_confirmation_c_v1",
        "identity": "PRIOR_V4_V5_ERROR_POOL_FIXED_ORDINARY_MODEL_DELIVERY_REPLAY",
        "development_or_confirmation": "PRIOR_ERROR_POOL_DEVELOPMENT_REPLAY_24_FAMILIES",
        "source_identity_correction": {
            "task_id_overlap_with_v4_v5_error_pool": "24/24",
            "independent_new_family_confirmation": False
        },
        "hidden_reference_policy_features": 0,
        "source_sha256": actual_hash,
        "conditions": {
            condition: condition_metrics(paired, condition)
            for condition in ("original", "ordinary_retry", "localization_feedback")
        },
        "transitions": {
            "ordinary_retry": transitions(paired, "ordinary_retry"),
            "localization_feedback": transitions(paired, "localization_feedback"),
        },
        "task_level": task_level_metrics(
            [
                {
                    **row[condition],
                    "condition": "original_frozen" if condition == "original" else condition,
                    "source_task_id": row["source_task_id"],
                    "variant": row["variant"],
                }
                for row in paired
                for condition in ("original", "ordinary_retry", "localization_feedback")
            ]
        ),
        "paired_family_differences": paired_family_differences(paired),
        "policies": {
            policy: policy_metrics(paired, policy)
            for policy in policies
        },
        "accounting": {
            "attempts": 216,
            "prompt_tokens": sum(
                int(row["prompt_tokens"])
                for condition in ("original", "ordinary_retry", "localization_feedback")
                for row in by_condition[condition].values()
            ),
            "completion_tokens": sum(
                int(row["completion_tokens"])
                for condition in ("original", "ordinary_retry", "localization_feedback")
                for row in by_condition[condition].values()
            ),
        },
    }
    write_jsonl(args.run_root / "delivery_confirmation_paired_c_v1.jsonl", paired)
    write_json(args.run_root / "DELIVERY_CONFIRMATION_C_V1.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
