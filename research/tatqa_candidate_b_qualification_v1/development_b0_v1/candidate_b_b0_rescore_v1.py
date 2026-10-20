#!/usr/bin/env python3
"""Rescore immutable Candidate B B0 raw responses with frozen unit semantics."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXECUTION_ROOT = ROOT / "research/tatqa_wp0_2026/history_collection_execution_v1"
QUALIFICATION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXECUTION_ROOT))

from collection_runner import parse_chat_response  # noqa: E402
from execution_core import (  # noqa: E402
    evaluate_expression,
    sha256_file,
    strict_json_object,
    validate_consume_response,
    validate_plan_response,
    write_json_lf,
)


def load_checker():
    path = QUALIFICATION_ROOT / "candidate_b_reference_checker_v1.py"
    spec = importlib.util.spec_from_file_location("candidate_b_reference_checker", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("checker_import_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def approx_equal(left: Any, right: Any) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)
    except (TypeError, ValueError):
        return False


def read_model_content(raw_root: Path, request_key: str) -> str:
    matches = []
    for request_path in raw_root.glob("*/request.json"):
        request = load_json(request_path)
        if request.get("logical_id") == request_key:
            matches.append(request_path.parent)
    if len(matches) != 1:
        raise RuntimeError(f"raw_request_identity_invalid:{request_key}:{len(matches)}")
    response = load_json(matches[0] / "response.json")["response"]
    parsed = parse_chat_response(response)
    return parsed["content"]


def classify(
    task_id: str,
    cluster_id: str,
    plan: dict[str, Any],
    tool_result: dict[str, Any],
    consume: dict[str, Any],
    reference: dict[str, Any],
    checker: Any,
) -> dict[str, Any]:
    plan_valid = plan.get("tool") == "calc"
    tool_success = tool_result.get("status") == "OK"
    consume_valid = consume.get("status") in {"ANSWER", "UNKNOWN", "REFUSE"}
    expected = reference["deterministic_reference"]
    mapped_unit = checker.infer_unit_context(consume.get("unit"))
    unit_match = mapped_unit == reference["target_unit"]
    if consume.get("status") == "ANSWER":
        reference_match = approx_equal(
            consume.get("delta_target"), expected["late_minus_early"]
        )
        answer_tool_consistency = approx_equal(
            consume.get("delta_target"), tool_result.get("returned_value")
        )
    else:
        reference_match = False
        answer_tool_consistency = False
    trajectory_complete = plan_valid and tool_success and consume_valid
    success = (
        trajectory_complete
        and reference_match
        and answer_tool_consistency
        and unit_match
    )
    return {
        "task_id": task_id,
        "source_cluster_id": cluster_id,
        "arm": "B0",
        "trajectory_complete": trajectory_complete,
        "plan_valid": plan_valid,
        "tool_execution_success": tool_success,
        "consume_contract_valid": consume_valid,
        "reference_match": reference_match,
        "answer_tool_consistency": answer_tool_consistency,
        "unit_semantic_match": unit_match,
        "mapped_unit": mapped_unit,
        "outcome": "SUCCESS" if success else "NON_SUCCESS",
        "plan": plan,
        "tool_result": tool_result,
        "consume": consume,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--original-result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw_root = args.raw_root.resolve()
    protocol = load_json(args.protocol)
    tasks_doc = load_json(QUALIFICATION_ROOT / "CANDIDATE_B_TASKS_DRAFT.json")
    hidden_doc = load_json(QUALIFICATION_ROOT / "HIDDEN_REFERENCE_MANIFEST.json")
    tasks = {row["task_id"]: row for row in tasks_doc["tasks"]}
    references = {row["task_id"]: row for row in hidden_doc["references"]}
    checker = load_checker()
    results = []

    for task_id in protocol["task_order"]:
        plan = validate_plan_response(
            strict_json_object(
                read_model_content(raw_root, f"plan|B0|{task_id}")
            )
        )
        tool_result = {
            "tool": "calc",
            "params": plan["params"],
            "returned_value": evaluate_expression(plan["params"]["expression"]),
            "status": "OK",
            "error": None,
        }
        consume = validate_consume_response(
            strict_json_object(
                read_model_content(raw_root, f"consume|B0|{task_id}")
            )
        )
        reference = references[task_id]
        results.append(
            classify(
                task_id,
                reference["source_cluster_id"],
                plan,
                tool_result,
                consume,
                reference,
                checker,
            )
        )

    success = sum(row["outcome"] == "SUCCESS" for row in results)
    non_success_clusters = sorted(
        {
            row["source_cluster_id"]
            for row in results
            if row["outcome"] == "NON_SUCCESS"
        }
    )
    if success == 16:
        decision = "CEILING_ON_THIS_PANEL"
    elif (
        sum(row["outcome"] != "SUCCESS" for row in results) < 2
        or len(non_success_clusters) <= 1
    ):
        decision = "LIMITED_HEADROOM"
    else:
        decision = "CONTINUE_TO_ARM_DESIGN"

    output = {
        "schema": "candidate_b_b0_rescore_v1",
        "status": "RESCORED_IMMUTABLE_RAW_WITH_FROZEN_UNIT_SEMANTICS",
        "scientific_status": "EXPLORATORY_POST_HOC_TECHNICAL_CORRECTION",
        "decision": decision,
        "success_count": success,
        "non_success_count": 16 - success,
        "non_success_clusters": sorted(
            {
                row["source_cluster_id"]
                for row in results
                if row["outcome"] == "NON_SUCCESS"
            }
        ),
        "original_runner_result_sha256": sha256_file(args.original_result),
        "root_cause": "candidate_b_b0_runner compared display unit strings exactly to canonical unit codes instead of using the frozen infer_unit_context unit/scale semantics",
        "correction_scope": "offline rescoring of immutable raw responses only; no task, reference, model output or request changed",
        "results": results,
    }
    write_json_lf(args.output, output)
    print(
        json.dumps(
            {
                "decision": decision,
                "success": success,
                "non_success": 16 - success,
                "semantic_unit_matches": sum(
                    row["unit_semantic_match"] for row in results
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
