# Paper E Layer-1 v2 Canonical Preregistration (Independent Binding Gold) v1

> Status: `FROZEN_BEFORE_ANY_V2_LABEL` (rev 2 clears K1-K6)
> Date: 2026-10-15
> Supersedes, before any v2 label is computed (rev 2 also supersedes `LAYER1_V2_CANONICAL_PREREG_v1.md` only before any label):
> - `research/paper_e_layer1_20261015/v2/LAYER1_V2_ANALYSIS_PLAN_v1.md`
> - `research/paper_e_layer1_20261015/v2/LAYER1_V2_ANALYSIS_PLAN_v2.md`
> - `paper/PAPER_E_LAYER1_V2_PREREG_DELTA_v1.md`
> v1 artifacts remain unchanged. v1 result remains `GOLD_NOT_ESTABLISHED`.

## 1. Purpose

v1 showed 35/59 dev cases `U`, of which 32 came from the table-wide rule "any empty
canonical source header makes every case on that table `U`". The purpose of this canonical
preregistration is to test whether a column-local empty-header rule yields a usable independent
binding gold, first on dev and then on the untouched held-out cases.

The v1 dev counterfactual is a design input only. It is not a v2 result and must never be cited
as evidence for v2.

## 2. Frozen rule relative to v1

Everything from v1 stays frozen except the empty-header/collision handling:

- `norm(.)` unchanged: NFKC -> casefold -> punctuation to ASCII space -> whitespace collapse
  -> strip.
- Injection identifier and outcome-blind SHA-256 split unchanged (`d mod 10 < 5` = dev).
- Provenance checks unchanged.
- Bytewise value-invariance unchanged.
- Ordinary unit-cost Levenshtein unchanged.
- Direct `i == o` preserved correspondence first.
- Unique nearest neighbour binds; tie is `U`.
- Labels remain `{LEGAL_VARIATION (E), HARMFUL_ERROR (H), INSUFFICIENT_EVIDENCE (U)}`.
- Checker verdict is read only after labels are frozen.

Column-local replacement rule:

1. Let `c` be the target column, `H[p]` the canonical header at position `p`.
2. Let `empty_positions = {p : H[p] == ""}`.
3. Empty positions are removed from the candidate binding set; they are not a table-wide error.
4. If `H[c] == ""`: case is `U`, reason `source_header_empty_after_norm_column_local`.
5. If `H[c]` equals a non-empty `H[p]` for some `p != c`: case is `U`, reason
   `source_header_canonical_collision_column_local`.
6. Obtain candidates as all positions not in `empty_positions`.
7. If the candidate set is empty: case is `U`, reason `source_header_set_empty`.
8. Otherwise apply the unchanged nearest-neighbour/tie rule over candidates only.

## 3. Closed case-level U reason codes

All codes not listed as new below are exactly the v1 codes:

`uid_not_string`, `table_lookup_missing`, `header_row_not_zero`, `table_header_missing`,
`source_header_not_list`, `injected_header_not_list`, `source_header_non_string`,
`column_index_not_integer`, `column_index_out_of_range`,
`original_header_provenance_mismatch`, `injected_header_provenance_mismatch`,
`row_count_mismatch`, `value_serialization_failure`, `value_invariance_failed_bytewise`,
`original_header_canonical_provenance_mismatch`, `header_non_string`,
`injected_header_empty_after_norm`, `nearest_neighbour_tie`.

New or renamed codes:

- `source_header_empty_after_norm_column_local` (replaces the v1 table-wide
  `source_header_empty_after_norm`)
- `source_header_canonical_collision_column_local` (replaces the v1 table-wide
  `source_header_canonical_collision`)
- `source_header_set_empty`

Precedence if several U causes apply: first source/provenance/serialization checks in the v1
order, then step 4 above, then step 5 above, then step 7 above, then `nearest_neighbour_tie`.
Every `U` case gets exactly one primary reason from the closed list.

## 4. Two-stage sample design

- Stage V2-D: dev 59 cases only.
- Stage V2-H: held-out 59 cases only, run only if Stage V2-D is established.
- The dev 59 were inspected during v1 and are development data.
- The held-out 59 were never labelled by v1 or v2 and are the validation sample.
- No mixing of dev and held-out in one confirmatory rate.

## 5. Exhaustive decision function

Stage V2-D:

- Stop if any Section 7 condition fires.
- Else if `u_rate_dev <= 0.30`: `GOLD_ESTABLISHED_ON_DEV`.
- Else: `GOLD_NOT_ESTABLISHED_NO_GO`; stop this branch.

Stage V2-H (only after `GOLD_ESTABLISHED_ON_DEV`):

