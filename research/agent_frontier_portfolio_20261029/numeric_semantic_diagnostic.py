"""Scoped post-hoc numeric-format diagnostic, not a validated task oracle.

The displayed decimal is treated as rounded to its last digit. Percent answers
need a percent sign or a unit-compatible fraction; ambiguous bare magnitudes
are not automatically accepted. Financial units beyond these controls require
task-specific references and are deliberately unresolved.
"""
from decimal import Decimal, InvalidOperation
import re

NUMBER = re.compile(r"^[+-]?(?:\d+)(?:\.\d+)?$")


def classify(expected, actual, mode):
    text = str(actual).strip().replace(",", "")
    if mode not in ("percent_fraction", "unitless"):
        raise ValueError("unsupported mode")
    percent = text.endswith("%")
    number = text[:-1].strip() if percent else text
    if not NUMBER.fullmatch(number):
        return "UNRESOLVED_FORMAT_OR_UNIT"
    try:
        value, target = Decimal(number), Decimal(str(expected))
    except InvalidOperation:
        return "UNRESOLVED_FORMAT_OR_UNIT"
    if mode == "unitless" and percent:
        return "UNRESOLVED_FORMAT_OR_UNIT"
    if mode == "percent_fraction" and not percent and abs(value) > 1:
        return "UNRESOLVED_BARE_PERCENT"
    scale = Decimal("0.01") if percent else Decimal(1)
    half_step = Decimal(1).scaleb(value.as_tuple().exponent) * scale / 2
    candidate = value * scale
    return "ROUNDING_COMPATIBLE" if abs(target - candidate) <= half_step else "INCOMPATIBLE"
