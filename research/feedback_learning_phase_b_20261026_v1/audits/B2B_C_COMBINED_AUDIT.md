# B2/B2B Combined Scientific Audit (Loop C)

Task ID: `phaseb-b2b-combined-audit-c-20261026`
Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Role: C independent audit
Date: 2026-10-26
Scope: same-start B2 training, the 192-token first development run, and the 384-token
B2B output-budget repair run.

**Verdict: `CONDITIONAL`** -- see section 9. The stop decision is accepted; the status
label is accepted only under the exact scope and four disclosures recorded there.

No model, judge, training, endpoint, database or production call was made by this
audit. Read-only filesystem and local Python only. Zero model calls.

---

## 1. Method and independence

Before reading any A interpretation, this audit read the frozen raw, reference and
scorer surfaces and re-derived every reported quantity from scratch:

| Surface | Role in recompute |
|---|---|
| `B1_CORRECTION_TRAJECTORIES.jsonl` | reference: `o_output.parsed_candidate`, `correction.set_binding_component.desired_reference_set`, `correction.e_patch`, `frozen_reference_target_for_audit` |
| `B2_DEVELOPMENT_PANEL_DRAFT.json` | 12-family / 36-trajectory panel, `originally_correct_on_original_variant` |
| `B1_LOCAL_PATCH_CONTRACT.json` | restricted-patch contract (paths, keys, fail-closed rules) |
| `b2/B2_DEVELOPMENT_RAW.jsonl` | first-run raw generations |
| `b2b/B2B_GENERATION_RAW.jsonl` | repair-run raw generations |

The recompute implemented, from the contract text and without importing A
analysis modules: independent strict/embedded JSON parsing, an independent
fail-closed restricted-patch applier, an independent `SET_BINDING_SET_ACCURACY`
evaluator, family aggregation and a 20 000-sample source-family bootstrap.

**Agreement with A is exact on every generative row.** Across all 288 rows
(216 first-run + 72 repair-run) there is zero disagreement on `syntax_source`,
`SET_BINDING_SET_ACCURACY`, or E patch legality. The 36 deterministic-control rows
also recompute 36/36 once the control is scored as the materialized reference patch
applied to O, which is the correct control definition. The A analysis is not
hallucinated and does not mis-score.

---

## 2. Checklist verification

### 2.1 Same effective ordinary parent, two real training runs, no retraining in B2B -- PASS

- Parent: `.../ordinary_answer_execution_sft/final_adapter`, `effective_identity:
  BASE_PLUS_FROZEN_ORDINARY_ADAPTER`. Its `adapter_config.json`
  (`bc2a50d7...a41c6`) and `adapter_model.safetensors` (`bc5f1052...1a1ff`) hash-match
  the frozen `parent_checkpoint` recorded independently in **both** training
  receipts, and match the on-disk parent read by this audit.
- Both receipts record `tensor_group_sha256_before == tensor_group_sha256_after ==
  d30ca750...73dfc4` and `unchanged: true` -- the parent was not mutated by either run.
- Both children embed `final_adapter/ordinary_parent/adapter_model.safetensors`
  with hash `bc5f1052...1a1ff` -- identical effective parent at generation time.
- Two real runs: distinct child `adapter_model.safetensors`
  (R `9cf9c306...eed5`, E `69405c84...1aba`), each `status: PASS`,
  `optimizer_steps: 128`, `global_step: 128`, `rows: 256`,
  `unique_source_tasks: 12`, `unique_trajectories: 36`,
  `eligible_correction_rows: 39`, `no_op_and_unresolved_rows: 217`.
  `run_totals.training_runs: 2`, `processed_text_tokens: 319948` (budget 2 000 000).
- No retraining in B2B: `B2B_PROTOCOL_FROZEN.same_artifacts.no_retraining: true`,
  `training_runs: 0`, `training_tokens: 0`; `B2B_GENERATION_RECEIPT` confirms
  `training_runs: 0`. B2B reloads the frozen child adapters only.

