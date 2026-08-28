"""碰撞语料生成器（扩语料碰撞实验, 设计稿 2026-08-27_collision_corpus_exp_design.md）。

在 95 注入表上叠加"移植列"overlay: meas 表 +2 列 / fix 表 +1 列,
移植列 = 他表注入变体（真值 canonical 存在于目标表）, 数据复制目标表真值列。
只写 overlay 工件, 不触原语料（95 表结构逐字节不变）。全合成, 甲方零进入。
"""
import hashlib
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "logs" / "graph" / "eval" / "vgmc_collision_overlay.json"
SEED = 20260828
E_MEAS, E_FIX = 4, 2
N_MEAS = 35  # 与 vgmc_exp1.split_uids 同口径


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    import m1_statement_parser as mp
    corpus = vg.load_corpus()
    fix_uids, meas_uids = vg.split_uids(list(corpus.keys()))
    assert len(meas_uids) == N_MEAS
    pool: list[dict] = []
    for uid, rec in corpus.items():
        for e in rec["entries"]:
            pool.append({"variant": rec["inj_header"][e["col"]],
                         "true_canonical": e["original"], "source_uid": uid})

    def canon_index(rec: dict, canonical: str):
        nk = mp.normalize_header(canonical)
        for i, h in enumerate(rec["orig_header"]):
            if mp.normalize_header(h) == nk:
                return i
        return None

    tables: dict[str, dict] = {}
    n_cols = 0
    for uid in sorted(corpus):
        rec = corpus[uid]
        e_n = E_MEAS if uid in set(meas_uids) else E_FIX
        own = {(rec["inj_header"][e["col"]]) for e in rec["entries"]}
        canon_set = {mp.normalize_header(c) for c in rec["canonicals"]}
        cols, used = [], set()
        for slot in range(e_n):
            rng = random.Random(f"{SEED}:{uid}:{slot}")
            cands = [p for p in pool
                     if p["source_uid"] != uid and p["variant"] not in own
                     and p["variant"] not in used
                     and mp.normalize_header(p["true_canonical"]) in canon_set]
            if not cands:
                continue
            p = rng.choice(cands)
            used.add(p["variant"])
            di = canon_index(rec, p["true_canonical"])
            if di is None:
                continue
            cols.append({"header": p["variant"], "true_canonical": p["true_canonical"],
                         "source_uid": p["source_uid"], "data_col_idx": di})
            n_cols += 1
        if cols:
            tables[uid] = {"cols": cols}
    overlay = {"meta": {"name": "vgmc-collision-overlay", "seed": SEED,
                        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "e_meas": E_MEAS, "e_fix": E_FIX, "n_tables": len(tables),
                        "n_cols": n_cols,
                        "caliber": "全合成移植列（数据复制目标表真值列）; 甲方零进入"},
               "tables": tables}
    OUT.write_text(json.dumps(overlay, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"n_tables": len(tables), "n_cols": n_cols,
                      "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "out": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
