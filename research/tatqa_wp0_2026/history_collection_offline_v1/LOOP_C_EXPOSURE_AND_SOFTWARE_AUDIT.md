# LOOP C EXPOSURE AND SOFTWARE AUDIT — history_collection_offline_v1

> Task id: `history-offline-audit-20261017`
> Role: Loop C independent reviewer. Mode: read-only offline audit.
> Audit window (UTC): 2026-10-17T15:05Z – 2026-10-17T15:20Z.
> **Verdict: `CONDITIONAL`** — see §10.
> AI review is not human semantic gold.

---

## 1. Scope and excluded actions

### In scope

Reviewed package: `research/tatqa_wp0_2026/history_collection_offline_v1/`

Required inputs — all read:

| File | Lines / size | Read |
|---|---|---|
| `EXPOSURE_AND_SPLIT_AUDIT.json` | 97,186 lines | summary blocks + full `cluster_rows` scan |
| `SOURCE_CLUSTERS.json` | 20,168 lines | full edge list + cluster list |
| `OFFLINE_RETURN.md` | 107 lines | full |
| `offline_core.py` | 135 lines | full |
| `source_cluster_builder.py` | 206 lines | full |
| `exposure_classifier.py` | 119 lines | full |
| `collection_chain.py` | 138 lines | full |
| `raw_capture.py` | 80 lines | full |
| `build_exposure_and_split_audit.py` | 182 lines | full |
| `fixtures/synthetic_offline_cases.json` | 86 lines | full |
| `tests/test_offline_v1.py` | 141 lines | full |
| `tests/TEST_RECEIPT.json` | 24 lines | full |

Source and evidence inputs — all read or hashed:

- `data/research/tatqa_raw_2026/tatqa_dataset_train.json` (sha256 `2df6e722…`)
- `data/research/tatqa_raw_2026/tatqa_dataset_dev.json` (sha256 `8da095a8…`)
- `data/research/tatqa_wp0_2026/candidate_items_v2.json` (sha256 `5f61f2a4…`)
- task-root `tq5_source_validation_v1/source_refs/origin_manifest.json`
- task-root `coordinator/pool_inventory.json`
- task-root `coordinator/case_provenance.json`
- task-root `tq4_calibration_v1/panel_v2/natural/SELECTION_LOG.json`
- task-root `tq5_source_validation_v1/panel/SELECTION_LOG.json`

Also present in the package but **outside** the required-input list (read for cross-consistency only): `run_offline_tests.py`, `LOOP_C_AUDIT_PROMPT.md`, `prepare_collection_gate.py`, `SPLIT_PROPOSAL.json`, `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json`.

### Excluded actions (as instructed)

No reviewed file, old WP-2 artifact, frozen material, or raw datum was modified. No commit, no push, no memory write. No model call, endpoint call, judge call, training call, service start, collection, or pilot. No new scientific request. No production/database probe. Cost of this audit: **model 0, endpoint 0, judge 0, training 0, service starts 0.**

One disclosed side effect of the permitted test run: `__pycache__/` directories were created under the package root and `tests/` at 23:14 +0800 by Python byte-compilation. No reviewed file content changed.

---

## 2. Commands and checks run

| # | Check | Result |
|---|---|---|
| C1 | `sha256` of train/dev/candidate vs `FETCH_RECEIPT.sha256` and audit `source_identity` | train + dev match fetch receipt; all three match `EXPOSURE_AND_SPLIT_AUDIT.json.source_identity` |
| C2 | `sha256` of 8 `*.py` + fixture vs `tests/TEST_RECEIPT.json` | 8/8 implementation hashes + fixture hash **match** |
| C3 | Rebuild `build_clusters(train, dev)` and diff vs `SOURCE_CLUSTERS.json` | **byte-identical**: 39 edges, 2,443 clusters, identical membership |
| C4 | Recompute exposure layers from task-root evidence | **exact match** 2,246 / 170 / 42 / 21 |
| C5 | Recompute contract-task total via `task_eligibility` | **exact match** 1,099 |
| C6 | Recompute split buckets from `cluster_rows` | **exact match** 176 / 0 / 164 / 12 / 12 |
| C7 | `python3 -m unittest discover -s tests -p "test_*.py" -v` | **10/10 PASS** (read-only runner; `TEST_RECEIPT.json` not rewritten) |
| C8 | Normalization probe on 18 sign/decimal/digit/punctuation cases | see §5 |
| C9 | `evaluate_expression` / `validate_plan` / `run_offline_episode` failure probe | see §6 |
| C10 | `AtomicRawStore` + `BudgetLedger` state-machine probe | see §6 |
| C11 | Import scan of all package `*.py` | stdlib only — no network/model/db/subprocess |
| C12 | U+2212 / fullwidth scan of 93,612 raw table cells | 73 cells use U+2212 |
| C13 | Code exposure register vs TQ-5 exclusion union | 233 vs 221, see §4 |
| C14 | Package mtime stability re-check at audit end | content files unchanged since 23:05:36 +0800 |

---

## 3. Count verification (audit question 3)

