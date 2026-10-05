from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


class SnapshotError(ValueError):
    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _require(condition: bool, code: str, **detail: object) -> None:
    if not condition:
        raise SnapshotError(code, **detail)


def _load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(code, path=str(path), error=str(exc)) from exc
    _require(isinstance(value, dict), code, path=str(path))
    return value


def _allowed_file_names(metadata: dict[str, Any], model_id: str) -> list[str]:
    models = metadata.get("models")
    _require(isinstance(models, list), "metadata_models_invalid")
    selected = [item for item in models if isinstance(item, dict) and item.get("id") == model_id]
    _require(len(selected) == 1, "model_id_not_unique", model_id=model_id, matches=len(selected))
    files = selected[0].get("files")
    _require(isinstance(files, list) and bool(files), "file_metadata_missing")
    names: list[str] = []
    for item in files:
        _require(isinstance(item, dict), "file_entry_invalid")
        name = item.get("name")
        _require(isinstance(name, str) and name == Path(name).name and name not in {"", ".", ".."}, "file_name_invalid", name=name)
        _require(name not in names, "file_name_duplicate", name=name)
        names.append(name)
    return names


def download(
    metadata_path: Path,
    model_id: str,
    revision: str,
    endpoint: str,
    target: Path,
) -> dict[str, object]:
    metadata = _load_json(metadata_path, "metadata_invalid")
    names = _allowed_file_names(metadata, model_id)
    revision = revision.lower()
    _require(len(revision) == 40 and all(char in "0123456789abcdef" for char in revision), "revision_invalid", revision=revision)
    _require(endpoint == "https://hf-mirror.com", "endpoint_not_approved", endpoint=endpoint)
    _require(not target.exists() or (target.is_dir() and not any(target.iterdir())), "target_not_empty", target=str(target))

    os.environ["HF_ENDPOINT"] = endpoint
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=model_id,
        revision=revision,
        local_dir=str(target),
        allow_patterns=names,
        token=False,
        max_workers=4,
    )
    actual_names = {item.name for item in target.iterdir() if item.is_file()}
    expected_names = set(names)
    _require(actual_names == expected_names, "top_level_file_set_mismatch", missing=sorted(expected_names - actual_names), extra=sorted(actual_names - expected_names))
    return {
        "record_type": "hf_snapshot_download",
        "record_version": "hf-snapshot-download-v1",
        "status": "DOWNLOADED_NOT_VALIDATED",
        "model_id": model_id,
        "revision": revision,
        "endpoint": endpoint,
        "token_sent": False,
        "hf_hub_disable_xet": True,
        "hf_hub_enable_hf_transfer": False,
        "target": str(target),
        "allowlist": names,
        "top_level_file_count": len(actual_names),
        "model_load_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Download an exact Hugging Face snapshot without using or sending a token")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--endpoint", default="https://hf-mirror.com")
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = download(args.metadata, args.model_id, args.revision, args.endpoint, args.target)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
