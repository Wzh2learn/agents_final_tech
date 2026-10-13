# Final Submission Checklist v1

> date: 2026-10-13 | artifact: `paper/overleaf_bundle/` | verdict: `SUBMISSION_READY (package) / PENDING_OWNER (external actions)`
> owner decisions recorded 2026-10-13: title = **T1** (confirmed, applied); venue = **SANER RENE** (default confirmed); artifact = **not public yet**, anonymous package prepared only.
> machine-verified by `scripts/pre_submission_audit.py` (PRE_SUBMISSION_AUDIT = PASS) plus the checks below.

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | **Title** | PASS | Single active title `Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation`, identical in manuscript, `.tex`, compiled PDF, claim matrix, scope lock, abstract package. No retired variant present. |
| 2 | **Abstract** | PASS | Revised per A1/A2/A3/A5/A6: three constructs, structural equivalence vs unresolved operating point, benign-absorption disclosure, defined-predicate FinQA wording, scope narrowing, and a closing consequence clause that blocks the three naive over-readings. |
| 3 | **Contribution** | PASS | Three contributions aligned to the adjudication §10.1: construct separation + family boundaries; protocol-identifiability audit with the split structural/calibration result and the ablation; failed-transfer autopsy. No hierarchy-superiority or transfer claim. |
| 4 | **Claim matrix** | PASS | `paper/saner_rene_claim_matrix_v1.json` C1-C3 rewritten; 15 evidence hashes verify exactly; forbidden-claims list intact; adjudication application recorded. |
| 5 | **Figures** | PASS | Three figures embedded with the revised captions; figure OUTPUT hashes verify against the binding manifest (both copies); Figure-3 caption carries the partial-information clause. |
| 6 | **References** | PASS | 21 cited / 21 bib entries, 0 missing, 0 unused; no `??` in the compiled PDF; NIST and RENE precedents verified from primary sources; IEEEtran proper-noun casing fixed. |
| 7 | **Anonymisation** | PASS | Identity-token scan clean (no author/organisation/hostname/username/email strings); PDF metadata Author empty, Title set; double-anonymous compliant (no acknowledgments, third-person self-citations). Repo-relative paths and a localhost string (`127.0.0.1:8004`) remain in the .tex and are non-identifying. |
| 8 | **Artifact statement** | PASS (factual) | Data Availability states "prepared for release" and "planned to be made available ... not yet established"; the staged package exists at `research/artifact_release_2026/` but is NOT released. |
| 9 | **Page limit** | PASS | Compiled PDF is 9 pages; main content including Appendix A fits within the 10-page RENE limit, references occupy about one page (limit 2 references-only). |
| 10 | **Compile** | PASS | pdfLaTeX-equivalent build (portable tectonic 0.15.0), 0 overfull boxes, 76 cosmetic underfull boxes, bundle self-contained (no local absolute paths). |

## What this checklist does NOT certify
- It does not certify scientific novelty or acceptance probability.
- It does not certify the authored revisions independently (self-audits only; the independent pass is outstanding).
- It does not authorise registration or submission: those remain owner actions.

## Owner actions that remain (the only blockers to actual submission)
1. ~~Decide the artifact release~~ -> **decided: prepare only, do not publish**; the anonymised repository is therefore not created and the Data Availability statement stays factual.
2. ~~Confirm the final title wording~~ -> **decided: T1**.
3. ~~Confirm the venue~~ -> **decided: SANER RENE**.
4. Authorise abstract registration (deadline 2026-10-19 AoE) and submission (2026-10-23 AoE).