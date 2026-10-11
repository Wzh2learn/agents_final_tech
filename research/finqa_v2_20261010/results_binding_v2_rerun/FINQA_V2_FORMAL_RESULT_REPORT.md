# FinQA v2 Binding V2 Minimal Rerun Result Report

- Task ID: `finqa-v2-minimal-rerun-pending-execution-20261010`
- Run status: `FORMAL_RUN_INVALID`
- `A_RECOMMENDED_CLASS`: `SECOND_FLOW_INVALID`
- Loop C gate: `SCORER_BINDING_GO = PASS`; this packet stops for fresh independent recomputation.

## Stop Condition

All 89 evaluation records failed closed with `BINDING_TRACE_MISMATCH` before the unchanged scorer returned an observation vector. The frozen contract requires `FORMAL_RUN_INVALID`; estimands and bootstrap resampling were not run.

## Binding V2

- Normalization version: `finqa_v2_scorer_normalization_20261010_v1`.
- Raw-to-normalized trace map: `994` rows and retained.
- `raw_payload_sha256` is the provenance hash.
- `normalized_payload_sha256` is the scorer-runtime authoritative hash.
- `op_family` is not reported as raw operator identity.

## Retained Evaluation Population

| Stage | Samples | Report clusters |
|---|---:|---:|
| E | 30 | 10 |
| P | 30 | 10 |
| N | 29 | 10 |
| **Total** | **89** | **30** |

## Estimands and Bootstrap

- All scientific V/D/O estimands: `NOT_IDENTIFIABLE`.
- Failure-accounting estimands: missing `0`, invalid `0`, scorer failures `89`, unevaluable `89`.
- Bootstrap: planned `10000`, attempted `0`, valid `0`, failed `0`, not attempted `10000`.
- `PERMUTATION_TEST = NOT_USED`.

## Accounting

The exact denominator remains `89`; all 89 rows are preserved with null observation vectors and null V/D/O. No adverse or null case was deleted.

## Claim Boundary

No visibility/detection transfer, semantic-correctness, harmfulness, hierarchy, localization, Stage E transfer or reduced-denominator claim is supported.

