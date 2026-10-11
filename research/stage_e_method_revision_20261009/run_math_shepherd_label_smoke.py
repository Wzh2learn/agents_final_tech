#!/usr/bin/env python3
"""Tiny Math-Shepherd-style rollout-label construction smoke on PRM800K prefixes."""
from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "research/math_shepherd_label_smoke_20261010"
DATA = ROOT / "research/stage_e_method_revision_20261009/sources/prm800k/phase2_test.jsonl"
MODEL_PATH = Path("/home/testuser/wzh/models/hf/Qwen3-4B")
VENDOR = Path("/home/testuser/wzh/external_stage_d_repro/vendor")
PRM_REPO = Path("/home/testuser/wzh/external_stage_d_repro/repos/prm800k")

SEED = 20261014
ROWS = 4
CONTINUATIONS = 4
STEP_INDEX = 1
MAX_NEW_TOKENS = 160
TEMPERATURE = 0.7
TOP_P = 0.95
FINAL_ANSWER_RE = re.compile(r"final answer\s*:\s*(.+)", re.IGNORECASE)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_grader():
    sys.path.insert(0, str(VENDOR))
    sys.path.insert(0, str(PRM_REPO))
    sys.path.insert(0, str(PRM_REPO / "prm800k"))
    return importlib.import_module("grading.grader")


def selected_ratings(label: dict[str, Any]) -> list[int | None]:
    ratings = []
    for step in label["steps"]:
        chosen = step.get("chosen_completion")
        if isinstance(chosen, int) and 0 <= chosen < len(step.get("completions", [])):
            ratings.append(step["completions"][chosen].get("rating"))
        else:
            ratings.append(None)
    return ratings


def extract_answer(text: str) -> str | None:
    matches = FINAL_ANSWER_RE.findall(text)
    if not matches:
        return None
    answer = matches[-1].strip()
    answer = re.sub(r"^[:\s]+", "", answer)
    answer = answer.replace("$", "").strip()
    boxed = re.search(r"\\boxed\{([^{}]+)\}", answer)
    if boxed:
        answer = boxed.group(1).strip()
    answer = re.split(r"[\n\r]", answer)[0].strip().rstrip(".")
    return answer or None


def build_prompt(problem: str, steps: list[str], prefix_count: int) -> str:
    prefix = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(steps[:prefix_count]))
    return (
        "Continue the mathematical solution from the next step. "
        "Do not repeat earlier steps. End with a single line in the exact form "
        "`Final answer: <answer>`.\n\n"
        f"Problem:\n{problem}\n\n"
        f"Partial solution:\n{prefix}\n\n"
        "Next step:"
    )


