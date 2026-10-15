ROLE: Loop A / GB10 execution (Layer-1 v2 delta)
RESEARCH QUESTION:
Re-run the Layer-1 independent-gold labelling for the frozen drift-v0 header-drift injections with
ONE pre-registered rule change: the empty-normalisation U condition moves from table-level to
column-local. Everything else is identical to v1.

AUTHORITY (both, in order):
- /home/testuser/wzh/projects/agents_final_tech/paper/PAPER_E_LAYER1_V2_PREREG_DELTA_v1.md  (the delta)
- /home/testuser/wzh/projects/agents_final_tech/research/paper_e_layer1_20261015/LAYER1_ANALYSIS_PLAN_v1.md (v1 rule)

INPUTS (read-only, frozen; same as v1):
- data/research/drift_v0/output/injection_map.json          (sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e)
- data/research/drift_v0/input/tatqa_tables.json            (sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302)
- data/research/drift_v0/output/injected_tables.json
- logs/graph/eval/t2_visibility_sensitivity.json            (comparison target only, NOT gold)

ALLOWED ACTIONS:
1. FIRST write research/paper_e_layer1_20261015/LAYER1_V2_ANALYSIS_PLAN_v1.md: a full restatement of
   the contract with the v2 delta applied, frozen before reading any case content.
2. Implement the delta (reuse the v1 script's unchanged parts; change only the empty/collision
   clause to column-local, and restrict candidates to non-empty canonical headers).
3. Deterministically label every dev case; same dev split; recompute value-invariance bytewise.
4. Read the frozen checker verdict per id; build the same 2x3 contingency and rates.
5. Emit LAYER1_V2_RESULTS_v1.json, LAYER1_V2_RECEIPT_v1.json, LAYER1_V2_SUMMARY_v1.md.
6. Self-check: input hashes match; each case exactly one of E/H/U; counts reconcile; calls=0.

FORBIDDEN ACTIONS:
- Any change other than the single v2 delta. Do NOT change norm(.), the split, the binding rule,
  the tie policy, thresholds, or label definitions.
- Any model/judge/endpoint/network/training call (calls must be 0).
- Modifying frozen inputs, or the v1 artifacts (v1 stays as historical record).
- Tuning any rule after seeing v2 results; claiming a population rate, OCR result, or harmful
  blind spot.

OUTPUTS (under /home/testuser/wzh/projects/agents_final_tech/research/paper_e_layer1_20261015/):
- LAYER1_V2_ANALYSIS_PLAN_v1.md
- LAYER1_V2_RESULTS_v1.json
- LAYER1_V2_RECEIPT_v1.json
- LAYER1_V2_SUMMARY_v1.md

STOP CONDITIONS:
- input absent -> INPUT_MISSING; expected-hash mismatch -> HASH_MISMATCH;
- rule not implementable unambiguously -> RULE_AMBIGUOUS;
- v2 U rate > 0.30 -> GOLD_NOT_ESTABLISHED (report; this branch then stops).

EVIDENCE CLASS:
PRIMARY = v2 contingency and rates. ENGINEERING = plan hash, script, receipt. EXPLORATORY = verdict.
