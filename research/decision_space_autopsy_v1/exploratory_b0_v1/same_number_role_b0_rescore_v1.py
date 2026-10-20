#!/usr/bin/env python3
"""Rescore immutable same-number role B0 raw responses after contract repair."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
PARENT = PACKAGE.parent
EXECUTION_ROOT = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"
sys.path.insert(0, str(EXECUTION_ROOT))

from collection_runner import parse_chat_response
from execution_core import (
    evaluate_expression,
    sha256_file,
    strict_json_object,
    write_json_lf,
)


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def load_runner():
    path = PACKAGE / "same_number_role_b0_runner.py"
    spec = importlib.util.spec_from_file_location("same_number_role_b0_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("runner_import_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_content(raw_root: Path, logical_id: str) -> str:
    matches = []
    for request_path in raw_root.glob("*/request.json"):
        request = load_object(request_path)
        if request.get("logical_id") == logical_id:
            matches.append(request_path.parent)
    if len(matches) != 1:
        raise RuntimeError(f"raw_identity_invalid:{logical_id}:{len(matches)}")
    response = load_object(matches[0] / "response.json")["response"]
    return parse_chat_response(response)["content"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--original-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    runner = load_runner()
    protocol = load_object(args.protocol)
    tasks_doc = load_object(PARENT / "SAME_NUMBER_ROLE_TASKS_DRAFT.json")
    hidden = {row["task_id"]: row for row in tasks_doc["hidden_references"]}
    raw_root = args.raw_root.resolve()
    results = []
    for task_id in protocol["task_order"]:
        plan = runner.validate_plan_response(
            strict_json_object(read_content(raw_root, f"plan|B0|{task_id}"))
        )
        tool_result = {
            "tool": "calc",
            "params": plan["params"],
            "returned_value": evaluate_expression(plan["params"]["expression"]),
            "status": "OK",
            "error": None,
        }
        consume = runner.validate_role_consume(
            strict_json_object(read_content(raw_root, f"consume|B0|{task_id}"))
        )
        results.append(
            runner.classify(
                task_id,
                hidden[task_id]["source_cluster_id"],
                plan,
                tool_result,
                consume,
                hidden[task_id],
            )
        )

    success = sum(row["outcome"] == "SUCCESS" for row in results)
    non_success_clusters = sorted(
        {row["source_cluster_id"] for row in results if row["outcome"] != "SUCCESS"}
    )
    if success == 24:
        decision = "CEILING_ON_THIS_PANEL"
    elif 24 - success < 2 or len(non_success_clusters) <= 1:
        decision = "LIMITED_HEADROOM"
    else:
        decision = "CONTINUE_TO_ARM_DESIGN"
    output = {
        "schema": "same_number_role_b0_rescore_v1",
        "status": "RESCORED_IMMUTABLE_RAW_AFTER_CONTRACT_REPAIR",
        "scientific_label": "EXPLORATORY_POST_HOC_TECHNICAL_CORRECTION",
        "decision": decision,
        "success_count": success,
        "non_success_count": 24 - success,
        "non_success_clusters": non_success_clusters,
        "original_runner_result_sha256": sha256_file(args.original_result),
        "correction_scope": "Only WRONG_ROLE was allowed to carry numeric calc_value/unit; no task, reference, prompt, raw response or request changed.",
        "results": results,
    }
    write_json_lf(args.output, output)
    print(
        json.dumps(
            {
                "decision": decision,
                "success": success,
                "non_success": 24 - success,
                "requests": 48,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
