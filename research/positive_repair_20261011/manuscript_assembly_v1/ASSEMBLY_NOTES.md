# Manuscript Assembly Notes v1 (saner_rene_manuscript_v1.md)

> date: 2026-10-11 | method: programmatic assembly; NO claim added; borrowed text is the audited/repaired `teacher_review_draft_v1.md`
> Target components (owner list): Introduction / RQ+constructs / methodology / Stage E results / multi-leaf ablation / FinQA failed-transfer / discussion+limitations / related work / conclusion.

## Source map
- Title / Abstract / Section 1 (Introduction incl. RQ1-RQ3 and the three constructs early): NEW (`manuscript_assembly_v1/front.md`), claim-safe, draw on the frozen claim matrix + Version-B proposal wording.
- Section 2 (Related Work): borrowed verbatim from `teacher_review_draft_v1.md` (audited).
- Section 3 (Method) 3.1-3.3: borrowed verbatim; NEW 3.4 (stage-aligned instrumentation + second dataflow description) from `s34.md`.
- Section 4 (Setup) 4.1-4.3: borrowed verbatim; NEW 4.4 (multi-leaf protocol) + 4.5 (second-dataflow execution boundary) from `s44.md`.
- Section 5 (Results) 5.1-5.4: borrowed verbatim (includes the F6 number fixes); NEW 5.5 (multi-leaf result WITH direct-codebook ablation) + 5.6 (FinQA failed-transfer) from `s55.md`/`s56.md`; the prior "5.5 Boundary case" paragraph is retained and renumbered to 5.7 (body verbatim).
- Section 6 (Discussion) 6.1-6.2: borrowed verbatim; NEW 6.3 (integration) from `s63.md`.
- Section 7 (Conclusion), References, Appendix A: borrowed verbatim.
- Every number in the NEW text is traceable to a frozen artifact: 96/118, OCR 0/13/11 clusters (stage_e_118_quantification_v1.md); affine 0.375 + non-identifiability (stage_e_matched_fpr_reanalysis_v1.md); 1.0/1.0/0.3333, tie 0.6667, p=1e-4, CI [1,1], 72 clusters/216 injections, 8-dead-columns (stage_e_multileaf_result_packet_v1.md / signature_ablation_v1.md); V/D/O 89/89, 0/89, 0/89 and 30 clusters (binding-v3 formal run + autopsy).

## Not yet done for SUBMISSION_DRAFT_COMPLETE
1. Figure integration/renumbering in Section 5 (Figures 1-3 + captions; Figure-3 status labels per residual R8); existing embedded Figure 2 reference retained.
2. References completion: official NIST citation decision (owner), final reference pass, BibTeX coverage.
3. Venue template / author block / anonymity; DOCX + PDF regeneration (residuals R6, R7); language-audit re-run on repaired wording.
4. R5: reconcile the three contribution decompositions (draft/scope-lock/V-B) at assembly review.