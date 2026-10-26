# C Independent Final Candidate And Closeout Audit

**Nature of document.** Advisory Loop C audit report. It reports and recommends; it does not
repair. Adjudication belongs to the human owner. No A artifact was modified.

**Audited object and baseline.** `research/natural_error_evidence_cost_20261026_v1/a_closeout/`
(9 files, authority commit `622b386986ca66c8119263e146f3d3e73c33e260`), audited against the
frozen P1 run (`/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/`), the pinned
TAT-QA dev source, and the preserved `a_prepare/` and `a_remediate/` identities. The
known-anomaly baseline is `audits/C_REAUDIT.md` findings **R1-R6**; anything inside that set is a
*known case*, not a new finding. This audit's question is closure of R1-R5 plus the R6 disclosure,
and the correctness of the final candidate disposition.

**Independence declaration.** This auditor did not author any audited artifact. Mitigations
performed, not promised: (a) the auditor re-executed `P2_RECOVERY_RECOMPUTE_FINAL.py` personally
into a scratch directory and diffed the entire published payload against the replay; (b) the
answer matcher was probed with a 51-case battery written from the **declared rule text only**,
containing the five R2 regression cases plus adversarial cases not present in A's self-tests; (c)
P1 population, sign-convention controls and every transcribed visible row were reproduced from
the frozen raw before A's conclusions were used; (d) all published aggregates were recomputed
from the pinned source without importing the audited module. Findings against this auditor's own
probes are recorded in full, including probe expectations that turned out to be wrong.

---

## Verdict

| Object | Verdict | Basis |
|---|---|---|
| R1 stale claims | **CLOSED** | Three supersessions published; `a_prepare/` and `a_remediate/` byte-identical (30/30 hashes). |
| R2 matcher + freeze | **CLOSED IN SUBSTANCE** | All five R2 failures fixed; 18/18 self-tests; freeze order structural and correct. Two declaration clauses remain unimplemented (R7, R8), both over-permissive and latent. |
| R3 metric declaration | **CLOSED** | Offline proxy and future model metric now declared separately in rule, receipt and payload. |
| R4 P1 transcription | **CLOSED** | Distinct rows 5/5, period-axis rows 3/3 where required, declared field lists == emitted on all 10 objects. One pre-existing reorder retained (R9). |
| R5 runtime aggregates | **CLOSED** | Zero count literals in the program; full replay reproduces; aggregates recomputed from pinned source match. |
| R6 call attribution | **CLOSED + DISCLOSED** | Zero attributable model/judge/training/production/confirmation calls; independent Loop B canary reported separately. |

**Overall: `CONDITIONAL`.** Every R1-R5 finding is substantively closed and the scientific
conclusion is verified at row level. Two low-severity declaration-vs-implementation gaps in the
frozen answer matcher (R7, R8) mean task item 2's literal requirement - "implements **all**
declared normalization" - is not fully met. Neither can mark a correct answer wrong, and the
matcher is still not on the scoring path, so neither is release-blocking in the R2 sense. Both
must be closed before any probe is authorized.

**Final candidate disposition: `NO_GO_STOP_MODEL_STAGE` - verified, unchanged, and the correct
conformant disposition.**

---

## Integrity of audited inputs

All frozen inputs re-hashed this session. `a_prepare/` (13 files) and `a_remediate/` (17 files)
match every hash declared in `A_CLOSEOUT_RESULT.prior_version_preservation` - **30/30 match, 0
mismatches, no file present on disk that is undeclared and none declared that is missing**.
`prior_version_preservation.byte_identical: true` is accurate. All 8 required `a_closeout/`
outputs match their declared `sha256` and `bytes`. The pinned dev source re-hashes to
`8da095a819af6db3`, matching the receipt and the program constant.

**`a_prepare/` was not modified.** Confirmed by hash, not by assertion.

---

## R1 - stale `5/5` and `229/507` claims superseded

**CLOSED.**

`a_closeout/MECHANISM_NEIGHBORS_CORRECTED.md` publishes three explicit `SUPERSEDED` markers:

| Superseded claim | Replacement | Verified |
|---|---|---|
| "Deterministically repairs all five frozen natural failures" | **4/5 overall / 4/4 genuine**, 0 residual | matches `control_replay_summary.single_visible_axis_scope_policy` and `gate.observed_residual_genuine_failures: 0` |
| row-2 table `229/507` | table-only `197/507` | reproduces from the replay |
| transparent-stop `293/507` | `481/507` | reproduces from the replay |

