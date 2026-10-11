# Task Contract: Causality-Aware Checkpoint Selection MVP DEV Smoke - Loop A

- Task ID: `causal-checkpoint-mvp-smoke-a-20261011`
- Role: Loop A / GB10 feasibility and implementation smoke
- Window: zero-endpoint, zero formal scientific experiment
- Input: old `216 x 12` multi-leaf matrix and frozen design qualification
- Evidence class: `ENGINEERING / DEV_ONLY`

## Frozen Design Authority

Read and obey:

- `research/causal_checkpoint_selection_mvp_20261011/METHOD_DESIGN_QUALIFICATION_V1.md`
- `config/eval_checkpoint_trees.json`
- `research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl`
- `research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl`

Do not change the design contract.

## Smoke Goal

Implement and exercise only the minimal selector/data-contract plumbing on the old matrix.

Required smoke checks:

1. load 216 rows and 12 response fields;
2. construct `SOURCE_LOCAL_RESPONSE` and `DOWNSTREAM_CAUSAL_RESPONSE` from a clearly labelled `DEV_ONLY` overlay;
3. implement hard budgets `B_check`, `B_call`;
4. implement causal/diagnostic greedy with frozen tie rule;
5. implement baselines:
   - all-checkpoints;
   - random-K with fixed seed;
   - manual/default stage-aligned;
   - coverage-only greedy;
   - ours;
   - terminal-only must return `NOT_AVAILABLE`;
6. implement group-disjoint split plumbing;
7. implement fixed nearest-centroid diagnosability plumbing with tie=failure;
8. emit a stable result schema containing selected IDs, budget usage, source-local/downstream counts and all metric fields.

The old matrix has one mechanism per M/R/N stage. Mechanism holdout is therefore `NOT_AVAILABLE` in the smoke; use stage/group split only to test plumbing and label it `DEV_ONLY_PSEUDO_FOLD`.

## Fixed Smoke Budgets

Use both:

- `B_check=4`, `B_call=0`;
- `B_check=8`, `B_call=2`.

These are smoke constraints only.

## Required Outputs

Under `research/causal_checkpoint_selection_mvp_20261011/smoke/`:

1. `causal_checkpoint_selection_mvp.py`
2. `test_causal_checkpoint_selection_mvp.py`
3. `dev_smoke_input_manifest.json`
4. `dev_smoke_result.json`
5. `dev_smoke_test.log`
6. `dev_smoke_receipt.json`

The receipt must state:

`ALGORITHM_SMOKE_DEV_ONLY`, zero scientific claim, zero formal experiment, and the exact input hashes.

## Forbidden

- Materialize a new 96-injection scientific dataset.
- Interpret smoke numbers as H1 evidence.
- Change candidate inventory, mechanisms, RIPR definitions, cost contract, metrics or baselines.
- Train a model, use PSO/RL, or run PRM/Stage D.
- Modify frozen multi-leaf artifacts.

## Stop Conditions

- old matrix shape is not 216x12;
- selector or baseline fails deterministic replay;
- budget enforcement can exceed hard limits;
- tie rule is ambiguous;
- result schema omits required fields;
- smoke accidentally creates formal scientific outputs.

## Success Exit

The DEV_ONLY smoke validates implementation plumbing and leaves `METHOD_DATASET_READY` for independent Loop C scientific audit only after the design contract is checked.
