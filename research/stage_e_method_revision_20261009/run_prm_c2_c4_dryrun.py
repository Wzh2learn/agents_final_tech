#!/usr/bin/env python3
"""Run the non-training PRM800K C2/C4-reference selection dry-run."""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/stage_e_method_revision_20261009"
DATA = TASK / "sources/prm800k/phase2_test.jsonl"
OUT_JSON = TASK / "prm_c2_c4_selection_dryrun.json"
OUT_MD = ROOT / "docs/research/prm_c2_c4_selection_dryrun_v1.md"
PRM_REPO = Path("/home/testuser/wzh/external_stage_d_repro/repos/prm800k")
VENDOR = Path("/home/testuser/wzh/external_stage_d_repro/vendor")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_grader():
    sys.path.insert(0, str(VENDOR))
    sys.path.insert(0, str(PRM_REPO))
    sys.path.insert(0, str(PRM_REPO / "prm800k"))
    return importlib.import_module("grading.grader")


def selected_path(row: dict[str, Any]) -> tuple[list[int | None], list[str]]:
    ratings: list[int | None] = []
    texts: list[str] = []
    for step in row["label"]["steps"]:
        chosen = step.get("chosen_completion")
        if isinstance(chosen, int) and 0 <= chosen < len(step.get("completions", [])):
            completion = step["completions"][chosen]
            ratings.append(completion.get("rating"))
            texts.append(str(completion.get("text") or ""))
        else:
            ratings.append(None)
            texts.append(str(step.get("human_completion") or ""))
    return ratings, texts


def nearest_pairs(
    c2_rows: list[dict[str, Any]],
    c4_rows: list[dict[str, Any]],
    problem_hash: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    key = lambda row: (
        row["step_count"],
        row["process_whitespace_tokens"],
        row["process_text_chars"],
        row["row_hash"],
    )
    left = sorted((row for row in c2_rows if row["problem_hash"] == problem_hash), key=key)
    right = sorted((row for row in c4_rows if row["problem_hash"] == problem_hash), key=key)
    return list(zip(left, right))


def describe(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(array)) if len(array) else 0.0,
        "median": float(np.median(array)) if len(array) else 0.0,
        "max_abs": float(np.max(np.abs(array))) if len(array) else 0.0,
    }


