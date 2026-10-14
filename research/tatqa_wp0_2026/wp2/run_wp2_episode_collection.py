#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
sys.path.insert(0, str(WP1_DIR))

import checker_v2  # noqa: E402
from adapter import ContextHook, build_prompt  # noqa: E402


MODEL_ID = "tatqa-wp2-qwen3-8b-b968826d"
SERVICE_URL = "http://127.0.0.1:8112/v1/completions"
MAX_TOTAL_ATTEMPTS = 40
MAX_TRANSPORT_RETRIES = 4
MAX_INPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 512
TEMPERATURE = 0
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
Do not provide the final answer in this stage.\n"""
CONSUME_PROTOCOL = """\nSTAGE=consume
Use the supplied tool trace and the evidence.
Return exactly one JSON object and no other text:
{"row":"<exact row label>","periods":["<late label>","<early label>"],"delta_source":"<calc result>","delta_target":"<converted calc result>","unit":"<target unit>"}\n"""
NUMERIC_PATTERN = r"-?(?:\d+(?:\.\d+)?|\.\d+)"
EXPRESSION_PATTERN = re.compile(
    rf"^\s*({NUMERIC_PATTERN})\s*([-+])\s*({NUMERIC_PATTERN})\s*$"
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


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(payload))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def opaque_id(prefix: str, internal_id: str) -> str:
    digest = hashlib.sha256(
        f"tatqa-wp2-opaque-v1:{prefix}:{internal_id}".encode("utf-8")
    ).hexdigest()
    return f"{prefix}_{digest[:12]}"


def json_decimal(value: Decimal) -> str | int | float:
    if value == value.to_integral_value():
        return int(value)
    normalized = value.normalize()
    return format(normalized, "f")


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1]).strip()
    decoder = json.JSONDecoder()
    parsed, end = decoder.raw_decode(stripped)
    if stripped[end:].strip():
        raise ValueError("JSON response contains trailing non-whitespace text")
    if not isinstance(parsed, dict):
        raise ValueError("JSON response must be an object")
    return parsed


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
    left = Decimal(match.group(1))
    operator = match.group(2)
    right = Decimal(match.group(3))
    result = left - right if operator == "-" else left + right
    return expression, result


def actor_request(
    prompt: str,
    tokenizer: Any,
    accounting: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt_tokens = len(tokenizer.encode(prompt, add_special_tokens=False))
    require(
        prompt_tokens <= MAX_INPUT_TOKENS,
        f"prompt exceeds frozen input cap: {prompt_tokens} tokens",
    )
    request_id = f"runner-{uuid.uuid4()}"
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
        started = time.monotonic()
        try:
            request = urllib.request.Request(
                SERVICE_URL,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=300) as response:
                status = int(response.status)
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw_response = exc.read().decode("utf-8", errors="replace")
            elapsed = time.monotonic() - started
            accounting.append(
                {
                    "runner_request_id": request_id,
                    "actor_request_id": None,
                    "http_status": int(exc.code),
                    "exit": "http_error",
                    "transport_retries": transport_retries,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": 0,
                    "elapsed_seconds": elapsed,
                    "response_sha256": hashlib.sha256(
                        raw_response.encode("utf-8")
                    ).hexdigest(),
                }
            )
            raise RuntimeError(
                f"actor HTTP error {exc.code}: {raw_response[:500]}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            elapsed = time.monotonic() - started
            transport_retries += 1
            accounting.append(
                {
                    "runner_request_id": request_id,
                    "actor_request_id": None,
                    "http_status": None,
                    "exit": "transport_error",
                    "transport_retries": transport_retries,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": 0,
                    "elapsed_seconds": elapsed,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            require(
                transport_retries <= MAX_TRANSPORT_RETRIES,
                "transport retry cap exceeded",
            )
            time.sleep(min(2**transport_retries, 8))
            continue
        elapsed = time.monotonic() - started
        require(status == 200, f"unexpected actor HTTP status: {status}")
        parsed = json.loads(raw_response)
        require(
            parsed.get("model") == MODEL_ID,
            "actor response model mismatch",
        )
        usage = parsed["usage"]
        accounting.append(
            {
                "runner_request_id": request_id,
                "actor_request_id": parsed.get("id"),
                "http_status": status,
                "exit": "success",
                "transport_retries": transport_retries,
                "prompt_tokens": int(usage["prompt_tokens"]),
                "completion_tokens": int(usage["completion_tokens"]),
                "elapsed_seconds": elapsed,
                "response_sha256": hashlib.sha256(
                    raw_response.encode("utf-8")
                ).hexdigest(),
            }
        )
        require(
            int(usage["prompt_tokens"]) <= MAX_INPUT_TOKENS,
            "actor service returned over-cap input token count",
        )
        return parsed


def run_episode(
    item: Mapping[str, Any],
    stage: str,
    arm: str,
    rules_text: str,
    tokenizer: Any,
    call_accounting: list[dict[str, Any]],
) -> dict[str, Any]:
    hook_type = "none" if arm == "B" else "static_rules"
    hook = ContextHook(arm=arm, hook_type=hook_type, text=rules_text)
    base_prompt = build_prompt(item, hook)
    plan_response = actor_request(
        base_prompt + PLAN_PROTOCOL,
        tokenizer,
        call_accounting,
    )
    plan_text = plan_response["choices"][0]["text"]
    plan = extract_json(plan_text)
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
    consume_response = actor_request(
        consume_prompt,
        tokenizer,
        call_accounting,
    )
    consume_text = consume_response["choices"][0]["text"]
    answer = extract_json(consume_text)
    required = {"row", "periods", "delta_source", "delta_target", "unit"}
    require(
        set(answer) == required,
        "final answer has fields outside the frozen format",
    )
    answer["delta_source"] = json_decimal(
        answer["delta_source"],
        "delta_source",
    )
    answer["delta_target"] = json_decimal(
        answer["delta_target"],
        "delta_target",
    )
    answer_text = json.dumps(answer, ensure_ascii=False, sort_keys=True)
    verdict = checker_v2.score_item(item, answer_text)
    item_id = str(item["item_id"])
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
    episode_id = opaque_id("episode", item_id)
    return {
        "episode_id": episode_id,
        "origin_ref": opaque_id("origin", origin_id),
        "internal_origin_id": origin_id,
        "internal_item_id": item_id,
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
                ROOT / "research/tatqa_wp0_2026/wp1/checker_v2.py"
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
        "raw_actor": {
            "plan_sha256": hashlib.sha256(
                plan_text.encode("utf-8")
            ).hexdigest(),
            "consume_sha256": hashlib.sha256(
                consume_text.encode("utf-8")
            ).hexdigest(),
            "plan_object": plan,
            "consume_object": answer,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=("history", "development"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    require(
        urllib.request.urlopen(
            "http://127.0.0.1:8112/health",
            timeout=10,
        ).status
        == 200,
        "actor service health check failed",
    )
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "/home/testuser/wzh/models/hf/Qwen3-8B",
        local_files_only=True,
        trust_remote_code=False,
    )
    split = load_json(
        ROOT / "research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json"
    )
    items_payload = load_json(
        ROOT / "data/research/tatqa_wp0_2026/candidate_items_v2.json"
    )
    role = "history" if args.stage == "history" else "development"
    origins = set(split["roles"][role])
    items = [
        item
        for item in items_payload["items"]
        if item["origin_id"] in origins
    ]
    require(
        len({item["origin_id"] for item in items})
        == (4 if role == "history" else 2),
        "stage origin count mismatch",
    )
    require(
        len(items) == (8 if role == "history" else 4),
        "stage item count mismatch",
    )
    existing_ledger = load_json(args.ledger) if args.ledger.exists() else {
        "schema": "tatqa_wp2_actor_call_ledger_v1",
        "task": "tatqa-wp2-s4s7-20261014",
        "budget": {
            "global_hard_cap": 300,
            "card_hard_cap": 40,
            "max_transport_retries_per_request": MAX_TRANSPORT_RETRIES,
            "judge_calls": 0,
        },
        "attempts": [],
        "stages": {},
    }
    prior_attempts = len(existing_ledger["attempts"])
    require(
        prior_attempts + 2 * len(items) <= MAX_TOTAL_ATTEMPTS,
        "S4/S5 actor-attempt cap would be exceeded",
    )
    call_accounting: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        stage = "S4_history" if role == "history" else "S5_development"
        arm = "B" if role == "history" else "S"
        episodes.append(
            run_episode(
                item,
                stage,
                arm,
                "" if arm == "B" else S_RULES,
                tokenizer,
                call_accounting,
            )
        )
        existing_ledger["attempts"] = existing_ledger["attempts"] + call_accounting
        call_accounting = []
        existing_ledger["stages"][stage] = {
            "episodes": len(episodes),
            "actor_request_attempts": 2 * len(episodes),
            "cumulative_actor_request_attempts": len(existing_ledger["attempts"]),
        }
        write_json(args.ledger, existing_ledger)
        print(
            f"EPISODE_COLLECTED stage={stage} index={index + 1}/{len(items)} "
            f"attempts={len(existing_ledger['attempts'])}",
            flush=True,
        )

    receipt = {
        "schema": "tatqa_wp2_episode_collection_receipt_v1",
        "task": "tatqa-wp2-s4s7-20261014",
        "status": "PASS",
        "stage": "S4_history" if role == "history" else "S5_development",
        "generated_at_utc": utc_now(),
        "role": role,
        "arm": "B" if role == "history" else "S",
        "counts": {
            "origins": len({episode["internal_origin_id"] for episode in episodes}),
            "episodes": len(episodes),
            "actor_request_attempts": 2 * len(episodes),
        },
        "settings": {
            "temperature": TEMPERATURE,
            "single_shot": True,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "input_token_cap": MAX_INPUT_TOKENS,
            "experience_block_cap": 600,
            "automatic_third_round_repair": False,
        },
        "service": {
            "url": SERVICE_URL,
            "model_id": MODEL_ID,
            "revision": "b968826d9c46dd6066d109eabc6255188de91218",
            "startup_receipt": str(
                Path("/tmp/tatqa-wp2-actor-20261014/STARTUP_RECEIPT.json")
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
            "stage_actor_request_attempts": 2 * len(episodes),
            "cumulative_actor_request_attempts": len(
                existing_ledger["attempts"]
            ),
            "global_actor_request_attempts_used": len(
                existing_ledger["attempts"]
            ),
            "transport_retries": sum(
                int(row["transport_retries"])
                for row in existing_ledger["attempts"]
            ),
            "judge_calls": 0,
        },
        "software": {
            "runner": {
                "path": str(Path(__file__).relative_to(ROOT)),
                "sha256": sha256_file(Path(__file__)),
            },
            "adapter": {
                "path": "research/tatqa_wp0_2026/wp1/adapter.py",
                "sha256": sha256_file(WP1_DIR / "adapter.py"),
            },
            "checker": {
                "path": "research/tatqa_wp0_2026/wp1/checker_v2.py",
                "sha256": sha256_file(WP1_DIR / "checker_v2.py"),
            },
        },
        "safety": {
            "external_network_calls": 0,
            "judge_calls": 0,
            "database_calls": 0,
            "production_service_calls": 0,
            "model_calls": 2 * len(episodes),
        },
    }
    write_json(args.output, receipt)
    print(
        f"EPISODE_COLLECTION_PASS stage={receipt['stage']} "
        f"episodes={len(episodes)} attempts={2 * len(episodes)} "
        f"output_sha256={sha256_file(args.output)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
