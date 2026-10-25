# Revision Operator Diagnostic Return

Date: 2026-10-25, Asia/Shanghai

Status: `PHASE_A_CORRECTED_GOVERNANCE_RETURNED_AWAITING_REVIEW`

## Scientific Judgment

The standardized revision wrapper removes the earlier runaway-instruction
failure: all 20 generated rows stop at EOS, none repeats the terminal
instruction, and actual non-padding lengths are recorded per row. A separate
raw serialization defect remains: copy/no-edit outputs sometimes end with
`")}` instead of `"}`. The previous generic adapter was too broad: it could
turn `1)0` into `10`. The corrected adapter only replaces a terminal
`"...)}` tail and requires strict whole-JSON parsing; embedded JSON is tracked
separately. Raw, strict and adapted results are preserved.

The control gate passes after that common adapter:

| Control | Raw strict JSON | Safe-adapter target exact | Interpretation |
|---|---:|---:|---|
| Correct copy | 0/2 | 2/2 | Stable semantic copy; raw serializer defect |
| Known minimal edit | 2/2 | 2/2 | Model can execute an explicit edit |

The known-edit controls are `DEVELOPMENT_REFERENCE_ASSISTED_NON_DEPLOYABLE`.
They establish a small execution upper bound only; they are not feedback,
confirmation, or deployment evidence.

## Mechanism Comparison

The two development cases do not have equal visible eligibility. The unit
case has no visible `million/thousand` scale in the task input, so its
reference unit cannot be inferred from deployment-visible evidence. The
reference case has visible row and period labels and is the only eligible
visible repair target. Each condition used the same checkpoint, compact
candidate, terminal instruction, greedy decoding and 64-token output limit.

| Condition | Eligible target exact | Ineligible unit cases | Main observation |
|---|---:|---:|---|
| Neutral revision | 0/1 | 1 | Did not correct the visible reference error |
| Category feedback | 0/1 | 1 | Did not correct the visible reference error |
| Visible localization | 0/1 | 1 | Identified visible row/period context but did not convert it into the edit |

The historical numeric 1/2 for each condition is not a repair result: the unit
case remains numerically correct while its unit is unverified, and the
reference case remains wrong. The only eligible target is corrected 0/1 by
neutral, category and localization. This is one development observation, not
a population-level diagnosis-utilization estimate.

## What Changed

- The claim that the current bottleneck is generic output instability is not
  supported for the standardized wrapper. The remaining raw issue is a bounded
  tail-serialization defect handled by a strict, non-semantic adapter.
- The claim that the model cannot execute any revision is excluded on these
  two development cases: it executes both known minimal edits exactly.
- On the single eligible visible error, category/localization do not add
  measurable correction over neutral revision. The unit case is not evidence
  for or against that mechanism because its scale is not visible.
- Student self-repair is not a prerequisite for learning research. A teacher,
  deterministic editor, or training-source reference can provide qualified
  correction targets.

## Evidence Identity

- Data: four exposed development tasks from the V4/V5 panel.
- Purpose: mechanism diagnosis only; no new-family or generalization claim.
- Known-edit controls use hidden development references and are excluded from
  deployment and confirmation results.
- Neutral/category/localization prompts contain no hidden answer or correct
  program.
- `strict_format_valid`, `embedded_format_valid` and adapter actions are
  separate fields; embedded JSON is not treated as strict contract compliance.
- The exposure-union guard runs before generation and records 8/8 selected
  task/table identities as exposed. The same guard hard-blocks overlaps when
  `allow_development_exposure=false`.

## Correction-Supervision Qualification

The next learning study may use two explicit deployment contracts:

1. Direct solver: input is the task prompt; output is the corrected structured
   program. Ordinary same-task answer supervision is the main control.
2. Feedback repairer: input is task prompt plus previous candidate and visible
   feedback; output is the corrected structured program. Neutral revision and
   direct ordinary supervision are controls.

Strong teacher generation, deterministic verified edits, or training-source
references may produce targets. The correction verifier must check execution,
evidence and unit semantics without using hidden confirmation answers for
selection or feedback. Teacher cost, task coverage, label quality and training
tokens must be matched. If the training target is simply repeated gold, name it
answer supervision rather than feedback learning.

## Next Experiment And Separate Budget

The next experiment should train from qualified teacher/tool corrections and
compare O/R/E from the same ordinary checkpoint, then confirm only on sources
that pass the exposure-union guard. This requires a new explicit budget and
must not consume the remaining 32 attempts as a full stage.

See `NEXT_PHASE_BUDGET_REQUEST_V1.json`. The single unified request is 672
generation attempts, 2.8M generation tokens, four training runs and 4.0M
training tokens. The allocation is 96 qualification + 108 development + 288
exposure-clean confirmation + 144 second seed + 36 reserve; previous
allocation variants are superseded and not additive.

## Paper E

Paper E remains a two-case measurement audit and should proceed through the
conditional ICAART primary route or sequential SN Computer Science backup.
The current 12-page package remains mechanically ready. No submission,
payment, signature, public release or presentation commitment was made.
