#!/usr/bin/env python3
"""M1 OCR 兜底 · Phase 1：单视觉模型一次性 OCR manifest 中全部图片。

用完即停、不常驻：模型在本进程内加载一次，处理完即随进程退出释放；
一次只起一个模型（默认 paddleocr-vl-1.6，输出含 markdown 表格结构）。
每页/每图生成阶段 30s 超时（SIGALRM），超时记 TIMEOUT 继续；
连续 3 次失败即停；OOM 记 BLOCKED 立即停，不重试。
仅写 /tmp，不下载模型，不联网。

用法（wzh_vision 环境）:
  ~/miniconda3/envs/wzh_vision/bin/python scripts/m1_ocr_fallback.py \
      --manifest /tmp/m1_ocr/manifest.json --out /tmp/m1_ocr/ocr_results.json

transformers 版本要求:
  PaddleOCR-VL 的随包远程代码 (modeling_paddleocr_vl.py / configuration_paddleocr_vl.py)
  针对 transformers ~4.55.0 编写 (config.json: transformers_version=4.55.0)。
  transformers 5.x 移除了其依赖的内部 API:
    - ROPE_INIT_FUNCTIONS["default"] 键
    - RotaryEmbedding.compute_default_rope_parameters mixin 方法
    - AutoModelForImageTextToText 期望 composite config.text_config 布局
  因此在 transformers>=5.0 环境下本脚本会在加载模型前快速失败 (exit 4,
  输出 PADDLEOCR_INCOMPATIBLE 标记), 由调用方回退到 :8004 视觉引擎。
  修复需将 wzh_vision 环境 transformers 降级到 ~4.55.x (会影响该环境其他模型, 暂不执行)。
"""
from __future__ import annotations

import argparse
import json
import signal
import time
from pathlib import Path
from typing import Any

PROMPTS = {
    "paddleocr": "OCR:",
    "minicpm": "Extract all text and tables from this document image. Preserve reading order; render tables as markdown.",
    "qwen3-vl": "Extract all text and tables from this document image. Preserve reading order; render tables as markdown.",
}

# PaddleOCR-VL remote code targets transformers ~4.55.0; 5.x dropped its internal APIs.
_TRANSFORMERS_MAX_EXCLUSIVE = (5, 0)


def _transformers_incompatibility() -> str | None:
    """Return a human-readable reason if the env transformers cannot load PaddleOCR-VL.

    Returns None when compatible. Only checks the version (cheap, no model load),
    so the caller can fail fast instead of hitting the 120s subprocess timeout.
    """
    try:
        import transformers
    except Exception as exc:  # noqa: BLE001
        return f"transformers import failed: {exc}"
    raw = getattr(transformers, "__version__", "0.0")
    parts: list[int] = []
    for chunk in str(raw).split(".")[:2]:
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 2:
        parts.append(0)
    if tuple(parts) >= _TRANSFORMERS_MAX_EXCLUSIVE:
        return (
            f"transformers {raw} >= 5.0 is incompatible with PaddleOCR-VL remote "
            f"code (requires ~4.55.x; needs ROPE_INIT_FUNCTIONS['default'], "
            f"RotaryEmbedding mixin, composite text_config)"
        )
    return None


class _GenTimeout(Exception):
    """Per-image generation timeout (SIGALRM)."""


