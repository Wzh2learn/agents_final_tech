#!/usr/bin/env python3
"""Static PRM800K outcome-versus-process reference-track smoke."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
PRM_ROOT = Path("/home/testuser/wzh/external_stage_d_repro/repos/prm800k")
DATA = Path("/home/testuser/wzh/research_stage_e_method_revision_20261009/sources/prm800k/phase2_test.jsonl")
OUT = TASK / "prm_reference_smoke.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_ratings(label: dict) -> list[int | None]:
    ratings = []
    for step in label["steps"]:
        chosen = step.get("chosen_completion")
        if chosen is None:
            ratings.append(None)
        else:
            ratings.append(step["completions"][chosen].get("rating"))
    return ratings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--limit", type=int, default=2762)
    args = parser.parse_args()
    normalizer = load_module("prm_math_normalize", PRM_ROOT / "prm800k/grading/math_normalize.py")
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines()[:args.limit]]
    terminal = []
    no_negative = []
    all_positive = []
    rating_paths = []
    first_error = []
    missing_selected_rating = 0
    for row in rows:
        predicted = normalizer.normalize_answer(row["question"]["pre_generated_answer"])
        expected = normalizer.normalize_answer(row["question"]["ground_truth_answer"])
        answer_ok = predicted == expected
        ratings = selected_ratings(row["label"])
        known = [rating for rating in ratings if rating is not None]
        if not known:
            missing_selected_rating += 1
        terminal.append(answer_ok)
        no_negative.append(bool(known) and all(rating >= 0 for rating in known))
        all_positive.append(bool(known) and all(rating > 0 for rating in known))
        rating_paths.append(ratings)
        first_error.append(next((i for i, rating in enumerate(ratings) if rating == -1), None))
    cross = Counter((terminal[i], no_negative[i]) for i in range(len(rows)))
    finish = Counter(row["label"]["finish_reason"] for row in rows)
    rating_counter = Counter(rating for ratings in rating_paths for rating in ratings if rating is not None)
    result = {
        "namespace": "PRM_REFERENCE_TRACK",
        "status": "STATIC_REFERENCE_SMOKE_NOT_TRAINING",
        "repo_commit": "7ecc794703b2877f63226f2477a49b34f9b25163",
        "dataset_file": {
            "path": str(DATA),
            "sha256": sha256(DATA),
            "rows": len(rows),
            "source_lfs_oid": "6b172efa884ac8341a946dd82e06947c135b7254109fb3f7aa907c715d98aaad",
            "source_lfs_size": 12240719,
        },
        "schema_observation": {
            "top_keys": sorted(rows[0]),
            "question_keys": sorted(rows[0]["question"]),
            "label_keys": sorted(rows[0]["label"]),
            "step_keys": sorted(rows[0]["label"]["steps"][0]),
            "completion_keys": sorted(rows[0]["label"]["steps"][0]["completions"][0]),
            "rating_values": sorted(rating_counter),
            "rating_counts": dict(sorted(rating_counter.items(), key=lambda item: str(item[0]))),
            "rating_counts_scope": "selected-path completion ratings only",
            "finish_reason_counts": dict(finish),
        },
        "label_semantics_from_readme": {
            "rating": "-1 incorrect, 0 no progress/not incorrect, +1 good step; exact labeler protocol is documented in phase instructions, not re-derived here",
            "flagged": "labeler could flag steps they did not know how to label",
            "chosen_completion": "index of selected candidate; null indicates human_completion path",
            "human_completion": "phase-1 human-written alternative; null for phase-2 pre-generated paths",
            "finish_reason": "found_error / solution / bad_problem / give_up",
        },
        "outcome_process_smoke": {
            "terminal_metric": "official math_normalize.normalize_answer string-equality subset",
            "official_grade_answer_status": "NOT_RUN_MISSING_PYLATEXENC_DEPENDENCY",
            "terminal_correct": sum(terminal),
            "terminal_incorrect": len(rows) - sum(terminal),
            "selected_path_no_negative": sum(no_negative),
            "selected_path_all_positive": sum(all_positive),
            "selected_path_rating_denominator": sum(bool([rating for rating in ratings if rating is not None]) for ratings in rating_paths),
            "rows_without_selected_rating": missing_selected_rating,
            "terminal_x_no_negative": {f"{k[0]}_{k[1]}": v for k, v in sorted(cross.items())},
            "first_negative_step_counts": dict(sorted(Counter(first_error).items(), key=lambda item: str(item[0]))),
            "interpretation": "This is a data/matching smoke using the official normalization subset. It does not execute the full official grader, train a PRM, or reproduce the paper's model results.",
        },
        "process_vs_outcome_comparison_design": {
            "C2_reference": "filter by terminal answer correctness from grader.grade_answer",
            "C4_reference": "filter by selected human step labels, e.g. no negative rating or all-positive path",
            "required_matching": ["MATH problem ID", "solution length", "answer token count", "problem split"],
            "forbidden_claims": ["PRM800K result is our novelty", "this smoke proves C4 superiority"],
        },
        "licence_and_scope": {
            "repository_licence": "MIT root licence present",
            "dataset_specific_licence": "UNVERIFIED",
            "training_use": "NOT_AUTHORIZED",
            "inspection_use": "AUTHORIZED for this static reference-track audit",
        },
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": len(rows), "output": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
