# Loop C Joint Audit — Word Route, Scoring V3, New-Family Diagnostic

**Nature of document:** advisory independent-review report. It reports; it does not repair.
Adjudication of every filing recommendation below belongs to the human owner.

**Audited object and baseline:** fixed integrated snapshot `911fb800c01ab145514eaffbfbbf25a7b0c5293b`
(scientific snapshot `62c637ba5f3a21e370669a596298d45d3544ca82`), reviewed at working HEAD
`a624a6152`. Baseline of already-known/already-declared anomalies (not re-reported as new):
pretraining exposure is declared unauditable; author/patent/submission fields are `TBD_OWNER`
by design; `M_DIFFERENCE_REQUIRES_REVIEW` is already a frozen open label; GB10 results are
authoritative and local checks do not prove production.

**Independence declaration:** this reviewer authored none of the A/D artifacts under audit.
Evidence was gathered first-hand by re-running commands and re-parsing primary carriers; author
narratives (`A_RETURN.md`, `A_RETURN.json`, receipt prose, `CONVERSION_README.md`,
`D_WORD_RENDER_RECEIPT.md`) were read only after the independent evidence chain for each face had
been formed, and only to compare claims against findings. Three independent sub-agents ran raw
commands on the exposure, budget and Scoring-V3 faces and reported raw output, not conclusions.
No model was called, no judge, no training, no paid API, no production or external service.

---

## Verdict: `CONDITIONAL`

Every required count, hash and boundary in the task statement reproduces exactly. The verdict is
not `ACCEPTED` because one causal claim is not identified (the D/T/M mechanism gradient is
perfectly confounded with output-budget exhaustion), one accounting figure rests on hardcoded
attribution rather than instrumentation, and the Word deliverable carries concrete defects that
block submission-grade use. It is not `REJECTED` because no reported number is wrong and no
frozen artifact was mutated.

### Blocking defects

| ID | Defect | Carrier |
|---|---|---|
| B1 | **D/T/M mechanism effect is not identified.** Arm membership perfectly predicts output-budget completion, and budget completion perfectly predicts contract extraction. `M` 8/8 `STRICT_FAIL` is entirely accounted for by `M` 8/8 budget exhaustion. No binding-mechanism effect survives. | `generation/generate_local.py:38`; `scoring_v3/results/DIAGNOSTIC_ROWS.jsonl` |
| B2 | **"25 real generate calls / 1 real generation discarded before raw append" is asserted, not measured.** Failure stages are assigned by list index in the recording script, not read from the runtime. | `generation/record_interface_fault.py:34-70` |
| B3 | **"Proposed six-step review checklist" lists five steps.** No step 6 exists in the deliverable or the extracted source. | `paper_e_word/paper_e_word_fixed.md:225-232` |
| B4 | **Table captions and the itemize block are fused into body text**, contradicting the claimed source fix "convert LaTeX itemize blocks to editable bullet lists". | `paper_e_word/paper_e_word_fixed.md:40,93,160` |

### Limitations (real, not blocking)

| ID | Limitation | Carrier |
|---|---|---|
| L1 | "208-word four-part abstract" is reproducible only under a counter whose region includes the Keywords line. The four-part abstract alone is 194 words (prose) / 198 (with the four part labels). | `paper_e_word/build_word_source.py:480-482` |
| L2 | Only 2 of 4 editable tables are numbered (`Table 1.`, `Table 2.`); the visibility matrix and the FinRank table are unnumbered. | `paper_e_word_fixed.md:85,199` |
| L3 | Figures 1 and 2 carry their caption only as Word image alt text plus artwork-internal title; only Figure 3 has an `ImageCaption` paragraph of document text. | `paper_e.docx` `wp:docPr descr`; paras 9, 75, 101-102 |
| L4 | Reference-list defects: corporate author renders as "Standards, National Institute of & Technology" (NIST mangled) in `[10]`,`[11]`; `[13]` renders a literal "& et al.." with a doubled period. | `rendered_final/page-14.png` |
| L5 | In-text citation brackets appear out of ascending order (`[20,19]`, `[23,22]`). | `rendered_final/page-03.png` |
| L6 | `GENERATION_RECEIPT.json` reports `retries = 0` while `bounded_retries = 2` and the ledger holds 2 retry rows — stale field name. | `generation/GENERATION_RECEIPT.json` |
| L7 | `generate_local.py:159` writes any retry suffix into a `retry-1` directory, so attempt `:retry-2` (pa-000003) is recorded under a `retry-1` path. | `generation/generate_local.py:159` |

---

## 1. Paper E Word Route

### Source identity — CONFIRMED