def main() -> int:
    if TASK.exists():
        raise RuntimeError(f"output directory already exists: {TASK}")
    TASK.mkdir(parents=True, exist_ok=False)
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    grader = load_grader()
    eligible = []
    seen_problem = set()
    for index, row in enumerate(rows):
        problem = str(row["question"].get("problem") or "")
        problem_hash = sha256_text(problem)
        pre_steps = row["question"].get("pre_generated_steps") or []
        ratings = selected_ratings(row["label"])
        if len(pre_steps) <= STEP_INDEX or len(ratings) <= STEP_INDEX:
            continue
        if any(rating is None for rating in ratings):
            continue
        if problem_hash in seen_problem:
            continue
        seen_problem.add(problem_hash)
        eligible.append({
            "row_index": index,
            "row_sha256": sha256_text(json.dumps(row, ensure_ascii=False, sort_keys=True)),
            "problem_hash": problem_hash,
            "problem": problem,
            "pre_steps": pre_steps,
            "ratings": ratings,
            "gold_answer": row["question"].get("ground_truth_answer"),
        })
    eligible.sort(key=lambda item: sha256_text(f"{SEED}:{item['problem_hash']}"))
    selected = eligible[:ROWS]
    if len(selected) != ROWS:
        raise RuntimeError(f"need {ROWS} eligible rows, found {len(selected)}")

    config = {
        "namespace": "MATH_SHEPHERD_STYLE_LABEL_CONSTRUCTION_SMOKE",
        "status": "REFERENCE_LABEL_CONSTRUCTION_SMOKE_NOT_PAPER_RESULT",
        "formal_training": False,
        "model_calls": ROWS * CONTINUATIONS,
        "seed": SEED,
        "rows": ROWS,
        "continuations_per_prefix": CONTINUATIONS,
        "step_index": STEP_INDEX,
        "max_new_tokens": MAX_NEW_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "data_path": str(DATA),
        "data_sha256": sha256_file(DATA),
        "model_path": str(MODEL_PATH),
        "model_config_sha256": sha256_file(MODEL_PATH / "config.json"),
        "selected_problem_hashes": [item["problem_hash"] for item in selected],
        "selected_row_hashes": [item["row_sha256"] for item in selected],
        "label_rules": {
            "hard": "1 if at least one sampled continuation has a parseable final answer graded correct, else 0",
            "soft": "correct parsed continuations / 4",
            "no_final_answer": "counted incorrect and reported separately",
            "gold_dependence": "ground_truth_answer is required",
            "human_comparison": "selected PRM rating at the same zero-based step index",
        },
        "licence": {
            "data": "LICENCE_PENDING_NONCOMMERCIAL_ACADEMIC_SMOKE_ONLY",
            "model": "Qwen model licence recorded separately; local non-commercial smoke only",
        },
    }
    (TASK / "smoke_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model.eval()

    records = []
    for row_position, item in enumerate(selected):
        prompt = build_prompt(item["problem"], item["pre_steps"], STEP_INDEX + 1)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        continuations = []
        for continuation_index in range(CONTINUATIONS):
            generation_seed = SEED + row_position * 100 + continuation_index
            torch.manual_seed(generation_seed)
            torch.cuda.manual_seed_all(generation_seed)
            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    do_sample=True,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    pad_token_id=tokenizer.eos_token_id,
                )
            text = tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            answer = extract_answer(text)
            correct = bool(answer is not None and grader.grade_answer(answer, str(item["gold_answer"])))
            continuations.append({
                "continuation_index": continuation_index,
                "seed": generation_seed,
                "generated_text": text,
                "extracted_answer": answer,
                "parseable_final_answer": answer is not None,
                "correct": correct,
            })
        correct_count = sum(continuation["correct"] for continuation in continuations)
        human_rating = item["ratings"][STEP_INDEX]
        records.append({
            "row_index": item["row_index"],
            "row_sha256": item["row_sha256"],
            "problem_hash": item["problem_hash"],
            "step_index": STEP_INDEX,
            "human_selected_rating": human_rating,
            "correct_continuations": correct_count,
            "hard_label": int(correct_count > 0),
            "soft_label": correct_count / CONTINUATIONS,
            "no_final_answer_count": sum(not continuation["parseable_final_answer"] for continuation in continuations),
            "continuations": continuations,
        })

    hard_positive = sum(record["hard_label"] for record in records)
    human_positive = sum(record["human_selected_rating"] > 0 for record in records)
    agreement = sum(record["hard_label"] == int(record["human_selected_rating"] > 0) for record in records)
    metrics = {
        "status": "LABEL_CONSTRUCTION_SMOKE_COMPLETE",
        "records": len(records),
        "continuations": len(records) * CONTINUATIONS,
        "hard_positive": hard_positive,
        "human_positive_at_step": human_positive,
        "hard_human_agreement": agreement,
        "total_soft_label": sum(record["soft_label"] for record in records),
        "total_no_final_answer": sum(record["no_final_answer_count"] for record in records),
        "paper_result": False,
        "claim_boundary": "Qwen3-4B reference smoke only; not Math-Shepherd reproduction and not C4 evidence",
        "records_detail": records,
    }
    (TASK / "smoke_results.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": metrics["status"],
        "records": metrics["records"],
        "continuations": metrics["continuations"],
        "hard_positive": metrics["hard_positive"],
        "human_positive_at_step": metrics["human_positive_at_step"],
        "agreement": metrics["hard_human_agreement"],
        "no_final_answer": metrics["total_no_final_answer"],
        "output": str(TASK / "smoke_results.json"),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
