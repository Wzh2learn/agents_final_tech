from pathlib import Path
from xml.etree import ElementTree

from docx import Document


REPO = Path(__file__).resolve().parents[1]
STORY = REPO / "paper" / "research_story_v2.md"
FIGURE = REPO / "paper" / "figures" / "fig_evaluate_distill_evolve_v1.svg"
DIRECTION_DOCX = REPO / "paper" / "research_story_v2.docx"


def test_three_stage_story_preserves_evidence_boundaries() -> None:
    text = STORY.read_text(encoding="utf-8")
    for stage in ("Stage E", "Stage D", "Stage R"):
        assert stage in text
    assert "不是蒸馏结果" in text
    assert "没有学生模型训练" in text
    assert "不主张已获得稳定显著净收益" in text


def test_three_stage_figure_is_valid_and_self_describing() -> None:
    root = ElementTree.parse(FIGURE).getroot()
    assert root.tag.endswith("svg")
    text = " ".join(element.text or "" for element in root.iter())
    for label in ("E · Evaluate", "D · Distill", "R · Evolve rules"):
        assert label in text
    assert "TRAINING RESULT MISSING" in text
    assert "MECHANISM EVIDENCE ONLY" in text


def test_teacher_direction_docx_contains_three_stage_summary() -> None:
    document = Document(DIRECTION_DOCX)
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    text += "\n" + "\n".join(
        cell.text for table in document.tables for row in table.rows for cell in row.cells
    )
    for label in ("E · Evaluate", "D · Distill", "R · Evolve rules"):
        assert label in text
    subject = document.core_properties.subject or ""
    assert "pending confirmation" in subject
    assert "gate open" not in subject
    assert document.core_properties.comments == (
        "Generated offline from paper/research_story_v2.md"
    )
