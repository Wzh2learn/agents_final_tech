"""DEV_ONLY active evidence acquisition simulation.

This probe uses frozen task-visible fields and reference-only evaluation fields.
It performs no model, judge, training, network, or service calls.
"""

from __future__ import annotations

import argparse
import math
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from probe_common import (
    ADJUDICATION_PATH,
    CHARTER_PATH,
    CONTRACTS_PATH,
    EXPECTED_KEEP_IDS,
    FEEDBACK_FIXTURE_PATH,
    FIXTURE_DIR,
    FREEZE_RECEIPT_PATH,
    INPUT_FIXTURE_PATH,
    KEEP_RULING,
    PROTOCOL_VERSION,
    RESULT_DIR,
    SCOPE_TASK_PATH,
    SCRIPT_DIR,
    contains_sufficient_set,
    covered_fact_ids,
    load_frozen_probe_inputs,
    normalize_candidate_ids,
    normalize_sufficient_sets,
    read_json,
    relative_to_script,
    sha256_bytes,
    sha256_file,
    unique_strings,
    validate_reference,
    write_json_atomic,
)


BUDGETS = (1, 2, 3)
RANDOM_SEEDS = (1729, 20261020, 314159, 271828)
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "what",
    "which",
    "with",
}
STRATEGIES = (
    "direct",
    "fixed",
    "random",
    "lexical",
    "score_disagreement",
    "oracle",
)


def tokenize(text: str) -> set[str]:
    """Tokenize visible text for a transparent lexical score."""
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOP_WORDS and len(token) > 1
    }


def lexical_score(question: str, candidate_text: str) -> float:
    """Return token Jaccard similarity between question and candidate."""
    left = tokenize(question)
    right = tokenize(candidate_text)
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def visible_scope_score(
    question: str,
    source_ticker: str,
    candidate: dict[str, Any],
) -> float:
    """Return a deterministic score from task-visible scope metadata and text."""
    scope = candidate["visible_source_scope"]
    question_lower = question.lower()
    text_lower = candidate["text"].lower()
    score = 0.0

    if scope.get("ticker") == source_ticker:
        score += 0.35

    question_years = set(re.findall(r"\b(?:19|20)\d{2}\b", question))
    candidate_year = str(scope.get("year", ""))
    if candidate_year in question_years:
        score += 0.25
    elif question_years and candidate_year:
        score -= 0.15

    question_forms = {
        form.lower()
        for form in re.findall(r"\b10-[KQ]\b", question, flags=re.IGNORECASE)
    }
    candidate_form = str(scope.get("doc_type", "")).lower()
    if question_forms:
        score += 0.15 if candidate_form in question_forms else -0.10

    month_tokens = {
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    }
    question_months = month_tokens.intersection(tokenize(question))
    candidate_months = month_tokens.intersection(tokenize(candidate["text"]))
    if question_months:
        score += 0.25 if question_months & candidate_months else -0.10

    return score


def normalize_scores(values: list[float]) -> list[float]:
    """Min-max normalize scores, mapping a constant vector to zeros."""
    if not values:
        return []
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def candidate_order(
    task: dict[str, Any],
    strategy: str,
    seed: int | None = None,
) -> list[str]:
    """Return the reference-blind acquisition order for one strategy."""
    candidates = task["actor_view"]["candidates"]
    source_order = [candidate["candidate_id"] for candidate in candidates]
    if strategy == "direct":
        return source_order[:1]
    if strategy == "fixed":
        return sorted(source_order)
    if strategy == "random":
        if seed is None:
            raise ValueError("random strategy requires a seed")
        task_digest = int(
            sha256_bytes(task["task_id"].encode("utf-8"))[:16],
            16,
        )
        shuffled = list(source_order)
        random.Random(seed ^ task_digest).shuffle(shuffled)
        return shuffled
    if strategy == "lexical":
        scored = [
            (
                lexical_score(
                    task["actor_view"]["question"], candidate["text"]
                ),
                source_order.index(candidate["candidate_id"]),
                candidate["candidate_id"],
            )
            for candidate in candidates
        ]
        return [item[2] for item in sorted(scored, key=lambda item: (-item[0], item[1]))]
    if strategy == "score_disagreement":
        by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
        lexical = normalize_scores(
            [
                lexical_score(
                    task["actor_view"]["question"], candidate["text"]
                )
                for candidate in candidates
            ]
        )
        scope = normalize_scores(
            [
                visible_scope_score(
                    task["actor_view"]["question"],
                    task["source_ticker"],
                    candidate,
                )
                for candidate in candidates
            ]
        )
        unseen = list(source_order)
        order: list[str] = []
        while unseen:
            ranked = []
            for candidate_id in unseen:
                index = source_order.index(candidate_id)
                disagreement = abs(lexical[index] - scope[index])
                combined_confidence = lexical[index] + scope[index]
                ranked.append(
                    (-disagreement, -combined_confidence, index, candidate_id)
                )
            selected = min(ranked)[-1]
            order.append(selected)
            unseen.remove(selected)
        return order
    if strategy == "oracle":
        required = unique_strings(
            candidate_id
            for candidate_set in task["reference"]["minimal_sufficient_sets"]
            for candidate_id in candidate_set
        )
        optional = task["reference"]["optional_redundant"]
        remaining = [
            candidate_id
            for candidate_id in source_order
            if candidate_id not in required and candidate_id not in optional
        ]
        return unique_strings([*required, *optional, *remaining])
    raise ValueError(f"Unknown strategy: {strategy}")


