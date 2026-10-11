# FinQA v2 Candidate Sample Manifest v1

> Status: `CANDIDATE_SAMPLE_IDS_FROZEN_NOT_EXECUTION` | Outcome-blind candidate IDs only | No formal FinQA execution

## 1. Counts

| Stage | Selected clusters | Selected injections | Eligible clusters after disjointness |
|---|---:|---:|---:|
| E | 24 | 72 | 594 |
| P | 24 | 72 | 526 |
| N | 24 | 72 | 553 |

Stages consume disjoint report clusters. Each selected cluster has exactly three candidate injections.

## 2. Frozen operations

- `E`: remove the uniquely resolved required evidence block from the candidate evidence bundle.
- `P`: replace an add/minus/multiply/divide operator with its fixed same-arity counterpart.
- `N`: mutate one numeric literal argument by a fixed nonzero delta.

Expected first checkpoints are frozen as `evidence.required_hit`, `program.operator_consistency`, and `program.argument_consistency`.

## 3. Gate status

| Gate | Status |
|---|---|
| ID_GO | `PASS_CANDIDATE_IDS_FROZEN_NOT_EXECUTION` |
| JOIN_GO | `PASS_RESOLVER_AND_CANDIDATES_NOT_FORMAL` |
| SPLIT_GO | `BLOCKED_SPLIT_ROLE_NOT_FROZEN` |
| PREREG_GO | `BLOCKED_UNTIL_SCORER_AND_SPLIT_FREEZE` |

`FACT`: exact candidate IDs and operations are frozen without reading evaluator output.

`BLOCKER`: split roles are not frozen. This manifest is not authorization to execute the second-flow experiment.

## 4. Mechanism boundary

These IDs do not create multiple mutation mechanisms per stage. Mechanism generalization remains `NOT_IDENTIFIED`.