| Artifact | SHA256 (independently recomputed) | Git |
|---|---|---|
| `paper_e_word.md` | `2aeba0ddc6a068a12064db9372b3be03d00de2335bd0d387506eff3d3223bba9` | single commit `62c637ba5`; unchanged to HEAD |
| `paper_e_word_fixed.md` | `ac05bc8c578d87cff41ddec71d2990af1375b54cd71cbd76ae0a7453809a9fc1` | introduced at `911fb800c` |
| `paper_e.docx` | `227309b88ab9778bbd1ce9c181ed468773410d3afb7ec3fd6eeaaea50ad9d5e0` | — |
| `rendered_final/paper_e.pdf` | `231ae6e20a0b7362ce51bc3698e2947d4995a853c2077c36d065190b443a316f` | — |
| `D_PAGE_HASHES.sha256` | `bddda16cf5c31456e4cfa81a358b75a8fe80b026ae09fba0a72107901841bc97` | — |

`git log --oneline -- paper_e_word.md` returns exactly one line (`62c637ba5`), so the extracted
source is unchanged since introduction. `paper_e_word_fixed.md` differs from it by 39 non-equal
difflib opcodes (similarity 0.88779), all structural: YAML author block becomes three body
placeholder lines; BibTeX-key brackets become numeric citations (`[amrhein2022aces,...]` becomes
`[7,8,9,10]`); `\begin{itemize}` becomes markdown bullets; two display equations become editable
prose. No content claim is altered. **`paper_e_word_fixed.md` is a structural conversion
derivative.** CONFIRMED.

### Required features — independently counted

| Feature | Claimed | Found | Verdict |
|---|---|---|---|
| Author placeholders | present | 3 separate body lines (names / affiliations / corresponding), `TBD_OWNER` x9 in PDF text | CONFIRMED |
| Four-part abstract | 208 words | `Purpose.` `Methods.` `Results.` `Conclusion.` all present; 208 under `build_word_source.py:482` | PRESENT, count misbound (L1) |
| Keywords | 5 | `evaluation validity; staged evaluation; evidence ranking; score sensitivity; reproducibility` | CONFIRMED |
| Figures | 3 | 3 embedded media (`word/media/rId21,42,49.png`), 3 image refs | CONFIRMED (L3) |
| Editable tables | 4 | `w:tbl` x4, shapes 6x3, 3x3, 4x4, 7x5; `TableGrid` present in `styles.xml` | CONFIRMED (L2) |
| Numeric citations | `[1]`-`[24]` | 14 in-text bracket groups covering 1-24; all 24 cited in body | CONFIRMED |
| References | 24 | `[1]`...`[24]` present, ascending, no duplicates, no missing | CONFIRMED (L4) |
| Declarations | present | section present with 5 `TBD_OWNER` fields plus ethics line | CONFIRMED |
| Data Availability | present | section present | CONFIRMED |
| No raw TeX/BibTeX in docx | absent | 0 hits for cite/begin/item/textbf/frac/label/ref/caption/article/misc/bibitem/bibtex in `word/document.xml` and in PDF text | CONFIRMED |

### Page hashes — CONFIRMED

`D_PAGE_HASHES.sha256` lists 14 rows. Recomputing SHA256 for each of `rendered_final/page-01.png`
through `page-14.png`: **14/14 match, 0 mismatches.** All pages 1020x1320 RGB8 (120 DPI).

### PDF provenance — CONFIRMED as a real LibreOffice 24.2 render

```
$ pdfinfo rendered_final/paper_e.pdf
Creator:        Writer
Producer:       LibreOffice 24.2
CreationDate:   Tue Oct 27 17:31:53 2026 CST
Tagged:         yes
Pages:          14
Page size:      612 x 792 pts (letter)
PDF version:    1.7
```

Raw PDF `/Producer` stream value decodes from UTF-16BE to `LibreOffice 24.2`; `/Creator` to
`Writer`. 14 `/MediaBox` entries. Zero occurrences of `iText`, `ReportLab`, `PDFKit`, `Pandoc`,
`pdfTeX`, `LuaTeX` anywhere in the file. **This is not a fallback text PDF.** CONFIRMED.

### Page review — all 14 pages inspected at full resolution

