# FinQA v2 Formal Rerun V3 Task Card

- Task ID: `finqa-v2-formal-rerun-v3-pending-user-execution-20261010`
- Status: `END_TO_END_PREFLIGHT_PASS_READY_NOT_EXECUTED`
- Scientific execution authorized: `false`
- Scope: frozen formal scorer -> V/D/O -> frozen estimands -> frozen bootstrap only
- Output namespace: `research/finqa_v2_20261010/results_binding_v3_rerun/`

## Certified Preflight

- `END_TO_END_PREFLIGHT_PASS = PASS`
- `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = YES`
- Runtime bindings: `89/89`
- Evaluation traces: `420/420`
- Report groups: `30/30`
- Silent defaults / missing metadata / identity drift / split drift / scientific outputs: all `0`
- Corruption controls: `23/23 FAIL_CLOSED`
- Previous invalid runs: immutable

## Frozen RQ

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Inputs

Use only authorities hash-bound in `docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md` and `research/finqa_v2_20261010/preflight_v1/finqa_v2_end_to_end_preflight_manifest.json`:

- 89 evaluation pairs / 30 report groups;
- binding-v3 runtime contract and trace map;
- unchanged scorer source;
- `FINQA_V2_ANALYSIS_PLAN.md`;
- bootstrap seed `20261017`, 10,000 report-cluster replicates, 95% percentile CI.

## Execution Steps

1. Re-run `formal_experiment_preflight.py` and require exit `0`.
2. Verify all authority hashes and both prior invalid-run receipts.
3. Run the unchanged scorer through binding-v3 on exactly the 89 evaluation pairs.
4. Materialize V/D/O exactly as frozen.
5. Compute only frozen primary/secondary estimands.
6. Run only the frozen 10,000-replicate cluster bootstrap.
7. Preserve all rows and null/adverse cases; no denominator reduction.
8. Hash-bind results and stop for Loop C independent recomputation.

## Forbidden

- Change sample IDs, split, join, scorer, thresholds, metrics or analysis plan.
- Use raw manifest hash as scorer runtime authority.
- Report `op_family` as raw operator identity.
- Add permutation tests or semantic-correctness claims.
- Overwrite either previous invalid run.
- Execute PRM, Stage D or model training.

## Required Outputs

- scorer rows with raw and normalized binding hashes;
- V/D/O rows;
- frozen estimands;
- bootstrap replicate accounting;
- execution receipt and environment/hash logs;
- result report for independent C recomputation.

This task card is generated only. Do not execute until separately approved.
