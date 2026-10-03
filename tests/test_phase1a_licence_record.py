from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "docs" / "datasets" / "phase1a_licence_record_v1.json"
EVIDENCE = REPO / "docs" / "datasets" / "2026-09-24_dB_licence_evidence.md"

EXPECTED_KEYS = {
    "record_type",
    "record_version",
    "status",
    "accepted_by",
    "accepted_at",
    "permitted_uses",
    "covered_artifact_sha256",
    "covered_artifacts",
    "scope",
    "evidence_ref",
    "data_boundary",
}
EXPECTED_USES = ["training", "tuning", "evaluation", "rule_acceptance"]
EXPECTED_HASHES = {
    "finqa_repo_license": "92c0e67bd762c15c07ba60de09558338315a8ebf99aac4f51f487179809ac087",
    "finqa_readme": "eb86779cfed6f0a253913761d8e4fabe032a29d9fcf2944e56c23bf007064605",
    "valentine_repo_license": "f4960433bd98568685898d782e724fc28b5481be2a4b57b6280bf6e8c262e99d",
}
EXPECTED_NOT_GRANTED = [
    "redistribution",
    "public_release",
    "commercial_use",
    "other_data_sources",
    "other_licence_interpretations",
]
EXPECTED_RECORD_SHA256 = "57592fa141806d83791bb13a8b110edc0a007f0003279c80a949b6e8a85dd8d8"


def _record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_licence_record_identity_and_time_are_real() -> None:
    record = _record()
    assert set(record) == EXPECTED_KEYS
    assert record["record_type"] == "phase1a_licence_record"
    assert record["record_version"] == "phase1a-licence-record-v1"
    assert record["status"] == "accepted"
    assert record["accepted_by"] == "Wzh"

    accepted_at = datetime.fromisoformat(record["accepted_at"].replace("Z", "+00:00"))
    assert accepted_at.tzinfo is not None
    assert accepted_at.utcoffset() == timezone.utc.utcoffset(None)
    assert record["accepted_at"] == "2026-10-03T17:01:42Z"
    assert record["accepted_by"] not in {"fixture-user", "data-owner"}
    assert "PENDING" not in RECORD.read_text(encoding="utf-8")


def test_permitted_uses_are_exact_and_not_expanded() -> None:
    record = _record()
    assert record["permitted_uses"] == EXPECTED_USES
    assert record["scope"]["not_granted"] == EXPECTED_NOT_GRANTED
    assert set(record["permitted_uses"]).isdisjoint(EXPECTED_NOT_GRANTED)


def test_covered_hashes_are_db_annex_only() -> None:
    record = _record()
    assert record["covered_artifact_sha256"] == EXPECTED_HASHES
    assert set(record["covered_artifact_sha256"]) == set(EXPECTED_HASHES)
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in EXPECTED_HASHES.values())

    covered_ids = {item["id"] for item in record["covered_artifacts"]}
    assert covered_ids == set(EXPECTED_HASHES)
    assert covered_ids.isdisjoint({
        "source_tables",
        "schema",
        "injection_map",
        "label_ledger",
        "learnability_feature_ledger",
        "convfinqa",
    })
    assert record["evidence_ref"] == "docs/datasets/2026-09-24_dB_licence_evidence.md"
    assert EVIDENCE.is_file()


def test_data_boundary_does_not_authorise_new_downloads() -> None:
    record = _record()
    assert record["data_boundary"] == {
        "d_c_minimal_download_completed": True,
        "new_downloads_authorized": False,
        "q3_three_file_allowlist_is_downstream_only": True,
    }


def test_formal_record_is_byte_stable() -> None:
    assert hashlib.sha256(RECORD.read_bytes()).hexdigest() == EXPECTED_RECORD_SHA256
