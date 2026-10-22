"""Measure actual-module verification channels on pinned Partridge candidates."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from g2_contract_verifier_v3 import INVALID, UNRESOLVED, VALID, sha256_file


CASES = (
    {
        "id": "partridge_parent",
        "verifier_id": "partridge_parent",
        "reference": INVALID,
        "worktree": "partridge_parent",
        "kind": "natural_parent_commit",
        "reference_provenance": "parent_commit_role_reference",
    },
    {
        "id": "partridge_gold",
        "verifier_id": "partridge_gold",
        "reference": VALID,
        "worktree": "partridge_gold",
        "kind": "natural_gold_commit",
        "reference_provenance": "upstream_migration_commit_reference",
    },
    {
        "id": "partridge_source_fallback",
        "verifier_id": "partridge_source_fallback",
        "reference": INVALID,
        "worktree": "partridge_source_fallback",
        "kind": "manual_control_real_repository",
        "reference_provenance": "manual_contract_adjudication",
    },
    {
        "id": "partridge_alias",
        "verifier_id": "partridge_alias",
        "reference": VALID,
        "worktree": "partridge_alias",
        "kind": "manual_control_real_repository",
        "reference_provenance": "manual_contract_adjudication",
    },
    {
        "id": "partridge_audit_counterexample",
        "verifier_id": "partridge_audit_counterexample",
        "reference": INVALID,
        "worktree": "partridge_audit_counterexample",
        "kind": "audit_counterexample_real_repository",
        "reference_provenance": "manual_contract_adjudication",
    },
    {
        "id": "partridge_model_candidate_001",
        "verifier_id": "partridge_model_candidate_001",
        "reference": VALID,
        "worktree": "partridge_model_candidate_001",
        "kind": "natural_model_output",
        "reference_provenance": "gold_diff_neutral_bytearray_change_plus_independent_execution",
    },
)


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
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "parsed": parsed,
            "wall_clock_seconds": round(time.perf_counter() - started, 6),
            "accounting_attempts": 0,
            "accounting_tokens": 0,
        }
    except Exception as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "exit_code": None,
            "status": "ERROR",
            "stdout_tail": "",
            "stderr_tail": f"{type(exc).__name__}: {exc}",
            "parsed": None,
            "wall_clock_seconds": round(time.perf_counter() - started, 6),
            "accounting_attempts": 0,
            "accounting_tokens": 0,
        }


def derive_prediction(
    static_prediction: str,
    consumption_prediction: str,
    behavior_status: str,
) -> tuple[str, str]:
    if static_prediction == INVALID or consumption_prediction == INVALID:
        return INVALID, "independent_evidence_contains_invalid_result"
    if behavior_status == "FAIL":
        return INVALID, "independent_behavior_contract_fails"
    if (
        static_prediction == VALID
        and consumption_prediction == VALID
        and behavior_status == "PASS"
    ):
        return VALID, "static_consumption_and_behavior_contract_agree"
    return UNRESOLVED, "required_evidence_channel_unresolved"


def policy(
    name: str,
    rows: list[dict[str, Any]],
    evaluator: Callable[[dict[str, Any]], tuple[list[str], str]],
) -> dict[str, Any]:
    total = 0.0
    action_count = 0
    decisions: dict[str, str] = {}
    executed: dict[str, list[str]] = {}
    for row in rows:
        actions, decision = evaluator(row)
        executed[row["id"]] = actions
        decisions[row["id"]] = decision
        action_count += len(actions)
        total += sum(float(row["actions"][action]["wall_clock_seconds"]) for action in actions)
    correct = false_accept = false_reject = deferred = unresolved = 0
    for row in rows:
        decision = decisions[row["id"]]
        reference = row["reference"]
        if decision == "DEFER":
            deferred += 1
        elif decision == UNRESOLVED:
            unresolved += 1
        elif decision == VALID and reference == VALID:
            correct += 1
        elif decision == INVALID and reference == INVALID:
            correct += 1
        elif decision == VALID and reference == INVALID:
            false_accept += 1
        elif decision == INVALID and reference == VALID:
            false_reject += 1
    return {
        "policy": name,
        "executed_actions": executed,
        "action_count": action_count,
        "wall_clock_seconds": round(total, 6),
        "decisions": decisions,
        "metrics": {
            "correct": correct,
            "false_accept": false_accept,
            "false_reject": false_reject,
            "deferred": deferred,
            "unresolved": unresolved,
            "n": len(rows),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--behavior-contract", type=Path, required=True)
    parser.add_argument("--worktree-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    python_path = Path(str(args.python.absolute()))
    verifier_path = args.verifier.resolve()
    behavior_path = args.behavior_contract.resolve()
    worktree_root = args.worktree_root.resolve()
    behavior_reference_module = (
        worktree_root / "partridge_parent/partridge/utilities.py"
    ).resolve()
    behavior_fixture_root = (worktree_root / "partridge_parent/tests/fixtures").resolve()

    env_command = [
        str(python_path),
        "-c",
        "import json,platform,sys,numpy,pandas,cchardet,chardet,pytest;"
        "print(json.dumps({'python':sys.version,'platform':platform.platform(),"
        "'numpy':numpy.__version__,'pandas':pandas.__version__,"
        "'cchardet':getattr(cchardet,'__version__','unknown'),"
        "'chardet':getattr(chardet,'__version__','unknown'),"
        "'pytest':pytest.__version__}))",
    ]
    environment = run_command(env_command, worktree_root)

    rows: list[dict[str, Any]] = []
    for case in CASES:
        worktree = (worktree_root / case["worktree"]).resolve()
        module = worktree / "partridge/utilities.py"
        manifest = worktree / "setup.py"
        actions = {
            "preflight": run_command(
                [
                    str(python_path),
                    "-c",
                    "import chardet,cchardet,numpy,pandas; print('imports_ok')",
                ],
                worktree,
            ),
            "repository_tests": run_command(
                [
                    str(python_path),
                    "-m",
                    "pytest",
                    "-q",
                    "--disable-warnings",
                    "tests",
                ],
                worktree,
            ),
            "behavior_contract": run_command(
                [
                    str(python_path),
                    str(behavior_path),
                    "--module",
                    str(module),
                    "--reference-module",
                    str(behavior_reference_module),
                    "--fixture-root",
                    str(behavior_fixture_root),
                ],
                worktree,
            ),
            "static_contract": run_command(
                [
                    str(python_path),
                    str(verifier_path),
                    "--candidate-id",
                    case["verifier_id"],
                    "--module",
                    str(module),
                    "--manifest",
                    str(manifest),
                    "--reference",
                    case["reference"],
                    "--behavior-status",
                    "NOT_RUN",
                    "--evidence-channel",
                    "static_contract",
                ],
                worktree,
            ),
            "consumption": run_command(
                [
                    str(python_path),
                    str(verifier_path),
                    "--candidate-id",
                    case["verifier_id"],
                    "--module",
                    str(module),
                    "--manifest",
                    str(manifest),
                    "--reference",
                    case["reference"],
                    "--behavior-status",
                    "NOT_RUN",
                    "--evidence-channel",
                    "consumption",
                ],
                worktree,
            ),
        }
        static_prediction = actions["static_contract"]["parsed"]["prediction"]
        consumption_prediction = actions["consumption"]["parsed"]["prediction"]
        behavior_status = (
            actions["behavior_contract"]["parsed"]["status"]
            if actions["behavior_contract"]["parsed"]
            else "ERROR"
        )
        prediction, reason = derive_prediction(
            static_prediction,
            consumption_prediction,
            behavior_status,
        )
        rows.append(
            {
                **case,
                "module_path": str(module),
                "module_sha256": sha256_file(module),
                "manifest_path": str(manifest),
                "manifest_sha256": sha256_file(manifest),
                "actions": actions,
                "derived": {
                    "static_prediction": static_prediction,
                    "consumption_prediction": consumption_prediction,
                    "behavior_status": behavior_status,
                    "repository_tests_status": actions["repository_tests"]["status"],
                    "prediction": prediction,
                    "prediction_reason": reason,
                },
            }
        )

    policies = [
        policy("no_revalidation", rows, lambda row: ([], VALID)),
        policy(
            "repository_tests_only",
            rows,
            lambda row: (
                ["preflight", "repository_tests"],
                VALID if row["actions"]["repository_tests"]["status"] == "PASS" else INVALID,
            ),
        ),
        policy(
            "strong_static_plus_behavior",
            rows,
            lambda row: (
                ["preflight", "static_contract", "behavior_contract"]
                if row["derived"]["static_prediction"] != INVALID
                else ["preflight", "static_contract"],
                (
                    INVALID
                    if row["derived"]["static_prediction"] == INVALID
                    or row["derived"]["behavior_status"] == "FAIL"
                    else (
                        VALID
                        if row["derived"]["behavior_status"] == "PASS"
                        and row["derived"]["static_prediction"] == VALID
                        else UNRESOLVED
                    )
                ),
            ),
        ),
        policy(
            "strong_static_plus_repository_tests",
            rows,
            lambda row: (
                ["preflight", "static_contract", "repository_tests"]
                if row["derived"]["static_prediction"] != INVALID
                else ["preflight", "static_contract"],
                (
                    INVALID
                    if row["derived"]["static_prediction"] == INVALID
                    or row["derived"]["repository_tests_status"] == "FAIL"
                    else (
                        VALID
                        if row["derived"]["repository_tests_status"] == "PASS"
                        and row["derived"]["static_prediction"] == VALID
                        else UNRESOLVED
                    )
                ),
            ),
        ),
        policy(
            "consumption_plus_behavior",
            rows,
            lambda row: (
                ["preflight", "consumption", "behavior_contract"]
                if row["derived"]["consumption_prediction"] != INVALID
                else ["preflight", "consumption"],
                (
                    INVALID
                    if row["derived"]["consumption_prediction"] == INVALID
                    or row["derived"]["behavior_status"] == "FAIL"
                    else (
                        VALID
                        if row["derived"]["behavior_status"] == "PASS"
                        and row["derived"]["consumption_prediction"] == VALID
                        else UNRESOLVED
                    )
                ),
            ),
        ),
        policy(
            "combined_short_circuit",
            rows,
            lambda row: (
                (
                    ["preflight", "static_contract"]
                    if row["derived"]["static_prediction"] == INVALID
                    else (
                        ["preflight", "static_contract", "consumption"]
                        if row["derived"]["consumption_prediction"] == INVALID
                        else [
                            "preflight",
                            "static_contract",
                            "consumption",
                            "behavior_contract",
                        ]
                    )
                ),
                row["derived"]["prediction"],
            ),
        ),
    ]
    payload = {
        "schema": "g3_real_action_policy_probe_v2_actual_module",
        "date": "2026-10-22",
        "evidence_identity": "GB10_ACTUAL_MODULE_BEHAVIOR_STATIC_AND_PAIRED_CONSUMPTION_ACTIONS",
        "environment": environment,
        "binding_contract": {
            "module": "actual worktree partridge/utilities.py",
            "manifest": "same worktree setup.py",
            "function": "detect_encoding",
            "paired_intervention": "same b'AB' input with legal target results latin-1 and utf-16-le",
            "reference_prediction_separation": True,
        },
        "rows": rows,
        "policies": policies,
        "timing_scope": {
            "kind": "one_observation_per_action_shared_receipt_policy_replay",
            "supports_stable_cost_ranking": False,
            "planner_status": "PAUSED",
        },
        "nonclaims": [
            "Manual controls and the audit counterexample are separated from natural parent/gold commits.",
            "Repository tests and the independent behavior contract are separate channels.",
            "Wall-clock timings include process startup and are not stable population cost estimates.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": rows, "policies": policies}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
