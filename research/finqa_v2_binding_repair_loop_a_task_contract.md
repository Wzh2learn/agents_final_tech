# Task Contract: FinQA v2 Raw/Normalized Binding Diagnosis and Minimal Repair - Loop A

- Task ID: `finqa-v2-binding-repair-a-20261010`
- Role: Loop A / GB10 technical diagnosis and repair
- Window: zero-endpoint, non-training
- Scope: new `binding_v2` namespace only
- Skills: systematic-debugging, experiment-autopsy, audit-cycle, verify-before-done, offline-eval-playbook, self-eval-bias, project-conventions, scientific-toolkit-skill

## Objective

Determine whether the 89/89 `artifact_sha256_mismatch` failure is only a deterministic serialization/normalization hash-domain mismatch, then create a superseding artifact-binding contract without changing the old invalid run or reopening established gates.

## Frozen RQ

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Baseline to Preserve

- Keep the complete old `FORMAL_RUN_INVALID` run unchanged.
- Keep SOURCE/ID/JOIN/SPLIT population and memberships unchanged.
- Do not modify the scorer, old manifests, analysis plan, task card, sample IDs or result files.
- Do not normalize or rewrite stored paired artifacts.

## Root-Cause Hypothesis

The raw manifest binds `sha256(canonical_json(raw artifact))`, while `score_pair` validates `sha256(canonical_json(normalized bound_payload))`. The scorer normalizes step `op` to `op_family`, sorts evidence IDs and canonicalizes step fields before hashing. If this fully explains the mismatch without content/identity drift, it is an engineering hash-domain contract bug.

## Required Diagnosis

For all frozen pairs and steps, independently compute and record:

1. raw payload hash;
2. normalized scorer payload hash;
3. normalization function and version;
4. source artifact ID and sample ID;
5. raw step identity and normalized step identity;
6. step index and stable trace key.

Verify:

- `op -> op_family` is deterministic and replayable;
- all expected steps map exactly once;
- normalization does not change sample identity;
- normalization does not change task semantics or stored raw data;
- normalization does not change split/group membership;
- normalization does not change scorer measurement meaning beyond the already-frozen scorer normalization;
- labels, outcomes, stage labels and result fields are absent from normalization/hash input;
- raw and normalized payloads are traceable one-to-one by source artifact + step index;
- any lossy `op` collapse is documented; do not call it bijective unless true.

Required decision flags:

- `DETERMINISTIC`
- `SEMANTICS_PRESERVING`
- `BIJECTIVE_OR_TRACEABLE`
- `NO_LEAKAGE`
- `NO_SAMPLE_ID_CHANGE`

If any flag is false or unverified, stop with `BINDING_REPAIR_NOT_AUTHORIZED`.

## Minimal Repair Contract

Create a superseding contract under:

`research/finqa_v2_20261010/binding_v2/`

The contract must state:

- `raw_payload_sha256` = provenance hash over raw stored payload;
- `normalized_payload_sha256` = scorer-runtime authoritative hash;
- `normalization_function = finqa_independent_observation_scorer_v2.py::_normalized_steps + artifact_hash`;
- frozen normalization version;
- source artifact ID linkage;
- raw-to-normalized trace keys;
- fail-closed behavior for any missing/untraceable step;
- old run remains `SECOND_FLOW_INVALID` and is not superseded scientifically.

Implement a minimal runtime binding adapter that supplies the normalized hash to the unchanged scorer while retaining the raw hash separately. Do not alter the scorer.

## Required Tests

Use synthetic fixtures only until Loop C authorizes frozen-pair scoring:

- deterministic normalization replay;
- raw hash preservation;
- normalized hash equality with scorer expectation;
- exact 215-pair / 994-step mapping accounting;
- sample ID and group membership invariance;
- no label/outcome/stage/result fields in hash inputs;
- positive-control corruption must fail closed;
- missing trace key must fail closed;
- old invalid-run hashes remain unchanged.

## Required Outputs

1. `FINQA_V2_ARTIFACT_BINDING_CONTRACT_V2.md`
2. `finqa_v2_artifact_binding_contract_v2.json`
3. `finqa_v2_raw_normalized_mapping.jsonl`
4. `finqa_v2_normalization_audit.json`
5. `finqa_v2_scorer_runtime_binding_v2.py`
6. `tests/test_finqa_v2_scorer_runtime_binding_v2.py`
7. exact test logs
8. `finqa_v2_binding_v2_receipt.json` with input/output hashes and decision flags

## Forbidden Actions

- Modify old frozen artifacts or invalid-run results.
- Reopen SOURCE_GO, ID_GO, JOIN_GO or SPLIT_GO.
- Change metrics, thresholds, split, joins, sample population or analysis plan.
- Score frozen pairs as a new formal experiment.
- Hide or remove the old failure.
- Claim normalization is bijective if it is only traceable.

## Stop Conditions

- normalization is nondeterministic;
- semantics/identity/leakage checks fail;
- raw-to-normalized trace is incomplete;
- repair would require modifying scorer or frozen payloads;
- positive-control corruption does not fail closed;
- old artifacts drift.

## Success Exit

Root cause is confirmed as hash-domain mismatch; all five decision flags pass; binding-v2 contract and tests are hash-complete; old invalid run remains unchanged. Stop for Loop C independent audit before any formal rerun.
