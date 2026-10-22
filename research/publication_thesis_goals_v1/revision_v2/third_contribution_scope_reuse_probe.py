"""Low-cost qualification probe for scope-aware reuse of behavioral evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["id"]: row for row in payload["rows"]}


def behavior_status(row: dict[str, Any]) -> str:
    parsed = row["actions"]["behavior_contract"].get("parsed") or {}
    return parsed.get("status", "ERROR")


def policy_metrics(
    name: str,
    rows: list[dict[str, Any]],
    predictor: Any,
) -> dict[str, Any]:
    correct = false_transfer = abstain = unnecessary_revalidation = 0
    decisions: dict[str, str] = {}
    for row in rows:
        decision, revalidated = predictor(row)
        decisions[row["id"]] = decision
        expected = row["short_observation"]
        if decision == "ABSTAIN":
            abstain += 1
        elif decision == expected:
            correct += 1
            unnecessary_revalidation += int(revalidated and row["fixture_observation"] == expected)
        else:
            false_transfer += 1
    return {
        "policy": name,
        "correct": correct,
        "false_transfer_or_error": false_transfer,
        "abstain": abstain,
        "unnecessary_revalidation_in_observed_equal_cases": unnecessary_revalidation,
        "n": len(rows),
        "decisions": decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-results", type=Path, required=True)
    parser.add_argument("--short-input-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture_rows = load_rows(args.fixture_results)
    short_rows = load_rows(args.short_input_results)
    shared = sorted(set(fixture_rows) & set(short_rows))
    rows = []
    for candidate_id in shared:
        fixture = fixture_rows[candidate_id]
        short = short_rows[candidate_id]
        rows.append(
            {
                "id": candidate_id,
                "kind": fixture["kind"],
                "reference": fixture["reference"],
                "fixture_observation": behavior_status(fixture),
                "short_observation": behavior_status(short),
                "fixture_behavior_wall_clock_seconds": fixture["actions"]["behavior_contract"][
                    "wall_clock_seconds"
                ],
                "short_behavior_wall_clock_seconds": short["actions"]["behavior_contract"][
                    "wall_clock_seconds"
                ],
                "dependency_changed_from_parent": candidate_id != "partridge_parent",
                "input_regime_changed": True,
            }
        )
    policies = [
        policy_metrics(
            "never_revalidate",
            rows,
            lambda row: (row["fixture_observation"], False),
        ),
        policy_metrics(
            "dependency_change_only",
            rows,
            lambda row: (
                row["short_observation"] if row["dependency_changed_from_parent"] else row["fixture_observation"],
                row["dependency_changed_from_parent"],
            ),
        ),
        policy_metrics(
            "exact_input_reuse_only",
            rows,
            lambda row: ("ABSTAIN", False),
        ),
        policy_metrics(
            "scope_fingerprint_dependency_and_input_regime",
            rows,
            lambda row: (
                row["short_observation"],
                row["dependency_changed_from_parent"] or row["input_regime_changed"],
            ),
        ),
        policy_metrics(
            "always_revalidate",
            rows,
            lambda row: (row["short_observation"], True),
        ),
    ]
    never = next(row for row in policies if row["policy"] == "never_revalidate")
    scope = next(
        row
        for row in policies
        if row["policy"] == "scope_fingerprint_dependency_and_input_regime"
    )
    dependency_only = next(
        row for row in policies if row["policy"] == "dependency_change_only"
    )
    scope_increment_identified = (
        scope["correct"] > dependency_only["correct"]
        or scope["unnecessary_revalidation_in_observed_equal_cases"]
        < dependency_only["unnecessary_revalidation_in_observed_equal_cases"]
    )
    if never["false_transfer_or_error"] > 0 and dependency_only["false_transfer_or_error"] == 0:
        qualification = (
            "TRANSPARENT_INVALIDATION_CANDIDATE_CONTINUE_SCOPE_METHOD_PAUSED"
        )
    else:
        qualification = "NOT_QUALIFIED_ON_CURRENT_PROBE"
    payload = {
        "schema": "third_contribution_scope_reuse_probe_v1",
        "date": "2026-10-22",
        "question": (
            "When conditions change, when can prior behavioral evidence be reused, "
            "and when does a transparent scope fingerprint need to trigger revalidation?"
        ),
        "evidence_identity": "DEV_ONLY_TWO_REGIME_MECHANISM_PROBE_WITH_REAL_MODULE_EXECUTION",
        "rows": rows,
        "policies": policies,
        "qualification": qualification,
        "scope_increment_identified": scope_increment_identified,
        "interpretation": (
            "Global evidence reuse can transfer a PASS from real repository fixtures "
            "to a short-input regime where the same module no longer matches the parent. "
            "Dependency-change invalidation already avoids that false transfer on this "
            "probe; the broader input-regime fingerprint adds no identified benefit. "
            "The next qualification case must change the input regime while keeping the "
            "dependency identity fixed."
        ),
        "nonclaims": [
            "This is a two-regime mechanism probe, not a natural distribution estimate.",
            "The probe does not establish a learned evidence-expiry policy or a third thesis contribution.",
            "The short-input diagnostics depend on current chardet/cchardet behavior and must be versioned.",
            "Scope-aware invalidation is paused because the simple dependency-change rule is sufficient on the current cases.",
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
