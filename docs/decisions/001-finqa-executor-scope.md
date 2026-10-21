# FinQA Executor Scope After Conditional Qualification

Date: 2026-10-19

## Context

The old FinQA transfer produced `V=89/89, D=0/89, O=0/89` but was accepted as a `MEASUREMENT_OBJECT_MISMATCH`, not a detection result. Loop A built a pinned official-source executor contract to determine whether a future P/N mutation could causally reach the `qa.steps[].res` and `qa.answer` fields consumed by D.

Loop A replayed the terminal `qa.exe_ans` exactly for 7,134/7,134 frozen records and proved P/N propagation on synthetic controls only. Loop C independently found that the hop into rendered `res/answer` fields remains unproven; 5,319 step-value divergences across 4,751 records show that the mapping is not merely unspecified.

## Options

1. Reverse-engineer a `res/answer` renderer from corpus examples and proceed.
2. Keep the full executor contract open and keep searching for an authoritative rendering rule.
3. Qualify a narrow terminal-execution sub-contract, stop the D-field causal route, and move to Candidate B offline qualification.

## Decision

Choose option 3.

- Preserve the full package as `EXECUTOR_FEASIBILITY_CONDITIONAL`.
- Export the supported scope as `TERMINAL_EXECUTION_ONLY`: official raw-operator execution and exact `qa.exe_ans` replay.
- Do not claim mutation propagation into D-consumed `res/answer` fields.
- Do not run the causal-exposure experiment.
- Move the next research loop to Candidate B: source/exposure/reference qualification for evidence binding before calculation.

## Why

Corpus fitting would turn an unverified semantic contract into a measurement artifact. Searching indefinitely for a renderer would delay a decision without new evidence. The terminal-only sub-contract is already independently reviewable and useful as a boundary result; Candidate B has a real action position, explicit controls and a clean stop path.

## Consequences

Easy:

- A qualified terminal-execution boundary can be reported without overclaiming D-field propagation.
- The next work package is bounded to offline task/reference qualification and remains stoppable before model use.

Hard:

- The stronger FinQA causal-exposure route remains blocked unless an authoritative `res/answer` rendering contract is later supplied.
- Existing 12 calculation histories remain only partially relevant to Candidate B and may require a new task-matched collection.
