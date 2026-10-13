# Loop C independent re-audit (v3, read-only) - A1-A7 residual verification

You are **Loop C**: an independent reviewer. You are READ-ONLY. Do not modify any file, do not commit, do not push, do not create runners, do not call services beyond your own reasoning.

Repo root: `wzh/projects/agents_final_tech`

## Context
An independent audit (v2, 2026-10-13) of the A1-A7 revision returned CONDITIONAL with nine residuals. A residual pass has since been applied in the working tree. Your job: verify the fixes and that nothing regressed.

## Authorised scope (read-only)
- `paper/saner_rene_manuscript_v1.md`, `paper/saner_rene_manuscript_v1.tex`, `paper/overleaf_bundle/saner_rene_manuscript_v1.tex` and the compiled `saner_rene_manuscript_v1.pdf`
- `paper/saner_rene_claim_matrix_v1.json`, `paper/saner_rene_manuscript_scope_lock_v1.md`
- `docs/research/figures_saner/figure_source_binding_manifest.json`, `research/positive_repair_20261011/track_a_figures_mirror/figure_source_binding_manifest.json`
- `research/positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md`
- `docs/research/SUBMISSION_READY_CHECKLIST_v1.md`
- `docs/research/figures_saner/fig3_localization_ablation.svg` (actual figure content)
- `scripts/verify_claim_evidence.py`, `scripts/pre_submission_audit.py` (read; run them)

## Verify each v2 residual (file:line evidence; verdict RESOLVED / NOT_RESOLVED)
(a) scope-lock row that named "matched-FPR non-identifiability";
(b) manuscript sentence "non-identifiability is reported" (Section 4.3);
(c) Data Availability phrase "released scripts";
(d) Section 1 sentence about separating protocols / observing a defect family (per-clause scoping);
(e) Figure 3 caption "remains above ... majority ... baseline";
(f) Section 5.1 attribution of the four judge-versus-DR4 disagreements (must not retell the D1 versus DR4 granularity axis);
(g) abstract in the registration package (must be verbatim identical to the manuscript abstract);
(h) claim-matrix `figure_3` and scope-lock Figure 3 definition versus the actual figure (ablation panels macro-F1 / top-1; the FinQA boundary is carried in text);
(i) checklist item 7 wording and the stale `.tex` "UNCOMPILED" header comment.

## Regression checks
1. Run `python3 scripts/verify_claim_evidence.py` (expected PASS) and `python3 scripts/pre_submission_audit.py` (expected PASS: 9 pages, author empty, forbidden=[], '??'=0).
2. Confirm the scope-lock pin in BOTH manifest copies equals `sha256sum paper/saner_rene_manuscript_scope_lock_v1.md`, and that the two manifest files are byte-identical (`cmp`).
3. Frozen-number spot-check: 96/118, 0/13, 2,382, 0.375, 1.0, 0.3333, 0.6667, 0.1667, 89/89, 112/118, 75/95, 20/95, 219/282, 20/21, 40/67, 90/111.
4. Any new claim-boundary or consistency problem introduced by the residual pass (or "none").

## Output (stdout only)
Per residual: `(x) ... RESOLVED - evidence file:line`. Then new issues or "none". Then exactly these lines:
`LOOP_C_ITEMS_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_CLAIM_BOUNDARY_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_PACKAGE_CONSISTENCY_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_INDEPENDENT_VERDICT = PASS | CONDITIONAL | FAIL`
and one closing line naming the single weakest remaining point.
