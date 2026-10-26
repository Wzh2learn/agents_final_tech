"""Frozen local Qwen3-4B actor and a zero-output dry-run actor."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Protocol

from .contracts import MODEL_DECODE_SPEC, MODEL_PATH, sha256_bytes, sha256_file


class ModelActor(Protocol):
    def generate(self, prompt: str) -> dict[str, Any]:
        ...


class NullActor:
    def generate(self, prompt: str) -> dict[str, Any]:
        raise RuntimeError("generation_forbidden_in_zero_output_dry_run")


def model_freeze_files() -> dict[str, str]:
    names = [
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "vocab.json",
        "merges.txt",
        "model.safetensors.index.json",
    ]
    result = {name: sha256_file(MODEL_PATH / name) for name in names}
    index = json.loads((MODEL_PATH / "model.safetensors.index.json").read_text("utf-8"))
    shard_names = sorted(set(index["weight_map"].values()))
    for name in shard_names:
        result[name] = sha256_file(MODEL_PATH / name)
    return result


def qualify_model_interface() -> dict[str, Any]:
    from transformers import AutoConfig, AutoTokenizer

    if not MODEL_PATH.is_dir():
        raise RuntimeError("model_path_missing")
    config = AutoConfig.from_pretrained(MODEL_PATH, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    probe = "Visible evidence only. Return JSON."
    encoded = tokenizer(probe, return_tensors=None)
    decoded = tokenizer.decode(encoded["input_ids"], skip_special_tokens=True)
    hashes = model_freeze_files()
    return {
        "status": "PASS",
        "model_path": str(MODEL_PATH),
        "architecture": list(config.architectures),
        "model_type": config.model_type,
        "tokenizer_class": tokenizer.__class__.__name__,
        "tokenizer_roundtrip": decoded == probe,
        "dtype": MODEL_DECODE_SPEC["dtype"],
        "decoding": MODEL_DECODE_SPEC,
        "prompt_template_sha256": sha256_bytes(
            __import__(
                "research.publication_proxy_calibration_20261026_v1.raw.contracts",
                fromlist=["PROMPT_TEMPLATE"],
            ).PROMPT_TEMPLATE.encode("utf-8")
        ),
        "model_file_hashes": hashes,
        "generation_calls_used_for_qualification": 0,
        "note": "Tokenizer/config interface qualification only; no model output was generated.",
    }


class LocalQwenActor:
    def __init__(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH, local_files_only=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            local_files_only=True,
            dtype=torch.bfloat16,
            device_map="cuda",
        )
        self.model.eval()
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def generate(self, prompt: str) -> dict[str, Any]:
        encoded = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            return_tensors="pt",
        ).to(self.model.device)
        prompt_tokens = int(encoded["input_ids"].shape[1])
        started = time.perf_counter()
        with self.torch.inference_mode():
            output = self.model.generate(
                **encoded,
                do_sample=MODEL_DECODE_SPEC["do_sample"],
                max_new_tokens=MODEL_DECODE_SPEC["max_new_tokens"],
                use_cache=MODEL_DECODE_SPEC["use_cache"],
                pad_token_id=self.tokenizer.pad_token_id,
            )
        generated_ids = output[0, prompt_tokens:]
        output_tokens = int(generated_ids.shape[0])
        text = self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        return {
            "complete_response": text,
            "input_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": None,
            "wall_seconds": time.perf_counter() - started,
        }
