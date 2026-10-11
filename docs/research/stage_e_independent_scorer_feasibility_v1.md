# Stage E Independent-Scorer Feasibility v1

> Status: `INDEPENDENT_SCORER_PROTOTYPE_PASS_NOT_FROZEN` | Measurement object: paired checkpoint observation reproduction | Existing FinQA semantic scorer remains `CONDITIONAL_WRONG_MEASUREMENT_OBJECT`

## 1. Existing artifact

The repository contains:

- `research/finqa_step_checkpoint_adapter.py`;
- `research/finqa_step_checkpoint_scorer.py`;
- `tests/test_finqa_step_checkpoint_scorer.py`;
- preregistration v2 and historical v1/v2 result records.

`FACT`: the scorer is deterministic, zero-model, zero-connect, fail-closed on unparseable cases, hash-binds its preregistration and corpus/layers, and reports missing/unevaluable denominators explicitly.

## 2. Independence audit

| Requirement | Status | Evidence |
|---|---|---|
| Independent implementation of the target semantics | `PARTIAL` | separate Decimal re-execution implementation, but imports `op_family` and `apply_fault` from the adapter |
| Independent of injection/generator code | `FAIL` | `score_record()` calls `apply_fault()` from the same adapter package |
| Independent of primary Stage E scorer | `PASS` | no :8004 semantic judge or Stage E leaf aggregation is used |
| Same measurement object as Stage E | `FAIL` | scorer evaluates FinQA reasoning-step `op/arg/res`, not header-injection leaf states |
| Stable released sample bridge | `NOT APPLICABLE` | scorer operates on a constructed FinQA step corpus |
| Historical route open | `NO` | V2-3 stop condition fired and prohibits reopening without a new source authorization |

## 3. Historical result boundary

The step-level route measured 1,970 constructed records. Under both preregistered percent readings, interpretation fidelity remained below 0.5:

- `mantissa_direct`: `0.0298` on percent-form steps;
- `mantissa_scaled`: `0.2233` on percent-form steps.

The preregistration required stopping, and that stop condition must remain closed. Detection/localization numbers from this route are not Stage E evidence.

## 4. Feasibility decision

```text
EXISTING_FINQA_SCORER = ENGINEERING_REFERENCE_ONLY
STAGE_E_INDEPENDENT_SCORER = PROTOTYPE_PASS_NOT_FROZEN
EXISTING_SCORER_REASON = WRONG_MEASUREMENT_OBJECT_AND_SHARED_FAULT_GENERATOR
NEW_SCORER_MEASUREMENT_OBJECT = PAIRED_CHECKPOINT_OBSERVATION_REPRODUCTION
SCORER_GO = PROTOTYPE_PASS_NOT_FROZEN
```

The existing scorer can support future FinQA v2 engineering only if a new namespace explicitly reuses it as a non-independent reference implementation. It cannot close the Stage E independent-scorer requirement.

## 5. What a valid Stage E independent scorer would require

1. target the frozen header-injection leaf-state cells or the future v2 raw checkpoint trace;
2. implement scoring independently of the mutation generator and primary scorer;
3. reproduce the same measurement object under a frozen decision predicate;
4. compare cell-level outputs, not just aggregate detection;
5. disclose disagreements and missing evidence;
6. run under a new preregistration and fresh-context audit.

`DECIDE NEXT LOOP: STOP_BRANCH` for the existing FinQA scorer. Do not rerun V2-3 or relabel its outputs.

## 6. Independent observation scorer v2 prototype

`FACT`: `research/finqa_independent_observation_scorer_v2.py` does not import the existing FinQA adapter/scorer or Stage E aggregation. It reads hash-bound paired clean/mutant artifacts and emits a five-feature observation vector:

- `evidence_required_hit`
- `operator_consistency`
- `argument_consistency`
- `step_result_consistency`
- `answer_consistency`

`FACT`: `tests/test_finqa_independent_observation_scorer_v2.py` has five passing tests covering separate feature responses, label blindness, hash binding, missing-field failure and clean-evidence validity.

`VALUE`: this prototype defines the measurement object as **leaf-state/observation reproduction**, not semantic process correctness. `SCORER_GO` remains not frozen until exact FinQA sample IDs, causal resolver contract and pre-result hash receipt are complete.
