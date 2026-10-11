# Multi-Leaf Mechanism-Generalization Audit v1

> Status: `MECHANISM_GENERALIZATION_NOT_IDENTIFIED` | Read-only audit of frozen M/R/N sample manifest | No formal result rerun

## 1. Frozen design inventory

| Stage | Rows | Clusters | Source IDs | Mutation mechanisms | Templates | Source namespace |
|---|---:|---:|---:|---:|---:|---|
| M | 72 | 24 | 24 | 1 | 65 | TAT-QA financial tables |
| R | 72 | 24 | 24 | 1 | 72 | TAT-DQA QA/evidence records |
| N | 72 | 24 | 24 | 1 | 50 | TAT-QA financial tables |

## 2. Mechanism-generalization decision

| Test | Status | Reason |
|---|---|---|
| Leave-one-mutation-mechanism-out | `NOT_FEASIBLE` | M/R/N each expose one frozen injection operation |
| Train on one mechanism, test on another within stage | `NOT_IDENTIFIED` | no second mechanism is frozen per stage |
| Leave-one-template-out within mechanism | `POSSIBLE_DESCRIPTIVE_ONLY` | headers/questions/identities vary, but this is not mechanism transfer |
| Cross-source-family transfer | `NOT_IDENTIFIED` | M/N share TAT-QA tables; R is TAT-DQA QA; all are financial-domain sources |

## 3. Boundary conclusion

The current result cannot support a mechanism-generalization claim. The direct-codebook ablation already shows that perfect localization is carried by explicitly instrumented stage signals. A stronger future test requires at least two independently defined mutation mechanisms per stage and a preregistered cross-mechanism split.

`MECHANISM_GENERALIZATION_NOT_IDENTIFIED`

## 4. Provenance caveat

Literal M/N table UIDs are disjoint and R uses a separate document namespace, but semantic origin aliases across datasets were not independently audited. This is a provenance gap, not evidence of leakage.
