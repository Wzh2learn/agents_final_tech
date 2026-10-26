"""Hash-bound constants for the remediation P2 execution chain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


TASK_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = TASK_ROOT.parents[1]
RAW_ROOT = Path(__file__).resolve().parent
RECEIPTS_ROOT = TASK_ROOT / "p2_proxy_calibration" / "receipts"
RUNS_ROOT = RAW_ROOT / "runs"

DEFAULT_SELECTION = RECEIPTS_ROOT / "P2_SELECTION_RECEIPT.json"
DEFAULT_REFERENCE = RECEIPTS_ROOT / "P2_REFERENCE_CHAIN.json"
DEFAULT_ROW_RESULTS = (
    REPOSITORY_ROOT
    / "research"
    / "natural_error_evidence_cost_20261026_v1"
    / "a_closeout"
    / "P2_RECOVERY_RECOMPUTE_FINAL.json"
)
DEFAULT_QUALIFICATION = (
    REPOSITORY_ROOT
    / "research"
    / "natural_error_evidence_cost_20261026_v1"
    / "a_prepare"
    / "P2_TASK_QUALIFICATION.json"
)
DEFAULT_RAW_DEV = Path(
    "/home/testuser/wzh/projects/agents_final_tech/data/research/"
    "tatqa_raw_2026/tatqa_dataset_dev.json"
)
MODEL_PATH = Path("/home/testuser/wzh/models/hf/Qwen3-4B")

SOURCE_SHA256 = {
    "row_results": "efe134217e0629ec90b72ba302998d5b43756a9f46ff125fd2f2e09c01f7c9de",
    "raw_dev": "8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5",
    "qualification": "d3b3ee96f8edff54205b7ff1eca28d7e48da85e7449e1d15a425d6ab3f664451",
}

ARMS = {
    "table_top3": 3,
    "table_top5": 5,
    "table_all": None,
}

PROMPT_TEMPLATE = """You are answering a financial question from visible evidence only.
Use only the question and evidence below. Do not infer hidden labels or reference answers.
If the visible evidence is insufficient, set unknown to true and answer UNKNOWN.

Return exactly one JSON object with these keys and no extra text:
answer, numeric_value, unit, evidence_refs, unknown, clarification
Rules:
- answer is a string or array of strings.
- numeric_value is a JSON number when a numeric answer is applicable; otherwise null.
- unit is a visible unit or UNKNOWN.
- evidence_refs is an array of visible evidence references such as TABLE:C1 or P1.
- unknown is true or false.
- clarification is an empty string unless it briefly explains an UNKNOWN.

Question:
{question}

Visible evidence:
{context}
"""

PROMPT_TEMPLATE_SHA256 = hashlib.sha256(
    PROMPT_TEMPLATE.encode("utf-8")
).hexdigest()

MODEL_DECODE_SPEC = {
    "dtype": "bfloat16",
    "device": "cuda",
    "do_sample": False,
    "temperature": None,
    "top_p": None,
    "top_k": None,
    "max_new_tokens": 160,
    "use_cache": True,
    "calculator": "safe_decimal_numeric_value_only_v1",
}

MAX_GENERATION_CALLS = 48
MAX_GENERATION_TOKENS = 240_000
PRIMARY_CALLS = 36
MAX_RETRY_CALLS = 12


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_call_id(question_uid: str, arm: str, attempt: int) -> str:
    payload = f"p2-remediation-v1:{question_uid}:{arm}:{attempt}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]

