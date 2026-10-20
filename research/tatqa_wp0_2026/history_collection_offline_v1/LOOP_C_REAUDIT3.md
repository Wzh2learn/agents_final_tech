# Loop C final focused re-audit — N1/N2 closure

**Verdict: `ACCEPTED`**

**Task id:** `history-offline-audit-20261017-r3` · **Role:** Loop C independent reviewer · **Date:** 2026-10-18
**Mode:** read-only focused re-audit of the two residual findings from `LOOP_C_REAUDIT.md` (N-1, N-2)

No files were modified. No model, endpoint, judge, or training call was made. No data was collected and no online collection was authorized. **AI review is not human semantic gold.**

`ACCEPTED` is scoped narrowly: **N-1 and N-2 are closed** and the offline package is reproducible, hash-consistent, and honestly self-labelled. It does **not** mean scientific readiness (`scientific_status: NOT_A_SCIENTIFIC_RESULT`; human semantic gold not provided) and does **not** mean online readiness (collection, pilot, training, source switching, public release remain `NOT_AUTHORIZED`). Future-task qualification remains `CONDITIONAL`.

---

## 2. N-2 — accounting sign convention — **CLOSED**

**Location:** `offline_core.py:56-66`. The repair is the one the finding asked for: parenthesis-negation now applies **only when the stripped inner text is unsigned** (`if negative_parentheses and number > 0`). A minus already inside the parentheses is left alone.

### 2.1 Scope cases — all correct

| Input | Result | Status |
|---|---|---|
| `parse_numeric("−1.25")` | `-1.25` | **OK** |
| `parse_numeric("–1.25")` | `-1.25` | **OK** |
| `parse_numeric("—1.25")` | `-1.25` | **OK** |
| `parse_numeric("(−1.25)")` | `-1.25` | **OK** |
| `parse_numeric("(-1.25)")` | `-1.25` | **OK** |
| `parse_numeric("(1.25)")` | `-1.25` | **OK** |

Parenthesis and minus both mark negativity and do **not** cancel.

### 2.2 Placeholder-only dash forms remain `None`

Verified by execution over `−`, `–`, `—`, `-`, `－`, `(—)`, `(–)`, `(−)`, `(-)`, `(－)`, `—.`, `− `, `(-) `, `( )`, `()` — **all `None`**. Unbalanced forms (`(−1.25`, `−1.25)`) also `None`. `—1` correctly returns `-1.0` (a signed number, not a placeholder). `re.fullmatch(r"-?\d+(\.\d+)?")` rejects every dash-only residue.

### 2.3 No `(−N)` double-inversion remains

Corpus sweep over the pinned raw train+dev (2,479 records, 93,612 table cells): **3,542** accounting-parenthesis cells; **zero** parse to `None` or to a positive value. The 14 inner-sign cells named in N-2 are present with exactly the stated multiplicity and all parse to correct negative values:

| Cell | Count | `parse_numeric` | | Cell | Count | `parse_numeric` |
|---|---|---|---|---|---|---|
| `(−21)` | 4 | `-21.0` | | `(−51)` | 1 | `-51.0` |
| `(−6)` | 2 | `-6.0` | | `(−49)` | 1 | `-49.0` |
| `(−0.06)` | 1 | `-0.06` | | `(−16)` | 1 | `-16.0` |
| `(−1.46)` | 1 | `-1.46` | | `(−15)` | 1 | `-15.0` |
| | | | | `(−79)` | 1 | `-79.0` |
| | | | | `(−69)` | 1 | `-69.0` |

Full 14-cell set from N-2. **No sign error remains in `usable_rows[].value`**, so the input a future gold reference would use for `delta_source = late_value − early_value` is sound. The other 3,528 parenthesised cells carry no inner sign and are correctly negated to `-N`.

### 2.4 Tests cover the corrected behavior

`tests/test_offline_v1.py:30-38` asserts all six scope forms plus `(—) → None`. Independent run on this host: **11 tests, 11 passed, 0 failures, 0 errors, 0 skipped.**

### 2.5 Counts unaffected, as predicted

Headline numbers unchanged by the fix: **1,149 contract tasks / 177 eligible clusters / 0 immediate / 165 pending-program-review / 12 history**, `future_status: CONDITIONAL_PASS_PENDING_PROGRAM_REVIEW`. Value-level fix, not count-level — exactly as the finding predicted.

**N-2: CLOSED.**

---

## 3. N-1 — provenance citations — **CLOSED**

**Location:** `exposure_classifier.py:24-48`, surfaced at `EXPOSURE_AND_SPLIT_AUDIT.json → exposure_model.model_exposure_provenance` (embedded by `build_exposure_and_split_audit.py:150`).

