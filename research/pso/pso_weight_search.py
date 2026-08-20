#!/usr/bin/env python3
"""PSO weight search v0 (K5/K7 landing point 1; patent embodiment-3 data feed).

Fitness = mean Root-Score separation between normal set Z (baseline leaf scores)
and defect mutant set D (K2 v1 discrimination suite leaf deltas), aggregated by
Algorithm 1 (sibling-normalized bottom-up weighted mean) - identical to
scripts/eval_checkpoint_aggregate.py, re-expressed as a pure function of
(leaf scores, node weights) so PSO can search the weight space.

Verification gate: with baseline weights, this script must reproduce every
mutant root_score in checkpoint_discrimination_report.json before PSO runs.

Pure stdlib. No network, no inference, no client data (leaf scores are eval
metrics over synthetic mutants + baseline artifacts).
"""
import json, random, copy, datetime, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
TREES_PATH = REPO / "config" / "eval_checkpoint_trees.json"
DISC_PATH = REPO / "logs" / "graph" / "eval" / "checkpoint_discrimination_report.json"
OUT_JSON = REPO / "logs" / "graph" / "eval" / "pso_weight_search_v0.json"

def iter_nodes(node):
    yield node
    for c in node.get("children", []):
        yield from iter_nodes(c)

def aggregate(trees, leaf_scores, weight_over=None):
    """Algorithm 1 as pure function. weight_over: node_id -> weight override.
    Returns (per_tree_roots {tree_id: root}, overall_root)."""
    per_tree = {}
    for tree in trees:
        def dfs(node):
            ch = node.get("children", [])
            if not ch:
                return float(leaf_scores[node["id"]])
            pairs = []
            for c in ch:
                s = dfs(c)
                w = weight_over.get(c["id"], c.get("weight", 1)) if weight_over else c.get("weight", 1)
                pairs.append((s, w))
            wsum = sum(w for _, w in pairs) or 1.0
            return sum(s * w for s, w in pairs) / wsum
        per_tree[tree["id"]] = dfs(tree)
    wsum = sum(t.get("weight", 1) for t in trees) or 1.0
    overall = sum(per_tree[t["id"]] * t.get("weight", 1) for t in trees) / wsum
    return per_tree, overall

def collect_weight_nodes(trees):
    ids = []
    for t in trees:
        for n in iter_nodes(t):
            if "weight" in n and n.get("children"):
                ids.append(n["id"])
    return ids

