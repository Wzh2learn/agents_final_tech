# CONDITION_CHANGE_FIX_C Review

Task ID: `gb10-condition-change-feedback-20261020-fix-c`
Reviewed package: `condition_change_feedback_v1` (V2 bounded revision)
Review type: post-fix scoped re-review (Loop C), scientific identifiability only

## Evidence Discipline

`FACT`: Model requests `0`. Judge calls `0`. Training calls `0`. Network
requests `0`. Service requests `0`. Production Memory writes `0`. No probe,
canary, or health check of any endpoint was performed.

`FACT`: This review wrote exactly one file, this one. `verify_condition_change.py`
was deliberately **not** executed because its final step writes
`MACHINE_VERIFICATION_V2.json` (line 389, `write_json(MACHINE_VERIFICATION_PATH,
verification)`), which would have mutated a frozen artifact. Its checks were
re-derived independently instead. The focused unit suite was executed because
`test_probe_result_is_reproducible` calls the pure function `build_probe_result()`
and the suite performs no writes.

`FACT`: Commands actually run in this review:

```text
python3 -B -m unittest -v test_condition_change.py
```

plus read-only Python recomputation (hashing, JSON inspection, reference
re-derivation) executed from the package directory. Result: `Ran 15 tests in
0.009s / OK`, 15 passed, 0 failed, 0 skipped, runtime CPython `3.12.3` at
`/usr/bin/python3`.

---

## 1. Blocker 1 — Actor input did not expose the policy change

**Status: `CLOSED`.**

### FACT

`ACTOR_TASKS_V2.json` carries `schema_version=condition_change_actor_tasks_v2`,
`actor_input_only=true`, 26 tasks (`CC001:pre` … `CC013:post`), 13 pre and 13
post. Every one of the 26 tasks has exactly the top-level keys
`actor_input_only, case_id, observation, policy_context, policy_version_id,
source_cluster, stage, task_id`, and every `policy_context` has exactly the keys
`applicable_policy_text, explicit_policy_delta_text, policy_version_id`.

For every case, pre and post differ in policy and are identical in observation:

| Field | pre | post |
|---|---|---|
| `policy_version_id` | `expense_policy_pre_v1` | `expense_policy_post_v1` |
| `applicable_policy_text` | 4352 bytes, sha256 `5d49e532895aa744…` | 5909 bytes, sha256 `444a644746dc44bd…` |
| `explicit_policy_delta_text` | `Applicable baseline text; no condition-change delta applies.` | `For conference claims over USD 100 with manager approval, the post-change policy requires a valid receipt and manager approval; the card-statement plus merchant-invoice proof alternative is not applicable.` |
| `observation` | — | byte-identical to pre |

`FACT`: the post delta text is the `actor_policy_delta.expense_policy_post_v1`
string in `POLICY_SPEC_V2.json`; the pre string is
`actor_policy_delta.expense_policy_pre_v1`. The delta text is not free-hand
narrative, it is bound to the policy record.

`FACT`: gold is absent from actor input. A full-text scan of
`ACTOR_TASKS_V2.json` finds the strings `gold`, `sufficient`, `adjudicat`, and
`reference_fact` exactly once each, all four inside the single top-level
`boundary` object as negative flags (`contains_gold_answers: false`,
`contains_minimal_sufficient_sets: false`, `contains_reference_facts: false`,
`contains_adjudication_fields: false`, `contains_reference_labels: false`,
`contains_applicable_policy_context: true`). No key named `decision`,
`minimal_sufficient_sets`, `canonical_sufficient_set`, `reference_*`, `gold_*`,
or `adjudicat*` occurs in any actor task. `EVIDENCE_FACTS_V2.json` contains no
`decision` or `minimal_sufficient_sets` key.

`FACT`: the observation exposes only `claim`, `evidence_inventory`
(`fact_id`, `kind`, `valid`), and `prior_experience`
(`baseline_submitted_outcome`, `plan_evidence_ids`). `prior_experience` is the
prior plan under evaluation, not gold: for `CC001:post` it is `approve` while
the derived decision is `reject`.

