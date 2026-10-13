# Loop C independent audit (read-only) - SANER Route A, 2026-10-13

You are **Loop C**: an independent reviewer. You are READ-ONLY. Do not modify any file, do not commit, do not push, do not create runners, do not call models or services beyond your own reasoning.

Repo root: `wzh/projects/agents_final_tech`

## Authorised scope
Read these files and produce a verdict report on stdout. Nothing else is authorised.

- `docs/research/SANER_SCIENTIFIC_ADJUDICATION_v1.md` (the author-level adjudication, items A1-A7; A2 is BLOCKING)
- `paper/saner_rene_manuscript_v1.md` (the revised manuscript)
- `paper/saner_rene_claim_matrix_v1.json` (claim authority)
- `paper/saner_rene_manuscript_scope_lock_v1.md`
- `research/positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md`
- `docs/research/LOOP_C_REVIEW_A1A7_REVISION_v1.md` (the previous SELF-review you are to challenge)
- `docs/research/SUBMISSION_READY_CHECKLIST_v1.md`
- `docs/research/RENE_ADVERSARIAL_REVIEW_v1.md`
- `paper/overleaf_bundle/saner_rene_manuscript_v1.tex` (or the compiled PDF if you prefer)

## Questions (answer each with FACT / INFERENCE / UNVERIFIED, one or two sentences)
1. Has each of A1-A7 actually been applied in the manuscript *and* in the claim matrix / scope lock? Name any item you judge NOT applied.
2. Is any claim now stronger than the adjudication permits? Name it precisely if so.
3. Is the A2 rewrite correct: does it separate the positive affine/rank structural equivalence from the clean-panel calibration degeneracy, and does it avoid both a blanket non-identifiability claim and an over-claim of equality?
4. Is the A4 correction numerically right: does the text now report the judge-vs-DR4 comparisons separately from the deterministic visibility-vs-equivalence comparison (the source table is `docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md` lines 122-151)?
5. Does the prefix "Long-Horizon" survivor count in the manuscript / matrix / scope lock overstate the empirical scope anywhere it still appears?
6. Is the compiled package internally consistent (title, abstract, contributions, references, anonymity)? Report any inconsistency.
7. Name the single weakest point of the revision.
8. Does anything in the revised text contradict a FROZEN number (96/118, 0/13, 2,382, 0.375, 1.000, 0.3333, 0.6667, 0.1667, 89/89, 112/118, 75/95, 20/95)?

## Output (stdout only)
For each question: the answer with its label. Then exactly these lines:
`LOOP_C_ITEM_APPLICATION_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_CLAIM_BOUNDARY_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_PACKAGE_CONSISTENCY_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_INDEPENDENT_VERDICT = PASS | CONDITIONAL | FAIL`
and one closing line naming the top residual risk.