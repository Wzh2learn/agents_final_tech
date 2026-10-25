# Loop C - B1 Narrow Set-Binding Re-Audit (remediation2)

Task ID: `phaseb-b1-reaudit2-c-20261026`
Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Date: 2026-10-26, Asia/Shanghai
Role: C independent re-audit of the narrowed `VISIBLE_SET_BINDING_REBINDING`
contract and A remediation2 outputs against the C-1 conditions G1/G2/G3 closed by
`B1_A_REMEDIATION2_TASK.md`. Read-only over A-owned artifacts. No A-owned file,
code, label, manifest, trajectory, task card or ledger was modified.
Files written by this task: `audits/B1_C_REAUDIT2.md`,
`audits/TASK_RESULT_C_REAUDIT2.json`.

Labels: **FACT** (first-hand recomputed or read from a frozen artifact),
**INFERENCE** (derived judgment), **VALUE** (threshold/policy call),
**UNVERIFIED** (could not be checked in this execution surface).

---

## 0. Scope and method

Read: `B1_A_REMEDIATION2_TASK.md`, `B1_REMEDIATION2_RESULT_A.json`,
`B1_ERROR_TYPE_TAXONOMY.json`, `B1_SUPERVISION_MANIFEST.json`,
`B1_CORRECTION_TRAJECTORIES.jsonl`, `B1_LOCAL_EDIT_APPLIER.py`,
`B1_LOCAL_PATCH_CONTRACT.json`, `B1_BUILD_SUPERVISION.py`,
`B2_DEVELOPMENT_PANEL_DRAFT.json`, `B1_QUALIFICATION_RECEIPT.json`, `B1_REPORT.md`,
and the prior C re-audit `audits/B1_C_REAUDIT.md`.

Independently rerun, all deterministic and offline:

```
python3 - 72-trajectory recomputation of eligibility, set-binding/direction
           decomposition, patch application, preservation and claim flags
python3 - independent application of materialize_set_binding_target's stated
           rule to each eligible family, compared with the emitted operations
python3 - sha256 of 18 remediation2 outputs and 16 receipt artifacts
python3 - B2 panel selection-rule reproduction from PANEL_SEED + source_task_id,
           plus 36 trajectory_sha256 recomputations
python3 - importlib load of B1_LOCAL_EDIT_APPLIER.py and 8 fail-closed probes
python3 -m unittest B1_TEST_LOCAL_EDIT_APPLIER -v
grep    - report / manifest / taxonomy disclosure scan
```

**Model / judge / training / canary / production / health-probe calls made by C: 0.**
Generation attempts: 0. Training runs: 0.

---

## 1. Set-binding / direction separation (C-1 G3) - CLOSED

### 1.1 The split is present and machine-checkable

- **FACT (recomputed).** All 72 rows carry `schema: b1_correction_trajectory_v3`
  under task_id `phaseb-b1-remediation2-a-20261026`. Every row has a
  `correction.direction_component` and a `correction.set_binding_component`.
- **FACT (recomputed).** Corpus-wide flags:
  `direction_component.training_target` is `False` on **72/72**;
  `direction_component.patch_paths_allowed` is empty on **72/72**;
  `direction_component.reference_direction_inference` is `False` on **72/72**;
  `patch.direction_edited`, `operator_edited`, `unit_edited` and
  `hidden_reference_fallback` are `False` on **72/72**.
- **FACT (recomputed).** All 14 patch operations across the corpus touch only
  `/program/left/ref` (5), `/evidence_refs/0` (5), `/program/right/ref` (2),
  `/evidence_refs/1` (2). **Zero `/unit`, zero `/program/op`, zero const
  operations.**

### 1.2 The direction is genuinely not gold-derived - independently demonstrated

The decisive test is not the declared flags but whether the materialized target
follows the gold operand order. Decomposing the 3 eligible source families:

| family | O candidate | set-binding materialization | frozen reference (audit only) | order vs gold |
|---|---|---|---|---|
| `dac4e923` | `R4:C1 - R4:C2` | `R2:C2 - R4:C2` | `R2:C2 - R4:C2` | **identical** |
| `bdeeb701` | `R4:C1 - R2:C1` | `R3:C1 - R2:C1` | `R2:C1 - R3:C1` | **sign-reversed** |
| `b74eaf04` | `R9:C1 - R9:C2` | `R11:C1 - R11:C2` | `R11:C2 - R11:C1` | **sign-reversed** |

- **FACT (recomputed).** In all 3 families the materialized reference *set* equals
  the frozen reference set exactly. In **2 of 3** the operand *order* is the
  reverse of the gold order. In 1 of 3 (`dac4e923`) it coincides with gold, which
  is the expected coincidence: the candidate's right operand `R4:C2` was already
  a member of the desired set and the preservation rule kept it in its own slot.
- **FACT (recomputed).** `e_patch.target_sha256` hashes the **materialized
  set-binding program**, not the gold program: 5/5 eligible rows match
  `sha256(canonical(set_binding_target))`, and none match
  `sha256(canonical(gold))` except where the two happen to coincide (`dac4e923`,
  2 rows).
- **FACT (code).** `materialize_set_binding_target` derives the desired operand set
  via `refs_in_program(reference_target.program)` - a set of refs only. It never
  reads the reference program's left/right slot assignment. Slot assignment is
  then fixed by a three-step rule on the **candidate skeleton** plus ref column
  identity: (i) keep any candidate ref already in the desired set in its own slot,
  (ii) match remaining desired refs to remaining slots by equal column index when
  unambiguous, (iii) fall back to sorted order. C re-executed this rule independently
  for all three families and reproduced the emitted operations exactly.
- **INFERENCE.** The direction leak identified in the prior re-audit (C-1 G3) is
  **closed at the training-target level**. Had the target been gold-derived, all
  three families would carry gold order and `target_sha256` would equal
  `sha256(canonical(gold))` in every case. The empirical signature is the opposite:
  two of three are sign-reversed relative to gold. The rule consumes the reference
  only as an unordered set, which is what
  `reference_role: REFERENCE_DERIVED_UNORDERED_SET_LABEL` claims.

### 1.3 Direction is out of scope everywhere, not merely undeclared

- **FACT (code + data).** `label_reference_identity.training_reference` and
  `teacher_reference` both carry `direction_action: PRESERVE_O_OR_UNRESOLVED` and
  `direction_training_target: false`. The emitted `minimal_edit_instruction` for
  every eligible row specifies only ref rebinds plus "Do not edit unit"; it contains
  **no** operand-order or sign instruction.
- **FACT (recomputed).** The 6 `OPERAND_ORDER_SIGN_REVERSAL` rows are
  `correction_target_status: SET_PRESERVED_DIRECTION_UNRESOLVED`, carry
  `e_patch: null`, and have `set_binding_component.training_target: false`.
  No patch is fabricated for them.
- **FACT (recomputed).** `verification.semantic.decision` on the 5 eligible rows is
  `SET_BINDING_ACCEPTED_DIRECTION_UNRESOLVED`; `eligible_direction_gold_claim` is
  `False` on 72/72.
- **FACT.** `structural_identity.definition` is "canonical equality to the
  materialized unordered set-binding target while preserving O operator, slot
  skeleton and unit", with `full_reference_target_is_training_target: false` and
  `semantic_gold_equated_by_target_sha256: false` on 72/72.

**Verdict on G3: CLOSED.** The set-binding/direction separation is real, the
direction is frozen to the O candidate and excluded from R/E targets and from the
legal patch surface, and the correction target is no longer a hidden reference for
the sign dimension.


---

## 2. Correct-preservation direction (C-1 G2) - CLOSED

- **FACT (recomputed).** A recursive key scan of the taxonomy, manifest and panel
  for `preserv` / `direction` / `damage` now returns hits in all three, in contrast
  to the 0-hit result recorded in the prior re-audit.
  `registered_mechanism.correct_preservation_direction` is
  `status: PRE_REGISTERED` with preserve list
  `[unchanged_references, operator, order, unit]`, the rule "E must not damage an
  originally correct family ... with a no-op set-binding target", and
  `unit_component_training_target: false` /
  `direction_component_training_target: false`. The same block appears in
  `B1_SUPERVISION_MANIFEST.json` and `B2_DEVELOPMENT_PANEL_DRAFT.json`.