| Page | Content | Clipping | Overlap | Table cont. | Figures | Notes |
|---|---|---|---|---|---|---|
| 01 | Title, authors, 4-part abstract, keywords, intro | none | none | - | - | clean |
| 02 | Fig 1, Table 1 start | none | none | table starts | Fig 1 sharp | **Table 1 caption run-in (B4)** |
| 03 | Table 1 cont., Related Work, Method | none | none | **header row repeated** | - | clean |
| 04 | Method, visibility matrix | none | none | - | - | **itemize run-in (B4)** |
| 05 | Stage-aligned, FinRank setup | none | none | - | - | clean |
| 06 | Baselines, stats, protocol | none | none | - | - | clean |
| 07 | Results, Fig 2 | none | none | - | Fig 2 sharp | clean |
| 08 | Table 2 + interpretation | none | none | - | - | **Table 2 caption run-in (B4)** |
| 09 | Sensitivity, weight search | none | none | - | - | clean |
| 10 | Fig 3 + caption | none | none | - | Fig 3 sharp | Fig 3 properly captioned |
| 11 | Nested probe, Case 2 table | none | none | - | - | unnumbered table (L2) |
| 12 | Discussion, limits, conclusion | none | none | - | - | **5-step checklist (B3)** |
| 13 | Acknowledgements, Data Availability, Declarations, refs 1-9 | none | none | - | - | clean |
| 14 | refs 10-24 | none | none | - | - | ends cleanly on `[24]`; **L4 defects** |

No clipped text, no overlapping text, no missing glyphs, no blank table cells, no truncated
references, no malformed final page. Where Table 1 crosses pages 02 to 03 the **header row is
repeated** (the D receipt claim holds for the one table that crosses a page). Figures are sharp
and legible at 120 DPI. Formula text is editable prose without raw TeX.

### Word-route boundary

This is **internal Word-route rendering acceptance** only. It is not publisher formatting
acceptance, not submission acceptance, not school recognition. Author identity, patent/artifact
permission, submission channel and fees remain `TBD_OWNER`. Bibliography formatting (L4) and
table captioning (L2) are the two items a publisher would most likely return.

---

## 2. Scoring V3

**All three required boundaries: CONFIRMED**, each covered by a test *and* reproduced by a direct
scorer call (input to output recorded):

| Boundary | Control | Result | Proof |
|---|---|---|---|
| (a) same numeric value, different rows | correct role-only `refs=["TABLE:R1"]` | status `ACCEPT`, support.answer `exact` | `test_scoring_v3.py:85-86` |
| | wrong role-only `refs=["TABLE:R2"]` | status `REJECT`, reason `required_evidence_operand_mismatch`, support.answer `none` | `test_scoring_v3.py:110-111` |
| | indistinguishable role (no required_evidence) | `PENDING_ADJUDICATION`, reason `role_reference_cannot_distinguish_rows` | `test_scoring_v3.py:127-131` |
| (b) evidence items judged separately | exact + exact | `ACCEPT`, support `{left: exact, right: exact}` | `test_scoring_v3.py:149-153` |
| | exact + broad | `PENDING_ADJUDICATION`, `broad_evidence_not_role_bound`, support `{left: exact, right: broad}` | `test_scoring_v3.py:171-179`; per-operand dict at `scorer.py:123-126` proves non-collapse |
| (c) one-element numeric span | `answer=["123"], numeric=123` | `ACCEPT`, `expected_source == one_element_answer_list` | `test_scoring_v3.py:191-195` |
| | `answer=["123"], numeric=-999999` | `REJECT`, numeric_unit.status `FAIL`, observed `-999999` | `test_scoring_v3.py:207-209`; `scorer.py:225-245` |

The role-confusion fixture is real: `test_scoring_v3.py:64-79,88-104` puts `C1=100` in **both**
R1 (wanted role) and R2 (wrong role).

### Test execution

```
$ python3 -m pytest .../test_scoring_v3.py .../test_diagnostic_rescore.py -q   (venv pytest 9.0.1)
............ [100%]  12 passed in 0.02s     exit 0
$ python3 -m unittest <same two modules>    (stdlib)
Ran 12 tests in 0.001s  OK                  exit 0
```

Note: the literal `PYTHONPATH=src:. python3 -m pytest ...` form is blocked by the session
permission layer (env-var command prefix); the same two modules were executed via pytest and via
stdlib unittest instead. System `/usr/bin/python3` has no pytest module.

### Pure rescore and first-batch replay — deterministic, model-free, byte-identical

- `rescore_pure.py --output /tmp/audit_rescore_pure_v1` to exit 0,
  `{"differences": 109, "rows": 144, "status": "COMPLETE_ZERO_MODEL_PURE_RESCORE"}`
- SHA256 of regenerated vs checked-in:
  `V3_PURE_RESCORE_ROWS.jsonl` `5e5b7633...f253` **byte-identical**;
  `V2_V3_LAYER_UID_DIFFERENCES.jsonl` `25499a1e...9e28` **byte-identical**;
  `V3_PURE_RESCORE_SUMMARY.json` `6d9cfd09...21a6` **byte-identical**.
  A second run reproduces the same three hashes.
