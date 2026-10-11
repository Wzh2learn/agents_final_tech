# Task Contract: FinQA v2 Binding V2 Minimal Rerun Independent Audit - Loop C

- Task ID: `finqa-v2-minimal-rerun-audit-c-20261010`
- Role: Loop C / GB10 fresh-context independent recomputation
- Window: zero-endpoint, non-training
- Scope: audit the new `results_binding_v2_rerun/` run only

## Objective

Independently recompute or reproduce scorer outputs where possible, all frozen estimands/bootstrap where possible, and determine the correct scientific result class. Do not repair the binding or rerun a replacement experiment.

## Inputs

- frozen sample/split/paired-artifact/scorer-binding manifests;
- `FINQA_V2_ANALYSIS_PLAN.md`;
- binding-v2 contract, mapping, runtime adapter and C binding audit;
- `results_binding_v2_rerun/` files;
- A execution logs.

## Required Checks

1. Verify all frozen/binding/result hashes.
2. Verify population remains 89 evaluation samples / 30 groups.
3. Independently inspect and reproduce `BINDING_TRACE_MISMATCH`.
4. Determine whether any scorer observation vector was returned.
5. Recompute V/D/O and primary estimands if rows exist.
6. Recompute the 10,000-cluster bootstrap if estimands exist.
7. Verify no denominator manipulation or exclusions.
8. Verify no leakage, threshold or analysis-plan changes.
9. Verify old INVALID run remains unchanged.
10. Compare A/C outputs exactly.

## Output

Return the full report in the task log. Required verdict:

- `PASS` if valid scientific outputs exist and reproduce;
- `CONDITIONAL` if valid outputs exist but audit evidence is incomplete;
- `FAIL` if the run is invalid or no scientific estimands exist.

Also report `SECOND_FLOW_POSITIVE/MIXED/NULL/INVALID` recommendation and scientific reason.

## Forbidden Actions

- Repair or modify any binding/contract/result.
- Force scorer success by changing hashes/traces.
- Add metrics/thresholds/exclusions.
- Interpret null failure rows as scientific null results.

## Success Exit

Failure or success is independently reproduced, accounting is verified, and the scientific class is supported without overclaiming.
