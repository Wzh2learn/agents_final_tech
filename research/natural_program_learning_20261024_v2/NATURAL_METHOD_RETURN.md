# Natural Program Method Return

> **V3 measurement correction:** the relevant-change rows below were scored on
> stale task tables and the `0%` adaptation interpretation is superseded. The
> authoritative corrected results and two frozen confirmations are in
> [METHOD_RESEARCH_RETURN_V3](METHOD_RESEARCH_RETURN_V3.md) and
> [VARIANT_RESCORE_V3](VARIANT_RESCORE_V3.json). The original v2 numbers remain
> preserved as historical output.

Date: 2026-10-24, Asia/Shanghai

Status: `ORDINARY_SFT_STRONG_BASELINE / VISIBLE_FILTER_NOT_CONFIRMED / RELEVANT_ADAPTATION_FAILED`

## 1. What Was Executed

This stage used natural TAT-QA arithmetic questions and gold derivations, not
the previous generated change template. A derivation was accepted only when
its arithmetic executed and non-scaling numeric operands could be mapped to
visible table cells. The resulting dataset contains 1,752 tasks:

- train 1,142;
- dev 217;
- test 198;
- same-benchmark dev-file external 195.

Two real Qwen3-4B LoRA SFT arms were trained on 512 unique tasks each:

- `ordinary_answer_execution_sft`: hidden answer/program execution filtering;
- `visible_program_filter_sft`: question/program/ref/execution filtering without
  hidden expected answers.

Both arms completed 512 steps. The base model and both adapters were then
evaluated on 24 tasks per slice, each with original, relevant-change and
irrelevant-change variants.

## 2. Strong Baseline And Method Comparison

The transparent row/year calculator is not sufficient on natural questions:

- test: 36/198 tasks solved;
- external: 22/195 tasks solved.

The stronger baseline is ordinary answer/execution-filtered SFT.

| Model | Test original | Test irrelevant invariant | Test paired all-three | External original | External irrelevant invariant | External paired all-three |
|---|---:|---:|---:|---:|---:|---:|
| Base Qwen3-4B | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Ordinary answer/execution SFT | 75.0% | 70.8% | 0.0% | 79.2% | 79.2% | 0.0% |
| Visible program filter SFT | 54.2% | 45.8% | 0.0% | 54.2% | 50.0% | 0.0% |

The ordinary-minus-visible source-cluster differences are:

- original correctness: test `+20.8pp`, 95% interval `[0, 41.7]`;
  external `+25.0pp`, interval `[8.3, 41.7]`;
- irrelevant invariance: test `+25.0pp`, interval `[4.2, 45.8]`;
  external `+29.2pp`, interval `[12.5, 50.0]`.

Therefore the visible-program candidate is not confirmed and is inferior on
the current natural task. It should not be expanded as a feedback method.

All three models have zero relevant-change adaptation. This is the most useful
residual: the current training target still permits constant memorization or
mixed ref/constant programs, so outputting a syntactically valid program does
not guarantee that the calculation consumes the changed visible operand.

## 3. C3 Delivery Result

The strong deployment rule accepts only parseable outputs with valid refs and
an executable program. Hidden reference values are used only for final offline
correctness.

- Ordinary SFT test: strong rule accepts 72/72, 36 correct and 36 wrong;
  conditional wrong-delivery 50%.
- Ordinary SFT external: accepts 71/72, 38 correct and 33 wrong;
  conditional wrong-delivery 46.5%.
- Visible-filter SFT test: accepts 69/72, 24 correct and 45 wrong;
  conditional wrong-delivery 65.2%.
- Visible-filter SFT external: accepts 70/72, 25 correct and 45 wrong;
  conditional wrong-delivery 64.3%.

The dev-calibrated logistic policy selects the same decisions as the strong
rule. It provides zero incremental coverage or risk reduction. Per the frozen
rule, complex delivery-policy expansion stops. The correct next mechanism is
not another risk classifier; it is a stronger deployment-visible binding check
or a program representation that cannot mix hidden constants with visible
operands.

## 4. Scientific Judgment Changes

1. C2 ordinary SFT is a real strong baseline on natural financial questions.
2. The proposed visible-program feedback filter is worse than ordinary
   answer/execution filtering on this task. Its current form is stopped.
3. Relevant-change failure is not an output-format-only problem. The residual
   is operand binding and program construction under changed values.
4. C3 reference-assisted checks were invalid deployment features; after their
   removal, the simple risk model has no increment over the all-check rule.
5. TAT-QA train/dev remain same-benchmark splits. External results are
   source-file evidence, not cross-dataset generalization.

## 5. Next Discriminating Experiment

Use a stricter program contract where every arithmetic leaf must be an explicit
visible `R:C` reference and no numeric constants are allowed except declared
scale constants (`1`, `100`). Train ordinary SFT and an operand-binding
candidate on relevant-change pairs. Compare:

- ordinary SFT with visible-only program trees;
- a candidate that verifies each operand against question roles/periods before
  execution;
- the transparent row/year calculator.

Primary outcomes remain relevant-change adaptation and final delivered
correctness. If the strict reference-only contract closes most of the gap, stop
feedback-filter research and report that ordinary learning plus executable
programs explains the task. If relevant-change failures remain, the residual is
then a real method problem.

## 6. Resources And Evidence

Raw outputs remain on GB10 under
`/home/testuser/wzh/research_runs/natural_program_finance_20261024_v2`.
The current receipts are:

- 1,024 training rows, 970,872 training tokens, 843.75 GPU-seconds;
- successful generation: 648 accounting attempts, 363,941 tokens;
- interrupted first evaluation: conservative upper bound 288 attempts and
  275,581 tokens;
- combined upper bound: 936 attempts and 1,610,394 tokens including training.

The local protocol token estimate of 1.2M omitted training tokens and the
interrupted upper bound. The global authorization remains sufficient, and no
further generation is planned before the next confirmation design. Judge calls,
paid API calls and production Memory writes are zero.
