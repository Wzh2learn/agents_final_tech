"""Measure real verification actions and policy cost on the pinned Partridge task."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable


def run_command(command: list[str], cwd: Path, timeout: int = 120) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        parsed: Any = None
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None
        return {
            "command": command,
            "cwd": str(cwd),
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
            "parsed": parsed,
            "wall_clock_seconds": round(time.perf_counter() - started, 6),
            "status": "PASS" if proc.returncode == 0 else "FAIL",
        }
    except Exception as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "exit_code": None,
            "stdout_tail": "",
            "stderr_tail": f"{type(exc).__name__}: {exc}",
            "parsed": None,
            "wall_clock_seconds": round(time.perf_counter() - started, 6),
            "status": "ERROR",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--parent-dir", type=Path, required=True)
    parser.add_argument("--gold-dir", type=Path, required=True)
    parser.add_argument("--source-fallback-dir", type=Path, required=True)
    parser.add_argument("--alias-dir", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    python_path = Path(os.path.abspath(args.python))
    verifier_path = Path(os.path.abspath(args.verifier))

    cases = [
        {
            "id": "partridge_parent",
            "verifier_case": "partridge_real_parent",
            "reference": "INVALID",
            "kind": "natural_parent_commit",
            "cwd": str(args.parent_dir.resolve()),
        },
        {
            "id": "partridge_gold",
            "verifier_case": "partridge_real_gold",
            "reference": "VALID",
            "kind": "natural_gold_commit",
            "cwd": str(args.gold_dir.resolve()),
        },
        {
            "id": "partridge_source_fallback",
            "verifier_case": "partridge_target_call_then_source_fallback",
            "reference": "INVALID",
            "kind": "synthetic_real_repository_control",
            "cwd": str(args.source_fallback_dir.resolve()),
        },
        {
            "id": "partridge_alias",
            "verifier_case": "partridge_alias_valid",
            "reference": "VALID",
            "kind": "synthetic_real_repository_control",
            "cwd": str(args.alias_dir.resolve()),
        },
    ]
    test_command = [str(python_path), "-m", "pytest", "-q", "--disable-warnings", "tests"]
    preflight_command = [
        str(python_path),
        "-c",
        "import chardet, cchardet, numpy, pandas; print('imports_ok')",
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        static_command = [
            str(python_path),
            str(verifier_path),
            "--case",
            case["verifier_case"],
            "--action",
            "static_contract",
        ]
        runtime_command = [
            str(python_path),
            str(verifier_path),
            "--case",
            case["verifier_case"],
            "--action",
            "runtime_consumption",
        ]
        actions = {
            "preflight": run_command(preflight_command, case["cwd"]),
            "behavior": run_command(test_command, case["cwd"]),
            "static_contract": run_command(static_command, case["cwd"]),
            "runtime_consumption": run_command(runtime_command, case["cwd"]),
        }
        for action in actions.values():
            action["accounting_attempts"] = 0
            action["accounting_tokens"] = 0
        static_pass = bool(actions["static_contract"]["parsed"] and actions["static_contract"]["parsed"]["static_pass"])
        source_dependency = bool(
            actions["static_contract"]["parsed"]
            and (
                actions["static_contract"]["parsed"]["source_imported"]
                or actions["static_contract"]["parsed"]["source_call_present"]
            )
        )
        runtime_pass = bool(actions["runtime_consumption"]["parsed"] and actions["runtime_consumption"]["parsed"]["target_result_consumed"])
        behavior_pass = actions["behavior"]["status"] == "PASS"
        actions["derived"] = {
            "static_contract": static_pass,
            "source_dependency": source_dependency,
            "runtime_consumption": runtime_pass,
            "enhanced_behavior": behavior_pass,
            "candidate_hybrid": bool(not source_dependency and runtime_pass and behavior_pass),
            "runtime_behavior": bool(runtime_pass and behavior_pass),
        }
        rows.append({**case, "actions": actions})

    def policy(name: str, evaluation: str) -> dict[str, Any]:
        total = 0.0
        action_count = 0
        decisions = {}
        executed: dict[str, list[str]] = {}
        for row in rows:
            actions: list[str] = []
            if evaluation == "defer":
                actions, decision = ["preflight"], "DEFER"
            elif evaluation == "behavior":
                actions = ["preflight", "behavior"]
                decision = "ACCEPT" if row["actions"]["behavior"]["status"] == "PASS" else "REJECT"
            elif evaluation == "static":
                actions = ["preflight", "static_contract"]
                decision = "ACCEPT" if row["actions"]["derived"]["static_contract"] else "REJECT"
            elif evaluation == "static_behavior":
                actions = ["preflight", "static_contract"]
                if not row["actions"]["derived"]["static_contract"]:
                    decision = "REJECT"
                else:
                    actions.append("behavior")
                    decision = "ACCEPT" if row["actions"]["derived"]["enhanced_behavior"] else "REJECT"
            elif evaluation == "full":
                actions = ["preflight", "static_contract"]
                if row["actions"]["derived"]["source_dependency"]:
                    decision = "REJECT"
                else:
                    actions.append("runtime_consumption")
                    if not row["actions"]["derived"]["runtime_consumption"]:
                        decision = "REJECT"
                    else:
                        actions.append("behavior")
                        decision = "ACCEPT" if row["actions"]["derived"]["candidate_hybrid"] else "REJECT"
            elif evaluation == "runtime_behavior":
                actions = ["preflight", "runtime_consumption"]
                if not row["actions"]["derived"]["runtime_consumption"]:
                    decision = "REJECT"
                else:
                    actions.append("behavior")
                    decision = "ACCEPT" if row["actions"]["derived"]["runtime_behavior"] else "REJECT"
            else:
                actions, decision = [], "ACCEPT"
            executed[row["id"]] = actions
            decisions[row["id"]] = decision
            action_count += len(actions)
            total += sum(float(row["actions"][action]["wall_clock_seconds"]) for action in actions)
        return {
            "policy": name,
            "executed_actions": executed,
            "action_count": action_count,
            "wall_clock_seconds": round(total, 6),
            "decisions": decisions,
            "metrics": {
                "correct": sum(
                    (decision == "ACCEPT" and row["reference"] == "VALID")
                    or (decision == "REJECT" and row["reference"] == "INVALID")
                    for row, decision in ((row, decisions[row["id"]]) for row in rows)
                ),
                "false_accept": sum(
                    decision == "ACCEPT" and row["reference"] == "INVALID"
                    for row, decision in ((row, decisions[row["id"]]) for row in rows)
                ),
                "false_reject": sum(
                    decision == "REJECT" and row["reference"] == "VALID"
                    for row, decision in ((row, decisions[row["id"]]) for row in rows)
                ),
                "deferred": sum(decision == "DEFER" for decision in decisions.values()),
                "n": len(rows),
            },
        }

    policies = [
        policy("no_revalidation", "none"),
        policy("always_defer", "defer"),
        policy("behavior_only", "behavior"),
        policy("static_contract_only", "static"),
        policy("static_then_behavior_short_circuit", "static_behavior"),
        policy("source_guard_runtime_behavior_short_circuit", "full"),
        policy("result_consumption_plus_behavior", "runtime_behavior"),
    ]
    payload = {
        "schema": "g3_real_action_policy_probe_v2",
        "date": "2026-10-22",
        "evidence_identity": "REAL_GB10_EXECUTION_FOR_TWO_PINNED_PARTRIDGE_COMMITS",
        "task": {
            "repository": "https://github.com/remix/partridge",
            "parent_commit": "daefcbe6a03e92a0bfc0c2433279b9fd3d179f6c",
            "gold_commit": "09e89d98b5a00db44394204d2f3e70c220b51764",
            "license": "MIT",
            "test_command": test_command,
            "environment": "GB10 Python 3.11.16, NumPy 1.23.5, Pandas 1.5.3, pytest 7.4.4",
        },
        "rows": rows,
        "policies": policies,
        "nonclaims": [
            "This is a two-revision real task probe, not a population estimate.",
            "Wall-clock time includes process startup and test execution and is not a model-token cost.",
            "The comparison tests whether adaptive ordering adds value over a short-circuit static/runtime/behavior contract; it does not validate a learned policy.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": rows, "policies": policies}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
