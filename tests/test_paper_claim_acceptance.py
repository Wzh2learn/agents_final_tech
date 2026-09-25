import json
from pathlib import Path
import re

from docx import Document

from research.build_teacher_review_docx import build

from research.validate_paper_claims import DEFAULT_MANIFEST, validate


def test_teacher_review_paper_satisfies_claim_manifest() -> None:
    result = validate(DEFAULT_MANIFEST)
    assert result["status"] == "PASS", result["errors"]


def test_ocr_visibility_wording_matches_stored_evidence() -> None:
    root = DEFAULT_MANIFEST.parent.parent
    evidence = json.loads((root / "logs/graph/eval/checkpoint_discrimination_tables_v2.json").read_text())
    ocr = evidence["by_type"]["ocr_similar"]
    assert (ocr["n_visible"], ocr["n_injections"], ocr["n_absorbed"]) == (0, 13, 13)
    markdown = (DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.md").read_text()
    docx = Document(DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.docx")
    for text in (markdown, "\n".join(p.text for p in docx.paragraphs)):
        assert re.search(r"OCR-like perturbations are visible in 0/13 cases", text)
        assert "invisible in 0/13" not in text


def test_acceptance_rejects_reversed_visibility_claim(tmp_path) -> None:
    manifest = json.loads(DEFAULT_MANIFEST.read_text())
    source = (DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.md").read_text()
    broken = tmp_path / "broken.md"
    broken.write_text(source.replace("are visible in 0/13 cases", "are invisible in 0/13 cases"))
    manifest["paper"] = str(broken)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    assert validate(path)["status"] == "FAIL"


def test_audit_records_are_mechanically_checked() -> None:
    result = validate(DEFAULT_MANIFEST)
    assert result["status"] == "PASS", result["errors"]
    audit_checks = [c for c in result["checks"] if ":audit_record:" in str(c["check"])]
    assert len(audit_checks) == 5
    assert all(c["pass"] for c in audit_checks)


def test_acceptance_rejects_dangling_audit_record(tmp_path) -> None:
    manifest = json.loads(DEFAULT_MANIFEST.read_text())
    for claim in manifest["claims"]:
        if claim["id"] == "SP-C5":
            claim["audit_records"] = ["docs/experiments/does_not_exist_audit.md"]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    result = validate(path)
    assert result["status"] == "FAIL"
    assert any("missing audit record" in error for error in result["errors"])


def test_evaluation_docx_matches_current_source(tmp_path) -> None:
    source = DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.md"
    current = Document(DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.docx")
    rebuilt = Document(build(source=source, output=tmp_path / "rebuilt.docx"))
    assert [p.text for p in current.paragraphs] == [p.text for p in rebuilt.paragraphs]
    assert [[c.text for r in t.rows for c in r.cells] for t in current.tables] == [
        [c.text for r in t.rows for c in r.cells] for t in rebuilt.tables]


def test_table_protocol_labels_do_not_reuse_full_tree_leaf_counts() -> None:
    text = (DEFAULT_MANIFEST.parent / "teacher_review_draft_v1.md").read_text()
    assert "| Detection signal |" in text
    assert "| Flat | Field-hit-rate drop |" in text
    assert "| Hierarchical, expert weights | Pruned parsing-root drop |" in text
    assert "| 12 leaves |" not in text


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