All frozen hashes recomputed by this audit and match their claims:
`B2_PROTOCOL_FROZEN` `f21af57c...`, `B2B_D` decision `3281eb80...`, panel
`56e3c270...`, first-run raw `a21456b3...`, first-run receipt `ca76711c...`,
partial-failures `1c3352d2...`, both training receipts, both child adapters,
`B2B_PROTOCOL_FROZEN` `b7d28b4c...`, B2B raw `a50e5275...`.

### 2.2 Panel and 36 repeated-measure trajectories unchanged -- PASS

Panel hash `56e3c270...` is identical in the B2 protocol, the B2B protocol and the
on-disk file. 12 families, 12 unique `source_cluster_id`, 36 unique trajectory ids,
3 variants per family. Every `trajectory_sha256` in the panel recomputed against
`B1_CORRECTION_TRAJECTORIES.jsonl`: **0 mismatches**. Variants are repeated
measures within `source_cluster_id`; A sets `independence.source_family_unit: true`
and `variant_rows_independent: false`, and both analyses bootstrap on
`SOURCE_FAMILY`. Correct.

*Minor documentation inconsistency (non-blocking):* `B2_DEVELOPMENT_PANEL_DRAFT.json`
still carries `"status": "PROPOSED_NOT_FROZEN"`. The operative freeze is the
hash pin enforced by `B2B_REPAIR_RUN.require_protocol` (`panel_changed_after_freeze`
-> stop), which this audit verified. The stale status string should not be read as
an unfrozen panel.

### 2.3 Primary estimand is row-level `SET_BINDING_SET_ACCURACY`, family-then-across -- PASS

Definition independently reimplemented and confirmed:
candidate has exactly `program`, `evidence_refs`, `unit` keys, `desired_reference_set`
is non-null, program refs valid against rendered table cells, `evidence_refs` valid
and unique, program refs list-equal `evidence_refs`, and
`set(program refs) == set(desired_reference_set)`.

Aggregation confirmed: row-level score -> mean within each of 12 source families ->
mean across 12 families. Paired differences computed per family then averaged;
intervals resample 12 families (20 000 samples). `ALL_THREE_VARIANTS_CORRECT` is
carried only as `SEPARATE_DIAGNOSTIC_NOT_PRIMARY`. Correct.

Note on denominator: 4 of 36 trajectories have `status: UNRESOLVED` and therefore
`desired_reference_set: null`. Those rows are forced to `SET_BINDING_SET_ACCURACY:
False` by estimator construction and delivered UNKNOWN. This biases every arm
row-level accuracy downward by 4/36 equally, so **paired differences are
unaffected**. Correct and consistently applied.

### 2.4 First 192-token run: interface-truncation development run -- PASS, failures preserved

- 108 retained logical attempts (3 arms x 36), 116 physical generation calls.
- R and E each produced exactly `36 * 192 = 6,912` completion tokens -- 72/72 rows
  saturated the 192 cap. N finished cleanly (47 or 51 tokens, no truncation).
- Syntax first run: N and O `36/36 STRICT_WHOLE_JSON`; R and E
  `24 SYNTAX_ADAPTER_FAILURE + 12 EMBEDDED_JSON` each; E `0/36` legal patches.
- Conservative token bounds, independently reconstructed and correct:
  retained 67 696; unretained failed batch 8 calls / 3 482 prompt tokens /
  completion `[0, 1536]`; `actual_generation_tokens` explicitly `null`;
  bounds `[71 178, 72 714]`; deterministic-replay expectation 71 554.
- `B2_EVALUATION_PARTIAL_FAILURES.json` is preserved and records
  `N_BATCH_0_RAW_ROW_ERROR` (8-trajectory batch, `generation_outputs_retained:
  false`) plus three post-generation zero-call repairs, with
  `generative_raw_sha256_before_zero_call_recovery: a617afce...` and the final
  `a21456b3...` -- the 108 retained generative rows are byte-covered by the prior
  hash. `B2B_FAILURES.json` carries
  `first_run_unretained_generation_cost.tokens: UNKNOWN_NOT_INFERRED, preserved:
  true`. **No failure is erased.**

