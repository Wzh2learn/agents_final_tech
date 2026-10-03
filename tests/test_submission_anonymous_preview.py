from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.build_submission_anonymous_preview import (
    DEFAULT_SOURCE,
    anonymize,
    build,
)

REPO = Path(__file__).resolve().parents[1]
TRACKED_OUTPUT = REPO / "paper" / "submission_draft_arr_www_anonymous_v0.md"
TRACKED_MAP = REPO / "paper" / "submission_redaction_map_v1.json"
TRACKED_OUTPUT_SHA256 = "9d4edf42eba194fc6959e685483336755d547f7460b0fafc507bb7e7e2ab4d39"
TRACKED_MAP_SHA256 = "36114ceb6fd6a19f75f436f5d0f20f901a4afd3b88fd10dd4e8faff4cb34f678"
FORBIDDEN = (
    "logs/graph",
    "docs/experiments",
    "data/research",
    "scripts/",
    "127.0.0.1",
    "Qwen3.6",
    "GGUF",
    "GB10",
    "Loop D",
    "patent-status",
    "Author and affiliation are to be filled in",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_anonymous_preview_removes_internal_identity() -> None:
    source = DEFAULT_SOURCE.read_text(encoding="utf-8")
    output, redactions = anonymize(source)

    for marker in FORBIDDEN:
        assert marker not in output, marker
    assert "Anonymous submission-source preview" in output
    for section in ("## Abstract", "## 1. Introduction", "## 2. Related Work",
                    "## 3. Method", "## 4. Experimental Setup", "## 5. Results",
                    "## 6. Discussion and Limitations", "## 7. Conclusion",
                    "## References"):
        assert section in output, section
    assert sum(int(item["count"]) for item in redactions["redactions"]) >= 10


def test_claim_tokens_survive_redaction() -> None:
    source = DEFAULT_SOURCE.read_text(encoding="utf-8")
    output, _ = anonymize(source)
    manifest = json.loads((REPO / "paper" / "claim_manifest_v1.json").read_text(encoding="utf-8"))

    for claim in manifest["claims"]:
        for token in claim["manuscript_tokens"]:
            assert token in output, (claim["id"], token)


def test_double_build_is_byte_identical_and_source_unchanged(tmp_path: Path) -> None:
    source_hash = _sha256(DEFAULT_SOURCE)
    output = tmp_path / "submission_preview.md"
    map_output = tmp_path / "redaction_map.json"

    first = build(DEFAULT_SOURCE, output, map_output)
    first_output = output.read_bytes()
    first_map = map_output.read_bytes()
    second = build(DEFAULT_SOURCE, output, map_output)

    assert first == second
    assert output.read_bytes() == first_output
    assert map_output.read_bytes() == first_map
    assert _sha256(DEFAULT_SOURCE) == source_hash
    assert first["source_sha256"] == source_hash


def test_redaction_map_records_expected_paths(tmp_path: Path) -> None:
    output = tmp_path / "submission_preview.md"
    map_output = tmp_path / "redaction_map.json"
    build(DEFAULT_SOURCE, output, map_output)
    redaction_map = json.loads(map_output.read_text(encoding="utf-8"))

    labels = {item["label"]: item["count"] for item in redaction_map["redactions"]}
    assert labels["internal_status_header"] == 1
    assert labels["figure_1_path"] == 1
    assert labels["figure_2_path"] == 1
    assert labels["judge_model_endpoint"] == 1
    assert labels["source_artifact"] == 1
    assert labels["injection_artifact"] == 1


def test_tracked_preview_matches_generator() -> None:
    source = DEFAULT_SOURCE.read_text(encoding="utf-8")
    expected_text, expected_map = anonymize(source)
    assert TRACKED_OUTPUT.read_text(encoding="utf-8") == expected_text
    assert _sha256(TRACKED_OUTPUT) == TRACKED_OUTPUT_SHA256
    assert _sha256(TRACKED_MAP) == TRACKED_MAP_SHA256

    tracked_map = json.loads(TRACKED_MAP.read_text(encoding="utf-8"))
    assert tracked_map["source_sha256"] == _sha256(DEFAULT_SOURCE)
    assert tracked_map["output_path"] == "paper/submission_draft_arr_www_anonymous_v0.md"
    assert tracked_map["redactions"] == expected_map["redactions"]
