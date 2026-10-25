# Loop C - B1 Remediation Re-Audit

Task ID: `phaseb-b1-reaudit-c-20261026`
Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Date: 2026-10-26, Asia/Shanghai
Role: C independent re-audit of A remediation against `B1_D_REMEDIATION_GATE.md`.
Read-only over the frozen first C audit, A remediation outputs and raw derivatives.
No A-owned file, code, label, manifest, trajectory, task card or ledger was modified.
Files written by this task: `audits/B1_C_REAUDIT.md`, `audits/TASK_RESULT_C_REAUDIT.json`.

Labels: **FACT** (first-hand recomputed or read from a frozen artifact),
**INFERENCE** (derived judgment), **VALUE** (threshold/policy call),
**UNVERIFIED** (could not be checked in this execution surface).

---

## 0. Scope and method

Read: the frozen first C audit (`audits/B1_C_PREAUDIT.md`, `audits/TASK_RESULT_C.json`),
D gate (`B1_D_REMEDIATION_GATE.md`), A remediation task and all A-owned outputs and
the raw derivatives the first audit indexed.

Independently rerun, all deterministic and offline:

```
git rev-parse HEAD / git cat-file -t|-s|blob <pin>:docs/research/LOOP_D_RESEARCH_PROMPT.md
sha256sum of the pinned blob (raw and CR-stripped) and of the worktree file
sha256sum of all 13 receipt artifacts and all 14 remediation outputs
python3 -c 72-trajectory recomputation of eligibility, unit, patch, parity, verification
python3 -c question-text and operand decomposition of every natural-error row
python3 -c B2 panel selection-rule reproduction from PANEL_SEED + source_task_id
python3 -c unittest run of B1_TEST_LOCAL_EDIT_APPLIER.py via importlib
```

**Model / judge / training / canary / production / health-probe calls made by C: 0.**
Generation attempts: 0. Training runs: 0.

---

## 1. Independent recomputation of the B1 corpus

- **FACT.** `B1_CORRECTION_TRAJECTORIES.jsonl` holds exactly **72** rows, schema
  `b1_correction_trajectory_v2`, all under task_id
  `phaseb-b1-remediation-a-20261026`. 24 source families x 3 variants
  (`original`, `irrelevant_change`, `relevant_change`).
- **FACT.** Variants are model re-executions on a perturbed table cell, not label
  corruption: for `bdeeb701` the `relevant_change` variant changes R2:C1 from
  $2,059 to 2264.9 and the O candidate changes from `R2:C1-R3:C1` to
  `R4:C1-R2:C1`, while the reference target is byte-identical across all three
  variants. The errors are naturally produced by O on a different input.
- **FACT (recomputed).** Eligibility counts match A manifest exactly:
  `CORRECT_NO_OP` 40, `CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL` 16,
  `ELIGIBLE` 5, `UNRESOLVED` 11, total 72.
- **FACT (recomputed).** `unit_field_status`: 17 `UNRESOLVED`, 55
  `NOT_DIFFERENT_FROM_CANDIDATE`. `program.op` mismatches between candidate and
  reference target across all 72 rows: **0**.
- **FACT (recomputed).** Patch operations across the whole corpus: **16** total -
  `/program/left/ref` 5, `/evidence_refs/0` 5, `/program/right/ref` 3,
  `/evidence_refs/1` 3. **Zero `/unit` operations.**
- **FACT.** All 13 artifact hashes in `B1_QUALIFICATION_RECEIPT.json` and all 14
  output hashes in `B1_REMEDIATION_RESULT_A.json` reproduce exactly. Receipt is
  self-consistent; nothing is stale.

---
## 2. C-1 taxonomy - CONDITIONAL (open)

### 2.1 What A actually delivered

- **FACT.** `B1_ERROR_TYPE_TAXONOMY.json` registers two types with distinct
  visible-evidence sufficiency tests and named frozen correction operators:
  `ROW_ROLE_MISBINDING` / `VISIBLE_ROW_ROLE_REF_REBIND` (3 trajectories) and
  `ROW_AND_PERIOD_ROLE_MISBINDING` / `VISIBLE_ROW_AND_PERIOD_REF_REBIND`
  (2 trajectories). Both have `unit_edits_allowed: false` and identical legal
  paths: `/program/left/ref`, `/program/right/ref`, `/evidence_refs/<index>`.