*Disclosure precision (non-blocking, see 9.3):* the top-level
`cost.total_scientific_generation_tokens: 67696` is the retained/logical figure;
the physical/bound figures sit in `execution_disclosure`. A skimming reader
understates GPU cost by up to 5 018 tokens. Cumulative physical generation calls
are 188 (116 + 72), not the 180 logical attempts reported in
`known_cumulative_B2_plus_B2B`.

### 2.5 B2B used exactly 72 new R/E attempts, no new training; N/O reused as first-run comparators -- PASS

`B2B_GENERATION_RECEIPT`: `new_generation_attempts: 72`,
`attempt_budget_remaining: 0`, `training_runs: 0`, `training_tokens: 0`,
`scientific_generation_call_failures: 0`. Raw contains exactly 72 rows, 36 R + 36 E.
`same_artifacts.comparators.reused_arms: [O_FROZEN_ORDINARY, N_NEUTRAL_RETRY]`
with `new_generation_attempts_for_comparators: 0`. This audit confirms O and N rows
are taken unchanged from the first run and are correctly labelled
`reused_comparator_metrics` in the analysis.

*Comparability caveat (non-blocking, see 9.3):* the reused N comparator is **not**
generation-configuration-matched to the new R/E. First-run N used the frozen
sampling configuration (`do_sample: true`, temperature 0.7, top_p 0.95) with
`max_new_tokens: 192` and no contract-only suffix, and terminated cleanly at
47-51 tokens. B2B R/E use greedy decoding, `max_new_tokens: 384`, and a
`contract_only_suffix`. R-N and E-N are therefore contrasts across decoding
configurations as well as arms. This does not rescue E (see 3.5) but it does mean
the small R-N gap of -0.028 should not be over-read.

---

## 3. Independent recomputation of the primary estimand

Row-level `SET_BINDING_SET_ACCURACY` (this audit, from raw text):

| Arm | Source | Correct / 36 | Family-then-across mean |
|---|---|---|---|
| `O_FROZEN_ORDINARY` | reused, first run | 27 | 0.750000 |
| `N_NEUTRAL_RETRY` | reused, first run | 26 | 0.722222 |
| `R_FULL_REVISION` | **B2B, new** | 25 | 0.694444 |
| `E_RESTRICTED_PATCH` | **B2B, new** | 0 | 0.000000 |

Paired differences, mean row-level difference within source family then across 12
families, 20 000-sample source-family bootstrap:

| Contrast | Mean | 95% source-family interval |
|---|---|---|
| E - R | **-0.694444** | [-0.916667, -0.444444] |
| E - N | **-0.722222** | [-0.944444, -0.472222] |
| R - N | **-0.027778** | [-0.194444, +0.138889] |

Per-family differences reproduced exactly, including the E-R per-family vector
`[-1,-1,-1,-1,0,-1,-1,0,0,-1,-0.333,-1]` and R-N
`[0,0,0,0,0,0,0,0,-0.333,+0.667,-0.667,0]`.

**Secondary paired completion** (`ALL_THREE_VARIANTS_CORRECT`, separate diagnostic):
O 8/12, N 8/12, R 8/12, E 0/12 families (originally-correct subset 6/7, 6/7, 5/7, 0/7).

**Method gate (B1 thresholds as substituted in `thresholds_from_B1_gate`):**

| Threshold | Required | Observed | Pass |
|---|---|---|---|
| `E_minus_N_min` | >= +0.03 | -0.722222 | **NO** |
| `E_minus_R_min` | >= +0.05 | -0.694444 | **NO** |
| `additional_originally_correct_family_damage_vs_R_max` | <= 0 | **+5** | **NO** |
| `eligible_subtype_direction_reversal_allowed` | false | reversal present | **NO** |

