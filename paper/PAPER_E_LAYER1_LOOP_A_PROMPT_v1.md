ROLE: Loop A / GB10 execution
RESEARCH QUESTION:
Can an independent, task-level gold be defined for the existing frozen drift-v0 header-drift
injections WITHOUT using the audited greedy header matcher or the semantic judge — and if so, what
three-way label (LEGAL_VARIATION / HARMFUL_ERROR / INSUFFICIENT_EVIDENCE) does each dev case get
under a contract frozen before any case is read?

AUTHORITY:
/home/testuser/wzh/projects/agents_final_tech/paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md
(the design is authoritative; implement it exactly, do not redesign it)

INPUTS (read-only, frozen):
- /home/testuser/wzh/projects/agents_final_tech/data/research/drift_v0/output/injection_map.json  (expect sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e)
- /home/testuser/wzh/projects/agents_final_tech/data/research/drift_v0/input/tatqa_tables.json   (expect sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302)
- /home/testuser/wzh/projects/agents_final_tech/data/research/drift_v0/output/injected_tables.json
- /home/testuser/wzh/projects/agents_final_tech/logs/graph/eval/t2_visibility_sensitivity.json   (comparison target only, NOT gold)

ALLOWED ACTIONS:
1. FIRST write research/paper_e_layer1_20261015/LAYER1_ANALYSIS_PLAN_v1.md stating, before reading
   any case: the exact canonicalization norm(.), the tie policy, the U-rules, the value-invariance
   check, and an outcome-blind dev-split rule (hash of injection id). Freeze it (record its hash).
2. Implement the contract in a self-contained script under research/paper_e_layer1_20261015/.
3. Deterministically label every dev case; recompute value-invariance bytewise per case.
4. Read the frozen checker verdict (visible/blind) per injection id and build the 2x3 contingency.
5. Emit: LAYER1_ANALYSIS_PLAN_v1.md, LAYER1_RESULTS_v1.json (per-case rows + contingency + rates),
   LAYER1_RECEIPT_v1.json (input hashes, plan hash, counts, calls=0), LAYER1_SUMMARY_v1.md.
6. Self-check: input hashes match; each case labelled exactly one of E/H/U; counts reconcile.

FORBIDDEN ACTIONS:
- Any model call, judge call, endpoint call, network call, or training. calls must be 0.
- Modifying, moving, or rewriting any frozen input (injection_map / tables / t2 evidence).
- Tuning norm(.), the tie policy, the dev split, or the U-rules after looking at results.
- Using the audited greedy matcher output as the gold for any case.
- Claiming a harmful blind spot, an OCR conclusion, or any population rate from this dev analysis.
- Auto-labelling a U case by a model; U cases must stay U and be listed for human adjudication.

OUTPUTS (all under /home/testuser/wzh/projects/agents_final_tech/research/paper_e_layer1_20261015/):
- LAYER1_ANALYSIS_PLAN_v1.md
- LAYER1_RESULTS_v1.json
- LAYER1_RECEIPT_v1.json
- LAYER1_SUMMARY_v1.md

STOP CONDITIONS (report and stop; do not fix, do not expand):
- Any required input absent -> report INPUT_MISSING.
- Any input hash mismatch vs the expected value above -> report HASH_MISMATCH and stop.
- The dev-split rule or norm(.) cannot be stated unambiguously -> report RULE_AMBIGUOUS.
- The INSUFFICIENT_EVIDENCE rate exceeds 30% of dev cases -> report GOLD_NOT_ESTABLISHED.

EVIDENCE CLASS:
PRIMARY = the frozen independent contract and the dev contingency table.
ENGINEERING = script, plan hash, receipt, self-check counts.
EXPLORATORY = the feasibility verdict in LAYER1_SUMMARY_v1.md (no confirmatory claim).
