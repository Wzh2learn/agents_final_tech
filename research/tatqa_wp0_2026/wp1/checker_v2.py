from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

import checker as checker_v1


SCALES = checker_v1.SCALES
UNIT_ALIASES = checker_v1.UNIT_ALIASES
CORRECT_OUTCOMES = checker_v1.CORRECT_OUTCOMES
OUTCOME_CLASSES = checker_v1.OUTCOME_CLASSES
Gold = checker_v1.Gold
PreparedItem = checker_v1.PreparedItem

normalize_unit = checker_v1.normalize_unit
parse_numeric_cell = checker_v1.parse_numeric_cell
conversion_factor = checker_v1.conversion_factor
recompute_gold = checker_v1.recompute_gold
prepare_item = checker_v1.prepare_item
parse_answer = checker_v1.parse_answer


def score_prepared(
    prepared: PreparedItem, answer_text: str
) -> dict[str, str]:
    answer = parse_answer(answer_text)
    if answer is None:
        return {"outcome": "unknown"}
    if answer["answer_class"] != "parsed":
        return {"outcome": answer["answer_class"]}
    if answer["row"] != prepared.row_label:
        return {"outcome": "wrong"}

    gold = prepared.gold
    if (
        answer["periods"] == [prepared.early_period, prepared.late_period]
        and answer["delta_source"] == -gold.delta_source
        and answer["unit"] != gold.target_unit
    ):
        return {"outcome": "wrong_unit"}
    if (
        answer["periods"] == [prepared.early_period, prepared.late_period]
        and answer["delta_source"] == -gold.delta_source
        and answer["delta_target"] == -gold.delta_target
    ):
        return {"outcome": "correct_other_form"}
    if answer["periods"] == [
        prepared.early_period,
        prepared.late_period,
    ]:
        return {"outcome": "wrong"}

    if answer["periods"] != [prepared.late_period, prepared.early_period]:
        return {"outcome": "wrong_period"}

    source_correct = answer["delta_source"] == gold.delta_source
    target_correct = answer["delta_target"] == gold.delta_target
    if source_correct and not target_correct:
        return {"outcome": "wrong_unit"}
    if (
        source_correct
        and target_correct
        and answer["unit"] != gold.target_unit
    ):
        return {"outcome": "wrong_unit"}
    if (
        source_correct
        and target_correct
        and answer["unit"] == gold.target_unit
    ):
        return {"outcome": "correct"}
    return {"outcome": "wrong"}


def score_item(item: Mapping[str, Any], answer_text: str) -> dict[str, str]:
    prepared = prepare_item(item)
    return score_prepared(prepared, answer_text)


aggregate_outcomes = checker_v1.aggregate_outcomes
paired_origin_differences = checker_v1.paired_origin_differences
apply_regression = checker_v1.apply_regression


__all__ = [
    "CORRECT_OUTCOMES",
    "OUTCOME_CLASSES",
    "SCALES",
    "UNIT_ALIASES",
    "Gold",
    "PreparedItem",
    "aggregate_outcomes",
    "apply_regression",
    "conversion_factor",
    "normalize_unit",
    "paired_origin_differences",
    "parse_answer",
    "parse_numeric_cell",
    "prepare_item",
    "recompute_gold",
    "score_item",
    "score_prepared",
]
