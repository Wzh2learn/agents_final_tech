#!/usr/bin/env python3
"""Freeze B0-first reuse diagnostic contexts, selection and branch gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


SEED = "reuse-h-selection-20261019"
ARMS = ("R", "C", "H")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def task_features(task: dict[str, Any]) -> dict[str, Any]:
    actor_task = task.get("actor_task", task)
    spec = actor_task["task"]
    return {
        "row_tokens": tokens(spec["row_label"]),
        "source_unit": spec["source_unit"],
        "target_unit": spec["target_unit"],
        "period_tokens": tokens(spec["period_early"] + " " + spec["period_late"]),
    }


def h_score(task: dict[str, Any], experience: dict[str, Any]) -> tuple[float, str]:
    left = task_features(task)
    right = task_features(experience["task"])
    union = left["row_tokens"] | right["row_tokens"]
    jaccard = len(left["row_tokens"] & right["row_tokens"]) / len(union) if union else 0.0
    score = 2.0 * jaccard
    score += 3.0 if left["source_unit"] == right["source_unit"] else 0.0
    score += 1.0 if left["target_unit"] == right["target_unit"] else 0.0
    score += 1.0 if left["period_tokens"] & right["period_tokens"] else 0.0
    tie = hashlib.sha256(
        f"{SEED}:{task['task_id']}:{experience['experience_id']}".encode("utf-8")
    ).hexdigest()
    return score, tie


def approx_tokens(value: Any) -> int:
    return math.ceil(len(json.dumps(value, ensure_ascii=False, separators=(",", ":"))) / 4)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--future-manifest", required=True, type=Path)
    parser.add_argument("--history-pool", required=True, type=Path)
    parser.add_argument("--plan-prompt", required=True, type=Path)
    parser.add_argument("--consume-prompt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.future_manifest.read_text(encoding="utf-8"))
    pool = json.loads(args.history_pool.read_text(encoding="utf-8"))
    tasks = [row for row in manifest["tasks"] if row["bucket"] == "future_test"]
    rules = (
        "Use only the supplied row and two periods. Compute signed difference as late "
        "minus early. Preserve the stated unit. Request the exact calc tool and consume "
        "its actual return. Return the frozen JSON contract."
    )
    domain = (
        "Financial tables may use parentheses for negatives and place units in headers "
        "or neighboring cells. Percentage-change columns are not absolute quantity "
        "columns. Keep units explicit and do not substitute values outside the supplied "
        "evidence."
    )
    arm_contexts = {}
    h_selections = {}
    context_lengths = {}
    for task in tasks:
        scored = sorted(
            (
                (h_score(task, experience), experience)
                for experience in pool["experiences"]
            ),
            key=lambda pair: (-pair[0][0], pair[0][1]),
        )
        selected = [experience for _, experience in scored[:2]]
        h_context = [
            {
                "experience_id": experience["experience_id"],
                "task": experience["task"],
                "actual_attempts": experience["actual_attempts"],
                "post_feedback_action_change": experience["post_feedback_action_change"],
            }
            for experience in selected
        ]
        h_selections[task["task_id"]] = [row["experience_id"] for row in h_context]
        arm_contexts[task["task_id"]] = {
            "B0": None,
            "R": rules,
            "C": domain,
            "H": h_context,
        }
        context_lengths[task["task_id"]] = {
            arm: approx_tokens(arm_contexts[task["task_id"]][arm])
            for arm in ("B0", "R", "C", "H")
        }

    b0_slots = []
    for task in tasks:
        for stage in ("plan", "consume"):
            b0_slots.append({
                "request_key": f"{stage}|B0|{task['task_id']}",
                "task_id": task["task_id"],
                "cluster_id": task["hidden"]["source_cluster_id"],
                "arm": "B0",
                "stage": stage,
            })
    stage3_slots = []
    for task_index, task in enumerate(tasks):
        rotation = task_index % len(ARMS)
        arm_order = ARMS[rotation:] + ARMS[:rotation]
        for arm in arm_order:
            for stage in ("plan", "consume"):
                stage3_slots.append({
                    "request_key": f"{stage}|{arm}|{task['task_id']}",
                    "task_id": task["task_id"],
                    "cluster_id": task["hidden"]["source_cluster_id"],
                    "arm": arm,
                    "stage": stage,
                })
    protocol = {
        "schema": "reuse_diagnostic_protocol_v1",
        "status": "FROZEN_BEFORE_B0",
        "measurement_question": (
            "Does real history add improvement over no context, generic operation rules, "
            "or general domain/tool context in restricted table calculation?"
        ),
        "task_order": [task["task_id"] for task in tasks],
        "arm_contexts": arm_contexts,
        "h_selection_rule": {
            "seed": SEED,
            "features": ["row-label token Jaccard", "source unit", "target unit", "period token overlap"],
            "forbidden_features": ["future answer", "reference", "B0 result", "model outcome"],
            "selection": "top two score descending, SHA-256 tie-break",
            "selected": h_selections,
        },
        "context_length_approx_tokens": context_lengths,
        "branch_gates": {
            "all_16_success": "CEILING_ON_THIS_PANEL",
            "fewer_than_2_nonsuccess_or_single_cluster": "LIMITED_HEADROOM",
            "at_least_2_clusters_with_nonsuccess": "CONTINUE_STAGE_THREE",
            "technical_failure": "TECHNICAL_INVALID_STOP",
        },
        "b0_request_slots": b0_slots,
        "stage3_request_slots": stage3_slots,
        "budget": {
            "new_request_cap": 128,
            "new_token_cap": 1700000,
            "b0_request_cap": 32,
            "stage3_request_cap": 96,
            "retry_cap": 0,
            "concurrency": 1,
        },
        "deadline": "2026-10-19T22:00:00+08:00",
        "artifact_hashes": {
            args.future_manifest.name: sha256_file(args.future_manifest),
            args.history_pool.name: sha256_file(args.history_pool),
            args.plan_prompt.name: sha256_file(args.plan_prompt),
            args.consume_prompt.name: sha256_file(args.consume_prompt),
        },
    }
    if len(b0_slots) != 32 or len(stage3_slots) != 96:
        raise ValueError("request slot count mismatch")
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": protocol["status"],
        "b0_slots": len(b0_slots),
        "stage3_slots": len(stage3_slots),
        "h_pairs": h_selections,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
