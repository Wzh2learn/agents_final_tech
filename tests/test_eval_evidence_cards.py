"""v1 evidence card 合成器测试（批复 ⑤）。

合成 report + fixture, 验证卡片合成/等级判定/leaderboard/主入口。
不读活工件、不调服务、不碰冻结 fixture（用 tmp 副本）。
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eval_evidence_cards as ec  # noqa: E402


def _write(d, name, obj):
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


@pytest.fixture()
def eval_env(tmp_path):
    d = tmp_path / "eval"
    d.mkdir()
    _write(d, "m2_deterministic_report.json", {
        "overall": "PASS", "n_questions": 3, "n_pass": 2,
        "results": [
            {"id": "qa", "turns": ["总权益?"], "answers": ["100 元"],
             "sources": [{"doc": "s1"}], "route": "direct",
             "latency_ms": 2100, "all_pass": True,
             "checks": [
                 {"type": "source_required", "pass": True,
                  "evidence": "s1#表1"},
                 {"type": "exact_numeric", "pass": True,
                  "evidence": "100"}]},
            {"id": "qb", "turns": ["不存在指标?"], "answers": ["未找到"],
             "sources": [], "route": "direct", "all_pass": True,
             "checks": [{"type": "refusal_expected", "pass": True}]},
            {"id": "qc", "turns": ["坏答案?"], "answers": ["编造值"],
             "sources": [], "route": "agent", "all_pass": False,
             "checks": [{"type": "refusal_expected", "pass": False}]},
        ]})
    _write(d, "m2_judge_report.json", {
        "summary": {dim: {"avg": 5.0, "n": 2} for dim in (
            "faithfulness", "numeric_correctness", "citation_quality",
            "refusal_appropriateness")},
        "results": [
            {"id": "qa", "scores": {dim: {"score": 5, "reason": "ok"}
                                    for dim in (
                "faithfulness", "numeric_correctness", "citation_quality",
                "refusal_appropriateness")}},
            {"id": "qb", "scores": {dim: {"score": 3, "reason": "mid"}
                                    for dim in (
                "faithfulness", "numeric_correctness", "citation_quality",
                "refusal_appropriateness")}},
        ]})
    _write(d, "number_faithfulness_report.json", {
        "results": [{"id": "qa", "pass": True, "ungrounded": []}],
        "n_fail": 0, "top_k": 5})
    fx = tmp_path / "fixture.json"
    _write(tmp_path, "fixture.json", {"questions": [
        {"id": "qa", "question": "总权益是多少?"},
        {"id": "qb", "question": "不存在的指标?"},
        {"id": "qc", "question": "坏答案题?"}]})
    return str(d), str(fx)


def test_grades_and_order(eval_env):
    d, fx = eval_env
    cards = ec.build_cards(d, fx)
    by_id = {c["id"]: c for c in cards}
    assert by_id["qa"]["grade"] == "A"    # 全契约过 + judge 全 5
    assert by_id["qb"]["grade"] == "B"    # 契约过但 judge 有维 <4
    assert by_id["qc"]["grade"] == "C"    # 契约失败
    assert cards[0]["id"] == "qa"         # A 排首
    assert [c["grade"] for c in cards] == sorted(
        (c["grade"] for c in cards), key=lambda g: {"A": 0, "B": 1, "C": 2}[g])


def test_check_leaf_mapping_and_evidence(eval_env):
    d, fx = eval_env
    cards = ec.build_cards(d, fx)
    qa = next(c for c in cards if c["id"] == "qa")
    types = {c["type"]: c for c in qa["checks"]}
    assert types["source_required"]["checkpoint_leaf"] == \
        "qa.retrieval.source_required"
    assert types["exact_numeric"]["checkpoint_leaf"] == "qa.numeric.exact"
    assert types["source_required"]["evidence"] == "s1#表1"
    assert qa["judge_scores"]["faithfulness"]["checkpoint_leaf"] == \
        "qa.faithfulness.judge"
    assert qa["number_faithfulness"]["pass"] is True
    assert qa["question"] == "总权益是多少?"


def test_main_writes_cards_and_leaderboard(eval_env, tmp_path):
    d, fx = eval_env
    rc = ec.main(["--eval-dir", d, "--fixture", fx])
    assert rc == 0
    cards = json.load(open(os.path.join(d, "evidence_cards.json"),
                           encoding="utf-8"))
    assert len(cards["cards"]) == 3
    md = open(os.path.join(d, "evidence_cards_leaderboard.md"),
              encoding="utf-8").read()
    assert "Leaderboard" in md
    assert "qa" in md and "qc" in md


def test_main_missing_det_report_exit2(tmp_path, capsys):
    d = tmp_path / "empty"
    d.mkdir()
    rc = ec.main(["--eval-dir", str(d)])
    assert rc == 2