- **FACT.** Per-trajectory `visible_evidence_test` is present and `PASS` on 5/5
  eligible rows, with `hidden_reference_used_by_test: false`,
  `structural_only_difference: true`, `operator_shape_test: true`, and
  `required_visible_tokens` checked against the question
  (`tokens_present_in_question: true` on 5/5).
- **FACT.** `explicitly_absent_types` records `WRONG_OPERATOR` with
  `natural_occurrence_count: 0`; the manifest carries
  `natural_wrong_operator_count: 0`. Synthetic operator mutations are excluded.
- **FACT (no fabrication).** Five further types are narrowed to `UNRESOLVED` with
  reasons rather than invented: `OPERAND_ORDER_SIGN_REVERSAL` (6 rows, reason
  `COMPARISON_DIRECTION_NOT_VISIBLE`), `TOTAL_ROW_LABEL_NOT_VISIBLE` (2),
  `TOTAL_ROW_AND_PERIOD_LABELS_NOT_VISIBLE` (1), `PERIOD_HEADER_NOT_VISIBLE` (1),
  `UNIT_SCALE_NOT_VISIBLE` (1). Every `OPERAND_ORDER_SIGN_REVERSAL` row has
  `e_patch: null` - no patch is fabricated for an unresolved case.

**INFERENCE.** On the letter of D C-1 (define visible-evidence sufficiency and a
frozen correction operator for each natural error type; demonstrate at least two
types pass) A satisfies the wording. On the substance of
`B1_D_FREEZE_GATE.md` Supervision Gate item 1 (at least two naturally occurring
eligible error types with visible evidence) three gaps remain.

### 2.2 Gap A - the second type rests on one source family

- **FACT (recomputed).** The 5 ELIGIBLE trajectories come from **3 source
  families**, not 5 independent units:

  | source family | variants | type |
  |---|---|---|
  | `NAT_train_dac4e923_dccd9dbf` | original, irrelevant_change | `ROW_AND_PERIOD_ROLE_MISBINDING` |
  | `NAT_train_b74eaf04_caa15292` | original, irrelevant_change | `ROW_ROLE_MISBINDING` |
  | `NAT_train_bdeeb701_c6f0281e` | relevant_change | `ROW_ROLE_MISBINDING` |

- **FACT.** `B1_D_FREEZE_GATE.md` states: variants from one source family are
  repeated measures, not independent samples.
- **INFERENCE.** `ROW_AND_PERIOD_ROLE_MISBINDING` is evidenced by exactly **one**
  source family (`dac4e923`). Under the frozen independence rule the second
  registered type has n = 1 independent unit. The two types are also the same
  `program.*.ref` set-rebinding signature split only by whether a period token is
  additionally requested; their correction operators share identical legal paths and
  near-identical mechanism text (visible requested row/role binding versus visible
  requested row-and-period binding).

### 2.3 Gap B - pre-registered correct-preservation direction is absent

- **FACT.** The first C audit F1 VALUE note pre-registered three items for this
  split: (i) a per-type visible-evidence sufficiency test, (ii) a **per-type
  correct-preservation direction**, (iii) an explicit statement that `program.op`
  errors do not occur.
- **FACT (recomputed).** (i) is present, (iii) is present. For (ii) a recursive key
  search over `B1_ERROR_TYPE_TAXONOMY.json`, `B1_SUPERVISION_MANIFEST.json` and
  `B2_DEVELOPMENT_PANEL_DRAFT.json` for any key containing `preserv`, `direction`
  or `damage` returns **0 hits**. The registered types carry no
  correct-preservation direction.
- **INFERENCE.** Requirement (ii) of the pre-registration is unmet.

---
### 2.4 Gap C - the correction target carries a reference-derived direction (new)

- **FACT (recomputed).** Decomposing every natural-error row into *cell set* and
  *operand order*: the two families narrowed as `OPERAND_ORDER_SIGN_REVERSAL`
  (`04e7f446`, `819641fb`) have an **identical** cell set in candidate and target
  and differ **only** in operand order. The three ELIGIBLE families have a
  **different** cell set. That set difference is what A rule is actually keying on,
  and it is coherent.
