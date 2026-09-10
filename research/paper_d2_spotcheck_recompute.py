import json, io, hashlib, os

# --- F04 纪律改造 (2026-09-10, TASK-20260910-A4A5A4W 修复包 ④; 引擎见 research/spotcheck_lib.py) ---
#  (1) 输入/输出路径可用环境变量重定向 (SPOTCHECK_ARTIFACT / SPOTCHECK_OUT 等):
#      默认路径与文件名**不变**, 但验收方能把抽验工件写到仓外, 不覆盖 logs/graph/eval/ 下的审计证据。
#  (2) 恒真项与存在性补充项用 ck(..., gate=False) 登记为 OBSERVE, 不入 PASS 分母。
#  (3) 结尾给出**退出码** (改前本脚本 sys.exit 出现 0 次 => 抽验失败对上游完全不可见)。
import sys as _sys
def _env_path(var, default):
    _v = __import__("os").environ.get(var)
    return _v if _v else default
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = _env_path("SPOTCHECK_ARTIFACT", os.path.join(R, "logs", "graph", "eval", "d2_cross_matcher_det.json"))
D1 = _env_path("SPOTCHECK_D1", os.path.join(R, "logs", "graph", "eval", "d1_mutant_validity_audit.json"))
d = json.load(open(ART, encoding="utf-8"))
p = d["payload"]
out = []
def ck(name, ok, detail, gate=True):
    """gate=False => OBSERVE 行: 描述性/存在性补充, 不入 PASS 分母 (F04 纪律 2)。"""
    out.append((("PASS " if ok else "FAIL ") if gate else "OBSERVE ") + name + " :: " + str(detail)[:240])

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
ck("transition_rows_33", n33 == 33, {"rows": n33})
mct = p["matcher_class_transitions"]
# 改前靠 for/else 走通后 ck(..., True) —— 条件恒真且不可审计。现显式算出实测量再断言。
_totals = {m: sum(sum(b2.values()) for b2 in blk["matrix_prod_to_k"].values()) for m, blk in mct.items()}
ck("transition_totals_all_33", all(v == 118 for v in _totals.values()), _totals)

print("\n".join(out))
_gating = [o for o in out if not o.startswith("OBSERVE")]
_res = sum(1 for o in _gating if o.startswith("PASS"))
_fail = sum(1 for o in _gating if o.startswith("FAIL"))
print("\nD2-A spotcheck: %d/%d PASS (gating 分母; OBSERVE 不入分母 %d 项; FAIL %d)"
      % (_res, len(_gating), len(out) - len(_gating), _fail))
if not _gating:
    print("FAIL: 零 gating 项 —— 没有闸门的抽验不算通过"); raise SystemExit(2)
raise SystemExit(0 if _fail == 0 else 1)