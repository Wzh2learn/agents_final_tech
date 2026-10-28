# Paper E v3 revision review

Status: private content-review draft, not submission-ready; no claim of independent scientific or human review.

- Created v3 as a separate file by 12 exact replacements applied to v2; v2 is unchanged. `build_revision_v3.py` documents each replacement and checks each source passage occurs exactly once.
- Intro now covers the post-hoc six-system family. The staged example describes the documented field-hit-rate and weighted-root drop signals rather than asserting an unverified flat aggregate. The 0.375 threshold relationship is approximate and restricted to the single-responsive-leaf construction. Added the three per-seed numerator/denominator figures, after checking the frozen long draft.
- FinRank identity and filtering statements are separated; the BEIR cutoff and tie-order interventions are explicitly separate. The initial MAP implementation is not re-described as a community practice; its exact old denominator was not independently verified, so Gemini's proposed specific rewrite was not applied.
- Dense and six-system analyses are presented under one heading in chronological order; Holm's monotonic step-down property and metric/test conditions are explicit. All prior post-hoc, unequal comparison-family, assumption, no-user-study and no-dense-score limitations remain.
- GB10 LibreOffice 24.2 rendered `paper_e_review_revision_v3.docx` to an 11-page Letter PDF. Contact sheet visually reviewed: no obvious page clipping at contact-sheet resolution. Tables 1 and 2 split across pages; final venue formatting and page-specific accessibility checks remain. `javaldx` emitted a warning; conversion produced PDF.
- No independent re-execution of original case data, comprehensive statistical expert review, full-text citation verification, target venue template validation, user study, human annotation or posting was carried out in this revision.

## Holm numeric check

Directly sorted `mc_recheck.json` SciFact's 15 per-pair p-values. BGE versus BM25(1.2,0.75) is sixth with p=0.006409967950160249; its own step factor is ten (0.06409967950160249). The preceding fifth comparison BGE versus BM25(0.9,0.4) has p=0.005999970000149999, times 11 = 0.06599967000165. The Holm running maximum carries this value forward and rounds to 0.066000. This is a check of saved inputs and implemented calculation, not new independent data.

## Files

- `paper_e_review_revision_v3.md`, `.docx`, `.pdf`: new draft and review render.
- `build_revision_v3.py`: reproducible exact-text edits from v2.
- `v3_contact.jpg`: review contact sheet; optional disposable render, not research evidence.

Source of key denominators and signal labels: prior `paper_e_ijcnn2027_submission.md` sections 3.1–3.3 and 5.2–5.3; statistical source: `research/paper_e_evidence_followup_20261028/mc_recheck.json` in the separate integration worktree. Full provenance and raw-source checking remain necessary before submission.