The corrected frontier table is not hand-written prose: every figure reproduces from the replayed
`published_payloads.frontiers` payload (see R5). The always-expand row's `mean 1829.9, p95 5153,
max 9111` matches the replayed `always_expand` summary exactly.

**Non-blocking residual (waivable).** The corrected row-2 `Strongest deployable action` cell still
carries the phrase "Use latest-minus-previous, inclusive-range, and
section-row-plus-named-entity rules", which `C_REAUDIT` R1 listed among the stale row-2
assertions. The deployed policy is `VISIBLE_AXIS_SCOPE_POLICY_V1`, a 6-rule ordered policy
(`1_visible_completeness`, `2_explicit_period_binding`, `3_change_direction`, `4_inclusive_range`,
`5_label_scope`, `6_numeric_reference_validation`). The three *falsified* clauses ("all five",
"229/507", "293/507") are explicitly superseded; this phrase is a partial description of the
deployable action in a non-falsified column. Accuracy nit only - it does not reinstate any
superseded claim.

## R2 - final matcher, self-tests and freeze order

**CLOSED IN SUBSTANCE. Two declaration gaps remain (R7, R8).**

### The five R2 failures are fixed

Auditor-written probes, each passing now (all previously returned `numeric_parse_failure`):

| candidate | reference | scale | result | reason |
|---|---|---|---|---|
| `68.07%` | 68.07 | percent | **True** | `numeric_isclose` |
| `68.07 percent` | 68.07 | percent | **True** | `numeric_isclose` |
| `$1,496.5` | 1496.5 | million | **True** | `numeric_isclose` |
| `1,496.5` | 1496.5 | million | **True** | `numeric_isclose` |
| `(1,955)` | -1955 | - | **True** | `numeric_isclose` |

The declared numeric normalization is implemented and now observed: dollar sign and `usd`/`dollar`
tokens (`_parse_number:490`), percent sign and `percent`/`percentage` words (`:497`, `:491-496`),
`billion`/`million`/`thousand` scale words with `bn`/`mn`/`tn`/`k` aliases, parenthesized negatives
including an inner explicit minus (`:488-503`), and the frozen `math.isclose(rel_tol=1e-6,
abs_tol=1e-6)` tolerance (`:550-557`). Common normalization is implemented in `normalize_text`
(`:161-167`): NFKC, casefold, quote translation, dash/minus translation including U+2212
(`TEXT_TRANSLATION:119-138`), whitespace collapse, digit-adjacent comma removal, terminal
punctuation trim that excludes `%`.

### Self-tests

**18/18 pass.** All 9 names in `executable_implementation.required_self_tests` are present and
passing, and the program hard-fails (`ANSWER_MATCHING_SELF_TEST_FAILED`, `:677-679`) before any
computation if one fails. Task item 3's required cases are all covered: `68.07%`, `68.07 percent`,
`$1,496.5`, `1,496.5`, parenthesized negatives (`parenthesized_negative`,
`parenthesized_explicit_negative`), multi-span (`multi_span_order`), count (`count_integer`) and
UNKNOWN (`reasonable_unknown`, `unsupported_unknown`).

Auditor's independent 51-case battery, written from the declared rule text alone, agreed with the
implementation on **48/51**. The three disagreements are R7 and R8 below.

### Freeze order - correct and structural

Three independent routes agree:

1. **Hash chain.** `rule.executable_implementation.implementation_sha256` == program sha;
   `receipt.program_sha256` == program sha; `receipt.answer_matching_rule_sha256` == rule sha.
   All three verified against disk. The receipt's own hash appears unchanged inside
   `preregistration.receipt_sha256` in the payload.
2. **Filesystem mtime order** (UTC, 2026-10-26): program `09:48:27.910` -> rule `09:48:58.269`
   -> receipt `09:49:22.582` -> recompute output `09:54:58.645` -> the other four outputs
   `09:54:58.687` -> `A_CLOSEOUT_RESULT.json` `09:56:06.427`. The implementation hash is fixed
   **before** the rule that cites it, and the rule is frozen **before** the receipt that cites it.
3. **Program-enforced.** `verify_preregistration` (`:623-657`) hard-fails unless all 8 checks
   hold; all 8 are `true` in the published payload. `frozen_at` 09:49:18 UTC precedes
   `execution_started_at` 09:54:58 UTC by 5 m 40 s.

Known non-blocking caveat, carried forward from `C_REAUDIT`: `frozen_at` self-reported timestamps
precede their own file mtimes (rule by 18 s, receipt by 4 s). A self-reported timestamp cannot
prove its own ordering. The load-bearing evidence is the hash chain plus mtime order, both of
which hold. This audit confirms the structural ordering, not the stamps.

---

### New residuals against the same premise

The R2 premise is "a frozen scoring rule must implement what it declares." Two declared clauses
are still not implemented. Both are **over-permissive** - the opposite direction from R2, so
neither can mark a numerically correct answer wrong - and both are **latent**, because
`match_full_semantic_answer` is called **only** from `answer_matching_self_tests` (`:578-597`) and
never in the row loop or the screen (call-site scan confirms; `answer_matching_self_tests` is
invoked at `:677` as a gate and `:1054` for reporting only). No published number depends on the
matcher.

**R7 [NEW] - `frozen-rule-strips-all-commas-not-only-digit-adjacent`** (severity: low, latent).
`answer_normalization.common` declares "remove thousands separators **only** when a comma is
between ASCII digits", and the numeric list repeats "strip commas **between digits** as thousands
separators". `normalize_text:165` implements this correctly (`(?<=\d),(?=\d)`), but
`_parse_number:498` then runs an unconditional `text.replace(",", "")`, so any comma survives
normalization into a numeric parse. Probe: candidate `1, 496` (comma followed by a space) scores
**True** against reference `1496`; under the declared rule the comma is not a thousands separator
and the string does not parse as a single number. Harm direction is benign - a slightly wider set
of comma placements is accepted - but a candidate that writes `1, 496` meaning two values would be
scored as one correct number. Fix before probe release: restrict `_parse_number`'s comma removal to
digit-adjacent commas, or narrow the declaration.

**R8 [NEW] - `frozen-count-rule-does-not-reject-negative`** (severity: low/informational, latent).
`count_handling.accepted` declares "Exactly one finite **non-negative** integer". The
implementation (`:546-549`) checks only `is_integer()` and equality. Probes: `match("-5", -5,
"count", "", False)` -> **True**; `match("(5)", -5, "count", "", False)` -> **True**. Practically
unreachable - TAT-QA count gold is never negative, so a negative candidate against real gold fails
equality (verified: `match("5", -5, ...)` -> False) - but the declared constraint is unimplemented.
Fix before probe release: reject non-finite or negative parsed values for `count`, or narrow the
declaration to "integer".

## R3 - prereg metric separates the offline proxy from the future model metric

**CLOSED.** The R3 divergence is resolved in all three places it matters:

- `P2_ANSWER_MATCHING_RULE_FINAL.json.metric_scope` splits `executed_screen`
  (`semantic_reference_potential`, denominator 507, "offline evidence-sufficiency proxy; not model
  accuracy") from `future_model_evaluation` (`full_semantic_answer_accuracy`, denominator 506).
- `P2_PREREG_RECEIPT_FINAL.json` now has separate `executed_screen` and `future_model_evaluation`
  blocks, and the top-level `primary_metric` / `paired_analysis_unit` are explicitly scoped "for
  the executed offline screen". The old R3 mismatch - a receipt declaring
  `full_semantic_answer_accuracy` while the screen computed gaps on
  `semantic_reference_potential` over 507 - is gone.
- `P2_RECOVERY_RECOMPUTE_FINAL.json.screen_metric_contract` carries the same four fields, and
  `metric_warning` still states that `semantic_reference_potential` is an offline evidence ceiling
  and that characters are not measured tokens, latency, memory or cost.

`full_semantic_answer_accuracy` is computed nowhere - correctly, since zero model output exists. It
is declared only as the future metric, which is what R3 asked for. The 507/506 denominators are
accurate: 507 table-text questions, 506 with `reference_status != NOT_MODEL_READY` (the single
`unresolved` `source_requirement` item is excluded).

## R4 - P1 example transcription

**CLOSED.** All three required corrections verified against the frozen raw, not against A's labels.

**Distinct visible rows.** `len(set(relevant_visible_rows)) == len(relevant_visible_rows)` on all
5 diagnoses and all 5 ledger `per_candidate` entries (2/2, 1/1, 2/2, 2/2, 1/1). The prior
duplicate-target-row defect is gone. `visible_example_transcription.distinct_relevant_visible_rows:
true` is accurate.

**Period-axis row.** Emitted in 3 of 5 - `38e317da`, `cf77f5f9`, `b7814ec0` - which is exactly the
set `C_REAUDIT` R4 flagged as missing it. `visible_example_transcription.period_axis_rows_emitted:
3` is accurate. The other two are correct omissions: `72f960c0`'s axis lives in its emitted
`table_header` (`columns: C0= | C1= | C2=2019 | C3=2018`) and its question names no years;
`4c2c23e7`'s axis is person names (`Chris Lien | Wister Walcott | Robert Bertz`), not periods.

**Declared field lists == emitted fields.**
`supervision_visibility_separation.actor_visibility_fields` and `offline_reference_fields` match the
emitted key sets exactly on all 10 objects (5 diagnoses + 5 ledger candidates). The undeclared
`deployment_leakage` key is gone, and `offline_reference_only` now carries the frozen
`evidence_refs` key that R4 noted was dropped.

**Transcription fidelity, independently checked.** Against
`source_disjoint_instances_v4.jsonl`, for all 5: every `relevant_visible_rows` entry is a literal
line of the raw `table_text`; every `table_header` equals the raw first line; every question text
matches; and `offline_reference_only.{answer,evidence_refs,program,unit}` matches the frozen
`expected` object.

**Residual R9 [NEW, waivable] - `evidence_refs-order-not-frozen-order`** (severity: low). For
`4c2c23e7` only, `legal_evidence.evidence_refs` and `offline_reference_only.evidence_refs` are
emitted sorted ascending (`R2:C1, R2:C2, R2:C3`) while the frozen `expected.evidence_refs` is
`R2:C3, R2:C2, R2:C1` - the gold program's evaluation order. Same cell set; the other 4 of 5 match
the frozen order exactly. `offline_reference_only.program` is preserved byte-for-byte and recovers
the evaluation order, so no information is lost. This is the same one-item reorder `C_REAUDIT` R4
already recorded; it was not in R4's required fix list and is not a regression. Record only.

---

## R5 - runtime-derived aggregates, row-level reproducibility

**CLOSED.**

**No count literals remain.** A literal scan of `P2_RECOVERY_RECOMPUTE_FINAL.py` for
`507|506|229|246|414|452|486|293|197|265|44|927751|223082` returns **zero hits**. Every published
count derives from a runtime accumulator (`answers_present_count`, `complete_reference_count`,
`incomplete_reference_count`, `record_count`, `all_question_count`, `source_cluster_count`,
`nonempty_table_count`, `valid_rel_paragraph_set_count`) at `:691-716` and `:798-811`. The prior
literals at `:734`, `:805`, `:856-859`, `:874-875` of the remediation program are gone.

**Independent replay.** `python3 P2_RECOVERY_RECOMPUTE_FINAL.py --output-dir /tmp/cfinal_replay_a`
-> exit 0, `rows: 507`, `row_results_sha256 = 93ce50e26d51359c5e8dca9cca9381607b50f762c93ff3cce3da164d830f340e`,
`disposition: NO_GO_STOP_MODEL_STAGE`, `diagnostic_candidate: null`. That row hash reproduces
**exactly** and is identical to `prior_remediation_row_results_sha256`, so row-level identity is
preserved across the closeout.

**Full payload diff, published vs replay: 3 differences only** - `execution_started_at`,
`execution_completed_at`, `preregistration.receipt_path` (different output directory). Every one
of the 507 rows and every aggregate is identical.

**Hash chain recomputes** under the program's own canonicalization
(`ensure_ascii=False, sort_keys=True, separators=(",",":")`): `row_results_sha256`,
`frontiers_payload_sha256` (`8a015ce0ef344914...`), `qualification_payload_sha256`
(`383cdaf8cd6d6a92...`) all match their payloads at `published_payloads.frontiers` /
`.qualification`. 507 rows, 507 unique `question_uid`.

**Aggregates recomputed from the pinned source without the program.** 507 table-text questions,
278 records, 1668 total questions, answer types arithmetic 205 / span 181 / multi-span 101 /
count 20, `answers_present` 507 - all match the published payload exactly.
`source_requirement` table 197 / both 265 / paragraph 44 / unresolved 1 and `scale_source`
not_required 170 / paragraph 237 / question 60 / table 13 / table_and_paragraph 6 / unresolved 21
match the `C_REAUDIT` independently-verified baseline.

**Frontier arithmetic re-derived independently.** Every gap (`100 * (always_potential - potential)
/ 507`), every char ratio (`total / 927751`) and every budget flag (`ratio <= 0.75` / `<= 0.50`
and `actions <= 3`) is correct:

| Frontier | potential | gap pp | char ratio | total chars | gold recovery | actions | 75% | 50% | margin |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| `table_only` | 197 | 60.946746 | 0.240455 | 223,082 | 0 | 0 | pass | pass | fail |
| `small_topk_3` | 452 | 10.650888 | 0.667945 | 619,687 | 441 | 3 | pass | fail | fail |
| `fixed_top1_neighbor` | 414 | 18.145957 | 0.590626 | 547,954 | 381 | 3 | pass | fail | fail |
| `larger_topk_5` | 486 | 3.944773 | 0.834024 | 773,767 | 482 | 5 | fail | fail | fail |
| `always_expand` | 506 | 0.0 | 1.0 | 927,751 | 507 | all | - | - | baseline |
| `transparent_stop_expand` | 481 | 4.930966 | 0.846059 | 784,932 | 480 | <=5 stages | fail | fail | fail |

*Non-blocking note.* `A_CLOSEOUT_RESULT.json.aggregate_counts` states `p2_table_text_questions:
507` and `p2_complete_semantic_references: 506` as literals in a **report** file. Both agree with
the runtime values. R5 was scoped to the recompute program's output; a result document stating its
own computed values is expected and is not a hardcoded aggregate in the derivation path.

## R6 / task item 6 - call attribution

**CLOSED. Zero model, judge, training, production or confirmation call is attributable to this
task.** Self-proven, then disclosed separately.

`a_closeout/` scanned in full for
`requests|urllib|httpx|http://|https://|socket|openai|anthropic|litellm|subprocess|psycopg|sqlalchemy|os.system|eval(|exec(|canary|loop_b|qwen_harness|opencode|curl|pytest|model ports|chat/completions`:
**6 hits total, all of them declarations** - `judge_calls: 0`, `zero_judge: true`, and the receipt
scope string. Zero import or call surface. `P2_RECOVERY_RECOMPUTE_FINAL.py` (1,121 lines) has no
network, model, judge or database surface and completes in ~0.2 s.
`scientific_totals_added` is all zeros; `zero_endpoint_calls`, `zero_judge`, `zero_generation`,
`zero_training`, `zero_production_calls`, `zero_confirmation_calls`, `zero_database_calls` are all
true in both `A_CLOSEOUT_RESULT.json` and `STAGE_CANDIDATE_FINAL.json`.

