# Same-Number Role Arm Comparison

Status: `EXPLORATORY_COMPARISON_COMPLETE_BUDGET_EXHAUSTED`

## Frozen comparison

All arms use the same 12 matched tasks from the six B0 failure clusters: one supported and one wrong-role task per cluster.

| arm | success | non-success | decision match | valid plan | interpretation |
|---|---:|---:|---:|---:|---|
| B0 | 6/12 | 6 | 6/12 | 12/12 | role binding has real headroom |
| R | 8/12 | 4 | 9/12 | 11/12 | strong role rule helps but does not close the gap |
| C | 7/12 | 5 | 7/12 | 9/12 | generic context is weaker and introduces plan failures |

R residual failures occur in four clusters: two wrong-role false accepts, one supported false reject, and one invalid plan. C residual failures occur in five clusters, including three `UNKNOWN` responses and two role mistakes.

## Mechanism reading

`FACT`: numeric/tool behavior is mostly stable; the contested behavior is whether equal numbers are accepted under the wrong row/period role.

`INFERENCE`: a strong static role-checking rule accounts for part of the headroom, but it does not explain all role decisions. General context is not a sufficient substitute and may distract plan generation.

`UNVERIFIED`: real history could improve the residual role decisions. The current 12 calculation histories do not contain wrong-role corrections and cannot populate H. B0/R/C outputs cannot be recycled as experience.

## Decision

The task family is scientifically viable, but the current evidence supports only:

> role binding has headroom; a strong rule improves it; experience-specific benefit is unmeasured.

Do not claim that H would win. Do not run H without a new task-matched history collection and a prospective context contract.

## Budget

- Same-number B0: 48 requests / 29,207 tokens.
- R: 24 requests / 16,385 tokens.
- C: 24 requests / 15,929 tokens.
- Cumulative project ledger: 228/228 requests and 243,014/2,450,000 tokens.
- Remaining request budget: 0.

## Required next authorization

One new authorization is required for either:

1. a task-matched history collection plus H comparison; or
2. acceptance of the current exploratory boundary and closure of the experience-reuse route.

Any future run must freeze corrected `SUPPORTED/WRONG_ROLE` semantics prospectively and keep `calc_value/unit` for both decisions.
