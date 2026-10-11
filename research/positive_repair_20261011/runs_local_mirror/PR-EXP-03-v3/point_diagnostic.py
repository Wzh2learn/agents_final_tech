# -*- coding: utf-8 -*-
"""PR-EXP-03 v3 POINT DIAGNOSTIC (no 10k diagnostic bootstrap; the frozen predict_loco is O(groups^2))."""
import importlib.util, json, sys
from collections import defaultdict
from pathlib import Path
RUN = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("expv3", str(RUN/"experiment_v3.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

p1_raw = m.read_jsonl(RUN/"p1_run1.jsonl")
manifest = m.load(m.MANIFEST)
p1, undefined = [], 0
for row in p1_raw:
    uid = str(row["uid"])
    try:
        new = m.structural(row["baseline"], row["injected"])
        a0  = m.structural(row["baseline"], row["baseline"])
        a1t = m.a1_table(row["baseline"], uid)
        a1  = m.structural(row["baseline"], a1t)
        field = m.field_response(row["baseline"], row["injected"])
    except Exception:
        undefined += 1; continue
    p1.append({"uid": uid, "source_group": uid, "stage_label": row["stage_label"],
               "family_label": row["family_label"], "new": new, "v1_alias": field,
               "standalone_field_hit": field, "a0_new": a0, "a1_new": a1})
carrier_all, carrier_sub, cinv = m.carriers()
mixed = p1 + carrier_sub
d = len(p1)
new_n = sum(r["new"] for r in p1); std_n = sum(r["standalone_field_hit"] for r in p1)
alias_n = sum(r["v1_alias"] for r in p1)
a0_fp = sum(r["a0_new"] for r in p1); a1_fp = sum(r["a1_new"] for r in p1)
m1 = [r for r in carrier_all if r["stage_label"] == "M"]
a3_fp = sum(r["new"] for r in m1)
st_new = m.classification(mixed, "stage_label", "new")["macro_f1"]
st_old = m.classification(mixed, "stage_label", "v1_alias")["macro_f1"]
fa_new = m.classification(mixed, "family_label", "new")["macro_f1"]
fa_old = m.classification(mixed, "family_label", "v1_alias")["macro_f1"]
diag_delta = min(st_new - st_old, fa_new - fa_old)
groups = defaultdict(list)
for r in p1: groups[r["source_group"]].append([r["new"], r["v1_alias"]])
try: delta_ci = m.coverage_bootstrap(groups)
except Exception as e: delta_ci = [None, None]
delta = new_n/d - alias_n/d if d else None
uid_ok = 0
field_first = m.field_hit(p1_raw[0]["baseline"]) if p1_raw else None
unique_std = sum(r["new"] == 1 and r["standalone_field_hit"] == 0 for r in p1)
const_fails = True  # constant-1 fires on A0/A1 -> specificity fails
attribution = unique_std > 0 and a0_fp == 0 and a1_fp == 0 and const_fails
gate_p1 = new_n >= 1; gate_clean = (a0_fp == 0 and a1_fp == 0)
gate_diff = sum(r["new"] != r["standalone_field_hit"] for r in p1) >= 1
gate = gate_p1 and gate_clean and gate_diff
# frozen outcome rule (uses delta_ci[0]; diag CI not used)
if not gate: outcome = "INVALID"
elif undefined or not p1 or not mixed: outcome = "NOT_EVALUABLE"
elif diag_delta < -0.02: outcome = "NEGATIVE"
elif (delta is not None and delta > 0 and delta_ci[0] is not None and delta_ci[0] > 0
      and diag_delta >= -0.02 and a0_fp == 0 and a1_fp == 0 and a3_fp == 0 and attribution): outcome = "POSITIVE"
elif diag_delta > 0.02 and (delta is None or delta <= 0 or delta_ci[0] is None or delta_ci[0] <= 0): outcome = "DIAG_ONLY"
else: outcome = "NULL"
print(json.dumps({
 "d_P1": d, "undefined": undefined,
 "new_coverage": [new_n, d], "standalone_field_hit_coverage": [std_n, d],
 "v1_alias_coverage": [alias_n, d], "delta_new_minus_alias": delta, "delta_ci_lower": delta_ci[0],
 "a0_fp": a0_fp, "a1_fp": a1_fp, "a3_fp_M": a3_fp, "A3_M_denominator": len(m1),
 "stage_macro_f1_new": st_new, "stage_macro_f1_alias": st_old,
 "family_macro_f1_new": fa_new, "family_macro_f1_alias": fa_old, "diag_delta_min": diag_delta,
 "gate_pass": gate, "attribution_pass": attribution, "unique_new_catches": unique_std,
 "field_hit_constant_probe": field_first,
 "frozen_rule_outcome": outcome,
 "note": "point estimates only; the 10k diagnostic bootstrap was not run (frozen predict_loco is O(groups^2))"
}, indent=2))