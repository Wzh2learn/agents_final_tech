# C Independent No-Go And Premise Audit

**Nature of this document.** Advisory audit report. It reports; it does not repair. No
A-owned or D-owned artifact was modified. Adjudication of every filing recommendation
belongs to the human owner.

**Audited object and baseline.** Goal `DECISION_RESIDUAL_PILOT_20261026`, task
`phaseb-postb-nogo-audit-c-20261026`, bound to commit
`19ddd7feffe90779f021304345ce894550c92816`. Audited artifacts: `a_prepare/*`,
`A_PREPARE_TASK.md`, `D_PREMISE_CORRECTION.md`, `D_NO_GO_DECISION.md`,
`D_TATQA_TEXT_SCREEN.py`, `D_TATQA_TEXT_SCREEN.json`. Baseline of already-known anomalies
is `memory/THREADS.md` (2026-10-26) plus `memory/STATE.md`; hits inside that baseline are
reported as confirmed-known, not as new findings.

**Independence declaration.** This auditor authored neither the A artifacts nor the D
artifacts; file ownership for this role is limited to `audits/C_NO_GO_AUDIT.md` and
`audits/TASK_RESULT_C_NO_GO.json`. Disclosed deviation: `D_PREMISE_CORRECTION.md` and
`D_NO_GO_DECISION.md` (both conclusion-bearing) were read before the reasoning chain was
formed. Mitigations actually executed, not promised: (a) three sub-agents were dispatched
under explicit prohibition against reading those two files, and each gathered evidence by
raw command from primary carriers; (b) the central numeric chain (TAT-QA coverage) was
re-derived from an independent implementation before the corresponding reported figures
were compared against it; (c) every finding that points at A's own work is recorded in full
below and not softened. Sub-agent evidence was used only where re-verified first-hand,
except the search-zero results for FinQA provenance, which this auditor re-ran
independently.

---

## 1. Claim list and baseline

### 1.1 Claims under audit

| # | Claim | Asserted by | Carrier |
|---|---|---|---|
| K1 | Training activates only the child adapter; parent forward computation was not established | D | `D_PREMISE_CORRECTION.md` section 1 |
| K2 | Canonicalization / SHA-256 / integrity metadata belong in tools, not in the model | D | section 2 |
| K3 | 5 qualified set-binding corrections across 3 source families | D, A | section 3; `PREMISE_VERIFICATION.json` |
| K4 | 39 correction + 217 no-op rows per arm, 256 rows, 36 trajectories, 12 tasks, 7 repeats | D, A | section 3; `PREMISE_VERIFICATION.json` |
| K5 | Target is a set-binding proxy; 3 of 5 eligible targets sign-reversed vs audit reference | D, A | section 4 |
| K6 | O/N strict whole JSON; repaired R/E 36/36 embedded JSON and 36/36 `MAX_NEW_TOKENS` | D, A | section 5 |
| K7 | Missing explicit EOS is not a verified root cause (TRL handles EOS automatically) | D | section 5 |
| K8 | O 27/36, N 26/36, R 25/36, E 0/36 are `SET_BINDING_SET_ACCURACY` counts, not answer correctness | D | Metric Correction |
| K9 | Prompt identity = Git blob `5c3f970d` + canonical GB10 LF `327fb04a` + Windows raw `e4c53572`, the last noncanonical | D | Evidence Identity |
| K10 | C1 residual fully explained by visible role equality (4/4) | A | `CANDIDATE_SCREEN.json` |
| K11 | C2 FinQA top-k/radius coverage 168/171/177/186/195 over 198 | A | `CANDIDATE_SCREEN.json` |
| K12 | TAT-QA text-only: top-3 378, top-5 385, top-3+neighbor 385, top-10 389 / 389 | D | `D_NO_GO_DECISION.md` |
| K13 | Zero model / judge / training / production / confirmation calls in this task | A, D | `PREMISE_VERIFICATION.json`; `D_NO_GO_DECISION.md` |
| K14 | Verdict `NO_GO_FOR_MODEL_PROBE`; no candidate retains a deployable residual | D | `D_NO_GO_DECISION.md` |

