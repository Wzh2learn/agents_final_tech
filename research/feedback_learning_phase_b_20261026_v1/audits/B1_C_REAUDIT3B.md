# Loop C Disclosure and Estimand Re-Audit — B1 (REAUDIT3B)

**Task id:** `phaseb-b1-reaudit3b-c-20261026` · **Role:** Loop C independent reviewer · **Date:** 2026-10-26 (Asia/Shanghai)
**Goal:** `FEEDBACK_LEARNING_PHASE_B_20261026`
**PROJECT_DIR binding:** `/home/testuser/wzh/phase_b_worktree_20261026`
**Mode:** read-only focused re-audit of H1/H2 against `B1_REMEDIATION3_RESULT_A.json`, `B1_REPORT.md`, `B1_SUPERVISION_MANIFEST.json`, `B1_CORRECTION_TRAJECTORIES.jsonl` and the referenced source, target and receipt hashes.

**Verdict: `CONDITIONAL`** — exact scope in section 7.

H1 (sign-reversal disclosure and estimand) and H2 (operand-order narrowing rule) are **substantively verified and accepted exactly as scoped below**. The single open condition is a low-severity internal inconsistency in `B1_REPORT.md` section Tests (subcase count 26 vs. ground truth 27); it does not touch the estimand, the sign-reversal counts, or H2. Full-suite, GB10 and all endpoint work were not run (section 6).

No file other than the two named deliverables was created or modified. No model, judge, canary, training, endpoint, database or production call was made. **Model calls: 0 · endpoint probes: 0 · DB probes: 0 · new runs: 0.** AI review is not human semantic gold.

---

## 0. Interface evidence preserved from the failed re-audit3

The prior execution `phaseb-b1-reaudit3-c-20261026` returned `REJECTED / AUDIT_NOT_EXECUTABLE_INPUTS_INACCESSIBLE`, archived verbatim at `archive/B1_C_REAUDIT3_INACCESSIBLE_20261026.log`. Its verdict was **not** a substantive H1/H2 finding: zero named inputs were readable because that session was sandboxed to a different directory, and write access to `audits/` was denied. It is retained as interface evidence only and is **superseded as an H1/H2 judgement** by this re-run.

This execution is bound to `PROJECT_DIR=/home/testuser/wzh/phase_b_worktree_20261026`. Read access to the corpus and write access to `audits/` were both available. Provenance note carried over from that log and still true: the B1 corpus is **uncommitted working-tree content** on branch `phase-b-feedback-learning-20261026` (tip `caa18102b`, same as `main`). That remains a provenance weakness for a package whose claims rest on content hashes; it is not a defect in the hashes themselves, which were recomputed first-hand here (section 5).

---

## 1. What was verified

| ID | Requirement | Status |
|---|---|---|
| H1-a | Disclosed sign-reversal counts match the trajectories | **ACCEPTED** |
| H1-b | Per-family disclosed target forms match the materialized targets | **ACCEPTED** |
| H1-c | Sole qualified estimand is `SET_BINDING_SET_ACCURACY` | **ACCEPTED** |
| H1-d | Operator, order and unit preserved as deployment contract fields | **ACCEPTED** |
| H1-e | Not answer correctness; never scored against the reference answer | **ACCEPTED** |
| H1-f | No feedback-derived-learning claim | **ACCEPTED** |
| H1-g | No new-source confirmation claim | **ACCEPTED** |
| H2 | Order-only `OPERAND_ORDER_SIGN_REVERSAL` remains `UNRESOLVED` | **ACCEPTED** |
| R-1 | Report/receipt internal consistency (test subcase count) | **OPEN — condition** |

---

## 2. H1-a / H1-b — sign-reversal disclosure, independently recomputed

Method: every eligible row was re-derived from `B1_CORRECTION_TRAJECTORIES.jsonl` by applying that row's `e_patch.operations` to `o_output.parsed_candidate` and comparing the result with `correction.frozen_reference_target_for_audit` and `verification.execution`. Nothing was taken from the disclosure on trust.

Corpus: 72 trajectories, 24 source families x 3 variants. Eligibility: `ELIGIBLE` 5 · `CORRECT_NO_OP` 40 · `CORRECT_NO_OP_WITH_UNRESOLVED_UNIT_LABEL` 16 · `UNRESOLVED` 11.

