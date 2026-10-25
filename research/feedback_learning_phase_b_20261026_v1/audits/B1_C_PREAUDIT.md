# Loop C — B1 Pre-Audit of Supervision Qualification

Task ID: `phaseb-b1-preaudit-c-20261026`
Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Date: 2026-10-26, Asia/Shanghai
Role: C independent audit (pre-acceptance). Read-only over frozen raw / reference /
scorer / A-owned material. No code, label, manifest, raw-data or A-owned file was
modified. Files written by this task: `audits/B1_C_PREAUDIT.md`, `audits/TASK_RESULT_C.json`.

Labels: **FACT** (first-hand recomputed or read from a frozen artifact), **INFERENCE**
(derived judgment), **VALUE** (threshold/policy call), **UNVERIFIED** (could not be
checked in this execution surface).

---

## 0. Authority binding

- **FACT.** Authority is `docs/research/LOOP_D_RESEARCH_PROMPT.md`. Commit pin
  `caa18102bdbbcfe99a889bcf82a125dcc20fdcca` is exact: `git rev-parse HEAD` returns it and
  the worktree file is byte-identical to `git cat-file blob` at that commit (blob
  `c7053b678ce4c67f38656f73932991632107b4fe`, 21673 bytes).
- **FACT (defect F5).** The SHA-256 declared in `B1_A_SUPERVISION_QUALIFICATION_TASK.md`,
  `B1_C_PREAUDIT_TASK.md`, `B1_A_PAPER_AND_THESIS_TASK.md` and `PHASE_B_BUDGET_LEDGER.json`
  is `c23ec144fe778d1ea8b36ab35def58a13b59d9682f1da4adf6005c2ea378e922`. The actual
  SHA-256 of the pinned file is
  `3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7`. The commit pin alone
  identifies the document; the declared digest is wrong.

## 1. Scope and snapshot

Audited: (1) frozen natural task/output derivatives in-repo —
`REVISION_OPERATOR_INSPECTION_V1.json`, `REVISION_OPERATOR_DIAGNOSTIC_PROTOCOL_V1.json`,
`_V2.json`, `_V3_MECHANISM.json`, `REVISION_OPERATOR_V3_MECHANISM.json`,
`PHASE_A_RECOMPUTE_V1.json`; (2) task-build and scoring contracts —
`build_natural_tasks_v2.py`, `natural_program_contract_v2.py`, `task_semantics_v2.py`,
`source_role_contract_v3.py`, `deployable_tool_contract_v2.py`,
`semantic_delivery_check_v3.py`, `analyze_binding_residual_v3.py`,
`run_natural_program_experiment_v2.py`, `run_natural_error_repair_v4.py`,
`NATURAL_METHOD_PROTOCOL_V2.json`; (3) exposure/source contracts —
`exposure_union_guard_v1.py`, `EXPOSURE_UNION_SOURCES_V1.json`,
`SOURCE_DISJOINT_TASK_MANIFEST_V4.json`; (4) the B1 contract set; (5) A-owned material at
snapshot, read-only — `B1_LOCAL_EDIT_APPLIER.py` (282 lines, sha256
`7dbbbe863a05bb9a2ff5d6a962af2d2f20db2e9efffa6d07ca2f5f2fc27216de`) and
`B1_A_PAPER_AND_THESIS_TASK.md`. `audits/`, `paper_e/`, `thesis_draft/` were empty.

**FACT.** At snapshot the B1 A-EXP deliverables `B1_CORRECTION_TRAJECTORIES.jsonl`,
`B1_SUPERVISION_MANIFEST.json`, `B1_LOCAL_PATCH_CONTRACT.json`,
`B1_TEST_LOCAL_EDIT_APPLIER.py`, `B1_QUALIFICATION_RECEIPT.json`, `B1_REPORT.md`,
`B1_PREFLIGHT_DRAFT.json`, `TASK_RESULT.json` did **not** exist. This pre-audit judges the
**contract and the frozen premise set** and pre-registers the conditions under which A's
implementation may later be accepted. It cannot accept an implementation not yet on disk.

## 2. Commands executed (all deterministic, offline)

