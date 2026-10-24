"""Correct variant scoring by executing against the table shown in the prompt."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from analyze_binding_residual_v3 import extract_target, parse_cells, program_value, refs_in_program


def extract_prompt_table(prompt: str) -> str:
    """Extract the visible table block from a natural-program prompt."""
    marker = "Table:\n"
    start = prompt.find(marker)
    if start < 0:
        raise ValueError("prompt_table_marker_missing")
    start += len(marker)
    end = prompt.find("\n\nQuestion:", start)
    if end < 0:
        raise ValueError("prompt_question_marker_missing")
    table = prompt[start:end].strip()
    if not table.startswith("columns:"):
        raise ValueError("prompt_table_columns_missing")
    return table


def rescore_generation(
    result: dict[str, Any],
    instance: dict[str, Any],
) -> dict[str, Any]:
    """Rescore one frozen generation against its actual visible variant table."""
    prompt_table = extract_prompt_table(str(instance["prompt"]))
    cells = parse_cells(prompt_table)
    target = extract_target(str(result.get("generated_text", "")))
    output = dict(result)
    output["program_correct_v2"] = bool(result.get("program_correct"))
    output["failure_v2"] = str(result.get("failure"))
    output["table_text_v2"] = instance.get("table_text")
    output["table_text"] = prompt_table
    output["table_text_source"] = "prompt_variant_v3"
    if target is None:
        output.update({
            "interface_valid": False,
            "program_executable": False,
            "program_correct": False,
            "program_value": None,
            "refs_valid": False,
            "failure": "program_parse",
        })
    else:
        refs = refs_in_program(target.get("program"))
        refs_valid = bool(refs) and all(ref in cells for ref in refs)
        try:
            value = program_value(target["program"], cells)
            executable = math.isfinite(value)
        except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError):
            value = None
            executable = False
        correct = (
            executable
            and value is not None
            and math.isclose(
                float(value),
                float(instance["expected"]["answer"]),
                rel_tol=1e-6,
                abs_tol=1e-6,
            )
        )
        output.update({
            "interface_valid": True,
            "program_executable": executable,
            "program_correct": correct,
            "program_value": value,
            "refs_valid": refs_valid,
            "failure": "none" if correct else ("tool_execution" if executable else "program_execution"),
        })
    output["measurement_flip"] = bool(output["program_correct_v2"] != output["program_correct"])
    output["measurement_correction"] = (
        "V2_SCORED_ON_STALE_TASK_TABLE"
        if output["measurement_flip"] and instance.get("table_text") != prompt_table
        else "NONE"
    )
    return output
