"""Local Qwen loader invoked only after a persistent reservation exists."""

from __future__ import annotations

import json
import re
from typing import Any


MODEL_PATH = "/home/testuser/wzh/models/hf/Qwen3-4B"
MAX_NEW_TOKENS = 512
_MODEL: Any = None
_TOKENIZER: Any = None


def _complete_json(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped.startswith("{"):
        return False
    depth = 0
    in_string = False
    escaped = False
    for character in stripped:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return True
    return False


class CompleteJsonStopping:
    def __init__(self, tokenizer: Any, prompt_length: int):
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length
        self.eos_token_id = tokenizer.eos_token_id

    def __call__(self, input_ids: Any, scores: Any, **kwargs: Any) -> bool:
        del scores
        del kwargs
        token_ids = input_ids[0].tolist()[self.prompt_length :]
        text = self.tokenizer.decode(token_ids, skip_special_tokens=True)
        return _complete_json(text)


def load_and_generate(spec: Any) -> tuple[str, dict[str, int | None]]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    global _MODEL, _TOKENIZER
    messages = spec.payload["messages"]
    if _TOKENIZER is None:
        _TOKENIZER = AutoTokenizer.from_pretrained(
            MODEL_PATH,
            local_files_only=True,
        )
    encoded = _TOKENIZER.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    input_ids = encoded["input_ids"]
    expected_input = int(spec.input_tokens_upper_bound) - MAX_NEW_TOKENS
    actual_input = int(input_ids.shape[1])
    if actual_input != expected_input:
        raise RuntimeError(
            f"tokenized_input_mismatch:{actual_input}!={expected_input}"
        )
    if actual_input > 6000:
        raise RuntimeError(f"input_token_cap_exceeded:{actual_input}")
    if _MODEL is None:
        _MODEL = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            attn_implementation="sdpa",
            local_files_only=True,
        )
        _MODEL.eval()
    set_seed(20261027)
    torch.manual_seed(20261027)
    torch.cuda.manual_seed_all(20261027)
    input_ids = input_ids.to(_MODEL.device)
    attention_mask = torch.ones_like(input_ids)
    stopping = CompleteJsonStopping(_TOKENIZER, actual_input)
    with torch.inference_mode():
        output_ids = _MODEL.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            pad_token_id=_TOKENIZER.eos_token_id,
            eos_token_id=_TOKENIZER.eos_token_id,
            stopping_criteria=[stopping],
        )
    generated = output_ids[0][actual_input:]
    response_text = _TOKENIZER.decode(generated, skip_special_tokens=True)
    usage = {
        "input_tokens": actual_input,
        "output_tokens": int(generated.shape[0]),
        "cached_tokens": None,
        "reasoning_tokens": None,
    }
    return response_text, usage


def raw_persisted_scorer(
    raw_event: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    del context
    return {
        "schema": "word_new_family_raw_persist_receipt_v1",
        "status": "RAW_PERSISTED_NOT_SCORED",
        "physical_attempt_id": raw_event["physical_attempt_id"],
        "logical_call_id": raw_event["logical_call_id"],
        "raw_event_sha256": raw_event["event_sha256"],
        "scored": False,
        "model_loaded_in_scorer": False,
    }


def main() -> int:
    raise RuntimeError("loader_entrypoint_not_a_cli")


if __name__ == "__main__":
    raise SystemExit(main())
