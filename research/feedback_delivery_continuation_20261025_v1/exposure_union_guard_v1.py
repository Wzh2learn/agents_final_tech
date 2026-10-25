"""Pre-generation guard against already exposed task and source identities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class ExposureOverlapError(RuntimeError):
    """Raised when a confirmation selection intersects the exposure union."""


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    value = json.loads(text)
    return value if isinstance(value, list) else [value]


def identity_values(value: Any) -> set[str]:
    output: set[str] = set()
    if isinstance(value, dict):
        for key in ("task_id", "source_task_id", "base_instance_id", "question_uid", "table_uid"):
            item = value.get(key)
            if item:
                text = str(item)
                output.add(text)
                output.add(text.split("::", 1)[0])
        for key in ("selected_task_ids", "selected_table_uids", "task_ids", "source_keys"):
            items = value.get(key)
            if isinstance(items, list):
                output.update(str(item) for item in items if item)
    elif isinstance(value, list):
        for item in value:
            output.update(identity_values(item))
    return output


def load_exposure_union(manifest_path: Path) -> tuple[set[str], list[dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    union: set[str] = set()
    receipts = []
    for source in manifest["sources"]:
        path = Path(source["path"])
        if not path.exists():
            raise FileNotFoundError(path)
        identities = set()
        for row in load_json_or_jsonl(path):
            identities.update(identity_values(row))
        union.update(identities)
        receipts.append({
            "path": str(path),
            "role": source["role"],
            "identity_count": len(identities),
        })
    return union, receipts


def check_exposure(
    selected_task_ids: Iterable[str],
    selected_table_uids: Iterable[str],
    manifest_path: Path,
    *,
    allow_development_exposure: bool,
) -> dict[str, Any]:
    selected = {str(item).split("::", 1)[0] for item in selected_task_ids}
    selected.update(str(item) for item in selected_table_uids if item)
    union, source_receipts = load_exposure_union(manifest_path)
    overlap = sorted(selected & union)
    receipt = {
        "schema": "exposure_union_guard_v1",
        "manifest_path": str(manifest_path),
        "selected_identity_count": len(selected),
        "exposure_identity_count": len(union),
        "overlap_count": len(overlap),
        "overlap": overlap,
        "allow_development_exposure": allow_development_exposure,
        "sources": source_receipts,
    }
    if overlap and not allow_development_exposure:
        raise ExposureOverlapError(
            f"confirmation_selection_overlaps_exposure_union:{overlap[:8]}"
        )
    return receipt


def assert_unexposed_for_confirmation(
    selected_task_ids: Iterable[str],
    selected_table_uids: Iterable[str],
    manifest_path: Path,
) -> dict[str, Any]:
    return check_exposure(
        selected_task_ids,
        selected_table_uids,
        manifest_path,
        allow_development_exposure=False,
    )
