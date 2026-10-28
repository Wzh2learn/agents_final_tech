# Paper E revision: research review and handoff

## Current artifact
`paper_e_review_revision.md` is a private English content-review draft, not a submission-ready conference paper. It revises the previous short draft; it does not introduce the parallel GB10 experiment, human gold, user study, or a new audit method validation. Its three tables organize existing observations and retain post-hoc and null results.

## Important findings and editorial actions
1. The earlier short draft lacked a reader-facing comparison table and the single-active-leaf condition; Table 1 organizes claim → evidence → interpretation, Table 2 restores 75/95 and 20/95 at reported operating points and the 0.375 scaling, and Table 3 summarizes BEIR comparison evidence and the equality-respecting baseline. The detailed long draft describes these as seed-42 per-table counts; these are not independent mutation counts.
2. A 0.375 slope is a positive score rescaling in one construction, not a generally calibrated threshold. The clean-only threshold remains unresolved. Surface visibility does not prove downstream harm; the sole semantic judge does not constitute human gold.
3. The original retrospective BEIR implementation correction is described as the authors' own development issue, not falsely represented as common community practice; do not remove or relabel its provenance. Holm-adjusted sign-flip tests and bootstrap intervals are distinct inferential procedures.
4. The old BGE subsection remains a single-model post-hoc comparison and is not incorporated into the 10-pair family. No inference is made about the ongoing parallel GB10 work.
5. FinRank identity counts are post-hoc/source-informed. The local/global reproduction gap remains unresolved. The FinQA probe did not recompute downstream fields and is not a measured failure rate.

## Blocking before submission
- Independently audit all experimental values and their labels against raw artifacts, and review the new tables against frozen scripts; our comparison was with prior drafts, not independent re-execution.
- Incorporate new GB10 results only after their experiment owner supplies auditable evidence and freeze status. Before/after decision illustrations must be marked constructed unless a real prospective choice is documented.
- Choose an actual venue/track; adapt template, page limits, anonymous artifact, AI disclosures and author metadata. This draft does not claim ACM or IEEE compliance.
- Verify all citation metadata from primary sources; earlier authors' bibliography was preserved and not independently checked in this pass. Check index terms, external-data licenses, suitable artifact distribution, disclosure and any human-label protocol.
- Conduct independent scientific and typographical review after integration; this is not a user study or human expert review.

## Suggested Gemini prompt
Please review the attached draft as a skeptical empirical evaluation reviewer. Distinguish manuscript facts, interpretation, and conjecture; do not invent common-practice baselines or assume the new GB10 experiment is completed. Check the three tables against the text, independent units and denominators, exact-tie versus statistical baseline, single-leaf scaling and sensitivity, and BGE's retrospective status. Recommend only text changes that preserve scientific scope. Identify any issues needing raw-artifact validation, and do not claim venue compliance without the relevant official template.
