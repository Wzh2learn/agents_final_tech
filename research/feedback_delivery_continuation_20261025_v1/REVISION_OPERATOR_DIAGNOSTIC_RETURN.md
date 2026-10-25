# Revision Operator Diagnostic Return

Date: 2026-10-25, Asia/Shanghai

Status: `CONTROL_QUALIFIED_FEEDBACK_NO_INCREMENT_TEACHING_STILL_OPEN`

## Scientific Judgment

The standardized revision wrapper removes the earlier runaway-instruction
failure: all 20 generated rows stop at EOS, none repeats the terminal
instruction, and actual non-padding lengths are recorded per row. A separate
raw serialization defect remains: copy/no-edit outputs sometimes end with
`")}` instead of `"}`. A common syntax adapter removes exactly one unmatched
close parenthesis only after strict parsing fails. Raw and adapted results are
reported separately.

The control gate passes after that common adapter:

| Control | Raw JSON valid | Adapted target exact | Interpretation |
|---|---:|---:|---|
| Correct copy | 0/2 | 2/2 | Stable semantic copy; raw serializer defect |
| Known minimal edit | 2/2 | 2/2 | Model can execute an explicit edit |

The known-edit controls are `DEVELOPMENT_REFERENCE_ASSISTED_NON_DEPLOYABLE`.
They establish a small execution upper bound only; they are not feedback,
confirmation, or deployment evidence.

## Mechanism Comparison

The two development error cases are: a wrong unit field, and a wrong first
evidence binding with a coordinated reference edit. Each condition used the
same checkpoint, compact candidate, terminal instruction, greedy decoding and
64-token output limit.

| Condition | Target exact | Numeric correct | Main observation |
|---|---:|---:|---|
| Neutral revision | 0/2 | 1/2 | Did not change the intended field |
| Category feedback | 0/2 | 1/2 | Did not change the intended field |
| Visible localization | 0/2 | 1/2 | Identified row/period or unit context but did not convert it into the edit |

The numeric 1/2 is not a successful repair: the unit case remains numerically
correct while retaining the wrong unit, and the reference case remains wrong.
Neutral, category and localization are tied at 0/2 target-exact correction.

## What Changed

- The claim that the current bottleneck is generic output instability is no
  longer supported for the standardized wrapper. The remaining raw issue is a
  bounded one-character serialization defect handled uniformly.
- The claim that the model cannot execute any revision is excluded on these
  two development cases: it executes both known minimal edits exactly.
- The current visible category/localization prompts do not add measurable
  correction over neutral revision. This is consistent with a
  diagnosis-to-edit utilization gap, but the two-task panel cannot separate
  feedback granularity from learned revision policy.
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

See `NEXT_PHASE_BUDGET_REQUEST_V1.json`. The requested increment is 672
generation attempts, 2.8M generation tokens, four training runs and 4.0M
training tokens. Each block states the question it resolves.

## Paper E

Paper E remains a two-case measurement audit and should proceed through the
conditional ICAART primary route or sequential SN Computer Science backup.
The current 12-page package remains mechanically ready. No submission,
payment, signature, public release or presentation commitment was made.
