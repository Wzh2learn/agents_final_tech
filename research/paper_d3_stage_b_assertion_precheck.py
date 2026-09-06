# -*- coding: utf-8 -*-
"""D3 阶段 B 派发前断言预演（加编 3 C3-1 五条硬断言 + 卡文绑定 + 审计拷入字节/sha 复算）。
纪律（F04 新抽验纪律）: 缺键即失败（KeyError → 非零退出）; 无恒真项; 观察项列 INFO 不入 PASS 分母; 任一 FAIL → 退出码 1。
证据级别: recompute=独立重算 / match=存值一致 / exists=字段·文本存在。零端点, 只读冻结工件。"""
import hashlib, io, json, os, sys, datetime
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(ROOT, *a)
def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def load(p):
    with io.open(p, encoding="utf-8") as f: return json.load(f)

D1 = P("logs/graph/eval/d1_mutant_validity_audit.json")
T2 = P("logs/graph/eval/checkpoint_discrimination_tables_v2.json")
D3 = P("logs/graph/eval/d3_matched_fpr_stage_a.json")
DR4 = P("logs/graph/eval/dr4_d1_reclassification_review.json")
CARD = P("docs/experiments/2026-09-01_d3_matched_specificity_card.md")
AUD_LOCAL = P("docs/governance/audit/harness_audit_20260905")
AUD_EXT = r"D:/AIRcommend/JinRongAgents/harness_audit_20260905"
OUT = P("logs/graph/eval/d3_stage_b_assertion_precheck.json")

SILENT15 = [("1fe3e1d6",2),("21c316d6",2),("3c609073",1),("3c609073",3),("44c7c9ef",1),("567a03c7",1),("5fe2c49e",1),("5fe2c49e",2),("68b8d514",1),("6a5e5192",0),("6f9a0eb1",0),("c0f66238",3),("d2bba753",0),("d7d65228",3),("e11338f6",0)]
DIL0_6 = [("24ff90f9",2),("24ff90f9",4),("32cfcadb",2),("32cfcadb",4),("97176853",2),("97176853",4)]
JN2_7 = ["50e78448-3cf5-439c-a609-ee866bd1f05a#2","54c494f7-d731-49bf-b9cd-d494aea72e34#2","5e60c056-5073-441d-8525-7f834deb5c64#0","73a817fc-25df-494d-b0f2-79cfdab34076#1","b5aae4e9-040d-4e55-a42d-39cde217978f#0","e67f7bf2-fc15-4a7a-9856-febb066998fd#4","e9730ea3-e003-4db6-a513-9c9e6f40e371#2"]
JN1_21 = ["%s#%d" % (u, c) for u, c in SILENT15 + DIL0_6]
H2E = "3789d7da#1"

checks = []
def chk(cid, desc, level, passed, detail):
    checks.append({"id": cid, "desc": desc, "evidence_level": level, "pass": bool(passed), "detail": detail})

d1 = load(D1).get("payload") or load(D1)
inj = d1["injections"]
d3p = load(D3).get("payload") or load(D3)
per = d3p["a3_dilution_rescue"]["per_case"]
dr4p = load(DR4).get("payload") or load(DR4)
t2 = load(T2)

# A1: J-N1 21 == silent15(D1) ∪ dil0-6(D3 a3)
s15 = {(r["uid"][:8], r["col"]) for r in inj if r["class"] == "HI" and r["invisibility_mechanism"] == "absorption_silent"}
d06 = {(c["uid_alias"], c["col"]) for c in per if c["single_drop10"] == 0.0}
a1 = (s15 == set(SILENT15)) and (d06 == set(DIL0_6)) and (len(s15 | d06) == 21) and not (s15 & d06)
chk("A1", "J-N1 21 == D1 silent 15 ∪ D3 a3 dilution-0 6（缺键即 KeyError）", "recompute", a1,
    {"silent15_match": s15 == set(SILENT15), "dil06_match": d06 == set(DIL0_6), "union_n": len(s15 | d06), "disjoint": not (s15 & d06),
     "silent_type_split": {t: sum(1 for r in inj if r["class"]=="HI" and r["invisibility_mechanism"]=="absorption_silent" and r["type"]==t) for t in ("ocr_similar","date_variant")}})

# A2: J-N2 7 == D1 E 集 == DR4 E→H keys
e7 = {(r["uid"][:8], r["col"]) for r in inj if r["class"] == "E"}
dr_keys = [c["key"] for c in dr4p["diff"]["current_e_to_oracle_h"]]
jn2_pairs = {(k.split("#")[0][:8], int(k.split("#")[1])) for k in JN2_7}
a2 = (e7 == jn2_pairs) and (sorted(dr_keys) == sorted(JN2_7))
chk("A2", "J-N2 7 == D1 class=E 集 == DR4 diff.current_e_to_oracle_h keys（全 key 逐字）", "recompute", a2,
    {"e7_match": e7 == jn2_pairs, "dr4_keys_match": sorted(dr_keys) == sorted(JN2_7), "n_dr4": len(dr_keys)})