`FACT`: `test_actor_input_is_separate_from_reference_data` asserts the exclusion
list and the presence of `policy_context` for every task and passes.

### INFERENCE

The actor can now observe the condition change on three independent channels
(policy text, explicit delta text, policy version id) while remaining unable to
read the answer. Because `observation` is held constant across the pair, any
pre/post behavioural difference is attributable to the policy channel alone.
Blocker 1 is closed in substance, not merely in schema.

`INFERENCE`: the boundary object is a self-declaration and would be worthless on
its own; the independent full-text scan above is what makes the exclusion claim
credible.

---

## 2. Blocker 2 — The out-of-scope probe was a double fault

**Status: `CLOSED`.**

### FACT — the V1 defect, confirmed from preserved V1 bytes

`FEEDBACK_PROBE_RESULTS_V1.json` records `OUT_OF_SCOPE_ADDITION` as
`selected_evidence_ids = [CC003:manager_approval, CC003:receipt,
CC003:team_note]`, `submitted_outcome = "approve"`, against
`decision.outcome = "reject"`. Its composite row reads
`answer_coverage: false`, `plan_sufficient: true`, `plan_precision:
0.6666666666666666`, `reason_code: "OUT_OF_SCOPE_ADDITION"`.

`FACT`: that V1 fixture changed two factors at once — the submitted outcome was
wrong *and* an out-of-scope fact was present — and V1 conflated them into a
single `reason_code` field (composite `OUT_OF_SCOPE_ADDITION`, exact-match
`CANONICAL_PLAN_OR_ANSWER_MISMATCH`). V1 also had no counterfactual fixture.

### FACT — the V2 fix

`FEEDBACK_PROBE_FIXTURES_V2.json` is now a single-factor pair on one source
task:

| | `OUT_OF_SCOPE_ADDITION` | `OUT_OF_SCOPE_COUNTERFACTUAL` |
|---|---|---|
| `source_task_id` | `CC003:post` | `CC003:post` |
| `submitted_outcome` | `reject` | `reject` |
| `selected_evidence_ids` | `[CC003:receipt, CC003:team_note]` | `[CC003:receipt]` |
| set difference | exactly `{CC003:team_note}` | — |

`FACT`: `CC003:post` derives `decision.outcome = "reject"`
(`rule_id=post_meal_cap`, `reason_code=MEAL_CAP_EXCEEDED`) from
`minimal_sufficient_sets = [["CC003:receipt"]]`,
`in_scope_evidence_ids = [CC003:manager_approval, CC003:receipt]`,
`out_of_scope_evidence_ids = [CC003:team_note]`. Both fixtures submit the
derived outcome and both contain a minimal sufficient set. The only
manipulated factor is `CC003:team_note`, whose `kind` is `operational_note`,
absent from `in_scope_fact_kinds = [receipt, card_statement, merchant_invoice,
manager_approval]`.

`FACT`: measured dispositions in `FEEDBACK_PROBE_RESULTS_V2.json`:

| Probe | exact_match | sufficiency_only | composite | composite `contract_reason_code` | `reason_codes` |
|---|---|---|---|---|---|
| `OUT_OF_SCOPE_ADDITION` | REVISE | RETAIN | REVISE | `SCOPE_PRECISION_FAILED` | `["SCOPE_IMURITY"]` |
| `OUT_OF_SCOPE_COUNTERFACTUAL` | RETAIN | RETAIN | RETAIN | `COMPOSITE_CONTRACT_SATISFIED` | `[]` |
| `VALID_ALTERNATE_SET` | REVISE | RETAIN | RETAIN | `COMPOSITE_CONTRACT_SATISFIED` | `[]` |

`FACT`: the pair differs in composite disposition by one factor, and the
composite rejection is attributed to scope precision (`plan_precision
0.500000000000` vs `1.000000000000`) with `answer_coverage: true` and
`plan_sufficient: true` on both sides. `SCOPE_IMURITY` occurs 6 times in
`FEEDBACK_PROBE_RESULTS_V2.json`, all of them on the three contract rows of
`OUT_OF_SCOPE_ADDITION`; zero occurrences on the counterfactual.

