from pathlib import Path

from docx import Document

from research.validate_paper_claims import DEFAULT_MANIFEST, validate


def test_teacher_review_paper_satisfies_claim_manifest() -> None:
    result = validate(DEFAULT_MANIFEST)
    assert result["status"] == "PASS", result["errors"]


def test_manifest_is_repository_relative() -> None:
    manifest = DEFAULT_MANIFEST.read_text(encoding="utf-8")
    assert str(Path.home()) not in manifest


def test_teacher_review_docx_keeps_patent_gate_closed() -> None:
    docx_path = DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.docx"
    document = Document(docx_path)
    subject = document.core_properties.subject or ""
    assert "pending confirmation" in subject
    assert "gate open" not in subject

    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    for heading in ("Abstract", "1. Introduction", "7. Conclusion", "References"):
        assert heading in text
    for marker in ("TODO", "Loop D", "logs/graph/eval", "docs/experiments/"):
        assert marker not in text