| Source family | Variant | Frozen reference target | Materialized target | Set equal | Order equal | `patched_after` | Reference answer | Sign-reversed |
|---|---|---|---|---|---|---|---|---|
| `NAT_train_dac4e923_dccd9dbf` | `original` | `R2:C2 - R4:C2` (million) | `R2:C2 - R4:C2` (million) | yes | yes | `937.4` | `937.4` | no |
| `NAT_train_dac4e923_dccd9dbf` | `irrelevant_change` | `R2:C2 - R4:C2` (million) | `R2:C2 - R4:C2` (million) | yes | yes | `937.4` | `937.4` | no |
| `NAT_train_bdeeb701_c6f0281e` | `relevant_change` | `R2:C1 - R3:C1` (million) | `R3:C1 - R2:C1` (million) | yes | **no** | `-1715.9` | `1715.9` | **yes** |
| `NAT_train_b74eaf04_caa15292` | `original` | `R11:C2 - R11:C1` (reported) | `R11:C1 - R11:C2` (reported) | yes | **no** | `-78.41` | `78.41` | **yes** |
| `NAT_train_b74eaf04_caa15292` | `irrelevant_change` | `R11:C2 - R11:C1` (reported) | `R11:C1 - R11:C2` (reported) | yes | **no** | `-78.41` | `78.41` | **yes** |

Recomputed totals against the disclosed numbers:

| Quantity | Disclosed (result / manifest / report) | Recomputed | Match |
|---|---|---|---|
| eligible rows | 5 | 5 | yes |
| eligible source families | 3 | 3 | yes |
| sign-reversed eligible rows | 3 | 3 | yes |
| sign-reversed eligible source families | 2 of 3 | 2 of 3 | yes |
| `bdeeb701` sign-reversed rows / family trajectories | 1 / 3 (`relevant_change`) | 1 / 3 | yes |
| `b74eaf04` sign-reversed rows / family trajectories | 2 / 3 (`original`, `irrelevant_change`) | 2 / 3 | yes |
| `bdeeb701` executed value vs reference | `-1715.9` vs `1715.9` | identical | yes |
| `b74eaf04` executed value vs reference | `-78.41` vs `78.41` | identical | yes |
| materialized target executes to reference answer | `false` both families | `false` both | yes |

Every cell set is preserved in the materialized target (`set_equal: true` on 5/5); only the subtraction order differs. The unit is preserved on 5/5. The disclosure table in `B1_REPORT.md` (section "Materialized Target Sign-Reversal Disclosure") names the correct frozen and materialized `evidence_refs`, program strings and units for both families.

**Mechanism, for the record.** The sign reversal is a direct consequence of freezing the direction component to the O-candidate slot skeleton (`direction_component.status = FROZEN_TO_O_CANDIDATE`, `reference_direction_inference = false`, `patch_paths_allowed = []` on 66/72 rows, `UNRESOLVED` on the remaining 6). The set-binding patch rebinds reference-valued operand slots and the matching `evidence_refs` entries, so the operand order it leaves behind is O's order, not the reference's. On `dac4e923` those coincide; on `bdeeb701` and `b74eaf04` they do not, and the materialized target executes to the negative of the frozen reference answer. That is exactly what remediation3 was asked to disclose, and it is disclosed.

**Third-family completeness note (advisory, non-blocking).** The manifest discloses the two sign-reversed families individually and states the totals (3 of 5 rows, 2 of 3 families), so the complement is derivable, but it does not name `NAT_train_dac4e923_dccd9dbf` as the non-sign-reversed eligible family; a reader who wants that positive fact must open the trajectories. Not a count error, not blocking; recorded for D's freeze note.

---

## 3. H1-c / H1-d / H1-e — estimand, contract fields, claim limit

The qualified estimand is **byte-identical** across `B1_SUPERVISION_MANIFEST.json` (`qualified_estimand`), `B1_REMEDIATION3_RESULT_A.json` (`estimand`) and `B1_QUALIFICATION_RECEIPT.json` (`qualified_estimand`):