- **FACT (recomputed).** The rule is implemented, not merely declared. The 56
  originally-correct/no-op rows carry `set_binding_component.status:
  PRESERVE_ORIGINAL`, `reference_role: O_CANDIDATE_PRESERVATION`, an empty
  `operations` list, and `desired_reference_set` equal to the candidate's own ref
  set. **0 of 56 violate any of these.**
- **INFERENCE.** G2 is closed. E has a no-op set-binding target on every
  originally-correct family and no legal path by which to damage reference set,
  operator, order or unit.

---

## 3. Mechanism and family counts (C-1 G1) - CLOSED

- **FACT (recomputed).** `B1_ERROR_TYPE_TAXONOMY.json` registers
  `mechanism: VISIBLE_SET_BINDING_REBINDING` with
  `independent_mechanism_count: 1`, `status: ONE_MECHANISM_TWO_OBSERVED_SUBTYPES`,
  `independent_subtype_mechanism_claim: false`, and both registered types carry
  `independent_mechanism: false`.
- **FACT (recomputed).** Counts are reported separately at both granularities and
  match the corpus exactly:

  | subtype | trajectories | source families |
  |---|---|---|
  | `ROW_ROLE_MISBINDING` | 3 | 2 (`b74eaf04`, `bdeeb701`) |
  | `ROW_AND_PERIOD_ROLE_MISBINDING` | 2 | 1 (`dac4e923`) |
  | mechanism total | 5 | 3 |

- **FACT (recomputed).** `B1_ERROR_TYPE_TAXONOMY.json`,
  `B1_SUPERVISION_MANIFEST.json`, `B2_DEVELOPMENT_PANEL_DRAFT.json` and
  `B1_REMEDIATION2_RESULT_A.json` all agree on these numbers. Eligibility counts
  reproduce exactly: `CORRECT_NO_OP` 40, `CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL`
  16, `ELIGIBLE` 5, `UNRESOLVED` 11, total 72.
- **INFERENCE.** G1 is closed. The two types are presented as observed subtypes of
  one visible set-rebinding mechanism, with source-family counts reported alongside
  trajectory counts. The residual "second type rests on a single source family" is
  now disclosed rather than inflated, which is what the condition required.

---

## 4. Patch legality, fail-closed behaviour and hashes - VERIFIED

- **FACT (code).** `ALLOWED_PATHS` is exactly `/program/left/ref` and
  `/program/right/ref`, plus the `/evidence_refs/<n>` regex. `MAX_OPERATIONS = 8`.
- **FACT (independent probe).** C loaded the applier via importlib and ran 8 probes:

  | probe | result |
  |---|---|
  | legitimate set-binding ops (control) | applied |
  | edit `/program/op` | `operation_path_not_allowed` |
  | edit `/program/left/const` | `operation_path_not_allowed` |
  | edit `/unit` | `operation_path_not_allowed` |
  | mixed direction-flip style ops | `patched_program_evidence_refs_mismatch` |
  | non-visible reference value | `operation_value_reference_not_visible` |
  | non-`replace` op | `operation_op_must_be_replace` |
  | duplicate path | `operation_duplicate_path` |

  On the legitimate patch the unit and operator are byte-identical to the
  candidate and `target_sha256` verifies.
- **FACT.** `evaluate_semantic_acceptance` is a separate, working policy function:
  a structurally different but executable candidate with valid evidence/unit/
  role/period semantics returns `ACCEPTED_LEGAL_EQUIVALENCE` with
  `legal_equivalence_accepted: true`; `unit_valid=False` returns
  `REJECTED_OR_UNRESOLVED`.
- **FACT (recomputed).** **18/18** remediation2 output hashes and **16/16**
  `B1_QUALIFICATION_RECEIPT.json` artifact hashes reproduce exactly.
  `archive/B1_REMEDIATION1_RAW_TRAJECTORIES.jsonl` and
  `archive/B1_REMEDIATION1_SCORE_RESULT_A.json` are present and hash as declared;
  the archived score file is byte-identical to the preserved
  `B1_REMEDIATION_RESULT_A.json` (`eae35b9d...`).
