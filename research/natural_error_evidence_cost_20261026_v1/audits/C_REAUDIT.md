# C Independent Corrected Candidate Qualification Re-Audit

**Nature of document.** Advisory Loop C audit report. It reports and recommends; it does not
repair. Adjudication belongs to the human owner. No A artifact was modified.

**Audited object and baseline.** `research/natural_error_evidence_cost_20261026_v1/a_remediate/`
(11 files, authority commit `622b386986ca66c8119263e146f3d3e73c33e260`), audited against the
frozen P1 run, the pinned TAT-QA dev source, and the preserved `a_prepare/` identity. The
known-anomaly baseline is `audits/C_PREAUDIT.md` findings **F1-F5** plus its non-blocking
transcription note; anything inside that set is a *known case*, not a new finding.

**Independence declaration.** This auditor did not author any audited artifact. Mitigations
performed, not promised: (a) all load-bearing numbers were reproduced first-hand - the auditor
re-executed `P2_RECOVERY_RECOMPUTE.py` personally, and two independent sub-agents were run with
explicit instructions to read no conclusion/recommendation/`overall_status`/`corrections`
narrative and to reimplement the P2 pipeline from the pinned raw without importing the audited
module; (b) verdicts on P1 and P2 were formed from frozen raw before A's conclusions were read.
Disclosed ingestion exception: during the hash-integrity step the auditor read
`A_REMEDIATION_RESULT.json` keys plus the fields `output_sha256`, `prior_version_preservation`,
`model_probe_authorized` and the one-line `overall_status`. No conclusion prose (`corrections`,
`validation`, `p1_aggregate`, `p2_aggregate`) was read before the P1/P2 verdicts were formed,
and the P1/P2 sub-agents were barred from those fields entirely. Findings that point at this
auditor's own reproduction are recorded in full.

---

## Verdict

| Candidate | Verdict | Basis |
|---|---|---|
| P1_VISIBLE_SEMANTIC_ROLE_BINDING | **remediated, still BLOCKED** | 4 natural model errors / 1 reference defect correctly separated; one gold-free policy replays 4/5 overall and 4/4 genuine; residual after visible-only controls = 0, so the stage-gate preference test still fails. |
| P2_TABLE_TEXT_EVIDENCE_COST | **remediated, still NO_GO** | Every published number reproduces from the pinned source at row level; no restricted frontier passes both the -2.0 pp margin and a frozen context budget. |

**Overall: `CONDITIONAL`.** Both C findings F1-F5 are substantively closed and the no-go
conclusion is verified at row level. Two release-blocking residuals remain (R1, R2 below); neither
changes any scientific conclusion, but neither should ship into a released probe.

**Primary recommendation for D: no primary candidate - `NO_GO_STOP_MODEL_STAGE`.**

---

## Integrity of audited inputs

All five frozen inputs re-hashed this session against the `C_PREAUDIT` baseline - all match:

| Input | SHA-256 (first 16) | Status |
|---|---|---|
| `A_PREPARE_TASK.md` | `b14cbcda5544b70c` | match |
| `D_STAGE_GATE.md` | `384ef47ce94331e5` | match |
| `source_disjoint_results_v4.jsonl` | `3723c388ff6f12a1` | match |
| `source_disjoint_instances_v4.jsonl` | `00b92fb31a3ef37b` | match |
| `tatqa_dataset_dev.json` (pinned) | `8da095a819af6db3` | match |
| `SOURCE_EXPOSURE_QUALIFICATION.json` | `39045142db735865` | match (4 copies, all identical) |

`a_prepare/` is unmodified: all 9 hashes declared in `A_PREPARE_RESULT.output_sha256` match on
disk. All 10 hashes declared in `A_REMEDIATION_RESULT.output_sha256` match on disk (the result
file correctly excludes itself from its own fixed-point hash). All 11 required outputs of
`A_REMEDIATE_TASK.md` are present.

---