**FACT — all six headline counts reproduce exactly from the recorded inputs and code.**

| Claimed (`OFFLINE_RETURN.md`) | Artifact | Recomputed independently | Status |
|---|---:|---:|---|
| Raw records 2,479 | `source_clusters.raw_records` 2,479 | 2,479 (2,201 train + 278 dev; 2,479 unique uids) | **REPRODUCED** |
| Source-association clusters 2,443 | `source_clusters.clusters` 2,443 | 2,443 | **REPRODUCED** |
| Conservative association edges 39 | `edge_count` 39 | 39 | **REPRODUCED** |
| Eligible clusters (≥2 tasks) 176 | `eligible_clusters_with_ge2_tasks` 176 | 176 | **REPRODUCED** |
| Contract-valid tasks 1,099 | `contract_tasks` 1,099 | 1,099 | **REPRODUCED** |
| Pending future clusters 164 | `pending_program_review_future_clusters` 164 | 164 | **REPRODUCED** |
| History clusters after reservation 12 | `history_clusters_after_future_reservation` 12 | 12 | **REPRODUCED** |

**FACT** — cluster-size histogram from the rebuild: 2,410 singletons + 30 pairs + 3 triples = 2,443 clusters / 2,479 records.

**FACT** — edge-reason counts reproduce exactly and match `EXPOSURE_AND_SPLIT_AUDIT.json.normalization_and_association.edge_reason_counts`: `paragraph_near_duplicate` 25, `paragraph_reuse_table_divergence` 15, `table_near_duplicate` 14, `table_reuse_paragraph_divergence` 8, `exact_table` 9, `joint_near_duplicate` 4 (75 reason instances over 39 edges).

**FACT** — artifact hash chain is self-consistent: `EXPOSURE_AND_SPLIT_AUDIT.json.outputs.source_clusters_sha256` (`ff9415d7…`) equals the on-disk `SOURCE_CLUSTERS.json`; `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` reproduces the same `ff9415d7…` / `640ac4eb…` / `6ef9ee7d…` / `254a0e79…` values.

**INFERENCE (D1)** — the 1,099 figure is *reproducible* but is an **undercount** of the corpus semantics. See finding D1 in §8.

**VALUE** — the split shape (0 immediate future / ≥8 pending future / 12 history) is robust: a minus-tolerant reparse moves 1,099→1,149, 176→177, 164→165 but leaves 0 / 12 unchanged.

---

## 4. Exposure-layer verification (audit questions 1 and 2)

### Q1 — five layers distinguished? **YES.**

**FACT** — `exposure_classifier.py:10-14` defines all five categories; `exposure_classifier.py:16-22` ranks them; `exposure_classifier.py:78-99` assigns by strongest-evidence precedence (`model` > `diagnostic` > `generated` > `structural` > unknown). `classify_cluster` (`exposure_classifier.py:102-119`) takes the max-rank member category and maps it to `future_test_state` with an explicit five-way table including `EXPOSURE_UNKNOWN → EXCLUDE`.

**FACT** — UID-level counts reproduce exactly:

| Layer | Claimed | Recomputed |
|---|---:|---:|
| `STRUCTURAL_SCAN_ONLY` | 2,246 | 2,246 |
| `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` | 170 | 170 |
| `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` | 42 | 42 |
| `MODEL_OR_FEEDBACK_EXPOSURE` | 21 | 21 |
| `EXPOSURE_UNKNOWN` | 0 | 0 |
| sum | 2,479 | 2,479 |

**Note (JSON path `exposure_model.category_counts_by_uid`)**: the JSON omits the `EXPOSURE_UNKNOWN` key entirely rather than recording `"EXPOSURE_UNKNOWN": 0`. The `OFFLINE_RETURN.md:18` table does state 0. Cosmetic, but the artifact is less explicit than the narrative.

### Q2 — TQ-5 exclusion-list membership not treated as model exposure? **YES.**

**FACT** — `build_evidence_sets` (`exposure_classifier.py:31-75`) never reads `tq5_selection["exclusions"]`. The TQ-5 exclusion list is:

```
exclusions.sources = { origin_manifest: 182, pool_inventory: 50,
                       tq_case_provenance: 12, tq4_natural_log: 4 }
exclusions.union_count = 221
```

**FACT** — recomputing that union from the four sources gives **221**, matching `union_count`. It is not used as model-exposure evidence anywhere in the code.

**FACT** — the code's model set is built instead from `tq4_natural["selected"]` (4) ∪ `tq5_selection["selected"]` (12) ∪ five literal UUIDs (`exposure_classifier.py:64-68`), intersected with raw uids = 21.

**FACT** — the five literal UUIDs are each inside the 221 exclusion union and each appears in recorded model-run / result artifacts (`research/positive_repair_20261011/runs/PR-EXP-03-v3/p1_run1.jsonl`, `research/paper_e_layer1_20261015/LAYER1_RESULTS_v1.json`, `research/paper_e_layer1_20261015/v4/V4_RESULTS_v1.json`, `…/v4/V4_HELDOUT_LABELS_FROZEN_v1.json`). Their `MODEL_OR_FEEDBACK_EXPOSURE` label rests on recorded use, not on exclusion-list membership. (See D11 — no provenance comment in code.)

