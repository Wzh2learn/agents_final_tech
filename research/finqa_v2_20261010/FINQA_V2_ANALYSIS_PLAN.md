# FinQA v2 Pre-Result Statistical Analysis Plan

- Task ID: `finqa-v2-analysis-freeze-a-20261010`
- Evidence class: `PRIMARY_PREREGISTRATION_AND_HASH_CLOSURE`
- Window: zero-endpoint, non-training, zero formal scorer outputs
- Status: frozen for independent Loop C audit; not an execution authorization
- Formal scorer outputs before plan creation: `0`

## Frozen Research Question

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

This plan does not change the task-card claim boundaries, the independent scorer, its measurement object, the retained population, the split, the causal join, or any frozen artifact.

## Population and Unit

The primary population is the frozen evaluation role only: 89 retained paired samples in 30 report-cluster groups. The frozen per-stage evaluation populations are:

| Stage | Samples | Report clusters |
|---|---:|---:|
| E | 30 | 10 |
| P | 30 | 10 |
| N | 29 | 10 |

All point estimates are sample-weighted. The resampling unit is the frozen report-cluster origin/group (`report_cluster_id`), represented in the frozen split by its canonical group and in the sample identity by the stage-scoped cluster. Groups are never recomputed from results.

## Frozen Scorer Fields

The analysis uses only these independent-scorer fields, exactly as frozen:

1. `evidence_required_hit`
2. `operator_consistency`
3. `argument_consistency`
4. `step_result_consistency`
5. `answer_consistency`

The scorer measurement object remains `paired_checkpoint_observation_reproduction`.

## Binary Variables

The following variables are defined before any formal scorer output exists:

- `V = 1` iff at least one of the five observation-vector fields equals `1`; otherwise `V = 0`.
- `D = 1` iff `step_result_consistency == 1 OR answer_consistency == 1`; otherwise `D = 0`.
- `O = 1` iff `answer_consistency == 1`; otherwise `O = 0`.

These definitions consume frozen scorer output only. They do not alter, calibrate, threshold, or re-implement the scorer.

## Exact Estimands

### Primary evaluation estimands

For `N_eval = 89`:

1. Visibility count and rate: `N(V=1)` and `N(V=1)/N_eval`.
2. Detection count and rate: `N(D=1)` and `N(D=1)/N_eval`.
3. The 2x2 `(V,D)` counts and cell rates for `(0,0)`, `(0,1)`, `(1,0)`, and `(1,1)`, where each cell rate is `N(cell)/N_eval`.
4. `P(D=1 | V=1) = N(V=1,D=1)/N(V=1)`.
5. `P(D=1 | V=0) = N(V=0,D=1)/N(V=0)`.

### Secondary evaluation estimands

6. Per-stage E/P/N profiles for visibility count/rate, detection count/rate, and the four-cell 2x2 table count/rate. Per-stage sample denominators are 30, 30, and 29 respectively.
7. Terminal outcome count and rate: `N(O=1)` and `N(O=1)/N_eval`.
8. Missing, invalid, scorer-failure, and unevaluable accounting for the 89 expected evaluation samples. These are reported as explicit counts and reconciled against the frozen population; no surviving-row denominator may replace `N_eval`.

No additional result-oriented metric, subgroup, threshold search, localization statistic, hierarchy comparison, harmfulness measure, or semantic-correctness measure is authorized.

## Uncertainty Contract

- Primary bootstrap unit: the 30 frozen evaluation report clusters, sampled with replacement.
- Per-stage bootstrap unit: the 10 frozen evaluation report clusters within that stage, sampled with replacement.
- Cluster sampling retains all paired samples in every selected cluster. If a cluster is selected multiple times, its complete paired-sample set enters the replicate the same number of times.
- Replicates: `10000`.
- Deterministic seed: `20261017`.
- Interval: `95%` percentile interval using the `2.5`th and `97.5`th percentiles of valid replicate estimates.
- Point estimates remain sample-weighted and are not replaced by bootstrap means.
- For every estimand, record `seed`, `replicate_count=10000`, `valid_replicate_count`, `failed_replicate_count`, `cluster_unit`, and `ci_method`.

The percentile interval method remains fixed for all estimands, including counts, rates, table cells, conditional rates, terminal outcome, and explicit failure accounting.

## Permutation Contract

`PERMUTATION_TEST = NOT_USED`

The primary research question is construct-separation estimation, not a permutation-based localization test. A permutation test must not be added after results exist.

## Failure Handling

- A zero conditional denominator is reported as `NOT_IDENTIFIABLE`; zero is not substituted.
- A bootstrap replicate with a zero denominator for one estimand is marked failed and excluded only from that estimand's percentile calculation.
- If all replicates fail for an estimand, report `NOT_IDENTIFIABLE`.
- If all valid replicate estimates for an estimand are identical, report `[x,x]`, label it `DEGENERATE_EMPIRICAL_INTERVAL`, and retain the same percentile CI method.
- A missing or invalid retained record, or a scorer failure after split, makes the formal run `FORMAL_RUN_INVALID`. Cases are not silently excluded and no denominator is reduced.
- Thresholds are not changed; metrics and tests are not added; adverse cases are not deleted; claim language does not change as a function of results.

## Result-Class Rules

- `SECOND_FLOW_POSITIVE`: contract valid, C audit passes, both `V` and `D` are nonconstant, and at least one sample has `V=1,D=0`.
- `SECOND_FLOW_MIXED`: contract valid but transfer is present for only a subset of stages, or one construct is degenerate while nonidentity remains informative.
- `SECOND_FLOW_NULL`: contract valid and `V=D` for every evaluation sample, or no informative nonidentity is observed.
- `SECOND_FLOW_INVALID`: contract, leakage, scorer, split, or failure-handling violation.

These classes are applied exactly as written and cannot be changed after outputs.

## Forbidden Actions

- Run formal scorer outputs or experiments.
- Modify existing freeze packets, receipts, manifests, sample IDs, exclusions, split roles, joins, paired artifacts, scorer code, tests, or measurement object.
- Add metrics, tests, thresholds, permutation tests, or result-dependent claims after inspecting results.
- Use result fields to design or revise this plan.
- Execute PRM, model training, model calls, endpoint calls, or probes.
- Make hierarchy-beats-flat, hierarchy-localization, semantic-correctness, natural-failure-localization, or automatic Stage E transfer claims.

## Pre-Result Closure

This plan was created from the frozen task contract and manifests only. Existing freeze hashes were checked before creation, and formal scorer outputs were confirmed to be zero before creation. The companion machine-readable plan, hash manifest, and freeze receipt bind the exact files and frozen analysis definitions for fresh-context Loop C audit.