- **FACT (recomputed from the rendered prompts).** The stated rationale for the
  narrowing is that the visible phrase uses unordered between-A-and-B wording and
  the subtraction direction is not uniquely derivable without the reference. The
  question wording of the eligible rows is materially the same:

  | family | question | candidate to target | direction versus mention order |
  |---|---|---|---|
  | `04e7f446` UNRESOLVED | What is the **difference in** debt instruments **between** 2018 **and** 2019? | `R3:C1-R3:C2` to `R3:C2-R3:C1` | target follows mention order |
  | `819641fb` UNRESOLVED | What was the **change in** operating profit **between** the third **and** fourth quarter? | `R5:C3-R5:C4` to `R5:C4-R5:C3` | target reverses mention order |
  | `dac4e923` ELIGIBLE | What was the **difference in** net sales in 2018 **between** AMER **and** EMEA regions? | `R4:C1-R4:C2` to `R2:C2-R4:C2` | target follows mention order |
  | `b74eaf04` ELIGIBLE | What is **difference between** the value of Others, Allowances of the CEO **and** COO? | `R9:C1-R9:C2` to `R11:C2-R11:C1` | **target reverses mention order** (COO minus CEO) |
  | `bdeeb701` ELIGIBLE | What is the **difference in** ... **for** Consumer Cyber Safety **and** Enterprise Security? | `R4:C1-R2:C1` to `R2:C1-R3:C1` | **target reverses mention order** (Enterprise minus Consumer) |

- **FACT.** The visible-evidence sufficiency test asserts only that role/period
  *tokens* appear in the question (`required_visible_tokens`,
  `tokens_present_in_question`). It performs **no** test that the subtraction
  direction of the correction target is derivable from visible input.
- **INFERENCE.** In 2 of the 3 eligible families the frozen `correction_target` /
  `r_target` asserts a subtraction direction that the question unordered
  difference-between-A-and-B wording does not determine - the same undecidability A
  used to declare `OPERAND_ORDER_SIGN_REVERSAL` `UNRESOLVED`. To reach
  `target_exact`, E must reproduce a direction that is reference-derived, not
  visible. This is the hidden-reference class C-2/C-3 were meant to close, surviving
  in the sign/direction dimension.
- **VALUE.** The set-binding component of these three families is genuinely
  visible-derivable and should remain eligible. The direction component should be
  split out and either (a) frozen as a separate, explicitly reference-derived
  convention (documented as such, excluded from any visible-evidence claim), or
  (b) marked `UNRESOLVED` with the correction target reduced to an unordered cell
  set. The current sufficiency test cannot support the claim it is used for.

**Verdict on C-1: CONDITIONAL - open.** No fabrication occurred and the narrowing
is honest, but the two-type demonstration rests on 3 source families with the second
type at n = 1, the pre-registered correct-preservation direction is missing, and the
correction targets embed an under-tested reference-derived direction.

---

## 3. C-2 units - CLOSED

- **FACT (recomputed).** 17 of 72 rows have a unit-field mismatch
  (`unit_field_status: UNRESOLVED`); 16 of those are unit-only
  (`program_correct: true`). All 17 carry
  `correction_target_unit_action: PRESERVE_CANDIDATE` and
  `unit_correction_status: UNRESOLVED`. Candidate unit equals patched unit in
  every case.
- **FACT (recomputed).** Zero `/unit` operations in any of the 16 patch operations.
  `B1_LOCAL_PATCH_CONTRACT.json` lists `/unit` under `forbidden_paths` and omits
  it from `allowed_paths`.
- **FACT (code).** `B1_LOCAL_EDIT_APPLIER.py` `ALLOWED_PATHS` covers
  `/program/op`, `/program/left/ref`, `/program/left/const`,
  `/program/right/ref`, `/program/right/const` plus `/evidence_refs/<index>`;
  `/unit` is not reachable. `apply_patch` raises `candidate_unit_mutated` if the
  unit changes.
- **FACT (test).** `_all_unit_mismatches_are_unresolved_and_no_patch_edits_unit`
  and `_unit_path_is_forbidden_even_when_lexically_visible` assert exactly this.

**INFERENCE.** C-2 is satisfied. Unit targets are excluded from R/E supervision and
from the patch schema legal edit targets.