**Separate disclosure - independent Loop B canary (informational).** Per `CLAUDE.md` ("if a
permitted read-only health probe occurs, report its count explicitly"): the **Loop B daemon**
continued its routine 1800 s QA canary cycles on the host throughout 2026-10-26.
`logs/graph/b4_ask_log.jsonl` (under `scripts/graph/loop_b_verify.sh`, outside this goal) holds
**132 entries dated 2026-10-26** = 33 cycles x 4 model calls, and `logs/graph/canary_latest.txt`
reports `q06_minan_cash_balance`, `adv_ocr_meta`, `adv_cross_doc`, `adv_refusal` at **4/4 PASS**.
Bounding the A closeout artifact-production window by file mtime (**09:48:27 - 09:56:06 UTC**),
**0 canary model calls fall inside it**; the nearest cycles are 4 calls at 09:36:21-09:38:22 UTC
(immediately before) and 4 calls beginning 10:09:06 UTC (immediately after). Provenance is
decisively not A's and not this goal's. Recorded so that no one later claims zero model calls
occurred anywhere on the host that day.

---

## Blocking fixes before any probe is authorized

1. **R7** Restrict `_parse_number`'s comma removal to digit-adjacent commas (or narrow the
   declaration), and add a self-test for `1, 496`.
2. **R8** Reject non-finite or negative parsed values for `count` (or narrow the declaration to
   "integer"), and add a negative-count self-test.

