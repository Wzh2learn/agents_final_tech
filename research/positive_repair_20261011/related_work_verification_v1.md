# Related-Work Precedent Verification v1

> date: 2026-10-11 | Loop D (primary-source web verification) | NO manuscript citation added; fail-closed per owner directive
> rule: a RENE precedent may enter related work ONLY after it is confirmed on an official SANER program or proceedings source. Gemini-provided precedents are NOT authority.

## Method
Fetched the official researchr SANER program pages and matched candidate titles against the RENE track listing (plain-text extraction of served HTML; no model or judge calls):
- SANER 2026 RENE track: https://conf.researchr.org/track/saner-2026/saner-2026-reproducibility-studies-and-negative-results-rene-track
- SANER 2025 RENE track: https://conf.researchr.org/track/saner-2025/saner-2025-reproducibility-studies-and-negative-results-rene-track

## Results

| Candidate (owner-supplied) | Status | Evidence |
|---|---|---|
| Does the Tool Matter? | VERIFIED | SANER 2025 RENE program lists: Does the Tool Matter? Exploring Some Causes of Threats to Validity in Mining Software Repositories (RENE Track). |
| Can We Classify Flaky Tests Using Only Test Code? | VERIFIED | SANER 2026 RENE program lists: Can We Classify Flaky Tests Using Only Test Code? An LLM-Based Empirical Study (RENE Track; presenter Luca Traini). |
| Static Analysis Traces can help Dynamic Symbolic Execution: a Replication Study | VERIFIED | SANER 2026 RENE program lists the title verbatim (RENE Track; presenter Manel Abdellatif). |
| The Limits of the Identifiable ... (RENE 2024) | UNVERIFIED | The SANER-2024 RENE track URL returned 404 and the 2024 home page carried no matching title; not confirmed on a primary source. |

## Decision
- 3 of 4 candidates are VERIFIED on official SANER RENE program pages and may enter the candidate pool.
- The 4th candidate is UNVERIFIED and must not be cited.
- NO precedent is inserted into the manuscript in this pass: paper/saner_rene_manuscript_v1.md Related Work currently cites no RENE precedent. This is the fail-closed outcome required by the owner (pause writing into related work until verified).

## Remaining step (before any insertion)
Run the normal paper-lookup/citation pass (DOI or proceedings record per paper) and add verified entries to paper/references_v0.md before wording them into Related Work.