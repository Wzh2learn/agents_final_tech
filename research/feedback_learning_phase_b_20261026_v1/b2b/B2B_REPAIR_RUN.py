"""Execute and analyze the bounded B2B R/E output-budget repair."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
B2_DIR = OUT_DIR.parent / "b2"
PRIOR_DIR = OUT_DIR.parent
HELPERS = ROOT / "research/natural_program_learning_20261024_v2"
sys.path.insert(0, str(B2_DIR))
sys.path.insert(0, str(PRIOR_DIR))
sys.path.insert(0, str(HELPERS))

import B2_TRAIN_RUN as b2  # noqa: E402


TASK_ID = "phaseb-b2b-output-repair-a-20261026"
GOAL_ID = "FEEDBACK_LEARNING_PHASE_B_20261026"
PARENT_B2_TASK_ID = "phaseb-b2-same-start-a-20261026"
SEED = 20261026
MAX_NEW_TOKENS = 384
GENERATION_BATCH = 8
ATTEMPTS_PER_ARM = 36
REPAIR_ATTEMPT_BUDGET = 72
REPAIR_TOKEN_BUDGET = 180000
CONTRACT_SUFFIX = (
    "\nFinal response must be exactly one JSON object and no prose, Markdown "
    "fences, bullets, or explanation."
)
ARMS = ("R_FULL_REVISION", "E_RESTRICTED_PATCH")

D_DECISION_PATH = PRIOR_DIR / "B2B_D_OUTPUT_BUDGET_REPAIR_DECISION.md"
B2_PROTOCOL_PATH = B2_DIR / "B2_PROTOCOL_FROZEN.json"
B2_PANEL_PATH = PRIOR_DIR / "B2_DEVELOPMENT_PANEL_DRAFT.json"
B2_RAW_PATH = B2_DIR / "B2_DEVELOPMENT_RAW.jsonl"
B2_GENERATION_RECEIPT_PATH = B2_DIR / "run/generation_receipt.json"
B2_PARTIAL_FAILURES_PATH = B2_DIR / "B2_EVALUATION_PARTIAL_FAILURES.json"
R_RECEIPT_PATH = B2_DIR / "B2_TRAINING_RECEIPT_R.json"
E_RECEIPT_PATH = B2_DIR / "B2_TRAINING_RECEIPT_E.json"

PROTOCOL_PATH = OUT_DIR / "B2B_PROTOCOL_FROZEN.json"
RAW_PATH = OUT_DIR / "B2B_GENERATION_RAW.jsonl"
GENERATION_RECEIPT_PATH = OUT_DIR / "B2B_GENERATION_RECEIPT.json"
ANALYSIS_PATH = OUT_DIR / "B2B_DEVELOPMENT_ANALYSIS.json"
FAILURES_PATH = OUT_DIR / "B2B_FAILURES.json"
TASK_RESULT_PATH = OUT_DIR / "TASK_RESULT_A_B2B.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def object_hash(value: Any) -> str:
    return sha256_bytes(b2.canonical_json(value).encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def adapter_hashes(path: Path) -> dict[str, str]:
    return {
        name: sha256_file(path / name)
        for name in ("adapter_config.json", "adapter_model.safetensors")
    }


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{label}".encode()).hexdigest()[:8], 16)


def validate_authority() -> dict[str, Any]:
    allowed_paths = [
        D_DECISION_PATH,
        B2_PROTOCOL_PATH,
        B2_PANEL_PATH,
        B2_RAW_PATH,
        B2_GENERATION_RECEIPT_PATH,
        B2_PARTIAL_FAILURES_PATH,
        R_RECEIPT_PATH,
        E_RECEIPT_PATH,
        b2.TRAJECTORY_PATH,
    ]
    if any("confirmation" in str(path).lower() for path in allowed_paths):
        raise RuntimeError("confirmation_artifact_in_authority_set")
    protocol = load_json(B2_PROTOCOL_PATH)
    if protocol.get("confirmation_outputs_inspected") is not False:
        raise RuntimeError("b2_confirmation_inspection_state_invalid")
    return {
        "checked_paths": [str(path) for path in allowed_paths],
        "confirmation_artifact_paths_accessed": [],
        "confirmation_outputs_inspected": False,
    }


def validate_adapters(protocol: dict[str, Any]) -> dict[str, Any]:
    parent_path = Path(protocol["parent_checkpoint"]["adapter_path"])
    expected_parent = protocol["parent_checkpoint"]["adapter_file_sha256"]
    observed_parent = adapter_hashes(parent_path)
    if observed_parent != {
        name: expected_parent[name]
        for name in observed_parent
    }:
        raise RuntimeError("parent_adapter_hash_mismatch")

    receipt_hashes = {}
    for arm, receipt_path in (("R", R_RECEIPT_PATH), ("E", E_RECEIPT_PATH)):
        receipt = load_json(receipt_path)
        if receipt.get("status") != "PASS" or receipt.get("arm") != {
            "R": "R_FULL_REVISION",
            "E": "E_RESTRICTED_PATCH",
        }[arm]:
            raise RuntimeError(f"training_receipt_not_pass:{arm}")
        child = receipt["child_adapter"]
        child_path = Path(child["adapter_path"])
        observed_child = adapter_hashes(child_path)
        if observed_child != child["adapter_file_sha256"]:
            raise RuntimeError(f"child_adapter_hash_mismatch:{arm}")
        if adapter_hashes(parent_path) != {
            name: receipt["parent_checkpoint"]["adapter_file_sha256"][name]
            for name in observed_parent
        }:
            raise RuntimeError(f"receipt_parent_hash_mismatch:{arm}")
        receipt_hashes[arm] = {
            "receipt_path": str(receipt_path),
            "receipt_sha256": sha256_file(receipt_path),
            "adapter_path": str(child_path),
            "adapter_file_sha256": observed_child,
        }
    return {
        "parent": {
            "adapter_path": str(parent_path),
            "adapter_file_sha256": observed_parent,
        },
        "children": receipt_hashes,
        "match_b2_receipts": True,
    }


def validate_panel() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    items, panel = b2.panel_trajectories()
    expected_panel_hash = load_json(B2_PROTOCOL_PATH)["development_panel"]["sha256"]
    observed_panel_hash = sha256_file(B2_PANEL_PATH)
    if observed_panel_hash != expected_panel_hash:
        raise RuntimeError("panel_hash_changed")
    if len(items) != 36 or panel["family_count"] != 12:
        raise RuntimeError("panel_shape_changed")
    trajectory_index = {
        row["source_identity"]["instance_id"]: row
        for row in load_jsonl(b2.TRAJECTORY_PATH)
    }
    mismatches = []
    for item in items:
        trajectory_id = item["trajectory_id"]
        trajectory = item["trajectory"]
        variant = trajectory["source_identity"]["variant"]
        expected = item["family"]["trajectory_sha256"][variant]
        observed = object_hash(trajectory)
        if observed != expected:
            mismatches.append(trajectory_id)
        if trajectory_index.get(trajectory_id) != trajectory:
            mismatches.append(trajectory_id)
    if mismatches:
        raise RuntimeError(f"panel_trajectory_hash_mismatch:{sorted(set(mismatches))}")
    return items, panel, {
        "panel_path": str(B2_PANEL_PATH),
        "panel_sha256": observed_panel_hash,
        "family_count": 12,
        "trajectory_count": 36,
        "trajectory_hashes_match": True,
    }


def validate_comparators(items: list[dict[str, Any]]) -> dict[str, Any]:
    raw_hash = sha256_file(B2_RAW_PATH)
    generation_receipt = load_json(B2_GENERATION_RECEIPT_PATH)
    if raw_hash != generation_receipt["raw_sha256"]:
        raise RuntimeError("first_run_raw_hash_mismatch")
    rows = load_jsonl(B2_RAW_PATH)
    expected_ids = {item["trajectory_id"] for item in items}
    for arm in ("O_FROZEN_ORDINARY", "N_NEUTRAL_RETRY"):
        arm_rows = [row for row in rows if row["arm"] == arm]
        if len(arm_rows) != 36 or {row["trajectory_id"] for row in arm_rows} != expected_ids:
            raise RuntimeError(f"comparator_panel_mismatch:{arm}")
    return {
        "first_run_raw_path": str(B2_RAW_PATH),
        "first_run_raw_sha256": raw_hash,
        "first_run_generation_receipt_path": str(B2_GENERATION_RECEIPT_PATH),
        "first_run_generation_receipt_sha256": sha256_file(B2_GENERATION_RECEIPT_PATH),
        "first_run_partial_failures_path": str(B2_PARTIAL_FAILURES_PATH),
        "first_run_partial_failures_sha256": sha256_file(B2_PARTIAL_FAILURES_PATH),
        "reused_arms": ["O_FROZEN_ORDINARY", "N_NEUTRAL_RETRY"],
        "new_generation_attempts_for_comparators": 0,
    }


def repaired_prompt(item: dict[str, Any], arm: str) -> str:
    trajectory = item["trajectory"]
    prompt = b2.target_prompt(
        trajectory["visible_input"],
        trajectory["o_output"]["parsed_candidate"],
        arm,
    )
    return prompt + CONTRACT_SUFFIX


def budget_projection(items: list[dict[str, Any]]) -> dict[str, Any]:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(b2.BASE_MODEL)
    projections = {}
    total_prompt_tokens = 0
    padded_prompt_positions = 0
    for arm in ARMS:
        prompts = [repaired_prompt(item, arm) for item in items]
        lengths = [
            len(tokenizer(prompt, add_special_tokens=True)["input_ids"])
            for prompt in prompts
        ]
        prompt_tokens = sum(lengths)
        padded = sum(
            max(lengths[start : start + GENERATION_BATCH])
            * len(lengths[start : start + GENERATION_BATCH])
            for start in range(0, len(lengths), GENERATION_BATCH)
        )
        total_prompt_tokens += prompt_tokens
        padded_prompt_positions += padded
        projections[arm] = {
            "attempts": len(prompts),
            "prompt_tokens": prompt_tokens,
            "padded_prompt_positions": padded,
            "max_possible_completion_tokens": ATTEMPTS_PER_ARM * MAX_NEW_TOKENS,
            "max_possible_total_tokens": prompt_tokens
            + ATTEMPTS_PER_ARM * MAX_NEW_TOKENS,
        }
    conservative_cap = total_prompt_tokens + REPAIR_ATTEMPT_BUDGET * MAX_NEW_TOKENS
    padded_cap = padded_prompt_positions + REPAIR_ATTEMPT_BUDGET * MAX_NEW_TOKENS
    if REPAIR_ATTEMPT_BUDGET != ATTEMPTS_PER_ARM * len(ARMS):
        raise RuntimeError("repair_attempt_budget_not_enforced")
    if conservative_cap > REPAIR_TOKEN_BUDGET or padded_cap > REPAIR_TOKEN_BUDGET:
        raise RuntimeError("repair_token_budget_not_enforceable_before_generation")
    return {
        "attempts": REPAIR_ATTEMPT_BUDGET,
        "max_new_tokens_per_attempt": MAX_NEW_TOKENS,
        "max_possible_completion_tokens": REPAIR_ATTEMPT_BUDGET * MAX_NEW_TOKENS,
        "prompt_tokens": total_prompt_tokens,
        "max_possible_logical_generation_tokens": conservative_cap,
        "padded_prompt_positions": padded_prompt_positions,
        "max_possible_padded_input_plus_completion_tokens": padded_cap,
        "generation_token_budget": REPAIR_TOKEN_BUDGET,
        "remaining_token_headroom": REPAIR_TOKEN_BUDGET - conservative_cap,
        "enforced_before_generation": True,
        "arms": projections,
    }


def preflight() -> dict[str, Any]:
    authority = validate_authority()
    protocol = load_json(B2_PROTOCOL_PATH)
    adapters = validate_adapters(protocol)
    items, panel, panel_receipt = validate_panel()
    comparators = validate_comparators(items)
    budget = budget_projection(items)
    if RAW_PATH.exists() or GENERATION_RECEIPT_PATH.exists():
        raise RuntimeError("scientific_output_preexists")
    payload = {
        "schema": "b2b_protocol_frozen_v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_B2_TASK_ID,
        "goal_id": GOAL_ID,
        "status": "FROZEN_BEFORE_REPAIRED_GENERATION",
        "frozen_at": utc_now(),
        "authority": {
            "d_decision_path": str(D_DECISION_PATH),
            "d_decision_sha256": sha256_file(D_DECISION_PATH),
            "b2_protocol_path": str(B2_PROTOCOL_PATH),
            "b2_protocol_sha256": sha256_file(B2_PROTOCOL_PATH),
        },
        "same_artifacts": {
            "parent_and_child_adapters": adapters,
            "development_panel": panel_receipt,
            "comparators": comparators,
            "no_retraining": True,
            "training_runs": 0,
            "training_tokens": 0,
        },
        "development_panel": {
            "role": "EXPOSED_DEVELOPMENT_SUPERVISION",
            "families": panel["family_count"],
            "trajectories": panel["trajectory_count"],
            "confirmation_claim": "NONE",
        },
        "generation": {
            "arms": list(ARMS),
            "trajectories_per_arm": ATTEMPTS_PER_ARM,
            "attempts": REPAIR_ATTEMPT_BUDGET,
            "max_new_tokens": MAX_NEW_TOKENS,
            "batch_size": GENERATION_BATCH,
            "do_sample": False,
            "decoding": "GREEDY_SAME_AS_FROZEN_B2_R_E",
            "same_prompt_except_contract_only_suffix": True,
            "contract_only_suffix": CONTRACT_SUFFIX,
            "budget_projection": budget,
            "token_budget": REPAIR_TOKEN_BUDGET,
            "attempt_budget": REPAIR_ATTEMPT_BUDGET,
        },
        "primary_estimand": {
            "name": "SET_BINDING_SET_ACCURACY",
            "unit": "TRAJECTORY_VARIANT_ROW",
            "paired_aggregation": (
                "mean row-level paired difference within each source family, "
                "then mean across 12 source families"
            ),
            "bootstrap_unit": "SOURCE_FAMILY",
            "bootstrap_samples": 20000,
            "answer_correctness_scored": False,
        },
        "secondary_paired_completion": {
            "name": "ALL_THREE_VARIANTS_CORRECT",
            "status": "SEPARATE_DIAGNOSTIC_NOT_PRIMARY",
            "bootstrap_unit": "SOURCE_FAMILY",
        },
        "diagnostics_kept_separate": [
            "syntax_source",
            "contract_only_output",
            "patch_legality",
            "semantic_tool_failure",
            "candidate_semantics",
            "delivery",
            "O_transitions",
            "cost",
        ],
        "stop_conditions": {
            "parent_child_adapter_hash_mismatch": "STOP_BEFORE_GENERATION",
            "panel_hash_change": "STOP_BEFORE_GENERATION",
            "confirmation_artifact_read": "STOP_BEFORE_GENERATION",
            "repair_budget_not_enforceable": "STOP_BEFORE_GENERATION",
            "pervasive_interface_definition": (
                "either R or E has more than 18 of 36 syntax-adapter failures "
                "or more than 18 of 36 interface-caused UNKNOWN deliveries"
            ),
            "method_gate": load_json(B2_PROTOCOL_PATH)[
                "thresholds_from_B1_gate"
            ],
        },
        "claim_boundaries": {
            "feedback_derived_learning": "NOT_QUALIFIED",
            "answer_correctness": "NOT_SCORED",
            "new_source_generalization": "NOT_TESTED",
            "confirmation_claim": "NONE",
        },
        "authority_read_receipt": authority,
    }
    write_json(PROTOCOL_PATH, payload)
    return payload


def require_protocol() -> dict[str, Any]:
    protocol = load_json(PROTOCOL_PATH)
    if protocol.get("status") != "FROZEN_BEFORE_REPAIRED_GENERATION":
        raise RuntimeError("b2b_protocol_not_frozen")
    if protocol["same_artifacts"]["development_panel"]["panel_sha256"] != sha256_file(
        B2_PANEL_PATH
    ):
        raise RuntimeError("panel_changed_after_freeze")
    validate_adapters(load_json(B2_PROTOCOL_PATH))
    validate_authority()
    return protocol


def generation_row(
    row: dict[str, Any],
    arm: str,
    item: dict[str, Any],
    generated_text: str,
    syntax_source: str,
    generation: dict[str, Any],
    evaluation: dict[str, Any],
    target_identity: str,
) -> dict[str, Any]:
    row["schema"] = "b2b_generation_raw_v1"
    row["task_id"] = TASK_ID
    row["parent_task_id"] = PARENT_B2_TASK_ID
    row["arm"] = arm
    row["raw_generated_text"] = generated_text
    row["syntax_source"] = syntax_source
    row["generation"] = generation
    row["evaluation"] = evaluation
    row["target_identity"] = target_identity
    return row


def generate_batch(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
) -> list[dict[str, Any]]:
    import torch

    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    torch.manual_seed(SEED)
    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        add_special_tokens=True,
    ).to(model.device)
    input_width = int(inputs["input_ids"].shape[1])
    started = time.time()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.time() - started
    rows = []
    for index, prompt in enumerate(prompts):
        token_ids = output[index][input_width:].tolist()
        finish_reason = "MAX_NEW_TOKENS"
        if tokenizer.eos_token_id in token_ids:
            stop_index = token_ids.index(tokenizer.eos_token_id)
            token_ids = token_ids[: stop_index + 1]
            finish_reason = "EOS"
        generated_text = tokenizer.decode(token_ids, skip_special_tokens=True)
        rows.append(
            {
                "generated_text": generated_text,
                "raw_token_count": len(token_ids),
                "generated_token_sha256": sha256_bytes(
                    json.dumps(token_ids, separators=(",", ":")).encode("utf-8")
                ),
                "completion_tokens": len(token_ids),
                "completion_tokens_before_stop": max(
                    0, len(token_ids) - int(finish_reason == "EOS")
                ),
                "finish_reason": finish_reason,
                "truncated_at_max_new_tokens": finish_reason
                == "MAX_NEW_TOKENS",
                "prompt_tokens": int(inputs["attention_mask"][index].sum().item()),
                "batch_prompt_positions": input_width * len(prompts),
                "latency_ms": elapsed * 1000.0 / len(prompts),
                "batch_latency_ms": elapsed * 1000.0,
                "batch_size": len(prompts),
                "do_sample": False,
                "seed": SEED,
                "max_new_tokens": MAX_NEW_TOKENS,
            }
        )
    return rows


def generate() -> int:
    require_protocol()
    if RAW_PATH.exists() or GENERATION_RECEIPT_PATH.exists():
        raise RuntimeError("scientific_output_preexists")
    items, _ = b2.panel_trajectories()
    for item in items:
        trajectory = item["trajectory"]
        _, patched = b2.materialized_targets(trajectory)
        trajectory["structural_target"] = patched

    rows: list[dict[str, Any]] = []
    arm_totals: dict[str, Any] = {}
    for arm in ARMS:
        arm_started = time.time()
        receipt = load_json(B2_DIR / f"B2_TRAINING_RECEIPT_{arm[0]}.json")
        adapter_path = Path(receipt["child_adapter"]["adapter_path"])
        active_name = "b2_child_r" if arm == "R_FULL_REVISION" else "b2_child_e"
        model, tokenizer = b2.model_for_arm(adapter_path, active_name)
        prompts = [repaired_prompt(item, arm) for item in items]
        arm_rows: list[dict[str, Any]] = []
        for start in range(0, len(items), GENERATION_BATCH):
            batch_items = items[start : start + GENERATION_BATCH]
            batch_prompts = prompts[start : start + GENERATION_BATCH]
            generated = generate_batch(model, tokenizer, batch_prompts)
            for item, generation in zip(batch_items, generated):
                trajectory = item["trajectory"]
                desired = trajectory["correction"]["set_binding_component"][
                    "desired_reference_set"
                ]
                parsed, syntax_source = b2.parse_object(generation["generated_text"])
                if arm == "R_FULL_REVISION":
                    evaluation = (
                        b2.evaluate_generated_candidate(
                            parsed,
                            trajectory,
                            desired,
                        )
                        if parsed is not None
                        else {
                            "delivered_candidate": None,
                            "SET_BINDING_SET_ACCURACY": False,
                            "syntax_adapter_failure": True,
                        }
                    )
                    target_identity = (
                        "MATERIALIZED_SET_BINDING_TARGET"
                        if trajectory["correction"]["set_binding_component"][
                            "status"
                        ]
                        == "QUALIFIED"
                        else "O_NO_OP_OR_UNRESOLVED"
                    )
                else:
                    evaluation = (
                        b2.evaluate_generated_patch(
                            parsed,
                            trajectory,
                            desired,
                        )
                        if parsed is not None
                        else {
                            "patch_legal": False,
                            "patch_failure": "PATCH_JSON_NOT_PARSEABLE",
                            "delivered_candidate": None,
                            "SET_BINDING_SET_ACCURACY": False,
                        }
                    )
                    target_identity = (
                        "RESTRICTED_REFERENCE_DERIVED_PATCH"
                        if trajectory["correction"]["set_binding_component"][
                            "status"
                        ]
                        == "QUALIFIED"
                        else "EMPTY_PATCH_NO_OP"
                    )
                row = b2.raw_row(
                    arm=arm,
                    item=item,
                    generated_text=generation["generated_text"],
                    syntax_source=syntax_source,
                    generation=generation,
                    evaluation=evaluation,
                    target_identity=target_identity,
                )
                arm_rows.append(
                    generation_row(
                        row,
                        arm,
                        item,
                        generation["generated_text"],
                        syntax_source,
                        generation,
                        evaluation,
                        target_identity,
                    )
                )
            with RAW_PATH.open("a", encoding="utf-8", newline="\n") as handle:
                for row in arm_rows[-len(batch_items) :]:
                    handle.write(
                        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                    )
            actual_tokens = sum(
                row["generation"].get("prompt_tokens", 0)
                + row["generation"].get("completion_tokens", 0)
                for row in rows
            ) + sum(
                row["generation"].get("prompt_tokens", 0)
                + row["generation"].get("completion_tokens", 0)
                for row in arm_rows
            )
            if actual_tokens > REPAIR_TOKEN_BUDGET:
                raise RuntimeError("repair_token_budget_exceeded")
        del model
        gc.collect()
        import torch

        torch.cuda.empty_cache()
        arm_totals[arm] = {
            "rows": len(arm_rows),
            "new_generation_attempts": len(arm_rows),
            "prompt_tokens": sum(
                row["generation"]["prompt_tokens"] for row in arm_rows
            ),
            "completion_tokens": sum(
                row["generation"]["completion_tokens"] for row in arm_rows
            ),
            "padded_prompt_positions": sum(
                row["generation"]["batch_prompt_positions"]
                / row["generation"]["batch_size"]
                for row in arm_rows
            ),
            "finish_reason": dict(
                Counter(row["generation"]["finish_reason"] for row in arm_rows)
            ),
            "wall_seconds": time.time() - arm_started,
        }
        rows.extend(arm_rows)
    if len(rows) != REPAIR_ATTEMPT_BUDGET:
        raise RuntimeError(f"raw_row_count:{len(rows)}")
    new_attempts = sum(arm["new_generation_attempts"] for arm in arm_totals.values())
    new_tokens = sum(
        arm["prompt_tokens"] + arm["completion_tokens"] for arm in arm_totals.values()
    )
    padded_tokens = sum(
        arm["padded_prompt_positions"] + arm["completion_tokens"]
        for arm in arm_totals.values()
    )
    if new_attempts != REPAIR_ATTEMPT_BUDGET:
        raise RuntimeError("repair_attempt_budget_mismatch")
    if new_tokens > REPAIR_TOKEN_BUDGET or padded_tokens > REPAIR_TOKEN_BUDGET:
        raise RuntimeError("repair_token_budget_exceeded")
    write_json(
        GENERATION_RECEIPT_PATH,
        {
            "schema": "b2b_generation_receipt_v1",
            "task_id": TASK_ID,
            "goal_id": GOAL_ID,
            "status": "PASS",
            "arms": arm_totals,
            "new_generation_attempts": new_attempts,
            "new_generation_tokens": new_tokens,
            "new_generation_padded_input_plus_completion_tokens": padded_tokens,
            "attempt_budget": REPAIR_ATTEMPT_BUDGET,
            "token_budget": REPAIR_TOKEN_BUDGET,
            "attempt_budget_remaining": REPAIR_ATTEMPT_BUDGET - new_attempts,
            "token_budget_remaining": REPAIR_TOKEN_BUDGET - new_tokens,
            "raw_path": str(RAW_PATH),
            "raw_sha256": sha256_file(RAW_PATH),
            "protocol_sha256": sha256_file(PROTOCOL_PATH),
            "training_runs": 0,
            "training_tokens": 0,
            "scientific_generation_failures": 0,
            "finished_at": utc_now(),
        },
    )
    return 0


def recover_generation_receipt_from_raw() -> int:
    require_protocol()
    if RAW_PATH.exists() is False:
        raise RuntimeError("raw_output_missing")
    rows = load_jsonl(RAW_PATH)
    if len(rows) != REPAIR_ATTEMPT_BUDGET:
        raise RuntimeError(f"raw_recovery_row_count:{len(rows)}")
    arm_totals: dict[str, Any] = {}
    for arm in ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm]
        if len(arm_rows) != ATTEMPTS_PER_ARM:
            raise RuntimeError(f"raw_recovery_arm_count:{arm}")
        wall_seconds = 0.0
        batch_started = False
        for index, row in enumerate(arm_rows):
            same_batch_continuation = (
                batch_started
                and row["generation"]["batch_size"]
                == arm_rows[index - 1]["generation"]["batch_size"]
                and row["generation"]["batch_latency_ms"]
                == arm_rows[index - 1]["generation"][
                    "batch_latency_ms"
                ]
            )
            if not same_batch_continuation:
                wall_seconds += row["generation"]["batch_latency_ms"] / 1000.0
            batch_started = True
        arm_totals[arm] = {
            "rows": len(arm_rows),
            "new_generation_attempts": len(arm_rows),
            "prompt_tokens": sum(
                row["generation"]["prompt_tokens"] for row in arm_rows
            ),
            "completion_tokens": sum(
                row["generation"]["completion_tokens"] for row in arm_rows
            ),
            "padded_prompt_positions": sum(
                row["generation"]["batch_prompt_positions"]
                / row["generation"]["batch_size"]
                for row in arm_rows
            ),
            "finish_reason": dict(
                Counter(row["generation"]["finish_reason"] for row in arm_rows)
            ),
            "wall_seconds": wall_seconds,
        }
    new_attempts = sum(arm["new_generation_attempts"] for arm in arm_totals.values())
    new_tokens = sum(
        arm["prompt_tokens"] + arm["completion_tokens"] for arm in arm_totals.values()
    )
    padded_tokens = sum(
        arm["padded_prompt_positions"] + arm["completion_tokens"]
        for arm in arm_totals.values()
    )
    if new_attempts != REPAIR_ATTEMPT_BUDGET:
        raise RuntimeError("repair_attempt_budget_mismatch")
    if new_tokens > REPAIR_TOKEN_BUDGET or padded_tokens > REPAIR_TOKEN_BUDGET:
        raise RuntimeError("repair_token_budget_exceeded")
    write_json(
        GENERATION_RECEIPT_PATH,
        {
            "schema": "b2b_generation_receipt_v1",
            "task_id": TASK_ID,
            "goal_id": GOAL_ID,
            "status": "PASS_WITH_POST_GENERATION_ACCOUNTING_RECOVERY",
            "arms": arm_totals,
            "new_generation_attempts": new_attempts,
            "new_generation_tokens": new_tokens,
            "new_generation_padded_input_plus_completion_tokens": padded_tokens,
            "attempt_budget": REPAIR_ATTEMPT_BUDGET,
            "token_budget": REPAIR_TOKEN_BUDGET,
            "attempt_budget_remaining": REPAIR_ATTEMPT_BUDGET - new_attempts,
            "token_budget_remaining": REPAIR_TOKEN_BUDGET - new_tokens,
            "raw_path": str(RAW_PATH),
            "raw_sha256": sha256_file(RAW_PATH),
            "protocol_sha256": sha256_file(PROTOCOL_PATH),
            "training_runs": 0,
            "training_tokens": 0,
            "scientific_generation_failures": 0,
            "post_generation_accounting_failures": 1,
            "recovery": {
                "reason": (
                    "The first receipt attempt repeated each batch's padded "
                    "prompt-position count once per row and tripped the "
                    "post-generation assertion."
                ),
                "rerun_performed": False,
                "raw_rows_modified": False,
                "source": "72 retained raw rows",
            },
            "finished_at": utc_now(),
        },
    )
    return 0


def bootstrap_interval(values: list[float], label: str) -> dict[str, Any]:
    if not values:
        return {
            "mean": None,
            "lower": None,
            "upper": None,
            "samples": 0,
            "unit": "SOURCE_FAMILY",
        }
    rng = random.Random(stable_seed(label))
    estimates = []
    for _ in range(20000):
        sample = [values[rng.randrange(len(values))] for _ in values]
        estimates.append(statistics.fmean(sample))
    estimates.sort()
    return {
        "mean": statistics.fmean(values),
        "lower": estimates[int(0.025 * (len(estimates) - 1))],
        "upper": estimates[int(0.975 * (len(estimates) - 1))],
        "samples": len(estimates),
        "unit": "SOURCE_FAMILY",
    }


def accuracy(row: dict[str, Any]) -> bool:
    return bool(row["evaluation"].get("SET_BINDING_SET_ACCURACY", False))


def interface_unknown(row: dict[str, Any]) -> bool:
    evaluation = row["evaluation"]
    return bool(
        evaluation.get("set_binding_target_available") is not False
        and (
            evaluation.get("syntax_adapter_failure")
            or not evaluation.get("candidate_keys_valid", True)
            or evaluation.get("patch_legal") is False
        )
    )


def transition_label(o_row: dict[str, Any], row: dict[str, Any]) -> str:
    o_state = "CORRECT" if accuracy(o_row) else (
        "UNKNOWN"
        if o_row["delivery"] == "UNKNOWN"
        else "WRONG"
    )
    state = "CORRECT" if accuracy(row) else (
        "UNKNOWN" if row["delivery"] == "UNKNOWN" else "WRONG"
    )
    return f"O_{o_state}_TO_{state}"


def arm_metrics(rows: list[dict[str, Any]], o_by_id: dict[str, Any]) -> dict[str, Any]:
    syntax = Counter(row["syntax_source"] for row in rows)
    delivery = Counter(row["delivery"] for row in rows)
    semantic = Counter(
        row["evaluation"].get("semantic_decision", "NOT_APPLICABLE") for row in rows
    )
    semantic_tool_failures = [
        {
            "trajectory_id": row["trajectory_id"],
            "reasons": row["evaluation"].get("semantic_reasons", []),
        }
        for row in rows
        if row["evaluation"].get("semantic_decision") == "TOOL_ERROR"
    ]
    parsed_rows = [
        row for row in rows if row["syntax_source"] != "SYNTAX_ADAPTER_FAILURE"
    ]
    patch_rows = [row for row in rows if "patch_legal" in row["evaluation"]]
    legal_patch_rows = [
        row for row in patch_rows if row["evaluation"].get("patch_legal")
    ]
    illegal_patch_rows = [
        row
        for row in parsed_rows
        if "patch_legal" in row["evaluation"]
        and not row["evaluation"].get("patch_legal")
    ]
    transitions = Counter(transition_label(o_by_id[row["trajectory_id"]], row) for row in rows)
    completion_lengths = [
        row["generation"].get("completion_tokens", 0) for row in rows
    ]
    interface_unknown_rows = [row for row in rows if interface_unknown(row)]
    target_unavailable_rows = [
        row
        for row in rows
        if row["evaluation"].get("set_binding_target_available") is False
    ]
    return {
        "rows": len(rows),
        "SET_BINDING_SET_ACCURACY": statistics.fmean(map(accuracy, rows)),
        "SET_BINDING_SET_ACCURACY_count": sum(map(accuracy, rows)),
        "syntax": dict(syntax),
        "contract_only_output": syntax["STRICT_WHOLE_JSON"],
        "embedded_json_non_contract_output": syntax["EMBEDDED_JSON"],
        "syntax_adapter_failure": syntax["SYNTAX_ADAPTER_FAILURE"],
        "patch": {
            "patch_evaluation_rows": len(patch_rows),
            "legal": len(legal_patch_rows),
            "illegal_on_parseable": len(illegal_patch_rows),
            "unparseable_patch_json": sum(
                row["evaluation"].get("patch_failure") == "PATCH_JSON_NOT_PARSEABLE"
                for row in rows
            ),
            "legal_rate_on_parseable": (
                len(legal_patch_rows) / len(parsed_rows) if parsed_rows else 0.0
            ),
            "failure_reasons": dict(
                Counter(
                    row["evaluation"].get("patch_failure")
                    for row in illegal_patch_rows
                    if row["evaluation"].get("patch_failure")
                )
            ),
        },
        "contract_preserved_from_O": sum(
            row["evaluation"].get("operator_order_unit_preserved_from_O", True)
            for row in rows
        ),
        "structural_target_exact": sum(
            row["evaluation"].get("structural_target_exact", False)
            for row in rows
        ),
        "program_executable": sum(
            row["evaluation"].get("program_executable", False)
            for row in rows
        ),
        "delivery": dict(delivery),
        "coverage": (delivery["CORRECT"] + delivery["WRONG"]) / len(rows),
        "wrong_delivery": delivery["WRONG"],
        "interface_caused_unknown_delivery": len(interface_unknown_rows),
        "reasonable_unknown_target_unavailable": len(target_unavailable_rows),
        "explicit_abstention_rows": 0,
        "reasonable_unknown_or_abstention": len(target_unavailable_rows),
        "O_transitions": dict(transitions),
        "O_wrong_to_correct": sum(
            not accuracy(o_by_id[row["trajectory_id"]]) and accuracy(row)
            for row in rows
        ),
        "O_correct_to_wrong_or_unknown": sum(
            accuracy(o_by_id[row["trajectory_id"]])
            and not accuracy(row)
            for row in rows
        ),
        "finish_reason": dict(
            Counter(
                row["generation"].get("finish_reason", "NO_NEW_GENERATION")
                for row in rows
            )
        ),
        "truncated_at_max_new_tokens": sum(
            row["generation"].get("truncated_at_max_new_tokens", False)
            for row in rows
        ),
        "target_token_length": {
            "sum": sum(completion_lengths),
            "mean": statistics.fmean(completion_lengths),
            "min": min(completion_lengths),
            "max": max(completion_lengths),
        },
        "prompt_tokens": sum(
            row["generation"].get("prompt_tokens", 0) for row in rows
        ),
        "completion_tokens": sum(completion_lengths),
        "generation_tokens": sum(
            row["generation"].get("prompt_tokens", 0)
            + row["generation"].get("completion_tokens", 0)
            for row in rows
        ),
        "semantic_tool_failure_count": len(semantic_tool_failures),
        "semantic_tool_failures": semantic_tool_failures,
        "candidate_semantics_not_scored": dict(semantic),
    }


def paired_source_family_analysis(
    rows_by_arm: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    families = sorted(
        {row["source_task_id"] for rows in rows_by_arm.values() for row in rows}
    )
    family_scores = {}
    all_three_scores = {}
    for family in families:
        family_scores[family] = {}
        all_three_scores[family] = {}
        for arm, rows in rows_by_arm.items():
            family_rows = sorted(
                [row for row in rows if row["source_task_id"] == family],
                key=lambda row: row["trajectory_id"],
            )
            family_scores[family][arm] = statistics.fmean(map(accuracy, family_rows))
            all_three_scores[family][arm] = len(family_rows) == 3 and all(
                map(accuracy, family_rows)
            )
    paired = {}
    paired_completion = {}
    for comparison, left, right in (
        ("E-R", "E_RESTRICTED_PATCH", "R_FULL_REVISION"),
        ("E-N", "E_RESTRICTED_PATCH", "N_NEUTRAL_RETRY"),
        ("R-N", "R_FULL_REVISION", "N_NEUTRAL_RETRY"),
    ):
        paired[comparison] = [
            family_scores[family][left] - family_scores[family][right]
            for family in families
        ]
        paired_completion[comparison] = [
            float(all_three_scores[family][left])
            - float(all_three_scores[family][right])
            for family in families
        ]
    intervals = {
        name: bootstrap_interval(values, f"row_level:{name}")
        for name, values in paired.items()
    }
    completion_intervals = {
        name: bootstrap_interval(values, f"completion:{name}")
        for name, values in paired_completion.items()
    }
    eligible_subtypes = sorted(
        {
            row["eligible_subtype"]
            for row in rows_by_arm["E_RESTRICTED_PATCH"]
            if row["eligible_correction"]
        }
    )
    subtype_differences = {}
    for subtype in eligible_subtypes:
        differences = []
        e_by_id = {
            row["trajectory_id"]: row
            for row in rows_by_arm["E_RESTRICTED_PATCH"]
            if row["eligible_correction"] and row["eligible_subtype"] == subtype
        }
        r_by_id = {
            row["trajectory_id"]: row
            for row in rows_by_arm["R_FULL_REVISION"]
            if row["eligible_correction"] and row["eligible_subtype"] == subtype
        }
        for family in sorted({row["source_task_id"] for row in e_by_id.values()}):
            family_ids = sorted(
                trajectory_id
                for trajectory_id, row in e_by_id.items()
                if row["source_task_id"] == family
            )
            differences.append(
                statistics.fmean(
                    float(accuracy(e_by_id[trajectory_id]))
                    - float(accuracy(r_by_id[trajectory_id]))
                    for trajectory_id in family_ids
                )
            )
        subtype_differences[subtype] = {
            "source_families": len(differences),
            "E_minus_R": statistics.fmean(differences),
            "family_level_differences": differences,
        }
    return {
        "primary": {
            "estimand": "SET_BINDING_SET_ACCURACY",
            "family_scores": family_scores,
            "paired_family_differences": paired,
            "paired_source_family_intervals": intervals,
            "point_estimates": {
                name: statistics.fmean(values) for name, values in paired.items()
            },
            "eligible_subtype_diagnostics": subtype_differences,
        },
        "secondary_all_three_variants_correct": {
            "family_scores": all_three_scores,
            "paired_family_differences": paired_completion,
            "paired_source_family_intervals": completion_intervals,
            "point_estimates": {
                name: statistics.fmean(values)
                for name, values in paired_completion.items()
            },
            "status": "SEPARATE_DIAGNOSTIC_NOT_PRIMARY",
        },
    }


def failure_payload(
    rows: list[dict[str, Any]],
    generation_receipt: dict[str, Any],
) -> dict[str, Any]:
    failures = {}
    for arm in ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm]
        syntax_failures = [
            row["trajectory_id"]
            for row in arm_rows
            if row["syntax_source"] == "SYNTAX_ADAPTER_FAILURE"
        ]
        patch_failures = [
            {
                "trajectory_id": row["trajectory_id"],
                "failure": row["evaluation"].get("patch_failure"),
            }
            for row in arm_rows
            if row["evaluation"].get("patch_legal") is False
        ]
        semantic_tool_failures = [
            {
                "trajectory_id": row["trajectory_id"],
                "reasons": row["evaluation"].get("semantic_reasons", []),
            }
            for row in arm_rows
            if row["evaluation"].get("semantic_decision") == "TOOL_ERROR"
        ]
        failures[arm] = {
            "syntax_adapter_failures": syntax_failures,
            "patch_legality_failures": patch_failures,
            "semantic_tool_failures": semantic_tool_failures,
            "semantic_tool_failures_kept_separate_from_candidate_semantics": True,
        }
    return {
        "schema": "b2b_failures_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "status": "NO_SCIENCE_GENERATION_CALL_FAILURES"
        if generation_receipt.get("scientific_generation_failures") == 0
        else "GENERATION_CALL_FAILURES_PRESENT",
        "preflight_stop_conditions": "PASS_ALL",
        "scientific_generation_call_failures": generation_receipt.get(
            "scientific_generation_failures"
        ),
        "post_generation_accounting_failures": [
            {
                "failure_id": "PADDED_BATCH_PROMPT_ACCOUNTING_SCALED_BY_ROW",
                "stage": "GENERATION_RECEIPT_FINALIZATION",
                "cause": (
                    "batch prompt positions were repeated per row before "
                    "padded-token accounting and falsely exceeded the repair cap"
                ),
                "new_generation_attempts_after_failure": 0,
                "rerun_performed": False,
                "raw_rows_modified": False,
                "recovery": (
                    "receipt reconstructed from the 72 retained raw rows with "
                    "batch prompt positions divided by batch size"
                ),
            }
        ],
        "failures_by_arm": failures,
        "candidate_semantics_not_classified_as_tool_failures": True,
        "first_run_unretained_generation_cost": {
            "source": str(B2_PARTIAL_FAILURES_PATH),
            "new_generation_attempts_in_b2b_from_first_run_failure": 0,
            "tokens": "UNKNOWN_NOT_INFERRED",
            "preserved": True,
        },
        "created_at": utc_now(),
    }


def analyze() -> int:
    require_protocol()
    generation_receipt = load_json(GENERATION_RECEIPT_PATH)
    if generation_receipt.get("status") not in {
        "PASS",
        "PASS_WITH_POST_GENERATION_ACCOUNTING_RECOVERY",
    }:
        raise RuntimeError("generation_receipt_not_pass")
    if sha256_file(RAW_PATH) != generation_receipt["raw_sha256"]:
        raise RuntimeError("repaired_raw_hash_mismatch")
    repaired_rows = load_jsonl(RAW_PATH)
    if len(repaired_rows) != REPAIR_ATTEMPT_BUDGET:
        raise RuntimeError("analysis_repaired_row_count")
    first_rows = load_jsonl(B2_RAW_PATH)
    comparator_rows = [
        copy.deepcopy(row)
        for row in first_rows
        if row["arm"] in {"O_FROZEN_ORDINARY", "N_NEUTRAL_RETRY"}
    ]
    for row in comparator_rows:
        row["delivery"] = b2.delivery_outcome(row)
    for row in repaired_rows:
        row["delivery"] = b2.delivery_outcome(row)
    rows_by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repaired_rows + comparator_rows:
        rows_by_arm[row["arm"]].append(row)
    o_by_id = {
        row["trajectory_id"]: row for row in rows_by_arm["O_FROZEN_ORDINARY"]
    }
    n_by_id = {
        row["trajectory_id"]: row for row in rows_by_arm["N_NEUTRAL_RETRY"]
    }
    expected_ids = set(o_by_id)
    if set(n_by_id) != expected_ids or any(
        {row["trajectory_id"] for row in rows_by_arm[arm]} != expected_ids
        for arm in ARMS
    ):
        raise RuntimeError("paired_trajectory_alignment_failed")
    paired = paired_source_family_analysis(
        {
            arm: rows_by_arm[arm]
            for arm in (
                "E_RESTRICTED_PATCH",
                "R_FULL_REVISION",
                "N_NEUTRAL_RETRY",
            )
        }
    )
    metrics = {
        arm: arm_metrics(rows_by_arm[arm], o_by_id)
        for arm in ARMS
    }
    comparator_metrics = {
        arm: arm_metrics(rows_by_arm[arm], o_by_id)
        for arm in ("O_FROZEN_ORDINARY", "N_NEUTRAL_RETRY")
    }
    all_three = paired["secondary_all_three_variants_correct"]
    originally_correct_families = {
        row["source_task_id"]
        for row in rows_by_arm["O_FROZEN_ORDINARY"]
        if row["originally_correct_family"]
    }
    damage_vs_r = sum(
        all_three["family_scores"][family]["R_FULL_REVISION"]
        and not all_three["family_scores"][family]["E_RESTRICTED_PATCH"]
        for family in originally_correct_families
    )
    thresholds = load_json(B2_PROTOCOL_PATH)["thresholds_from_B1_gate"]
    primary = paired["primary"]
    e_minus_r = primary["point_estimates"]["E-R"]
    e_minus_n = primary["point_estimates"]["E-N"]
    subtype_pass = all(
        item["E_minus_R"] >= 0
        for item in primary["eligible_subtype_diagnostics"].values()
    )
    interval_positive = (
        primary["paired_source_family_intervals"]["E-R"]["lower"] is not None
        and primary["paired_source_family_intervals"]["E-R"]["lower"] > 0
    )
    threshold_pass = (
        e_minus_r >= thresholds["E_minus_R_min"]
        and e_minus_n >= thresholds["E_minus_N_min"]
        and damage_vs_r <= thresholds[
            "additional_originally_correct_family_damage_vs_R_max"
        ]
        and subtype_pass
    )
    pervasive = any(
        metrics[arm]["syntax_adapter_failure"] > 18
        or metrics[arm]["interface_caused_unknown_delivery"] > 18
        for arm in ARMS
    )
    if pervasive:
        status = "INTERFACE_REPRESENTATION_FAILURE_STOP_R_E_CANDIDATE"
    elif not threshold_pass:
        status = "DEVELOPMENT_METHOD_NEGATIVE_STOP_R_E_CANDIDATE"
    elif not interval_positive:
        status = "DEVELOPMENT_GATE_INCONCLUSIVE_STOP_BEFORE_CONFIRMATION"
    else:
        status = "DEVELOPMENT_GATE_PASS_STOP_BEFORE_SEPARATE_CONFIRMATION_PANEL"
    write_json(FAILURES_PATH, failure_payload(repaired_rows, generation_receipt))
    b2b_wall_seconds = sum(arm["wall_seconds"] for arm in generation_receipt["arms"].values())
    b2_training_receipts = [load_json(R_RECEIPT_PATH), load_json(E_RECEIPT_PATH)]
    first_generation_receipt = load_json(B2_GENERATION_RECEIPT_PATH)
    analysis = {
        "schema": "b2b_development_analysis_v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_B2_TASK_ID,
        "goal_id": GOAL_ID,
        "status": status,
        "raw_path": str(RAW_PATH),
        "raw_sha256": sha256_file(RAW_PATH),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "independence": {
            "source_family_unit": True,
            "variants_per_family": 3,
            "variant_rows_independent": False,
        },
        "primary_estimand": "SET_BINDING_SET_ACCURACY",
        "answer_correctness_scored": False,
        "paired_analysis": paired,
        "metrics_by_repaired_arm": metrics,
        "reused_comparator_metrics": comparator_metrics,
        "originally_correct_family_completion_damage": {
            "E_relative_to_R": damage_vs_r,
            "maximum_allowed": thresholds[
                "additional_originally_correct_family_damage_vs_R_max"
            ],
        },
        "threshold_decision": {
            "thresholds": thresholds,
            "E_minus_R_pass": e_minus_r >= thresholds["E_minus_R_min"],
            "E_minus_N_pass": e_minus_n >= thresholds["E_minus_N_min"],
            "damage_pass": damage_vs_r
            <= thresholds["additional_originally_correct_family_damage_vs_R_max"],
            "subtype_direction_pass": subtype_pass,
            "E_minus_R_source_family_interval_positive": interval_positive,
            "E_minus_N_source_family_interval": primary[
                "paired_source_family_intervals"
            ]["E-N"],
            "pervasive_interface_failure": pervasive,
        },
        "cost": {
            "b2b_incremental": {
                "generation_attempts": generation_receipt[
                    "new_generation_attempts"
                ],
                "generation_tokens": generation_receipt["new_generation_tokens"],
                "padded_input_plus_completion_tokens": generation_receipt[
                    "new_generation_padded_input_plus_completion_tokens"
                ],
                "token_budget": REPAIR_TOKEN_BUDGET,
                "token_budget_remaining": generation_receipt[
                    "token_budget_remaining"
                ],
                "wall_seconds": b2b_wall_seconds,
                "gpu_seconds_lower_bound": b2b_wall_seconds,
                "training_runs": 0,
                "training_tokens": 0,
                "generation_call_failures": generation_receipt[
                    "scientific_generation_failures"
                ],
                "post_generation_accounting_failures": generation_receipt.get(
                    "post_generation_accounting_failures", 0
                ),
            },
            "known_cumulative_B2_plus_B2B": {
                "training_runs": 2,
                "training_processed_text_tokens": sum(
                    receipt["dataset"]["processed_text_tokens"]["sum"]
                    for receipt in b2_training_receipts
                ),
                "generation_attempts": first_generation_receipt[
                    "new_generation_attempts"
                ]
                + generation_receipt["new_generation_attempts"],
                "generation_tokens": first_generation_receipt[
                    "new_generation_tokens"
                ]
                + generation_receipt["new_generation_tokens"],
                "first_run_unretained_batch_tokens": "UNKNOWN_NOT_INFERRED",
            },
            "power_energy_measurement": "UNAVAILABLE_NOT_INFERRED",
        },
        "failures_path": str(FAILURES_PATH),
        "failures_sha256": sha256_file(FAILURES_PATH),
        "claim_boundary": {
            "feedback_derived_learning": "NOT_QUALIFIED",
            "answer_correctness": "NOT_SCORED",
            "new_source_generalization": "NOT_TESTED",
            "confirmation_claim": "NONE",
            "confirmation_outputs_inspected": False,
        },
        "analyzed_at": utc_now(),
    }
    write_json(ANALYSIS_PATH, analysis)
    return 0


def finalize() -> int:
    required = [
        PROTOCOL_PATH,
        RAW_PATH,
        GENERATION_RECEIPT_PATH,
        ANALYSIS_PATH,
        FAILURES_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"required_outputs_missing:{missing}")
    analysis = load_json(ANALYSIS_PATH)
    generation_receipt = load_json(GENERATION_RECEIPT_PATH)
    result = {
        "schema": "task_result_a_b2b_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "role": "A-EXP",
        "status": analysis["status"],
        "stop_before_confirmation": True,
        "outputs": {
            path.name: {
                "path": str(path),
                "sha256": sha256_file(path),
            }
            for path in required
        },
        "runner": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "execution": {
            "training_runs": 0,
            "training_tokens": 0,
            "new_generation_attempts": generation_receipt[
                "new_generation_attempts"
            ],
            "new_generation_tokens": generation_receipt["new_generation_tokens"],
            "repair_attempt_budget": REPAIR_ATTEMPT_BUDGET,
            "repair_token_budget": REPAIR_TOKEN_BUDGET,
            "budget_enforced": True,
        },
        "primary_estimand": analysis["primary_estimand"],
        "paired_completion_status": "SEPARATE_DIAGNOSTIC_NOT_PRIMARY",
        "claim_boundaries": {
            "feedback_derived_learning": "NOT_QUALIFIED",
            "answer_correctness": "NOT_SCORED",
            "new_source_generalization": "NOT_TESTED",
            "confirmation_claim": "NONE",
        },
        "skill_loading": {
            "loaded": [
                "graph-loop-rules",
                "agent-prompt-contracts",
                "verify-before-done",
            ],
            "rationale": (
                "Graph red lines were unconditional; prompt-contract and "
                "verification skills cover machine-readable output and final "
                "evidence gates."
            ),
        },
        "file_ownership_respected": True,
        "finished_at": utc_now(),
    }
    write_json(TASK_RESULT_PATH, result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=(
            "preflight",
            "generate",
            "recover-receipt",
            "analyze",
            "finalize",
            "all",
        ),
    )
    args = parser.parse_args()
    if args.stage in {"preflight", "all"}:
        preflight()
    if args.stage in {"generate", "all"}:
        generate()
    if args.stage == "recover-receipt":
        recover_generation_receipt_from_raw()
    if args.stage in {"analyze", "all"}:
        analyze()
    if args.stage in {"finalize", "all"}:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
