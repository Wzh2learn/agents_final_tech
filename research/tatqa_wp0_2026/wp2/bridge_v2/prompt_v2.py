from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path(__file__).with_name("BRIDGE_SCHEMAS_v2.json")
SYSTEM_INSTRUCTION = "Return exactly one JSON object; no prose, no code fences"
STAGES = frozenset({"plan", "consume"})
PLAN_EXAMPLE = {
    "tool": "calc",
    "params": {"expression": "12 - 4"},
}
CONSUME_EXAMPLE = {
    "row": "Revenue",
    "periods": ["2019", "2018"],
    "delta_source": 8,
    "delta_target": 8,
    "unit": "unit",
}


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _example(stage: str) -> dict[str, Any]:
    if stage == "plan":
        return PLAN_EXAMPLE
    if stage == "consume":
        return CONSUME_EXAMPLE
    raise ValueError(f"unsupported stage: {stage}")


def build_messages(stage: str, task_prompt: str) -> list[dict[str, str]]:
    if stage not in STAGES:
        raise ValueError(f"unsupported stage: {stage}")
    if not isinstance(task_prompt, str) or not task_prompt:
        raise ValueError("task prompt must be a non-empty string")
    example = json.dumps(
        _example(stage),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    user = (
        f"{task_prompt}\n"
        "LOCKED_EXAMPLE="
        f"{example}\n"
        "Return the requested stage output now."
    )
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": user},
    ]


def render_chat_prompt(
    tokenizer: Any,
    stage: str,
    task_prompt: str,
) -> str:
    return str(
        tokenizer.apply_chat_template(
            build_messages(stage, task_prompt),
            tokenize=False,
            add_generation_prompt=True,
        )
    )


def _template_sha256(stage: str) -> str:
    messages = build_messages(stage, "<LOCKED_TASK_PROMPT>")
    return hashlib.sha256(_canonical_bytes(messages)).hexdigest()


PLAN_TEMPLATE_SHA256 = _template_sha256("plan")
CONSUME_TEMPLATE_SHA256 = _template_sha256("consume")


def template_metadata() -> dict[str, Any]:
    return {
        "schema": "tatqa_wp2_bridge_prompt_templates_v2",
        "system_instruction": SYSTEM_INSTRUCTION,
        "locked_examples_per_stage": 1,
        "plan_template_sha256": PLAN_TEMPLATE_SHA256,
        "consume_template_sha256": CONSUME_TEMPLATE_SHA256,
        "plan_example": PLAN_EXAMPLE,
        "consume_example": CONSUME_EXAMPLE,
    }


if __name__ == "__main__":
    print(json.dumps(template_metadata(), ensure_ascii=False, indent=2, sort_keys=True))