### 1.2 Baseline (already-known; not new findings)

From `memory/THREADS.md`: `PHASE-B-VALIDITY` (parent adapter not activated; method-level
attribution must narrow), `ADAPTER-SEMANTICS` (strict/embedded split already verified),
`UNIT-OBSERVABILITY`, `LEDGER-340`, `NEXT-C2-SUPERVISION`, `C2-FEEDBACK-REPAIR`
(implementation stopped; no clean method-level negative), `SKILL-METADATA-DEBT`.
From prior memory: the direction leak was closed by freezing direction to the O candidate,
which is precisely what produces sign-reversed targets. K1, K2, K5 and the R/E stop are
therefore **confirmations of the baseline**, not new discoveries.

---

## 2. Verification by claim

### 2.1 K1 child-only adapter activation - VERIFIED

Primary carrier `research/feedback_learning_phase_b_20261026_v1/b2/B2_TRAIN_RUN.py`:

- line 704: `model = PeftModel.from_pretrained(model, PARENT_ADAPTER, adapter_name="ordinary_parent")`
- lines 710-720: `model.add_adapter("b2_child", LoraConfig(...))`
- line 721: `model.set_adapter("b2_child")`
- line 731: `trainer = SFTTrainer(...)` and line 758: `result = trainer.train()`

`set_adapter` precedes both trainer construction and training, so the active adapter at
loss/backward time is `b2_child` only. Installed PEFT 0.21.2
(`agents_final_tech/venv/lib/python3.12/site-packages/peft`, `set_adapter` docstring)
states verbatim: *"Only one adapter can be active at a time."* Lines 761-763 raise if the
`ordinary_parent` tensor hash changed, which proves the parent **weights** were preserved;
it does not prove parent **forward** computation. K1 holds. Baseline item `PHASE-B-VALIDITY`.

### 2.2 K2 tool-owned integrity fields - VERIFIED, and the defect is confirmed in source

Hashing is tool-side (`sha256_file`, `canonical_sha256`, `tensor_group_hash`). But the E
arm contract puts integrity fields on the model: `target_prompt` at
`B2_TRAIN_RUN.py:323-328` instructs - *"Return exactly one strict patch JSON object with
keys schema, candidate_sha256, target_sha256, and operations."* The model is therefore
required to emit SHA-256 values. D's correction is a genuine defect of the old E design,
not a hypothetical. Cross-check: `empty_patch` (lines 370-376) sets both `candidate_sha256`
and `target_sha256` to `canonical_sha256(candidate)` - correct, since an empty patch means
target equals candidate; not a bug.

### 2.3 K3 5 corrections / 3 source families - VERIFIED

Recomputed from row-level `B1_CORRECTION_TRAJECTORIES.jsonl` (72 rows), not from any
summary: `set_binding_component.status` counts
`PRESERVE_ORIGINAL 56, UNRESOLVED 5, SET_PRESERVED_DIRECTION_UNRESOLVED 6, QUALIFIED 5`.
The 5 QUALIFIED rows span exactly 3 source tasks:
`NAT_train_dac4e923_dccd9dbf` (2 rows), `NAT_train_bdeeb701_c6f0281e` (1),
`NAT_train_b74eaf04_caa15292` (2). K3 holds.

### 2.4 K4 39/217 composition - VERIFIED in total, with an undisclosed pad

`B2_PROTOCOL_FROZEN.json` -> `training`: `final_eligible_correction_rows_per_arm 39`,
`final_no_op_and_unresolved_rows_per_arm 217`, `final_rows_per_arm 256`,
`unique_trajectories_per_arm 36`, `unique_source_tasks_per_arm 12`, `repeats 7`,
`eligible_correction_rows_per_base_cycle 5`,
`no_op_and_unresolved_rows_per_base_cycle 31`,
`loss_normalization` = *"mean over all non-padding prompt-plus-target tokens; no sample
weighting"*. `B2_TRAIN_RUN.py:744` `completion_only_loss=False` corroborates the loss
scope. 128 optimizer steps x 2 grad-accum x 1 sample = 256, matching the row count.

