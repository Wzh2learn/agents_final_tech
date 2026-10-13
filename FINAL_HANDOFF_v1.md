# FINAL HANDOFF v1

> date: 2026-10-13 | the single entry for the next session | frozen version = the commit that contains this file (`git log -1 --oneline -- FINAL_HANDOFF_v1.md`)
> LOCAL = origin/main = GB10 (tree hashes verified equal) | `PRE_SUBMISSION_AUDIT = PASS`

## Owner decisions already recorded (do not re-ask)

| Decision | Value |
|---|---|
| Paper E title | **T1**: "Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation" (applied everywhere) |
| Venue | **SANER RENE** (default confirmed) |
| Artifact | **Not public.** Prepare the anonymous package only; do not release; the Data Availability statement therefore stays factual ("prepared for release") |
| WP-0 source family | **TAT-QA** |
| WP-0 goal | finish qualification + leave a minimal-experiment entry; **not** method development |

## Paper E - state

- Package: `paper/overleaf_bundle/` (tex + bib + 3 figure assets + compiled PDF), 9 pages, 0 overfull, self-contained.
- Science: `paper/saner_rene_manuscript_v1.md` is the source of truth; A1-A7 applied; three-persona adversarial review applied W1-W3 wording hardenings; **frozen**.
- Claim authority: `paper/saner_rene_claim_matrix_v1.json` (C1-C3, 15 evidence hashes verifying).
- Checklist: `docs/research/SUBMISSION_READY_CHECKLIST_v1.md` (10 items PASS).
- Gate: `docs/research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md` (status + §12 revision record).
- Audit: `python scripts/pre_submission_audit.py` -> PASS (evidence / anonymisation / format / artifact).
- Reviewer defence: `docs/research/RENE_ADVERSARIAL_REVIEW_v1.md`, `docs/research/RENE_REVIEWER_RISK_SIMULATION_v1.md`.

### What still stands between the frozen package and a submission
1. Owner authorisation for abstract registration and submission (owner-only).
2. A genuine **independent** review (every delegated audit failed this session; existing reviews are self-audits - do not describe them as independent).
3. Native-speaker language pass (optional; the US-spelling and dash pass is done).

### Forbidden from here
- No number, evidence-hash, split, threshold, tie-rule or weight change.
- No claim change without a new author-level adjudication.
- No reopening of Route B, the FinQA binding questions, or PR-03.
- No self-submission, no uploading, no registration.

## Thesis (WP-0) - state

- Entry: `docs/research/WP0_ENTRY_PACKAGE_v1.md` (source landscape / candidate ranking / gap map).
- Assessment: `docs/research/WP0_QUALIFICATION_REPORT_v1.md` (`SOURCE_INSUFFICIENT` overall).
- TAT-QA package: `docs/research/WP0_TATQA_PACKAGE_v1.md` - licence **verified** (MIT repo + CC BY 4.0 data, primary sources, today), task pool **sized** (188 tables with both multi-period columns and units), task/evaluation contracts drafted, and the **binding blocker identified**: the normalized projection has no report/company identifier, so report-level origins need the raw TAT-QA records (a small public download).
- The one thing that unblocks WP-0: **owner authorisation to fetch the raw TAT-QA records** (public, CC BY 4.0). Everything else in WP-0 is ready.
- `G-RQ = HOLD`, `G-M = HOLD`, `METHOD_NOVELTY = NOT_IDENTIFIED` - unchanged.

## Read order for the next session

1. `FINAL_HANDOFF_v1.md` (this file)
2. `PROJECT_FINAL_STATE_BEFORE_SUBMISSION.md` (freeze guardrails)
3. `docs/research/SUBMISSION_READY_CHECKLIST_v1.md`
4. `paper/saner_rene_claim_matrix_v1.json`
5. `docs/research/WP0_TATQA_PACKAGE_v1.md`
6. `docs/INDEX.md` (navigation)