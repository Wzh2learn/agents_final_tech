#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


from constrained_decoding_v2 import build_processor
from prompt_v2 import (
    CONSUME_TEMPLATE_SHA256,
    PLAN_TEMPLATE_SHA256,
    render_chat_prompt,
)
from validate_v2 import SCHEMA_PATH, sha256_bytes


MODEL_ID = "tatqa-wp2-qwen3-8b-b968826d"
REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
MAX_INPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 512
STAGES = frozenset({"plan", "consume"})


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class ActorServiceV2:
    def __init__(self, model_root: Path, metadata_path: Path) -> None:
        self.model_root = model_root
        self.metadata_path = metadata_path
        self.lock = threading.Lock()
        self.request_counter = 0
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_root),
            local_files_only=True,
            trust_remote_code=False,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_root),
            local_files_only=True,
            trust_remote_code=False,
            dtype=torch.bfloat16,
            device_map="cuda:0",
            low_cpu_mem_usage=True,
        )
        self.model.eval()

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("model") != MODEL_ID:
            raise ValueError("model must be tatqa-wp2-qwen3-8b-b968826d")
        stage = payload.get("schema_stage")
        if stage not in STAGES:
            raise ValueError("schema_stage must be plan or consume")
        prompt = payload.get("prompt")
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        max_tokens = payload.get("max_tokens")
        if (
            isinstance(max_tokens, bool)
            or not isinstance(max_tokens, int)
            or not 1 <= max_tokens <= MAX_OUTPUT_TOKENS
        ):
            raise ValueError("max_tokens must be an integer in [1, 512]")
        if payload.get("temperature") != 0:
            raise ValueError("temperature must be exactly 0")
        if payload.get("n", 1) != 1:
            raise ValueError("n must be exactly 1")
        if payload.get("echo", False) is not False:
            raise ValueError("echo must be false")
        top_p = payload.get("top_p")
        if top_p is not None and float(top_p) != 1.0:
            raise ValueError("top_p must be omitted or 1.0")
        stop = payload.get("stop")
        if stop is not None and not isinstance(stop, list):
            raise ValueError("stop must be omitted or a list")

        rendered_prompt = render_chat_prompt(
            self.tokenizer,
            stage,
            prompt,
        )
        token_ids = self.tokenizer(
            rendered_prompt,
            add_special_tokens=False,
            return_tensors="pt",
        )["input_ids"]
        input_tokens = int(token_ids.shape[1])
        if input_tokens > MAX_INPUT_TOKENS:
            raise ValueError("input exceeds the frozen 4096-token cap")
        processor = build_processor(
            stage,
            self.tokenizer,
            prefix_token_count=input_tokens,
        )
        with self.lock:
            self.request_counter += 1
            request_id = f"tatqa-wp2-bridge-v2-{self.request_counter:06d}"
            started = time.monotonic()
            input_tensor = token_ids.to(self.model.device)
            attention_mask = torch.ones_like(input_tensor)
            with torch.inference_mode():
                generated = self.model.generate(
                    input_tensor,
                    attention_mask=attention_mask,
                    max_new_tokens=max_tokens,
                    do_sample=False,
                    num_beams=1,
                    use_cache=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    logits_processor=[processor],
                )
            completion_ids = generated[0, input_tokens:]
            text = self.tokenizer.decode(
                completion_ids,
                skip_special_tokens=True,
            )
            completion_tokens = int(completion_ids.shape[0])
            elapsed = time.monotonic() - started
        return {
            "id": request_id,
            "object": "text_completion",
            "created": int(time.time()),
            "model": MODEL_ID,
            "choices": [
                {
                    "index": 0,
                    "text": text,
                    "finish_reason": (
                        "length"
                        if completion_tokens >= max_tokens
                        else "stop"
                    ),
                    "logprobs": None,
                }
            ],
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": input_tokens + completion_tokens,
            },
            "actor_request_id": request_id,
            "schema_stage": stage,
            "elapsed_seconds": elapsed,
        }


def build_handler(actor: ActorServiceV2) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "TatqaWp2ActorV2/1"

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._write_json(
                    200,
                    {
                        "status": "READY",
                        "model": MODEL_ID,
                        "revision": REVISION,
                        "model_requests": actor.request_counter,
                        "decoder": "minimum_custom_prefix_constraints",
                    },
                )
                return
            if self.path == "/v1/models":
                self._write_json(
                    200,
                    {
                        "object": "list",
                        "data": [
                            {
                                "id": MODEL_ID,
                                "object": "model",
                                "revision": REVISION,
                            }
                        ],
                    },
                )
                return
            self._write_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/v1/completions":
                self._write_json(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(
                    self.rfile.read(length).decode("utf-8")
                )
                result = actor.complete(payload)
            except Exception as exc:
                self._write_json(
                    400,
                    {
                        "error": {
                            "message": str(exc),
                            "type": "invalid_request_error",
                        }
                    },
                )
                return
            self._write_json(200, result)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8112)
    parser.add_argument("--startup-receipt", type=Path, required=True)
    args = parser.parse_args()
    args.model_root = args.model_root.resolve()
    args.metadata = args.metadata.resolve()
    actor = ActorServiceV2(args.model_root, args.metadata)
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    model_rows = [
        row for row in metadata["models"] if row.get("id") == "Qwen/Qwen3-8B"
    ]
    if len(model_rows) != 1 or model_rows[0]["revision"] != REVISION:
        raise RuntimeError("pinned model metadata mismatch")
    receipt = {
        "schema": "tatqa_wp2_actor_service_v2_startup_receipt",
        "status": "READY",
        "started_at_utc": utc_now(),
        "model_id": MODEL_ID,
        "revision": REVISION,
        "model_root": str(args.model_root),
        "host": args.host,
        "port": args.port,
        "decoder": {
            "implementation": "minimum_custom_prefix_constrained_logits_processor",
            "outlines_installed": False,
            "reason": (
                "python3.12 -m pip install --user outlines was blocked by "
                "PEP 668; no --break-system-packages override was used"
            ),
            "schema_path": str(SCHEMA_PATH),
            "schema_sha256": sha256_bytes(SCHEMA_PATH.read_bytes()),
            "plan_template_sha256": PLAN_TEMPLATE_SHA256,
            "consume_template_sha256": CONSUME_TEMPLATE_SHA256,
        },
        "runtime": {
            "implementation": "transformers greedy constrained completion server",
            "transformers_dtype": "bfloat16",
            "device": "cuda:0",
            "temperature": 0,
            "do_sample": False,
            "num_beams": 1,
            "max_input_tokens": MAX_INPUT_TOKENS,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        },
        "safety": {
            "external_network_calls": 0,
            "judge_calls": 0,
            "database_calls": 0,
            "production_service_calls": 0,
        },
    }
    args.startup_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.startup_receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    server = ThreadingHTTPServer((args.host, args.port), build_handler(actor))
    print(
        f"ACTOR_V2_READY {MODEL_ID} {args.host}:{args.port} "
        f"revision={REVISION}",
        flush=True,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