def build_frozen_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build immutable C2/C3 inputs from the frozen upstream research artifacts."""
    adjudication = read_json(ADJUDICATION_PATH)
    scope_tasks = read_json(SCOPE_TASK_PATH)
    cases_by_id = {case["task_id"]: case for case in adjudication["cases"]}
    tasks_by_id = {task["task_id"]: task for task in scope_tasks["tasks"]}

    keep_ids = tuple(
        case["task_id"]
        for case in adjudication["cases"]
        if case["ruling"] == KEEP_RULING
    )
    if keep_ids != EXPECTED_KEEP_IDS:
        raise ValueError(f"Unexpected KEEP task IDs: {keep_ids!r}")

    frozen_tasks: list[dict[str, Any]] = []
    for task_id in EXPECTED_KEEP_IDS:
        case = cases_by_id[task_id]
        source_task = tasks_by_id[task_id]
        actor_view = source_task["actor_view"]
        candidates = actor_view["candidates"]
        candidate_ids = {candidate["candidate_id"] for candidate in candidates}
        (
            sufficient_sets,
            optional_redundant,
            facts,
            contrast_anchors,
        ) = validate_reference(case, candidate_ids)

        frozen_candidates = []
        for candidate in candidates:
            frozen_candidates.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "text": candidate["text"],
                    "text_sha256": sha256_bytes(candidate["text"].encode("utf-8")),
                    "page_number": candidate.get("page_number"),
                    "visible_source_scope": candidate["visible_source_scope"],
                }
            )

        frozen_tasks.append(
            {
                "task_id": task_id,
                "split": source_task["split"],
                "source_cluster_id": source_task["source_cluster_id"],
                "source_report_key": source_task["source_report_key"],
                "source_ticker": source_task["source_ticker"],
                "actor_view": {
                    "instruction": actor_view["instruction"],
                    "question": actor_view["question"],
                    "question_scope": actor_view["question_scope"],
                    "candidates": frozen_candidates,
                },
                "reference": {
                    "minimal_sufficient_sets": sufficient_sets,
                    "optional_redundant": optional_redundant,
                    "allowed_candidate_ids": sorted(
                        set(optional_redundant).union(*map(set, sufficient_sets))
                    ),
                    "fact_atoms": facts,
                    "contrast_anchors": contrast_anchors,
                    "canonical_answer": case["canonical_answer"],
                    "adjudication_note": case["note"],
                },
            }
        )

    input_payload = {
        "schema": "open_research_probe_inputs_v1",
        "status": "DEV_ONLY_FROZEN_INPUTS",
        "protocol_version": PROTOCOL_VERSION,
        "evidence_class": "DETERMINISTIC_MECHANISM_PROBES",
        "source_files": {
            relative_to_script(path): sha256_file(path)
            for path in (
                CONTRACTS_PATH,
                CHARTER_PATH,
                ADJUDICATION_PATH,
                SCOPE_TASK_PATH,
            )
        },
        "active_acquisition": {
            "budgets": list(BUDGETS),
            "random_seeds": list(RANDOM_SEEDS),
            "strategies": list(STRATEGIES),
            "metric_thresholds": {
                "sufficient_set_discovery": "any frozen minimal_sufficient_set is contained in looked-up IDs",
                "useful_fact_coverage": "covered frozen adjudication anchor facts / all anchor facts",
                "regret_to_oracle": "oracle macro rate minus strategy macro rate, floored at zero",
            },
            "lexical_rule": "lowercase alphanumeric token Jaccard after a frozen stop-word list",
            "score_disagreement_rule": "max absolute min-max disagreement between lexical and visible-scope scores; ties prefer higher combined confidence then source order",
            "oracle_rule": "reference-derived upper bound; not a deployable policy",
        },
        "tasks": frozen_tasks,
    }

    task_lookup = {task["task_id"]: task for task in frozen_tasks}

    def make_case(
        case_id: str,
        task_id: str,
        selection: list[str],
        ground_truth_class: str,
        description: str,
    ) -> dict[str, Any]:
        task = task_lookup[task_id]
        candidate_ids = {
            candidate["candidate_id"] for candidate in task["actor_view"]["candidates"]
        }
        if not set(selection).issubset(candidate_ids):
            raise ValueError(f"{case_id}: selection contains unknown candidates")
        return {
            "case_id": case_id,
            "task_id": task_id,
            "selection": selection,
            "ground_truth_class": ground_truth_class,
            "description": description,
            "revision_selection": task["reference"]["minimal_sufficient_sets"][0],
        }

    feedback_cases = [
        make_case(
            "canonical_exact_multi_fact",
            "ESD_004",
            ["cand_003", "cand_005"],
            "VALID_CANONICAL",
            "Exact frozen minimal set covering both required facts.",
        ),
        make_case(
            "valid_alternative_with_redundant_support",
            "ESD_010",
            ["cand_003", "cand_007"],
            "VALID_ALTERNATIVE",
            "Contains the sufficient subset cand_003 and adds explicitly optional redundant support cand_007.",
        ),
        make_case(
            "partial_supported_multi_fact",
            "ESD_003",
            ["cand_006"],
            "PARTIAL_SUPPORTED",
            "Supported first fact but omits the second required fact.",
        ),
        make_case(
            "unsupported_extra_with_complete_facts",
            "ESD_001",
            ["cand_001", "cand_002"],
            "UNSUPPORTED_EXTRA",
            "Covers all anchors through cand_001 but adds out-of-scope cand_002.",
        ),
        make_case(
            "unsupported_cross_period_extra",
            "ESH_010",
            ["cand_002", "cand_005"],
            "UNSUPPORTED_EXTRA",
            "Covers the requested period through cand_002 but adds a March-period distractor cand_005.",
        ),
        make_case(
            "unsupported_only",
            "ESD_002",
            ["cand_004"],
            "UNSUPPORTED_ONLY",
            "Selects a same-company prior-period distractor and no supported evidence.",
        ),
        make_case(
            "empty_selection",
            "ESD_001",
            [],
            "EMPTY",
            "No evidence selected.",
        ),
    ]
    feedback_payload = {
        "schema": "open_research_feedback_cases_v1",
        "status": "DEV_ONLY_CONTROLLED_MECHANISM_FIXTURES",
        "protocol_version": PROTOCOL_VERSION,
        "feedback_contracts": ["exact_match", "minimal_sufficient_set", "fact_coverage"],
        "update_rule": {
            "accepted": "RETAIN unchanged selection",
            "rejected_scope_valid_or_partial_supported": "REVISE to the first frozen minimal sufficient set",
            "otherwise": "REJECT",
        },
        "ground_truth_scope_rule": (
            "A selection is scope-valid when it contains a frozen minimal sufficient "
            "set and every selected ID is within minimal sets plus optional_redundant."
        ),
        "cases": feedback_cases,
    }
    return input_payload, feedback_payload


def freeze(replace: bool = False) -> None:
    """Freeze task inputs and feedback cases before computing outcomes."""
    target_paths = (
        INPUT_FIXTURE_PATH,
        FEEDBACK_FIXTURE_PATH,
        FREEZE_RECEIPT_PATH,
    )
    existing = [path for path in target_paths if path.exists()]
    if existing and not replace:
        raise FileExistsError(
            "Frozen fixtures already exist; pass --replace only for a versioned repair: "
            + ", ".join(str(path) for path in existing)
        )

    input_payload, feedback_payload = build_frozen_inputs()
    write_json_atomic(INPUT_FIXTURE_PATH, input_payload)
    write_json_atomic(FEEDBACK_FIXTURE_PATH, feedback_payload)
    fixture_paths = (INPUT_FIXTURE_PATH, FEEDBACK_FIXTURE_PATH)
    receipt = {
        "schema": "open_research_probe_freeze_receipt_v1",
        "protocol_version": PROTOCOL_VERSION,
        "fixture_sha256": {
            relative_to_script(path): sha256_file(path)
            for path in fixture_paths
        },
        "upstream_sha256": {
            relative_to_script(path): sha256_file(path)
            for path in (
                CONTRACTS_PATH,
                CHARTER_PATH,
                ADJUDICATION_PATH,
                SCOPE_TASK_PATH,
            )
        },
        "task_count": len(input_payload["tasks"]),
        "feedback_case_count": len(feedback_payload["cases"]),
        "random_seeds": list(RANDOM_SEEDS),
        "budgets": list(BUDGETS),
    }
    write_json_atomic(FREEZE_RECEIPT_PATH, receipt)
    print(f"Froze {receipt['task_count']} tasks and {receipt['feedback_case_count']} cases")


def evaluate_strategy(
    task: dict[str, Any],
    strategy: str,
    budget: int,
    seed: int | None = None,
) -> dict[str, Any]:
    """Evaluate one acquisition order without exposing reference fields to policy."""
    order = candidate_order(task, strategy, seed)
    lookup_ids = order[:budget]
    facts = task["reference"]["fact_atoms"]
    covered = covered_fact_ids(lookup_ids, facts)
    return {
        "task_id": task["task_id"],
        "source_cluster_id": task["source_cluster_id"],
        "strategy": strategy,
        "seed": seed,
        "budget": budget,
        "lookup_ids": lookup_ids,
        "lookup_cost": len(lookup_ids),
        "sufficient_set_discovered": contains_sufficient_set(
            lookup_ids, task["reference"]["minimal_sufficient_sets"]
        ),
        "covered_fact_ids": covered,
        "fact_coverage": len(covered) / len(facts),
    }


def mean(values: list[float]) -> float:
    """Return the arithmetic mean of a non-empty list."""
    return sum(values) / len(values) if values else 0.0


def macro_average(rows: list[dict[str, Any]], field: str) -> float:
    """Average a numeric metric across task rows."""
    return mean([float(row[field]) for row in rows])


def cluster_macro_average(rows: list[dict[str, Any]], field: str) -> float:
    """Average task means within source clusters, then average clusters equally."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row["source_cluster_id"]].append(float(row[field]))
    return mean([mean(values) for values in grouped.values()])