Every gate fails. The two effect thresholds are not marginal misses.

### 3.1 O transitions (row level, vs reused O)

| Arm | O correct -> correct | O correct -> lost | O wrong -> correct | O wrong -> wrong | O unknown -> unknown |
|---|---|---|---|---|---|
| N | 25 | 2 | 1 | 4 | 4 |
| R | 23 | 4 | 2 | 3 | 4 |
| E | 0 | **27** | 0 | 5 | 4 |

R repairs 2 O-error rows and damages 4 O-correct rows. E repairs nothing and
destroys all 27 rows that O had correct.

### 3.2 Originally-correct family damage -- +5 added vs R, confirmed

7 of 12 families are `originally_correct_on_original_variant`. Family-level
damage (O family mean 1.0, arm family mean lower), identical under both the
"all three O rows correct" and "O family mean == 1.0" rules:

- R damages **1**: `NAT_train_f1f2c2cb_27cb53a0`
- E damages **6**: `0417ded2`, `223d66c3`, `2c20edd3`, `abc6297d`, `f1f2c2cb`, `f440390f`
- **Added damage vs R = 5** (`0417ded2`, `223d66c3`, `2c20edd3`, `abc6297d`, `f440390f`)

Matches the task description of five added originally-correct family damages.
Against the gate ceiling of 0 this is a hard fail.

### 3.3 UNKNOWN / wrong delivery

| Arm | CORRECT | WRONG (target available, not met) | UNKNOWN (no target) |
|---|---|---|---|
| O | 27 | 5 | 4 |
| N | 26 | 6 | 4 |
| R | 25 | 7 | 4 |
| E | 0 | 32 | 4 |

The 4 UNKNOWN rows per arm are the `UNRESOLVED`-status trajectories with
`desired_reference_set: null`; they are correctly delivered UNKNOWN rather than
WRONG, and A reports `reasonable_unknown_target_unavailable: 4` for O, N and R.
`explicit_abstention_rows: 0` for all arms -- no arm abstains on its own.

**E delivery taxonomy -- see 9.1.** A reports `delivery: UNKNOWN = 36` and
`wrong_delivery: 0` for E, because no legal patch was ever applied and
`delivered_candidate` is null. Under a target-availability taxonomy E is 32 WRONG
+ 4 UNKNOWN. A does mitigate this by reporting
`O_correct_to_wrong_or_unknown: 27` and `interface_caused_unknown_delivery: 36`,
so the harm is not hidden; but `wrong_delivery: 0` must not be quoted alone.

### 3.4 Syntax, contract and truncation

| Arm / run | STRICT_WHOLE_JSON | EMBEDDED_JSON | SYNTAX_ADAPTER_FAILURE | truncated |
|---|---|---|---|---|
| N, first run | 36 | 0 | 0 | 0/36 |
| O, first run (frozen) | 36 | 0 | 0 | 0/36 |
| R, first run | 0 | 12 | 24 | **36/36 at 192** |
| E, first run | 0 | 12 | 24 | **36/36 at 192** |
| R, B2B | **0** | 36 | 0 | **36/36 at 384** |
| E, B2B | **0** | 36 | 0 | **36/36 at 384** |

**All 72 B2B generations are truncated at `MAX_NEW_TOKENS = 384`.** Verified row by
row: `completion_tokens == 384`, `finish_reason == MAX_NEW_TOKENS`,
`truncated_at_max_new_tokens == true` for every one of the 72 rows. Doubling the
output budget moved R/E from syntax-adapter failure to embedded-JSON-with-prose,
never to a contract-compliant object. `contract_only_output: 0` for both R and E
in B2B despite the added `contract_only_suffix`; N and O had `contract_only_output:
36` in the first run.

This is the strongest single piece of evidence for the interface label: **the
untrained ordinary parent emits strict whole JSON on 36/36 rows, while both trained
children emit zero contract-compliant objects across 72 attempts and 2x budget.**

### 3.5 Patch legality and hallucinated schema/hash fields -- E 0/72 legal across both runs

