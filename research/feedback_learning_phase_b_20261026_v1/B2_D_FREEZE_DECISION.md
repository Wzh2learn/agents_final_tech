# B2 Development Freeze Decision

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Date: 2026-10-26, Asia/Shanghai
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority commit: `caa18102bdbbcfe99a889bcf82a125dcc20fdcca`

## Gate Status

B1 remediation3 is accepted for B2 development only after the following
explicit D disposition of the sole open C item:

- C task `phaseb-b1-reaudit3b-c-20261026` independently closed H1-a through
  H1-g and H2.
- C verdict remains `CONDITIONAL` only for `R-1`: `B1_REPORT.md` says 26
  deterministic subcases, while `B1_TEST_LOCAL_EDIT_APPLIER.py`,
  `B1_REMEDIATION3_RESULT_A.json`, and `B1_QUALIFICATION_RECEIPT.json` all
  establish 27.
- This is a documentation count mismatch, not a supervision, label, target,
  hash, model, or method defect. D records it here and does not rewrite the
  hash-pinned B1 report. The 27-case ground truth and the two 27-case receipts
  control. No claim or estimand depends on the stale 26.

This disposition satisfies C's permitted alternative: freeze with the
discrepancy recorded explicitly. The earlier `REJECTED` C run is retained only
as `AUDIT_NOT_EXECUTABLE_INPUTS_INACCESSIBLE` interface evidence and is not an
H1/H2 finding.

## Frozen Development Panel

- Artifact: `B2_DEVELOPMENT_PANEL_DRAFT.json`
- SHA-256: `56e3c270a379fab39ed59da5b9b4f1f2f90a03abc41efff86263c2e6259708f0`
- Status: `FROZEN_DEVELOPMENT_ONLY`
- Families: 12
- Trajectories: 36, three repeated-measure variants per family
- Originally-wrong source families: 5
- Originally-correct source families: 7
- Originally-correct family denominator: `7/12`
- Variants within a source family are not independent samples.
- Exposure identity: `EXPOSED_DEVELOPMENT_SUPERVISION`
- Confirmation claim: `NONE`

## Sole Qualified Estimand

`SET_BINDING_SET_ACCURACY` means the predicted candidate uses the correct
visible evidence-cell set while preserving the O candidate's operator, operand
order and unit as deployment contract fields.

It is not answer correctness. No R/E output, target, patch, score or claim may
be evaluated against the frozen reference answer. `target_exact` is structural
identity to the materialized set-binding target only.

The eligible targets execute to the negative reference answer in 3 of 5 rows
across 2 of 3 eligible source families. This is expected from the no-gold
direction rule and is not repaired by inferring reference order.

## R/E Training Contract

- O is the frozen ordinary checkpoint output.
- N is one neutral retry from the same model and visible input.
- R and E continue from the same effective ordinary checkpoint.
- R outputs the complete corrected candidate object, but its supervised change
  is restricted to set binding while operator, order and unit remain fixed to
  O.
- E outputs restricted set-binding replace operations applied by
  `B1_LOCAL_EDIT_APPLIER.py`.
- Both arms receive the same visible task, evidence, O candidate, runtime
  visible reference/unit sets and neutral feedback.
- R/E share eligible tasks, labels, rehearsal, optimizer/update budget and task
  coverage. Target-length and compute differences are recorded, not assumed
  equal.
- Training may edit only `/program/left/ref`, `/program/right/ref`, and
  `/evidence_refs/*`. Operator, const, order/direction and unit are excluded.
- Patch failure is `REJECT_AND_RECORD`; no reference fallback is permitted.
- Correct and no-op cases remain no-op. Unresolved unit and order-only cases
  have no direction/unit training target.
- All current trajectories and panel items are exposed development material.
  The qualified supervision identity is
  `REFERENCE_DERIVED_VISIBLE_SET_BINDING_REVISION_SUPERVISION`, not
  feedback-derived learning.

## Frozen Development Decision Rules

Primary comparisons are E-R and E-N on `SET_BINDING_SET_ACCURACY`, with
source-family clustered paired intervals. Report row-level results but do not
treat 36 rows as 36 independent source samples.

- Minimum useful development effect: E-R at least +5 percentage points and
  E-N at least +3 percentage points.
- E must not reverse direction on either observed eligible subtype.
- On this 12-family development panel, E must add zero newly damaged
  originally-correct families relative to R. Any additional damage stops the
  local-edit candidate from confirmation.
- A point estimate below threshold, or a wide source-cluster interval crossing
  zero, is `INCONCLUSIVE`, not success.
- JSON, syntax-adapter, patch legality, structural target identity, semantic
  acceptance and final delivery are reported separately.
- If development does not pass this gate, B3 confirmation and second-seed
  budgets remain unused.

## Claim Boundary

B2 is same-start method development on exposed data. It cannot establish
feedback-derived learning, new-source generalization, answer correctness,
report/company independence, or a second thesis contribution. Confirmation
requires a separately frozen, pre-generation exposure-clean source panel and an
independent C recomputation before generation.
