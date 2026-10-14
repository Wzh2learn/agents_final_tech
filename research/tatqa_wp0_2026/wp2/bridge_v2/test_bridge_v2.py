from __future__ import annotations

import json
import sys
from pathlib import Path

BRIDGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BRIDGE_DIR))

from constrained_decoding_v2 import build_language
from prompt_v2 import (
    CONSUME_TEMPLATE_SHA256,
    PLAN_TEMPLATE_SHA256,
    build_messages,
)
from validate_v2 import (
    StageRetryState,
    load_schema_document,
    validate_stage_response,
)


PLAN_VALID = '{"tool":"calc","params":{"expression":"12 - 4"}}'
CONSUME_VALID = (
    '{"row":"Revenue","periods":["2019","2018"],'
    '"delta_source":-8.5,"delta_target":0,"unit":"unit"}'
)


def test_schema_document_hash_is_pinned() -> None:
    document = load_schema_document()
    assert document["schema_document_sha256"] == (
        "53c3665fcd2679c19a5735a79e74834750cacb516f3f6d2ac995b74a45fd81c3"
    )
    assert set(document["schemas"]) == {"plan", "consume"}


def test_three_parse_routes_and_schema_validation() -> None:
    strict = validate_stage_response("plan", PLAN_VALID)
    fenced = validate_stage_response(
        "consume",
        "```json\n" + CONSUME_VALID + "\n```",
    )
    embedded = validate_stage_response(
        "plan",
        "prose before " + PLAN_VALID + " prose after",
    )
    violation = validate_stage_response(
        "consume",
        json.dumps(
            {
                "row": "Revenue",
                "periods": ["2019"],
                "delta_source": 8,
                "delta_target": 8,
                "unit": "unit",
            }
        ),
    )
    assert strict.ok and strict.route == "strict_json"
    assert fenced.ok and fenced.route == "code_fenced_json"
    assert embedded.ok and embedded.route == "first_balanced_object"
    assert not violation.ok
    assert violation.schema_error is not None


def test_never_silently_coerce_number_or_expression() -> None:
    string_number = validate_stage_response(
        "consume",
        json.dumps(
            {
                "row": "Revenue",
                "periods": ["2019", "2018"],
                "delta_source": "8",
                "delta_target": 8,
                "unit": "unit",
            }
        ),
    )
    bad_expression = validate_stage_response(
        "plan",
        '{"tool":"calc","params":{"expression":"1,801.5 - 1,661.1"}}',
    )
    assert not string_number.ok
    assert not bad_expression.ok
    assert "JSON number" in (string_number.schema_error or "")
    assert "character class" in (bad_expression.schema_error or "")

    exponent_number = validate_stage_response(
        "consume",
        '{"row":"Revenue","periods":["2019","2018"],'
        '"delta_source":8e2,"delta_target":8,"unit":"unit"}',
    )
    assert not exponent_number.ok
    assert "decimal character class" in (exponent_number.schema_error or "")


def test_retry_is_counted_and_bounded() -> None:
    state = StageRetryState()
    state.count_request()
    failure = validate_stage_response("plan", "not json")
    first = state.retry_prompt("MOCK task", failure)
    assert state.requests == 1 and state.retries == 1
    assert "PREVIOUS_OUTPUT_ERROR=" in first
    try:
        state.retry_prompt("MOCK task", failure)
    except ValueError as exc:
        assert "exhausted" in str(exc)
    else:
        raise AssertionError("second retry must fail closed")


def test_prompt_hashes_and_one_example_per_stage() -> None:
    plan = build_messages("plan", "MOCK")
    consume = build_messages("consume", "MOCK")
    assert plan[0]["role"] == "system" and consume[0]["role"] == "system"
    assert plan[0]["content"] == "Return exactly one JSON object; no prose, no code fences"
    assert plan[1]["content"].count("LOCKED_EXAMPLE=") == 1
    assert consume[1]["content"].count("LOCKED_EXAMPLE=") == 1
    assert PLAN_TEMPLATE_SHA256 == (
        "39cf699dfbb1c6f5494d33ec5232c2d14e4cf91313f5b6e302028e8f601b3616"
    )
    assert CONSUME_TEMPLATE_SHA256 == (
        "fe6708ecb9c99ecffb15b447d0b169b11688017094b0c2418fde1cecc567c925"
    )


def test_prefix_languages_accept_and_reject_examples() -> None:
    plan = build_language("plan")
    consume = build_language("consume")
    assert plan.is_complete(PLAN_VALID)
    assert consume.is_complete(CONSUME_VALID)
    assert not plan.is_complete('{"tool":"calc","params":{"expression":""}}')
    assert not consume.is_prefix(CONSUME_VALID[:-1] + "e")
    assert consume.is_prefix(CONSUME_VALID)