```
git rev-parse HEAD
git show <pin>:docs/research/LOOP_D_RESEARCH_PROMPT.md | sha256sum
git cat-file blob <pin>:docs/research/LOOP_D_RESEARCH_PROMPT.md | sha256sum
git cat-file -s   <pin>:docs/research/LOOP_D_RESEARCH_PROMPT.md
sha256sum <all evidence files listed in section 8>
python3 -c '<independent recompute of REVISION_OPERATOR_INSPECTION_V1.json>'
python3 -c '<24-family panel vs SOURCE_DISJOINT_TASK_MANIFEST_V4.json cross-check>'
python3 -c '<PHASE_A_RECOMPUTE_V1.json / EXPOSURE_UNION_SOURCES_V1.json dump>'
```

**Model / judge / training / production endpoint calls made by C: 0.** Canaries: 0.
Health probes: 0. Generation attempts: 0. Training runs: 0.

---

## 3. Scope item 1 — Label visibility

### 3.1 Unit scale is not deployment-visible (F2, blocking)

- **FACT.** `build_natural_tasks_v2.py:77-80` defines `unit_from_scale(scale)` as
  `str(scale or "").strip().lower()` else `"reported"`. Lines 153 and 160 set both
  `expected.unit` and `target.unit` to `unit_from_scale(question.get("scale"))`.
- **FACT.** `build_natural_tasks_v2.py:84-92` builds the deployment prompt from exactly
  four visible parts: instruction, optional relevant-paragraph context, rendered table, and
  the question string. The TAT-QA gold question field `scale` is **never** rendered into
  the prompt.
- **FACT.** `semantic_delivery_check_v3.py:60-113` `semantic_check` performs row-role
  visibility, period visibility and average-denominator checks only. It performs **no** unit
  or scale check.
- **FACT (independent recompute).** Of 72 candidate rows in
  `REVISION_OPERATOR_INSPECTION_V1.json`, 16 rows differ from the reference on the `unit`
  field alone, across 6 source families. All 16 have `initial_program_correct == True`: the
  arithmetic program is already correct and only the unit string differs. Unit
  candidate-to-expected pairs: `thousand->reported` 8, `thousand->million` 2,
  `percent->reported` 2, `million->thousand` 2, `million->reported` 2, `crore->reported` 1.
  13 of 16 target `reported`, the default returned when the gold `scale` field is empty.
