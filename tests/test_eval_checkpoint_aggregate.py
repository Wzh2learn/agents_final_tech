"""K2 评测协议原型测试 — 检查点树聚合 (Algorithm 1) 的确定性行为。

覆盖: 归一化/加权/缺失叶子降级/阈值敏感; 不触碰既有测试与冻结文件。
纯内存计算, 不读活工件、不调任何服务。
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from eval_checkpoint_aggregate import (
    _contract_pass_rate,
    _judge_avg,
    _nf_pass_rate,
    _regression_overall_binary,
    _regression_row_pass_rate,
    aggregate_tree,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREES = os.path.join(REPO, "config", "eval_checkpoint_trees.json")


def _art(overall="PASS", rows=None, det=None, judge=None, nf=None):
    rows = rows if rows is not None else [{"label": "嘉合#0", "status": "PASS",
                                           "expected": [100.0], "actual": [100.0],
                                           "diffs": []}]
    det = det if det is not None else [{"id": "q01", "checks": [
        {"type": "source_required", "pass": True},
        {"type": "exact_numeric", "pass": True}], "all_pass": True}]
    judge = judge if judge is not None else {
        "summary": {d: {"avg": 5.0, "n": 16}
                    for d in ("faithfulness", "numeric_correctness",
                              "citation_quality", "refusal_appropriateness")}}
    nf = nf if nf is not None else {"n_fail": 0, "results": [{"id": "a", "pass": True}] * 9}
    return {
        "m1_regression": {"overall": overall, "rows": rows},
        "m2_deterministic": {"overall": "PASS", "n_questions": 2,
                             "n_pass": 2, "results": det},
        "m2_judge": judge,
        "m2_number_faithfulness": nf,
    }


def _load_trees():
    with open(TREES, encoding="utf-8") as fh:
        return json.load(fh)


def _tree_def(tid):
    for t in _load_trees()["trees"]:
        if t["id"] == tid:
            return t
    raise AssertionError(tid)


def _leaf_ids(tree):
    out = []
    def walk(n):
        if n.get("children"):
            for c in n["children"]:
                walk(c)
        else:
            out.append(n["id"])
    walk(tree)
    return out


class TestNormalization:
    def test_leaf_mapping_judge_scale(self):
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "l1", "requirement": "x", "weight": 1, "source": "m2_judge",
             "mapping": "judge_dim_0_5", "dim": "faithfulness", "missing_score": 5},
        ]}
        res = aggregate_tree(tree, _art(), (5, 7, 8))
        assert res["subtree_score"] == 10.0
        assert res["leaves"]["l1"] == 10.0

    def test_leaf_mapping_rate_scale(self):
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "l2", "requirement": "x", "weight": 1, "source": "m2_deterministic",
             "mapping": "pass_rate_contract", "contract": "source_required",
             "missing_score": 5},
        ]}
        res = aggregate_tree(tree, _art(), (5, 7, 8))
        assert res["leaves"]["l2"] == 10.0

    def test_sibling_weight_normalization(self):
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "w1", "requirement": "x", "weight": 1, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 0},
            {"id": "w3", "requirement": "x", "weight": 3, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 0},
        ]}
        res = aggregate_tree(tree, _art(overall="FAIL"), (5, 7, 8))
        # 兄弟归一化: (1*0 + 3*0)/4 = 0, 全 fail → 0
        assert res["subtree_score"] == 0.0

    def test_weighted_mix(self):
        # 一个 10 一个 0, weight 1:3 → (1*10 + 3*0)/4 = 2.5
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "a", "requirement": "x", "weight": 1, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 5},
            {"id": "b", "requirement": "x", "weight": 3, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 5},
        ]}
        art = _art(overall="PASS", rows=[{"label": "s1", "status": "PASS",
                                          "expected": [100.0], "actual": [100.0],
                                          "diffs": []}])
        art["m1_regression"] = {"overall": "PASS"}   # 双叶都吃整体 PASS
        res = aggregate_tree(tree, art, (5, 7, 8))
        assert res["leaves"] == {"a": 10.0, "b": 10.0}
        art["m1_regression"] = {"overall": "FAIL"}
        res = aggregate_tree(tree, art, (5, 7, 8))
        assert res["leaves"] == {"a": 0.0, "b": 0.0}
        # 权重混合: a=overall PASS(10), b=overall FAIL(0) → 需两个整体不可能 → 用 mapping 区分:
        # a 走 row_pass_rate (1 PASS 行 → 10), b 走整体 FAIL(0) → (1*10+3*0)/4=2.5
        tree2 = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "a2", "requirement": "x", "weight": 1, "source": "m1_regression",
             "mapping": "row_pass_rate", "missing_score": 5},
            {"id": "b2", "requirement": "x", "weight": 3, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 5},
        ]}
        art2 = _art(overall="FAIL", rows=[{"label": "s1", "status": "PASS",
                                           "expected": [100.0], "actual": [100.0],
                                           "diffs": []}])
        res2 = aggregate_tree(tree2, art2, (5, 7, 8))
        assert res2["leaves"] == {"a2": 10.0, "b2": 0.0}
        assert res2["subtree_score"] == 2.5


class TestMissingDegradation:
    def test_missing_artifact_degraded_not_zero(self):
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "l", "requirement": "x", "weight": 1, "source": "missing_src",
             "mapping": "overall_status_binary", "missing_score": 5},
        ]}
        res = aggregate_tree(tree, {}, (5, 7, 8))
        assert res["leaves"]["l"] == 5.0  # 显式降级, 不是 0

    def test_hinge_missing_scores_zero(self):
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "h", "requirement": "x", "weight": 1, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 0},
        ]}
        res = aggregate_tree(tree, {}, (5, 7, 8))
        assert res["leaves"]["h"] == 0.0
        assert res["sr"]["7"]["leaf_sr"] == 0.0

    def test_missing_dimensional_leaf(self):
        # judge 报告缺 numeric_correctness 维 → 该叶降级 5, 其余 10
        tree = _tree_def("qa")
        judge = {"summary": {"faithfulness": {"avg": 5.0, "n": 16},
                             "citation_quality": {"avg": 5.0, "n": 16},
                             "refusal_appropriateness": {"avg": 5.0, "n": 16}}}
        # 语义: 整工件缺失才用 missing_score 降级; 工件存在而单维缺失 → 按 1.0 率映射 (无证据不扣分)
        res = aggregate_tree(tree, _art(judge=judge), (5, 7, 8))
        for lid in ("qa.faithfulness.judge", "qa.citation.judge", "qa.refusal.judge"):
            assert res["leaves"][lid] == 10.0
        assert res["leaves"]["qa.numeric.exact"] == 10.0
        assert res["leaves"]["qa.numeric.number_grounding"] == 10.0


class TestThresholdSensitivity:
    def test_different_thresholds_change_leaf_sr(self):
        rows = [
            {"label": "s1", "status": "PASS", "expected": [100.0], "actual": [100.0],
             "diffs": []},
            {"label": "s2", "status": "PASS", "expected": [50.0], "actual": [50.0],
             "diffs": []},
        ]
        tree = _tree_def("parse")
        art = _art(rows=rows)
        art["m1_regression"]["timestamp"] = "2026-08-16 23:04:26"  # doc 级叶读 timestamp
        res = aggregate_tree(tree, art, (5, 7, 8))
        assert res["leaves"]["parse.table.regression"] == 10.0
        assert res["leaves"]["parse.doc.throughput"] == 10.0
        # 全绿 → parse 5 叶全 10 → 三档 leaf_sr 均 1.0
        for k in ("5", "7", "8"):
            assert res["sr"][k]["leaf_sr"] == 1.0
        # 含一条 FAIL 行 → 表级叶 0.67*10≈6.7 被 8 档阈值抖落, 5/7 档仍过
        rows2 = rows + [{"label": "s3", "status": "FAIL", "expected": [100.0],
                         "actual": [60.0], "diffs": [{"hit_rate": -40}]}]
        res2 = aggregate_tree(tree, _art(rows=rows2), (5, 7, 8))
        assert res2["leaves"]["parse.table.regression"] == round(10.0 * (2 / 3), 4)
        # 行 FAIL 还会拖垮 field/reconcile (阈值敏感: 各档 leaf_sr 单调不增)
        s5, s7, s8 = (res2["sr"]["5"]["leaf_sr"], res2["sr"]["7"]["leaf_sr"],
                      res2["sr"]["8"]["leaf_sr"])
        assert s5 >= s7 >= s8
        assert s5 < 1.0

    def test_threshold_sensitive_score(self):
        # 混一个 0 分叶子 (fail) → k=5 时不过, k=... 全不过 → leaf_sr 变化
        rows = [
            {"label": "s1", "status": "PASS", "expected": [100.0], "actual": [100.0],
             "diffs": []},
            {"label": "s2", "status": "FAIL", "expected": [100.0], "actual": [50.0],
             "diffs": [{"hit_rate": -50}]},
        ]
        tree = {"id": "root", "requirement": "x", "weight": 1, "children": [
            {"id": "l1", "requirement": "x", "weight": 1, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 5},
            {"id": "l2", "requirement": "x", "weight": 1, "source": "m1_regression",
             "mapping": "overall_status_binary", "missing_score": 5},
        ]}
        art = _art(rows=rows, overall="FAIL")
        res = aggregate_tree(tree, art, (5, 7, 8))
        assert res["leaves"] == {"l1": 0.0, "l2": 0.0}
        assert res["sr"]["5"]["leaf_sr"] == 0.0
        assert res["sr"]["7"]["leaf_sr"] == 0.0
        assert res["sr"]["8"]["leaf_sr"] == 0.0
        assert res["stable"]["stable"] is False

    def test_root_sr_branching(self):
        # 两子树一个过阈值一个不过 → root_sr = 0.5
        def mk(v):
            return {"id": f"t{v}", "requirement": "x", "weight": 1, "children": [
                {"id": f"l{v}", "requirement": "x", "weight": 1,
                 "source": "m1_regression", "mapping": "overall_status_binary",
                 "missing_score": 5}]}
        tree = {"id": "root", "requirement": "x", "weight": 1,
                "children": [mk(1), mk(2)]}
        rows = [{"label": "s1", "status": "PASS", "expected": [100.0],
                 "actual": [100.0], "diffs": []}]
        res = aggregate_tree(tree, _art(rows=rows, overall="PASS"), (5, 7, 8))
        assert res["subtree_score"] == 10.0
        assert res["sr"]["7"]["root_sr"] == 1.0


class TestTreesDefinition:
    def test_trees_file_loads_and_self_consistent(self):
        trees = _load_trees()
        assert trees["meta"]["version"] == "0.1.0"
        assert set(trees["meta"]["success_rates"]) == {"root_sr", "leaf_sr"}
        ids = set()
        parents = set()
        for t in trees["trees"]:
            assert t.get("weight", 1) in (1, 2, 3)
            def walk(n):
                assert set(n.keys()) <= {
                    "id", "label", "requirement", "weight", "children",
                    "source", "mapping", "contract", "dim", "missing_score"}
                ids.add(n["id"])
                for c in n.get("children", []):
                    parents.add(c["id"])
                    assert c.get("weight", 1) in (1, 2, 3)
                    walk(c)
            walk(t)
        # 无悬空引用 + 原子叶子: 20 个 (parse 7 + qa 13)
        assert parents <= ids
        assert len(ids) == 23  # 全部节点含中间层

    def test_trees_mapping_routes_resolve(self):
        from eval_checkpoint_aggregate import LEAF_ROUTERS
        trees = _load_trees()
        seen = []
        for t in trees["trees"]:
            stack = [t]
            while stack:
                n = stack.pop()
                if n.get("children"):
                    stack.extend(n["children"])
                else:
                    seen.append(n)
        assert len(seen) == 12
        for leaf in seen:
            assert leaf["source"] in LEAF_ROUTERS
            assert leaf["mapping"] in LEAF_ROUTERS[leaf["source"]]

    def test_hinge_and_missing_fields_present(self):
        trees = _load_trees()
        missing_keys = {"missing_score"}
        for t in trees["trees"]:
            def walk(n):
                if n.get("children"):
                    for c in n["children"]:
                        walk(c)
                    return
                assert missing_keys <= set(n.keys())
                assert n.get("missing_score", -1) in (0, 5, 10) or n["source"] == "m1_regression"
            walk(t)


class TestLeafFactories:
    def test_contract_pass_rate(self):
        rep = {"results": [{"id": "q", "checks": [
            {"type": "source_required", "pass": True},
            {"type": "source_required", "pass": False}]}]}
        rate, n, _ = _contract_pass_rate(rep, "source_required")
        assert rate == 0.5 and n == 2

    def test_contract_missing_type_reports_zero(self):
        rep = {"results": [{"id": "q", "checks": [
            {"type": "exact_numeric", "pass": True}]}]}
        rate, n, note = _contract_pass_rate(rep, "source_required")
        assert rate == 1.0 and n == 0 and note

    def test_judge_avg(self):
        rep = {"summary": {"faithfulness": {"avg": 4.5, "n": 16}}}
        assert _judge_avg(rep, "faithfulness") == (4.5, 16, "")

    def test_nf_pass_rate(self):
        rep = {"n_fail": 1, "results": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}
        assert _nf_pass_rate(rep) == (2 / 3, 3, "")

    def test_regression_binary(self):
        rep = {"overall": "PASS", "rows": [{"status": "PASS"}]}
        assert _regression_overall_binary(rep) == (10.0, 1, "")
        rep = {"overall": "FAIL", "rows": [{"status": "FAIL"}]}
        assert _regression_overall_binary(rep) == (0.0, 1, "")

    def test_regression_row_pass_rate(self):
        rows = [{"status": "PASS"}, {"status": "PASS"}, {"status": "FAIL"},
                {"status": "SKIP(quick)"}]
        rate, n, _ = _regression_row_pass_rate({"rows": rows})
        assert rate == 2 / 3 and n == 3

    def test_nf_empty_results(self):
        rep = {"n_fail": 0, "results": []}
        rate, n, note = _nf_pass_rate(rep)
        assert rate == 1.0 and n == 0 and note