**FACT** — both TQ-4 and TQ-5 selection logs carry freeze notes asserting no model outputs existed at selection time (`"No TQ-4 model outputs exist at freeze time; selection is structural only."` / `"No TQ-5 model outputs exist at freeze time; selection is structural + recomputation gates only."`). The panels were subsequently executed, so their selected uids are correctly treated as model exposure.

**INDEPENDENT FINDING (D4)** — the register the return asks to freeze is 221, but the code's exposure union is **233** (= 221 ∪ the 12 TQ-5 panel-selected uids). `OFFLINE_RETURN.md:91` ("the 221-UID exposure register") would leave 12 model-exposed uids outside the freeze set.

---

## 5. Source-cluster verification (audit questions 4 and 5)

### Q4 — separate edge reasons preserved, conflicts conservatively merged? **YES.**

**FACT** — `association_reasons` (`source_cluster_builder.py:44-97`) appends every applicable reason to a list; nothing is overwritten. 28 of 39 edges carry ≥2 distinct reason kinds (e.g. `exact_table` + `table_near_duplicate` + `table_reuse_paragraph_divergence`).

**FACT** — all 23 conflict edges (`table_reuse_paragraph_divergence` and/or `paragraph_reuse_table_divergence`) resolve to the **same** cluster on both endpoints — 23/23 merged. `build_clusters` (`source_cluster_builder.py:138-154`) takes connected components over any-edge adjacency, so a divergence conflict merges rather than splits. That is the conservative direction for source-association (assume dependence).

**FACT** — no `exact_paragraphs` or `report_id` edge was produced. `report_identity` (`source_cluster_builder.py:39-41`) returns `None` for all 2,479 records — `report_identity_available: false` confirmed by direct scan. `OFFLINE_RETURN.md:27` ("Report identity: unavailable in raw schema; no report-level independence claim is made") is accurate and appropriately limited.

### Q5 — normalization preserves signs / decimals / digits / punctuation, exact-only for empty and short text? **PARTIAL — see D1.**

**FACT** — `normalize_text` (`offline_core.py:22-25`) applies NFKC + whitespace collapse only; no character stripping. Probe results:

| Input | Output | Preserved? |
|---|---|---|
| `-1.25` | `-1.25` | YES |
| `1.25` / `1,234.56` / `1.0.0` | unchanged | YES |
| `(1.25)` / `+2.5` / `12.5%` / `$1,000` | unchanged | YES |
| `a-b` / `x–y` (U+2013) | unchanged | YES |
| `−1.25` (U+2212) | unchanged | YES |
| `– 3.50` | unchanged | YES |
| `－1.25` (U+FF0D) | `-1.25` | CHANGED (compat. fold to ASCII) |
| `１２` / `－１` | `12` / `-1` | CHANGED (compat. fold) |
| `½` / `①` | `1⁄2` / `1` | CHANGED (compat. decomposition) |

**FACT** — punctuation is *effective*, not merely retained: `text_ngrams("a-b") != text_ngrams("a b")`.

**FACT** — exact-only handling is implemented as claimed: empty text → `set()` (`offline_core.py:30-31`), so two empty strings score jaccard `0.0` and never match by similarity; text shorter than the 5-gram size returns the whole normalized string as one token (`offline_core.py:32-33`), so short texts match only when identical (case-folded). Cross-length non-match confirmed: `jaccard(text_ngrams("abcd"), text_ngrams("abcdefgh")) == 0.0`.

**FACT** — `SOURCE_CLUSTERS.json.normalization` records `"signs_and_punctuation": "preserved"`. That is true for the ASCII/BMP forms that dominate the corpus but is an over-statement for NFKC compatibility characters (see table). 0 fullwidth characters exist in the corpus, so no data was affected by this specific over-statement.

**FACT (D1, this is the substantive one)** — `parse_numeric` (`offline_core.py:56-63`) accepts only `r"-?\d+(\.\d+)?"` after NFKC. NFKC **preserves** U+2212, so a U+2212 cell fails the regex and returns `None`. The corpus contains **73** such cells (62 train + 11 dev). `task_eligibility` (`offline_core.py:108-115`) therefore drops those values from `usable_rows`. A U+2212/–/—-tolerant reparse raises the contract-task total **1,099 → 1,149** across **12** records (largest single change: `c83c3a82-fb5e-403b-a73b-d3b1628092ef` 6 → 15). See §8 D1.

### Q6 — thresholds fixed in code, not tuned after results? **YES, with one omission (D7).**

**FACT** — `THRESHOLDS` is a module-level constant (`source_cluster_builder.py:15-22`). `build_clusters` takes no threshold argument and the CLIs expose none, so thresholds cannot be varied from the command line. `SOURCE_CLUSTERS.json.thresholds` equals the code constant and the rebuild matched exactly.

**FACT (D7)** — the `paragraph_reuse_table_divergence` rule uses a bare literal `0.50` at `source_cluster_builder.py:90` instead of a `THRESHOLDS` entry, and `OFFLINE_RETURN.md:32-37` lists only four frozen threshold pairs, omitting the paragraph-reuse/table-divergence rule entirely.