---
## 4. C-3 information parity - CLOSED

- **FACT (recomputed).** `allowed_answer_units` is empty in **63/72** rows. The 9
  non-empty rows carry only `reported` (`c5b624e7`, `223d66c3`) or `percent`
  (`bdeeb701`); each string was verified to occur literally in that row rendered
  prompt. The rule field is identical on 72/72 rows: lexical unit-vocabulary strings
  literally present in the deployment prompt, no gold-scale inference.
  `contains_hidden_scale_claim` is `False` on 72/72.
- **FACT (recomputed).** `minimal_edit_instruction` holds non-null content (edit
  path **and** correct value) in `training_reference` (72 rows) and
  `teacher_reference` (72 rows) only. In `deployment_feedback` it is **null on
  72/72 rows**. The deployment feedback payload is the neutral instruction
  Revise the candidate using only the visible question and table; do not use hidden
  references, gold programs, or development edit instructions, with
  `reference_program_input: false`.
- **FACT (recomputed).** `r_e_feedback_content_diff` is present on every trajectory
  with `differences: []`, `identical: true`,
  `minimal_edit_instruction_in_deployment_feedback: false`; the R and E instruction
  strings are byte-identical.
- **FACT (code).** `apply_patch` accepts `allowed_evidence_refs` only and rejects
  any reference outside that set (`operation_value_reference_not_visible`,
  `patched_evidence_reference_not_visible`). Since `/unit` is unreachable,
  `allowed_answer_units` cannot reintroduce `expected.unit` as a legal edit target.

**INFERENCE.** C-3 is satisfied. `allowed_answer_units` is visibility-honest and
empty where nothing is visible; `minimal_edit_instruction` is confined to
training/teacher reference fields; the R-versus-E feedback-content diff is recorded
per trajectory and is empty by construction.

---

## 5. C-4 equivalence - CLOSED, one residual

- **FACT (code).** `evaluate_semantic_acceptance` is a separate function from
  structural identity. It takes `execution_equal`, `visible_evidence_valid`,
  `unit_valid`, `role_period_valid` and returns `ACCEPTED_STRUCTURAL_EXACT` or
  `ACCEPTED_LEGAL_EQUIVALENCE` with `legal_equivalence_accepted` set accordingly.
- **FACT (test).** `_semantic_acceptance_allows_executable_legal_equivalence`
  constructs a structurally different but semantically valid candidate and asserts
  `decision == ACCEPTED_LEGAL_EQUIVALENCE` and
  `legal_equivalence_accepted is True`, and that `unit_valid=False` rejects.
- **FACT (recomputed).** Trajectory field `verification.structural_identity` carries
  `definition: canonical equality to the legal structural target` and
  `semantic_gold_equated_by_target_sha256: false` on 72/72 rows. `target_exact` is
  therefore structural identity, not semantic gold.
- **FACT (residual).** `B1_BUILD_SUPERVISION.py` calls
  `evaluate_semantic_acceptance(legal_target, legal_target, ...)` - the legal target
  against itself - and then emits a **hardcoded**
  `decision = ACCEPTED_STRUCTURAL_EXACT if overall is PASS else UNRESOLVED` and
  `legal_equivalence_accepted = False`. Recomputed over the corpus:
  `legal_equivalence_accepted` is `False` on 72/72; `decision` is only
  `ACCEPTED_STRUCTURAL_EXACT` (30) or `UNRESOLVED` (42). No trajectory can ever
  record `ACCEPTED_LEGAL_EQUIVALENCE`.
- **INFERENCE.** The separation required by C-4 is real and tested at the policy
  level. The residual is that the emitted supervision cannot express legal
  equivalence, and the call site is self-referential. This is harmless for the
  present corpus (no row has a legally-equivalent-but-structurally-different
  candidate) but B2 must compute semantic acceptance on actual candidate outputs via
  `evaluate_semantic_acceptance`, not read the emitted constant. Non-blocking.

---

## 6. C-5 authority binding - CLOSED, one residual

