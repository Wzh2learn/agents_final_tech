# FinQA Process/Checkpoint v2 Preregistration Draft v1

> Status: `DESIGN_ONLY_NOT_AUTHORIZED` | Namespace: `FINQA_PROCESS_CHECKPOINT_V2_NAMESPACE` | No adapter execution, sample selection or result access

## 1. Objective

Test whether label-blind checkpoint dynamics contain stage-localizing information when response signatures overlap:

```text
E: evidence grounding
P: program operator execution
N: numeric operand/reference consistency
```

This is a different measurement object from the frozen Stage E header-injection experiment and must never be described as its replication.

## 2. Source and origin

- Source files: GB10 staging `finqa/train.json` and `finqa/dev.json`.
- Source revision: FinQA `0f16e2867befa6840783e58be38c9efb9229d742`.
- Dataset licence: `LICENCE_PENDING`.
- Origin cluster: report lineage `TICKER/YEAR/page`, preserving all examples from one report in one fold.
- Primary eligible subset: multi-step examples with `len(qa.steps) >= 2`.
- Single-step examples are excluded from the localization denominator and counted separately.

## 3. Label-blind feature extractor

The extractor may read paired clean/mutated pipeline outputs and gold program/answer only for consistency checks. It must not read stage label, mutation type, generator branch, sample namespace or expected-first-stage.

Frozen response vector:

| Feature | Clean/mutated comparison |
|---|---|
| `evidence.required_hit` | required gold evidence present in retrieved/input evidence |
| `program.operator_consistency` | mutated operator root equals clean/gold operator root |
| `program.argument_consistency` | mutated args/reference set equals clean/gold args/reference set |
| `program.step_result_consistency` | recomputed step `res` values match clean/gold step results |
| `answer.consistency` | final executable answer matches clean/gold answer |

Missing/failed execution is encoded in the relevant consistency feature and separately counted; it is not silently treated as zero evidence.

## 4. Fault families and expected first stage

| Family | Source perturbation | Expected first stage | Shared downstream response | Overlap purpose |
|---|---|---|---|---|
| E1 | Remove a required `gold_inds` evidence block used by a program argument | `E` | `program.argument_consistency`, `program.step_result_consistency`, `answer.consistency` | E/N overlap |
| E2 | Replace required evidence with a non-gold block while preserving question/answer | `E` | `evidence.required_hit`, `answer.consistency` | E-only contrast |
| P | Mutate one valid operator root to another same-arity operator | `P` | `program.step_result_consistency`, `answer.consistency` | P/N overlap |
| N | Mutate one numeric operand or valid argument reference | `N` | `program.argument_consistency`, `program.step_result_consistency`, `answer.consistency` | N/E and N/P overlap |

All operations are deterministic and fixed before outcome inspection. The expected first stage is derived from the injection location and pipeline consumption order, not from the observed response.

## 5. Signature requirement

A v2 run is valid only if:

1. at least two stages share at least one responsive feature;
2. at least one pair of stage classes has overlapping response support;
3. feature extraction is demonstrably blind to stage labels;
4. no stage is represented solely by a constant one-hot codebook.

If the resulting signatures are again disjoint and perfectly decodable, classify the result as `INVALID_FOR_V2_GENERAL_LOCALIZATION` and report only a codebook reproduction.

## 6. Predictor and metrics

- Predictor: deterministic nearest-centroid, Euclidean distance, leave-one-report-cluster-out.
- Classes: `E/P/N`.
- Tie: scored incorrect.
- Primary: macro-F1 and top-1 accuracy.
- Baselines: chance/majority, direct-feature codebook, non-direct-feature ablation.
- Permutation: two-sided cluster-label permutation, seed and replicate count must be frozen before result access.
- Bootstrap: report-cluster resampling, seed and replicate count frozen before result access.
- Secondary: per-stage visibility, feature ablation, shared-leaf/overlap counts.
- Exploratory: propagation depth, first-visible distance, silent absorption.

## 7. Sample-size status

The existing conditional planning tier can be reused only as a design prior:

- `TARGET`: 24 report clusters/stage, 3 injections/cluster, pooled macro claim.
- `STRONG`: 50 clusters/stage, per-stage claims.

Current approved staging has approximately 88 report clusters at `M=8`, so the 72-cluster TARGET design is geometrically plausible, but role/layer gates and exact sample IDs are `NOT YET DEFINED`. STRONG is not established by the current staging.

## 8. Hard blockers before execution

1. dataset licence record;
2. new namespace and immutable source hashes;
3. exact sample IDs and mutation manifests selected outcome-blind;
4. role/split gate for gate-validation and sealed-test, or explicitly development-only scope;
5. independent implementation for at least one non-trivial checkpoint;
6. label-blind extractor unit tests with shared-leaf and missing-evidence cases;
7. pre-result freeze receipt;
8. no reuse of the stopped V2-3 fidelity route.

## 9. Allowed and forbidden claims

Allowed after successful v2:

> Label-blind checkpoint dynamics contain stage-localizing information for the preregistered FinQA E/P/N perturbations, with overlapping signatures and report-cluster validation.

Forbidden:

- hierarchy localizes failures;
- natural-task localization is established;
- this is a replication of frozen Stage E;
- this is Stage D distillation or action-label evidence;
- per-stage confirmatory claims unless power supports them.

`DECIDE NEXT LOOP: CONTINUE` only to implement and freeze the adapter/extractor after the eight blockers close.

## 1.1 Approved-staging overlap feasibility (2026-10-10)

`OVERLAP_DESIGN_FEASIBLE` in the existing FinQA staging: 7,134 records / 768 report clusters / 2,894 multi-step records.

- E1/N overlap: 6,915 records and 628 multi-step report clusters.
- P/N overlap: 6,794 records and 628 multi-step report clusters.
- TARGET requirement: 24 report clusters per stage; the observed overlap pools are larger.

`UNVERIFIED`: the E1 join currently uses numeric-token overlap between program arguments and gold evidence text. This is a feasibility proxy, not a causal evidence-to-argument mapping. The causal join and exact sample IDs remain blockers.
