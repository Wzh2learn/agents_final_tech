"""Source-role isolation and semantic constant contracts for document tasks."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


SOURCE_FIELDS = (
    "document_uid",
    "report_uid",
    "company_uid",
    "table_uid",
    "question_uid",
)


@dataclass(frozen=True)
class SourceRole:
    """Stable source identity used to keep related tasks in one split."""

    task_id: str
    keys: tuple[tuple[str, str], ...]

    @property
    def primary_key(self) -> tuple[str, str]:
        return self.keys[-1]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_role(task: dict[str, Any]) -> SourceRole:
    """Build the highest available source identity for one task."""
    task_id = str(task.get("task_id") or task.get("question_uid") or "")
    keys = tuple(
        (field, str(task[field]))
        for field in SOURCE_FIELDS
        if task.get(field) not in (None, "")
    )
    if not keys:
        raise ValueError(f"missing_source_identity:{task_id}")
    return SourceRole(task_id=task_id, keys=keys)


def role_groups(tasks: Iterable[dict[str, Any]]) -> dict[tuple[str, str], set[str]]:
    groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for task in tasks:
        role = source_role(task)
        for key in role.keys:
            groups[key].add(role.task_id)
    return groups


def assert_role_disjoint(assignments: dict[str, Iterable[dict[str, Any]]]) -> None:
    """Reject any source key shared by two named roles."""
    seen: dict[tuple[str, str], str] = {}
    for role_name, tasks in assignments.items():
        for key, task_ids in role_groups(tasks).items():
            if key in seen and seen[key] != role_name:
                raise ValueError(f"source_role_overlap:{key}:{seen[key]}:{role_name}")
            seen[key] = role_name
            if not task_ids:
                raise ValueError(f"empty_source_role_group:{role_name}:{key}")


def select_source_disjoint_tasks(
    tasks: Iterable[dict[str, Any]],
    *,
    excluded_task_ids: Iterable[str] = (),
    excluded_source_keys: Iterable[tuple[str, str]] = (),
    count: int,
) -> list[dict[str, Any]]:
    """Select tasks whose complete source-role key set is unseen."""
    excluded_ids = set(excluded_task_ids)
    excluded = set(excluded_source_keys)
    candidates = []
    for task in tasks:
        role = source_role(task)
        if role.task_id in excluded_ids:
            continue
        if any(key in excluded for key in role.keys):
            continue
        candidates.append(task)
    candidates.sort(key=lambda task: stable_hash(source_role(task).task_id))
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str]] = set()
    for task in candidates:
        role = source_role(task)
        if any(key in selected_keys for key in role.keys):
            continue
        selected.append(task)
        selected_keys.update(role.keys)
        if len(selected) == count:
            return selected
    raise ValueError(f"insufficient_source_disjoint_tasks:{len(selected)}")


def role_manifest(
    assignments: dict[str, Iterable[dict[str, Any]]],
) -> dict[str, Any]:
    """Return a machine-readable role manifest and overlap report."""
    roles: dict[str, Any] = {}
    all_keys: dict[tuple[str, str], list[str]] = defaultdict(list)
    for role_name, tasks in assignments.items():
        task_list = list(tasks)
        groups = role_groups(task_list)
        roles[role_name] = {
            "task_count": len(task_list),
            "source_keys": [
                {"field": field, "value": value, "task_ids": sorted(task_ids)}
                for (field, value), task_ids in sorted(groups.items())
            ],
        }
        for key in groups:
            all_keys[key].append(role_name)
    overlaps = [
        {"field": field, "value": value, "roles": role_names}
        for (field, value), role_names in sorted(all_keys.items())
        if len(role_names) > 1
    ]
    return {"roles": roles, "overlaps": overlaps}


def expected_average_count(question: str, numerator: Any) -> int | None:
    """Infer a structural divisor only from explicit count evidence."""
    text = question.casefold()
    if not re.search(r"\baverage\b|\bmean\b", text):
        return None
    range_match = re.search(
        r"\bfrom\s+((?:19|20)\d{2})\s+to\s+((?:19|20)\d{2})\b",
        text,
    )
    if range_match:
        start, end = map(int, range_match.groups())
        return end - start + 1 if end >= start else None
    hyphen_range = re.search(
        r"\b((?:19|20)\d{2})\s*-\s*((?:19|20)\d{2})\b",
        text,
    )
    if hyphen_range:
        start, end = map(int, hyphen_range.groups())
        return end - start + 1 if end >= start else None
    years = [int(year) for year in re.findall(r"\b(?:19|20)\d{2}\b", text)]
    if len(years) >= 2:
        return len(set(years))
    if re.search(r"\b(?:and|&)\b", text) and re.search(r"\baverage\b|\bmean\b", text):
        return 2
    return None


def additive_leaf_count(program: Any) -> int:
    """Count leaf operands in an additive numerator."""
    if not isinstance(program, dict):
        return 0
    if "ref" in program or "const" in program:
        return 1
    if program.get("op") == "add":
        return additive_leaf_count(program.get("left")) + additive_leaf_count(program.get("right"))
    return max(additive_leaf_count(program.get("left")), additive_leaf_count(program.get("right")))


def classify_average_denominator(
    question: str,
    denominator: dict[str, Any],
    denominator_cell: dict[str, Any] | None,
    numerator: Any = None,
) -> str:
    """Classify a small denominator without treating every integer as evidence."""
    if not re.search(r"\baverage\b|\bmean\b", question, re.I):
        return "NON_AVERAGE_DENOMINATOR"
    value = denominator.get("const") if "const" in denominator else None
    if value is not None and denominator_cell is None:
        expected = expected_average_count(question, denominator)
        operand_count = additive_leaf_count(numerator)
        if expected is not None and abs(float(value) - expected) < 1e-9:
            return "STRUCTURAL_CONSTANT_ALREADY"
        if operand_count >= 2 and abs(float(value) - operand_count) < 1e-9:
            return "STRUCTURAL_CONSTANT_ALREADY"
    if value is None and denominator_cell is not None:
        value = denominator_cell.get("value")
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "UNRESOLVED"
    expected = expected_average_count(question, denominator)
    operand_count = additive_leaf_count(numerator)
    label_text = " ".join(
        str(denominator_cell.get(field, ""))
        for field in ("row_label", "column_label")
    ).casefold() if denominator_cell is not None else ""
    question_text = question.casefold()
    semantic_overlap = any(
        token and token in label_text
        for token in re.findall(r"[a-z0-9]+", question_text)
        if len(token) > 3
    )
    single_year_average = bool(
        re.search(r"\b(?:19|20)\d{2}\b", question)
        and re.search(r"\baverage\b|\bmean\b", question)
    )
    if expected is not None and abs(numeric - expected) < 1e-9:
        return "STRUCTURAL_CONSTANT_MISBOUND"
    if single_year_average and operand_count >= 2 and abs(numeric - operand_count) < 1e-9:
        return "UNRESOLVED_REFERENCE_QUESTION_MISMATCH"
    if operand_count >= 2 and abs(numeric - operand_count) < 1e-9:
        return "STRUCTURAL_CONSTANT_MISBOUND"
    if semantic_overlap:
        return "LEGAL_FINANCIAL_DENOMINATOR"
    if denominator_cell is not None and 2 <= numeric <= 12:
        return "UNRESOLVED"
    return "LEGAL_FINANCIAL_DENOMINATOR"
