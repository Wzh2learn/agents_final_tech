# GB10 Loop A Implementation Task

Task ID: `gb10-condition-change-feedback-20261020-a2`

Read this contract first; it is the exact acceptance target:

`research/research_direction_sprint_20261020_v1/execution_v2/condition_change_feedback_v1/SPRINT_CONTRACT.md`

Implement only the focused `condition_change_feedback_v1` package. Do not send
model requests or edit frozen FinRank/Paper E artifacts.

Use a declarative policy spec and evidence-fact records so the reference
builder derives answers and minimal sufficient sets. Do not hard-code per-case
gold answers. Keep actor input separate from reference data.

Required outputs:

- frozen policy/case inputs and hash receipt;
- reference builder and strict task/tool schema;
- deterministic baseline and three feedback-contract probe;
- focused tests and machine verification;
- `RETURN.md` summarizing counts, contract dispositions, headroom, and stop
  recommendation.

Write only inside `condition_change_feedback_v1/` plus the unique files
`execution_v2/CONDITION_CHANGE_LOOP_A_RETURN.md` and
`execution_v2/CONDITION_CHANGE_LOOP_A_VERIFICATION.json`. Do not overwrite the
existing `GB10_LOOP_A_RETURN.md` or `GB10_LOOP_A_VERIFICATION.json`. Revise the
partial `IMPLEMENTATION_PLAN.md` to use these unique names before continuing.
Preserve exact commands, Python version, hashes, and zero-request accounting.
