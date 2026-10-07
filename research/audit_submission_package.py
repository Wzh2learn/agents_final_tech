"""Audit the internal small-paper submission package without model or network calls.

Mechanical PASS means the tracked artifacts are internally consistent. It never
means the paper is ready for external submission: venue, authorship, patent and
camera-ready gates remain explicit pending items.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "paper" / "teacher_review_draft_v1.md"
ANONYMOUS = REPO / "paper" / "submission_draft_arr_www_anonymous_v0.md"
REDACTION_MAP = REPO / "paper" / "submission_redaction_map_v1.json"
CLAIM_MANIFEST = REPO / "paper" / "claim_manifest_v1.json"
SUBMISSION_REFERENCES = REPO / "paper" / "submission_references_arr_www_v1.md"
READINESS = REPO / "paper" / "submission_readiness_arr_www_v1.md"
REPRO_STATEMENT = REPO / "paper" / "reproducibility_statement_arr_www_v1.md"
LICENCE_RECORD = REPO / "docs" / "datasets" / "phase1a_licence_record_v1.json"

EXPECTED_OUTPUT_SHA256 = "088928018006bf1311ae8400d961a81e5702978107e636c60d915d369704a0b5"
EXPECTED_MAP_SHA256 = "f537d476d2ebd348995c3d57a483c57b172da32393db5ef75212f3f4988fb300"
EXPECTED_SOURCE_SHA256 = "bb67196adbfa55c497fdd33792efe3347057ba77b9a9bf97166f300cdfff1321"
EXPECTED_USES = ["training", "tuning", "evaluation", "rule_acceptance"]
EXPECTED_LICENCE_HASHES = {
    "finqa_repo_license": "92c0e67bd762c15c07ba60de09558338315a8ebf99aac4f51f487179809ac087",
    "finqa_readme": "eb86779cfed6f0a253913761d8e4fabe032a29d9fcf2944e56c23bf007064605",
    "valentine_repo_license": "f4960433bd98568685898d782e724fc28b5481be2a4b57b6280bf6e8c262e99d",
}
FORBIDDEN_PREVIEW = (
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
HASHED_PACKAGE_FILES = (
    "paper/teacher_review_draft_v1.md",
    "paper/teacher_review_draft_v1.docx",
    "paper/teacher_review_note_v2.md",
    "paper/research_story_v2.md",
    "paper/research_story_v2.docx",
    "paper/claim_manifest_v1.json",
    "paper/acceptance_report_v1.json",
    "paper/references_v0.md",
    "docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg",
    "docs/experiments/figures_paper/fig_visibility_spectrum.png",
    "paper/figures/fig_evaluate_distill_evolve_v1.svg",
    "paper/submission_references_arr_www_v1.md",
    "paper/reproducibility_statement_arr_www_v1.md",
    "paper/submission_draft_arr_www_anonymous_v0.md",
    "paper/submission_redaction_map_v1.json",
    "paper/submission_package_audit_v1.json",
    "paper/submission_review_risk_register_v1.md",
    "paper/related_work_contribution_matrix_v1.md",
    "paper/submission_language_audit_v1.md",
)


class SubmissionAuditError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_section(text: str, section: str) -> bool:
    return any(
        line.startswith("## ") and line.split(". ", 1)[-1] == section
        for line in text.splitlines()
    ) or f"## {section}" in text


def _reference_ids(text: str) -> set[str]:
    tail = text.split("## References", 1)[-1]
    return set(re.findall(r"arXiv:([0-9.]+)", tail))


def _map_reference_ids(text: str) -> set[str]:
    table = text.split("## 1 主稿引用映射", 1)[-1].split("## 2", 1)[0]
    return set(re.findall(r"arXiv:([0-9.]+)", table))


def _bib_keys(text: str) -> set[str]:
    return set(re.findall(r"@article\{([^,]+)", text))


def _check(name: str, passed: bool, detail: object) -> dict[str, object]:
    return {"check": name, "pass": bool(passed), "detail": detail}


def audit() -> dict[str, object]:
    source_text = SOURCE.read_text(encoding="utf-8")
    anonymous_text = ANONYMOUS.read_text(encoding="utf-8")
    claim_manifest = json.loads(CLAIM_MANIFEST.read_text(encoding="utf-8"))
    redaction_map = json.loads(REDACTION_MAP.read_text(encoding="utf-8"))
    references_text = SUBMISSION_REFERENCES.read_text(encoding="utf-8")
    readiness_text = READINESS.read_text(encoding="utf-8")
    licence = json.loads(LICENCE_RECORD.read_text(encoding="utf-8"))

    checks: list[dict[str, object]] = []
    required_sections = claim_manifest["required_sections"]
    source_sections = {section: _has_section(source_text, section) for section in required_sections}
    preview_sections = {section: _has_section(anonymous_text, section) for section in required_sections}
    checks.append(_check("required_sections_source", all(source_sections.values()), source_sections))
    checks.append(_check("required_sections_anonymous_preview", all(preview_sections.values()), preview_sections))

    missing_source_tokens = [
        (claim["id"], token)
        for claim in claim_manifest["claims"]
        for token in claim["manuscript_tokens"]
        if token not in source_text
    ]
    missing_preview_tokens = [
        (claim["id"], token)
        for claim in claim_manifest["claims"]
        for token in claim["manuscript_tokens"]
        if token not in anonymous_text
    ]
    checks.append(_check("claim_tokens_source", not missing_source_tokens, missing_source_tokens))
    checks.append(_check("claim_tokens_anonymous_preview", not missing_preview_tokens, missing_preview_tokens))

    main_refs = _reference_ids(source_text)
    map_refs = _map_reference_ids(references_text)
    bib_keys = _bib_keys(references_text)
    checks.append(_check(
        "reference_sets",
        len(main_refs) == 15 and main_refs == map_refs and len(bib_keys) == 15,
        {"main": len(main_refs), "map": len(map_refs), "bib": len(bib_keys),
         "map_only": sorted(map_refs - main_refs), "main_only": sorted(main_refs - map_refs)},
    ))

    preview_forbidden = [marker for marker in FORBIDDEN_PREVIEW if marker in anonymous_text]
    checks.append(_check("anonymous_preview_forbidden_markers", not preview_forbidden, preview_forbidden))
    checks.append(_check(
        "redaction_map_hashes",
        _sha256(SOURCE) == EXPECTED_SOURCE_SHA256
        and _sha256(ANONYMOUS) == EXPECTED_OUTPUT_SHA256
        and _sha256(REDACTION_MAP) == EXPECTED_MAP_SHA256
        and redaction_map["source_sha256"] == EXPECTED_SOURCE_SHA256
        and redaction_map["output_path"] == "paper/submission_draft_arr_www_anonymous_v0.md",
        {"source": _sha256(SOURCE), "preview": _sha256(ANONYMOUS), "map": _sha256(REDACTION_MAP)},
    ))

    missing_hashes = [
        relative for relative in HASHED_PACKAGE_FILES
        if _sha256(REPO / relative) not in readiness_text
    ]
    checks.append(_check("readiness_hashes", not missing_hashes, missing_hashes))

    licence_ok = (
        licence["status"] == "accepted"
        and licence["accepted_by"] == "Wzh"
        and licence["permitted_uses"] == EXPECTED_USES
        and licence["covered_artifact_sha256"] == EXPECTED_LICENCE_HASHES
        and licence["scope"]["not_granted"] == [
            "redistribution", "public_release", "commercial_use",
            "other_data_sources", "other_licence_interpretations",
        ]
    )
    checks.append(_check("d_b_licence_scope", licence_ok, licence["covered_artifact_sha256"]))

    repro_ok = (
        "phase1a_licence_record_v1.json" in REPRO_STATEMENT.read_text(encoding="utf-8")
        and "不外发" in REPRO_STATEMENT.read_text(encoding="utf-8")
    )
    checks.append(_check("reproducibility_boundary", repro_ok, repro_ok))

    mechanical_pass = all(item["pass"] for item in checks)
    result = {
        "schema_version": 1,
        "audit_type": "submission-package-integrity",
        "mechanical_status": "PASS" if mechanical_pass else "FAIL",
        "submission_status": "PENDING_EXTERNAL_ITEMS",
        "overall": "NOT_READY_FOR_SUBMISSION" if mechanical_pass else "MECHANICAL_FAILURE",
        "checks": checks,
        "pending_external_items": [
            "venue_official_template_and_cfp_verification",
            "author_affiliation_and_anonymization",
            "patent_status_confirmation",
            "camera_ready_pdf_visual_acceptance",
        ],
        "source_sha256": _sha256(SOURCE),
        "anonymous_preview_sha256": _sha256(ANONYMOUS),
        "redaction_map_sha256": _sha256(REDACTION_MAP),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "mechanical_status": result["mechanical_status"],
        "submission_status": result["submission_status"],
        "checks_passed": sum(item["pass"] for item in result["checks"]),
        "checks_total": len(result["checks"]),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if result["mechanical_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
