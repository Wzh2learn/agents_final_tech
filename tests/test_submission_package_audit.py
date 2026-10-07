from __future__ import annotations

import json
from pathlib import Path

from research.audit_submission_package import audit


def test_submission_package_mechanically_passes_but_is_not_ready() -> None:
    result = audit()
    assert result["mechanical_status"] == "PASS"
    assert result["submission_status"] == "PENDING_EXTERNAL_ITEMS"
    assert result["overall"] == "NOT_READY_FOR_SUBMISSION"
    assert all(item["pass"] for item in result["checks"])
    assert result["pending_external_items"] == [
        "venue_official_template_and_cfp_verification",
        "author_affiliation_and_anonymization",
        "patent_status_confirmation",
        "camera_ready_pdf_visual_acceptance",
    ]


def test_audit_checks_cover_required_artifact_contracts() -> None:
    result = audit()
    names = {item["check"] for item in result["checks"]}
    assert {
        "required_sections_source",
        "required_sections_anonymous_preview",
        "claim_tokens_source",
        "claim_tokens_anonymous_preview",
        "reference_sets",
        "anonymous_preview_forbidden_markers",
        "redaction_map_hashes",
        "readiness_hashes",
        "d_b_licence_scope",
        "reproducibility_boundary",
    } <= names
    assert result["source_sha256"] == "bb67196adbfa55c497fdd33792efe3347057ba77b9a9bf97166f300cdfff1321"
    assert result["anonymous_preview_sha256"] == "088928018006bf1311ae8400d961a81e5702978107e636c60d915d369704a0b5"


def test_audit_output_is_json_serializable(tmp_path: Path) -> None:
    result = audit()
    output = tmp_path / "audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded == result
