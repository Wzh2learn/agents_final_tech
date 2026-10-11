# PR-03 v3 Design Decision v1 (Track P recovery #1)

> date: 2026-10-11 | status: DESIGN DECIDED, prereg NOT yet written, NOT executed | prerequisite: EXECUTION_PREFLIGHT_PASS
> core question UNCHANGED: does a preregistered table-structure oracle recover held-out structural failures that the existing field-hit-derived oracle misses?

## Round-1 failure recap (frozen record unchanged)
Registered INVALID via prereg-v2 sanity gate; Loop C post-result audit: CHALLENGE -> recommended NOT_EVALUABLE. Two causes: (i) the "carrier non-monotonicity" sanity clause is unsatisfiable-by-construction on structurally-null carriers (a constant-zero structural column is vacuously monotone) and contradicts the A3 expected-0 arm; (ii) 2 held-out P1 tables have all-empty headers where the field-hit baseline was undefined.

## Decisions (to be frozen verbatim in the v3 prereg + implementation contract)
1. **PATH A chosen: total oracle definition.** `structural_signature = (column_count, ordered positional header-token sequence under the pinned canonicalizer with "" allowed as a token, row_count)`. Empty-header tables are DEFINED: their signature is `(n_cols, ["",...], n_rows)`; transposing two empty headers yields an identical signature -> response 0 (defined, not undefined). No population exclusion.
2. **Baseline totality by task semantics (frozen before outcomes).** Where the field-hit baseline is undefined (all-empty header), its semantic value is defined as zero observable hits -> hit-rate 0 -> response `0 < 0 = false = 0`. This is a semantics-based definition, not a per-case patch.
3. **Sanity gate replaced (Loop D contract repair).** Remove the non-monotonicity-vs-field-hit clause. New non-degeneracy gate, evaluated on fixtures/controls BEFORE P1 outcomes: (a) the structural oracle is not constant (fires on a control set that DOES contain structural changes and is expected 1); (b) it returns 0 on no-op/identity and value-only arms (A0/A1); (c) it is not identical to field-hit on the P1 population (>=1 disagreement), which measures the design-intended difference rather than a structural-null tautology. Constant-1 detectors fail (b).
4. **Mixed-diagnosability ground truth fixed (audit F3).** The diagnosability population uses: P1 rows -> `stage=M`, `family=topology_transposition` (the artifact genuinely carries the structural change); frozen-carrier rows -> stage labels only (their contract-derived artifacts vary by stage, so carrier family labels are not used for a family metric). Report stage and family components separately + the combined floor; declare the composition.
5. **No post-hoc exclusion.** Justification: (i) the 2 empty-header cases are retained IN the population under PATH A; (ii) nothing is dropped after seeing outcomes; (iii) the gate and semantics are frozen before P1 generation; Loop C must re-verify this order in the pre-result audit.
6. **Metrics unchanged.** Primary: held-out incremental coverage + stage/family diagnosability. Secondary: unique catches, M1 regression, cost. POSITIVE/NULL/NEGATIVE/INVALID/NOT_EVALUABLE taxonomy from the round-1 audit (DIAG_ONLY recorded with NULL; NOT_EVALUABLE never merged into NULL).

## Failure policy (owner-set)
If v3 again stops at schema / gate / provenance / undefined-domain WITHOUT entering effect measurement -> `PR-03 = NOT_EVALUABLE_FINAL`, branch stopped; no fourth engineering repair.

## Sequence
v3 prereg (with the above frozen) -> Loop A implementation + EXECUTION_PREFLIGHT_PASS -> Loop C pre-result audit -> formal run -> Loop C post-result recompute.