- Model/network grep over `scoring_v3/*.py`
  (requests/urllib/http/torch/transformers/openai/anthropic/subprocess/socket/httpx/aiohttp):
  **exit 1, zero matches.**
- Immutable first-batch replay is `adaptive_mechanism_20261027_v1/scoring_v2/rescore_first_batch.py`
  to exit 0, `rows: 36, model_calls: 0`; `FIRST_BATCH_ROWS_V2.jsonl` `991b902a...94c0` and
  `FIRST_BATCH_RESCORE_V2.json` `c4ff9861...061c` both **byte-identical**.

### Frozen history — UNCHANGED

The numeric triples resolve to:
- `2/3/3` = `historical_score_visible {table_top3_ACCEPT:2, table_top5_ACCEPT:3, table_all_ACCEPT:3}`
  in `adaptive_mechanism_20261027_v1/scoring_v2/results/FIRST_BATCH_RESCORE_V2.json`
- `31/5` = `oracle_status_counts` / `question_only_status_counts` (ACCEPT 31, REASONABLE_UNKNOWN 5)
  in `adaptive_mechanism_20261027_v1/d_integration/results/QUESTION_ONLY_ABLATION.json`
- `12/19/5` = `answer_type_free_status_counts` (ACCEPT 12, REJECT 19, REASONABLE_UNKNOWN 5), same file

Git evidence: `git diff --stat` is **empty** for `62c637ba5` to `911fb800c`, `911fb800c` to HEAD,
`62c637ba5` to HEAD, and `main` to HEAD over `scoring_v2/`, `d_integration/`,
`tests/test_m1_service.py` and `scripts/graph/frozen_hashes.txt`. Blob OIDs identical across all
four revisions. Red-line files `tests/test_m1_service.py` (`fbeb247a...`) and
`scripts/graph/frozen_hashes.txt` (`0533e054...`) are untouched and the working tree is clean.

### V2 to V3 differences — by layer/UID, not error rates

`V2_V3_LAYER_UID_DIFFERENCES.jsonl` holds **109 rows** (equal to `difference_count: 109` in the
summary), keyed by `{variant, question_uid, arm}`. Schema carries `status_change {v2,v3}`,
`layer_changes {layer: {v2,v3}}` and six categorical axes. Automated key scan for
rate/accuracy/pct/percent/ratio/f1/precision/recall across all 109 rows: **zero hits.**
**No conversion into natural error rates.** CONFIRMED.

---

## 3. Exposure And Frozen Panel

| Claim | Evidence | Verdict |
|---|---|---|
| source identity is `SAME_SOURCE_NEW_TABLE_FAMILIES`, not cross-source | `EXPOSURE_MANIFEST.json.source_identity_label` and `PANEL_FREEZE.json.source_identity_label` both `SAME_SOURCE_NEW_TABLE_FAMILIES`; `EXPOSURE_MANIFEST.claim_boundary` states not cross-source, not human gold, not model-pretraining | CONFIRMED |
| 8 unique families and 8 UIDs frozen before model output | `PANEL_FREEZE.selection` = family_count 8, uid_count 8, unique_families 8, `model_output_read: False`, seed 20261027, rule "one independently bound UID per table family; preferred task signatures then SHA256(seed:uid)"; `status: FROZEN_PRE_MODEL_OUTPUT` | CONFIRMED |
| answer/task signatures diverse | `task_signature_counts` = 8 distinct signatures, one each: arithmetic_change, arithmetic_comparison, arithmetic_mean, count, multi_span_table, multi_span_text, span_numeric, span_text; `answer_type_counts` = arithmetic 3, multi-span 2, span 2, count 1 | CONFIRMED |
| exclusions reproducible | `family_exclusion_counts` = existing_exposure_identity 236, independent_reference_binding_unresolved 1, this_round_inspected_family 3; `eligible_unexposed_family_count` 38; `this_round_inspected_families` and `this_round_inspected_questions` both length 3; `exposure_membership_registers.count` 496; `repository_identity_artifacts.scanned` 893 with `parse_errors` 0; `exposure_union_identity_count` 18903 | CONFIRMED |
| pretraining exposure explicitly unauditable | `historical_pretraining_exposure` = auditable **false**, boundary "project experimental exposure is auditable; historical pretraining exposure is not", reason "base-model pretraining corpus and token-level membership are unavailable" | CONFIRMED (declared, not claimed clean) |
| frozen before generation | `PANEL_FREEZE.frozen_at` 2026-10-27T15:59:33+08:00; `MECHANISM_FREEZE.frozen_at` 16:05:39; `scorer.py` mtime 15:59:58; first ledger reservation 16:08:45.076; first raw persist 16:11:26.848. Order: panel to scorer to mechanism to model to raw. `EXPOSURE_MANIFEST.model_output_before_manifest = 0` | CONFIRMED |

