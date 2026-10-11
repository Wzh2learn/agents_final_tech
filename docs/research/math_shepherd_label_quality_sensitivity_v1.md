# Math-Shepherd Label-Quality Sensitivity v1

> Status: `DETERMINISTIC_METHOD_ANALYSIS_NO_DATA_REPRODUCTION` | Scope: finite-rollout hard/soft label statistics only | No model or training call

## 1. Method under analysis

For a step prefix with true continuation-success probability `p`, Math-Shepherd samples `N` continuations and constructs:

```text
soft label = k / N
hard label = 1 if k > 0 else 0
```

where `k` is the number of continuations reaching the gold answer. The paper uses a reported `N=8` completer setting.

## 2. Statistical consequences at N=8

Assume independent continuation outcomes as a reference model:

```text
E[soft] = p
SD(soft) = sqrt(p(1-p)/N)
P(hard=1) = 1 - (1-p)^N
```

| True `p` | `P(hard=1)` | Hard-label bias `P(hard=1)-p` | `SD(soft)` |
|---:|---:|---:|---:|
| 0.01 | 0.077255 | 0.067255 | 0.035178 |
| 0.05 | 0.336580 | 0.286580 | 0.077055 |
| 0.10 | 0.569533 | 0.469533 | 0.106066 |
| 0.20 | 0.832228 | 0.632228 | 0.141421 |
| 0.50 | 0.996094 | 0.496094 | 0.176777 |

## 3. Interpretation

`FACT`: under the independent-rollout reference, the hard label is an optimistic existence event. A step with true success probability 0.10 is marked positive about 57% of the time with `N=8`.

`FACT`: the soft label estimates the continuation-success probability but has substantial finite-rollout variance; `N=8` alone does not make it a precise step-correctness probability.

`INFERENCE`: hard and soft labels answer different questions. Hard labels ask whether any sampled continuation succeeds; soft labels approximate rollout success probability. They must not be collapsed into a single noiseless correctness label.

`VALUE`: future Math-Shepherd-style adapters should retain `N`, completer revision, decoded-answer rule, duplicate-removal policy, `k`, soft label and hard label. Report uncertainty or sensitivity across `N`, and prefer soft labels for graded filtering unless the task explicitly requires an existence criterion.

## 4. Comparison with PRM800K

| Dimension | PRM800K | Math-Shepherd |
|---|---|---|
| Source label | human step rating `-1/0/+1` | rollout-derived hard/soft label |
| Evidence level | human-derived candidate, subject to missing/annotator protocol | verifier/rollout-derived, `L3` in project ladder |
| Gold answer | used by grading context | required to score continuations |
| Main noise | human/protocol/missing labels | finite rollout, completer error, answer decoding |
| Best use | reference human-process selection | scalable derived-process sensitivity arm |

`VALUE`: the strongest future design is a provenance-stratified comparison: human-derived PRM labels versus automatic rollout labels on matched problem groups. Neither source should be treated as native truth without its own uncertainty/provenance record.

## 5. Boundary

This analysis does not reproduce Math-Shepherd training, verify its released data, establish an official repository, or justify C4 superiority. It only shows why hard/soft labels require explicit provenance and noise accounting.

`DECIDE NEXT LOOP: STOP_BRANCH` unless an official Math-Shepherd data/implementation source is established.
