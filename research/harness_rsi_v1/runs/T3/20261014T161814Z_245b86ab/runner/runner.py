#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


RUN_ID_PATTERN = re.compile(
    r"^\d{8}T\d{6}Z_[0-9a-f]{8}$",
)
OUTCOME_COUNTERS = {
    "success": "successful_requests",
    "failure": "failed_requests",
    "timeout": "timeout_requests",
    "manual_retry": "manual_retry_requests",
    "crash": "crashed_requests",
}


class DuplicateRunIdError(RuntimeError):
    pass


class OverwriteRejectedError(RuntimeError):
    pass


class PolicyDeniedError(RuntimeError):
    pass


class BudgetExhaustedError(RuntimeError):
    pass


def dump_json(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def update_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def append_jsonl(path: Path, payload: Any) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


class Runner:
    def __init__(self, workspace: Path, run_id: str, fixture: dict[str, Any]) -> None:
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError(f"invalid run_id: {run_id}")
        self.workspace = workspace.resolve()
        self.run_id = run_id
        self.run_dir = self.workspace / run_id
        self.fixture = fixture
        self.fixed_time = fixture.get("fixed_time", "2026-10-14T16:18:14Z")
        self.profile = fixture.get("profile", {"cheap_requests": 0, "strong_requests": 0})
        self.budget_cap = int(self.profile.get("cheap_requests", 0))
        self.counters = {
            "model_extra_requests": 0,
            "transport_calls": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "manual_retry_requests": 0,
            "crashed_requests": 0,
            "manual_retries": 0,
            "budget_rejections": 0,
            "policy_rejections": 0,
            "overwrite_rejections": 0,
        }
        self.previous_counters: dict[str, int] = dict(self.counters)
        self.attempt_sequence = 0
        self.policy_sequence = 0
        self.budget_status = "NOT_EXHAUSTED"
        self.execution_status = "RUNNING"

    def create_run(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        try:
            self.run_dir.mkdir()
        except FileExistsError as exc:
            raise DuplicateRunIdError(str(self.run_dir)) from exc
        (self.run_dir / ".run_id").write_text(self.run_id + "\n", encoding="utf-8")
        dump_json(
            self.run_dir / "run_state.json",
            {
                "execution_status": "RUNNING",
                "generated_at": self.fixed_time,
                "profile": self.profile,
                "run_id": self.run_id,
                "schema": "t3_mock_run_state_v1",
                "scope_domain": "LOCAL_DEV_HOST",
            },
        )

    def ensure_path_allowed(self, requested_path: str) -> Path:
        candidate = Path(requested_path)
        if not candidate.is_absolute():
            candidate = self.run_dir / candidate
        resolved = candidate.resolve()
        if self.run_dir.resolve() not in resolved.parents and resolved != self.run_dir.resolve():
            raise PolicyDeniedError(f"path outside run allowlist: {resolved}")
        return resolved

    def record_policy_rejection(self, action: dict[str, Any]) -> None:
        self.policy_sequence += 1
        evidence_dir = self.run_dir / "policy_rejections"
        evidence_dir.mkdir(exist_ok=True)
        rejection = {
            "action": action,
            "counters": dict(self.counters),
            "denial_reason": action.get("denial_reason", "DENIED_BY_POLICY"),
            "generated_at": self.fixed_time,
            "schema": "t3_policy_rejection_v1",
            "sequence": self.policy_sequence,
            "target": action.get("target", "UNRESOLVED"),
        }
        dump_json(evidence_dir / f"rejection-{self.policy_sequence:04d}.json", rejection)
        self.increment("policy_rejections")
        append_jsonl(
            self.run_dir / "events.jsonl",
            {
                "counters": dict(self.counters),
                "event": "policy_rejected",
                "generated_at": self.fixed_time,
                "sequence": self.policy_sequence,
                "target": rejection["target"],
            },
        )

    def validate_policy(self, action: dict[str, Any]) -> None:
        category = action["category"]
        if category in {"network", "sealed", "production", "database"}:
            raise PolicyDeniedError(f"{category} access denied")
        if category == "file_path":
            self.ensure_path_allowed(str(action["target"]))
            return
        raise PolicyDeniedError(f"unknown policy category: {category}")

    def increment(self, name: str, amount: int = 1) -> None:
        current = self.counters[name]
        updated = current + amount
        if updated < current:
            raise RuntimeError(f"counter regression: {name}")
        self.counters[name] = updated
        history = self.run_dir / "count_history.jsonl"
        append_jsonl(
            history,
            {
                "after": updated,
                "before": current,
                "counter": name,
                "generated_at": self.fixed_time,
                "monotonic": updated >= current,
            },
        )

    def persist_attempt_request(
        self, attempt_id: str, action: dict[str, Any]
    ) -> tuple[Path, Path]:
        attempts_dir = self.run_dir / "attempts"
        attempts_dir.mkdir(exist_ok=True)
        attempt_dir = attempts_dir / attempt_id
        try:
            attempt_dir.mkdir()
        except FileExistsError as exc:
            self.increment("overwrite_rejections")
            dump_json(
                attempt_dir / "overwrite_rejection.json",
                {
                    "attempt_id": attempt_id,
                    "generated_at": self.fixed_time,
                    "mode": "exclusive_create",
                    "outcome": "DENIED",
                    "reason": "attempt_directory_exists",
                    "schema": "t3_overwrite_rejection_v1",
                },
            )
            raise OverwriteRejectedError(str(attempt_dir)) from exc
        request_path = attempt_dir / "request.json"
        response_path = attempt_dir / "response.json"
        request = {
            "attempt_id": attempt_id,
            "generated_at": self.fixed_time,
            "mode": "persist_before_call",
            "payload": action.get("payload", {}),
            "retry_of": action.get("retry_of"),
            "schema": "t3_attempt_request_v1",
        }
        dump_json(request_path, request)
        append_jsonl(
            self.run_dir / "events.jsonl",
            {
                "attempt_id": attempt_id,
                "counters": dict(self.counters),
                "event": "request_persisted",
                "generated_at": self.fixed_time,
                "mode": "exclusive_create",
            },
        )
        return request_path, response_path

    def check_budget(self, action: dict[str, Any]) -> None:
        if self.counters["model_extra_requests"] >= self.budget_cap:
            self.budget_status = "FAIL_CLOSED"
            self.increment("budget_rejections")
            dump_json(
                self.run_dir / "budget_rejection.json",
                {
                    "action": action,
                    "budget_cap": self.budget_cap,
                    "counters": dict(self.counters),
                    "generated_at": self.fixed_time,
                    "outcome": "FAIL_CLOSED",
                    "reason": "budget_cap_reached",
                    "schema": "t3_budget_rejection_v1",
                    "transport_called": False,
                },
            )
            append_jsonl(
                self.run_dir / "events.jsonl",
                {
                    "counters": dict(self.counters),
                    "event": "budget_rejected",
                    "generated_at": self.fixed_time,
                    "transport_called": False,
                },
            )
            raise BudgetExhaustedError("budget cap reached before transport")

    def run_transport_action(self, action: dict[str, Any]) -> None:
        self.attempt_sequence += 1
        attempt_id = action.get("attempt_id", f"attempt-{self.attempt_sequence:04d}")
        self.check_budget(action)
        request_path, response_path = self.persist_attempt_request(attempt_id, action)
        if not request_path.exists():
            raise RuntimeError("request was not persisted before transport")
        outcome = action["outcome"]
        if outcome not in OUTCOME_COUNTERS:
            raise ValueError(f"unknown outcome: {outcome}")
        self.increment("model_extra_requests")
        self.increment("transport_calls")
        append_jsonl(
            self.run_dir / "events.jsonl",
            {
                "attempt_id": attempt_id,
                "counters": dict(self.counters),
                "event": "transport_called",
                "generated_at": self.fixed_time,
                "outcome": outcome,
                "request_persisted": True,
            },
        )
        self.increment(OUTCOME_COUNTERS[outcome])
        if action.get("retry_of"):
            self.increment("manual_retries")
        if outcome == "crash":
            dump_json(
                self.run_dir / "attempts" / attempt_id / "crash.json",
                {
                    "attempt_id": attempt_id,
                    "counters": dict(self.counters),
                    "evidence_preserved": True,
                    "generated_at": self.fixed_time,
                    "phase": "mock_transport",
                    "schema": "t3_crash_evidence_v1",
                    "status": "INCOMPLETE",
                },
            )
            self.execution_status = "INCOMPLETE"
            append_jsonl(
                self.run_dir / "events.jsonl",
                {
                    "attempt_id": attempt_id,
                    "counters": dict(self.counters),
                    "event": "crash_recorded",
                    "evidence_preserved": True,
                    "generated_at": self.fixed_time,
                    "status": "INCOMPLETE",
                },
            )
            return
        response = {
            "attempt_id": attempt_id,
            "counters": dict(self.counters),
            "generated_at": self.fixed_time,
            "mock": True,
            "network_used": False,
            "outcome": outcome,
            "request_persisted_before_transport": request_path.exists(),
            "schema": "t3_mock_response_v1",
        }
        dump_json(response_path, response)
        append_jsonl(
            self.run_dir / "events.jsonl",
            {
                "attempt_id": attempt_id,
                "counters": dict(self.counters),
                "event": "transport_result",
                "generated_at": self.fixed_time,
                "outcome": outcome,
            },
        )

    def execute(self) -> int:
        self.create_run()
        for preseed in self.fixture.get("preseed_attempts", []):
            attempt_dir = self.run_dir / "attempts" / preseed
            attempt_dir.mkdir(parents=True)
            (attempt_dir / "preexisting.txt").write_text(
                "preserve existing evidence\n", encoding="utf-8"
            )
        exit_code = 0
        try:
            for action in self.fixture["actions"]:
                action_type = action["type"]
                if action_type == "policy_probe":
                    try:
                        self.validate_policy(action)
                    except PolicyDeniedError:
                        self.record_policy_rejection(action)
                    continue
                if action_type == "overwrite_probe":
                    try:
                        self.persist_attempt_request(
                            action.get("attempt_id", "attempt-0001"), action
                        )
                    except OverwriteRejectedError:
                        append_jsonl(
                            self.run_dir / "events.jsonl",
                            {
                                "attempt_id": action.get("attempt_id", "attempt-0001"),
                                "counters": dict(self.counters),
                                "event": "overwrite_rejected",
                                "generated_at": self.fixed_time,
                                "existing_evidence_preserved": True,
                            },
                        )
                    continue
                if action_type != "transport":
                    raise ValueError(f"unknown action type: {action_type}")
                self.run_transport_action(action)
                if self.execution_status == "INCOMPLETE":
                    exit_code = 4
                    break
        except BudgetExhaustedError:
            self.execution_status = "FAILED"
            exit_code = 5
        except Exception as exc:
            self.execution_status = "INCOMPLETE"
            dump_json(
                self.run_dir / "unexpected_crash.json",
                {
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "evidence_preserved": True,
                    "generated_at": self.fixed_time,
                    "schema": "t3_unexpected_crash_v1",
                    "status": "INCOMPLETE",
                },
            )
            exit_code = 4
        if self.execution_status == "RUNNING":
            self.execution_status = "COMPLETE"
        summary = {
            "budget_cap": self.budget_cap,
            "budget_status": self.budget_status,
            "counters": dict(self.counters),
            "count_monotonic": True,
            "execution_chat_usage": "UNRESOLVED",
            "execution_status": self.execution_status,
            "generated_at": self.fixed_time,
            "mock_transport_only": True,
            "model_extra_requests": self.counters["model_extra_requests"],
            "network_used": False,
            "profile": self.profile,
            "run_id": self.run_id,
            "schema": "t3_mock_run_summary_v1",
            "scope_domain": "LOCAL_DEV_HOST",
        }
        dump_json(self.run_dir / "run_summary.json", summary)
        update_json(
            self.run_dir / "run_state.json",
            {
                "counters": dict(self.counters),
                "execution_status": self.execution_status,
                "generated_at": self.fixed_time,
                "profile": self.profile,
                "run_id": self.run_id,
                "schema": "t3_mock_run_state_v1",
                "scope_domain": "LOCAL_DEV_HOST",
            },
        )
        print(
            json.dumps(
                {
                    "execution_status": self.execution_status,
                    "run_dir": str(self.run_dir),
                    "run_id": self.run_id,
                },
                sort_keys=True,
            )
        )
        return exit_code


def load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("fixture root must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="T3 policy-level mock runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--workspace", required=True, type=Path)
    execute_parser.add_argument("--run-id", required=True)
    execute_parser.add_argument("--fixture", required=True, type=Path)
    args = parser.parse_args()
    try:
        fixture = load_fixture(args.fixture)
        return Runner(args.workspace, args.run_id, fixture).execute()
    except DuplicateRunIdError as exc:
        print(json.dumps({"error": "duplicate_run_id", "target": str(exc)}, sort_keys=True))
        return 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"error": type(exc).__name__, "message": str(exc)},
                sort_keys=True,
            )
        )
        return 6


if __name__ == "__main__":
    sys.exit(main())