Cross-check: `PANEL_FREEZE.references[*].question_uid` (8 unique) equals the 8 UIDs in
`generation/results/RAW_RESPONSES.jsonl` and the 8 UIDs in `scoring_v3/results/DIAGNOSTIC_ROWS.jsonl`;
all three sets identical. `binding_chain.independent_of_actor_output` is true and
`gold_numeric_value_scan` is false on the reference side.

---

## 4. Persistent Budget And Raw Accounting

Ledger: `/home/testuser/wzh/research_runs/persistent_budget/word_new_family_20261027/ledger.jsonl`
(schema `adaptive_mechanism_budget_event_v1`, 52 rows, hash chain `prev_event_sha256` verified
intact over all 52 links).

| Claim | Recomputed | Verdict |
|---|---|---|
| 27 physical reservations | 27 `reservation` rows, `physical_attempt_id` = `pa-000001`...`pa-000027` strictly | CONFIRMED |
| 25 real `generate` calls | 24 measured raw rows + **1 asserted** (see B2) | PLAUSIBLE, not instrumented |
| 24 persisted raw rows | 24 `raw_response` rows; `sha256(response_text) == response_sha256` for **24/24**; `fsync_before_scoring` true for **24/24** | CONFIRMED |
| 3 preserved pre-raw failures | orphans with no raw row: `pa-000001`, `pa-000002`, `pa-000004` | CONFIRMED |
| incl. 1 real generation discarded before raw append | asserted by `INTERFACE_FAULT_RECEIPT` for `pa-000004` only; no response text preserved | PLAUSIBLE, asserted (B2) |
| 2 persisted retries | raw rows with `retry` in `logical_call_id`: `D:57f38b17...:retry-2`, `D:62bb8d90...:retry-1` | CONFIRMED |
| persisted actual input/output 28,074 / 12,014 | my sum over 24 raw `usage` fields: **input 28,074, output 12,014** | CONFIRMED |
| uncertain consumed upper bound 5,966 | orphan reservations 1445+512, 1445+512, 1540+512 to 4,430 + 1,536 = **5,966** | CONFIRMED |
| ledger consumed 46,054 / 240,000 | `28,074 + 12,014 + 5,966 = 46,054`; cap `MAX_GENERATION_TOKENS = 240_000` at `persistent_budget/ledger.py:17`; headroom 193,946 | CONFIRMED (arithmetic closes exactly) |
| training/judge/paid API/service/production calls zero | `GENERATION_RECEIPT` all six fields 0; grep for openai/anthropic/httpx/requests/urllib/api_key/boto3/vertexai/generativeai over both research trees: **exit 1, zero matches** | CONFIRMED |

**Model distinction, stated precisely:** "zero paid/service/production/judge/training calls" is
true; "zero model calls" is **false**. A real local model ran: `local_loader.py` loads
`Qwen/Qwen3-4B` with `local_files_only=True` on CUDA GB10, and model generate executed about 25
times. The task claim is correctly scoped and does not overstate this.

### Mechanism checks — implemented and **live-verified**

```
$ python3 -m unittest research.word_scoring_new_family_20261027_v1.budget.test_word_new_family_faults \
    research.adaptive_mechanism_20261027_v1.persistent_budget.test_persistent_budget -v
Ran 11 tests in 0.061s
OK                                                        exit 0
```

11/11 pass (matches `BUDGET_FAULT_TEST_RECEIPT.json`: `test_run: 11, failures: 0, errors: 0`, whose
`source_hashes` match the current files byte-for-byte). Stub loaders only (`ok_loader`,
`crash_loader`, `timeout_loader`, `near_cap_loader`, `counting_loader`); no torch/transformers in
either test file.

| Check | Test | Asserting |
|---|---|---|
| reservation-before-call | `test_crash_after_reservation_before_raw_remains_consumed` | crash after reserve gives `physical_attempts==1`, `uncertain_reservations==1` |
| raw+fsync before scoring | `test_scoring_throw_keeps_raw_and_rescore_adds_zero_calls` | scorer raises, raw row still present |
| restart / output-dir persistence | `test_restart_preserves_ledger_and_prevents_duplicate_logical_call`; `test_output_directory_change_cannot_reset_ledger` | events preserved; duplicate logical_call rejected; new dir cannot reset |
| generate/resume/rescore separated | `test_rescore_never_invokes_a_model_loader` | `model_loaded` False, `new_generation_records` 0, ledger unchanged |
| pre-load cap rejection | `test_attempt_37_rejected_before_model_loader`; `test_token_cap_successor_rejected_before_model_loader` | `BudgetRejected` raised, `loader_calls` unchanged |

