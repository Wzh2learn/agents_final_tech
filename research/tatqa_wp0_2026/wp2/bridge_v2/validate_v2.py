from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping


SCHEMA_PATH = Path(__file__).with_name("BRIDGE_SCHEMAS_v2.json")
STAGES = frozenset({"plan", "consume"})
PARSER_ROUTES = ("strict_json", "code_fenced_json", "first_balanced_object")
FENCED_JSON_PATTERN = re.compile(
    r"\A```(?:json)?[ \t]*\r?\n(?P<body>.*?)\r?\n```[ \t]*\Z",
    re.DOTALL | re.IGNORECASE,
)
PLAN_EXPRESSION_PATTERN = re.compile(r"^[0-9+\-*/(). ]+$")
DECIMAL_PATTERN = re.compile(r"^-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$")


class RawNumber(str):
    """JSON numeric lexeme preserved for non-coercing schema validation."""


@dataclass(frozen=True)
class RouteResult:
    route: str
    ok: bool
    error: str | None


@dataclass(frozen=True)
class ValidationResult:
    stage: str
    ok: bool
    route: str | None
    payload: dict[str, Any] | None
    parse_routes: list[RouteResult]
    schema_error: str | None
    retry_error: str | None

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def canonical_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_schema_document(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "tatqa_wp2_bridge_schemas_v2":
        raise ValueError("bridge schema document name mismatch")
    schemas = document.get("schemas")
    if not isinstance(schemas, dict) or set(schemas) != STAGES:
        raise ValueError("bridge schema document stages mismatch")
    digest = sha256_bytes(
        json.dumps(
            schemas,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    if digest != document.get("schema_document_sha256"):
        raise ValueError("bridge schema document hash mismatch")
    return document


def _first_balanced_candidate(text: str) -> str | None:
    for start, character in enumerate(text):
        if character != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for end in range(start, len(text)):
            current = text[end]
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : end + 1]
                    return candidate
    return None


def _parse_raw_object(candidate: str) -> dict[str, Any]:
    parsed = json.loads(
        candidate,
        parse_float=RawNumber,
        parse_int=RawNumber,
    )
    if not isinstance(parsed, dict):
        raise ValueError("JSON response must be an object")
    return parsed


def _parse_actual_object(candidate: str) -> dict[str, Any]:
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("JSON response must be an object")
    return parsed


def parse_three_routes(
    text: str,
) -> tuple[
    dict[str, Any] | None,
    str | None,
    str | None,
    list[RouteResult],
]:
    if not isinstance(text, str):
        raise ValueError("completion text must be a string")
    results: list[RouteResult] = []
    strict_candidate = text.strip()
    strict_error = None
    try:
        strict_parsed = _parse_actual_object(strict_candidate)
    except (json.JSONDecodeError, ValueError) as exc:
        strict_parsed = None
        strict_error = f"{type(exc).__name__}: {exc}"
    if isinstance(strict_parsed, dict):
        results.append(RouteResult("strict_json", True, None))
        return strict_parsed, "strict_json", strict_candidate, results
    results.append(
        RouteResult(
            "strict_json",
            False,
            strict_error or "strict JSON response was not an object",
        )
    )

    fenced_match = FENCED_JSON_PATTERN.fullmatch(strict_candidate)
    fenced_error = "code fence unavailable or body invalid"
    if fenced_match is not None:
        fenced_candidate = fenced_match.group("body").strip()
        try:
            fenced_parsed = _parse_actual_object(fenced_candidate)
        except (json.JSONDecodeError, ValueError) as exc:
            fenced_error = f"{type(exc).__name__}: {exc}"
        else:
            if isinstance(fenced_parsed, dict):
                results.append(RouteResult("code_fenced_json", True, None))
                return fenced_parsed, "code_fenced_json", fenced_candidate, results
            fenced_error = "fenced JSON response was not an object"
    results.append(RouteResult("code_fenced_json", False, fenced_error))

    balanced_candidate = _first_balanced_candidate(text)
    if balanced_candidate is not None:
        try:
            balanced = _parse_actual_object(balanced_candidate)
        except (json.JSONDecodeError, ValueError):
            balanced = None
    else:
        balanced = None
    if balanced is not None:
        results.append(RouteResult("first_balanced_object", True, None))
        return balanced, "first_balanced_object", balanced_candidate, results
    results.append(
        RouteResult("first_balanced_object", False, "balanced object absent")
    )
    return None, None, None, results


def _plain_error(stage: str, message: str) -> ValidationResult:
    return ValidationResult(
        stage=stage,
        ok=False,
        route=None,
        payload=None,
        parse_routes=[],
        schema_error=None,
        retry_error=message,
    )


def _validate_plan(payload: Mapping[str, Any]) -> None:
    if set(payload) != {"tool", "params"}:
        raise ValueError("plan fields must be exactly tool,params")
    if payload["tool"] != "calc" or isinstance(payload["tool"], bool):
        raise ValueError("plan tool must be enum calc")
    params = payload["params"]
    if not isinstance(params, dict) or set(params) != {"expression"}:
        raise ValueError("plan params must be exactly expression")
    expression = params["expression"]
    if not isinstance(expression, str) or not expression:
        raise ValueError("plan expression must be a non-empty string")
    if PLAN_EXPRESSION_PATTERN.fullmatch(expression) is None:
        raise ValueError(
            "plan expression violates decimal/operator character class "
            "[0-9+\\-*/(). ]"
        )


def _validate_decimal(payload: Mapping[str, Any], field: str) -> None:
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, (RawNumber, int, float)):
        raise ValueError(f"{field} must be a JSON number")
    lexical = (
        str(value)
        if isinstance(value, RawNumber)
        else format(value, ".15g")
        if isinstance(value, float)
        else str(value)
    )
    if DECIMAL_PATTERN.fullmatch(lexical) is None:
        raise ValueError(f"{field} violates decimal character class")
    try:
        parsed = Decimal(lexical)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not a decimal") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")


