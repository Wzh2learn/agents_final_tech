# Task Contract: FinQA v2 Formal Result Independent Audit - Loop C

- Task ID: `finqa-v2-formal-audit-c-20261010`
- Role: Loop C / GB10 fresh-context independent audit
- Window: zero-endpoint, non-training
- Evidence class: NEGATIVE execution/integrity audit

## Objective

Independently audit the FinQA v2 formal run and determine whether `FORMAL_RUN_INVALID / SECOND_FLOW_INVALID` is correct. Do not repair or rerun the experiment.

## Inputs

- frozen analysis plan and pre-result receipt;
- frozen sample/split/paired-artifact/scorer-binding manifests;
- frozen independent scorer source;
- `research/finqa_v2_20261010/results/finqa_v2_formal_sample_rows.jsonl`;
- `finqa_v2_formal_results.json`;
- `finqa_v2_formal_execution_receipt.json`;
- `FINQA_V2_FORMAL_RESULT_REPORT.md`;
- A execution logs.

## Required Independent Checks

1. Verify all frozen and result hashes.
2. Independently count expected/attempted/success/failed/unevaluable evaluation rows.
3. Verify all 89 rows and 30 groups remain present with no denominator reduction.
4. Independently invoke the frozen scorer on representative and/or all exact paired records.
5. Reproduce the `artifact_sha256_mismatch` failure without changing inputs.
6. Determine the exact hash-contract mismatch:
   - raw stored-pair manifest binding;
   - normalized scorer payload self-hash;
   - value passed by the formal runner.
7. Verify no V/D/O vector or scientific estimand was produced.
8. Verify bootstrap was not run and permutation remained `NOT_USED`.
9. Verify split/group integrity and leakage controls remain intact.
10. Verify no threshold, metric, exclusion or claim rule changed after failure.
11. Audit the allowed/forbidden claim boundary.

## Output

Return the full report in the task log. Do not modify any artifact.

Required verdict on the scientific run:

- `PASS` only if a valid formal scientific result exists;
- `CONDITIONAL` if scientific estimands are valid but some audit evidence is incomplete;
- `FAIL` if the run is invalid or no scientific estimand exists.

Also state the scientific reason and whether `SECOND_FLOW_INVALID` is the correct final class.

## Forbidden Actions

- Modify scorer, manifests, hashes, freeze packet or results.
- Normalize/hash-wire inputs to make scoring succeed.
- Rerun as a replacement formal experiment.
- Add metrics, thresholds or exclusions.
- Interpret V/D separation from null/failure rows.

## Stop Conditions

- Any attempt to repair the frozen binding.
- Any successful scoring that changes A's failure population.
- Any hash or count mismatch not present in A's accounting.

## Success Exit

The mismatch is independently reproduced and attributed, accounting is verified, and the final scientific class is supported without overclaiming.
