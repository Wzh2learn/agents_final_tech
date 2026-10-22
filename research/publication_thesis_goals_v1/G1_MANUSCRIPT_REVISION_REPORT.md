# Paper E Manuscript Revision Report

Date: 2026-10-22

Status: `REVIEWABLE_DRAFT_WITH_OWNER_ITEMS_PENDING`

## Scientific Changes

1. **Injection-seed analysis unit corrected.**
   The `219/282 = 0.7766` value is retained as a descriptive table-run
   estimate. The previous pooled interval `[0.7270, 0.8227]` is no longer used
   as source-table uncertainty because 282 table-runs map to only 119 unique
   source-table UIDs. The manuscript now reports:
   - source-table UID-cluster bootstrap: `[0.7117, 0.8364]`;
   - UID-equal sensitivity: `0.7535 [0.6835, 0.8207]`;
   - three-seed range and leave-one-seed-out values.
   The reanalysis is explicitly labelled post-hoc and deterministic.

2. **Interpretation corrections made explicit.**
   The Introduction now contains a table mapping common interpretations to
   audit evidence and narrower revised interpretations. The same distinctions
   are carried through Results, Discussion and Conclusion.

3. **Scope and provenance preserved.**
   Exactly two cases remain. FinQA is still nested in Case 1. The FinRank
   `442/305` and `33/2` identity counts remain post-hoc v2 corrections after
   the wrong-identity v1 application. The global and metadata reproduction gap
   remains unresolved.

4. **Related work positioning tightened.**
   The section now emphasizes empirical software evaluation and
   reproducibility-audit precedent rather than presenting the paper as a SANER
   track-specific result.

5. **AI disclosure is prepared but not Owner-approved.**
   The manuscript contains a proposed disclosure naming OpenAI Codex and the
   writing/revision work it supported. Final tool history and the venue's
   citation form remain Owner/venue confirmation items. AI assistance is not
   described as human verification.

## Evidence Rebinding

Three FinRank JSON files had stale historical hash bindings after the verified
workspace integration. Their current HEAD bytes were rebound without editing
the files. The scope-lock hash was re-pinned after adding the statistical
evidence row. Old and new values are recorded in `G1_HASH_REBIND.md`.

## Mechanical Verification

- `python scripts/verify_claim_evidence.py`:
  `WIDE_EVIDENCE_CHECK = PASS`.
- `python scripts/pre_submission_audit.py`:
  `PRE_SUBMISSION_AUDIT = PASS`.
- ICAART/SCITEPRESS PDF: 11 A4 pages, no overfull boxes, 21 citations and 21
  bibliography entries, no unresolved references. Alternate Overleaf PDF is a
  historical 10-page build.
- Official 9pt table/reference typography is restored. The deterministic
  FinRank strict-win gap is corrected to 13.820 and its movement to 0.359.
- Focused G1 reanalysis tests: `3 passed`.

## Author-Approval Package

The package under `G1_SUBMISSION_PACKAGE/` contains:

- ICAART and IEEE Access cover-letter drafts;
- IEEE-aligned AI-use disclosure draft;
- artifact release plan;
- submission checklist;
- Owner decision list.

## Remaining Owner/External Actions

- recheck the ICAART live submission system immediately before upload;
- keep ICAART primary and IEEE Access backup unless a blocking route change
  appears;
- confirm authors, order, BUPT first affiliation, ORCID and patent status;
- confirm the complete AI tool history and affected sections;
- approve payment/license/public artifact actions if applicable;
- give explicit external-submission authorization.
