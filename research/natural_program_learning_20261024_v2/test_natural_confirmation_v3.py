"""Focused tests for unseen-family selection and corrected variants."""

from __future__ import annotations

import json
from pathlib import Path

from run_natural_confirmation_v3 import build_instances, corrected_variants, select_tasks
from run_natural_program_experiment_v2 import training_rows


def make_tasks() -> list[dict[str, object]]:
    rows = []
    for index in range(600):
        task_id = f"NAT_train_{index:04d}"
        rows.append({
            "task_id": task_id,
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


def test_selection_excludes_training_tasks(tmp_path: Path) -> None:
    tasks = make_tasks()
    prior = tmp_path / "prior.jsonl"
    prior.write_text(json.dumps({"instance_id": "x", "table_uid": "table-0599"}) + "\n", encoding="utf-8")
    training_ids = {row["task_id"] for row in training_rows(tasks, "ordinary_answer_execution_sft")}
    selected = select_tasks(tasks, prior)
    assert len(selected) == 24
    assert not ({task["task_id"] for task in selected} & training_ids)
    assert all(task["table_uid"] != "table-0599" for task in selected)


def test_corrected_variants_store_prompt_table() -> None:
    variants = corrected_variants(make_tasks()[0])
    assert len(variants) == 3
    assert all(variant["table_text"] in variant["prompt"] for variant in variants)
    assert variants[0]["table_text"] == make_tasks()[0]["table_text"]