- name: `SET_BINDING_SET_ACCURACY`
- definition: *correct visible cell set with operator, order and unit preserved*
- `is_answer_correctness: false`
- `score_against_reference_answer: "NEVER"`

`B1_REPORT.md` (section "Target Semantics") states the same in prose: *"It is not answer correctness and must never be scored against the reference answer."*

Operator, order and unit are preserved as **deployment contract fields**, not as training targets:

| Contract field | Value | Source |
|---|---|---|
| `arms.R.output` | set-binding-only training target; operator, order and unit are not targets | manifest |
| `arms.E.output` | restricted set-binding-only patch | manifest |
| `reference_program_input` | `false` | manifest |
| `embedded_json_fallback` | `false` | manifest |
| `patch_failure_action` | `REJECT_AND_RECORD; never substitute a reference program` | manifest |
| `strict_json_requirement` | O must parse as one strict whole JSON object before patch application | manifest |
| `label_roles.direction_training_target` | `false` | manifest |
| `label_roles.unit_training_target` | `false` | manifest |
| `label_roles.feedback_derived_fields` | `[]` | manifest |

Not answer correctness — first-hand:

- `verification.execution.eligible_set_binding_target_answer_claim = false` on 5/5 eligible rows.
- `correction.frozen_reference_target_qualification = AUDIT_ONLY_NOT_A_TRAINING_TARGET` on 72/72.
- `target_semantics.target_exact_is_not_semantic_gold = true`; `target_exact` is canonical structural identity to the *materialized unordered set-binding target* only.
- `B1_REPORT.md`: the sign-reversed targets *"are never qualified evidence for answer correctness, semantic acceptance or feedback-derived learning."*

Not feedback-derived learning — first-hand:

- `label_reference_identity.feedback_learning_claim = NOT_QUALIFIED` on 72/72.
- `scientific_qualification.feedback_learning_status = NOT_QUALIFIED`; `supervision_mode = REFERENCE_DERIVED_VISIBLE_SET_BINDING_REVISION_SUPERVISION`.
- `deployment_feedback.minimal_edit_instruction = null` on 72/72; `minimal_edit_instruction` non-null only in `training_reference` (61/72) and `teacher_reference` (61/72), exactly the two reference-only fields named in `reference_only_edit_instruction_fields`.
- `r_e_feedback_content_diff`: `identical = true` and `differences = []` on 72/72. The field is a non-empty envelope carrying an empty diff, so the report's "72/72 diffs empty" is accurate.
- No deployment feedback event exists; `B1_REPORT.md` (section "Exposure And Claim Limit") states the qualified mode is *"reference-derived visible set-binding revision supervision, not feedback-derived learning."*

Not a new-source confirmation claim — first-hand:

- `exposure.confirmation_claim = "NONE"`; `confirmation_gold = null` on 72/72; `human_gold = false`.
- `exposure.role = EXPOSED_DEVELOPMENT_SUPERVISION` and `eligible_for_current_confirmation = false` on 72/72.
- The reserved future pool is explicitly `RESERVED_CANDIDATE_NOT_CURRENTLY_EXPOSURE_CLEAN`, with the blocking condition that the entire source-disjoint pool is already named in the exposure-union manifest, and a `minimum_next_action` requiring D to freeze a reserved split and C to recompute a new pre-generation union first.
- Report/company independence is stated as unavailable and unclaimed in both `B1_REPORT.md` and the manifest identity boundary.
- `B2_DEVELOPMENT_PANEL_DRAFT.json`: `confirmation_claim = "NONE"`, `development_only = true`, `training_authorized = false`, `status = PROPOSED_NOT_FROZEN`. The manifest's `b2_training_authorized = false`.

---

## 4. H2 — order-only `OPERAND_ORDER_SIGN_REVERSAL` remains `UNRESOLVED`

The rule block is byte-identical in the manifest, the result and the receipt:

```
between_A_and_B_phrase_alone_is_discriminator : false
order_only_difference                         : UNRESOLVED_NO_TRAINING_TARGET
set_difference                                : CAN_YIELD_ELIGIBLE_SET_BINDING_COMPONENT
status                                        : UNRESOLVED
```