**UNVERIFIED** — whether the values were chosen before or after inspecting results cannot be established from package artifacts. Nothing in the package indicates post-hoc tuning.

---

## 6. Tool-chain and raw-capture verification (audit questions 7, 8, 9)

### Q7 — plan → actual calculator → consume avoids gold correction and preserves tool errors? **MIXED.**

**FACT — no gold correction.** `execute_tool` (`collection_chain.py:53-71`) evaluates the validated expression and returns the value untouched. `consume_answer` (`collection_chain.py:94-118`) only compares `actor_answer.delta_target` to `tool_result.returned_value` and never rewrites either; a mismatch yields `ANSWER_TOOL_MISMATCH`. `independent_reference` (`collection_chain.py:74-91`) recomputes from `task.cells` and `source_to_target_factor`, independently of the plan expression. The test `test_tool_uses_actor_parameters_without_gold_correction` (`tests/test_offline_v1.py:90-99`) pins this.

**FACT — tool errors preserved at `execute_tool` level.** `execute_tool` catches all exceptions and returns `{"status": "TOOL_ERROR", "returned_value": None, "error": <ExceptionType>}`. Verified: `execute_tool({"expression": "1/0"})` → `TOOL_ERROR` / `ZeroDivisionError`. `consume_answer` correctly refuses a non-OK tool result with `NOT_CONSUMABLE`.

**FACT — defect D2: tool errors are NOT preserved at the episode entry point.** `validate_plan` (`collection_chain.py:45`) calls `evaluate_expression(expression)` to pre-validate, and that call is **not** wrapped. The same evaluator then runs in `execute_tool`. Consequences, all reproduced:

| Expression | `validate_plan` | `run_offline_episode` | `execute_tool` alone |
|---|---|---|---|
| `1/0` | raises `ZeroDivisionError` | raises `ZeroDivisionError` | `TOOL_ERROR` |
| `1 +` | raises `SyntaxError` | raises `SyntaxError` | `TOOL_ERROR` |
| `2**3` | raises `ValueError` | raises `ValueError` | `TOOL_ERROR` |

So `run_offline_episode` (`collection_chain.py:121-138`) — the documented chain entry point — raises instead of returning a `tool_result` carrying `TOOL_ERROR`. The error-preservation contract is unreachable through the episode path for every realistic error class. `OFFLINE_RETURN.md:69` lists "plan -> actual calculator -> consume chain" as a qualified software item.

**Minor** — `validate_plan` returns only `plan_status: "VALID"`; there is no `INVALID` status, invalid plans raise. `consume_answer` never checks `actor_answer.delta_source`, and nothing cross-checks `reference` against `tool_result` (the reference is computed and returned but not used in scoring).

**Security note (positive)** — the AST evaluator rejects `**`, `abs()`, `__import__`, conditional expressions and string constants (`ValueError: unsupported_expression_node`); `True` evaluates to `1.0` via the `isinstance(…, int)` path, a harmless edge case.

### Q8 — independent reference checker distinguishes `REFERENCE_RECOMPUTED` from `REFERENCE_UNSCORABLE`? **YES.**

**FACT** — `collection_chain.py:78-82` returns `REFERENCE_UNSCORABLE` with reason `missing_numeric_cells` (non-numeric `late_value`/`early_value`) or `invalid_unit_factor` (factor not numeric, or `<= 0`); `collection_chain.py:83-91` returns `REFERENCE_RECOMPUTED` with `delta_source`, `delta_target`, and both units. All four paths reproduced, including the unit-conversion case (`-4.75 * 0.001 = -0.00475`) asserted at `tests/test_offline_v1.py:105`.

**Minor** — `isinstance(value, (int, float))` at `collection_chain.py:78` admits `bool`; `cells={"late_value": True, "early_value": 1}` returns `REFERENCE_RECOMPUTED` with `delta_source: 0.0`.

### Q9 — raw capture and budget prevent overwrite, preserve crash state, stop at hard caps? **PARTIAL.**

**FACT — what works.** `begin_request` (`raw_capture.py:18-23`) builds `{logical_id}_{uuid4.hex[:12]}` and creates the directory with `exist_ok=False`, so request identity is unique. `persist_response` refuses overwrite of `response.json` (`raw_capture.py:28-29`, `FileExistsError` — verified) and requires `request.json` to exist (`raw_capture.py:30-32`). All writes go through `_write_atomic` (`raw_capture.py:42-46`), a temp-file + `os.replace` pair. `BudgetLedger.reserve` (`raw_capture.py:58-70`) stops at exact hard caps: with `request_cap=1` the second reserve raises `REQUEST_CAP_REACHED`; with `token_cap=10` a reserve of `11` raises `TOKEN_CAP_REACHED` before any counter is incremented; an exact-cap reserve of `10` succeeds. Once stopped, every further reserve raises.

**FACT — defects D8/D9.** Reproduced:

