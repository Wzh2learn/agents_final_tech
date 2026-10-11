# FinQA v2 Formal Second-Flow Result Report

- Task ID: `finqa-v2-formal-experiment-a-20261010`
- Run status: `FORMAL_RUN_INVALID`
- `A_RECOMMENDED_CLASS`: `SECOND_FLOW_INVALID`
- Final class status: deferred; Loop C must audit this invalid run.

## Stop Condition

All 89 authorized scorer calls failed closed on `artifact_sha256_mismatch` before any observation vector was returned. The frozen contract requires `FORMAL_RUN_INVALID`; the run stopped before estimands or bootstrap resampling.

## Retained Evaluation Population

| Stage | Samples | Report clusters |
|---|---:|---:|
| E | 30 | 10 |
| P | 30 | 10 |
| N | 29 | 10 |
| **Total** | **89** | **30** |

Train `81` and calibration `45` were not scored.

## Estimands

Visibility, detection, the 2x2 V×D table, both conditional rates, per-stage profiles and O are `NOT_IDENTIFIABLE` because the scorer returned no valid observation vectors. No result-dependent value, threshold, exclusion or metric was substituted.

## Bootstrap

- Seed reserved: `20261017`.
- Planned replicates: `10000`.
- Attempted replicates: `0`.
- Valid replicates: `0`.
- Failed replicates: `0`.
- Status: `NOT_RUN_FORMAL_RUN_INVALID`.
- `PERMUTATION_TEST = NOT_USED`.

## Exclusions, Missing, Invalid and Unevaluable Accounting

| Account | Count |
|---|---:|
| Expected evaluation records | 89 |
| Scorer calls attempted | 89 |
| Scorer successes | 0 |
| Scorer failures | 89 |
| Missing retained records | 0 |
| Invalid retained records | 0 |
| Unevaluable evaluation records | 89 |
| Preserved evaluation rows | 89 |

All 89 rows remain in `finqa_v2_formal_sample_rows.jsonl` with null V/D/O and explicit scorer-failure status. The denominator was not reduced.

## Leakage and Integrity Audit

- Frozen file hashes: PASS, 0 mismatches.
- Nested paired-artifact hashes: PASS, 645 checks.
- Focused preflight: 19 passed.
- Formal output precheck: 0.
- Split/group leakage: PASS.
- Assignment fail-closed checks: PASS.
- Scorer label blindness/independence: PASS.
- Threshold search: NOT PERFORMED.
- Train/calibration scorer calls: 0.
- Raw manifest hash and normalized scorer payload hash are retained under distinct fields.

## Negative and Null Cases

No V/D category is computable. The failure is reported unchanged as NEGATIVE execution evidence; all 89 attempted cases are preserved.

## Allowed Claims

- Report that the formal run is `FORMAL_RUN_INVALID`.
- Report the exact accounting: 89 attempted, 0 successful, 89 failed.
- State that no scientific estimand, interval or result class beyond `SECOND_FLOW_INVALID` is supported.

## Forbidden Claims

- Any hierarchy-beats-flat or hierarchy-localization claim.
- Any semantic-correctness or harmfulness claim.
- Any claim that visibility/detection separation transferred.
- Any natural-failure-localization or automatic Stage E transfer claim.
- Any reduced-denominator, threshold, metric or permutation result.

## Evidence Grading

| Evidence | Grade | Boundary |
|---|---|---|
| Scorer hash-binding failure | NEGATIVE | Execution/integrity only |
| Scientific V/D/O estimands | NOT GRADED | Scorer returned no vectors |

