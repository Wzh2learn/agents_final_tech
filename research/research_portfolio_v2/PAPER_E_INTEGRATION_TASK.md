# Paper E Canonical Integration Task

Status: `IMPLEMENTATION_SPEC`
Date: 2026-10-21

Canonical manuscript:
`paper/saner_rene_manuscript_v1.md`.

Merge
`research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_REVISION_DRAFT.md`
into the canonical manuscript. Do not create a second canonical manuscript.

## Required scientific boundary

- Disposition: `NARROW_AND_CONTINUE`.
- Exactly two counted cases:
  1. staged document evaluator;
  2. FinRank evidence-ranking audit.
- FinQA is a nested boundary probe inside Case 1.
- MA-CERD and adaptive revalidation are not Paper E cases.
- FinRank v1 tie metrics and thresholds are preregistered and unchanged.
- The canonical `text_sha1` identity branch and the 442/305 and 33/2 counts
  are post-hoc v2 corrections after the wrong-identity v1 application.
- Residual global and metadata metric drift is exposed but its cause is
  unresolved.
- Keep visibility, detection, harmfulness, score sensitivity, decision
  stability and reproduction gap as separate constructs.
- The six-step review sequence is a proposed checklist, not a validated
  universal method.

## Manuscript edits

- Adopt the title:
  `Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and Evidence-Ranking Evaluation`.
- Rewrite abstract and introduction around the bounded two-case audit.
- Merge Caban, Bean and Mansouri comparisons into Related Work.
- Reframe Method 3.4 as a nested FinQA boundary probe.
- Add FinRank setup and v1/v2 provenance in Method and Setup.
- Remove the compact feedback/gain-collateral result from the submission body.
- Add the compact FinRank results with tie-positive versus strict/half-credit
  metrics and separate score sensitivity from decision stability.
- Remove or mark internal-only the AI-assisted 24-task review and deferred
  model-free/scoring routes.
- Preserve the unresolved reproduction gap and post-hoc labels in the
  Discussion, Conclusion and Data Availability.

## Synchronize derivative governance

- Amend, without rewriting historical freeze records:
  `paper/saner_rene_claim_matrix_v1.json`;
  `paper/saner_rene_manuscript_scope_lock_v1.md`;
  `docs/research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md`.
- Mark `paper/claim_manifest_v1.json` historical/internal-only and correct
  stale submission-authority wording.
- Regenerate TeX/derivative package only if existing scripts succeed. Do not
  publish or submit.

## Verification

- Run claim verification, docs lint, `_md2tex.py`, `_to_bundle_tex.py` and
  available PDF build checks.
- Check citations, forbidden markers, two-case accounting, page budget and
  derivative consistency.
- Do not modify raw scores or 2026-10-21 correction/recomputation evidence.
- Do not commit because the shared worktree is dirty.