## Check 1 - P1 separates 4 natural model errors from 1 reference defect

**PASS.** Reproduced from the frozen raw, not from A's labels.

Population reproduces exactly: `ordinary_answer_execution_sft` x `original` = 24 rows,
`program_correct` True 19 / False 5. Failing instances (results and instances files are
line-parallel): `NAT_train_38e317da_60cdb35a` (line 1), `NAT_train_72f960c0_a2eb030c` (4),
`NAT_train_cf77f5f9_a3aade99` (13), `NAT_train_b7814ec0_7b6669a8` (19),
`NAT_train_4c2c23e7_204e680d` (43).

Per-item verdicts, arithmetic recomputed from visible evidence:

| Instance | Model | Gold | Verdict |
|---|---|---|---|
| `38e317da` | R11:C2-R11:C3 = 10,020-25,318 = -15,298 (2018-2017) | R11:C1-R11:C2 = 1,015-10,020 = **-9,005** | genuine model error (wrong period pair) |
| `72f960c0` | R2:C3-R2:C2 = 3.5-5.7 = **-2.2** | R2:C2-R2:C3 = 5.7-3.5 = **+2.2** | genuine model error (direction inverted) |
| `cf77f5f9` | R5:C1+R5:C3 = 82,413+48,016 = 130,429 | R5:C1+C2+C3 = **198,646** | genuine model error (interior column dropped) |
| `b7814ec0` | R5:C1-R5:C2 = 3,552-5,507 = **-1,955** | R5:C2-R5:C1 = 5,507-3,552 = **+1,955** | **reference/scoring defect** |
| `4c2c23e7` | R2:C1+R3:C1+R4:C1 -> non-numeric operand, unexecutable | C3+C2+C1 = **1,904,063** | genuine model error (row and column scope) |

**Sign-convention tally (independent, all 24 originals).** 20 of 24 are change/difference
items. **19 later-minus-earlier, 1 inverted - the inverted one is `b7814ec0`.** Four items share
the identical template "change in X between 2018 and 2019" on axis `C1=2019 | C2=2018`:
`38e317da` (-9,005), `85d4834f` (+1,249), `c2535a25` (-29), `f897bcf7` (+368) - all
later-minus-earlier. `b7814ec0` uses the same template and the opposite sign. F1 is closed.

Denominators are explicit in `P1_SEMANTIC_LEDGER_CORRECTED.json`:
`frozen_program_incorrect_candidates` 5, `genuine_model_semantic_errors` 4,
`reference_scoring_defects` 1, `genuine_errors_over_ordinary_originals` "4/24",
`genuine_errors_over_program_incorrect` "4/5", `ordinary_original_questions` 24. Both
denominators are reported as required.

## Check 2 - one deployable gold-free rule policy, 4/5 and 4/4

**PASS.** `VISIBLE_AXIS_SCOPE_POLICY_V1` is a single ordered 6-rule policy
(`1_visible_completeness`, `2_explicit_period_binding`, `3_change_direction`,
`4_inclusive_range`, `5_label_scope`, `6_numeric_reference_validation`) with
`single_ordered_policy: true`, `no_per_case_branching: true`, `gold_free: true`, and
`forbidden_actor_inputs` = gold answer / gold program / gold evidence row ids / hidden unit
scale. This is one visible policy, not per-instance recipes. F2 is closed.

`control_replay_summary.single_visible_axis_scope_policy`: `pass` **"4/5"**, `overall_repaired`
4, `genuine_repaired` 4, `denominator` 5. Matches the required 4/5 overall / 4/4 genuine.

**4/5 is a ceiling, not a shortfall.** Independently proved by indistinguishability:
`38e317da` and `b7814ec0` share every policy-relevant visible feature (same question template,
same axis `C1=2019 | C2=2018`, same two-operand subtraction on the bound row) yet their gold
signs are opposite. Any rule emitting later-minus-earlier fails `b7814ec0`; any rule flipping
fails `38e317da` and the 17 other later-minus-earlier items. No visible feature separates them.
No gold-free policy can reach 5/5.

