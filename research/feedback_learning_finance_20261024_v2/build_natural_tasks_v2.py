"""Build executable natural-question tasks from TAT-QA arithmetic derivations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from natural_program_contract_v2 import (
    ast_to_program,
    execute_program,
    literal_values,
    parse_derivation_ast,
    program_refs,
    restore_top_level_scale,
    table_cells,
    unique_literal_refs,
)


def sha256_file(path: Path) -> str:
    """Return SHA-256 for one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_for_uid(uid: str, source_split: str) -> str:
    """Assign source-cluster splits deterministically."""
    if source_split == "external":
        return "external"
    bucket = int(hashlib.sha256(uid.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "train" if bucket < 0.75 else ("dev" if bucket < 0.875 else "test")


def render_table(table: list[list[Any]]) -> str:
    """Render raw table cells with stable visible IDs."""
    width = max((len(row) for row in table), default=0)
    header = table[0] if table else []
    lines = [
        "columns: "
        + " | ".join(
            f"C{column}={str(header[column]).strip() if column < len(header) else ''}"
            for column in range(width)
        )
    ]
    for row_index, row in enumerate(table[1:], start=1):
        values = []
        for column in range(width):
            raw = row[column] if column < len(row) else ""
            values.append(f"C{column}={str(raw).strip()}")
        row_label = str(row[0]).strip() if row else ""
        lines.append(f"R{row_index} [{row_label}] " + " | ".join(values))
    return "\n".join(lines)


def visible_context(record: dict[str, Any], question: dict[str, Any]) -> str:
    """Include only referenced paragraphs for table-text questions."""
    if question.get("answer_from") != "table-text":
        return ""
    paragraphs = record.get("paragraphs", [])
    indices = question.get("rel_paragraphs") or []
    selected = []
    for index in indices:
        if isinstance(index, int) and 0 <= index < len(paragraphs):
            text = paragraphs[index]
            if isinstance(text, dict):
                text = text.get("text", "")
            selected.append(str(text))
    return "\n".join(selected)


def unit_from_scale(scale: Any) -> str:
    """Map TAT-QA scale to the v2 output unit."""
    value = str(scale or "").strip().lower()
    return value if value else "reported"


def build_prompt(question: str, table_text: str, context: str) -> str:
    """Build a natural-question program prompt with no hidden reference."""
    context_block = f"Relevant document text:\n{context}\n\n" if context else ""
    return (
        "Answer the financial-document question using only the visible evidence. "
        "Return one JSON object with a structured arithmetic program over visible "
        "R:C evidence references, evidence_refs, and unit. Do not return a numeric "
        "answer.\n\n"
        f"{context_block}Table:\n{table_text}\n\nQuestion: {question}"
    )


def build_task(
    record: dict[str, Any],
    record_index: int,
    source_split: str,
    question: dict[str, Any],
) -> dict[str, Any] | None:
    """Create one natural task when derivation operands map uniquely to cells."""
    if question.get("answer_type") != "arithmetic":
        return None
    if question.get("answer_from") not in {"table", "table-text"}:
        return None
    derivation = question.get("derivation")
    if not derivation:
        return None
    table = record.get("table", {}).get("table")
    table_uid = str(record.get("table", {}).get("uid"))
    if not isinstance(table, list) or len(table) < 2:
        return None
    try:
        tree = parse_derivation_ast(str(derivation))
        cells = table_cells(table)
        literal_refs, exclusions = unique_literal_refs(tree, cells)
        if exclusions:
            return None
        program = restore_top_level_scale(
            ast_to_program(tree, literal_refs),
            literal_refs.get(100.0),
        )
        executed = execute_program(program, cells)
        answer = float(question["answer"][0] if isinstance(question["answer"], list) else question["answer"])
    except (ValueError, TypeError, KeyError, ZeroDivisionError, SyntaxError, OverflowError):
        return None
    if not math.isfinite(executed) or not math.isclose(
        executed,
        answer,
        rel_tol=1e-6,
        abs_tol=1e-6,
    ):
        return None
    table_text = render_table(table)
    context = visible_context(record, question)
    question_text = str(question["question"])
    refs = program_refs(program)
    return {
        "schema": "natural_tatqa_program_task_v2",
        "task_id": f"NAT_{source_split}_{table_uid[:8]}_{question['uid'][:8]}",
        "question_uid": question["uid"],
        "table_uid": table_uid,
        "record_index": record_index,
        "source_split": source_split,
        "split": split_for_uid(table_uid, source_split),
        "answer_from": question["answer_from"],
        "question": question_text,
        "prompt": build_prompt(question_text, table_text, context),
        "table_text": table_text,
        "context_text": context,
        "expected": {
            "answer": answer,
            "unit": unit_from_scale(question.get("scale")),
            "program": program,
            "evidence_refs": refs,
        },
        "target": {
            "program": program,
            "evidence_refs": refs,
            "unit": unit_from_scale(question.get("scale")),
        },
    }


def build_dataset(
    train_path: Path,
    external_path: Path,
    max_tasks_per_table: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Build deterministic natural program tasks from both TAT-QA files."""
    tasks: list[dict[str, Any]] = []
    for source_split, path in (("train", train_path), ("external", external_path)):
        records = json.loads(path.read_text(encoding="utf-8"))
        for record_index, record in enumerate(records):
            candidates = [
                task for question in record.get("questions", [])
                for task in [build_task(record, record_index, source_split, question)]
                if task is not None
            ]
            rng = random.Random(f"{seed}:{source_split}:{record_index}")
            rng.shuffle(candidates)
            tasks.extend(candidates[:max_tasks_per_table])
    return sorted(tasks, key=lambda task: task["task_id"])


def question_row_score(question: str, row_label: str) -> int:
    """Score a transparent row match using visible words only."""
    stop = {"what", "was", "were", "the", "a", "an", "in", "for", "and", "or", "of", "to", "from", "between"}
    question_words = {
        word for word in re.findall(r"[a-z0-9]+", question.casefold())
        if word not in stop and len(word) > 2
    }
    row_words = {
        word for word in re.findall(r"[a-z0-9]+", row_label.casefold())
        if word not in stop and len(word) > 2
    }
    return len(question_words & row_words)


def natural_rule_candidate(task: dict[str, Any]) -> dict[str, Any] | None:
    """Transparent question-cue plus row/period baseline with no gold access."""
    cells = table_cells_from_text(task["table_text"])
    row_scores: dict[str, int] = defaultdict(int)
    row_labels: dict[str, str] = {}
    for cell in cells.values():
        row_scores[cell["row_id"]] = max(
            row_scores[cell["row_id"]],
            question_row_score(task["question"], cell["row_label"]),
        )
        row_labels[cell["row_id"]] = cell["row_label"]
    scored_rows = sorted(row_scores.items(), key=lambda item: (-item[1], item[0]))
    if not scored_rows or scored_rows[0][1] <= 0:
        return None
    best_score = scored_rows[0][1]
    best_rows = [row_id for row_id, score in scored_rows if score == best_score]
    if len(best_rows) != 1:
        return None
    row_id = best_rows[0]
    row_cells = [cell for cell in cells.values() if cell["row_id"] == row_id]
    years = sorted(
        [cell for cell in row_cells if re.search(r"(?:19|20)\d{2}", cell["column_label"])],
        key=lambda cell: int(re.findall(r"(?:19|20)\d{2}", cell["column_label"])[0]),
    )
    lowered = task["question"].casefold()
    if "percentage change" in lowered and len(years) >= 2:
        prior, current = years[0], years[-1]
        program = {
            "op": "mul",
            "left": {
                "op": "div",
                "left": {"op": "sub", "left": {"ref": current["ref"]}, "right": {"ref": prior["ref"]}},
                "right": {"ref": prior["ref"]},
            },
            "right": {"const": 100.0},
        }
    elif any(word in lowered for word in ("difference", "change", "increase", "decrease")) and len(years) >= 2:
        prior, current = years[0], years[-1]
        program = {
            "op": "sub",
            "left": {"ref": current["ref"]},
            "right": {"ref": prior["ref"]},
        }
    elif any(word in lowered for word in ("average", "mean")) and len(row_cells) >= 2:
        selected = row_cells[-2:]
        program = {
            "op": "div",
            "left": {"op": "add", "left": {"ref": selected[0]["ref"]}, "right": {"ref": selected[1]["ref"]}},
            "right": {"const": 2.0},
        }
    else:
        return None
    try:
        value = execute_structured(program, cells)
    except (ValueError, ZeroDivisionError):
        return None
    return {
        "program": program,
        "evidence_refs": program_refs(program),
        "unit": task["expected"]["unit"],
        "answer": value,
    }


def table_cells_from_text(table_text: str) -> dict[str, dict[str, Any]]:
    """Parse rendered table cells for the transparent baseline."""
    lines = table_text.splitlines()
    columns = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"(C\d+)=([^|]+)", lines[0])
    }
    cells: dict[str, dict[str, Any]] = {}
    for line in lines[1:]:
        row_match = re.match(r"^(R\d+) \[(.*?)\] (.*)$", line)
        if not row_match:
            continue
        row_id, row_label, body = row_match.groups()
        for match in re.finditer(r"(C\d+)=([^|]+)", body):
            column_id, value_text = match.groups()
            try:
                value = float(value_text.strip().replace(",", ""))
            except ValueError:
                continue
            ref = f"{row_id}:{column_id}"
            cells[ref] = {
                "ref": ref,
                "row_id": row_id,
                "row_label": row_label,
                "column_label": columns.get(column_id, ""),
                "value": value,
            }
    return cells


def execute_structured(program: dict[str, Any], cells: dict[str, dict[str, Any]]) -> float:
    """Execute a transparent structured program over parsed text cells."""
    if "ref" in program:
        return float(cells[program["ref"]]["value"])
    if "const" in program:
        return float(program["const"])
    left = execute_structured(program["left"], cells)
    right = execute_structured(program["right"], cells)
    return {
        "add": lambda: left + right,
        "sub": lambda: left - right,
        "mul": lambda: left * right,
        "div": lambda: left / right,
    }[program["op"]]()


def baseline_metrics(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate the transparent natural-question baseline by split."""
    output: dict[str, Any] = {}
    for split in sorted({task["split"] for task in tasks}):
        subset = [task for task in tasks if task["split"] == split]
        rows = []
        for task in subset:
            candidate = natural_rule_candidate(task)
            correct = bool(candidate) and math.isclose(
                float(candidate["answer"]),
                float(task["expected"]["answer"]),
                rel_tol=1e-6,
                abs_tol=1e-6,
            )
            rows.append({"task_id": task["task_id"], "solved": correct})
        output[split] = {
            "tasks": len(subset),
            "solved": sum(row["solved"] for row in rows),
            "accuracy": sum(row["solved"] for row in rows) / len(rows) if rows else 0.0,
            "task_rows": rows,
        }
    return output


def main() -> int:
    """Build the natural-task dataset and transparent baseline receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--external", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--max-tasks-per-table", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    tasks = build_dataset(
        args.train,
        args.external,
        args.max_tasks_per_table,
        args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for task in tasks:
            handle.write(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n")
    receipt = {
        "schema": "natural_tatqa_program_dataset_v2",
        "date": "2026-10-24",
        "identity": "NATURAL_TATQA_QUESTIONS_WITH_UNIQUELY_MAPPED_EXECUTABLE_DERIVATIONS",
        "source_hashes": {
            "train": sha256_file(args.train),
            "external": sha256_file(args.external),
        },
        "dataset_sha256": sha256_file(args.output),
        "task_count": len(tasks),
        "split_counts": dict(Counter(task["split"] for task in tasks)),
        "operator_shape_counts": dict(Counter(
            task["expected"]["program"].get("op", "leaf") for task in tasks
        )),
        "baseline": baseline_metrics(tasks),
    }
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