First run E: 0/36 legal (24 `PATCH_JSON_NOT_PARSEABLE`, 12 `patch_keys_mismatch`).
B2B E: 0/36 legal -- 16 `patch_schema_mismatch`, 20 `patch_keys_mismatch`. Total
**0 legal patches in 72 attempts**. Independent applier reproduces the stored
legality verdict 72/72.

Hallucinated patch schema/hash fields, verbatim from the fail-closed rejections:

| Emitted | Count | Contract requires |
|---|---|---|
| `target_sha264` | 5 | `target_sha256` |
| `target_sha2456` | 1 | `target_sha256` |
| `target_sha24` | 1 | `target_sha256` |
| `target_sha265` | 1 | `target_sha256` |
| JSON-Schema objects (`properties`, `required`) | 10 | patch object keys |
| JSON-Schema with `$schema`, `title`, `type` | 1 | patch object keys |
| bare `op`/`path`/`value` operation object | 1 | patch keys plus `operations` |

The model invents near-miss hash field names and emits JSON-Schema descriptions
instead of patch instances. This is a representation/contract failure of the
restricted-patch interface, not a decision-quality failure: E never reached the
point where the correctness of its set-binding choice could be measured. Note also
that the contract requires two 64-hex SHA-256 fields the model cannot compute --
the representation itself is arguably unlearnable at this scale and configuration.
That is an implementation-specific observation, not a statement about local editing.

### 3.6 Eligible-subtype diagnostics and the direction gate

Only 5 rows per arm carry `eligible_correction` (3 families, 2 subtypes):

| Subtype | Families | E - R (family level) |
|---|---|---|
| `ROW_AND_PERIOD_ROLE_MISBINDING` | 1 (`dac4e923`) | -1.0 |
| `ROW_ROLE_MISBINDING` | 2 (`b74eaf04`, `bdeeb701`) | 0.0, 0.0 |

Reproduces A exactly.

**Direction reversal -- structural, inherited from B1, not an E failure.**
Because `direction_component` is frozen to `O_CANDIDATE_SLOT_SKELETON`
(`patch_paths_allowed: []`, `direction_training_target: false`), the materialized
set-binding target takes O operand order with the reference cells substituted.
Executing the materialized target against the frozen reference:

| Family | Subtype | Gold value | Materialized target value |
|---|---|---|---|
| `b74eaf04` (2 rows) | ROW_ROLE_MISBINDING | +78.41 | **-78.41** |
| `bdeeb701` (1 row) | ROW_ROLE_MISBINDING | +1715.90 | **-1715.90** |
| `dac4e923` (2 rows) | ROW_AND_PERIOD_ROLE_MISBINDING | +937.40 | +937.40 |

**2 of 3 eligible families carry a sign-reversed set-binding target by
construction.** Consequently `eligible_subtype_direction_reversal_allowed: false`
cannot be satisfied on this panel by any E effect size. A records
`subtype_direction_pass: false` but does not state that the condition is
structurally unsatisfiable here. This is why answer correctness is correctly
`NOT_SCORED`: a perfect learner of this supervision would still deliver a
sign-reversed answer on those families.

### 3.7 Cost

| | First run | B2B | Cumulative |
|---|---|---|---|
| Logical generation attempts | 108 | 72 | 180 |
| Physical generation calls | **116** | 72 | **188** |
| Retained generation tokens | 67 696 | 66 592 | 134 288 |
| Unretained batch | 8 calls, 3 482 prompt, completion [0, 1 536] | -- | bounds [71 178, 72 714] first run |
| Padded input + completion | not asserted | 84 164 | -- |
| Token budget / remaining | 420 000 authorised | 180 000 / **113 408** | -- |
| Training runs / processed text tokens | 2 / 319 948 | **0 / 0** | 2 / 319 948 |
| GPU seconds | >= 719.46 recorded | 435.55 | -- |