Arithmetic check: 31 x 7 = 217 exactly. But 5 x 7 = 35 != 39, and 36 x 7 = 252 != 256. The
gap is explicit at `B2_TRAIN_RUN.py:407-409`:

    repeated = [copy.deepcopy(row) for row in rows for _ in range(7)]
    eligible = [row for row in repeated if row["eligible_correction"]]
    repeated.extend(copy.deepcopy(row) for row in eligible[:4])

Because `repeated` expands each base row 7x consecutively, `eligible[:4]` is four copies of
the single earliest-appearing eligible base row. Result: **one** of the 5 corrections
receives 7 + 4 = 11 of the 39 correction rows and the other four receive 7 each
(11 + 4x7 = 39). Both D and A describe this as "7 repeats" of 5 corrections; neither names
the pad. The 39/217 figures are correct; the stated construction is incomplete. See
incident `training-composition-undocumented-asymmetric-pad`.

### 2.5 K5 proxy target scope and sign-reversal - VERIFIED

Applied each `r_target` patch set to the actual `o_output.parsed_candidate.program` and
compared direction against `frozen_reference_target_for_audit.program`:

| Trajectory | Training target | Audit reference | Verdict |
|---|---|---|---|
| `dac4e923::original` | R2:C2 - R4:C2 | R2:C2 - R4:C2 | match |
| `dac4e923::irrelevant_change` | R2:C2 - R4:C2 | R2:C2 - R4:C2 | match |
| `bdeeb701::relevant_change` | R3:C1 - R2:C1 | R2:C1 - R3:C1 | **sign-reversed** |
| `b74eaf04::original` | R11:C1 - R11:C2 | R11:C2 - R11:C1 | **sign-reversed** |
| `b74eaf04::irrelevant_change` | R11:C1 - R11:C2 | R11:C2 - R11:C1 | **sign-reversed** |

**Sign-reversed = 3 of 5**, exactly as claimed (equivalently 2 of 3 source families).
Evidence-set equality holds in all 5; unit is preserved in all 5; `direction_component`
carries `training_target: false` and `status: FROZEN_TO_O_CANDIDATE`; every row is
`frozen_reference_target_qualification: AUDIT_ONLY_NOT_A_TRAINING_TARGET`. R's prompt
(`B2_TRAIN_RUN.py:320-321`) orders *"Preserve O's operator, operand order, and unit."* K5
holds in full. Baseline-consistent (prior direction-leak closure), not new.

---

### 2.6 K6 output layers - VERIFIED

`b2/B2_DEVELOPMENT_ANALYSIS.json`: `strict_whole_json 36` for `O_FROZEN_ORDINARY`,
`N_NEUTRAL_RETRY`, `ORDINARY_SUPERVISION_CONTROL`; `embedded_json 0` for those arms; and
`embedded_json 12` / `strict_whole_json 0` for `R_FULL_REVISION` and `E_RESTRICTED_PATCH`
in the pre-repair run. `b2b/B2B_DEVELOPMENT_ANALYSIS.json` repaired arms:
`embedded_json_non_contract_output 36` and `truncated_at_max_new_tokens 36` for both
`R_FULL_REVISION` and `E_RESTRICTED_PATCH` (72 `MAX_NEW_TOKENS` finishes total).
E first fails on keys/schema - `structural_target_exact 0`, `program_executable 0`,
`interface_caused_unknown_delivery 36`, `syntax_adapter_failure 0` - so the hash fields are
an additional contract burden and not a proven sole cause. K6 holds.

### 2.7 K7 EOS non-root-cause - VERIFIED

Installed TRL 1.14.1 contains 85 `eos_token_id` / `_get_eos_token_id` sites, including
automatic propagation from tokenizer to `model.generation_config` and post-EOS masking
(`chat_template_utils.py`, `gkd_trainer.py`). No evidence was found that a missing explicit
EOS token caused any failure. K7 correctly demotes EOS from root cause to unproven.

