"""Small, controlled revision-operator diagnostic on exposed development data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "natural_program_learning_20261024_v2"),
)
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_binding_residual_v3 import extract_target
from exposure_union_guard_v1 import check_exposure
from run_natural_program_experiment_v2 import evaluate_target
from semantic_delivery_check_v3 import question_from_prompt, semantic_check
from analyze_binding_residual_v3 import parse_cells


TERMINAL_INSTRUCTION = (
    "Return exactly one JSON object with keys program, evidence_refs, and unit. "
    "Output no other text."
)


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


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def target_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    return extract_target(str(row.get("generated_text", "")))


def normalize_generated_text(text: str) -> tuple[str, bool, list[str]]:
    raw = str(text)
    if extract_target(raw) is not None:
        return raw, False, []
    start = raw.find("{")
    if start < 0:
        return raw, False, []
    for index in range(len(raw) - 1, start, -1):
        if raw[index] != ")":
            continue
        candidate = raw[:index] + raw[index + 1:]
        if extract_target(candidate) is not None:
            return candidate, True, ["remove_one_close_paren_before_final_json"]
    return raw, False, []


def expected_target(instance: dict[str, Any]) -> dict[str, Any]:
    expected = instance["expected"]
    return {
        "program": expected["program"],
        "evidence_refs": expected["evidence_refs"],
        "unit": expected["unit"],
    }


def diff_target(candidate: Any, expected: Any) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []

    def visit(a: Any, b: Any, path: str) -> None:
        if canonical(a) == canonical(b):
            return
        if isinstance(a, dict) and isinstance(b, dict):
            keys = sorted(set(a) | set(b))
            for key in keys:
                visit(a.get(key), b.get(key), f"{path}.{key}" if path else key)
            return
        differences.append({"path": path, "candidate": a, "expected": b})

    visit(candidate, expected, "")
    return differences


def minimal_edit_instruction(differences: list[dict[str, Any]]) -> str | None:
    if len(differences) == 1:
        item = differences[0]
        path = item["path"]
        if path.endswith(".unit"):
            return (
                f"Change only the unit field from {item['candidate']!r} to "
                f"{item['expected']!r}."
            )
        if path.endswith(".ref"):
            return (
                f"At program path {path[:-4] or 'root'}, replace evidence reference "
                f"{item['candidate']!r} with {item['expected']!r}."
            )
        if path.endswith(".op"):
            return (
                f"At program path {path[:-4] or 'root'}, replace operation "
                f"{item['candidate']!r} with {item['expected']!r}."
            )
        return (
            f"At {path}, replace {item['candidate']!r} with the verified development "
            f"value {item['expected']!r}."
        )

    reference_changes = [item for item in differences if item["path"].endswith(".ref")]
    evidence_changes = [item for item in differences if item["path"] == "evidence_refs"]
    if len(differences) == 2 and len(reference_changes) == 1 and len(evidence_changes) == 1:
        reference = reference_changes[0]
        evidence = evidence_changes[0]
        return (
            f"At program path {reference['path'][:-4] or 'root'}, replace evidence "
            f"reference {reference['candidate']!r} with {reference['expected']!r}, "
            f"and update evidence_refs from {evidence['candidate']!r} to "
            f"{evidence['expected']!r}."
        )
    return None


def inspect_candidates(
    instances: dict[str, dict[str, Any]],
    frozen: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for row in frozen:
        instance = instances[row["instance_id"]]
        candidate = target_from_row(row)
        expected = expected_target(instance)
        differences = diff_target(candidate, expected)
        edit = minimal_edit_instruction(differences)
        rows.append({
            "instance_id": row["instance_id"],
            "source_task_id": row["source_task_id"],
            "table_uid": row["table_uid"],
            "variant": row["variant"],
            "initial_program_correct": bool(row["program_correct"]),
            "target_exact": canonical(candidate) == canonical(expected),
            "difference_count": len(differences),
            "differences": differences,
            "minimal_edit_instruction": edit,
        })
    return {
        "schema": "revision_operator_diagnostic_inspection_v1",
        "identity": "ZERO_GENERATION_DEVELOPMENT_CASE_SELECTION",
        "copy_exact_candidates": [row for row in rows if row["target_exact"]],
        "single_edit_candidates": [
            row for row in rows if row["minimal_edit_instruction"]
        ],
        "single_edit_error_candidates": [
            row for row in rows
            if not row["initial_program_correct"]
            and row["minimal_edit_instruction"]
        ],
        "difference_count_histogram": dict(Counter(
            row["difference_count"] for row in rows
        )),
        "candidate_rows": rows,
        "all_candidate_count": len(rows),
    }


def standardized_prompt(
    instance: dict[str, Any],
    previous_text: str,
    payload: dict[str, str],
    terminal_instruction: str = TERMINAL_INSTRUCTION,
) -> str:
    candidate = extract_target(previous_text)
    candidate_json = canonical(candidate) if candidate is not None else canonical({"raw": previous_text.strip()})
    return "\n".join([
        str(instance["prompt"]),
        "",
        "Previous candidate:",
        candidate_json,
        "",
        "Revision information:",
        f"status: {payload['status']}",
        f"finding: {payload['finding']}",
        f"edit: {payload['edit']}",
        "",
        terminal_instruction,
    ])


def actual_generation_row(
    model: Any,
    tokenizer: Any,
    instance: dict[str, Any],
    prompt: str,
    protocol_row: dict[str, Any],
) -> dict[str, Any]:
    import torch

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_width = int(inputs["input_ids"].shape[1])
    started = time.time()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=int(protocol_row["max_new_tokens"]),
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    latency_ms = (time.time() - started) * 1000.0
    generated_ids = output[0][input_width:]
    eos_positions = [
        index for index, token_id in enumerate(generated_ids.tolist())
        if token_id == tokenizer.eos_token_id
    ]
    actual_end = (eos_positions[0] + 1) if eos_positions else int(generated_ids.shape[0])
    raw_generated = tokenizer.decode(generated_ids[:actual_end], skip_special_tokens=True)
    generated, syntax_adapter_applied, syntax_actions = normalize_generated_text(raw_generated)
    scored = evaluate_target(generated, instance)
    target = extract_target(generated)
    return {
        "attempt_id": protocol_row["attempt_id"],
        "condition": protocol_row["condition"],
        "instance_id": instance["instance_id"],
        "source_task_id": instance["source_task_id"],
        "table_uid": instance["table_uid"],
        "variant": instance["variant"],
        "generated_text": generated,
        "raw_generated_text": raw_generated,
        "prompt_tokens": int(inputs["input_ids"].shape[1]),
        "raw_format_valid": extract_target(raw_generated) is not None,
        "syntax_adapter_applied": syntax_adapter_applied,
        "syntax_adapter_actions": syntax_actions,
        "actual_completion_tokens": int(actual_end),
        "max_new_tokens": int(protocol_row["max_new_tokens"]),
        "stop_reason": "eos" if eos_positions else "length_or_no_eos",
        "latency_ms": latency_ms,
        "terminal_instruction_repeats": generated.count(
            str(protocol_row.get("terminal_instruction_text", TERMINAL_INSTRUCTION))
        ),
        "left_brace_count": generated.count("{"),
        "format_valid": target is not None,
        **scored,
        "semantic_decision": None,
    }


def semantic_enrich(row: dict[str, Any], instance: dict[str, Any]) -> dict[str, Any]:
    target = extract_target(str(row["generated_text"]))
    decision, reasons = semantic_check(
        question_from_prompt(str(instance["prompt"])),
        (target or {}).get("program"),
        parse_cells(str(instance["table_text"])),
    )
    row["semantic_decision"] = decision
    row["semantic_reasons"] = reasons
    row["target_exact"] = canonical(target) == canonical(expected_target(instance))
    return row


def summarize(rows: list[dict[str, Any]], exposure: dict[str, Any]) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_condition.setdefault(row["condition"], []).append(row)
    metrics = {}
    for condition, subset in sorted(by_condition.items()):
        metrics[condition] = {
            "attempts": len(subset),
            "format_valid": sum(row["format_valid"] for row in subset),
            "raw_format_valid": sum(bool(row.get("raw_format_valid")) for row in subset),
            "syntax_adapter_applied": sum(bool(row.get("syntax_adapter_applied")) for row in subset),
            "numeric_correct": sum(bool(row["program_correct"]) for row in subset),
            "target_exact": sum(bool(row["target_exact"]) for row in subset),
            "semantic_valid": sum(row["semantic_decision"] == "VALID" for row in subset),
            "stop_reasons": dict(Counter(row["stop_reason"] for row in subset)),
            "terminal_instruction_repeats": dict(Counter(
                row["terminal_instruction_repeats"] for row in subset
            )),
            "actual_completion_tokens": sum(row["actual_completion_tokens"] for row in subset),
        }
    return {
        "schema": "revision_operator_diagnostic_v1",
        "identity": "SMALL_DEVELOPMENT_REVISION_OPERATOR_CONTROL",
        "development_only": True,
        "confirmation_claim": False,
        "hidden_reference_use": {
            "known_edit_control": "DEVELOPMENT_REFERENCE_ASSISTED_NON_DEPLOYABLE",
            "neutral_and_visible_feedback": "NO_HIDDEN_ANSWER_OR_PROGRAM",
        },
        "exposure_receipt": exposure,
        "metrics": metrics,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--frozen-results", type=Path, required=True)
    parser.add_argument("--exposure-manifest", type=Path, required=True)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--adapter-root", type=Path)
    parser.add_argument("--allow-development-exposure", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=32)
    args = parser.parse_args()

    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    frozen = [
        row for row in load_jsonl(args.frozen_results)
        if row.get("model_arm") == "ordinary_answer_execution_sft"
    ]
    if len(frozen) != 72:
        raise ValueError(f"expected_72_frozen_rows:{len(frozen)}")
    if args.protocol is None:
        inspection = inspect_candidates(instances, frozen)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "REVISION_OPERATOR_INSPECTION_V1.json", inspection)
        print(json.dumps(inspection, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    base_protocol = None
    if "attempts" not in protocol and protocol.get("base_protocol"):
        base_path = args.protocol.parent / str(protocol["base_protocol"])
        base_protocol = json.loads(base_path.read_text(encoding="utf-8"))
    source_protocol = base_protocol or protocol
    attempts = source_protocol["attempts"]
    if protocol.get("attempt_ids"):
        wanted = set(protocol["attempt_ids"])
        attempts = [row for row in attempts if row["attempt_id"] in wanted]
        if len(attempts) != len(wanted):
            raise ValueError("attempt_id_filter_miss")
    protocol = {
        **source_protocol,
        **protocol,
        "attempts": attempts,
    }
    if len(attempts) > args.max_attempts:
        raise ValueError(f"attempt_limit:{len(attempts)}>{args.max_attempts}")
    selected_ids = [row["instance_id"].split("::", 1)[0] for row in attempts]
    selected_tables = [
        str(instances[row["instance_id"]]["table_uid"])
        for row in attempts
    ]
    exposure = check_exposure(
        selected_ids,
        selected_tables,
        args.exposure_manifest,
        allow_development_exposure=args.allow_development_exposure,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "EXPOSURE_RECEIPT_V1.json", exposure)

    if not args.model_path or not args.adapter_root:
        raise ValueError("model_path_and_adapter_root_required_for_run")
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

    rows = []
    terminal_instruction = str(
        protocol.get("terminal_instruction", TERMINAL_INSTRUCTION)
    )
    for protocol_row in attempts:
        protocol_row = {
            **protocol_row,
            "max_new_tokens": int(
                protocol_row.get("max_new_tokens", protocol.get("max_new_tokens", 64))
            ),
            "terminal_instruction_text": terminal_instruction,
        }
        instance = instances[protocol_row["instance_id"]]
        frozen_row = next(row for row in frozen if row["instance_id"] == instance["instance_id"])
        prompt = standardized_prompt(
            instance,
            str(frozen_row["generated_text"]),
            protocol_row["payload"],
            terminal_instruction,
        )
        result = actual_generation_row(model, tokenizer, instance, prompt, protocol_row)
        rows.append(semantic_enrich(result, instance))
        write_jsonl(args.output_dir / "revision_operator_rows_v1.partial.jsonl", rows)
        print(f"{protocol_row['attempt_id']}: {len(rows)}/{len(attempts)}", flush=True)
    write_jsonl(args.output_dir / "revision_operator_rows_v1.jsonl", rows)
    summary = summarize(rows, exposure)
    summary["input_sha256"] = {
        "instances": hashlib.sha256(args.instances.read_bytes()).hexdigest(),
        "frozen_results": hashlib.sha256(args.frozen_results.read_bytes()).hexdigest(),
        "protocol": hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
        "base_protocol": (
            hashlib.sha256(
                (args.protocol.parent / str(protocol["base_protocol"])).read_bytes()
            ).hexdigest()
            if protocol.get("base_protocol") else None
        ),
    }
    write_json(args.output_dir / "REVISION_OPERATOR_DIAGNOSTIC_V1.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
