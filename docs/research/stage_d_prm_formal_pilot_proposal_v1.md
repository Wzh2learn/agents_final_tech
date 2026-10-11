# Stage D PRM Formal Pilot Proposal v1

> Status: `PRM_FORMAL_PILOT_NOT_READY` | Basis: PRM dry-run `VALIDATED_NON_TRAINING` + reference smoke `PIPELINE_CLOSED` | Formal C0/C1/C2/C4 training not executed

## 1. Scientific question

At the same mother pool, model, optimizer, token budget, origin-group budget and evaluation set, does human process-label selection provide incremental training-data selection value over terminal-outcome selection?

This is a C4-minus-C2 comparison. C0 and C1 are diagnostic controls and cannot rescue a failed C4-C2 contrast.

## 2. Proposed arms

| Arm | Selection rule | Role |
|---|---|---|
| C0 | unfiltered mother pool | sanity baseline |
| C1 | random selection matched on rows, tokens and origin/problem groups | chance control |
| C2 | terminal answer correctness from official `grading.grader.grade_answer` | outcome comparator |
| C4 | complete selected human process path with all step ratings positive | process comparator |

A lenient no-negative C4 variant is sensitivity-only and cannot replace the primary C4 arm.

## 3. Mother pool and split

Required source: PRM800K official training payload, not the phase2-test reference subset.

Proposed grouping and split:

- group key: derived SHA-256 of `question.problem`, explicitly marked `DERIVED`;
- all rows from one problem group stay in one role;
- roles: proposal, train, gate-validation, sealed-test;
- no cross-role problem-text overlap;
- native token counts must come from the frozen tokenizer, not whitespace/character proxies;
- missing selected labels are excluded from C4 and reported in the denominator.

Current status:

| Requirement | Status |
|---|---|
| phase2-test reference schema | `VERIFIED` |
| official train payload body | `LFS_POINTER_ONLY` |
| dataset licence | `LICENCE_PENDING` |
| native token matching | `NOT YET AVAILABLE` |
| frozen role split | `NOT YET FROZEN` |
| process label provenance | human PRM labels verified on test subset |
| outcome oracle | official grader verified on test subset |
| formal power plan | `NOT YET APPLIED TO TRAIN PAYLOAD` |

## 4. Model and training budget

Pilot engineering proposal only:

- model: local Qwen3-4B;
- method: LoRA SFT, `q_proj/v_proj`;
- reference smoke used one seed; any formal pilot must use at least three seeds;
- fixed token budget and optimizer schedule before training; no post-result budget changes;
- no hyperparameter search;
- one checkpoint per arm;
- held-out exact-answer and LM-loss evaluation;
- no claim from the tiny reference-smoke loss values.

The existing 64M non-padding tokens per arm/seed estimate remains planning-only until the train payload, split and native token accounting are frozen. Formal pilot readiness requires at least three seeds and an independent held-out evaluation.

## 5. Evaluation contract

Primary:

- held-out task exact-match/official grader accuracy;
- C4 minus C2 paired difference over matched problem/origin groups.

Secondary:

- held-out LM loss;
- step-count/token-count balance;
- per-op/problem-family slices where available.

Safety/risk:

- do not infer semantic harmfulness from PRM process labels;
- report missing-label and licence restrictions;
- preserve negative/null results;
- no external publication or redistribution while `LICENCE_PENDING`.

## 6. Identification controls

The C4-C2 contrast is interpretable only if:

1. same mother pool and source revision;
2. same student model and tokenizer;
3. same optimizer, learning-rate schedule and seed count;
4. matched token and origin/problem-group budgets;
5. same held-out evaluation set;
6. no sealed-test access during selection or tuning;
7. process labels are not derived from terminal answers;
8. missing labels are not silently imputed.

## 7. Stop gates

Do not launch formal training until all are closed:

```text
DATA CONTRACT READY
+ SPLIT READY
+ PROCESS SIGNAL READY
+ OUTCOME READY
+ EVALUATION READY
+ MODEL_GO
+ TRAINING_GO
```

## 9. Power, resource and sample contract

| Contract field | Current value | Readiness |
|---|---|---|
| Mother pool | official PRM train payload; exact row/problem-group scale `NOT YET AVAILABLE` | BLOCKED |
| C2/C4 disagreement | verified on phase2 test: 262 C2-only and 54 strict-C4-only matched pairs | PASS_REFERENCE_ONLY |
| Group-disjoint split | derived problem hash; exact role allocation `NOT YET FROZEN` | BLOCKED |
| Sample count matching | equal selected rows and matched problem groups required | DESIGN_READY |
| Token matching | frozen tokenizer non-padding counts required | BLOCKED |
| Leakage control | problem-group disjointness plus train/dev/gate/sealed role checks | DESIGN_READY |
| Base model | Qwen3-4B exact validated revision | READY |
| Optimizer | LoRA `q_proj/v_proj`, AdamW, fixed LR schedule | READY |
| Training budget | 64M non-padding tokens/arm/seed is planning-only | BLOCKED |
| Seeds | at least 3 | DESIGN_READY |
| Independent evaluation | fixed held-out problem groups and exact-match primary | DESIGN_READY |
| MDE / power | `NOT ESTIMABLE` from the 2-step smoke; smoke loss is not an effect size | BLOCKED |

`PRM_FORMAL_PILOT_NOT_READY`

The identification target is C2 terminal-outcome selection versus C4 process-evidence selection under matched problem distribution, sample count, token budget, groups, model, optimizer and evaluation. It is not process-supervised data versus random data.

Current decision: `NO-GO_FOR_FORMAL_TRAINING`, `PRM_FORMAL_PILOT_NOT_READY`, `GO_FOR_CONTRACT_REVIEW`.

## 8. What the reference smoke established

The smoke established only the chain:

```text
dataset -> C2/C4 selection -> LoRA training -> checkpoint -> held-out evaluation
```

It did not establish C4 superiority, data licence closure, representative power or paper-ready evidence. `DECIDE NEXT LOOP: STOP_BRANCH` for additional smoke runs; proceed to formal pilot only after the gates above.