def run() -> None:
    """Run the frozen deterministic active-acquisition simulation."""
    inputs, _ = load_frozen_probe_inputs()
    if inputs["protocol_version"] != PROTOCOL_VERSION:
        raise ValueError("Protocol version mismatch")

    aggregate_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    for budget in BUDGETS:
        for strategy in STRATEGIES:
            if strategy == "random":
                strategy_rows = [
                    evaluate_strategy(task, strategy, budget, seed)
                    for task in inputs["tasks"]
                    for seed in RANDOM_SEEDS
                ]
                grouped_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in strategy_rows:
                    grouped_by_task[row["task_id"]].append(row)
                averaged_rows = []
                for task_id, rows in grouped_by_task.items():
                    first = rows[0]
                    averaged_rows.append(
                        {
                            **first,
                            "seed": "SEEDED_MACRO_AVERAGE",
                            "sufficient_set_discovered": mean(
                                [
                                    float(row["sufficient_set_discovered"])
                                    for row in rows
                                ]
                            ),
                            "fact_coverage": mean(
                                [float(row["fact_coverage"]) for row in rows]
                            ),
                            "lookup_cost": mean(
                                [float(row["lookup_cost"]) for row in rows]
                            ),
                            "seed_detail": [
                                {
                                    "seed": row["seed"],
                                    "lookup_ids": row["lookup_ids"],
                                    "sufficient_set_discovered": row[
                                        "sufficient_set_discovered"
                                    ],
                                    "fact_coverage": row["fact_coverage"],
                                }
                                for row in rows
                            ],
                        }
                    )
                detail_rows.extend(averaged_rows)
                evaluated_rows = averaged_rows
            else:
                evaluated_rows = [
                    evaluate_strategy(task, strategy, budget)
                    for task in inputs["tasks"]
                ]
                detail_rows.extend(evaluated_rows)

            aggregate_rows.append(
                {
                    "budget": budget,
                    "strategy": strategy,
                    "task_count": len(evaluated_rows),
                    "task_macro_sufficient_set_discovery_rate": macro_average(
                        evaluated_rows, "sufficient_set_discovered"
                    ),
                    "source_cluster_macro_sufficient_set_discovery_rate": (
                        cluster_macro_average(
                            evaluated_rows, "sufficient_set_discovered"
                        )
                    ),
                    "task_macro_fact_coverage": macro_average(
                        evaluated_rows, "fact_coverage"
                    ),
                    "source_cluster_macro_fact_coverage": cluster_macro_average(
                        evaluated_rows, "fact_coverage"
                    ),
                    "mean_lookup_cost": macro_average(evaluated_rows, "lookup_cost"),
                }
            )

    oracle_by_budget = {
        row["budget"]: row
        for row in aggregate_rows
        if row["strategy"] == "oracle"
    }
    for row in aggregate_rows:
        oracle = oracle_by_budget[row["budget"]]
        row["discovery_regret_to_oracle"] = max(
            0.0,
            oracle["task_macro_sufficient_set_discovery_rate"]
            - row["task_macro_sufficient_set_discovery_rate"],
        )
        row["fact_coverage_regret_to_oracle"] = max(
            0.0,
            oracle["task_macro_fact_coverage"] - row["task_macro_fact_coverage"],
        )

    best_non_oracle: list[dict[str, Any]] = []
    for budget in BUDGETS:
        eligible = [
            row
            for row in aggregate_rows
            if row["budget"] == budget and row["strategy"] != "oracle"
        ]
        best = max(
            eligible,
            key=lambda row: (
                row["task_macro_sufficient_set_discovery_rate"],
                row["task_macro_fact_coverage"],
                -row["mean_lookup_cost"],
            ),
        )
        best_non_oracle.append(
            {
                "budget": budget,
                "strategy": best["strategy"],
                "task_macro_sufficient_set_discovery_rate": best[
                    "task_macro_sufficient_set_discovery_rate"
                ],
                "task_macro_fact_coverage": best["task_macro_fact_coverage"],
            }
        )

    result = {
        "schema": "active_evidence_probe_result_v1",
        "status": "DEV_ONLY_SIMULATION_COMPLETED",
        "evidence_class": "DETERMINISTIC_OFFLINE_MECHANISM_PROBE",
        "protocol_version": PROTOCOL_VERSION,
        "scientific_scope": (
            "Frozen finite-panel simulation of evidence-check ordering. "
            "It is not a model effect, natural experiment, deployed-agent result, "
            "or independent-generalization claim."
        ),
        "resource_accounting": {
            "model_requests": 0,
            "judge_requests": 0,
            "training_runs": 0,
            "network_calls": 0,
        },
        "task_count": len(inputs["tasks"]),
        "source_cluster_count": len(
            {task["source_cluster_id"] for task in inputs["tasks"]}
        ),
        "budgets": list(BUDGETS),
        "strategies": list(STRATEGIES),
        "random_seeds": list(RANDOM_SEEDS),
        "metric_definitions": {
            "sufficient_set_discovery": (
                "The looked-up set contains at least one frozen minimal sufficient set. "
                "For ESD_010, cand_003 alone is sufficient; cand_007 is optional redundant support."
            ),
            "fact_coverage": (
                "Fraction of frozen supporting adjudication anchors whose candidate was "
                "looked up. Contrast/distractor anchors are recorded separately and do "
                "not count as useful facts."
            ),
            "lookup_cost": "Mean number of candidate lookups actually made.",
            "regret_to_oracle": (
                "Oracle task-macro rate minus strategy task-macro rate, floored at zero. "
                "The oracle uses reference labels and is only an upper bound."
            ),
        },
        "aggregate": aggregate_rows,
        "best_non_oracle_by_budget": best_non_oracle,
        "by_task": detail_rows,
        "interpretation_limits": [
            "The 13 tasks have already been reviewed and are development-only.",
            "The oracle is reference-informed and cannot be interpreted as a realizable policy.",
            "Anchor coverage is not full semantic answer correctness.",
            "The transparent scores are mechanism probes, not learned retrieval models.",
            "Only two source clusters are represented; task-macro and cluster-macro values are both reported.",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULT_DIR / "active_evidence_probe_results.json"
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

