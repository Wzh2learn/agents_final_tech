"""Post-hoc deterministic feedback-contract analysis for real B0 V2 traces.

The script reads only the four authorized finrank_dev evidence files. It makes
no model, judge, training, service or network call and does not modify shared
generation accounting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
FINRANK_DIR = SCRIPT_DIR.parents[1] / "finrank_dev"
B0_RESULT_PATH = (
    FINRANK_DIR / "results" / "B0_V2_ENGINEERING_FIX" / "B0_RESULT.json"
)
REFERENCES_PATH = FINRANK_DIR / "REFERENCES_V1.json"
C1_RETURN_PATH = FINRANK_DIR / "C1_RETURN.md"
C2_ROOT_CAUSE_PATH = FINRANK_DIR / "C2_ROOT_CAUSE.md"
FIXTURE_DIR = SCRIPT_DIR / "fixture"
FIXTURE_PATH = FIXTURE_DIR / "real_trace_feedback_fixture.json"
RECEIPT_PATH = FIXTURE_DIR / "FREEZE_RECEIPT.json"
RESULT_PATH = SCRIPT_DIR / "REAL_TRACE_FEEDBACK_ANALYSIS.json"

SCHEMA_VERSION = "real_trace_feedback_posthoc_v1"
EXPECTED_RUN_ID = "FINRANK_C1_B0_V2_ENGINEERING_FIX_20261020T031024.100294Z"
EXPECTED_BUNDLE_SHA256 = (
    "be910bc82200466c5218912943ff5b896da5c734ecefe5f8bdd9acc36e7d08ca"
)
EXPECTED_TASK_IDS = (
    "ESD_001",
    "ESD_002",
    "ESD_003",
    "ESD_004",
    "ESD_006",
    "ESD_010",
    "ESD_012",
)
ESD_006_C2_REQUIRED_ATOMS = (
    "derived_gross_profit",
    "derived_gross_margin",
)


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object and fail loudly on malformed data."""
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize JSON deterministically."""
    return (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def write_json_atomic(path: Path, payload: Any) -> None:
    """Atomically write a JSON object."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent, suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def sha256_file(path: Path) -> str:
    """Return a lowercase SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path) -> str:
    """Return an explicit path relative to this analysis directory."""
    return Path(os.path.relpath(path, SCRIPT_DIR)).as_posix()


def normalize_candidate_ids(value: Any) -> list[str]:
    """Normalize source optional_redundant values represented as string/list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ValueError(f"Invalid candidate IDs: {value!r}")


def contains_sufficient_set(
    selected_ids: list[str],
    sufficient_sets: list[list[str]],
) -> bool:
    """Return whether selection contains any frozen minimal sufficient set."""
    selected = set(selected_ids)
    return any(set(required).issubset(selected) for required in sufficient_sets)


def matched_atom_names(match_block: dict[str, Any]) -> set[str]:
    """Extract atom names already matched by the frozen B0 checker."""
    values = match_block.get("matched_atoms", [])
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise ValueError("Invalid matched_atoms")
    return set(values)


def validate_sources(
    b0_result: dict[str, Any],
    references: dict[str, Any],
) -> None:
    """Validate the narrow evidence contract before creating a fixture."""
    if b0_result.get("run_id") != EXPECTED_RUN_ID:
        raise ValueError("Unexpected B0 run identity")
    if b0_result.get("bundle_sha256") != EXPECTED_BUNDLE_SHA256:
        raise ValueError("Unexpected B0 bundle identity")
    if b0_result.get("generation_requests") != 14:
        raise ValueError("Expected 14 real generation requests")
    if b0_result.get("success_count") != 1:
        raise ValueError("Expected one B0 success")
    if b0_result.get("non_success_count") != 6:
        raise ValueError("Expected six B0 non-successes")
    if references.get("human_confirmed") is not False:
        raise ValueError("REFERENCES_V1 must remain AI-assisted and unconfirmed")
    task_ids = tuple(result["task_id"] for result in b0_result["results"])
    if task_ids != EXPECTED_TASK_IDS:
        raise ValueError(f"Unexpected B0 task order: {task_ids!r}")


