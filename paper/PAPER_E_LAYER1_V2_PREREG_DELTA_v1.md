# Paper E Layer-1 v2 Preregistration Delta (empty-header localisation) v1

> status: `FROZEN_DELTA_BEFORE_RERUN` | date: 2026-10-15 | author: Loop D
> authority: `paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md` (unchanged) plus this one delta.
> This file changes exactly one rule. It changes no frozen number, no manuscript, no claim.

## 1. What v1 produced (recorded fact, not a reason to tune)

`research/paper_e_layer1_20261015/LAYER1_SUMMARY_v1.md`: 59 dev cases -> LEGAL 12 / HARMFUL 12 /
INSUFFICIENT 35; U rate 0.593 > 0.30 -> `GOLD_NOT_ESTABLISHED`. The U-reason histogram is
32 x `source_header_empty_after_norm`, 3 x `nearest_neighbour_tie`, 0 x other.

## 2. The single change (structural justification, not outcome-driven)

v1 rule (table-level): if **any** source header in the table normalises to the empty string, the
whole table's cases are `INSUFFICIENT_EVIDENCE`.

v2 rule (column-local): an empty canonical header elsewhere in the table must NOT invalidate a
different column's case. It only removes that empty header from the candidate set, because it can
never be a binding target anyway. Formally, replace the v1 condition

    if any(header == "" for header in canonical_headers): -> U (whole table)

with:

    empty_positions = {p : canonical_headers[p] == ""}
    # empty headers are simply not candidates, and not an error for other columns
    if canonical_headers[c] == "":  -> U (case, reason source_header_empty_after_norm_column_local)
    if canonical_headers[c] in {canonical_headers[p] for p != c if p not in empty_positions}:
        -> U (case, reason source_header_canonical_collision_column_local)
    candidates = [p for p in positions if p not in empty_positions]
    # then apply the unchanged nearest-neighbour binding over `candidates` only

Rationale: a blank cell in an unrelated column of a financial table cannot change whether THIS
column's header still denotes its own column. v1's table-level rule was an over-broad
implementation of the design's "the header is empty after normalization" clause; the design
intended the clause to be about the case's own header. The change is justified by structure, was
identified from the reason histogram (not from which cases would flip), and is fixed before v2
re-reads any case content.

## 3. What is NOT changed (all frozen as in v1)

- `norm(.)`: NFKC -> casefold -> punctuation to space -> whitespace collapse -> strip. Unchanged.
- Injection identifier and the SHA-256 dev split (d mod 10 < 5). Unchanged.
- Value-invariance bytewise check. Unchanged.
- Nearest-neighbour binding: ordinary unit-cost Levenshtein over canonical strings; direct
  `i == o` preserved correspondence first; unique nearest neighbour binds; a tie is `U`.
  Unchanged.
- Labels, priority order, contingency, rates and the 30% U ceiling. Unchanged.
- Direction of harmfulness, claim boundary, and the prohibition on population/OCR claims. Unchanged.
- No model calls, judge calls, network, endpoints, training. calls = 0.

## 4. Decision rule for v2

- If v2 `U rate <= 0.30`: `GOLD_ESTABLISHED_ON_DEV` -> Layer 1 has produced a usable independent
  contract on the decidable subset; Layer 2 becomes eligible (separate authorisation).
- If v2 `U rate > 0.30`: stop this branch. Layer 1 conclusion stands as `GOLD_NOT_ESTABLISHED`;
  keep Paper E as the present case study; do not build Layer 2 on it.
- Report every number as-is; no further rule change after v2. This is the final prereg round.

## 5. Non-tuning statement

The change is a one-clause structural correction; it was not selected by trying variants against
outcomes and keeping the one that looked best. The dev split, the binding rule, the thresholds,
and the label definitions are identical to v1. Loop C must audit this delta before its result is
used for any decision.