Neither changes any number in this report. Both are prerequisites for *release*, not for the D
decision below. They are strictly weaker than the original R2: the original could mark a correct
answer wrong, these cannot.

---

## Recommendation (advisory evidence for D only)

**No primary. `NO_GO_STOP_MODEL_STAGE`.** Independently reconfirmed:

- **P1** requires at least two genuine natural failures with a residual not explained by
  visible-only simple controls. Population reproduces from the frozen raw:
  `ordinary_answer_execution_sft` x `original` = 24 rows, `program_correct` True 19 / False 5,
  failing instances `38e317da`, `72f960c0`, `cf77f5f9`, `b7814ec0`, `4c2c23e7`. Four are genuine
  model errors, one (`b7814ec0`) is a reference/scoring defect - reconfirmed by sign-convention
  analysis: all five `identically_phrased_controls` in the ledger verify against the frozen raw as
  `R#:C1 - R#:C2` (later-minus-earlier on axis `C1=2019 | C2=2018`) with gold values -9005.0,
  +368.0, -29.0, +1.6, +1249.0, while `b7814ec0` alone uses `R5:C2 - R5:C1` = +1955.0. Residual
  after `VISIBLE_AXIS_SCOPE_POLICY_V1` = **0**. Fails.
- **P2** requires a real cost frontier after strong baselines. Cost-and-action-passing set is
  {`table_only`, `small_topk_3`, `fixed_top1_neighbor`}; smallest gap in that set is **10.650888
  pp** (`small_topk_3`), 5.3x outside the -2.0 pp margin. Margin-passing restricted set is empty.
  The two near-margin frontiers fail on **cost**, not margin: `larger_topk_5` (3.944773 pp) fails
  both budgets (0.834 > 0.75) and the 3-action cap (5); `transparent_stop_expand` (4.930966 pp)
  fails both budgets (0.846 > 0.75). No margin in (0, 5] pp produces a qualified challenger.
  Fails.

