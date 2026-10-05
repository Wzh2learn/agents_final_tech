from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path, PurePosixPath
from typing import Any


class ArtifactError(ValueError):
    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _require(condition: bool, code: str, **detail: object) -> None:
    if not condition:
        raise ArtifactError(code, **detail)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    digest.update(b"blob ")
    digest.update(str(path.stat().st_size).encode("ascii"))
    digest.update(b"\x00")
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, code: str) -> dict[str, Any]:
    _require(path.is_file(), code, path=str(path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactError(code, path=str(path), error=str(exc)) from exc
    _require(isinstance(value, dict), code, path=str(path))
    return value


def _parse_manifest(path: Path) -> tuple[bytes, dict[str, str]]:
    _require(path.is_file(), "manifest_missing", path=str(path))
    raw = path.read_bytes()
    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        if not raw_line:
            continue
        try:
            text = raw_line.decode("utf-8")
            digest, name = text.split("  ", 1)
        except (UnicodeError, ValueError) as exc:
            raise ArtifactError("manifest_line_invalid", path=str(path), line=line_number) from exc
        _require(len(digest) == 64 and all(char in "0123456789abcdef" for char in digest), "manifest_digest_invalid", path=str(path), line=line_number)
        relative = PurePosixPath(name)
        _require(not relative.is_absolute() and "\\" not in name and ".." not in relative.parts and name not in {"", "."}, "manifest_path_must_be_model_root_relative", path=str(path), line=line_number, name=name)
        _require(name not in entries, "manifest_duplicate_path", path=str(path), name=name)
        entries[name] = digest
    return raw, entries


def _validate_manifest(
    path: Path,
    model_dir: Path,
    expected_paths: set[str],
    code: str,
) -> dict[str, object]:
    raw, entries = _parse_manifest(path)
    aggregate = hashlib.sha256(raw).hexdigest()
    root = model_dir.resolve()
    actual_paths = set(entries)
    _require(actual_paths == expected_paths, f"{code}_path_set_mismatch", missing=sorted(expected_paths - actual_paths), extra=sorted(actual_paths - expected_paths))
    expected_lines = [f"{_sha256(model_dir / name)}  {name}" for name in sorted(expected_paths)]
    expected_raw = ("\n".join(expected_lines) + "\n").encode("utf-8")
    _require(raw == expected_raw, f"{code}_content_mismatch")
    for name, expected_digest in entries.items():
        resolved = (model_dir / name).resolve()
        _require(resolved == root or root in resolved.parents, f"{code}_path_outside_model_dir", name=name)
        _require(resolved.is_file(), f"{code}_file_missing", name=name)
        _require(_sha256(resolved) == expected_digest, f"{code}_file_hash_mismatch", name=name)
    return {
        "format": "model_root_relative_sorted_v1",
        "path": str(path),
        "aggregate_sha256": aggregate,
        "entries": len(entries),
        "status": "PASS",
    }


def _validate_safetensors_shard(path: Path, expected_keys: set[str]) -> dict[str, object]:
    _require(path.is_file(), "shard_missing", path=str(path))
    file_size = path.stat().st_size
    _require(file_size >= 8, "shard_too_small", path=str(path), size=file_size)
    with path.open("rb") as handle:
        header_length = struct.unpack("<Q", handle.read(8))[0]
        _require(header_length <= 64 * 1024 * 1024, "shard_header_too_large", path=str(path), length=header_length)
        _require(8 + header_length <= file_size, "shard_header_out_of_bounds", path=str(path), length=header_length, size=file_size)
        try:
            header = json.loads(handle.read(header_length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ArtifactError("shard_header_invalid", path=str(path), error=str(exc)) from exc
    _require(isinstance(header, dict), "shard_header_type_invalid", path=str(path))
    tensor_keys = {key for key in header if key != "__metadata__"}
    _require(tensor_keys == expected_keys, "shard_tensor_keys_mismatch", path=str(path), missing=sorted(expected_keys - tensor_keys), extra=sorted(tensor_keys - expected_keys))
    tensor_offsets: list[tuple[int, int, str]] = []
    for key in tensor_keys:
        item = header[key]
        _require(isinstance(item, dict), "shard_tensor_entry_invalid", path=str(path), key=key)
        offsets = item.get("data_offsets")
        _require(isinstance(offsets, list) and len(offsets) == 2, "shard_offsets_invalid", path=str(path), key=key)
        begin, end = offsets
        _require(isinstance(begin, int) and isinstance(end, int) and 0 <= begin < end, "shard_offset_range_invalid", path=str(path), key=key)
        tensor_offsets.append((begin, end, key))
    previous_end = 0
    for begin, end, key in sorted(tensor_offsets):
        _require(begin == previous_end, "shard_offsets_not_contiguous", path=str(path), key=key, begin=begin, previous_end=previous_end)
        previous_end = end
    data_end = previous_end
    _require(file_size == 8 + header_length + data_end, "shard_trailing_or_missing_data", path=str(path), size=file_size, expected=8 + header_length + data_end)
    return {
        "path": str(path),
        "bytes": file_size,
        "tensor_entries": len(tensor_keys),
        "header_parse": "PASS",
    }


def validate(
    metadata_path: Path,
    model_dir: Path,
    model_id: str,
    clean_manifest_path: Path,
    full_manifest_path: Path,
) -> dict[str, object]:
    metadata = _load_json(metadata_path, "metadata_invalid")
    models = metadata.get("models")
    _require(isinstance(models, list), "metadata_models_invalid")
    selected = [item for item in models if isinstance(item, dict) and item.get("id") == model_id]
    _require(len(selected) == 1, "model_id_not_unique", model_id=model_id, matches=len(selected))
    record = selected[0]
    revision = record.get("revision")
    _require(isinstance(revision, str) and len(revision) in {40, 64} and all(char in "0123456789abcdef" for char in revision), "revision_invalid", revision=revision)
    files = record.get("files")
    _require(isinstance(files, list) and bool(files), "file_metadata_missing")

    _require(model_dir.is_dir(), "model_dir_missing", path=str(model_dir))
    top_level_files = {item.name for item in model_dir.iterdir() if item.is_file()}
    expected_names = {str(item.get("name")) for item in files if isinstance(item, dict)}
    _require(len(expected_names) == len(files), "file_name_not_unique")
    _require(top_level_files == expected_names, "top_level_file_set_mismatch", missing=sorted(expected_names - top_level_files), extra=sorted(top_level_files - expected_names))

    checked: list[dict[str, object]] = []
    for item in files:
        _require(isinstance(item, dict), "file_entry_invalid")
        name = str(item["name"])
        path = model_dir / name
        expected_bytes = item.get("bytes")
        _require(path.is_file(), "file_missing", name=name)
        _require(path.stat().st_size == expected_bytes, "file_size_mismatch", name=name, actual=path.stat().st_size, expected=expected_bytes)
        content_sha256 = _sha256(path)
        lfs_sha256 = item.get("lfs_sha256")
        if lfs_sha256 is not None:
            _require(content_sha256 == lfs_sha256, "file_identity_mismatch", name=name, identity_mode="lfs_sha256", actual=content_sha256, expected=lfs_sha256)
            _require(item.get("lfs_size") == expected_bytes, "file_identity_mismatch", name=name, identity_mode="lfs_size", actual=expected_bytes, expected=item.get("lfs_size"))
            identity_mode = "lfs_sha256"
            identity_value = content_sha256
        else:
            git_blob_sha1 = _git_blob_sha1(path)
            _require(git_blob_sha1 == item.get("git_blob_sha1"), "file_identity_mismatch", name=name, identity_mode="git_blob_sha1", actual=git_blob_sha1, expected=item.get("git_blob_sha1"))
            identity_mode = "git_blob_sha1"
            identity_value = git_blob_sha1
        checked.append({"name": name, "bytes": path.stat().st_size, "identity_mode": identity_mode, "identity_value": identity_value, "content_sha256": content_sha256})

    tree_path = model_dir / ".cache" / "huggingface" / "trees" / f"{revision}.json"
    tree = _load_json(tree_path, "mirror_tree_invalid")
    tree_files = tree.get("files")
    _require(isinstance(tree_files, dict), "mirror_tree_files_invalid")
    _require(set(tree_files) == expected_names, "mirror_tree_file_set_mismatch", missing=sorted(expected_names - set(tree_files)), extra=sorted(set(tree_files) - expected_names))
    for item in files:
        name = str(item["name"])
        entry = tree_files[name]
        _require(isinstance(entry, dict), "mirror_tree_entry_invalid", name=name)
        _require(entry.get("size") == item.get("bytes"), "mirror_tree_size_mismatch", name=name)
        _require(entry.get("blob_id") == item.get("git_blob_sha1"), "mirror_tree_blob_mismatch", name=name)
        _require(entry.get("lfs_sha256") == item.get("lfs_sha256"), "mirror_tree_lfs_mismatch", name=name)
        _require(entry.get("lfs_size") == item.get("lfs_size"), "mirror_tree_lfs_size_mismatch", name=name)

    config = _load_json(model_dir / "config.json", "model_config_invalid")
    tokenizer_config = _load_json(model_dir / "tokenizer_config.json", "tokenizer_config_invalid")
    index = _load_json(model_dir / "model.safetensors.index.json", "model_index_invalid")
    weight_map = index.get("weight_map")
    _require(isinstance(weight_map, dict) and bool(weight_map), "weight_map_invalid")
    receipt = record.get("download_receipt")
    _require(isinstance(receipt, dict), "download_receipt_missing")
    expected_entries = receipt.get("model_index_weight_entries")
    _require(len(weight_map) == expected_entries, "weight_entry_count_mismatch", actual=len(weight_map), expected=expected_entries)
    shard_names = {name for name in expected_names if name.endswith(".safetensors")}
    referenced_shards = set(weight_map.values())
    _require(referenced_shards == shard_names, "weight_shard_set_mismatch", missing=sorted(shard_names - referenced_shards), extra=sorted(referenced_shards - shard_names))

    shard_receipts: list[dict[str, object]] = []
    all_tensor_keys: set[str] = set()
    for shard_name in sorted(shard_names):
        keys = {key for key, target in weight_map.items() if target == shard_name}
        shard_receipts.append(_validate_safetensors_shard(model_dir / shard_name, keys))
        all_tensor_keys.update(keys)
    _require(all_tensor_keys == set(weight_map), "weight_map_tensor_coverage_mismatch")

    license_text = (model_dir / "LICENSE").read_text(encoding="utf-8", errors="strict")
    _require("Apache License" in license_text and "Version 2.0" in license_text, "license_text_mismatch")
    _require(config.get("model_type") == "qwen3", "model_type_mismatch", actual=config.get("model_type"))
    architectures = config.get("architectures")
    _require(isinstance(architectures, list) and "Qwen3ForCausalLM" in architectures, "architecture_mismatch", actual=architectures)
    _require(tokenizer_config.get("tokenizer_class") in {"Qwen2Tokenizer", "Qwen2TokenizerFast"}, "tokenizer_class_mismatch", actual=tokenizer_config.get("tokenizer_class"))

    clean_manifest = _validate_manifest(
        clean_manifest_path,
        model_dir,
        expected_names,
        "clean_manifest",
    )
    all_cache_paths = {path.relative_to(model_dir).as_posix() for path in model_dir.rglob("*") if path.is_file()}
    full_manifest = _validate_manifest(
        full_manifest_path,
        model_dir,
        all_cache_paths,
        "full_manifest",
    )

    return {
        "record_type": "qwen_artifact_validation",
        "record_version": "qwen-artifact-validation-v1",
        "status": "PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO",
        "model_id": model_id,
        "revision": revision,
        "tokenizer_revision": revision,
        "tokenizer_identity_method": "same immutable revision bound by mirror tree metadata",
        "license": "apache-2.0",
        "model_type": config.get("model_type"),
        "architectures": architectures,
        "tokenizer_class": tokenizer_config.get("tokenizer_class"),
        "top_level_file_count": len(checked),
        "immutable_identity_checks": {
            "status": "PASS",
            "checked_files": len(checked),
            "lfs_sha256_files": sum(item["identity_mode"] == "lfs_sha256" for item in checked),
            "git_blob_sha1_files": sum(item["identity_mode"] == "git_blob_sha1" for item in checked),
        },
        "model_index": {
            "status": "PASS",
            "weight_entries": len(weight_map),
            "shards": shard_receipts,
        },
        "manifests": {
            "clean": clean_manifest,
            "legacy_download_clean_manifest_sha256": receipt.get("clean_model_files_manifest_sha256"),
            "full": full_manifest,
            "legacy_download_full_manifest_sha256": receipt.get("full_local_cache_manifest_sha256"),
        },
        "files": checked,
        "model_load_started": False,
        "model_go": False,
        "training_go": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local Qwen artifact without loading model weights")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--clean-manifest", type=Path, required=True)
    parser.add_argument("--full-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.metadata, args.model_dir, args.model_id, args.clean_manifest, args.full_manifest)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
