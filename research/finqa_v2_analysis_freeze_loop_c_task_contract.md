# Task Contract: FinQA v2 Analysis Plan Freeze Audit - Loop C

- Task ID: `finqa-v2-analysis-freeze-c-20261010`
- Role: Loop C / GB10 fresh-context independent audit
- Window: zero-endpoint, non-training, zero formal scorer outputs
- Evidence class: PRIMARY preregistration verification

## Objective

Independently verify that the FinQA v2 analysis plan was frozen before any formal result, is hash-complete, and contains no result-dependent statistical choices.

## Frozen RQ

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Inputs

- `research/finqa_v2_20261010/FINQA_V2_ANALYSIS_PLAN.md`
- `research/finqa_v2_20261010/finqa_v2_analysis_plan.json`
- `research/finqa_v2_20261010/finqa_v2_analysis_preresult_freeze_receipt.json`
- existing frozen manifests, scorer, task card and pre-result receipt.

## Required Independent Checks

1. Recompute all input/output SHA-256 hashes.
2. Verify analysis plan predates any formal scorer/evaluator output.
3. Verify no formal output paths or result files exist.
4. Verify exact estimands match the contract:
   - V count/rate;
   - D count/rate;
   - 2x2 VxD table;
   - `P(D=1|V=1)`;
   - `P(D=1|V=0)`;
   - per-stage E/P/N profiles;
   - O secondary.
5. Verify definitions are deterministic and use only frozen scorer fields.
6. Verify bootstrap uses evaluation report clusters, 10,000 replicates, seed `20261017`, 95% percentile CI.
7. Verify `PERMUTATION_TEST = NOT_USED`.
8. Verify zero-denominator, degenerate-bootstrap and invalid-record handling.
9. Verify no metric, threshold, exclusion or claim rule is result-dependent.
10. Verify the existing sample IDs, split, join and scorer hashes remain unchanged.

## Output

Return the report in the task log. Do not modify any artifact.

Required verdict:

- `PASS` if plan and hash closure are complete with zero outputs;
- `CONDITIONAL` if evidence is incomplete but no defect is found;
- `FAIL` for hash mismatch, existing outputs, result-dependent choices or contract inconsistency.

Also output `PREREG_GO = PASS_FINAL` only for `PASS`.

## Forbidden Actions

- Modify any artifact.
- Run formal scorer outputs or experiments.
- Reopen SOURCE/ID/JOIN/SPLIT/SCORER design.
- Add statistical methods or metrics.

## Success Exit

`PASS`, `PREREG_GO = PASS_FINAL`, and no formal output exists.