1. `persist_response` after `mark_crash` **succeeds** and writes `COMPLETE` alongside the existing `CRASH` marker — contradictory terminal state (`raw_capture.py:25-34`; `persist_response` never consults `CRASH`).
2. `mark_crash` after `persist_response`/`COMPLETE` **succeeds** (`raw_capture.py:36-40`) — same contradiction in reverse.
3. `COMPLETE` is silently rewriteable: `_write_atomic` uses `os.replace` with no existence guard (`raw_capture.py:43-46`). Overwrite refusal covers **only** `response.json`.
4. `BudgetLedger.reserve(-5)` is accepted and sets `tokens_reserved = -5`, which can be used to walk the token counter below the cap and bypass it (`raw_capture.py:58-70` — no sign/range validation on `estimated_tokens`).

**FACT** — crash state is *recorded* (the `CRASH` marker is never deleted) but does not *freeze* the request. Tests `test_raw_capture_is_unique_atomic_and_overwrite_safe` and `test_budget_stops_at_request_and_token_caps` (`tests/test_offline_v1.py:109-130`) cover the happy paths and the caps, but none of the four defects above is covered.

**INFERENCE** — `BudgetLedger` and `AtomicRawStore` are not wired to each other or to `collection_chain`; there is no integration of budget → capture → chain anywhere in the package. The return's §4 bullets are accurate as *component* claims.

### Q11 — no model / endpoint / judge / training / service / collection / pilot side effects? **YES.**

**FACT** — complete import inventory across all 9 package `*.py` files: `__future__, argparse, ast, collections, hashlib, json, math, operator, os, pathlib, re, sys, tempfile, typing, unittest, unicodedata, uuid`. No `requests`, `urllib`, `http`, `socket`, `subprocess`, model SDK, DB driver, `torch`, or training module. No `os.system`, no `eval`. `run_offline_tests.py` writes only `tests/TEST_RECEIPT.json`. `raw_capture` writes only under its own root. CLIs write only to `--output` / `--output-dir`.

**FACT** — `EXPOSURE_AND_SPLIT_AUDIT.json.cost` records `model_calls / endpoint_calls / judge_calls / training_calls` all 0, consistent with the code.

---

## 7. Test and receipt verification (audit question 10)

**FACT** — I re-ran the suite with a read-only runner (`python3 -m unittest discover -s tests -p "test_*.py" -v`), deliberately **not** `run_offline_tests.py`, which rewrites `tests/TEST_RECEIPT.json`. Result: **`Ran 10 tests … OK`**, 10/10 PASS, 0 failures / 0 errors / 0 skipped. Assertions were not weakened or bypassed for this run.

**FACT** — `tests/TEST_RECEIPT.json` is internally consistent with the tree at audit time: `fixture_sha256` matches `fixtures/synthetic_offline_cases.json`; all 8 `implementation_hashes` match their files. The receipt was regenerated at 23:05:36 +0800, after `prepare_collection_gate.py` was added at 23:05:35, so it covers that file too.

**FACT (D5)** — the receipt hashes the fixture and `ROOT.glob("*.py")` but **not** `tests/test_offline_v1.py` (`run_offline_tests.py:30-34`). The test file hashes to `59f4ac8af31f1cbe8da0bb017b16c571face32bd62b9fb018fde504e13807075` and that value appears nowhere in `TEST_RECEIPT.json`. Assertions could therefore be weakened without invalidating the receipt. The later `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` *does* pin it (`resolved.implementation["tests/test_offline_v1.py"] == 59f4ac8a…`, verified equal to the on-disk hash), so the gap is in the receipt, not in the draft bundle.

**FACT (D6)** — `OFFLINE_RETURN.md:78` claims "GB10 tests: 10/10 PASS." There is exactly **one** test receipt in the repository (`tests/TEST_RECEIPT.json`), it carries no host, platform, or Python-version label, and there is no second receipt. `grep -ri gb10` over the package hits only `OFFLINE_RETURN.md:78` and the audit prompt. **The GB10 leg of the software claim is unsupported by any artifact in the package.** Repository policy (`CLAUDE.md`) requires that GB10 results be authoritative and local results be labelled local; an unlabelled receipt cannot substantiate a GB10 claim. The local 10/10 result is independently confirmed (above); the GB10 result is **UNVERIFIED**.

**VALUE** — the assertions themselves are substantive, not weakened: they pin multi-reason edge retention, conflict-merge behaviour, exposure precedence across all five layers, unit-conversion reference recomputation, overwrite refusal, and both budget caps. The absence of a test-file hash is a receipt-strength gap, not a test-content gap.

---

## 8. Findings and exact locations

Severity: **M** = must close before the package is frozen for collection; **m** = should close; **o** = observation/disclosure.

### D1 — `parse_numeric` rejects the Unicode minus sign, understating contract tasks — **M** (correctness)

