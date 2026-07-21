"""Focused unit coverage for the isolated vision MCP boundary."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from vision_mcp_server import service


def make_image(tmp_path: Path, name: str = "公开示例.png") -> Path:
    root = tmp_path / "allowed"
    root.mkdir()
    image = root / name
    image.write_bytes(b"not-decoded-by-unit-tests")
    return image


def test_model_and_token_validation() -> None:
    assert service.validate_model_key("paddleocr") == "paddleocr"
    assert service.validate_max_new_tokens(256) == 256
    with pytest.raises(service.VisionInputError):
        service.validate_model_key("/caller/model")
    with pytest.raises(service.VisionInputError):
        service.validate_max_new_tokens(0)
    with pytest.raises(service.VisionInputError):
        service.validate_max_new_tokens(True)


def test_image_must_be_regular_allowed_image(tmp_path: Path) -> None:
    image = make_image(tmp_path)
    environment = {"JINRONG_VISION_ALLOWED_ROOTS": str(image.parent)}
    assert service.resolve_image_path(str(image), environment) == image.resolve()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"x")
    with pytest.raises(service.VisionInputError, match="allowed root"):
        service.resolve_image_path(str(outside), environment)
    text_file = image.parent / "input.txt"
    text_file.write_text("x")
    with pytest.raises(service.VisionInputError, match="supported image"):
        service.resolve_image_path(str(text_file), environment)


def test_default_allowed_roots_are_project_assets_and_data() -> None:
    assert service.DEFAULT_ALLOWED_ROOTS == (
        service.PROJECT_ROOT / "assets",
        service.PROJECT_ROOT / "data",
    )


def test_image_path_rejects_traversal_outside_root(tmp_path: Path) -> None:
    image = make_image(tmp_path)
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"x")
    environment = {"JINRONG_VISION_ALLOWED_ROOTS": str(image.parent)}
    traversal = image.parent / ".." / "outside.jpg"
    with pytest.raises(service.VisionInputError, match="allowed root"):
        service.resolve_image_path(str(traversal), environment)


def test_subprocess_command_uses_fixed_mapping_and_not_caller_path(tmp_path: Path) -> None:
    image = make_image(tmp_path)
    environment = {
        "JINRONG_VISION_ALLOWED_ROOTS": str(image.parent),
        "JINRONG_VISION_PYTHON": "/opt/vision/bin/python",
        "JINRONG_VISION_MODEL_PADDLEOCR": "/srv/models/paddleocr",
    }
    command = service.build_inference_command(image, "paddleocr", 12, environment)
    assert command[0] == "/opt/vision/bin/python"
    assert command[command.index("--model-path") + 1] == "/srv/models/paddleocr"
    assert command[command.index("--image") + 1] == str(image)
    assert "--kind" in command


def test_vision_mcp_launcher_uses_mcp_python_not_inference_python() -> None:
    script = service.PROJECT_ROOT / "scripts" / "start_vision_mcp_server.sh"
    environment = {
        "JINRONG_MCP_PYTHON": "/bin/echo",
        "JINRONG_VISION_PYTHON": "/bin/false",
    }

    result = subprocess.run(
        ["bash", str(script)],
        env=environment,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "-m vision_mcp_server.server"


def test_parse_output_selects_safe_payload_only(tmp_path: Path) -> None:
    image = make_image(tmp_path)
    payload = {
        "model_path": "/private/models/paddleocr",
        "image": "/private/images/公开示例.png",
        "image_size": [1524, 1368],
        "device": "cuda",
        "elapsed_sec": 1.234,
        "peak_cuda_memory_gib": 2.5,
        "text": "ok\x00\ntext",
    }
    result = service.parse_inference_output(json.dumps(payload), "paddleocr", image)
    assert result == {
        "status": "success",
        "model_key": "paddleocr",
        "image": {"basename": "公开示例.png", "size": [1524, 1368]},
        "device": "cuda",
        "elapsed_sec": 1.234,
        "peak_cuda_memory_gib": 2.5,
        "text": "ok\ntext",
    }
    assert "/private" not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize("stdout", ["not json", "[]", '{"image_size": [1, 2]}'])
def test_parse_output_rejects_malformed_payload(tmp_path: Path, stdout: str) -> None:
    with pytest.raises(service.VisionInferenceError):
        service.parse_inference_output(stdout, "paddleocr", make_image(tmp_path))


def test_run_handles_timeout_nonzero_and_malformed_output(tmp_path: Path) -> None:
    image = make_image(tmp_path)
    environment = {"JINRONG_VISION_ALLOWED_ROOTS": str(image.parent)}

    def timeout_runner(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("vision", 1)

    with pytest.raises(service.VisionInferenceError, match="timed out"):
        service.run_vision_ocr(str(image), environment=environment, runner=timeout_runner)

    with pytest.raises(service.VisionInferenceError, match="failed"):
        service.run_vision_ocr(
            str(image),
            environment=environment,
            runner=lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout=""),
        )
    with pytest.raises(service.VisionInferenceError, match="malformed JSON"):
        service.run_vision_ocr(
            str(image),
            environment=environment,
            runner=lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="bad"),
        )


def test_run_constructs_bounded_subprocess_request(tmp_path: Path) -> None:
    image = make_image(tmp_path)
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    environment = {
        "JINRONG_VISION_ALLOWED_ROOTS": str(image.parent),
        "JINRONG_VISION_TIMEOUT_SECONDS": "42",
    }
    payload = {
        "image_size": [4, 5],
        "device": "cpu",
        "elapsed_sec": 0.1,
        "peak_cuda_memory_gib": None,
        "text": "ok",
    }

    def runner(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload))

    result = service.run_vision_ocr(
        str(image), "paddleocr", 10, environment=environment, runner=runner
    )
    assert result["text"] == "ok"
    assert calls[0][1]["timeout"] == 42
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["check"] is False
