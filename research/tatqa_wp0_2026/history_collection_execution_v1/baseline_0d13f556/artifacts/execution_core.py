#!/usr/bin/env python3
"""Deterministic core for the bounded history-collection execution package."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import operator
import os
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any


TASK_SELECT_SEED = "history-collection-execution-v1-task-select-20261018"
EXPECTED_CANDIDATE_RULE = (
    "value(late) - value(early) on row_index, both read from the table cells"
)
ALLOWED_PLAN_KEYS = {"tool", "params"}
ALLOWED_PLAN_PARAM_KEYS = {"expression"}
ALLOWED_CONSUME_KEYS = {"status", "delta_target", "unit"}
ALLOWED_TOOL_RESULT_KEYS = {
    "tool", "params", "returned_value", "status", "error", "request_id"
}
UNIT_TOKENS = (
    ("%", "%"),
    ("million", "million"),
    ("thousand", "thousand"),
    ("billion", "billion"),
    ("usd", "USD"),
    ("eur", "EUR"),
    ("gbp", "GBP"),
    ("rmb", "RMB"),
    ("cny", "CNY"),
)
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_lf(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def normalize_text(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).split())


def parse_numeric(value: Any) -> float | None:
    text = normalize_text(value).replace(",", "")
    text = re.sub(r"[−–—－]", "-", text)
    negative_parentheses = text.startswith("(") and text.endswith(")")
    if negative_parentheses:
        text = text[1:-1]
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    number = float(text)
    return -number if negative_parentheses and number > 0 else number


def evaluate_expression(expression: str) -> float:
    if not isinstance(expression, str):
        raise ValueError("expression_must_be_string")
    if not expression.strip() or len(expression) > 200:
        raise ValueError("expression_length_invalid")

    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("unsupported_constant")
            value = float(node.value)
            if not math.isfinite(value):
                raise ValueError("non_finite_constant")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return float(OPERATORS[type(node.op)](evaluate(node.operand)))
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            try:
                return float(
                    OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
                )
            except ArithmeticError as exc:
                raise ValueError("arithmetic_error") from exc
        raise ValueError("unsupported_expression_node")

    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise ValueError("expression_parse_error") from exc
    result = evaluate(tree)
    if not math.isfinite(result):
        raise ValueError("non_finite_result")
    return result


def _exact_keys(payload: Any, allowed: set[str], label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label}_must_be_object")
    keys = set(payload)
    if keys != allowed:
        missing = sorted(allowed - keys)
        unknown = sorted(keys - allowed)
        raise ValueError(f"{label}_keys_invalid missing={missing} unknown={unknown}")
    return payload


def strict_json_object(text: str, max_bytes: int = 65536) -> dict[str, Any]:
    if not isinstance(text, str):
        raise ValueError("model_content_must_be_string")
    raw = text.encode("utf-8")
    if len(raw) > max_bytes:
        raise ValueError("model_content_too_large")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model_json_invalid:{exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("model_json_must_be_object")
    return payload


def validate_plan_response(payload: Any) -> dict[str, Any]:
    payload = _exact_keys(payload, ALLOWED_PLAN_KEYS, "plan")
    params = _exact_keys(payload["params"], ALLOWED_PLAN_PARAM_KEYS, "plan_params")
    expression = params["expression"]
    if not isinstance(expression, str):
        raise ValueError("expression_must_be_string")
    evaluate_expression(expression)
    return {"tool": "calc", "params": {"expression": expression}}


def validate_consume_response(payload: Any) -> dict[str, Any]:
    payload = _exact_keys(payload, ALLOWED_CONSUME_KEYS, "consume")
    status = payload["status"]
    if status not in {"ANSWER", "UNKNOWN", "REFUSE"}:
        raise ValueError("consume_status_invalid")
    delta_target = payload["delta_target"]
    unit = payload["unit"]
    if status == "ANSWER":
        if isinstance(delta_target, bool) or not isinstance(delta_target, (int, float)):
            raise ValueError("answer_requires_numeric_delta_target")
        if not math.isfinite(float(delta_target)):
            raise ValueError("answer_delta_target_non_finite")
        if not isinstance(unit, str) or not unit.strip() or len(unit) > 64:
            raise ValueError("answer_requires_bounded_unit")
    elif delta_target is not None or unit is not None:
        raise ValueError("non_answer_must_use_explicit_nulls")
    return payload


def unit_tokens(label: Any) -> set[str]:
    text = normalize_text(label).lower()
    currency_code_scale = re.search(
        r"\b(usd|eur|gbp|rmb|cny)\s*(k|m|bn|b)(?![a-z0-9])", text
    )
    if currency_code_scale:
        scale = {"k": "thousand", "m": "million", "bn": "billion", "b": "billion"}[
            currency_code_scale.group(2)
        ]
        return {f"currency_{scale}"}
    currency_scale = re.search(r"[$¥£€]\s*(k|m|bn|b)(?![a-z0-9])", text)
    if currency_scale:
        scale = {"k": "thousand", "m": "million", "bn": "billion", "b": "billion"}[
            currency_scale.group(1)
        ]
        return {f"currency_{scale}"}
    if re.search(r"[$¥£€]", text):
        return {"currency"}
    found = set()
    for needle, normalized in UNIT_TOKENS:
        if re.search(rf"(?<![a-z0-9]){re.escape(needle)}s?(?![a-z0-9])", text):
            found.add(normalized)
    return found


def infer_unit(item: dict[str, Any]) -> tuple[str | None, str | None]:
    source_unit = item.get("source_unit")
    if isinstance(source_unit, str) and source_unit.strip():
        source_unit = normalize_text(source_unit)
        if len(source_unit) > 64:
            return None, "source_unit_too_long"
        return source_unit, None
    currency_change_units = set()
    for cell in item["table"][0]:
        header = normalize_text(cell).lower()
        if "change" not in header:
            continue
        tokens = unit_tokens(cell)
        currency_change_units.update(
            token for token in tokens
            if token == "currency" or token.startswith("currency_")
        )
    if len(currency_change_units) == 1:
        return next(iter(currency_change_units)), None
    period_tokens = unit_tokens(item["period_early"]["label"]) & unit_tokens(
        item["period_late"]["label"]
    )
    if len(period_tokens) == 1:
        return next(iter(period_tokens)), None
    primary_header = item["table"][0][0]
    primary_text = normalize_text(primary_header).lower()
    primary_tokens = unit_tokens(primary_header)
    if len(primary_tokens) == 1 and not any(
        marker in primary_text for marker in ("change", "margin", "ratio", "percent")
    ):
        return next(iter(primary_tokens)), None
    column_tokens: set[str] = set()
    for column in (item["period_early"]["col"], item["period_late"]["col"]):
        for row in item["table"][1:]:
            if column < len(row):
                column_tokens.update(unit_tokens(row[column]))
    if len(column_tokens) == 1:
        return next(iter(column_tokens)), None
    tokens: set[str] = set()
    for label in (
        item["period_early"]["label"],
        item["period_late"]["label"],
        *[str(cell) for cell in item["table"][0]],
    ):
        tokens.update(unit_tokens(label))
    if len(tokens) != 1:
        return None, "unit_not_unambiguous"
    return next(iter(tokens)), None


def validate_candidate_item(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"valid": False, "reason": "item_must_be_object"}
    required = {
        "item_id", "origin_id", "split", "table", "row_index",
        "period_late", "period_early", "source_unit", "requested_quantity",
        "gold_delta_source_unit", "gold_recompute_rule",
    }
    if set(item) != required:
        return {"valid": False, "reason": "candidate_item_keys_invalid"}
    if not isinstance(item["item_id"], str) or not item["item_id"] or len(item["item_id"]) > 128:
        return {"valid": False, "reason": "item_id_invalid"}
    if not isinstance(item["origin_id"], str) or not re.fullmatch(r"tatqa_[0-9a-f-]{36}", item["origin_id"]):
        return {"valid": False, "reason": "origin_id_invalid"}
    if not isinstance(item["table"], list) or not (2 <= len(item["table"]) <= 50):
        return {"valid": False, "reason": "table_bounds_invalid"}
    if any(not isinstance(row, list) or not (1 <= len(row) <= 20) for row in item["table"]):
        return {"valid": False, "reason": "table_row_invalid"}
    if not isinstance(item["row_index"], int) or isinstance(item["row_index"], bool):
        return {"valid": False, "reason": "row_index_invalid"}
    if not (1 <= item["row_index"] < len(item["table"])):
        return {"valid": False, "reason": "row_index_out_of_bounds"}
    for key in ("period_early", "period_late"):
        period = item[key]
        if not isinstance(period, dict) or set(period) != {"col", "label"}:
            return {"valid": False, "reason": f"{key}_shape_invalid"}
        if not isinstance(period["col"], int) or isinstance(period["col"], bool):
            return {"valid": False, "reason": f"{key}_col_invalid"}
        if not isinstance(period["label"], str) or not period["label"].strip() or len(period["label"]) > 128:
            return {"valid": False, "reason": f"{key}_label_invalid"}
    row = item["table"][item["row_index"]]
    if item["period_early"]["col"] == item["period_late"]["col"]:
        return {"valid": False, "reason": "period_columns_not_distinct"}
    for key in ("period_early", "period_late"):
        col = item[key]["col"]
        if not (0 <= col < len(row)) or parse_numeric(row[col]) is None:
            return {"valid": False, "reason": f"{key}_value_not_numeric"}
    if item["gold_recompute_rule"] != EXPECTED_CANDIDATE_RULE:
        return {"valid": False, "reason": "candidate_rule_not_frozen"}
    if parse_numeric(item["gold_delta_source_unit"]) is None:
        return {"valid": False, "reason": "candidate_gold_not_numeric"}
    unit, reason = infer_unit(item)
    if unit is None:
        return {"valid": False, "reason": reason}
    return {"valid": True, "unit": unit}


def independent_reference(item: dict[str, Any], unit: str) -> dict[str, Any]:
    row = item["table"][item["row_index"]]
    early_value = parse_numeric(row[item["period_early"]["col"]])
    late_value = parse_numeric(row[item["period_late"]["col"]])
    if early_value is None or late_value is None:
        return {"status": "REFERENCE_UNSCORABLE", "reason": "missing_numeric_cell"}
    delta_source = late_value - early_value
    candidate_gold = parse_numeric(item["gold_delta_source_unit"])
    agreement = (
        candidate_gold is not None
        and abs(delta_source - candidate_gold) <= 1e-9
    )
    return {
        "status": "REFERENCE_RECOMPUTED" if agreement else "REFERENCE_GOLD_MISMATCH",
        "delta_source": delta_source,
        "delta_target": delta_source,
        "source_unit": unit,
        "target_unit": unit,
        "scale_rule": "identity",
        "source_to_target_factor": 1.0,
        "candidate_gold_agreement": agreement,
    }


def actor_task(item: dict[str, Any], task_id: str, unit: str) -> dict[str, Any]:
    source_row = item["table"][item["row_index"]]
    row_label = normalize_text(source_row[0]) if source_row else ""
    if not row_label:
        raise ValueError("row_label_empty")
    early_col = item["period_early"]["col"]
    late_col = item["period_late"]["col"]
    header = ["row", item["period_early"]["label"], item["period_late"]["label"]]
    row = [row_label, str(source_row[early_col]), str(source_row[late_col])]
    return {
        "item_id": task_id,
        "task": {
            "row_label": row_label,
            "period_late": item["period_late"]["label"],
            "period_early": item["period_early"]["label"],
            "requested_quantity": "signed_difference",
            "source_unit": unit,
            "target_unit": unit,
            "scale_rule": "identity",
        },
        "evidence": {
            "table_projection": [header, row],
        },
    }


def selection_rank(bucket: str, cluster_id: str, item_id: str) -> str:
    return hashlib.sha256(
        f"{TASK_SELECT_SEED}:{bucket}:{cluster_id}:{item_id}".encode("utf-8")
    ).hexdigest()


def source_uid(item: dict[str, Any]) -> str:
    return item["origin_id"].removeprefix("tatqa_")


class ExecutionBudget:
    def __init__(self, request_cap: int, token_cap: int, per_request_reserve: int):
        if request_cap <= 0 or token_cap <= 0 or per_request_reserve <= 0:
            raise ValueError("budget_bounds_invalid")
        if request_cap * per_request_reserve > token_cap:
            raise ValueError("budget_worst_case_exceeds_token_cap")
        self.request_cap = request_cap
        self.token_cap = token_cap
        self.per_request_reserve = per_request_reserve
        self.requests = 0
        self.reserved_tokens = 0
        self.actual_tokens = 0
        self.stop_reason = None

    def reserve(self) -> str:
        if self.stop_reason:
            raise RuntimeError(self.stop_reason)
        if self.requests + 1 > self.request_cap:
            self.stop_reason = "REQUEST_CAP_REACHED"
            raise RuntimeError(self.stop_reason)
        if self.reserved_tokens + self.per_request_reserve > self.token_cap:
            self.stop_reason = "TOKEN_CAP_REACHED"
            raise RuntimeError(self.stop_reason)
        reservation_id = f"res_{uuid.uuid4().hex}"
        self.requests += 1
        self.reserved_tokens += self.per_request_reserve
        return reservation_id

    def settle(self, reservation_id: str, actual_tokens: int) -> None:
        if not isinstance(reservation_id, str) or not reservation_id.startswith("res_"):
            raise ValueError("reservation_id_invalid")
        if isinstance(actual_tokens, bool) or not isinstance(actual_tokens, int) or actual_tokens < 0:
            raise ValueError("actual_tokens_invalid")
        if actual_tokens > self.per_request_reserve:
            self.stop_reason = "ACTUAL_TOKENS_EXCEED_RESERVATION"
            raise RuntimeError(self.stop_reason)
        self.reserved_tokens -= self.per_request_reserve
        self.actual_tokens += actual_tokens

    def snapshot(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "reserved_tokens": self.reserved_tokens,
            "actual_tokens": self.actual_tokens,
            "request_cap": self.request_cap,
            "token_cap": self.token_cap,
            "per_request_reserve": self.per_request_reserve,
            "stop_reason": self.stop_reason,
        }


class ImmutableRawStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def begin_request(self, logical_id: str, request_payload: dict[str, Any]) -> str:
        if not isinstance(logical_id, str) or not re.fullmatch(r"[A-Za-z0-9_.|-]{1,128}", logical_id):
            raise ValueError("logical_id_invalid")
        safe_logical_id = re.sub(r"[^A-Za-z0-9_.-]", "_", logical_id)
        request_id = f"{safe_logical_id}_{uuid.uuid4().hex[:12]}"
        request_dir = self.root / request_id
        request_dir.mkdir(parents=False, exist_ok=False)
        payload = {"request_id": request_id, "logical_id": logical_id, "request": request_payload}
        self._write_exclusive_json(request_dir / "request.json", payload)
        return request_id

    def persist_response(self, request_id: str, response: dict[str, Any]) -> None:
        request_dir = self._request_dir(request_id)
        if (request_dir / "CRASH").exists():
            raise RuntimeError("terminal_crash_state")
        if (request_dir / "COMPLETE").exists():
            raise FileExistsError("complete_marker_overwrite_prohibited")
        if (request_dir / "response.json").exists():
            raise FileExistsError("response_overwrite_prohibited")
        request_path = request_dir / "request.json"
        if not request_path.exists():
            raise FileNotFoundError("request_identity_missing")
        request_identity = json.loads(request_path.read_text(encoding="utf-8"))
        if request_identity.get("request_id") != request_id:
            raise RuntimeError("request_response_identity_mismatch")
        self._write_exclusive_json(
            request_dir / "response.json",
            {"request_id": request_id, "response": response},
        )
        self._write_exclusive_json(request_dir / "COMPLETE", {"request_id": request_id})

    def mark_crash(self, request_id: str, reason: str) -> None:
        request_dir = self._request_dir(request_id)
        if (request_dir / "COMPLETE").exists():
            raise RuntimeError("complete_request_cannot_crash")
        if (request_dir / "CRASH").exists():
            raise FileExistsError("crash_marker_overwrite_prohibited")
        if not (request_dir / "request.json").exists():
            raise FileNotFoundError("request_identity_missing")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 256:
            raise ValueError("crash_reason_invalid")
        self._write_exclusive_json(request_dir / "CRASH", {"request_id": request_id, "reason": reason})

    def _request_dir(self, request_id: str) -> Path:
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_.|-]{1,160}", request_id):
            raise ValueError("request_id_invalid")
        request_dir = self.root / request_id
        if request_dir.parent.resolve() != self.root.resolve():
            raise ValueError("request_path_traversal")
        if not request_dir.exists():
            raise FileNotFoundError("request_identity_missing")
        return request_dir

    @staticmethod
    def _write_exclusive_json(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_name(path.name + f".tmp.{uuid.uuid4().hex}")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()


def synthetic_fixture_tasks() -> list[dict[str, Any]]:
    rows = [
        {
            "item_id": "fixture-percent",
            "table": [["row", "2020 %", "2022 %"], ["rate", "10", "14"]],
            "row_index": 1,
            "period_early": {"col": 1, "label": "2020 %"},
            "period_late": {"col": 2, "label": "2022 %"},
            "source_unit": None,
            "gold_delta_source_unit": 4,
            "gold_recompute_rule": EXPECTED_CANDIDATE_RULE,
        },
        {
            "item_id": "fixture-million",
            "table": [["row", "2018 million", "2021 million"], ["amount", "7.5", "6.25"]],
            "row_index": 1,
            "period_early": {"col": 1, "label": "2018 million"},
            "period_late": {"col": 2, "label": "2021 million"},
            "source_unit": None,
            "gold_delta_source_unit": -1.25,
            "gold_recompute_rule": EXPECTED_CANDIDATE_RULE,
        },
        {
            "item_id": "fixture-accounting",
            "table": [["row", "2019 $", "2020 $"], ["net", "(3)", "(5)"]],
            "row_index": 1,
            "period_early": {"col": 1, "label": "2019 $"},
            "period_late": {"col": 2, "label": "2020 $"},
            "source_unit": "currency",
            "gold_delta_source_unit": -2,
            "gold_recompute_rule": EXPECTED_CANDIDATE_RULE,
        },
    ]
    output = []
    for index, item in enumerate(rows, start=1):
        unit, reason = infer_unit(item)
        if unit is None:
            raise ValueError(reason)
        reference = independent_reference(item, unit)
        output.append({
            "task_id": f"X{index:02d}",
            "bucket": "qualification_fixture",
            "actor_task": actor_task(item, f"X{index:02d}", unit),
            "hidden": {
                "fixture_source": item,
                "reference": reference,
            },
        })
    return output
