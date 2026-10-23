"""Run financial feedback-learning dataset construction, SFT, generation and analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from feedback_learning_core import (
    build_tasks_from_records,
    canonical_target,
    choose_candidate,
    evaluate_prediction,
    stable_hash,
    target_to_training_text,
    write_json,
    write_jsonl,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = Path(__file__).with_name("EXPERIMENT_PROTOCOL.json")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    """Load JSON from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_protocol(path: Path) -> dict[str, Any]:
    """Load either a base protocol or a bounded amendment over the base."""
    payload = load_json(path)
    if payload.get("schema") != "financial_feedback_learning_protocol_amendment_v1":
        return payload
    base = load_json(DEFAULT_PROTOCOL)
    require(
        sha256_file(DEFAULT_PROTOCOL) == payload["base_protocol_sha256"],
        "base_protocol_hash_mismatch",
    )
    resolved = dict(base)
    for section, values in payload["changes"].items():
        if isinstance(values, dict) and isinstance(resolved.get(section), dict):
            merged = dict(resolved[section])
            merged.update(values)
            resolved[section] = merged
        else:
            resolved[section] = values
    resolved["status"] = payload["status"]
    resolved["protocol_amendment"] = {
        "path": str(path),
        "sha256": sha256_file(path),
    }
    return resolved


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows from disk."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def collect_training_receipts(run_root: Path) -> dict[str, Any]:
    """Load every arm receipt so separate training batches remain one ledger."""
    receipts: dict[str, Any] = {}
    training_root = run_root / "training"
    if training_root.exists():
        for receipt_path in sorted(training_root.glob("*/training_receipt.json")):
            receipt = load_json(receipt_path)
            receipts[str(receipt["arm"])] = receipt
    return receipts


def require(condition: bool, message: str) -> None:
    """Raise a deterministic experiment error when a gate fails."""
    if not condition:
        raise ValueError(message)


def sample_tasks(
    tasks: list[dict[str, Any]],
    limit: int | None,
) -> list[dict[str, Any]]:
    """Deterministically sample tasks by stable hash."""
    ordered = sorted(tasks, key=lambda task: stable_hash(task["task_id"]))
    return ordered if limit is None else ordered[:limit]