# A3: 21 ∩ 7 = ∅
inter = (set(SILENT15) | set(DIL0_6)) & jn2_pairs
chk("A3", "J-N1 ∩ J-N2 = 空集", "recompute", len(inter) == 0, {"intersection": sorted("%s#%d" % x for x in inter)})

# A4: 28 例 original/injected D1 vs tables_v2 逐例相等
t2map = {}
def walk(o):
    if isinstance(o, dict):
        if isinstance(o.get("uid"), str) and "injections" in o:
            for i in o["injections"]: t2map[(o["uid"][:8], i["col"])] = i
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(t2)
mism = []
need = []
for r in inj:
    full = r["uid"] + "#" + str(r["col"])
    short = r["uid"][:8] + "#" + str(r["col"])
    if full in JN2_7 or short in JN1_21:
        need.append((short, r["original"], r["injected"]))
for short, o1, i1 in need:
    u, c = short.split("#"); t = t2map.get((u, int(c)))
    if t is None: mism.append({"case": short, "problem": "tables_v2 missing"}); continue
    if t["original"] != o1 or t["injected"] != i1:
        mism.append({"case": short, "d1": [o1, i1], "t2": [t["original"], t["injected"]]})
chk("A4", "28 例 original/injected: D1 injections vs tables_v2 同 key 字段逐例相等", "match", len(need) == 28 and not mism,
    {"n_compared": len(need), "mismatches": mism})

# A5: 3789d7da#1 不在调用清单 + 确定性证据字段一致
h2e_t2 = t2map.get(("3789d7da", 1))
dr_h2e = [c for c in dr4p["diff"]["changes"] if c["direction"] == "H->E"]
a5 = (H2E not in JN1_21) and (H2E not in [k.split("#")[0][:8] + "#" + k.split("#")[1] for k in JN2_7]) \
     and h2e_t2 is not None and h2e_t2["visible"] is True and h2e_t2["absorbed"] is False and h2e_t2["match_tier"] == 0 \
     and len(dr_h2e) == 1 and dr_h2e[0]["uid8"] == "3789d7da" and dr_h2e[0]["col"] == 1 and dr_h2e[0]["oracle_label"] == "E"
chk("A5", "H→E 例 3789d7da#1 不在 28 调用清单 + tables_v2 visible/absorbed/match_tier=(true,false,0) + DR4 唯一 H->E oracle=E", "recompute", a5,
    {"in_call_list": H2E in JN1_21, "t2": {k: h2e_t2[k] for k in ("visible","absorbed","match_tier")} if h2e_t2 else None,
     "dr4_h2e_n": len(dr_h2e)})

# A6: 卡加编 3 文本绑定（21 短 key + 7 全 key 逐字在卡内）
card = io.open(CARD, encoding="utf-8").read()
sec = card.split("## 加编 3", 1)[1] if "## 加编 3" in card else ""
missing = [k for k in JN1_21 if k not in sec] + [k for k in JN2_7 if k not in sec]
chk("A6", "卡加编 3 C3-1 含全部 28 key 逐字（21 短 key + 7 全 key）", "exists", bool(sec) and not missing, {"missing": missing, "section_found": bool(sec)})

# A7: 审计四件拷入 = 字节和 53785 + 与外部源 sha 逐件相等（机械钉死 54,785 误报）
names = ["RESUME.md", "AUDIT_REPORT.md", "EVIDENCE.md", "CRITIQUE.md"]
sizes, sha_ok = [], []
for n in names:
    lp, ep = os.path.join(AUD_LOCAL, n), os.path.join(AUD_EXT, n)
    sizes.append(os.path.getsize(lp))
    sha_ok.append(sha_file(lp) == sha_file(ep))
chk("A7", "审计四件拷入: 字节和 == 53785 且与外部源 4/4 sha256 相等", "recompute", sum(sizes) == 53785 and all(sha_ok),
    {"sizes": dict(zip(names, sizes)), "sum": sum(sizes), "sha_match": dict(zip(names, sha_ok))})

all_pass = all(c["pass"] for c in checks)
payload = {"script": "research/paper_d3_stage_b_assertion_precheck.py",
           "ts": datetime.datetime.now().astimezone().isoformat(),
           "purpose": "D3 阶段 B 派发前断言预演（加编 3 C3-1 硬断言 A1-A5 + 卡文绑定 A6 + 审计拷入复算 A7）; 侧线独立复算为旁证（用户 09-06 批复）",
           "inputs_sha256": {os.path.relpath(p, ROOT).replace(os.sep, "/"): sha_file(p) for p in [D1, T2, D3, DR4, CARD]},
           "checks": checks, "n_checks": len(checks), "all_pass": all_pass, "zero_endpoint": True}
blob = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
payload["payload_sha256"] = hashlib.sha256(blob).hexdigest()
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
    f.write("\n")
print(json.dumps({c["id"]: c["pass"] for c in checks}, ensure_ascii=False))
print("all_pass =", all_pass, "| payload_sha256 =", payload["payload_sha256"][:16], "| byte_sum =", sum(sizes))
sys.exit(0 if all_pass else 1)
