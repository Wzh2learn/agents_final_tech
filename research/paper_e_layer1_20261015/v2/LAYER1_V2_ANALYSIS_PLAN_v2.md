# Paper E Layer-1 v2 Analysis Plan (Independent Binding Gold, rev 2)

> Status: `FROZEN_BEFORE_HELDOUT_LABELS`
> Date: 2026-10-15
> Supersedes: `LAYER1_V2_ANALYSIS_PLAN_v1.md` (before any held-out label was computed).
> Relation to v1: v1 remains unchanged and its result stays `GOLD_NOT_ESTABLISHED`.
> This rev-2 document answers the seven conditions in the native Loop C audit
> (`LAYER1_V2_PRERESULT_AUDIT_v1.md`, a raw launcher-log transcript, sha256
> `212034a364e139e0e0190a66a57b3854518813106b2815247d8998073a7bb77b`).

## 1. Why v2 exists

v1 used the rule "any empty canonical source header makes every case on that table
`INSUFFICIENT_EVIDENCE`". The v1 result had 35/59 dev cases labelled `U`, of which 32 were
caused by that table-wide empty-header rule, including tables where the empty header was not
the target column.

The v1 dev counterfactual (computed read-only after v1 froze) is a design input only. It is not
a v2 result and must not be cited as evidence for v2.

## 2. Scope

- Same frozen inputs as v1: 118 injections, 95 source tables, same injection map and checker
  comparison target.
- Same outcome-blind split as v1: 59 dev cases and 59 held-out cases.
- v2 labels are computed on the **held-out 59 cases only**. The dev 59 were inspected during
  v1 and can no longer serve as a confirmatory sample.
- This is a feasibility follow-up. It does not estimate a population rate and does not establish
  an OCR conclusion or a harmful blind spot.

## 3. Frozen rule changes (isolated to one mechanism)

The following parts of the v1 contract remain exactly as frozen:

- `norm(.)` canonicalization.
- Outcome-blind SHA-256 split.
- Provenance checks between injection entry and source/injected tables.
- Bytewise value-invariance check.
- Levenshtein distance over canonical header strings.
- Unique-nearest-neighbour binding and tie-as-`U` policy.
- Checker verdict is read only after labels are frozen.

The only v2 change is empty-header handling:

1. Empty canonical headers are removed from the candidate binding set.
2. If the target column's canonical header is empty, the case is `U`.
3. If the candidate binding set is empty, the case is `U`.
4. Collision checks apply to non-empty canonical headers only.
5. A non-target empty header no longer makes the whole table `U`.
6. Every other v1 `U` reason remains `U`.

The labels remain `{LEGAL_VARIATION (E), HARMFUL_ERROR (H), INSUFFICIENT_EVIDENCE (U)}`.

## 4. Closed U-reason codes

Every v2 case-level `U` must use exactly one of these codes:

`uid_not_string`, `table_lookup_missing`, `header_row_not_zero`, `table_header_missing`,
`source_header_not_list`, `injected_header_not_list`, `source_header_non_string`,
`column_index_not_integer`, `column_index_out_of_range`,
`original_header_provenance_mismatch`, `injected_header_provenance_mismatch`,
`row_count_mismatch`, `value_serialization_failure`, `value_invariance_failed_bytewise`,
`original_header_canonical_provenance_mismatch`, `header_non_string`,
`injected_header_empty_after_norm`, `target_header_empty_after_norm`, `candidate_set_empty`,
`source_header_canonical_collision`, `nearest_neighbour_tie`.

`source_header_canonical_collision` is evaluated over non-empty canonical headers only. v2
must not emit the v1 code `source_header_empty_after_norm`.

## 5. Exhaustive decision function

After all held-out case labels are frozen:

- If any stop condition in Section 7 fires: report the stop and do not compute further metrics.
- Else if `u_rate_heldout > 0.30`: report `GOLD_NOT_ESTABLISHED_NO_GO`.
- Else: report `GOLD_ESTABLISHED`.

`GOLD_ESTABLISHED` permits only a separate Layer 2 design/preregistration phase. It does not
authorize Layer 2 execution, does not authorize a manuscript change, and does not create a
population claim. Any Layer 2 sample-size planning may use the v2 estimates for design only and
must be labelled exploratory for that purpose.

## 6. Pinned hashes

- injection map:
  `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`
- source tables:
  `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302`
- injected tables:
  `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9`
- checker comparison target:
  `eff82b0b7abbb8edcb8aef24a921806a760624fc84b57b3c2e54331394f99ea5`
- v1 analysis plan:
  `a275e55ae3485db5f37716c6c6c229f9d4efd58dfbb078af2db5768cc043e3d9`
- v1 results:
  `359c7c047b792aaa9f70437137b1bf8973bba10dad4816075cebe81edbd420c4`

## 7. Stop conditions

Report and stop without changing this plan if:

- any required input is missing (`INPUT_MISSING`);
- any pinned hash differs (`HASH_MISMATCH`);
- the split or `norm(.)` is not implementable unambiguously (`RULE_AMBIGUOUS`);
- a case is not decided by the contract and is not clearly `U`;
- `u_rate_heldout > 0.30` (`GOLD_NOT_ESTABLISHED_NO_GO`);
- any rule, threshold, gate, or reason-code set in this plan is changed after the first
  held-out label is computed.

## 8. No-tuning list

Do not tune any of the following after held-out labels are read:

- `norm(.)`;
- split rule;
- provenance checks;
- bytewise value-invariance check;
- Levenshtein distance or tie policy;
- the empty-header/candidate-set rule;
- decision gates or the decision function;
- reason codes.

## 9. Outputs

All outputs go under `research/paper_e_layer1_20261015/v2/`:

- `LAYER1_V2_RESULTS_v1.json`
- `LAYER1_V2_RECEIPT_v1.json`
- `LAYER1_V2_SUMMARY_v1.md`

The receipt must record input hashes, plan hash, v1 artifact hashes, held-out case count,
zero model/judge/network/training calls, and every `U` reason and count.

## 10. Audit and execution order

1. Freeze this rev-2 plan and record its SHA-256.
2. Native/independent pre-result audit checks this plan against the seven conditions in
   `LAYER1_V2_PRERESULT_AUDIT_v1.md`.
3. Only after audit PASS: run v2 on the held-out cases.
4. Independent post-result audit recomputes counts and rates.