B2B padded accounting independently reconstructed per batch
(R `8464+8464+4728+4288+2008 = 27 952`, E `8600+8600+4864+4424+2076 = 28 564`)
and matches both the frozen projection and the receipt exactly. The
`PADDED_BATCH_PROMPT_ACCOUNTING_SCALED_BY_ROW` accounting bug is honestly recorded
in `B2B_FAILURES.json` with `raw_rows_modified: false, rerun_performed: false` --
it was a receipt-side double-count, not a science failure. `power_energy_measurement:
UNAVAILABLE_NOT_INFERRED` throughout; no energy figure is invented.

---

## 4. Does the evidence support `INTERFACE_REPRESENTATION_FAILURE_STOP_R_E_CANDIDATE`?

**Yes, for this implementation only -- with the scope in section 9.**

Grounding in the frozen stop condition, not a post-hoc label:
`B2B_PROTOCOL_FROZEN.stop_conditions.pervasive_interface_definition` fires when
either R or E has more than 18 of 36 syntax-adapter failures **or** more than 18
of 36 interface-caused UNKNOWN deliveries.

- Syntax-adapter clause: R 0/36, E 0/36 -- **does not fire**.
- Interface-caused UNKNOWN clause: E 36/36 (32/36 even after crediting the 4
  target-unavailable rows to the reasonable-UNKNOWN taxonomy used for R) --
  **fires decisively, 32 > 18**.

Supporting evidence, all independently confirmed:

1. 0/72 B2B outputs are contract-compliant strict whole JSON; 72/72 are embedded
   JSON with prose, against 36/36 strict for the untrained ordinary parent.
2. 72/72 B2B generations truncate at `MAX_NEW_TOKENS = 384`, after 72/72 truncated
   at 192 in the first run. The interface never terminates cleanly at either budget.
3. E emits 0 legal patches in 72 attempts across both runs, failing on hallucinated
   schema/hash field names and JSON-Schema objects rather than on set-binding choice.
4. D exit rule clause 1 (if the repaired run still has pervasive syntax/interface
   failures, stop the R/E candidate as an interface/representation failure) is met.
5. The stop is correctly taken **before** confirmation: `stop_before_confirmation:
   true`, `confirmation_outputs_inspected: false`,
   `authority_read_receipt.confirmation_artifact_paths_accessed: []`.

The label is therefore supported and the STOP is correct. What it must **not** be
used to say is recorded in section 9.

---

## 5. Confirmation non-access -- PASS

- No file whose name contains confirmation exists anywhere in the tree.
- `B2_PROTOCOL_FROZEN.confirmation_outputs_inspected: false`;
  `B2B_PROTOCOL_FROZEN.authority_read_receipt.confirmation_artifact_paths_accessed: []`.
- All 72 trajectories: `label_reference_identity.confirmation_gold: null`,
  `exposure.eligible_for_current_confirmation: false`,
  `exposure.role: EXPOSED_DEVELOPMENT_SUPERVISION`, `human_gold: false`.
- No confirmation source or output was read or generated by B2, B2B or this audit.
  The `exposure_clean_confirmation` allocation named in the D decision remains
  unreleased.

## 6. Information parity and claim boundaries -- PASS

`r_e_feedback_content_diff.identical: true` on all 72 trajectories; the minimal
edit instruction is **not** in the deployment feedback
(`minimal_edit_instruction_in_deployment_feedback: false`);
`deployment_feedback.origin: NEUTRAL_VISIBLE_INPUT_ONLY`;
`teacher_reference.origin: FROZEN_DEVELOPMENT_REFERENCE`;
`training_reference.origin: EXISTING_DETERMINISTIC_TASK_REFERENCE`.

The supervision is **reference-derived development supervision**, not feedback.
`feedback_learning_claim: NOT_QUALIFIED` on all 72 rows and in both protocols.
Answer correctness is `NOT_SCORED` everywhere; `program_value_audit_only_not_scored`
is correctly quarantined as audit-only. New-source generalization `NOT_TESTED`.
These boundaries are correctly carried into `TASK_RESULT_A_B2B.json`.