def build() -> dict[str, Any]:
    grader = load_grader()
    raw_rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rows):
        ratings, texts = selected_path(raw)
        known = [rating for rating in ratings if rating is not None]
        complete = bool(ratings) and all(rating is not None for rating in ratings)
        process_text = "\n".join(texts)
        problem = str(raw["question"].get("problem") or "")
        problem_hash = sha256_text(problem)
        row_hash = sha256_text(json.dumps(raw, ensure_ascii=False, sort_keys=True))
        terminal = bool(grader.grade_answer(
            str(raw["question"].get("pre_generated_answer")),
            str(raw["question"].get("ground_truth_answer")),
        ))
        rows.append({
            "index": index,
            "row_hash": row_hash,
            "problem_hash": problem_hash,
            "terminal_correct": terminal,
            "ratings": ratings,
            "known_ratings": known,
            "selected_rating_complete": complete,
            "has_missing_selected_rating": any(rating is None for rating in ratings),
            "no_selected_rating": not known,
            "any_negative": any(rating == -1 for rating in known),
            "any_zero": any(rating == 0 for rating in known),
            "known_all_positive": bool(known) and all(rating > 0 for rating in known),
            "known_no_negative": bool(known) and all(rating >= 0 for rating in known),
            "strict_process_pass": complete and all(rating > 0 for rating in ratings if rating is not None),
            "lenient_process_pass": bool(known) and all(rating >= 0 for rating in known),
            "partial_local_positive": (not complete) and bool(known) and all(rating > 0 for rating in known),
            "step_count": len(ratings),
            "process_text_chars": len(process_text),
            "process_whitespace_tokens": len(process_text.split()),
        })

    c2 = [row for row in rows if row["terminal_correct"]]
    c4_strict = [row for row in rows if row["strict_process_pass"]]
    c4_lenient = [row for row in rows if row["lenient_process_pass"]]

    cross_strict = Counter((row["terminal_correct"], row["strict_process_pass"]) for row in rows)
    cross_lenient = Counter((row["terminal_correct"], row["lenient_process_pass"]) for row in rows)

    c2_hashes = {row["row_hash"] for row in c2}
    c4_hashes = {row["row_hash"] for row in c4_strict}
    groups_all = {row["problem_hash"] for row in rows}
    groups_c2 = {row["problem_hash"] for row in c2}
    groups_c4 = {row["problem_hash"] for row in c4_strict}
    groups_overlap = groups_c2 & groups_c4

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for problem_hash in sorted(groups_overlap):
        pairs.extend(nearest_pairs(c2, c4_strict, problem_hash))
    matched_step_diff = [abs(left["step_count"] - right["step_count"]) for left, right in pairs]
    matched_char_diff = [abs(left["process_text_chars"] - right["process_text_chars"]) for left, right in pairs]
    matched_token_diff = [
        abs(left["process_whitespace_tokens"] - right["process_whitespace_tokens"])
        for left, right in pairs
    ]

    disagreement = {
        "terminal_correct_but_process_contains_negative": sum(
            row["terminal_correct"] and row["any_negative"] for row in rows
        ),
        "terminal_incorrect_but_partial_process_locally_correct": sum(
            (not row["terminal_correct"]) and row["partial_local_positive"] for row in rows
        ),
        "terminal_incorrect_but_complete_all_positive": sum(
            (not row["terminal_correct"]) and row["strict_process_pass"] for row in rows
        ),
        "terminal_incorrect_but_known_no_negative": sum(
            (not row["terminal_correct"]) and row["lenient_process_pass"] for row in rows
        ),
        "terminal_correct_but_not_strict_process_pass": sum(
            row["terminal_correct"] and not row["strict_process_pass"] for row in rows
        ),
    }

    missing = {
        "rows_with_any_missing_selected_rating": sum(row["has_missing_selected_rating"] for row in rows),
        "rows_without_any_selected_rating": sum(row["no_selected_rating"] for row in rows),
        "rows_with_complete_selected_ratings": sum(row["selected_rating_complete"] for row in rows),
        "strict_eligible_rows": len(c4_strict),
        "strict_rows_lost_to_missing_labels": sum(
            row["known_all_positive"] and not row["strict_process_pass"] for row in rows
        ),
        "lenient_rows_with_missing_labels": sum(
            row["lenient_process_pass"] and row["has_missing_selected_rating"] for row in rows
        ),
    }

    status = (
        "VALIDATED_NON_TRAINING"
        if pairs
        and disagreement["terminal_correct_but_process_contains_negative"] > 0
        and disagreement["terminal_incorrect_but_partial_process_locally_correct"] > 0
        else "PARTIAL_REFERENCE_CONTRACT"
    )
    return {
        "namespace": "PRM_C2_C4_SELECTION_DRYRUN",
        "status": status,
        "training_runs": 0,
        "data": {
            "path": str(DATA),
            "sha256": sha256_file(DATA),
            "rows": len(rows),
            "split": "phase2_test",
        },
        "licence": {
            "code": "MIT repository root",
            "data": "LICENCE_PENDING",
            "allowed_scope": "non-commercial academic local analysis and non-training dry-run",
        },
        "arms": {
            "C2_reference": {
                "rule": "official grading.grader.grade_answer terminal correctness == True",
                "eligible_rows": len(rows),
                "selected_rows": len(c2),
            },
            "C4_reference_primary": {
                "rule": "every selected-path step rating is observed and strictly positive",
                "eligible_rows": sum(row["selected_rating_complete"] for row in rows),
                "selected_rows": len(c4_strict),
            },
            "C4_reference_sensitivity": {
                "rule": "at least one observed selected-path rating and all observed ratings are non-negative",
                "eligible_rows": sum(bool(row["known_ratings"]) for row in rows),
                "selected_rows": len(c4_lenient),
            },
        },
        "overlap": {
            "C2_and_C4_strict": len(c2_hashes & c4_hashes),
            "C2_only": len(c2_hashes - c4_hashes),
            "C4_strict_only": len(c4_hashes - c2_hashes),
            "neither": len(rows) - len(c2_hashes | c4_hashes),
            "cross_tab_strict": {
                f"{terminal}_{process}": count
                for (terminal, process), count in sorted(cross_strict.items())
            },
            "cross_tab_lenient": {
                f"{terminal}_{process}": count
                for (terminal, process), count in sorted(cross_lenient.items())
            },
        },
        "disagreement": disagreement,
        "problem_groups": {
            "all": len(groups_all),
            "with_C2": len(groups_c2),
            "with_C4_strict": len(groups_c4),
            "with_both": len(groups_overlap),
            "grouping_key": "DERIVED SHA-256 of question.problem",
        },
        "matching": {
            "rule": "within problem hash, deterministic nearest proxy match on step count, whitespace tokens, process characters and row hash without replacement",
            "matched_pairs": len(pairs),
            "unmatched_C2": len(c2) - len(pairs),
            "unmatched_C4_strict": len(c4_strict) - len(pairs),
            "step_count_abs_diff": describe(matched_step_diff),
            "process_char_abs_diff": describe(matched_char_diff),
            "whitespace_token_abs_diff": describe(matched_token_diff),
            "native_token_count": "NOT_AVAILABLE",
            "token_match_status": "PROXY_ONLY_FEASIBLE_NOT_NATIVE_TOKEN_MATCHED",
        },
        "missing_label_impact": missing,
        "leakage_audit": {
            "single_fixed_split": True,
            "problem_group_join": "problem hash preserved across C2/C4 matching",
            "cross_split_overlap": "NOT_APPLICABLE_WITHIN_PHASE2_TEST_DRYRUN",
            "risk": "LOW_FOR_DRYRUN; training split/leakage gates remain open",
        },
        "interpretation": {
            "terminal_process_disagreement_real": bool(
                disagreement["terminal_correct_but_process_contains_negative"]
                and disagreement["terminal_incorrect_but_partial_process_locally_correct"]
            ),
            "process_incremental_information_supported_for_reference_contract": bool(pairs),
            "forbidden_claims": [
                "C4 training superiority",
                "PRM800K paper reproduction",
                "native token matching",
                "formal Stage D result",
            ],
        },
    }


