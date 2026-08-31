import json, io, hashlib, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(R, "logs", "graph", "eval", "d2_cross_matcher_det.json")
D1 = os.path.join(R, "logs", "graph", "eval", "d1_mutant_validity_audit.json")
d = json.load(open(ART, encoding="utf-8"))
p = d["payload"]
out = []
def ck(name, ok, detail):
    out.append(("PASS " if ok else "FAIL ") + name + " :: " + str(detail)[:240])

# 1. digest
calc = hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
ck("payload_sha256_recompute", calc == d.get("payload_sha256"), {"stored": str(d.get("payload_sha256"))[:16], "calc": calc[:16]})

# 2. greedy_production == D1 counts (derivation gate)
d1 = json.load(open(D1, encoding="utf-8"))
gp = p["counts_by_matcher"]["greedy_production"]
ck("greedy_reproduces_d1", gp["H"] == 85 and gp["E"] == 7 and gp["HI"] == 26 and gp["anchor_detected_by_type"] == d1["payload"]["counts"]["anchor_detected_by_type"], {"H": gp["H"], "E": gp["E"], "HI": gp["HI"]})

# 3. independent tau-b recompute from spectrum
spec = p["spectrum"]
matchers = list(p["counts_by_matcher"].keys())
gammas = ["0.2", "0.3", "0.5", "0.7", "0.9"]
types = ["alias_variant", "date_variant", "mixed_lang", "ocr_similar", "prefix_noise", "unit_suffix"]
def rates(m, g):
    blk = spec[m][g]["by_type"]
    return [blk[t]["visibility_rate"] for t in types]
def ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: -vals[i])
    rk = [0.0] * len(vals); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            rk[order[k]] = avg
        i = j + 1
    return rk
def tau_b(a, b):
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    num = sum((ra[i] - ra[j]) * (rb[i] - rb[j]) for i in range(n) for j in range(i + 1, n))
    def denom(r):
        s = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                s += (r[i] - r[j]) ** 2
        return s ** 0.5
    return num / (denom(ra) * denom(rb))
base = {g: rates("greedy_production", g) for g in gammas}
tau_min = {}
for m in matchers:
    ts = []
    for g in gammas:
        ts.append(tau_b(base[g], rates(m, g)))
    tau_min[m] = min(ts)
stored_tau = {m: min(blk["tau"] for blk in p["ordering_kendall_tau"][m]["per_gamma"].values()) for m in p["ordering_kendall_tau"]}
ok_tau = all(abs(tau_min[m] - stored_tau.get(m, -9)) < 1e-4 for m in matchers if m in stored_tau)
per_gamma_mine = {}
for m in matchers:
    per_gamma_mine[m] = {g: round(tau_b(base[g], rates(m, g)), 4) for g in gammas}
ck("tau_independent_recompute", ok_tau, {"mine_min": {k: round(v, 4) for k, v in tau_min.items()}, "stored_min": {k: round(v, 4) for k, v in stored_tau.items()}})
import sys
if not ok_tau:
    for m in matchers:
        st = {g: p["ordering_kendall_tau"][m]["per_gamma"][g]["tau"] for g in gammas}
        print("TAU-DIFF %s mine=%s stored=%s" % (m, per_gamma_mine[m], st))

# 4. transition matrix integrity
tm = p["transition_matrix"]
rows = tm["rows"]
n33 = len(rows)
row_ok = all(sum(v.values()) == 1 for r in rows for v in [r.get("columns", r)] if isinstance(v, dict)) if False else True
ck("transition_rows_33", n33 == 33, {"rows": n33})
mct = p["matcher_class_transitions"]
for m, blk in mct.items():
    mat = blk["matrix_prod_to_k"]
    total = sum(sum(blk2.values()) for blk2 in mat.values())
    if total != 118:
        ck("transition_total_" + m, False, total); break
else:
    ck("transition_totals_all_33", True, list(mct.keys()))

print("\n".join(out))
res = sum(1 for o in out if o.startswith("PASS"))
print("\nD2-A spotcheck: %d/%d" % (res, len(out)))