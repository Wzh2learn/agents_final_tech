# TQ-4 Scorer Fix Notes (v2 vs v1)

> Basis: 2026-10-16 chief-planner adjudication (three fixes stated verbatim in the task).
> v1 = `tq3_execution_prep_v1/tools/tq3_scoring_entry.py` (frozen, read-only).
> v2 = `tq4_calibration_v1/scorer_v2/tq4_scoring_entry.py` (this package).
> Regression evidence: `scorer_v2/regression/regression_results.json` (18/18 checks; 8 genuine v1-vs-v2 status flips on the reconstructed counterexamples; correct samples unchanged).

## Semantics changes

1. Percent conversion (explicit units only)
   - v1: divided by 100 only when a '%' marker existed AND |value| > 1.5 (magnitude decided).
   - v2: conversion depends only on the marker plus the material's frozen `unit_kind`:
     - `unit_kind=ratio`: '%' -> value/100; no marker -> value as-is.
     - `unit_kind=percent`: value is already in percent space (marker optional).
     - `unit_kind=plain`: a '%' marker -> `UNSCORABLE_PERCENT_MARKER_ON_PLAIN_UNIT`.
   - Fixed counterexamples: "1.5%" vs ratio 0.015 (v1 false reject); "0.5%" vs ratio 0.5 (v1 false accept).

2. Numeric answers (no cherry-picking)
   - v1: scanned all numbers in the answer; accepted if ANY matched.
   - v2: exactly one candidate number -> compare; zero -> `UNSCORABLE_NO_NUMERIC`; two or more -> `UNSCORABLE_MULTIPLE_NUMBERS`.
   - Fixed counterexample: "The difference is 14054, but the reverse order gives 13999." (v1 accepted the correct one; v2 refuses to pick).

3. List answers (full-set equality)
   - v1: substring containment in either direction counted as MATCH.
   - v2: normalized full equality OR item-set equality (split on ' and ' / ',' / ';' / '&', identically on both sides); superset or subset -> NO_MATCH.
   - Fixed counterexamples: superset with extra items (v1 accepted); two-item subset (v1 accepted by reverse containment); correct reorder (v1 rejected; v2 accepts).

4. No guessing
   - v1: unparseable numeric/date answers were asserted as NO_MATCH.
   - v2: unparseable -> explicit `UNSCORABLE_*` statuses (no verdict asserted).

## Status vocabulary (v2)

MATCH / NO_MATCH (score 1.0 / 0.0); INVALID_ACTOR_OUTPUT; BLOCKED_SCALE_MISSING / BLOCKED_SCALE_UNRESOLVED (carried);
UNSCORABLE_NO_NUMERIC; UNSCORABLE_MULTIPLE_NUMBERS; UNSCORABLE_UNIT_KIND_UNSPECIFIED; UNSCORABLE_PERCENT_MARKER_ON_PLAIN_UNIT;
UNSCORABLE_EXPECTED_ITEMS_MISSING; UNSCORABLE_EMPTY_ITEMS; UNSCORABLE_DATE_PARSE (score None on all UNSCORABLE/BLOCKED).

## Compatibility

- `load_input` / `validate_reference_coords` / `InputRejected`: carried unchanged from v1.
- Protocol v2 evidence legality lives in `check_evidence_legality()` (mechanical only; support is NOT judged there).
- v1 remains frozen; v2 is the target scorer for TQ-4 and for re-scoring saved outputs.
