"""Focused tests for paired task analysis."""

from __future__ import annotations

from analyze_source_disjoint_confirmation_v4 import paired_rows


def test_paired_metrics_require_all_three_variants() -> None:
    rows = []
    for variant, correct in (("original", True), ("relevant_change", True), ("irrelevant_change", True)):
        rows.append({
            "model_arm": "ordinary",
            "source_task_id": "t1",
            "table_uid": "table-1",
            "variant": variant,
            "program_correct": correct,
        })
    assert paired_rows(rows)[0]["paired_all_three"] is True