### 2.8 K8 metric correction - VERIFIED

`b2b/B2B_DEVELOPMENT_ANALYSIS.json` gives `SET_BINDING_SET_ACCURACY_count` 25/36 for
`R_FULL_REVISION` and 0/36 for `E_RESTRICTED_PATCH`, with `reused_comparator_metrics`
carrying `N_NEUTRAL_RETRY` 26/36; `b2/B2_DEVELOPMENT_ANALYSIS.json` gives
`O_FROZEN_ORDINARY` 0.75 = 27/36. All four are on the same 36 exposed development rows -
O and N enter as explicitly labelled reused comparators, so the list is not a mix of
incomparable panels. `answer_correctness_scored` is `False` in both files and
`claim_boundary.answer_correctness` is `NOT_SCORED`. D's disclosure that R-N has an
unmatched configuration is correct: R is repaired/embedded-output while N is strict whole
JSON. K8 holds.

### 2.9 K9 prompt identity binding - VERIFIED as three distinct labels; one nuance unstated

All recomputed first-hand at commit `19ddd7feffe90779f021304345ce894550c92816` (which is
also `HEAD`):

- Git blob: `git rev-parse 19ddd7fef:docs/research/LOOP_D_RESEARCH_PROMPT.md` ->
  `5c3f970db754b0ce712161373c74fa34c36d42d0` (type blob, 22776 bytes). Working-tree
  `git hash-object` reproduces the same id; `git diff 19ddd7fef -- <path>` is empty.
- Canonical GB10 LF SHA-256: `git cat-file blob 5c3f970d | sha256sum` ->
  `327fb04ae18ff6e057338f28686389d183c24a797e22c325e8557cbea58f0cbe`. Matches the
  on-disk `sha256sum`.
- Windows raw SHA-256: LF->CRLF (`sed 's/$/\r/'`) then SHA-256 ->
  `e4c53572a01e1d0b6a86e7377948a8e2416dd3d9ffbcce43f2a40d715d4b7ef2`, 22972 bytes.

The three are distinguished and correctly labelled. Two nuances D leaves unstated:
(i) the stored blob is pure LF (0 CR bytes, 196 LF bytes), so the raw digest and the
canonical-LF digest **coincide** - only two distinct SHA-256 values exist among the three
labels; (ii) `.gitattributes` has no rule matching this path (`git check-attr` was blocked;
the single `.gitattributes` was read in full and contains no `docs/**` pattern), so no
line-ending conversion is configured. D's label *"noncanonical line-ending view; not the
authority digest"* is correct.

### 2.10 K12 TAT-QA text-only screen - INDEPENDENTLY REPRODUCED EXACTLY

Pinned source re-hashed first-hand:
`/home/testuser/wzh/projects/agents_final_tech/data/research/tatqa_raw_2026/tatqa_dataset_dev.json`
-> `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`, matching
`D_TATQA_TEXT_SCREEN.json.input_sha256`. 278 records, 1668 questions,
`answer_from` counts text 389, table-text 507, table 772.

Rather than re-run `D_TATQA_TEXT_SCREEN.py` (sklearn is not importable under this
sandbox), TF-IDF + cosine was **reimplemented independently in pure NumPy** to sklearn's
documented defaults (`lowercase`, `ngram_range=(1,2)`, `smooth_idf=True`, sublinear_tf
off, L2 norm, token pattern `(?u)\b\w\w+\b`) with the same order tie-break:

| Method | top-3 | top-5 | top-3 + top-1 neighbor | top-10 |
|---|---|---|---|---|
| Reported (D) | 378 | 385 | 385 | 389 |
| **C independent recompute** | **378** | **385** | **385** | **389** |

Exact match on all four counts. Robustness sweep (independent variants):

