"""Oracle-assisted localization upper bound for development diagnosis only."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from same_candidate_feedback_a_v1 import (
    expected_discrepancies,
    load_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
)

from run_natural_program_experiment_v2 import generate_and_score_batch


def diagnostic_feedback(
    instance: dict[str, Any],
    previous_text: str,
    initial_correct: bool,
) -> str:
    if initial_correct:
        categories = []
        guidance = (
            "No numerical correction is required for the previous candidate. "
            "Retain it unless the visible evidence contains a direct contradiction."
        )
    else:
        discrepancy = expected_discrepancies(instance, previous_text)
        categories = [
            category for category in discrepancy["categories"]
            if category != "numeric_mismatch"
        ]
        guidance = (
            "The previous candidate is numerically wrong. Its discrepancy class is listed above. "
            "Find the visible evidence and make at most one correction."
        )
    return "\n".join([
        "Feedback type: oracle-assisted development localization upper bound.",
        "This is not a deployable method and is not a confirmation result. It uses hidden reference status only to diagnose whether the model can follow a correct error class.",
        f"Diagnostic discrepancy classes: {json.dumps(categories, ensure_ascii=False)}",
        "The diagnostic intentionally omits the correct answer, correct program, and correct evidence references.",
        guidance,
        "Return exactly one JSON object with program, evidence_refs, and unit; do not return a numeric answer.",
    ])


def revision_prompt(
    instance: dict[str, Any],
    previous_text: str,
    initial_correct: bool,
) -> str:
    return (
        f"{instance['prompt']}\n\n"
        "You previously returned the following candidate.\n\n"
        f"Previous candidate:\n{previous_text}\n\n"
        f"{diagnostic_feedback(instance, previous_text, initial_correct)}"
    )


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
    frozen = [
        row for row in load_jsonl(args.frozen_results)
        if row.get("model_arm") == "ordinary_answer_execution_sft"
    ]
    if len(frozen) != 72:
        raise ValueError(f"expected_72_frozen_candidates:{len(frozen)}")
    selected = []
    for row in frozen:
        instance = instances[row["instance_id"]]
        selected.append({
            **instance,
            "instance_id": f"{row['instance_id']}::oracle_localization_diagnostic_a_v3",
            "base_instance_id": row["instance_id"],
            "condition": "oracle_localization_diagnostic_a_v3",
            "slice": "oracle_assisted_development_diagnostic_a_v3",
            "prompt": revision_prompt(
                instance,
                str(row["generated_text"]),
                bool(row["program_correct"]),
            ),
            "previous_candidate": str(row["generated_text"]),
            "feedback_only_visible": False,
            "oracle_assisted": True,
        })
    args.run_root.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.run_root / "oracle_localization_instances_a_v3.jsonl", selected)

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
    started = time.time()
    for start in range(0, len(selected), args.batch_size):
        batch = selected[start : start + args.batch_size]
        output = generate_and_score_batch(model, tokenizer, batch, args.max_new_tokens)
        for item, result in zip(batch, output):
            result["condition"] = "oracle_localization_diagnostic_a_v3"
            result["base_instance_id"] = item["base_instance_id"]
            result["previous_candidate"] = item["previous_candidate"]
            result["model_arm"] = "ordinary_answer_execution_sft"
            result["oracle_assisted"] = True
            rows.append(result)
        with (args.run_root / "oracle_localization_results_a_v3.partial.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as handle:
            for result in output:
                handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"oracle_localization_diagnostic_a_v3: {len(rows)}/{len(selected)}", flush=True)
    write_jsonl(args.run_root / "oracle_localization_results_a_v3.jsonl", rows)
    write_json(args.run_root / "ORACLE_LOCALIZATION_RECEIPT_A_V3.json", {
        "schema": "oracle_localization_receipt_a_v3",
        "identity": "ORACLE_ASSISTED_DEVELOPMENT_DIAGNOSTIC_NOT_DEPLOYABLE_NOT_CONFIRMATION",
        "hidden_reference_diagnostic_features": ["initial_correctness", "discrepancy_classes"],
        "hidden_answer_or_program_in_prompt": False,
        "attempts": len(rows),
        "prompt_tokens": sum(int(row["prompt_tokens"]) for row in rows),
        "completion_tokens": sum(int(row["completion_tokens"]) for row in rows),
        "wall_seconds": time.time() - started,
        "max_new_tokens": args.max_new_tokens,
        "results_sha256": sha256_file(args.run_root / "oracle_localization_results_a_v3.jsonl"),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