---

## 7. What the evidence does and does not establish

**Established, for this implementation only:**

1. On this frozen 12-family exposed development panel, with this same-start
   training configuration and this restricted-patch contract, the E restricted-patch
   arm produced 0 legal patches in 72 attempts and 0/36 set-binding accuracy.
2. The R full-revision arm recovered to 25/36 set-binding accuracy but is
   **below neutral retry (26/36) and below frozen ordinary (27/36)**; R - N =
   -0.0278, source-family interval [-0.194, +0.139] -- indistinguishable from zero
   and on the negative side. The recovered 25/36 is real and is still a negative.
3. The trained children cannot emit a contract-compliant object at either 192 or
   384 tokens, while the untrained parent can. That is an interface/representation
   failure of this training + contract combination.
4. E added 5 originally-correct family damages relative to R, against a ceiling of 0.

**Explicitly NOT established -- none of the following may be promoted:**

- **Not feedback-derived learning.** Supervision is frozen reference-derived
  set-binding targets. `feedback_learning_claim: NOT_QUALIFIED`.
- **Not answer correctness.** `answer_correctness: NOT_SCORED`. The estimand is a
  visible evidence-cell set match, and 2 of 3 eligible families carry a
  sign-reversed target by construction (section 3.6).
- **Not new-source confirmation.** No confirmation source or output was read or
  generated. `confirmation_claim: NONE`, `new_source_generalization: NOT_TESTED`.
- **Not a claim that local-edit or feedback methods are ineffective in general.**
  The failure is of the restricted replace-only patch *representation* under this
  model, this LoRA configuration (r=16, q_proj/v_proj, 128 steps, 256 rows, 12
  source tasks) and this contract, on this 12-family development panel. E never
  produced one legal patch, so its decision quality was never measured. The correct
  reading is that this representation failed, not that local editing carries no
  useful information.
- **Not a 24-family-panel or semantic-correctness gate result** (section 9.2).

---

## 8. Discrepancies found

No numerical discrepancy between this audit independent recompute and the A
analysis. All 288 rows agree on syntax source, set accuracy and patch legality;
all family scores, paired differences, intervals, O transitions, damage counts and
token totals reproduce exactly. The findings below are scope, labelling and
disclosure issues, not scoring errors.

---

## 9. Conditions attached to the verdict

Verdict **`CONDITIONAL`**: the stop decision and the raw/derived numbers are
accepted as accurate; the status label `INTERFACE_REPRESENTATION_FAILURE_STOP_R_E_CANDIDATE`
may stand only if the following four disclosures are carried into any downstream
record that quotes it.

**9.1 Correct or footnote the E delivery taxonomy.**
`wrong_delivery: 0` with `delivery: UNKNOWN = 36` for E reads as no harm when
taken alone. Either re-label E as 32 WRONG (target available, not delivered) + 4
UNKNOWN under a target-availability taxonomy, or require
`O_correct_to_wrong_or_unknown: 27` to be quoted in the same breath. Relatedly,
`interface_caused_unknown_delivery: 36` over-counts by 4: the same
`UNRESOLVED`-status rows are credited as `reasonable_unknown_or_abstention: 4` for
O, N and R but attributed wholly to the interface for E. Correcting to 32 leaves
the frozen `pervasive_interface_definition` firing (32 > 18) and changes no
conclusion.

**9.2 Disclose the B1 -> B2 threshold substitution.**
`B1_D_FREEZE_GATE.md` states the minimum useful effect in final semantic
correctness on the full eligible evaluation population, and allows E to damage
at most one additional originally-correct family **per 24-family panel**.
`thresholds_from_B1_gate` substitutes `SET_BINDING_SET_ACCURACY` on a **12-family**
panel with `additional_originally_correct_family_damage_vs_R_max: 0`. The
substitution is stricter and is documented in the frozen protocol, but the field
name implies literal inheritance. E fails by a wide margin under either reading
(-0.72 vs +0.03; +5 damage vs 0 or vs 1-per-24), so no decision changes. Do not
report that E failed the B1 gate as though the B1 estimand had been scored.

