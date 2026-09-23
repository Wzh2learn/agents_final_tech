from pathlib import Path
import json
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
PREREGISTRATION = REPO / "docs" / "experiments" / "2026-09-22_distillation_mvp_preregistration.md"
SOURCE_REGISTRY = REPO / "docs" / "datasets" / "paper-public-source-registry-v1.json"
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
    assert "不声称首次“小模型+大模型”" in text
    assert "Valentine" in text and "Magneto" in text and "Matchmaker" in text


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
        "Risk}_{\\mathrm{student}}(\\tau)",
        "Delta_s",
        "Delta_p",
        "Delta_g",
        "命题 1",
        "命题 2",
        "只能支持第一个累计局部界",
        "arXiv:1506.02629",
        "不能声称已有 conformal guarantee",
        "不等价于在线学习收敛",
        "hold` 是任务标签",
        "U_{1-\\alpha_{\\mathrm{sig}}}",
        "source-lineage UID 组",
        "w_i^{(1)}=u_i",
        "不能**声称首次",
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
        "Valentine 的 NYC schema-matching benchmark 是 P0 动作来源",
        "FinQA 与 ConvFinQA 在完成 report/question UID 去重前不得跨",
        "人工标注源 → package label ledger → learnability view",
        "RQ2 标 `NOT_IDENTIFIED`",
    ):
        assert required in text


def test_method_bibliography_has_unique_verified_keys() -> None:
    text = METHOD_BIB.read_text(encoding="utf-8")
    keys = re.findall(r"@article\{([^,]+),", text)
    assert len(keys) == 42
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
        "2006.01862",
        "2306.13649",
        "2412.08194",
        "2410.24105",
        "2010.07386",
        "2210.03849",
    ):
        assert arxiv_id in text

    theory = THEORY.read_text(encoding="utf-8")
    listed_keys = set(re.findall(r"^\| `([^`]+)` \|", theory, flags=re.MULTILINE))
    assert listed_keys <= set(keys)


def test_public_source_registry_is_metadata_only_and_fail_closed() -> None:
    registry = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    assert registry["status"] == "METADATA_ONLY_NOT_DOWNLOAD_APPROVAL"
    assert registry["policy"]["contains_data_bodies"] is False
    assert registry["policy"]["download_approved"] is False

    sources = registry["sources"]
    ids = [source["dataset_id"] for source in sources]
    assert len(ids) == len(set(ids)) == 10
    for source in sources:
        assert re.fullmatch(r"[0-9a-f]{40}", source["checked_default_head"])
        assert source["official_repo"].startswith("https://github.com/")
        assert source["download_approved"] is False
        assert source["data_license_state"] != "APPROVED"
        assert source["independence_cluster_namespace"]
        assert "independence_cluster" not in source

    by_id = {source["dataset_id"]: source for source in sources}
    assert (
        by_id["finqa"]["independence_cluster_namespace"]
        == by_id["convfinqa"]["independence_cluster_namespace"]
    )
    assert by_id["finqa"]["decision"] == "P0_PROCESS_SOURCE_PREFLIGHT"
    assert by_id["valentine_nyc"]["decision"] == "P0_ACTION_SOURCE_PREFLIGHT"
    assert by_id["tatqa"]["decision"] == "HISTORICAL_ONLY_UNTIL_EXPOSURE_AUDIT"


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


def test_distillation_preregistration_matches_current_authority() -> None:
    text = PREREGISTRATION.read_text(encoding="utf-8")
    for required in (
        "DRAFT_NOT_FROZEN",
        "RQ2 / RQ3 / RQ4",
        "SIMPLE_SUFFICIENT",
        "size/token/group-matched（主口径）",
        "Qwen3-4B LoRA/QLoRA，极少步",
        "paper_result=false",
        "historical_exposure_manifest_sha256",
        "sealed_test_open_once",
    ):
        assert required in text
    assert "Claim：SP-RQ2" not in text
    assert "低成本对照候选：Qwen3-4B" not in text
