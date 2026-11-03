#!/usr/bin/env python3
"""Summarize completed geospatial development episodes without exposing gold to agents."""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_output(test_file):
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EXPECTED_RESULT" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("missing upstream expected result")


def second(value):
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).replace(microsecond=0)
    except (AttributeError, ValueError):
        return None


def summarize_case(case, expected):
    receipt_path = case / "receipt.json"
    intervention_path = case / "intervention.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    intervention = json.loads(intervention_path.read_text(encoding="utf-8"))
    expected_arm = "no_skill" if intervention["condition"] == "no_history" else intervention["condition"]
    if (receipt["arm"] != expected_arm
            or receipt["task"] != f"earthquake-plate-calculation-{intervention['task']}"):
        raise ValueError(f"receipt and intervention differ: {case}")
    raw = case / "raw.jsonl"
    if sha(raw) != receipt["raw_sha256"]:
        raise ValueError(f"raw trace hash differs: {case}")
    events = [json.loads(x) for x in raw.read_text(encoding="utf-8").splitlines() if x.strip()]
    verifier = (case / "verifier.txt").read_text(encoding="utf-8")
    tests = re.findall(r"(?m)^(test_\w+)\s+\([^\n]+\)(?:\n[^\n]*)?\s*\.\.\.\s*(ok|FAIL|ERROR)\s*$", verifier)
    if len(dict(tests)) != len(tests) or len(tests) not in (0, 8):
        raise ValueError(f"unexpected upstream test-result structure: {case}")
    answer_path = case / "work/answer.json"
    try:
        answer = json.loads(answer_path.read_text(encoding="utf-8")) if answer_path.exists() else None
    except (ValueError, OSError):
        answer = None
    aliases = str(answer.get("id", "")).strip(",").split(",") if isinstance(answer, dict) else []
    tool_inputs = [event.get("part", {}).get("state", {}).get("input", {})
                   for event in events if event.get("type") == "tool_use"]
    errors = [event.get("error", {}).get("name", "UNKNOWN")
              for event in events if event.get("type") == "error"]
    calls = receipt["model_http_requests"]
    tokens = receipt["step_finish_tokens"]
    reported = {key: sum(int(item.get(key, 0) or 0) for item in tokens)
                for key in ("total", "input", "output", "reasoning")}
    reported["cache_read"] = sum(int(item.get("cache", {}).get("read", 0) or 0) for item in tokens)
    distance = answer.get("distance_km") if isinstance(answer, dict) else None
    numeric_distance = isinstance(distance, (int, float)) and not isinstance(distance, bool)
    same_coordinates = (isinstance(answer, dict)
                        and all(isinstance(answer.get(key), (int, float))
                                and not isinstance(answer.get(key), bool)
                                and math.isclose(answer[key], expected[key], rel_tol=0, abs_tol=1e-6)
                                for key in ("latitude", "longitude")))
    return {
        "condition": intervention["condition"], "task": intervention["task"],
        "agent_exit": receipt["agent_exit"], "verifier_exit": receipt["verifier_exit"],
        "upstream_passed": sum(status == "ok" for _, status in tests) if tests else None,
        "upstream_total": len(tests), "test_statuses": dict(tests),
        "test_status_scope": "eight per-field tests" if tests else "no per-field tests ran; inspect verifier log",
        "answer_present_and_parseable": isinstance(answer, dict),
        "event_id_exact": answer.get("id") == expected["id"] if isinstance(answer, dict) else None,
        "event_id_contains_reference_as_alias": expected["id"] in aliases if isinstance(answer, dict) else None,
        "same_place": answer.get("place") == expected["place"] if isinstance(answer, dict) else None,
        "same_coordinates_as_reference": same_coordinates if isinstance(answer, dict) else None,
        "time_matches_reference_to_seconds": (second(answer.get("time")) == second(expected["time"])) if isinstance(answer, dict) else None,
        "reported_distance_km": distance,
        "distance_minus_reference_km": round(float(distance) - expected["distance_km"], 2) if numeric_distance else None,
        "history_file_mentioned_in_tool_input": any(
            any(name in json.dumps(tool, ensure_ascii=False) for name in ("source_trace.jsonl", "source_history.json", "source_skill.md"))
            for tool in tool_inputs),
        "error_types": errors,
        "model_post_count": sum(str(call).startswith("POST ") for call in calls),
        "locally_denied_count": sum(str(call).startswith("DENIED") for call in calls),
        "forwarded_post_body_bytes": sum(receipt["post_content_lengths"]),
        "reported_step_tokens": reported,
        "elapsed_seconds_including_verifier": receipt["elapsed_seconds"],
        "raw_sha256": sha(raw), "receipt_sha256": sha(receipt_path),
        "intervention_sha256": sha(intervention_path),
        "answer_sha256": sha(answer_path) if answer_path.exists() else None,
        "dependency_tree": intervention["dependency_tree"],
        "instruction_sha256": intervention["instruction_sha256"],
        "input_sha256": intervention["input_sha256"], "image": intervention["image"],
    }