| Variant | top-3 | top-5 | neighbor | top-10 |
|---|---|---|---|---|
| tfidf (1,2) smooth | 378 | 385 | 385 | 389 |
| tfidf (1,1) smooth | 377 | 385 | 384 | 389 |
| tfidf (1,2) sublinear | 378 | 386 | 385 | 389 |
| tfidf (1,2) no smoothing | 380 | 386 | 385 | 389 |
| word overlap (unigrams) | 378 | 388 | 385 | 389 |

The conclusion is not an artifact of one vectorizer configuration; a plain word-overlap
baseline reaches 388/389 at top-5.

Structural checks (not in D): `empty_gold_among_text = 0`, so no question is trivially
covered by an empty gold set; `gold_refs_not_matching_any_order = 0`; 1668 unique UIDs;
gold size 381x1 + 8x2.

**Degenerate-control caveat.** Paragraph counts per record: min 2, mean 4.878, max 26. For
text questions, 130/389 have at most 3 paragraphs, 262/389 at most 5, **359/389 at most
10**. So top-10 is identical to always-expand for 92.3 percent of the panel, and top-5 is
already always-expand for 67 percent. The `top-10 = 389/389` figure therefore carries
little retrieval information - it is largely restating "give every paragraph". This does
**not** weaken the no-go; it strengthens it (there is no acquisition headroom to exploit).
It does mean the screen should not be cited as evidence that retrieval ranking works.

Residual decomposition: top-3 misses 11; top-5 closes 7 of them leaving 4
(`e302a7ec` 14 paras, `32b27169` 7, `5486fae6` 7, `5ebb9f4f` 7); top-10 closes all 4,
3 of which are degenerate. **Residual after always-expand / larger top-k = 0.**

---

### 2.11 K11 FinQA snapshot - SOURCE-SCOPE RESTRICTION NOT RESPECTED BY A; CORRECTED BY D

Negative provenance result, self-proved across four search forms from repo root:

1. grep for `top_3_radius_1|top_3_radius_5|text_only_gold_denominator` -> only
   `a_prepare/CANDIDATE_SCREEN.json`, `a_prepare/A_PREPARE_RESULT.json`
2. grep -rli `radius` over `research/finqa_causal_exposure_20261010/` and
   `research/finqa_v2_20261010/` -> **zero hits**
3. grep for `195/198|186/198|177/198|171/198|168/198|radius 5|radius 2|radius-5|radius-2`
   -> only `a_prepare/` files (plus `PROBE_CONTRACT_DRAFT.json` future-arm wording)
4. grep for `text_only_gold|text-only gold|198 text` -> only `a_prepare/` files

The figures 168/171/177/186/195 over denominator 198 have **no prior frozen receipt
anywhere in the repository**. They were produced inside this task by a fresh deterministic
scan (`CANDIDATE_SCREEN.json.deterministic_scan`) over
`/home/testuser/wzh/phase1a_staging_20260925/finqa/dev.json`. That is using the FinQA
snapshot as a **new task source**, which the task restriction forbids. They cannot be
relabelled "historical evidence", because no historical carrier exists.

D's disposition is the correct one: *"The FinQA snapshot may remain historical evidence but
is not reauthorized as a new task source. It is excluded from the new candidate claim."*
D then supplies an independent, unrestricted screen (TAT-QA) that reaches the same
practical conclusion. The NO_GO therefore does not rest on FinQA.

### 2.12 K13 zero model / judge / training / production / confirmation source - VERIFIED

Independently hunted for counter-evidence and found none:

- Directory inventory: 12 files, all `.md/.json/.jsonl/.py`. No raw generation dumps,
  checkpoints, judge logs, network captures, or run transcripts.
- Repo-wide freshness (find -newermt 2026-10-26 11:08): the only post-checkout writes are
  the 12 task files and the audit harness's own state. No model output created today.
- Network sweep: only `endpoint_calls: 0` and the prohibition text in
  `A_PREPARE_TASK.md:12`. Zero hits for `requests.`/`httpx`/`urllib`/`openai`/`anthropic`/
  `api_key`/hosts. Model-name sweep: zero hits.
