# B1 Remediation Report

Task: `phaseb-b1-remediation3-a-20261026`

## Verdict

A-side remediation3 is `A_REMEDIATION3_COMPLETE_PENDING_C_REAUDIT3`. The
remaining C-1 set-binding, direction and preservation findings are closed in
the A-owned artifacts, and the H1 disclosure and H2 operative-rule defects are
remediated.
B2 training remains blocked until Loop C accepts the re-audit and D freezes the
proposed development panel.

## Authority

The canonical identity is Git commit
`caa18102bdbbcfe99a889bcf82a125dcc20fdcca`, path
`docs/research/LOOP_D_RESEARCH_PROMPT.md`, blob
`c7053b678ce4c67f38656f73932991632107b4fe`, size
`21673` bytes, and GB10 LF SHA-256
`3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7`. The earlier Windows-byte
value is retained only as superseded noncanonical metadata.

## Narrow Set-Binding Mechanism

- One mechanism is registered: `VISIBLE_SET_BINDING_REBINDING`.
- It has two observed subtypes, not two independent mechanisms:
  `ROW_ROLE_MISBINDING` (3
  trajectories / 2
  source families) and `ROW_AND_PERIOD_ROLE_MISBINDING`
  (2
  trajectories / 1
  source families).
- Total mechanism evidence is 5 trajectories from
  3 source families; trajectories and source
  families are counted separately.
- Visible-evidence tests passing: 5/5.
- `OPERAND_ORDER_SIGN_REVERSAL` (6) is narrowed under the operative rule: a
  set difference can yield an eligible set-binding component, while an
  order-only difference has no training target and is `UNRESOLVED`. The phrase
  "between A and B" alone is not the discriminator. Operator and order remain
  frozen to O and are not training targets.
- Natural `program.op` errors: 0; synthetic operator mutations are excluded.
- Unit mismatches: 17 total and
  16 unit-only. Every unit
  correction is `UNRESOLVED`; no R/E target or legal patch edits `/unit`.
- Verification outcomes: 30 `PASS`
  and 42 `UNRESOLVED`;
  19 rows retain unresolved period semantics.

`allowed_answer_units` is derived only by lexical lookup of the visible
deployment prompt. `minimal_edit_instruction` exists only in training and
teacher-reference fields. Deployment feedback is neutral and identical for R
and E in all 72 trajectories (72/72 diffs empty).

## Target Semantics

The sole qualified estimand is `SET_BINDING_SET_ACCURACY`: the prediction has
the correct visible cell set with operator, order and unit preserved. It is
not answer correctness and must never be scored against the reference answer.

Every eligible correction is split into `set_binding_component` and
`direction_component`. R targets and E patches contain only reference-valued
set-binding operations. Operator, subtraction-order direction and unit are not
training targets. `target_exact` is identity to the materialized unordered
set-binding target, never semantic gold. Eligible direction remains unresolved
and is never inferred from gold.

### Materialized Target Sign-Reversal Disclosure

Two of the three eligible source families materialize the reference-derived
cell set with the opposite operand order from the frozen reference target.
Their eligible R/E set-binding targets therefore execute to the negative of the
frozen reference answer and do not execute to that answer. These are disclosed
per family as follows; the frozen reference target remains audit-only.

| Source family | Materialized eligible target form | Frozen reference target form | Count | Execution evidence |
|---|---|---|---|---|
| `NAT_train_bdeeb701_c6f0281e` | `evidence_refs=[R3:C1,R2:C1]`; `R3:C1 - R2:C1`; `unit=million` | `evidence_refs=[R2:C1,R3:C1]`; `R2:C1 - R3:C1`; `unit=million` | 1 sign-reversed eligible row (`relevant_change`) of 3 family trajectories | `patched_after=-1715.9`; reference answer `1715.9` |
| `NAT_train_b74eaf04_caa15292` | `evidence_refs=[R11:C1,R11:C2]`; `R11:C1 - R11:C2`; `unit=reported` | `evidence_refs=[R11:C2,R11:C1]`; `R11:C2 - R11:C1`; `unit=reported` | 2 sign-reversed eligible rows (`original`, `irrelevant_change`) of 3 family trajectories | `patched_after=-78.41`; reference answer `78.41` |

Across all five eligible rows, 3 rows in 2 of 3 eligible source families have
this sign reversal. Consequently these targets are qualified only for
`SET_BINDING_SET_ACCURACY`; they are never qualified evidence for answer
correctness, semantic acceptance or feedback-derived learning.

The pre-registered correct-preservation direction preserves all unchanged
references, operator, order and unit; E must not damage an originally correct
family.

## Development Panel

`B2_DEVELOPMENT_PANEL_DRAFT.json` proposes exactly 12 source families and 36
repeated-measure trajectories. It includes all five originally-wrong families
plus the seven lowest SHA-256-ranked families among the 19 originally-correct
families under the frozen selection seed. The originally-correct family
denominator is exactly **7/12**.
The panel is exposed development data and is not frozen until D acts.

## Exposure And Claim Limit

All 72 rows remain exposed development supervision. No deployment feedback
event exists; the qualified mode is reference-derived visible set-binding
revision supervision, not feedback-derived learning. Report/company
independence is unavailable and is not claimed.

The remediation1 raw trajectory version and score/result version are preserved
under `archive/` with their original SHA-256 values; immutable source raw and
score files were not modified.

## Tests

Fresh command:

`PYTHONPATH=src python3 -m unittest discover -s
research/feedback_learning_phase_b_20261026_v1
-p 'B1_TEST_LOCAL_EDIT_APPLIER.py' -v`

Focused result: `OK`, exit code `0`, one registered test with
26 deterministic subcases.

Previously recorded local full repository result: `FAIL`, exit code
`1` with
967 passed, 1
failed, 14 skipped and
1 deselected. The single failure is an
unrelated missing FinQA fixture; the focused B1 suite passes. The full-suite log
reports no health or model probe. GB10 runtime was not run.

## Next Gate

Loop C must independently re-audit the H1 disclosure, H2 operative rule,
`SET_BINDING_SET_ACCURACY` scope, narrowed mechanism, direction split,
correct-preservation direction, counts, patch legality and hashes. After C
acceptance, D must freeze the exact panel, the sole qualified estimand and
denominators before any B2 dispatch. The retained prior full-suite result is
not a fresh remediation3 test; GB10 runtime remains not run.
