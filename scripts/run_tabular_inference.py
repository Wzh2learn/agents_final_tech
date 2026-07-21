"""Isolated child CLI for one validated TabPFN or TabFM classification request."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import numpy as np
import pandas as pd

from smoke_test_tabular_model import build_classifier
from tabular_mcp_server.service import (
    TABFM_MODEL_VERSION,
    TABPFN_MODEL_VERSION,
    TabularInputError,
    validate_request,
)


DEFAULT_TABFM_CHECKPOINT = "/home/testuser/wzh/models/hf/tabfm-1.0.0-pytorch"


def _error_result() -> None:
    print(json.dumps({"status": "error"}))


def _read_request() -> dict[str, Any]:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        raise TabularInputError("request must be one JSON object") from exc
    if not isinstance(payload, dict):
        raise TabularInputError("request must be one JSON object")
    return validate_request(
        payload.get("feature_names"),
        payload.get("train_rows"),
        payload.get("labels"),
        payload.get("predict_rows"),
        payload.get("model", "tabpfn"),
        payload.get("model_version", TABPFN_MODEL_VERSION),
    )


def run_request(request: dict[str, Any]) -> dict[str, Any]:
    """Load the server-selected model and return only the MCP response contract."""
    # Prevent an MCP call from causing a model download if a local checkpoint is absent.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    checkpoint = os.environ.get("JINRONG_TABFM_CHECKPOINT_PATH", DEFAULT_TABFM_CHECKPOINT)
    args = argparse.Namespace(
        model=request["model"],
        model_version=TABPFN_MODEL_VERSION,
        checkpoint_path=checkpoint,
        device="cuda",
    )
    classifier, _ = build_classifier(args)
    train = pd.DataFrame(request["train_rows"], columns=request["feature_names"])
    predict = pd.DataFrame(request["predict_rows"], columns=request["feature_names"])
    started = time.perf_counter()
    classifier.fit(train, np.asarray(request["labels"]))
    predictions = classifier.predict(predict)
    probabilities = classifier.predict_proba(predict)
    elapsed = time.perf_counter() - started
    return {
        "status": "success",
        "model_key": request["model"],
        "model_version": (
            TABPFN_MODEL_VERSION if request["model"] == "tabpfn" else TABFM_MODEL_VERSION
        ),
        "train_count": len(train),
        "predict_count": len(predict),
        "predictions": np.asarray(predictions).tolist(),
        "probabilities": np.asarray(probabilities).tolist(),
        "elapsed_sec": round(elapsed, 3),
    }


def main() -> int:
    """Read exactly one request and emit exactly one JSON result."""
    try:
        print(json.dumps(run_request(_read_request()), separators=(",", ":")))
    except Exception:  # The parent intentionally receives no model/runtime details.
        _error_result()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
