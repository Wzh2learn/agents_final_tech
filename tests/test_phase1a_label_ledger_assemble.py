"""Tests for the phase1a label_ledger assembler (JSON Lines, fail-closed)."""
from __future__ import annotations

import json

import pytest

from research.phase1a_label_ledger_assemble import (
    LabelAssemblyError,
    assemble,
)

LABEL_FIELDS = {
    "sample_id", "uid", "col", "gold_action", "gold_target",
    "quality_grade", "reviewers", "adjudication",
}


def _rev(rid: str, *jud: tuple) -> dict:
    return {
        "reviewer_id": rid,
        "template_version": "t1",
        "judgments": [
            {"sample_id": s, "uid": u, "col": c, "action": a, "target": t}
            for (s, u, c, a, t) in jud
        ],
    }


def _adj(entries: list[dict], aid: str = "adj") -> dict:
    return {"adjudicator_id": aid, "entries": entries}


R1 = lambda: _rev("r1", ("s1", "u1", 0, "map_to", "asset"))
R2 = lambda: _rev("r2", ("s1", "u1", 0, "map_to", "asset"))


def test_positive_agreement() -> None:
    rows, meta = assemble(R1(), R2(), _adj([]), "gen")
    assert len(rows) == 1
    row = rows[0]
    assert set(row) == LABEL_FIELDS
    assert row["quality_grade"] == "Q3"
    assert row["gold_action"] == "map_to" and row["gold_target"] == "asset"
    assert row["adjudication"] is None
    assert [r["reviewer_id"] for r in row["reviewers"]] == ["r1", "r2"]
    assert meta["agreement_rate"] == 1.0


def test_positive_disagreement_adjudicated() -> None:
    r2 = _rev("r2", ("s1", "u1", 0, "skip", None))
    adj = _adj([{"sample_id": "s1", "col": 0, "action": "map_to", "target": "asset",
                 "rationale_ref": "doc#3"}])
    rows, meta = assemble(R1(), r2, adj, "gen")
    assert rows[0]["gold_action"] == "map_to"
    assert rows[0]["adjudication"]["adjudicator_id"] == "adj"
    assert rows[0]["adjudication"]["rationale_ref"] == "doc#3"
    assert meta["agreement_rate"] == 0.0


def test_generator_in_reviewers_rejected() -> None:
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), R2(), _adj([]), "r1")
    assert exc.value.code == "generator_in_reviewers"


def test_reviewers_not_distinct_rejected() -> None:
    r2 = _rev("r1", ("s1", "u1", 0, "map_to", "asset"))
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), r2, _adj([]), "gen")
    assert exc.value.code == "reviewers_not_distinct"


def test_adjudicator_is_reviewer_rejected() -> None:
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), R2(), _adj([], aid="r2"), "gen")
    assert exc.value.code == "adjudicator_is_reviewer"


def test_incomplete_pair_rejected() -> None:
    r2 = _rev("r2", ("s2", "u2", 0, "skip", None))
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), r2, _adj([]), "gen")
    assert exc.value.code == "incomplete_review_pair"


def test_missing_adjudication_rejected() -> None:
    r2 = _rev("r2", ("s1", "u1", 0, "skip", None))
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), r2, _adj([]), "gen")
    assert exc.value.code == "missing_adjudication"


def test_invalid_judgment_rejected() -> None:
    bad = _rev("r2", ("s1", "u1", 0, "map_to", None))  # map_to needs a target
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), bad, _adj([]), "gen")
    assert exc.value.code == "invalid_judgment"


def test_jsonl_shape(tmp_path) -> None:
    from research.phase1a_label_ledger_assemble import main
    import sys

    p1 = tmp_path / "r1.json"; p1.write_text(json.dumps(R1()), encoding="utf-8")
    p2 = tmp_path / "r2.json"; p2.write_text(json.dumps(R2()), encoding="utf-8")
    pa = tmp_path / "adj.json"; pa.write_text(json.dumps(_adj([])), encoding="utf-8")
    out = tmp_path / "ledger.jsonl"
    argv = ["x", "--r1", str(p1), "--r2", str(p2), "--adjudications", str(pa),
            "--generator-id", "gen", "--out", str(out)]
    monkey = pytest.MonkeyPatch()
    monkey.setattr(sys, "argv", argv)
    try:
        assert main() == 0
    finally:
        monkey.undo()
    lines = [ln for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    assert set(json.loads(lines[0])) == LABEL_FIELDS
    meta = json.loads(out.with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert meta["reviewer_carriers"] == ["r1", "r2"]

def test_missing_target_key_rejected() -> None:
    bad = {"reviewer_id": "r2", "template_version": "t1",
           "judgments": [{"sample_id": "s1", "uid": "u1", "col": 0, "action": "skip"}]}
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), bad, _adj([]), "gen")
    assert exc.value.code == "invalid_judgment"


def test_missing_uid_rejected() -> None:
    bad = {"reviewer_id": "r2", "template_version": "t1",
           "judgments": [{"sample_id": "s1", "col": 0, "action": "skip", "target": None}]}
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), bad, _adj([]), "gen")
    assert exc.value.code == "invalid_judgment"


def test_non_dict_judgment_rejected() -> None:
    bad = {"reviewer_id": "r2", "template_version": "t1", "judgments": ["x"]}
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), bad, _adj([]), "gen")
    assert exc.value.code == "invalid_judgment"


def test_non_dict_adjudication_entry_rejected() -> None:
    r2 = _rev("r2", ("s1", "u1", 0, "skip", None))
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), r2, _adj(["y"]), "gen")
    assert exc.value.code == "invalid_adjudication_entry"


def test_missing_rationale_ref_rejected() -> None:
    r2 = _rev("r2", ("s1", "u1", 0, "skip", None))
    adj = _adj([{"sample_id": "s1", "col": 0, "action": "map_to", "target": "asset"}])
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), r2, adj, "gen")
    assert exc.value.code == "missing_rationale_ref"


def test_unparseable_input_rejected(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    from research.phase1a_label_ledger_assemble import main

    p1 = tmp_path / "r1.json"; p1.write_text("{not json", encoding="utf-8")
    p2 = tmp_path / "r2.json"; p2.write_text(json.dumps(R2()), encoding="utf-8")
    pa = tmp_path / "adj.json"; pa.write_text(json.dumps(_adj([])), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["x", "--r1", str(p1), "--r2", str(p2),
                                      "--adjudications", str(pa),
                                      "--generator-id", "gen",
                                      "--out", str(tmp_path / "o.jsonl")])
    with pytest.raises(LabelAssemblyError) as exc:
        main()
    assert exc.value.code == "invalid_input_json"

def test_top_level_non_dict_review_doc_rejected() -> None:
    with pytest.raises(LabelAssemblyError) as exc:
        assemble([], R2(), _adj([]), "gen")
    assert exc.value.code == "invalid_review_doc"


def test_top_level_non_dict_adjudication_doc_rejected() -> None:
    with pytest.raises(LabelAssemblyError) as exc:
        assemble(R1(), R2(), [], "gen")
    assert exc.value.code == "invalid_adjudication_doc"