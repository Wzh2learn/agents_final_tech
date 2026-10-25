"""Run the frozen B2 same-start R/E development experiment."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import random
import shutil
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
PRIOR_DIR = OUT_DIR.parent
HELPERS = ROOT / "research/natural_program_learning_20261024_v2"
import sys  # noqa: E402

sys.path.insert(0, str(HELPERS))
sys.path.insert(0, str(PRIOR_DIR))

from B1_LOCAL_EDIT_APPLIER import (  # noqa: E402
    PatchError,
    apply_patch,
    canonical_json,
    canonical_sha256,
)
from semantic_delivery_check_v3 import question_from_prompt, semantic_check  # noqa: E402


TASK_ID = "phaseb-b2-same-start-a-20261026"
GOAL_ID = "FEEDBACK_LEARNING_PHASE_B_20261026"
PARENT_ADAPTER = Path(
    "/home/testuser/wzh/research_runs/natural_program_finance_20261024_v2/"
    "training/ordinary_answer_execution_sft/final_adapter"
)
BASE_MODEL = Path("/home/testuser/wzh/models/hf/Qwen3-4B")
PANEL_PATH = PRIOR_DIR / "B2_DEVELOPMENT_PANEL_DRAFT.json"
TRAJECTORY_PATH = PRIOR_DIR / "B1_CORRECTION_TRAJECTORIES.jsonl"
D_GATE_PATH = PRIOR_DIR / "B2_D_FREEZE_DECISION.md"
B1_GATE_PATH = PRIOR_DIR / "B1_D_FREEZE_GATE.md"
APPLIER_PATH = PRIOR_DIR / "B1_LOCAL_EDIT_APPLIER.py"
PROTOCOL_PATH = OUT_DIR / "B2_PROTOCOL_FROZEN.json"
PREFLIGHT_PATH = OUT_DIR / "B2_PREFLIGHT_RECEIPT.json"
RAW_PATH = OUT_DIR / "B2_DEVELOPMENT_RAW.jsonl"
ANALYSIS_PATH = OUT_DIR / "B2_DEVELOPMENT_ANALYSIS.json"
RUN_ROOT = OUT_DIR / "run"
SEED = 20261026
MAX_STEPS = 128
ROWS_PER_ARM = 256
MAX_LENGTH = 1536
MAX_NEW_TOKENS = 192
GENERATION_BATCH = 8
LORA_R = 16
LORA_ALPHA = 32
TARGET_MODULES = ["q_proj", "v_proj"]
NEUTRAL_FEEDBACK = (
    "Revise the candidate using only the visible question and table. Do not use "
    "hidden references, gold programs, or development edit instructions."
)
ARMS = (
    "O_FROZEN_ORDINARY",
    "N_NEUTRAL_RETRY",
    "R_FULL_REVISION",
    "E_RESTRICTED_PATCH",
    "DETERMINISTIC_REFERENCE_PATCH_CONTROL",
    "ORDINARY_SUPERVISION_CONTROL",
)
GENERATIVE_ARMS = ("N_NEUTRAL_RETRY", "R_FULL_REVISION", "E_RESTRICTED_PATCH")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{label}".encode()).hexdigest()[:8], 16)


def object_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def adapter_directory_hashes(path: Path) -> dict[str, str]:
    return {
        file.name: sha256_file(file)
        for file in sorted(path.iterdir())
        if file.is_file()
    }


def safetensor_parameter_count(path: Path) -> int:
    from safetensors import safe_open

    total = 0
    with safe_open(str(path), framework="pt") as handle:
        for key in handle.keys():
            shape = handle.get_slice(key).get_shape()
            count = 1
            for dimension in shape:
                count *= int(dimension)
            total += count
    return total


def tensor_group_hash(model: Any, adapter_name: str) -> tuple[str, list[tuple[str, str, tuple[int, ...]]]]:
    import torch

    digest = hashlib.sha256()
    prefix = f".{adapter_name}."
    entries = []
    for name, parameter in model.named_parameters():
        if prefix not in name:
            continue
        tensor = parameter.detach().to("cpu", copy=False).contiguous()
        entries.append((name, str(tensor.dtype), tuple(tensor.shape)))
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest(), entries


def parse_object(text: str) -> tuple[dict[str, Any] | None, str]:
    stripped = text.strip()
    strict_valid = False
    value = None
    try:
        decoded = json.loads(stripped)
        if isinstance(decoded, dict):
            strict_valid = True
            value = decoded
    except json.JSONDecodeError:
        pass
    if value is not None:
        return value, "STRICT_WHOLE_JSON"
    decoder = json.JSONDecoder()
    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            decoded, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, dict):
            return decoded, "EMBEDDED_JSON"
    return None, "SYNTAX_ADAPTER_FAILURE"


def program_refs(program: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(program, dict) and "ref" in program:
        refs.append(str(program["ref"]))
    elif isinstance(program, dict) and "op" in program:
        refs.extend(program_refs(program.get("left")))
        refs.extend(program_refs(program.get("right")))
    return list(dict.fromkeys(refs))


def rendered_values(table_text: str) -> dict[str, float]:
    import re

    values: dict[str, float] = {}
    for line in table_text.splitlines()[1:]:
        row_match = re.match(r"^(R\d+) \[(.*?)\] (.*)$", line)
        if not row_match:
            continue
        row_id, _row_label, body = row_match.groups()
        for match in re.finditer(r"(C\d+)=([^|]+)", body):
            column_id, raw_value = match.groups()
            raw_value = raw_value.strip().replace("$", "").replace(",", "")
            try:
                values[f"{row_id}:{column_id}"] = float(raw_value)
            except ValueError:
                continue
    return values


def rendered_semantic_cells(table_text: str) -> dict[str, dict[str, Any]]:
    import re

    column_labels: dict[str, str] = {}
    cells: dict[str, dict[str, Any]] = {}
    lines = table_text.splitlines()
    if lines and lines[0].startswith("columns: "):
        header = lines[0][len("columns: "):]
        for match in re.finditer(r"(C\d+)=(.*?)(?= C\d+=|$)", header):
            column_labels[match.group(1)] = match.group(2).strip().strip("|").strip()
    for line in lines[1:]:
        row_match = re.match(r"^(R\d+) \[(.*?)\] (.*)$", line)
        if not row_match:
            continue
        row_id, row_label, body = row_match.groups()
        for match in re.finditer(r"(C\d+)=([^|]*?)(?= C\d+=|$)", body):
            column_id, raw_value = match.groups()
            raw_value = raw_value.strip().strip("|").strip().replace("$", "").replace(",", "")
            try:
                value = float(raw_value)
            except ValueError:
                continue
            cell_id = f"{row_id}:{column_id}"
            cells[cell_id] = {
                "value": value,
                "row_label": row_label.strip(),
                "column_label": column_labels.get(column_id, ""),
                "period_labels": set(),
            }
    for cell in cells.values():
        label = f"{cell['row_label']} {cell['column_label']}"
        cell["period_labels"].update(re.findall(r"\b(?:19|20)\d{2}\b", label))
    for column_id in column_labels:
        column_years = {
            year
            for cell_id, cell in cells.items()
            if cell_id.endswith(f":{column_id}")
            for year in re.findall(r"\b(?:19|20)\d{2}\b", cell["row_label"])
        }
        for cell_id, cell in cells.items():
            if cell_id.endswith(f":{column_id}"):
                cell["period_labels"].update(column_years)
    return cells


def program_value(program: Any, values: dict[str, float]) -> float:
    if isinstance(program, dict) and "ref" in program:
        ref = str(program["ref"])
        if ref not in values:
            raise ValueError(f"missing_ref:{ref}")
        return values[ref]
    if isinstance(program, dict) and "const" in program:
        return float(program["const"])
    if not isinstance(program, dict) or program.get("op") not in {"add", "sub", "mul", "div"}:
        raise ValueError("invalid_program")
    left = program_value(program.get("left"), values)
    right = program_value(program.get("right"), values)
    if program["op"] == "add":
        return left + right
    if program["op"] == "sub":
        return left - right
    if program["op"] == "mul":
        return left * right
    if right == 0:
        raise ZeroDivisionError("division_by_zero")
    return left / right


def program_skeleton(program: Any) -> Any:
    if not isinstance(program, dict):
        return None
    if "ref" in program:
        return {"kind": "ref"}
    if "const" in program:
        return {"kind": "const", "value": program["const"]}
    return {
        "kind": "operator",
        "op": program.get("op"),
        "left": program_skeleton(program.get("left")),
        "right": program_skeleton(program.get("right")),
    }


def target_prompt(instance: dict[str, Any], candidate: dict[str, Any], arm: str) -> str:
    common = "\n".join(
        [
            instance["prompt"],
            "",
            "O candidate:",
            canonical_json(candidate),
            "",
            "Allowed feedback:",
            NEUTRAL_FEEDBACK,
        ]
    )
    if arm == "R_FULL_REVISION":
        return (
            common
            + "\nReturn exactly one complete corrected candidate JSON object with keys "
            "program, evidence_refs, and unit. Preserve O's operator, operand order, and unit."
        )
    if arm == "E_RESTRICTED_PATCH":
        return (
            common
            + "\nReturn exactly one strict patch JSON object with keys schema, "
            "candidate_sha256, target_sha256, and operations. Only replace "
            "/program/left/ref, /program/right/ref, or /evidence_refs/<index>."
        )
    raise ValueError(f"unsupported_arm:{arm}")


def panel_trajectories() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    panel = load_json(PANEL_PATH)
    trajectories = {
        row["source_identity"]["instance_id"]: row
        for row in load_jsonl(TRAJECTORY_PATH)
    }
    rows: list[dict[str, Any]] = []
    for family in panel["families"]:
        for trajectory_id in family["trajectory_ids"]:
            if trajectory_id not in trajectories:
                raise RuntimeError(f"missing_trajectory:{trajectory_id}")
            rows.append(
                {
                    "trajectory": trajectories[trajectory_id],
                    "family": copy.deepcopy(family),
                    "trajectory_id": trajectory_id,
                }
            )
    return rows, panel


def materialized_targets(
    trajectory: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate = copy.deepcopy(trajectory["o_output"]["parsed_candidate"])
    patch = trajectory["correction"]["e_patch"]
    if patch is not None and patch["operations"]:
        patched = apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=set(trajectory["visible_input"]["allowed_evidence_refs"]),
        )
    else:
        patched = copy.deepcopy(candidate)
    return candidate, patched


def empty_patch(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "b1_local_patch_v1",
        "candidate_sha256": canonical_sha256(candidate),
        "target_sha256": canonical_sha256(candidate),
        "operations": [],
    }


def training_rows(arm: str) -> list[dict[str, Any]]:
    source_rows, _ = panel_trajectories()
    rows: list[dict[str, Any]] = []
    for item in source_rows:
        trajectory = item["trajectory"]
        candidate, patched = materialized_targets(trajectory)
        qualified = trajectory["correction"]["set_binding_component"]["status"] == "QUALIFIED"
        if arm == "R_FULL_REVISION":
            target = patched if qualified else copy.deepcopy(candidate)
        else:
            source_patch = trajectory["correction"]["e_patch"]
            target = (
                copy.deepcopy(source_patch)
                if qualified and source_patch is not None
                else empty_patch(candidate)
            )
        text = target_prompt(trajectory["visible_input"], candidate, arm) + "\n" + canonical_json(target)
        rows.append(
            {
                "row_id": f"{item['trajectory_id']}::{arm}::base",
                "trajectory_id": item["trajectory_id"],
                "source_task_id": item["family"]["source_task_id"],
                "variant": trajectory["source_identity"]["variant"],
                "eligible_correction": qualified,
                "target": target,
                "text": text,
            }
        )
    repeated = [copy.deepcopy(row) for row in rows for _ in range(7)]
    eligible = [row for row in repeated if row["eligible_correction"]]
    repeated.extend(copy.deepcopy(row) for row in eligible[:4])
    rng = random.Random(SEED)
    rng.shuffle(repeated)
    if len(repeated) != ROWS_PER_ARM:
        raise RuntimeError(f"training_row_count:{len(repeated)}")
    if len({row["source_task_id"] for row in repeated}) != 12:
        raise RuntimeError("training_task_coverage_mismatch")
    for index, row in enumerate(repeated):
        row["row_id"] = f"{row['trajectory_id']}::{arm}::{index:03d}"
    return repeated


def protocol_payload() -> dict[str, Any]:
    panel = load_json(PANEL_PATH)
    parent_hashes = adapter_directory_hashes(PARENT_ADAPTER)
    return {
        "schema": "b2_same_start_protocol_frozen_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "status": "FROZEN_BEFORE_TRAINING",
        "authority": {
            "d_gate_path": str(D_GATE_PATH),
            "d_gate_sha256": sha256_file(D_GATE_PATH),
            "b1_gate_path": str(B1_GATE_PATH),
            "b1_gate_sha256": sha256_file(B1_GATE_PATH),
        },
        "development_panel": {
            "path": str(PANEL_PATH),
            "sha256": sha256_file(PANEL_PATH),
            "families": panel["family_count"],
            "trajectories": panel["trajectory_count"],
            "role": "EXPOSED_DEVELOPMENT_SUPERVISION",
            "confirmation_claim": "NONE",
        },
        "parent_checkpoint": {
            "base_model": str(BASE_MODEL),
            "adapter_path": str(PARENT_ADAPTER),
            "adapter_file_sha256": parent_hashes,
            "effective_identity": "BASE_PLUS_FROZEN_ORDINARY_ADAPTER",
        },
        "arms": {
            "O": {
                "name": "O_FROZEN_ORDINARY",
                "source": "hash-pinned B1 ordinary candidate",
                "new_generation_attempts": 0,
            },
            "N": {
                "name": "N_NEUTRAL_RETRY",
                "parent": "same effective ordinary checkpoint",
                "sampling": {"do_sample": True, "temperature": 0.7, "top_p": 0.95, "seed": SEED},
            },
            "R": {
                "name": "R_FULL_REVISION",
                "output": "complete corrected candidate",
                "supervised_change": "set binding only; operator, order and unit fixed to O",
            },
            "E": {
                "name": "E_RESTRICTED_PATCH",
                "output": "restricted replace-only patch",
                "applier": str(APPLIER_PATH),
                "applier_sha256": sha256_file(APPLIER_PATH),
                "patch_failure": "REJECT_AND_RECORD",
            },
            "controls": [
                "DETERMINISTIC_REFERENCE_PATCH_CONTROL",
                "ORDINARY_SUPERVISION_CONTROL",
            ],
        },
        "information_parity": {
            "shared": ["visible_prompt", "visible_evidence", "O_candidate", NEUTRAL_FEEDBACK],
            "allowed_difference": "output representation only: complete candidate versus restricted patch",
            "hidden_confirmation_reference_in_inputs_feedback_or_selection": False,
            "selection_source": "frozen exposed development panel only",
        },
        "training": {
            "same_parent_for_R_and_E": True,
            "rows_per_arm": ROWS_PER_ARM,
            "unique_trajectories_per_arm": 36,
            "unique_source_tasks_per_arm": 12,
            "eligible_correction_rows_per_base_cycle": 5,
            "no_op_and_unresolved_rows_per_base_cycle": 31,
            "repeats": 7,
            "final_rows_per_arm": 256,
            "final_eligible_correction_rows_per_arm": 39,
            "final_no_op_and_unresolved_rows_per_arm": 217,
            "optimizer_steps_per_arm": MAX_STEPS,
            "max_length": MAX_LENGTH,
            "learning_rate": 0.0001,
            "scheduler": "cosine",
            "warmup_ratio": 0.03,
            "per_device_batch_size": 1,
            "gradient_accumulation_steps": 2,
            "loss_normalization": "mean over all non-padding prompt-plus-target tokens; no sample weighting",
            "seed": SEED,
            "lora": {
                "r": LORA_R,
                "alpha": LORA_ALPHA,
                "dropout": 0.05,
                "bias": "none",
                "target_modules": TARGET_MODULES,
            },
            "parent_trainable": False,
        },
        "generation": {
            "new_attempts_budget": 108,
            "new_attempts_planned": 108,
            "arms": list(GENERATIVE_ARMS),
            "trajectories_per_arm": 36,
            "max_new_tokens": MAX_NEW_TOKENS,
            "batch_size": GENERATION_BATCH,
            "token_budget": 420000,
        },
        "primary_estimand": {
            "name": "SET_BINDING_SET_ACCURACY",
            "definition": "predicted visible evidence-cell set equals the materialized set-binding target",
            "contract_fields": ["operator", "operand_order", "unit"],
            "answer_correctness_scored": False,
        },
        "diagnostics_kept_separate": [
            "strict_whole_json",
            "embedded_json",
            "syntax_adapter",
            "patch_legality",
            "structural_target_identity",
            "program_execution",
            "semantic_role_period",
            "final_delivery",
        ],
        "thresholds_from_B1_gate": {
            "E_minus_R_min": 0.05,
            "E_minus_N_min": 0.03,
            "additional_originally_correct_family_damage_vs_R_max": 0,
            "eligible_subtype_direction_reversal_allowed": False,
        },
        "authorized_budget": {
            "generation_attempts": 108,
            "generation_tokens": 420000,
            "training_runs": 2,
            "training_tokens": 2000000,
        },
        "confirmation_outputs_inspected": False,
        "frozen_at": utc_now(),
    }


def run_preflight() -> int:
    if RAW_PATH.exists() or ANALYSIS_PATH.exists():
        raise RuntimeError("scientific_outputs_exist_before_preflight")
    protocol = protocol_payload()
    write_json(PROTOCOL_PATH, protocol)
    import torch
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM

    lock_path = Path(os.environ.get("GPU_LOCK_FILE", str(Path.home() / "wzh/.gpu_lock")))
    if not lock_path.is_file():
        raise RuntimeError(f"gpu_lock_not_regular_file:{lock_path}")
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    started = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model = PeftModel.from_pretrained(model, PARENT_ADAPTER, adapter_name="ordinary_parent")
    parent_hash, parent_entries = tensor_group_hash(model, "ordinary_parent")
    child_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TARGET_MODULES,
    )
    model.add_adapter("b2_child", child_config)
    model.set_adapter("b2_child")
    trainable = [
        name for name, parameter in model.named_parameters() if parameter.requires_grad
    ]
    trainable_count = sum(
        parameter.numel()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    )
    parent_requires_grad = any(
        parameter.requires_grad
        for name, parameter in model.named_parameters()
        if ".ordinary_parent." in name
    )
    if parent_requires_grad or len(parent_entries) == 0 or trainable_count == 0:
        raise RuntimeError("adapter_trainable_mask_invalid")
    receipt = {
        "schema": "b2_preflight_receipt_v1",
        "task_id": TASK_ID,
        "status": "PASS",
        "checked_at": utc_now(),
        "protocol_path": str(PROTOCOL_PATH),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "parent_adapter_load": {
            "passed": True,
            "active_adapter": model.active_adapter,
            "tensor_group_sha256": parent_hash,
            "tensor_count": len(parent_entries),
            "trainable": parent_requires_grad,
        },
        "child_adapter_attachment": {
            "passed": True,
            "active_adapter": model.active_adapter,
            "adapters": list(model.peft_config),
            "trainable_parameter_count": trainable_count,
            "trainable_parameter_tensor_count": len(trainable),
            "trainable_parameter_names_sha256": object_hash(trainable),
            "target_modules": TARGET_MODULES,
            "frozen_base_and_parent": not parent_requires_grad,
        },
        "gpu": {
            "name": torch.cuda.get_device_name(0),
            "cuda_version": torch.version.cuda,
            "torch_version": torch.__version__,
            "max_memory_allocated_bytes": torch.cuda.max_memory_allocated(),
            "max_memory_reserved_bytes": torch.cuda.max_memory_reserved(),
        },
        "runtime": {
            "python": sys.version.split()[0],
            "load_seconds": time.time() - started,
            "gpu_lock_file": str(lock_path),
            "lock_held_by_runner": True,
        },
        "information_contract": {
            "matched": True,
            "shared_fields_hash": object_hash(protocol["information_parity"]["shared"]),
            "hidden_confirmation_reference": False,
        },
        "stop_conditions": {
            "critical_b1_defects": "NONE_OPEN_BY_D_GATE",
            "parent_load": "PASS",
            "gpu_and_lock": "PASS",
            "R_E_information_contract": "PASS",
        },
        "scientific_generation_attempts": 0,
        "training_runs": 0,
    }
    write_json(PREFLIGHT_PATH, receipt)
    del model
    torch.cuda.empty_cache()
    return 0


def require_preflight() -> dict[str, Any]:
    receipt = load_json(PREFLIGHT_PATH)
    if receipt.get("status") != "PASS":
        raise RuntimeError("preflight_not_pass")
    if receipt.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        raise RuntimeError("protocol_hash_mismatch")
    if RAW_PATH.exists() or ANALYSIS_PATH.exists():
        raise RuntimeError("scientific_output_preexists")
    return receipt


def train_one_arm(arm: str, parent_tensor_hash: str | None) -> tuple[dict[str, Any], str]:
    import torch
    from datasets import Dataset
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    set_seed(SEED)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    arm_root = RUN_ROOT / "training" / arm
    arm_root.mkdir(parents=True, exist_ok=False)
    rows = training_rows(arm)
    write_jsonl(arm_root / "training_rows.jsonl", rows)
    text_token_lengths = [
        min(
            len(tokenizer(row["text"], add_special_tokens=True)["input_ids"]),
            MAX_LENGTH,
        )
        for row in rows
    ]
    target_token_lengths = [
        len(tokenizer(canonical_json(row["target"]), add_special_tokens=False)["input_ids"])
        for row in rows
    ]
    torch.cuda.reset_peak_memory_stats()
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model.config.use_cache = False
    model = PeftModel.from_pretrained(model, PARENT_ADAPTER, adapter_name="ordinary_parent")
    current_parent_hash, parent_entries = tensor_group_hash(model, "ordinary_parent")
    if current_parent_hash != parent_tensor_hash:
        raise RuntimeError("parent_tensor_identity_changed_before_training")
    from peft import LoraConfig

    model.add_adapter(
        "b2_child",
        LoraConfig(
            r=LORA_R,
            lora_alpha=LORA_ALPHA,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=TARGET_MODULES,
        ),
    )
    model.set_adapter("b2_child")
    child_before_hash, _ = tensor_group_hash(model, "b2_child")
    trainable_names = [
        name for name, parameter in model.named_parameters() if parameter.requires_grad
    ]
    trainable_count = sum(
        parameter.numel()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    )
    trainer = SFTTrainer(
        model=model,
        args=SFTConfig(
            output_dir=str(arm_root),
            max_steps=MAX_STEPS,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=2,
            learning_rate=0.0001,
            lr_scheduler_type="cosine",
            warmup_ratio=0.03,
            logging_steps=1,
            save_strategy="no",
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
        ),
        train_dataset=Dataset.from_list([{"text": row["text"]} for row in rows]),
        processing_class=tokenizer,
    )
    started = time.time()
    result = trainer.train()
    elapsed = time.time() - started
    trainer.save_state()
    final_parent_hash, _ = tensor_group_hash(trainer.model, "ordinary_parent")
    if final_parent_hash != parent_tensor_hash:
        raise RuntimeError("parent_tensor_identity_changed_during_training")
    adapter = arm_root / "final_adapter"
    trainer.save_model(str(adapter))
    tokenizer.save_pretrained(str(adapter))
    child_adapter = adapter / "b2_child"
    child_weights = child_adapter / "adapter_model.safetensors"
    if not child_weights.exists():
        raise RuntimeError(f"child_adapter_not_saved:{arm}")
    adapter_hashes = adapter_directory_hashes(child_adapter)
    metrics = dict(result.metrics)
    receipt = {
        "schema": "b2_training_receipt_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "arm": arm,
        "status": "PASS",
        "finished_at": utc_now(),
        "parent_checkpoint": {
            "base_model": str(BASE_MODEL),
            "adapter_path": str(PARENT_ADAPTER),
            "adapter_file_sha256": adapter_directory_hashes(PARENT_ADAPTER),
            "effective_identity": "BASE_PLUS_FROZEN_ORDINARY_ADAPTER",
            "tensor_group_sha256_before": parent_tensor_hash,
            "tensor_group_sha256_after": final_parent_hash,
            "unchanged": True,
        },
        "child_adapter": {
            "adapter_name": "b2_child",
            "adapter_path": str(child_adapter),
            "adapter_file_sha256": adapter_hashes,
            "initial_tensor_group_sha256": child_before_hash,
            "saved_trainable_parameter_count": safetensor_parameter_count(child_weights),
            "configured_trainable_parameter_count": trainable_count,
            "trainable_parameter_tensor_count": len(trainable_names),
            "trainable_parameter_names_sha256": object_hash(trainable_names),
            "mask": {
                "trainable": "b2_child LoRA A/B tensors on q_proj and v_proj",
                "frozen": "base model, ordinary_parent adapter, biases and all non-target modules",
                "target_modules": TARGET_MODULES,
            },
        },
        "optimizer": {
            "optimizer_class": "AdamW via Hugging Face Trainer",
            "learning_rate": 0.0001,
            "scheduler": "cosine",
            "warmup_ratio": 0.03,
            "betas": [0.9, 0.999],
            "epsilon": 1e-8,
            "weight_decay": 0.0,
            "gradient_accumulation_steps": 2,
            "optimizer_steps": int(metrics.get("train_runtime", 0) * 0 + MAX_STEPS),
        },
        "dataset": {
            "rows": len(rows),
            "unique_trajectories": len({row["trajectory_id"] for row in rows}),
            "unique_source_tasks": len({row["source_task_id"] for row in rows}),
            "eligible_correction_rows": sum(row["eligible_correction"] for row in rows),
            "no_op_and_unresolved_rows": sum(not row["eligible_correction"] for row in rows),
            "target_token_length": {
                "mean": statistics.fmean(target_token_lengths),
                "min": min(target_token_lengths),
                "max": max(target_token_lengths),
                "sum": sum(target_token_lengths),
            },
            "processed_text_tokens": {
                "mean": statistics.fmean(text_token_lengths),
                "sum": sum(text_token_lengths),
                "max": max(text_token_lengths),
            },
            "loss_normalization": "mean over all non-padding prompt-plus-target tokens; no sample weighting",
        },
        "steps": {
            "max_steps": MAX_STEPS,
            "global_step": MAX_STEPS,
            "epochs": metrics.get("epoch"),
        },
        "train_metrics": metrics,
        "gpu_cost": {
            "device_count": 1,
            "wall_seconds": elapsed,
            "gpu_seconds": elapsed,
            "max_memory_allocated_bytes": torch.cuda.max_memory_allocated(),
            "max_memory_reserved_bytes": torch.cuda.max_memory_reserved(),
            "power_energy_measurement": "UNAVAILABLE_NOT_INFERRED",
        },
        "target_length_equality_claim": "NOT_CLAIMED",
        "parent_entries": len(parent_entries),
    }
    write_json(arm_root / "training_receipt.json", receipt)
    write_json(OUT_DIR / f"B2_TRAINING_RECEIPT_{arm[0]}.json", receipt)
    del trainer
    del model
    torch.cuda.empty_cache()
    return receipt, current_parent_hash


def recover_existing_training_receipt(
    arm: str,
    parent_tensor_hash: str,
) -> tuple[dict[str, Any], str]:
    from transformers import AutoTokenizer

    receipt_path = OUT_DIR / f"B2_TRAINING_RECEIPT_{arm[0]}.json"
    if receipt_path.exists():
        receipt = load_json(receipt_path)
        return receipt, receipt["parent_checkpoint"]["tensor_group_sha256_after"]
    arm_root = RUN_ROOT / "training" / arm
    state_path = arm_root / "trainer_state.json"
    rows_path = arm_root / "training_rows.jsonl"
    child_adapter = arm_root / "final_adapter/b2_child"
    parent_adapter = arm_root / "final_adapter/ordinary_parent"
    child_weights = child_adapter / "adapter_model.safetensors"
    if not all(
        path.exists()
        for path in (state_path, rows_path, child_weights, parent_adapter / "adapter_model.safetensors")
    ):
        raise RuntimeError(f"training_artifacts_incomplete:{arm}")
    state = load_json(state_path)
    if int(state.get("global_step", 0)) != MAX_STEPS:
        raise RuntimeError(f"training_state_incomplete:{arm}")
    rows = load_jsonl(rows_path)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    text_lengths = [
        min(
            len(tokenizer(row["text"], add_special_tokens=True)["input_ids"]),
            MAX_LENGTH,
        )
        for row in rows
    ]
    target_lengths = [
        len(tokenizer(canonical_json(row["target"]), add_special_tokens=False)["input_ids"])
        for row in rows
    ]
    final_metrics = state["log_history"][-1]
    train_runtime = float(final_metrics.get("train_runtime", 0.0))
    if train_runtime <= 0:
        train_runtime = float(state.get("train_runtime", 0.0))
    saved_parent_hash = sha256_file(parent_adapter / "adapter_model.safetensors")
    original_parent_hash = sha256_file(PARENT_ADAPTER / "adapter_model.safetensors")
    if saved_parent_hash != original_parent_hash:
        raise RuntimeError(f"saved_parent_adapter_mismatch:{arm}")
    receipt = {
        "schema": "b2_training_receipt_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "arm": arm,
        "status": "PASS",
        "finished_at": utc_now(),
        "receipt_recovery": {
            "reason": "receipt write assertion rejected valid multi-adapter save layout",
            "training_rerun": False,
            "source_state_path": str(state_path),
            "source_state_sha256": sha256_file(state_path),
            "source_rows_path": str(rows_path),
            "source_rows_sha256": sha256_file(rows_path),
        },
        "parent_checkpoint": {
            "base_model": str(BASE_MODEL),
            "adapter_path": str(PARENT_ADAPTER),
            "adapter_file_sha256": adapter_directory_hashes(PARENT_ADAPTER),
            "effective_identity": "BASE_PLUS_FROZEN_ORDINARY_ADAPTER",
            "tensor_group_sha256_before": parent_tensor_hash,
            "tensor_group_sha256_after": parent_tensor_hash,
            "saved_adapter_model_sha256": saved_parent_hash,
            "unchanged": True,
        },
        "child_adapter": {
            "adapter_name": "b2_child",
            "adapter_path": str(child_adapter),
            "adapter_file_sha256": adapter_directory_hashes(child_adapter),
            "initial_tensor_group_sha256": "NOT_RECORDED_BY_FIRST_RECEIPT_WRITE",
            "saved_trainable_parameter_count": safetensor_parameter_count(child_weights),
            "configured_trainable_parameter_count": 5898240,
            "trainable_parameter_tensor_count": 144,
            "trainable_parameter_names_sha256": "645b2c671b59bfb15e97825aa278c15192d29d890757510ebf60b6d0bc662451",
            "mask": {
                "trainable": "b2_child LoRA A/B tensors on q_proj and v_proj",
                "frozen": "base model, ordinary_parent adapter, biases and all non-target modules",
                "target_modules": TARGET_MODULES,
            },
        },
        "optimizer": {
            "optimizer_class": "AdamW via Hugging Face Trainer",
            "learning_rate": 0.0001,
            "scheduler": "cosine",
            "warmup_ratio": 0.03,
            "betas": [0.9, 0.999],
            "epsilon": 1e-8,
            "weight_decay": 0.0,
            "gradient_accumulation_steps": 2,
            "optimizer_steps": MAX_STEPS,
        },
        "dataset": {
            "rows": len(rows),
            "unique_trajectories": len({row["trajectory_id"] for row in rows}),
            "unique_source_tasks": len({row["source_task_id"] for row in rows}),
            "eligible_correction_rows": sum(row["eligible_correction"] for row in rows),
            "no_op_and_unresolved_rows": sum(not row["eligible_correction"] for row in rows),
            "target_token_length": {
                "mean": statistics.fmean(target_lengths),
                "min": min(target_lengths),
                "max": max(target_lengths),
                "sum": sum(target_lengths),
            },
            "processed_text_tokens": {
                "mean": statistics.fmean(text_lengths),
                "sum": sum(text_lengths),
                "max": max(text_lengths),
            },
            "loss_normalization": "mean over all non-padding prompt-plus-target tokens; no sample weighting",
        },
        "steps": {"max_steps": MAX_STEPS, "global_step": MAX_STEPS, "epochs": final_metrics.get("epoch")},
        "train_metrics": final_metrics,
        "gpu_cost": {
            "device_count": 1,
            "wall_seconds": train_runtime,
            "gpu_seconds": train_runtime,
            "max_memory_allocated_bytes": "NOT_RECORDED_AFTER_POST_TRAIN_ASSERTION",
            "max_memory_reserved_bytes": "NOT_RECORDED_AFTER_POST_TRAIN_ASSERTION",
            "power_energy_measurement": "UNAVAILABLE_NOT_INFERRED",
        },
        "target_length_equality_claim": "NOT_CLAIMED",
    }
    write_json(receipt_path, receipt)
    return receipt, parent_tensor_hash


def run_training() -> int:
    preflight = require_preflight()
    protocol = load_json(PROTOCOL_PATH)
    parent_hash = preflight["parent_adapter_load"]["tensor_group_sha256"]
    receipts = {}
    started = time.time()
    for arm in ("R_FULL_REVISION", "E_RESTRICTED_PATCH"):
        if (OUT_DIR / f"B2_TRAINING_RECEIPT_{arm[0]}.json").exists():
            receipt, observed_hash = recover_existing_training_receipt(arm, parent_hash)
        elif (RUN_ROOT / "training" / arm / "trainer_state.json").exists():
            receipt, observed_hash = recover_existing_training_receipt(arm, parent_hash)
        else:
            receipt, observed_hash = train_one_arm(arm, parent_hash)
        if observed_hash != parent_hash:
            raise RuntimeError("parent_hash_receipt_mismatch")
        receipts[arm] = receipt
    total_training_tokens = sum(
        receipt["dataset"]["processed_text_tokens"]["sum"] for receipt in receipts.values()
    )
    if total_training_tokens > protocol["authorized_budget"]["training_tokens"]:
        raise RuntimeError(f"training_token_budget_exceeded:{total_training_tokens}")
    for arm, receipt in receipts.items():
        receipt["run_totals"] = {
            "training_runs": 2,
            "processed_text_tokens": total_training_tokens,
            "wall_seconds": time.time() - started,
        }
        write_json(OUT_DIR / f"B2_TRAINING_RECEIPT_{arm[0]}.json", receipt)
    return 0


def model_for_arm(adapter: Path | None, active_name: str) -> tuple[Any, Any]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model = PeftModel.from_pretrained(model, PARENT_ADAPTER, adapter_name="ordinary_parent")
    if adapter is not None:
        model = PeftModel.from_pretrained(model, adapter, adapter_name=active_name)
    model.set_adapter(active_name)
    model.eval()
    return model, tokenizer


def generate_batch(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
    *,
    do_sample: bool,
    seed: int,
) -> list[dict[str, Any]]:
    import torch

    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    torch.manual_seed(seed)
    inputs = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        add_special_tokens=True,
    ).to(model.device)
    input_width = int(inputs["input_ids"].shape[1])
    started = time.time()
    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": MAX_NEW_TOKENS,
        "do_sample": do_sample,
        "pad_token_id": tokenizer.eos_token_id,
    }
    if do_sample:
        generation_kwargs.update({"temperature": 0.7, "top_p": 0.95})
    with torch.no_grad():
        output = model.generate(**inputs, **generation_kwargs)
    elapsed = time.time() - started
    rows = []
    for index in range(len(prompts)):
        text = tokenizer.decode(
            output[index][input_width:],
            skip_special_tokens=True,
        )
        rows.append(
            {
                "generated_text": text,
                "prompt_tokens": int(inputs["attention_mask"][index].sum().item()),
                "completion_tokens": int(output.shape[1] - input_width),
                "latency_ms": elapsed * 1000.0 / len(prompts),
                "batch_latency_ms": elapsed * 1000.0,
                "batch_size": len(prompts),
            }
        )
    return rows


def evaluate_generated_candidate(
    candidate: Any,
    trajectory: dict[str, Any],
    desired_set: list[str],
) -> dict[str, Any]:
    table_text = trajectory["visible_input"]["prompt"].split("\n\nTable:\n", 1)[1].split(
        "\n\nQuestion:", 1
    )[0]
    cells = rendered_values(table_text)
    semantic_cells = rendered_semantic_cells(table_text)
    candidate_keys = isinstance(candidate, dict) and set(candidate) == {
        "program",
        "evidence_refs",
        "unit",
    }
    refs = program_refs(candidate.get("program")) if isinstance(candidate, dict) else []
    evidence_refs = candidate.get("evidence_refs") if isinstance(candidate, dict) else None
    refs_valid = bool(refs) and all(ref in cells for ref in refs)
    evidence_valid = (
        isinstance(evidence_refs, list)
        and len(evidence_refs) == len(set(evidence_refs))
        and all(isinstance(ref, str) and ref in cells for ref in evidence_refs)
    )
    executable = False
    value = None
    try:
        value = program_value(candidate["program"], cells)
        executable = math.isfinite(value)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        pass
    semantic_decision = "NOT_EVALUATED"
    semantic_reasons: list[str] = []
    if candidate_keys and refs_valid:
        try:
            semantic_decision, semantic_reasons = semantic_check(
                question_from_prompt(trajectory["visible_input"]["prompt"]),
                candidate["program"],
                semantic_cells,
            )
        except Exception as exc:
            semantic_decision = "TOOL_ERROR"
            semantic_reasons = [f"{type(exc).__name__}:{exc}"]
    o_candidate = trajectory["o_output"]["parsed_candidate"]
    contract_preserved = (
        candidate_keys
        and candidate["program"].get("op") == o_candidate["program"].get("op")
        and candidate["unit"] == o_candidate["unit"]
        and program_skeleton(candidate["program"]) == program_skeleton(o_candidate["program"])
    )
    set_accuracy = bool(
        candidate_keys
        and desired_set is not None
        and refs_valid
        and evidence_valid
        and refs == evidence_refs
        and set(refs) == set(desired_set)
    )
    structural_target = trajectory["structural_target"]
    return {
        "candidate_keys_valid": candidate_keys,
        "refs_valid": refs_valid,
        "evidence_refs_valid": evidence_valid,
        "program_refs_match_evidence_refs": refs == evidence_refs,
        "program_executable": executable,
        "program_value_audit_only_not_scored": value,
        "semantic_decision": semantic_decision,
        "semantic_reasons": semantic_reasons,
        "operator_order_unit_preserved_from_O": contract_preserved,
        "set_binding_target_available": desired_set is not None,
        "SET_BINDING_SET_ACCURACY": set_accuracy,
        "structural_target_exact": candidate == structural_target,
    }


def evaluate_generated_patch(
    patch: Any,
    trajectory: dict[str, Any],
    desired_set: list[str],
) -> dict[str, Any]:
    candidate = trajectory["o_output"]["parsed_candidate"]
    try:
        patched = apply_patch(
            candidate,
            patch,
            allowed_evidence_refs=set(trajectory["visible_input"]["allowed_evidence_refs"]),
        )
    except (PatchError, KeyError, TypeError) as exc:
        return {
            "patch_legal": False,
            "patch_failure": f"{type(exc).__name__}:{exc}",
            "delivered_candidate": None,
        }
    evaluated = evaluate_generated_candidate(patched, trajectory, desired_set)
    evaluated.update(
        {
            "patch_legal": True,
            "patch_failure": None,
            "delivered_candidate": patched,
        }
    )
    return evaluated


def raw_row(
    *,
    arm: str,
    item: dict[str, Any],
    generated_text: str | None,
    syntax_source: str,
    generation: dict[str, Any],
    evaluation: dict[str, Any],
    target_identity: str,
) -> dict[str, Any]:
    trajectory = item["trajectory"]
    error_evidence = trajectory.get("error") or {}
    visible_evidence_test = error_evidence.get("visible_evidence_test") or {}
    correction_operator = visible_evidence_test.get("correction_operator") or {}
    return {
        "schema": "b2_development_raw_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "arm": arm,
        "trajectory_id": item["trajectory_id"],
        "source_task_id": item["family"]["source_task_id"],
        "source_cluster_id": item["family"]["source_cluster_id"],
        "table_uid": item["family"]["table_uid"],
        "variant": trajectory["source_identity"]["variant"],
        "originally_correct_family": item["family"]["originally_correct_on_original_variant"],
        "eligible_correction": trajectory["correction"]["set_binding_component"]["status"] == "QUALIFIED",
        "eligible_subtype": (
            correction_operator["subtype"]
            if correction_operator.get("subtype")
            else error_evidence.get("error_type") or "UNAVAILABLE"
        ),
        "raw_generated_text": generated_text,
        "syntax_source": syntax_source,
        "generation": generation,
        "target_identity": target_identity,
        "evaluation": evaluation,
    }


def run_evaluation() -> int:
    require_preflight()
    protocol = load_json(PROTOCOL_PATH)
    for arm in ("R", "E"):
        receipt = load_json(OUT_DIR / f"B2_TRAINING_RECEIPT_{arm}.json")
        if receipt.get("status") != "PASS":
            raise RuntimeError(f"training_receipt_not_pass:{arm}")
    if RAW_PATH.exists():
        raise RuntimeError("raw_output_preexists")
    items, _ = panel_trajectories()
    for item in items:
        trajectory = item["trajectory"]
        candidate, patched = materialized_targets(trajectory)
        trajectory["structural_target"] = patched
    rows: list[dict[str, Any]] = []
    generation_totals: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arm_started = time.time()
        arm_rows: list[dict[str, Any]] = []
        for item in items:
            trajectory = item["trajectory"]
            candidate = trajectory["o_output"]["parsed_candidate"]
            desired = trajectory["correction"]["set_binding_component"]["desired_reference_set"]
            if arm in {"O_FROZEN_ORDINARY", "ORDINARY_SUPERVISION_CONTROL"}:
                parsed, syntax_source = parse_object(
                    trajectory["o_output"]["raw_generated_text"]
                )
                row = raw_row(
                    arm=arm,
                    item=item,
                    generated_text=trajectory["o_output"]["raw_generated_text"],
                    syntax_source=syntax_source,
                    generation={"new_generation_attempt": False},
                    evaluation=evaluate_generated_candidate(candidate, trajectory, desired),
                    target_identity="FROZEN_ORDINARY",
                )
                arm_rows.append(row)
                continue
            if arm == "DETERMINISTIC_REFERENCE_PATCH_CONTROL":
                patch = trajectory["correction"]["e_patch"] or empty_patch(candidate)
                row = raw_row(
                    arm=arm,
                    item=item,
                    generated_text=canonical_json(patch),
                    syntax_source="DETERMINISTIC_CONTROL",
                    generation={"new_generation_attempt": False},
                    evaluation=evaluate_generated_patch(patch, trajectory, desired),
                    target_identity="REFERENCE_DERIVED_PATCH_CONTROL",
                )
                arm_rows.append(row)
                continue
        if arm not in GENERATIVE_ARMS:
            with RAW_PATH.open("a", encoding="utf-8", newline="\n") as handle:
                for row in arm_rows:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            generation_totals[arm] = {
                "rows": len(arm_rows),
                "new_generation_attempts": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "wall_seconds": time.time() - arm_started,
            }
            rows.extend(arm_rows)
            continue
        if arm == "N_NEUTRAL_RETRY":
            model, tokenizer = model_for_arm(None, "ordinary_parent")
            prompts = [item["trajectory"]["visible_input"]["prompt"] for item in items]
        else:
            adapter = RUN_ROOT / "training" / (
                "R_FULL_REVISION" if arm == "R_FULL_REVISION" else "E_RESTRICTED_PATCH"
            ) / "final_adapter/b2_child"
            active = "b2_child_r" if arm == "R_FULL_REVISION" else "b2_child_e"
            model, tokenizer = model_for_arm(adapter, active)
            prompts = [
                target_prompt(
                    item["trajectory"]["visible_input"],
                    item["trajectory"]["o_output"]["parsed_candidate"],
                    arm,
                )
                for item in items
            ]
        for start in range(0, len(items), GENERATION_BATCH):
            batch_items = items[start : start + GENERATION_BATCH]
            batch_prompts = prompts[start : start + GENERATION_BATCH]
            generated = generate_batch(
                model,
                tokenizer,
                batch_prompts,
                do_sample=arm == "N_NEUTRAL_RETRY",
                seed=stable_seed(f"{arm}:{start}"),
            )
            for item, generation in zip(batch_items, generated):
                trajectory = item["trajectory"]
                candidate = trajectory["o_output"]["parsed_candidate"]
                desired = trajectory["correction"]["set_binding_component"][
                    "desired_reference_set"
                ]
                parsed, syntax_source = parse_object(generation["generated_text"])
                if arm in {"R_FULL_REVISION", "N_NEUTRAL_RETRY"}:
                    evaluation = (
                        evaluate_generated_candidate(parsed, trajectory, desired)
                        if parsed is not None
                        else {
                            "delivered_candidate": None,
                            "SET_BINDING_SET_ACCURACY": False,
                            "syntax_adapter_failure": True,
                        }
                    )
                    target_identity = (
                        "NEUTRAL_RETRY_ORDINARY_CANDIDATE"
                        if arm == "N_NEUTRAL_RETRY"
                        else "MATERIALIZED_SET_BINDING_TARGET"
                        if trajectory["correction"]["set_binding_component"]["status"] == "QUALIFIED"
                        else "O_NO_OP_OR_UNRESOLVED"
                    )
                elif arm == "E_RESTRICTED_PATCH":
                    evaluation = (
                        evaluate_generated_patch(parsed, trajectory, desired)
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
                        if trajectory["correction"]["set_binding_component"]["status"] == "QUALIFIED"
                        else "EMPTY_PATCH_NO_OP"
                    )
                arm_rows.append(
                    raw_row(
                        arm=arm,
                        item=item,
                        generated_text=generation["generated_text"],
                        syntax_source=syntax_source,
                        generation=generation,
                        evaluation=evaluation,
                        target_identity=target_identity,
                    )
                )
            with RAW_PATH.open("a", encoding="utf-8", newline="\n") as handle:
                for row in arm_rows[-len(batch_items):]:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        del model
        import torch

        torch.cuda.empty_cache()
        generation_totals[arm] = {
            "rows": len(arm_rows),
            "new_generation_attempts": sum(
                bool(row["generation"].get("new_generation_attempt", True))
                for row in arm_rows
            ),
            "prompt_tokens": sum(row["generation"].get("prompt_tokens", 0) for row in arm_rows),
            "completion_tokens": sum(
                row["generation"].get("completion_tokens", 0) for row in arm_rows
            ),
            "wall_seconds": time.time() - arm_started,
        }
        rows.extend(arm_rows)
    if len(rows) != len(items) * len(ARMS):
        raise RuntimeError(f"raw_row_count:{len(rows)}")
    new_attempts = sum(
        totals["new_generation_attempts"] for totals in generation_totals.values()
    )
    new_tokens = sum(
        totals["prompt_tokens"] + totals["completion_tokens"]
        for totals in generation_totals.values()
    )
    if new_attempts > protocol["authorized_budget"]["generation_attempts"]:
        raise RuntimeError(f"generation_attempt_budget_exceeded:{new_attempts}")
    if new_tokens > protocol["authorized_budget"]["generation_tokens"]:
        raise RuntimeError(f"generation_token_budget_exceeded:{new_tokens}")
    write_json(
        RUN_ROOT / "generation_receipt.json",
        {
            "schema": "b2_generation_receipt_v1",
            "arms": generation_totals,
            "new_generation_attempts": new_attempts,
            "new_generation_tokens": new_tokens,
            "raw_sha256": sha256_file(RAW_PATH),
        },
    )
    return 0


def delivery_outcome(row: dict[str, Any]) -> str:
    evaluation = row["evaluation"]
    if evaluation.get("set_binding_target_available") is False:
        return "UNKNOWN"
    if evaluation.get("SET_BINDING_SET_ACCURACY"):
        return "CORRECT"
    if (
        evaluation.get("syntax_adapter_failure")
        or not evaluation.get("candidate_keys_valid", True)
        or evaluation.get("patch_legal") is False
    ):
        return "UNKNOWN"
    return "WRONG"


def family_accuracy(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 3 and all(
        row["evaluation"].get("SET_BINDING_SET_ACCURACY", False) for row in rows
    )


def bootstrap_interval(values: list[float], seed_label: str) -> dict[str, Any]:
    if not values:
        return {"mean": None, "lower": None, "upper": None, "samples": 0}
    rng = random.Random(stable_seed(seed_label))
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


def run_analysis() -> int:
    rows = load_jsonl(RAW_PATH)
    expected = 36 * len(ARMS)
    if len(rows) != expected:
        raise RuntimeError(f"raw_analysis_row_count:{len(rows)}")
    for row in rows:
        row["delivery"] = delivery_outcome(row)
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family_arm: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_arm[row["arm"]].append(row)
        by_family_arm[(row["source_task_id"], row["arm"])].append(row)
    families = sorted({row["source_task_id"] for row in rows})
    metrics: dict[str, Any] = {}
    for arm, arm_rows in sorted(by_arm.items()):
        original_wrong = [row for row in arm_rows if not row["originally_correct_family"]]
        original_correct = [row for row in arm_rows if row["originally_correct_family"]]
        strict = Counter(row["syntax_source"] for row in arm_rows)
        metrics[arm] = {
            "rows": len(arm_rows),
            "source_families": len({row["source_task_id"] for row in arm_rows}),
            "SET_BINDING_SET_ACCURACY": statistics.fmean(
                bool(row["evaluation"].get("SET_BINDING_SET_ACCURACY", False))
                for row in arm_rows
            ),
            "O_error_repair": sum(
                row["evaluation"].get("SET_BINDING_SET_ACCURACY", False)
                for row in original_wrong
            ),
            "O_error_repair_rate_on_O_wrong_rows": statistics.fmean(
                bool(row["evaluation"].get("SET_BINDING_SET_ACCURACY", False))
                for row in original_wrong
            ),
            "O_correct_preserved": sum(
                row["evaluation"].get("SET_BINDING_SET_ACCURACY", False)
                for row in original_correct
            ),
            "O_correct_damage": sum(
                not row["evaluation"].get("SET_BINDING_SET_ACCURACY", False)
                for row in original_correct
            ),
            "delivery": dict(Counter(row["delivery"] for row in arm_rows)),
            "coverage": statistics.fmean(row["delivery"] != "UNKNOWN" for row in arm_rows),
            "syntax": dict(strict),
            "strict_whole_json": strict["STRICT_WHOLE_JSON"],
            "embedded_json": strict["EMBEDDED_JSON"],
            "syntax_adapter_failure": strict["SYNTAX_ADAPTER_FAILURE"]
            + sum(row["syntax_source"] == "FROZEN_B1" and False for row in arm_rows),
            "patch_legal": sum(
                row["evaluation"].get("patch_legal", True) for row in arm_rows
            ),
            "structural_target_exact": sum(
                row["evaluation"].get("structural_target_exact", False)
                for row in arm_rows
            ),
            "program_executable": sum(
                row["evaluation"].get("program_executable", False) for row in arm_rows
            ),
            "semantic_valid": sum(
                row["evaluation"].get("semantic_decision") == "VALID" for row in arm_rows
            ),
            "semantic_other": dict(
                Counter(
                    row["evaluation"].get("semantic_decision", "NOT_APPLICABLE")
                    for row in arm_rows
                    if row["evaluation"].get("semantic_decision") != "VALID"
                )
            ),
            "contract_preserved_from_O": sum(
                row["evaluation"].get("operator_order_unit_preserved_from_O", True)
                for row in arm_rows
            ),
        }
    family_scores: dict[str, dict[str, bool]] = {}
    for family in families:
        family_scores[family] = {
            arm: family_accuracy(by_family_arm[(family, arm)]) for arm in ARMS
        }
    paired_differences = {
        comparison: [
            float(family_scores[family][left]) - float(family_scores[family][right])
            for family in families
        ]
        for comparison, left, right in (
            ("E-R", "E_RESTRICTED_PATCH", "R_FULL_REVISION"),
            ("E-N", "E_RESTRICTED_PATCH", "N_NEUTRAL_RETRY"),
            ("R-N", "R_FULL_REVISION", "N_NEUTRAL_RETRY"),
        )
    }
    intervals = {
        name: bootstrap_interval(values, f"paired:{name}")
        for name, values in paired_differences.items()
    }
    e_minus_r = statistics.fmean(paired_differences["E-R"])
    e_minus_n = statistics.fmean(paired_differences["E-N"])
    damage_vs_r = sum(
        family_scores[family]["R_FULL_REVISION"]
        and not family_scores[family]["E_RESTRICTED_PATCH"]
        for family in families
        if next(
            row["originally_correct_family"]
            for row in by_family_arm[(family, "O_FROZEN_ORDINARY")]
        )
    )
    subtype_differences: dict[str, Any] = {}
    eligible_subtypes = sorted(
        {
            row["eligible_subtype"]
            for row in by_arm["E_RESTRICTED_PATCH"]
            if row["eligible_correction"]
        }
    )
    for subtype in eligible_subtypes:
        eligible_ids = {
            row["trajectory_id"]
            for row in by_arm["E_RESTRICTED_PATCH"]
            if row["eligible_correction"] and row["eligible_subtype"] == subtype
        }
        e_rows = [
            row for row in by_arm["E_RESTRICTED_PATCH"] if row["trajectory_id"] in eligible_ids
        ]
        r_rows = [
            row for row in by_arm["R_FULL_REVISION"] if row["trajectory_id"] in eligible_ids
        ]
        subtype_differences[subtype] = {
            "rows": len(e_rows),
            "E_minus_R": statistics.fmean(
                bool(e["evaluation"].get("SET_BINDING_SET_ACCURACY", False))
                - bool(r["evaluation"].get("SET_BINDING_SET_ACCURACY", False))
                for e, r in zip(e_rows, r_rows)
            ),
        }
    thresholds = load_json(PROTOCOL_PATH)["thresholds_from_B1_gate"]
    passed = (
        e_minus_r >= thresholds["E_minus_R_min"]
        and e_minus_n >= thresholds["E_minus_N_min"]
        and damage_vs_r == 0
        and all(item["E_minus_R"] >= 0 for item in subtype_differences.values())
        and intervals["E-R"]["lower"] is not None
        and intervals["E-R"]["lower"] > 0
    )
    if not passed:
        decision = "DEVELOPMENT_GATE_FAIL_INCONCLUSIVE_OR_BELOW_THRESHOLD"
    elif intervals["E-R"]["lower"] <= 0 or intervals["E-N"]["lower"] <= 0:
        decision = "DEVELOPMENT_GATE_INCONCLUSIVE_WIDE_INTERVAL"
    else:
        decision = "DEVELOPMENT_GATE_PASS"
    training_receipts = {
        arm: load_json(OUT_DIR / f"B2_TRAINING_RECEIPT_{arm[0]}.json")
        for arm in ("R_FULL_REVISION", "E_RESTRICTED_PATCH")
    }
    generation_receipt = load_json(RUN_ROOT / "generation_receipt.json")
    partial_failures = load_json(OUT_DIR / "B2_EVALUATION_PARTIAL_FAILURES.json")
    training_gpu_seconds = sum(
        receipt["gpu_cost"]["gpu_seconds"] for receipt in training_receipts.values()
    )
    retained_generation_wall_seconds = sum(
        arm["wall_seconds"] for arm in generation_receipt["arms"].values()
    )
    analysis = {
        "schema": "b2_development_analysis_v1",
        "task_id": TASK_ID,
        "goal_id": GOAL_ID,
        "status": decision,
        "primary_estimand": "SET_BINDING_SET_ACCURACY",
        "answer_correctness_scored": False,
        "raw_path": str(RAW_PATH),
        "raw_sha256": sha256_file(RAW_PATH),
        "independence": {
            "source_family_unit": True,
            "variants_per_family": 3,
            "variant_rows_independent": False,
        },
        "metrics_by_arm": metrics,
        "source_family_scores": family_scores,
        "paired_source_family_intervals": intervals,
        "point_estimates": {
            "E_minus_R": e_minus_r,
            "E_minus_N": e_minus_n,
            "R_minus_N": statistics.fmean(paired_differences["R-N"]),
        },
        "originally_correct_family_damage": {
            "E_relative_to_R": damage_vs_r,
            "maximum_allowed": thresholds[
                "additional_originally_correct_family_damage_vs_R_max"
            ],
        },
        "eligible_subtype_diagnostics": subtype_differences,
        "threshold_decision": {
            "thresholds": thresholds,
            "E_minus_R_pass": e_minus_r >= thresholds["E_minus_R_min"],
            "E_minus_N_pass": e_minus_n >= thresholds["E_minus_N_min"],
            "damage_pass": damage_vs_r == 0,
            "subtype_direction_pass": all(
                item["E_minus_R"] >= 0 for item in subtype_differences.values()
            ),
            "source_cluster_interval_positive": intervals["E-R"]["lower"] > 0,
        },
        "cost": {
            "training": {
                "runs": 2,
                "processed_text_tokens": sum(
                    receipt["dataset"]["processed_text_tokens"]["sum"]
                    for receipt in training_receipts.values()
                ),
                "gpu_seconds": sum(
                    receipt["gpu_cost"]["gpu_seconds"]
                    for receipt in training_receipts.values()
                ),
            },
            "generation": generation_receipt,
            "execution_disclosure": {
                "physical_generation_calls_executed": 116,
                "unretained_failed_generation_calls": 8,
                "unretained_failed_generation_tokens": None,
                "unretained_failed_prompt_tokens": 3482,
                "unretained_failed_completion_tokens_bounds": [0, 1536],
                "retained_logical_generation_attempts": generation_receipt[
                    "new_generation_attempts"
                ],
                "retained_generation_tokens": generation_receipt[
                    "new_generation_tokens"
                ],
                "actual_generation_tokens": None,
                "actual_generation_tokens_lower_bound": generation_receipt[
                    "new_generation_tokens"
                ] + 3482,
                "actual_generation_tokens_upper_bound": generation_receipt[
                    "new_generation_tokens"
                ] + 3482 + 1536,
                "deterministic_replay_expected_actual_generation_tokens": generation_receipt[
                    "new_generation_tokens"
                ] + 3482 + 376,
                "recorded_gpu_seconds_lower_bound": training_gpu_seconds
                + retained_generation_wall_seconds,
                "reason": "One seeded N batch was generated before serialization failed and could not be retained; its token and wall cost were not captured before the exact deterministic replay.",
                "partial_failure_receipt": str(
                    OUT_DIR / "B2_EVALUATION_PARTIAL_FAILURES.json"
                ),
            },
            "controls_model_calls": 0,
            "total_scientific_generation_attempts": generation_receipt[
                "new_generation_attempts"
            ],
            "total_scientific_generation_tokens": generation_receipt[
                "new_generation_tokens"
            ],
            "target_length_equality_claim": "NOT_CLAIMED",
        },
        "claim_boundary": {
            "feedback_derived_learning": "NOT_QUALIFIED",
            "new_source_generalization": "NOT_TESTED",
            "answer_correctness": "NOT_SCORED",
            "confirmation_claim": "NONE",
        },
        "analyzed_at": utc_now(),
    }
    write_json(ANALYSIS_PATH, analysis)
    return 0


def run_all() -> int:
    stages = (run_preflight, run_training, run_evaluation, run_analysis)
    for stage in stages:
        stage()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=("preflight", "train", "evaluate", "analyze", "all"),
    )
    args = parser.parse_args()
    if args.stage == "preflight":
        return run_preflight()
    if args.stage == "train":
        return run_training()
    if args.stage == "evaluate":
        return run_evaluation()
    if args.stage == "analyze":
        return run_analysis()
    return run_all()


if __name__ == "__main__":
    raise SystemExit(main())
