"""Run transparent reuse decisions before observing each new input regime."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable


VALID = "PASS"
INVALID = "FAIL"
UNRESOLVED = "UNRESOLVED"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_behavior_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("partridge_behavior_contract_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("behavior_contract_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_previous_status(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for row in payload["rows"]:
        behavior = row["actions"]["behavior_contract"].get("parsed") or {}
        result[row["id"]] = behavior.get("status", UNRESOLVED)
    return result


def choose_action(fingerprint: dict[str, Any]) -> tuple[str, str]:
    if not fingerprint.get("fingerprint_available"):
        return "DEFER", "missing_scope_fingerprint"
    if fingerprint.get("dependency_changed_since_old_evidence"):
        return "FULL_CHECK", "dependency_changed"
    if not fingerprint.get("input_regime_changed"):
        if fingerprint.get("exact_input_match"):
            if fingerprint.get("old_evidence_granularity") == "per_input":
                return "REUSE", "exact_input_and_dependency_unchanged"
            return "DEFER", "old_evidence_not_per_input"
        return "PARTIAL_CHECK", "same_regime_new_input"
    return "FULL_CHECK", "input_regime_changed"


def policy_decision(
    name: str,
    fingerprint: dict[str, Any],
    old_status: str,
) -> tuple[str, str]:
    if name == "never_revalidate":
        return "REUSE", "reuse_old_evidence"
    if name == "dependency_change_only":
        if fingerprint.get("dependency_changed_since_old_evidence"):
            return "FULL_CHECK", "dependency_changed"
        return "REUSE", "dependency_unchanged"
    if name == "exact_input_reuse_only":
        if (
            fingerprint.get("fingerprint_available")
            and fingerprint.get("exact_input_match")
            and fingerprint.get("old_evidence_granularity") == "per_input"
        ):
            return "REUSE", "exact_input_match"
        return "DEFER", (
            "old_evidence_not_per_input"
            if fingerprint.get("exact_input_match")
            else "input_not_exactly_reused"
        )
    if name == "always_full_check":
        return (
            ("FULL_CHECK", "always_revalidate_available_input")
            if fingerprint.get("fingerprint_available")
            else ("DEFER", "missing_scope_fingerprint")
        )
    return choose_action(fingerprint)[0], choose_action(fingerprint)[1]


def observe_batch(
    behavior_module: Any,
    candidate_module: Path,
    reference_module: Path,
    raw_inputs: list[bytes],
) -> dict[str, Any]:
    started = time.perf_counter()
    candidate, candidate_name = behavior_module.load_module(candidate_module)
    reference, reference_name = behavior_module.load_module(reference_module)
    rows = []
    try:
        for index, raw in enumerate(raw_inputs):
            expected = behavior_module.observe(reference, raw)
            actual = behavior_module.observe(candidate, raw)
            rows.append(
                {
                    "index": index,
                    "bytes": len(raw),
                    "reference": expected,
                    "candidate": actual,
                    "pass": (
                        expected["error"] is None
                        and actual["error"] is None
                        and actual["decoded_text"] == expected["decoded_text"]
                    ),
                }
            )
    finally:
        sys.modules.pop(candidate_name, None)
        sys.modules.pop(reference_name, None)
    return {
        "status": VALID if rows and all(row["pass"] for row in rows) else INVALID,
        "probe_count": len(rows),
        "mismatch_count": sum(not row["pass"] for row in rows),
        "wall_clock_seconds": round(time.perf_counter() - started, 6),
        "rows": rows,
    }


def build_scenarios(
    behavior_module: Any,
    fixture_root: Path,
) -> list[dict[str, Any]]:
    fixtures = behavior_module.select_fixtures(fixture_root, 24)
    same = fixtures[0]
    partial = fixtures[1:4]
    short_inputs = [b"abc\n", b"caf\xe9\n", b"caf\xc3\xa9\n"]
    return [
        {
            "scenario_id": "unchanged_exact_fixture",
            "condition_class": "completely_unchanged",
            "fingerprint": {
                "fingerprint_available": True,
                "dependency_changed_since_old_evidence": False,
                "input_regime_changed": False,
                "exact_input_match": True,
                "old_evidence_granularity": "per_input",
            },
            "action_inputs": [same.read_bytes()],
            "hidden_inputs": [same.read_bytes()],
            "input_description": str(same.relative_to(fixture_root)),
        },
        {
            "scenario_id": "same_regime_new_fixtures",
            "condition_class": "different_inputs_within_scope",
            "fingerprint": {
                "fingerprint_available": True,
                "dependency_changed_since_old_evidence": False,
                "input_regime_changed": False,
                "exact_input_match": False,
                "old_evidence_granularity": "aggregate",
            },
            "action_inputs": [path.read_bytes() for path in partial],
            "hidden_inputs": [path.read_bytes() for path in partial],
            "input_description": ",".join(
                str(path.relative_to(fixture_root)) for path in partial
            ),
        },
        {
            "scenario_id": "short_input_regime",
            "condition_class": "condition_changed_result_may_change",
            "fingerprint": {
                "fingerprint_available": True,
                "dependency_changed_since_old_evidence": False,
                "input_regime_changed": True,
                "exact_input_match": False,
                "old_evidence_granularity": "aggregate",
            },
            "action_inputs": short_inputs,
            "hidden_inputs": short_inputs,
            "input_description": "short-byte-regime",
        },
        {
            "scenario_id": "missing_scope_fingerprint",
            "condition_class": "insufficient_visible_evidence",
            "fingerprint": {
                "fingerprint_available": False,
                "dependency_changed_since_old_evidence": False,
                "input_regime_changed": False,
                "exact_input_match": False,
                "old_evidence_granularity": "none",
            },
            "action_inputs": [],
            "hidden_inputs": [],
            "input_description": "unavailable",
        },
    ]


def execute_policy(
    policy_name: str,
    cases: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    behavior_module: Any,
    reference_module: Path,
    previous_status: dict[str, str],
) -> dict[str, Any]:
    rows = []
    for case in cases:
        for scenario in scenarios:
            old_evidence_started = time.perf_counter()
            old_evidence = (
                observe_batch(
                    behavior_module,
                    case["module"],
                    reference_module,
                    scenario["hidden_inputs"],
                )
                if scenario["scenario_id"] == "unchanged_exact_fixture"
                else None
            )
            old_evidence_wall = round(time.perf_counter() - old_evidence_started, 6)
            policy_old_status = (
                old_evidence["status"]
                if old_evidence is not None
                else previous_status[case["id"]]
            )
            action, reason = policy_decision(
                policy_name, scenario["fingerprint"], policy_old_status
            )
            hidden_started = time.perf_counter()
            hidden = (
                observe_batch(
                    behavior_module,
                    case["module"],
                    reference_module,
                    scenario["hidden_inputs"],
                )
                if scenario["hidden_inputs"]
                else {"status": UNRESOLVED, "probe_count": 0, "mismatch_count": 0}
            )
            hidden_wall = round(time.perf_counter() - hidden_started, 6)
            if action == "REUSE":
                decision = policy_old_status
                observed = {
                    "status": decision,
                    "probe_count": 0,
                    "mismatch_count": 0,
                    "wall_clock_seconds": 0.0,
                    "rows": [],
                }
            elif action == "DEFER":
                decision = UNRESOLVED
                observed = {
                    "status": UNRESOLVED,
                    "probe_count": 0,
                    "mismatch_count": 0,
                    "wall_clock_seconds": 0.0,
                    "rows": [],
                }
            else:
                observed = observe_batch(
                    behavior_module,
                    case["module"],
                    reference_module,
                    scenario["action_inputs"],
                )
                decision = observed["status"]
            expected = hidden["status"]
            if decision == UNRESOLVED:
                outcome = "ABSTAIN"
            elif expected == UNRESOLVED:
                outcome = "UNRESOLVED_REFERENCE"
            elif decision == expected:
                outcome = "CORRECT"
            elif decision == VALID:
                outcome = "FALSE_ACCEPT"
            else:
                outcome = "FALSE_REJECT"
            rows.append(
                {
                    "candidate_id": case["id"],
                    "scenario_id": scenario["scenario_id"],
                    "condition_class": scenario["condition_class"],
                    "input_description": scenario["input_description"],
                    "old_evidence_status": previous_status[case["id"]],
                    "policy_old_status": policy_old_status,
                    "old_evidence_granularity": scenario["fingerprint"].get(
                        "old_evidence_granularity"
                    ),
                    "old_evidence_wall_clock_seconds": old_evidence_wall,
                    "action": action,
                    "reason": reason,
                    "decision": decision,
                    "hidden_outcome": expected,
                    "outcome": outcome,
                    "observed_action": observed,
                    "hidden_evaluation_wall_clock_seconds": hidden_wall,
                }
            )
    counts = {
        key: sum(row["outcome"] == key for row in rows)
        for key in ("CORRECT", "FALSE_ACCEPT", "FALSE_REJECT", "ABSTAIN", "UNRESOLVED_REFERENCE")
    }
    return {
        "policy": policy_name,
        "rows": rows,
        "metrics": {
            **counts,
            "n": len(rows),
            "action_wall_clock_seconds": round(
                sum(float(row["observed_action"]["wall_clock_seconds"]) for row in rows), 6
            ),
            "probe_count": sum(int(row["observed_action"]["probe_count"]) for row in rows),
            "action_count": sum(row["action"] != "REUSE" for row in rows),
            "probe_action_count": sum(
                row["action"] in {"PARTIAL_CHECK", "FULL_CHECK"} for row in rows
            ),
            "defer_count": sum(row["action"] == "DEFER" for row in rows),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree-root", type=Path, required=True)
    parser.add_argument("--behavior-contract", type=Path, required=True)
    parser.add_argument("--previous-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    behavior_module = load_behavior_module(args.behavior_contract.resolve())
    worktree_root = args.worktree_root.resolve()
    reference_module = (worktree_root / "partridge_parent/partridge/utilities.py").resolve()
    fixture_root = (worktree_root / "partridge_parent/tests/fixtures").resolve()
    cases = [
        {"id": "partridge_parent", "module": worktree_root / "partridge_parent/partridge/utilities.py"},
        {"id": "partridge_gold", "module": worktree_root / "partridge_gold/partridge/utilities.py"},
        {"id": "partridge_source_fallback", "module": worktree_root / "partridge_source_fallback/partridge/utilities.py"},
        {"id": "partridge_alias", "module": worktree_root / "partridge_alias/partridge/utilities.py"},
        {"id": "partridge_audit_counterexample", "module": worktree_root / "partridge_audit_counterexample/partridge/utilities.py"},
    ]
    previous_status = load_previous_status(args.previous_results.resolve())
    scenarios = build_scenarios(behavior_module, fixture_root)
    policies = [
        execute_policy(name, cases, scenarios, behavior_module, reference_module, previous_status)
        for name in (
            "never_revalidate",
            "dependency_change_only",
            "exact_input_reuse_only",
            "scope_policy",
            "always_full_check",
        )
    ]
    payload = {
        "schema": "reuse_policy_development_experiment_v1",
        "date": "2026-10-23",
        "question": (
            "Before observing a new input regime, can a transparent scope policy "
            "choose REUSE/PARTIAL_CHECK/FULL_CHECK/DEFER without increasing false transfer?"
        ),
        "evidence_identity": "DEV_ONLY_REAL_MODULE_OBSERVATIONS_WITH_HIDDEN_OUTCOME_EVALUATION",
        "reference_module": str(reference_module),
        "reference_module_sha256": sha256_file(reference_module),
        "candidate_bindings": [
            {
                "id": case["id"],
                "module": str(case["module"]),
                "module_sha256": sha256_file(case["module"]),
            }
            for case in cases
        ],
        "decision_information": [
            "old evidence status",
            "dependency identity delta",
            "input regime fingerprint",
            "exact input match flag",
        ],
        "scenarios": [
            {
                "scenario_id": scenario["scenario_id"],
                "condition_class": scenario["condition_class"],
                "fingerprint": scenario["fingerprint"],
                "input_description": scenario["input_description"],
            }
            for scenario in scenarios
        ],
        "policies": policies,
        "timing_scope": {
            "kind": "development_single_run_per_action",
            "hidden_evaluation_cost_excluded_from_policy_cost": True,
            "supports_stable_cost_ranking": False,
        },
        "nonclaims": [
            "The 20 transitions are development scenarios over five candidates, not 20 natural families.",
            "Parent-derived decoded text is the independent behavioral reference for this probe.",
            "The probe measures evidence reuse decisions and verification cost, not repair success or learned memory.",
            "A qualified mechanism still requires a second natural module and a real downstream outcome benefit.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"policies": policies}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
