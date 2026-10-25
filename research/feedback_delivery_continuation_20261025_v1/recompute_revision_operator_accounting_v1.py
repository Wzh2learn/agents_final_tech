"""Recompute actual prompt and completion token accounting for the diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from revision_operator_diagnostic_v1 import (
    TERMINAL_INSTRUCTION,
    load_jsonl,
    standardized_prompt,
    write_json,
)


def load_protocol(path: Path) -> tuple[dict, list[dict]]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    base = None
    if "attempts" not in protocol and protocol.get("base_protocol"):
        base = json.loads(
            (path.parent / str(protocol["base_protocol"])).read_text(encoding="utf-8")
        )
    source = base or protocol
    attempts = source["attempts"]
    if protocol.get("attempt_ids"):
        wanted = set(protocol["attempt_ids"])
        attempts = [row for row in attempts if row["attempt_id"] in wanted]
    return {**source, **protocol}, attempts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--frozen-results", type=Path, required=True)
    parser.add_argument("--base-protocol", type=Path, required=True)
    parser.add_argument("--v2-protocol", type=Path, required=True)
    parser.add_argument("--v3-protocol", type=Path, required=True)
    parser.add_argument("--v1-rows", type=Path, required=True)
    parser.add_argument("--v2-rows", type=Path, required=True)
    parser.add_argument("--v3-rows", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    instances = {row["instance_id"]: row for row in load_jsonl(args.instances)}
    frozen = {
        row["instance_id"]: row
        for row in load_jsonl(args.frozen_results)
        if row.get("model_arm") == "ordinary_answer_execution_sft"
    }
    protocols = [
        ("v1", args.base_protocol),
        ("v2_control", args.v2_protocol),
        ("v3_mechanism", args.v3_protocol),
    ]
    row_paths = {
        "v1": args.v1_rows,
        "v2_control": args.v2_rows,
        "v3_mechanism": args.v3_rows,
    }
    events = []
    total_prompt = 0
    total_completion = 0
    total_attempts = 0
    for name, protocol_path in protocols:
        protocol, attempts = load_protocol(protocol_path)
        by_id = {row["attempt_id"]: row for row in attempts}
        rows = load_jsonl(row_paths[name])
        prompt_tokens = 0
        completion_tokens = 0
        for row in rows:
            spec = by_id[row["attempt_id"]]
            instance = instances[row["instance_id"]]
            prompt = standardized_prompt(
                instance,
                str(frozen[row["instance_id"]]["generated_text"]),
                spec["payload"],
                str(protocol.get("terminal_instruction", TERMINAL_INSTRUCTION)),
            )
            prompt_tokens += len(tokenizer(prompt)["input_ids"])
            completion_tokens += int(row["actual_completion_tokens"])
        total_prompt += prompt_tokens
        total_completion += completion_tokens
        total_attempts += len(rows)
        events.append({
            "id": f"REVISION_OPERATOR_DIAGNOSTIC_{name.upper()}",
            "attempts": len(rows),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "accounting_tokens": prompt_tokens + completion_tokens,
            "rows_sha256": hashlib.sha256(row_paths[name].read_bytes()).hexdigest(),
        })
    receipt = {
        "schema": "revision_operator_resource_receipt_v1",
        "date": "2026-10-25",
        "events": events,
        "runner_failures_before_generation": 1,
        "accounting_attempts": total_attempts,
        "physical_generation_calls": total_attempts,
        "local_batched_generate_calls": total_attempts,
        "prompt_tokens": total_prompt,
        "actual_non_padding_completion_tokens": total_completion,
        "accounting_tokens": total_prompt + total_completion,
        "new_training_runs": 0,
        "new_judge_calls": 0,
        "new_http_calls": 0,
    }
    write_json(args.output, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
