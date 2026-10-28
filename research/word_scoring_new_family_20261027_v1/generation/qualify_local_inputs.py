"""Qualify frozen prompts with the tokenizer and local artifact manifest."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import torch
import transformers
from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PLANNED_PATH = ROOT / "mechanism" / "PLANNED_PROMPTS.jsonl"
FREEZE_PATH = ROOT / "mechanism" / "MECHANISM_FREEZE.json"
MODEL_PATH = Path("/home/testuser/wzh/models/hf/Qwen3-4B")
RECEIPT_PATH = ROOT / "generation" / "TOKEN_QUALIFICATION.json"
MAX_INPUT = 6000
MAX_NEW_TOKENS = 512
TOKEN_CAP = 240_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    planned = [
        json.loads(line)
        for line in PLANNED_PATH.read_text(encoding="utf-8").splitlines()
        if line
    ]
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    rows = []
    for row in planned:
        token_ids = tokenizer.apply_chat_template(
            row["messages"],
            tokenize=True,
            add_generation_prompt=True,
            return_dict=False,
        )
        rows.append(
            {
                "logical_call_id": row["logical_call_id"],
                "arm": row["arm"],
                "family_id": row["family_id"],
                "question_uid": row["question_uid"],
                "input_tokens": len(token_ids),
                "reservation_upper_bound": len(token_ids) + MAX_NEW_TOKENS,
                "prompt_sha256": row["prompt_sha256"],
            }
        )
    artifact_paths = sorted(
        path
        for path in MODEL_PATH.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )
    artifacts = [
        {
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in artifact_paths
    ]
    max_input = max(row["input_tokens"] for row in rows)
    planned_upper_total = sum(row["reservation_upper_bound"] for row in rows)
    qualified = (
        len(rows) == 24
        and max_input <= MAX_INPUT
        and planned_upper_total <= TOKEN_CAP
        and all(row["prompt_sha256"] == next(
            item["prompt_sha256"]
            for item in planned
            if item["logical_call_id"] == row["logical_call_id"]
        ) for row in rows)
    )
    receipt = {
        "schema": "word_new_family_token_qualification_v1",
        "status": "QUALIFIED_PRE_GENERATION" if qualified else "NOT_QUALIFIED",
        "model_loaded": False,
        "generation_calls": 0,
        "training_runs": 0,
        "python": platform.python_version(),
        "transformers": transformers.__version__,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "model_path": str(MODEL_PATH),
        "model_id": freeze["model"]["id"],
        "upstream_revision": freeze["model"]["upstream_revision"],
        "prior_file_manifest_sha256": freeze["model"]["file_manifest_sha256"],
        "artifacts": artifacts,
        "tokenizer_class": tokenizer.__class__.__name__,
        "tokenizer_vocab_size": len(tokenizer),
        "chat_template_sha256": hashlib.sha256(
            (tokenizer.chat_template or "").encode("utf-8")
        ).hexdigest(),
        "planned_prompt_sha256": freeze["planned_prompts"]["sha256"],
        "planned_calls": len(rows),
        "max_input_tokens": max_input,
        "input_upper_bound_per_attempt": MAX_INPUT,
        "max_new_tokens_per_attempt": MAX_NEW_TOKENS,
        "planned_reservation_upper_bound_total": planned_upper_total,
        "token_cap": TOKEN_CAP,
        "rows": rows,
        "source_hashes": {
            str(PLANNED_PATH.relative_to(REPO)): sha256(PLANNED_PATH),
            str(FREEZE_PATH.relative_to(REPO)): sha256(FREEZE_PATH),
        },
    }
    RECEIPT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "planned_calls": len(rows),
                "max_input_tokens": max_input,
                "planned_upper_total": planned_upper_total,
                "model_loaded": False,
            },
            sort_keys=True,
        )
    )
    return 0 if qualified else 1


if __name__ == "__main__":
    raise SystemExit(main())