- **FACT (rerun).** `python3 -m unittest B1_TEST_LOCAL_EDIT_APPLIER -v` in this
  session: 1 registered test, `REGISTERED_SUBCASES = 26`, result OK, testsRun 1,
  failures 0, errors 0. This reproduces `B1_TEST_OUTPUT.txt` and the receipt.
- **EXCLUDED.** Full repository suite and GB10 runtime were **not** run by C; this
  audit is local and must be labelled local. GB10 remains authoritative. A's own
  full-suite log records one unrelated missing-fixture failure
  (`tests/test_finqa_v2_scorer_runtime_binding_v2.py`) and reports no health or
  model probe; C did not re-run it.
- **EXCLUDED.** No model, judge, training, canary, production or service probe.
  Count of such calls by C: **0**.

---

## 5. Exact 12-family development panel - VERIFIED

- **FACT (independently reproduced).** The declared rule is: include all source
  families whose `original` variant is not program-correct; from the remaining
  families sort by `SHA-256(PANEL_SEED + source_task_id)` and take the first seven,
  with `panel_seed = phaseb-b2-development-panel-v1:20261026:`. Re-executing this
  over the 72 trajectories reproduces the declared 12 families **exactly**
  (declared-only and recomputed-only sets are both empty).
  The 5 originally-wrong families are `04e7f446`, `2e038152`, `819641fb`,
  `b74eaf04`, `dac4e923`. The 7 hash-selected families are `0417ded2`, `223d66c3`,
  `2c20edd3`, `abc6297d`, `bdeeb701`, `f1f2c2cb`, `f440390f`. The rank boundary is
  unambiguous (7th `5ba5b416...`, 8th `679d3073...`).
- **FACT (recomputed).** Family count 12, trajectory count 36, 3 variants per
  family on all 12. Originally-correct family denominator is **7/12** and matches
  the declared fraction. All three eligible source families are inside the panel.
- **FACT (recomputed).** All **36/36** `trajectory_sha256` values reproduce as
  `sha256(canonical_json(trajectory))` keyed by variant. `trajectory_ids` and
  `variants` fields match the corpus. `source_cluster_id` equals `table_uid` on all
  12, consistent with the declared `task_id/question_uid/table_uid` identity
  boundary. `source_population.variant_independence` is
  `REPEATED_MEASURES_WITHIN_SOURCE_FAMILY`.
- **FACT.** Status is `PROPOSED_NOT_FROZEN`, `training_authorized: false`,
  `development_only: true`, `source_role: EXPOSED_DEVELOPMENT_SUPERVISION`,
  `confirmation_claim: NONE`. The panel carries the same
  `correct_preservation_direction` block as the taxonomy and manifest.
- **INFERENCE.** C-6 content requirement is fixed and exactly reproducible. The
  freeze act remains D's and has not occurred; A correctly lists
  `panel_not_frozen` as `BLOCKING_FOR_B2`.


---

## 6. Findings