def one(root, pattern):
    matches = sorted(path for path in root.glob(pattern) if path.is_dir())
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {pattern}, found {len(matches)}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_root", type=Path)
    parser.add_argument("task_root", type=Path)
    parser.add_argument("qualification_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--include-required", action="store_true")
    parser.add_argument("--geodesic-receipt", type=Path,
                        help="optional post-hoc geodesic control receipt")
    args = parser.parse_args()
    specs = [("source_no_history", 1, "earthquake-plate-calculation-1__no_skill__*"),
             ("target_no_history", 3, "earthquake-plate-calculation-3__no_skill__*"),
             ("target_raw_history", 3, "earthquake-plate-calculation-3__raw_history__*"),
             ("target_generated_skill", 3, "earthquake-plate-calculation-3__generated_skill__*")]
    if args.include_required:
        specs += [("target_raw_history_required", 3, "earthquake-plate-calculation-3__raw_history_required__*"),
                  ("target_generated_skill_required", 3, "earthquake-plate-calculation-3__generated_skill_required__*")]
    cases = {}
    for name, task, pattern in specs:
        path = one(args.episode_root, pattern)
        test_file = args.task_root / f"earthquake-plate-calculation-{task}/tests/test_outputs.py"
        cases[name] = summarize_case(path, expected_output(test_file))
    target = [cases[name] for name, _, _ in specs if name.startswith("target_")]
    if (len({x["instruction_sha256"] for x in target}) != 1
            or len({json.dumps(x["dependency_tree"], sort_keys=True) for x in target}) != 1
            or len({json.dumps(x["input_sha256"], sort_keys=True) for x in target}) != 1
            or len({x["image"] for x in target}) != 1):
        raise ValueError("target conditions did not use the same task and dependency tree")
    author_path = args.episode_root / "source_experience/ledger.json"
    author = json.loads(author_path.read_text(encoding="utf-8"))
    if author["status"] != "RECEIVED":
        raise ValueError("source experience generation did not finish")
    projection_path = args.qualification_root / "projection_controls/receipt.json"
    projections = json.loads(projection_path.read_text(encoding="utf-8"))
    geodesic_path = args.geodesic_receipt or args.qualification_root / "geodesic_control_10m.json"
    geodesic = json.loads(geodesic_path.read_text(encoding="utf-8"))
    if (geodesic["agent_answer_sha256"] != cases["target_no_history"]["answer_sha256"]
            or geodesic["bounds"]["lower_km"] > geodesic["bounds"]["upper_km"]):
        raise ValueError("geodesic control is not bound to the target baseline answer")
    for case in target:
        distance = case["reported_distance_km"]
        if (case["event_id_exact"] and case["same_coordinates_as_reference"]
                and isinstance(distance, (int, float)) and not isinstance(distance, bool)):
            # Answers are rounded to 0.01 km; include 0.005 km rounding on either side.
            case["distance_within_wgs84_sampling_bound"] = (
                geodesic["bounds"]["lower_km"] - 0.005 <= distance
                <= geodesic["bounds"]["upper_km"] + 0.005)
        else:
            case["distance_within_wgs84_sampling_bound"] = None
    result = {"status": "SINGLE_EXPOSED_FAMILY_DEVELOPMENT_NOT_GENERALIZATION",
              "scope": "upstream reference-relative results; task does not specify exact projection; no independent geodesic gold",
              "cases": cases, "source_experience_generation": {"ledger_sha256": sha(author_path),
                  "usage": author["usage"], "finish_reason": author["finish_reason"],
                  "model": author.get("response_model"), "calls": 1},
              "projection_controls": {"receipt_sha256": sha(projection_path), "results": projections["controls"]},
              "geodesic_control": {"receipt_sha256": sha(geodesic_path),
                  "bounds_km": [geodesic["bounds"]["lower_km"], geodesic["bounds"]["upper_km"]],
                  "spacing_m": geodesic["spacing_m"],
                  "unique_two_decimal_distance_km": (
                      round(geodesic["bounds"]["lower_km"], 2)
                      if round(geodesic["bounds"]["lower_km"], 2) == round(geodesic["bounds"]["upper_km"], 2)
                      else None),
                  "scope": "only the selected target event; not an independent ranking of all events"},
              "total_agent_posts": sum(c["model_post_count"] for c in cases.values()),
              "total_reported_agent_tokens": sum(c["reported_step_tokens"]["total"] for c in cases.values()),
              "total_reported_cache_read": sum(c["reported_step_tokens"]["cache_read"] for c in cases.values()),
              "source_and_target_data_shared": True}
    if args.output.exists():
        raise FileExistsError("refusing to overwrite a prior summary")
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cases": list(cases),
                      "agent_posts": result["total_agent_posts"],
                      "agent_tokens": result["total_reported_agent_tokens"]}), flush=True)


if __name__ == "__main__":
    main()