def build_fixture() -> dict[str, Any]:
    """Extract only the fields needed for the post-hoc mechanism analysis."""
    b0_result = read_json(B0_RESULT_PATH)
    references = read_json(REFERENCES_PATH)
    validate_sources(b0_result, references)
    reference_by_id = {task["task_id"]: task for task in references["tasks"]}

    traces = []
    for result in b0_result["results"]:
        task_id = result["task_id"]
        reference = reference_by_id[task_id]
        minimal_sets = [list(value) for value in reference["minimal_sufficient_sets"]]
        optional_redundant = normalize_candidate_ids(reference["optional_redundant"])
        allowed_ids = sorted(
            set(optional_redundant).union(*map(set, minimal_sets))
        )
        required_atoms_v1 = [atom["name"] for atom in reference["answer_atoms"]]
        required_atoms_sensitivity = (
            list(ESD_006_C2_REQUIRED_ATOMS)
            if task_id == "ESD_006"
            else list(required_atoms_v1)
        )
        traces.append(
            {
                "task_id": task_id,
                "source_cluster_id": result["source_cluster_id"],
                "real_trace": {
                    "run_id": b0_result["run_id"],
                    "bundle_sha256": b0_result["bundle_sha256"],
                    "outcome": result["outcome"],
                    "error_class": result["error_class"],
                    "plan_contract_valid": result["plan_contract_valid"],
                    "tool_execution_success": result["tool_execution_success"],
                    "consume_contract_valid": result["consume_contract_valid"],
                    "plan_candidate_ids": list(
                        result["plan"]["evidence_candidate_ids"]
                    ),
                    "consume_candidate_ids": list(
                        result["consume"]["used_candidate_ids"]
                    ),
                    "answer_status": result["consume"]["answer_status"],
                    "facts": list(result["consume"]["facts"]),
                    "answer_reference_match_v1": {
                        "match": result["answer_reference_match"]["match"],
                        "matched_atoms": list(
                            result["answer_reference_match"]["matched_atoms"]
                        ),
                        "missing_atoms": list(
                            result["answer_reference_match"]["missing_atoms"]
                        ),
                    },
                    "answer_tool_consistency": {
                        "consistent": result["answer_tool_consistency"][
                            "consistent"
                        ],
                        "cited_absent_ids": list(
                            result["answer_tool_consistency"]["cited_absent_ids"]
                        ),
                        "unsupported_numeric_values": list(
                            result["answer_tool_consistency"][
                                "unsupported_numeric_values"
                            ]
                        ),
                    },
                },
                "ai_development_reference": {
                    "human_confirmed": False,
                    "minimal_sufficient_sets": minimal_sets,
                    "optional_redundant": optional_redundant,
                    "allowed_candidate_ids": allowed_ids,
                    "required_answer_atoms_v1": required_atoms_v1,
                    "required_answer_atoms_c2_sensitivity": (
                        required_atoms_sensitivity
                    ),
                    "adjudication_note": reference["adjudication_note"],
                },
            }
        )

    return {
        "schema": "real_trace_feedback_fixture_v1",
        "status": "POSTHOC_DEVELOPMENT_INTERVENTION_FIXTURE",
        "schema_version": SCHEMA_VERSION,
        "evidence_identity": {
            "real_model_trace": (
                "B0_V2_ENGINEERING_FIX plan/consume outputs and frozen checker "
                "fields recorded in B0_RESULT.json."
            ),
            "ai_development_reference": (
                "REFERENCES_V1.json; human_confirmed=false and not human gold."
            ),
            "posthoc_feedback_intervention": (
                "C4 deterministic contract scoring applied after observing B0; "
                "not a feedback channel available to the actor."
            ),
        },
        "source_sha256": {
            relative_path(path): sha256_file(path)
            for path in (
                B0_RESULT_PATH,
                REFERENCES_PATH,
                C1_RETURN_PATH,
                C2_ROOT_CAUSE_PATH,
            )
        },
        "contract_definitions": {
            "exact_match": (
                "consume selection equals one minimal set and all V1 answer atoms match"
            ),
            "minimal_sufficient_set": (
                "consume selection contains one minimal set; answer correctness ignored"
            ),
            "fact_coverage": (
                "all V1 answer atoms match; evidence precision ignored"
            ),
            "set_valued_sufficiency_scope_precision": (
                "consume contains one minimal set and uses only minimal/optional IDs"
            ),
            "composite_trace": (
                "set_valued_sufficiency_scope_precision and all V1 answer atoms match"
            ),
            "composite_trace_c2_sensitivity": (
                "same as composite_trace, with ESD_006 required atoms reduced to "
                "derived_gross_profit and derived_gross_margin per C2_ROOT_CAUSE"
            ),
        },
        "traces": traces,
    }


