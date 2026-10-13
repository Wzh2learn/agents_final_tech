# FINAL HANDOFF v1

> date: 2026-10-13 | the single entry for the next session | frozen version = the commit that contains this file (`git log -1 --oneline -- FINAL_HANDOFF_v1.md`)
> LOCAL = origin/main = GB10 (tree hashes verified equal) | `PRE_SUBMISSION_AUDIT = PASS` | Loop C independent audit delivered; WP-0 TAT-QA A1-A6 closed (2026-10-13)

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
- Independent audit: `docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md` (v2 CONDITIONAL -> 9/9 fixed -> v3 items PASS / claim boundary PASS; one prescribed word fix applied; machine re-verified both hosts).
- Submission execution handoff: `docs/research/SUBMISSION_EXECUTION_HANDOFF_v1.md` (owner-gated steps + copy-paste block; nothing auto-executed).
- Reviewer defence: `docs/research/RENE_ADVERSARIAL_REVIEW_v1.md`, `docs/research/RENE_REVIEWER_RISK_SIMULATION_v1.md`.

### What still stands between the frozen package and a submission
1. Owner authorisation for abstract registration and submission (owner-only).
2. ~~A genuine independent review~~ -> **DELIVERED 2026-10-13** (v2 CONDITIONAL -> 9/9 fixed -> v3 items PASS / claim boundary PASS; one prescribed word fix applied; record: `docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`).
3. ~~Native-speaker language pass~~ -> final English language edit pass applied 2026-10-13 (model-executed; 14 expression edits + 2 source blank-line fixes; rebuild + full audit PASS; abstract resynced in the package and the submission handoff). A human native-speaker read remains optional.

### Forbidden from here
- No number, evidence-hash, split, threshold, tie-rule or weight change.
- No claim change without a new author-level adjudication.
- No reopening of Route B, the FinQA binding questions, or PR-03.
- No self-submission, no uploading, no registration.

## Thesis (WP-0) - state

- Entry: `docs/research/WP0_ENTRY_PACKAGE_v1.md` (source landscape / candidate ranking / gap map).
- Assessment: `docs/research/WP0_QUALIFICATION_REPORT_v1.md` (historical `SOURCE_INSUFFICIENT`; Sec.10 update: TAT-QA A1-A6 closed).
- TAT-QA execution: raw fetched (owner-authorised; 2,479 records, sha256-gated; receipt on GB10); origins 182 / candidate items 60; appendix `docs/research/WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`; contracts `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md`; scripts `research/tatqa_wp0_2026/`.
- Gate recommendation: **G-RQ -> QUALIFIED_CONDITIONAL** (remaining bindings: feedback right; actor revision freeze; budget/window - owner/advisor decide); **G-M -> HOLD**; `METHOD_NOVELTY = NOT_IDENTIFIED`.
- WP-1 (thin runner): owner-approved and executed 2026-10-13 (runs 1-3; run 3 PASS under spec rev 1.2; independent audit v1 CONDITIONAL -> focused re-audit v2: items/scope PASS, one spec residual filed for the WP-2 freeze). Record: `docs/research/WP1_COMPLETION_RECORD_v1.md`.
- Not authorised: WP-2 (pilot), any episode collection, any training.
- Prep drafts (reversible): `docs/research/WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_DRAFT_v1.md`, `docs/research/WP0_ACTOR_REVISION_FREEZE_PLAN_v1.md`, `docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md`, `docs/research/WP0_TATQA_LOOP_A_EXECUTION_PACKAGE_v1.md`.
- Advisor brief: `docs/research/ADVISOR_RESEARCH_STATUS_BRIEF_v1.md`.
- Directions map (for owner discussion): `docs/research/THESIS_DIRECTIONS_AND_DECISIONS_MAP_v1.md`.

## Read order for the next session

1. `FINAL_HANDOFF_v1.md` (this file)
2. `PROJECT_FINAL_STATE_BEFORE_SUBMISSION.md` (freeze guardrails)
3. `docs/research/SUBMISSION_READY_CHECKLIST_v1.md`
4. `docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md` (independent audit record)
5. `paper/saner_rene_claim_matrix_v1.json`
6. `docs/research/WP0_TATQA_QUALIFICATION_APPENDIX_v1.md` + `docs/research/WP0_TATQA_PACKAGE_v1.md`
7. `docs/INDEX.md` (navigation)