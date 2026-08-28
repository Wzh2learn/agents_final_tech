"""DPO 偏好对 v0 生成器（设计稿 2026-08-28_dpo_pairs_v0_design.md）。

机械生成零端点; synthetic 标记经 force_inject 同 RNG 确定性重构
（建议流水未携带该字段, 重构口径与 research/vgmc_exp1.py force_inject 逐行一致）。
"""
import importlib.util
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
GEN_SEED = 20260828
FORCE_RATE, FORCE_SEED = 0.5, 20260827
SOURCES = [("noise_L3", "vgmc_noise_L3_checkpoint.json", None),
           ("collision_C1", "vgmc_collision_C1_checkpoint.json", "vgmc_collision_overlay.json")]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def synthetic_target(m, corpus, uid, c):
    rec = corpus[uid]
    rng = random.Random(f"{FORCE_SEED}:{uid}:{c}")
    if rng.random() > FORCE_RATE:
        return None
    e = next((e for e in rec["entries"] if e["col"] == c), None)
    true_c = next((x for x in rec["canonicals"] if e and
                   m.mp.normalize_header(x) == m.mp.normalize_header(e["original"])), None)
    wrong = [x for x in rec["canonicals"] if x != true_c]
    if not wrong:
        return None
    return rng.choice(wrong)


def main() -> int:
    m = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    events, corpora = [], {}
    for regime, fn, ovl in SOURCES:
        overlay = json.loads((EVAL / ovl).read_text(encoding="utf-8")) if ovl else None
        corpus = m.load_corpus(overlay)
        corpora[regime] = corpus
        ck = json.loads((EVAL / fn).read_text(encoding="utf-8"))
        for arm in ("gated", "ungated"):
            for s in ck["arm_" + arm]["sugg_log"]:
                synth = synthetic_target(m, corpus, s["uid"], s["col"])
                events.append({**s, "regime": regime, "arm": arm,
                               "synthetic": synth is not None and s.get("target") == synth})
    pairs: dict[tuple, dict] = {}

    def add_pair(uid, col, chosen, rejected, ptype, ev, flag=None):
        key = (uid, col, json.dumps(chosen, ensure_ascii=False),
               json.dumps(rejected, ensure_ascii=False))
        p = pairs.setdefault(key, {"uid": uid, "col": col, "chosen": chosen,
                                   "rejected": rejected, "types": set(), "sources": [],
                                   "gate_fooled": False})
        p["types"].add(ptype)
        p["sources"].append(f"{ev['regime']}/{ev['arm']}/r{ev['round']}")
        p["gate_fooled"] = p["gate_fooled"] or bool(flag)

    gated = {(e["regime"], e["uid"], e["col"]): e for e in events if e["arm"] == "gated"}
    for e in events:
        if e["arm"] == "gated" and e["reason"] == "gated_fail":
            add_pair(e["uid"], e["col"], {"action": "skip"},
                     {"action": "map_to", "target": e["target"]}, "A", e)
        if e["synthetic"]:
            add_pair(e["uid"], e["col"], {"action": "skip"},
                     {"action": "map_to", "target": e["target"]}, "C", e,
                     flag=(e["arm"] == "gated" and e["reason"] == "gated_pass"))
    for (r1, uid, col), e1 in gated.items():
        for r2 in ("noise_L3", "collision_C1"):
            if r2 <= r1:
                continue
            e2 = gated.get((r2, uid, col))
            if not e2:
                continue
            acc, rej = (e1, e2) if e1["reason"] == "gated_pass" and e2["reason"] == "gated_fail" else \
                       (e2, e1) if e2["reason"] == "gated_pass" and e1["reason"] == "gated_fail" else (None, None)
            if acc and acc.get("target") != rej.get("target"):
                add_pair(uid, col, {"action": "map_to", "target": acc["target"]},
                         {"action": "map_to", "target": rej["target"]}, "B", acc)
    all_cols = {(e["uid"], e["col"]) for e in events}
    paired_cols = {k[:2] for k in pairs}
    by_type = {}
    for p in pairs.values():
        p["types"] = sorted(p["types"])
        for t in p["types"]:
            by_type[t] = by_type.get(t, 0) + 1
    out = {"meta": {"name": "dpo-pairs-v0", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "design": "docs/experiments/2026-08-28_dpo_pairs_v0_design.md",
                    "gen_seed": GEN_SEED, "endpoint_calls": 0,
                    "sources": [f"{r} ({f})" for r, f, _ in SOURCES],
                    "synthetic_reconstruction": "force_inject 同 RNG 重构（种子 20260827, rate 0.5）"},
           "summary": {"n_pairs": len(pairs), "by_type": by_type,
                       "gate_fooled_n": sum(1 for p in pairs.values() if p["gate_fooled"]),
                       "coverage": {"columns_total": len(all_cols),
                                    "columns_paired": len(paired_cols),
                                    "rate": round(len(paired_cols) / len(all_cols), 4)},
                       "source_distribution": {r: sum(1 for p in pairs.values()
                                                      if any(s.startswith(r) for s in p["sources"]))
                                               for r, _f, _o in SOURCES}},
           "pairs": sorted(pairs.values(), key=lambda p: (p["uid"], p["col"]))}
    (EVAL / "dpo_pairs_v0.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
