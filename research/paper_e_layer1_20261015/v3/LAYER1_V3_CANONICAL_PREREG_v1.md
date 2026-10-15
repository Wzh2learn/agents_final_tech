# Paper E Layer-1 v3 Canonical Preregistration (held-out only)

> Status: `FROZEN_BEFORE_ANY_V3_LABEL` | 2026-10-15
> Supersedes, before any v3 label exists: `LAYER1_V2_ANALYSIS_PLAN_v1.md`,
> `LAYER1_V2_ANALYSIS_PLAN_v2.md`, `LAYER1_V2_CANONICAL_PREREG_v1.md`,
> `LAYER1_V2_CANONICAL_PREREG_v2.md`, `paper/PAPER_E_LAYER1_V2_PREREG_DELTA_v1.md`.
> v1 remains unchanged: `GOLD_NOT_ESTABLISHED`.

## 0. Design amendment recorded before v3 labels

The original design used table-level collision. v3 localises collision to the target column:
a non-empty duplicate elsewhere cannot determine whether THIS column still denotes its own
column. Justification: after empty-header localisation, table-level collision would preserve
the same structural defect under a different mechanism. This amendment is structural, not
outcome-fitted; no v3 label exists at freeze time.

## 1. Why v3 exists

v1 failed its 30% U ceiling (35/59, U=0.593220) because 32/35 U came from empty headers
elsewhere in the table. An independent audit's dev sensitivity (case-level empty reading)
gave 29E/23H/7U (U=0.118644), but that dev result is public and cannot be confirmatory.
v3 therefore freezes the exact rule and runs only the untouched held-out 59.

## 2. Frozen rule

- `norm(.)`: NFKC -> casefold -> punctuation to ASCII space -> whitespace collapse -> strip.
- Outcome-blind SHA-256 split unchanged; v3 sample = held-out 59 only.
- Provenance checks, bytewise value-invariance, unit-cost Levenshtein, direct `i == o` first,
  unique-nearest binding, tie-as-U: all unchanged from v1.
- Labels: E, H, U.

Column-local procedure for target column c:

1. Canonical headers H[p].
2. empty_positions = {p : H[p] == ""}; they leave the candidate set and are not table-wide errors.
3. If H[c] == "": U, `source_header_empty_after_norm_column_local`.
4. If H[c] equals non-empty H[p], p != c: U, `source_header_canonical_collision_column_local`.
5. Candidates = positions not in empty_positions.
6. If candidates empty: U, `source_header_set_empty`.
7. Else apply unchanged nearest-neighbour/tie rule over candidates.

## 3. Closed U codes

`uid_not_string`, `table_lookup_missing`, `header_row_not_zero`, `table_header_missing`,
`source_header_not_list`, `injected_header_not_list`, `source_header_non_string`,
`column_index_not_integer`, `column_index_out_of_range`,
`original_header_provenance_mismatch`, `injected_header_provenance_mismatch`,
`row_count_mismatch`, `value_serialization_failure`, `value_invariance_failed_bytewise`,
`original_header_canonical_provenance_mismatch`, `header_non_string`,
`injected_header_empty_after_norm`, `nearest_neighbour_tie`,
`source_header_empty_after_norm_column_local`,
`source_header_canonical_collision_column_local`, `source_header_set_empty`.

Precedence: source/provenance/serialization checks in v1 order; then `header_non_string`; then
`injected_header_empty_after_norm`; then the three new column-local codes in the order listed;
then `nearest_neighbour_tie`.

## 4. Decision rule

- u_rate_heldout = n(U among held-out 59) / 59.
- Any stop fires -> stop/report.
- Else u_rate_heldout <= 0.30 -> `GOLD_ESTABLISHED_ON_HELDOUT`.
- Else -> `GOLD_NOT_ESTABLISHED`.
- `GOLD_ESTABLISHED_ON_HELDOUT` allows only a separate Layer 2 design phase; no Layer 2
  execution, no manuscript change, no population claim.
- v3 does not replace v1; no v3 number is a dev number, no v1 number is validation.

## 5. Pinned hashes

- plan: pinned by `GOVERNING_MANIFEST_v1.json` after freeze (receipt records it)
- injection map: `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`
- source tables: `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302`
- injected tables: `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9`
- checker target: `eff82b0b7abbb8edcb8aef24a921806a760624fc84b57b3c2e54331394f99ea5`
- v1 plan: `a275e55ae3485db5f37716c6c6c229f9d4efd58dfbb078af2db5768cc043e3d9`
- v1 results: `359c7c047b792aaa9f70437137b1bf8973bba10dad4816075cebe81edbd420c4`

## 6. Stop conditions

`INPUT_MISSING`, `HASH_MISMATCH`, `RULE_AMBIGUOUS`, `UNDECIDED_CASE`,
`ZERO_CALL_VIOLATION` (any model/judge/API/network/training call invalidates the run),
`POST_FREEZE_CHANGE` (any rule/threshold/gate/reason code changes after the first v3 label),
`u_rate_heldout > 0.30` -> `GOLD_NOT_ESTABLISHED`.

## 7. Outputs

Under `research/paper_e_layer1_20261015/v3/`: `V3_RESULTS_v1.json`, `V3_RECEIPT_v1.json`,
`V3_SUMMARY_v1.md`. Receipt records input hashes, plan hash from the governing manifest,
held-out sample size, zero-call attestation, U reason counts, verdict.

## 8. Audit and execution

1. Freeze this plan and `GOVERNING_MANIFEST_v1.json`; record hashes.
2. Independent final pre-result audit. Any scope change beyond the frozen amendment = STOP.
3. Only after audit PASS: run held-out v3 once.
4. Independent post-result audit recomputes counts and rates.