- The only executable artifact, `D_TATQA_TEXT_SCREEN.py`, imports `argparse`, `hashlib`,
  `json`, `pathlib`, `sklearn` only - local TF-IDF, no network, no model.
- `git status --porcelain` -> `?? research/decision_residual_pivot_20261026_v1/` only,
  zero modified tracked files (corroborates `old_phase_b_files_modified: 0`).
- `B2_PROTOCOL_FROZEN.json.confirmation_outputs_inspected = False`; selected examples are
  marked `EXPOSED_DEVELOPMENT_ONLY` /
  `ASSUMED_EXPOSED_BY_TASK_DIRECTIVE_FOR_ALL_FUTURE_CONFIRMATION`, which bars future
  confirmation reuse rather than consuming a confirmation set.
- `probe_release.authorized_generation_attempts / judge_calls / training_runs /
  production_calls` are all 0; `PROBE_CONTRACT_DRAFT.json` is
  `NOT_EXECUTED_ZERO_AUTHORIZATION`.

Residual caveat (not counter-evidence): the zero-call conclusion rests on absence of
contradicting artifacts plus self-receipts, because the producing work left no independent
call ledger. Two deterministic dev-dataset screens were computed today (FinQA and TAT-QA);
both are labelled development screening with examples marked exposed, and no in-repo
document designates either dataset as a sealed confirmation source.

---

## 3. Residual determination (task item 4)

**Neither candidate retains a deployable residual.**

- **C1 `CONDITIONAL_EVIDENCE_ROLE_APPLICABILITY` - no residual.** After metadata/period
  rules (including row position), every selected failure is determined by visible role
  binding. Exact cache cannot create a decision and cannot establish a learned residual.
  The panel is program-generated same-number/same-delta collision fixtures
  (`case_type: same_number`), not natural post-feedback decision traces - the tasks
  themselves carry `role_match: false` and `expected_decision: WRONG_ROLE` by construction.
  All four model failures share one shape: the model computes a zero difference of two
  identical numbers, gets `numeric_match: true`, and returns `SUPPORTED` where `WRONG_ROLE`
  is expected.
- **C2 `VERIFIABLE_EVIDENCE_ACQUISITION` - no residual.** FinQA is excluded as a source.
  On the unrestricted TAT-QA text-only screen the residual after top-5 is 4/389 (1.03
  percent), all 4 closed by top-10 or always-expand, 3 of them degenerately. Always-expand
  is cheap here (mean 4.878 paragraphs).

**Scope limit of this determination.** The screens measure coverage, not cost. A
cost-aware expansion policy (saving tokens versus always-expand on the long-tail records
with 14-26 paragraphs) was not evaluated and no cost evidence was gathered. That is an
untested dimension, not a surviving residual: no deployable action with an unsupplied value
was ever instantiated with evidence, which the pre-probe gate requires. The correct next
requirement is unchanged and is stated correctly by both A and D.

---

## 4. Incidents (fingerprint-named; filing recommended, not performed)

