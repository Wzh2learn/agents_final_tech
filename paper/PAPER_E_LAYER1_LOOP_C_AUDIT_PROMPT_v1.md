ROLE: Loop C / independent audit (read-only; do not modify any Loop A output)

WHAT TO AUDIT:
The Layer-1 independent-gold design and its implementation for the drift-v0 header-drift injections.
Read-only sources:
- paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md
- research/paper_e_layer1_20261015/LAYER1_ANALYSIS_PLAN_v1.md
- research/paper_e_layer1_20261015/LAYER1_RESULTS_v1.json
- research/paper_e_layer1_20261015/LAYER1_RECEIPT_v1.json
- research/paper_e_layer1_20261015/LAYER1_SUMMARY_v1.md

CHALLENGE, and give PASS / CONDITIONAL / FAIL with reasons for each:
1. Independence: are norm(.) and the tie policy genuinely independent of the audited greedy matcher,
   or a re-implementation of it? Is the gold derived from injection-map truth rather than the checker?
2. Dev split blind: is the split outcome-blind and stated before any case is read?
3. No fitting: are the E/H/U rules fully stated before results, with no post-hoc threshold/tie/norm change?
4. No silent auto-labelling: is every INSUFFICIENT_EVIDENCE case left as U and never resolved by a model?
5. Arithmetic: recompute the 2x3 contingency and reported rates from the per-case rows; do they reconcile?
6. Claim boundary: does the summary claim a harmful blind spot, an OCR result, or a population rate the
   dev evidence cannot support? It must not.

OUTPUT: docs/research/PAPER_E_LAYER1_LOOP_C_AUDIT_v1.md with verdict per item, any counterexample,
the arithmetic recheck, and a final one-line verdict (PASS / CONDITIONAL / FAIL). State defects; do not fix.

BOUNDARY: read-only; no endpoints; no training; no network; do not fabricate any number.
