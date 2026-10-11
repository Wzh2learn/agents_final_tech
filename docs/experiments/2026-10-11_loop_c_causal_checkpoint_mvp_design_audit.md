# Loop C Design Audit — Causality-Aware Checkpoint Selection MVP

- Task ID: `causal-checkpoint-mvp-design-audit-c-20261011`
- Role: Loop C / independent scientific audit (fresh context)
- Window: zero-endpoint, zero new scientific dataset — honored (model/endpoint/database/training/PRM/Stage-D counts all `0`)
- Evidence class: design audit + engineering verification
- Date: 2026-10-11

## Nature / Object / Independence

**Nature of this document.** Advisory audit report. It reports; it does not repair. No design or smoke
artifact was modified; no scientific experiment was run; no dataset was materialized; no mechanism,
metric or baseline was added.

**Audited object and baseline.** `research/causal_checkpoint_selection_mvp_20261011/` —
`METHOD_DESIGN_QUALIFICATION_V1.md` (design), `loop_a_dev_smoke_contract.md`, and the DEV_ONLY smoke
under `smoke/`. Baseline of already-known anomalies (pre-existing, not new findings of this audit):
FinQA v2 formal runs are `FORMAL_RUN_INVALID / SECOND_FLOW_INVALID`; multi-leaf is exploratory with a
narrowed claim; `docs_lint` has 6 known warnings; skill-doctor has 139 tracked warnings. Hits inside
this baseline are demoted to known.

