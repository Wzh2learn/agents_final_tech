from pathlib import Path
import re
from xml.etree import ElementTree

from docx import Document

from research.build_teacher_review_docx import build


REPO = Path(__file__).resolve().parents[1]
STORY = REPO / "paper" / "research_story_v2.md"
FIGURE = REPO / "paper" / "figures" / "fig_evaluate_distill_evolve_v1.svg"
DIRECTION_DOCX = REPO / "paper" / "research_story_v2.docx"
THEORY = REPO / "paper" / "method_theory_materials_v1.md"
DATA_PROTOCOL = REPO / "paper" / "dataset_protocol_v1.md"
METHOD_BIB = REPO / "paper" / "method_data_references_v1.bib"
RULE_FIGURE = REPO / "paper" / "figures" / "fig_rule_gate_replay_v1.svg"
STAGES = ("E · Evaluate", "D · Distill", "R · Evolve rules")


def _assert_current_three_stage_summary(text: str) -> None:
    for label in (
        *STAGES,
        "8B rule-candidate policy",
        "4B: training smoke only",
        "candidate proposal/prescreen",
        "final deterministic gate",
        "gate-validation not sealed test",
        "TRAINING RESULT MISSING",
        "MECHANISM EVIDENCE ONLY",
    ):
        assert label in text, f"Missing current role/boundary: {label}"
    for stale_label in (
        "Train 4B/8B student",
        "Train 4B / 8B student",
        "process policy or verifier",
        "Filter teacher traces",
        "SFT + preference learning",
    ):
        assert stale_label not in text


def _assert_direction_docx_summary(document) -> None:
    summaries = [
        table for table in document.tables
        if tuple(cell.text for cell in table.rows[0].cells) == STAGES
    ]
    assert len(summaries) == 1
    # Inspect the native figure table, so current body prose cannot mask drift.
    text = "\n".join(cell.text for row in summaries[0].rows for cell in row.cells)
    _assert_current_three_stage_summary(text)
    assert any(paragraph.text.startswith("Target loop:") for paragraph in document.paragraphs)
    subject = document.core_properties.subject or ""
    assert "patent" in subject
    assert "pending confirmation" in subject
    assert "gate open" not in subject
    assert document.core_properties.comments == (
        "Generated offline from paper/research_story_v2.md"
    )


def test_three_stage_story_preserves_evidence_boundaries() -> None:
    text = STORY.read_text(encoding="utf-8")
    for stage in ("Stage E", "Stage D", "Stage R"):
        assert stage in text
    assert "不是蒸馏结果" in text
    assert "没有学生模型训练" in text
    assert "不主张已获得稳定显著净收益" in text


def test_build_story_docx_preserves_current_roles_and_markdown_body(tmp_path: Path) -> None:
    output = tmp_path / "research_story_v2.docx"
    assert build(source=STORY, output=output) == output
    document = Document(output)
    _assert_direction_docx_summary(document)

    # Compare narrative paragraphs with the source, not a second route/config.
    source_lines = STORY.read_text(encoding="utf-8").splitlines()
    body_lines = [
        line for line in source_lines
        if line.strip() and not re.match(r"^(?:[#>!|*\-]|\d+\. )", line)
    ]
    assert body_lines
    paragraphs = {paragraph.text for paragraph in document.paragraphs}
    assert source_lines[0].removeprefix("# ") in paragraphs
    for line in body_lines:
        assert re.sub(r"[*`]", "", line) in paragraphs


def test_three_stage_figure_is_valid_and_self_describing() -> None:
    root = ElementTree.parse(FIGURE).getroot()
    assert root.tag.endswith("svg")
    # Required labels must be visible, not hidden solely in the SVG description.
    text = " ".join(
        "".join(element.itertext())
        for element in root.findall(".//{http://www.w3.org/2000/svg}text")
    )
    _assert_current_three_stage_summary(text)
    assert "Target loop:" in text


def test_teacher_direction_docx_contains_three_stage_summary(tmp_path: Path) -> None:
    document = Document(DIRECTION_DOCX)
    _assert_direction_docx_summary(document)
    regenerated = Document(build(source=STORY, output=tmp_path / "current.docx"))
    assert [paragraph.text for paragraph in document.paragraphs] == [
        paragraph.text for paragraph in regenerated.paragraphs
    ]
    assert [[cell.text for row in table.rows for cell in row.cells] for table in document.tables] == [
        [cell.text for row in table.rows for cell in row.cells] for table in regenerated.tables
    ]


def test_method_materials_keep_theory_and_evidence_boundaries() -> None:
    text = THEORY.read_text(encoding="utf-8")
    for required in (
        "Risk}(\\tau)",
        "Delta_s",
        "Delta_p",
        "Delta_g",
        "命题 1",
        "命题 2",
        "只能支持第一个累计局部界",
        "arXiv:1506.02629",
        "不能声称已有 conformal guarantee",
        "不等价于在线学习收敛",
    ):
        assert required in text


def test_dataset_protocol_separates_quality_from_experiment_role() -> None:
    text = DATA_PROTOCOL.read_text(encoding="utf-8")
    for required in (
        "Q3 是标签质量，不是“测试集”",
        "proposal/train",
        "gate-validation",
        "sealed test",
        "future replay",
        "HISTORICAL_ONLY",
        "TAT-DQA 继续冻结",
        "不下载 PubTables-1M",
    ):
        assert required in text


def test_method_bibliography_has_unique_verified_keys() -> None:
    text = METHOD_BIB.read_text(encoding="utf-8")
    keys = re.findall(r"@article\{([^,]+),", text)
    assert len(keys) == 17
    assert len(keys) == len(set(keys))
    for arxiv_id in (
        "1705.08500",
        "2208.02814",
        "1506.02629",
        "1503.02531",
        "2305.20050",
        "2105.07624",
        "2109.00122",
        "2206.01347",
    ):
        assert arxiv_id in text


def test_rule_gate_figure_is_valid_and_keeps_data_firewall_visible() -> None:
    root = ElementTree.parse(RULE_FIGURE).getroot()
    assert root.tag.endswith("svg")
    text = " ".join(
        "".join(element.itertext())
        for element in root.findall(".//{http://www.w3.org/2000/svg}text")
    )
    for required in (
        "Same candidate order",
        "proposal / train",
        "gate-validation",
        "sealed test",
        "future replay",
        "no GB10 replay or paper result yet",
    ):
        assert required in text