def _alarm_handler(signum, frame):  # noqa: ARG001
    raise _GenTimeout("generation exceeded per-image timeout")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("/tmp/m1_ocr/ocr_results.json"))
    p.add_argument("--model-path", type=Path,
                   default=Path.home() / "wzh/models/hf/paddleocr-vl-1.6")
    p.add_argument("--kind", choices=tuple(PROMPTS), default="paddleocr")
    p.add_argument("--max-new-tokens", type=int, default=2048)
    p.add_argument("--timeout", type=int, default=30, help="per-image generation timeout (s)")
    p.add_argument("--max-pixels", type=int, default=0,
                   help="override processor longest_edge in pixels (0 = model default)")
    p.add_argument("--max-failures", type=int, default=3, help="consecutive failures to stop")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    images = manifest["images"]
    if not images:
        args.out.write_text(json.dumps({"images": [], "note": "empty manifest"},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
        print("manifest has no images")
        return 0
    if not args.model_path.is_dir():
        print(f"BLOCKED: model dir missing: {args.model_path}")
        return 3

    incompat = _transformers_incompatibility()
    if incompat is not None:
        # Stable marker so the caller (scripts/m1_statement_parser.py) can cache a
        # permanent skip and fall back to the vision engine without re-spawning.
        print(f"PADDLEOCR_INCOMPATIBLE: {incompat}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(
            {"model": args.model_path.name, "kind": args.kind, "stopped": "INCOMPATIBLE",
             "note": incompat, "n_images": len(images), "results": []},
            ensure_ascii=False, indent=2), encoding="utf-8")
        return 4

    import torch
    from PIL import Image
    from transformers import AutoModel, AutoProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    prompt = PROMPTS[args.kind]

    t0 = time.perf_counter()
    processor = AutoProcessor.from_pretrained(str(args.model_path), trust_remote_code=True)
    # AutoModel (not AutoModelForImageTextToText): config.json auto_map registers the
    # bundled remote class only under AutoModel/AutoModelForCausalLM, so AutoModel loads
    # the model's own 4.55-era code that matches its flat config (no composite text_config).
    model = AutoModel.from_pretrained(
        str(args.model_path), dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    ).eval()
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    cold_start = round(time.perf_counter() - t0, 3)
    print(f"[load] device={device} dtype={dtype} cold_start={cold_start}s model={args.model_path.name}")

    template_kwargs: dict[str, Any] = {}
    generation_kwargs: dict[str, Any] = {}
    if args.kind == "minicpm":
        template_kwargs.update(downsample_mode="16x", max_slice_nums=36)
        generation_kwargs["downsample_mode"] = "16x"
    if args.kind == "paddleocr":
        ip = processor.image_processor
        edge_kwargs: dict[str, int] = {
            "shortest_edge": getattr(ip, "min_pixels", 112896),
            "longest_edge": getattr(ip, "max_pixels", 1003520),
        }
        if args.max_pixels > 0:
            edge_kwargs["longest_edge"] = args.max_pixels
        template_kwargs["images_kwargs"] = {"size": edge_kwargs}

    results: list[dict[str, Any]] = []
    consecutive_failures = 0
    stopped = ""
    signal.signal(signal.SIGALRM, _alarm_handler)

    for entry in images:
        png = Path(entry["png"])
        if not png.is_file():
            results.append({**_meta(entry), "status": "ERROR", "note": "png missing",
                            "text": "", "text_len": 0, "elapsed_sec": 0.0})
            consecutive_failures += 1
            continue
        img = Image.open(png).convert("RGB")
        messages = [{"role": "user", "content": [
            {"type": "image", "image": img}, {"type": "text", "text": prompt}]}]
        status = "ok"
        text = ""
        note = ""
        elapsed = 0.0
        peak = None
        try:
            inputs = processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt", **template_kwargs,
            ).to(model.device)
            if device == "cuda":
                torch.cuda.reset_peak_memory_stats()
            prompt_len = inputs["input_ids"].shape[-1]
            tg0 = time.perf_counter()
            signal.alarm(args.timeout)
            try:
                with torch.inference_mode():
                    gen_ids = model.generate(
                        **inputs, max_new_tokens=args.max_new_tokens,
                        do_sample=False, **generation_kwargs)
            finally:
                signal.alarm(0)
            elapsed = round(time.perf_counter() - tg0, 3)
            out_ids = gen_ids[0][prompt_len:]
            text = processor.decode(out_ids, skip_special_tokens=True).strip()
            if device == "cuda":
                peak = round(torch.cuda.max_memory_allocated() / 1024**3, 3)
            consecutive_failures = 0
        except _GenTimeout:
            status = "TIMEOUT"
            note = f"generation > {args.timeout}s"
            consecutive_failures += 1
            if device == "cuda":
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
        except torch.cuda.OutOfMemoryError as exc:
            status = "OOM"
            note = f"cuda OOM: {exc}"
            results.append({**_meta(entry), "status": status, "note": note,
                            "text": text, "text_len": len(text),
                            "elapsed_sec": elapsed, "peak_cuda_memory_gib": peak,
                            "prompt_tokens": locals().get("prompt_len", -1)})
            stopped = "OOM_BLOCKED"
            break
        except Exception as exc:  # noqa: BLE001
            status = "ERROR"
            note = f"{type(exc).__name__}: {exc}"
            consecutive_failures += 1

        results.append({**_meta(entry), "status": status, "note": note,
                        "text": text, "text_len": len(text),
                        "elapsed_sec": elapsed, "peak_cuda_memory_gib": peak,
                        "prompt_tokens": locals().get("prompt_len", -1)})
        print(f"  [{status:7}] {entry['png_basename']:40} len={len(text):5} t={elapsed}s")
        if consecutive_failures >= args.max_failures:
            stopped = f"CONSECUTIVE_FAILURES={consecutive_failures}"
            break

    payload = {
        "model": args.model_path.name,
        "kind": args.kind,
        "device": device,
        "cold_start_sec": cold_start,
        "max_new_tokens": args.max_new_tokens,
        "timeout_sec": args.timeout,
        "stopped": stopped,
        "n_images": len(images),
        "n_processed": len(results),
        "results": results,
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"[done] processed={len(results)} ok={ok} stopped='{stopped}' -> {args.out}")
    return 0


def _meta(entry: dict) -> dict:
    return {"sample": entry["sample"], "unit": entry["unit"],
            "png_basename": entry["png_basename"],
            "width": entry["width"], "height": entry["height"]}


if __name__ == "__main__":
    raise SystemExit(main())