`FACT`: `test_scope_fixture_is_single_factor_with_clean_counterfactual` asserts
the counterfactual linkage, same source task, same submitted outcome, set
difference of exactly one element, that element being a subset of
`out_of_scope_evidence_ids`, and that both fixtures submit the derived outcome
and contain a minimal set. It passes.

### INFERENCE

Scope precision is now isolated. The sufficiency-only contract retaining the
extra while composite revises it is exactly the intended separation, and the
clean counterfactual proves the composite does not over-reject. Blocker 2 is
closed.

---

## 3. Blocker 3 — No pair tested invariant outcome with a changed sufficient set

**Status: `CLOSED`, with one material qualification (section 7.1).**

### FACT

`CC013` is appended without altering any V1 case.
`test_source_inputs_have_no_per_case_gold_answers` asserts
`source_cases_v2.cases[:12] == source_cases.cases`, i.e. the first 12 V2 cases
are the 12 V1 cases byte-identically.
`condition_change_feedback_v2_revision.source.json` declares
`appended_case.case_id = "CC013"` and
`policy_delta.rule.id = "post_conference_evidence_standard"` inserted before
`post_reimbursable`.

`FACT`: derived references for `CC013`:

| | `CC013:pre` | `CC013:post` |
|---|---|---|
| `decision.outcome` | `approve` | `approve` |
| `decision.rule_id` | `pre_reimbursable` | `post_conference_evidence_standard` |
| `minimal_set_count` | 2 | 1 |
| `minimal_sufficient_sets` | `[manager_approval, receipt]`, `[card_statement, manager_approval, merchant_invoice]` | `[manager_approval, receipt]` |

`FACT`: I re-derived both stages independently from `POLICY_SPEC_V2.json` and
`EVIDENCE_FACTS_V2.json` by hand-executing the declared semantics
(`first_match_in_declared_order`, Cartesian product over requirement
alternatives) without reading `REFERENCE_TASKS_V2.json`. The claim
`category=conference, amount_usd=120, manager_approval=true` matches
`pre_reimbursable` (pre) and `post_conference_evidence_standard` (post) exactly
as recorded; the pre proof-of-purchase alternatives yield `{receipt}` and
`{card_statement, merchant_invoice}`, crossed with the `manager_approval`
requirement (active because `amount_usd > 100`) giving exactly the two recorded
minimal sets; the post rule retains only the `{receipt}` alternative, giving
exactly the one recorded set. The outcome is invariant; the minimal-set family
is not.

`FACT`: `reference_builder.py` contains no per-case branch.
`derive_all_references` iterates every `case_id` present in
`EVIDENCE_FACTS_V2.json` and applies both policy versions; `derive_reference`
selects the rule by predicate matching and computes requirement sets by
Cartesian product. `gold_source` is `declarative_policy_and_evidence_facts` on
all 26 references. `test_reference_builder_rederives_without_actor_tasks`
recomputes `derive_all_references(POLICY_PATH, FACTS_PATH)` and asserts equality
with the stored payload; it passes.

`FACT`: `reference_counts` records
`invariant_decision_minimal_set_change_pairs: 1`, `decision_flips: 3`,
`invariant_pairs: 10`, `paired_cases: 13`, and
`decision_flips + invariant_pairs == paired_cases`.

### INFERENCE

Blocker 3 is closed as specified: a pair exists whose decision is invariant
across the policy delta while its minimal sufficient set changes, and both
stages are derived by the same policy engine from the same declarative sources.
The qualification in section 7.1 concerns how much discriminating power the
frozen baseline actually extracts from this pair.

---

## 4. Fixed-decimal reproducibility and provenance

**Status: `CLOSED` for `plan_precision_mean`; `CLOSED` for provenance.**

### FACT — fixed decimal

