# -*- coding: utf-8 -*-
"""PSO question-set search v0 (landing point 2; patent embodiment-3 data feed).

Particle = binary selection vector z in {0,1}^M over the candidate question
bank (16 deterministic + NF + judge samples + adversarial canary ids).
Fitness J2(z) = (1 - keep_rate(z)) + lam2*(|z|/M) + coverage penalty,
keep_rate = fraction of QA-tree mutants (M2..M8 of the K2 v1 discrimination
suite) still detectable under subset z: mutant m detected iff every target
leaf of m retains >=1 selected question contributing to that leaf.
Parse-tree mutants (M1/M9) are artifact-level (M1 regression), outside the
question dimension -> documented exclusion, not counted in keep_rate.

Pure stdlib. Deterministic seed. No network, no client data.
Output: logs/graph/eval/pso_question_set_v0.json
"""
import json, math, random, time, pathlib, sys, collections

REPO = pathlib.Path(__file__).resolve().parents[2]
EVAL = REPO / "logs" / "graph" / "eval"
DISC = EVAL / "checkpoint_discrimination_report.json"
DET = EVAL / "m2_deterministic_report.json"
OUT = EVAL / "pso_question_set_v0.json"

QA_MUTANT_PREFIX = ("M2_", "M3_", "M4_", "M5_", "M6_", "M7_", "M8_")
LAM2 = 0.3          # patent embodiment 5.3.1 caliber
N_PARTICLES = 30    # patent embodiment caliber
N_ITER = 50
SEED = 20260825

LEAF_BY_CHECK = {
    "exact_numeric": "qa.numeric.exact",
    "source_required": "qa.retrieval.source_required",
    "refusal_expected": "qa.refusal.deterministic",
    "number_grounding": "qa.numeric.number_grounding",
}
COVERAGE_TYPES = ["exact_numeric", "source_required", "refusal_expected",
                  "number_grounding", "judge"]

