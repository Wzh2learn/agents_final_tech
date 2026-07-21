"""Validation and subprocess boundary for the read-only tabular MCP tool."""

from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_MODELS = ("tabpfn", "tabfm")
TABPFN_MODEL_VERSION = "v2"
TABFM_MODEL_VERSION = "1.0.0-pytorch"
MAX_FEATURES = 64
MAX_TRAIN_ROWS = 1_000
MAX_PREDICT_ROWS = 256
MAX_FEATURE_NAME_LENGTH = 64
DEFAULT_TIMEOUT_SECONDS = 600


class TabularInputError(ValueError):
    """Raised when a caller supplies an unsupported tabular request."""


class TabularInferenceError(RuntimeError):
    """Raised when the isolated inference process cannot produce a safe result."""


def tabular_python(environment: Mapping[str, str] | None = None) -> str:
    """Return the isolated interpreter used for heavyweight tabular inference."""
    env = os.environ if environment is None else environment
    return env.get("JINRONG_TABULAR_PYTHON", "~/miniconda3/envs/wzh_tabular/bin/python")


def timeout_seconds(environment: Mapping[str, str] | None = None) -> int:
    """Read a bounded subprocess timeout without returning local configuration."""
    env = os.environ if environment is None else environment
    raw_value = env.get("JINRONG_TABULAR_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise TabularInputError("JINRONG_TABULAR_TIMEOUT_SECONDS must be an integer") from exc
    if not 1 <= value <= DEFAULT_TIMEOUT_SECONDS:
        raise TabularInputError(
            f"JINRONG_TABULAR_TIMEOUT_SECONDS must be between 1 and {DEFAULT_TIMEOUT_SECONDS}"
        )
    return value


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TabularInputError(f"{field_name} must contain only numeric values")
    number = float(value)
    if not math.isfinite(number):
        raise TabularInputError(f"{field_name} must contain only finite numeric values")
    return number


def _validate_rows(value: Any, field_name: str, expected_width: int, maximum: int) -> list[list[float]]:
    if not isinstance(value, list) or not value or len(value) > maximum:
        raise TabularInputError(f"{field_name} must contain between 1 and {maximum} rows")
    rows: list[list[float]] = []
    for row_index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != expected_width:
            raise TabularInputError(f"{field_name}[{row_index}] must match feature_names exactly")
        rows.append([_finite_number(item, f"{field_name}[{row_index}]") for item in row])
    return rows


def validate_request(
    feature_names: Any,
    train_rows: Any,
    labels: Any,
    predict_rows: Any,
    model: Any = "tabpfn",
    model_version: Any = TABPFN_MODEL_VERSION,
) -> dict[str, Any]:
    """Validate a small, rectangular in-memory classification request."""
    if not isinstance(feature_names, list) or not 1 <= len(feature_names) <= MAX_FEATURES:
        raise TabularInputError(f"feature_names must contain between 1 and {MAX_FEATURES} names")
    if any(
        not isinstance(name, str) or not name.strip() or len(name) > MAX_FEATURE_NAME_LENGTH
        for name in feature_names
    ):
        raise TabularInputError("feature_names must contain short, non-empty strings")
    if len(set(feature_names)) != len(feature_names):
        raise TabularInputError("feature_names must be unique")
    if model not in SUPPORTED_MODELS:
        raise TabularInputError(f"model must be one of: {', '.join(SUPPORTED_MODELS)}")
    if model_version != TABPFN_MODEL_VERSION:
        raise TabularInputError(f"model_version must be {TABPFN_MODEL_VERSION}")
    train = _validate_rows(train_rows, "train_rows", len(feature_names), MAX_TRAIN_ROWS)
    predict = _validate_rows(predict_rows, "predict_rows", len(feature_names), MAX_PREDICT_ROWS)
    if not isinstance(labels, list) or len(labels) != len(train):
        raise TabularInputError("labels must be a list matching train_rows")
    checked_labels = [_finite_number(item, "labels") for item in labels]
    if len(set(checked_labels)) < 2:
        raise TabularInputError("labels must contain at least two classes")
    return {
        "feature_names": list(feature_names),
        "train_rows": train,
        "labels": checked_labels,
        "predict_rows": predict,
        "model": model,
        "model_version": TABPFN_MODEL_VERSION,
    }


def build_inference_command(environment: Mapping[str, str] | None = None) -> list[str]:
    """Build a fixed child CLI command without caller-controlled code or paths."""
    return [
        str(Path(tabular_python(environment)).expanduser()),
        str(PROJECT_ROOT / "scripts" / "run_tabular_inference.py"),
    ]


def _safe_result(payload: Any, request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise TabularInferenceError("Tabular inference returned an invalid result")
    model = request["model"]
    expected_version = TABPFN_MODEL_VERSION if model == "tabpfn" else TABFM_MODEL_VERSION
    if payload.get("model_key") != model or payload.get("model_version") != expected_version:
        raise TabularInferenceError("Tabular inference returned an invalid model result")
    if payload.get("train_count") != len(request["train_rows"]):
        raise TabularInferenceError("Tabular inference returned an invalid train count")
    if payload.get("predict_count") != len(request["predict_rows"]):
        raise TabularInferenceError("Tabular inference returned an invalid predict count")
    predictions = payload.get("predictions")
    probabilities = payload.get("probabilities")
    if not isinstance(predictions, list) or len(predictions) != len(request["predict_rows"]):
        raise TabularInferenceError("Tabular inference returned invalid predictions")
    if not isinstance(probabilities, list) or len(probabilities) != len(predictions):
        raise TabularInferenceError("Tabular inference returned invalid probabilities")
    class_count = len(set(request["labels"]))
    safe_predictions = [_finite_number(value, "predictions") for value in predictions]
    safe_probabilities: list[list[float]] = []
    for row in probabilities:
        if not isinstance(row, list) or len(row) != class_count:
            raise TabularInferenceError("Tabular inference returned invalid probabilities")
        safe_probabilities.append([_finite_number(value, "probabilities") for value in row])
    elapsed = _finite_number(payload.get("elapsed_sec"), "elapsed_sec")
    if elapsed < 0:
        raise TabularInferenceError("Tabular inference returned an invalid elapsed time")
    return {
        "status": "success",
        "model_key": model,
        "model_version": expected_version,
        "train_count": len(request["train_rows"]),
        "predict_count": len(request["predict_rows"]),
        "predictions": safe_predictions,
        "probabilities": safe_probabilities,
        "elapsed_sec": elapsed,
    }


def run_tabular_classify(
    feature_names: list[str],
    train_rows: list[list[float]],
    labels: list[float],
    predict_rows: list[list[float]],
    model: str = "tabpfn",
    model_version: str = TABPFN_MODEL_VERSION,
    *,
    environment: Mapping[str, str] | None = None,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Execute one small read-only classification call in the isolated environment."""
    request = validate_request(feature_names, train_rows, labels, predict_rows, model, model_version)
    try:
        completed = runner(
            build_inference_command(environment),
            cwd=PROJECT_ROOT,
            input=json.dumps(request, separators=(",", ":")),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds(environment),
        )
    except subprocess.TimeoutExpired as exc:
        raise TabularInferenceError("Tabular inference timed out") from exc
    except OSError as exc:
        raise TabularInferenceError("Tabular inference could not start") from exc
    if completed.returncode != 0:
        raise TabularInferenceError("Tabular inference failed")
    try:
        return _safe_result(json.loads(completed.stdout), request)
    except (TypeError, json.JSONDecodeError) as exc:
        raise TabularInferenceError("Tabular inference returned malformed JSON") from exc
