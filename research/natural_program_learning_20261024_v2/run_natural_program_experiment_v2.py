"""Natural TAT-QA structured-program SFT and visible-feedback comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "feedback_learning_finance_20261024_v2"),
)

from natural_program_contract_v2 import execute_program, program_refs, table_cells
from natural_program_contract_v2 import parse_numeric
from build_natural_tasks_v2 import (
    build_prompt,
    render_table,
    table_cells_from_text,
)


def sha256_file(path: Path) -> str:
    """Hash a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    """Write pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def resolve_protocol(path: Path) -> dict[str, Any]:
    """Load the base protocol or merge a bounded amendment."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "natural_tatqa_program_learning_amendment_v1":
        return payload
    base_path = path.parent / payload["base_protocol"]
    base = json.loads(base_path.read_text(encoding="utf-8"))
    for section, values in payload.get("changes", {}).items():
        if isinstance(values, dict) and isinstance(base.get(section), dict):
            merged = dict(base[section])
            merged.update(values)
            base[section] = merged
        else:
            base[section] = values
    base["status"] = payload["status"]
    base["protocol_amendment"] = {
        "path": str(path),
        "sha256": sha256_file(path),
        "base_sha256": sha256_file(base_path),
    }
    return base


def stable_hash(value: str) -> str:
    """Return a stable hash."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def program_value(program: dict[str, Any], cell_values: dict[str, float]) -> float:
    """Execute a structured program over rendered cell values."""
    if "ref" in program:
        ref = str(program["ref"])
        if ref not in cell_values:
            raise ValueError(f"missing_ref:{ref}")
        return float(cell_values[ref])
    if "const" in program:
        return float(program["const"])
    left = program_value(program["left"], cell_values)
    right = program_value(program["right"], cell_values)
    op = program["op"]
    if op == "add":
        return left + right
    if op == "sub":
        return left - right
    if op == "mul":
        return left * right
    if op == "div":
        if right == 0:
            raise ZeroDivisionError("division_by_zero")
        return left / right
    raise ValueError(f"unsupported_op:{op}")


def rendered_values(table_text: str) -> dict[str, float]:
    """Parse numeric values from rendered R:C table text."""
    values: dict[str, float] = {}
    for line in table_text.splitlines()[1:]:
        row_match = re.match(r"^(R\d+) \[(.*?)\] (.*)$", line)
        if not row_match:
            continue
        row_id, _row_label, body = row_match.groups()
        for match in re.finditer(r"(C\d+)=([^|]+)", body):
            column_id, raw_value = match.groups()
            value = parse_numeric(raw_value)
            if value is not None:
                values[f"{row_id}:{column_id}"] = value
    return values


def program_is_valid(program: dict[str, Any], values: dict[str, float]) -> bool:
    """Check that a program references visible cells and executes."""
    try:
        refs = program_refs(program)
        return bool(refs) and all(ref in values for ref in refs) and math.isfinite(
            program_value(program, values)
        )
    except (ValueError, KeyError, TypeError, ZeroDivisionError):
        return False


def question_operator_cue(question: str) -> str | None:
    """Infer a coarse operator cue from natural language."""
    lowered = question.casefold()
    if "percentage change" in lowered or "percent change" in lowered:
        return "percent"
    if any(word in lowered for word in ("difference", "change", "increase", "decrease")):
        return "difference"
    if any(word in lowered for word in ("average", "mean")):
        return "aggregate"
    return None


def program_shape(program: dict[str, Any]) -> str:
    """Classify the root program shape."""
    if "op" not in program:
        return "leaf"
    return str(program["op"])


def visible_filter(task: dict[str, Any], candidate: dict[str, Any]) -> bool:
    """Filter candidates using only visible question/table/program fields."""
    values = rendered_values(task["table_text"])
    if not program_is_valid(candidate["program"], values):
        return False
    if set(candidate.get("evidence_refs", [])) != set(program_refs(candidate["program"])):
        return False
    cue = question_operator_cue(task["question"])
    root = program_shape(candidate["program"])
    if cue == "percent":
        return root in {"mul", "div"}
    if cue == "difference":
        return root == "sub"
    return True


def mutate_constant(program: dict[str, Any]) -> dict[str, Any]:
    """Change one numeric constant in a program."""
    updated = deepcopy(program)

    def visit(node: dict[str, Any]) -> bool:
        if "const" in node:
            node["const"] = float(node["const"]) + 1.0
            return True
        if "op" in node:
            return visit(node["left"]) or visit(node["right"])
        return False

    if not visit(updated):
        raise ValueError("no_constant_to_mutate")
    return updated


def mutate_reference(
    program: dict[str, Any],
    values: dict[str, float],
) -> dict[str, Any]:
    """Replace one evidence ref with another visible cell."""
    updated = deepcopy(program)
    refs = program_refs(updated)
    replacement = next((ref for ref in values if ref not in refs), None)
    if replacement is None:
        raise ValueError("no_replacement_ref")

    def visit(node: dict[str, Any]) -> bool:
        if "ref" in node:
            node["ref"] = replacement
            return True
        if "op" in node:
            return visit(node["left"]) or visit(node["right"])
        return False

    visit(updated)
    return updated


def mutate_operator(program: dict[str, Any]) -> dict[str, Any]:
    """Change the root arithmetic operator."""
    updated = deepcopy(program)
    replacements = {"add": "sub", "sub": "add", "mul": "div", "div": "mul"}
    if "op" not in updated:
        raise ValueError("leaf_program")
    updated["op"] = replacements.get(str(updated["op"]), "add")
    return updated


def mutate_rendered_cell(table_text: str, ref: str, value: float) -> str:
    """Mutate one rendered R:C cell without changing unrelated text."""
    row_match = re.match(r"R(\d+):C(\d+)$", ref)
    if not row_match:
        raise ValueError(f"invalid_ref:{ref}")
    row_id, column_id = row_match.groups()
    lines = table_text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(f"R{row_id} "):
            continue
        updated = re.sub(
            rf"(C{column_id}=)[^|]+",
            rf"\g<1>{value}",
            line,
            count=1,
        )
        if updated != line:
            lines[index] = updated
            return "\n".join(lines)
    raise ValueError(f"rendered_ref_not_found:{ref}")


def candidate_pool(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Create controlled teacher candidates for feedback comparison."""
    gold = deepcopy(task["target"])
    values = rendered_values(task["table_text"])
    candidates = [
        {
            "candidate_id": "gold",
            "target": gold,
            "error_type": "none",
        }
    ]
    try:
        candidates.append({
            "candidate_id": "wrong_constant",
            "target": {**gold, "program": mutate_constant(gold["program"])},
            "error_type": "wrong_constant",
        })
    except ValueError:
        pass
    try:
        wrong_ref = mutate_reference(gold["program"], values)
        candidates.append({
            "candidate_id": "wrong_reference",
            "target": {
                **gold,
                "program": wrong_ref,
                "evidence_refs": program_refs(wrong_ref),
            },
            "error_type": "wrong_reference",
        })
    except ValueError:
        pass
    try:
        wrong_op = mutate_operator(gold["program"])
        candidates.append({
            "candidate_id": "wrong_operator",
            "target": {
                **gold,
                "program": wrong_op,
                "evidence_refs": program_refs(wrong_op),
            },
            "error_type": "wrong_operator",
        })
    except ValueError:
        pass
    for candidate in candidates:
        try:
            result = program_value(candidate["target"]["program"], values)
            candidate["program_value"] = float(result)
            candidate["visible_filter_pass"] = visible_filter(task, candidate["target"])
            candidate["hidden_answer_pass"] = math.isclose(
                float(result),
                float(task["expected"]["answer"]),
                rel_tol=1e-6,
                abs_tol=1e-6,
            )
        except (ValueError, KeyError, TypeError, ZeroDivisionError):
            candidate["program_value"] = None
            candidate["visible_filter_pass"] = False
            candidate["hidden_answer_pass"] = False
    return candidates