| Fingerprint | Severity | Symptom | Root cause | Premise violated | Disposition |
|---|---|---|---|---|---|
| `authority-digest-compared-without-line-ending-normalization` | medium | `PREMISE_VERIFICATION.json.binding.authority_hash_discrepancy` = `DECLARED_PROMPT_SHA256_NOT_FOUND_IN_GIT_HISTORY`; `A_PREPARE_RESULT.json` calls it a `binding_metadata_exception` | The Windows-raw CRLF digest `e4c53572` was compared against LF-stored content digests with no matching normalization. The digest is not missing - it is the LF->CRLF view of blob `5c3f970d` at the bound commit. | Task item 2: the three digests must be distinguished | **needs new filing** - reclassify as a false positive; the binding is sound |
| `binding-receipt-hash-stale-after-edit` | medium | `PREMISE_VERIFICATION.json` records `D_PREMISE_CORRECTION.md` SHA-256 `9294a81b0d70fec9...`; the file now hashes `1a7796999ea5c31e...` (3909 bytes). `A_PREPARE_TASK.md` still matches its recorded `5c2f258bfb84c8cc...`. | `D_PREMISE_CORRECTION.md` mtime 11:47 postdates the verification at 11:39; the file was edited after being hashed. | Authority/handoff closure must carry current hashes | **needs new filing** - re-bind or re-hash; premise facts remain independently verified |
| `simple-baseline-figure-exceeds-stated-rule` | high | `CANDIDATE_SCREEN.json` claims `four_selected_failures_explained: 4` for the rule "requested_role equals candidate_role; any row-label or period mismatch is WRONG_ROLE". That rule explains 3 of 4. | `NR_development_1582_N2` has identical visible `row_label` ("Adjusted operating costs1") and `period` ("2019") for `requested_role` and `candidate_citation`; the table contains that label twice (row indices 4 and 9). Only row **position** distinguishes them. | Task item 4 / pre-probe gate: the named baseline must actually explain its stated count | **needs new filing** - correct to 3/4 under the stated rule, 4/4 under a positional-role rule. Disposition unchanged: metadata rules are inside the stated control battery, so still no residual |
| `training-composition-undocumented-asymmetric-pad` | medium | 39 correction rows are described as 5 corrections x 7 repeats. 5 x 7 = 35. | `B2_TRAIN_RUN.py:409` appends `eligible[:4]` - four extra copies of the single earliest eligible correction, giving it 11/39 weight while the other four get 7/39. | Disclosed-confound completeness | **needs new filing** - disclose the pad and the resulting 11/7/7/7/7 weighting; it strengthens rather than weakens the "small and repeated" caution |
| `restricted-source-used-as-new-task-source` | high | A's `CANDIDATE_SCREEN.json` runs a fresh `deterministic_scan` over the FinQA dev snapshot and reports 168/171/177/186/195 over 198 as `simple_baseline_evidence`. | The FinQA snapshot was re-authorized implicitly as a task source. No prior receipt exists (four-form zero-hit search). | Task item 3: FinQA is historical evidence only, not a new task source | **needs new filing** - D's exclusion is the correct disposition; do not carry these numbers forward as new evidence |
| `degenerate-top-k-reported-as-retrieval-coverage` | low | `D_NO_GO_DECISION.md` reports "top-10 covers 389/389" as acquisition headroom evidence. | For 359/389 text questions top-10 equals always-expand (at most 10 paragraphs). | Claim precision | **waivable** - disclosed here; does not alter the verdict and in fact strengthens the no-go |

Already-filed and therefore **not** re-reported as new: parent-adapter non-activation
(`PHASE-B-VALIDITY`), strict/embedded split (`ADAPTER-SEMANTICS`), sign-reversed targets
(prior direction-leak closure), R/E implementation stop (`C2-FEEDBACK-REPAIR`).

---

## 5. Verdict

**`CONDITIONAL`** - exact scope below.

### Accepted without condition

1. The disposition `NO_GO_FOR_MODEL_PROBE` and the release block
   (`probe_release` = `BLOCKED_MISSING_NATURAL_RESIDUAL`). Neither candidate retains a
   deployable residual after the full control battery.
2. All five D premise corrections (K1-K7), each independently re-derived from source.
3. The metric correction (K8) and its claim boundaries
   (`answer_correctness NOT_SCORED`, `feedback_derived_learning NOT_QUALIFIED`,
   `new_source_generalization NOT_TESTED`, `confirmation_claim NONE`).
4. The prompt identity binding as three distinct labels (K9), including D's explicit
   marking of the Windows raw digest as noncanonical.
5. The D source-scope correction: FinQA excluded from the new candidate claim.
6. The missing-condition statement, which is correctly specified in both A and D.
7. K13 zero-call compliance, with the disclosed caveat that it rests partly on absence of
   counter-artifacts.

### Conditional - required before this evidence chain is relied on

