# TQ-5 post-run focused review v1

> Reviewer: Loop D (AI), same orchestration context. Scope: focused deterministic verification of the completed TQ-5 run. This is not a fresh-context independent review and does not replace the already delivered TQ-4 run review or TQ-5 pre-run review.
> Run: `20261017T072340Z_5d8942bd` | Evidence: `TQ5_POST_RUN_RECOMPUTE_v1.py` / `.json`
> Verdict: `PASS_WITH_INTERPRETATION_LIMITS`

## 1. Fresh checks completed

- Run manifest: 83/83 listed run files match hash and byte count; no unexpected or missing run files.
- Execution snapshot: 8/8 files match; embedded snapshot-manifest hash matches `a9c1c79e...`.
- `RUN_META`: frozen config, runner, template, and authorization hashes match the actual files; `resumed=false`; 36 steps.
- Ledger: 36 reserve / 36 settle / 0 retry, 44,867 tokens on both the raw and ledger sides. The master mirror has 72 matching operational records after its existing `panel/run_id` addition and per-entry `utc` omission are normalized.
- Window: first request 15:23:54, last response 15:27:10 Asia/Shanghai, 196 seconds.
- Request surface: 36/36 parameter sets match the frozen model parameters; 36/36 HTTP 200; no retries.
- Output recomputation: actor scoring and evidence legality match the stored analysis exactly. Decisions recompute to B `accept10/alarm1/abstain1`, C `accept9/invalid3`. The original label is preserved as observed, and the corrected label/source hash/result-value invariants all validate.
- Prompt isolation: 36/36 canonical message hashes match; no construction-label markers; B sees the candidate answer/evidence surface, C does not see actor evidence or notes.

## 2. Findings

1. **Analysis label, corrected outside the snapshot.** The generic analyzer wrote the TQ-4 label into `part1.summary.label`. `TQ5_RESULTS_CORRECTED_v1.json` preserves all values and changes only that label plus provenance metadata. The frozen execution snapshot and original run analysis remain unchanged.
2. **T01 is a scorer-format limitation.** `(2.4)pts.` is standard accounting notation for a 2.4-point decrease and is copied from the source table. The frozen numeric parser reads it as positive 2.4 and scores NO_MATCH against -2.4. Do not count this as a proven actor error.
3. **T07 is UNSCORABLE as a gold comparison.** The question requires AVX total sales, while the official derivation uses `Product and equipment sales to affliates` as the denominator. Pre-run field/arithmetic checks cannot establish that semantic substitution. The actor output is separately internally inconsistent and its evidence has one out-of-bounds cell.
4. **T08 retains reference uncertainty.** The official derivation interprets "all years" as aggregate implied share-years (`321.7/0.64=502.66` million); the actor uses a 2020 point-in-time share count. B identifies the period/scope issue, C accepts. This is a reference-model disagreement, not an independently adjudicated gold error.
5. **T10 and T12 are precision-policy mismatches.** The outputs are reasonable rounded renderings (`3%` for 2.81%; `5.7%` for 5.67%) but fail the frozen reference-decimal tolerance. The questions do not specify output precision. Keep frozen NO_MATCH and semantic status `UNSCORABLE_FOR_PROVEN_ERROR`; they are not proven errors.
6. **Three C outputs are format failures.** C-T06 and C-T07 mix prose with embedded JSON; C-T10 truncates at 2,048 tokens. They remain `invalid`, not accept/alarm/abstain. No prose harvesting or retry is allowed.

## 3. Contribution boundary

- Supported: the run was executed once within budget from an immutable snapshot; saved bytes reproduce the machine scores, legality labels, decision counts, and isolation surface; the developmental table-disjoint result is descriptive.
- Not supported: C superior to B, a shared checker blind spot, a valid error rate, human scientific gold, proof that a reference is wrong or an actor answer is correct, report-level independence, training-data independence, or header-drift causality.
- Reference support remains `NOT_ASSESSED`. `scientific_gold_validity` remains `NOT_ESTABLISHED`.
- Recommended ruling: `NO_PROMOTION` for empirical claims; methods/limitations material may be retained as a non-promotional addendum.
