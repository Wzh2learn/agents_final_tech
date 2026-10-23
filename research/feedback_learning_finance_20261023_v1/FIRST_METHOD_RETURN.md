# First Method Experiment Return

Date: 2026-10-24, Asia/Shanghai

Status: `C2_CURRENT_FILTER_NOT_CONFIRMED / C3_STRICT_DELIVERY_BLOCKED_BY_INTERFACE`

Evidence identity: real Qwen3-4B LoRA SFT and frozen greedy generations over
derived TAT-QA financial-table tasks. Controlled corruptions are mechanism
probes, not natural error-frequency estimates. No judge, paid API or production
Memory write was used.

## 1. Paper E

Paper E remains unchanged as the mature contribution: a two-case measurement
audit with an internal submission handoff. This experiment neither adds a third
case nor changes the submission boundary. Owner-only actions remain author and
affiliation confirmation, AI disclosure approval, artifact release/license,
formal submission/payment, patent status, presentation and school recognition.

## 2. Hypotheses And Frozen Design

The experiment tested three separable hypotheses:

1. Evidence-dependency feedback filtering improves paired correct completion
   over answer/execution filtering and cheap consistency filtering.
2. Adding paired relevant-change examples improves adaptation without sacrificing
   invariance to irrelevant changes.
3. A calibrated delivery policy can improve correct-delivery coverage over the
   all-applicable-checks-pass rule at comparable wrong-delivery risk and cost.

The source is TAT-QA real financial tables under CC BY 4.0. Derived tasks ask
for row-scoped, period-bound numeric change or percentage change with a visible
unit. Table UID is the split unit. The task builder generated 928 tasks:
640 train, 96 dev, 96 test and 96 external; the experiment used 32 dev, 14
test and 14 external task IDs. Original and paired variants stayed together.

Six real LoRA SFT arms used Qwen3-4B:

| Arm | Original rows | Added CF rows | Controlled error rows retained | Training tokens | GPU seconds |
|---|---:|---:|---|---:|---:|
| `exec_orig` | 160 | 0 | 16 same-value wrong evidence, 69 unit errors | 58,175 | 52.78 |
| `cheap_orig` | 160 | 0 | 16 same-value wrong evidence; 0 unit errors | 58,175 | 49.96 |
| `evidence_orig` | 160 | 0 | 0 | 58,173 | 50.58 |
| `exec_cf` | 160 | 160 | same controlled mix as `exec_orig` | 117,141 | 98.79 |
| `cheap_cf` | 160 | 160 | 16 same-value wrong evidence; 0 unit errors | 117,141 | 153.47 |
| `evidence_cf` | 160 | 160 | 0 | 117,139 | 101.04 |

The CF main effect is confounded with additional rows and updates. Filter
comparisons within `*_orig` or `*_cf` use the same task IDs and are the primary
mechanism comparisons.

## 3. Actual Model Results

Strict JSON success is zero for every model because outputs contain prose and/or
truncate before the contract is complete. This is an interface/output-budget
failure, not zero semantic capability. The table below reports:

- `direct`: model-written numeric answer is correct;
- `tool`: executing the model's visible-cell formula gives the correct answer;
- `evidence`: exact visible cell references are correct;
- `paired`: original, irrelevant-change invariance and relevant-change adaptation
  are all correct.

| Model | Test direct | Test tool | Test evidence | Test paired direct | Test paired tool | External direct | External tool | External evidence | External paired direct | External paired tool |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base Qwen3-4B | 28.6% | 31.0% | 42.9% | 7.1% | 0.0% | 11.9% | 9.5% | 14.3% | 7.1% | 0.0% |
| `exec_orig` | 45.2% | 88.1% | 90.5% | 28.6% | 42.9% | 7.1% | 95.2% | 95.2% | 0.0% | 21.4% |
| `cheap_orig` | 47.6% | 85.7% | 88.1% | 42.9% | 57.1% | 11.9% | 92.9% | 92.9% | 0.0% | 35.7% |
| `evidence_orig` | 50.0% | 85.7% | 85.7% | 35.7% | 57.1% | 7.1% | 81.0% | 81.0% | 0.0% | 21.4% |
| `exec_cf` | 64.3% | 92.9% | 92.9% | 57.1% | 64.3% | 16.7% | 97.6% | 97.6% | 0.0% | 35.7% |
| `cheap_cf` | 61.9% | 90.5% | 90.5% | 57.1% | 64.3% | 11.9% | 95.2% | 95.2% | 0.0% | 21.4% |
| `evidence_cf` | 71.4% | 92.9% | 92.9% | 71.4% | 78.6% | 14.3% | 97.6% | 97.6% | 0.0% | 28.6% |

