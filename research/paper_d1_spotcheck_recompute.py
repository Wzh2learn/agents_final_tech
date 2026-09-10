import json, io, hashlib, os

# --- F04 纪律改造 (2026-09-10, TASK-20260910-A4A5A4W 修复包 ④, 见 research/spotcheck_lib.py) ---
#  (1) 输入/输出可重定向: SPOTCHECK_OUT 让验收方把抽验工件写到仓外,
#      不覆盖 logs/graph/eval/ 下的审计证据 (历史默认路径与文件名不变)。
#  (2) 恒真/存在性补充项用 ck(..., gate=False) 登记为 OBSERVE, 不入 PASS 分母。
#  (3) 结尾给出**退出码** (改前本脚本 sys.exit 出现 0 次 => 抽验失败对上游不可见)。
import sys as _sys
def _env_path(var, default):
    import os as _os
    v = _os.environ.get(var)
    return v if v else default
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = _env_path("SPOTCHECK_ARTIFACT", os.path.join(R, "logs", "graph", "eval", "d1_mutant_validity_audit.json"))
T2 = _env_path("SPOTCHECK_T2", os.path.join(R, "logs", "graph", "eval", "t2_visibility_sensitivity.json"))
d = json.load(open(ART, encoding="utf-8"))
pay = d["payload"]
out = []
def ck(name, ok, detail, gate=True):
    """gate=False => OBSERVE 行: 描述性/存在性补充, 不入 PASS 分母 (F04 纪律 4)。"""
    out.append((("PASS " if ok else "FAIL ") if gate else "OBSERVE ") + name + " :: " + str(detail)[:260])
    return ok

# 1. payload digest recompute (recipe per W2 assemble: dumps ensure_ascii=False sort_keys default separators)
stored = d.get("payload_sha256")
calc = hashlib.sha256(json.dumps(pay, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
ck("payload_sha256_recompute", calc == stored, {"stored": str(stored)[:16], "calc": calc[:16]})

# 2. three-way counts from per-injection table
inj = pay.get("injections") or pay.get("injection_table") or pay.get("per_injection")
if inj is None:
    for k, v in pay.items():
        if isinstance(v, list) and len(v) == 118:
            inj = v; break
cls = {}
uids_equiv = []
for r in inj:
    c = r.get("class") or r.get("cls") or r.get("category")
    cls[c] = cls.get(c, 0) + 1
    if c == "E":
        uids_equiv.append(r.get("uid"))
ck("counts_from_table", cls.get("H") == 85 and cls.get("E") == 7 and cls.get("HI") == 26 and sum(cls.values()) == 118, cls)

# 3. equivalence set vs T2 frozen
t2 = json.load(open(T2, encoding="utf-8"))
t2eq = set(x["uid"] for x in t2["payload" if "payload" in t2 else "e2_2_equivalence_correction"]["e2_2_equivalence_correction"]["equivalent_list"]) if "payload" in t2 else set(x["uid"] for x in t2["e2_2_equivalence_correction"]["equivalent_list"])
ck("equiv_set_matches_t2_frozen", set(uids_equiv) == t2eq and len(uids_equiv) == 7, {"d1": len(uids_equiv), "t2": len(t2eq), "equal": set(uids_equiv) == t2eq})

# 4. OCR all HI
ocr_hi = all((r.get("class") or r.get("cls") or r.get("category")) == "HI" for r in inj if r.get("type") == "ocr_similar")
n_ocr = sum(1 for r in inj if r.get("type") == "ocr_similar")
ck("ocr_all_HI", ocr_hi and n_ocr == 13, {"n_ocr": n_ocr})

# 5. mutant table
mut = pay.get("mutants") or pay.get("mutant_table") or pay.get("checkpoint_mutants")
if isinstance(mut, list):
    mm = {m.get("id"): (m.get("classification") or m.get("class") or m.get("cls")) for m in mut}
else:
    mm = mut
ck("mutant_classification", mm.get("M7_nf_fail_3") == "MU" and sum(1 for v in mm.values() if v == "MO") == 8 and len(mm) == 9, mm)

# 6. gates + prereg
g = d["gates"]
ck("gates_all_pass", g.get("all_pass") is True, json.dumps(g, ensure_ascii=False)[:200])
pr = d.get("prereg_predicates", {})
ck("prereg_present", len(pr) >= 5, list(pr.keys()))

print("\n".join(out))
_gating = [o for o in out if not o.startswith("OBSERVE")]
_res = sum(1 for o in _gating if o.startswith("PASS"))
_fail = sum(1 for o in _gating if o.startswith("FAIL"))
print("\nD1 spotcheck: %d/%d PASS (gating 分母; OBSERVE 不入分母 %d 项; FAIL %d)" % (
    _res, len(_gating), len(out) - len(_gating), _fail))
if not _gating:
    print("FAIL: 零 gating 项 —— 没有闸门的抽验不算通过")
    raise SystemExit(2)
raise SystemExit(0 if _fail == 0 else 1)
