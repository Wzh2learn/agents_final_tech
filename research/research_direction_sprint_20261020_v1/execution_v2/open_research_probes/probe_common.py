"""Shared deterministic utilities for the DEV_ONLY mechanism probes."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
SPRINT_DIR = SCRIPT_DIR.parents[1]
CONTRACTS_PATH = SCRIPT_DIR.parent / "SPRINT_CONTRACTS.md"
CHARTER_PATH = SPRINT_DIR / "OPEN_RESEARCH_CHARTER.md"
ADJUDICATION_PATH = (
    SPRINT_DIR
    / "execution_v1"
    / "ai_semantic_adjudication_v1"
    / "ADJUDICATION.json"
)
SCOPE_TASK_PATH = (
    SPRINT_DIR / "execution_v1" / "experience_scope" / "SCOPE_TASK_DRAFT.json"
)
FIXTURE_DIR = SCRIPT_DIR / "fixtures"
RESULT_DIR = SCRIPT_DIR / "results"
INPUT_FIXTURE_PATH = FIXTURE_DIR / "probe_inputs_frozen.json"
FEEDBACK_FIXTURE_PATH = FIXTURE_DIR / "feedback_cases_frozen.json"
FREEZE_RECEIPT_PATH = FIXTURE_DIR / "FREEZE_RECEIPT.json"

PROTOCOL_VERSION = "open_research_probes_dev_v1"
KEEP_RULING = "KEEP_DEVELOPMENT"
EXPECTED_KEEP_IDS = (
    "ESD_001",
    "ESD_002",
    "ESD_003",
    "ESD_004",
    "ESD_006",
    "ESD_010",
    "ESD_012",
    "ESH_001",
    "ESH_005",
    "ESH_006",
    "ESH_007",
    "ESH_009",
    "ESH_010",
)


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object and fail loudly on malformed input."""
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize JSON deterministically for hashing and atomic output."""
    return (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def write_json_atomic(path: Path, payload: Any) -> None:
    """Write a JSON object without leaving a partial file on failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(payload)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent, suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def sha256_bytes(data: bytes) -> str:
    """Return a lowercase SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_to_script(path: Path) -> str:
    """Return a portable path relative to the probe directory."""
    return Path(os.path.relpath(path, SCRIPT_DIR)).as_posix()


def normalize_candidate_ids(value: Any) -> list[str]:
    """Normalize optional_redundant, which is string-or-list in the source."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ValueError(f"Invalid candidate ID value: {value!r}")


def normalize_sufficient_sets(value: Any) -> list[list[str]]:
    """Validate and normalize minimal sufficient sets."""
    if not isinstance(value, list) or not value:
        raise ValueError("minimal_sufficient_sets must be a non-empty list")
    normalized: list[list[str]] = []
    for candidate_set in value:
        if not isinstance(candidate_set, list) or not candidate_set:
            raise ValueError(f"Invalid sufficient set: {candidate_set!r}")
        if not all(isinstance(candidate_id, str) for candidate_id in candidate_set):
            raise ValueError(f"Invalid sufficient set: {candidate_set!r}")
        normalized.append(list(candidate_set))
    return normalized


def unique_strings(values: Iterable[str]) -> list[str]:
    """Return values in first-seen order without duplicates."""
    return list(dict.fromkeys(values))


def validate_reference(
    case: dict[str, Any],
    candidate_ids: set[str],
) -> tuple[
    list[list[str]],
    list[str],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    """Validate one adjudicated reference against its actor-visible candidates."""
    sufficient_sets = normalize_sufficient_sets(case["minimal_sufficient_sets"])
    optional_redundant = normalize_candidate_ids(case.get("optional_redundant"))
    for candidate_id in [*optional_redundant, *sum(sufficient_sets, [])]:
        if candidate_id not in candidate_ids:
            raise ValueError(
                f"{case['task_id']}: reference uses unknown candidate {candidate_id}"
            )

    sufficient_candidate_ids = set().union(*map(set, sufficient_sets))
    facts: list[dict[str, str]] = []
    contrast_anchors: list[dict[str, str]] = []
    for index, anchor in enumerate(case.get("anchors", [])):
        candidate_id = anchor.get("candidate_id")
        quote = anchor.get("quote")
        if not isinstance(candidate_id, str) or candidate_id not in candidate_ids:
            raise ValueError(f"{case['task_id']}: invalid anchor candidate")
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError(f"{case['task_id']}: invalid anchor quote")
        item = {
            "fact_id": f"anchor_{index + 1:02d}",
            "candidate_id": candidate_id,
            "quote": quote,
        }
        if candidate_id in sufficient_candidate_ids:
            facts.append(item)
        else:
            contrast_anchors.append(item)
    if not facts:
        raise ValueError(f"{case['task_id']}: reference has no supporting fact anchors")
    return sufficient_sets, optional_redundant, facts, contrast_anchors


def contains_sufficient_set(
    selected_ids: Iterable[str],
    sufficient_sets: list[list[str]],
) -> bool:
    """Return whether a selection contains at least one sufficient set."""
    selected = set(selected_ids)
    return any(set(required).issubset(selected) for required in sufficient_sets)


def covered_fact_ids(
    selected_ids: Iterable[str],
    facts: list[dict[str, str]],
) -> list[str]:
    """Return reference fact anchors covered by selected evidence."""
    selected = set(selected_ids)
    return [
        fact["fact_id"]
        for fact in facts
        if fact["candidate_id"] in selected
    ]


def verify_freeze_receipt() -> dict[str, Any]:
    """Verify that frozen fixtures still match their recorded hashes."""
    receipt = read_json(FREEZE_RECEIPT_PATH)
    for relative_path, expected_hash in receipt["fixture_sha256"].items():
        path = SCRIPT_DIR / relative_path
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Frozen fixture hash mismatch for {relative_path}: "
                f"{actual_hash} != {expected_hash}"
            )
    return receipt


def load_frozen_probe_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and hash-verify the two frozen probe fixture files."""
    verify_freeze_receipt()
    return read_json(INPUT_FIXTURE_PATH), read_json(FEEDBACK_FIXTURE_PATH)

