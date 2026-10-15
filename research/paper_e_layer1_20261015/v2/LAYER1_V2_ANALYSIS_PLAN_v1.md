# Paper E Layer-1 v2 Analysis Plan (Independent Binding Gold)

> Status: `FROZEN_BEFORE_HELDOUT_LABELS`
> Date: 2026-10-15
> Relation to v1: v1 remains unchanged and its result is `GOLD_NOT_ESTABLISHED`.
> This v2 plan is a separate pre-registered follow-up; it does not rewrite v1 and it does not
> convert any v1 dev case into confirmatory evidence.

## 1. Why v2 exists

v1 used the rule "any empty canonical source header makes every case on that table
`INSUFFICIENT_EVIDENCE`". The v1 result had 35/59 dev cases labelled `U`, of which 32 were
caused by that table-wide empty-header rule, including tables where the empty header was not
the target column.

The v1 dev counterfactual (computed read-only after v1 froze) suggested that most of those
cases become decidable when empty non-target headers are removed from the candidate binding
set. That counterfactual is a design input only. It is not a v2 result and must not be cited as
evidence for v2.

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

## 4. Pre-registered decision gates

- `GOLD_ESTABLISHED` if `u_rate_heldout <= 0.30`.
- `LAYER2_GO` if all three hold:
  - `u_rate_heldout <= 0.30`;
  - at least 8 held-out cases are `H`;
  - at least 8 held-out cases are `E`;
  - at least 8 held-out cases are checker-blind.
- Otherwise: `LAYER1_V2_NO_GO` and keep the current case-study manuscript.

No threshold may be changed after held-out labels are read.

## 5. Outputs

All outputs go under `research/paper_e_layer1_20261015/v2/`:

- `LAYER1_V2_RESULTS_v1.json`
- `LAYER1_V2_RECEIPT_v1.json`
- `LAYER1_V2_SUMMARY_v1.md`

The receipt must record:

- input hashes;
- plan hash;
- v1 artifact hashes;
- held-out case count;
- zero model/judge/network/training calls;
- every `U` reason and count.

## 6. Stop conditions

- Any input hash mismatch -> stop.
- Any attempt to tune `norm(.)`, the split, the tie policy, or the gates after held-out labels
  are read -> run invalid.
- `u_rate_heldout > 0.30` -> `GOLD_NOT_ESTABLISHED`, no Layer 2.
- No model call, judge call, network call, or training call.
- Do not modify the v1 run directory, the manuscript, claim matrix, or scope lock.

## 7. Audit and execution order

1. Freeze this plan (record SHA-256).
2. Independent pre-result audit (Loop C) checks the rule change, the held-out separation, and
   the absence of post-hoc threshold fitting.
3. Only after audit PASS: run v2 on the held-out cases.
4. Loop C post-result audit recomputes counts and rates.

The v2 run is not authorized by this document alone. It becomes executable only after the
pre-result audit passes.