`D_STAGE_GATE.md`: "No candidate is forced. If neither passes, stop the model stage and continue
Paper E and thesis work." `STAGE_CANDIDATE_FINAL.json` is conformant: `selected_primary_candidate:
null`, `model_probe_authorized: false`, disposition `NO_GO_STOP_MODEL_STAGE`. The A closeout task
card's own guard - "Final disposition must remain `NO_GO_STOP_MODEL_STAGE` unless the final
row-level replay actually produces a restricted frontier passing both the frozen margin and
budget" - is satisfied: it does not, so the disposition is correct.

If D nonetheless elects to revive a candidate after R7 and R8 are fixed:
**P2_TABLE_TEXT_EVIDENCE_COST** is the only legally qualified task (506/507 always-expand complete
by construction; retrieval is correctly described as record-internal, never corpus retrieval), and
only as a *diagnostic* investigation of the 3.94 pp / 4.93 pp near-margin frontiers - never as a
method result. **P1 must not be revived**: its four genuine errors are fully explained by
deterministic visible-only rules and one of its five is a reference defect. P1 and P2 must not be
merged into one novelty claim.

## Reproduction notes

All counts were recomputed in this session from the frozen P1 run files under
`/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/` and the pinned TAT-QA dev raw,
using read-only parsing, plus one execution of the published program into `/tmp/cfinal_replay_a/`
and one 51-case matcher probe battery written from the declared rule text alone. External reads
and hashing were done via `python3` (`pathlib`/`hashlib`); the audited module was imported only to
*observe* matcher behaviour on the probe battery, never to accept its conclusions. Skill load list
for this task (per `docs/SKILL_ROUTING.md` section 4, inferred - the task card carries no load
list): `audit-cycle` only, as the Loop C audit evidence-discipline layer; 1 of 5 budget used.

**Zero endpoint for this audit:** 0 model calls, 0 canaries, 0 judges, 0 generation, 0 training,
0 production calls, 0 confirmation calls, 0 database calls. The only external execution was the
read-only re-run of the published deterministic program (~0.2 s, no network surface) and pure
Python parsing of frozen files. The Loop B canary model calls disclosed in R6 are background,
independent of this goal, and are counted explicitly above - not claimed by this task. No file
outside `research/natural_error_evidence_cost_20261026_v1/audits/C_FINAL_AUDIT.md` and
`research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_FINAL.json` was modified.
