# G3 V2 Report: Real Verification Actions And Cost

Date: 2026-10-22, Asia/Shanghai

Status: `SIMPLE_FIXED_RULE_SUFFICIENT_ON_CURRENT_TASK`

## Measured Surface

Four objects were evaluated in real Partridge worktrees: natural parent, natural
gold, target-call/source-fallback control and valid alias control. Every object
ran the real 42-test repository suite. Static and runtime actions used the same
v2 verifier as G2. Costs are GB10 wall-clock including process startup.

## Results

| Policy | Correct | False accepts | False rejects | Deferred | Actions | Seconds |
|---|---:|---:|---:|---:|---:|---:|
| No revalidation | 2 | 2 | 0 | 0 | 0 | 0.00 |
| Always defer | 0 | 0 | 0 | 4 | 4 | 0.66 |
| Behavior only | 2 | 2 | 0 | 0 | 8 | 13.71 |
| Static contract only | 3 | 0 | 1 | 0 | 8 | 0.78 |
| Static then behavior | 3 | 0 | 1 | 0 | 9 | 4.09 |
| Source guard + runtime + behavior | 4 | 0 | 0 | 0 | 12 | 7.33 |
| Runtime consumption + behavior | 4 | 0 | 0 | 0 | 10 | 7.26 |

The two invalid objects pass all repository tests, so behavior-only is not
enough. Static-only rejects the valid alias. Runtime consumption plus behavior
is the simplest tested rule that classifies all four correctly.

## Interpretation

This result supports a fixed short-circuit evidence sequence, not a learned
adaptive policy. The old 62/99 planning simulation remains a development
artifact and is superseded for real cost claims by this receipt. The sample is
one repository and four objects; it does not estimate population error or
cross-project cost.

## Decision

Do not develop a complex planner on the current evidence. Continue G3 only as
the cost/risk analysis layer for G2, and test whether the simple rule survives
new task families. If fixed runtime+behavior remains sufficient, close the
complex-policy candidate and report a boundary result.