| ID | Sev | Label | Finding |
|---|---|---|---|
| H1 | **medium** | FACT+INFERENCE+VALUE | The materialized set-binding target executes to the **negative** of the frozen reference answer in 2 of 3 eligible source families (`bdeeb701`: `patched_after` -1715.9 vs expected 1715.9; `b74eaf04`: -78.41 vs 78.41). This is the correct consequence of freezing direction to the O candidate, and it is recorded at trajectory level (`eligible_set_binding_target_answer_claim: false` on 5/5), but it is **not disclosed** in `B1_REPORT.md` or `B1_SUPERVISION_MANIFEST.json` - a scan for `sign`/`revers`/`negat`/`answer_claim` returns 0 substantive hits in the manifest and only the unrelated `OPERAND_ORDER_SIGN_REVERSAL` name in the report. |
| H2 | low | FACT | `unresolved_types.OPERAND_ORDER_SIGN_REVERSAL.reason` still attributes narrowing to "the visible phrase uses unordered 'between A and B' wording". That wording also occurs in two *eligible* families (`dac4e923` "between AMER and EMEA", `b74eaf04` "difference between ... CEO and COO"). The operative discriminator - set-difference present yields an eligible set-binding component, order-only yields nothing that is a training target - is implemented and implied at mechanism level but never stated in the reason text. |
| H3 | low | FACT | G4 residual: `B1_BUILD_SUPERVISION.py` now calls `evaluate_semantic_acceptance(set_binding_target, reference_target, ...)` and records the honest result under `dataset_reference_acceptance`, but the emitted top-level `semantic.legal_equivalence_accepted` is still hardcoded `False`. `ACCEPTED_LEGAL_EQUIVALENCE` remains unrepresentable in that emitted field. |
| H4 | low | FACT | G5 residual: `B1_A_SUPERVISION_QUALIFICATION_TASK.md`, `B1_A_PAPER_AND_THESIS_TASK.md`, `B1_C_PREAUDIT_TASK.md` and `TASK_RESULT_A_PAPER.json` still declare `c23ec144...` under a bare SHA-256 label with no correction pointer. Frozen historical records; the superseding fact lives in `B1_AUTHORITY_BINDING_CORRECTION.json` and the ledger. |
| H5 | low | FACT | G6 residual: `B1_QUALIFICATION_RECEIPT.json` records `budget_ledger_modified: false` while `PHASE_B_BUDGET_LEDGER.json` carries the corrected authority block. The flag should be relabelled. |
| H6 | low | FACT | `scientific_qualification.supervision_mode` is now `REFERENCE_DERIVED_VISIBLE_SET_BINDING_REVISION_SUPERVISION`, a rename of the earlier `REFERENCE_DERIVED_LEGAL_STRUCTURAL_REVISION_SUPERVISION`. Still reference-derived and correctly scoped, but downstream text must use the new string consistently. |

Non-blocking confirmations: G1, G2 and G3 closed; C-2 units closed (17/17
`UNRESOLVED`, zero `/unit` operations, `/unit` unreachable and rejected on probe);
C-3 information parity closed (`allowed_answer_units` empty on 63/72 and
lexical-visible only, `minimal_edit_instruction` null in deployment feedback on
72/72, R/E diffs identical on 72/72); C-5 authority binding correct on all declared
values (commit `caa18102...`, blob `c7053b67...`, size 21673, GB10 LF
`3ed5e1fc...`, 0 carriage returns); C-6 panel exact; all hashes self-consistent;
no red line crossed.

---

## 7. Supervision qualification assessment

- **FACT.** `B1_SUPERVISION_MANIFEST.json` records
  `feedback_learning_status: NOT_QUALIFIED`, `label_roles.confirmation_gold: null`,
  `human_gold: false`, `exposure.selected_source_role:
  EXPOSED_DEVELOPMENT_SUPERVISION`, `exposure.confirmation_claim: NONE`, and
  `exposure.identity_boundary` of `task_id/question_uid/table_uid` only with
  report/company identity unavailable. `B1_REMEDIATION2_RESULT_A.json` lists
  `feedback_learning_claim_not_qualified` as a `CLAIM_LIMIT` and
  `all_sources_exposed` as `BLOCKING_FOR_CONFIRMATION`.
- **INFERENCE.** Reference-derived R/E revision supervision is qualified in the
  narrowed form only:
  - **Qualified:** exposed, same-dataset, table-disjoint **visible set-binding
    reference-rebinding** development supervision over 3 source families / 5
    eligible trajectories, inside a 72-row corpus supplying 56 correct/no-op
    preservation controls and 11 unresolved controls, with a fail-closed
    deterministic applier, an empty R/E feedback-content diff, and direction/unit/
    operator excluded from every training target and every legal patch path.
  - **Not qualified:** unit-field corrections (17/17 `UNRESOLVED`);
    comparison-direction corrections (`OPERAND_ORDER_SIGN_REVERSAL`, 6 rows
    `UNRESOLVED`); the direction component of the eligible targets, which is
    frozen to O and is not a target; **answer correctness of the materialized
    set-binding target**, which is sign-reversed against the reference in 2 of 3
    eligible families (H1); any report/company or cross-dataset independence
    claim; any confirmation claim; and **any feedback-derived learning claim**.