The single misleading comment is replaced by a four-group map separating three genuinely different exposure mechanisms. Each group traced to first-hand evidence.

### 3.1 The four groups are accurately distinguished

| Group | UIDs | Link mechanism | Verified |
|---|---|---|---|
| `tq4_natural_selected` | 4 (N1–N4) | tasks selected by uid, used in TQ-4 run | **OK** |
| `tq5_selected` | 12 (T01–T12) | tasks selected by uid, used in TQ-5 run | **OK** |
| `tq4_candidate_source_mapping` | 3 (Q02/Q03/Q04) | **deterministic content mapping only** | **OK** |
| `wp2_prompt_exposure` | 2 | **WP2 opaque-ID prompt exposure** | **OK** |

**TQ-4 selected.** `panel_v2/natural/SELECTION_LOG.json:selected[].uid` → N1–N4 (UIDs `195174fe…`, `5fe2c49e…`, `9bce514f…`, `70cf5260…`). The claim *"selected TQ-4 **tasks** subsequently appeared in TQ-4 model run artifacts"* holds: `runs/20261016T082849Z_430d927a/prompts/` contains `0001_actor_N1.json` … `0012_b_N4.json`; `part1_results.json` carries N1–N4.

**TQ-5 selected.** `tq5_source_validation_v1/panel/SELECTION_LOG.json:selected[].uid` → T01–T12. Run `20261017T072340Z_5d8942bd` (`reviews/TQ5_RESULTS_CORRECTED_v1.json`) records `panel: "TQ-5"`, `part1.planned: 12`, rows T01–T12. Citation resolves.

### 3.2 No claim of raw-UID appearance in TQ-4 artifacts

**This is the requirement N-1 turned on, and it is met.** The map states: *"candidate inputs Q02-Q04 entered TQ-4 B/C prompts; **raw source UIDs were recovered by deterministic content mapping**."*

Confirmed first-hand: the three register UIDs are **absent from the entire `tq4_calibration_v1/**` tree** (recursive grep, no matches), absent from the TQ-4 **prompts** (`329e3ff5`, `195174fe`, `70cf5260` all absent from the `prompts/` blob), and absent from the candidate inputs `panel_v2/candidates/inputs/Q0{2,3,4}.json`. The map claims content mapping where only content mapping exists, and *task* exposure (not UID exposure) where tasks were used. The prior comment's error is not repeated anywhere.

### 3.3 The content mapping is real, deterministic, and stronger than claimed

`coordinator/case_provenance.json` binds each case to its raw table UID with a full injection record. Comparing each TQ-4 candidate input against the pinned raw record:

| Case | UID | Raw source | Table match | Paragraphs |
|---|---|---|---|---|
| Q02 | `329e3ff5…` | dev:165 | identical except injected cell (0,2) `Segment Assets` → `资产(assets)` | 2/2 uids equal, 0 text diffs |
| Q03 | `d2bba753…` | train:290 | identical except injected cell (0,0) `Capital stock` → `capitai stock` | 4/4 uids equal, 0 text diffs |
| Q04 | `44c7c9ef…` | dev:193 | identical except injected cell (0,1) `Operating Leases` → `operat1ng Leases` | 2/2 uids equal, 0 text diffs |

The candidate inputs reach the model as claimed: `prompts/` contains `0013_b_Q02-C1.json` … `0020_c_Q02-C4.json`; `part2_results.json` carries Q02–Q04. The per-case descriptors (*exact table/paragraph*, *unique near*, *exact paragraph*) are consistent with this; where "near" is used it is the more cautious label, not an overstatement.

**Stronger than the repair required:** raw **paragraph** UIDs are preserved in the TQ-4 candidate inputs (e.g. `6718b37b-c1dc-41b5-8f21-5cfba7daf4ca` inside `inputs/Q02.json`) — a second deterministic join key alongside content matching. Table UIDs remain absent, so the map's statement is still the accurate one.

### 3.4 WP2 opaque-ID exposure — pairing verified by recomputation

The map names, per UID, the opaque origin used in the prompts: `3ab739eb-…` → `origin_fbb782143f9a`; `97176853-…` → `origin_5c4e334806b6`. These pairings are **not assertions** — they are reproducible. `run_wp2_episode_collection_v2.py:134-138` derives refs as `sha256("tatqa-wp2-opaque-v2:origin:<origin_id>")[:12]`. Recomputing:

```
opaque_id("origin", "tatqa_3ab739eb-c0d7-44f5-9377-b8a02bafb361") == origin_fbb782143f9a   MATCH
opaque_id("origin", "tatqa_97176853-a81e-422a-a8c1-e0542348d051") == origin_5c4e334806b6   MATCH
```

