# Natural Program Method Research Return V3

Date: 2026-10-24, Asia/Shanghai

Status: `MEASUREMENT_CORRECTED / ORDINARY_SFT_STRONG_BASELINE / VISIBLE_FILTER_STOPPED / PAIRED_STABILITY_STOPPED / C3_NO_POLICY_INCREMENT`

## 1. Measurement Correction

The v2 natural-variant scorer used `instance["table_text"]`, which stayed at the
original task table even when the relevant/irrelevant change was written into
the prompt. The expected answer was computed from the changed table, so the
scorer compared a changed reference against execution on stale values.

This is a measurement bug, not evidence that the models failed to adapt. The
old generations and old scores remain preserved. A versioned post-hoc rescore
executed the frozen programs against the exact table visible in each prompt:

- 648 frozen generation rows rescored;
- 95 rows flipped from false to true;
- ordinary SFT relevant-change adaptation changed from 0 to dev 66.7%,
  test 75.0%, external 79.2%;
- ordinary SFT paired completion became dev 50.0%, test 70.8%,
  external 79.2%.

The corrected source-cluster comparison still favors ordinary
answer/execution SFT over visible-program filtering. On test, ordinary minus
visible is +20.8pp for original correctness and +25.0pp for paired completion;
on external it is +25.0pp and +29.2pp. The visible-program filter is stopped
as a feedback method.

## 2. Same-Source New-Family Confirmation

A frozen confirmation selected 24 TAT-QA table families excluded from the 512
training tasks and all prior evaluation tables. This is a new-family check
within TAT-QA, not cross-dataset generalization.

| Arm | Original | Relevant adaptation | Irrelevant invariance | Paired all-three |
|---|---:|---:|---:|---:|
| Ordinary answer/execution SFT | 95.8% | 91.7% | 91.7% | 87.5% |
| Visible-program filter SFT | 58.3% | 58.3% | 50.0% | 50.0% |

Ordinary minus visible paired completion is +37.5pp with table-cluster 95%
interval `[16.7pp, 58.3pp]`. The transparent row/year calculator solves
10/24 = 41.7%. The ordinary arm is therefore a real strong baseline on this
bounded panel, while visible filtering is not a viable improvement.

## 3. Stability-Supervision Candidate

The residual errors included unstable evidence references across visible
variants. A frozen cost-matched experiment compared:

- `duplicate_original_control_sft`: 1,024 rows from duplicated original tasks;
- `paired_variant_stability_sft`: 1,024 rows from original plus deterministic
  relevant/irrelevant variants with the same target program.

Both arms used 512 steps and the same Qwen3-4B LoRA configuration. The
confirmation used 24 additional unseen table families and 72 instances per
arm.

| Arm | Paired all-three | Reference stability | Relevant adaptation |
|---|---:|---:|---:|
| Ordinary SFT | 83.3% | 95.8% | 87.5% |
| Duplicate-original control | 83.3% | 95.8% | 83.3% |
| Paired-variant stability SFT | 83.3% | 91.7% | 87.5% |

The candidate has zero paired-completion gain over both comparators and a
-4.2pp reference-stability difference with interval `[-12.5pp, 0]`. It is
stopped under the frozen rule. This is a negative method result, not evidence
that stability supervision is universally ineffective.

## 4. C3 Delivery

With deployment-visible checks only, the ordinary strong rule accepts all
confirmation outputs and delivers 68/72 correct and 4/72 wrong (5.6%
conditional wrong). On the stability confirmation, the corresponding numbers
are 62/72 correct and 10/72 wrong (13.9%). The candidate stability arm has
63/72 correct and 9/72 wrong, but no acceptance decision separates it from
always-accept. No learned policy is fitted on confirmation data. The previous
dev-calibrated logistic policy already equaled the strong rule. Complex
delivery-policy expansion remains stopped; the visible rule is not a new
method contribution.

## 5. Evidence Boundary

- `VARIANT_RESCORE_V3.json` is post-hoc rescore of frozen outputs, not a new
  prospective experiment.
- `CONFIRMATION_SUMMARY_V3.json` and `PAIRED_STABILITY_CONFIRMATION_V3.json`
  are same-source new-family confirmations, not independent benchmark results.
- The natural method uses TAT-QA train/dev files and executable gold
  derivations; DocMath remains gated and FinQA is exposed Paper E material.
- No judge, paid API, production Memory write, or hidden-reference policy
  feature was used in the new deployment checks.

## 6. Scientific Judgment

1. The old relevant-change failure claim is withdrawn because of stale-table
   scoring. Ordinary SFT already performs causal operand adaptation on most
   tasks.
2. Ordinary answer/execution SFT plus a fixed calculator is the strong
   baseline. Visible program filtering is inferior and stopped.
3. Pairing counterfactual surfaces with unchanged target programs does not
   improve this panel; reference instability remains a small residual problem,
   not a validated method opportunity.
4. C3 has no incremental policy signal after deployment-visible checks;
   stop complex delivery strategies on this panel.
5. The next information-bearing step is a new natural source or a deterministic
   row/period binding checker evaluated on the remaining reference-instability
   cases. It must be tested before any further training and must not reuse
   these confirmation families for method selection.