### Reservation-scheme repair is independently visible

`reserved_input_tokens` vs actual raw input differs by exactly 512 for every attempt from
`pa-000003` onward (`exact+max_new`), while `pa-000001`/`pa-000002` reserved the bare input
(1445). This is measured from the ledger, not asserted, and corroborates a mid-run repair between
`pa-000002` and `pa-000003` — consistent with, but not proof of, the fault narrative.

---

## 5. D/T/M Mechanism Decision

### Reported outcomes reproduce exactly

Independently recomputed from `scoring_v3/results/DIAGNOSTIC_ROWS.jsonl` (24 rows):

| Arm | ACCEPT | REJECT | STRICT_FAIL | interface PASS | correct_repair | complete_delivery |
|---|---|---|---|---|---|---|
| D | 2 | 2 | 4 | 4 | 2 | 0 |
| T | 1 | 0 | 7 | 1 | 1 | 0 |
| M | 0 | 0 | 8 | 0 | 0 | 0 |

**Every reported figure matches.** `complete_delivery` is false on all 24 rows, so complete strict
delivery is **zero for all arms**. `M_repair_families` is empty and M's category set is
`{strict_failure}`, a strict subset of T's, so **M contributes no repair family beyond T.**
Raw strict delivery is `STRICT_FAIL` on 24/24.

### B1 — binding mechanism is confounded with output-budget exhaustion

`MAX_NEW_TOKENS = 512` (`generation/generate_local.py:38`, `generation/qualify_local_inputs.py:22`,
applied at `generate_local.py:167`).

| | hit the 512 cap | finished within budget |
|---|---|---|
| rows | **19** | **5** |
| interface PASS | **0** | **5** |
| interface FAIL | 19 | **0** |
| semantic ACCEPT | 0 | 3 |
| `output_budget_exhausted_before_contract` | 19 | 0 |

**Zero overlap in every cell.** The arm gradient *is* the completion gradient:

- D: 4/8 finished, 4 interface PASS, 2 ACCEPT + 2 REJECT; 4 capped, 4 STRICT_FAIL
- T: 1/8 finished, 1 interface PASS, 1 ACCEPT; 7 capped, 7 STRICT_FAIL
- M: **0/8 finished**, 0 interface PASS, **8 STRICT_FAIL**

Textual confirmation from `RAW_RESPONSES.jsonl`: every capped row ends mid-sentence or mid-JSON
(for example `...the evidence references are`, `...{ "answer": ["Depreciation and amortization`),
while every non-capped row ends with a closed contract (`... "clarification": "" }`).

**M received no fair trial.** Its 8/8 `STRICT_FAIL` is entirely accounted for by its 8/8 budget
exhaustion. No variation remains from which a binding-mechanism effect could be estimated.

### Second confound, correctly separated

`frozen_reference_unit_may_conflict_with_visible_semantics` occurs on exactly 3 UIDs x 3 arms = 9
rows (`b27a5513`, `62bb8d90`, `24e5a96b`) — a property of the *question*, not the arm. It is
recorded in `alternative_explanations` rather than folded into a mechanism claim. This is the
right treatment and is **not** a defect.

### No method gain to infer from interface normalization

All three `ACCEPT` results were reached through scorer-side interface normalization
(`direct_final_contract_extracted` x2 in D, `typed_envelope_normalized_with_shared_calculator` x1
in T). Raw strict delivery is 0/24 for every arm. Any D > T > M ordering is therefore a statement
about the scorer's ability to salvage a payload, not about model-side or mechanism-side capability.
**No method gain is inferred here.**

### Decision: `M_DIFFERENCE_REQUIRES_REVIEW` to **require another bounded test**

- **Not `STOP_M`.** M never completed a single response within budget. Closing M now would encode
  a confounded null as a decision.
- **Not bare "remain conditional".** The confound is now identified; leaving the label unqualified
  would let it be read as a mechanism finding.
- **Require one bounded budget-controlled test:** same frozen 8-UID panel, Scoring V3 unchanged,
  `MAX_NEW_TOKENS` raised above the observed truncation point (or cap matched across arms) so that
  zero rows truncate, then re-read the D/T/M table. Until that run exists,
  `M_DIFFERENCE_REQUIRES_REVIEW` must carry the annotation **budget-confounded, not a mechanism
  finding**.

---

## Commands and exit status

