# FinQA v2 Minimal Formal Rerun Task Card

- Task ID: `finqa-v2-minimal-rerun-pending-execution-20261010`
- Status: `SCORER_BINDING_GO_PASS_READY_NOT_EXECUTED`
- Scope: formal scorer -> frozen estimands -> frozen bootstrap only
- Old run: preserved as `FORMAL_RUN_INVALID / SECOND_FLOW_INVALID`
- New execution namespace: `research/finqa_v2_20261010/results_binding_v2_rerun/`

## Frozen RQ

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Inherited Without Re-freeze

- SOURCE_GO, ID_GO, JOIN_GO, SPLIT_GO populations and memberships;
- exact 89 evaluation samples / 30 report clusters;
- frozen scorer and measurement object;
- frozen V/D/O definitions and estimands;
- bootstrap seed `20261017`, 10,000 replicates, 95% percentile CI;
- `PERMUTATION_TEST = NOT_USED`;
- failure handling and claim boundaries.

## New Binding Contract

Use `binding_v2` only:

- `raw_payload_sha256` = provenance hash;
- `normalized_payload_sha256` = scorer-runtime authoritative hash;
- normalization version `finqa_v2_scorer_normalization_20261010_v1`;
- retain the 994-row raw-to-normalized trace map;
- never report `op_family` as raw operator identity.

## Execution Steps

1. Verify old-run, frozen-input and binding-v2 hashes.
2. Verify `SCORER_BINDING_GO = PASS` from the independent Loop C audit.
3. Confirm no prior outputs exist in `results_binding_v2_rerun/`.
4. Run the unchanged scorer through `finqa_v2_scorer_runtime_binding_v2.py` on exactly the 89 evaluation pairs.
5. Stop with `FORMAL_RUN_INVALID` on any missing/invalid record or scorer failure.
6. Materialize frozen V/D/O values.
7. Compute only frozen primary/secondary estimands.
8. Run only the frozen 10,000-replicate cluster bootstrap.
9. Preserve all null/adverse cases and exact denominators.
10. Hash-bind outputs and stop for Loop C independent recomputation.

## Forbidden

- Reopen or change SOURCE/ID/JOIN/SPLIT.
- Change scorer, normalization, metrics, thresholds, analysis plan or population.
- Hide or overwrite the old invalid run.
- Add permutation tests, semantic-correctness claims or hierarchy/localization claims.
- Run PRM/Stage D/model training.

## Required Outputs

- formal sample rows with raw and normalized binding hashes;
- observation vectors;
- frozen estimands;
- bootstrap replicate accounting;
- result report;
- execution receipt;
- environment/test/hash logs.

## Post-Run Requirement

Loop C must independently recompute scorer rows, V/D/O, all frozen estimands and bootstrap intervals before any scientific class is accepted.

This task card is generated only and has not been executed.
