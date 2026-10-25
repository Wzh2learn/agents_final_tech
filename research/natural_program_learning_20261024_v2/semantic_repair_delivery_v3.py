"""Bounded visible repair for structural average denominators."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from analyze_binding_residual_v3 import (
    extract_target,
    parse_cells,
    program_value,
    refs_in_program,
)
from semantic_delivery_check_v3 import (
    additive_leaf_count,
    denominator_nodes,
    question_from_prompt,
    semantic_check,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def repair_structural_denominator(
    program: Any,
    question: str,
    cells: dict[str, dict[str, Any]],
) -> tuple[Any, list[str]]:
    updated = deepcopy(program)
    repairs = []
    for parent, right in list(denominator_nodes(updated)):
        ref = right.get("ref")
        cell = cells.get(str(ref)) if ref else None
        if not cell:
            continue
        value = float(cell.get("value", float("nan")))
        operand_count = additive_leaf_count(parent.get("left"))
        if (
            re.search(r"\baverage\b|\bmean\b", question, re.I)
            and operand_count >= 2
            and math.isfinite(value)
            and abs(value - operand_count) < 1e-9
        ):
            parent["right"] = {"const": operand_count}
            repairs.append(f"replace_structural_denominator:{ref}:const:{operand_count}")
    return updated, repairs


def evaluate(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    accepted = []
    repair_actions = 0
    for row in rows:
        outcomes = row.get("policy_outcomes")
        if outcomes is None or policy not in outcomes:
            raise ValueError(policy)
        outcome = outcomes[policy]
        accepted.append((bool(outcome["accepted"]), bool(outcome["correct"])))
        repair_actions += int(outcome.get("repair_actions", 0))
    accepted_count = sum(accept for accept, _ in accepted)
    correct = sum(accept and ok for accept, ok in accepted)
    wrong = sum(accept and not ok for accept, ok in accepted)
    return {
        "items": len(rows),
        "accepted": accepted_count,
        "acceptance_rate": accepted_count / len(rows) if rows else 0.0,
        "correct_delivery_count": correct,
        "correct_delivery_coverage": correct / len(rows) if rows else 0.0,
        "wrong_delivery_count": wrong,
        "conditional_wrong_delivery_rate": wrong / accepted_count if accepted_count else None,
        "retained_or_unresolved": len(rows) - accepted_count,
        "repair_actions": repair_actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    enriched = []
    for result in load_jsonl(args.results):
        instance = instances[result["instance_id"]]
        target = extract_target(str(result.get("generated_text", "")))
        program = (target or {}).get("program")
        cells = parse_cells(str(result.get("table_text") or instance["table_text"]))
        question = question_from_prompt(str(instance["prompt"]))
        decision, reasons = semantic_check(question, program, cells)
        repaired, repairs = repair_structural_denominator(program or {}, question, cells)
        repair_valid = False
        repair_decision = "NOT_APPLICABLE"
        correct_after_repair = bool(result["program_correct"])
        if repairs:
            repair_decision, _ = semantic_check(question, repaired, cells)
            try:
                repaired_value = program_value(repaired, cells)
                repair_valid = (
                    repair_decision == "VALID"
                    and math.isfinite(repaired_value)
                    and all(ref in cells for ref in refs_in_program(repaired))
                )
                correct_after_repair = math.isclose(
                    repaired_value,
                    float(instance["expected"]["answer"]),
                    rel_tol=1e-6,
                    abs_tol=1e-6,
                )
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                repair_valid = False
        original_outcome = {
            "accepted": True,
            "correct": bool(result["program_correct"]),
            "repair_actions": 0,
            "selected_program": program,
            "selected_action": "original",
        }
        executable_outcome = {
            **original_outcome,
            "accepted": bool(result["interface_valid"] and result["program_executable"] and result["refs_valid"]),
            "selected_action": "original_if_executable",
        }
        semantic_outcome = {
            **original_outcome,
            "accepted": decision == "VALID",
            "selected_action": "original_if_semantic_valid",
        }
        if decision == "VALID":
            repair_outcome = {
                **original_outcome,
                "selected_action": "original_if_semantic_valid",
            }
        elif repair_valid:
            repair_outcome = {
                "accepted": True,
                "correct": correct_after_repair,
                "repair_actions": 1,
                "selected_program": repaired,
                "selected_action": "one_shot_structural_repair",
            }
        else:
            repair_outcome = {
                "accepted": False,
                "correct": False,
                "repair_actions": 1 if repairs else 0,
                "selected_program": None,
                "selected_action": "retain_unresolved",
            }
        enriched.append({
            **result,
            "semantic_decision": decision,
            "semantic_reasons": reasons,
            "repair_valid": repair_valid,
            "repair_decision": repair_decision,
            "repairs": repairs,
            "correct_after_repair": correct_after_repair,
            "policy_outcomes": {
                "always_accept": original_outcome,
                "executable_rule": executable_outcome,
                "semantic_rule": semantic_outcome,
                "semantic_repair_rule": repair_outcome,
            },
        })
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        grouped[row["model_arm"]].append(row)
    output = {
        "schema": "semantic_repair_delivery_v3",
        "identity": "VISIBLE_EVIDENCE_ONLY_BOUNDED_STRUCTURAL_DENOMINATOR_REPAIR",
        "models": {
            arm: {
                "repair_counts": dict(Counter(
                    "repaired" if row["repair_valid"] else "not_repaired"
                    for row in rows
                )),
                "semantic_decisions": dict(Counter(row["semantic_decision"] for row in rows)),
                "policies": {
                    policy: evaluate(rows, policy)
                    for policy in ("always_accept", "executable_rule", "semantic_rule", "semantic_repair_rule")
                },
            }
            for arm, rows in sorted(grouped.items())
        },
        "new_model_calls": 0,
        "hidden_reference_policy_features": 0,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
