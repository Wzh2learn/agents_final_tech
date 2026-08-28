"""对抗注入层单测（#13, 设计稿 2026-08-28_adversarial_suggester_arm_design.md）。"""
import importlib.util
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
EVAL = os.path.join(REPO, "logs", "graph", "eval")


def _load():
    spec = importlib.util.spec_from_file_location(
        "vgmc_exp1", os.path.join(REPO, "research", "vgmc_exp1.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_adv_map_deterministic_nested_wrong_target():
    m = _load()
    overlay = json.load(open(os.path.join(EVAL, "vgmc_collision_overlay.json"), encoding="utf-8"))
    corpus = m.load_corpus(overlay)
    fix, meas = m.split_uids(list(corpus.keys()))
    adv10, k10 = m.build_adv_map(corpus, overlay, fix, 1.0)
    adv10b, _ = m.build_adv_map(corpus, overlay, fix, 1.0)
    adv05, _ = m.build_adv_map(corpus, overlay, fix, 0.5)
    assert adv10 == adv10b, "确定性"
    assert set(adv05) <= set(adv10), "前缀嵌套 0.5 ⊂ 1.0"
    assert len(adv10) <= 16 and len(adv10) > 0
    fix_cols = set()
    for uid in fix:
        spec = overlay.get("tables", {}).get(uid)
        if spec:
            base = len(corpus[uid]["inj_header"]) - len(spec["cols"])
            fix_cols.update((uid, base + i) for i in range(len(spec["cols"])))
    assert set(adv10) <= fix_cols, "只取 fix 碰撞列（更正口径）"
    for (uid, ci), tgt in adv10.items():
        true_c = next(e["true_canonical"] for e in k10 if e["uid"] == uid and e["col"] == ci)
        assert tgt != true_c, "对抗目标必须非真值"
        assert tgt in corpus[uid]["canonicals"]


def test_adv_rate_zero_noop():
    m = _load()
    adv, k = m.build_adv_map({}, {}, [], 0.0)
    assert adv == {} and k == []
