import json, io, hashlib, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(R, "logs", "graph", "eval", "d1_mutant_validity_audit.json")
T2 = os.path.join(R, "logs", "graph", "eval", "t2_visibility_sensitivity.json")
d = json.load(open(ART, encoding="utf-8"))
pay = d["payload"]
out = []
def ck(name, ok, detail):
    out.append(("PASS " if ok else "FAIL ") + name + " :: " + str(detail)[:260])
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
res = sum(1 for o in out if o.startswith("PASS"))
print("\nD1 spotcheck: %d/%d PASS" % (res, len(out)))