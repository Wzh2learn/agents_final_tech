from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    ROOT
    / "research/research_direction_sprint_20261020_v1/execution_v1/"
    "paper_e_audit/outputs/APPLICATION_RESULTS.json"
)
FULL_ROWS = (
    ROOT
    / "research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/"
    "PAPER_E_PRIVATE_ARTIFACT_CANDIDATE/inputs/FINRANK_FULL_PRECISION_ROWS.json"
)


def test_full_precision_source_rounds_to_13821() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    pair = payload["models"]["tfidf"]
    hard = pair["hard_negative_pairwise"]["accuracy_strict"]
    random = pair["random_negative_pairwise"]["accuracy_strict"]
    raw_gap = pair["random_negative_pairwise"]["gap_random_minus_hard_strict"]
    assert raw_gap == random - hard
    assert f"{raw_gap:.3f}" == "13.821"
    assert f"{round(random, 3) - round(hard, 3):.3f}" == "13.820"


def test_artifact_full_precision_extract_matches_source() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    extract = json.loads(FULL_ROWS.read_text(encoding="utf-8"))
    rows = {(row["model"], row["tie_policy"]): row for row in extract["rows"]}
    pair = source["models"]["tfidf"]
    strict = rows[("TF-IDF", "strict-win")]
    assert strict["hard"] == pair["hard_negative_pairwise"]["accuracy_strict"]
    assert strict["random"] == pair["random_negative_pairwise"]["accuracy_strict"]


def test_active_paper_uses_full_precision_display() -> None:
    markdown = (ROOT / "paper/saner_rene_manuscript_v1.md").read_text(encoding="utf-8")
    tex = (ROOT / "paper/icaart_2027_submission_v1/manuscript.tex").read_text(encoding="utf-8")
    assert "| TF-IDF | strict-win | 77.030 | 90.850 | 13.821 |" in markdown
    assert "TF-IDF & strict-win & 77.030 & 90.850 & 13.821 \\\\" in tex
    for text in (markdown, tex):
        assert "13.820514366083984" in text
        assert "13.821" in text