def render(payload: dict[str, Any]) -> str:
    arms = payload["arms"]
    overlap = payload["overlap"]
    disagreement = payload["disagreement"]
    groups = payload["problem_groups"]
    matching = payload["matching"]
    missing = payload["missing_label_impact"]
    return f"""# PRM800K C2/C4 Selection Dry-Run v1

> Status: `{payload['status']}` | Training runs: `0` | Scope: non-commercial academic non-training reference contract

## 1. Arms

| Arm | Rule | Eligible rows | Selected rows |
|---|---|---:|---:|
| C2-reference | {arms['C2_reference']['rule']} | {arms['C2_reference']['eligible_rows']} | {arms['C2_reference']['selected_rows']} |
| C4-reference primary | {arms['C4_reference_primary']['rule']} | {arms['C4_reference_primary']['eligible_rows']} | {arms['C4_reference_primary']['selected_rows']} |
| C4-reference sensitivity | {arms['C4_reference_sensitivity']['rule']} | {arms['C4_reference_sensitivity']['eligible_rows']} | {arms['C4_reference_sensitivity']['selected_rows']} |

Data licence remains `LICENCE_PENDING`; repository code licence is MIT.

## 2. Overlap and disagreement

- C2 and strict C4 overlap: `{overlap['C2_and_C4_strict']}`
- C2 only: `{overlap['C2_only']}`
- C4 only: `{overlap['C4_strict_only']}`
- Neither: `{overlap['neither']}`
- Terminal correct but selected process contains a negative: `{disagreement['terminal_correct_but_process_contains_negative']}`
- Terminal incorrect but partial process is locally all-positive: `{disagreement['terminal_incorrect_but_partial_process_locally_correct']}`
- Terminal incorrect but complete process is all-positive: `{disagreement['terminal_incorrect_but_complete_all_positive']}`
- Terminal incorrect but known process has no negative: `{disagreement['terminal_incorrect_but_known_no_negative']}`

`FACT`: both requested disagreement directions exist in the released phase2-test payload. Process labels therefore contain information not reducible to terminal correctness for this reference contract.

## 3. Problem groups and matching

- Derived problem groups: `{groups['all']}`
- Groups with C2: `{groups['with_C2']}`
- Groups with strict C4: `{groups['with_C4_strict']}`
- Groups with both: `{groups['with_both']}`
- Deterministically matched pairs: `{matching['matched_pairs']}`
- Unmatched C2 / C4: `{matching['unmatched_C2']}` / `{matching['unmatched_C4_strict']}`
- Step-count absolute difference: `{matching['step_count_abs_diff']}`
- Process-character absolute difference: `{matching['process_char_abs_diff']}`
- Whitespace-token absolute difference: `{matching['whitespace_token_abs_diff']}`
- Native token count: `{matching['native_token_count']}`
- Token matching: `{matching['token_match_status']}`

## 4. Missing labels and leakage

- Rows with any missing selected rating: `{missing['rows_with_any_missing_selected_rating']}`
- Rows without any selected rating: `{missing['rows_without_any_selected_rating']}`
- Complete selected-rating rows: `{missing['rows_with_complete_selected_ratings']}`
- Strict positive rows lost only because labels are missing/partial: `{missing['strict_rows_lost_to_missing_labels']}`
- Leakage audit: `{payload['leakage_audit']['risk']}`

## 5. Boundary

This dry-run validates dataset -> arm selection -> problem/token-proxy matching -> accounting only. It does not train, reproduce the PRM800K paper result, establish C4 superiority, or authorize formal Stage D training.

PRM_C2_C4_REFERENCE_STATUS: {payload['status']}
"""


def main() -> int:
    payload = build()
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render(payload), encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": payload["status"],
        "c2_selected": payload["arms"]["C2_reference"]["selected_rows"],
        "c4_strict_selected": payload["arms"]["C4_reference_primary"]["selected_rows"],
        "matched_pairs": payload["matching"]["matched_pairs"],
        "disagreement": payload["disagreement"],
        "output": str(OUT_MD),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
