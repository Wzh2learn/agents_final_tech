ACK FIRST LINE: ACK pe-l1-v2-preresult-audit: Loop C independent auditor

ROLE: Loop C independent auditor on GB10. Read-only. Do not modify any Loop A output.

GOAL:
Audit whether `LAYER1_V2_CANONICAL_PREREG_v2.md` is a valid pre-registered follow-up to the
already-completed v1 probe, before any held-out v2 label is computed.

AUDIT SOURCES:
- research/paper_e_layer1_20261015/LAYER1_ANALYSIS_PLAN_v1.md
- research/paper_e_layer1_20261015/LAYER1_RESULTS_v1.json
- research/paper_e_layer1_20261015/LAYER1_SUMMARY_v1.md
- research/paper_e_layer1_20261015/v2/LAYER1_V2_CANONICAL_PREREG_v2.md

CHALLENGE AND VERDICT FOR EACH ITEM (PASS / CONDITIONAL / FAIL):
1. v1 is preserved unchanged; v2 does not rewrite or suppress the v1 `GOLD_NOT_ESTABLISHED`
   result.
2. The v2 rule change is isolated: norm(.), split, provenance, bytewise value invariance,
   Levenshtein distance, and tie policy are unchanged from v1; only empty-header handling
   changes.
3. The v2 sample is genuinely held-out: v1 results contain labels only for the dev 59, and
   the v2 plan says labels are computed on the held-out 59 only.
4. The v2 decision gates are stated before held-out labels are computed; no gate is defined
   using held-out outcomes.
5. The plan cannot silently relabel a `U` case, and every remaining `U` reason is explicit.
6. The plan does not claim a population rate, OCR result, harmful blind spot, or Layer 2
   authorization before the audit passes.

RED FLAGS TO CHECK EXPLICITLY:
- any dev counterfactual in the v2 plan being cited as a v2 result;
- any threshold or rule that could have been chosen after seeing held-out labels;
- any missing stop condition or missing zero-call discipline;
- any wording that would allow v2 to replace v1 rather than stand beside it.

OUTPUT:
Write only:
`research/paper_e_layer1_20261015/v2/LAYER1_V2_CANONICAL_PRERESULT_AUDIT_v2.md`

The audit must include the verdict per item, a final one-line verdict
`VERDICT: PASS / CONDITIONAL / FAIL`, and any counterexample or ambiguity.

FORBIDDEN:
No edits outside the audit file; no git write; no model endpoint beyond this audit call;
no training; no network; no modification of frozen inputs or Loop A outputs.



ADDITIONAL CONFLICT CHECK:
Confirm that the canonical prereg explicitly supersedes the prior v2 prereg delta and the two earlier v2 plan drafts before any v2 label exists, and that the column-local collision rule is the single governing rule.



FINAL K-CHECK:
Confirm that the rev-2 clarifications K1-K6 are present and that they close the prior audit's six conditions. If any remain open, list it; otherwise PASS.