- Location: `offline_core.py:56-63` (regex `r"-?\d+(\.\d+)?"`), consumers at `offline_core.py:108-115` and `build_exposure_and_split_audit.py:56-58`.
- **FACT**: `normalize_text` preserves U+2212 (`'−1.25' -> '−1.25'`, verified); `parse_numeric("−1.25")` returns `None`. The two subsystems disagree on minus handling.
- **FACT**: 73 raw table cells contain U+2212 (62 in `tatqa_dataset_train.json`, 11 in `tatqa_dataset_dev.json`); 0 fullwidth cells.
- **FACT**: a minus-tolerant reparse gives contract tasks **1,149** vs claimed **1,099** (Δ +50) across 12 records:
  `4ebf4ce6…` 6→8, `9d5adcb7…` 7→9, `66210694…` 1→6, `ee312f2a…` 10→14, `99a0fe81…` 7→10, `ce8bc5c1…` 9→13, `8cbf706f…` 2→6, `4565ded8…` 4→7, `52d79de5…` 7→9, `32c45a53…` 4→9, `c83c3a82…` 6→15, `65cde743…` 4→11.
- **FACT**: split impact under the same reparse — eligible clusters 176→**177**, pending future 164→**165**, history 12→**12**, immediate future 0→**0**. Newly eligible: `cluster_0970` (1→6 tasks, `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW`).
- **VALUE**: the headline *shape* is robust; the headline *numbers* are not. `OFFLINE_RETURN.md:41` ("Contract-valid tasks: 1,099") and `EXPOSURE_AND_SPLIT_AUDIT.json.source_clusters.contract_tasks` will be frozen into `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` as a figure that mis-describes the corpus.

### D2 — episode chain raises instead of preserving tool errors — **M** (software contract)

- Location: `collection_chain.py:45` (`evaluate_expression(expression)` uncaught inside `validate_plan`), reached from `collection_chain.py:126` (`run_offline_episode`).
- **FACT**: `run_offline_episode` with expression `1/0` raises `ZeroDivisionError`; `1 +` raises `SyntaxError`; `2**3` raises `ValueError`. None returns a `tool_result` with `status: "TOOL_ERROR"`.
- **FACT**: `execute_tool` alone does preserve the error correctly, so the contract exists but is unreachable from the documented entry point.
- **INFERENCE**: any downstream runner that wraps the episode must catch arbitrary exceptions, which is not the contract the package documents.

### D3 — "history clusters" is not computed as a set and equals the excluded clusters — **M** (disclosure)

- Location: `build_exposure_and_split_audit.py:94` (`history_after_future_reservation = max(0, len(eligible_clusters) - len(future_pool))`); narrative `OFFLINE_RETURN.md:49-50`.
- **FACT**: the expression is a *count*, not a set difference; the code never emits a history cluster list.
- **FACT**: the 12 history cluster ids are **exactly** the 12 `excluded_future_clusters` ids — `{cluster_0482, 0548, 0810, 0893, 0943, 1052, 1443, 1737, 1744, 1816, 1978, 2147}`. Composition: 10 `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` + 2 `MODEL_OR_FEEDBACK_EXPOSURE`. `SPLIT_PROPOSAL.json.history` confirms the same 12 with those categories.
- **INFERENCE**: `OFFLINE_RETURN.md:49-50` presents "Excluded future clusters: 12" and "History clusters left after reserving all 164 pending future clusters: 12" as two separate facts; they are the same 12 clusters. The design may well intend history == already-exposed material, but that identity is not stated and the reader is likely to infer two disjoint groups.

### D4 — freeze-set size: 221 vs 233 — **M** (evidence completeness)

- Location: `OFFLINE_RETURN.md:91` ("the 221-UID exposure register") vs `exposure_classifier.py:49-75`.
- **FACT**: the code's exposure union over raw uids is **233** = 221 ∪ the 12 TQ-5 panel-selected uids (`1cccc413…`, `1f358d9f…`, `36395829…`, `3661fba5…`, `7fa11b39…`, `96d14a5f…`, `bd504c68…`, `c13323c3…`, `c66e5d6e…`, `cce45fed…`, `dd5eac5a…`, `fe1ea22e…`). The TQ-5 exclusion union is a strict subset (221 minus code = ∅).
- **INFERENCE**: freezing "the 221-UID exposure register" would leave 12 model-exposed uids outside the frozen register.

### D5 — test receipt does not pin the test file — **m** (assertion integrity)

- Location: `run_offline_tests.py:30-34` (`implementation_hashes` = `ROOT.glob("*.py")` only); `tests/TEST_RECEIPT.json`.
- **FACT**: `tests/test_offline_v1.py` (sha256 `59f4ac8a…`) is absent from the receipt. `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json.resolved.implementation` does pin it.

### D6 — GB10 claim unsupported — **m** (verification evidence)

- Location: `OFFLINE_RETURN.md:78`.
- **FACT**: one receipt only (`tests/TEST_RECEIPT.json`), no host/platform/Python label, no GB10-specific receipt. Local 10/10 independently confirmed by me; GB10 **UNVERIFIED**.

### D7 — one threshold not in the frozen map, and omitted from the return — **m** (threshold hygiene)

- Location: `source_cluster_builder.py:90` (bare `0.50`); `source_cluster_builder.py:15-22` (`THRESHOLDS` lacks a `paragraph_reuse_table_divergence` entry); `OFFLINE_RETURN.md:32-37` (lists 4 threshold pairs, omits the paragraph-reuse/table-divergence rule).
- **FACT**: the rule fires 15 times in the real graph, so it is not inert.

