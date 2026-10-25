"""Analyze preserved Experiment C raw results without model calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_binding_residual_v3 import extract_target
from run_delivery_confirmation_c_v1 import (
    condition_metrics,
    paired_family_differences,
    policy_metrics,
    semantic_state,
    transitions,
)
from same_candidate_feedback_a_v1 import (
    binding_relation,
    is_unknown_or_clarify,
    load_jsonl,
    sha256_file,
    task_level_metrics,
    write_json,
    write_jsonl,
)


def base_id(row: dict, suffix: str) -> str:
    return str(row.get("base_instance_id") or str(row["instance_id"]).removesuffix(suffix))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--ordinary-retry", type=Path, required=True)
    parser.add_argument("--localization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    original_rows = load_jsonl(args.original)
    retry_rows = load_jsonl(args.ordinary_retry)
    localization_rows = load_jsonl(args.localization)
    if [len(original_rows), len(retry_rows), len(localization_rows)] != [72, 72, 72]:
        raise ValueError("unexpected_result_counts")

    mappings = {
        "original": {row["instance_id"]: row for row in original_rows},
        "ordinary_retry": {
            base_id(row, "::ordinary_retry"): row for row in retry_rows
        },
        "localization_feedback": {
            base_id(row, "::localization_feedback"): row for row in localization_rows
        },
    }
    if any(set(mapping) != set(instances) for mapping in mappings.values()):
        raise ValueError("instance_alignment_failure")

    paired = []
    for instance_id, instance in instances.items():
        item = {
            "source_task_id": instance["source_task_id"],
            "variant": instance["variant"],
        }
        for condition, mapping in mappings.items():
            row = mapping[instance_id]
            decision, reasons = semantic_state(instance, str(row["generated_text"]))
            item[condition] = {
                **row,
                "semantic_decision": decision,
                "semantic_reasons": reasons,
                "binding_relation": binding_relation(
                    str(row["generated_text"]),
                    instance["expected"],
                ),
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
        "identity": "FROZEN_NEW_FAMILIES_FIXED_ORDINARY_MODEL_DELIVERY_CONFIRMATION",
        "development_or_confirmation": "BOUNDED_CONFIRMATION_24_NEW_FAMILIES",
        "hidden_reference_policy_features": 0,
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
                    "condition": (
                        "original_frozen" if condition == "original" else condition
                    ),
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
                for mapping in mappings.values()
                for row in mapping.values()
            ),
            "completion_tokens": sum(
                int(row["completion_tokens"])
                for mapping in mappings.values()
                for row in mapping.values()
            ),
        },
        "input_sha256": {
            "instances": sha256_file(args.instances),
            "original": sha256_file(args.original),
            "ordinary_retry": sha256_file(args.ordinary_retry),
            "localization": sha256_file(args.localization),
        },
    }
    output_rows = args.output.with_suffix(".jsonl")
    write_jsonl(output_rows, paired)
    summary["output_sha256"] = sha256_file(output_rows)
    write_json(args.output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