| # | Condition | Owner |
|---|---|---|
| C-1 | Reclassify `authority_hash_discrepancy` / `binding_metadata_exception` as a false positive caused by unnormalized digest comparison. `e4c53572` is the LF->CRLF view of blob `5c3f970d`, not a missing or divergent prompt version. | A artifact owner |
| C-2 | Re-bind `D_PREMISE_CORRECTION.md`: recorded `9294a81b` does not equal current `1a77969`. Either re-hash the current file or restore the hashed content. | A artifact owner |
| C-3 | Correct the C1 figure: `four_selected_failures_explained` is 4 only under a positional/ordinal role-equality rule; the stated label+period rule gives 3/4. Name the rule that actually explains the count. | A artifact owner |
| C-4 | Disclose the 4-row asymmetric pad and the resulting 11/7/7/7/7 per-correction weighting in any reuse of the 39/217 composition. | A and D artifact owners |
| C-5 | Do not carry the FinQA 168/171/177/186/195 figures forward as new evidence or as a historical receipt; they are new-task computation on a restricted source with no prior carrier. | D artifact owner |

### Rejected

None. No claim under audit was found to be fabricated or inverted. The defects are
evidence-chain precision and source-scope defects, not outcome defects.

### Conditions for the NO_GO to be accepted as unconditional

Both acceptance conditions named in the task card are **substantively met at the level of
the decision** and **not met at the level of A's evidence chain**:

- *Simple-baseline explanation independently reproduced* - fully reproduced for C2
  (exact 378/385/385/389 from an independent implementation, robust across five retrieval
  variants); reproduced for C1 only under a strengthened rule (see C-3).
- *FinQA source restriction respected* - respected by D, violated by A (see C-5).

Once C-1 through C-5 are recorded, this verdict converts to `ACCEPTED` for the
`NO_GO_FOR_MODEL_PROBE` disposition. The model probe remains unreleased either way; no
generation, training, judge or production action is authorized by this audit.

### Advisory boundary

This audit modified nothing outside its two owned files. No A-owned or D-owned artifact was
edited, no historical record was rewritten, and no repair was applied "while here".
Incidents are recommended for filing only; recording belongs to the append-only ledger flow.

---

## 6. Evidence index

| Evidence | Carrier |
|---|---|
| Adapter activation | `research/feedback_learning_phase_b_20261026_v1/b2/B2_TRAIN_RUN.py:704,710-721,731,758,761-763` |
| PEFT single-active-adapter | installed PEFT 0.21.2 `peft_model.py` `set_adapter` docstring |
| Integrity-field ownership | `B2_TRAIN_RUN.py:323-328,370-376` |
| Correction counts | `B1_CORRECTION_TRAJECTORIES.jsonl` (72 rows, recomputed) |
| Training composition | `b2/B2_PROTOCOL_FROZEN.json.training`; `B2_TRAIN_RUN.py:407-418,744` |
| Target scope / sign-reversal | `B1_CORRECTION_TRAJECTORIES.jsonl` `r_target` vs `frozen_reference_target_for_audit` |
| Output layers | `b2/B2_DEVELOPMENT_ANALYSIS.json`; `b2b/B2B_DEVELOPMENT_ANALYSIS.json` |
| EOS handling | installed TRL 1.14.1 source |
| Prompt identity | `git rev-parse` / `cat-file` / `sha256sum` at `19ddd7fef`; `.gitattributes` |
| TAT-QA recompute | pinned `tatqa_dataset_dev.json` sha256 `8da095a819af6db3...`, pure-NumPy TF-IDF |
| C1 screen | `research/decision_space_autopsy_v1/SAME_NUMBER_ROLE_TASKS_DRAFT.json`; `exploratory_b0_v1/B0_RESULT_RESCORE_V1.json` |
| FinQA provenance | four-form repo-wide grep, zero hits outside `a_prepare/` |
| Zero-call | directory inventory, freshness scan, network sweep, `git status --porcelain` |
| Baseline | `memory/THREADS.md`, `memory/STATE.md` |

Local recomputation only. No GB10, production or runtime behavior is established by this
audit. Model calls made by this audit: **0**. Judge calls: **0**. Training runs: **0**.
Production probes: **0**.
