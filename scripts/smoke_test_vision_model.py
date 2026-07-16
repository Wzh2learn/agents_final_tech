"""Run one local OCR/VLM image inference and print a compact JSON result."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


PROMPTS = {
    "paddleocr": "OCR:",
    "minicpm": "Extract all text from this document image. Preserve its reading order.",
    "qwen3-vl": "Extract all text from this document image. Preserve its reading order.",
}


def parse_args() -> argparse.Namespace:
    """Parse the local model, image, and inference settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--kind", choices=tuple(PROMPTS), required=True)
    parser.add_argument("--prompt", help="Override the task-specific default prompt.")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    return parser.parse_args()


def main() -> None:
    """Load one vision model, run deterministic generation, and report resources."""
    args = parse_args()
    if not args.model_path.is_dir():
        raise SystemExit(f"Model directory does not exist: {args.model_path}")
    if not args.image.is_file():
        raise SystemExit(f"Image does not exist: {args.image}")

    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    image = Image.open(args.image).convert("RGB")
    prompt = args.prompt or PROMPTS[args.kind]

    started = time.perf_counter()
    processor = AutoProcessor.from_pretrained(str(args.model_path))
    model = AutoModelForImageTextToText.from_pretrained(
        str(args.model_path),
        dtype=dtype,
        device_map="auto" if device == "cuda" else None,
    ).eval()
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    template_kwargs: dict[str, Any] = {}
    generation_kwargs: dict[str, Any] = {}
    if args.kind == "minicpm":
        template_kwargs.update(downsample_mode="16x", max_slice_nums=36)
        generation_kwargs["downsample_mode"] = "16x"
    if args.kind == "paddleocr":
        image_processor = processor.image_processor
        template_kwargs["images_kwargs"] = {
            "size": {
                "shortest_edge": getattr(image_processor, "min_pixels", 112896),
                "longest_edge": getattr(image_processor, "max_pixels", 1003520),
            }
        }

    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        **template_kwargs,
    ).to(model.device)
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
            **generation_kwargs,
        )
    prompt_length = inputs["input_ids"].shape[-1]
    output_ids = generated_ids[0][prompt_length:]
    text = processor.decode(output_ids, skip_special_tokens=True).strip()

    result = {
        "kind": args.kind,
        "model_path": str(args.model_path),
        "image": str(args.image),
        "image_size": list(image.size),
        "device": device,
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "peak_cuda_memory_gib": (
            round(torch.cuda.max_memory_allocated() / 1024**3, 3) if device == "cuda" else None
        ),
        "text": text,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
