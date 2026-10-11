# FinQA v2 Measurement-Object Mismatch Autopsy v1

> Status: `ACCEPTED_METHODOLOGICAL_BOUNDARY`
> Evidence class: `NEGATIVE / FAILED_TRANSFER`
> Scientific execution: none in this record
> Formal result class remains `SECOND_FLOW_MIXED`

## Accepted Conclusion

The FinQA v2 run produced `V=89/89`, `D=0/89`, `O=0/89`, but this is not evidence of protocol blindness. The scientific interpretation is:

`MEASUREMENT_OBJECT_MISMATCH`

The visibility scorer observed source/local field changes, while the detection rule consumed downstream result fields that were not causally recomputed for those perturbations.

## Evidence Boundary

- Formal result: `research/finqa_v2_20261010/results_binding_v3_rerun/finqa_v2_formal_results.json`
- Independent recomputation: `docs/experiments/2026-10-10_loop_c_finqa_v2_formal_v3_recompute_audit.md`
- Causal construction audit: `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`
- Existing scorer definitions: `research/finqa_independent_observation_scorer_v2.py`
- Existing paired-artifact construction: `research/finqa_v2_20261010/build_finqa_v2_execution_freeze.py`

## Interpretation

- `V=1` is partly construction-driven because each injected mechanism targets an observed source field.
- `D=0` is not a valid estimate of detection ability when the downstream `res`/`answer` fields are not recomputed from the mutated program semantics.
- The correct conclusion is a failed-transfer/measurement-object boundary, not universal evaluator blindness.
- A future positive transfer claim requires causally aligned measurement objects and downstream execution evidence.

## Claim Boundary

Allowed:

- The run demonstrates a measurement-object mismatch and failed transfer boundary.
- Cross-dataflow validation requires causal alignment between perturbation and measurement objects.

Forbidden:

- FinQA confirms protocol blindness.
- Visibility-detection separation transfers to the FinQA dataflow.
- The result establishes natural-failure localization or semantic process correctness.