- Stop if any Section 7 condition fires.
- Else if `u_rate_heldout <= 0.30`: `GOLD_ESTABLISHED_ON_HELDOUT`.
- Else: `GOLD_NOT_CONFIRMED_ON_HELDOUT`; keep Paper E as the current case study.

`GOLD_ESTABLISHED_ON_HELDOUT` permits only a separate Layer 2 design/preregistration phase.
It does not authorize Layer 2 execution, a manuscript change, or a population claim.

## 6. Pinned hashes

- injection map:
  `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`
- source tables:
  `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302`
- injected tables:
  `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9`
- checker comparison target:
  `eff82b0b7abbb8edcb8aef24a921806a760624fc84b57b3c2e54331394f99ea5`
- v1 plan:
  `a275e55ae3485db5f37716c6c6c229f9d4efd58dfbb078af2db5768cc043e3d9`
- v1 results:
  `359c7c047b792aaa9f70437137b1bf8973bba10dad4816075cebe81edbd420c4`

## 7. Stop conditions

- `INPUT_MISSING`: any required input absent.
- `HASH_MISMATCH`: any pinned hash differs.
- `RULE_AMBIGUOUS`: split or `norm(.)` not implementable unambiguously.
- `UNDECIDED_CASE`: a case cannot be decided by the contract and is not explicitly U.
- `GOLD_NOT_ESTABLISHED_NO_GO` or `GOLD_NOT_CONFIRMED_ON_HELDOUT`: rate gate fails.
- `ZERO_CALL_VIOLATION`: any model, judge, API, endpoint, network, or training call is made.
  Any such call invalidates the run; it is not acceptable to merely record it.
- `POST_FREEZE_CHANGE`: any rule, threshold, gate, or reason code changes after the first label
  of the relevant stage is computed.

## 8. No-tuning list

After the first v2 label is computed, do not change `norm(.)`, split, provenance checks,
bytewise value invariance, Levenshtein/tie policy, the column-local rule, reason codes, gates,
or the decision function.

## 9. Outputs

Stage V2-D writes only under `research/paper_e_layer1_20261015/v2/dev/`:
`V2D_RESULTS_v1.json`, `V2D_RECEIPT_v1.json`, `V2D_SUMMARY_v1.md`.

Stage V2-H writes only under `research/paper_e_layer1_20261015/v2/heldout/`:
`V2H_RESULTS_v1.json`, `V2H_RECEIPT_v1.json`, `V2H_SUMMARY_v1.md`.

Each receipt records input hashes, plan hash, stage sample size, zero-call attestation, every
U reason and count, and the stage verdict.

## 10. Audit and execution order

1. Freeze this canonical prereg and record its SHA-256.
2. Independent pre-result audit checks this plan against prior conditions A-G and the conflict
   with the delta.
3. Only after audit PASS: run Stage V2-D.
4. Independent post-result audit of Stage V2-D.
5. Only if Stage V2-D is established: run Stage V2-H.
6. Independent post-result audit of Stage V2-H.

Layer 2 execution remains separately unauthorized.


## 11. Rev-2 clarifications (K1-K6, before any label)

K1. Sections 7 and 8 bind across both stages. No rule, threshold, gate, or reason code may
change between Stage V2-D and Stage V2-H. The clause "of the relevant stage" in Section 7 is
read as "of either stage"; this section is the controlling reading.

K2. Precedence when multiple U causes apply: after the source/provenance/serialization checks,
`header_non_string` is checked first, then `injected_header_empty_after_norm`, then
`source_header_empty_after_norm_column_local`, then
`source_header_canonical_collision_column_local`, then `source_header_set_empty`, then
`nearest_neighbour_tie`. Therefore, if both an empty injected header and an empty target header
apply, the primary reason is `injected_header_empty_after_norm`.

K3. v2 does not replace v1. v1's `GOLD_NOT_ESTABLISHED` result stands and is reported as v1's
result. No Stage V2-D (dev) number may be reported as a v2 validation result. Only Stage V2-H
(held-out) can produce the confirmatory `GOLD_ESTABLISHED_ON_HELDOUT` verdict.

K4. Disclosure: Stage V2-D labels the dev 59 and is development-side. Only Stage V2-H is
confirmatory. The held-out header pairs were visible in v1's `scope.held_out_injection_ids`,
but no held-out label was computed; "untouched" in Section 1 means untouched by any label,
not unread as identifiers.

K5. Rates are defined exactly as `u_rate_dev = n(U among dev 59) / 59` and
`u_rate_heldout = n(U among held-out 59) / 59`. Emit only the closed reason codes in Section 3;
never emit the earlier drafts' `target_header_empty_after_norm`, `candidate_set_empty`, or
`source_header_canonical_collision`.

K6. Stage V2-D must not run until an independent pre-result audit of this rev-2 document passes.
Preparation of runner scripts and prompts is allowed; label computation is not.
