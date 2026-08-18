"""v1 judge --runs k (K1 T2 ensemble) 单元测试。

monkeypatch _judge_once, 不发真实请求; 验证:
- runs=1 与历史单次行为一致（原样返回）
- runs>1 均值/方差/runs 留档/最近均分理由
- 全失败 -> score None（error 形状保持）
- rubric 版本元数据在场
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import m2_eval_judge as judge  # noqa: E402


def _canned(scores, reason="r"):
    return {d: {"score": s, "reason": reason} for d, s in scores.items()}


def test_runs1_returns_single_call_unchanged(monkeypatch):
    canned = _canned({"faithfulness": 5, "numeric_correctness": 4,
                      "citation_quality": 3, "refusal_appropriateness": 5})
    calls = []

    def fake(*a, **kw):
        calls.append(1)
        return canned

    monkeypatch.setattr(judge, "_judge_once", fake)
    out = judge.judge_one("q", "c", "a", "s", "e", False, runs=1)
    assert out is canned
    assert len(calls) == 1


def test_runs3_mean_std_and_runs_archive(monkeypatch):
    seq = [
        _canned({"faithfulness": 5, "numeric_correctness": 5,
                 "citation_quality": 5, "refusal_appropriateness": 5},
                reason="high"),
        _canned({"faithfulness": 3, "numeric_correctness": 5,
                 "citation_quality": 5, "refusal_appropriateness": 5},
                reason="low"),
        _canned({"faithfulness": 4, "numeric_correctness": 5,
                 "citation_quality": 5, "refusal_appropriateness": 5},
                reason="mid"),
    ]
    monkeypatch.setattr(judge, "_judge_once",
                        lambda *a, **kw: seq.pop(0))
    out = judge.judge_one("q", "c", "a", "s", "e", False, runs=3)
    f = out["faithfulness"]
    assert f["score"] == 4.0          # (5+3+4)/3
    assert f["runs"] == [5, 3, 4]
    assert f["std"] is not None and f["std"] > 0
    assert f["reason"] == "mid"       # 4 最接近均分 4.0
    assert out["numeric_correctness"]["score"] == 5.0
    assert out["numeric_correctness"]["std"] == 0.0


def test_all_runs_unusable_keeps_none_shape(monkeypatch):
    monkeypatch.setattr(judge, "_judge_once",
                        lambda *a, **kw: {"error": "boom", **{
                            d: {"score": None, "reason": "judge call failed"}
                            for d in judge.DIMS}})
    out = judge.judge_one("q", "c", "a", "s", "e", False, runs=3)
    for d in judge.DIMS:
        assert out[d]["score"] is None
        assert out[d]["runs"] == [None, None, None]
    assert out["faithfulness"]["n_unusable"] == 3


def test_partial_unusable_excluded_from_mean(monkeypatch):
    good = _canned({"faithfulness": 4, "numeric_correctness": 4,
                    "citation_quality": 4, "refusal_appropriateness": 4})
    bad = {"error": "parse", **{d: {"score": None, "reason": "unparsable"}
                                for d in judge.DIMS}}
    seq = [good, bad]
    monkeypatch.setattr(judge, "_judge_once",
                        lambda *a, **kw: seq.pop(0))
    out = judge.judge_one("q", "c", "a", "s", "e", False, runs=2)
    assert out["faithfulness"]["score"] == 4.0  # 只有 1 个有效分
    assert out["faithfulness"]["runs"] == [4, None]


def test_rubric_version_metadata():
    assert judge.RUBRIC_VERSION == "v_k1"
    # prompt 文本本身不得含版本元数据（防 prompt 漂移）
    assert "v_k1" not in judge.JUDGE_PROMPT
