#!/usr/bin/env python3
"""Run a non-paper PRM800K C2/C4-reference training-pipeline smoke."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/prm_reference_training_smoke_20261010"
DATA = ROOT / "research/stage_e_method_revision_20261009/sources/prm800k/phase2_test.jsonl"
MODEL_PATH = Path("/home/testuser/wzh/models/hf/Qwen3-4B")
VENDOR = Path("/home/testuser/wzh/external_stage_d_repro/vendor")
PRM_REPO = Path("/home/testuser/wzh/external_stage_d_repro/repos/prm800k")

SEED = 20261013
TRAIN_PAIRS = 8
EVAL_PAIRS = 4
MAX_STEPS = 2
MAX_LENGTH = 256
MAX_NEW_TOKENS = 32


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_grader():
    sys.path.insert(0, str(VENDOR))
    sys.path.insert(0, str(PRM_REPO))
    sys.path.insert(0, str(PRM_REPO / "prm800k"))
    return importlib.import_module("grading.grader")


def selected_path(row: dict[str, Any]) -> tuple[list[int | None], str]:
    ratings: list[int | None] = []
    texts: list[str] = []
    for step in row["label"]["steps"]:
        chosen = step.get("chosen_completion")
        if isinstance(chosen, int) and 0 <= chosen < len(step.get("completions", [])):
            completion = step["completions"][chosen]
            ratings.append(completion.get("rating"))
            texts.append(str(completion.get("text") or ""))
        else:
            ratings.append(None)
            texts.append(str(step.get("human_completion") or ""))
    return ratings, "\n".join(text for text in texts if text.strip())


def prepare_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grader = load_grader()
    raw_rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = []
    for index, raw in enumerate(raw_rows):
        ratings, process_text = selected_path(raw)
        complete = bool(ratings) and all(rating is not None for rating in ratings)
        strict_process = complete and all(rating is not None and rating > 0 for rating in ratings)
        terminal = bool(grader.grade_answer(
            str(raw["question"].get("pre_generated_answer")),
            str(raw["question"].get("ground_truth_answer")),
        ))
        problem = str(raw["question"].get("problem") or "")
        prompt = f"Solve the math problem.\n\nProblem:\n{problem}\n\nReasoning:\n"
        completion = f"{process_text}\n\nFinal answer: {raw['question'].get('pre_generated_answer')}"
        rows.append({
            "index": index,
            "row_hash": sha256_text(canonical_json(raw)),
            "problem_hash": sha256_text(problem),
            "terminal_correct": terminal,
            "strict_process": strict_process,
            "prompt": prompt,
            "completion": completion,
            "text": prompt + completion,
            "step_count": len(ratings),
            "process_chars": len(process_text),
        })

    c2_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    c4_by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["terminal_correct"]:
            c2_by_problem[row["problem_hash"]].append(row)
        if row["strict_process"]:
            c4_by_problem[row["problem_hash"]].append(row)
    key = lambda row: (row["step_count"], row["process_chars"], row["row_hash"])
    pairs = []
    for problem_hash in sorted(set(c2_by_problem) & set(c4_by_problem)):
        left = sorted(c2_by_problem[problem_hash], key=key)
        right = sorted(c4_by_problem[problem_hash], key=key)
        if left and right:
            pairs.append({"problem_hash": problem_hash, "C2": left[0], "C4": right[0]})
        if len(pairs) >= TRAIN_PAIRS + EVAL_PAIRS:
            break
        if len(pairs) >= TRAIN_PAIRS + EVAL_PAIRS:
            break
    if len(pairs) < TRAIN_PAIRS + EVAL_PAIRS:
        raise RuntimeError(f"not enough matched pairs: {len(pairs)}")
    return pairs, {
        "source_rows": len(rows),
        "matched_pairs_available": len(pairs),
        "train_problem_groups": TRAIN_PAIRS,
        "eval_problem_groups": EVAL_PAIRS,
    }


def build_dataset(rows: list[dict[str, Any]]) -> Dataset:
    return Dataset.from_list([
        {"prompt": row["prompt"], "completion": row["completion"], "text": row["text"]}
        for row in rows
    ])


def set_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def train_arm(
    arm: str,
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    tokenizer: Any,
    output_root: Path,
) -> dict[str, Any]:
    set_determinism(SEED)
    arm_dir = output_root / arm
    arm_dir.mkdir(parents=True, exist_ok=False)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model.config.use_cache = False
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )
    args = SFTConfig(
        output_dir=str(arm_dir),
        max_steps=MAX_STEPS,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=2e-4,
        lr_scheduler_type="constant",
        warmup_steps=0,
        logging_steps=1,
        save_strategy="steps",
        save_steps=MAX_STEPS,
        save_total_limit=1,
        eval_strategy="steps",
        eval_steps=MAX_STEPS,
        max_length=MAX_LENGTH,
        completion_only_loss=False,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        report_to=[],
        seed=SEED,
        data_seed=SEED,
        remove_unused_columns=False,
        use_cache=False,
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=build_dataset(train_rows),
        eval_dataset=build_dataset(eval_rows),
        peft_config=peft_config,
        processing_class=tokenizer,
    )
    train_result = trainer.train()
    eval_result = trainer.evaluate()
    adapter_dir = arm_dir / "final_adapter"
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    generations = []
    for row in eval_rows[:2]:
        inputs = tokenizer(row["prompt"], return_tensors="pt").to(model.device)
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        generations.append({
            "problem_hash": row["problem_hash"],
            "prompt_sha256": sha256_text(row["prompt"]),
            "generated_text": generated,
        })
    (arm_dir / "generation_smoke.json").write_text(
        json.dumps(generations, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    metrics = {
        "arm": arm,
        "train_runtime_seconds": train_result.metrics.get("train_runtime"),
        "train_loss": train_result.metrics.get("train_loss"),
        "eval_loss": eval_result.get("eval_loss"),
        "eval_runtime_seconds": eval_result.get("eval_runtime"),
        "global_step": int(train_result.global_step),
        "train_examples": len(train_rows),
        "eval_examples": len(eval_rows),
        "adapter_path": str(adapter_dir),
        "adapter_files": sorted(path.name for path in adapter_dir.iterdir() if path.is_file()),
        "checkpoint_present": any(arm_dir.glob("checkpoint-*")),
        "generation_smoke_rows": len(generations),
    }
    del trainer, model
    torch.cuda.empty_cache()
    return metrics


def main() -> int:
    if TASK.exists():
        raise RuntimeError(f"smoke output already exists: {TASK}")
    TASK.mkdir(parents=True, exist_ok=False)
    pairs, selection = prepare_rows()
    train_pairs = pairs[:TRAIN_PAIRS]
    eval_pairs = pairs[TRAIN_PAIRS:TRAIN_PAIRS + EVAL_PAIRS]
    train_rows = {
        "C2": [pair["C2"] for pair in train_pairs],
        "C4": [pair["C4"] for pair in train_pairs],
    }
    eval_rows = {
        "C2": [pair["C2"] for pair in eval_pairs],
        "C4": [pair["C4"] for pair in eval_pairs],
    }

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    config = {
        "namespace": "PRM_REFERENCE_TRAINING_SMOKE",
        "status": "AUTHORIZED_REFERENCE_TRAINING_SMOKE_NOT_PAPER_RESULT",
        "formal_training": False,
        "seed": SEED,
        "model_path": str(MODEL_PATH),
        "model_config_sha256": sha256_file(MODEL_PATH / "config.json"),
        "model_index_sha256": sha256_file(MODEL_PATH / "model.safetensors.index.json"),
        "tokenizer_sha256": sha256_file(MODEL_PATH / "tokenizer.json"),
        "data_path": str(DATA),
        "data_sha256": sha256_file(DATA),
        "selection": selection,
        "train_problem_hashes": [pair["problem_hash"] for pair in train_pairs],
        "eval_problem_hashes": [pair["problem_hash"] for pair in eval_pairs],
        "row_hashes": {
            "C2_train": [pair["C2"]["row_hash"] for pair in train_pairs],
            "C4_train": [pair["C4"]["row_hash"] for pair in train_pairs],
            "C2_eval": [pair["C2"]["row_hash"] for pair in eval_pairs],
            "C4_eval": [pair["C4"]["row_hash"] for pair in eval_pairs],
        },
        "training": {
            "model": "Qwen3-4B",
            "method": "LoRA SFT",
            "target_modules": ["q_proj", "v_proj"],
            "lora_r": 8,
            "lora_alpha": 16,
            "max_steps": MAX_STEPS,
            "max_length": MAX_LENGTH,
            "per_device_batch_size": 1,
            "learning_rate": 2e-4,
            "optimizer": "adamw_torch",
            "precision": "bf16",
            "checkpoint": "one checkpoint at final smoke step",
            "evaluation": "held-out matched-pair LM loss plus two greedy generation smoke rows",
            "hyperparameter_search": False,
            "external_api_calls": 0,
        },
        "licences": {
            "code": "MIT PRM800K repository root",
            "data": "LICENCE_PENDING_NONCOMMERCIAL_ACADEMIC_SMOKE_ONLY",
            "model": "Qwen model licence recorded separately; local non-commercial smoke only",
        },
    }
    (TASK / "smoke_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    metrics = {
        "status": "RUNNING",
        "config_sha256": sha256_file(TASK / "smoke_config.json"),
        "arms": {},
        "paper_result": False,
    }
    for arm in ("C2", "C4"):
        metrics["arms"][arm] = train_arm(
            arm,
            train_rows[arm],
            eval_rows[arm],
            tokenizer,
            TASK,
        )
    metrics["status"] = (
        "PIPELINE_CLOSED"
        if all(
            arm["global_step"] == MAX_STEPS
            and arm["checkpoint_present"]
            and arm["eval_loss"] is not None
            and np.isfinite(float(arm["eval_loss"]))
            for arm in metrics["arms"].values()
        )
        else "PIPELINE_NOT_CLOSED"
    )
    metrics["chain"] = {
        "dataset": "PASS",
        "selection": "PASS",
        "training": "PASS" if all(arm["global_step"] == MAX_STEPS for arm in metrics["arms"].values()) else "FAIL",
        "checkpoint": "PASS" if all(arm["checkpoint_present"] for arm in metrics["arms"].values()) else "FAIL",
        "evaluation": "PASS" if all(arm["eval_loss"] is not None for arm in metrics["arms"].values()) else "FAIL",
    }
    (TASK / "smoke_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": metrics["status"],
        "chain": metrics["chain"],
        "arms": metrics["arms"],
        "output": str(TASK / "smoke_metrics.json"),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if metrics["status"] == "PIPELINE_CLOSED" else 1


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    raise SystemExit(main())
