# Loop C delta re-audit: revision 3 WP2 designation closure

Task id: `history-split-delta-reaudit-20261018-r2`
Role: Loop C independent reviewer.
Mode: read-only delta re-audit of `SPLIT_PROPOSAL.json` revision 3 against `LOOP_C_SPLIT_REAUDIT.md` N-1.

Use shell commands and mechanical recomputation before judgment. Do not trust descriptions, return text, or prior verdicts as proof. Do not modify reviewed files, raw data, old WP-2 artifacts, frozen material, scores, or prior reports. Do not start services, collect data, call scientific models, train, pilot, authorize collection, switch source, or release data. This AI review is not human semantic gold.

## Blocking finding to verify

`LOOP_C_SPLIT_REAUDIT.md` N-1 held that WP2 dry-run role designation had been applied selectively:

- r1 marked only `cluster_0584` and `cluster_1360` `EXPOSURE_UNKNOWN`;
- 17 other pending clusters with the same `WP2 dryrun role` evidence were left clean;
- revision 2 promoted `cluster_2314` into future despite its `pilot` designation.

The authorized conservative resolution is Reading C: every r1 appendix entry whose evidence records `WP2 dryrun role` is `EXPOSURE_UNKNOWN`, regardless of its original pool position.

## Revision 3 claim

Verify mechanically that revision 3:

1. applies that rule to all 19 WP2-designated pending clusters and reclassifies the 17 previously clean entries;
2. records raw r1 category counts 158 clean / 2 unknown / 5 exposed and adjusted counts 141 clean / 19 unknown / 5 exposed;
3. reruns the unchanged rank and produces future `1340, 0306, 0615, 0978, 1724, 1628, 2060, 1642`;
4. produces development `2010, 2096`;
5. produces 8 future / 2 development / 12 history / 131 reserve / 24 excluded, pairwise disjoint and closing to 177;
6. excludes `cluster_2314` as `EXPOSURE_UNKNOWN`;
7. keeps every selected future cluster at two or more contract-valid tasks with `task_eligible: true`;
8. preserves original unfiltered, revision 2, and revision 3 rejection traceability;
9. contains no task answer, gold, score, model result, effect estimate, or manual allowlist in selection;
10. leaves `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` at `NOT_READY_FOR_COLLECTION` with online authorization absent.

Also verify the advisory readability fix: each non-history bucket exposes `effective_exposure_category`, and N-4's test name now matches its count-error behavior.

## Output

Write one report if permitted:

`research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_SPLIT_DELTA_REAUDIT.md`

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED`.

State whether r2 N-1 is closed, list any new discrepancy, and whether revision 3 can be frozen for owner collection review. Explicitly state that this is AI evidence review, not human semantic gold, and that online collection remains unauthorized. If write access is denied, return the complete report in the task output for Loop D to transcribe.
