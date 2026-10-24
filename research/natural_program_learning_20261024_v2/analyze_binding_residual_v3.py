"""Attribute natural-program failures to alias binding or other causes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REF_RE = re.compile(r"^R(\d+):C(\d+)$")
ROW_RE = re.compile(r"^(R\d+) \[(.*?)\] (.*)$")
CELL_RE = re.compile(r"(C\d+)=([^|]+)")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_number(text: str) -> float | None:
    value = str(text).strip().replace(",", "").rstrip("%")
    negative = value.startswith("(") and value.endswith(")")
    value = value.strip("()").replace("$", "").replace("£", "").replace("€", "").replace("¥", "")
    try:
        number = float(value)
    except ValueError:
        return None
    return -number if negative else number


def parse_cells(table_text: str) -> dict[str, dict[str, Any]]:
    lines = table_text.splitlines()
    columns = {
        match.group(1): match.group(2).strip()
        for match in CELL_RE.finditer(lines[0] if lines else "")
    }
    cells: dict[str, dict[str, Any]] = {}
    for line in lines[1:]:
        row_match = ROW_RE.match(line)
        if not row_match:
            continue
        row_id, row_label, body = row_match.groups()
        for match in CELL_RE.finditer(body):
            column_id, raw_value = match.groups()
            value = parse_number(raw_value)
            if value is None:
                continue
            ref = f"{row_id}:{column_id}"
            cells[ref] = {
                "ref": ref,
                "row_id": row_id,
                "column_id": column_id,
                "row_label": row_label.strip(),
                "column_label": columns.get(column_id, "").strip(),
                "value": value,
            }
    return cells


def refs_in_program(program: Any) -> list[str]:
    if isinstance(program, dict):
        if "ref" in program:
            return [str(program["ref"])]
        if "op" in program:
            refs = refs_in_program(program.get("left")) + refs_in_program(program.get("right"))
            return list(dict.fromkeys(refs))
    return []


def program_value(program: Any, cells: dict[str, dict[str, Any]]) -> float:
    if isinstance(program, dict) and "ref" in program:
        return float(cells[str(program["ref"])]["value"])
    if isinstance(program, dict) and "const" in program:
        return float(program["const"])
    if not isinstance(program, dict) or "op" not in program:
        raise ValueError("invalid_program")
    left = program_value(program["left"], cells)
    right = program_value(program["right"], cells)
    op = program["op"]
    if op == "add":
        return left + right
    if op == "sub":
        return left - right
    if op == "mul":
        return left * right
    if op == "div":
        return left / right
    raise ValueError(f"unsupported_op:{op}")


def extract_target(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and {"program", "evidence_refs", "unit"} <= set(value):
            return value
    return None


def alias_refs(ref: str, cells: dict[str, dict[str, Any]]) -> list[str]:
    target = cells.get(ref)
    if not target:
        return []
    return [
        other["ref"]
        for other in cells.values()
        if other["ref"] != ref
        and other["row_id"] == target["row_id"]
        and math.isclose(float(other["value"]), float(target["value"]), rel_tol=0, abs_tol=1e-9)
    ]


def unique_binding(ref: str, cells: dict[str, dict[str, Any]]) -> bool:
    target = cells.get(ref)
    if not target:
        return False
    matches = [
        other for other in cells.values()
        if other["row_label"] == target["row_label"]
        and other["column_label"] == target["column_label"]
    ]
    return len(matches) == 1 and matches[0]["ref"] == ref


def classify_row(
    result: dict[str, Any],
    task: dict[str, Any],
    cells: dict[str, dict[str, Any]],
) -> str:
    if not result.get("interface_valid"):
        return "format_or_parse"
    if not result.get("program_executable"):
        return "program_execution"
    generated_target = extract_target(result.get("generated_text", ""))
    generated_refs = refs_in_program((generated_target or {}).get("program"))
    gold_refs = refs_in_program(task["expected"]["program"])
    if result.get("program_correct"):
        return "correct"
    if result.get("variant") != "relevant_change":
        return "other_wrong"
    original_values = parse_cells(task["table_text"])
    try:
        original_value = program_value(extract_target(result["generated_text"])["program"], original_values)
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        return "other_wrong"
    if math.isclose(
        original_value,
        float(task["expected"]["answer"]),
        rel_tol=1e-6,
        abs_tol=1e-6,
    ) and set(generated_refs) != set(gold_refs):
        if all(ref in cells for ref in generated_refs):
            return "same_value_alias_or_reference"
    return "operand_or_operator_error"


def analyze(tasks_path: Path, results_path: Path) -> dict[str, Any]:
    tasks = {task["task_id"]: task for task in load_jsonl(tasks_path)}
    results = load_jsonl(results_path)
    alias_task_count = 0
    alias_ref_count = 0
    binding_unique_ref_count = 0
    gold_ref_count = 0
    per_task_alias = {}
    for task_id, task in tasks.items():
        cells = parse_cells(task["table_text"])
        refs = refs_in_program(task["expected"]["program"])
        gold_ref_count += len(refs)
        task_aliases = sorted({alias for ref in refs for alias in alias_refs(ref, cells)})
        per_task_alias[task_id] = task_aliases
        alias_ref_count += len(task_aliases)
        if task_aliases:
            alias_task_count += 1
        binding_unique_ref_count += sum(unique_binding(ref, cells) for ref in refs)
    grouped: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    sample_rows = []
    for result in results:
        task = tasks.get(result.get("source_task_id"))
        if not task:
            continue
        cells = parse_cells(result.get("table_text") or task["table_text"])
        cause = classify_row(result, task, cells)
        grouped[(result["model_arm"], result["slice"], result["variant"])][cause] += 1
        if cause == "same_value_alias_or_reference" and len(sample_rows) < 12:
            sample_rows.append({
                "instance_id": result["instance_id"],
                "model_arm": result["model_arm"],
                "slice": result["slice"],
                "gold_refs": refs_in_program(task["expected"]["program"]),
                "generated_refs": refs_in_program(
                    (extract_target(result.get("generated_text", "")) or {}).get("program")
                ),
                "alias_refs": per_task_alias[result["source_task_id"]],
            })
    return {
        "schema": "natural_program_binding_residual_v3",
        "identity": "POST_HOC_FAILURE_ATTRIBUTION_OF_FROZEN_GENERATIONS",
        "inputs": {
            "tasks_sha256": sha256_file(tasks_path),
            "results_sha256": sha256_file(results_path),
        },
        "binding_coverage": {
            "tasks": len(tasks),
            "gold_refs": gold_ref_count,
            "tasks_with_same_row_value_alias": alias_task_count,
            "same_row_value_alias_refs": alias_ref_count,
            "gold_refs_with_unique_visible_row_column_binding": binding_unique_ref_count,
            "unique_binding_rate": binding_unique_ref_count / gold_ref_count if gold_ref_count else 0.0,
        },
        "failure_attribution": {
            f"{arm}|{slice_name}|{variant}": dict(counts)
            for (arm, slice_name, variant), counts in sorted(grouped.items())
        },
        "alias_failure_samples": sample_rows,
        "interpretation_boundary": "same_value_alias_or_reference is a post-hoc diagnosis, not a new score or proof that role binding will improve models",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = analyze(args.tasks, args.results)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
