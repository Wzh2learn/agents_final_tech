#!/usr/bin/env python3
"""S4C online qualification runner (frozen 2026-10-14; owner-approved).

Scope: <=3 probe requests to the bridge-v2 actor service on 127.0.0.1:8112.
- preflight mode: tokenizer-only render checks + frozen component hash checks
  (zero model calls, zero network calls).
- run mode: persist-first, exactly one POST per probe, no transport retries,
  early stop on first criterion failure. No judge/database/training/production
  calls. Writes ledger + raw evidence + run result only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WP2 = HERE.parent
BRIDGE_V2 = WP2 / "bridge_v2"

MODEL_ID = "tatqa-wp2-qwen3-8b-b968826d"
MAX_OUTPUT_TOKENS = 512
REQUEST_TIMEOUT_SECONDS = 1800


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def repo_root() -> Path:
    return WP2.parents[2]


def rel(path: Path) -> str:
    return str(Path(path).resolve().relative_to(repo_root().resolve())).replace("\\", "/")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_v2_frozen", BRIDGE_V2 / "validate_v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_probes():
    return json.loads((HERE / "PROBES_FROZEN.json").read_text(encoding="utf-8"))


def component_hash_checks() -> dict:
    receipt = json.loads((WP2 / "BRIDGE_V2_RECEIPT.json").read_text(encoding="utf-8"))
    results = {}
    ok = True
    for relpath, expected in receipt["component_hashes"].items():
        actual = sha256_file(repo_root() / relpath)
        match = actual == expected
        ok = ok and match
        results[relpath] = {"expected": expected, "actual": actual, "match": match}
    return {"all_match": ok, "components": results}


def get_json(url: str, timeout: float = 60.0):
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def post_completion(url: str, payload: dict):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def preflight(args) -> int:
    checks = {"preflight_at_utc": utc_now()}
    checks["runner_sha256"] = sha256_file(Path(__file__))
    checks["validator_sha256"] = sha256_file(BRIDGE_V2 / "validate_v2.py")
    checks["probes_frozen_sha256"] = sha256_file(HERE / "PROBES_FROZEN.json")
    checks["component_hashes"] = component_hash_checks()

    probes_doc = load_probes()
    checks["probe_source_receipt_sha256_expected"] = probes_doc["source_receipt_sha256"]
    checks["probe_source_receipt_sha256_actual"] = sha256_file(
        WP2 / "S4B_BRIDGE_PROTOCOL_RECEIPT.json"
    )
    checks["probe_source_failure_prompt_sha256_expected"] = probes_doc[
        "source_final_failure_prompt_sha256"
    ]
    checks["probe_source_failure_prompt_sha256_actual"] = sha256_file(
        WP2 / "s4b_run" / "attempts" / "S4_history-01-wp2_3ab739eb_r2_p0-plan-3" / "prompt.txt"
    )
    checks["probe_source_links_ok"] = (
        checks["probe_source_receipt_sha256_expected"]
        == checks["probe_source_receipt_sha256_actual"]
        and checks["probe_source_failure_prompt_sha256_expected"]
        == checks["probe_source_failure_prompt_sha256_actual"]
    )

    sys.path.insert(0, str(BRIDGE_V2))
    from prompt_v2 import (  # noqa: E402
        CONSUME_TEMPLATE_SHA256,
        PLAN_TEMPLATE_SHA256,
        render_chat_prompt,
    )
    from transformers import AutoTokenizer  # noqa: E402

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_root, local_files_only=True, trust_remote_code=False
    )
    checks["template_sha256"] = {
        "plan": PLAN_TEMPLATE_SHA256,
        "consume": CONSUME_TEMPLATE_SHA256,
    }
    rendered = []
    for probe in probes_doc["probes"]:
        text = render_chat_prompt(tokenizer, probe["stage"], probe["task_prompt"])
        token_count = len(tokenizer(text, add_special_tokens=False)["input_ids"])
        rendered.append(
            {
                "probe_id": probe["probe_id"],
                "stage": probe["stage"],
                "task_prompt_sha256": probe["task_prompt_sha256"],
                "rendered_prompt_sha256": sha256_bytes(text.encode("utf-8")),
                "rendered_prompt_tokens": token_count,
                "within_input_cap": token_count <= 4096,
            }
        )
    checks["rendered_prompts"] = rendered
    checks["all_within_input_cap"] = all(row["within_input_cap"] for row in rendered)
    checks["status"] = (
        "PASS"
        if (
            checks["component_hashes"]["all_match"]
            and checks["probe_source_links_ok"]
            and checks["all_within_input_cap"]
        )
        else "FAIL"
    )
    out = HERE / "PREFLIGHT_RENDER_RECEIPT.json"
    write_json(out, checks)
    print(
        json.dumps(
            {
                "status": checks["status"],
                "receipt": str(out),
                "tokens": [row["rendered_prompt_tokens"] for row in rendered],
            }
        )
    )
    return 0 if checks["status"] == "PASS" else 1


def run(args) -> int:
    probes_doc = load_probes()
    if len(probes_doc["probes"]) != 3:
        print("frozen probe count is not 3; refusing to run")
        return 2
    attempts_root = HERE / "attempts"
    if attempts_root.exists() and any(attempts_root.iterdir()):
        print("attempts directory is not empty; refusing to run a second time")
        return 2

    validator = load_validator()
    ledger_path = HERE / "ACTOR_CALL_LEDGER_QUAL.json"
    if ledger_path.exists():
        prior = HERE / "ACTOR_CALL_LEDGER_QUAL_PRIOR.json"
        if prior.exists():
            print("prior ledger archive already exists; refusing a third run")
            return 2
        prior.write_bytes(ledger_path.read_bytes())
    ledger = {
        "schema": "tatqa_wp2_s4c_qualification_ledger_v1",
        "task": probes_doc["task"],
        "persist_first": True,
        "budget": {
            "global_hard_cap": 300,
            "global_attempts_used_before": 9,
            "this_card_max_requests": 3,
            "transport_retries_allowed": 0,
            "judge_calls_allowed": 0,
        },
        "accounting": {
            "this_card_requests_attempted": 0,
            "transport_retries": 0,
        },
        "attempts": [],
        "updated_at_utc": utc_now(),
    }
    write_json(ledger_path, ledger)

    base = args.base_url.rstrip("/")
    results = []
    stopped_early = False
    health_before = None

    for index, probe in enumerate(probes_doc["probes"], start=1):
        probe_id = probe["probe_id"]
        attempt_dir = attempts_root / probe_id
        entry = {
            "probe_index": index,
            "probe_id": probe_id,
            "stage": probe["stage"],
            "logical_request_id": probe_id,
            "started_at_utc": utc_now(),
            "transport_retries": 0,
        }

        try:
            health_status, health = get_json(base + "/health")
            entry["health_before"] = {"http_status": health_status, **health}
            if health_before is None:
                health_before = entry["health_before"]
        except Exception as exc:  # pre-transmission engineering failure
            entry["exit"] = "health_check_failed_before_transmission"
            entry["error"] = "{}: {}".format(type(exc).__name__, exc)
            entry["counted_attempt"] = False
            ledger["attempts"].append(entry)
            ledger["updated_at_utc"] = utc_now()
            write_json(ledger_path, ledger)
            results.append(entry)
            stopped_early = True
            break

        payload = {
            "model": MODEL_ID,
            "prompt": probe["task_prompt"],
            "schema_stage": probe["stage"],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0,
            "n": 1,
        }
        payload_canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        write_json(
            attempt_dir / "request.json",
            {
                "probe_id": probe_id,
                "stage": probe["stage"],
                "task_prompt_sha256": probe["task_prompt_sha256"],
                "payload": payload,
                "payload_canonical_sha256": sha256_bytes(payload_canonical),
                "transmission_state": "about_to_transmit",
                "created_at_utc": utc_now(),
            },
        )
        entry["counted_attempt"] = True
        entry["transmission"] = "attempted"
        ledger["accounting"]["this_card_requests_attempted"] += 1
        started = time.monotonic()
        try:
            status, raw_bytes = post_completion(base + "/v1/completions", payload)
            entry["http_status"] = status
            (attempt_dir / "raw_response.txt").write_bytes(raw_bytes)
            entry["raw_response_sha256"] = sha256_bytes(raw_bytes)
            entry["raw_response_path"] = rel(attempt_dir / "raw_response.txt")
            if status != 200:
                entry["exit"] = "http_error"
                entry["criterion_met"] = False
                entry["transmission"] = "completed_http_error"
                write_json(
                    attempt_dir / "failure_record.json",
                    {"probe_id": probe_id, "http_status": status, "recorded_at_utc": utc_now()},
                )
            else:
                envelope = json.loads(raw_bytes.decode("utf-8"))
                choice = envelope["choices"][0]
                text = choice["text"]
                completion_bytes = text.encode("utf-8")
                (attempt_dir / "completion.txt").write_bytes(completion_bytes)
                entry["completion_sha256"] = sha256_bytes(completion_bytes)
                entry["completion_path"] = rel(attempt_dir / "completion.txt")
                entry["completion_tokens"] = envelope.get("usage", {}).get("completion_tokens")
                entry["prompt_tokens"] = envelope.get("usage", {}).get("prompt_tokens")
                entry["finish_reason"] = choice.get("finish_reason")
                entry["actor_request_id"] = envelope.get("actor_request_id")
                result = validator.validate_stage_response(probe["stage"], text)
                record = result.to_record()
                criterion_met = bool(result.ok and result.route == "strict_json")
                record["criterion_met"] = criterion_met
                write_json(attempt_dir / "validation_result.json", record)
                entry["parse_route"] = result.route
                entry["parse_ok"] = result.ok
                entry["schema_error"] = result.schema_error
                entry["criterion_met"] = criterion_met
                entry["exit"] = "success" if criterion_met else "criterion_failure"
                entry["transmission"] = "completed"
        except Exception as exc:  # transport failure after transmit: counted, no retry
            entry["exit"] = "transport_failure"
            entry["error"] = "{}: {}".format(type(exc).__name__, exc)
            entry["criterion_met"] = False
            entry["transmission"] = "attempted_failed"
            write_json(
                attempt_dir / "failure_record.json",
                {"probe_id": probe_id, "error": entry["error"], "recorded_at_utc": utc_now()},
            )

        entry["elapsed_seconds"] = round(time.monotonic() - started, 3)
        ledger["attempts"].append(entry)
        ledger["updated_at_utc"] = utc_now()
        write_json(ledger_path, ledger)
        results.append(entry)
        if not entry.get("criterion_met"):
            stopped_early = True
            break

    try:
        health_after_status, health_after = get_json(base + "/health")
    except Exception as exc:
        health_after_status, health_after = None, {"error": "{}: {}".format(type(exc).__name__, exc)}

    transmitted = [row for row in results if row.get("counted_attempt")]
    met = [row for row in transmitted if row.get("criterion_met")]
    if len(transmitted) == 3 and len(met) == 3:
        status = "PASS"
    elif any(row.get("exit") == "criterion_failure" or row.get("exit") == "http_error" for row in transmitted):
        status = "FAIL"
    elif transmitted and all(row.get("criterion_met") for row in transmitted) and len(transmitted) < 3:
        status = "ENGINEERING_INCOMPLETE"
    elif not transmitted:
        status = "ENGINEERING_INCOMPLETE"
    else:
        status = "FAIL"

    run_result = {
        "schema": "tatqa_wp2_s4c_qualification_run_result_v1",
        "task": probes_doc["task"],
        "status": status,
        "stopped_early": stopped_early,
        "requests_attempted": len(transmitted),
        "probes_total": 3,
        "probes_not_run": [row["probe_id"] for row in probes_doc["probes"][len(results):]],
        "criterion": probes_doc["criterion"],
        "attempts": results,
        "health_before": health_before,
        "health_after": {"http_status": health_after_status, **(health_after or {})},
        "runner_sha256": sha256_file(Path(__file__)),
        "probes_frozen_sha256": sha256_file(HERE / "PROBES_FROZEN.json"),
        "validator_sha256": sha256_file(BRIDGE_V2 / "validate_v2.py"),
        "generated_at_utc": utc_now(),
    }
    write_json(HERE / "QUAL_RUN_RESULT.json", run_result)
    print(
        json.dumps(
            {
                "status": status,
                "requests_attempted": len(transmitted),
                "stopped_early": stopped_early,
                "result_path": str(HERE / "QUAL_RUN_RESULT.json"),
            }
        )
    )
    return 0 if status == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["preflight", "run"], required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8112")
    parser.add_argument(
        "--model-root",
        default="/home/testuser/wzh/models/hf/Qwen3-8B",
    )
    args = parser.parse_args()
    if args.mode == "preflight":
        return preflight(args)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())