A reverse sweep across all 182 origins in `source_refs/origin_manifest.json` returns **exactly these two** — no collision, no ambiguity. The two raw UIDs are still absent from all S4B artifacts (as N-1 found), but the opaque refs are present there in `S4B_BRIDGE_PROTOCOL_RECEIPT.json` and `S4B_BRIDGE_PROBE_RECEIPT.json`, alongside `history_item_ref` and recorded `prompt_full`. **The re-tracer's dead end is gone**: UID → deterministic opaque-id derivation → S4B receipt with the actual prompt.

### 3.5 Provenance map is in the audit JSON

Present at `exposure_model.model_exposure_provenance`, populated directly from the module constant by `build_exposure_and_split_audit.py:150`. Not comment-only.

**N-1: CLOSED.**

---

## 4. Final package consistency

### 4.1 Receipts pin implementation and test hashes

| Receipt | tests_run | fail/err/skip | status | Host |
|---|---|---|---|---|
| `TEST_RECEIPT.json` | 11 | 0/0/0 | **PASS** | `LOCAL_WINDOWS`, Windows-10-10.0.19045-SP0, Python 3.9.10 |
| `TEST_RECEIPT_GB10.json` | 11 | 0/0/0 | **PASS** | `GB10`, Linux-6.17.0-1018-nvidia-aarch64-with-glibc2.39, Python 3.12.3 |

Each pins 8 implementation hashes + 1 test hash + fixture sha256. **20/20 links match on-disk.** The two receipts agree on `fixture_sha256`, `implementation_hashes`, `test_hashes`, `tests_run`, `failures`, `errors`, `skipped`, `status`; only host/platform/interpreter differ.

The GB10 leg is authoritative and this host **is** that machine — `platform.platform()` and `sys.version` match the receipt fields byte-identically, and the 11/11 run is first-hand corroboration. The Windows/3.9.10 deviation (carried N-6) sits only on the non-authoritative leg, is correctly labelled local, and is not corroborated here.

### 4.2 Hash chain mutually consistent

`PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` → disk, every link **MATCH**: `exposure_audit_sha256 29a793ca…`, `source_clusters_sha256 12bb9d0f…`, `split_proposal_sha256 ae13dc0a…`, `local_test_receipt_sha256 49d067ff…`, `gb10_test_receipt_sha256 23448822…`, and `implementation` **10/10** (8 `.py`, fixture, `tests/test_offline_v1.py`).

Cross-file: `EXPOSURE_AND_SPLIT_AUDIT.json.outputs.source_clusters_sha256` equals on-disk `SOURCE_CLUSTERS.json`. Exposure register is 233 UIDs, sorted and unique, canonical hash recomputes to `d6c37842…` as pinned. **End-of-audit re-check: no drift.**

### 4.3 Split shape

8 future / 2 development / 12 history / 155 reserve = **177**, seed `history-collection-offline-v1-split-20261017`, rule `sha256(seed:scope:cluster_id) ascending`. Independently verified **all four buckets pairwise disjoint** (177 rows, 177 unique ids, zero cross-bucket duplicates); every id is a real cluster. Supersedes carried N-5: the built-in self-check covers three buckets, but the invariant holds across all four.

### 4.4 Fixes recorded, readiness not overstated

`status: "NOT_READY_FOR_COLLECTION"` — **unchanged, correct**. Records `parse_numeric_accounting_sign_convention: RESOLVED_NEGATIVE_PARENS_NOT_DOUBLE_INVERTED` (N-2) and `provenance_comment_citations: RESOLVED_MODEL_EXPOSURE_PROVENANCE_MAP` (N-1). `loop_c_independent_review: "R2_CONDITIONAL_D1_D9_CLOSED; R3_N1_N2_PENDING"` was accurate at writing time; this report is the R3 result. `task_and_reference_manifest: NOT_MATERIALIZED` correctly still gated.

### 4.5 Authorization state unchanged

`beijing_window: NOT_AUTHORIZED`; `online_collection_runner_and_prompt_templates: NOT_IMPLEMENTED_OR_NOT_BOUND`; `tokenizer_chat_template_service_binary_generation_parameters: NOT_BOUND`; `judge_calls: 0`; `training_calls: 0`. `OFFLINE_RETURN.md:115` records that no online probe, collection, pilot, training, memory write-back, source switch, or public release occurred. Budget controls (`collection_request_cap: 54`, `collection_token_cap: 600000`, `retry_cap: 0`, `concurrency: 1`) match the "one new collection only, no bundled pilot" rule. Cost counters 0/0/0/0. **Model 0, endpoint 0, judge 0, training 0, service 0, collection 0, pilot 0.**