**Independence declaration.** Loop A authored the audited artifacts; this Loop C session did not build
them. Mitigations actually taken, not promised: (a) two independent sub-agents gathered first-hand
source evidence by raw file reads, not author summaries; (b) the two most load-bearing claims
(duplicate-checkpoint aliasing; ablation collapse) were **re-verified personally** against primary
carriers before any verdict was formed; (c) the design document was read as the *object* under audit —
its readiness claims were not used as evidence. Ingestion disclosure: `memory/STATE.md` line 126-128
(Loop A's own status claim) was read at session start before evidence gathering; it asserts
`METHOD_DATASET_READY_PENDING_INDEPENDENT_LOOP_C_AUDIT`. That claim is an input under test, not a
premise. The reasoning chain below rests only on artifacts cited with file:line.

---

## FACT

F1. **Four frozen input hashes match exactly.** Independently recomputed:
`METHOD_DESIGN_QUALIFICATION_V1.md` `bcd83b66…301a3`, `config/eval_checkpoint_trees.json`
`0931d952…6bf25`, `multileaf_prediction_rows.jsonl` `37bb3601…2afa06`,
`multileaf_paired_artifacts.jsonl` `39c3a2c5…65e53f` — identical to `EXPECTED_INPUT_HASHES`
(`smoke/causal_checkpoint_selection_mvp.py:26-31`).

F2. **Smoke tests execute green, independently.** Command and result:
```
$ ./venv/bin/python -m pytest research/causal_checkpoint_selection_mvp_20261011/smoke/test_causal_checkpoint_selection_mvp.py -q -p no:cacheprovider
.........                                                                [100%]
9 passed in 0.94s
```
**Label: LOCAL.** Python 3.12.3 / pytest 9.0.1 via `./venv/bin/python`. Per repository rules this is
`DEV_ONLY / NON_AUTHORITATIVE`; it does **not** prove GB10 runtime. GB10 execution remains unverified.
The suite is read-only (it builds results in memory and *reads* the emitted JSON; it never calls
`generate_smoke_artifacts`), so the audit could not and did not rewrite audited artifacts.

F3. **Result schema is complete as specified.** `dev_smoke_result.json` carries all of
`REQUIRED_RESULT_FIELDS` and every baseline carries all of `REQUIRED_SELECTION_FIELDS`;
`required_fields_present: true`. Shape `PASS_216_X_12` (216 rows, 12 response fields, 12 checkpoints).
Split `DEV_ONLY_PSEUDO_FOLD` / `STAGE_STRATIFIED_GROUP_DISJOINT`, 57 train / 15 test groups,
171 / 45 rows, `group_overlap: []`, `mechanism_holdout: NOT_AVAILABLE`.

F4. **Zero scientific production.** `dev_smoke_receipt.json`: `scientific_claim=ZERO`,
`formal_experiment=ZERO`, `scientific_claim_count=0`, `formal_experiment_count=0`, `endpoint_calls=0`,
`model_training_runs=0`, `new_scientific_dataset_rows=0`, `design_contract_changed=false`,
`frozen_multi_leaf_artifacts_changed=false`. Inputs are the four frozen 216x12 carriers only. Check 11
**verified**.

F5. **`parse.table.regression` and `parse.field.hit_rate` are the same measurement.**
`research/stage_e_multileaf_20261010/run_multileaf_formal.py:257-258`:
```python
response["parse.table.regression"] = int(mutated_hit < baseline_hit)
response["parse.field.hit_rate"] = int(mutated_hit < baseline_hit)
```
Confirmed in data: the two columns are identical across all 216 rows.

F6. **8 of 12 response columns are identically zero** over all 216 rows:
`parse.doc.ok`, `parse.doc.throughput`, `qa.citation.judge`, `qa.faithfulness.judge`, `qa.numeric.exact`,
`qa.numeric.number_grounding`, `qa.refusal.deterministic`, `qa.refusal.judge`. Only three distinct bits
exist in the matrix: `parse.field.hit_rate` (M), `qa.retrieval.source_required` (R),
`parse.reconcile.equations` (N) — plus the M bit's duplicate (F5).

F7. **The only "downstream causal response" in the smoke is an alias of the source-local bit.**
`smoke/causal_checkpoint_selection_mvp.py:39-43` designates `POTENTIAL_DOWNSTREAM["M"] =
("parse.table.regression",)`. Measured: M rows where that "downstream" bit equals the source-local bit
= **72/72**. Designated downstream leaves for R (`qa.numeric.number_grounding`, `qa.faithfulness.judge`)
and N (`qa.numeric.exact`, `qa.numeric.number_grounding`) have **0 nonzero rows**.
Hence `overlay_counts`: `source_local_positive_rows=216`, `downstream_causal_positive_rows=72`, and the
72 are exactly the M rows.

F8. **The project's own ablation already demonstrates the tautology** (`multileaf_signature_ablation.json`):
`full_vector` (12 leaves) `macro_f1=1.0` = `direct_target_codebook` (3 leaves) `1.0`;
`full_equals_direct_codebook: true`; `non_direct_leaves_only` collapses to `0.3333` with
`tie_rate=0.6667`. Dropping either aliased leaf alone leaves `1.0` (its twin remains). The artifact's
own `interpretation`: *"This confirms Loop C's tautology concern and limits the claim to the
constructed observation surface."* Status `EXPLORATORY_POST_HOC`, `formal_result_changed: false`.

F9. **No mutation operator is implemented for M2, R2 or N2.** `scripts/research/drift_inject.py`
implements only six lexical header-token rewrites (`alias_variant`, `mixed_lang`, `unit_suffix`,
`date_variant`, `ocr_similar`, `prefix_noise`; all header-row only). Multi-form search for
transpos*/swap*/permut*/column*/distract*/promot*/rank*/operator*/coefficient*/perturb*/sign plus
Chinese equivalents returns zero operator hits. The six mechanism IDs (`M1_FIELD_TOKEN_REPLACEMENT` …
`N2_OPERATOR_COEFFICIENT_PERTURBATION`) appear **only** in `METHOD_DESIGN_QUALIFICATION_V1.md:15-20`.
No separate "six-mechanism contract" artifact exists; that input resolves to §Six Mutation Mechanisms
of the design document (search for `six.mechanism|M2_TABLE_TOPOLOGY|R2_DISTRACTOR|N2_OPERATOR_COEFFICIENT`
returns only the design doc and the audit contract).

F10. **RIPR emits booleans, not `NOT_IDENTIFIABLE`.** `build_dev_only_overlay` sets
`REACHED/INFECTED/PROPAGATED/REVEALED` as `int(...)` ∈ {0,1} (`smoke/…mvp.py:291-296`). Only
`raw_state_pre_hash`, `raw_state_post_hash` carry `NOT_IDENTIFIABLE`
(`:307-308`), with `dependency_path_status = "DEV_ONLY_DESIGN_PATH_PRESENT_NO_RAW_STATE_PROOF"`
(`:309`).

F11. **Hard-budget greedy and tie order are correct.** No human cost weights anywhere
(`cost_definition.human_cost_weights: 0`; `marginal_gain` is coverage + stage-F1 + family-F1 only).
`tie_order` (`:589-600`) is exactly
`(model_or_judge_calls, check_count, measured_runtime_ms|inf, checkpoint_id)`, matching the frozen
order. All `measured_runtime_ms` are `None`, so runtime degrades deterministically to fixed checkpoint
ID. `assert_hard_budget` raises on excess; no baseline in either budget exceeds its limits
(verified in the emitted result: `within_hard_budgets: true` for all 12 baseline×budget cells).

F12. **Diagnosability is a fixed nearest-centroid with tie=failure.** `nearest_centroid_predict`
(`:510-539`) fits centroids on train rows, Euclidean (squared — argmin-equivalent) distance,
`TIE_EPSILON=1e-12`, and returns `__TIE_FAILURE__` when >1 centroid is tied; empty selection also
returns `__TIE_FAILURE__`. Macro-F1 computed separately for `stage_label` and `family_label`.
`test_nearest_centroid_tie_counts_as_failure` asserts `macro_f1 == 0.0` on a forced tie.

F13. **MINIMUM rule uses effect size + direction consistency + group uncertainty; no p-value.**
Design lines 113-141: both directions `A->B` / `B->A`; paired group-level effect size
`ours - coverage-only`; direction consistency; group-level bootstrap 95% CI over held-out groups,
10,000 resamples, seed `20261013`, percentile. Positive rule requires both directions non-negative,
≥1 direction improving ≥0.05 absolute, pooled CI lower bound > 0, persistence after removing
source-local-only cases, and both budgets satisfied. No p-value appears anywhere in the rule. Check 8
**verified at design level**.

F14. **Baseline inventory is complete (6/6).** `all-checkpoints`, `random-K` (fixed seed 20261011),
`manual/default stage-aligned`, `coverage-only greedy`, `ours`, `terminal-only` — matches the design
list exactly. `terminal-only` returns `NOT_AVAILABLE` with reason
`NO_COMPARABLE_FINAL_OUTPUT_MONITOR_IN_AUTHORITATIVE_ARTIFACTS`.

F15. **MINIMUM rule is specification-only.** Search `MINIMUM|bootstrap|20261013|A->B|direction` across
the artifact directory hits only `METHOD_DESIGN_QUALIFICATION_V1.md` and the audit contract. No
implementation of the A->B / B->A directions, the 10,000-resample group bootstrap, or the
"result remains after removing source-local-only cases" clause exists.

---

## INFERENCE

I1. **The M-stage pair is not empirically separable.** From F5+F7: M1 and M2 share
`parse.table.regression` / `parse.field.hit_rate` as candidate downstream checkpoints, and those two
are the same measurement. Two mechanisms whose designated oracles are a single aliased bit cannot be
distinguished by observation, so "2 true mechanisms per stage" is unachievable for M while that alias
persists.

I2. **`downstream_causal_coverage` is not a causal quantity on this evidence base.** From F7+F8: for M
it restates source-local response; for R and N it is identically zero. The anti-tautology contract
requires a non-source state change *along at least one recorded dependency edge*; the smoke asserts
this via a static `stage → leaf` map while recording no path (`dependency_path_status` admits
`NO_RAW_STATE_PROOF`). Under the design's own clause — "if the apparent advantage disappears after
removing source-local-only cases, classify `MINIMUM_NO_INCREMENT` or method failure" — the existing
evidence scores as **method failure**, which the project's ablation already records.

I3. **The 12-checkpoint inventory is a tree definition, not an instrumented surface.** From F6: two
thirds of the candidate set has never produced a response. `delta_downstream_causal_coverage` is
therefore non-estimable for R and N on any existing carrier, so the MINIMUM positive rule cannot be
evaluated even in principle on the old matrix.

I4. **Half the mechanisms' "automatic: YES" feasibility is unasserted by evidence.** From F9: M2, R2,
N2 have no executable operator anywhere in the repository. The claim is a design assertion. This is
*expected* for a design-ahead-of-implementation document, but it must not be read as demonstrated
feasibility at materialization time.

I5. **`missing_score` asymmetry collides with the RIPR rule.** In `config/eval_checkpoint_trees.json`
every `parse.*` leaf has `missing_score: 0` and every `qa.*` leaf has `missing_score: 5` (full marks on
the 0-10 scale). If an unidentifiable qa leaf inherits `missing_score=5`, non-identifiability becomes a
perfect score — the opposite of "missing state or missing path is `NOT_IDENTIFIABLE`, never zero".
Combined with F10 (flags are 0/1), the design's non-identifiability discipline is specified but not
enforced anywhere in the stack.

I6. **The terminal-only negative is asserted, not self-proved.** The reason string is hardcoded
(`smoke/…mvp.py:471`) with no recorded search. A plausible counter-instance exists in an authoritative
frozen-design input (`config/eval_checkpoint_trees.json`, listed as Frozen Design Authority in the Loop A
contract): answer-level final-output monitors do exist — `qa.numeric.exact` ("exact_numeric 确定性"),
`qa.numeric.number_grounding` ("答案数值 claim 全部在 top_k 检索 chunk 里落地"),
`qa.faithfulness.judge`. A terminal/answer-level-only subset of the existing 12 is constructible without
inventing anything. Whether that counts as "a comparable final-output monitor" is undefined in the
design. Verdict on check 9: **inventory VERIFIED; the `NOT_AVAILABLE` decision is UNVERIFIED /
contestable** pending an explicit definition of "comparable".

I7. **A latent propagation-over-attribution defect exists but does not fire here.** `PROPAGATED` is set
from the sibling aggregate `downstream_causal` (`smoke/…mvp.py:294`), so if two downstream leaves were
designated and only one responded, the silent leaf would still be flagged `PROPAGATED=1`. Measured on
this matrix: **0 of 2592** flag cells are mis-set — it does not manifest, because M designates exactly
one downstream leaf and R/N's never respond. It would bite at materialization, where multiple
downstream leaves per mechanism are planned.

I8. **The greedy objective uses in-sample diagnosability.** `causal_or_diagnostic_gain` calls
`diagnosability_macro_f1(rows, rows, …)` (`:633-634`) — centroids fit and scored on the same rows.
Selection itself is confined to `train_rows` (no test leakage), and evaluation is properly held-out, so
this is an objective-definition weakness rather than leakage. It does mean the `delta_*_diagnosability`
terms of `marginal_gain` are resubstitution quantities.

---

## UNVERIFIED

U1. **GB10 runtime.** All verification above is LOCAL. GB10 authority remains untested by this audit.
U2. **Any H1 claim.** No scientific claim is made or implied; DEV_ONLY smoke numbers are not H1 evidence.
U3. **Executability of M2 / R2 / N2** and of any `DESIGN_EDGE` (see edge table).
U4. **RIPR `raw_state_*` capture** — never exercised; hashes are `NOT_IDENTIFIABLE` throughout.
U5. **MINIMUM rule behaviour** — unimplemented (F15); its edge cases (a direction with no evaluable
groups; a pooled CI with zero variance) are unknown.
U6. **Whether a "comparable final-output monitor" exists** (I6) — requires a definition decision from
the owner.
U7. **Materialization of the 96-injection dataset** — deliberately not attempted (forbidden).

---

## Mechanism verdicts (checks 1–2)

Distinctness tested against the "template/string/parameter variant" exclusion. Each pair differs in
**mutation locus** and **operator type**, not in template or parameter:

| mechanism | source state | mutation operator | expected causal path | candidate downstream | auto? | downstream owner | verdict |
|---|---|---|---|---|---|---|---|
| `M1_FIELD_TOKEN_REPLACEMENT` | `table[0][col]` | substitute one header token | source token → mapping state → mapping score | `parse.field.hit_rate`, `parse.table.regression` | claimed YES (drift_inject exists) | executor/mapper | **DISTINCT** — lexical substitution on one header cell |
| `M2_TABLE_TOPOLOGY_TRANSPOSITION` | full grid + header order | permute two complete columns | topology → shape/order state → structural score | `parse.table.regression`, `parse.field.hit_rate`, `parse.doc.ok` | claimed YES — **unimplemented** | executor/table validator | **DISTINCT as an operator** (permutation ≠ substitution) — but **not separable in observation** (I1) |
| `R1_REQUIRED_EVIDENCE_DELETION` | `required_evidence_ids` + bundle | delete exactly one required block | bundle → retrieved set → source-required oracle | `qa.retrieval.source_required`, `qa.numeric.number_grounding` | claimed YES (synthetic bundle only) | retrieval/checkpoint executor | **DISTINCT** — set deletion |
| `R2_DISTRACTOR_PROMOTION` | ranked list + top-k membership | promote distractor / swap rank, text unchanged | ranking state → top-k set → source-required oracle | `qa.retrieval.source_required`, `qa.numeric.number_grounding`, `qa.faithfulness.judge` | claimed YES — **unimplemented** | retrieval/checkpoint executor | **DISTINCT** — ordering/selection change with text preserved; not a deletion |
| `N1_OPERAND_VALUE_PERTURBATION` | numeric cell/operand | add fixed nonzero delta, type/format preserved | numeric source → operand state → recomputed relation | `parse.reconcile.equations`, `qa.numeric.exact`, `qa.numeric.number_grounding` | claimed YES | executor/reconciliation | **DISTINCT** — value perturbation |
| `N2_OPERATOR_COEFFICIENT_PERTURBATION` | relation operator/coefficient | replace operator or flip coefficient/sign | relation definition → recomputed identity → reconciliation oracle | `parse.reconcile.equations`, `qa.numeric.exact`, `qa.numeric.number_grounding` | claimed YES — **unimplemented** | executor/reconciliation | **DISTINCT** — relation-semantics change; not a value perturbation |

All six carry all six required contract fields. Cross-stage loci (M/R/N) are disjoint objects.

**Check 1/2 verdict: `MECHANISM_DIVERSITY_PASS`** — the six are genuinely distinct operators, not
template/string/parameter variants. Conditions attached (do not upgrade to unqualified PASS):
(a) M2/R2/N2 operators do not exist yet (F9), so their "automatic: YES" is unproven; (b) the M pair is
not *observably* separable while its designated oracles remain aliased (I1).

## Edge verdicts (check 3)

Classification against source evidence. `EXECUTION_CONFIRMED_EDGE` requires a run that actually
computed the relation — a definition file is not execution evidence.

| edge (design row) | design label | **audit verdict** | basis |
|---|---|---|---|
| source header token → canonical mapping state | EXECUTION_CONFIRMED | **EXECUTION_CONFIRMED_EDGE** *(carrier differs)* | `drift_inject.py:287-416` header-only rewrites; real mapper `src/biz/m1_statement_parser.py:213` `map_headers`; executed in `research/paper_d3_matched_fpr_stage_a.py:474-511` with `rule_eval_map_headers_calls = 7549` in `logs/graph/eval/d3_matched_fpr_stage_a.json`. **Not** exercised by `run_multileaf_formal.py`, which recomputes a trivial token-overlap locally (`:248-258`) and never calls `map_headers`. |
| canonical mapping state → `parse.field.hit_rate` | EXECUTION_CONFIRMED | **EXECUTION_CONFIRMED_EDGE** | `run_multileaf_formal.py:258`; M rows in `multileaf_paired_artifacts.jsonl` respond; `multileaf_formal_results.json` M profile `parse.field.hit_rate: 72` |
| canonical mapping state → `parse.table.regression` ("table regression score") | EXECUTION_CONFIRMED | **EXECUTION_CONFIRMED_EDGE, relation label REFUTED** | Field is written (`:257`) and appears in artifacts, but as a copy of the field-hit predicate (F5). There is no table-shape/structure oracle. The label "table regression score" does not describe what the carrier computes. |
| evidence bundle → retrieved candidate/top-k set | EXECUTION_CONFIRMED (R1-style) | **EXECUTION_CONFIRMED_EDGE, causal content vacuous** | `run_multileaf_formal.py:295-299`: `injected_bundle` is always exactly `["__DISTRACTOR_BLOCK__"]`, so `baseline_pass` is always True and `injected_pass` always False — a set-membership tautology, not an observed retrieval run |
| retrieved top-k set → `qa.retrieval.source_required` | EXECUTION_CONFIRMED | **EXECUTION_CONFIRMED_EDGE — but the cited carrier is DEFINITION_ONLY** | `config/eval_checkpoint_trees.json:83` only *defines* the leaf. Execution evidence lives at `run_multileaf_formal.py:301` + R rows in the paired artifacts. Citation invalid; edge itself holds. |
| table topology → table-shape/header-order state | DESIGN_EDGE | **DESIGN_EDGE** (confirmed) | No M2 operator exists (F9) |
| table-shape state → `parse.table.regression` | DESIGN_EDGE | **DESIGN_EDGE** (confirmed) — and **blocked by aliasing** | Target leaf is aliased (F5), so this edge cannot be confirmed as a distinct structural relation |
| ranked evidence list → retrieved top-k set | DESIGN_EDGE | **DESIGN_EDGE** (confirmed) | No R2 operator exists (F9) |
| numeric operand → identity operand state | EXECUTION_CONFIRMED | **EXECUTION_CONFIRMED_EDGE** | `identity_passes` `:218-229`, `check_n` `:321-325`; freeze samples carry `value_before → value_after`; N rows record `original_identity_pass`/`mutated_identity_fail` |
| identity operand state → `parse.reconcile.equations` | EXECUTION_CONFIRMED | **EXECUTION_CONFIRMED_EDGE** | `:335`; N profile `parse.reconcile.equations: 72` |
| operator/coefficient → identity relation state | DESIGN_EDGE | **DESIGN_EDGE** (confirmed) | No N2 operator exists (F9) |
| identity relation/result state → `qa.numeric.exact` / `qa.numeric.number_grounding` | DESIGN_EDGE | **DESIGN_EDGE** (confirmed) — and **unobservable** | Both leaves are identically zero (F6) |

Summary: 7 design-labelled `EXECUTION_CONFIRMED` → **5 clean**, **1 relation-label refuted** (aliased),
**1 vacuous causal content**, plus **1 citation defect** (definition-only carrier). 5 `DESIGN_EDGE`
labels are correct and honestly marked.

## Anti-tautology verdict (check 4)

**FAIL — source-local / downstream separation is not evidentially grounded.**

- *Source-local responses cannot count as primary causal gain.* The contract states this correctly
  (design lines 47-51). Enforced? No. `source_local_only_coverage` is computed
  (`smoke/…mvp.py:832-846`), but nothing removes those cases before a decision — that clause is
  unimplemented (F15).
- *Downstream causal response requires a recorded dependency path.* **Not satisfied.** `DOWNSTREAM_CAUSAL_RESPONSE`
  is `any(responses[leaf] > 0 for leaf in POTENTIAL_DOWNSTREAM[stage])` over a hardcoded map
  (`:277`), with `dependency_path_status = DEV_ONLY_DESIGN_PATH_PRESENT_NO_RAW_STATE_PROOF`. No
  dependency path and no state hash is recorded.
- *Source-local-only advantage is method failure.* On this evidence base the only "downstream" signal is
  a byte-identical copy of the source-local bit (F5/F7), and removing the source-local coordinates
  collapses performance to chance (F8: `0.3333`, `tie_rate 0.6667`, `full_equals_direct_codebook: true`).
  Under the contract that is **method failure** — already recorded in the project's own ablation
  interpretation.

The design's anti-tautology *wording* is sound. The *measurement* that would enforce it does not exist,
and the one dataset that would exercise it cannot separate the two categories. This is the audit's
principal objection and the source of the single blocker below.

## RIPR / `NOT_IDENTIFIABLE` (check 5)

**Partially verified.** The four fields plus `SOURCE_LOCAL_RESPONSE`, `DOWNSTREAM_CAUSAL_RESPONSE`,
`oracle_response`, `raw_state_pre_hash`, `raw_state_post_hash`, `dependency_path` are specified
(design 55-72). `raw_state_*` correctly read `NOT_IDENTIFIABLE`. But the flags themselves are 0/1
booleans (F10), so "missing state or missing path is `NOT_IDENTIFIABLE`, never zero" is **not enforced**;
and `missing_score` 0-vs-5 asymmetry (I5) would convert an unidentifiable qa leaf into full marks.
`checkpoint_changed` alone is correctly not treated as propagation in the text. Verdict: **contract
correct, enforcement absent** — carry the fix into materialization or RIPR will silently encode
non-identifiability as failure (parse) and as perfection (qa).

## Greedy (check 6) — **VERIFIED**
No human cost weights; hard budgets `B_check`/`B_call` only; `assert_hard_budget` raises on excess;
tie order exactly as frozen (F11). Minor: the greedy objective uses in-sample diagnosability (I8).
Note also `MANUAL_PRIORITY` lists `qa.numeric.number_grounding` twice
(`smoke/…mvp.py:51,53`) — harmless (deduped) but a copy-paste defect.

## Diagnosability (check 7) — **VERIFIED**
Fixed nearest-centroid, Euclidean, centroids fit on design groups only, held-out groups for evaluation,
tie = `__TIE_FAILURE__` = incorrect, macro-F1 for stage and family separately, classifier and tie rule
frozen before results (F12).

## MINIMUM rule (check 8) — **DESIGN VERIFIED / IMPLEMENTATION ABSENT**
Effect size (`>= 0.05` absolute), direction consistency (both `A->B` and `B->A` non-negative), and
group-level bootstrap uncertainty (10,000 resamples, seed `20261013`) — **no p-value anywhere** (F13).
Correct as a decision rule. Unimplemented and untested (F15); also depends on the source-local-removal
clause that does not exist, and on 2-mechanism-per-stage separability that the M pair currently lacks
(I1). Check 8 passes on the specification and is **not** certified as an executable gate.

## Baselines (check 9) — **INVENTORY VERIFIED / terminal-only UNVERIFIED**
6/6 present and correct (F14). `terminal-only` → `NOT_AVAILABLE` is *plausibly* right but the negative is
hardcoded without search evidence and a counter-construction exists in authoritative artifacts (I6).
Recommend the owner define "comparable final-output monitor" explicitly before materialization.

---

## Top three scientific objections

1. **The primary causal metric is currently a restatement of the source-local signal.**
   `parse.table.regression` ≡ `parse.field.hit_rate` (same predicate, `run_multileaf_formal.py:257-258`;
   identical columns over all 216 rows). The smoke's only nonzero downstream response (72 M rows) is that
   duplicate. The project's own ablation shows the advantage vanishes when source-local coordinates are
   removed (`non_direct_leaves_only` = 0.3333) and that `full_equals_direct_codebook: true`. Under the
   frozen anti-tautology contract this is **method failure**, not causal gain. Any H1 claim built on this
   surface would be a tautology of the instrumentation.

2. **Downstream causal response is non-estimable for two of three stages.** 8/12 candidate checkpoints
   are identically zero (F6); every downstream leaf designated for R1/R2/N1/N2 has 0 responding rows (F7).
   The 12-checkpoint inventory is a tree *definition*, not an instrumented surface, so
   `delta_downstream_causal_coverage` — a term in the frozen `marginal_gain` — cannot be estimated for R
   or N on any existing carrier.

3. **Non-identifiability discipline is specified but unenforced, and the defaults are inverted.**
   RIPR flags emit 0/1 rather than `NOT_IDENTIFIABLE` (F10), while `config/eval_checkpoint_trees.json`
   sets `missing_score: 0` for every `parse.*` leaf and `missing_score: 5` for every `qa.*` leaf. A
   non-identifiable qa checkpoint would therefore score perfect marks and a parse one zero — the precise
   opposite of "missing state or missing path is `NOT_IDENTIFIABLE`, never zero". Materializing 96
   injections on these defaults would bake the inversion into the scientific dataset.

## Filed incidents (pattern-named; recommended, not recorded)

| fingerprint | severity | symptom | premise violated |
|---|---|---|---|
| `aliased-checkpoint-pair-labelled-as-distinct-oracles` | HIGH | one predicate written to two leaves, described as "table regression score" vs "mapping score" | mechanism separability + anti-tautology |
| `downstream-response-asserted-by-map-not-dependency-path` | HIGH | downstream classification from a static dict, `NO_RAW_STATE_PROOF` | anti-tautology: downstream requires a recorded path |
| `execution-confirmed-edge-relation-label-not-matching-carrier` | HIGH | edge labelled "table regression score", carrier computes a field-hit copy | edge classification integrity |
| `missing-score-asymmetry-converts-nonidentifiable-to-full-marks` | MED | `qa.*` `missing_score=5` vs `parse.*` `missing_score=0` | `NOT_IDENTIFIABLE` never zero |
| `ripr-flags-emit-boolean-zero-instead-of-not-identifiable` | MED | flags are 0/1 | `NOT_IDENTIFIABLE` never zero |
| `negative-conclusion-asserted-without-search-evidence` | MED | terminal-only reason string hardcoded | audit self-proof of negatives |
| `decision-rule-specified-but-not-implemented` | MED | MINIMUM gate has no code | do not treat spec as validated |
| `execution-confirmed-edge-citation-is-definition-only` | MED | edge 5 cited to a config definition file | first-hand evidence discipline |
| `greedy-objective-uses-in-sample-diagnosability` | LOW | `diagnosability_macro_f1(rows, rows, …)` | objective definition |
| `latent-propagated-flag-over-attribution` | LOW | sibling-aggregate `PROPAGATED`; 0/2592 mis-set here | RIPR semantics (latent) |
| `manual-priority-list-duplicate-entry` | LOW | `qa.numeric.number_grounding` listed twice | data hygiene |

## Single blocker

**BLOCKED.**

> **The `SOURCE_LOCAL_RESPONSE` / `DOWNSTREAM_CAUSAL_RESPONSE` partition — on which both the
> anti-tautology contract and the MINIMUM rule depend — is not well-defined for the M stage**, because
> the designated direct oracle (`parse.field.hit_rate`) and the designated downstream oracle
> (`parse.table.regression`) are the same measurement in the only existing implementation
> (`run_multileaf_formal.py:257-258`; identical columns across all 216 rows).

Concrete consequence: materializing the 96-injection dataset on this definition would produce a dataset
in which "the result remains after removing source-local-only cases" (MINIMUM positive rule, item 4) is
*undefined for M*, and in which M1 vs M2 cannot be distinguished — breaking the two-mechanisms-per-stage
requirement that the `A->B` / `B->A` design rests on.

Repair condition (owner's call, not performed here): de-alias the two M-stage oracles so
`parse.table.regression` is a genuine table-shape/header-order structural oracle independent of
`parse.field.hit_rate`, and define downstream response by a recorded dependency path plus
`raw_state_*` hashes rather than by a stage→leaf map.

## Final readiness decision

| decision | verdict |
|---|---|
| `MECHANISM_DIVERSITY` | **PASS** — six genuinely distinct operators; conditions (a) M2/R2/N2 unimplemented, (b) M-pair not observably separable |
| `METHOD_DATASET_READY` | **BLOCKED** — single blocker above |
| `SANER_MVP` | **CONDITIONAL** — design structure is sound (contracts, hard budgets, tie order, diagnosability, MINIMUM rule all correctly specified); becomes FEASIBLE once the M-stage oracles are de-aliased, downstream response is path-evidenced, RIPR emits `NOT_IDENTIFIABLE`, and M2/R2/N2 operators are implemented |

The audit certifies the **engineering plumbing** of the DEV_ONLY smoke as sound and reproducible
(9/9 local, schema complete, hashes frozen, zero scientific production) and does **not** certify the
design as safe to materialize. One concrete blocker stands between the design and materialization.

*Report authored by Loop C. Advisory only — no repair performed, no artifact modified, no commit.*