def freeze(replace: bool = False) -> None:
    """Freeze the post-hoc input fixture and source hashes."""
    if RECEIPT_PATH.exists() and not replace:
        raise FileExistsError("Fixture already frozen; use explicit --replace")
    fixture = build_fixture()
    write_json_atomic(FIXTURE_PATH, fixture)
    receipt = {
        "schema": "real_trace_feedback_freeze_receipt_v1",
        "schema_version": SCHEMA_VERSION,
        "fixture_sha256": sha256_file(FIXTURE_PATH),
        "source_sha256": fixture["source_sha256"],
        "trace_count": len(fixture["traces"]),
        "real_generation_requests_observed": 14,
        "new_generation_requests": 0,
    }
    write_json_atomic(RECEIPT_PATH, receipt)
    print(f"Froze {receipt['trace_count']} real traces")


def verify_freeze() -> dict[str, Any]:
    """Hash-verify the frozen fixture before analysis."""
    receipt = read_json(RECEIPT_PATH)
    actual_hash = sha256_file(FIXTURE_PATH)
    if actual_hash != receipt["fixture_sha256"]:
        raise ValueError("Frozen fixture hash mismatch")
    for source_name, expected_hash in receipt["source_sha256"].items():
        source_path = (SCRIPT_DIR / source_name).resolve()
        if sha256_file(source_path) != expected_hash:
            raise ValueError(f"Source hash mismatch: {source_name}")
    return receipt


def evidence_contract_accepts(
    contract: str,
    trace: dict[str, Any],
) -> bool:
    """Evaluate an evidence-only contract on the actual consume selection."""
    selection = trace["real_trace"]["consume_candidate_ids"]
    reference = trace["ai_development_reference"]
    sufficient = contains_sufficient_set(
        selection, reference["minimal_sufficient_sets"]
    )
    if contract == "minimal_sufficient_set":
        return sufficient
    if contract == "set_valued_sufficiency_scope_precision":
        return sufficient and set(selection).issubset(
            set(reference["allowed_candidate_ids"])
        )
    raise ValueError(f"Not an evidence-only contract: {contract}")


def answer_contract_accepts(
    contract: str,
    trace: dict[str, Any],
    c2_sensitivity: bool = False,
) -> bool:
    """Evaluate answer atom coverage under V1 or the labeled C2 sensitivity."""
    reference = trace["ai_development_reference"]
    required = (
        reference["required_answer_atoms_c2_sensitivity"]
        if c2_sensitivity
        else reference["required_answer_atoms_v1"]
    )
    matched = matched_atom_names(
        trace["real_trace"]["answer_reference_match_v1"]
    )
    if contract in {"fact_coverage", "composite_trace"}:
        return set(required).issubset(matched)
    raise ValueError(f"Not an answer contract: {contract}")


def contract_accepts(
    contract: str,
    trace: dict[str, Any],
) -> bool:
    """Evaluate one of the fixed feedback contracts on one real trace."""
    selection = trace["real_trace"]["consume_candidate_ids"]
    reference = trace["ai_development_reference"]
    exact_selection = any(
        set(selection) == set(candidate_set)
        for candidate_set in reference["minimal_sufficient_sets"]
    )
    if contract == "exact_match":
        return exact_selection and answer_contract_accepts(
            "fact_coverage", trace
        )
    if contract == "minimal_sufficient_set":
        return evidence_contract_accepts(contract, trace)
    if contract == "fact_coverage":
        return answer_contract_accepts(contract, trace)
    if contract == "set_valued_sufficiency_scope_precision":
        return evidence_contract_accepts(contract, trace)
    if contract == "composite_trace":
        return evidence_contract_accepts(
            "set_valued_sufficiency_scope_precision", trace
        ) and answer_contract_accepts("fact_coverage", trace)
    if contract == "composite_trace_c2_sensitivity":
        return evidence_contract_accepts(
            "set_valued_sufficiency_scope_precision", trace
        ) and answer_contract_accepts(
            "fact_coverage", trace, c2_sensitivity=True
        )
    raise ValueError(f"Unknown contract: {contract}")


