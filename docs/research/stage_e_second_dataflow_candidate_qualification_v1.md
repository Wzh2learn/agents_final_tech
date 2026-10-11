# Stage E Second-Dataflow Candidate Qualification v1

> Status: `BEST_CANDIDATE_SELECTED_DESIGN_ONLY` | Scope: existing-source qualification only; no download, adapter execution or second-flow experiment

## 1. Selection criteria

A second dataflow is eligible only if it provides:

1. a pipeline different from the frozen table-header mapping flow;
2. multiple observable stages;
3. controlled perturbations that can be defined before results;
4. task outcome availability;
5. stable origin grouping;
6. feasible non-commercial academic use;
7. a clean boundary from the frozen Stage E namespace.

## 2. Candidate matrix

| Candidate | Different pipeline | Multiple stages | Controlled perturbation | Outcome | Origin groups | Academic-use status | Decision |
|---|---|---|---|---|---|---|---|
| FinQA process/checkpoint stream | Yes: financial QA plus program/reasoning steps over tables | Yes: evidence retrieval, program step, numeric result, final answer | Yes: evidence/program operand/operator perturbations can be preregistered | Yes: gold answer and gold program steps | Yes: report-level `TICKER/YEAR` lineage | Repository MIT; dataset licence `LICENCE_PENDING` | `BEST` |
| MultiHiertt | Yes: multi-hierarchical financial QA | Likely: hierarchy/evidence/program/answer | Possible but ontology/adapter not frozen | Yes | Unverified fresh cluster counts | Drive/data terms `UNVERIFIED` | `RESERVE_NOT_READY` |
| TheAgentCompany | Yes: long-horizon agent/service tasks | Yes: task checkpoints and final score in code | Possible through task/environment faults | Yes in evaluator contract | Task family/environment lineage | Code/data scope partially recorded | `RESERVE_BRIDGE_UNAVAILABLE` |
| ToolAlpaca | Yes: tool-use trajectories | Partial: thought/action/observation/final | Syntactic/execution perturbations possible | Incomplete terminal outcome | API/task grouping possible | Dataset licence `LICENCE_PENDING` | `NOT_SECOND_FLOW_PRIMARY` |

## 3. BEST SECOND-DATAFLOW CANDIDATE

**FinQA process/checkpoint stream, in a new namespace.**

Existing verified evidence:

- official repo revision `0f16e2867befa6840783e58be38c9efb9229d742`;
- `train.json` and `dev.json` are already on GB10 under the approved staging scope;
- 7,134 examples;
- 10,960 gold intermediate steps;
- step key set is consistently `(op,arg1,arg2,res)`;
- 21 operation roots;
- multi-step examples are 40.6%;
- report-level `TICKER/YEAR` origin grouping is available;
- the existing split instrument is deterministic, label-blind and hash-bound.

Why it is the best current candidate:

- It changes the measurement object from header-mapping visibility to process/checkpoint evidence.
- It supports at least three natural stages: evidence grounding, program step execution, numeric/final outcome.
- It supplies task outcomes and process steps on the same example.
- It can test whether the multi-leaf result survives a different pipeline and non-header defect families.

## 4. Hard boundaries

`FACT`: the old V2-3 FinQA step-level re-execution route stopped at its preregistered fidelity threshold. That route must not be silently reopened or relabeled as the second-flow experiment.

Required new work before execution:

1. a new task/namespace and preregistration, separate from the stopped route;
2. an explicit perturbation contract for evidence, operator and operand faults;
3. a new checkpoint adapter with expected-first-stage definitions fixed before results;
4. dataset-licence record; current state is `LICENCE_PENDING`;
5. role/split gate for gate-validation and sealed-test, or an explicitly development-only scope;
6. enough independent report clusters for the chosen estimand;
7. an independent scorer or deterministic implementation for at least one non-trivial checkpoint.

Forbidden shortcuts:

- inventing an action vocabulary for FinQA;
- reusing frozen Stage E visibility/detection numbers;
- treating gold program steps as model trajectory checkpoints without a declared adapter;
- changing the stopped V2-3 criterion after seeing new fidelity results;
- claiming external validity from a development-only pilot.

## 5. Reserve candidates

- **MultiHiertt:** potentially stronger hierarchy stress, but revision, Drive/data terms, fresh cluster counts and adapter ontology remain unverified.
- **TheAgentCompany:** strong native checkpoint/task-evaluator concept, but zero released `traj_*.json` / `eval_*.json` pairs in the inspected clone, so `SAME_SAMPLE_BRIDGE_UNAVAILABLE`.

## 6. Decision

```text
BEST SECOND-DATAFLOW CANDIDATE = FINQA_PROCESS_CHECKPOINT_V2_NAMESPACE
STATUS = QUALIFIED_FOR_PREREGISTRATION_DESIGN_NOT_EXECUTION
```

`DECIDE NEXT LOOP: CONTINUE` only if a new preregistration and licence/role gates can be prepared without reopening the stopped V2-3 route. Otherwise `STOP_BRANCH`.
