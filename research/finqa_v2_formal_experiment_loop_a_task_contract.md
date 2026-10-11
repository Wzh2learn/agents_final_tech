# Task Contract: FinQA v2 Formal Second-Flow Experiment - Loop A

- Task ID: `finqa-v2-formal-experiment-a-20261010`
- Role: Loop A / GB10 formal execution
- Status: authorized by user after `PREREG_GO = PASS_FINAL`
- Window: zero-endpoint, non-training
- Evidence class: CONFIRMATORY / SECONDARY / NEGATIVE as defined by the frozen analysis plan

## Frozen RQ

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Immutable Inputs

Use only the hash-bound files in:

- `FINQA_V2_FORMAL_EXPERIMENT_TASK_CARD.md`
- `FINQA_V2_ANALYSIS_PLAN.md`
- `finqa_v2_analysis_plan.json`
- `finqa_v2_analysis_preresult_freeze_receipt.json`
- frozen sample/split/paired-artifact/scorer-binding manifests and prior freeze receipt.

Do not change any frozen contract.

## Execution Steps

1. Recompute and verify all frozen hashes.
2. Re-run the 19 focused tests as a technical preflight; do not change code or assertions.
3. Confirm zero formal outputs before execution.
4. Select exactly the 89 evaluation pairs / 30 report clusters from the frozen split.
5. Run the frozen independent scorer on every selected pair.
6. If any scorer call fails or any retained evaluation record is missing/invalid, stop with `FORMAL_RUN_INVALID`.
7. Materialize `V`, `D`, `O` exactly as frozen in `FINQA_V2_ANALYSIS_PLAN.md`.
8. Compute the exact primary and secondary estimands.
9. Compute cluster-bootstrap uncertainty with seed `20261017`, 10,000 replicates, 95% percentile intervals and the frozen failure handling.
10. Record valid/failed replicate counts for every estimand.
11. Do not run permutation tests.
12. Report all adverse/null cases unchanged.
13. Classify using the frozen `SECOND_FLOW_*` rules, but label it `A_RECOMMENDED_CLASS` until Loop D decides after C audit.

## Exact Scoring Scope

- Evaluation samples: `89`.
- Evaluation report clusters: `30`.
- E: `30 samples / 10 groups`.
- P: `30 samples / 10 groups`.
- N: `29 samples / 10 groups`.
- Train and calibration records are not used for primary scoring or analysis.

## Frozen Variables

- `V=1` iff any of the five scorer fields is 1.
- `D=1` iff `step_result_consistency==1 OR answer_consistency==1`.
- `O=1` iff `answer_consistency==1`.

## Required Outputs

1. `research/finqa_v2_20261010/results/finqa_v2_formal_sample_rows.jsonl`
2. `research/finqa_v2_20261010/results/finqa_v2_formal_results.json`
3. `research/finqa_v2_20261010/results/finqa_v2_bootstrap_replicates.jsonl`
4. `research/finqa_v2_20261010/results/FINQA_V2_FORMAL_RESULT_REPORT.md`
5. `research/finqa_v2_20261010/results/finqa_v2_formal_execution_receipt.json`
6. exact test/execution/environment logs and hashes.

The result report must include:

- retained evaluation samples/groups;
- visibility count/rate;
- detection count/rate;
- 2x2 VxD counts/rates;
- `P(D=1|V=1)`;
- `P(D=1|V=0)`;
- per-stage E/P/N profiles;
- O secondary;
- bootstrap estimates and intervals;
- valid/failed replicate counts;
- exclusions/missing/invalid accounting;
- leakage audit;
- negative/null cases;
- allowed and forbidden claims;
- evidence grading.

## Leakage and Integrity Controls

- No result-dependent exclusions, thresholds, metrics or claim changes.
- Stage labels may be used only for the preregistered secondary profile.
- No hierarchy/flat comparison.
- No semantic-correctness claim.
- No harmfulness claim.
- Keep raw manifest hash and normalized scorer payload hash under distinct field names.
- Preserve all 89 evaluation rows even if their observed values are null/adverse; any scorer failure invalidates the run rather than reducing the denominator.

## Stop Conditions

- hash mismatch;
- focused-test failure;
- existing formal output before execution;
- missing/invalid record;
- scorer failure;
- bootstrap implementation deviates from the frozen contract;
- any request or code path that would modify frozen inputs.

## Forbidden Actions

- Redesign split, scorer, join, metrics, thresholds or analysis.
- Run model/API/database calls or training.
- Add permutation tests or metrics.
- Delete adverse cases.
- Modify Paper E or any paper text.
- Start PRM/Stage D work.

## Success Exit

All 89 evaluation pairs score successfully; frozen estimands and bootstrap accounting are materialized; null/adverse cases are preserved; outputs are hash-bound for Loop C fresh-context independent recomputation.