def disposition(
    contract: str,
    accepted: bool,
    trace: dict[str, Any],
) -> dict[str, Any]:
    """Apply a deterministic retain/revise/reject rule to the real trace."""
    task_id = trace["task_id"]
    selection = trace["real_trace"]["consume_candidate_ids"]
    reference = trace["ai_development_reference"]
    allowed = set(reference["allowed_candidate_ids"])
    supported_selected = sorted(set(selection) & allowed)
    evidence_valid = contract_accepts(
        "set_valued_sufficiency_scope_precision", trace
    )
    answer_v1_valid = answer_contract_accepts("fact_coverage", trace)
    answer_c2_valid = answer_contract_accepts(
        "fact_coverage", trace, c2_sensitivity=True
    )

    retained_components = [
        "real_plan_trace",
        "real_tool_execution",
        "real_consume_trace",
        "real_outcome_record",
    ]
    if accepted:
        if task_id == "ESD_006" and not answer_v1_valid and answer_c2_valid:
            return {
                "status": "RETAIN",
                "qualification": "RETAIN_AFTER_REFERENCE_REVISION",
                "retained_components": retained_components,
                "rejected_components": ["reference_v1_required_operand_atoms"],
                "revision_target": "REFERENCE_SCOPE_V1_TO_C2_SENSITIVITY",
                "reason": (
                    "Retain only under the labeled C2 answer-scope sensitivity; "
                    "REFERENCES_V1 itself remains unchanged and needs revision "
                    "before any scientific scoring rerun."
                ),
            }
        return {
            "status": "RETAIN",
            "qualification": "RETAIN_AS_RECORDED",
            "retained_components": retained_components,
            "rejected_components": [],
            "revision_target": None,
            "reason": "The post-hoc contract accepts the recorded trace.",
        }

    if task_id == "ESD_006" and answer_c2_valid and not answer_v1_valid:
        return {
            "status": "REVISE",
            "qualification": "REVISE_REFERENCE",
            "retained_components": retained_components,
            "rejected_components": ["reference_v1_required_operand_atoms"],
            "revision_target": "REFERENCE_SCOPE_V1_TO_C2_SENSITIVITY",
            "reason": (
                "The real output answers the requested derived values; C2 "
                "identifies the two V1 operand atoms as over-required."
            ),
        }
    if evidence_valid and not answer_v1_valid:
        return {
            "status": "REVISE",
            "qualification": "REVISE_TRACE",
            "retained_components": [
                *retained_components,
                "supported_evidence_selection",
            ],
            "rejected_components": ["incomplete_or_wrong_answer_facts"],
            "revision_target": "ANSWER_FACTS",
            "reason": "Evidence is sufficient and precise, but answer atoms are incomplete.",
        }
    if supported_selected:
        return {
            "status": "REVISE",
            "qualification": "REVISE_TRACE",
            "retained_components": [
                *retained_components,
                "partial_supported_evidence",
            ],
            "rejected_components": [
                "current_complete_selection_claim",
                "current_answer_claim",
            ],
            "revision_target": "EVIDENCE_SELECTION_AND_ANSWER_FACTS",
            "reason": "Only part of the sufficient evidence was used and the answer is incomplete.",
        }
    return {
        "status": "REJECT",
        "qualification": "REJECT_CURRENT_CLAIM",
        "retained_components": retained_components,
        "rejected_components": [
            "current_selected_evidence_claim",
            "current_answer_claim",
        ],
        "revision_target": None,
        "reason": (
            "No selected candidate is supported by the development reference; "
            "retain only the real failure record."
        ),
    }