def load_items(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d.get("results", d.get("questions", []))

def build_bank():
    bank = {}  # qid -> {"leaves": set, "types": set}
    for it in load_items(DET):
        qid = it.get("id", "?")
        leaves, types = set(), set()
        for ch in it.get("checks", []):
            t = ch.get("type")
            if t in LEAF_BY_CHECK:
                leaves.add(LEAF_BY_CHECK[t]); types.add(t)
        if leaves or types:
            bank[qid] = {"leaves": leaves, "types": types}
    # NF report (glob-tolerant)
    for nf in sorted(EVAL.glob("*nf_report*.json")):
        try:
            for it in load_items(nf):
                qid = it.get("id", "?")
                e = bank.setdefault(qid, {"leaves": set(), "types": set()})
                e["leaves"].add("qa.numeric.number_grounding")
                e["types"].add("number_grounding")
        except Exception:
            pass
    # judge report (glob-tolerant): judge leaves per judged question
    for jg in sorted(EVAL.glob("m2_judge_report*.json")):
        try:
            for it in load_items(jg):
                qid = it.get("id", "?")
                e = bank.setdefault(qid, {"leaves": set(), "types": set()})
                for leaf in ("qa.faithfulness.judge", "qa.citation.judge"):
                    e["leaves"].add(leaf)
                if "refusal" in qid:
                    e["leaves"].add("qa.refusal.judge")
                e["types"].add("judge")
        except Exception:
            pass
    # adversarial canary fallback entries (public ids only)
    adv = {"adv_refusal": ({"qa.refusal.deterministic"}, {"refusal_expected"}),
           "adv_ocr_meta": ({"qa.retrieval.source_required"}, {"source_required"}),
           "adv_cross_doc": ({"qa.retrieval.source_required"}, {"source_required"})}
    for qid, (lv, ty) in adv.items():
        e = bank.setdefault(qid, {"leaves": set(), "types": set()})
        e["leaves"] |= lv; e["types"] |= ty
    return bank

def load_qa_mutants():
    d = json.loads(DISC.read_text(encoding="utf-8"))
    ms = []
    for m in d.get("mutants", []):
        if not m["id"].startswith(QA_MUTANT_PREFIX):
            continue
        targets = set()
        for h in m.get("target_hits", []):
            targets.add(h["leaf"])
        for h in m.get("graded_hits", []):
            targets.add(h["leaf"])
        ms.append({"id": m["id"], "targets": targets, "verdict": m.get("verdict")})
    return ms

def keep_rate(z, bank_ids, bank, mutants):
    sel = {bank_ids[i] for i, v in enumerate(z) if v > 0.5}
    leaf_covered = set()
    for q in sel:
        leaf_covered |= bank[q]["leaves"]
    hit = 0
    for m in mutants:
        if m["targets"] and m["targets"] <= leaf_covered:
            hit += 1
    return hit / len(mutants) if mutants else 1.0

def coverage_violations(z, bank_ids, bank):
    sel_types = set()
    for i, v in enumerate(z):
        if v > 0.5:
            sel_types |= bank[bank_ids[i]]["types"]
    return sum(1 for t in COVERAGE_TYPES if t not in sel_types)

def fitness(z, bank_ids, bank, mutants, budget):
    size = sum(1 for v in z if v > 0.5)
    kr = keep_rate(z, bank_ids, bank, mutants)
    over = max(0, size - budget)
    return (1.0 - kr) + LAM2 * size / len(z) + 0.5 * coverage_violations(z, bank_ids, bank) + 1.0 * over

def sigmoid(x):
    if x > 30: return 1.0
    if x < -30: return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def pso(bank_ids, bank, mutants, budget, rng):
    M = len(bank_ids)
    xs, vs, pbests, pbest_f = [], [], [], []
    for _ in range(N_PARTICLES):
        x = [1.0 if rng.random() < min(0.5, budget / M) else 0.0 for _ in range(M)]
        xs.append(x); vs.append([rng.uniform(-1, 1) for _ in range(M)])
        f = fitness(x, bank_ids, bank, mutants, budget)
        pbests.append(x[:]); pbest_f.append(f)
    gi = min(range(N_PARTICLES), key=lambda i: pbest_f[i])
    gbest, gbest_f = pbests[gi][:], pbest_f[gi]
    trace = []
    for it in range(N_ITER):
        w = 0.9 - 0.5 * it / max(1, N_ITER - 1)
        for i in range(N_PARTICLES):
            for j in range(M):
                r1, r2 = rng.random(), rng.random()
                vs[i][j] = w * vs[i][j] + 1.5 * r1 * (pbests[i][j] - xs[i][j]) + 1.5 * r2 * (gbest[j] - xs[i][j])
                xs[i][j] = 1.0 if rng.random() < sigmoid(vs[i][j]) else 0.0
            f = fitness(xs[i], bank_ids, bank, mutants, budget)
            if f < pbest_f[i]:
                pbest_f[i] = f; pbests[i] = xs[i][:]
                if f < gbest_f:
                    gbest_f = f; gbest = xs[i][:]
        trace.append({"iter": it, "gbest_f": round(gbest_f, 4),
                      "gbest_size": int(sum(1 for v in gbest if v > 0.5)),
                      "keep_rate": round(keep_rate(gbest, bank_ids, bank, mutants), 4)})
    return gbest, gbest_f, trace

def greedy(bank_ids, bank, mutants, budget):
    # baseline: greedy set cover on mutant target leaves
    need = set()
    for m in mutants: need |= m["targets"]
    sel, covered = [], set()
    pool = list(range(len(bank_ids)))
    while len(sel) < budget and covered != need and pool:
        best_i, best_gain = None, 0
        for i in pool:
            gain = len((bank[bank_ids[i]]["leaves"] & need) - covered)
            if gain > best_gain:
                best_gain, best_i = gain, i
        if best_i is None: break
        sel.append(best_i); covered |= bank[bank_ids[best_i]]["leaves"]; pool.remove(best_i)
    z = [1.0 if i in sel else 0.0 for i in range(len(bank_ids))]
    return z, fitness(z, bank_ids, bank, mutants, budget)

def main():
    t0 = time.time()
    deadline = time.mktime(time.strptime("03:55", "%H:%M")) if time.strftime("%H%M") < "2300" else None
    bank = build_bank()
    bank_ids = sorted(bank.keys())
    mutants = load_qa_mutants()
    if not mutants:
        print("[fatal] no QA mutants found - run eval_checkpoint_discrimination.py first", file=sys.stderr)
        return 2
    rng = random.Random(SEED)
    results = {}
    for B in (4, 6, 8, 10, 12):
        if B > len(bank_ids): continue
        z, f, trace = pso(bank_ids, bank, mutants, B, rng)
        zg, fg = greedy(bank_ids, bank, mutants, B)
        sel = [bank_ids[i] for i, v in enumerate(z) if v > 0.5]
        results[f"B={B}"] = {
            "pso_subset": sel, "pso_size": len(sel),
            "pso_fitness": round(f, 4), "pso_keep_rate": round(keep_rate(z, bank_ids, bank, mutants), 4),
            "greedy_size": int(sum(1 for v in zg if v > 0.5)),
            "greedy_fitness": round(fg, 4),
            "greedy_keep_rate": round(keep_rate(zg, bank_ids, bank, mutants), 4),
            "convergence_tail": trace[-3:],
        }
    # per-question signal rank: how many QA mutants each question covers
    sig = collections.Counter()
    for m in mutants:
        for qid in bank_ids:
            if m["targets"] & bank[qid]["leaves"]:
                sig[qid] += 1
    payload = {
        "meta": {"name": "pso-question-set-search", "version": "v0",
                 "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "caliber": "docs/33 K5 landing 2 / 2026-08-18 proposal J2; lam2=0.3, 30 particles x 50 iter (patent 5.3.1)",
                 "bank_size": len(bank_ids), "qa_mutants": [m["id"] for m in mutants],
                 "note": "parse-tree mutants (M1/M9) excluded: artifact-level, outside question dimension",
                 "runtime_s": round(time.time() - t0, 2)},
        "question_signal_rank": sorted(
            [{"q": q, "mutants_covered": sig[q], "leaves": sorted(bank[q]["leaves"])} for q in bank_ids],
            key=lambda r: -r["mutants_covered"]),
        "results_by_budget": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"bank": len(bank_ids), "mutants": len(mutants),
                      "B=8": results.get("B=8", {}).get("pso_keep_rate"),
                      "min_full_keep_budget": next(
                          (k for k, v in results.items() if v["pso_keep_rate"] >= 1.0), None)},
                     ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