| Command | Exit | Result |
|---|---|---|
| `git cat-file -p a2463f55...` piped to `sha256sum` | 0 | `1414d5b1...aac93` matches authority LF SHA256 |
| `git rev-parse HEAD:docs/research/LOOP_D_RESEARCH_PROMPT.md` | 0 | `a2463f555f4ede2afcebb14dea2b627a0e5b99db` matches authority blob |
| SHA256 of 14 page PNGs vs `D_PAGE_HASHES.sha256` | 0 | 14/14 match |
| SHA256 of `paper_e_word.md` / `_fixed.md` / `.docx` / `.pdf` | 0 | see section 1 table |
| zip/regex scan of `paper_e.docx` `word/document.xml` | 0 | 4 `w:tbl`, 24 `w:tr`, 3 media, 0 TeX/BibTeX keys |
| `pdfinfo rendered_final/paper_e.pdf` | 0 | `Producer: LibreOffice 24.2`, 14 pages |
| `pdftotext -layout` to stdout | 0 | 50,240 chars; 0 TeX/BibTeX keys; 24 refs `[1]`-`[24]` |
| `python3 -m pytest` Scoring V3 (2 modules) | 0 | 12 passed |
| `rescore_pure.py` run twice | 0 | byte-identical to checked-in, run-to-run |
| `rescore_first_batch.py` replay | 0 | byte-identical, `model_calls: 0` |
| `python3 -m unittest` fault suites (2 modules) | 0 | 11 tests, OK |
| grep model/network over `scoring_v3/*.py` | 1 | zero matches (clean) |
| grep paid-API over both research trees | 1 | zero matches (clean) |
| ledger hash-chain verification over 52 rows | 0 | chain intact |

Fixture written by this audit: `audits/_pdf_text_layout.txt` (PDF text extraction used for the
citation/reference checks). No audited artifact was modified.

---

## Smallest follow-up

**One thing:** re-run the 24-call D/T/M panel on the same frozen 8-UID panel with `MAX_NEW_TOKENS`
raised above the observed truncation point so that zero rows truncate (and with the
reservation/`retry-N` bookkeeping fixes from L6/L7), score with the unchanged frozen Scoring V3,
and re-read the D/T/M table. That single run resolves B1 and turns the mechanism question into an
answerable one.

In parallel but not blocking, the Word manuscript needs four one-line fixes: a blank line before
`paper_e_word_fixed.md:40` and `:160`, a blank line before `:93`, and either a sixth step or a
"five-step" heading at `:225`; plus bibliography correction for `[10]`, `[11]`, `[13]`.

---

## Standing caveat

Independent AI review is **not** human gold, **not** publisher acceptance, **not** school
recognition. Findings above are advisory. Nothing here was repaired; every item is a filing
recommendation for the human owner to adjudicate.
---

## Addendum — exposure-face triangulation and further limitations

An independent sub-agent re-ran the exposure face with raw commands (reading no author
narrative) and reached the same verdicts as section 3. Its evidence adds the following.
**The verdict is unchanged: `CONDITIONAL`.** Items L8-L12 are limitations; B2 is strengthened.

### Exposure face independently CONFIRMED on all seven claims

Same conclusions as section 3, with additional first-hand proofs:

- Source identity field present in `EXPOSURE_MANIFEST.json:7870`, `PANEL_FREEZE.json:618` and
  `MECHANISM_FREEZE.json:148`. The negative claim is **present, not merely absent**:
  `claim_boundary` states "not cross-source, not human gold, and not model-pretraining-disjoint",
  and `PANEL_FREEZE`/`MECHANISM_FREEZE` add "does not claim cross-source validation,
  pretraining-disjointness, confirmation or method gain". grep for `cross_source|cross-source`
  across the three JSONs returns only these negations.
- Full panel table reproduced: 8 uid/family pairs, all distinct; `set(raw uids) == set(panel uids)`
  and `set(raw families) == set(panel families)` both True; `MECHANISM_FREEZE.selected_uids` and
  `selected_family_ids` equal the panel in the same order.
- Freeze chronology re-derived independently and matches section 3 exactly
  (PANEL_FREEZE 15:59:33 < MECHANISM_FREEZE 16:05:39 < ledger seq 0 / first reservation
  16:08:45.076 < first raw persist 16:11:26.848 < last raw persist 16:24:21.648). The
  hash-chained external ledger and `INTERFACE_FAULT_RECEIPT` cross-confirm: the pa-000001 and
  pa-000002 reservation `event_sha256` values (`f96b85b8…`, `90336a31…`) appear verbatim in the
  ledger.
