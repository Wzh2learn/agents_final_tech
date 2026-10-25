"""Same-candidate feedback intervention for frozen natural-program outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "natural_program_learning_20261024_v2"),
)
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_binding_residual_v3 import (
    extract_target,
    parse_cells,
    program_value,
    refs_in_program,
)
from run_natural_program_experiment_v2 import generate_and_score_batch
from semantic_delivery_check_v3 import question_from_prompt, semantic_check


CONDITIONS = (
    "deterministic_rerun_control",
    "neutral_revision_interface_failure_v2",
    "ordinary_retry",
    "execution_feedback",
    "localization_feedback",
    "oracle_localization_diagnostic_a_v3",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_unit(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def ref_set(target: Any) -> set[str]:
    if not isinstance(target, dict):
        return set()
    return {str(ref) for ref in target.get("evidence_refs", [])}


def visible_ref_details(
    target: Any,
    cells: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for ref in sorted(ref_set(target)):
        cell = cells.get(ref)
        output.append({
            "ref": ref,
            "row_label": None if cell is None else cell.get("row_label"),
            "period_labels": [] if cell is None else cell.get("period_labels", []),
            "unit_labels": [] if cell is None else cell.get("unit_labels", []),
            "raw_column_labels": [] if cell is None else cell.get("column_labels", []),
            "value": None if cell is None else cell.get("value"),
        })
    return output


def execution_feedback(instance: dict[str, Any], previous_text: str) -> str:
    cells = parse_cells(str(instance["table_text"]))
    target = extract_target(str(previous_text))
    lines = [
        "Feedback type: deterministic execution trace.",
        "This feedback contains only the visible question/table and the previous candidate's own execution. It does not contain a reference answer.",
    ]
    if target is None:
        lines.append("Parse result: no complete JSON object with program, evidence_refs, and unit.")
    else:
        refs = refs_in_program(target.get("program"))
        lines.append(f"Previous candidate JSON: {json.dumps(target, ensure_ascii=False, sort_keys=True)}")
        lines.append("Referenced visible cells:")
        for detail in visible_ref_details(target, cells):
            lines.append(json.dumps(detail, ensure_ascii=False, sort_keys=True))
        try:
            value = program_value(target.get("program"), cells)
            lines.append(f"Executed value from the candidate program: {value!r}")
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as exc:
            lines.append(f"Execution failed: {type(exc).__name__}: {exc}")
    return "\n".join(lines)


def localization_feedback(instance: dict[str, Any], previous_text: str) -> str:
    cells = parse_cells(str(instance["table_text"]))
    target = extract_target(str(previous_text))
    question = question_from_prompt(str(instance["prompt"]))
    decision, reasons = semantic_check(question, (target or {}).get("program"), cells)
    lines = [
        "Feedback type: visible evidence localization.",
        "This feedback uses only the question, visible table labels, recovered periods/units, and the previous candidate's references. It does not contain a reference answer or hidden program.",
        f"Visible semantic status: {decision}",
        f"Visible findings: {json.dumps(reasons, ensure_ascii=False)}",
    ]
    if target is not None:
        lines.append("Previous candidate bindings:")
        for detail in visible_ref_details(target, cells):
            lines.append(json.dumps(detail, ensure_ascii=False, sort_keys=True))
    else:
        lines.append("Previous candidate binding: no parseable complete target.")
    lines.append("Treat these findings as diagnostic prompts, not as an answer. Revise only when the visible evidence supports the change.")
    return "\n".join(lines)


def revision_prompt(
    instance: dict[str, Any],
    previous_text: str,
    condition: str,
) -> str:
    if condition == "deterministic_rerun_control":
        return str(instance["prompt"])
    if condition == "ordinary_retry":
        return (
            f"{instance['prompt']}\n\n"
            "You previously returned the following candidate.\n\n"
            f"Previous candidate:\n{previous_text}\n\n"
            "No targeted feedback is provided. Review the candidate and make at most one revision. "
            "Return exactly one JSON object with program, evidence_refs, and unit; do not return a numeric answer."
        )
    if condition == "execution_feedback":
        feedback = execution_feedback(instance, previous_text)
    elif condition == "localization_feedback":
        feedback = localization_feedback(instance, previous_text)
    else:
        raise ValueError(condition)
    return (
        f"{instance['prompt']}\n\n"
        "You previously returned the following candidate. Use the feedback to make at most one revision. "
        "Return exactly one JSON object with program, evidence_refs, and unit; do not return a numeric answer.\n\n"
        f"Previous candidate:\n{previous_text}\n\n"
        f"{feedback}"
    )


def is_unknown_or_clarify(text: str, target: Any) -> bool:
    lowered = text.casefold()
    terms = ("unknown", "clarify", "insufficient evidence", "cannot determine", "undetermined")
    if any(term in lowered for term in terms):
        return True
    return isinstance(target, dict) and normalize_unit(target.get("unit")) in {"unknown", "clarify"}


def expected_discrepancies(
    instance: dict[str, Any],
    generated_text: str,
) -> dict[str, Any]:
    cells = parse_cells(str(instance["table_text"]))
    candidate = extract_target(str(generated_text))
    expected = instance["expected"]
    candidate_refs = ref_set(candidate)
    expected_refs = ref_set(expected)
    question = question_from_prompt(str(instance["prompt"]))
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", question))
    years.update(f"20{y}" for y in re.findall(r"\bFY(\d{2})\b", question, flags=re.I))

    def periods(refs: set[str]) -> set[str]:
        return {
            period
            for ref in refs
            for period in (cells.get(ref, {}).get("period_labels") or [])
        }

    def rows(refs: set[str]) -> set[str]:
        return {
            str(cells.get(ref, {}).get("row_label") or "")
            for ref in refs
        }

    expected_periods = periods(expected_refs)
    candidate_periods = periods(candidate_refs)
    expected_rows = rows(expected_refs)
    candidate_rows = rows(candidate_refs)
    structure_equal = (
        isinstance(candidate, dict)
        and candidate.get("program") == expected.get("program")
    )
    categories = []
    if normalize_unit((candidate or {}).get("unit")) != normalize_unit(expected.get("unit")):
        categories.append("unit_mismatch")
    if candidate_refs != expected_refs:
        categories.append("reference_set_mismatch")
    if candidate_rows != expected_rows:
        categories.append("row_role_mismatch")
    if years and not years.issubset(candidate_periods):
        categories.append("period_mismatch")
    if not structure_equal:
        categories.append("program_structure_mismatch")
    if (
        isinstance(candidate, dict)
        and all(ref in cells for ref in candidate_refs)
        and not math.isclose(
            float(program_value(candidate.get("program"), cells)),
            float(expected["answer"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
    ):
        categories.append("numeric_mismatch")
    return {
        "categories": sorted(set(categories)),
        "candidate_refs": sorted(candidate_refs),
        "expected_refs": sorted(expected_refs),
        "candidate_periods": sorted(candidate_periods),
        "expected_periods": sorted(expected_periods),
        "candidate_rows": sorted(candidate_rows),
        "expected_rows": sorted(expected_rows),
    }


def localizer_assessment(
    reasons: list[str],
    discrepancies: dict[str, Any],
    initial_correct: bool,
) -> dict[str, Any]:
    reason_map = {
        "question_row_role_not_visible_in_program": "row_role_mismatch",
        "question_period_not_visible_in_program": "period_mismatch",
        "structural_average_denominator_misbound": "program_structure_mismatch",
        "missing_visible_reference": "reference_set_mismatch",
        "no_visible_reference": "reference_set_mismatch",
    }
    claimed = {reason_map[reason] for reason in reasons if reason in reason_map}
    true_categories = set(discrepancies["categories"])
    supported = sorted(claimed & true_categories)
    false_alarms = sorted(claimed - true_categories)
    sufficient = bool(supported)
    return {
        "claimed_categories": sorted(claimed),
        "supported_categories": supported,
        "false_alarm_categories": false_alarms,
        "feedback_error": bool(false_alarms),
        "feedback_insufficient": bool(not initial_correct and not sufficient),
    }


def binding_relation(generated: str, expected: dict[str, Any]) -> dict[str, Any]:
    target = extract_target(generated)
    actual = ref_set(target)
    gold = ref_set(expected)
    exact = actual == gold
    sufficient = bool(gold) and gold.issubset(actual)
    if not actual:
        relation = "NO_TARGET"
    elif exact:
        relation = "EXACT_REFERENCE_SET"
    elif sufficient:
        relation = "EXPECTED_REFS_INCLUDED_WITH_EXTRAS"
    elif actual.issubset(gold):
        relation = "PARTIAL_EXPECTED_REFS"
    elif actual & gold:
        relation = "PARTIAL_OVERLAP"
    else:
        relation = "DISJOINT_REFERENCE_SET"
    return {
        "relation": relation,
        "exact": exact,
        "expected_refs_included": sufficient,
        "precision": len(actual & gold) / len(actual) if actual else 0.0,
        "recall": len(actual & gold) / len(gold) if gold else 0.0,
    }


def enrich_row(
    result: dict[str, Any],
    instance: dict[str, Any],
    condition: str,
) -> dict[str, Any]:
    generated = str(result.get("generated_text", ""))
    target = extract_target(generated)
    cells = parse_cells(str(instance["table_text"]))
    decision, reasons = semantic_check(
        question_from_prompt(str(instance["prompt"])),
        (target or {}).get("program"),
        cells,
    )
    unknown = is_unknown_or_clarify(generated, target)
    binding = binding_relation(generated, instance["expected"])
    revised_discrepancies = expected_discrepancies(instance, generated)
    previous_text = str(result.get("previous_candidate") or generated)
    initial_discrepancies = expected_discrepancies(instance, previous_text)
    previous_target = extract_target(previous_text)
    try:
        initial_value = program_value(previous_target.get("program"), cells)
        initial_correct = math.isclose(
            float(initial_value),
            float(instance["expected"]["answer"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
    except (KeyError, ValueError, TypeError, ZeroDivisionError, AttributeError):
        initial_correct = condition == "original_frozen" and bool(result.get("program_correct"))
    assessment = None
    if condition == "localization_feedback":
        previous_decision, previous_reasons = semantic_check(
            question_from_prompt(str(instance["prompt"])),
            (previous_target or {}).get("program"),
            cells,
        )
        assessment = {
            **localizer_assessment(
                previous_reasons,
                initial_discrepancies,
                initial_correct,
            ),
            "feedback_semantic_decision": previous_decision,
            "feedback_reasons": previous_reasons,
            "assessment_input": "FROZEN_INITIAL_CANDIDATE_AND_ACTUAL_VISIBLE_FEEDBACK",
        }
    elif condition == "execution_feedback":
        assessment = {
            "trace_visibility_error": False,
            "feedback_error": False,
            "feedback_insufficient_not_claimed": bool(not result.get("program_correct")),
        }
    return {
        **result,
        "condition": condition,
        "unknown_or_clarify": unknown,
        "semantic_decision": decision,
        "semantic_reasons": reasons,
        "binding_relation": binding,
        "initial_correct": initial_correct,
        "posthoc_discrepancies_initial": initial_discrepancies,
        "posthoc_discrepancies_revised": revised_discrepancies,
        "feedback_assessment": assessment,
        "wrong_delivery": bool(not result.get("program_correct") and not unknown),
        "unnecessary_refusal": bool(unknown and instance.get("expected")),
    }


def transition_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    original = {
        row["instance_id"]: row
        for row in rows
        if row["condition"] == "original_frozen"
    }
    output = {}
    active_conditions = [
        condition for condition in CONDITIONS
        if any(row["condition"] == condition for row in rows)
    ]
    for condition in active_conditions:
        transitions = Counter()
        for row in rows:
            if row["condition"] != condition:
                continue
            base_id = str(row.get("base_instance_id") or row["instance_id"])
            before = bool(original[base_id]["program_correct"])
            after = bool(row["program_correct"])
            transitions[
                ("correct" if before else "wrong") + "_to_" + ("correct" if after else "wrong")
            ] += 1
        output[condition] = dict(transitions)
    return output


def task_level_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(row["condition"], row["source_task_id"])][row["variant"]] = row
    output = {}
    for condition in ("original_frozen", *[
        condition for condition in CONDITIONS
        if any(row["condition"] == condition for row in rows)
    ]):
        task_rows = []
        for (row_condition, _task), variants in grouped.items():
            if row_condition != condition or {"original", "relevant_change", "irrelevant_change"} - set(variants):
                continue
            task_rows.append({
                "original": bool(variants["original"]["program_correct"]),
                "relevant": bool(variants["relevant_change"]["program_correct"]),
                "irrelevant": bool(variants["irrelevant_change"]["program_correct"]),
                "paired": all(bool(variants[name]["program_correct"]) for name in variants),
            })
        output[condition] = {
            "tasks": len(task_rows),
            "original_correct": sum(item["original"] for item in task_rows),
            "relevant_change_correct_given_original": sum(item["original"] and item["relevant"] for item in task_rows),
            "irrelevant_change_correct_given_original": sum(item["original"] and item["irrelevant"] for item in task_rows),
            "all_three_correct": sum(item["paired"] for item in task_rows),
        }
    return output


def condition_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = {}
    for condition in ("original_frozen", *[
        condition for condition in CONDITIONS
        if any(row["condition"] == condition for row in rows)
    ]):
        subset = [row for row in rows if row["condition"] == condition]
        accepted = [
            row for row in subset
            if not row["unknown_or_clarify"] and row["interface_valid"] and row["program_executable"]
        ]
        output[condition] = {
            "items": len(subset),
            "numeric_correct": sum(bool(row["program_correct"]) for row in subset),
            "numeric_correct_rate": sum(bool(row["program_correct"]) for row in subset) / len(subset) if subset else 0.0,
            "interface_valid": sum(bool(row["interface_valid"]) for row in subset),
            "program_executable": sum(bool(row["program_executable"]) for row in subset),
            "exact_reference_set": sum(bool(row["binding_relation"]["exact"]) for row in subset),
            "expected_refs_included": sum(bool(row["binding_relation"]["expected_refs_included"]) for row in subset),
            "numeric_correct_alternate_binding": sum(
                bool(row["program_correct"]) and not bool(row["binding_relation"]["exact"])
                for row in subset
            ),
            "semantic_valid": sum(row["semantic_decision"] == "VALID" for row in subset),
            "semantic_unresolved": sum(row["semantic_decision"] == "UNRESOLVED" for row in subset),
            "semantic_invalid": sum(row["semantic_decision"] == "INVALID" for row in subset),
            "unknown_or_clarify": sum(bool(row["unknown_or_clarify"]) for row in subset),
            "wrong_delivery_count": sum(bool(row["wrong_delivery"]) for row in subset),
            "correct_delivery_coverage": sum(bool(row["program_correct"]) for row in subset) / len(subset) if subset else 0.0,
            "completion_rate": len(accepted) / len(subset) if subset else 0.0,
            "prompt_tokens": sum(int(row.get("prompt_tokens", 0)) for row in subset),
            "completion_tokens": sum(int(row.get("completion_tokens", 0)) for row in subset),
            "wall_seconds": sum(float(row.get("latency_ms", 0.0)) for row in subset) / 1000.0,
        }
    return output


def build_summary(rows: list[dict[str, Any]], receipts: dict[str, Any]) -> dict[str, Any]:
    localizer_rows = [
        row for row in rows
        if row["condition"] == "localization_feedback" and row["feedback_assessment"] is not None
    ]
    return {
        "schema": "same_candidate_feedback_intervention_a_v1",
        "identity": "FROZEN_ORDINARY_CANDIDATES_VISIBLE_MAIN_ARMS_PLUS_ORACLE_ASSISTED_DEVELOPMENT_DIAGNOSTIC",
        "conditions": [
            "original_frozen",
            *[condition for condition in CONDITIONS if any(row["condition"] == condition for row in rows)],
        ],
        "hidden_reference_in_prompts": {
            "main_visible_and_neutral_arms": "NONE",
            "oracle_localization_diagnostic_a_v3": [
                "initial_correctness_status",
                "posthoc_discrepancy_classes"
            ],
            "hidden_answer_in_any_prompt": False,
            "hidden_program_in_any_prompt": False,
            "hidden_reference_ids_in_any_prompt": False
        },
        "max_additional_generations_per_candidate": 1,
        "metrics": condition_metrics(rows),
        "transitions_from_frozen_original": transition_metrics(rows),
        "task_level_paired": task_level_metrics(rows),
        "localization_feedback_assessment": {
            "items": len(localizer_rows),
            "feedback_error_count": sum(bool(row["feedback_assessment"]["feedback_error"]) for row in localizer_rows),
            "feedback_error_rate": (
                sum(bool(row["feedback_assessment"]["feedback_error"]) for row in localizer_rows) / len(localizer_rows)
                if localizer_rows else 0.0
            ),
            "feedback_insufficient_count": sum(bool(row["feedback_assessment"]["feedback_insufficient"]) for row in localizer_rows),
            "feedback_insufficient_rate": (
                sum(bool(row["feedback_assessment"]["feedback_insufficient"]) for row in localizer_rows) / len(localizer_rows)
                if localizer_rows else 0.0
            ),
            "boundary": "Post-hoc expected-program discrepancy mapping; algebraically equivalent programs can be mislabeled and are not hidden-reference prompt features.",
        },
        "execution_feedback_assessment": {
            "items": sum(row["condition"] == "execution_feedback" for row in rows),
            "trace_visibility_error_count": 0,
            "diagnostic_sufficiency_claimed": False,
        },
        "generation_receipts": receipts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--frozen-results", type=Path, required=True)
    parser.add_argument("--adapter-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    frozen_all = load_jsonl(args.frozen_results)
    frozen = [
        row for row in frozen_all
        if row.get("model_arm") == "ordinary_answer_execution_sft"
    ]
    if len(frozen) != 72:
        raise ValueError(f"expected_72_frozen_ordinary_candidates:{len(frozen)}")
    if any(row["instance_id"] not in instances for row in frozen):
        raise ValueError("frozen_result_missing_instance")

    args.run_root.mkdir(parents=True, exist_ok=False)
    frozen_rows = [
        enrich_row({**row, "condition": "original_frozen"}, instances[row["instance_id"]], "original_frozen")
        for row in frozen
    ]
    write_jsonl(args.run_root / "frozen_candidates_enriched_a_v1.jsonl", frozen_rows)

    intervention_instances = []
    for row in frozen:
        instance = instances[row["instance_id"]]
        for condition in CONDITIONS:
            intervention_instances.append({
                **deepcopy(instance),
                "instance_id": f"{row['instance_id']}::{condition}",
                "base_instance_id": row["instance_id"],
                "condition": condition,
                "slice": "same_candidate_feedback_a_v1",
                "prompt": revision_prompt(instance, str(row["generated_text"]), condition),
                "previous_candidate": str(row["generated_text"]),
                "feedback_only_visible": condition != "ordinary_retry",
            })
    write_jsonl(args.run_root / "intervention_instances_a_v1.jsonl", intervention_instances)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model = PeftModel.from_pretrained(
        model,
        args.adapter_root / "ordinary_answer_execution_sft" / "final_adapter",
    )
    model.eval()

    generated_rows: list[dict[str, Any]] = []
    receipts = {}
    for condition in CONDITIONS:
        subset = [row for row in intervention_instances if row["condition"] == condition]
        started = time.time()
        arm_rows = []
        for start in range(0, len(subset), args.batch_size):
            batch = subset[start : start + args.batch_size]
            output = generate_and_score_batch(model, tokenizer, batch, args.max_new_tokens)
            for item, result in zip(batch, output):
                result["condition"] = condition
                result["base_instance_id"] = item["base_instance_id"]
                result["previous_candidate"] = item["previous_candidate"]
                result["model_arm"] = "ordinary_answer_execution_sft"
                arm_rows.append(result)
                generated_rows.append(result)
            with (args.run_root / "intervention_results_a_v1.partial.jsonl").open(
                "a", encoding="utf-8", newline="\n"
            ) as handle:
                for result in output:
                    handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            print(f"{condition}: {len(arm_rows)}/{len(subset)}", flush=True)
        receipts[condition] = {
            "attempts": len(arm_rows),
            "prompt_tokens": sum(int(row["prompt_tokens"]) for row in arm_rows),
            "completion_tokens": sum(int(row["completion_tokens"]) for row in arm_rows),
            "wall_seconds": time.time() - started,
            "max_new_tokens": args.max_new_tokens,
        }

    enriched = []
    for result in generated_rows:
        base_id = str(result["base_instance_id"])
        enriched.append(enrich_row(result, instances[base_id], str(result["condition"])))
    write_jsonl(args.run_root / "intervention_results_a_v1.jsonl", enriched)
    all_rows = frozen_rows + enriched
    summary = build_summary(all_rows, receipts)
    summary["new_accounting_attempts"] = len(enriched)
    summary["new_accounting_tokens"] = sum(
        int(row["prompt_tokens"]) + int(row["completion_tokens"])
        for row in enriched
    )
    summary["input_sha256"] = {
        "instances": sha256_file(args.instances),
        "frozen_results": sha256_file(args.frozen_results),
    }
    summary["output_sha256"] = sha256_file(args.run_root / "intervention_results_a_v1.jsonl")
    write_json(args.run_root / "SAME_CANDIDATE_FEEDBACK_A_V1.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
