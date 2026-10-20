"""DEV_ONLY feedback-contract mechanism probe.

The script scores the same frozen selections under three feedback semantics and
applies one deterministic update rule. It does not use model or judge outputs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from active_evidence_probe import freeze
from probe_common import (
    PROTOCOL_VERSION,
    RESULT_DIR,
    contains_sufficient_set,
    covered_fact_ids,
    load_frozen_probe_inputs,
    write_json_atomic,
)


FEEDBACK_CONTRACTS = (
    "exact_match",
    "minimal_sufficient_set",
    "fact_coverage",
)


def scope_truth(
    selection: list[str],
    reference: dict[str, Any],
) -> bool:
    """Apply the frozen sufficiency plus scope-precision rule."""
    if not selection:
        return False
    allowed = set(reference["allowed_candidate_ids"])
    return contains_sufficient_set(
        selection, reference["minimal_sufficient_sets"]
    ) and set(selection).issubset(allowed)


def feedback_accepts(
    contract: str,
    selection: list[str],
    reference: dict[str, Any],
) -> bool:
    """Evaluate one feedback contract without coercing invalid selections."""
    if contract == "exact_match":
        selected = set(selection)
        return any(
            selected == set(candidate_set)
            for candidate_set in reference["minimal_sufficient_sets"]
        )
    if contract == "minimal_sufficient_set":
        return contains_sufficient_set(
            selection, reference["minimal_sufficient_sets"]
        )
    if contract == "fact_coverage":
        return len(covered_fact_ids(selection, reference["fact_atoms"])) == len(
            reference["fact_atoms"]
        )
    raise ValueError(f"Unknown feedback contract: {contract}")


def update_experience(
    contract: str,
    accepted: bool,
    selection: list[str],
    reference: dict[str, Any],
    revision_selection: list[str],
) -> dict[str, Any]:
    """Apply the frozen retain/revise/reject update rule."""
    if accepted:
        return {
            "status": "RETAIN",
            "post_update_selection": list(selection),
            "post_update_feedback": True,
            "update_reason": "The feedback contract accepted the proposed selection.",
        }

    selected = set(selection)
    allowed = set(reference["allowed_candidate_ids"])
    covered_any = bool(covered_fact_ids(selection, reference["fact_atoms"]))
    can_revise = (
        bool(selected)
        and selected.issubset(allowed)
        and covered_any
    )
    if can_revise:
        return {
            "status": "REVISE",
            "post_update_selection": list(revision_selection),
            "post_update_feedback": feedback_accepts(
                contract, revision_selection, reference
            ),
            "update_reason": (
                "Rejected selection contains only supported evidence and at least one "
                "covered fact; replace it with the first frozen minimal sufficient set."
            ),
        }
    return {
        "status": "REJECT",
        "post_update_selection": [],
        "post_update_feedback": False,
        "update_reason": (
            "No supported partial evidence remains under the frozen update rule."
        ),
    }


def run() -> None:
    """Score all frozen cases and write the mechanism-intervention result."""
    inputs, feedback_fixture = load_frozen_probe_inputs()
    tasks_by_id = {task["task_id"]: task for task in inputs["tasks"]}
    rows: list[dict[str, Any]] = []

    for case in feedback_fixture["cases"]:
        task = tasks_by_id[case["task_id"]]
        reference = task["reference"]
        selection = case["selection"]
        valid = scope_truth(selection, reference)
        covered = covered_fact_ids(selection, reference["fact_atoms"])
        case_row = {
            "case_id": case["case_id"],
            "task_id": case["task_id"],
            "ground_truth_class": case["ground_truth_class"],
            "description": case["description"],
            "selection": selection,
            "scope_valid": valid,
            "covered_fact_ids": covered,
            "fact_coverage": len(covered) / len(reference["fact_atoms"]),
            "contracts": {},
        }
        for contract in FEEDBACK_CONTRACTS:
            accepted = feedback_accepts(contract, selection, reference)
            update = update_experience(
                contract,
                accepted,
                selection,
                reference,
                case["revision_selection"],
            )
            case_row["contracts"][contract] = {
                "accepted": accepted,
                "update_status": update["status"],
                "post_update_selection": update["post_update_selection"],
                "post_update_feedback": update["post_update_feedback"],
                "update_reason": update["update_reason"],
                "false_negative_rejection": valid and not accepted,
                "false_positive_acceptance": not valid and accepted,
                "unnecessary_revision": valid and update["status"] == "REVISE",
                "unsupported_retention": (not valid)
                and update["status"] == "RETAIN",
            }
        rows.append(case_row)

    summary = []
    for contract in FEEDBACK_CONTRACTS:
        contract_rows = [row["contracts"][contract] for row in rows]
        summary.append(
            {
                "feedback_contract": contract,
                "accepted_count": sum(row["accepted"] for row in contract_rows),
                "false_negative_rejection_count": sum(
                    row["false_negative_rejection"] for row in contract_rows
                ),
                "false_positive_acceptance_count": sum(
                    row["false_positive_acceptance"] for row in contract_rows
                ),
                "unnecessary_revision_count": sum(
                    row["unnecessary_revision"] for row in contract_rows
                ),
                "unsupported_retention_count": sum(
                    row["unsupported_retention"] for row in contract_rows
                ),
                "update_status_counts": dict(
                    sorted(Counter(row["update_status"] for row in contract_rows).items())
                ),
            }
        )

    valid_alternatives = [
        row for row in rows if row["ground_truth_class"] == "VALID_ALTERNATIVE"
    ]
    unsupported_extras = [
        row for row in rows if row["ground_truth_class"] == "UNSUPPORTED_EXTRA"
    ]
    exact_false_negatives = sum(
        row["contracts"]["exact_match"]["false_negative_rejection"]
        for row in valid_alternatives
    )
    sufficient_unsupported_admissions = sum(
        row["contracts"]["minimal_sufficient_set"]["false_positive_acceptance"]
        for row in unsupported_extras
    )
    coverage_unsupported_admissions = sum(
        row["contracts"]["fact_coverage"]["false_positive_acceptance"]
        for row in unsupported_extras
    )

    result = {
        "schema": "feedback_contract_probe_result_v1",
        "status": "DEV_ONLY_CONTROLLED_MECHANISM_PROBE_COMPLETED",
        "evidence_class": "DETERMINISTIC_MECHANISM_INTERVENTION",
        "protocol_version": PROTOCOL_VERSION,
        "scientific_scope": (
            "A controlled intervention on feedback semantics over frozen candidate "
            "selections. This is not a natural experiment, real-history claim, "
            "validated learning method, or language-model judgment."
        ),
        "resource_accounting": {
            "model_requests": 0,
            "judge_requests": 0,
            "training_runs": 0,
            "network_calls": 0,
        },
        "feedback_contracts": list(FEEDBACK_CONTRACTS),
        "case_count": len(rows),
        "scope_valid_case_count": sum(row["scope_valid"] for row in rows),
        "summary": summary,
        "targeted_findings": {
            "valid_alternative_case_count": len(valid_alternatives),
            "exact_match_false_negative_updates_on_valid_alternatives": (
                exact_false_negatives
            ),
            "unsupported_extra_case_count": len(unsupported_extras),
            "minimal_sufficient_set_unsupported_admissions": (
                sufficient_unsupported_admissions
            ),
            "fact_coverage_unsupported_admissions": (
                coverage_unsupported_admissions
            ),
        },
        "by_case": rows,
        "interpretation_limits": [
            "The cases are frozen deterministic fixtures, not sampled model trajectories.",
            "Revision is computed with reference-informed fixtures and is not a learned repair method.",
            "The probe identifies contract failure modes; it does not establish downstream task benefit.",
            "A production feedback contract would also need adversarial, ambiguity and human-semantic review.",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULT_DIR / "feedback_contract_probe_results.json"
    write_json_atomic(output_path, result)
    print(f"Wrote {output_path}")


def parse_args() -> argparse.Namespace:
    """Parse the two-command probe interface required by the sprint contract."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true", help="Freeze inputs before run")
    group.add_argument("--run", action="store_true", help="Run frozen simulation")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace local fixtures during an explicit versioned repair",
    )
    return parser.parse_args()


def main() -> None:
    """Dispatch freeze or run mode."""
    args = parse_args()
    if args.freeze:
        freeze(replace=args.replace)
    else:
        if args.replace:
            raise ValueError("--replace is only valid with --freeze")
        run()


if __name__ == "__main__":
    main()
