"""Focused unit coverage for the isolated tabular MCP boundary."""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from tabular_mcp_server import service


REQUEST = {
    "feature_names": ["age", "debt_ratio"],
    "train_rows": [[20, 0.1], [40, 0.8], [25, 0.2], [55, 0.9]],
    "labels": [0, 1, 0, 1],
    "predict_rows": [[30, 0.3], [60, 0.7]],
}


def success_payload() -> dict[str, object]:
    return {
        "status": "success", "model_key": "tabpfn", "model_version": "v2",
        "train_count": 4, "predict_count": 2, "predictions": [0, 1],
        "probabilities": [[0.8, 0.2], [0.1, 0.9]], "elapsed_sec": 1.2,
        "checkpoint": "/private/model", "environment": "private",
    }


def test_request_validation_rejects_non_rectangular_nonfinite_and_single_class() -> None:
    assert service.validate_request(**REQUEST)["model"] == "tabpfn"
    for field, value in (
        ("train_rows", [[1, 2], [3]]),
        ("predict_rows", [[float("nan"), 0.2]]),
        ("labels", [0, 0, 0, 0]),
        ("feature_names", ["same", "same"]),
    ):
        invalid = dict(REQUEST)
        invalid[field] = value
        with pytest.raises(service.TabularInputError):
            service.validate_request(**invalid)


def test_request_validation_limits_models_versions_and_rows() -> None:
    with pytest.raises(service.TabularInputError):
        service.validate_request(**REQUEST, model="/model/path")
    with pytest.raises(service.TabularInputError):
        service.validate_request(**REQUEST, model_version="v3")
    invalid = dict(REQUEST)
    invalid["predict_rows"] = [[1, 2]] * (service.MAX_PREDICT_ROWS + 1)
    with pytest.raises(service.TabularInputError):
        service.validate_request(**invalid)


def test_child_command_uses_tabular_interpreter_only() -> None:
    command = service.build_inference_command({"JINRONG_TABULAR_PYTHON": "/opt/tabular/python"})
    assert command[0] == "/opt/tabular/python"
    assert command[1].endswith("scripts/run_tabular_inference.py")


def test_tabular_mcp_launcher_uses_mcp_python_not_inference_python() -> None:
    script = service.PROJECT_ROOT / "scripts" / "start_tabular_mcp_server.sh"
    result = subprocess.run(
        ["bash", str(script)],
        env={"JINRONG_MCP_PYTHON": "/bin/echo", "JINRONG_TABULAR_PYTHON": "/bin/false"},
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "-m tabular_mcp_server.server"


def test_run_sends_json_to_child_and_sanitizes_response() -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def runner(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(success_payload()))

    result = service.run_tabular_classify(**REQUEST, environment={"JINRONG_TABULAR_TIMEOUT_SECONDS": "42"}, runner=runner)
    assert result == {
        "status": "success", "model_key": "tabpfn", "model_version": "v2",
        "train_count": 4, "predict_count": 2, "predictions": [0.0, 1.0],
        "probabilities": [[0.8, 0.2], [0.1, 0.9]], "elapsed_sec": 1.2,
    }
    assert calls[0][1]["timeout"] == 42
    assert calls[0][1]["check"] is False
    assert "checkpoint" not in json.dumps(result)


@pytest.mark.parametrize("stdout", ["bad", "[]", '{"status":"success"}'])
def test_run_rejects_malformed_child_output(stdout: str) -> None:
    with pytest.raises(service.TabularInferenceError):
        service.run_tabular_classify(
            **REQUEST, runner=lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout)
        )


def test_run_handles_timeout_and_nonzero_child() -> None:
    def timeout_runner(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("tabular", 1)

    with pytest.raises(service.TabularInferenceError, match="timed out"):
        service.run_tabular_classify(**REQUEST, runner=timeout_runner)
    with pytest.raises(service.TabularInferenceError, match="failed"):
        service.run_tabular_classify(
            **REQUEST, runner=lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="")
        )