### D8 — raw-capture terminal states are not mutually exclusive — **m** (state machine)

- Location: `raw_capture.py:25-34` (`persist_response` ignores `CRASH`), `raw_capture.py:36-40` (`mark_crash` ignores `COMPLETE`), `raw_capture.py:42-46` (`_write_atomic` has no existence guard).
- **FACT**: `persist_response` after `mark_crash` → both `CRASH` and `COMPLETE` present. `mark_crash` after completion → same. `COMPLETE` silently rewriteable. Overwrite refusal covers `response.json` only.

### D9 — negative `estimated_tokens` bypasses the token cap — **m** (budget)

- Location: `raw_capture.py:58-70`.
- **FACT**: `BudgetLedger(request_cap=3, token_cap=10).reserve(-5)` succeeds with `tokens_reserved = -5`.

### D10 — "clusters" are effectively single records; structural layer contributes no tasks — **o** (interpretation)

- **FACT**: 175 of 176 eligible clusters have `member_count == 1`. Only `cluster_1973` is multi-member (2 records, 3 tasks). `SPLIT_PROPOSAL.json` entries all show `task_eligible_record_count: 1`.
- **FACT**: all 1,099 contract tasks come from non-structural uids — `STRUCTURAL_SCAN_ONLY` contributes **0** tasks and **0** eligible clusters (`TASKS_BY_CATEGORY = {PROGRAM_GENERATED…: 1021, STRUCTURAL_SCAN_ONLY: 0, METHOD_DEVELOPMENT…: 60, MODEL_OR_FEEDBACK…: 18}`).
- **INFERENCE**: `OFFLINE_RETURN.md:14` labels the 2,246 `STRUCTURAL_SCAN_ONLY` uids "eligible for developmental test", which reads as a large usable future pool; in the split sense those uids yield nothing. "12 disjoint history clusters" is effectively "12 TAT-QA records". The return does state "Immediate future-test clusters: 0", so nothing is hidden — but the juxtaposition invites over-reading.
- **VALUE**: also explains why `immediate_future == 0` is definitional rather than empirical — the task-eligible set is exactly the 182-record `origin_manifest` uid set (verified set equality: `eligible == generated == origin_manifest uids`), and every one of those is classified `PROGRAM_GENERATED…` or stronger.

### D11 — five literal UUIDs lack provenance comments — **o** (traceability)

- Location: `exposure_classifier.py:64-68`.
- **FACT**: no comment, no reference to a source artifact. Verified independently that all five are within the TQ-5 exclusion union and appear in recorded model-run/result artifacts, so the classification is conservative and evidenced — just not self-documenting.

### D12 — package assembled during the audit window — **o** (process)

- **FACT**: `OFFLINE_RETURN.md` was written 23:03:11 +0800; `prepare_collection_gate.py`, `SPLIT_PROPOSAL.json`, `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` at 23:05:35; `tests/TEST_RECEIPT.json` regenerated at 23:05:36. Three files therefore post-date the return document and are not mentioned in it. All content files were stable from 23:05:36 to the end of the audit (15:15Z / 23:15 +0800). The artifacts are mutually consistent (hash chain verified), so this is a sequencing observation, not an integrity failure.

---

## 9. Unresolved items

**UNVERIFIED**

1. Whether the association thresholds (`0.95 / 0.90 / 0.85 / 0.75 / 0.95 / 0.50`) were fixed before results were inspected. Not determinable from package artifacts; no evidence of post-hoc tuning was found.
2. The GB10 test run claimed at `OFFLINE_RETURN.md:78`. No receipt, no host label.
3. Whether unrecorded historical model access exists beyond the registered evidence. `OFFLINE_RETURN.md:20` explicitly disclaims this ("it is not a claim that no unrecorded historical access can ever exist") — the disclaimer is appropriate and should be retained.

**OPEN — carried forward, not created here**

4. Independent review of whether program-generated tasks/references entered any designer, actor, feedback, correction, or effect-analysis context (`OFFLINE_RETURN.md:53`). This is the gate on the 164 pending clusters and is correctly left open.
5. Human semantic gold for the task/reference contract. AI review is not human semantic gold.
6. G-M remains `HOLD / NOT_IDENTIFIED` (`OFFLINE_RETURN.md:107`).

**Correctly left NOT_AUTHORIZED**

7. Online collection, pilot, training, service start, source switch, public release — none occurred and none is authorized. `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` self-reports `status: NOT_READY_FOR_COLLECTION` with `loop_c_independent_review: PENDING`, which matches this audit's status.

---

## 10. Verdict and decision handoff to Loop D

### Verdict: **`CONDITIONAL`**

**Bounded offline package is reproducible and free of model, endpoint, judge, training, service, collection and pilot side effects. Specific evidence remains missing, and four correctness/disclosure defects must close before anything is frozen for collection.**

What is solid (accept without further work):