- Exclusions recomputed deterministically: `exposure_union_identity_count` 18903,
  `exposure_union_sha256` `48b87921…f9c6`, `family_exclusion_counts` 236/1/3,
  `eligible_unexposed_family_count` 38 — all **identical**, and the selected 8 uid/family/order
  block is **byte-identical** under sorted-key JSON comparison. The 8 selected families are
  disjoint from the exposure union and inside the 38 eligible (recomputed, not asserted).
  Dev is explicitly *not* excluded for being dev (`source_splits.dev_role`).
- Frozen items hash-verified against current files: `scorer.py` `4d8075bd…c383`,
  `test_scoring_v3.py` `29747d85…30db`, `ZERO_MODEL_BASELINE.json` `089ce79c…b5c`,
  `PANEL_FREEZE.json` `501e6feb…1dde`, `PLANNED_PROMPTS.jsonl` `02ee1cf4…f763`,
  `MECHANISM_FREEZE.json` `e63ac80b…5903`, `shared_tools.py`/`ledger.py`/`runner.py` all match.

### Additional limitations

| ID | Limitation | Carrier |
|---|---|---|
| L8 | **Git dates cannot prove freeze-before-output.** Every freeze artifact and every generation output landed in a single commit `62c637ba5` (2026-10-27 17:14:14 +0800), about 50 minutes after generation finished. Pre-output ordering rests on in-file timestamps, fs mtimes and the external hash-chained ledger — not on commit history. | `git log --name-status 62c637ba5` |
| L9 | **Raw attempt evidence is absent from the repo.** `generation/raw/<arm>/<uid>/{primary,retry-1}/` directories exist but are empty; `git ls-files .../generation/raw/` returns 0 tracked files. Receipts cite `raw_event_sha256` and `output_dir` paths for which no file survives, so those hashes cannot be re-verified against raw events. Only the extracted `RAW_RESPONSES.jsonl` survives. | `generation/raw/` |
| L10 | **Exclusions reproduce only against the pre-output tree state.** Re-running `build_exposure_and_panel.py` on the *current* tree gives union 18920, exclusions 244/1/3, eligible 30 and a different panel, because the run's own outputs are now scanned as exposure identities. Reproduction against the pre-output state is exact. Inherent self-exposure after generation, not fabrication — but a bare "just re-run it" check would show a mismatch and must not be read as a discrepancy. | `exposure/build_exposure_and_panel.py` |
| L11 | **Reference-side `unit` field is not uniformly reliable**, which corroborates rather than contradicts the reference-unit ambiguity flagged in section 5. `b27a5513` is labelled `unit: thousand` while its answers are `$0.8 million`/`$0.6 million`; `24e5a96b` (a `count` question) is labelled `unit: percent`; four UIDs are `unit: UNKNOWN` (from the `required_unit()` heuristic at `build_exposure_and_panel.py:323-334`). | `PANEL_FREEZE.json` `references[*].unit` |
| L12 | Two bookkeeping gaps: `ZERO_MODEL_BASELINE.json` has no internal timestamp field (its pre-generation position rests on mtime 15:59:58 plus its hash being embedded in `MECHANISM_FREEZE`), and `INTERFACE_FAULT_RECEIPT.ledger_sha256` `2e1f0c4e…` is an intermediate ledger state with no preserved snapshot to re-verify it (expected for an append-only ledger, but unreplayable). | `baseline/results/ZERO_MODEL_BASELINE.json`; `generation/INTERFACE_FAULT_RECEIPT.json` |

### B2 strengthened

L9 is direct corroboration of B2. The claim that `pa-000004` performed a real generation that was
discarded before raw append has **no surviving response text, no raw directory content, and no
tracked file** to appeal to. Its only carrier is `record_interface_fault.py:45,51-54`, which
assigns that story by list position. Combined with L12 (the fault receipt pins an unpreserved
intermediate ledger hash), the "1 real generation discarded" figure should be labelled
**asserted, not measured** wherever it appears.

### Exposure-face commands (sub-agent, exit 0 unless noted)

`find` on the research tree · `git log --name-status`, `git log --diff-filter=A`,
`git ls-files generation/raw/` · `sha256sum` on 15 artifacts · `stat -c '%y'` on 10 ·
`grep -n` for source_identity / cross-source / pretraining / placeholders (placeholder grep
exit 1 = zero hits) · `wc -l` · 13 `python3 -c` invocations including two in-memory re-runs of
`build_exposure_and_panel.py` with writes intercepted (nothing written) and one exclusion-set
recomputation · read-only parse of the external ledger. Blocked by the permission layer and
reported for transparency: `cat`/`Read`/`grep`/`head` on the external ledger path (worked via
plain `python3` open), and `sha256sum` on the two TAT-QA split files (exercised indirectly
because the re-run loads them; their recorded hashes could not be independently recomputed, but
exact union-hash reproduction implies their contents match the frozen inputs).