The tool column is a post-hoc diagnostic over frozen outputs. It is not a
strict model success and must not replace the direct-output result.

## 4. Strong-Baseline Comparisons

On held-out test table UIDs from the same TAT-QA train source:

- `evidence_cf - exec_cf` paired direct completion is `+11.5 pp`, source-cluster
  95% interval `[0.0, 30.8]` pp.
- `evidence_cf - cheap_cf` paired direct completion is `+11.5 pp`, interval
  `[0.0, 30.8]` pp.
- The point estimate reaches the proposed +5 pp threshold, but the interval
  lower bound is zero, so the predeclared confirmation condition is not met.
- Under tool execution, `evidence_cf - exec_cf` paired is `+11.5 pp` on test but
  `-7.1 pp` on external, interval `[-28.6, 14.3]` pp.

On the external TAT-QA dev source:

- All models have zero direct paired completion.
- `exec_cf` and `cheap_orig` have the best tool-paired completion at 35.7%.
- `evidence_cf` has 28.6%, so evidence-dependency filtering does not beat the
  strongest simple arm.
- Trained models preserve formula/evidence selection at 81.0-97.6% while direct
  answers collapse to 7.1-16.7%. The main external failure is result
  calculation/output transfer, not exact evidence binding.

Scientific decision: **do not claim a feedback-filter learning gain**. Keep the
real training result as evidence that operand/formula selection is learnable,
but stop promoting evidence-dependency filtering over cheap consistency or
answer/execution filtering on the current task.

## 5. C3 Delivery Replay

The strong rule accepts only if the strict interface and every applicable check
pass. Because strict interface success is zero, both the strong rule and strict
risk policy deliver zero answers with zero observed wrong deliveries. The cost
is still incurred: approximately 386 cost units per test item and 416 per
external item for the CF models.

A post-hoc diagnostic replay first recovers embedded JSON and then applies the
same checks:

| Model | Test strong coverage | Test risk coverage | External strong coverage | External risk coverage | Wrong deliveries |
|---|---:|---:|---:|---:|---:|
| `exec_cf` | 31.0% | 64.3% | 7.1% | 16.7% | 0 observed |
| `cheap_cf` | 31.0% | 61.9% | 4.8% | 11.9% | 0 observed |
| `evidence_cf` | 35.7% | 71.4% | 4.8% | 14.3% | 0 observed |

This is promising headroom but **not a deployable C3 result**:

- the accepted outputs violate the strict response contract;
- only 14 paired tasks are available per held-out slice;
- zero observed wrong deliveries is not zero risk;
- the risk policy is calibrated on only 32 dev outputs per model.

Scientific decision: stop complex delivery-policy claims for this round. First
remove the interface failure with constrained JSON/short output plus a frozen
calculator step, then rerun the same strong-rule comparison on fresh source
families.

## 6. Failure Analysis And Next Experiment

The experiment localized a real mismatch:

1. SFT learns which visible cells and formula shape to use.
2. The 4B model often calculates or serializes the numeric answer incorrectly.
3. The strict interface adds another failure layer before delivery policy can be
   evaluated.

The most informative next experiment is therefore not another feedback filter.
Use a fixed two-stage contract:

1. the model emits only row/column operands and an operator under constrained
   JSON;
2. a frozen calculator executes that program;
3. the strong delivery rule and the candidate policy judge the tool result.

Compare `cheap_orig` and `exec_cf` as the strongest simple arms against one
candidate method on a fresh external source. Stop the candidate unless it
improves tool-resolved paired completion and delivery coverage at non-inferior
wrong-delivery risk. This directly tests the residual problem without letting
arithmetic serialization masquerade as evidence learning.

## 7. Raw Evidence And Cost

Raw GB10 run root:

`/home/testuser/wzh/research_runs/feedback_learning_finance_20261023_v1`

Key immutable outputs:

- `financial_feedback_tasks.jsonl`, SHA-256
  `e507c6dc22410558add07748a19fc6b18acf9270966d72c19c9f330bd7d72ab0`
- `generation_results.jsonl`, SHA-256
  `9e9ba35f2f76de718f2485099e0088abbe342d87054c7564cf414a1a17abea9e`
- `RESULT_SUMMARY.json`, SHA-256
  `7a897097da4ab257a17fef214b6d24b8549a7a56221773cc995286294c3a4cf6`

Resource totals are in `RESOURCE_RECEIPT.json`. Six training runs consumed
525,944 training tokens and 506.6 GPU-seconds. The successful batched evaluation
used 812 accounting attempts and 295,973 generation tokens. The interrupted
sequential evaluation is conservatively counted as 128 attempts and 58,743
tokens. Total new accounting is therefore at most 940 attempts and 880,660
tokens including training. Judge calls, paid API calls and production Memory
writes are zero.

