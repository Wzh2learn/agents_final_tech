"""v1 判别力测试床测试 — 构造缺陷样本的确定性行为验证。

纯内存/tmp 工件, 不读活工件、不调任何服务、不碰冻结文件。
覆盖: control 零漂移 / 目标叶子下降判据 / 非目标叶子局部性 /
各 mutator 的确定性效果。
"""

import copy
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import eval_checkpoint_discrimination as disc  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREES = os.path.join(REPO, "config", "eval_checkpoint_trees.json")


def _write(d, name, obj):
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


@pytest.fixture()
def green_eval_dir(tmp_path):
    d = tmp_path / "eval"
    d.mkdir()
    _write(d, disc.ARTIFACTS["m1_regression"], {
        "overall": "PASS", "quick": True, "timestamp": "t0",
        "rows": [
            {"label": "s1", "status": "PASS", "diffs": [],
             "expected": [100.0, 90.0], "actual": [100.0, 90.0]},
            {"label": "s2", "status": "PASS", "diffs": [],
             "expected": [80.0, 70.0], "actual": [80.0, 70.0]},
        ]})
    _write(d, disc.ARTIFACTS["m2_deterministic"], {
        "overall": "PASS", "n_questions": 2, "n_pass": 2,
        "results": [
            {"id": "q1", "turns": ["问1"], "answers": ["答1"],
             "sources": [{"doc": "s1"}], "route": "direct",
             "all_pass": True,
             "checks": [{"type": "source_required", "pass": True},
                        {"type": "exact_numeric", "pass": True}]},
            {"id": "q2", "turns": ["问2"], "answers": ["未找到"],
             "sources": [], "route": "direct", "all_pass": True,
             "checks": [{"type": "refusal_expected", "pass": True}]},
        ]})
    _write(d, disc.ARTIFACTS["m2_judge"], {
        "summary": {dim: {"avg": 5.0, "n": 2} for dim in (
            "faithfulness", "numeric_correctness", "citation_quality",
            "refusal_appropriateness")},
        "results": [
            {"id": "q1", "scores": {dim: {"score": 5, "reason": "ok"}
                                    for dim in (
                "faithfulness", "numeric_correctness", "citation_quality",
                "refusal_appropriateness")}},
        ]})
    _write(d, disc.ARTIFACTS["m2_number_faithfulness"], {
        "results": [{"id": "q1", "pass": True, "ungrounded": []},
                    {"id": "q2", "pass": True, "ungrounded": []}],
        "n_fail": 0, "top_k": 5})
    return str(d)


def test_control_zero_drift_and_all_mutants_pass(green_eval_dir, tmp_path):
    out_json = str(tmp_path / "disc.json")
    out_md = str(tmp_path / "disc.md")
    rc = disc.main(["--eval-dir", green_eval_dir, "--trees", TREES,
                    "--out", out_json, out_md, "--keep"])
    rep = json.load(open(out_json, encoding="utf-8"))
    assert rep["control"]["zero_drift"] is True
    assert rep["summary"]["all_pass"] is True
    assert rep["summary"]["n_mutants"] == len(disc.build_mutants())
    assert rc == 0
    assert os.path.exists(out_md)


def test_m1_rows_fail_targets(green_eval_dir):
    d = green_eval_dir
    disc.mut_m1_rows_fail(d)
    rep = json.load(open(os.path.join(
        d, disc.ARTIFACTS["m1_regression"]), encoding="utf-8"))
    assert rep["overall"] == "FAIL"
    fails = [r for r in rep["rows"] if r["status"] == "FAIL"]
    assert len(fails) == 2
    assert all(r["diffs"] for r in fails)


def test_contract_fail_only_flips_target_contract(green_eval_dir):
    d = green_eval_dir
    disc.mut_contract_fail(d, "exact_numeric")
    rep = json.load(open(os.path.join(
        d, disc.ARTIFACTS["m2_deterministic"]), encoding="utf-8"))
    for r in rep["results"]:
        for ch in r["checks"]:
            if ch["type"] == "exact_numeric":
                assert ch["pass"] is False
            elif ch["type"] in ("source_required", "refusal_expected"):
                assert ch["pass"] is True


def test_judge_degrade_only_target_dim(green_eval_dir):
    d = green_eval_dir
    disc.mut_judge_degrade(d, "faithfulness", 2.0)
    rep = json.load(open(os.path.join(
        d, disc.ARTIFACTS["m2_judge"]), encoding="utf-8"))
    assert rep["summary"]["faithfulness"]["avg"] == 2.0
    assert rep["summary"]["citation_quality"]["avg"] == 5.0


def test_nf_fail_sets_n_fail(green_eval_dir):
    d = green_eval_dir
    disc.mut_nf_fail(d, 3)
    rep = json.load(open(os.path.join(
        d, disc.ARTIFACTS["m2_number_faithfulness"]), encoding="utf-8"))
    assert rep["n_fail"] == 2  # min(3, n_results=2)
    assert all(r["pass"] is False for r in rep["results"])


def test_missing_artifact_degrades_not_crashes(green_eval_dir, tmp_path):
    d = green_eval_dir
    disc.mut_delete_artifact(d, "m2_judge")
    import eval_checkpoint_aggregate as agg
    trees_def = agg._load_json(TREES)
    res = disc.run_aggregate(trees_def, d)
    # judge 三叶降到 missing_score=5, 其余不受影响
    assert res["qa"]["leaves"]["qa.faithfulness.judge"] == 5.0
    assert res["qa"]["leaves"]["qa.numeric.exact"] == 10.0
    assert res["parse"]["subtree_score"] == 10.0