def main():
    cfg = json.loads(TREES_PATH.read_text(encoding="utf-8"))
    trees = cfg["trees"]
    disc = json.loads(DISC_PATH.read_text(encoding="utf-8"))
    base = dict(disc["control"]["live_leaves"])
    mutants = disc["mutants"]

    def mutant_scores(m):
        ls = dict(base)
        for hit in (m.get("target_hits", []) + m.get("graded_hits", [])):
            lf = hit["leaf"]
            if lf in ls:
                ls[lf] = max(0.0, min(10.0, ls[lf] + hit["delta"]))
        for lf, d in (m.get("non_target_moves") or {}).items():
            if lf in ls:
                ls[lf] = max(0.0, min(10.0, ls[lf] + d))
        return ls

    # live-leaf pruning variant: restrict each tree to live leaves only
    live = set(base)
    def prune(tree):
        t = copy.deepcopy(tree)
        def rec(n):
            ch = n.get("children", [])
            if not ch:
                return n["id"] in live
            kept = [c for c in ch if rec(c)]
            n["children"] = kept
            return bool(kept)
        rec(t)
        return t
    trees_live = [prune(t) for t in trees]

    # --- verification gate: which tree caliber reproduces report roots? ---
    variant = None
    for name, tt in (("all_leaves_missing_score", None), ("live_only", trees_live)):
        ok = True
        for m in mutants:
            ls = mutant_scores(m)
            if name == "all_leaves_missing_score":
                full = dict(ls)
                for t in trees:
                    for n in iter_nodes(t):
                        if not n.get("children") and n["id"] not in full:
                            full[n["id"]] = float(n.get("missing_score", 5.0))
                per, _ = aggregate(trees, full, None)
            else:
                per, _ = aggregate(tt, ls, None)
            rep = m.get("root_scores", {})
            for tid, val in rep.items():
                if abs(per.get(tid, -99) - val) > 0.01:
                    ok = False
        if ok:
            variant = name
            break
    if variant is None:
        print("VERIFY FAIL: neither caliber reproduces report roots")
        sys.exit(1)
    print(f"VERIFY PASS via variant={variant}")

    if variant == "live_only":
        work_trees = trees_live
        def score_of(ls, w):
            return aggregate(work_trees, ls, w)
    else:
        work_trees = trees
        def _fill(ls):
            full = dict(ls)
            for t in trees:
                for n in iter_nodes(t):
                    if not n.get("children") and n["id"] not in full:
                        full[n["id"]] = float(n.get("missing_score", 5.0))
            return full
        def score_of(ls, w):
            return aggregate(work_trees, _fill(ls), w)

    D = [mutant_scores(m) for m in mutants]
    Z = dict(base)

    def fitness(w):
        _, rz = score_of(Z, w)
        sep = 0.0
        for d in D:
            _, rd = score_of(d, w)
            sep += (rz - rd)
        return sep / len(D)  # maximize

    # --- PSO (params per P2 3.2 / patent 5.3.1) ---
    dim_ids = collect_weight_nodes(work_trees)
    DIM = len(dim_ids)
    P, TMAX = 30, 50
    C1 = C2 = 2.0
    W0, W1 = 0.7, 0.4
    EPS = 0.001
    random.seed(20260821)

    def rand_pos():
        return [random.uniform(1.0, 3.0) for _ in range(DIM)]
    def discretize(x):
        return {dim_ids[i]: max(1, min(3, round(x[i]))) for i in range(DIM)}

    X = [rand_pos() for _ in range(P)]
    V = [[random.uniform(-0.5, 0.5) for _ in range(DIM)] for _ in range(P)]
    J = [-fitness(discretize(x)) for x in X]
    pbest = [list(x) for x in X]; pbestJ = list(J)
    g = min(range(P), key=lambda i: J[i]); gbest = list(X[g]); gbestJ = J[g]
    history = []
    iters_to_conv = None
    for t in range(TMAX):
        w = W0 - (W0 - W1) * t / max(TMAX - 1, 1)
        for p in range(P):
            for i in range(DIM):
                r1, r2 = random.random(), random.random()
                V[p][i] = w * V[p][i] + C1 * r1 * (pbest[p][i] - X[p][i]) + C2 * r2 * (gbest[i] - X[p][i])
                X[p][i] += V[p][i]
            j = -fitness(discretize(X[p]))
            J[p] = j
            if j < pbestJ[p]:
                pbestJ[p] = j; pbest[p] = list(X[p])
            if j < gbestJ:
                gbestJ = j; gbest = list(X[p])
        history.append(round(-gbestJ, 6))
        if iters_to_conv is None and len(history) >= 2 and abs(history[-1] - history[-2]) < EPS:
            iters_to_conv = t + 1
    best_w = discretize(gbest)

    base_over = None
    base_fit = fitness(base_over)
    opt_fit = fitness(best_w)
    per_m_base, per_m_opt = [], []
    for m, d in zip(mutants, D):
        _, rzb = score_of(Z, None); _, rdb = score_of(d, None)
        _, rzo = score_of(Z, best_w); _, rdo = score_of(d, best_w)
        per_m_base.append({"id": m["id"], "sep": round(rzb - rdb, 4)})
        per_m_opt.append({"id": m["id"], "sep": round(rzo - rdo, 4)})

    baseline_weights = {}
    for t in work_trees:
        for n in iter_nodes(t):
            if n.get("children") and "weight" in n:
                baseline_weights[n["id"]] = n["weight"]
    diff = {k: {"baseline": baseline_weights[k], "pso": best_w[k]}
            for k in best_w if best_w[k] != baseline_weights.get(k)}

    out = {
        "meta": {
            "name": "pso-weight-search", "version": "v0", "landing": "K5 point 1",
            "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "variant": variant, "n_mutants": len(mutants),
            "params": {"P": P, "Tmax": TMAX, "w": "0.7->0.4", "c1": C1, "c2": C2, "eps": EPS, "seed": 20260821},
            "patent_ref": "2026-08-21_patent_full_revised.md 5.3.3",
        },
        "verify": {"gate": "reproduce discrimination report roots", "result": "PASS", "variant": variant},
        "baseline_separation_overall": round(base_fit, 6),
        "optimized_separation_overall": round(opt_fit, 6),
        "delta_separation": round(opt_fit - base_fit, 6),
        "iterations_to_converge": iters_to_conv,
        "history_best_fitness": history,
        "per_mutant_baseline": per_m_base,
        "per_mutant_optimized": per_m_opt,
        "weight_diff_nodes": diff,
        "n_weight_dims": DIM,
        "best_weights": best_w,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"baseline sep={base_fit:.4f}  optimized sep={opt_fit:.4f}  delta={opt_fit-base_fit:.4f}")
    print(f"iters_to_converge={iters_to_conv}  dims={DIM}  weight_diffs={len(diff)}")
    print(f"report: {OUT_JSON}")

if __name__ == "__main__":
    main()