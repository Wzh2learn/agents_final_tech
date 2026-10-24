"""Classify suspicious average denominators without assuming numeric identity."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from source_role_contract_v3 import classify_average_denominator


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def iter_denominator_nodes(program: Any, ref: str):
    if not isinstance(program, dict):
        return
    if program.get("op") == "div" and isinstance(program.get("right"), dict):
        if program["right"].get("ref") == ref:
            yield program["right"]
    for key in ("left", "right"):
        if key in program:
            yield from iter_denominator_nodes(program[key], ref)


def review_cases(
    audit_path: Path,
    tasks_path: Path,
) -> dict[str, Any]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    tasks = {task["task_id"]: task for task in load_jsonl(tasks_path)}
    reviewed = []
    for case in audit["reference_semantics"]["potential_cases"]:
        task = tasks[case["task_id"]]
        ref = case["denominator_cells"][0]["ref"]
        denominator_nodes = list(
            iter_denominator_nodes(task["target"]["program"], ref)
        )
        denominator = denominator_nodes[0] if denominator_nodes else {"ref": ref}
        label = classify_average_denominator(
            task["question"],
            denominator,
            case["denominator_cells"][0],
            task["target"]["program"].get("left"),
        )
        reviewed.append({
            **case,
            "label": label,
            "impact": (
                "CORRECT_REFERENCE_AND_REVIEW_TRAINING_SUPERVISION"
                if case["in_training"] and label == "STRUCTURAL_CONSTANT_MISBOUND"
                else "CORRECT_REFERENCE_ONLY"
                if label == "STRUCTURAL_CONSTANT_MISBOUND"
                else "EXCLUDE_OR_MANUAL_REVIEW_SUPERVISION"
                if case["in_training"] and label == "UNRESOLVED_REFERENCE_QUESTION_MISMATCH"
                else "NO_REFERENCE_CHANGE"
            ),
            "review_identity": "DETERMINISTIC_RULE_PLUS_MANUAL_REVIEW_REQUIRED_FOR_UNRESOLVED",
        })
    counts = Counter(item["label"] for item in reviewed)
    return {
        "schema": "semantic_constant_review_v3",
        "audit_identity": audit["identity"],
        "counts": dict(counts),
        "in_training_counts": dict(Counter(
            item["label"] for item in reviewed if item["in_training"]
        )),
        "cases": reviewed,
        "rule_boundary": "explicit average counts and semantic label overlap are evidence; numeric equality alone is not",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review_cases(args.audit, args.tasks)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
