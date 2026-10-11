# Task Contract: FinQA v2 Analysis Plan Pre-Result Freeze - Loop A

- Task ID: `finqa-v2-analysis-freeze-a-20261010`
- Role: Loop A / GB10 execution
- Status: authorized for analysis-plan freeze only
- Window: zero-endpoint, non-training, zero formal scorer outputs
- Evidence class: PRIMARY preregistration and hash closure

## Objective

Create and hash-bind the missing FinQA v2 statistical analysis contract before any formal result exists. Do not run the formal experiment.

## Frozen RQ

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Immutable Existing Contract

Do not modify:

- existing freeze packet or receipt;
- sample IDs, retained/excluded records;
- train/calibration/evaluation split;
- causal join or paired artifacts;
- independent scorer or its measurement object;
- task card scientific question or claim boundaries.

## Fixed Analysis Definitions

Population: frozen evaluation role only for primary analysis; 89 paired samples in 30 report clusters. Per-stage evaluation: E 30 samples/10 groups, P 30/10, N 29/10.

Independent scorer fields remain exactly:

`evidence_required_hit`, `operator_consistency`, `argument_consistency`, `step_result_consistency`, `answer_consistency`.

Define binary variables before results:

- `V = 1` iff at least one of the five observation-vector fields equals 1; otherwise `V = 0`.
- `D = 1` iff `step_result_consistency == 1 OR answer_consistency == 1`; otherwise `D = 0`.
- `O = 1` iff `answer_consistency == 1`; otherwise `O = 0`.

These definitions use only the frozen scorer output and do not alter the scorer.

## Exact Estimands

Primary, sample-weighted over retained evaluation pairs:

1. visibility count `N(V=1)` and rate `N(V=1)/N_eval`.
2. detection count `N(D=1)` and rate `N(D=1)/N_eval`.
3. 2x2 table counts and rates for `(V,D) = (0,0),(0,1),(1,0),(1,1)`.
4. `P(D=1 | V=1) = N(V=1,D=1)/N(V=1)`.
5. `P(D=1 | V=0) = N(V=0,D=1)/N(V=0)`.

Secondary already present in the task card:

6. per-stage E/P/N profiles for visibility, detection and the 2x2 table.
7. terminal outcome count/rate `N(O=1)/N_eval`.
8. missing/invalid/unevaluable accounting.

No additional result-oriented metric is authorized.

## Uncertainty Contract

- Unit of resampling: frozen `report_cluster_id` origin/group.
- Primary bootstrap: resample 30 evaluation report clusters with replacement, retaining all paired samples in each selected cluster.
- Per-stage bootstrap: resample the 10 evaluation report clusters within that stage with replacement.
- Replicates: `10,000`.
- Deterministic seed: `20261017`.
- Interval: 95% percentile interval using the 2.5th and 97.5th percentiles of valid replicate estimates.
- Point estimates remain sample-weighted.
- Record `seed`, `replicate_count=10000`, `valid_replicate_count`, `failed_replicate_count`, `cluster_unit`, and `ci_method` for every estimand.

## Permutation Contract

`PERMUTATION_TEST = NOT_USED`

The primary RQ is construct separation estimation, not a permutation-based localization test. Do not add a permutation test after seeing results.

## Failure Handling

- Zero conditional denominator: report `NOT_IDENTIFIABLE`; do not substitute zero.
- Bootstrap replicate with zero denominator for that estimand: mark replicate failed and exclude only from that estimand's percentile calculation.
- All replicates failed: `NOT_IDENTIFIABLE`.
- All valid replicate estimates identical: report the degenerate empirical interval `[x,x]` and label it `DEGENERATE_EMPIRICAL_INTERVAL`; do not change CI method.
- Missing/invalid retained record or scorer failure after split: `FORMAL_RUN_INVALID`; do not silently exclude.
- No threshold changes, metric additions, deletion of adverse cases or result-dependent claim changes.

## Result-Class Rules

- `SECOND_FLOW_POSITIVE`: contract valid, C audit passes, both V and D are nonconstant, and at least one sample has `V=1,D=0`, demonstrating visible-but-undetected cases.
- `SECOND_FLOW_MIXED`: contract valid but transfer is present for only a subset of stages or one construct is degenerate while nonidentity remains informative.
- `SECOND_FLOW_NULL`: contract valid and `V=D` for every evaluation sample, or no informative nonidentity is observed.
- `SECOND_FLOW_INVALID`: contract/leakage/scorer/split/failure-handling violation.

These class rules cannot be changed after outputs.

## Required Outputs

1. `research/finqa_v2_20261010/FINQA_V2_ANALYSIS_PLAN.md`
2. `research/finqa_v2_20261010/finqa_v2_analysis_plan.json`
3. `research/finqa_v2_20261010/finqa_v2_analysis_preresult_freeze_receipt.json`
4. a hash manifest binding:
   - analysis plan;
   - formal task card;
   - sample manifest;
   - split manifest;
   - paired-artifact manifest;
   - scorer binding manifest;
   - scorer source/tests;
   - prior freeze packet/receipt;
   - metric definitions, seed, replicate count and failure handling.

The receipt must record zero formal scorer outputs before and after plan creation.

## Forbidden Actions

- Run formal scorer outputs or experiments.
- Modify existing frozen artifacts.
- Add metrics/tests/thresholds after inspecting results.
- Use any result fields to design the analysis plan.
- Execute PRM or model training.

## Stop Conditions

- any existing freeze hash mismatch;
- any formal output already exists;
- any inability to bind the analysis plan to the frozen population/scorer;
- any request to change the RQ or measurement object.

## Success Exit

`FINQA_V2_ANALYSIS_PLAN` and its complete hash receipt exist, with zero formal outputs, ready for Loop C fresh-context freeze audit.
