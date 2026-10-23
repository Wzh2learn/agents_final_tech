"""Core task construction and deterministic scoring for feedback-learning experiments."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import random
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


YEAR_PATTERN = re.compile(r"(?:19|20)\d{2}")
NUMBER_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")
UNIT_PATTERN = re.compile(
    r"(%|\$|¥|£|€|EUR|USD|RMB|CNY|million|thousand|billion)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CellRef:
    """Visible reference to one table cell."""

    row_id: str
    column_id: str
    row_label: str
    column_label: str

    def to_json(self) -> str:
        return f"{self.row_id}:{self.column_id}"


@dataclass(frozen=True)
class SourceCell:
    """Source cell with numeric value and visible identity."""

    row_index: int
    column_index: int
    row_label: str
    column_label: str
    value: float

    @property
    def ref(self) -> CellRef:
        return CellRef(
            row_id=f"R{self.row_index}",
            column_id=f"C{self.column_index}",
            row_label=self.row_label,
            column_label=self.column_label,
        )


def stable_hash(value: str) -> str:
    """Return a stable SHA-256 hex digest."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_number(value: float) -> int | float:
    """Convert a finite float to a compact JSON number."""
    if not math.isfinite(value):
        raise ValueError("non_finite_number")
    if abs(value - round(value)) < 1e-12:
        return int(round(value))
    return round(value, 8)


def parse_numeric(value: Any) -> float | None:
    """Parse a conservative financial-table numeric cell."""
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"n/a", "na", "-", "—"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = text.replace("%", "").replace("$", "").replace("£", "")
    text = text.replace("€", "").replace("¥", "")
    if not NUMBER_PATTERN.fullmatch(text):
        return None
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid_numeric_cell:{value!r}") from exc
    result = float(parsed)
    return -result if negative else result


def normalize_label(value: Any) -> str:
    """Normalize visible labels without changing their semantic content."""
    return re.sub(r"\s+", " ", str(value).strip())


def infer_unit(row_label: str, column_label: str) -> str:
    """Infer a visible unit label from row/header text."""
    text = f"{row_label} {column_label}"
    lowered = text.lower()
    if "%" in text or "rate" in lowered or "margin" in lowered:
        return "percent"
    match = UNIT_PATTERN.search(text)
    return match.group(1).lower() if match else "reported"


def formula_result(formula: str) -> float:
    """Evaluate a restricted arithmetic formula used by generated tasks."""
    tree = ast.parse(formula, mode="eval")

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left = visit(node.left)
            right = visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError(formula)
                return left / right
        raise ValueError(f"unsupported_formula:{formula}")

    return visit(tree)


