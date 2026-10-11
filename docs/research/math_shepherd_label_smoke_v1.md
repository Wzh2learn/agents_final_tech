# Math-Shepherd-Style Label Construction Smoke v1

> Status: `LABEL_CONSTRUCTION_SMOKE_COMPLETE_NOT_PAPER_RESULT` | 4 PRM prefixes × 4 Qwen3-4B continuations | No training and no Math-Shepherd reproduction

## 1. Frozen smoke design

- Source: PRM800K `phase2_test.jsonl`.
- Selection: four distinct problem hashes with complete selected human step ratings and at least two model-generated steps.
- Prefix: first two `pre_generated_steps`.
- Human comparator: selected PRM rating at zero-based step index 1.
- Continuations: 4 per prefix, temperature `0.7`, top-p `0.95`, max 160 new tokens.
- Seed: `20261014` plus deterministic row/continuation offsets.
- Gold dependence: official `ground_truth_answer` is required.
- Hard label: at least one continuation has a parseable `Final answer` graded correct.
- Soft label: correct continuations divided by 4.
- Missing `Final answer` counts as incorrect and is reported separately.

## 2. Result

| Problem hash | Human rating | Correct continuations | Hard | Soft | No final answer |
|---|---:|---:|---:|---:|---:|
| `0a1707d5...99f0` | +1 | 0/4 | 0 | 0.0 | 4 |
| `c667b151...6554` | +1 | 2/4 | 1 | 0.5 | 1 |
| `24079eb2...dd66` | +1 | 4/4 | 1 | 1.0 | 0 |
| `79b7b095...1bd2` | +1 | 0/4 | 0 | 0.0 | 4 |

Totals:

- hard-positive prefixes: `2/4`;
- human-positive prefixes at the selected step: `4/4`;
- hard/human agreement: `2/4`;
- total soft-label mass: `1.5`;
- continuations without parseable final answer: `9/16`.

## 3. Interpretation

`FACT`: automatic rollout labels are constructible from a problem, step prefix and gold answer without human step annotation.

`FACT`: in this tiny smoke, hard/soft rollout labels disagree with human step labels and are heavily affected by final-answer formatting/continuation success.

`INFERENCE`: the disagreement is not evidence that human labels are wrong or rollout labels are wrong. The two constructs differ: human rating judges a selected step, while rollout success measures whether a sampled continuation from that prefix reaches the gold answer.

`VALUE`: retain both label origins and their uncertainty. A future automatic process-supervision arm must record completer identity, sampling parameters, `N`, answer extraction, `k/N`, human comparison and missing-answer rate.

## 4. Relation to the sensitivity analysis

With `N=4`, the hard existence label can be positive from a single success and is unsuitable as a noise-free correctness probability. The observed `2/4` hard positives and `9/16` missing answers empirically illustrate why the earlier finite-rollout sensitivity analysis is necessary.

## 5. Boundary

This is not the original Math-Shepherd method or completer, not a reproduction of its reported results, not a PRM800K training experiment, and not C4 evidence. It supports only an engineering/reference conclusion:

```text
MATH_SHEPHERD_STYLE_LABELS = CONSTRUCTIBLE_BUT_COMPLETER_AND_EXTRACTION_SENSITIVE
```

`DECIDE NEXT LOOP: STOP_BRANCH` for this smoke. A larger rollout-label study requires a separately preregistered completer, answer parser and uncertainty plan.
