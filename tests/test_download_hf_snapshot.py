from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.download_hf_snapshot import SnapshotError, download


def _metadata(names: list[str]) -> dict[str, object]:
    return {
        "models": [
            {
                "id": "Qwen/Test",
                "revision": "a" * 40,
                "files": [{"name": name} for name in names],
            }
        ]
    }


def test_nonempty_target_fails_before_network(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps(_metadata(["config.json"])), encoding="utf-8")
    target = tmp_path / "target"
    target.mkdir()
    (target / "existing").write_text("keep", encoding="ascii")
    with pytest.raises(SnapshotError) as exc:
        download(metadata, "Qwen/Test", "a" * 40, "https://hf-mirror.com", target)
    assert exc.value.code == "target_not_empty"


def test_unapproved_endpoint_fails_before_network(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps(_metadata(["config.json"])), encoding="utf-8")
    with pytest.raises(SnapshotError) as exc:
        download(metadata, "Qwen/Test", "a" * 40, "https://huggingface.co", tmp_path / "target")
    assert exc.value.code == "endpoint_not_approved"


def test_nested_allowlist_name_fails_closed(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps(_metadata(["nested/config.json"])), encoding="utf-8")
    with pytest.raises(SnapshotError) as exc:
        download(metadata, "Qwen/Test", "a" * 40, "https://hf-mirror.com", tmp_path / "target")
    assert exc.value.code == "file_name_invalid"