def build_dataset(
    protocol: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    """Build source-cluster-separated financial feedback tasks."""
    source = protocol["source"]
    train_path = Path(source["train_path_gb10"])
    external_path = Path(source["external_path_gb10"])
    require(sha256_file(train_path) == source["train_sha256"], "train_source_hash_mismatch")
    require(
        sha256_file(external_path) == source["external_sha256"],
        "external_source_hash_mismatch",
    )
    train_records = load_json(train_path)
    external_records = load_json(external_path)
    train_tasks = build_tasks_from_records(train_records, "train")
    external_tasks = build_tasks_from_records(external_records, "external")
    tasks = train_tasks + external_tasks
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        by_split[task["split"]].append(task)
    limits = {
        "train": 640,
        "dev": 96,
        "test": 96,
        "external": 96,
    }
    selected: list[dict[str, Any]] = []
    split_summary: dict[str, Any] = {}
    for split, split_tasks in sorted(by_split.items()):
        kept = sample_tasks(split_tasks, limits.get(split))
        selected.extend(kept)
        split_summary[split] = {
            "generated": len(split_tasks),
            "selected": len(kept),
            "table_uids": len({task["table_uid"] for task in kept}),
            "task_types": dict(Counter(task["task_type"] for task in kept)),
            "units": dict(Counter(task["unit"] for task in kept)),
        }
    split_uids = {
        split: {task["table_uid"] for task in selected if task["split"] == split}
        for split in split_summary
    }
    for left, left_uids in split_uids.items():
        for right, right_uids in split_uids.items():
            if left < right:
                require(not (left_uids & right_uids), f"source_uid_overlap:{left}:{right}")
    require(split_summary.get("train", {}).get("selected", 0) >= 160, "insufficient_train_tasks")
    require(split_summary.get("dev", {}).get("selected", 0) >= 48, "insufficient_dev_tasks")
    require(split_summary.get("test", {}).get("selected", 0) >= 20, "insufficient_test_tasks")
    require(
        split_summary.get("external", {}).get("selected", 0) >= 20,
        "insufficient_external_tasks",
    )

    run_root.mkdir(parents=True, exist_ok=True)
    dataset_path = run_root / "financial_feedback_tasks.jsonl"
    write_jsonl(dataset_path, selected)
    receipt = {
        "schema": "financial_feedback_dataset_receipt_v1",
        "protocol_sha256": sha256_file(DEFAULT_PROTOCOL),
        "source_hashes": {
            "train": sha256_file(train_path),
            "external": sha256_file(external_path),
        },
        "dataset_sha256": sha256_file(dataset_path),
        "task_count": len(selected),
        "split_summary": split_summary,
        "source_cluster_isolation": "PASS",
        "identity": (
            "Real TAT-QA financial tables with deterministic derived questions and "
            "controlled candidate corruptions. Not a natural error-frequency sample."
        ),
    }
    write_json(run_root / "dataset_receipt.json", receipt)
    return receipt


def load_dataset(run_root: Path) -> list[dict[str, Any]]:
    """Load the generated task dataset."""
    return load_jsonl(run_root / "financial_feedback_tasks.jsonl")


def training_examples(
    tasks: list[dict[str, Any]],
    arm: str,
) -> list[dict[str, Any]]:
    """Create matched SFT rows for one feedback-filter arm."""
    config = {
        "exec_orig": ("answer_execution", False),
        "cheap_orig": ("cheap_consistency", False),
        "evidence_orig": ("evidence_dependency", False),
        "exec_cf": ("answer_execution", True),
        "cheap_cf": ("cheap_consistency", True),
        "evidence_cf": ("evidence_dependency", True),
    }
    require(arm in config, f"unknown_training_arm:{arm}")
    filter_name, with_cf = config[arm]
    train_tasks = [task for task in tasks if task["split"] == "train"]
    train_tasks = sample_tasks(train_tasks, 160)
    rows: list[dict[str, Any]] = []
    for task in train_tasks:
        candidate = choose_candidate(task, filter_name)
        target = {
            "answer": float(candidate["target"]["answer"]),
            "unit": candidate["target"]["unit"],
            "formula": candidate["target"]["formula"],
            "evidence_refs": candidate["target"]["evidence_refs"],
        }
        rows.append(
            {
                "row_id": f"{task['task_id']}::original",
                "source_task_id": task["task_id"],
                "variant": "original",
                "filter": filter_name,
                "candidate_id": candidate["candidate_id"],
                "text": target_to_training_text(task, target),
                "completion": canonical_target(target),
                "prompt_tokens": None,
                "completion_tokens": None,
            }
        )
    if with_cf:
        for task in train_tasks:
            variant = task["variants"].get("relevant_change")
            require(variant is not None, f"missing_relevant_variant:{task['task_id']}")
            expected = variant["expected"]
            target = {
                "answer": float(expected["answer"]),
                "unit": expected["unit"],
                "formula": expected["formula"],
                "evidence_refs": expected["evidence_refs"],
            }
            completion = canonical_target(target)
            rows.append(
                {
                    "row_id": f"{task['task_id']}::relevant_change",
                    "source_task_id": task["task_id"],
                    "variant": "relevant_change",
                    "filter": filter_name,
                    "candidate_id": "controlled_counterfactual_reference",
                    "text": variant["prompt"] + "\n" + completion,
                    "completion": completion,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                }
            )
    return rows


def train_arms(
    protocol: dict[str, Any],
    run_root: Path,
    arms: list[str],
) -> dict[str, Any]:
    """Train one or more LoRA SFT arms on GB10."""
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    tasks = load_dataset(run_root)
    config = protocol["training"]
    model_path = Path(config["model_path_gb10"])
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    train_config: dict[str, Any] = {}
    for arm in arms:
        set_seed(int(config["seed"]))
        rows = training_examples(tasks, arm)
        write_jsonl(run_root / f"training_rows_{arm}.jsonl", rows)
        tokenized_lengths = [
            len(tokenizer(row["text"], add_special_tokens=False)["input_ids"])
            for row in rows
        ]
        completion_lengths = [
            len(tokenizer(row["completion"], add_special_tokens=False)["input_ids"])
            for row in rows
        ]
        arm_dir = run_root / "training" / arm
        arm_dir.mkdir(parents=True, exist_ok=False)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        model.config.use_cache = False
        peft_config = LoraConfig(
            r=int(config["lora_r"]),
            lora_alpha=int(config["lora_alpha"]),
            lora_dropout=float(config["lora_dropout"]),
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=list(config["target_modules"]),
        )
        max_steps = (
            int(config["max_steps_counterfactual_arms"])
            if arm.endswith("_cf")
            else int(config["max_steps_original_arms"])
        )
        args = SFTConfig(
            output_dir=str(arm_dir),
            max_steps=max_steps,
            per_device_train_batch_size=int(config["per_device_train_batch_size"]),
            gradient_accumulation_steps=int(config["gradient_accumulation_steps"]),
            learning_rate=float(config["learning_rate"]),
            lr_scheduler_type=str(config["lr_scheduler"]),
            warmup_ratio=float(config["warmup_ratio"]),
            logging_steps=10,
            save_strategy="no",
            max_length=int(config["max_length"]),
            completion_only_loss=False,
            bf16=True,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},
            report_to=[],
            seed=int(config["seed"]),
            data_seed=int(config["seed"]),
            remove_unused_columns=False,
            use_cache=False,
        )
        trainer = SFTTrainer(
            model=model,
            args=args,
            train_dataset=Dataset.from_list(
                [{"text": row["text"]} for row in rows]
            ),
            peft_config=peft_config,
            processing_class=tokenizer,
        )
        started = time.time()
        train_result = trainer.train()
        elapsed = time.time() - started
        adapter_dir = arm_dir / "final_adapter"
        trainer.save_model(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))
        metrics = {
            "schema": "financial_feedback_training_receipt_v1",
            "arm": arm,
            "filter": rows[0]["filter"],
            "counterfactual_mix": arm.endswith("_cf"),
            "rows": len(rows),
            "unique_source_tasks": len({row["source_task_id"] for row in rows}),
            "candidate_counts": dict(Counter(row["candidate_id"] for row in rows)),
            "prompt_tokens": sum(tokenized_lengths),
            "completion_tokens": sum(completion_lengths),
            "max_sequence_tokens_observed": max(tokenized_lengths),
            "max_steps": max_steps,
            "train_runtime_seconds": elapsed,
            "train_metrics": train_result.metrics,
            "adapter_path": str(adapter_dir),
            "model_path": str(model_path),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
        write_json(arm_dir / "training_receipt.json", metrics)
        train_config[arm] = metrics
        del trainer
        del model
        torch.cuda.empty_cache()
    all_receipts = collect_training_receipts(run_root)
    all_receipts.update(train_config)
    write_json(run_root / "training_summary.json", all_receipts)
    return all_receipts


def evaluation_instances(tasks: list[dict[str, Any]], protocol: dict[str, Any]) -> list[dict[str, Any]]:
    """Select frozen evaluation tasks and variants."""
    limits = protocol["evaluation"]["planned_tasks_per_slice"]
    variants_by_slice = protocol["evaluation"]["variants_by_slice"]
    instances: list[dict[str, Any]] = []
    for slice_name in ("dev", "test", "external"):
        slice_tasks = sample_tasks(
            [task for task in tasks if task["split"] == slice_name],
            int(limits[slice_name]),
        )
        for task in slice_tasks:
            for variant_name in variants_by_slice[slice_name]:
                if variant_name == "original":
                    prompt = task["prompt"]
                    expected = task["expected"]
                else:
                    variant = task["variants"].get(variant_name)
                    require(variant is not None, f"missing_variant:{task['task_id']}:{variant_name}")
                    prompt = variant["prompt"]
                    expected = variant["expected"]
                instances.append(
                    {
                        "instance_id": f"{task['task_id']}::{variant_name}",
                        "source_task_id": task["task_id"],
                        "table_uid": task["table_uid"],
                        "slice": slice_name,
                        "variant": variant_name,
                        "prompt": prompt,
                        "expected": expected,
                        "question": task["question"],
                        "current_period": task["current_period"],
                        "prior_period": task["prior_period"],
                        "row_label": task["row_label"],
                        "table_text": task["table_text"],
                    }
                )
    return instances


def generate_with_model(
    model: Any,
    tokenizer: Any,
    instance: dict[str, Any],
    max_new_tokens: int,
) -> dict[str, Any]:
    """Generate and score one frozen answer."""
    import torch

    inputs = tokenizer(instance["prompt"], return_tensors="pt").to(model.device)
    started = time.time()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    latency_ms = (time.time() - started) * 1000.0
    generated = tokenizer.decode(
        output[0][inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
    )
    check_started = time.time()
    scored = evaluate_prediction(
        generated,
        {
            "table_text": instance["table_text"],
            "expected": instance["expected"],
            "current_period": instance["current_period"],
            "prior_period": instance["prior_period"],
        },
        instance["expected"],
    )
    check_latency_ms = (time.time() - check_started) * 1000.0
    prompt_tokens = int(inputs["input_ids"].shape[1])
    completion_tokens = int(output.shape[1] - inputs["input_ids"].shape[1])
    return {
        "model_arm": instance["model_arm"],
        "instance_id": instance["instance_id"],
        "source_task_id": instance["source_task_id"],
        "table_uid": instance["table_uid"],
        "slice": instance["slice"],
        "variant": instance["variant"],
        "generated_text": generated,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": latency_ms,
        "check_latency_ms": check_latency_ms,
        **scored,
    }


def generate_batch_with_model(
    model: Any,
    tokenizer: Any,
    instances: list[dict[str, Any]],
    max_new_tokens: int,
) -> list[dict[str, Any]]:
    """Generate a fixed batch with the same greedy contract as single generation."""
    import torch

    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    prompts = [instance["prompt"] for instance in instances]
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
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    batch_latency_ms = (time.time() - started) * 1000.0
    per_item_latency_ms = batch_latency_ms / len(instances)
    rows: list[dict[str, Any]] = []
    for index, instance in enumerate(instances):
        generated = tokenizer.decode(
            output[index][input_width:],
            skip_special_tokens=True,
        )
        check_started = time.time()
        scored = evaluate_prediction(
            generated,
            {
                "table_text": instance["table_text"],
                "expected": instance["expected"],
                "current_period": instance["current_period"],
                "prior_period": instance["prior_period"],
            },
            instance["expected"],
        )
        check_latency_ms = (time.time() - check_started) * 1000.0
        prompt_tokens = int(inputs["attention_mask"][index].sum().item())
        completion_tokens = int(output.shape[1] - input_width)
        rows.append(
            {
                "model_arm": instance["model_arm"],
                "instance_id": instance["instance_id"],
                "source_task_id": instance["source_task_id"],
                "table_uid": instance["table_uid"],
                "slice": instance["slice"],
                "variant": instance["variant"],
                "generated_text": generated,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": per_item_latency_ms,
                "batch_latency_ms": batch_latency_ms,
                "batch_size": len(instances),
                "check_latency_ms": check_latency_ms,
                **scored,
            }
        )
    return rows


def evaluate_models(
    protocol: dict[str, Any],
    run_root: Path,
    model_arms: list[str],
) -> dict[str, Any]:
    """Generate frozen answers for the base model and trained adapters."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tasks = load_dataset(run_root)
    instances = evaluation_instances(tasks, protocol)
    write_jsonl(run_root / "evaluation_instances.jsonl", instances)
    model_path = Path(protocol["training"]["model_path_gb10"])
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows: list[dict[str, Any]] = []
    receipts: dict[str, Any] = {}
    for model_arm in model_arms:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        if model_arm != "base_qwen3_4b":
            adapter_path = run_root / "training" / model_arm / "final_adapter"
            require(adapter_path.exists(), f"missing_adapter:{adapter_path}")
            model = PeftModel.from_pretrained(model, adapter_path)
        model.eval()
        arm_rows: list[dict[str, Any]] = []
        started = time.time()
        batch_size = 8
        for batch_start in range(0, len(instances), batch_size):
            batch_instances = [
                {**instance, "model_arm": model_arm}
                for instance in instances[batch_start : batch_start + batch_size]
            ]
            batch_rows = generate_batch_with_model(
                model,
                tokenizer,
                batch_instances,
                max_new_tokens=192,
            )
            arm_rows.extend(batch_rows)
            rows.extend(batch_rows)
            print(
                f"{model_arm}: generated {len(arm_rows)}/{len(instances)}",
                flush=True,
            )
        receipts[model_arm] = {
            "instances": len(arm_rows),
            "accounting_attempts": len(arm_rows),
            "prompt_tokens": sum(row["prompt_tokens"] for row in arm_rows),
            "completion_tokens": sum(row["completion_tokens"] for row in arm_rows),
            "generation_wall_seconds": time.time() - started,
            "interface_valid": sum(bool(row["interface_valid"]) for row in arm_rows),
            "answer_correct": sum(bool(row["answer_correct"]) for row in arm_rows),
        }
        del model
        torch.cuda.empty_cache()
    output_path = run_root / "generation_results.jsonl"
    write_jsonl(output_path, rows)
    receipt = {
        "schema": "financial_feedback_generation_receipt_v1",
        "generation_results_sha256": sha256_file(output_path),
        "models": receipts,
        "total_accounting_attempts": sum(value["accounting_attempts"] for value in receipts.values()),
        "total_prompt_tokens": sum(value["prompt_tokens"] for value in receipts.values()),
        "total_completion_tokens": sum(value["completion_tokens"] for value in receipts.values()),
        "judge_calls": 0,
    }
    write_json(run_root / "generation_receipt.json", receipt)
    return receipt


def mean_safe(values: list[float]) -> float:
    """Return a finite mean or zero."""
    return statistics.fmean(values) if values else 0.0


def paired_metrics(
    rows: list[dict[str, Any]],
    correct_key: str = "answer_correct",
) -> dict[str, Any]:
    """Compute paired invariance/adaptation metrics by source task."""
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["source_task_id"]][row["variant"]] = row
    invariance: list[float] = []
    adaptation: list[float] = []
    paired_complete: list[float] = []
    for variants in grouped.values():
        original = variants.get("original")
        relevant = variants.get("relevant_change")
        irrelevant = variants.get("irrelevant_change")
        if original is None or relevant is None or irrelevant is None:
            continue
        invariance.append(
            float(
                original[correct_key]
                and irrelevant[correct_key]
                and math.isclose(
                    float(original["target"]["answer"]) if original["target"] else float("nan"),
                    float(irrelevant["target"]["answer"]) if irrelevant["target"] else float("nan"),
                    rel_tol=1e-6,
                    abs_tol=1e-6,
                )
            )
        )
        adaptation.append(float(original[correct_key] and relevant[correct_key]))
        paired_complete.append(float(invariance[-1] and adaptation[-1]))
    return {
        "pairs": len(paired_complete),
        "irrelevant_invariance": mean_safe(invariance),
        "relevant_adaptation": mean_safe(adaptation),
        "paired_correct_completion": mean_safe(paired_complete),
    }


def cluster_bootstrap_difference(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    metric: str,
    repetitions: int = 2000,
) -> dict[str, Any]:
    """Bootstrap paired model differences over source table UIDs."""
    left = {
        row["instance_id"]: row
        for row in left_rows
        if row["variant"] == "original"
    }
    right = {
        row["instance_id"]: row
        for row in right_rows
        if row["variant"] == "original"
    }
    common = sorted(set(left) & set(right))
    require(bool(common), "no_common_instances_for_bootstrap")
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for instance_id in common:
        score_left = float(left[instance_id][metric])
        score_right = float(right[instance_id][metric])
        by_cluster[left[instance_id]["table_uid"]].append(score_left - score_right)
    clusters = sorted(by_cluster)
    observed = mean_safe([mean_safe(values) for values in by_cluster.values()])
    rng = random.Random(20261024)
    samples: list[float] = []
    for _ in range(repetitions):
        selected = [rng.choice(clusters) for _ in clusters]
        samples.append(mean_safe([mean_safe(by_cluster[cluster]) for cluster in selected]))
    samples.sort()
    return {
        "metric": metric,
        "clusters": len(clusters),
        "paired_instances": len(common),
        "difference": observed,
        "ci95": [samples[int(0.025 * repetitions)], samples[int(0.975 * repetitions)]],
    }


def paired_score_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Return per-source-task paired correctness scores."""
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["source_task_id"]][row["variant"]] = row
    scores: dict[str, float] = {}
    for task_id, variants in grouped.items():
        original = variants.get("original")
        relevant = variants.get("relevant_change")
        irrelevant = variants.get("irrelevant_change")
        if original is None or relevant is None or irrelevant is None:
            continue
        same_answer = (
            original["target"] is not None
            and irrelevant["target"] is not None
            and math.isclose(
                float(original["target"]["answer"]),
                float(irrelevant["target"]["answer"]),
                rel_tol=1e-6,
                abs_tol=1e-6,
            )
        )
        invariance = bool(original["answer_correct"] and irrelevant["answer_correct"] and same_answer)
        adaptation = bool(original["answer_correct"] and relevant["answer_correct"])
        scores[task_id] = float(invariance and adaptation)
    return scores


def paired_cluster_difference(
    left_rows: list[dict[str, Any]],
    right_rows: list[dict[str, Any]],
    repetitions: int = 2000,
) -> dict[str, Any]:
    """Bootstrap paired-correctness differences over source table UIDs."""
    left = paired_score_rows(left_rows)
    right = paired_score_rows(right_rows)
    common = sorted(set(left) & set(right))
    require(bool(common), "no_common_pairs_for_bootstrap")
    row_by_task = {
        row["source_task_id"]: row
        for row in left_rows + right_rows
        if row["variant"] == "original"
    }
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for task_id in common:
        by_cluster[row_by_task[task_id]["table_uid"]].append(left[task_id] - right[task_id])
    clusters = sorted(by_cluster)
    observed = mean_safe([mean_safe(values) for values in by_cluster.values()])
    rng = random.Random(20261024)
    samples: list[float] = []
    for _ in range(repetitions):
        selected = [rng.choice(clusters) for _ in clusters]
        samples.append(mean_safe([mean_safe(by_cluster[cluster]) for cluster in selected]))
    samples.sort()
    return {
        "metric": "paired_correct_completion",
        "clusters": len(clusters),
        "paired_tasks": len(common),
        "difference": observed,
        "ci95": [samples[int(0.025 * repetitions)], samples[int(0.975 * repetitions)]],
    }


def policy_metrics(rows: list[dict[str, Any]], accepted: list[bool]) -> dict[str, Any]:
    """Compute delivery risk, coverage, retention and cost."""
    accepted_rows = [row for row, flag in zip(rows, accepted) if flag]
    correct_accepted = sum(bool(row["answer_correct"]) for row in accepted_rows)
    wrong_accepted = len(accepted_rows) - correct_accepted
    cost_units = []
    for row in rows:
        cost_units.append(
            row["prompt_tokens"]
            + 2 * row["completion_tokens"]
            + float(row.get("check_latency_ms", 0.0)) / 10.0
        )
    return {
        "items": len(rows),
        "accepted": len(accepted_rows),
        "correct_delivered": correct_accepted,
        "wrong_delivered": wrong_accepted,
        "wrong_delivery_rate": wrong_accepted / len(accepted_rows) if accepted_rows else 0.0,
        "correct_delivery_coverage": correct_accepted / len(rows) if rows else 0.0,
        "retention_rate": len(accepted_rows) / len(rows) if rows else 0.0,
        "mean_cost_units": mean_safe(cost_units),
    }


def analyze_results(
    protocol: dict[str, Any],
    run_root: Path,
) -> dict[str, Any]:
    """Summarize C2 training effects and C3 delivery-policy tradeoffs."""
    rows = load_jsonl(run_root / "generation_results.jsonl")
    instances = {
        instance["instance_id"]: instance
        for instance in load_jsonl(run_root / "evaluation_instances.jsonl")
    }
    for row in rows:
        instance = instances[row["instance_id"]]
        rescored = evaluate_prediction(
            row["generated_text"],
            {
                "table_text": instance["table_text"],
                "expected": instance["expected"],
                "current_period": instance["current_period"],
                "prior_period": instance["prior_period"],
            },
            instance["expected"],
        )
        row.update(rescored)
    by_model_slice: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_model_slice[(row["model_arm"], row["slice"])].append(row)
        by_model[row["model_arm"]].append(row)
    model_metrics: dict[str, Any] = {}
    for model_arm, model_rows in sorted(by_model.items()):
        slice_metrics: dict[str, Any] = {}
        for slice_name in ("dev", "test", "external"):
            subset = by_model_slice[(model_arm, slice_name)]
            slice_metrics[slice_name] = {
                "items": len(subset),
                "interface_valid": mean_safe([float(row["interface_valid"]) for row in subset]),
                "embedded_valid": mean_safe([float(row["embedded_valid"]) for row in subset]),
                "postprocess_recovered": mean_safe(
                    [float(row["postprocess_recovered"]) for row in subset]
                ),
                "semantic_answer_correct": mean_safe(
                    [float(row["answer_correct"]) for row in subset]
                ),
                "strict_answer_correct": mean_safe(
                    [float(row["strict_answer_correct"]) for row in subset]
                ),
                "exact_evidence": mean_safe(
                    [float(row["checks"]["exact_evidence"]) for row in subset]
                ),
                "unit_correct": mean_safe([float(row["checks"]["unit"]) for row in subset]),
                "calculation_valid": mean_safe(
                    [float(row["checks"]["calculation"]) for row in subset]
                ),
                "paired_semantic": paired_metrics(subset, "answer_correct"),
                "paired_strict": paired_metrics(subset, "strict_answer_correct"),
            }
        model_metrics[model_arm] = slice_metrics

    comparisons: dict[str, Any] = {}
    evidence_candidates = ["evidence_cf", "evidence_orig"]
    baseline_candidates = [
        "exec_cf",
        "cheap_cf",
        "evidence_orig",
        "exec_orig",
        "cheap_orig",
        "base_qwen3_4b",
    ]
    for evidence_arm in evidence_candidates:
        for baseline_arm in baseline_candidates:
            if evidence_arm == baseline_arm:
                continue
            key = f"{evidence_arm}_minus_{baseline_arm}"
            evidence_test = [
                row for row in by_model[evidence_arm] if row["slice"] == "test"
            ]
            baseline_test = [
                row for row in by_model[baseline_arm] if row["slice"] == "test"
            ]
            evidence_external = [
                row for row in by_model[evidence_arm] if row["slice"] == "external"
            ]
            baseline_external = [
                row for row in by_model[baseline_arm] if row["slice"] == "external"
            ]
            comparisons[key] = {
                "test_answer_correct": cluster_bootstrap_difference(
                    evidence_test,
                    baseline_test,
                    "answer_correct",
                ),
                "external_answer_correct": cluster_bootstrap_difference(
                    evidence_external,
                    baseline_external,
                    "answer_correct",
                ),
                "test_paired_correct_completion": paired_cluster_difference(
                    evidence_test,
                    baseline_test,
                ),
                "external_paired_correct_completion": paired_cluster_difference(
                    evidence_external,
                    baseline_external,
                ),
            }

    delivery: dict[str, Any] = {}
    feature_names = [
        "calculation",
        "unit",
        "period",
        "scope",
        "evidence_values",
        "exact_evidence",
    ]
    for model_arm, model_rows in sorted(by_model.items()):
        dev_rows = [row for row in model_rows if row["slice"] == "dev"]
        x_dev = [
            [float(row["checks"][name]) for name in feature_names]
            + [float(row["interface_valid"]), float(row["embedded_valid"])]
            for row in dev_rows
        ]
        y_dev = [bool(row["answer_correct"]) for row in dev_rows]
        try:
            from sklearn.linear_model import LogisticRegression

            risk_model = LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=20261024,
            )
            risk_model.fit(x_dev, y_dev)
            dev_probability = risk_model.predict_proba(x_dev)[:, 1]
        except Exception as exc:
            risk_model = None
            dev_probability = [1.0 if row["answer_correct"] else 0.0 for row in dev_rows]
            fit_error = repr(exc)
        else:
            fit_error = None
        strong_flags = [
            row["interface_valid"]
            and all(row["checks"][name] for name in feature_names)
            for row in dev_rows
        ]
        strong_dev = policy_metrics(dev_rows, strong_flags)
        threshold = 1.0
        best_coverage = -1.0
        for candidate_threshold in [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
            flags = [float(value) >= candidate_threshold for value in dev_probability]
            metrics = policy_metrics(dev_rows, flags)
            if metrics["wrong_delivery_rate"] <= strong_dev["wrong_delivery_rate"] + 0.01:
                if metrics["correct_delivery_coverage"] > best_coverage:
                    threshold = candidate_threshold
                    best_coverage = metrics["correct_delivery_coverage"]
        slice_delivery: dict[str, Any] = {}
        for slice_name in ("test", "external"):
            subset = [row for row in model_rows if row["slice"] == slice_name]
            x_subset = [
                [float(row["checks"][name]) for name in feature_names]
                + [float(row["interface_valid"]), float(row["embedded_valid"])]
                for row in subset
            ]
            probability = (
                risk_model.predict_proba(x_subset)[:, 1]
                if risk_model is not None
                else [1.0 if row["answer_correct"] else 0.0 for row in subset]
            )
            policy_flags = {
                "all_applicable_pass": [
                    row["interface_valid"]
                    and all(row["checks"][name] for name in feature_names)
                    for row in subset
                ],
                "risk_logistic": [
                    row["interface_valid"] and float(value) >= threshold
                    for row, value in zip(subset, probability)
                ],
                "postprocessed_all_applicable_pass": [
                    row["embedded_valid"]
                    and all(row["checks"][name] for name in feature_names)
                    for row in subset
                ],
                "postprocessed_risk_logistic": [
                    row["embedded_valid"] and float(value) >= threshold
                    for row, value in zip(subset, probability)
                ],
                "any_pass": [
                    row["interface_valid"]
                    and any(row["checks"][name] for name in feature_names)
                    for row in subset
                ],
                "majority_pass": [
                    row["interface_valid"]
                    and sum(bool(row["checks"][name]) for name in feature_names) >= 3
                    for row in subset
                ],
                "always_unknown": [False for _ in subset],
            }
            slice_delivery[slice_name] = {
                policy: policy_metrics(subset, flags)
                for policy, flags in policy_flags.items()
            }
        delivery[model_arm] = {
            "dev_calibration": {
                "strong_rule": strong_dev,
                "risk_threshold": threshold,
                "risk_fit_error": fit_error,
            },
            "held_out": slice_delivery,
        }

    training_summary = collect_training_receipts(run_root)
    generation_receipt = load_json(run_root / "generation_receipt.json")
    summary = {
        "schema": "financial_feedback_learning_result_summary_v1",
        "protocol_sha256": sha256_file(DEFAULT_PROTOCOL),
        "evidence_identity": {
            "task_source": "REAL_TAT-QA_TABLES",
            "task_derivation": "CONTROLLED_DETERMINISTIC_FINANCIAL_CHANGE_TASKS",
            "feedback_corruptions": "CONTROLLED_NOT_NATURAL_ERROR_FREQUENCY",
            "training": "REAL_LORA_SFT",
            "evaluation": "FROZEN_GENERATIONS_WITH_DETERMINISTIC_EXECUTABLE_SCORING",
            "delivery_policy": "POST_HOC_REPLAY_OVER_FROZEN_ANSWERS_AND_CHECK_VECTORS",
        },
        "model_metrics": model_metrics,
        "paired_comparisons": comparisons,
        "delivery": delivery,
        "training": training_summary,
        "generation": generation_receipt,
    }
    write_json(run_root / "RESULT_SUMMARY.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    """Parse experiment stage arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=("build", "train", "evaluate", "analyze", "all"),
    )
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument(
        "--arms",
        nargs="+",
        default=["exec_orig", "evidence_orig", "exec_cf", "evidence_cf"],
    )
    return parser.parse_args()


def main() -> int:
    """Run the requested experiment stage."""
    args = parse_args()
    protocol = resolve_protocol(args.protocol)
    require(
        protocol.get("status")
        in {
            "FROZEN_BEFORE_MODEL_GENERATION_AND_TRAINING",
            "FROZEN_BEFORE_CHEAP_TRAINING_AND_ALL_EVALUATION",
            "FROZEN_BEFORE_BATCHED_EVALUATION_AFTER_INTERRUPTED_RUN",
        },
        "protocol_not_frozen",
    )
    if args.stage in {"build", "all"}:
        build_dataset(protocol, args.run_root)
    if args.stage in {"train", "all"}:
        train_arms(protocol, args.run_root, args.arms)
    if args.stage in {"evaluate", "all"}:
        evaluate_models(
            protocol,
            args.run_root,
            ["base_qwen3_4b", *args.arms],
        )
    if args.stage in {"analyze", "all"}:
        summary = analyze_results(protocol, args.run_root)
        print(json.dumps(summary["model_metrics"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

