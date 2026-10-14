#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[3]
WP1_DIR = ROOT / "research/tatqa_wp0_2026/wp1"
WP2_DIR = ROOT / "research/tatqa_wp0_2026/wp2"
sys.path.insert(0, str(WP1_DIR))

import checker_v2  # noqa: E402
from adapter import ContextHook, build_prompt  # noqa: E402


TASK = "tatqa-wp2-s4b-20261014"
MODEL_ID = "tatqa-wp2-qwen3-8b-b968826d"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
SERVICE_URL = "http://127.0.0.1:8112/v1/completions"
HEALTH_URL = "http://127.0.0.1:8112/health"
PRIOR_CARD_ATTEMPTS = 1
CARD_REMAINING_ATTEMPTS = 39
MAX_TRANSPORT_RETRIES = 4
MAX_INPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 512
TEMPERATURE = 0
EXPERIENCE_CAP = 600
BRIDGE_RECEIPT_PATH = WP2_DIR / "S4B_BRIDGE_PROTOCOL_RECEIPT.json"
S_RULES = """1. Read the exact requested row from the complete evidence table.
2. Subtract the early-period cell from the late-period cell.
3. Use calc exactly once for that subtraction.
4. Report periods in [late, early] order.
5. Treat an absent source unit as unit; percent remains percent.
6. Keep thousand, million, and billion identity-only.
7. Output the requested target unit exactly as supplied in evidence.
8. Never invent a hidden recomputation or use an unexecuted correction."""
PLAN_PROTOCOL = """\nSTAGE=plan
Return exactly one JSON object and no other text:
{"tool":"calc","params":{"expression":"<LEFT_NUMBER> <PLUS_OR_MINUS> <RIGHT_NUMBER>"}}
Use the two exact numeric evidence cells for LEFT_NUMBER and RIGHT_NUMBER.
Do not provide the final answer in this stage.
FORMAT_EXAMPLE={"tool":"calc","params":{"expression":"12 - 4"}}
"""
CONSUME_PROTOCOL = """\nSTAGE=consume
Use the supplied tool trace and the evidence.
Return exactly one JSON object and no other text:
{"row":"<exact row label>","periods":["<late label>","<early label>"],"delta_source":"<calc result>","delta_target":"<converted calc result>","unit":"<target unit>"}
FORMAT_EXAMPLE={"row":"Revenue","periods":["2019","2018"],"delta_source":8,"delta_target":8,"unit":"unit"}
"""
PROMPT_VERSION = {
    "schema": "tatqa_wp2_bridge_prompt_v1",
    "format_examples": 1,
    "settings_unchanged": True,
    "temperature": TEMPERATURE,
    "max_output_tokens": MAX_OUTPUT_TOKENS,
    "input_token_cap": MAX_INPUT_TOKENS,
    "experience_cap": EXPERIENCE_CAP,
    "automatic_third_round_repair": False,
    "parser_order": ["strict_json", "code_fenced_json", "first_balanced_object"],
    "plan_protocol": PLAN_PROTOCOL,
    "consume_protocol": CONSUME_PROTOCOL,
}
NUMERIC_PATTERN = (
    r"-?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
)
EXPRESSION_PATTERN = re.compile(
    rf"^\s*\(?({NUMERIC_PATTERN})\)?\s*([-+])\s*\(?({NUMERIC_PATTERN})\)?\s*$"
)
FENCED_JSON_PATTERN = re.compile(
    r"\A```(?:json)?[ \t]*\r?\n(?P<body>.*?)\r?\n```[ \t]*\Z",
    re.DOTALL | re.IGNORECASE,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(canonical_bytes(payload))
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    temporary.replace(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def opaque_id(prefix: str, internal_id: str) -> str:
    digest = hashlib.sha256(
        f"tatqa-wp2-opaque-v2:{prefix}:{internal_id}".encode("utf-8")
    ).hexdigest()
    return f"{prefix}_{digest[:12]}"


def json_decimal(value: Decimal) -> str | int | float:
    if value == value.to_integral_value():
        return int(value)
    normalized = value.normalize()
    return format(normalized, "f")


def _first_balanced_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
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
                    try:
                        parsed, consumed = decoder.raw_decode(candidate)
                    except json.JSONDecodeError:
                        break
                    if consumed == len(candidate) and isinstance(parsed, dict):
                        return parsed
                    break
    return None


def extract_json(text: str) -> tuple[dict[str, Any], str]:
    if not isinstance(text, str):
        raise ValueError("completion text must be a string")
    strict_candidate = text.strip()
    strict_error = None
    try:
        parsed = json.loads(strict_candidate)
    except json.JSONDecodeError as exc:
        strict_error = f"{type(exc).__name__}: {exc}"
    else:
        if not isinstance(parsed, dict):
            raise ValueError("strict JSON response must be an object")
        return parsed, "strict_json"

    fenced_match = FENCED_JSON_PATTERN.fullmatch(strict_candidate)
    if fenced_match is not None:
        try:
            parsed = json.loads(fenced_match.group("body").strip())
        except json.JSONDecodeError:
            pass
        else:
            if not isinstance(parsed, dict):
                raise ValueError("fenced JSON response must be an object")
            return parsed, "code_fenced_json"

    balanced = _first_balanced_object(text)
    if balanced is not None:
        return balanced, "first_balanced_object"
    raise ValueError(
        "all JSON bridge parse routes failed: "
        f"strict={strict_error}; fenced=unavailable_or_invalid; "
        "balanced_object=absent"
    )


def canonical_decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{field} must be numeric")
    text = str(value).strip()
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not a decimal") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def execute_calc(params: Mapping[str, Any]) -> tuple[str, Decimal]:
    if set(params) != {"expression"}:
        raise ValueError("calc params must contain only expression")
    expression = params["expression"]
    if not isinstance(expression, str):
        raise ValueError("calc expression must be a string")
    match = EXPRESSION_PATTERN.fullmatch(expression)
    if match is None:
        raise ValueError("calc expression must be one decimal subtraction/addition")
    left = Decimal(match.group(1).replace(",", ""))
    operator = match.group(2)
    right = Decimal(match.group(3).replace(",", ""))
    result = left - right if operator == "-" else left + right
    return expression, result


def render_actor_prompt(prompt: str, tokenizer: Any) -> str:
    return str(
        tokenizer.apply_chat_template(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a precise table-calculation agent. "
                        "Follow the user's frozen tool protocol and return "
                        "only the requested stage output."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
    )


class PersistFirstLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.payload = (
            load_json(path)
            if path.exists()
            else {
                "schema": "tatqa_wp2_actor_call_ledger_v2",
                "task": TASK,
                "persist_first": True,
                "prior_card_attempts": PRIOR_CARD_ATTEMPTS,
                "budget": {
                    "global_hard_cap": 300,
                    "prior_card_attempts": PRIOR_CARD_ATTEMPTS,
                    "this_card_remaining_at_start": CARD_REMAINING_ATTEMPTS,
                    "max_transport_retries_per_logical_request": (
                        MAX_TRANSPORT_RETRIES
                    ),
                    "judge_calls": 0,
                },
                "attempts": [],
                "stages": {},
            }
        )
        require(
            self.payload.get("schema") == "tatqa_wp2_actor_call_ledger_v2",
            "incompatible ledger schema",
        )
        require(self.payload.get("task") == TASK, "ledger task mismatch")

    def save(self) -> None:
        self.payload["updated_at_utc"] = utc_now()
        self.payload["accounting"] = {
            "prior_card_attempts": PRIOR_CARD_ATTEMPTS,
            "current_card_attempts": len(self.payload["attempts"]),
            "global_attempts_used": (
                PRIOR_CARD_ATTEMPTS + len(self.payload["attempts"])
            ),
            "global_attempts_remaining": (
                300 - PRIOR_CARD_ATTEMPTS - len(self.payload["attempts"])
            ),
            "this_card_attempts_remaining": (
                CARD_REMAINING_ATTEMPTS - len(self.payload["attempts"])
            ),
            "transport_retries": sum(
                int(row.get("transport_retries", 0))
                for row in self.payload["attempts"]
            ),
            "judge_calls": 0,
        }
        write_json(self.path, self.payload)

    def persist(self, record: Mapping[str, Any]) -> None:
        self.payload["attempts"].append(dict(record))
        self.save()

    def update(self, runner_request_id: str, fields: Mapping[str, Any]) -> None:
        matches = [
            row
            for row in self.payload["attempts"]
            if row["runner_request_id"] == runner_request_id
        ]
        require(len(matches) == 1, "attempt update target is not unique")
        matches[0].update(dict(fields))
        self.save()


class BridgeFailure(RuntimeError):
    pass


def actor_request(
    prompt: str,
    tokenizer: Any,
    ledger: PersistFirstLedger,
    logical_request_id: str,
    purpose: str,
    stage: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rendered_prompt = render_actor_prompt(prompt, tokenizer)
    prompt_bytes = rendered_prompt.encode("utf-8")
    prompt_sha256 = sha256_bytes(prompt_bytes)
    prompt_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))
    require(
        prompt_tokens <= MAX_INPUT_TOKENS,
        f"prompt exceeds frozen input cap: {prompt_tokens} tokens",
    )
    payload = {
        "model": MODEL_ID,
        "prompt": prompt,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": TEMPERATURE,
        "n": 1,
        "echo": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    transport_retries = 0
    while True:
        sequence = (
            sum(
                row.get("logical_request_id") == logical_request_id
                for row in ledger.payload["attempts"]
            )
            + 1
        )
        runner_request_id = f"{logical_request_id}-{sequence}"
        attempt_dir = ledger.path.parent / "attempts" / runner_request_id
        attempt_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = attempt_dir / "prompt.txt"
        prompt_path.write_bytes(prompt_bytes)
        started = time.monotonic()
        record: dict[str, Any] = {
            "runner_request_id": runner_request_id,
            "logical_request_id": logical_request_id,
            "purpose": purpose,
            "stage": stage,
            "prompt_sha256": prompt_sha256,
            "prompt_tokens": prompt_tokens,
            "counted_attempt": True,
            "transport_retries": transport_retries,
            "started_at_utc": utc_now(),
            "http_status": None,
            "actor_request_id": None,
            "completion_tokens": None,
            "elapsed_seconds": None,
            "raw_response_path": None,
            "raw_response_sha256": None,
            "response_envelope_parse": "not_started",
            "completion_parse": "not_started",
            "exit": "in_progress",
        }
        ledger.persist(record)
        try:
            request = urllib.request.Request(
                SERVICE_URL,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=300) as response:
                http_status = int(response.status)
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw_response = exc.read().decode("utf-8", errors="replace")
            raw_path = attempt_dir / "raw_response.txt"
            raw_path.write_text(raw_response, encoding="utf-8", newline="\n")
            record.update(
                {
                    "http_status": int(exc.code),
                    "elapsed_seconds": time.monotonic() - started,
                    "raw_response_path": str(raw_path.relative_to(ROOT)),
                    "raw_response_sha256": sha256_bytes(
                        raw_response.encode("utf-8")
                    ),
                    "response_envelope_parse": "not_attempted_http_error",
                    "completion_parse": "not_attempted_http_error",
                    "exit": "http_error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            ledger.update(runner_request_id, record)
            raise RuntimeError(
                f"actor HTTP error {exc.code}: {raw_response[:500]}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            record.update(
                {
                    "elapsed_seconds": time.monotonic() - started,
                    "response_envelope_parse": "not_attempted_transport_error",
                    "completion_parse": "not_attempted_transport_error",
                    "exit": "transport_error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            ledger.update(runner_request_id, record)
            transport_retries += 1
            require(
                transport_retries <= MAX_TRANSPORT_RETRIES,
                "transport retry cap exceeded",
            )
            time.sleep(min(2**transport_retries, 8))
            continue

        elapsed = time.monotonic() - started
        raw_path = attempt_dir / "raw_response.txt"
        raw_path.write_text(raw_response, encoding="utf-8", newline="\n")
        record.update(
            {
                "http_status": http_status,
                "elapsed_seconds": elapsed,
                "raw_response_path": str(raw_path.relative_to(ROOT)),
                "raw_response_sha256": sha256_bytes(
                    raw_response.encode("utf-8")
                ),
                "response_envelope_parse": "persisted_before_parse",
            }
        )
        ledger.update(runner_request_id, record)

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            record.update(
                {
                    "response_envelope_parse": "failed",
                    "exit": "response_envelope_parse_failure",
                    "parse_error": f"{type(exc).__name__}: {exc}",
                }
            )
            ledger.update(runner_request_id, record)
            raise BridgeFailure(
                f"actor response envelope is not JSON: {raw_response[:500]}"
            ) from exc
        require(
            isinstance(parsed, dict),
            "actor response envelope must be an object",
        )
        record["response_envelope_parse"] = "strict_json_ok"
        try:
            require(
                parsed.get("model") == MODEL_ID,
                "actor response model mismatch",
            )
            usage = parsed["usage"]
            choices = parsed["choices"]
            require(isinstance(choices, list) and len(choices) == 1, "choices")
            completion_text = choices[0]["text"]
            require(isinstance(completion_text, str), "completion text")
            record.update(
                {
                    "actor_request_id": parsed.get("id"),
                    "completion_tokens": int(usage["completion_tokens"]),
                    "response_envelope_parse": "strict_json_ok",
                    "completion_parse": "persisted_after_response_parse",
                }
            )
            completion_path = attempt_dir / "completion.txt"
            completion_path.write_text(
                completion_text,
                encoding="utf-8",
                newline="\n",
            )
            record["completion_path"] = str(completion_path.relative_to(ROOT))
            record["completion_sha256"] = sha256_bytes(
                completion_text.encode("utf-8")
            )
            require(
                int(usage["prompt_tokens"]) <= MAX_INPUT_TOKENS,
                "actor service returned over-cap input token count",
            )
            require(
                int(usage["prompt_tokens"]) == prompt_tokens,
                "actor service prompt-token mismatch",
            )
            record["exit"] = "success"
            ledger.update(runner_request_id, record)
        except Exception as exc:
            record.update(
                {
                    "completion_parse": "failed",
                    "exit": "response_envelope_validation_failure",
                    "parse_error": f"{type(exc).__name__}: {exc}",
                }
            )
            ledger.update(runner_request_id, record)
            raise
        parsed["_completion_text"] = completion_text
        parsed["_attempt_record"] = record
        return parsed, record


def parse_actor_payload(
    response: Mapping[str, Any],
    ledger: PersistFirstLedger,
    purpose: str,
) -> tuple[dict[str, Any], str]:
    completion_text = str(response["_completion_text"])
    record = dict(response["_attempt_record"])
    attempt_dir = ledger.path.parent / "attempts" / record["runner_request_id"]
    try:
        parsed, route = extract_json(completion_text)
    except ValueError as exc:
        record.update(
            {
                "completion_parse": "failed_all_bridge_routes",
                "exit": "bridge_parse_failure",
                "parse_error": f"{type(exc).__name__}: {exc}",
            }
        )
        ledger.update(record["runner_request_id"], record)
        raise BridgeFailure(
            f"{purpose} bridge parse failed after persisting raw response: {exc}"
        ) from exc
    parsed_path = attempt_dir / "parsed_payload.json"
    write_json(parsed_path, parsed)
    record.update(
        {
            "completion_parse": "ok",
            "bridge_parse_route": route,
            "parsed_payload_path": str(parsed_path.relative_to(ROOT)),
            "parse_result": "PASS",
        }
    )
    ledger.update(record["runner_request_id"], record)
    return parsed, route


def stage_items(split: Mapping[str, Any], role: str) -> list[Mapping[str, Any]]:
    items_payload = load_json(
        ROOT / "data/research/tatqa_wp0_2026/candidate_items_v2.json"
    )
    origins = set(split["roles"][role])
    items = [
        item
        for item in items_payload["items"]
        if item["origin_id"] in origins
    ]
    items.sort(key=lambda item: str(item["item_id"]))
    expected_origins = 4 if role == "history" else 2
    expected_items = 8 if role == "history" else 4
    require(
        len({item["origin_id"] for item in items}) == expected_origins,
        "stage origin count mismatch",
    )
    require(len(items) == expected_items, "stage item count mismatch")
    return items


def run_episode(
    item: Mapping[str, Any],
    stage: str,
    arm: str,
    rules_text: str,
    tokenizer: Any,
    ledger: PersistFirstLedger,
    item_index: int,
) -> dict[str, Any]:
    hook_type = "none" if arm == "B" else "static_rules"
    hook = ContextHook(arm=arm, hook_type=hook_type, text=rules_text)
    base_prompt = build_prompt(item, hook)
    item_id = str(item["item_id"])
    logical_plan_id = f"{stage}-{item_index + 1:02d}-{item_id}-plan"
    plan_response, _ = actor_request(
        base_prompt + PLAN_PROTOCOL,
        tokenizer,
        ledger,
        logical_plan_id,
        "plan",
        stage,
    )
    plan, plan_route = parse_actor_payload(plan_response, ledger, "plan")
    require(
        set(plan) == {"tool", "params"},
        "plan fields outside frozen bridge schema",
    )
    require(plan.get("tool") == "calc", "plan tool must be calc")
    expression, calc_result = execute_calc(plan["params"])
    consume_prompt = (
        base_prompt
        + CONSUME_PROTOCOL
        + "PREVIOUS_PLAN="
        + json.dumps(plan, ensure_ascii=False, sort_keys=True)
        + "\nTOOL_RESULT="
        + json.dumps(
            {
                "tool": "calc",
                "params": {"expression": expression},
                "returned_value": json_decimal(calc_result),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    )
    logical_consume_id = (
        f"{stage}-{item_index + 1:02d}-{item_id}-consume"
    )
    consume_response, _ = actor_request(
        consume_prompt,
        tokenizer,
        ledger,
        logical_consume_id,
        "consume",
        stage,
    )
    answer, consume_route = parse_actor_payload(
        consume_response,
        ledger,
        "consume",
    )
    required = {"row", "periods", "delta_source", "delta_target", "unit"}
    require(
        set(answer) == required,
        "final answer has fields outside the frozen format",
    )
    answer["delta_source"] = json_decimal(
        canonical_decimal(answer["delta_source"], "delta_source"),
        "delta_source",
    )
    answer["delta_target"] = json_decimal(
        canonical_decimal(answer["delta_target"], "delta_target"),
        "delta_target",
    )
    answer_text = json.dumps(answer, ensure_ascii=False, sort_keys=True)
    verdict = checker_v2.score_item(item, answer_text)
    origin_id = str(item["origin_id"])
    projection = {
        "row": item["table"][item["row_index"]][0],
        "periods": [
            item["period_late"]["label"],
            item["period_early"]["label"],
        ],
        "delta_source": answer["delta_source"],
        "delta_target": answer["delta_target"],
        "unit": answer["unit"],
    }
    tool_trace = {
        "params": {"expression": expression},
        "returned_value": json_decimal(calc_result),
        "trace_ref": opaque_id("trace", item_id),
    }
    episode: dict[str, Any] = {
        "episode_id": opaque_id("episode", item_id),
        "origin_ref": opaque_id("origin", origin_id),
        "arm_role": "history" if arm == "B" else "development",
        "stage": stage,
        "arm": arm,
        "repeat": 1,
        "task": {
            "period_late": item["period_late"]["label"],
            "period_early": item["period_early"]["label"],
            "requested_quantity": item["requested_quantity"],
            "target_unit": item.get("target_unit")
            or item.get("source_unit")
            or "unit",
        },
        "tool_trace": tool_trace,
        "answer": projection,
        "verdict": {
            "class": verdict["outcome"],
            "source": "checker",
            "checker_version_hash": sha256_file(
                WP1_DIR / "checker_v2.py"
            ),
        },
        "correction": {
            "executed": False,
            "steps": [],
            "execution_ref": None,
        },
        "licence_note": (
            "The drift-v0 injection map and any task projection are "
            "*derivatives*; the artifact must state that the tables are "
            "derived from TAT-QA and that perturbations were added by "
            "this project."
        ),
        "bridge": {
            "plan_route": plan_route,
            "consume_route": consume_route,
            "plan_attempt_ref": plan_response["_attempt_record"][
                "runner_request_id"
            ],
            "consume_attempt_ref": consume_response["_attempt_record"][
                "runner_request_id"
            ],
        },
    }
    episode["sha256"] = sha256_bytes(canonical_bytes(episode))
    return episode


def probe_bridge(
    tokenizer: Any,
    ledger: PersistFirstLedger,
    output: Path,
    item_index: int,
) -> int:
    split = load_json(WP2_DIR / "SPLIT_RERUN_RECEIPT.json")
    items = stage_items(split, "history")
    item = items[item_index]
    hook = ContextHook(arm="B", hook_type="none", text="")
    base_prompt = build_prompt(item, hook)
    logical_plan_id = f"S4B-probe-history-{item_index + 1:02d}-plan"
    plan_response, _ = actor_request(
        base_prompt + PLAN_PROTOCOL,
        tokenizer,
        ledger,
        logical_plan_id,
        "probe_plan",
        "S4B_bridge_probe",
    )
    plan, plan_route = parse_actor_payload(
        plan_response,
        ledger,
        "probe_plan",
    )
    require(set(plan) == {"tool", "params"}, "probe plan schema")
    require(plan.get("tool") == "calc", "probe plan tool")
    expression, calc_result = execute_calc(plan["params"])
    consume_prompt = (
        base_prompt
        + CONSUME_PROTOCOL
        + "PREVIOUS_PLAN="
        + json.dumps(plan, ensure_ascii=False, sort_keys=True)
        + "\nTOOL_RESULT="
        + json.dumps(
            {
                "tool": "calc",
                "params": {"expression": expression},
                "returned_value": json_decimal(calc_result),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    )
    logical_consume_id = (
        f"S4B-probe-history-{item_index + 1:02d}-consume"
    )
    consume_response, _ = actor_request(
        consume_prompt,
        tokenizer,
        ledger,
        logical_consume_id,
        "probe_consume",
        "S4B_bridge_probe",
    )
    answer, consume_route = parse_actor_payload(
        consume_response,
        ledger,
        "probe_consume",
    )
    receipt = {
        "schema": "tatqa_wp2_s4b_bridge_probe_receipt_v1",
        "task": TASK,
        "status": "PASS",
        "generated_at_utc": utc_now(),
        "stage": "S4B_bridge_probe",
        "history_item_index": item_index,
        "history_origin_ref": opaque_id("origin", str(item["origin_id"])),
        "history_item_ref": opaque_id("item", str(item["item_id"])),
        "prompt_version_sha256": sha256_bytes(canonical_bytes(PROMPT_VERSION)),
        "prompt_version": PROMPT_VERSION,
        "plan": {
            "route": plan_route,
            "parsed": plan,
            "attempt_ref": plan_response["_attempt_record"][
                "runner_request_id"
            ],
            "raw_response_sha256": plan_response["_attempt_record"][
                "raw_response_sha256"
            ],
            "completion_sha256": plan_response["_attempt_record"][
                "completion_sha256"
            ],
        },
        "consume": {
            "route": consume_route,
            "parsed": answer,
            "attempt_ref": consume_response["_attempt_record"][
                "runner_request_id"
            ],
            "raw_response_sha256": consume_response["_attempt_record"][
                "raw_response_sha256"
            ],
            "completion_sha256": consume_response["_attempt_record"][
                "completion_sha256"
            ],
        },
        "accounting": {
            "probe_actor_requests": 2,
            "global_actor_requests_used_after_probe": (
                PRIOR_CARD_ATTEMPTS + len(ledger.payload["attempts"])
            ),
            "judge_calls": 0,
        },
        "safety": {
            "external_network_calls": 0,
            "judge_calls": 0,
            "database_calls": 0,
            "production_service_calls": 0,
            "training_calls": 0,
            "memory_write_back": False,
        },
    }
    write_json(output, receipt)
    print(
        f"BRIDGE_PROBE_PASS plan_route={plan_route} "
        f"consume_route={consume_route} output_sha256={sha256_file(output)}",
        flush=True,
    )
    return 0


def collect_stage(
    args: argparse.Namespace,
    tokenizer: Any,
    ledger: PersistFirstLedger,
) -> int:
    require(BRIDGE_RECEIPT_PATH.exists(), "bridge protocol receipt missing")
    bridge_receipt = load_json(BRIDGE_RECEIPT_PATH)
    require(
        bridge_receipt.get("status") == "PASS",
        "bridge protocol receipt is not PASS",
    )
    require(
        bridge_receipt["software"]["runner_v2"]["sha256"]
        == sha256_file(Path(__file__)),
        "bridge receipt runner hash mismatch",
    )
    split = load_json(WP2_DIR / "SPLIT_RERUN_RECEIPT.json")
    role = "history" if args.stage == "history" else "development"
    items = stage_items(split, role)
    planned_requests = 2 * len(items)
    require(
        len(ledger.payload["attempts"]) + planned_requests
        <= CARD_REMAINING_ATTEMPTS,
        "this-card attempt cap would be exceeded",
    )
    stage_name = "S4_history" if role == "history" else "S5_development"
    arm = "B" if role == "history" else "S"
    episodes: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(items):
            episodes.append(
                run_episode(
                    item,
                    stage_name,
                    arm,
                    "" if arm == "B" else S_RULES,
                    tokenizer,
                    ledger,
                    index,
                )
            )
            ledger.payload["stages"][stage_name] = {
                "completed_episodes": len(episodes),
                "requested_episodes": len(items),
                "actor_requests": 2 * len(episodes),
                "cumulative_actor_requests": len(ledger.payload["attempts"]),
            }
            ledger.save()
            print(
                f"EPISODE_COLLECTED stage={stage_name} "
                f"index={index + 1}/{len(items)} "
                f"attempts={len(ledger.payload['attempts'])}",
                flush=True,
            )
    except Exception as exc:
        failure_path = args.failure_output or args.output.with_name(
            f"{args.output.stem}_FAILED.json"
        )
        write_json(
            failure_path,
            {
                "schema": "tatqa_wp2_s4b_stage_failure_receipt_v1",
                "task": TASK,
                "status": "STOP_THIS_PANEL"
                if isinstance(exc, BridgeFailure)
                else "ENGINEERING_FAILURE",
                "generated_at_utc": utc_now(),
                "stage": stage_name,
                "completed_episodes": len(episodes),
                "failure": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "same_family_repeat_rule": (
                        "A second same-family bridge failure ends this panel."
                    ),
                },
                "accounting": ledger.payload.get("accounting", {}),
            },
        )
        raise
    receipt = {
        "schema": "tatqa_wp2_episode_collection_receipt_v2",
        "task": TASK,
        "status": "PASS",
        "stage": stage_name,
        "generated_at_utc": utc_now(),
        "role": role,
        "arm": arm,
        "persist_first": True,
        "counts": {
            "origins": len(
                {str(item["origin_id"]) for item in items}
            ),
            "episodes": len(episodes),
            "actor_request_attempts_this_stage": 2 * len(episodes),
        },
        "settings": {
            "temperature": TEMPERATURE,
            "single_shot": True,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "input_token_cap": MAX_INPUT_TOKENS,
            "experience_block_cap": EXPERIENCE_CAP,
            "automatic_third_round_repair": False,
        },
        "service": {
            "url": SERVICE_URL,
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "startup_receipt": str(
                Path(
                    "/tmp/tatqa-wp2-actor-20261014/"
                    "STARTUP_RECEIPT.json"
                )
            ),
            "startup_command": str(
                Path(
                    "/tmp/tatqa-wp2-actor-20261014/"
                    "start_transformers_command.txt"
                )
            ),
        },
        "episodes": episodes,
        "accounting": {
            "actor_request_attempts_this_stage": 2 * len(episodes),
            "prior_card_attempts": PRIOR_CARD_ATTEMPTS,
            "current_card_attempts": len(ledger.payload["attempts"]),
            "global_actor_request_attempts_used": (
                PRIOR_CARD_ATTEMPTS + len(ledger.payload["attempts"])
            ),
            "global_actor_request_attempts_remaining": (
                300 - PRIOR_CARD_ATTEMPTS - len(ledger.payload["attempts"])
            ),
            "transport_retries": sum(
                int(row.get("transport_retries", 0))
                for row in ledger.payload["attempts"]
            ),
            "judge_calls": 0,
        },
        "software": {
            "runner_v2": {
                "path": str(Path(__file__).relative_to(ROOT)),
                "sha256": sha256_file(Path(__file__)),
            },
            "adapter": {
                "path": str((WP1_DIR / "adapter.py").relative_to(ROOT)),
                "sha256": sha256_file(WP1_DIR / "adapter.py"),
            },
            "checker": {
                "path": str((WP1_DIR / "checker_v2.py").relative_to(ROOT)),
                "sha256": sha256_file(WP1_DIR / "checker_v2.py"),
            },
            "bridge_receipt": {
                "path": str(BRIDGE_RECEIPT_PATH.relative_to(ROOT)),
                "sha256": sha256_file(BRIDGE_RECEIPT_PATH),
            },
        },
        "safety": {
            "external_network_calls": 0,
            "judge_calls": 0,
            "database_calls": 0,
            "production_service_calls": 0,
            "training_calls": 0,
            "memory_write_back": False,
            "model_calls": 2 * len(episodes),
        },
    }
    write_json(args.output, receipt)
    print(
        f"EPISODE_COLLECTION_PASS stage={stage_name} "
        f"episodes={len(episodes)} attempts={2 * len(episodes)} "
        f"output_sha256={sha256_file(args.output)}",
        flush=True,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("probe", "collect"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("history", "development"),
    )
    parser.add_argument(
        "--probe-history-item-index",
        type=int,
        default=0,
        help="Zero-based index into the deterministic history item list.",
    )
    parser.add_argument("--failure-output", type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.ledger = args.ledger.resolve()
    if args.failure_output is not None:
        args.failure_output = args.failure_output.resolve()
    if args.mode == "collect":
        require(args.stage is not None, "--stage is required for collect")
    health = json.loads(
        urllib.request.urlopen(HEALTH_URL, timeout=10).read().decode("utf-8")
    )
    require(health.get("status") == "READY", "actor service health check failed")
    require(
        health.get("model") == MODEL_ID,
        "actor service model mismatch",
    )
    require(
        health.get("revision") == MODEL_REVISION,
        "actor service revision mismatch",
    )
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "/home/testuser/wzh/models/hf/Qwen3-8B",
        local_files_only=True,
        trust_remote_code=False,
    )
    ledger = PersistFirstLedger(args.ledger)
    if args.mode == "probe":
        return probe_bridge(
            tokenizer,
            ledger,
            args.output,
            args.probe_history_item_index,
        )
    return collect_stage(args, tokenizer, ledger)


if __name__ == "__main__":
    raise SystemExit(main())
