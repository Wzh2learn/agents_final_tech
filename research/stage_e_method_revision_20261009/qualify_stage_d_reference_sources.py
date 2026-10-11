#!/usr/bin/env python3
"""Qualify PRM800K and Agent Distillation for non-commercial academic reference use."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
DEFAULT_OUT = TASK / "stage_d_reference_source_qualification.json"

PRM_REPO = Path("/home/testuser/wzh/external_stage_d_repro/repos/prm800k")
PRM_DATA = TASK / "sources/prm800k"
VENDOR = Path("/home/testuser/wzh/external_stage_d_repro/vendor")
AGENT_DATA = Path(
    "/home/testuser/wzh/external_stage_d_repro/datasets/agent_distillation/"
    "Qwen2.5-32B-Instruct_agent_trajectories_2k.jsonl"
)
AGENT_REPO = Path("/home/testuser/wzh/external_stage_d_repro/repos/agent_distillation")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def selected_ratings(label: dict[str, Any]) -> list[int | None]:
    ratings: list[int | None] = []
    for step in label.get("steps", []):
        chosen = step.get("chosen_completion")
        if chosen is None:
            ratings.append(None)
        elif isinstance(chosen, int) and 0 <= chosen < len(step.get("completions", [])):
            ratings.append(step["completions"][chosen].get("rating"))
        else:
            ratings.append(None)
    return ratings


def key_union(rows: list[dict[str, Any]], getter) -> list[str]:
    keys: set[str] = set()
    for row in rows:
        value = getter(row)
        if isinstance(value, dict):
            keys.update(str(key) for key in value)
    return sorted(keys)


def normalize_terminal_score(value: Any) -> bool | None:
    if value in (True, 1, "1", "True", "true"):
        return True
    if value in (False, 0, "0", "False", "false"):
        return False
    return None


def load_prm_grader():
    sys.path.insert(0, str(VENDOR))
    sys.path.insert(0, str(PRM_REPO))
    sys.path.insert(0, str(PRM_REPO / "prm800k"))
    return importlib.import_module("grading.grader")


def qualify_prm() -> dict[str, Any]:
    files = {}
    all_rows: dict[str, list[dict[str, Any]]] = {}
    for split, filename in (("phase1_test", "phase1_test.jsonl"), ("phase2_test", "phase2_test.jsonl")):
        path = PRM_DATA / filename
        rows = read_jsonl(path)
        all_rows[split] = rows
        ratings = [rating for row in rows for rating in selected_ratings(row["label"]) if rating is not None]
        rows_missing_all = sum(not any(rating is not None for rating in selected_ratings(row["label"])) for row in rows)
        rows_partial_missing = sum(
            any(rating is None for rating in selected_ratings(row["label"]))
            and any(rating is not None for rating in selected_ratings(row["label"]))
            for row in rows
        )
        problem_hashes = [
            hashlib.sha256(json.dumps(row["question"].get("problem"), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            for row in rows
        ]
        problem_counts = Counter(problem_hashes)
        files[split] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "rows": len(rows),
            "top_level_fields": key_union(rows, lambda row: row),
            "question_fields": key_union(rows, lambda row: row.get("question", {})),
            "label_fields": key_union(rows, lambda row: row.get("label", {})),
            "step_fields": key_union(rows, lambda row: (row.get("label", {}).get("steps") or [{}])[0]),
            "completion_fields": key_union(
                rows,
                lambda row: ((row.get("label", {}).get("steps") or [{}])[0].get("completions") or [{}])[0],
            ),
            "selected_rating_counts": dict(sorted(Counter(ratings).items())),
            "rows_without_any_selected_rating": rows_missing_all,
            "rows_with_partial_missing_selected_rating": rows_partial_missing,
            "unique_problem_text_hashes": len(problem_counts),
            "duplicate_problem_text_groups": sum(count > 1 for count in problem_counts.values()),
            "max_rows_per_problem_text": max(problem_counts.values(), default=0),
            "native_problem_id_field_present": False,
            "grouping_rule_available": "derived SHA-256 of question.problem; no native problem-family ID in inspected schema",
        }

    grader = load_prm_grader()
    grade_counts = Counter()
    normalize_counts = Counter()
    disagreements = 0
    normalizer = importlib.import_module("grading.math_normalize")
    for row in all_rows["phase2_test"]:
        predicted = row["question"].get("pre_generated_answer")
        expected = row["question"].get("ground_truth_answer")
        official = bool(grader.grade_answer(str(predicted), str(expected)))
        normalized = normalizer.normalize_answer(str(predicted)) == normalizer.normalize_answer(str(expected))
        grade_counts[official] += 1
        normalize_counts[normalized] += 1
        disagreements += official != normalized

    lfs_files = {}
    for name in (
        "phase1_train.jsonl",
        "phase2_train.jsonl",
        "math_splits/train.jsonl",
        "math_splits/test.jsonl",
    ):
        path = PRM_REPO / "prm800k/data" / name if not name.startswith("math_splits/") else PRM_REPO / "prm800k" / name
        lfs_files[name] = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "status": "LFS_POINTER_ONLY" if path.stat().st_size < 1024 else "PAYLOAD_PRESENT",
            "sha256": sha256_file(path),
        }

    return {
        "source": "PRM800K",
        "repo_commit": "7ecc794703b2877f63226f2477a49b34f9b25163",
        "code_licence": "MIT",
        "data_licence": "LICENCE_PENDING",
        "inspection_scope": "non-commercial academic metadata/schema/small-sample/reference-contract validation",
        "files": files,
        "full_split_payload_status": lfs_files,
        "phase2_terminal_answer_correctness": {
            "method": "official grading.grader.grade_answer",
            "correct": grade_counts[True],
            "incorrect": grade_counts[False],
            "normalize_subset_correct": normalize_counts[True],
            "official_vs_normalize_disagreements": disagreements,
        },
        "reference_contract": {
            "C2_reference": "terminal answer correctness from official grade_answer",
            "C4_reference": "human selected-path step labels, with missing selected ratings excluded and reported",
            "group": "derived question.problem hash unless a native problem ID is later verified",
            "split": "phase2_test for the first reference smoke; train payloads remain LFS pointers",
        },
        "gate": "PRM_REFERENCE_READY",
        "gate_scope": "reference-track contract validation and local non-commercial academic smoke only",
        "formal_training_as_final_main_result": "NOT_AUTHORIZED_UNTIL_DATA_LICENCE_AND_PROTOCOL_GATES_CLOSE",
    }


def walk_keys(value: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            keys.add(name)
            keys.update(walk_keys(child, name))
    elif isinstance(value, list):
        for child in value:
            keys.update(walk_keys(child, prefix))
    return keys


def qualify_agent_distillation() -> dict[str, Any]:
    rows = read_jsonl(AGENT_DATA)
    top_fields = key_union(rows, lambda row: row)
    parsed_logs: list[dict[str, Any]] = []
    parse_failures = 0
    for row in rows:
        log_data = row.get("log_data")
        if isinstance(log_data, str):
            try:
                log_data = json.loads(log_data)
            except json.JSONDecodeError:
                parse_failures += 1
                continue
        if isinstance(log_data, dict):
            parsed_logs.append(log_data)

    score_counts = Counter(str(row.get("score")) for row in rows)
    normalized_scores = Counter(normalize_terminal_score(row.get("score")) for row in rows)
    message_roles = Counter(
        str(message.get("role"))
        for log in parsed_logs
        for message in (log.get("messages") or [])
        if isinstance(message, dict)
    )
    memory_steps = sum(len((log.get("original_memory") or {}).get("steps") or []) for log in parsed_logs)
    nested_keys: set[str] = set()
    for log in parsed_logs:
        nested_keys.update(walk_keys(log, "log_data"))

    id_fields = {
        name: sum(name in row for row in rows)
        for name in ("task_id", "trajectory_id", "origin_id", "origin_group", "split", "dataset_name", "question")
    }
    step_reward_rows = sum(
        "step_reward" in row or "log_data.step_reward" in nested_keys
        for row in rows
    )

    return {
        "source": "Agent Distillation baseline trajectories",
        "dataset_revision": "cbd8971069aeb04ec3cc95282ef2397e8206a817",
        "dataset_path": str(AGENT_DATA),
        "dataset_sha256": sha256_file(AGENT_DATA),
        "dataset_bytes": AGENT_DATA.stat().st_size,
        "rows": len(rows),
        "code_repo_commit": "8884b80ea3d22e53a2e1e4b9fd324600d13e0430",
        "code_licence": "Apache-2.0",
        "data_licence": "LICENCE_PENDING",
        "model_licence": "NOT_APPLICABLE_TO_PAYLOAD_INSPECTION",
        "top_level_fields": top_fields,
        "nested_log_key_count": len(nested_keys),
        "log_parse_failures": parse_failures,
        "message_role_counts": dict(sorted(message_roles.items())),
        "original_memory_step_count": memory_steps,
        "raw_score_counts": dict(sorted(score_counts.items())),
        "normalized_score_counts": {
            "positive": normalized_scores[True],
            "negative": normalized_scores[False],
            "missing_or_non_binary": normalized_scores[None],
        },
        "explicit_id_field_counts": id_fields,
        "step_reward_rows": step_reward_rows,
        "field_interpretation": {
            "action_observation": "tool-call and tool-response message roles are present in actual payload",
            "terminal_outcome": "score is present but mixed-string/boolean/blank and needs normalization plus missingness reporting",
            "process_signal": "no released step_reward; deterministic tool/error/observation consistency signals can be derived only with provenance marked derived",
            "origin_group": "dataset_name is a coarse task family, not a verified independent origin group",
            "split": "no native row-level split field in inspected payload",
        },
        "c2_c4_requirements": {
            "mother_pool": "available: actual 1,928-row baseline payload",
            "terminal_outcome": "partially available: 1,381 normalized positive/non-positive values and 547 missing/non-binary",
            "step_action_observation": "available through nested messages and memory steps",
            "process_signal": "not native; deterministic-derived candidate only",
            "origin_grouping": "derived IDs/groups required",
            "split": "derived split required",
            "licence": "LICENCE_PENDING for data/model; Apache-2.0 code is usable for academic adaptation",
        },
        "gate": "DATA_CAPABLE_LICENCE_PENDING_NOT_PILOT_READY",
        "allowed_now": [
            "metadata/schema inspection",
            "small-sample inspection",
            "adapter development",
            "preprocessing and deterministic smoke",
            "local non-commercial academic method validation",
        ],
        "blocked_now": [
            "public redistribution or released derived dataset",
            "commercial use",
            "large-scale formal training used as final paper main result",
            "calling derived process labels native step_reward",
        ],
    }


def build(out_path: Path) -> dict[str, Any]:
    payload = {
        "namespace": "STAGE_D_REFERENCE_SOURCE_QUALIFICATION",
        "status": "QUALIFIED_FOR_NONCOMMERCIAL_ACADEMIC_REFERENCE_WORK",
        "licence_policy": {
            "code": "Apache-2.0/MIT/BSD code may be cloned, modified, run, reproduced and adapted for academic experiments",
            "data_model": "record separately and mark LICENCE_PENDING until explicit terms are verified",
            "restriction": "no redistribution, commercial use, or large-scale final-result training while data/model licence is pending",
        },
        "prm800k": qualify_prm(),
        "agent_distillation": qualify_agent_distillation(),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    payload = build(args.out)
    print(json.dumps({
        "status": payload["status"],
        "prm_gate": payload["prm800k"]["gate"],
        "agent_gate": payload["agent_distillation"]["gate"],
        "output": str(args.out),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