- **FACT (independently re-derived).** `git rev-parse HEAD` =
  `caa18102bdbbcfe99a889bcf82a125dcc20fdcca`. Blob at that commit for
  `docs/research/LOOP_D_RESEARCH_PROMPT.md` =
  `c7053b678ce4c67f38656f73932991632107b4fe`, size **21673** bytes. SHA-256 of the
  raw blob = `3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7`.
  Carriage returns in the blob: **0**, so the CR-stripped digest is identical. The
  worktree file hashes to the same value. All four declared values in
  `B1_AUTHORITY_BINDING_CORRECTION.json` and `B1_SUPERVISION_MANIFEST.json` are
  correct.
- **FACT.** `PHASE_B_BUDGET_LEDGER.json` now carries
  `gb10_lf_sha256: 3ed5e1fc...` and
  `windows_raw_sha256_noncanonical: c23ec144...`. The correction is recorded as
  required by D C-5 wording.
- **FACT (residual).** Three historical task cards still declare
  `c23ec144...` under the bare label SHA-256 with no inline correction pointer:
  `B1_A_SUPERVISION_QUALIFICATION_TASK.md`, `B1_A_PAPER_AND_THESIS_TASK.md`,
  `B1_C_PREAUDIT_TASK.md`. `TASK_RESULT_A_PAPER.json` also still carries
  `required_sha256: c23ec144...`. These are frozen historical records; the
  superseding fact is now in `B1_AUTHORITY_BINDING_CORRECTION.json` and the ledger.
- **FACT (receipt accuracy).** `B1_QUALIFICATION_RECEIPT.json` and
  `B1_REMEDIATION_RESULT_A.json` record `budget_ledger_modified: false`, yet the
  ledger authority block contains the corrected digest. Either the flag means budget
  numbers unmodified or it is inaccurate; it should be relabelled.
- **INFERENCE.** C-5 is satisfied in substance. D should annotate the three cards
  and `TASK_RESULT_A_PAPER.json` with a pointer to the correction artifact rather
  than rewrite them, and clarify the ledger flag.

---
## 7. C-6 damage panel - CLOSED on A side; D freeze still outstanding

- **FACT (independently reproduced).** `B2_DEVELOPMENT_PANEL_DRAFT.json` declares
  `panel_seed = phaseb-b2-development-panel-v1:20261026:` and the rule include all
  five source families whose original variant is not program-correct; from the 19
  originally-correct families, sort by SHA-256 of PANEL_SEED plus source_task_id and
  include the first seven. Re-executing that rule over the 72 trajectories
  reproduces the declared 7 families **exactly**:
  `0417ded2`, `223d66c3`, `2c20edd3`, `abc6297d`, `bdeeb701`, `f1f2c2cb`,
  `f440390f`. The 5 originally-wrong set also matches exactly.
- **FACT (recomputed).** Originally-correct family denominator is **7/12**, matching
  the declaration. Family count 12, trajectory count 36.
- **FACT.** `source_cluster_id` equals `table_uid` on all 12 families, consistent
  with the declared identity boundary (`task_id/question_uid/table_uid` only).
  `source_population.variant_independence` is
  `REPEATED_MEASURES_WITHIN_SOURCE_FAMILY`, satisfying the variants remain repeated
  measures requirement.
- **FACT (recomputed).** All 36 `trajectory_sha256` values reproduce as the
  canonical JSON of the corresponding trajectory rows. The panel is fully
  reproducible from the corpus.
- **FACT.** Status is `PROPOSED_NOT_FROZEN` and `training_authorized: false`. All
  three ELIGIBLE source families are inside the panel.
- **INFERENCE.** C-6 content requirement - exact development family IDs, source
  cluster identity and the originally-correct family denominator - is now fixed,
  reproducible and correct. The gate before-B2 step is D act of freezing and has not
  occurred; A correctly lists `panel_not_frozen` as a `BLOCKING_FOR_B2` risk.
  This is not an A-side defect.

---

## 8. Deterministic checks rerun

- **FACT.** `B1_TEST_LOCAL_EDIT_APPLIER.py` re-executed in this session: **1**
  registered test, `REGISTERED_SUBCASES = 23`, result OK, testsRun 1, failures 0,
  errors 0, wall 0.029s. This reproduces `B1_TEST_OUTPUT.txt` and the receipt
  recorded output exactly.
