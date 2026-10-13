from __future__ import annotations

from decimal import Decimal


def canonical_plain_decimal(value: Decimal) -> str:
    if not isinstance(value, Decimal):
        raise TypeError("value must be Decimal")
    if value.is_zero():
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _grouped_integer(value: Decimal) -> str | None:
    if value != value.to_integral_value():
        return None
    rendered = canonical_plain_decimal(value)
    sign = "-" if rendered.startswith("-") else ""
    digits = rendered.lstrip("+-")
    grouped = ""
    while len(digits) > 3:
        grouped = "," + digits[-3:] + grouped
        digits = digits[:-3]
    return f"{sign}{digits}{grouped}"


def _scientific(value: Decimal) -> str | None:
    if not value.is_finite() or value.is_zero():
        return None
    rendered = format(value.normalize(), "E")
    return rendered.replace("E+", "e").replace("E", "e")


def _zero_padded_integer(value: Decimal) -> str | None:
    if value != value.to_integral_value():
        return None
    rendered = canonical_plain_decimal(value)
    sign = "-" if rendered.startswith("-") else ""
    digits = rendered.lstrip("+-")
    return f"{sign}{digits.zfill(6)}"


def answer_value_needles(
    value: Decimal, exact_str: str | None = None
) -> list[str]:
    forms = [
        canonical_plain_decimal(value),
        str(value),
    ]
    if exact_str is not None:
        forms.append(str(exact_str))
    grouped = _grouped_integer(value)
    scientific = _scientific(value)
    zero_padded = _zero_padded_integer(value)
    forms.extend(
        form for form in (grouped, scientific, zero_padded) if form is not None
    )

    needles: list[str] = []
    for form in forms:
        if form not in needles:
            needles.append(form)
    return needles


__all__ = ["answer_value_needles", "canonical_plain_decimal"]
