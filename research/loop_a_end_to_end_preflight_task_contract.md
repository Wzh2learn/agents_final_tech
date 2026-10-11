# Task Contract: Materialize End-to-End Preflight Certificate - Loop A

- Task ID: `finqa-v2-end-to-end-preflight-a-20261010`
- Role: Loop A / GB10 repair and materialization
- Scope: existing preflight checker and FinQA formal-run authority set only
- Window: zero-endpoint, non-training, zero scientific output

## Sole Objective

Close `END_TO_END_PREFLIGHT_PASS_UNMATERIALIZED_AND_NON_CERTIFIABLE` and produce an executable certificate candidate. Do not execute formal FinQA scoring or extend the governance framework.

## Frozen Inputs

Do not modify:

- FinQA source/IDs/split/join/scorer semantics;
- `FINQA_V2_ANALYSIS_PLAN.md`;
- frozen sample/split/scorer-binding manifests;
- binding-v3 runtime contract;
- prior invalid-run results or receipts.

## Required Checker Repairs

`scripts/graph/formal_experiment_preflight.py` must fail closed on:

1. empty `hash_bindings`;
2. empty `scientific_output_paths`;
3. empty `previous_invalid_runs`;
4. empty/incomplete `expected_population`;
5. empty `expected_qualification`;
6. missing required authority artifact;
7. zero checked bindings;
8. required metadata fallback patterns:
   - `record.get(field, default)`;
   - keyword `default=`;
   - `record.get(field) or fallback`;
   - `setdefault(field, fallback)`;
   - missing/null/empty required fields.
9. missing runtime metadata policy;
10. any existing scientific output path.

Add focused corruption tests for every class. The checker must not interpret an empty result set as PASS.

## Authority Map Materialization

Update only the FinQA authority entries in `docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md` with exact:

- path;
- SHA-256;
- status;
- superseded/superseded-by;
- owner.

Required authorities:

1. analysis plan;
2. frozen sample manifest;
3. split manifest;
4. scorer source;
5. scorer binding manifest;
6. binding-v3 runtime contract;
7. current historical task card;
8. bootstrap seed/replicate plan;
9. previous invalid-run receipts.

Use the existing `binding_v2/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md` path unless a new execution task card is explicitly created. Do not invent a new authority.

## Zero-Scientific-Output Qualification

Create a preflight manifest and receipt under:

`research/finqa_v2_20261010/preflight_v1/`

The qualification must execute:

```text
authority resolution
-> sample/split loading
-> runner payload construction
-> binding_v3
-> adapter
-> scorer input construction
-> hash/trace validation
-> analysis-plan resolution
-> STOP BEFORE V/D/O
```

Required counts:

- runtime bindings: `89/89`;
- evaluation trace rows: `420/420`;
- report groups: `30/30`;
- missing metadata: `0`;
- silent defaults: `0`;
- empty-set bypasses: `0`;
- identity drift: `0`;
- split drift: `0`;
- scientific outputs: `0`;
- previous invalid-run drift: `0`.

## Outputs

1. updated preflight checker;
2. focused corruption tests and exact logs;
3. updated FinQA rows in the authority map;
4. `preflight_v1/finqa_v2_end_to_end_preflight_manifest.json`;
5. `preflight_v1/finqa_v2_end_to_end_preflight_certificate.json`;
6. `preflight_v1/finqa_v2_end_to_end_preflight_receipt.json`;
7. exact command/environment/hash logs;
8. status `END_TO_END_PREFLIGHT_PASS_CANDIDATE_PENDING_LOOP_C`.

## Forbidden

- Formal scorer execution or V/D/O generation.
- Change scientific design, metrics, thresholds, split, join or scorer.
- Add new PASS levels or governance frameworks.
- Modify prior invalid runs.
- Run PRM/Stage D/model training.
- Claim `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN` before Loop C certification.

## Stop Conditions

- any checker bypass remains;
- authority path/hash missing;
- any count differs from 89/420/30;
- any scientific output is created;
- previous run drift;
- inability to stop before V/D/O.

## Success Exit

Checker corruption controls fail closed, authority map is complete for the listed set, the full preflight manifest/certificate/receipt is materialized, and the candidate is handed to Loop C.
