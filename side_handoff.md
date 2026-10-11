# Project: JinRongAgents
# Last updated: 2026-10-12 by Loop D final neat closeout (language pass, evidence verifier, memory automation, Loop C self-audit)
# Scope: fresh-session handoff for SANER Route A

## Start here

Read `PROJECT_CLOSEOUT_AND_HANDOFF_v1.md` first. It carries the current status, the canonical asset entry points, the branch ledger, the human-only blockers, the known debt, and the recommended continuation. This file is the short pointer; that file is the authority.

## Current status

- `PRIMARY_ROUTE = A` (SANER 2027 RENE, submission type `RENE: NegativeResult`).
- `SUBMISSION_DRAFT_COMPLETE = YES`. The bundle is compiled and audited: `paper/overleaf_bundle/saner_rene_manuscript_v1.pdf` (8 pages, 0 overfull boxes, references resolved, figures verified).
- Manuscript science is FROZEN for this stage: `paper/saner_rene_manuscript_v1.md` is the source of truth; do not modify title, abstract, contributions, results, discussion, or conclusion without a new user decision.
- Route B is `B_QUALIFICATION = NO / STOP_BRANCH`. Do not reopen it.
- Track P is CLOSED: PR-03 v3 = NEGATIVE, Evidence Ladder = LEVEL_0, no fourth recovery, spillover audit CLEAN. PR-EXP-01/04/07 remain frozen.
- Repository governance is `PASS`. LOCAL, GB10, and `origin/main` reconcile at the commit containing this handoff (tree hashes verified equal).
- 2026-10-12 additions: native language pass (US spelling + dash grammar; rebuilt PDF still 8 pages, 0 overfull); `scripts/verify_claim_evidence.py` now checks four groups (claim matrix, figure binding, citation resolution, prereg pins) and returns `WIDE_EVIDENCE_CHECK = PASS`; two stale figure-manifest source pins were re-pinned with a provenance note; a biweekly `memory-hygiene` automation was created; parent-workspace scratch was archived to `../_archive_2026-10-11/`; and `research/positive_repair_20261011/LOOP_C_SELF_AUDIT_v1.md` records the Loop C content as a self-audit (A/B/C all PASS with mechanical proofs) because every delegated audit failed to return.

## Scientific and claim boundary

- FinQA formal-v3 remains `SECOND_FLOW_MIXED`; the accepted interpretation is `MEASUREMENT_OBJECT_MISMATCH`, not protocol blindness or confirmed transfer.
- Multi-leaf evidence is positive but construct-sensitive: the direct-codebook ablation is also `1.0`, so claims must preserve that boundary.
- Stage E: 96/118 visible, OCR-like `0/13` across 11 clusters; single-responsive-leaf flat/hierarchy are affine/rank-equivalent; clean-only matched-FPR is `NOT_IDENTIFIABLE`.
- Paper story: blind spots exist; hierarchy alone does not create diagnosability; stage-aligned instrumentation matters; measurement objects must be causally aligned; observation surfaces themselves require validity auditing.

## Canonical evidence

- Claim authority: `paper/saner_rene_claim_matrix_v1.json`
- Scope lock: `paper/saner_rene_manuscript_scope_lock_v1.md`
- Venue requirements: `paper/SANER_RENE_2027_REQUIREMENTS.md`
- Submission bundle: `paper/overleaf_bundle/`
- Layout audit: `research/positive_repair_20261011/PDF_LAYOUT_AUDIT_v1.md`
- Abstract registration pack: `research/positive_repair_20261011/ABSTRACT_REGISTRATION_PACKAGE_v1.md`
- Track P registry + PR-03 closeout: `research/positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json`, `PR-03_v3_RESULT_v1.md`, `PR03_SPILLOVER_AUDIT_v1.md`
- FinQA interpretation: `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`

## Verification baseline

- Compiled PDF: 8 pages, 0 overfull `\hbox`, 0 undefined citations, 196 cosmetic underfull boxes.
- Anonymization: source scan PASS; PDF metadata Author empty, Title set.
- References: 21 entries, all verified (arXiv API + Crossref + official SANER RENE pages + NIST DOIs).
- GB10 full pytest: `929 passed / 13 skipped / 1 deselected / 10 warnings` (unchanged).
- Paper claims: `PASS 79/79` (5 claims) at the last governance audit.
- Cross-host receipts: `RECEIPT_VERIFIED`.
- Raw-byte note: one LOCAL receipt sidecar changes under Windows/Git EOL normalization; the normalized identity hash remains the cross-host authority.

## Next-session handoff

1. Wait for the owner decisions in `PROJECT_CLOSEOUT_AND_HANDOFF_v1.md` section 5 (coauthor ordering, corresponding author, final venue, anonymized artifact URL).
2. Then: fill the Data Availability anonymized URL, register the abstract (deadline 2026-10-19 AoE), and submit (deadline 2026-10-23 AoE). These are owner-triggered; the repository must not self-submit.
3. If continuing science, the only sanctioned next experiments are PR-04-R (generalization) and PR-01 v3 (checker fix); both need a reliable Loop A dispatch and must not touch the submission package.
4. Do not reopen Route B, the FinQA binding questions, or PR-03 (including any metric, baseline, or runtime optimization).
5. Do not modify frozen scientific results, metrics, thresholds, splits, joins, or sample populations.

## External blockers

- H1: coauthor ordering and corresponding author (advisor).
- Venue: final venue decision (SANER RENE is the default; CAIN/ICST are candidates).
- Anonymized artifact repository URL and its de-anonymization test.
- Owner authorization for abstract registration and submission.

## Workspace residue

Closeout removed two mojibake-named duplicate docs (byte-identical to their tracked namesakes) and committed eight previously untracked Stage E / Stage D scripts that tracked docs already reference. Remaining explained holds: GB10 runtime logs and untracked run directories (`research/positive_repair_20261011/runs/`), external repro/data/model assets, and LOCAL EOL-normalized surfaces. None of these is a current scientific authority.