def _validate_consume(payload: Mapping[str, Any]) -> None:
    required = {"row", "periods", "delta_source", "delta_target", "unit"}
    if set(payload) != required:
        raise ValueError(
            "consume fields must be exactly row,periods,delta_source,"
            "delta_target,unit"
        )
    if not isinstance(payload["row"], str):
        raise ValueError("consume row must be a string")
    periods = payload["periods"]
    if (
        not isinstance(periods, list)
        or len(periods) != 2
        or any(not isinstance(period, str) for period in periods)
    ):
        raise ValueError("consume periods must be an array of exactly two strings")
    _validate_decimal(payload, "delta_source")
    _validate_decimal(payload, "delta_target")
    if not isinstance(payload["unit"], str):
        raise ValueError("consume unit must be a string")


def validate_schema(stage: str, payload: Mapping[str, Any]) -> None:
    if stage == "plan":
        _validate_plan(payload)
    elif stage == "consume":
        _validate_consume(payload)
    else:
        raise ValueError(f"unsupported stage: {stage}")


def validate_stage_response(stage: str, text: str) -> ValidationResult:
    if stage not in STAGES:
        return _plain_error(stage, f"unsupported stage: {stage}")
    payload, route, candidate, parse_routes = parse_three_routes(text)
    if payload is None:
        return ValidationResult(
            stage=stage,
            ok=False,
            route=None,
            payload=None,
            parse_routes=parse_routes,
            schema_error=None,
            retry_error=(
                "all JSON bridge parse routes failed: "
                + "; ".join(
                    f"{row.route}={row.error}" for row in parse_routes
                )
            ),
        )
    try:
        validation_payload = (
            _parse_raw_object(candidate) if candidate is not None else payload
        )
        validate_schema(stage, validation_payload)
    except ValueError as exc:
        return ValidationResult(
            stage=stage,
            ok=False,
            route=route,
            payload=payload,
            parse_routes=parse_routes,
            schema_error=str(exc),
            retry_error=str(exc),
        )
    return ValidationResult(
        stage=stage,
        ok=True,
        route=route,
        payload=payload,
        parse_routes=parse_routes,
        schema_error=None,
        retry_error=None,
    )


class StageRetryState:
    def __init__(self, max_retries: int = 1) -> None:
        if max_retries != 1:
            raise ValueError("the frozen bridge policy permits exactly one retry")
        self.max_retries = max_retries
        self.requests = 0
        self.retries = 0

    def count_request(self) -> int:
        self.requests += 1
        return self.requests

    def retry_prompt(self, task_prompt: str, result: ValidationResult) -> str:
        if result.ok:
            raise ValueError("a valid response does not consume a retry")
        if self.retries >= self.max_retries:
            raise ValueError("stage retry budget exhausted")
        if not result.retry_error:
            raise ValueError("retry feedback requires a concrete error")
        self.retries += 1
        return (
            f"{task_prompt}\n"
            "PREVIOUS_OUTPUT_ERROR="
            f"{result.retry_error}\n"
            "Return the corrected requested stage output now."
        )


def persist_failure(
    directory: Path,
    stage: str,
    raw_text: str,
    result: ValidationResult,
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    raw_bytes = raw_text.encode("utf-8")
    raw_path = directory / "raw_completion.txt"
    result_path = directory / "validation_result.json"
    raw_path.write_bytes(raw_bytes)
    record = result.to_record()
    record["raw_completion_sha256"] = sha256_bytes(raw_bytes)
    record["stage"] = stage
    result_path.write_bytes(canonical_bytes(record))
    return {
        "raw_completion_path": str(raw_path),
        "validation_result_path": str(result_path),
        "raw_completion_sha256": record["raw_completion_sha256"],
    }


if __name__ == "__main__":
    print(json.dumps(load_schema_document(), ensure_ascii=False, indent=2, sort_keys=True))
