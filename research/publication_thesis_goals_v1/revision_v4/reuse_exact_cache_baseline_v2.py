"""Replay an exact-cache plus miss-revalidation baseline from frozen receipts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(decision: str, expected: str) -> str:
    if decision == "UNRESOLVED":
        return "ABSTAIN"
    if decision == expected:
        return "CORRECT"
    if decision == "PASS":
        return "FALSE_ACCEPT"
    return "FALSE_REJECT"


def replay(results: dict[str, Any]) -> dict[str, Any]:
    policies = {row["policy"]: row for row in results["policies"]}
    scope = policies["scope_policy"]
    full = policies["always_full_check"]
    scenarios = {row["scenario_id"]: row for row in results["scenarios"]}
    full_rows = {
        (row["candidate_id"], row["scenario_id"]): row for row in full["rows"]
    }
    rows = []
    for scope_row in scope["rows"]:
        fingerprint = scenarios[scope_row["scenario_id"]]["fingerprint"]
        if not fingerprint["fingerprint_available"]:
            action, decision, probes = "DEFER", "UNRESOLVED", 0
        elif (
            not fingerprint["dependency_changed_since_old_evidence"]
            and fingerprint["exact_input_match"]
            and fingerprint.get("old_evidence_granularity") == "per_input"
        ):
            action = "REUSE"
            decision = scope_row["policy_old_status"]
            probes = 0
        else:
            full_row = full_rows[
                (scope_row["candidate_id"], scope_row["scenario_id"])
            ]
            action = "FULL_CHECK"
            decision = full_row["decision"]
            probes = int(full_row["observed_action"]["probe_count"])
        rows.append({
            "candidate_id": scope_row["candidate_id"],
            "scenario_id": scope_row["scenario_id"],
            "action": action,
            "decision": decision,
            "outcome": classify(decision, scope_row["hidden_outcome"]),
            "probe_count": probes,
        })
    scope_decisions = [row["decision"] for row in scope["rows"]]
    cache_decisions = [row["decision"] for row in rows]
    return {
        "schema": "reuse_exact_cache_baseline_v2",
        "date": "2026-10-23",
        "evidence_identity": "POST_HOC_RECOMBINATION_OF_FROZEN_ACTION_RECEIPTS_NOT_FRESH_MODULE_EXECUTION",
        "policy": (
            "Defer when fingerprint is missing; reuse only exact-input per-input "
            "evidence with unchanged dependency; otherwise full-check the miss."
        ),
        "counts": dict(Counter(row["outcome"] for row in rows)),
        "probe_count": sum(row["probe_count"] for row in rows),
        "same_decisions_as_scope_policy": scope_decisions == cache_decisions,
        "rows": rows,
        "nonclaims": [
            "This is not a new real-module run or natural-family estimate.",
            "It does not establish a general cache method contribution.",
            "It explains the five-probe saving through exact-input reuse only.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = replay(load(args.results))
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "counts": output["counts"],
        "probe_count": output["probe_count"],
        "same_decisions_as_scope_policy": output["same_decisions_as_scope_policy"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