First-hand confirmation on the rows the rule governs: the 6 trajectories with `error_type = OPERAND_ORDER_SIGN_REVERSAL` all carry `eligibility_status = UNRESOLVED`, `direction_component.status = UNRESOLVED`, `correction_target_status = SET_PRESERVED_DIRECTION_UNRESOLVED`, and a null `e_patch` with `set_binding_component.training_target = false`. No order-only difference produced a training target.

`B1_REPORT.md` states the operative rule in the required form: *"a set difference can yield an eligible set-binding component, while an order-only difference has no training target and is `UNRESOLVED`. The phrase 'between A and B' alone is not the discriminator. Operator and order remain frozen to O and are not training targets."* This closes re-audit2 finding H2, which was that the narrowing reason still named the between-A-and-B wording.

---

## 5. Hashes — source, target and receipt

Every referenced hash was recomputed first-hand.

**External sources** (5/5 match the manifest declarations): `weighted_confirmation_instances_v5.jsonl` = `02cb67fb...003c1`, `weighted_confirmation_results_v5.jsonl` = `456aa2a6...35e0f6`, `EXPOSURE_UNION_SOURCES_V1.json` = `fb969366...ac8f3`, `source_disjoint_results_v4.jsonl` = `3723c388...22e31`, `natural_tasks_source_disjoint_v4.jsonl` = `2d53ed2e...ba0ace`.

**Per-trajectory source and target hashes:**

- `source_identity.instance_sha256 = 02cb67fb...003c1` on 72/72 rows; all 72 rows name the same frozen instances file; `model_arm` is `ordinary_answer_execution_sft` (O) on 72/72.
- `visible_input.table_sha256` recomputes from `table_text` on 72/72.
- `e_patch.candidate_sha256` recomputed via `B1_LOCAL_EDIT_APPLIER.canonical_sha256` against `o_output.parsed_candidate`: **61/61 match** (the 11 rows without a patch have no candidate binding).
- `e_patch.target_sha256` recomputed by applying the recorded operations with `apply_patch(..., allowed_evidence_refs = visible_input.allowed_evidence_refs)`: **61/61 match**. The recorded applier self-checks (`candidate_sha256_verified`, `target_sha256_verified`) agree.
- `correction.set_binding_component` is identical to `correction.r_target.set_binding_component` in `desired_reference_set`, `operations` and `set_binding_label_sha256` wherever both are present.

**Receipt and result hashes:**

- all 16 entries in `B1_QUALIFICATION_RECEIPT.json.artifacts` match;
- all 10 entries in `B1_REMEDIATION3_RESULT_A.json.outputs` match;
- 7 shared keys cross-check equal between the two;
- the preserved archive copies (`archive/B1_REMEDIATION1_RAW_TRAJECTORIES.jsonl`, `archive/B1_REMEDIATION1_SCORE_RESULT_A.json`) match their recorded digests, and `B1_REMEDIATION_RESULT_A.json` is byte-identical to the archived remediation1 score result (`eae35b9d...73688a`), as declared.

**Authority identity** (independently re-derived): `git rev-parse HEAD` = `caa18102bdbbcfe99a889bcf82a125dcc20fdcca`; blob id `c7053b678ce4c67f38656f73932991632107b4fe`; size `21673` bytes; GB10 LF SHA-256 `3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7`. All four match the manifest. The Windows-byte value `c23ec144...` is retained only as superseded noncanonical metadata.

---

## 6. Tests and what was not run

Focused suite executed fresh this session:

`python3 research/feedback_learning_phase_b_20261026_v1/B1_TEST_LOCAL_EDIT_APPLIER.py -v`

Result: `Ran 1 test in 0.034s` · `OK` · exit code 0. The registered case list contains **27** entries and the test asserts `len(cases) == REGISTERED_SUBCASES` with `REGISTERED_SUBCASES = 27`, covering the remediation3 disclosure and estimand assertions (`_remediation3_discloses_sign_reversal_and_sole_estimand`) and the panel assertion (`_development_panel_is_exact_12_families_with_7_correct`).

**Not run by C:**

