# Task Contract: FinQA v2 Runtime Binding Integration Qualification - Loop A

- Task ID: `finqa-v2-binding-v3-qualification-a-20261010`
- Role: Loop A / GB10 repair and qualification
- Scope: binding/runtime interface only
- Window: zero-endpoint, non-training, zero scientific scoring
- Skills: systematic-debugging, experiment-autopsy, verify-before-done, audit-cycle, offline-eval-playbook, project-conventions

## Frozen Root Cause

`RUNTIME_METADATA_NOT_FORWARDED_TO_BINDING_SEAM`

The runner did not explicitly pass:

- `split_role`
- `stage`
- `cluster_id`
- `report_cluster`

With those fields supplied, the prior audit observed `420/420` evaluation trace rows matching. Do not reopen SOURCE, ID, JOIN, SPLIT, analysis plan or scorer measurement object.

## Objective

Create superseding binding interface v3 and qualify the complete runner -> binding adapter -> scorer-input-construction -> hash/trace-validation path for all frozen evaluation pairs, stopping before scientific scoring.

## Interface V3 Contract

Separate immutable identity from runtime metadata.

Immutable identity fields:

- `source_artifact_id`
- `sample_id`
- `raw_payload_sha256`
- `normalized_payload_sha256`
- `normalization_version`

Runtime metadata fields:

- `split_role`
- `stage`
- `cluster_id`
- `report_cluster`

All four metadata fields must be explicit inputs. Missing, null or empty values must raise a typed fail-closed error. No silent `""` or `None` defaults are allowed anywhere in the runner/adapter seam.

The trace map must distinguish:

- immutable step/artifact identity;
- runtime metadata used for cross-checking only.

## Required Qualification

Run binding-only qualification over:

- 89 frozen evaluation pairs;
- 30 report clusters;
- E 30/10, P 30/10, N 29/10;
- expected evaluation trace rows 420.

Pipeline boundary:

```text
runner
-> binding adapter v3
-> unchanged scorer input construction
-> raw/normalized hash validation
-> trace validation
-> STOP BEFORE score_pair / observation vector / V / D / O
```

Required results:

- `89/89` runtime bindings PASS;
- `420/420` evaluation trace rows MATCH;
- all four metadata fields present and consistent;
- zero silent defaults;
- zero sample identity drift;
- zero group/split drift;
- zero leakage;
- zero V/D/O or scientific output files.

## Integration Tests

Add end-to-end seam tests covering at least:

1. runner forwards all four metadata fields;
2. missing `split_role` raises/fails closed;
3. missing `stage` raises/fails closed;
4. missing `cluster_id` raises/fails closed;
5. missing `report_cluster` raises/fails closed;
6. full raw -> normalized -> runtime binding path;
7. complete 89-pair binding qualification;
8. corruption control;
9. deterministic replay.

Tests must exercise the real runner/adapter interface, not only adapter functions in isolation. Include positive controls proving missing-field guards can fail.

## Required Outputs

Under `research/finqa_v2_20261010/binding_v3/`:

1. `FINQA_V2_RUNTIME_BINDING_INTERFACE_V3.md`
2. `finqa_v2_runtime_binding_interface_v3.json`
3. `finqa_v2_runtime_binding_v3.py`
4. `tests/test_finqa_v2_runtime_binding_v3_integration.py`
5. `finqa_v2_binding_v3_qualification_rows.jsonl`
6. `finqa_v2_binding_v3_qualification_summary.json`
7. exact integration-test and qualification logs
8. `finqa_v2_binding_v3_qualification_receipt.json`

The receipt must hash-bind v3 interface, implementation, tests, qualification rows/summary, frozen inputs and both prior INVALID runs.

## Preserve

- both prior `FORMAL_RUN_INVALID` runs byte-for-byte;
- frozen source/IDs/split/join/scorer/analysis plan;
- scorer semantics and measurement object;
- raw-to-normalized trace map;
- old binding-v2 artifacts.

## Forbidden Actions

- Call `score_pair` or create observation vectors.
- Calculate V/D/O, estimands or bootstrap.
- Modify frozen contracts or prior runs.
- Default missing metadata to empty/null.
- Change sample population, split, join, metrics or thresholds.
- Run a third formal scientific rerun.

## Stop Conditions

- any required metadata is absent/null/empty without a typed error;
- any binding/trace mismatch remains;
- any silent default is found;
- any identity/group/split drift or leakage;
- any V/D/O/scientific output is generated;
- prior invalid-run hashes drift.

## Success Exit

`89/89` bindings pass, `420/420` traces match, integration tests pass including fail-closed controls, zero silent defaults, zero scientific outputs, and the qualification receipt is hash-complete. Stop for Loop C independent review.
