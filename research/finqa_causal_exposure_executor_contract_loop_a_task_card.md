# FinQA Executor Contract Qualification - Loop A

Task ID: `finqa-executor-contract-a-20261019`

Role: Loop A / GB10 offline implementation and qualification

Mode: `research-driven-design` plus `inquiry-methods` first-principles / minimal-experiment boundary

Status: `DRAFT_EXECUTION_AUTHORIZED_OFFLINE_ONLY`

## Decision supported

Can the existing FinQA causal-exposure proposal obtain a deterministic, independently reviewable executor contract so that a future P/N mutation can be proven to propagate through:

`injection target -> downstream computation -> res -> answer -> D input`

This task does not execute the causal-exposure scientific experiment and does not estimate V, D or O.

## Inputs

Read-only project inputs:

- `research/loop_a_finqa_causal_exposure_design_contract.md`
- `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_design.json`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_feasibility.json`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_source_ledger.json`
- `research/finqa_independent_observation_scorer_v2.py`
- `research/finqa_step_checkpoint_scorer.py`
- `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`
- `docs/datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md`
- frozen staged sources at `/home/testuser/wzh/phase1a_staging_20260925/finqa/train.json` and `dev.json`

Official source code to inspect, pinned exactly to revision `0f16e2867befa6840783e58be38c9efb9229d742`:

- `https://raw.githubusercontent.com/czyssrs/FinQA/0f16e2867befa6840783e58be38c9efb9229d742/code/generator/finqa_utils.py`
- `https://raw.githubusercontent.com/czyssrs/FinQA/0f16e2867befa6840783e58be38c9efb9229d742/code/generator/utils.py`
- `https://raw.githubusercontent.com/czyssrs/FinQA/0f16e2867befa6840783e58be38c9efb9229d742/code/generator/operation_list.txt`
- `https://raw.githubusercontent.com/czyssrs/FinQA/0f16e2867befa6840783e58be38c9efb9229d742/code/evaluate/evaluate.py`

Do not silently substitute a different revision. Record response status, SHA-256 and byte count for every fetched source file.

## Required work

### 1. Executor semantics

Extract and document, without guessing:

- raw operator token parsing and normalized family/variant handling;
- numeric, percent, constant, `#k`, `none` and free-text argument grammar;
- dependency resolution for prior step references;
- arithmetic, division-by-zero, comparison ties, overflow/non-finite behavior;
- rounding, precision, percent rendering and exact result serialization;
- terminal answer derivation for numeric, boolean and other result forms;
- explicit exclusion codes for every unsupported or ambiguous case.

If the official source is incomplete for any rule, mark that rule `UNVERIFIED` and fail closed. Do not repair semantics from the existing reconstructed scorer unless the official source proves the same rule.

### 2. Deterministic executor

Create a new isolated implementation under:

`research/finqa_causal_exposure_20261010/executor_contract_v1/`

The implementation must:

- read a program and source context without importing the old fault adapter or scorer;
- recompute every dependent `res` and terminal answer from the mutated program;
- permit mutation stages to write only legal P/N target fields;
- deny manual writes to substantive `res` and terminal `answer` fields;
- produce stable canonical serialization and deterministic two-run hashes;
- return typed fail-closed errors for unsupported operations or unresolved arguments.

### 3. Clean replay

Run exact clean replay over the frozen 7,134-record FinQA train/dev staging set:

- compare every generated step `res` and terminal answer with gold;
- run twice and compare byte-identical serialized outputs;
- report valid, mismatch, unsupported, unresolved and non-deterministic counts by frozen code;
- do not exclude records silently or shrink the denominator;
- do not generate V/D/O or scientific estimand files.

### 4. Synthetic propagation qualification

Use only clearly labelled synthetic fixtures:

- unchanged sham;
- visible upstream/evidence-only control;
- direct result/answer control;
- legal P operator mutation;
- legal N argument mutation.

For P/N fixtures, prove that mutation writes only the target field and the executor recomputes downstream `res` and terminal answer. These fixtures are engineering qualification only and must never enter a research population.

### 5. Required outputs

All under `research/finqa_causal_exposure_20261010/executor_contract_v1/`:

1. `EXECUTOR_CONTRACT_V1.md`
2. `executor_contract_v1.json`
3. `finqa_executor_contract_v1.py`
4. `tests/test_finqa_executor_contract_v1.py`
5. `clean_replay_summary.json`
6. `synthetic_propagation_receipt.json`
7. `source_code_manifest.json`
8. `LOOP_A_RETURN.md`
9. `executor_contract_receipt.json`

The receipt must hash-bind the official source files, frozen FinQA inputs, implementation, tests and summaries. Preserve old artifacts byte-for-byte.

## Verification contract

Before declaring qualification, run and record:

- `python -m py_compile` on implementation and tests;
- focused pytest for executor contract;
- exact clean replay command and full counts;
- two-run determinism check;
- a source manifest hash comparison;
- a negative test proving manual `res`/`answer` edits are rejected;
- a negative test proving unsupported operations fail closed.

Use bash/evidence-first verification. Do not claim PASS from code inspection alone.

## Hard boundaries

- No model, judge, API, database, training or production-service calls.
- No V/D/O, bootstrap, threshold search or scientific scorer outputs.
- No edits to frozen FinQA results, Paper E, old runner, old scorer or old raw files.
- No commit or push.
- No new data source beyond the pinned official source code and the already staged FinQA JSON files.
- No hand-editing substantive `res` or `answer`.
- If official semantics or clean replay remain incomplete, return `EXECUTOR_FEASIBILITY_CONDITIONAL` with exact blocker codes; do not improvise.

## Exit states

- `EXECUTOR_CONTRACT_QUALIFIED`: official semantics are explicit, all clean replays are exact and deterministic, and synthetic P/N propagation is proven without manual result editing.
- `EXECUTOR_FEASIBILITY_CONDITIONAL`: one or more semantic/replay/contract blockers remain; list them precisely and stop.
- `TECHNICAL_INVALID`: source identity, frozen input or provenance checks fail; preserve evidence and stop.

This is Loop A execution only. Loop C will independently audit the implementation and qualification before any future causal-exposure execution is proposed.