Residual after the policy = 0 (`gate.observed_residual_genuine_failures: 0`), status
`BLOCKED_AFTER_SIMPLE_CONTROLS`. The other controls are correctly reported: full-context
restoration `already_satisfied` (5/5 - the prompts already carry the whole table), fixed
calculator 0, strict normalization 0, neutral retry `not_present`.

## Check 3 - scoring identity is explicit (F3)

**PASS.** `scoring_alignment` states `primary_metric` = "frozen program_correct numeric
equality", `implementation` = `math.isclose(executed_value, expected_answer, rel_tol=1e-6,
abs_tol=1e-6)`, and demotes `exact_program_identity` to "secondary strict diagnostic only; not
called the frozen numeric metric". This matches the frozen scorer (`evaluate_target`,
`run_natural_program_experiment_v2.py:522-531`), which decides correctness on numeric closeness
alone - `refs_valid` is computed but not used, `unit` is never checked, and program structure is
never compared. F3 is closed. Under the frozen metric the policy scores 4/5; under strict program
identity it would score 3/5 (`4c2c23e7` matches the gold value with a different operand order),
which A correctly does not present as the frozen metric.

## Check 4 - P2 reproduction at row level (F4)

**PASS. Reproduced, not accepted.** Three independent routes agree.

1. **This auditor re-executed the published program** into a scratch directory (the program reads
   the receipt and answer rule from `--output-dir`, so those two frozen files were copied there
   unchanged):
   `python3 .../a_remediate/P2_RECOVERY_RECOMPUTE.py --output-dir /tmp/crec_p2_rerun_c`
   -> exit 0, 0.255 s, stdout reports `diagnostic_candidate: null`, `disposition: NO_GO`,
   `rows: 507`, `zero_endpoint_calls: true` and `row_results_sha256 =
   93ce50e26d51359c5e8dca9cca9381607b50f762c93ff3cce3da164d830f340e`. That row-level hash
   reproduces **exactly**. `STRONG_BASELINE_FRONTIERS_CORRECTED.json` and
   `P2_TASK_QUALIFICATION_CORRECTED.json` are **byte-identical** to the published copies. The only
   differences in the main payload are `execution_started_at`, `execution_completed_at`, and
   `preregistration/receipt_path` (expected - different output directory).
2. **Hash chain verified:** `row_results_sha256`, `frontiers_payload_sha256` and
   `qualification_payload_sha256` all recompute from the published JSON under the program's own
   canonicalization (`ensure_ascii=False, sort_keys=True, separators=(",",":")`) and match. 507
   rows, 507 unique `question_uid`.
3. **Independent reimplementation** (own parsing code; the audited module was never imported)
   matches every aggregate **and all 507 x 6 row-level actions with zero mismatches**.

Reproduced aggregates (published = this audit = independent reimplementation):

| Frontier | potential | gap pp | char ratio | total chars | gold recovery | actions | 75% | 50% | margin |
|---|---|---|---|---|---|---|---|---|---|
| `table_only` | 197 | 60.946746 | 0.240455 | 223,082 | 0 | 0 | pass | pass | fail |
| `small_topk_3` | 452 | 10.650888 | 0.667945 | 619,687 | 441 | 3 | pass | fail | fail |
| `fixed_top1_neighbor` | 414 | 18.145957 | 0.590626 | 547,954 | 381 | 3 | pass | fail | fail |
| `larger_topk_5` | 486 | 3.944773 | 0.834024 | 773,767 | 482 | 5 | fail | fail | pass |
| `always_expand` | 506 | 0.0 | 1.0 | 927,751 | 507 | all | - | - | baseline |
| `transparent_stop_expand` | 481 | 4.930966 | 0.846059 | 784,932 | 480 | <=5 stages | fail | fail | pass |

Other reproduced quantities: 278 records / 1,668 questions; `answer_from` table 772, table-text
**507**, text 389; answer types arithmetic 205 / span 181 / multi-span 101 / count 20; 156
distinct table uids (= `record_clusters` 156); `source_requirement` table 197 / both 265 /
paragraph 44 / unresolved 1 = 507; `scale_source` not_required 170 / paragraph 237 / question 60
/ table 13 / table_and_paragraph 6 / unresolved 21 = 507. Stop-rule stages for
`transparent_stop_expand`: table_only 0, top1_neighbor 78, top3 30, top5 17, all 382.

Arithmetic re-derived independently from the published totals: every gap
(100 * (always_potential - potential) / 507), every char ratio (total / 927,751), every mean
(total / 507), and every budget flag (ratio <= 0.75 / <= 0.50) is correct.

**Provenance note.** The figures `229/246/31/1` and `229/460/414/491/293/506` are the
**pre-remediation** `a_prepare/` values that F4 declared unreproducible. The corrected values are
`197/265/44/1` and `197/452/414/486/506/481`, and those are exactly what this audit reproduces.
The old `transparent_stop_expand` figures (potential 293, chars 471,147, ratio 0.498) remain
**not reproducible from any available program** - there is no `a_prepare/` code to derive them.
That is the expected state after F4, not a new defect.

## Check 5 - gold leakage into action selection

**PASS for deployable actions. Self-proven negative.**

`deployable_action` carries only `ranking_scores` and `stop_stage` (3,042/3,042 shapes, 507 rows
x 6 frontiers). Empirical proof that selection is ranking-derived and not gold-derived:

- `small_topk_3` selection == top-3 by score: **507/507, 0 mismatches**.
- `larger_topk_5` selection == top-5 by score: **507/507, 0 mismatches**.
- `table_only` selects zero paragraphs: 507/507.
- No frontier selection contains an order absent from `ranking_scores`: 0 injections.
- `gold_inputs_used`, `gold_paragraph_ids_used`, `hidden_scale_used` = `false` on **507/507** rows.
- `build_frontier_actions` is invoked with only `question["question"]` and
  `record["paragraphs"]`; ranking reads only paragraph order/uid/text; the stop rule uses
  question-token coverage. No gold variable reaches ranking, neighbor construction or the stop
  rule. An independent gold-free pipeline reproduces 100% of published actions.

Gold lives only under `offline_reference_only` (`reference_answer`, `reference_scale`,
`required_paragraph_orders`, `reference_classification`) and in explicitly `_offline`-suffixed
scoring fields.

**Design boundary D must respect (not a violation).** The *frontier-level* screen is gold-scored
by construction: `semantic_reference_potential` is computed from gold `rel_paragraphs`/`answer`,
and the margin screen uses it to decide which frontier is a diagnostic candidate and whether the
disposition is NO_GO. This is permitted - `A_REMEDIATE_TASK.md` allows gold "only for offline
scoring" - but it means the **candidate-selection decision is an offline gold-scored judgement,
not a deployable gold-free rule**, and must never be reported as the latter.

*(Auditor's own false positive, recorded for the record: a first-pass leak scan reported 168
"leaks" of `reference_answer` into `deployable_action`. Those are substring collisions - short
numeric gold answers such as the string 1 matching the paragraph-order **keys** of
`ranking_scores`, which is a map keyed by paragraph order. Not leakage. Re-tested properly as
above.)*

## Check 6 - answer-matching rule and pre-registration receipt frozen before generation

**PASS on ordering and on zero generation. Two rule defects filed (R2, R3).**

Freeze ordering is established three independent ways:

1. Program-enforced: `verify_preregistration` (`P2_RECOVERY_RECOMPUTE.py:567-601`) hard-fails
   (`PRE_REGISTRATION_CHECK_FAILED`) unless `program_sha256`, `answer_matching_rule_sha256` and
   `source_sha256` in the receipt match the files on disk, the margin is `-2.0`, the budgets are
   75 and 50 percent, the selection rule and paired unit are present, and `frozen_at` is earlier
   than execution start. All 8 checks are `true` in the published payload. All 8 self-tests
   (`answer_matching_self_tests`) pass and the program refuses to run otherwise.
2. Timestamps: `frozen_at` 2026-10-26T16:37:47+08:00 (08:37:47 UTC) is earlier than
   `execution_started_at` 08:38:21.350 UTC - the freeze predates the frontier computation by
   34 s.
3. Filesystem: `P2_ANSWER_MATCHING_RULE.json` (16:38:03.918) and `P2_PREREG_RECEIPT.json`
   (16:38:21.309) were both written before `P2_RECOVERY_RECOMPUTE.json` (16:38:21.564). The
   program *reads* the receipt and rule and only *writes* the three outputs, so the ordering is
   structural, not asserted.

Caveat: the declared `frozen_at` (16:37:47) is 34 s earlier than the receipt file's own creation
time (16:38:21.309); it is stamped at program finalization. A self-reported timestamp cannot
prove its own ordering - the load-bearing evidence is the runtime hash check plus mtime order,
both of which hold. Non-blocking.

**Zero generation in remediation - self-proven.** The program contains no network, model, judge
or database surface at all (`requests`/`urllib`/`http`/`socket`/`openai`/`anthropic`/`litellm`/
`subprocess`/`psycopg`/`sqlalchemy`/`eval`/`exec`/`os.system`: **0 hits** in 1,018 lines) and
runs in 0.255 s. The whole goal directory has **0 hits** for the same token set. A's loop
transcript contains **194 `command_execution` items, and 0 of them** reference canary,
`loop_b`/`loop_b_verify`, pytest, `curl`, `qwen_harness_tools`, `opencode`, any model port
(`:5050`/`:8004`/`:8006`/`:8008`/`:4096`), or any OpenAI/Anthropic/LiteLLM/chat-completions
surface. A's commands are `apply_patch`, `python3` heredocs over frozen data, `jq`, `rg`, `cat`,
`sed`, `find`, `date`, `sha256sum` - pure offline analysis. **A made zero model, judge, training,
production and confirmation calls.**

## Check 7 - frontiers and the margin/budget screen at row level

**PASS. Answer to the question posed: no restricted challenger passes both conditions.**

Applying the frozen selection rule (budget at most 75% **or** at most 50% of always-expand
**and** at most 3 deterministic actions **and** gap at most 2.0 pp):

- Cost-and-action-passing set is `table_only`, `small_topk_3`, `fixed_top1_neighbor`.
  Smallest gap in that set = **10.650888 pp** (`small_topk_3`) - 5.3x outside the 2.0 pp margin.
- Margin-passing set among restricted frontiers is **empty**.
- Intersection is **empty** -> `qualified_challenger: null`, `diagnostic_candidate: null`,
  `disposition: NO_GO`. Correct.

The two near-margin frontiers fail on cost, not margin, so no margin value rescues them:
`larger_topk_5` (gap 3.944773) fails both budgets (0.834 > 0.75) **and** the action cap (5 > 3);
`transparent_stop_expand` (gap 4.930966) fails both budgets (0.846 > 0.75) and has a
stage-dependent action count. Flip thresholds are >= 60.946746 (`table_only`), >= 18.145957
(`fixed_top1_neighbor`), >= 10.650888 (`small_topk_3`). **No margin in the open interval (0, 5]
pp produces a qualified challenger**; the outcome is insensitive to the margin value in that
range. This is a stronger robustness statement than the prior pre-audit's (0, 2.96) interval.

## Check 8 - exposure and source clusters

**PASS.** `row_results` distributions reproduce the prior independently-verified baseline
exactly: `existing_role` UNASSIGNED 472 / reserve 21 / history 7 / development 1 /
excluded_pending_review 6 = 507; `effective_exposure_category` STRUCTURAL_SCAN_ONLY 448 /
PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE 22 / METHOD_DEVELOPMENT_OR_DIAGNOSTIC 16 /
MODEL_OR_FEEDBACK_EXPOSURE 14 / EXPOSURE_UNKNOWN 6 / PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW 1
= 507; 156 distinct `source_cluster_id`.

All five selected development examples verified field-by-field against the pinned raw **and**
against `SOURCE_EXPOSURE_QUALIFICATION.json`: `question_uid`, `question` text, `table_uid`,
`answer_from == "table-text"`, `record_index`, `question_index`, `source_cluster_id`
(cluster_0596, cluster_1151, cluster_0385, cluster_1707, cluster_1826),
`previous_effective_exposure_category == STRUCTURAL_SCAN_ONLY` and
`previous_existing_role == UNASSIGNED` - **5/5 all checks pass**. Proposed counts
UNASSIGNED 467 (= 472 - 5) / development 6 (= 1 + 5) / reserve 21 / history 7 /
excluded_pending_review 6 = 507 are arithmetically consistent. The five P1 examples are
correctly registered as prior frozen exposure with `new_development_exposure: false`.
`register_state` is `PROPOSED_ONLY_NOT_WRITTEN_BACK_TO_PRIOR_QUALIFICATION` and the prior
qualification hash is unchanged - the register is a proposal, not a rewrite. Correct.

---

## Findings

Dispositions: **[NEW]** needs new filing; **[BASELINE]** already filed in `C_PREAUDIT`, status
updated; **[WAIVABLE]** record only.

### Release-blocking

**R1 [NEW] - `superseded-claim-left-live-in-prior-version`** (severity: medium)
`a_prepare/MECHANISM_NEIGHBORS.md` row 2 still asserts "Deterministically repairs all five
frozen natural failures" and "Use latest-minus-previous, inclusive-range, and
section-row-plus-named-entity rules", and the table still quotes the unreproducible "229/507".
Both are superseded. Nothing in `a_remediate/` supersedes them - a full-text scan of the
directory returns only frontier-name hits for "neighbor". Root cause: F2's second clause
("correct `MECHANISM_NEIGHBORS.md` row 2") was **not carried into `A_REMEDIATE_TASK.md`'s
required corrections or its 11 required outputs**, while A was simultaneously forbidden to edit
`a_prepare/`. So A complied with its written contract and the stale claim survived. Premise
violated: a remediation must not leave a falsified claim readable in a live artifact. Fix:
publish a corrected neighbor row in `a_remediate/` and mark
`a_prepare/MECHANISM_NEIGHBORS.md` row 2 and the 229/507 figure **SUPERSEDED**. A must not edit
`a_prepare/`.

**R2 [NEW] - `frozen-rule-claims-unimplemented-normalization`** (severity: medium, latent)
`P2_ANSWER_MATCHING_RULE.json` declares numeric normalization as "Strip $, commas, percent sign,
and scale words only after checking explicit-unit compatibility". The implementation strips
commas between digits and handles parenthesized negatives and full scale words, but **does not
strip the dollar sign, the percent sign, or the scale word "percent"** - those all return
`numeric_parse_failure`:

| candidate | reference | scale | result |
|---|---|---|---|
| `68.07%` | 68.07 | percent | **False** (`numeric_parse_failure`) |
| `68.07 percent` | 68.07 | percent | **False** |
| `$1,496.5` | 1496.5 | million | **False** |
| `1,496.5 million` | 1496.5 | million | True |
| `(1,955)` | -1955 | - | True |

Latent only: `match_full_semantic_answer` is called **only** from `answer_matching_self_tests`
(`:534-541`), never in the row loop or the screen, so no published number is affected. But the
rule is frozen and hash-pinned into the receipt, and TAT-QA answers routinely carry percent
signs, dollar signs and percent scales - so a released probe scored under this rule would mark
numerically correct, unit-correct answers wrong. Premise violated: a frozen scoring rule must
implement what it declares. Fix before **any** probe release: implement the declared
normalization (or narrow the declared scope to what is implemented), extend the self-tests to
cover the percent sign, the dollar sign and the "percent" scale word, and re-freeze the rule plus
the receipt hash.

### Non-blocking

**R3 [NEW] - `declared-metric-and-unit-diverge-from-executed-screen`** (severity: low)
`P2_PREREG_RECEIPT.json` declares `primary_metric` = `full_semantic_answer_accuracy` and a
`paired_analysis_unit` over "the same 506 qualified questions ... excluded before output". The
executed screen measures the margin on `semantic_reference_potential` and computes every gap
with denominator **507** (`P2_RECOVERY_RECOMPUTE.py:742`). `full_semantic_answer_accuracy` is
computed nowhere - 0 occurrences in `P2_RECOVERY_RECOMPUTE.json`. The distinction is honestly
labelled (`metric_warning`: "semantic_reference_potential is an offline evidence ceiling, not
model accuracy"), so this is a declaration inconsistency, not a misrepresentation. Immaterial to
the decision: on the declared 506 unit the gap for `small_topk_3` is 10.671937 pp instead of
10.650888 pp - both far outside the 2.0 pp margin. Fix: align the receipt's `primary_metric` and
paired unit with the executed screen, or state explicitly that the pre-generation screen is a
ceiling proxy for the declared primary.

**R5 [NEW] - `hardcoded-count-literals-in-recompute-output`** (severity: low).
`answers_present=507`, `complete_semantic_answer_references=506`, `incomplete=1`,
`nonempty_tables=507`, `valid_nonempty_rel_paragraph_sets=507` are literals in
`P2_RECOVERY_RECOMPUTE.py` (`:734`, `:805`, `:856-859`, `:874-875`), not derived at runtime.
They match the current pinned data (verified), so no published number is wrong; the program
would silently misstate them if the source changed. The source is hash-pinned and the program
aborts on mismatch, which bounds the risk. Fix: derive the counts at runtime.

**R4 [BASELINE - scope widened] - `evidence-transcription-not-checkable-as-written`**
(severity: low). The pre-audit's non-blocking note is confirmed and is broader than stated:
`actor_visibility.relevant_visible_rows` **duplicates the target row** in **all 5** diagnoses
(listed 2/2/3/2/3 times, unique 1 each), and the R1 period-label row - where the sign convention
used by the `b7814ec0` diagnosis actually lives - is **omitted in 3 of 5** (`38e317da`,
`cf77f5f9`, `b7814ec0`). The pre-audit's separate candidate-2 header complaint is **fixed**
(`72f960c0` now carries the literal frozen `columns: C0= | C1= | C2=2019 | C3=2018`).
Conclusions are unaffected because `complete_table_and_header_visible: true` and the full table
is visible. Additionally `offline_reference_only` drops the frozen `expected.evidence_refs` key
and adds an undeclared `deployment_leakage: false`, while
`supervision_visibility_separation.offline_reference_fields` declares
`evidence_refs, program, unit, answer` - a declared-vs-emitted schema mismatch. Gold
`evidence_refs` do survive under `legal_evidence.evidence_refs` (4 of 5 identical to frozen; the
5th is the same cell set reordered). `actor_visibility` carries **no** gold answer, gold program
or gold refs (verified on all 5), so this is fidelity, not leakage. Fix: emit distinct visible
rows including the axis-label row, and make the declared field lists match what is emitted.

### Waivable / disclosure

**R6 [NEW] - `background-canary-not-attributable-to-task`** (severity: informational).
Per `CLAUDE.md` ("if a permitted read-only health probe occurs, report its count explicitly"):
during the remediation window the **Loop B daemon** completed one of its routine 1800 s cycles
and its standard QA canary made **4 model calls** (`q06_minan_cash_balance`, `adv_ocr_meta`,
`adv_cross_doc`, `adv_refusal`; entries at 16:44:55, 16:45:34, 16:46:24, 16:47:07 in
`logs/graph/b4_ask_log.jsonl`, matching `logs/graph/canary_latest.txt` reporting 4/4 passed).
Provenance is decisive and **not** A's: `loop_b.log` shows "Loop B starting in daemon mode
(poll every 1800s)" since 2026-07-30 and ends each cycle with "Sleeping 1800s until next
check"; `verify-report.json` declares `loop: B`, `role: independent_verification`,
`action: Loop A may continue`; and **0 of A's 194 commands** reference any canary or
verification entrypoint. The same 4-call cadence recurs all day. No scientific generation,
judge, training, production or confirmation call occurred on this goal, and no probe was run.
Recorded so that no one later claims zero model calls occurred anywhere on the host in that
window.

---

## Blocking fixes before D relies on these cards

1. **R1** Publish a corrected mechanism-neighbors row and mark
   `a_prepare/MECHANISM_NEIGHBORS.md` row 2 and its 229/507 figure SUPERSEDED. Do not edit
   `a_prepare/`.
2. **R2** Correct and re-freeze the answer-matching numeric normalization (or narrow its declared
   scope), extend self-tests to the percent sign, dollar sign and "percent" scale word,
   regenerate the receipt hash - **before any probe is authorized**.

Neither changes any conclusion in this report. Both are prerequisites for *release*, not for the
D decision below.

## Recommendation (advisory evidence for D only)

**No primary. `NO_GO_STOP_MODEL_STAGE`.** Both stage-gate preference tests fail on corrected,
now-reproducible evidence:

- **P1** requires at least two genuine natural failures with a residual not explained by
  visible-only simple controls. Observed residual after `VISIBLE_AXIS_SCOPE_POLICY_V1` = **0**,
  and one of the five failures is a reference defect. Fails.
- **P2** requires a real cost frontier after strong baselines. No restricted frontier passes both
  the -2.0 pp margin and a frozen context budget, and none would at any margin in (0, 5] pp.
  Fails.

`D_STAGE_GATE.md`: "No candidate is forced. If neither passes, stop the model stage and continue
Paper E and thesis work." The conformant disposition is therefore to stop the model stage and
continue Paper E and thesis work.

If D nonetheless elects to revive a candidate after R1 and R2 are fixed:
**P2_TABLE_TEXT_EVIDENCE_COST** is the only one whose task is already legally qualified (506/507
always-expand is complete by construction; retrieval is correctly described as record-internal,
never corpus retrieval), but only as a *diagnostic* investigation of the 3.94 pp / 4.93 pp
near-margin frontiers whose failure is cost, not margin - not as a method result. **P1 must not
be revived**: its four genuine errors are fully explained by deterministic visible-only rules and
one of its five is a reference defect. P1 and P2 must not be merged into one novelty claim.

## Reproduction notes

All counts were recomputed in this session from the frozen P1 run files under
`/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/` and the pinned TAT-QA dev
raw, using read-only parsing, plus one execution of the published program into
`/tmp/crec_p2_rerun_c/`. `ls` and `sha256sum` are blocked outside the worktree in this
environment; all external reads and hashing were done via `python3` (`pathlib`/`hashlib`). Two
independent sub-agents ran raw-command reproduction with conclusions withheld. Skill load list
for this task (per `docs/SKILL_ROUTING.md` section 4, inferred - the task card carries no load
list): `audit-cycle` only, as the Loop C audit evidence-discipline layer; 1 of 5 budget used.

**Zero endpoint for this audit:** 0 model calls, 0 canaries, 0 judges, 0 generation, 0 training,
0 production calls, 0 confirmation calls, 0 database calls. The only external execution was the
read-only re-run of the published deterministic program (0.255 s, no network surface). The 4
Loop B canary model calls in R6 are background and are counted explicitly, not claimed by this
task. No file outside
`research/natural_error_evidence_cost_20261026_v1/audits/C_REAUDIT.md` and
`research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_REAUDIT.json` was
modified.
