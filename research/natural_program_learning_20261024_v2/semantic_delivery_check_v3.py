"""Visible semantic checks and delivery replay for fixed generated programs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_binding_residual_v3 import (
    extract_target,
    parse_cells,
    program_value,
    refs_in_program,
)


STOPWORDS = {
    "what", "was", "were", "the", "a", "an", "in", "for", "and", "or", "of",
    "to", "from", "between", "average", "mean", "company", "total", "amount",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def question_from_prompt(prompt: str) -> str:
    marker = "\n\nQuestion:"
    index = prompt.rfind(marker)
    return prompt[index + len(marker):].strip() if index >= 0 else ""


def additive_leaf_count(program: Any) -> int:
    if not isinstance(program, dict):
        return 0
    if "ref" in program or "const" in program:
        return 1
    if program.get("op") == "add":
        return additive_leaf_count(program.get("left")) + additive_leaf_count(program.get("right"))
    return max(additive_leaf_count(program.get("left")), additive_leaf_count(program.get("right")))


def denominator_nodes(program: Any):
    if not isinstance(program, dict):
        return
    if program.get("op") == "div" and isinstance(program.get("right"), dict):
        yield program, program["right"]
    for key in ("left", "right"):
        if key in program:
            yield from denominator_nodes(program[key])


def semantic_check(
    question: str,
    program: Any,
    cells: dict[str, dict[str, Any]],
) -> tuple[str, list[str]]:
    reasons = []
    refs = refs_in_program(program)
    if not refs:
        return "INVALID", ["no_visible_reference"]
    ref_cells = [cells.get(ref) for ref in refs]
    if any(cell is None for cell in ref_cells):
        return "INVALID", ["missing_visible_reference"]
    question_words = {
        word for word in re.findall(r"[a-z0-9]+", question.casefold())
        if word not in STOPWORDS and len(word) > 3
    }
    row_text = " ".join(str(cell.get("row_label", "")) for cell in ref_cells).casefold()
    if question_words and not any(word in row_text for word in question_words):
        reasons.append("question_row_role_not_visible_in_program")
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", question))
    years.update(
        f"20{year}"
        for year in re.findall(r"\bFY(\d{2})\b", question, flags=re.I)
    )
    period_labels = {
        period
        for cell in ref_cells
        for period in cell.get("period_labels", [])
    }
    label_text = " ".join(
        f"{cell.get('row_label', '')} {cell.get('column_label', '')}"
        for cell in ref_cells
    )
    if years and not years.issubset(period_labels):
        reasons.append("question_period_not_visible_in_program")
    for parent, right in denominator_nodes(program):
        ref = right.get("ref")
        cell = cells.get(str(ref)) if ref else None
        if not cell:
            continue
        value = float(cell.get("value", float("nan")))
        operand_count = additive_leaf_count(parent.get("left"))
        if (
            re.search(r"\baverage\b|\bmean\b", question, re.I)
            and operand_count >= 2
            and abs(value - operand_count) < 1e-9
        ):
            label = f"{cell.get('row_label', '')} {cell.get('column_label', '')}".casefold()
            if not any(word in label for word in question_words):
                reasons.append("structural_average_denominator_misbound")
    if reasons:
        return ("UNRESOLVED" if set(reasons) == {"question_period_not_visible_in_program"} else "INVALID"), reasons
    return "VALID", []


def policy_metrics(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    accepted = []
    for row in rows:
        if policy == "always_accept":
            accept = True
        elif policy == "executable_rule":
            accept = bool(row["interface_valid"] and row["program_executable"] and row["refs_valid"])
        elif policy == "semantic_rule":
            accept = row["semantic_decision"] == "VALID"
        else:
            raise ValueError(policy)
        accepted.append((accept, bool(row["program_correct"])))
    accepted_count = sum(accept for accept, _ in accepted)
    correct_accepted = sum(accept and correct for accept, correct in accepted)
    wrong_accepted = sum(accept and not correct for accept, correct in accepted)
    return {
        "items": len(rows),
        "accepted": accepted_count,
        "acceptance_rate": accepted_count / len(rows) if rows else 0.0,
        "correct_delivery_count": correct_accepted,
        "correct_delivery_coverage": correct_accepted / len(rows) if rows else 0.0,
        "wrong_delivery_count": wrong_accepted,
        "conditional_wrong_delivery_rate": wrong_accepted / accepted_count if accepted_count else None,
        "retained_or_unresolved": len(rows) - accepted_count,
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
        decision, reasons = semantic_check(
            question_from_prompt(str(instance["prompt"])),
            program,
            cells,
        )
        enriched.append({
            **result,
            "semantic_decision": decision,
            "semantic_reasons": reasons,
        })
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        grouped[row["model_arm"]].append(row)
    output = {
        "schema": "semantic_delivery_check_v3",
        "identity": "VISIBLE_EVIDENCE_ONLY_THREE_WAY_SEMANTIC_CHECK_ON_FROZEN_OUTPUTS",
        "models": {
            arm: {
                "semantic_decisions": dict(Counter(row["semantic_decision"] for row in rows)),
                "policies": {
                    policy: policy_metrics(rows, policy)
                    for policy in ("always_accept", "executable_rule", "semantic_rule")
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
