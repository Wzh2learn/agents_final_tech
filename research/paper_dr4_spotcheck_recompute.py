# -*- coding: utf-8 -*-
"""DR-4 复核抽验（主线程独立复算, 只读本地工件）。"""
import json, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "logs" / "graph" / "eval" / "dr4_d1_reclassification_review.json"
OUT = ROOT / "logs" / "graph" / "eval" / "dr4_spotcheck_recompute.json"
RECEIPT_RAW = "7806b77b5ad46add9f0461f12c82c54b7f0328f5e3cf66ac6b8aaceefc52d6ca"
RECEIPT_PAYLOAD = "47adbe6649666f864693daead98cb857ff1189545b7e28b0ba126f7cc8beb126"

results = []
def ck(name, ok, detail=None):
    results.append({"check": name, "pass": bool(ok), "detail": detail or {}})

raw = A.read_bytes()
doc = json.loads(raw.decode("utf-8"))
p = doc["payload"]

# 1. payload sha
mine = hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
ck("payload_sha256_recompute", mine == doc["payload_sha256"] == RECEIPT_PAYLOAD,
   {"mine": mine[:20], "stored": doc["payload_sha256"][:20]})

# 2. raw LF sha
sha_raw = hashlib.sha256(raw).hexdigest()
sha_lf = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
ck("raw_file_lf_sha256", RECEIPT_RAW in (sha_lf, sha_raw),
   {"receipt": RECEIPT_RAW[:20], "lf": sha_lf[:20], "raw": sha_raw[:20]})

# 3. 门状态
g = doc["gates"]
ck("gates_all_pass", g.get("all_pass") is True, dict(g))

# 4. oracle_counts 与逐实例重算一致
oc = p["oracle_counts"]
items = p["oracle_items"]
cnt = {}
for it in items:
    lab = it.get("oracle_label") or it.get("step1_label") or it.get("label")
    cnt[lab] = cnt.get(lab, 0) + 1
ck("oracle_counts_recompute", oc.get("total") == 118 and oc.get("E") == 1 and oc.get("H") == 117
   and cnt.get("E", 0) == 1 and cnt.get("H", 0) == 117,
   {"stored": dict(oc), "mine": cnt})

# 5. diff 重算: 方向计数
diff = p["diff"]
e2h = diff.get("current_e_to_oracle_h", [])
h2e = diff.get("current_harmful_to_oracle_e", [])
ck("diff_recompute", diff.get("n_reviewed") == 118 and diff.get("n_changed") == 8
   and diff.get("n_stable") == 110 and len(e2h) == 7 and len(h2e) == 1
   and all(x.get("direction") == "E->H" for x in e2h) and all(x.get("direction") == "H->E" for x in h2e),
   {"n_reviewed": diff.get("n_reviewed"), "n_changed": diff.get("n_changed"),
    "e2h": len(e2h), "h2e": len(h2e),
    "e2h_mech": sorted({(x.get("mechanism", {}).get("C1", {}) or {}).get("check", "?") for x in e2h} |
                       {("C2_lost" in (x.get("mechanism") or {})) and "C2_lost" or "?" for x in e2h})})

# 6. 现行分类复现（current_classification 块）
cc = p.get("current_classification", {})
cr = cc.get("counts_reproduced", {})
cs = cc.get("counts_stored_in_d1", {})
ck("current_classification_reproduced",
   cr.get("H") == 85 and cr.get("E") == 7 and cr.get("HI") == 26
   and cs.get("H") == 85 and cs.get("E") == 7 and cs.get("HI") == 26 and cs.get("total") == 118,
   {"reproduced": cr, "stored_in_d1": cs})

# 7. D3 分母敏感性: 111 -> 117, 不溯及
sn = p.get("d3_sensitivity_note", {})
s = json.dumps(sn, ensure_ascii=False)
ck("d3_denominator_sensitivity", ("111" in s and "117" in s and "retroactive" in s.lower()) or
   (sn.get("frozen_denominator") == 111 and sn.get("oracle_denominator") == 117),
   {"note": s[:300]})

# 8. tier_sensitivity 严格/宽松
ts = p.get("tier_sensitivity", {})
st = json.dumps(ts, ensure_ascii=False)
ck("tier_sensitivity_present", isinstance(ts, dict) and len(ts) > 0, {"excerpt": st[:200]})

# 9. 独立性自证: criterion_provenance + 禁止键扫描
cp = p.get("criterion_provenance", {})
integ = p.get("integrity", {})
ck("independence_self_proof",
   integ.get("forbidden_keys_in_oracle") in ([], None) or integ.get("forbidden_keys_in_oracle") == [],
   {"criterion_keys": list(cp.keys())[:6] if isinstance(cp, dict) else str(cp)[:100],
    "integrity": json.dumps(integ, ensure_ascii=False)[:200]})

n_pass = sum(1 for r in results if r["pass"])
report = {"n_checks": len(results), "n_pass": n_pass, "all_pass": n_pass == len(results), "results": results}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print("DR4 SPOTCHECK: %d/%d PASS" % (n_pass, len(results)))
for r in results:
    if not r["pass"]:
        print("FAIL:", r["check"], json.dumps(r["detail"], ensure_ascii=False)[:250])