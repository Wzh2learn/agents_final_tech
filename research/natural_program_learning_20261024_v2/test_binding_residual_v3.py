"""Focused tests for binding-residual attribution."""

from __future__ import annotations

from analyze_binding_residual_v3 import classify_row, extract_target, parse_cells, refs_in_program


def fixture() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    task = {
        "table_text": "columns: C0= | C1=2020 | C2=2019\nR1 [Revenue] C0=Revenue | C1=100 | C2=100",
        "expected": {
            "answer": 0,
            "program": {"op": "sub", "left": {"ref": "R1:C1"}, "right": {"ref": "R1:C2"}},
            "evidence_refs": ["R1:C1", "R1:C2"],
        },
    }
    result = {
        "interface_valid": True,
        "program_executable": True,
        "program_correct": False,
        "variant": "relevant_change",
        "generated_text": '{"program":{"op":"sub","left":{"ref":"R1:C2"},"right":{"ref":"R1:C2"}},"evidence_refs":["R1:C2"],"unit":"x"}',
    }
    return task, result, parse_cells(task["table_text"])


def test_same_value_reference_is_attributed_to_alias() -> None:
    task, result, cells = fixture()
    target = extract_target(result["generated_text"])
    assert target is not None
    assert refs_in_program(target["program"]) == ["R1:C2"]
    assert classify_row(result, task, cells) == "same_value_alias_or_reference"


def test_parse_failure_is_not_called_alias() -> None:
    task, result, cells = fixture()
    result["interface_valid"] = False
    result["generated_text"] = "not json"
    assert classify_row(result, task, cells) == "format_or_parse"