`run_feedback_probe.py` imports `fractions.Fraction`, sets
`FIXED_DECIMAL_PLACES = 12`, and defines `fixed_decimal(value, places)` as
integer `divmod` scaling with half-up rounding
(`if remainder * 2 >= value.denominator: quotient += 1`). `_metrics` sums
per-row `Fraction(numerator, denominator)` starting from `Fraction(0, 1)` and
divides by the row count, then emits `plan_precision_mean` as
`fixed_decimal(precision_mean)` together with the reduced
`plan_precision_numerator` / `plan_precision_denominator`.

`FACT`: independent recomputation from the 26 frozen baseline rows reproduces
the stored values exactly:

| Stage | recomputed mean | stored num/den | recomputed 12-place string | stored string |
|---|---|---|---|---|
| pre (n=13) | 37/39 | 37 / 39 | `0.948717948718` | `0.948717948718` |
| post (n=13) | 37/39 | 37 / 39 | `0.948717948718` | `0.948717948718` |
| overall (n=26) | 37/39 | 37 / 39 | `0.948717948718` | `0.948717948718` |

`FACT`: I reimplemented `fixed_decimal` independently in this review and
obtained the identical string. `test_baseline_is_deterministic_and_non_terminal`
asserts the value is a `str`, has exactly 12 fractional digits, and equals
`fixed_decimal(Fraction(numerator, denominator))`; it passes. V1 stored
`plan_precision_mean` as the binary float `0.9444444444444445`.

### FACT — provenance

`FROZEN_INPUT_MANIFEST_V2.json`, `FEEDBACK_PROBE_RESULTS_V2.json`, and
`MACHINE_VERIFICATION_V2.json` all carry `task_id =
condition_change_feedback_v1`. The literal launcher strings
`gb10-condition-change-feedback-20261020-a2` and
`gb10-condition-change-feedback-20261020-fix-a` occur in exactly one V2 file,
`PROBE_RUN_MANIFEST_V2.json`, under `launcher_ids` (`implementation`, `fix`).
`MACHINE_VERIFICATION_V2.json` records only the boolean
`provenance.launcher_ids_recorded_only_in_run_manifest: true` and
`provenance.package: condition_change_feedback_v1`; it embeds no launcher id.
`test_stable_package_provenance_and_launcher_manifest_boundary` asserts the
`launcher_ids` key is absent from manifest, results, fixtures and the machine
receipt; it passes.

`FACT`: V1 files retain the old launcher id
`gb10-condition-change-feedback-20261020-a2` as `task_id`
(`FROZEN_INPUT_MANIFEST.json`, `FEEDBACK_PROBE_RESULTS_V1.json`,
`MACHINE_VERIFICATION.json`). This is correct: those bytes must not change.

---

## 5. V1 artifacts unchanged

**Status: `CONFIRMED` on 11 of 14 V1 files by a pre-revision digest anchor;
the remaining 3 by hash agreement with the V2 manifest only.**

`FACT`: `MACHINE_VERIFICATION.json` (V1) has mtime `17:10:08` and records
SHA-256 digests for 11 V1 files. Every one of those 11 digests matches my
independent recomputation of the file as it exists on disk today:

| File | V1 receipt digest (written 17:10:08) | matches disk |
|---|---|---|
| `ACTOR_TASKS_V1.json` | `5eed6e6d19fd540c…` | yes |
| `EVIDENCE_FACTS_V1.json` | `7886dfe9b608ea1c…` | yes |
| `FEEDBACK_PROBE_FIXTURES_V1.json` | `ab7f0e72407534cf…` | yes |
| `FEEDBACK_PROBE_RESULTS_V1.json` | `13c14b5a2a06d0e9…` | yes |
| `POLICY_SPEC_V1.json` | `bcf098dc8f548c5c…` | yes |
| `PROBE_FREEZE_MANIFEST.json` | `934197e4e3d469e9…` | yes |
| `PROBE_RUN_MANIFEST.json` | `d531a1cded8f7cdf…` | yes |
| `REFERENCE_TASKS_V1.json` | `98c253cc298adf18…` | yes |
| `TASK_TOOL_SCHEMA.json` | `bd29b8651b4b6e7a…` | yes |
| `case_inputs_v1.source.json` | `d4fbc666ae9818a5…` | yes |
| `policy_spec_v1.source.json` | `912413058610daa8…` | yes |

