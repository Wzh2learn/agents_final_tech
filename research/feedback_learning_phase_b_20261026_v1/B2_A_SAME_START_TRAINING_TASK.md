# Loop A Task: B2 Same-Start R/E Development

Task ID: `phaseb-b2-same-start-a-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Prerequisites: `B2_D_FREEZE_DECISION.md` is the D gate. It records C's H1/H2
acceptance and explicitly disposes of the non-substantive 26-versus-27 report
count discrepancy without rewriting hash-pinned B1 evidence. The qualified
identity is reference-derived revision supervision, not feedback-derived
learning.

Role: A-EXP. File ownership:
`research/feedback_learning_phase_b_20261026_v1/b2/`.

## Scientific Contract

- O is the frozen ordinary checkpoint output; N is one neutral retry.
- R and E continue from the same effective ordinary checkpoint, not base.
- R outputs a full corrected program; E outputs a restricted patch applied by
  the deterministic applier. Both receive the same task, visible evidence, O
  candidate and allowed feedback.
- The sole primary estimand is `SET_BINDING_SET_ACCURACY`; never score target
  or answer correctness against the frozen reference answer.
- R/E share eligible tasks, labels, rehearsal, optimizer steps, update budget
  and task coverage. Record target token/length differences rather than
  claiming perfect compute equality.
- Include deterministic repair and ordinary supervision controls.
- No hidden confirmation reference in training inputs, feedback or selection.

## Required Evidence

1. Adapter identity, parent hash, trainable parameters, masks, optimizer,
   steps, loss normalization and GPU/token cost.
2. Frozen development panel and source-family paired metrics:
   `SET_BINDING_SET_ACCURACY`, O error repair, O correct damage, wrong delivery,
   UNKNOWN, coverage, and separate structural/semantic diagnostics with total
   cost.
3. Strict whole-JSON, embedded JSON, syntax-adapter and semantic/execution
   outcomes remain separate.
4. Use `B1_D_FREEZE_GATE.md` thresholds unchanged. Do not inspect confirmation
   outputs while tuning.
5. Save raw generations, partial failures and training logs. Do not modify
   frozen prior results.

## Outputs

- `b2/B2_PROTOCOL_FROZEN.json`
- `b2/B2_TRAINING_RECEIPT_R.json`
- `b2/B2_TRAINING_RECEIPT_E.json`
- `b2/B2_DEVELOPMENT_RAW.jsonl`
- `b2/B2_DEVELOPMENT_ANALYSIS.json`
- `b2/B2_PREFLIGHT_RECEIPT.json`
- `b2/TASK_RESULT_A_B2.json`

## Stop Conditions

Stop before training if B1/C has unresolved critical defects, the parent
adapter cannot be loaded, GPU/lock conditions cannot be met, or the R/E
information contracts are not matched. Do not use more than the authorized
B2 development budget.
