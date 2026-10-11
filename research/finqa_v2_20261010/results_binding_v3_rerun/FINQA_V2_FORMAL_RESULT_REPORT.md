# FinQA v2 Formal Second-Flow Result Report

- Task ID: `finqa-v2-formal-rerun-v3-loop-a-20261010`
- Run status: `FORMAL_RUN_COMPLETE_AWAITING_LOOP_C_RECOMPUTATION`
- `A_RECOMMENDED_CLASS`: `SECOND_FLOW_MIXED`
- Final class decision: deferred to Loop D after Loop C audit.
- Window: zero-endpoint, non-training, no permutation test.

## Frozen Research Question

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Retained Evaluation Population

| Stage | Samples | Report clusters |
|---|---:|---:|
| E | 30 | 10 |
| P | 30 | 10 |
| N | 29 | 10 |
| **Total** | **89** | **30** |

Train and calibration were not scored for primary analysis: `81 train`, `45 calibration`.

## Primary Visibility and Detection

| Estimand | Count/rate | Denominator |
|---|---:|---:|
| Visibility | 89 / 1.000000 | 89 |
| Detection | 0 / 0.000000 | 89 |
| P(D=1\|V=1) | 0.000000 | 89 |
| P(D=1\|V=0) | NOT_IDENTIFIABLE | 0 |

### 2x2 V×D

| V | D | Count | Rate |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0.000000 |
| 0 | 1 | 0 | 0.000000 |
| 1 | 0 | 89 | 1.000000 |
| 1 | 1 | 0 | 0.000000 |

## Per-Stage Secondary Profiles

| Stage | V count/rate | D count/rate | V0D0 | V0D1 | V1D0 | V1D1 |
|---|---:|---:|---:|---:|---:|---:|
| E | 30 / 1.000000 | 0 / 0.000000 | 0 | 0 | 30 | 0 |
| P | 30 / 1.000000 | 0 / 0.000000 | 0 | 0 | 30 | 0 |
| N | 29 / 1.000000 | 0 / 0.000000 | 0 | 0 | 29 | 0 |

## Terminal Outcome Secondary

- O count/rate: `0 / 0.000000` with denominator `89`.

## Exclusions, Missing, Invalid and Unevaluable Accounting

| Account | Count |
|---|---:|
| Candidate injections | 216 |
| Retained paired injections | 215 |
| Excluded before split | 1 ambiguous N join |
| Expected evaluation records | 89 |
| Successfully scored | 89 |
| Missing retained records | 0 |
| Invalid retained records | 0 |
| Scorer failures | 0 |
| Unevaluable evaluation records | 0 |
| Preserved evaluation rows | 89 |

No denominator reduction, result-dependent exclusion, threshold change, metric addition or adverse-case deletion occurred.

## Cluster Bootstrap

- Seed: `20261017`
- Replicates: `10000`
- Unit: `report_cluster_id`; all paired samples in each selected cluster are retained.
- Interval: 95% percentile, 2.5th/97.5th percentiles, linear interpolation.
- Point estimates remain sample-weighted.
- `PERMUTATION_TEST = NOT_USED`.

| Estimand | Point | 95% interval | Valid | Failed | Status |
|---|---:|---:|---:|---:|---|
| `detection_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `detection_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `detection_rate_given_visibility_negative` | NOT_IDENTIFIABLE | NOT_IDENTIFIABLE | 0 | 10000 | NOT_IDENTIFIABLE |
| `detection_rate_given_visibility_positive` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `failure_accounting.invalid_record_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `failure_accounting.missing_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `failure_accounting.scorer_failure_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `failure_accounting.unevaluable_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.detection_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.detection_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_count` | 30 | [30.000000, 30.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v0_d0_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v0_d0_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v0_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v0_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v1_d0_count` | 30 | [30.000000, 30.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v1_d0_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v1_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_detection_2x2.v1_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.E.visibility_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.detection_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.detection_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_count` | 29 | [27.000000, 30.000000] | 10000 | 0 | PERCENTILE_95 |
| `stage.N.visibility_detection_2x2.v0_d0_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_detection_2x2.v0_d0_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_detection_2x2.v0_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_detection_2x2.v0_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_detection_2x2.v1_d0_count` | 29 | [27.000000, 30.000000] | 10000 | 0 | PERCENTILE_95 |
| `stage.N.visibility_detection_2x2.v1_d0_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_detection_2x2.v1_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_detection_2x2.v1_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.N.visibility_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.detection_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.detection_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_count` | 30 | [30.000000, 30.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v0_d0_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v0_d0_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v0_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v0_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v1_d0_count` | 30 | [30.000000, 30.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v1_d0_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v1_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_detection_2x2.v1_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `stage.P.visibility_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `terminal_outcome_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `terminal_outcome_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_count` | 89 | [87.000000, 90.000000] | 10000 | 0 | PERCENTILE_95 |
| `visibility_detection_2x2.v0_d0_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_detection_2x2.v0_d0_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_detection_2x2.v0_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_detection_2x2.v0_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_detection_2x2.v1_d0_count` | 89 | [87.000000, 90.000000] | 10000 | 0 | PERCENTILE_95 |
| `visibility_detection_2x2.v1_d0_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_detection_2x2.v1_d1_count` | 0 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_detection_2x2.v1_d1_rate` | 0.000000 | [0.000000, 0.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |
| `visibility_rate` | 1.000000 | [1.000000, 1.000000] | 10000 | 0 | DEGENERATE_EMPIRICAL_INTERVAL |

## Leakage and Integrity Audit

- Frozen hash checks: `60`; mismatches `0`.
- Nested paired-artifact hash checks: `645`; mismatches `0`.
- End-to-end preflight checker: `PASS`.
- Formal outputs before execution: `0`.
- Split/group leakage: `PASS`.
- Assignment fail-closed checks: `PASS`.
- Scorer label blindness/independence: `PASS`.
- Train/calibration rows scored: `0`.
- Binding-v3 binds all 89 raw manifest hashes to distinct normalized scorer payload hashes.
- Stage labels were used only for the preregistered E/P/N secondary profile.

## Negative and Null Cases

| Case | Count |
|---|---:|
| `visibility_without_detection_v1_d0` | 89 |
| `detection_without_visibility_v0_d1` | 0 |
| `null_identity_v0_d0` | 0 |
| `null_identity_v1_d1` | 0 |

All 89 evaluation rows are preserved in `finqa_v2_formal_sample_rows.jsonl`, including null and adverse cases.

## Allowed Claims

- Report frozen V, D and O counts, rates, 2x2 cells, conditional rates and cluster-bootstrap intervals exactly as materialized.
- Describe construct distinction only as `A_RECOMMENDED_CLASS`, pending Loop C audit and Loop D decision.
- Label per-stage profiles, O and uncertainty as SECONDARY; label nonidentity/negative cases as NEGATIVE.

## Forbidden Claims

- Hierarchy beats flat.
- Hierarchy localizes failures.
- The independent scorer is semantically better or establishes semantic correctness.
- FinQA validates natural-failure localization.
- Harmfulness is established.
- Stage E multi-leaf results transfer automatically.

## Evidence Grading

| Evidence | Grade | Boundary |
|---|---|---|
| Overall V/D estimands | CONFIRMATORY | Frozen evaluation role and frozen scorer only |
| Per-stage, O and bootstrap summaries | SECONDARY | Preregistered secondary profiles/uncertainty |
| Adverse and null cases | NEGATIVE | Preserved without deletion or claim redesign |

No hierarchy/flat comparison, semantic-correctness claim, harmfulness claim, permutation test, metric search or threshold change is authorized.

