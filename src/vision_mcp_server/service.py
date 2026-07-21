"""Validation and subprocess boundary for the read-only vision MCP tool."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALLOWED_ROOTS = (PROJECT_ROOT / "assets", PROJECT_ROOT / "data")
SUPPORTED_MODELS = ("paddleocr", "minicpm", "qwen3-vl")
MODEL_ENVIRONMENT_VARIABLES = {
    "paddleocr": "JINRONG_VISION_MODEL_PADDLEOCR",
    "minicpm": "JINRONG_VISION_MODEL_MINICPM",
    "qwen3-vl": "JINRONG_VISION_MODEL_QWEN3_VL",
}
DEFAULT_MODEL_DIRECTORIES = {
    "paddleocr": Path.home() / "wzh/models/hf/paddleocr-vl-1.6",
    "minicpm": Path.home() / "wzh/models/hf/minicpm-v-4.6",
    "qwen3-vl": Path.home() / "wzh/models/hf/qwen3-vl-8b-instruct",
}
ALLOWED_IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
MIN_MAX_NEW_TOKENS = 1
MAX_MAX_NEW_TOKENS = 512
DEFAULT_TIMEOUT_SECONDS = 600
MAX_EXTRACTED_TEXT_CHARS = 100_000


class VisionInputError(ValueError):
    """Raised when a caller supplies an unsupported model, image, or limit."""


class VisionInferenceError(RuntimeError):
    """Raised when the isolated local inference process cannot produce a result."""


def _environment_path_list(value: str | None) -> tuple[Path, ...]:
    if not value:
        return DEFAULT_ALLOWED_ROOTS
    paths = tuple(Path(item).expanduser() for item in value.split(os.pathsep) if item)
    if not paths:
        raise VisionInputError("JINRONG_VISION_ALLOWED_ROOTS must contain at least one directory")
    return paths


def allowed_roots(environment: Mapping[str, str] | None = None) -> tuple[Path, ...]:
    """Return configured image roots, resolving symlinks before containment checks."""
    env = os.environ if environment is None else environment
    roots = _environment_path_list(env.get("JINRONG_VISION_ALLOWED_ROOTS"))
    resolved: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        resolved.append(root.resolve())
    if not resolved:
        raise VisionInputError("No configured image roots are available")
    return tuple(resolved)


def resolve_image_path(
    image_path: str, environment: Mapping[str, str] | None = None
) -> Path:
    """Resolve one ordinary image within a configured, read-only allowlist."""
    if not isinstance(image_path, str) or not image_path.strip():
        raise VisionInputError("image_path must not be empty")
    candidate = Path(image_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise VisionInputError("image_path must reference an existing image file") from exc
    if resolved.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise VisionInputError("image_path must use a supported image extension")
    if not resolved.is_file():
        raise VisionInputError("image_path must reference a regular image file")
    if not any(resolved.is_relative_to(root) for root in allowed_roots(environment)):
        raise VisionInputError("image_path must be inside a configured allowed root")
    return resolved


def validate_model_key(model: str) -> str:
    """Validate the public model key without accepting caller-controlled paths."""
    if model not in SUPPORTED_MODELS:
        raise VisionInputError(f"model must be one of: {', '.join(SUPPORTED_MODELS)}")
    return model


def validate_max_new_tokens(max_new_tokens: int) -> int:
    """Bound generation length to a conservative, fixed server-side limit."""
    if isinstance(max_new_tokens, bool) or not isinstance(max_new_tokens, int):
        raise VisionInputError("max_new_tokens must be an integer")
    if not MIN_MAX_NEW_TOKENS <= max_new_tokens <= MAX_MAX_NEW_TOKENS:
        raise VisionInputError(
            f"max_new_tokens must be between {MIN_MAX_NEW_TOKENS} and {MAX_MAX_NEW_TOKENS}"
        )
    return max_new_tokens


def model_directory(model: str, environment: Mapping[str, str] | None = None) -> Path:
    """Select a server-side model directory, optionally overridden by its own variable."""
    env = os.environ if environment is None else environment
    key = validate_model_key(model)
    configured = env.get(MODEL_ENVIRONMENT_VARIABLES[key])
    return Path(configured).expanduser() if configured else DEFAULT_MODEL_DIRECTORIES[key]


def vision_python(environment: Mapping[str, str] | None = None) -> str:
    """Return the isolated interpreter used for heavyweight model inference."""
    env = os.environ if environment is None else environment
    return env.get(
        "JINRONG_VISION_PYTHON", "~/miniconda3/envs/wzh_vision/bin/python"
    )


def timeout_seconds(environment: Mapping[str, str] | None = None) -> int:
    """Read a bounded subprocess timeout without surfacing local configuration."""
    env = os.environ if environment is None else environment
    raw_value = env.get("JINRONG_VISION_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise VisionInputError("JINRONG_VISION_TIMEOUT_SECONDS must be an integer") from exc
    if not 1 <= value <= 3600:
        raise VisionInputError("JINRONG_VISION_TIMEOUT_SECONDS must be between 1 and 3600")
    return value


def build_inference_command(
    image: Path, model: str, max_new_tokens: int, environment: Mapping[str, str] | None = None
) -> list[str]:
    """Build the isolated smoke-script invocation; paths never enter MCP output."""
    return [
        str(Path(vision_python(environment)).expanduser()),
        str(PROJECT_ROOT / "scripts/smoke_test_vision_model.py"),
        "--model-path",
        str(model_directory(model, environment)),
        "--image",
        str(image),
        "--kind",
        model,
        "--max-new-tokens",
        str(max_new_tokens),
    ]


def _number(value: Any, field_name: str, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VisionInferenceError(f"Vision inference returned an invalid {field_name}")
    return float(value)


def parse_inference_output(stdout: str, model: str, image: Path) -> dict[str, Any]:
    """Parse the child JSON and return only MCP-safe fields, never local paths."""
    try:
        payload = json.loads(stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise VisionInferenceError("Vision inference returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise VisionInferenceError("Vision inference returned an invalid JSON payload")
    raw_size = payload.get("image_size")
    if (
        not isinstance(raw_size, list)
        or len(raw_size) != 2
        or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in raw_size)
    ):
        raise VisionInferenceError("Vision inference returned an invalid image_size")
    device = payload.get("device")
    text = payload.get("text")
    if not isinstance(device, str) or not device.strip():
        raise VisionInferenceError("Vision inference returned an invalid device")
    if not isinstance(text, str):
        raise VisionInferenceError("Vision inference returned invalid extracted text")
    sanitized_text = "".join(
        character for character in text if character >= " " or character in "\n\t"
    )
    return {
        "status": "success",
        "model_key": model,
        "image": {"basename": image.name, "size": raw_size},
        "device": device.strip()[:64],
        "elapsed_sec": _number(payload.get("elapsed_sec"), "elapsed_sec"),
        "peak_cuda_memory_gib": _number(
            payload.get("peak_cuda_memory_gib"), "peak_cuda_memory_gib", allow_none=True
        ),
        "text": sanitized_text[:MAX_EXTRACTED_TEXT_CHARS],
    }


def run_vision_ocr(
    image_path: str,
    model: str = "paddleocr",
    max_new_tokens: int = 256,
    *,
    environment: Mapping[str, str] | None = None,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Execute a single read-only OCR inference in the isolated vision environment."""
    key = validate_model_key(model)
    token_limit = validate_max_new_tokens(max_new_tokens)
    image = resolve_image_path(image_path, environment)
    command = build_inference_command(image, key, token_limit, environment)
    try:
        completed = runner(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds(environment),
        )
    except subprocess.TimeoutExpired as exc:
        raise VisionInferenceError("Vision inference timed out") from exc
    except OSError as exc:
        raise VisionInferenceError("Vision inference could not start") from exc
    if completed.returncode != 0:
        raise VisionInferenceError("Vision inference failed")
    return parse_inference_output(completed.stdout, key, image)
