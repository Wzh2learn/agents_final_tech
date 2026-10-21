"""Run the bounded model/interface qualification without touching old ledgers."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "QUALIFICATION_SPEC.json").read_text(encoding="utf-8"))
TASKS = json.loads((ROOT / "TASKS.json").read_text(encoding="utf-8"))["tasks"]
RAW = ROOT / "raw"
LEDGER_PATH = ROOT / "QUALIFICATION_LEDGER.json"
RESULT_PATH = ROOT / "QUALIFICATION_RESULT.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def in_window(now: datetime) -> bool:
    tz = ZoneInfo(SPEC["window"]["timezone"])
    start = datetime.fromisoformat(SPEC["window"]["start"]).astimezone(tz)
    end = datetime.fromisoformat(SPEC["window"]["end"]).astimezone(tz)
    return start <= now <= end


def parse_json_object(content: str) -> dict[str, Any]:
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("response_not_object")
    return value


def validate(phase: str, value: dict[str, Any], task: dict[str, Any]) -> None:
    if phase == "plan":
        if set(value) != {"action", "arguments", "reason_code"}:
            raise ValueError("plan_keys")
        if value["action"] not in {"inspect_dependency", "inspect_change", "run_target_test"}:
            raise ValueError("plan_action")
        if not isinstance(value["arguments"], dict):
            raise ValueError("plan_arguments")
        if not isinstance(value["reason_code"], str) or not value["reason_code"]:
            raise ValueError("plan_reason")
        expected = task["plan"]["expected"]
    else:
        if set(value) != {"status", "facts", "evidence_ids"}:
            raise ValueError("consume_keys")
        if value["status"] not in {"ANSWER", "UNKNOWN", "REFUSE"}:
            raise ValueError("consume_status")
        if value["status"] != "ANSWER" and value["facts"] is not None:
            raise ValueError("nonanswer_facts_not_null")
        if value["status"] == "ANSWER" and not isinstance(value["facts"], dict):
            raise ValueError("answer_facts_not_object")
        if not isinstance(value["evidence_ids"], list) or not all(isinstance(x, str) for x in value["evidence_ids"]):
            raise ValueError("evidence_ids")
        if not set(value["evidence_ids"]).issubset(set(task["consume"]["evidence_ids"])):
            raise ValueError("evidence_not_supplied")
        expected = task["consume"]["expected"]
    for key in ("action", "arguments", "reason_code") if phase == "plan" else ("status", "facts", "evidence_ids"):
        if value[key] != expected[key] and key != "arguments":
            raise ValueError(f"expected_{key}")
    if phase == "plan" and value["arguments"] != expected["arguments"]:
        raise ValueError("expected_arguments")


def request(model: dict[str, Any], phase: str, task: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    prompt = task[phase]["prompt"]
    payload = {
        "model": model["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": SPEC["generation"]["temperature"],
        "top_p": SPEC["generation"]["top_p"],
        "max_tokens": SPEC["generation"]["max_tokens"],
        "response_format": {"type": SPEC["generation"]["response_format"]},
        "chat_template_kwargs": {"enable_thinking": SPEC["generation"]["enable_thinking"]},
    }
    key = f"{task['id']}:{phase}"
    request_hash = sha256(payload)
    req = urllib.request.Request(
        model["endpoint"],
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return payload, {"error": type(exc).__name__, "detail": str(exc)}, request_hash
    return payload, body, request_hash


def verify_model_identity(model: dict[str, Any]) -> dict[str, Any]:
    models_url = model["endpoint"].replace("/chat/completions", "/models")
    try:
        with urllib.request.urlopen(models_url, timeout=10) as response:
            body = json.loads(response.read().decode())
        ids: list[str] = []
        if isinstance(body, dict):
            if isinstance(body.get("data"), list):
                ids = [str(row.get("id")) for row in body["data"] if isinstance(row, dict)]
            elif isinstance(body.get("models"), list):
                ids = [str(row.get("name") or row.get("model")) for row in body["models"] if isinstance(row, dict)]
        return {"expected": model["model"], "observed": ids, "pass": model["model"] in ids}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"expected": model["model"], "observed": [], "pass": False, "error": str(exc)}


def main() -> int:
    ledger = {
        "schema": "research_model_interface_qualification_ledger_v1",
        "goal_id": SPEC["goal_id"],
        "reserved_attempts": SPEC["global_limits"]["reserved_attempts"],
        "reserved_accounting_tokens": SPEC["global_limits"]["reserved_accounting_tokens"],
        "attempts_used": 0,
        "physical_http_calls": 0,
        "accounting_tokens_used": 0,
        "records": [],
    }
    result: dict[str, Any] = {
        "schema": "research_model_interface_qualification_result_v1",
        "evidence_identity": SPEC["evidence_identity"],
        "started_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "models": {},
        "status": "IN_PROGRESS",
    }
    write_json(LEDGER_PATH, ledger)
    write_json(RESULT_PATH, result)
    if not in_window(datetime.now(ZoneInfo("Asia/Shanghai"))):
        result["status"] = "WINDOW_NOT_OPEN"
        write_json(RESULT_PATH, result)
        return 2
    for model in SPEC["models"]:
        identity = verify_model_identity(model)
        rows = []
        model_result = {"identity": identity, "attempts": 0, "valid": 0, "stop_reason": None, "rows": rows}
        result["models"][model["id"]] = model_result
        if not identity["pass"]:
            model_result["stop_reason"] = "IDENTITY_MISMATCH"
            break
        for task_index, task in enumerate(TASKS):
            for phase in ("plan", "consume"):
                if ledger["attempts_used"] >= ledger["reserved_attempts"] or ledger["accounting_tokens_used"] >= ledger["reserved_accounting_tokens"]:
                    model_result["stop_reason"] = "BUDGET_EXHAUSTED"
                    break
                if not in_window(datetime.now(ZoneInfo("Asia/Shanghai"))):
                    model_result["stop_reason"] = "WINDOW_EXIT"
                    break
                payload, body, request_hash = request(model, phase, task)
                ledger["attempts_used"] += 1
                ledger["physical_http_calls"] += 1
                record = {"model": model["id"], "task": task["id"], "phase": phase, "request_sha256": request_hash, "status": "FAILED"}
                if "error" in body:
                    record["error"] = body
                else:
                    try:
                        content = body["choices"][0]["message"]["content"]
                        value = parse_json_object(content)
                        validate(phase, value, task)
                        usage = int(body.get("usage", {}).get("total_tokens", 0) or 0)
                        if usage <= 0:
                            raise ValueError("usage_missing")
                        record.update({"status": "OK", "usage_total_tokens": usage, "prediction": value})
                        ledger["accounting_tokens_used"] += usage
                        model_result["valid"] += 1
                    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                        record["error"] = {"type": type(exc).__name__, "detail": str(exc)}
                record["raw_request"] = f"raw/{model['id']}/{task['id']}/{phase}/request.json"
                record["raw_response"] = f"raw/{model['id']}/{task['id']}/{phase}/response.json"
                write_json(ROOT / record["raw_request"], payload)
                write_json(ROOT / record["raw_response"], body)
                ledger["records"].append(record)
                rows.append(record)
                write_json(LEDGER_PATH, ledger)
                write_json(RESULT_PATH, result)
                if task_index == 0 and phase == "plan" and record["status"] != "OK":
                    model_result["stop_reason"] = "CANARY_FAILED"
                    break
                if record["status"] != "OK":
                    model_result["stop_reason"] = "QUALIFICATION_FAILURE"
                    break
                model_result["attempts"] += 1
            if model_result["stop_reason"]:
                break
        if model_result["stop_reason"]:
            break
    result["finished_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    result["status"] = "PASS" if all(m["valid"] == 12 for m in result["models"].values()) else "QUALIFICATION_INCOMPLETE"
    write_json(RESULT_PATH, result)
    write_json(LEDGER_PATH, ledger)
    print(json.dumps({"status": result["status"], "attempts": ledger["attempts_used"], "tokens": ledger["accounting_tokens_used"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
