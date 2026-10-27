# Scoring V2 Contract

Identity: AI/automatic development reanalysis, not human gold, not a preregistered score, and not a complete semantic oracle.

## Immutable input

The scorer reads only the first immutable 40-call raw JSONL, the frozen 12-row reference chain, its annotated historical scoring fields, and the hash-bound TAT-QA development source used to reconstruct visible paragraph indexes. It selects the maximum `call_number` for each of the 12 UIDs × 3 arms. Historical raw, scores, manifests and reports are not modified.

The actor payload never contains gold answers, expected references, hidden units, reference programs, or UID branches. Those fields are used only after response production by the offline scorer.

## Five separate layers

1. **Strict JSON/schema/format:** exact six-key JSON object; typed answer, scalar-or-null `numeric_value`, nonempty unit, typed reference list, boolean unknown, typed clarification; unknown consistency; reference syntax; numeric answer applicability; nonnegative integral count; numeric arrays never pass.
2. **Answer content and exact set completeness:** scalar numeric answers require one complete reduced number; count answers require the count rather than an enumerated member set; multi-span answers require exact cardinality and exact numeric/text set with no extra span.
3. **Numeric equivalence, unit/scale and direction:** signed numeric value must equal the reference within tolerance; visible unit aliases are normalized; hidden scale is PENDING when it cannot be reconstructed from deployed visible evidence.
4. **Evidence-reference existence and semantic support:** string, dict and list program representations are supported through numeric-cell, visible-paragraph, text-span and typed-count reconstruction; `P<n>` indexes are mapped from visible paragraph order; table references must exist in the visible table. Exact role binding passes, broad column-only support is PENDING, and wrong/missing/nonexistent/out-of-range support fails.
5. **Final delivery:** `ACCEPT` only when all layers pass. Determinative failures yield `REJECT`; contract failures yield `STRICT_FAIL`; unresolvable legal support yields `PENDING_ADJUDICATION`; correctly declared unknown with required evidence absent yields `REASONABLE_UNKNOWN`. PENDING is not WRONG.

## Controls

Positive controls cover semantically equivalent currency display, exact multi-span sets, and correct mean/count typed reductions. Adversarial controls cover wrong unit/direction, extra span, wrong period/row, missing/nonexistent/out-of-range references, numerically equal wrong-role answers, negative counts, numeric-array contract violations, reasonable unknown, and unresolvable-reference PENDING behavior.

Correct controls must reach `ACCEPT`; listed errors must not be silently accepted.