- All six headline counts reproduce exactly from the recorded inputs and code (§3).
- `SOURCE_CLUSTERS.json` is byte-identical on independent rebuild (§3).
- The five exposure layers are genuinely distinguished by evidence strength (§4, Q1 **PASS**).
- TQ-5 exclusion-list membership is **not** treated as model exposure; the TQ-5 exclusion union (221) is never read by the classifier (§4, Q2 **PASS**).
- Source association preserves separate edge reasons (28/39 multi-reason) and conservatively merges all 23 conflict edges (§5, Q4 **PASS**).
- Thresholds are module constants, not CLI-tunable; recorded values match code (§5, Q6 **PASS**).
- `REFERENCE_RECOMPUTED` / `REFERENCE_UNSCORABLE` are correctly distinguished (§6, Q8 **PASS**).
- The chain performs no gold correction (§6, Q7 **PASS** on that half).
- No side effects of any kind (§6, Q11 **PASS**).
- Local 10/10 PASS confirmed by independent read-only run (§7).

Why not `ACCEPTED`:

| ID | Blocks acceptance because |
|---|---|
| **D1** | The contract-task figure 1,099 understates the corpus by 50 tasks (true 1,149) because `parse_numeric` rejects the Unicode minus sign that `normalize_text` preserves. One headline number is wrong even though reproducible. |
| **D2** | `run_offline_episode` raises rather than preserving `TOOL_ERROR`, so the tool-error-preservation half of Q7 fails at the documented entry point. |
| **D3** | The 12 "history" clusters are the same 12 clusters excluded for model/diagnostic exposure; the return presents them as two facts and the code never materialises a history set. |
| **D4** | The freeze set named in the return (221) is smaller than the register the code actually builds (233), leaving 12 model-exposed uids unfrozen. |
| **D6** | The GB10 10/10 claim has no supporting receipt; the single receipt is unlabelled. |

Why not `REJECTED`: no evidence was fabricated, no claim of a scientific result is made (`scientific_status: NOT_A_SCIENTIFIC_RESULT`), the conservative direction is preserved throughout (conflict merges, strongest-evidence exposure precedence, `EXPOSURE_UNKNOWN → EXCLUDE`, `online collection NOT_AUTHORIZED`), and every defect above is repairable without altering TAT-QA semantics. The split decision the package reaches — future eligibility **conditional**, collection **not authorized** — is the correct and conservative one and is robust to D1's numeric correction.

### Required before freezing for collection (Loop D action list)

1. **D1** — either accept U+2212/–/— in `parse_numeric` and re-run `build_exposure_and_split_audit.py`, or document the ASCII-minus-only limitation explicitly and restate the affected counts. Update `OFFLINE_RETURN.md:41-50` and `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` accordingly.
2. **D2** — wrap the validating `evaluate_expression` call in `validate_plan` and return a structured invalid-plan status; add a test asserting `run_offline_episode` yields `TOOL_ERROR` rather than raising.
3. **D3** — state plainly that the 12 history clusters are the 12 model/diagnostic-exposed clusters, and materialise the history set explicitly rather than deriving it by subtraction.
4. **D4** — change the freeze target from 221 to 233 uids, or explain why the 12 TQ-5 panel uids are excluded from the register.
5. **D6** — produce a host-labelled GB10 receipt (host, platform, Python version, test-file hash) or retract the GB10 line and state the software claim as local-only.
6. **D5** — add `tests/test_offline_v1.py` to `run_offline_tests.py`'s hashed set.
7. **D7** — move the `0.50` literal into `THRESHOLDS` and add the paragraph-reuse/table-divergence rule to the return's frozen-threshold list.
8. **D8/D9** — make `CRASH` and `COMPLETE` mutually exclusive, guard `COMPLETE` against rewrite, and reject non-positive `estimated_tokens`; extend the tests to cover these paths.

### Handoff to Loop D

- This report is advisory. It does not authorize collection, and it does not change the `NOT_AUTHORIZED` status.
- Loop D should treat items D1–D4 and D6 as **blocking for the pre-collection freeze**, and D5/D7/D8/D9 as **blocking for the software-qualification claim** ("`SOFTWARE_PASS` for the offline contract only", `OFFLINE_RETURN.md:83`). Until D2 is fixed, that claim overstates what the episode chain delivers.
- The numeric shape required by the architect — 12 history clusters and a potential future set of at least 8 — is satisfied under both the current and the minus-tolerant counts (0 immediate / 164–165 pending / 12 history). If fewer than 8 clusters survive the program-generated-reference review, the architect's fallback (TAT-QA history plus a separately qualified MultiHiertt same-contract future source) should be applied as stated in `OFFLINE_RETURN.md:60`; SEC EDGAR acquisition remains unauthorized.
- Preserve verbatim the wording `developmental evaluation set qualified by scanning and isolated from this history/development material` (`OFFLINE_RETURN.md:58`).
- Old WP-2 trajectories remain prohibited from E/U experience contexts. Old panels and frozen materials remain unchanged.

---

*Produced by the Loop C independent reviewer, task `history-offline-audit-20261017`. Read-only offline audit. AI review is not human semantic gold.*