- **FACT.** Coverage confirmed by reading the suite: unit immutability and forbidden
  `/unit` path; lexical-visible-only `allowed_answer_units`; reference-only
  `minimal_edit_instruction`; R/E arm input equality;
  `ACCEPTED_LEGAL_EQUIVALENCE` on a structurally different candidate; the 12-family
  panel and 7/12 denominator; taxonomy counts and `OPERAND_ORDER_SIGN_REVERSAL`
  unresolved status; and 8 distinct `PatchError` fail-closed paths including
  `candidate_sha256_mismatch`, `target_sha256_mismatch`,
  `operation_path_not_allowed`, `operation_expected_value_mismatch`,
  `operation_value_reference_not_visible`, `operation_duplicate_path`,
  `patch_keys_mismatch`, `candidate_unit_must_be_string`.
- **FACT.** 13/13 receipt artifact hashes and 14/14 remediation output hashes match.
- **EXCLUDED.** Full repository suite and GB10 runtime were **not** run; this audit
  is local and must be labelled local. GB10 remains authoritative.
- **EXCLUDED.** No model, judge, training, canary, production or service probe.
  Count of such calls by C: **0**.

---

## 9. Findings

| ID | Sev | Label | Finding |
|---|---|---|---|
| G1 | **blocking** | FACT+INFERENCE | C-1 open: the two registered types are subtypes of one `program.*.ref` set-rebinding signature; `ROW_AND_PERIOD_ROLE_MISBINDING` rests on a single source family (`dac4e923`), so under the frozen repeated-measures rule the second type has n = 1 independent unit. |
| G2 | **blocking** | FACT | C-1 open: the pre-registered per-type **correct-preservation direction** (first audit F1 VALUE item ii) is absent - 0 keys matching `preserv`/`direction`/`damage` in taxonomy, manifest or panel. |
| G3 | **blocking** | FACT+INFERENCE | C-1 open: the visible-evidence sufficiency test checks role/period token presence but not subtraction-direction derivability. In `b74eaf04` and `bdeeb701` the frozen correction target reverses the question mention order, so E must reproduce a reference-derived direction to hit `target_exact` - the same undecidability used to narrow `OPERAND_ORDER_SIGN_REVERSAL` to `UNRESOLVED`. |
| G4 | medium | FACT | C-4 residual: `evaluate_semantic_acceptance` is called as `(legal_target, legal_target)` and the emitted `legal_equivalence_accepted` is hardcoded `False` on 72/72; `ACCEPTED_LEGAL_EQUIVALENCE` is unrepresentable in the emitted supervision. |
| G5 | low | FACT | C-5 residual: `B1_A_SUPERVISION_QUALIFICATION_TASK.md`, `B1_A_PAPER_AND_THESIS_TASK.md`, `B1_C_PREAUDIT_TASK.md` and `TASK_RESULT_A_PAPER.json` still declare `c23ec144...` as SHA-256 with no correction pointer. |
| G6 | low | FACT | Receipt field `budget_ledger_modified: false` conflicts with the corrected authority block now present in `PHASE_B_BUDGET_LEDGER.json`. |
| G7 | low | FACT | Eligible error evidence is 5 trajectories over **3** source families; any per-type count must state both numbers to avoid inflating the independent sample. |

Non-blocking confirmations: C-2 closed; C-3 closed; C-6 content fixed and exactly
reproducible; all artifact hashes self-consistent; no red line crossed; the
reference-derived / feedback-derived split is correctly labelled and not overstated.

---
## 10. Supervision qualification assessment

- **FACT.** `B1_SUPERVISION_MANIFEST.json` records
  `supervision_mode: REFERENCE_DERIVED_LEGAL_STRUCTURAL_REVISION_SUPERVISION`,
  `feedback_learning_status: NOT_QUALIFIED`, `feedback_derived_fields: []`,
  `label_roles.confirmation_gold: null`, `human_gold: false`, and
  `exposure.selected_source_role: EXPOSED_DEVELOPMENT_SUPERVISION` with
  `confirmation_claim: NONE`. `B1_REMEDIATION_RESULT_A.json` lists
  `feedback_learning_claim_not_qualified` as a `CLAIM_LIMIT`.