def canonical_target(target: dict[str, Any]) -> str:
    """Serialize a model target in the exact training/evaluation contract."""
    return json.dumps(
        {
            "answer": json_number(float(target["answer"])),
            "unit": target["unit"],
            "formula": target["formula"],
            "evidence_refs": list(target["evidence_refs"]),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def extract_contract_object(text: str) -> dict[str, Any] | None:
    """Extract the first complete contract-like JSON object for diagnostics."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and {"answer", "unit", "formula", "evidence_refs"} <= set(value):
            return value
    return None


def build_prompt(question: str, table_text: str) -> str:
    """Build a deterministic actor prompt with a strict output contract."""
    return (
        "You are answering a financial table calculation. Use only the visible "
        "table excerpt. Respect the requested row scope, periods, and unit.\n\n"
        f"{table_text}\n\nQuestion: {question}\n\n"
        "Return exactly one JSON object with keys answer, unit, formula, and "
        "evidence_refs. The formula must be a numeric arithmetic expression. "
        "evidence_refs must use visible row/column IDs such as R2:C1."
    )


def visible_table_text(
    table: list[list[Any]],
    row_indices: Iterable[int],
    column_indices: Iterable[int],
    mutations: dict[tuple[int, int], float] | None = None,
) -> str:
    """Render a compact actor-visible table with stable row/column IDs."""
    mutations = mutations or {}
    row_list = sorted(set(int(index) for index in row_indices))
    column_list = sorted(set(int(index) for index in column_indices))
    header = table[0] if table else []
    columns = " | ".join(
        f"C{column}={normalize_label(header[column]) if column < len(header) else ''}"
        for column in column_list
    )
    lines = [f"columns: {columns}"]
    for row_index in row_list:
        if row_index >= len(table):
            continue
        row = table[row_index]
        row_label = normalize_label(row[0]) if row else ""
        values = []
        for column in column_list:
            value = mutations.get((row_index, column))
            if value is None:
                raw = row[column] if column < len(row) else ""
                values.append(f"C{column}={normalize_label(raw)}")
            else:
                values.append(f"C{column}={json_number(value)}")
        lines.append(f"R{row_index} [{row_label}] " + " | ".join(values))
    return "\n".join(lines)


def _source_cells(table: list[list[Any]]) -> dict[tuple[int, int], SourceCell]:
    """Index all parseable numeric source cells."""
    cells: dict[tuple[int, int], SourceCell] = {}
    if not table:
        return cells
    header = table[0]
    for row_index, row in enumerate(table[1:], start=1):
        row_label = normalize_label(row[0]) if row else ""
        for column_index in range(1, min(len(row), len(header))):
            value = parse_numeric(row[column_index])
            if value is None:
                continue
            cells[(row_index, column_index)] = SourceCell(
                row_index=row_index,
                column_index=column_index,
                row_label=row_label,
                column_label=normalize_label(header[column_index]),
                value=value,
            )
    return cells


def _year_columns(table: list[list[Any]]) -> list[tuple[int, str]]:
    """Return year-bearing columns in chronological order."""
    if not table:
        return []
    columns: list[tuple[int, str]] = []
    for column_index, raw in enumerate(table[0]):
        years = YEAR_PATTERN.findall(normalize_label(raw))
        if years:
            columns.append((column_index, years[-1]))
    return sorted(columns, key=lambda pair: int(pair[1]))


def _candidate_targets(
    expected: dict[str, Any],
    table: list[list[Any]],
    cells: dict[tuple[int, int], SourceCell],
    target_cells: list[SourceCell],
    current_period: str,
    prior_period: str,
    task_type: str,
) -> list[dict[str, Any]]:
    """Construct controlled candidate completions and their check vectors."""
    answer = float(expected["answer"])
    formula = str(expected["formula"])
    unit = str(expected["unit"])
    refs = list(expected["evidence_refs"])
    candidates: list[dict[str, Any]] = [
        {
            "candidate_id": "correct",
            "target": {
                "answer": json_number(answer),
                "unit": unit,
                "formula": formula,
                "evidence_refs": refs,
            },
            "error_type": "none",
        }
    ]

    duplicate: SourceCell | None = None
    expected_ref_set = set(refs)
    target_values = [cell.value for cell in target_cells]
    for cell in cells.values():
        if cell.ref.to_json() in expected_ref_set:
            continue
        if any(math.isclose(cell.value, value, rel_tol=0, abs_tol=1e-9) for value in target_values):
            duplicate = cell
            break
    if duplicate is not None and len(target_cells) >= 2:
        swapped_refs = refs.copy()
        swapped_refs[0] = duplicate.ref.to_json()
        candidates.append(
            {
                "candidate_id": "answer_correct_evidence_wrong",
                "target": {
                    "answer": json_number(answer),
                    "unit": unit,
                    "formula": formula,
                    "evidence_refs": swapped_refs,
                },
                "error_type": "wrong_scope_same_value",
            }
        )

    wrong_unit = "reported" if unit != "reported" else "percent"
    candidates.append(
        {
            "candidate_id": "unit_error",
            "target": {
                "answer": json_number(answer),
                "unit": wrong_unit,
                "formula": formula,
                "evidence_refs": refs,
            },
            "error_type": "wrong_unit",
        }
    )

    alternate_cells = [
        cell
        for cell in cells.values()
        if cell.row_index == target_cells[0].row_index
        and cell.column_label not in {current_period, prior_period}
    ]
    if alternate_cells and len(target_cells) >= 2:
        replacement = alternate_cells[0]
        changed = target_cells.copy()
        changed[0] = replacement
        try:
            wrong_answer, wrong_formula = _recompute_target(changed, task_type)
        except ZeroDivisionError:
            pass
        else:
            wrong_refs = [cell.ref.to_json() for cell in changed]
            candidates.append(
                {
                    "candidate_id": "wrong_period",
                    "target": {
                        "answer": json_number(wrong_answer),
                        "unit": unit,
                        "formula": wrong_formula,
                        "evidence_refs": wrong_refs,
                    },
                    "error_type": "wrong_period",
                }
            )

    nearby = [
        cell
        for cell in cells.values()
        if cell.row_index != target_cells[0].row_index
        and cell.column_index == target_cells[0].column_index
    ]
    if nearby and len(target_cells) >= 2:
        changed = target_cells.copy()
        changed[0] = nearby[0]
        try:
            wrong_answer, wrong_formula = _recompute_target(changed, task_type)
        except ZeroDivisionError:
            pass
        else:
            wrong_refs = [cell.ref.to_json() for cell in changed]
            candidates.append(
                {
                    "candidate_id": "wrong_scope",
                    "target": {
                        "answer": json_number(wrong_answer),
                        "unit": unit,
                        "formula": wrong_formula,
                        "evidence_refs": wrong_refs,
                    },
                    "error_type": "wrong_scope",
                }
            )

    for candidate in candidates:
        target = candidate["target"]
        target["answer"] = float(target["answer"])
        candidate["checks"] = evaluate_target_checks(
            target,
            expected,
            cells,
            current_period,
            prior_period,
        )
    return candidates


def _recompute_target(
    cells: list[SourceCell],
    task_type: str,
) -> tuple[float, str]:
    """Recompute a target from two source cells."""
    if task_type == "difference":
        value = cells[1].value - cells[0].value
        formula = f"{json_number(cells[1].value)} - {json_number(cells[0].value)}"
        return value, formula
    if task_type == "percent_change":
        if cells[0].value == 0:
            raise ZeroDivisionError("percent_change_prior_zero")
        value = (cells[1].value - cells[0].value) / cells[0].value * 100.0
        formula = (
            f"({json_number(cells[1].value)} - {json_number(cells[0].value)}) / "
            f"{json_number(cells[0].value)} * 100"
        )
        return value, formula
    raise ValueError(f"unsupported_task_type:{task_type}")


def evaluate_target_checks(
    target: dict[str, Any],
    expected: dict[str, Any],
    cells: dict[tuple[int, int], SourceCell],
    current_period: str,
    prior_period: str,
) -> dict[str, bool]:
    """Evaluate the check vector for a candidate or model output."""
    try:
        calculated = formula_result(str(target["formula"]))
        calculation = math.isclose(
            calculated,
            float(target["answer"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
    except (ValueError, SyntaxError, ZeroDivisionError):
        calculation = False
    expected_refs = set(expected["evidence_refs"])
    target_refs = set(target.get("evidence_refs", []))
    exact_evidence = target_refs == expected_refs
    ref_to_cell = {cell.ref.to_json(): cell for cell in cells.values()}
    ref_values_exist = bool(target_refs) and all(ref in ref_to_cell for ref in target_refs)
    period_labels = {ref_to_cell[ref].column_label for ref in target_refs if ref in ref_to_cell}
    period = bool(period_labels) and period_labels <= {current_period, prior_period}
    expected_row_ids = {
        ref.split(":", 1)[0] for ref in expected_refs
    }
    target_row_ids = {ref.split(":", 1)[0] for ref in target_refs}
    scope = bool(target_row_ids) and target_row_ids <= expected_row_ids
    unit = target.get("unit") == expected["unit"]
    return {
        "calculation": calculation,
        "unit": unit,
        "period": period,
        "scope": scope,
        "evidence_values": ref_values_exist,
        "exact_evidence": exact_evidence,
    }


def _make_task(
    *,
    source_split: str,
    record_index: int,
    table_uid: str,
    table: list[list[Any]],
    row_index: int,
    current_column: int,
    prior_column: int,
    current_period: str,
    prior_period: str,
    task_type: str,
    max_table_rows: int = 9,
) -> dict[str, Any] | None:
    """Create one controlled financial-table task and paired variants."""
    cells = _source_cells(table)
    target_cells = [cells.get((row_index, prior_column)), cells.get((row_index, current_column))]
    if any(cell is None for cell in target_cells):
        return None
    typed_cells = [cell for cell in target_cells if cell is not None]
    try:
        answer, formula = _recompute_target(typed_cells, task_type)
    except ZeroDivisionError:
        return None
    if not math.isfinite(answer):
        return None
    row_label = typed_cells[0].row_label
    unit = infer_unit(row_label, typed_cells[1].column_label)
    refs = [cell.ref.to_json() for cell in typed_cells]
    expected = {
        "answer": json_number(answer),
        "unit": unit,
        "formula": formula,
        "evidence_refs": refs,
    }

    visible_rows = {
        row_index,
        max(1, row_index - 2),
        min(max(1, len(table) - 1), row_index + 2),
    }
    numeric_rows = sorted({cell.row_index for cell in cells.values()})
    if numeric_rows:
        visible_rows.add(numeric_rows[0])
        visible_rows.add(numeric_rows[-1])
    visible_rows = {index for index in visible_rows if 1 <= index < len(table)}
    visible_rows = set(sorted(visible_rows)[:max_table_rows])
    year_columns = _year_columns(table)
    visible_columns = {prior_column, current_column, 0}
    for column_index, _ in year_columns[:6]:
        visible_columns.add(column_index)

    table_text = visible_table_text(table, visible_rows, visible_columns)
    question = (
        f"Scope: {row_label}. From {prior_period} to {current_period}, "
        + (
            "what is the percentage change?"
            if task_type == "percent_change"
            else "what is the numeric change?"
        )
        + f" Report the answer in {unit} units."
    )
    prompt = build_prompt(question, table_text)

    candidates = _candidate_targets(
        expected,
        table,
        cells,
        typed_cells,
        current_period,
        prior_period,
        task_type,
    )

    irrelevant_cell = next(
        (
            cell
            for cell in cells.values()
            if cell.ref.to_json() not in set(refs)
            and cell.row_index in visible_rows
            and cell.column_index in visible_columns
        ),
        None,
    )
    irrelevant_variant: dict[str, Any] | None = None
    if irrelevant_cell is not None:
        mutated = irrelevant_cell.value + max(1.0, abs(irrelevant_cell.value) * 0.1)
        mutations = {(irrelevant_cell.row_index, irrelevant_cell.column_index): mutated}
        variant_text = visible_table_text(
            table,
            visible_rows,
            visible_columns,
            mutations=mutations,
        )
        irrelevant_variant = {
            "variant_id": "irrelevant_change",
            "prompt": build_prompt(question, variant_text),
            "expected": expected,
            "mutation_ref": irrelevant_cell.ref.to_json(),
        }

    mutated_cells = typed_cells.copy()
    mutated_cells[1] = SourceCell(
        row_index=typed_cells[1].row_index,
        column_index=typed_cells[1].column_index,
        row_label=typed_cells[1].row_label,
        column_label=typed_cells[1].column_label,
        value=typed_cells[1].value + max(1.0, abs(typed_cells[1].value) * 0.1),
    )
    relevant_answer, relevant_formula = _recompute_target(mutated_cells, task_type)
    relevant_expected = {
        "answer": json_number(relevant_answer),
        "unit": unit,
        "formula": relevant_formula,
        "evidence_refs": refs,
    }
    relevant_text = visible_table_text(
        table,
        visible_rows,
        visible_columns,
        mutations={
            (
                mutated_cells[1].row_index,
                mutated_cells[1].column_index,
            ): mutated_cells[1].value
        },
    )
    relevant_variant = {
        "variant_id": "relevant_change",
        "prompt": build_prompt(question, relevant_text),
        "expected": relevant_expected,
        "mutation_ref": mutated_cells[1].ref.to_json(),
    }

    bucket = int(stable_hash(table_uid)[:8], 16) / 0xFFFFFFFF
    derived_split = source_split
    if source_split == "train":
        derived_split = "train" if bucket < 0.75 else ("dev" if bucket < 0.875 else "test")
    period_token = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        f"{prior_period}_{current_period}",
    ).strip("_")
    task_id = (
        f"FL_{source_split}_{table_uid[:8]}_R{row_index}_"
        f"{period_token}_{task_type}"
    )
    return {
        "schema": "financial_feedback_task_v1",
        "task_id": task_id,
        "source_split": source_split,
        "split": derived_split,
        "source_record_index": record_index,
        "table_uid": table_uid,
        "row_index": row_index,
        "task_type": task_type,
        "question": question,
        "prompt": prompt,
        "table_text": table_text,
        "current_period": current_period,
        "prior_period": prior_period,
        "row_label": row_label,
        "unit": unit,
        "expected": expected,
        "candidates": candidates,
        "variants": {
            "irrelevant_change": irrelevant_variant,
            "relevant_change": relevant_variant,
        },
    }


def build_tasks_from_records(
    records: list[dict[str, Any]],
    source_split: str,
    *,
    max_tasks_per_table: int = 6,
    seed: int = 20261023,
) -> list[dict[str, Any]]:
    """Build controlled period/row/unit calculation tasks from TAT-QA records."""
    tasks: list[dict[str, Any]] = []
    for record_index, record in enumerate(records):
        table_payload = record.get("table", {})
        table = table_payload.get("table")
        table_uid = str(table_payload.get("uid", f"record_{record_index}"))
        if not isinstance(table, list) or len(table) < 3:
            continue
        year_columns = _year_columns(table)
        if len(year_columns) < 2:
            continue
        cells = _source_cells(table)
        table_tasks: list[dict[str, Any]] = []
        for row_index in sorted({cell.row_index for cell in cells.values()}):
            valid_columns = [
                (column_index, period)
                for column_index, period in year_columns
                if (row_index, column_index) in cells
            ]
            for pair_index in range(len(valid_columns) - 1):
                prior_column, prior_period = valid_columns[pair_index]
                current_column, current_period = valid_columns[pair_index + 1]
                for task_type in ("difference", "percent_change"):
                    task = _make_task(
                        source_split=source_split,
                        record_index=record_index,
                        table_uid=table_uid,
                        table=table,
                        row_index=row_index,
                        current_column=current_column,
                        prior_column=prior_column,
                        current_period=current_period,
                        prior_period=prior_period,
                        task_type=task_type,
                    )
                    if task is not None:
                        table_tasks.append(task)
                if len(table_tasks) >= max_tasks_per_table:
                    break
            if len(table_tasks) >= max_tasks_per_table:
                break
        rng = random.Random(f"{seed}:{table_uid}")
        rng.shuffle(table_tasks)
        tasks.extend(table_tasks[:max_tasks_per_table])
    return sorted(tasks, key=lambda task: task["task_id"])


def choose_candidate(task: dict[str, Any], filter_name: str) -> dict[str, Any]:
    """Choose a candidate completion under a deterministic feedback filter."""
    candidates = task["candidates"]
    by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    correct = by_id["correct"]
    if filter_name == "evidence_dependency":
        return correct
    preferred = (
        "answer_correct_evidence_wrong"
        if int(stable_hash(task["task_id"])[:8], 16) % 2 == 0
        else "unit_error"
    )
    if filter_name == "answer_execution":
        candidate = by_id.get(preferred)
        checks = candidate["checks"] if candidate else correct["checks"]
        if candidate and checks["calculation"]:
            return candidate
        return correct
    if filter_name == "cheap_consistency":
        candidate = by_id.get("answer_correct_evidence_wrong")
        if candidate and all(
            candidate["checks"][key]
            for key in ("calculation", "unit", "period", "evidence_values")
        ):
            return candidate
        return correct
    raise ValueError(f"unknown_filter:{filter_name}")


def target_to_training_text(task: dict[str, Any], target: dict[str, Any]) -> str:
    """Create one full causal-LM training string."""
    return task["prompt"] + "\n" + canonical_target(target)


def evaluate_prediction(
    generated_text: str,
    task: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Parse and score one model prediction against a task reference."""
    text = generated_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    strict_parsed = False
    parsed: dict[str, Any] | None = None
    try:
        candidate = json.loads(text)
        if isinstance(candidate, dict):
            parsed = candidate
            strict_parsed = True
    except json.JSONDecodeError:
        parsed = extract_contract_object(text)
    if parsed is None:
        return {
            "interface_valid": False,
            "embedded_valid": False,
            "postprocess_recovered": False,
            "answer_correct": False,
            "strict_answer_correct": False,
            "target": None,
            "checks": {
                "calculation": False,
                "unit": False,
                "period": False,
                "scope": False,
                "evidence_values": False,
                "exact_evidence": False,
            },
        }
    try:
        answer = float(parsed["answer"])
        target = {
            "answer": answer,
            "unit": str(parsed["unit"]),
            "formula": str(parsed["formula"]),
            "evidence_refs": [str(value) for value in parsed["evidence_refs"]],
        }
    except (ValueError, TypeError, KeyError):
        return {
            "interface_valid": False,
            "embedded_valid": False,
            "postprocess_recovered": False,
            "answer_correct": False,
            "strict_answer_correct": False,
            "target": None,
            "checks": {
                "calculation": False,
                "unit": False,
                "period": False,
                "scope": False,
                "evidence_values": False,
                "exact_evidence": False,
            },
        }
    checks = evaluate_target_checks(
        target,
        expected,
        _source_cells_from_task(task),
        task["current_period"],
        task["prior_period"],
    )
    answer_correct = math.isclose(
        answer,
        float(expected["answer"]),
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    return {
        "interface_valid": strict_parsed,
        "embedded_valid": True,
        "postprocess_recovered": not strict_parsed,
        "answer_correct": answer_correct,
        "strict_answer_correct": strict_parsed and answer_correct,
        "target": target,
        "checks": checks,
    }


def _source_cells_from_task(task: dict[str, Any]) -> dict[tuple[int, int], SourceCell]:
    """Reconstruct visible source cells from the rendered task table."""
    cells: dict[tuple[int, int], SourceCell] = {}
    lines = task["table_text"].splitlines()
    if not lines:
        return cells
    column_labels = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"(C\d+)=([^|]+)", lines[0])
    }
    for line in lines[1:]:
        row_match = re.match(r"^(R\d+) \[(.*?)\] (.*)$", line)
        if not row_match:
            continue
        row_id, row_label, value_text = row_match.groups()
        row_index = int(row_id[1:])
        for match in re.finditer(r"(C\d+)=([^|\s]+)", value_text):
            column_id, raw_value = match.groups()
            value = parse_numeric(raw_value)
            if value is None:
                continue
            column_index = int(column_id[1:])
            cells[(row_index, column_index)] = SourceCell(
                row_index=row_index,
                column_index=column_index,
                row_label=row_label,
                column_label=column_labels.get(column_id, ""),
                value=value,
            )
    return cells


def write_json(path: Path, payload: Any) -> None:
    """Write canonical pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write canonical JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

