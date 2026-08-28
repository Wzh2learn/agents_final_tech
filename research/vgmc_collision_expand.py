#!/usr/bin/env python3
"""B 扩碰撞语料（危害梯度）: 构造新共享变体对。

预注册（2026-08-29, 照 2026-08-29_collision_expansion_design.md §1）:
- seed=20260829; ρ ∈ {0.5, 1.0}（对照 ρ≈0 = ADV 窗数据）
- 新共享变体 = fix 与 meas 都有的 canonical 的变体（OCR 型单字符扰动）
- 放置 = 一个含该 canonical 的 meas 表 + 一个含它的 fix 表, 数据 = 真值列复制
- ρ = 可候选对（去重 canonical）中被共享的比例
- 产出 = 基础 overlay + 新共享移植列（shared=true, expansion=2）, 独立文件不覆盖
"""
import copy
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
SEED = 20260829
RHOS = {"rho05": 0.5, "rho10": 1.0}
REPL = "0123456789@#№£" + "abcdefghijklmnopqrstuvwxyz"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def mutate(A, seed):
    chars = list(A)
    idxs = [i for i, ch in enumerate(chars) if ch.isalnum()]
    rng = random.Random(f"MUTATE2:{seed}:{A}")
    rng.shuffle(idxs)
    for i in idxs:
        repl = rng.choice(REPL)
        if repl != chars[i]:
            chars[i] = repl
            break
    return "".join(chars)


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    base = json.loads((EVAL / "vgmc_collision_overlay.json").read_text(encoding="utf-8"))
    corpus = vg.load_corpus(base)
    fix, meas = vg.split_uids(list(corpus.keys()))
    norm = vg.mp.normalize_header
    # 可候选对: 去重, 记两侧持有表与真值列索引
    fix_canons, meas_canons = {}, {}
    for u in fix:
        for c in corpus[u]["canonicals"]:
            fix_canons.setdefault(norm(c), []).append(u)
    for u in meas:
        for c in corpus[u]["canonicals"]:
            meas_canons.setdefault(norm(c), []).append(u)
    elig = sorted(set(fix_canons) & set(meas_canons))
    # 变体存在性集合
    all_headers = {h for u in corpus for h in corpus[u]["inj_header"]}
    specs = []
    for n in elig:
        A = next(c for u in fix for c in corpus[u]["canonicals"] if norm(c) == n)
        v = mutate(A, SEED)
        if v in all_headers:
            continue
        specs.append({"variant": v, "canon": A, "norm": n,
                      "meas_h": meas_canons[n], "fix_h": fix_canons[n]})
    for tag, rho in RHOS.items():
        ovl = copy.deepcopy(base)
        n_shared, tables_hit = 0, set()
        for idx, s in enumerate(specs):
            rng = random.Random(f"EXPAND2:{SEED}:{s['variant']}")
            if rng.random() >= rho:
                continue
            mc = [m for m in s["meas_h"] if s["variant"] not in corpus[m]["inj_header"]]
            fc = [f for f in s["fix_h"] if s["variant"] not in corpus[f]["inj_header"]]
            if not mc or not fc:
                continue
            tgt_m, tgt_f = rng.choice(mc), rng.choice(fc)
            for tgt in (tgt_m, tgt_f):
                di = next(i for i, h in enumerate(corpus[tgt]["orig_header"])
                          if norm(h) == s["norm"])
                ovl["tables"].setdefault(tgt, {"cols": []})["cols"].append(
                    {"header": s["variant"], "true_canonical": s["canon"],
                     "source_uid": "EXPAND2", "data_col_idx": di,
                     "shared": True, "expansion": 2})
            n_shared += 1
            tables_hit.update([tgt_m, tgt_f])
        ovl["meta"] = {**base["meta"], "expansion": {"seed": SEED, "rho": rho,
                       "eligible_canons": len(elig), "shareable_unique": len(specs),
                       "shared_n": n_shared, "tables_hit": len(tables_hit),
                       "generated": time.strftime("%Y-%m-%d %H:%M:%S")}}
        out = EVAL / f"vgmc_collision_overlay_v2_{tag}.json"
        out.write_text(json.dumps(ovl, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{tag}: eligible={len(elig)} shareable={len(specs)} shared={n_shared} tables={len(tables_hit)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
