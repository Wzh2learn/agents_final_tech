#!/usr/bin/env python3
"""Canonical numeric-token identity shared by FinQA v2 selection and tests."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any


NUM_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)")
ARG_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


class NumericTokenCanonicalizationError(ValueError):
    def __init__(self, code: str, **detail: Any) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _decimal(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise NumericTokenCanonicalizationError(
            "invalid_numeric_token", token=text
        ) from exc
    if not value.is_finite():
        raise NumericTokenCanonicalizationError(
            "invalid_numeric_token", token=text
        )
    return value


def _format_decimal(value: Decimal) -> str:
    sign, digits, exponent = value.as_tuple()
    digit_text = "".join(str(digit) for digit in digits)
    if exponent >= 0:
        integer_text = digit_text + ("0" * exponent)
        fraction_text = ""
    else:
        split_at = len(digit_text) + exponent
        if split_at > 0:
            integer_text = digit_text[:split_at]
            fraction_text = digit_text[split_at:]
        else:
            integer_text = "0"
            fraction_text = ("0" * -split_at) + digit_text

    integer_text = integer_text.lstrip("0") or "0"
    fraction_text = fraction_text.rstrip("0")
    unsigned = (
        integer_text
        if not fraction_text
        else f"{integer_text}.{fraction_text}"
    )
    has_magnitude = any(digit != 0 for digit in digits)
    prefix = "-" if sign and has_magnitude else ""
    return f"{prefix}{unsigned}"


def canonical_numeric_token(value: Any) -> str:
    """Return the exact fixed-point canonical form of one numeric literal."""
    token_text = str(value).strip()
    if not ARG_RE.fullmatch(token_text):
        raise NumericTokenCanonicalizationError(
            "argument_not_numeric_literal", token=token_text
        )
    return _format_decimal(_decimal(token_text))


def try_canonical_numeric_token(value: Any) -> str | None:
    """Return a canonical token for a strict literal, otherwise ``None``."""
    token_text = str(value).strip()
    if not ARG_RE.fullmatch(token_text):
        return None
    try:
        return canonical_numeric_token(token_text)
    except NumericTokenCanonicalizationError:
        return None


def numeric_tokens(value: Any) -> set[str]:
    """Canonicalize every finite numeric literal found in free text."""
    tokens: set[str] = set()
    for match in NUM_RE.findall(str(value or "")):
        token = try_canonical_numeric_token(match)
        if token is not None:
            tokens.add(token)
    return tokens