- **INFERENCE.** Every `unit`-field difference in this panel is a disagreement with a gold
  annotation that is not derivable from the deployment-visible input. Under
  `B1_D_FREEZE_GATE.md` Supervision Gate item 4 ("Unobservable unit/period requirements are
  `UNRESOLVED`, never guessed") and authority section 4, all unit-field corrections are
  `UNRESOLVED`. They must not be used as R or E correction targets.

### 3.2 Row / period / reference evidence is visible (contrast case)

- **FACT.** `REVISION_OPERATOR_DIAGNOSTIC_PROTOCOL_V1.json` payload for
  `localization_ref_dac4` reads: *"The question requests AMER and EMEA in 2018. The candidate
  uses R4:C1 and R4:C2, whose visible row role is EMEA/EMEA and periods are 2019/2018."*
  Row roles and period labels are rendered in the table; the question states the requested
  roles/periods. The correct binding is derivable from visible information alone.
- **FACT.** `semantic_check` emits `question_row_role_not_visible_in_program` and
  `question_period_not_visible_in_program` from visible question/table text only.
- **INFERENCE.** Row-role and period binding errors are the one clearly visible,
  visible-evidence-repairable error family in the frozen panel.

### 3.3 Legal equivalence is not implemented in the diff/scorer layer (F4)

- **FACT.** `rescore_revision_operator_v1.py:23` and `revision_operator_diagnostic_v1.py:60`
  define `canonical(value)` as `json.dumps(value, ensure_ascii=False, sort_keys=True,
  separators=(",", ":"))`. `target_exact` is `canonical(target) ==
  canonical(expected_target(instance))`. `revision_operator_diagnostic_v1.py:95-112`
  `diff_target` is a recursive structural diff. No commutative, associative or
  constant-folding normalisation exists anywhere in the audited scoring path.
- **FACT.** `same_candidate_feedback_a_v1.py:501` self-documents the boundary: *"Post-hoc
  expected-program discrepancy mapping; algebraically equivalent programs can be mislabeled
  and are not hidden-reference prompt features."*
- **FACT.** `analyze_binding_residual_v3.py:218` recognises a `same_value_alias_or_reference`
  class (different refs, same executed value), but only as a post-hoc diagnosis in
  `classify_row`; it is not an acceptance rule in the scorer.
- **INFERENCE.** Authority section 4 requires that legally equivalent programs and
  references may be accepted under frozen semantics, and `B1_D_FREEZE_GATE.md` defines
  "Final semantic correctness" as correct program/evidence/unit/role/period. As written, a
  structurally different but legally equivalent program is counted as an error and as
  "damage" in the correct-preservation estimand. B1 must attach an explicit
  legal-equivalence acceptance rule to each correction target, or the estimand is
  mismeasured.
- **UNVERIFIED.** Whether any of the 5 natural error families in section 4.1 contains a
  legally-equivalent alternative cannot be settled without the per-task visible programs;
  the frozen task files are outside this execution surface (section 10).

### 3.4 `UNRESOLVED` handling exists and is used

- **FACT.** `source_role_contract_v3.py:167-215` `classify_average_denominator` returns
  `UNRESOLVED` / `UNRESOLVED_REFERENCE_QUESTION_MISMATCH`.
  `run_natural_error_repair_v4.py:55-82` `corrected_target` returns `None` when that label is
  hit, and the task is excluded from the correction set rather than guessed.
- **FACT.** `PHASE_A_RECOMPUTE_V1.json` records `ineligible_scale_unobservable_cases: 1` and
  `eligible_visible_repair_cases: 1` for each of the three diagnostic conditions.
- **INFERENCE.** The UNRESOLVED mechanism is real and was applied correctly in Phase A. The
  gap is that it was applied to one case, while section 3.1 shows the same unobservability is
  dataset-wide for the unit field.

---

## 4. Scope item 2 — Natural-error qualification (F1, blocking)

Independent recompute over `REVISION_OPERATOR_INSPECTION_V1.json`
(`all_candidate_count: 72` = 24 source families x 3 variants; 24 distinct `table_uid`).

### 4.1 What is actually a natural error

- **FACT.** On the `original` variant, exactly **5** of 24 families have
  `initial_program_correct == False` (O's frozen output executes to the wrong value). All
  five differ from the reference only on `evidence_refs` / `program.left.ref` /
  `program.right.ref`:

  | source family | candidate -> expected | structural flavour |
  |---|---|---|
  | `NAT_train_04e7f446_538c6915` | `R3:C1/R3:C2` -> `R3:C2/R3:C1` | operand order swap, same row |
  | `NAT_train_819641fb_108cfcb0` | `R5:C3/R5:C4` -> `R5:C4/R5:C3` | operand order swap, same row |
  | `NAT_train_2e038152_274875b0` | `R5:C1/R5:C2` -> `R6:C1/R6:C2` | row selection shift |
  | `NAT_train_b74eaf04_caa15292` | `R9:C1/R9:C2` -> `R11:C2/R11:C1` | row shift + order swap |
  | `NAT_train_dac4e923_dccd9dbf` | `R4:C1` -> `R2:C2` (left only) | single-operand row/role/period binding |

- **FACT.** Zero `program.op` differences occur anywhere in the 72 rows. There is no natural
  operator error in this panel. The `wrong_operator` family in
  `run_natural_program_experiment_v2.py:291` is a synthetic training mutation and must not be
  counted as a natural error type.
- **FACT.** All 16 `unit`-only differences have `initial_program_correct == True` (section
  3.1). They are label disagreements, not natural arithmetic errors.

### 4.2 Count of eligible natural error types

- **INFERENCE.** The five natural error families fall into two structural flavours:
  (a) row / row-role / period selection (`2e038152`, `b74eaf04`, `dac4e923`) and (b) operand
  order / subtraction direction (`04e7f446`, `819641fb`, `b74eaf04`). Flavour (a) has
  directly visible repair evidence (section 3.2). Flavour (b) is a sign or direction error
  whose visible repair evidence is the question's requested direction; that wording is not in
  the in-repo evidence, so its eligibility is **UNVERIFIED** here.
- **FACT.** Phase A, working from the 2-case mechanism diagnostic, recorded independently:
  *"The only eligible visible repair case is the row/period/reference error."*
  (`docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md` section 1).
  `PHASE_A_RECOMPUTE_V1.json` confirms `eligible_visible_repair_cases: 1`.
- **INFERENCE.** On current frozen evidence the "at least two naturally occurring eligible
  error types with visible evidence" requirement (`B1_D_FREEZE_GATE.md` Supervision Gate item
  1; authority section 4) is **not yet met**. Exactly one type (row/role/period binding) is
  clearly evidenced. The second candidate type is a structural sub-flavour of the same
  `program.*.ref` diff signature and has not been frozen as a labelled type with its own
  visible-evidence criterion.
- **VALUE.** Splitting one `program.*.ref` diff signature into two "error types" is a
  scientific claim about mechanism, not a fact about the diff. It must be pre-registered in
  `B1_SUPERVISION_MANIFEST.json` with (i) a per-type visible-evidence sufficiency test,
  (ii) a per-type correct-preservation direction, and (iii) an explicit statement that
  `program.op` errors do not occur in the panel. If the second type cannot pass its own
  visibility test, the A task's stop condition applies: stop without fabricating, report
  `QUALIFICATION_FAILED`, and do not launch B2.

### 4.3 Correct and no-op samples

- **FACT.** `B1_D_FREEZE_GATE.md` Supervision Gate item 2 and authority section 4 require
  correct and no-op trajectories alongside errors. The frozen panel supports this: 19 of 24
  families have `initial_program_correct == True` on `original`, and
  `REVISION_OPERATOR_INSPECTION_V1.json` `copy_exact_candidates` identifies
  difference-count-0 rows suitable for no-op controls (all three variants of `f440390f`,
  `f2340090`, `c5b624e7`).
- **INFERENCE.** The premise is satisfiable; the burden is on A to show the no-op/correct
  trajectories are actually retained in `B1_CORRECTION_TRAJECTORIES.jsonl`, not only error
  cases.

---

## 5. Scope item 3 — Source / exposure union and independence level

- **FACT.** `EXPOSURE_UNION_SOURCES_V1.json` declares `source_identity_boundary:
  "task_id/question_uid/table_uid only; report/company identity is unavailable and is not
  claimed"`.
- **FACT.** `NATURAL_METHOD_PROTOCOL_V2.json` `source.source_boundary` states the train/dev
  files are same-benchmark splits and that *"table UID is the independent cluster, not a new
  dataset family or full report/company identity"*.
- **FACT.** `SOURCE_DISJOINT_TASK_MANIFEST_V4.json` records `selected_split_counts:
  {"train": 96}`, `selected_task_count: 96`, `selected_source_key_count: 192`,
  `excluded_source_key_count: 1210`, `prior_task_count: 120`. Every selected task is from the
  TAT-QA **train** split.
- **FACT (independent recompute).** All 24 source families of the diagnostic panel appear in
  `selected_task_ids` (24/24) and their 24 `table_uid` values appear in `selected_table_uids`
  (24/24).
- **FACT.** `REVISION_OPERATOR_V3_MECHANISM.json` `exposure_receipt` shows `overlap_count: 4`
  with `allow_development_exposure: true` and `evidence_identity:
  EXPOSED_DEVELOPMENT_DATA_ONLY_NOT_CONFIRMATION`.
- **INFERENCE.** The panel is exposed development data at same-dataset, table-disjoint level.
  It is not report-isolated, not company-isolated, and not cross-dataset. The exposure guard
  (`exposure_union_guard_v1.py`) unions `task_id` / `question_uid` / `table_uid` /
  `source_task_id` / `base_instance_id` only — exactly matching the declared boundary.
- **VALUE.** `B1_A_SUPERVISION_QUALIFICATION_TASK.md` item 6 is correct to forbid
  report/company and cross-dataset claims and to ask only for a "future same-dataset
  source-isolated confirmation candidate". Any B1 or B2 output using "independent", "held-out"
  or "unseen" without the same-dataset/table-level qualifier is a claim defect. Table-level
  disjointness also does not preclude the same issuer under several `table_uid` values; that
  residual must be stated, not assumed away.

---

## 6. Scope items 4-5 — R/E parity and patch semantics

### 6.1 Feedback information parity

- **FACT.** `REVISION_OPERATOR_DIAGNOSTIC_PROTOCOL_V1.json` payloads are parity-clean on the
  tested conditions: `neutral_revision` ("No targeted diagnostic is provided.");
  `category_feedback` names only the class ("unit-role discrepancy with the monetary table
  context"; "evidence-role mismatch in the first subtraction operand") with no correct path
  and no correct value; `localization_feedback` states visible facts and the candidate's own
  values ("The candidate unit is 'thousand'"; "the candidate uses R4:C1 and R4:C2, whose
  visible row role is EMEA/EMEA and periods are 2019/2018") and does not hand over the
  correct reference or unit; `known_edit_control` does hand over the full correct edit and is
  explicitly labelled `DEVELOPMENT_REFERENCE_ASSISTED_NON_DEPLOYABLE` under
  `hidden_reference_use`.
- **FACT (risk F3/F6).** `revision_operator_diagnostic_v1.py:114+` `minimal_edit_instruction`
  emits, for the unit case, *"At unit, replace 'thousand' with **the verified development
  value** 'million'"* and, for the reference case, *"At program path program.left, replace
  evidence reference 'R4:C1' with 'R2:C2', and update evidence_refs from [...] to [...]"*.
  Both the path and the correct target value are present. That value is reference-derived,
  not visible.
- **INFERENCE.** Scope item 4 forbids E receiving the correct path/unit through feedback while
  R does not. If E's supervision or deployment feedback is built from
  `minimal_edit_instruction` while R receives only `neutral_revision` / `category_feedback`, E
  holds strictly more information and the E-R comparison is confounded.
  `B1_D_FREEZE_GATE.md` already requires such asymmetry be recorded, not declared matched; the
  contract is right, the trap is live.
- **VALUE.** `B1_CORRECTION_TRAJECTORIES.jsonl` must carry the four-way split demanded by
  authority section 4 and `B1_D_FREEZE_GATE.md` Supervision Gate item 5 — training reference /
  teacher reference / deployment feedback / confirmation gold — as four separate fields, plus
  a per-trajectory R-vs-E feedback-content diff. `minimal_edit_instruction` belongs in the
  teacher/training reference fields only. It must never appear in deployment feedback.

### 6.2 Patch semantics and fail-closed application

- **FACT.** `B1_LOCAL_EDIT_APPLIER.py` (sha256
  `7dbbbe863a05bb9a2ff5d6a962af2d2f20db2e9efffa6d07ca2f5f2fc27216de`) is genuinely
  fail-closed: `PatchError` is raised on every illegality path
  (`operation_op_must_be_replace`, `operation_path_not_allowed`, `operation_duplicate_path`,
  `operation_expected_value_mismatch`, `operation_value_illegal_operator`,
  `operation_value_unit_not_visible`, `operation_value_reference_not_visible`,
  `candidate_sha256_mismatch`, `target_sha256_mismatch`,
  `patched_program_evidence_refs_mismatch`, and others). `apply_patch` returns either a fully
  validated candidate or raises. There is no partial application and no soft-fail.
- **FACT.** No reference/gold program is read, imported or consulted anywhere in
  `B1_LOCAL_EDIT_APPLIER.py`. The prohibition on hidden reference fallback is satisfied by the
  applier.
- **FACT.** Paths are whitelisted to `ALLOWED_PATHS` = `{/program/op, /program/left/ref,
  /program/left/const, /program/right/ref, /program/right/const, /unit}` plus
  `/evidence_refs/<i>`, `MAX_OPERATIONS = 8`, `op` must be `replace`. All five natural error
  families of section 4.1 are expressible within this schema (2 to 4 operations each).
- **FACT (live condition F3).** `allowed_answer_units` is a caller-supplied set.
  `_validate_allowed_value` accepts a `/unit` replacement whenever the value is in that set.
  Nothing in the applier constrains how the set is built.
- **INFERENCE.** If A constructs `allowed_answer_units` from `expected.unit` (that is,
  `unit_from_scale(question["scale"])`), the gold scale annotation re-enters E as a legal edit
  target — a hidden-reference fallback in the deployment contract, which scope item 5 forbids.
  The only visibility-honest constructions are (i) the set of unit strings literally present
  in the visible prompt/table, or (ii) an empty unit-edit allowance with unit corrections
  recorded `UNRESOLVED`.
- **FACT (scope note).** `ALLOWED_PATHS` only reaches `/program/{left,right}/...` at depth 1.
  Deeper operands (for example `left.left.ref`) cannot be edited and will fail closed. This is
  safe but must be recorded in `B1_LOCAL_PATCH_CONTRACT.json` as an expressiveness bound, with
  a count of panel cases that fall outside it.
- **FACT (provenance note).** `target_sha256` is carried inside the patch and verified against
  the patched result. That proves internal consistency of the patch, not that the target was
  model-produced. `B1_QUALIFICATION_RECEIPT.json` must show each `target_sha256` came from the
  model's prediction path and not from a copied reference.

### 6.3 Independent verification requirement

- **INFERENCE.** `B1_A_SUPERVISION_QUALIFICATION_TASK.md` item 5 requires A to independently
  verify that each E patch applied to the exact O candidate yields the correction target and
  executes to the verified result, with strict JSON, embedded JSON, semantic and execution
  outcomes kept separate. The existing artifact vocabulary already separates these
  (`strict_format_valid`, `embedded_format_valid`, `syntax_adapter_applied`/`actions`,
  `semantic_decision`, `program_executable`, `program_correct`, `recomputed_program_correct`).
  The requirement is implementable without new infrastructure.

---

## 7. Scope item 6 — Frozen estimands and thresholds

- **FACT.** `B1_D_FREEZE_GATE.md` freezes: final semantic correctness; error repair (O wrong
  to final correct); correct preservation with O-correct-to-wrong counted separately; delivery
  (correct / wrong / reasonable UNKNOWN / coverage); cost (input/output/training tokens, GPU
  time, tool calls, wall time, adapter and application cost). It states variants from one
  source family are repeated measures, not independent samples. These match authority section
  5.
- **FACT.** Minimum useful effect frozen as: E-R at least +5 pp paired final semantic
  correctness; E-N at least +3 pp; E must cover at least 2 eligible natural error types
  without reversing direction in either; E may damage at most one additional originally-correct
  family per 24-family panel relative to R. `INCONCLUSIVE` (not success) when the point
  estimate is below threshold or the source-cluster interval crosses zero widely. Stopping
  rule if the advantage vanishes under matched supervision/compute or exists only in JSON
  format/length.
- **FACT (precision defect F8).** In the development panel the originally-correct denominator
  on the `original` variant is **19 of 24** (5 are wrong, section 4.1), not 24. "per 24-family
  panel" does not say which panel — the development diagnostic panel or the B3 confirmation
  panel (24 new families x 3 variants x 4 arms = 288).
- **VALUE.** The damage tolerance must name the panel identity and the exact denominator before
  B2. Suggested freeze text: *"relative to R, on the B3 confirmation panel of 24 new source
  families, E may convert at most 1 family that is correct under O into a wrong final answer."*
- **FACT.** `PHASE_B_BUDGET_LEDGER.json` allocations match authority section 9 exactly
  (96/108/288/144/36 = 672 attempts; 360k/420k/1220k/620k/180k = 2.8M generation tokens; 4
  training runs / 4.0M training tokens). `used` is all zeros and `events` is empty. Dispatch
  budget 2 of 16 one-shot attempts.
- **FACT.** C3 separation text in `B1_D_FREEZE_GATE.md` matches authority section 7
  (abstention alone is not improvement; the same E repairer is not a second innovation).

---

## 8. Evidence hashes

| artifact | sha256 |
|---|---|
| `docs/research/LOOP_D_RESEARCH_PROMPT.md` (pinned) | `3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7` |
| `REVISION_OPERATOR_INSPECTION_V1.json` | `d1abd77b41c0e30745264a087f5595f51e1e4d831db02a80be8803b4c9531249` |
| `REVISION_OPERATOR_DIAGNOSTIC_PROTOCOL_V1.json` | `dc40a8c132010e8ba54851977a0f1718c6a2fbdf666763805821e070b581a338` |
| `PHASE_A_RECOMPUTE_V1.json` | `4ab8cf7961a6d11a77943f8be7860771e46134e5e83fd3210063bb35b0f468f2` |
| `EXPOSURE_UNION_SOURCES_V1.json` | `fb96936698638cb531eadaa0cffde6ff5479a14cea83500701b8a3c1323ac8f3` |
| `build_natural_tasks_v2.py` | `23e4b913bca2ac7aa3c6905287021d29c367fec88b4df1704f2741a0fa42e489` |
| `SOURCE_DISJOINT_TASK_MANIFEST_V4.json` | `557272d3462d5f44c7028349ca119f87821bfc94c8ca8fa24c2702d88e69a9a6` |
| `B1_D_FREEZE_GATE.md` | `04301e4093416d2a8b4d2f9b137e438f6b7da3f09bfd0f7e17d3333ee7fefcdc` |
| `B1_A_SUPERVISION_QUALIFICATION_TASK.md` | `1c9c15b28da3a4d09f9ea6765fcd86d50ba4ef8243bff8908e2c7c22f0895352` |
| `B1_C_PREAUDIT_TASK.md` | `6a35af4e7872dc7b03f2ce26d33264e41e0191ff8da750d06d291a669fda487a` |
| `B1_LOCAL_EDIT_APPLIER.py` (A-owned, snapshot) | `7dbbbe863a05bb9a2ff5d6a962af2d2f20db2e9efffa6d07ca2f5f2fc27216de` |

Git blob of the pinned authority at `caa18102...`:
`c7053b678ce4c67f38656f73932991632107b4fe`, 21673 bytes.

---

## 9. Findings

| ID | Sev | Label | Finding |
|---|---|---|---|
| F1 | **blocking** | FACT+INFERENCE | Only one eligible natural error type (row/role/period binding) is evidenced with visible repair information. The at-least-two-type supervision gate is not yet met; a second type exists only as a structural sub-flavour of the same `program.*.ref` signature and is unlabelled. |
| F2 | **blocking** | FACT | Unit labels derive from the gold TAT-QA `scale` field, which is never rendered into the prompt. All 16 unit differences across 6 families are `UNRESOLVED` by visibility; 13 of 16 target the empty-scale default `reported`. |
| F3 | **blocking** | FACT+INFERENCE | `allowed_answer_units` is caller-supplied; if built from `expected.unit` it reintroduces the gold scale as a legal E edit target. `minimal_edit_instruction` already leaks path plus correct value and must be confined to teacher/training reference fields. |
| F4 | medium | FACT | No legal-equivalence rule in `canonical` / `target_exact` / `diff_target`; the code itself admits algebraically equivalent programs can be mislabeled. Correct-preservation will miscount equivalents as damage. |
| F5 | medium | FACT | Declared authority SHA-256 in all Phase B task cards and the budget ledger is wrong (`c23ec144...` vs actual `3ed5e1fc...`). Commit pin is correct. |
| F6 | medium | INFERENCE | R/E feedback-content asymmetry is a live confound; the four-way reference split and a per-trajectory R-vs-E feedback diff are mandatory before any E-R claim. |
| F7 | low | FACT | Independence is `task_id/question_uid/table_uid` only; the panel is exposed development data at same-dataset table-disjoint level. Report/company and cross-dataset independence must never be claimed. |
| F8 | low | FACT | Freeze-gate damage tolerance names "24-family panel" without panel identity; the development-panel originally-correct denominator is 19/24. |
| F9 | low | INFERENCE | `target_sha256` proves patch self-consistency, not model provenance; the qualification receipt must evidence the prediction path. Applier `ALLOWED_PATHS` reaches depth-1 operands only — an expressiveness bound to record. |

---

## 10. Excluded / unverified surfaces

- **UNVERIFIED.** All frozen run artifacts under `/home/testuser/wzh/research_runs/`
  (`weighted_confirmation_instances_v5.jsonl`, `weighted_confirmation_results_v5.jsonl`,
  `natural_tasks_v2.jsonl`, `evaluation_instances_v2.jsonl`, the ordinary checkpoint/adapter,
  and the TAT-QA raw at `data/research/tatqa_raw_2026/`) are outside this session's allowed
  working directory and could not be opened. All recomputation above therefore rests on the
  in-repo frozen derivatives listed in section 8, which are themselves hash-stamped by the
  Phase A / V3 receipts. This is a surface limitation, not a negative finding.
- **UNVERIFIED.** Per-task visible prompts for the 24 families, so the visibility of the
  subtraction-direction wording (flavour (b) in section 4.2) and the presence/absence of any
  scale token in the question text could not be checked case by case.
- **EXCLUDED.** `pytest` is not installed for the local `python3` (3.12.3,
  `/usr/bin/python3`, `No module named pytest`), so the existing suites
  (`test_exposure_union_guard_v1.py`, `test_task_semantics_v2.py`,
  `test_source_role_contract_v3.py`, `test_correction_v2.py`, `test_natural_tasks_v2.py`) were
  **not** run. All C recomputation was done with plain deterministic `python3` instead. Local
  results are local; GB10 remains authoritative.
- **EXCLUDED.** No model, judge, training, canary, production or service probe was run. Count
  of such calls by C: **0**.
- **EXCLUDED.** A-owned files were read only. No code, label, manifest, raw data, frozen
  output, task card, ledger or A-owned file was modified.

---

## 11. Verdict

# `CONDITIONAL`

The B1 contract set is sound in structure: it separates the four reference roles, requires
correct and no-op samples, forbids guessing hidden labels, forbids hidden reference fallback,
forbids report/company independence claims, and freezes estimands and thresholds before
confirmation. No red-line was crossed and the budget ledger is arithmetically consistent with
authority section 9.

It is **not** `ACCEPTED`, because the supervision gate's own necessary conditions are not yet
evidenced on the frozen data, and three blocking conditions are open.

Conditions that must be closed before B1 may report `QUALIFICATION_PASSED` and before B2
training is launched:

- **C-1 (F1).** Freeze in `B1_SUPERVISION_MANIFEST.json` a labelled natural-error taxonomy
  with, per type, a visible-evidence sufficiency test and a frozen correction operator.
  Demonstrate at least 2 types pass it. If only one passes, execute the A task's stop
  condition: report `QUALIFICATION_FAILED`, do not fabricate errors, do not launch B2, and
  hand D the smallest narrowing alternative.
- **C-2 (F2).** Mark every unit-field correction `UNRESOLVED`. Exclude unit targets from R and
  E supervision and from the patch schema's legal edit targets.
- **C-3 (F3).** Construct `allowed_answer_units` only from units literally visible in the
  deployment input (or empty). Confine `minimal_edit_instruction` to training/teacher
  reference fields. Record the R-vs-E feedback-content diff per trajectory.
- **C-4 (F4).** Attach a legal-equivalence acceptance rule to each correction target, or state
  explicitly that `target_exact` is structural and re-derive the correct-preservation estimand
  accordingly.
- **C-5 (F5).** D corrects the authority SHA-256 in the four task cards and
  `PHASE_B_BUDGET_LEDGER.json` to
  `3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7`, or records why the
  alternate digest is authoritative.
- **C-6 (F8).** Freeze the damage-tolerance panel identity and denominator before B2.

Non-blocking conditions F6, F7, F9 are recorded for the B1 report and the B2 gate.

---

## 12. Next gate

`D -> freeze B1 conditions C-1..C-6 -> A completes B1 deliverables against them -> C re-audits
B1_CORRECTION_TRAJECTORIES.jsonl / B1_SUPERVISION_MANIFEST.json / B1_LOCAL_PATCH_CONTRACT.json /
B1_QUALIFICATION_RECEIPT.json on GB10 -> D decides B2 launch or narrowing`. B2 training must
not start while C-1 is open.

Budget impact of this C task: generation attempts 0, generation tokens 0, training runs 0,
training tokens 0, judge calls 0, production probes 0. Collaboration dispatch attempts
consumed: 1 of 16.