- **VALUE.** C concurs with A's claim discipline and **does not promote** this
  corpus to feedback-derived learning or to confirmation. There is no
  deployment-feedback event anywhere in it; `feedback_derived_fields` is empty by
  construction. The only defensible description remains reference-derived visible
  set-binding revision supervision on exposed development data.


---

## 8. Verdict

# CONDITIONAL

The narrowed contract is sound and the remediation is honest. C-1 G1, G2 and G3
are closed and independently verified: the mechanism is registered as one visible
set-binding family with two observed subtypes and correct family counts; the
pre-registered correct-preservation direction is present and actually implemented
(56/56 no-op preservation rows, zero violations); and the direction leak is
genuinely removed rather than relabelled - the training target hashes to the
materialized set-binding program, which is sign-reversed against gold in 2 of 3
eligible families, and the materializer consumes the reference only as an
unordered set. Patch legality, fail-closed behaviour, all 18 output and 16 receipt
hashes, the focused test suite and the exact 12-family panel with its 7/12
denominator and 36 trajectory hashes all reproduce.

It is **not** ACCEPTED on one disclosure and estimand condition (H1). Closing the
direction leak by freezing direction to the O candidate has a material consequence:
the supervision target no longer produces the reference answer in 2 of 3 eligible
source families. That is the right trade, and it is recorded per trajectory, but it
is absent from `B1_REPORT.md` and `B1_SUPERVISION_MANIFEST.json`. D is about to
freeze B2 estimands against exactly this artifact. If the estimand is answer
correctness, the supervision actively teaches a sign-wrong program in two thirds of
the eligible families and the estimand is silently corrupted; if it is set-binding
set accuracy, the supervision is sound.

Conditions for ACCEPTED, smallest first:

1. **H1.** Disclose in `B1_REPORT.md` and `B1_SUPERVISION_MANIFEST.json` that the
   materialized set-binding target is sign-reversed relative to the frozen
   reference target in `bdeeb701` and `b74eaf04` and therefore does not execute to
   the reference answer, with the per-family numbers. State explicitly that the
   qualified estimand is **set-binding set accuracy** - correct visible cell set
   with operator, order and unit preserved - and not answer correctness. Carry that
   estimand definition into the D freeze gate so B2 cannot score against the
   reference answer.
2. **H2.** Restate the `OPERAND_ORDER_SIGN_REVERSAL` narrowing reason as the rule
   actually applied: a set difference yields an eligible set-binding component; an
   order-only difference leaves no training target and is therefore `UNRESOLVED`.
   Note that "between A and B" wording alone is not the discriminator.

Non-blocking follow-ups for D: H3 (emit the real `legal_equivalence_accepted`, or
delete the hardcoded field and rely on `dataset_reference_acceptance`), H4
(annotate the three task cards and `TASK_RESULT_A_PAPER.json` with a pointer to
`B1_AUTHORITY_BINDING_CORRECTION.json`), H5 (relabel `budget_ledger_modified`),
H6 (keep the renamed `supervision_mode` string consistent downstream).

B2 training remains forbidden while this condition is open. D must also freeze the
proposed 12-family panel before any B2 dispatch.

---

## 9. Claim limit

This audit does **not** promote the result to feedback-derived learning or to
confirmation. The corpus remains reference-derived visible set-binding revision
supervision on exposed development data. Independence is
`task_id/question_uid/table_uid` only; report/company and cross-dataset
independence are unavailable and are not claimed. Confirmation requires a reserved
split and a fresh pre-generation exposure-union recomputation.

---

## 10. Next gate

A discloses H1 and restates H2, then C verifies the disclosure against the
per-family numbers already recomputed here, then D freezes the exact 12-family
panel, the **set-binding** estimands and the 7/12 originally-correct denominator,
then B2 dispatch may be considered. B2 training must not start while H1 is open.

Budget impact of this C task: generation attempts 0, generation tokens 0, training
runs 0, training tokens 0, judge calls 0, canary calls 0, production probes 0,
health probes 0.