- **INFERENCE.** Reference-derived R/E revision supervision **is qualified in a
  narrowed form only**:
  - **Qualified:** exposed, same-dataset, table-disjoint development supervision for
    *row/role/period set rebinding*, over 3 source families / 5 eligible
    trajectories, inside a 72-row corpus that also supplies 40 correct/no-op and 16
    label-unresolved controls, with a fail-closed deterministic applier and an empty
    R/E feedback-content diff.
  - **Not qualified:** unit-field corrections (17/17 `UNRESOLVED`);
    comparison-direction corrections (`OPERAND_ORDER_SIGN_REVERSAL`, 6 rows
    `UNRESOLVED`, plus the direction component of the eligible targets per G3);
    any report/company or cross-dataset independence claim (boundary is
    `task_id/question_uid/table_uid` only); any confirmation claim; and **any
    feedback-derived learning claim**.
- **VALUE.** C concurs with A labelling and **does not promote** this corpus to
  feedback-derived learning. There is no deployment-feedback event anywhere in it;
  `feedback_derived_fields` is empty by construction. The only defensible
  description is reference-derived legal structural revision supervision on exposed
  development data. Confirmation requires a reserved split and a fresh
  pre-generation exposure-union recomputation, as the manifest itself states.

---

## 11. Verdict

# CONDITIONAL

The remediation is substantially sound and honest. C-2, C-3 and C-6 are closed on
the A side and independently verified; C-4 and C-5 are closed with recorded
non-blocking residuals. No red line was crossed: unit corrections are uniformly
`UNRESOLVED` rather than guessed, no errors were fabricated to reach a type count,
the applier remains fail-closed with no reference fallback, R and E receive
identical neutral feedback, every artifact hash reproduces, and the development
panel selection rule and denominator reproduce exactly. A own claim discipline -
`REFERENCE_DERIVED_LEGAL_STRUCTURAL_REVISION_SUPERVISION`, `NOT_QUALIFIED` for
feedback-derived learning - is correct and is endorsed.

It is **not** ACCEPTED, because C-1 remains open on three points (G1, G2, G3). The
two-type demonstration rests on 3 source families with the second type at a single
family; the pre-registered per-type correct-preservation direction is missing; and
the correction targets embed a subtraction direction that the visible evidence does
not determine, tested only for token presence. That last point is the same
hidden-reference class C-2/C-3 were written to close.

Conditions for closing C-1, smallest first:

1. **G3.** Split each eligible correction into its *set-binding* and *direction*
   components. Keep the set-binding component eligible. For the direction component
   either freeze an explicit, documented convention (labelled reference-derived,
   excluded from any visible-evidence claim) or mark it `UNRESOLVED` and reduce the
   correction target to an unordered cell set. Extend the sufficiency test to assert
   direction derivability, not only token presence. Reconcile the stated
   `OPERAND_ORDER_SIGN_REVERSAL` rationale with the rule actually applied
   (set-difference leads to eligible, order-only leads to unresolved) so the taxonomy
   is internally consistent.
2. **G2.** Add the per-type correct-preservation direction to
   `B1_SUPERVISION_MANIFEST.json` as pre-registered by the first audit.
3. **G1.** State type counts in source families as well as trajectories
   (2 types / 3 families, second type n = 1 family), and either present the two as
   subtypes of one visible set-rebinding mechanism or evidence
   `ROW_AND_PERIOD_ROLE_MISBINDING` on additional source families.

Non-blocking follow-ups for D: G4 (compute semantic acceptance on real candidates in
B2), G5 (annotate the three task cards and `TASK_RESULT_A_PAPER.json`), G6 (relabel
the ledger flag), G7 (report both counts).

B2 training remains forbidden while C-1 is open. D must also freeze the proposed
12-family panel before any B2 dispatch.

---

## 12. Next gate

A closes C-1 (G1/G2/G3), then C verifies the narrowed taxonomy, then D freezes the
exact 12-family panel, estimands and the 7/12 originally-correct denominator, then
B2 dispatch may be considered. B2 training must not start while C-1 is open.

Budget impact of this C task: generation attempts 0, generation tokens 0, training
runs 0, training tokens 0, judge calls 0, canary calls 0, production probes 0, health
probes 0. Collaboration dispatch attempts consumed by this task: 1 of 16
(cumulative 2 of 16).
