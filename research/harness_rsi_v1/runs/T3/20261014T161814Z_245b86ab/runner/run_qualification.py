#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


RUNNER_DIR = Path(__file__).resolve().parent
RUN_DIR = RUNNER_DIR.parent
FIXTURES = RUNNER_DIR / "fixtures"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def write_exclusive_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def run_fixture(
    pass_id: str, case_id: str, fixture_name: str, workspace: Path
) -> tuple[subprocess.CompletedProcess[str], Path]:
    digest = hashlib.sha256(f"{pass_id}:{case_id}".encode()).hexdigest()[:8]
    run_id = f"20261014T161814Z_{digest}"
    command = [
        sys.executable,
        str(RUNNER_DIR / "runner.py"),
        "execute",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--fixture",
        str(FIXTURES / fixture_name),
    ]
    completed = subprocess.run(
        command,
        cwd=RUN_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed, workspace / run_id


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("event line is not an object")
        events.append(value)
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="T3 local runner qualification")
    parser.add_argument("--pass-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    args = parser.parse_args()

    args.scratch_root.mkdir(parents=True, exist_ok=False)
    checks: list[dict[str, Any]] = []
    command_results: dict[str, dict[str, Any]] = {}

    def check(case_id: str, check_id: str, condition: bool, detail: str) -> None:
        checks.append(
            {
                "case_id": case_id,
                "check_id": check_id,
                "detail": detail,
                "status": "PASS" if condition else "FAIL",
            }
        )

    duplicate_workspace = args.scratch_root / "duplicate_workspace"
    duplicate_workspace.mkdir()
    duplicate_run_id = "20261014T161814Z_deadbeef"
    duplicate_dir = duplicate_workspace / duplicate_run_id
    duplicate_dir.mkdir()
    sentinel = duplicate_dir / "sentinel.txt"
    sentinel.write_text("must remain unchanged\n", encoding="utf-8")
    duplicate_command = [
        sys.executable,
        str(RUNNER_DIR / "runner.py"),
        "execute",
        "--workspace",
        str(duplicate_workspace),
        "--run-id",
        duplicate_run_id,
        "--fixture",
        str(FIXTURES / "success.json"),
    ]
    duplicate = subprocess.run(
        duplicate_command,
        cwd=RUN_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    duplicate_stdout = json.loads(duplicate.stdout)
    command_results["duplicate_id"] = {
        "command": "python3 runner/runner.py execute --workspace <scratch>/duplicate_workspace --run-id 20261014T161814Z_deadbeef --fixture runner/fixtures/success.json",
        "exit_code": duplicate.returncode,
        "stderr": duplicate.stderr,
        "stdout": duplicate_stdout,
    }
    check("duplicate_id", "exit_nonzero", duplicate.returncode != 0, str(duplicate.returncode))
    check(
        "duplicate_id",
        "explicit_rejection",
        duplicate_stdout.get("error") == "duplicate_run_id",
        duplicate_stdout.get("error", "missing"),
    )
    check(
        "duplicate_id",
        "existing_content_preserved",
        sentinel.read_text(encoding="utf-8") == "must remain unchanged\n",
        "sentinel unchanged",
    )
    check(
        "duplicate_id",
        "no_run_summary_created",
        not (duplicate_dir / "run_summary.json").exists(),
        "duplicate target not executed",
    )

    case_specs = [
        ("crash", "crash.json", 4),
        ("overwrite", "overwrite.json", 0),
        ("budget_bypass", "budget_bypass.json", 5),
        ("monotonic_counts", "monotonic_counts.json", 0),
        ("policy_denied", "policy_denied.json", 0),
        ("split_accounting", "split_accounting.json", 0),
        ("persist_before_call", "success.json", 0),
    ]
    summaries: dict[str, dict[str, Any]] = {}
    for case_id, fixture_name, expected_exit in case_specs:
        workspace = args.scratch_root / case_id
        completed, run_dir = run_fixture(
            args.pass_id, case_id, fixture_name, workspace
        )
        summaries[case_id] = read_json(run_dir / "run_summary.json")
        command_results[case_id] = {
            "command": (
                "python3 runner/runner.py execute --workspace "
                f"<scratch>/{case_id} --run-id <derived-local-id> "
                f"--fixture runner/fixtures/{fixture_name}"
            ),
            "exit_code": completed.returncode,
            "stderr": completed.stderr,
            "stdout": completed.stdout.strip(),
        }
        check(
            case_id,
            "expected_exit_code",
            completed.returncode == expected_exit,
            f"expected={expected_exit}, actual={completed.returncode}",
        )

    crash_summary = summaries["crash"]
    crash_run = args.scratch_root / "crash" / crash_summary["run_id"]
    check(
        "crash",
        "status_incomplete",
        crash_summary["execution_status"] == "INCOMPLETE",
        crash_summary["execution_status"],
    )
    check(
        "crash",
        "request_evidence_retained",
        (crash_run / "attempts" / "attempt-0001" / "request.json").exists(),
        "request.json retained",
    )
    check(
        "crash",
        "crash_evidence_retained",
        (crash_run / "attempts" / "attempt-0001" / "crash.json").exists(),
        "crash.json retained",
    )
    check(
        "crash",
        "crashed_request_counted",
        crash_summary["counters"]["crashed_requests"] == 1
        and crash_summary["counters"]["model_extra_requests"] == 1,
        "crashed=1, model_extra_requests=1",
    )

    overwrite_summary = summaries["overwrite"]
    overwrite_run = args.scratch_root / "overwrite" / overwrite_summary["run_id"]
    overwrite_attempt = overwrite_run / "attempts" / "attempt-0001"
    check(
        "overwrite",
        "existing_evidence_preserved",
        (overwrite_attempt / "preexisting.txt").read_text(encoding="utf-8")
        == "preserve existing evidence\n",
        "preexisting.txt unchanged",
    )
    check(
        "overwrite",
        "request_overwrite_rejected",
        not (overwrite_attempt / "request.json").exists()
        and (overwrite_attempt / "overwrite_rejection.json").exists(),
        "no request.json; rejection evidence present",
    )
    check(
        "overwrite",
        "overwrite_rejection_counted",
        overwrite_summary["counters"]["overwrite_rejections"] == 1,
        str(overwrite_summary["counters"]["overwrite_rejections"]),
    )

    budget_summary = summaries["budget_bypass"]
    budget_run = args.scratch_root / "budget_bypass" / budget_summary["run_id"]
    check(
        "budget_bypass",
        "fail_closed_status",
        budget_summary["execution_status"] == "FAILED"
        and budget_summary["budget_status"] == "FAIL_CLOSED",
        f"{budget_summary['execution_status']}/{budget_summary['budget_status']}",
    )
    check(
        "budget_bypass",
        "zero_transport_no_bypass",
        budget_summary["counters"]["transport_calls"] == 0
        and budget_summary["model_extra_requests"] == 0,
        "transport_calls=0, model_extra_requests=0",
    )
    check(
        "budget_bypass",
        "rejection_recorded",
        budget_summary["counters"]["budget_rejections"] == 1
        and (budget_run / "budget_rejection.json").exists(),
        "budget_rejections=1 and evidence exists",
    )

    monotonic_summary = summaries["monotonic_counts"]
    monotonic_run = args.scratch_root / "monotonic_counts" / monotonic_summary["run_id"]
    counters = monotonic_summary["counters"]
    check(
        "monotonic_counts",
        "all_outcomes_counted",
        counters["failed_requests"] == 1
        and counters["timeout_requests"] == 1
        and counters["manual_retry_requests"] == 1
        and counters["successful_requests"] == 1
        and counters["model_extra_requests"] == 4,
        "failure=1, timeout=1, manual_retry=1, success=1, total=4",
    )
    history = read_events(monotonic_run / "count_history.jsonl")
    history_by_counter: dict[str, list[int]] = {}
    monotonic_ok = True
    for event in history:
        history_by_counter.setdefault(event["counter"], []).append(event["after"])
        monotonic_ok = monotonic_ok and event["after"] >= event["before"]
    monotonic_ok = monotonic_ok and all(
        values == sorted(values) for values in history_by_counter.values()
    )
    check(
        "monotonic_counts",
        "count_history_monotonic",
        monotonic_ok,
        f"{len(history)} increments",
    )
    check(
        "monotonic_counts",
        "manual_retries_counted",
        counters["manual_retries"] == 2,
        str(counters["manual_retries"]),
    )

    policy_summary = summaries["policy_denied"]
    policy_run = args.scratch_root / "policy_denied" / policy_summary["run_id"]
    rejection_files = sorted((policy_run / "policy_rejections").glob("*.json"))
    categories = {
        read_json(path)["action"]["category"] for path in rejection_files
    }
    check(
        "policy_denied",
        "all_illegal_families_denied",
        categories
        == {"file_path", "network", "sealed", "production", "database"},
        ",".join(sorted(categories)),
    )
    check(
        "policy_denied",
        "denial_evidence_count",
        policy_summary["counters"]["policy_rejections"] == 5,
        str(policy_summary["counters"]["policy_rejections"]),
    )
    check(
        "policy_denied",
        "no_network_or_production_transport",
        policy_summary["network_used"] is False
        and policy_summary["counters"]["transport_calls"] == 0,
        "network_used=false, transport_calls=0",
    )

    split_summary = summaries["split_accounting"]
    check(
        "split_accounting",
        "ledgers_are_distinct",
        "model_extra_requests" in split_summary
        and "execution_chat_usage" in split_summary,
        "both fields present",
    )
    check(
        "split_accounting",
        "unknown_usage_not_zero",
        split_summary["execution_chat_usage"] == "UNRESOLVED",
        str(split_summary["execution_chat_usage"]),
    )
    check(
        "split_accounting",
        "orchestrated_count_separate",
        split_summary["model_extra_requests"] == 1,
        str(split_summary["model_extra_requests"]),
    )

    persist_summary = summaries["persist_before_call"]
    persist_run = args.scratch_root / "persist_before_call" / persist_summary["run_id"]
    response = read_json(
        persist_run / "attempts" / "attempt-0001" / "response.json"
    )
    request = read_json(
        persist_run / "attempts" / "attempt-0001" / "request.json"
    )
    events = read_events(persist_run / "events.jsonl")
    event_names = [event["event"] for event in events]
    check(
        "persist_before_call",
        "request_recorded_before_mock_result",
        request["mode"] == "persist_before_call"
        and response["request_persisted_before_transport"] is True,
        "exclusive request exists before response",
    )
    check(
        "persist_before_call",
        "event_order_verified",
        event_names.index("request_persisted")
        < event_names.index("transport_called"),
        "->".join(event_names[:3]),
    )

    failures = [item for item in checks if item["status"] != "PASS"]
    normalized = [
        {
            "case_id": item["case_id"],
            "check_id": item["check_id"],
            "detail": item["detail"],
            "status": item["status"],
        }
        for item in checks
    ]
    normalized_sha256 = hashlib.sha256(
        json.dumps(
            normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    result = {
        "checks": checks,
        "command_results": command_results,
        "counts": {
            "failed": len(failures),
            "passed": len(checks) - len(failures),
            "total": len(checks),
        },
        "network_or_model_calls": 0,
        "normalized_result_sha256": normalized_sha256,
        "pass_id": args.pass_id,
        "result": "PASS" if not failures else "FAIL",
        "runner_domain": "LOCAL_DEV_HOST",
        "schema": "t3_runner_qualification_pass_v1",
        "unverified_scope": [
            "OS-level sandbox enforcement",
            "GB10 authoritative runtime binding",
            "production, database, model endpoint and network isolation at kernel level"
        ],
    }
    write_exclusive_json(args.output, result)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
