# FinQA Executor Contract Independent Review - Loop C

Task ID: `finqa-executor-contract-c-20261019`

Role: Loop C independent scientific and software review

Status: `REVIEW_REQUESTED`

## Review object

Loop A task `finqa-executor-contract-a-20261019` produced:

`research/finqa_causal_exposure_20261010/executor_contract_v1/`

Its reported status is `EXECUTOR_FEASIBILITY_CONDITIONAL`.

## Evidence whitelist

Read only:

- `research/finqa_causal_exposure_executor_contract_loop_a_task_card.md`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/EXECUTOR_CONTRACT_V1.md`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/executor_contract_v1.json`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/finqa_executor_contract_v1.py`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/tests/test_finqa_executor_contract_v1.py`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/clean_replay_summary.json`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/synthetic_propagation_receipt.json`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/source_code_manifest.json`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/executor_contract_receipt.json`
- `research/finqa_causal_exposure_20261010/executor_contract_v1/LOOP_A_RETURN.md`
- the four files under `executor_contract_v1/official_sources/`
- `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_feasibility.json`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_source_ledger.json`
- `research/finqa_independent_observation_scorer_v2.py`
- `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`

Do not inspect non-whitelisted raw samples or modify any file.

## Required checks

1. Verify official source revision, HTTP receipts and SHA-256 values.
2. Verify the implementation never writes substantive `res` or terminal `answer` fields during mutation fixtures.
3. Verify clean replay counts and denominator: 7,134 terminal `exe_ans` matches, 7,134 unresolved step/display semantics, zero silent exclusions.
4. Verify the two-run deterministic hash and source manifest coverage.
5. Verify synthetic controls are labelled `SYNTHETIC_CONTROL` and are not research samples.
6. Verify no V/D/O, bootstrap, threshold or scientific scorer output was created.
7. Decide whether the listed blockers are real scientific blockers, engineering blockers, or both.
8. Decide whether `EXECUTOR_FEASIBILITY_CONDITIONAL` is the correct disposition, or whether the contract can be qualified with a narrower scope.
9. Challenge the causal graph: does the implementation prove `P/N mutation -> recomputed downstream res -> recomputed terminal answer -> D input`, or only prove terminal replay?

## Output contract

Return exactly one JSON object with no Markdown fences:

{
  "review_identity": "LOOP_C_FINQA_EXECUTOR_CONTRACT_INDEPENDENT_REVIEW_NOT_HUMAN_GOLD",
  "verdict": "ACCEPTED | CONDITIONAL | REJECTED",
  "scope": "...",
  "checks": ["actual command and result"],
  "blocking_findings": [{"id": "B1", "finding": "...", "impact": "...", "required_fix": "..."}],
  "non_blocking_findings": [{"id": "N1", "finding": "..."}],
  "disposition": "QUALIFIED | CONDITIONAL | STOP",
  "causal_graph_judgment": "...",
  "residual_disagreements": ["..."],
  "unverified_or_excluded": ["..."]
}

This is AI independent review only. It is not human semantic gold, blind review, advisor signature or execution authorization.