| Item | Status |
|---|---|
| full repository test suite | NOT_RUN (A's preserved remediation2 record: 967 passed, 1 failed on a missing FinQA fixture, 14 skipped, 1 deselected; log reports no health or model probe) |
| GB10 runtime | NOT_RUN — local results are labelled local; GB10 remains authoritative |
| model, judge, canary, training, endpoint, DB, production probes | NOT_RUN — zero-endpoint discipline |
| frozen artifacts under `/home/testuser/wzh/research_runs/` beyond hash recomputation | content read only as hash inputs |

Zero model/judge/training/generation calls. Zero health or model probes. No budget-ledger change. Two deliverable files written, listed in the task result.

---

## 7. Verdict and exact scope

**`CONDITIONAL`.**

**Accepted without reservation (exact scope):**

1. The H1 materialized-target sign-reversal disclosure is **accurate and complete at the level of counts and per-family forms**: 3 sign-reversed eligible rows in 2 of 3 eligible source families, with the stated per-family variants, executed values and reference answers. Independently reproduced.
2. The sole qualified estimand is **`SET_BINDING_SET_ACCURACY`** — correct visible cell set with operator, order and unit preserved — and nothing else. Operator, order and unit are preserved as deployment contract fields and are excluded from training targets.
3. The estimand is **not answer correctness**, is never scored against the reference answer, and the package contains **no** answer-correctness claim.
4. The package contains **no feedback-derived-learning claim** and **no new-source confirmation claim**. All 72 rows remain exposed development supervision. Report/company independence is unavailable and unclaimed.
5. The order-only `OPERAND_ORDER_SIGN_REVERSAL` rule **remains `UNRESOLVED`**, yields no training target, and the between-A-and-B phrase is no longer offered as the discriminator. Re-audit2 finding H2 is closed.
6. All referenced source, target, receipt and authority hashes recompute exactly.

**Open condition (must be resolved before D freezes):**

- **R-1 — report/receipt test-count inconsistency (low, FACT, not a substantive H1/H2 defect).** `B1_REPORT.md` section Tests states *"one registered test with 26 deterministic subcases."* Ground truth is **27**: `B1_TEST_LOCAL_EDIT_APPLIER.py` declares `REGISTERED_SUBCASES = 27`, the registered case list has 27 entries, and both `B1_REMEDIATION3_RESULT_A.json` (`tests.subcases`) and `B1_QUALIFICATION_RECEIPT.json` (`tests.subcases`) report 27. The report is the only artifact carrying the wrong number. Because `B1_REPORT.md` is hash-pinned in the receipt and the result, correcting it forces a digest refresh on both; alternatively D may freeze with the discrepancy recorded explicitly. Either way it must not be frozen silently.

**Not claimed by this audit:** that the materialized targets are answer-correct; that any direction correction is qualified; that the panel is frozen; that B2 training is authorized; that GB10 or production behaviour is verified; that the uncommitted provenance of the corpus is acceptable. This review is an AI audit and is not human semantic gold.

**Next gate:** A resolves R-1 (or D records the discrepancy) and refreshes the report/result/receipt digests if the report is edited; then D freezes the exact 12-family panel, the sole `SET_BINDING_SET_ACCURACY` estimand and the `7/12` originally-correct denominator before any B2 dispatch. **B2 training must not start** while the package is conditional.

---

```json
{
  "task_id": "phaseb-b1-reaudit3b-c-20261026",
  "goal_id": "FEEDBACK_LEARNING_PHASE_B_20261026",
  "verdict": "CONDITIONAL",
  "h1_sign_reversal_disclosure": "VERIFIED_ACCURATE",
  "h1_estimand": "VERIFIED_SET_BINDING_SET_ACCURACY_ONLY",
  "h1_answer_correctness_claim": "ABSENT_VERIFIED",
  "h1_feedback_learning_claim": "ABSENT_VERIFIED",
  "h1_new_source_confirmation_claim": "ABSENT_VERIFIED",
  "h2_order_only_rule": "VERIFIED_UNRESOLVED_NO_TRAINING_TARGET",
  "open_conditions": ["R-1 report subcase count 26 vs ground truth 27"],
  "model_calls": 0,
  "endpoint_probes": 0,
  "db_probes": 0,
  "new_runs": 0
}
```