def choose_training_target(
    task: dict[str, Any],
    arm: str,
) -> dict[str, Any]:
    """Choose one candidate using the specified feedback policy."""
    candidates = candidate_pool(task)
    if arm == "ordinary_answer_execution_sft":
        eligible = [candidate for candidate in candidates if candidate["hidden_answer_pass"]]
    elif arm == "visible_program_filter_sft":
        eligible = [candidate for candidate in candidates if candidate["visible_filter_pass"]]
    else:
        raise ValueError(f"unknown_arm:{arm}")
    if not eligible:
        eligible = [next(candidate for candidate in candidates if candidate["candidate_id"] == "gold")]
    index = int(stable_hash(task["task_id"] + arm)[:8], 16) % len(eligible)
    return eligible[index]["target"]


def target_text(target: dict[str, Any]) -> str:
    """Serialize the deployment target contract."""
    return json.dumps(
        {
            "program": target["program"],
            "evidence_refs": target["evidence_refs"],
            "unit": target["unit"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def training_rows(tasks: list[dict[str, Any]], arm: str) -> list[dict[str, Any]]:
    """Create matched natural-program SFT rows."""
    train_tasks = [task for task in tasks if task["split"] == "train"]
    train_tasks = sorted(train_tasks, key=lambda task: stable_hash(task["task_id"]))[:512]
    rows = []
    for task in train_tasks:
        target = choose_training_target(task, arm)
        rows.append({
            "row_id": f"{task['task_id']}::{arm}",
            "task_id": task["task_id"],
            "table_uid": task["table_uid"],
            "target": target,
            "text": task["prompt"] + "\n" + target_text(target),
        })
    return rows


def train_arm(arm: str, rows: list[dict[str, Any]], run_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Train one natural-program LoRA arm."""
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    set_seed(int(config["seed"]))
    model_path = Path(config["model_path_gb10"])
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    arm_dir = run_root / "training" / arm
    arm_dir.mkdir(parents=True, exist_ok=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model.config.use_cache = False
    trainer = SFTTrainer(
        model=model,
        args=SFTConfig(
            output_dir=str(arm_dir),
            max_steps=int(config["max_steps_per_arm"]),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=2,
            learning_rate=float(config["learning_rate"]),
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
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
        ),
        train_dataset=Dataset.from_list([{"text": row["text"]} for row in rows]),
        peft_config=LoraConfig(
            r=int(config["lora_r"]),
            lora_alpha=int(config["lora_alpha"]),
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=list(config["target_modules"]),
        ),
        processing_class=tokenizer,
    )
    started = time.time()
    result = trainer.train()
    elapsed = time.time() - started
    adapter = arm_dir / "final_adapter"
    trainer.save_model(str(adapter))
    tokenizer.save_pretrained(str(adapter))
    receipt = {
        "schema": "natural_program_training_receipt_v2",
        "arm": arm,
        "rows": len(rows),
        "unique_tasks": len({row["task_id"] for row in rows}),
        "training_runtime_seconds": elapsed,
        "train_metrics": result.metrics,
        "adapter_path": str(adapter),
        "model_path": str(model_path),
    }
    write_json(arm_dir / "training_receipt.json", receipt)
    del trainer
    del model
    torch.cuda.empty_cache()
    return receipt


def make_variants(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Create controlled relevant/irrelevant prompt variants."""
    variants = [
        {
            "variant": "original",
            "prompt": task["prompt"],
            "expected": deepcopy(task["expected"]),
        }
    ]
    values = rendered_values(task["table_text"])
    refs = task["expected"]["evidence_refs"]
    if refs:
        relevant_ref = refs[0]
        try:
            old_value = rendered_values(task["table_text"])[relevant_ref]
            new_value = old_value + max(1.0, abs(old_value) * 0.1)
            changed = mutate_rendered_cell(task["table_text"], relevant_ref, new_value)
            expected = deepcopy(task["expected"])
            cell_values = rendered_values(changed)
            expected["answer"] = program_value(expected["program"], cell_values)
            variants.append({
                "variant": "relevant_change",
                "prompt": build_prompt(task["question"], changed, task.get("context_text", "")),
                "expected": expected,
            })
        except (KeyError, ValueError, ZeroDivisionError):
            pass
    non_refs = [ref for ref in values if ref not in refs]
    if non_refs:
        irrelevant_ref = non_refs[0]
        try:
            old_value = rendered_values(task["table_text"])[irrelevant_ref]
            new_value = old_value + max(1.0, abs(old_value) * 0.1)
            changed = mutate_rendered_cell(task["table_text"], irrelevant_ref, new_value)
            variants.append({
                "variant": "irrelevant_change",
                "prompt": build_prompt(task["question"], changed, task.get("context_text", "")),
                "expected": deepcopy(task["expected"]),
            })
        except (KeyError, ValueError):
            pass
    return variants


def extract_target(text: str) -> dict[str, Any] | None:
    """Extract one structured target JSON object."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and {"program", "evidence_refs", "unit"} <= set(value):
            return value
    return None


def evaluate_target(
    generated: str,
    instance: dict[str, Any],
) -> dict[str, Any]:
    """Execute a generated program against the current variant table."""
    target = extract_target(generated)
    values = rendered_values(instance["table_text"])
    if target is None:
        return {
            "interface_valid": False,
            "program_executable": False,
            "program_correct": False,
            "program_value": None,
            "refs_valid": False,
            "failure": "program_parse",
        }
    refs = [str(ref) for ref in target.get("evidence_refs", [])]
    refs_valid = bool(refs) and all(ref in values for ref in refs)
    try:
        value = program_value(target["program"], values)
        executable = True
    except (ValueError, KeyError, TypeError, ZeroDivisionError):
        value = None
        executable = False
    correct = (
        executable
        and value is not None
        and math.isclose(
            float(value),
            float(instance["expected"]["answer"]),
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
    )
    return {
        "interface_valid": True,
        "program_executable": executable,
        "program_correct": correct,
        "program_value": value,
        "refs_valid": refs_valid,
        "failure": "none" if correct else ("tool_execution" if executable else "program_execution"),
    }


def generate_and_score(
    model: Any,
    tokenizer: Any,
    instance: dict[str, Any],
    max_new_tokens: int,
) -> dict[str, Any]:
    """Generate and score one natural-program instance."""
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
    latency = (time.time() - started) * 1000.0
    generated = tokenizer.decode(output[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    scored = evaluate_target(generated, instance)
    return {
        "instance_id": instance["instance_id"],
        "source_task_id": instance["source_task_id"],
        "table_uid": instance["table_uid"],
        "slice": instance["slice"],
        "variant": instance["variant"],
        "generated_text": generated,
        "prompt_tokens": int(inputs["input_ids"].shape[1]),
        "completion_tokens": int(output.shape[1] - inputs["input_ids"].shape[1]),
        "latency_ms": latency,
        **scored,
    }


def generate_and_score_batch(
    model: Any,
    tokenizer: Any,
    instances: list[dict[str, Any]],
    max_new_tokens: int,
) -> list[dict[str, Any]]:
    """Generate and score one fixed batch without changing the task contract."""
    import torch

    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    inputs = tokenizer(
        [instance["prompt"] for instance in instances],
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
    batch_latency = (time.time() - started) * 1000.0
    rows = []
    for index, instance in enumerate(instances):
        generated = tokenizer.decode(
            output[index][input_width:],
            skip_special_tokens=True,
        )
        scored = evaluate_target(generated, instance)
        rows.append({
            "instance_id": instance["instance_id"],
            "source_task_id": instance["source_task_id"],
            "table_uid": instance["table_uid"],
            "slice": instance["slice"],
            "variant": instance["variant"],
            "generated_text": generated,
            "prompt_tokens": int(inputs["attention_mask"][index].sum().item()),
            "completion_tokens": int(output.shape[1] - input_width),
            "latency_ms": batch_latency / len(instances),
            "batch_latency_ms": batch_latency,
            "batch_size": len(instances),
            **scored,
        })
    return rows


def evaluate_models(
    tasks: list[dict[str, Any]],
    run_root: Path,
    arms: list[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate base and two new adapters on natural task variants."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    selected = []
    for slice_name, count in config["tasks_per_slice"].items():
        subset = [task for task in tasks if task["split"] == slice_name]
        subset = sorted(subset, key=lambda task: stable_hash(task["task_id"]))[: int(count)]
        for task in subset:
            for variant in make_variants(task):
                selected.append({
                    "instance_id": f"{task['task_id']}::{variant['variant']}",
                    "source_task_id": task["task_id"],
                    "table_uid": task["table_uid"],
                    "slice": slice_name,
                    "variant": variant["variant"],
                    "prompt": variant["prompt"],
                    "expected": variant["expected"],
                    "table_text": task["table_text"],
                })
    write_jsonl(run_root / "evaluation_instances_v2.jsonl", selected)
    model_path = Path(config["model_path_gb10"])
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = []
    receipts = {}
    for arm in arms:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
        if arm != "base_qwen3_4b":
            model = PeftModel.from_pretrained(
                model,
                run_root / "training" / arm / "final_adapter",
            )
        model.eval()
        arm_rows = []
        started = time.time()
        batch_size = int(config.get("generation_batch_size", 8))
        max_new_tokens = int(config.get("max_new_tokens", 512))
        partial_path = run_root / "generation_results_v2.partial.jsonl"
        for start in range(0, len(selected), batch_size):
            batch = selected[start : start + batch_size]
            batch_rows = generate_and_score_batch(
                model,
                tokenizer,
                batch,
                max_new_tokens,
            )
            for row in batch_rows:
                row["model_arm"] = arm
                arm_rows.append(row)
                rows.append(row)
            with partial_path.open("a", encoding="utf-8", newline="\n") as handle:
                for row in batch_rows:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            print(f"{arm}: {len(arm_rows)}/{len(selected)}", flush=True)
        receipts[arm] = {
            "instances": len(arm_rows),
            "accounting_attempts": len(arm_rows),
            "prompt_tokens": sum(row["prompt_tokens"] for row in arm_rows),
            "completion_tokens": sum(row["completion_tokens"] for row in arm_rows),
            "wall_seconds": time.time() - started,
        }
        del model
        torch.cuda.empty_cache()
    write_jsonl(run_root / "generation_results_v2.jsonl", rows)
    receipt = {
        "schema": "natural_program_generation_receipt_v2",
        "results_sha256": sha256_file(run_root / "generation_results_v2.jsonl"),
        "instances": len(selected),
        "models": receipts,
        "accounting_attempts": sum(item["accounting_attempts"] for item in receipts.values()),
        "prompt_tokens": sum(item["prompt_tokens"] for item in receipts.values()),
        "completion_tokens": sum(item["completion_tokens"] for item in receipts.values()),
        "new_judge_calls": 0,
    }
    write_json(run_root / "generation_receipt_v2.json", receipt)
    return receipt


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize natural program results by model/slice/variant."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_arm"], row["slice"])].append(row)
    output = {}
    for (arm, slice_name), subset in sorted(grouped.items()):
        pairs = defaultdict(dict)
        for row in subset:
            pairs[row["source_task_id"]][row["variant"]] = row
        paired = []
        for variants in pairs.values():
            if {"original", "relevant_change", "irrelevant_change"} <= set(variants):
                paired.append(all(
                    variants[name]["program_correct"]
                    for name in ("original", "relevant_change", "irrelevant_change")
                ))
        output.setdefault(arm, {})[slice_name] = {
            "instances": len(subset),
            "program_correct": sum(row["program_correct"] for row in subset),
            "interface_valid": sum(row["interface_valid"] for row in subset),
            "refs_valid": sum(row["refs_valid"] for row in subset),
            "paired_tasks": len(paired),
            "paired_program_correct": sum(paired),
            "paired_rate": sum(paired) / len(paired) if paired else 0.0,
            "failures": dict(Counter(row["failure"] for row in subset)),
        }
    return output


def main() -> int:
    """Run build, training, evaluation and analysis stages."""
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("build", "train", "evaluate", "analyze", "all"))
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--train-source", type=Path, required=True)
    parser.add_argument("--external-source", type=Path, required=True)
    args = parser.parse_args()
    protocol = resolve_protocol(args.protocol)
    if protocol.get("status") not in {
        "FROZEN_BEFORE_NATURAL_TRAINING",
        "FROZEN_BEFORE_NATURAL_EVALUATION_RETRY",
    }:
        raise ValueError("protocol_not_frozen")
    run_root = args.run_root
    run_root.mkdir(parents=True, exist_ok=True)
    if args.stage in {"build", "all"}:
        import build_natural_tasks_v2

        tasks = build_natural_tasks_v2.build_dataset(
            args.train_source,
            args.external_source,
            max_tasks_per_table=2,
            seed=20261024,
        )
        write_jsonl(run_root / "natural_tasks_v2.jsonl", tasks)
        write_json(
            run_root / "natural_dataset_receipt_v2.json",
            {
                "schema": "natural_tatqa_program_dataset_v2",
                "task_count": len(tasks),
                "split_counts": dict(Counter(task["split"] for task in tasks)),
                "source_hashes": {
                    "train": sha256_file(args.train_source),
                    "external": sha256_file(args.external_source),
                },
            },
        )
    tasks = load_jsonl(run_root / "natural_tasks_v2.jsonl")
    if args.stage in {"train", "all"}:
        receipts = {
            arm: train_arm(arm, training_rows(tasks, arm), run_root, protocol["training"])
            for arm in ["ordinary_answer_execution_sft", "visible_program_filter_sft"]
        }
        write_json(run_root / "training_summary_v2.json", receipts)
    if args.stage in {"evaluate", "all"}:
        evaluate_models(
            tasks,
            run_root,
            ["base_qwen3_4b", "ordinary_answer_execution_sft", "visible_program_filter_sft"],
            protocol["evaluation"] | {"model_path_gb10": protocol["training"]["model_path_gb10"]},
        )
    if args.stage in {"analyze", "all"}:
        summary = summarize_results(load_jsonl(run_root / "generation_results_v2.jsonl"))
        write_json(run_root / "RESULT_SUMMARY_V2.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

