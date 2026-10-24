"""Focused tests for diversity-preserving error weighting."""

from __future__ import annotations

from run_weighted_error_repair_v5 import weighted_rows


def test_weighted_and_uniform_rows_keep_all_task_ids() -> None:
    tasks = []
    corrected = {}
    for index in range(48):
        task_id = f"t{index:02d}"
        tasks.append({
            "task_id": task_id,
            "table_uid": f"table-{index:02d}",
            "prompt": f"prompt {index}",
        })
        corrected[task_id] = {
            "program": {"ref": "R1:C1"},
            "evidence_refs": ["R1:C1"],
            "unit": "x",
        }
    wrong = {task["task_id"] for task in tasks[:9]}
    weighted = weighted_rows(tasks, corrected, wrong, "weighted_error_repair_sft")
    uniform = weighted_rows(tasks, corrected, wrong, "uniform_mixed_control_sft")
    assert len(weighted) == len(uniform) == 256
    assert {row["task_id"] for row in weighted} == {task["task_id"] for task in tasks}
    assert {row["task_id"] for row in uniform} == {task["task_id"] for task in tasks}
    assert sum(row["task_id"] in wrong for row in weighted) > sum(row["task_id"] in wrong for row in uniform)
