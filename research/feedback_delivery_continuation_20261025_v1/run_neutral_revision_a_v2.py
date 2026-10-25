"""Run the corrected neutral-revision condition for Experiment A."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from same_candidate_feedback_a_v1 import (
    load_jsonl,
    revision_prompt,
    sha256_file,
    write_json,
    write_jsonl,
)

from run_natural_program_experiment_v2 import generate_and_score_batch


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
            "instance_id": f"{row['instance_id']}::ordinary_retry",
            "base_instance_id": row["instance_id"],
            "condition": "ordinary_retry",
            "slice": "same_candidate_feedback_a_v2_neutral_revision",
            "prompt": revision_prompt(
                instance,
                str(row["generated_text"]),
                "ordinary_retry",
            ),
            "previous_candidate": str(row["generated_text"]),
            "feedback_only_visible": False,
        })
    args.run_root.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.run_root / "neutral_revision_instances_a_v2.jsonl", selected)

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
            result["condition"] = "ordinary_retry"
            result["base_instance_id"] = item["base_instance_id"]
            result["previous_candidate"] = item["previous_candidate"]
            result["model_arm"] = "ordinary_answer_execution_sft"
            rows.append(result)
        with (args.run_root / "neutral_revision_results_a_v2.partial.jsonl").open(
            "a", encoding="utf-8", newline="\n"
        ) as handle:
            for result in output:
                handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"ordinary_retry: {len(rows)}/{len(selected)}", flush=True)
    write_jsonl(args.run_root / "neutral_revision_results_a_v2.jsonl", rows)
    write_json(args.run_root / "NEUTRAL_REVISION_RECEIPT_A_V2.json", {
        "schema": "neutral_revision_receipt_a_v2",
        "identity": "FROZEN_CANDIDATE_STANDARD_NEUTRAL_REVISION_WITHOUT_TARGETED_FEEDBACK",
        "attempts": len(rows),
        "prompt_tokens": sum(int(row["prompt_tokens"]) for row in rows),
        "completion_tokens": sum(int(row["completion_tokens"]) for row in rows),
        "wall_seconds": time.time() - started,
        "max_new_tokens": args.max_new_tokens,
        "results_sha256": sha256_file(args.run_root / "neutral_revision_results_a_v2.jsonl"),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