**9.3 State that R is a method-level negative alongside the interface label.**
R is **not** an interface failure in the scoring sense: 36/36 parseable,
36/36 executable, 25/36 set-accurate. Its 25/36 sits below neutral retry 26/36 and
frozen ordinary 27/36. The joint status label covers two distinct outcomes --
E is a representation failure, R is a valid-output method negative. If the label
is quoted without R 25/36 < N 26/36, it erases a real result. Also carry: the
reused N comparator is sampling-configured (temperature 0.7 / top_p 0.95, 192 cap,
no contract suffix) while B2B R/E are greedy at 384 with the contract suffix, so
the small R - N gap is not configuration-matched; cumulative physical
generation calls are 188, not the 180 logical attempts; and the top-level
total token figure of 67 696 is the retained/logical cost of the first run only.

**9.4 Record that the direction gate is structurally unsatisfiable on this panel.**
2 of 3 eligible families carry a sign-reversed set-binding target by construction
(section 3.6). `subtype_direction_pass: false` is therefore inherited from the B1
direction decomposition and cannot be repaired by any E effect size. It must not be
read as an additional E failure, and it is the reason answer correctness is
correctly out of scope.

---

## 10. Exact scope of the accepted claim

Accepted, bounded by all of:

> On the frozen 12-family exposed development panel for
> `FEEDBACK_LEARNING_PHASE_B_20261026`, under the same-start training configuration
> of `phaseb-b2-same-start-a-20261026` (base `Qwen3-4B` plus one frozen ordinary
> adapter, two LoRA child runs, 128 optimizer steps, 256 rows, 12 source tasks)
> and the `b1_local_patch_v1` restricted replace-only patch contract, the R/E
> candidate is stopped as an interface/representation failure of **this
> implementation**. Both trained children produced zero contract-compliant objects
> in 72 repair-run attempts at `max_new_tokens: 384` after 72 first-run attempts at
> 192, while the untrained ordinary parent produced 36/36 strict whole JSON. E
> produced 0 legal patches in 72 attempts (hallucinated schema/hash field names)
> and 0/36 `SET_BINDING_SET_ACCURACY`; R produced 25/36, below neutral retry 26/36
> and frozen ordinary 27/36. E - R = -0.694 [-0.917, -0.444], E - N = -0.722
> [-0.944, -0.472], R - N = -0.028 [-0.194, +0.139]; E added 5 originally-correct
> family damages vs R against a ceiling of 0. Stopped before confirmation; no
> confirmation source or output was read or generated.

Forbidden extensions of this claim: feedback-derived learning; answer correctness;
new-source or out-of-panel generalization; any assertion that local-edit, patch-based
or feedback-driven repair methods are ineffective in general; any use of the 12-family
development numbers as a confirmation result; any reading of `subtype_direction_pass:
false` as an E-specific failure; any comparison to a 24-family-panel semantic-correctness
gate as though that estimand had been scored.

---

## 11. Audit trail

- Independent recompute: parse, restricted-patch apply and set-binding accuracy
  re-implemented from `B1_LOCAL_PATCH_CONTRACT.json` and the raw text; no A analysis
  module imported. Result: 288/288 row agreement on syntax source, set accuracy and
  patch legality; 36/36 agreement on deterministic-control rows.
- All frozen hashes recomputed and matched (section 2.1).
- Panel trajectory hashes recomputed: 0 mismatches (section 2.2).
- B2B per-batch padded prompt positions independently reconstructed and matched
  (section 3.7).
- Materialized set-binding targets executed against frozen reference values to
  establish sign reversal (section 3.6).
- Zero model, judge, training, endpoint, database or production calls by this audit.
- Temporary recompute scratch from this audit was removed after the figures above
  were extracted; it is not an audit deliverable and is not part of the evidence set.