---

## 5. New discrepancies

**None blocking.** Two non-blocking observations:

**O-1 — placeholder-dash test coverage is a single case** *(cosmetic)*. `tests/test_offline_v1.py:38` asserts only `(—) → None`. The other dash-only forms return `None` under execution (§2.2) but are not asserted. Low risk — `fullmatch` rejects them structurally. Worth one extra assertion if the file is ever reopened.

**O-2 — `wp2_prompt_exposure.use_evidence` phrasing** *(disclosure)*. Reads *"WP2 S4B prompt/bridge receipts and candidate_items_v2 opaque-id replay."* Substance is correct and verified (§3.4), and per-UID fields name the opaque origins so no dead end remains. But the sentence does not say outright that raw UIDs are **absent** from S4B artifacts and appear only via opaque refs, and "candidate_items_v2 opaque-id replay" names a file rather than the derivation that establishes the link (`run_wp2_episode_collection_v2.py:134-138`). Suggest — not require — an explicit qualifier.

Carried, unchanged, outside this scope: N-3, N-4, N-5, N-6, N-7.

---

## 6. Is the owner-facing collection request ready for review?

**Yes.** The two items `LOOP_C_REAUDIT.md` asked to add before the package is complete are now **closed rather than merely listed**:

1. **N-2** is fixed, not just recorded — the sign convention is settled, so the reason the task/reference manifest was gated has been removed at the parser level. The manifest correctly remains `NOT_MATERIALIZED` for its other open reasons; materializing it is a separate decision not made here.
2. **N-1** is corrected, not flagged — the provenance map cites artifact families where the evidence actually lives, and every citation in it resolves under independent tracing.

What the owner is reviewing, stated so it cannot be over-read: a **reproducible, hash-verified offline package** (four generated artifacts and two test receipts mutually consistent) that self-reports `NOT_READY_FOR_COLLECTION`; a **deterministic, disjoint split** 8/2/12/155 reproducible from a named seed; a **233-UID non-structural exposure register** with canonical hash and a provenance map separating TQ-4/TQ-5 selected tasks, Q02–Q04 content mapping, and WP2 opaque-ID exposure.

What the owner is **not** being asked to accept, and what this report does **not** establish:

- **Not a scientific result.** Human semantic gold is not provided and is not provided here. **This review is not human semantic gold.**
- **Not online readiness.** Online collection, pilot, training, service start, source switch, and public release remain **`NOT_AUTHORIZED`**. This report is advisory and does not authorize collection.
- **Not future-task qualification.** Remains **`CONDITIONAL`** — the 165 pending clusters are gated on independent review of whether program-generated tasks/references entered any designer, actor, feedback, correction, or effect-analysis context (`OFFLINE_RETURN.md:56`). Not mine to close. If fewer than 8 survive, apply the fallback at `OFFLINE_RETURN.md:62`; **SEC EDGAR acquisition remains unauthorized.**
- **Not pipeline qualification.** `SOFTWARE_PASS` for the offline deterministic contract stands; `BudgetLedger` and `AtomicRawStore` remain unintegrated with `collection_chain`, so §4 bullets are component claims, not a wired pipeline. G-M remains `HOLD / NOT_IDENTIFIED`.

---

## 7. Handoff

- This report is **advisory**. It does not authorize collection and does not change `NOT_AUTHORIZED`.
- Treat **N-1 and N-2 as closed**; they may be removed from the unresolved list. Everything carried in `LOOP_C_REAUDIT.md` §12 that is *not* N-1/N-2 remains open and unchanged: association-threshold timing undeterminable; program-generated-reference review open; human semantic gold absent; unrecorded historical model access not excluded (retain disclaimer at `OFFLINE_RETURN.md:20`); G-M `HOLD / NOT_IDENTIFIED`; budget → capture → chain not integrated.
- `SOFTWARE_PASS for the offline contract only` (`OFFLINE_RETURN.md:86`) continues to stand and is not extended by this pass.
- **Preserve verbatim** `developmental evaluation set qualified by scanning and isolated from this history/development material` (`OFFLINE_RETURN.md:60`).
- Old WP-2 trajectories remain prohibited from E/U experience contexts. Old panels and frozen materials unchanged. `LOOP_C_EXPOSURE_AND_SOFTWARE_AUDIT.md` and `LOOP_C_REAUDIT.md` are preserved and must not be edited.
- Loop D may proceed to owner review of the collection request preparation with N-1 and N-2 closed.