`FACT`: the three V1 files not pinned by the V1 receipt
(`FROZEN_INPUT_MANIFEST.json`, `FEEDBACK_PROBE_SUMMARY_V1.json`,
`MACHINE_VERIFICATION.json` itself) match the digests recorded in
`FROZEN_INPUT_MANIFEST_V2.json` `v1_frozen_hashes` /
`MACHINE_VERIFICATION_V2.json` `file_hashes.v1_frozen_inputs_and_results`,
which I also recomputed independently: `629c73b9…`, `d283ffbc…`, `e9ba595d…`.

`FACT`: mtime separation is clean. All 15 V1 files are stamped
`16:21`–`17:10:08`. Every V2 file is stamped `18:07:16`. The revised scripts and
this package prose are stamped `17:50`–`18:06`. No V1 file was written during
the revision window.

`FACT`: V1 content is still pre-fix in every respect the fix targeted — 24 actor
tasks, 12 paired cases, 35 evidence facts, 4 source clusters,
`plan_precision_mean` as a binary float, the conflated singular `reason_code`
field, the double-fault scope fixture, and no counterfactual. A rewrite that
preserved all of those defects byte-perfectly is not a plausible failure mode.

### INFERENCE

V1 preservation holds. The evidence chain is: a receipt written before the
revision pins 11 files; the V2 manifest pins the other 3; mtimes and defect
fingerprints are consistent with an untouched pre-fix state.

---

## 6. Contract separation and headroom

`FACT`: the three frozen probe fixtures separate the two failure modes the
sprint contract names. `exact_match` rejects a valid alternate sufficient set
(`VALID_ALTERNATE_SET` -> REVISE against canonical `[CC002:receipt]` while
`[CC002:card_statement, CC002:merchant_invoice]` is a genuine minimal set for
`CC002:pre`). `sufficiency_only` retains an out-of-scope extra
(`OUT_OF_SCOPE_ADDITION` -> RETAIN). `composite` rejects the extra and retains
both the clean counterfactual and the valid alternate set.

`FACT`: I re-derived the four reference tasks carrying alternative minimal sets
from the policy and confirmed each is naturally derived through the
`amount_usd > 100` conditional on the `manager_approval` requirement
(`CC002:pre`, `CC006:pre`, `CC006:post`, `CC013:pre`). The two distinct
out-of-scope fact ids are `CC003:team_note` (`operational_note`) and
`CC009:legacy_quote` (`legacy_quote`).

`FACT`: deterministic headroom is non-terminal at both stages. Baseline composite
acceptance is `7/13` pre, `5/13` post, `12/26` overall; 14 composite rejections,
rejection rate `0.5384615384615384`. Plan sufficiency `12/13` pre, `11/13` post,
`23/26` overall. Answer coverage `10/13` pre, `7/13` post, `17/26` overall.
Every stage metric lies strictly between 0 and 1.

`FACT`: I decomposed the 14 composite rejections independently from the frozen
rows — `ANSWER_MISMATCH` alone 7, `SCOPE_IMURITY` alone 3, `INSUFFICIENT_PLAN`
alone 2, `INSUFFICIENT_PLAN + ANSWER_MISMATCH` 1, `SCOPE_IMURITY +
ANSWER_MISMATCH` 1. Headroom is multi-factor, not a single artefact.

