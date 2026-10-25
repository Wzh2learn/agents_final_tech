# Loop A Task: B1 Supervision Qualification

Task ID: `phaseb-b1-supervision-a-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md` at commit
`caa18102bdbbcfe99a889bcf82a125dcc20fdcca`, SHA-256
`c23ec144fe778d1ea8b36ab35def58a13b59d9682f1da4adf6005c2ea378e922`.

Role: A-EXP. File ownership:
`research/feedback_learning_phase_b_20261026_v1/` except `audits/`,
`PHASE_B_BUDGET_LEDGER.json`, `B1_D_FREEZE_GATE.md`, and task cards.

## Allowed Work

1. Read the current authority, Phase A return/recompute, frozen natural task
   and output files, semantic/execution helpers and exposure guard.
2. Build a deterministic supervision qualification dataset from existing
   frozen ordinary outputs. This task does not issue model generation or
   training calls. Deterministic reference editing and execution are allowed.
3. Select natural errors with sufficient visible information. Require at least
   two eligible error types if the evidence supports them. Keep correct/no-op
   and `UNRESOLVED` cases.
4. Define full-program R targets and restricted local-edit E targets from the
   same correction. Implement a deterministic patch schema/applier with
   fail-closed legality checks. Never silently fall back to the reference
   program.
5. Independently verify that applying each E patch to the exact O candidate
   yields the correction target and executes to the verified result. Separate
   strict JSON, embedded JSON, semantic and execution outcomes.
6. Produce source/exposure manifests and an explicit deployment input contract.
   Identify a future same-dataset source-isolated confirmation candidate if
   available; do not claim report/company or cross-dataset independence.
7. Run focused tests and write real command output. Do not train R/E yet.

## Required Outputs

- `B1_CORRECTION_TRAJECTORIES.jsonl`
- `B1_SUPERVISION_MANIFEST.json`
- `B1_LOCAL_PATCH_CONTRACT.json`
- `B1_LOCAL_EDIT_APPLIER.py`
- `B1_TEST_LOCAL_EDIT_APPLIER.py`
- `B1_QUALIFICATION_RECEIPT.json`
- `B1_REPORT.md`
- `B1_PREFLIGHT_DRAFT.json`
- `TASK_RESULT.json`

Every trajectory must record source identity, visible input hash, O output,
error type/evidence, correction target, patch, verification, natural-error
status, exposure role and label/reference identity.

## Stop Conditions

- Stop without fabricating natural errors if fewer than two visible eligible
  error types exist.
- Mark unobservable scale/period cases `UNRESOLVED`.
- Do not call model endpoints, judges, training or production services.
- Do not modify frozen outputs, old scores, raw files or production code.
- If a contract defect cannot be fixed within this task, preserve the failing
  case and report `QUALIFICATION_FAILED` with the smallest next action.

## Return Contract

Final response must be one compact JSON object with keys `status`, `outputs`,
`tests`, `qualification`, `budget`, `risks`, `next_gate`. No prose outside JSON.
