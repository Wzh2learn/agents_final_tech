"""Qwen3-VL-8B-Instruct VLM server on :8007.

OpenAI-compatible /v1/chat/completions endpoint for vision-language tasks.
Loads model from local safetensors at ~/wzh/models/hf/qwen3-vl-8b-instruct/.
"""
import base64
import io
import os
import time
import logging
from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vlm8007")

MODEL_PATH = os.path.expanduser("~/wzh/models/hf/qwen3-vl-8b-instruct")

# Global model/processor (loaded at startup)
_model = None
_processor = None


def load_model():
    global _model, _processor
    from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
    log.info("Loading Qwen3-VL-8B-Instruct from %s ...", MODEL_PATH)
    t0 = time.time()
    _processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
    _model = Qwen3VLForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="sdpa",
    )
    _model.eval()
    log.info("Model loaded in %.1fs", time.time() - t0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


app = FastAPI(title="Qwen3-VL-8B VLM Server", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model": "Qwen3-VL-8B-Instruct", "loaded": _model is not None}


def _decode_image(image_url: str) -> Image.Image:
    """Decode base64 data URI or URL to PIL Image."""
    if image_url.startswith("data:image"):
        # data:image/png;base64,...
        header, b64data = image_url.split(",", 1)
        img_bytes = base64.b64decode(b64data)
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")
    else:
        # Assume URL - download
        import urllib.request
        with urllib.request.urlopen(image_url, timeout=30) as resp:
            return Image.open(io.BytesIO(resp.read())).convert("RGB")


@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """OpenAI-compatible chat completions with vision support."""
    messages = request.get("messages", [])
    max_tokens = request.get("max_tokens", 2048)
    temperature = request.get("temperature", 0.0)

    # Convert OpenAI format to Qwen VL format
    qwen_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if isinstance(content, list):
            # Multi-modal content
            qwen_content = []
            for part in content:
                if part.get("type") == "image_url":
                    url = part["image_url"].get("url", "")
                    try:
                        img = _decode_image(url)
                        qwen_content.append({"type": "image", "image": img})
                    except Exception as e:
                        log.warning("Failed to decode image: %s", e)
                        qwen_content.append({"type": "text", "text": "[image decode failed]"})
                elif part.get("type") == "text":
                    qwen_content.append({"type": "text", "text": part.get("text", "")})
            qwen_messages.append({"role": role, "content": qwen_content})
        else:
            qwen_messages.append({"role": role, "content": content})

    try:
        t0 = time.time()
        text = _processor.apply_chat_template(qwen_messages, tokenize=False, add_generation_prompt=True)

        # Extract images from messages
        images = []
        for msg in qwen_messages:
            if isinstance(msg["content"], list):
                for part in msg["content"]:
                    if part.get("type") == "image":
                        images.append(part["image"])

        inputs = _processor(
            text=[text],
            images=images if images else None,
            padding=True,
            return_tensors="pt",
        ).to(_model.device)

        with torch.no_grad():
            gen_kwargs = {"max_new_tokens": max_tokens}
            if temperature > 0:
                gen_kwargs["temperature"] = temperature
                gen_kwargs["do_sample"] = True
            else:
                gen_kwargs["do_sample"] = False

            output_ids = _model.generate(**inputs, **gen_kwargs)

        # Decode only the generated tokens
        generated = output_ids[0][inputs["input_ids"].shape[1]:]
        response_text = _processor.decode(generated, skip_special_tokens=True)
        elapsed = time.time() - t0

        log.info("Generated %d tokens in %.1fs", len(generated), elapsed)

        return {
            "id": f"vlm-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "Qwen3-VL-8B-Instruct",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": inputs["input_ids"].shape[1],
                "completion_tokens": len(generated),
                "total_tokens": inputs["input_ids"].shape[1] + len(generated),
            },
        }
    except Exception as e:
        log.error("Generation error: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007, log_level="info")