`FACT`: `headroom.real_model_phase_authorized` is `false` and
`stop_recommendation` is `STOP_BEFORE_REAL_MODEL` in all three V2 receipts. The
sprint stop rule ("Do not start a real-model phase from this sprint
automatically") was honoured: no model phase was started.

---

## 7. Limitations (non-blocking)

### 7.1 CC013 discriminating power is unexercised in the frozen baseline

`FACT`: the frozen baseline submits `prior_experience.plan_evidence_ids`
unchanged. For `CC013` that plan is all four in-scope facts at both stages,
producing identical metrics pre and post — `plan_sufficient: true`,
`answer_covered: true`, `plan_precision: 1.000000000000`,
`composite_accepted: true` at both stages.

`FACT`: `CC013` **canonical** sufficient set is `[manager_approval, receipt]` at
*both* stages. What changes is the *alternative* set
`[card_statement, manager_approval, merchant_invoice]`, which is minimal pre and
invalid post. A selection of exactly that alternative is sufficient pre and
insufficient post; a selection of the canonical set is never wrong.

`INFERENCE`: the pair is genuine at the reference level and does create a
revision opportunity, but only for a policy that commits to the card-statement
alternative. The frozen baseline never commits to it, so the pair contributes
zero discriminating signal to the reported headroom. The
`invariant_decision_minimal_set_change_pairs: 1` count should be quoted as a
*constructed opportunity*, not as a demonstrated behavioural test.

`INFERENCE`: recommended follow-up before or alongside the real-model phase —
add a frozen probe pair analogous to `VALID_ALTERNATE_SET` that submits the
`CC013` card-statement alternative at both stages, so the invariant-decision /
changed-set condition is exercised by a fixture and not only by whatever a model
happens to select. This is an addition, not a repair; it does not block.

### 7.2 `plan_precision` does not penalize in-scope over-selection

`FACT`: `scope_precision_components` computes
`len(selected ∩ in_scope) / len(selected)`. Selecting every in-scope fact
therefore scores `1.0`. The composite contract accepts on
`sufficient and precision == 1 and answer_covered`.

`FACT`: applying the diagnostic predicate `in_scope_over_selection` to the 26
frozen baseline rows fires on 6 rows, of which **3 are composite-ACCEPTED**.

`INFERENCE`: composite "scope precision" measures *out-of-scope contamination
rate*, not selection tightness. It separates the two cases the sprint contract
names, which is what the acceptance predicate requires, but it must not be
quoted as evidence that the contract penalises over-selection. The diagnostic
code `IN_SCOPE_OVER_SELECTION` reports the condition without acting on it.

### 7.3 Three of four diagnostic reason codes never fire on frozen data

`FACT`: `FEEDBACK_PROBE_RESULTS_V2.json` contains `SCOPE_IMURITY` 6 times,
`SCOPE_PRECISION_FAILED` 2, `CANONICAL_SET_MISMATCH` 4, and **zero** occurrences
of `ANSWER_MISMATCH`, `INSUFFICIENT_PLAN`, or `IN_SCOPE_OVER_SELECTION`.
Baseline rows do not persist `reason_codes` at all (row keys are
`actor_input_only, answer_covered, case_id, composite_accepted, plan_precision,
plan_precision_denominator, plan_precision_numerator, plan_sufficient,
reference_outcome, source_cluster, stage, task_id`).

`FACT`: `test_diagnostic_reason_codes_are_independent` demonstrates all four
codes firing in isolation, but on a synthetic inline reference, not on frozen
package data.

`INFERENCE`: the V1 requirement was *separation* of the codes, and that is
implemented and tested. The claim that frozen results "independently report" all
four is true of the scorer, not of the frozen evidence. Acceptable, but the
wording should not travel further than the scorer.

### 7.4 Macro vs micro averaging of `plan_precision_mean`

`FACT`: `plan_precision_mean` is the macro mean of per-task precision ratios,
reported as the reduced fraction `37/39`. The micro average over the same rows
(sum of in-scope selections / sum of selections) is `44/48 = 11/12 ≈ 0.91667`,
materially different from `37/39 ≈ 0.94872`.

`FACT`: `37/39` is not a count ratio. It is presented in `RETURN.md` alongside
genuine count ratios (`12/13`, `10/13`, `7/13`), where a reader will naturally
read it as "37 of 39".

`INFERENCE`: both aggregations are defensible; the ambiguity is presentational.
Any external quoting of `0.948717948718` should state "macro mean of per-task
plan precision" and give the micro value alongside.

### 7.5 Scope of the reproducibility claim

`FACT`: only `plan_precision_mean` was converted to fixed-decimal/Fraction form.
`answer_coverage_rate`, `composite_acceptance_rate`, `plan_sufficient_rate` and
`headroom.baseline_composite_rejection_rate` remain binary floats in all V2
receipts. They are quotients of small integers and therefore IEEE-754
deterministic, so this is not a defect.

`INFERENCE`: the cross-version reproducibility claim should be scoped to
`plan_precision_mean`, not to "the metrics".

### 7.6 Cosmetic: `SCOPE_IMURITY`

`FACT`: the diagnostic token is spelled `SCOPE_IMURITY` (missing `P`) in
`run_feedback_probe.py` line 114 and in every artifact and test that asserts it.
`contract_reason_code` uses the correctly spelled `SCOPE_PRECISION_FAILED`.

`INFERENCE`: naming debt. The string is now load-bearing in frozen hashes and
test assertions; renaming it would invalidate the freeze. Record it and leave
it.

---

## 8. UNVERIFIED

1. `UNVERIFIED` — `verify_condition_change.py` end-to-end. Not executed, because
   it writes `MACHINE_VERIFICATION_V2.json`. Its stored receipt reports
   `status: PASS`, `verification_errors: []`. I independently recomputed the
   substance of its checks (hashes, counts, dispositions, baseline metrics,
   fixed-decimal reconstruction, zero-request accounting, provenance) and found
   no discrepancy, but I did not run the script and therefore cannot attest that
   it currently returns `PASS`.
2. `UNVERIFIED` — CPython 3.11 behaviour. No 3.11 interpreter is installed in
   this runtime. The rational/fixed-decimal implementation is version-agnostic by
   construction and I reproduced its output on 3.12.3, but the literal 3.11
   execution claimed as a compatibility goal has not been performed by anyone.
3. `UNVERIFIED` — git-level immutability of V1. `git ls-files` for the sprint
   tree required an approval I did not grant, so V1 preservation is anchored on
   the pre-revision `MACHINE_VERIFICATION.json` digest chain and mtimes
   (section 5), not on a git blob comparison. If the sprint tree is untracked the
   anchor is as strong as section 5 makes it; if it is tracked, a `git diff`
   would be a stronger and cheap confirmation.
4. `UNVERIFIED` — any behavioural property of a real model. Zero requests were
   sent. Nothing in this review speaks to model capability, learning, or
   generalization.
5. `UNVERIFIED` — external validity. Evidence identity is
   `DEV_ONLY_CONTROLLED_MECHANISM`: 13 synthetic reimbursement pairs in one
   domain, `human_confirmed=false`, no natural observations, no human gold. This
   bounds every claim in this package.

---

## 9. Blocker Disposition

| # | V1 blocker | Status | Primary evidence |
|---|---|---|---|
| 1 | actor input did not expose the policy change | **CLOSED** | section 1: `policy_context` on all 26 tasks; pre/post policy text and delta text differ; observation held constant; gold excluded by full-text scan |
| 2 | out-of-scope probe was a double fault | **CLOSED** | section 2: single-factor pair on `CC003:post`, identical derived outcome, set difference exactly one out-of-scope fact, frozen clean counterfactual |
| 3 | no pair tested invariant outcome with changed sufficient set | **CLOSED** | section 3: `CC013` outcome `approve`->`approve`, minimal-set family 2->1, both stages independently re-derived from policy |
| — | fixed-decimal reproducibility | **CLOSED** | section 4: Fraction + 12-place fixed decimal, independently reproduced |
| — | stable provenance | **CLOSED** | section 4: `task_id=condition_change_feedback_v1`; launcher ids only in `PROBE_RUN_MANIFEST_V2.json` |
| — | V1 artifacts unchanged | **CONFIRMED** | section 5: 11/14 pinned by a pre-revision receipt, 3/14 by V2 manifest, mtimes and defect fingerprints consistent |

**No remaining blocker.**

---

## 10. Final Ruling

# `GO_FOR_BOUNDED_REAL_MODEL`

All three named V1 blockers are closed by direct, independently reproduced
evidence, not by assertion. The new fixed-decimal and provenance work checks
out. V1 is preserved. The three feedback contracts separate the intended failure
modes on frozen fixtures, and the deterministic baseline retains non-terminal
headroom at both stages (14/26 composite rejections, multi-factor).

This ruling authorises **only** the Tier 1 bounds in section 11. It does not
authorise a revision-pass comparison, a second model, a temperature sweep, a
retry budget beyond the single logged transport retry, or any claim of learning,
public generalization, or human gold.

---

## 11. Exact proposed bounds for `BOUNDED_REAL_MODEL_V1` (Tier 1)

Derived from the frozen actor payload, not estimated by feel.

`FACT` (measured on `ACTOR_TASKS_V2.json`): 26 tasks; largest serialized task
7,723 bytes (`CC013:post`), smallest 5,510 bytes (`CC004:pre`), mean 6,564
bytes; total serialized actor payload 170,670 bytes. At a conservative 2.5
bytes/token for mixed JSON and prose that is about 3,090 tokens/task worst case
and about 68,270 tokens for the full set. The submission tool
(`submit_reimbursement_decision`) requires only `task_id`, `outcome`,
`evidence_ids` (at most 4 ids of at most 24 chars), so a correct completion is
at most 100 tokens.

### Request bound

| Quantity | Exact bound |
|---|---|
| Model requests | **26** — exactly one per actor task `CC001:pre` … `CC013:post` |
| Samples per task | **1** |
| Temperature | **0** |
| Transport retries | **at most 1 per request**, logged separately, does not create a new attempt |
| Failed-after-retry requests | recorded as `NO_OUTPUT`, scored `ANSWER_MISMATCH` + `INSUFFICIENT_PLAN`, **never re-run** |
| Judge calls | **0** |
| Training calls | **0** |
| Network calls other than the 26 model requests | **0** |
| Service / production Memory calls | **0** |
| Deterministic scoring calls | 3 contracts x 26 tasks = **78 dispositions**, **0 model calls** |

### Token bound

| Quantity | Per request | Aggregate (26) |
|---|---|---|
| Input cap | **4,096** | **106,496** |
| Output cap | **256** | **6,656** |
| Combined cap | **4,352** | **113,152** |

Expected actuals, for comparison against the caps: input about **68,270** total
(about 3,090 worst-case single request), output about **2,600** total. The caps
are hard ceilings; a request exceeding an input cap is **truncated at the frozen
actor payload boundary and logged**, never silently dropped, and a request
exceeding the output cap is scored from the truncated completion as `NO_OUTPUT`
+ `INSUFFICIENT_PLAN`.

### Estimand (must be frozen before the first request)

Single fixed model, single configuration. Pass 1 only. For each of the 26 actor
tasks the model emits one `submit_reimbursement_decision` call; all three
feedback contracts then score that single submission deterministically. The
measured quantities are plan sufficiency, plan precision (macro and micro, both
reported), answer coverage, and composite acceptance — separately for pre (13)
and post (13) stages — plus the pre/post revision rate on the 3 decision flips
and the 10 invariant pairs.

### Explicit non-claims for this phase

- No feedback is shown to the model; therefore this phase measures **contract
  discrimination on model output**, not the effect of feedback.
- No learning, adaptation, retention, or generalization claim is available.
- Evidence identity remains `DEV_ONLY_CONTROLLED_MECHANISM` with
  `human_confirmed=false`.
- `CC013` is a constructed opportunity only (section 7.1); its behavioural
  discriminating power is not guaranteed by the frozen baseline.

### Out of scope for this ruling

Tier 2 (revision arms under feedback) would require **+78 requests** — 3
contract arms x 26 tasks — and at the same per-request caps would add 319,488
input and 19,968 output tokens, for a cumulative 104 requests / 425,984 input /
26,624 output. **This phase is not authorised by this ruling and needs a
separate review.** Any pre-registration of Tier 2 should also resolve section
7.1 by adding the `CC013` alternate-path probe pair first.

---

## Single Next Action

Freeze the Tier 1 estimand and the `CC013` alternate-path probe pair (section
7.1) in one pre-registration document, then run the 26 requests within the
bounds of section 11. Do not expand to Tier 2 without a separate review. Do not
quote `0.948717948718` as a count ratio, and do not describe composite
`plan_precision` as selection tightness (sections 7.2, 7.4).
