# Loop C focused re-audit: exposure-qualified split revision

Task id: `history-split-reaudit-20261018-r1`
Role: Loop C independent reviewer.
Mode: read-only focused re-audit of the revised future/development/history/reserve split.

Use shell commands and mechanical recomputation before any judgment. Do not trust the task description, `OFFLINE_RETURN.md`, prior review verdicts, or commit messages as proof. Do not modify reviewed artifacts, raw data, old WP-2 files, frozen material, scores, or prior reports. Do not start a service, collect data, call a scientific model, train, pilot, authorize collection, switch source, or release data. This AI review is not human semantic gold.

## Prior evidence

Read `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md`. Its r1 verdict is `CONDITIONAL` for the unfiltered split:

- 158 of 165 pending clusters are `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`;
- 2 are `EXPOSURE_UNKNOWN`;
- 5 are `MODEL_OR_FEEDBACK_EXPOSURE`;
- the original future 8 contained 5 clean, 2 unknown, and 1 exposed;
- the original review did not authorize making a replacement split.

## Revised proposal to audit

`SPLIT_PROPOSAL.json` revision 2 claims it:

1. excludes every non-clean reviewed category;
2. applies the unchanged `sha256(seed:scope:cluster_id) ascending` rank to the clean pool;
3. selects 8 future, then 2 development, then 148 reserve;
4. preserves 7 excluded pending-review clusters and the 12 existing history clusters;
5. does not use task answers, reference values, model results, scores, or effect estimates.

The claimed revised future set is:

- `cluster_1340`
- `cluster_0306`
- `cluster_0615`
- `cluster_0978`
- `cluster_1724`
- `cluster_1628`
- `cluster_2060`
- `cluster_2314`

## Required checks

1. Reparse all 165 per-cluster records from `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md`; verify category counts and cluster-level conservative aggregation.
2. Recompute the rank key from the declared seed and verify the revised future/development/reserve order is exactly the first clean clusters in that order.
3. Verify the only changes from the original proposal are removal of `cluster_0584`, `cluster_0599`, and `cluster_1360` and promotion of the next clean candidates under the same rule.
4. Verify no future cluster is `EXPOSURE_UNKNOWN`, exposed, method-development/diagnostic, or outside the 165 reviewed pending clusters.
5. Verify future, development, history, reserve, and excluded buckets are pairwise disjoint; accounting closes to 177 eligible clusters.
6. Verify each selected future cluster has at least two contract-valid tasks and each pending member is `task_eligible: true`.
7. Inspect the generator and tests for hidden selection based on gold, answers, scores, results, or manual per-cluster overrides.
8. Verify the original unfiltered proposal and rejected IDs remain traceable in `SPLIT_PROPOSAL.json.revision`.
9. Verify `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` includes the program review and current split hashes and remains `NOT_READY_FOR_COLLECTION`.
10. Confirm local and GB10 13/13 receipts pin the current implementation and tests.

## Output

Write exactly one report:

`research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_SPLIT_REAUDIT.md`

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED`.

The report must state:

- whether revision 2 is a pure qualification-and-rank reselection;
- the recomputed 8 future cluster IDs in order;
- any selected cluster that remains unsupported;
- any new discrepancy with file/line or JSON path;
- whether the revised split can be frozen for owner collection review;
- that this AI review is not human semantic gold;
- that online collection remains unauthorized.

Do not create a second summary file. Do not revise `OFFLINE_RETURN.md`, `SPLIT_PROPOSAL.json`, the hash bundle, tests, or implementation. If write access is denied, return the full report in the task output for Loop D to transcribe.