def run() -> None:
    """Compute the post-hoc contract comparison and write machine-readable output."""
    verify_freeze()
    fixture = read_json(FIXTURE_PATH)
    contracts = (
        "exact_match",
        "minimal_sufficient_set",
        "fact_coverage",
        "set_valued_sufficiency_scope_precision",
        "composite_trace",
        "composite_trace_c2_sensitivity",
    )
    per_trace = []
    for trace in fixture["traces"]:
        reference = trace["ai_development_reference"]
        selection = trace["real_trace"]["consume_candidate_ids"]
        plan_selection = trace["real_trace"]["plan_candidate_ids"]
        matched = matched_atom_names(
            trace["real_trace"]["answer_reference_match_v1"]
        )
        required_v1 = set(reference["required_answer_atoms_v1"])
        required_sensitivity = set(
            reference["required_answer_atoms_c2_sensitivity"]
        )
        contract_rows = {}
        for contract in contracts:
            accepted = contract_accepts(contract, trace)
            contract_rows[contract] = {
                "accepted": accepted,
                **disposition(contract, accepted, trace),
            }
        per_trace.append(
            {
                "task_id": trace["task_id"],
                "source_cluster_id": trace["source_cluster_id"],
                "real_outcome": trace["real_trace"]["outcome"],
                "plan_selection": plan_selection,
                "consume_selection": selection,
                "plan_contains_sufficient_set": contains_sufficient_set(
                    plan_selection, reference["minimal_sufficient_sets"]
                ),
                "consume_contains_sufficient_set": contains_sufficient_set(
                    selection, reference["minimal_sufficient_sets"]
                ),
                "consume_scope_precision": set(selection).issubset(
                    set(reference["allowed_candidate_ids"])
                ),
                "plan_has_unchecked_extra_ids": sorted(
                    set(plan_selection)
                    - set(reference["allowed_candidate_ids"])
                ),
                "answer_atoms_matched_v1": sorted(matched & required_v1),
                "answer_atoms_missing_v1": sorted(required_v1 - matched),
                "answer_coverage_v1": len(matched & required_v1)
                / len(required_v1),
                "answer_coverage_c2_sensitivity": len(
                    matched & required_sensitivity
                )
                / len(required_sensitivity),
                "contracts": contract_rows,
            }
        )

    summaries = []
    for contract in contracts:
        rows = [row["contracts"][contract] for row in per_trace]
        summaries.append(
            {
                "contract": contract,
                "accepted_count": sum(row["accepted"] for row in rows),
                "disposition_counts": dict(
                    sorted(Counter(row["status"] for row in rows).items())
                ),
                "accepted_task_ids": [
                    row["task_id"]
                    for row in per_trace
                    if row["contracts"][contract]["accepted"]
                ],
            }
        )

    non_success_rows = [
        row for row in per_trace if row["real_outcome"] == "NON_SUCCESS"
    ]
    sensitivity_actions = [
        {
            "task_id": row["task_id"],
            "status": row["contracts"]["composite_trace_c2_sensitivity"][
                "status"
            ],
            "qualification": row["contracts"][
                "composite_trace_c2_sensitivity"
            ]["qualification"],
            "revision_target": row["contracts"][
                "composite_trace_c2_sensitivity"
            ]["revision_target"],
        }
        for row in non_success_rows
    ]
    result = {
        "schema": "real_trace_feedback_analysis_v1",
        "schema_version": SCHEMA_VERSION,
        "status": "POSTHOC_DEV_ONLY_ANALYSIS_COMPLETED",
        "scientific_scope": (
            "Deterministic post-hoc feedback intervention over seven real B0 V2 "
            "plan/consume traces. References are AI-assisted development labels, "
            "not human gold. This is not an experience-learning effect."
        ),
        "resource_accounting": {
            "real_requests_observed": 14,
            "new_model_requests": 0,
            "judge_requests": 0,
            "training_runs": 0,
            "network_calls": 0,
            "shared_ledger_modified": False,
        },
        "evidence_identity": fixture["evidence_identity"],
        "source_sha256": fixture["source_sha256"],
        "trace_count": len(per_trace),
        "non_success_count": len(non_success_rows),
        "contract_summary": summaries,
        "per_trace": per_trace,
        "non_success_actions_under_composite_c2_sensitivity": (
            sensitivity_actions
        ),
        "judgment": {
            "most_explanatory_contract": "composite_trace_c2_sensitivity",
            "reason": (
                "It preserves ESD_010's valid redundant sufficient set, separates "
                "ESD_001's answer-fact defect from evidence acquisition, exposes "
                "ESD_006 as a reference-scope defect, and rejects only ESD_002's "
                "entirely unsupported current selection."
            ),
            "supports_real_history_h_now": False,
            "why_not": (
                "The six non-successes mix answer-fact omission, partial evidence "
                "selection, one unsupported selection and one reference defect. "
                "They do not yet provide a homogeneous residual decision space or "
                "real correction histories for a task-matched H comparison."
            ),
            "h_stop_condition": (
                "Do not run H unless a corrected/equal-visibility baseline leaves "
                "at least two comparable evidence-selection failures and at least "
                "two complete task-matched real histories can change that same "
                "decision. If residual errors are mainly answer/reference defects, "
                "or eligible correction histories cannot be formed, stop this H "
                "candidate and preserve the boundary result."
            ),
        },
        "interpretation_limits": [
            "All seven tasks share source_component_03; no report-level independence is claimed.",
            "B0 V2 plan-time visibility differs from the strong-rule comparison described in C2_ROOT_CAUSE.md.",
            "ESD_006 C2 atom reduction is a labeled sensitivity analysis, not a rewrite of REFERENCES_V1.",
            "Update dispositions are deterministic post-hoc interventions and were not shown to the actor.",
            "No conclusion is drawn about training, memory updates, general experience learning or deployed-agent benefit.",
        ],
    }
    write_json_atomic(RESULT_PATH, result)
    print(f"Wrote {RESULT_PATH}")


def parse_args() -> argparse.Namespace:
    """Parse the freeze/run interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--replace", action="store_true")
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
