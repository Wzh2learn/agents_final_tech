# Project: JinRongAgents
# Last updated: 2026-10-11 by Loop D repository-governance closeout
# Scope: fresh-session handoff for SANER Route A

## Current status

- `PRIMARY_ROUTE = A`. Resume the SANER RENE manuscript from `paper/saner_rene_manuscript_scope_lock_v1.md` and `paper/saner_rene_claim_matrix_v1.json`.
- Route B is `B_QUALIFICATION = NO / STOP_BRANCH`. Do not reopen it without a new user decision.
- Repository governance is `PASS / CROSS_HOST_RECEIPT_VERIFIED`. LOCAL, GB10, and `origin/main` reconcile at the commit containing this handoff.
- No new formal scientific experiment is required or authorized for the next Route A writing step.

## Scientific and claim boundary

- FinQA formal-v3 remains `SECOND_FLOW_MIXED`; the accepted interpretation is `MEASUREMENT_OBJECT_MISMATCH`, not protocol blindness or confirmed transfer.
- Both FinQA INVALID runs remain `INVALID_BUT_PRESERVED` and support no positive scientific claim.
- Multi-leaf evidence remains positive but construct-sensitive: the direct-codebook ablation is also `1.0`, so claims must preserve that boundary.
- The current paper story is: blind spots exist; hierarchy alone does not create diagnosability; stage-aligned instrumentation matters; measurement objects must be causally aligned; observation surfaces themselves require validity auditing.

## Canonical evidence

- Route A scope: `paper/saner_rene_manuscript_scope_lock_v1.md`
- Claim authority: `paper/saner_rene_claim_matrix_v1.json`
- Paper asset ledger: `paper/research_asset_map_v2.md`
- FinQA interpretation: `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`
- FinQA lineage: `docs/research/finqa_v2_asset_lineage_v1.md`
- Cross-host PASS: `docs/experiments/2026-10-11_cross_host_receipt_verification.json`
- Governance closeout: `docs/handoff/repository_governance_and_sync_2026-10-11.md`

## Verification baseline

- GB10 full pytest: `929 passed / 13 skipped / 1 deselected / 10 warnings`
- Final focused checks: `26 passed`
- Paper claims: `PASS 79/79`, 5 claims
- Submission package: `PASS 10/10`, `PENDING_EXTERNAL_ITEMS`, not submission-ready
- Docs lint: `PASS 0 fail / 6 existing warnings`
- Frozen hashes: `5/5`, 0 violations
- Cross-host receipts: `RECEIPT_VERIFIED`, content-semantic match and identity hash chains valid
- Raw-byte note: one LOCAL receipt sidecar changes under Windows/Git EOL normalization; normalized identity hash remains valid and is the cross-host authority.

## Next-session handoff

1. Resume Route A writing and evidence integration only.
2. Highest-ROI first task: bind Figure 1/2/3 source artifacts and complete the reviewer-attack claim audit.
3. Keep FinQA as a methodological boundary/failed-transfer autopsy, not transfer evidence.
4. Use NIST/construct-validity framing to connect the existing negative and construct-sensitive results.
5. Treat causal cost-aware checkpoint selection as future work, not a prerequisite for the SANER manuscript.
6. Do not modify frozen scientific results, metrics, thresholds, splits, joins, or sample populations.

## External blockers

External submission still requires official venue/template verification, authorship and affiliation, patent confirmation, anonymization, and camera-ready visual acceptance. None of these is solved by the repository-governance closeout.

## Workspace residue

No cleanup was performed. Preserved items include GB10 stashes/worktrees, external repro/data/model assets, 8 duplicate script holds, 2 UNKNOWN copies, two GB10 runtime-log snapshots, and LOCAL EOL/stat-only surfaces. They are explained holds, not current scientific authorities.
