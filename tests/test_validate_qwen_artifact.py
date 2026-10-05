from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import pytest

from research.validate_qwen_artifact import ArtifactError, validate


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def _write_manifest(path: Path, model_dir: Path, names: list[str]) -> str:
    lines = [f"{hashlib.sha256((model_dir / name).read_bytes()).hexdigest()}  {name}" for name in names]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, str]:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(json.dumps({"model_type": "qwen3", "architectures": ["Qwen3ForCausalLM"]}), encoding="utf-8")
    (model_dir / "tokenizer_config.json").write_text(json.dumps({"tokenizer_class": "Qwen2Tokenizer"}), encoding="utf-8")
    (model_dir / "LICENSE").write_text("Apache License Version 2.0\n", encoding="utf-8")

    header = {"weight": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}}
    header_raw = json.dumps(header, separators=(",", ":")).encode("utf-8")
    shard = model_dir / "model.safetensors"
    shard.write_bytes(struct.pack("<Q", len(header_raw)) + header_raw + struct.pack("<f", 1.0))
    index = {"metadata": {"total_size": 4}, "weight_map": {"weight": "model.safetensors"}}
    (model_dir / "model.safetensors.index.json").write_text(json.dumps(index), encoding="utf-8")

    revision = "a" * 40
    tree_dir = model_dir / ".cache" / "huggingface" / "trees"
    tree_dir.mkdir(parents=True)
    names = ["config.json", "tokenizer_config.json", "LICENSE", "model.safetensors", "model.safetensors.index.json"]
    tree_files = {}
    file_entries = []
    for name in names:
        path = model_dir / name
        entry = {"size": path.stat().st_size, "blob_id": _git_blob_sha1(path)}
        if name == "model.safetensors":
            entry["lfs_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            entry["lfs_size"] = path.stat().st_size
        tree_files[name] = entry
        metadata_entry = {
            "name": name,
            "bytes": path.stat().st_size,
            "git_blob_sha1": entry["blob_id"],
            "lfs_sha256": entry.get("lfs_sha256"),
            "lfs_size": entry.get("lfs_size"),
        }
        file_entries.append(metadata_entry)
    (tree_dir / f"{revision}.json").write_text(json.dumps({"format_version": 1, "files": tree_files}), encoding="utf-8")

    clean_manifest = tmp_path / "clean.sha256"
    all_names = sorted(path.relative_to(model_dir).as_posix() for path in model_dir.rglob("*") if path.is_file())
    full_manifest = tmp_path / "full.sha256"
    full_hash = _write_manifest(full_manifest, model_dir, all_names)
    names = sorted(names)
    clean_hash = _write_manifest(clean_manifest, model_dir, names)

    metadata = {
        "models": [
            {
                "id": "Qwen/Test",
                "revision": revision,
                "files": file_entries,
                "download_receipt": {
                    "clean_model_files_manifest_sha256": clean_hash,
                    "full_local_cache_manifest_sha256": full_hash,
                    "model_index_weight_entries": 1,
                },
            }
        ]
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return metadata_path, model_dir, clean_manifest, full_manifest, revision


def test_artifact_validation_passes_without_loading_model(tmp_path: Path) -> None:
    metadata, model_dir, clean, full, revision = _build_fixture(tmp_path)
    report = validate(metadata, model_dir, "Qwen/Test", clean, full)
    assert report["status"] == "PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO"
    assert report["revision"] == revision
    assert report["immutable_identity_checks"]["checked_files"] == 5
    assert report["model_index"]["weight_entries"] == 1
    assert report["model_load_started"] is False
    assert report["model_go"] is False


def test_tampered_shard_fails_closed(tmp_path: Path) -> None:
    metadata, model_dir, clean, full, _ = _build_fixture(tmp_path)
    shard = model_dir / "model.safetensors"
    data = bytearray(shard.read_bytes())
    data[-1] ^= 1
    shard.write_bytes(data)
    with pytest.raises(ArtifactError) as exc:
        validate(metadata, model_dir, "Qwen/Test", clean, full)
    assert exc.value.code == "file_identity_mismatch"


def test_extra_top_level_file_fails_closed(tmp_path: Path) -> None:
    metadata, model_dir, clean, full, _ = _build_fixture(tmp_path)
    (model_dir / "unexpected.txt").write_text("unexpected", encoding="ascii")
    with pytest.raises(ArtifactError) as exc:
        validate(metadata, model_dir, "Qwen/Test", clean, full)
    assert exc.value.code == "top_level_file_set_mismatch"


@pytest.mark.parametrize("bad_name", ["../outside.txt", "/tmp/outside.txt", "nested/../../outside.txt"])
def test_manifest_path_escape_fails_closed(tmp_path: Path, bad_name: str) -> None:
    metadata, model_dir, clean, full, _ = _build_fixture(tmp_path)
    clean.write_text(f"{'0' * 64}  {bad_name}\n", encoding="utf-8")
    with pytest.raises(ArtifactError) as exc:
        validate(metadata, model_dir, "Qwen/Test", clean, full)
    assert exc.value.code == "manifest_path_must_be_model_root_relative"


def test_weight_map_missing_tensor_fails_closed(tmp_path: Path) -> None:
    metadata, model_dir, clean, full, _ = _build_fixture(tmp_path)
    index_path = model_dir / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["weight_map"] = {"missing": "model.safetensors"}
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(ArtifactError) as exc:
        validate(metadata, model_dir, "Qwen/Test", clean, full)
    assert exc.value.code in {"file_size_mismatch", "file_identity_mismatch"}
