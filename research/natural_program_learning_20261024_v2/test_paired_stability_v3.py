"""Focused tests for cost-matched stability supervision."""

from __future__ import annotations

import json
from pathlib import Path

from run_paired_stability_v3 import (
    build_training_rows,
    select_confirmation_tasks,
    selected_variant,
)


def make_tasks() -> list[dict[str, object]]:
    rows = []
    for index in range(600):
        rows.append({
            "task_id": f"NAT_train_{index:04d}",
            "table_uid": f"table-{index:04d}",
            "split": "train",
            "question": "What was the change in Revenue between 2019 and 2020?",
            "table_text": "columns: C0= | C1=2020 | C2=2019\nR1 [Revenue] C0=Revenue | C1=110 | C2=100\nR2 [Cost] C0=Cost | C1=50 | C2=40",
            "context_text": "",
            "expected": {"answer": 10, "unit": "x", "program": {"op": "sub", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}}, "evidence_refs": ["R1:C1", "R1:C2"]},
            "target": {"unit": "x", "program": {"op": "sub", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}}, "evidence_refs": ["R1:C1", "R1:C2"]},
            "prompt": "Table:\ncolumns: C0= | C1=2020 | C2=2019\nR1 [Revenue] C0=Revenue | C1=110 | C2=100\nR2 [Cost] C0=Cost | C1=50 | C2=40\n\nQuestion: change?",
        })
    return rows


def test_training_arms_match_rows_and_pair_target() -> None:
    tasks = make_tasks()
    control = build_training_rows(tasks, "duplicate_original_control_sft")
    paired = build_training_rows(tasks, "paired_variant_stability_sft")
    assert len(control) == len(paired) == 1024
    assert control[0]["text"] == control[1]["text"]
    assert paired[0]["text"] != paired[1]["text"]
    assert paired[0]["target"] == paired[1]["target"]
    assert selected_variant(tasks[0])["expected"]["program"] == tasks[0]["target"]["program"]


def test_confirmation_excludes_prior_tables(tmp_path: Path) -> None:
    tasks = make_tasks()
    prior = tmp_path / "prior.jsonl"
    first = tmp_path / "first.jsonl"
    prior.write_text(json.dumps({"table_uid": "table-0599"}) + "\n", encoding="utf-8")
    first.write_text(json.dumps({"table_uid": "table-0598"}) + "\n", encoding="utf-8")
    selected = select_confirmation_tasks(tasks, prior, first)
    assert len(selected) == 24
    assert all(task["table_uid"] not in {"table-0598", "table-0599"} for task in selected)
