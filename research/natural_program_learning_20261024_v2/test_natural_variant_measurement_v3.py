"""Regression tests for prompt-visible variant scoring."""

from __future__ import annotations

from analyze_binding_residual_v3 import parse_cells
from natural_variant_measurement_v3 import extract_prompt_table, rescore_generation
from semantic_delivery_check_v3 import semantic_check


def test_rescore_uses_prompt_variant_table_not_stale_task_table() -> None:
    instance = {
        "prompt": (
            "Answer.\n\nTable:\n"
            "columns: C0= | C1=2020 | C2=2019\n"
            "R1 [Revenue] C0=Revenue | C1=120 | C2=100\n\n"
            "Question: change?"
        ),
        "table_text": (
            "columns: C0= | C1=2020 | C2=2019\n"
            "R1 [Revenue] C0=Revenue | C1=110 | C2=100"
        ),
        "expected": {
            "answer": 20,
            "program": {"op": "sub", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
        },
    }
    result = {
        "generated_text": '{"program":{"op":"sub","left":{"ref":"R1:C1"},"right":{"ref":"R1:C2"}},"evidence_refs":["R1:C1","R1:C2"],"unit":"x"}',
        "program_correct": False,
        "failure": "tool_execution",
    }
    corrected = rescore_generation(result, instance)
    assert extract_prompt_table(instance["prompt"]).endswith("R1 [Revenue] C0=Revenue | C1=120 | C2=100")
    assert corrected["program_correct_v2"] is False
    assert corrected["program_correct"] is True
    assert corrected["measurement_flip"] is True
    assert corrected["measurement_correction"] == "V2_SCORED_ON_STALE_TASK_TABLE"


def test_parse_failure_remains_fail_closed() -> None:
    instance = {
        "prompt": "Table:\ncolumns: C0= | C1=2020\nR1 [Revenue] C0=Revenue | C1=10\n\nQuestion: x?",
        "table_text": "stale",
        "expected": {"answer": 10},
    }
    corrected = rescore_generation(
        {"generated_text": "not json", "program_correct": True, "failure": "none"},
        instance,
    )
    assert corrected["program_correct"] is False
    assert corrected["failure"] == "program_parse"


def test_multiline_headers_restore_visible_period_bindings() -> None:
    table = (
        "columns: C0=At December 31, | C1= | C2=\n"
        "R1 [] C0= | C1=2019 | C2=2018\n"
        "R2 [Cash] C0=Cash | C1=437 | C2=268"
    )
    cells = parse_cells(table)
    assert cells["R2:C1"]["period_labels"] == ["2019"]
    assert cells["R2:C2"]["period_labels"] == ["2018"]
    decision, reasons = semantic_check(
        "What was the change in cash between 2018 and 2019?",
        {"op": "sub", "left": {"ref": "R2:C1"}, "right": {"ref": "R2:C2"}},
        cells,
    )
    assert decision == "VALID"
    assert reasons == []
