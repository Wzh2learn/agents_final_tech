# FinQA v2 Runtime Binding Interface V3

**Status:** Superseding binding-only qualification interface; stop for Loop C independent review after qualification.  
**Task:** `finqa-v2-binding-v3-qualification-a-20261010`  
**Scope:** Binding/runtime interface only; zero-endpoint, non-training, zero scientific scoring.  
**Frozen root cause:** `RUNTIME_METADATA_NOT_FORWARDED_TO_BINDING_SEAM`.

The binding-v2 runner did not explicitly forward `split_role`, `stage`, `cluster_id`, and `report_cluster`. The adapter therefore observed empty runtime metadata and failed its frozen trace cross-check on all 89 attempts. V3 supersedes that interface while preserving every frozen source, ID, join, split, population, scorer semantic, measurement object, analysis plan, binding-v2 artifact, and both prior `FORMAL_RUN_INVALID` runs.

## Skill loading

Red-line prerequisite: `graph-loop-rules`. Task skills: `systematic-debugging`, `experiment-autopsy`, `verify-before-done`, `audit-cycle`, and `offline-eval-playbook`. Project conventions are loaded from the repository `AGENTS.md`, `memory/`, `docs/INDEX.md`, and `docs/SKILL_ROUTING.md` because no separate `project-conventions` skill exists in this repository.

## Immutable identity

The immutable identity is serialized as one explicit block and is never replaced by runtime metadata:

1. `source_artifact_id`
2. `sample_id`
3. `raw_payload_sha256`
4. `normalized_payload_sha256`
5. `normalization_version`

The five fields are cross-bound to the frozen sample, paired-artifact, scorer-binding, split, and raw-to-normalized mapping records. A missing, null, empty, non-string, or inconsistent value raises a typed fail-closed error.

## Runtime metadata

The four runtime metadata fields are explicit, keyword-only runner inputs:

- `split_role`
- `stage`
- `cluster_id`
- `report_cluster`

No function in the runner/adapter seam defaults any of these fields to `""`, `None`, or another sentinel value. Python's internal required-field sentinel is rejected before any hash or trace work:

| Condition | Exception type | Error code |
|---|---|---|
| Field absent | `MissingRequiredFieldError` | `RUNTIME_METADATA_MISSING` |
| Field null | `RuntimeMetadataError` | `RUNTIME_METADATA_NULL` |
| Empty or whitespace-only string | `RuntimeMetadataError` | `RUNTIME_METADATA_EMPTY` |
| Non-string value | `RuntimeMetadataError` | `RUNTIME_METADATA_INVALID_TYPE` |

Runtime metadata is used only for cross-checking frozen split/group/trace context. It is not an immutable artifact identifier and is not inserted into the scorer payload.

## Pipeline boundary

```text
frozen formal runner load_evaluation_rows
-> BindingV3Runner
-> explicit immutable identity + explicit runtime metadata
-> RuntimeBindingV3 adapter
-> unchanged scorer input construction
-> raw hash validation
-> normalized hash validation
-> exact 420-row evaluation trace validation
-> STOP BEFORE scientific scoring / observation vector / V / D / O
```

The adapter imports only unchanged normalization helpers (`_normalized_steps`, `artifact_hash`, and canonical JSON). It does not import or invoke the scientific scoring entrypoint. The constructed scorer input contains the three raw payload fields plus `artifact_sha256 = normalized_payload_sha256`, but execution stops at `CONSTRUCTED_NOT_EXECUTED`.

## Trace-map classification

The frozen v2 mapping remains byte-for-byte unchanged. V3 interprets each row in two disjoint categories:

### Immutable step/artifact identity

`source_artifact_id`, `sample_id`, `raw_payload_sha256`, `normalized_payload_sha256`, `normalization_version`, `trace_key`, `step_side`, `step_index`, raw and normalized step identities, and raw and normalized step hashes.

### Runtime metadata cross-check only

`split_role`, `stage`, `cluster_id`, and `report_cluster`.

Each v3 qualification row contains the two classifications separately under `trace_map`. Exact row equality against the frozen mapping is mandatory. The lossy `op -> op_family` normalization remains traceable and is never treated as bijective.

## Qualification contract

The complete frozen evaluation population must satisfy:

- `89/89` runtime bindings PASS;
- `420/420` evaluation trace rows MATCH;
- 30 report clusters;
- stage bindings `E=30`, `P=30`, `N=29`;
- stage report clusters `E=10`, `P=10`, `N=10`;
- four metadata fields present and consistent on every binding;
- zero silent defaults;
- zero sample identity drift;
- zero group drift;
- zero split drift;
- zero leakage;
- zero endpoint, model, training, scientific-scoring, observation-vector, V/D/O, estimand, or bootstrap outputs in the new `binding_v3` namespace.

The qualification must exercise these controls:

1. real runner forwards all four metadata fields;
2. missing `split_role` fails closed;
3. missing `stage` fails closed;
4. missing `cluster_id` fails closed;
5. missing `report_cluster` fails closed;
6. full raw -> normalized -> runtime binding path;
7. complete 89-pair qualification;
8. corruption control;
9. deterministic replay;
10. scorer entrypoint guard and zero-scientific-output control;
11. byte-identical prior invalid-run controls.

## Required outputs

- `FINQA_V2_RUNTIME_BINDING_INTERFACE_V3.md`
- `finqa_v2_runtime_binding_interface_v3.json`
- `finqa_v2_runtime_binding_v3.py`
- `tests/test_finqa_v2_runtime_binding_v3_integration.py`
- `finqa_v2_binding_v3_qualification_rows.jsonl`
- `finqa_v2_binding_v3_qualification_summary.json`
- `finqa_v2_binding_v3_integration_tests.log`
- `finqa_v2_binding_v3_qualification.log`
- `finqa_v2_binding_v3_qualification_receipt.json`

The receipt hash-binds all required outputs, frozen inputs, and every substantive file in both prior invalid-run directories. The receipt excludes only its own `self_sha256` field under the documented canonical-JSON receipt hash rule.

## Stop conditions

Stop immediately if any metadata is absent/null/empty without a typed error; any binding or trace row mismatches; any silent default exists; sample/group/split drift or leakage exists; any new scientific output exists; either prior invalid-run manifest drifts; or the boundary reaches scientific scoring.

## Success exit

`89/89` bindings pass, `420/420` traces match, all integration controls pass including four positive missing-field controls, all zero counters remain zero, both prior invalid runs remain byte-identical, and the qualification receipt is hash-complete. Stop for Loop C independent review; do not run a third formal scientific experiment.
