# G3 V2 Report: Actual Actions And Simple-Baseline Necessity

Date: 2026-10-22, Asia/Shanghai

Status: `COMPLEX_PLANNER_PAUSED_SIMPLE_RULE_SUFFICIENT`

## Measured Surface

`G3_REAL_ACTION_RESULTS_V2_COMPACT.json` records six actual Partridge worktree
candidates: natural parent, natural migration commit, source-fallback control,
alias control, audit counterexample and one natural model output. Each object
runs:

- environment preflight;
- the original repository test suite;
- an independent 24-fixture behavior comparison against the parent;
- alias-aware static contract analysis on the actual module;
- paired target-result consumption intervention on the same module.

Module and manifest hashes are recorded per object. Timing is one observation
per action with shared receipts replayed for policies; it is not a stable cost
distribution.

## Results

| Policy | Correct | False accepts | False rejects | Unresolved | Actions | Seconds |
|---|---:|---:|---:|---:|---:|---:|
| No revalidation | 3/6 | 3 | 0 | 0 | 0 | 0.00 |
| Repository tests only | 4/6 | 2 | 0 | 0 | 12 | 20.64 |
| Strong static + repository tests | 6/6 | 0 | 0 | 0 | 16 | 14.32 |
| Strong static + independent behavior | 6/6 | 0 | 0 | 0 | 16 | 2.10 |
| Consumption + independent behavior | 6/6 | 0 | 0 | 0 | 15 | 1.88 |
| Combined short-circuit | 6/6 | 0 | 0 | 0 | 19 | 2.03 |

Repository tests alone accept the parent and source-fallback invalid objects.
Adding a strong alias-aware static contract removes those false accepts. The
paired consumption rule also removes them, but does not improve classification
over the simpler static-plus-behavior controls.

## Interpretation

The old `62/99` planning simulation is superseded for empirical claims. The new
evidence supports transparent short-circuit verification but does not support a
learned or complex adaptive planner. The apparent timing differences are not
stable enough to claim a cost winner; process startup dominates these small
actions.

## Decision

Keep the complex planner paused. Use G3 as a cost/risk and evidence-selection
analysis layer only. A future cost study would require repeated cold/warm runs,
fixed order, variance estimates and a task family where different evidence
channels are genuinely complementary.
