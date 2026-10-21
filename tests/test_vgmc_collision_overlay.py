"""碰撞语料 overlay 合并单测（段 A, 设计稿 2026-08-27_collision_corpus_exp_design.md）。"""
import importlib.util
import json
import os
import sys

from vgmc_test_support import overlay_base_corpus, simple_corpus

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "vgmc_exp1", os.path.join(REPO, "research", "vgmc_exp1.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_overlay_merge_adds_columns_and_entries():
    m = _load()
    corpus = simple_corpus()
    uid = next(iter(corpus))
    rec0 = corpus[uid]
    n_hdr, n_rows = len(rec0["inj_header"]), len(rec0["rows"])
    canon = rec0["canonicals"][0]
    overlay = {"meta": {"n_cols": 1, "seed": 1},
               "tables": {uid: {"cols": [{"header": "移植列X", "true_canonical": canon,
                                           "source_uid": "other", "data_col_idx": 0}]}}}
    merged = m.merge_overlay(corpus, overlay)
    rec = merged[uid]
    assert len(rec["inj_header"]) == n_hdr + 1
    assert rec["inj_header"][-1] == "移植列X"
    assert all(len(r) == len(rec["inj_header"]) for r in rec["rows"])
    assert len(rec["rows"]) == n_rows, "只增列不增行"
    e = rec["entries"][-1]
    assert e["type"] == "collision" and e["original"] == canon
    assert rec["rows"][1][-1] == rec["rows"][1][0], "数据复制真值列"


def test_overlay_none_is_identity():
    m = _load()
    corpus = simple_corpus()
    assert m.merge_overlay(corpus, None) is corpus


def test_real_overlay_artifact_loads():
    m = _load()
    path = os.path.join(REPO, "logs", "graph", "eval", "vgmc_collision_overlay.json")
    overlay = json.loads(open(path, encoding="utf-8").read())
    corpus = m.merge_overlay(overlay_base_corpus(overlay), overlay)
    n_col = sum(1 for u, t in overlay["tables"].items()
                for e in corpus[u]["entries"] if e.get("type") == "collision")
    assert n_col == overlay["meta"]["n_cols"]
