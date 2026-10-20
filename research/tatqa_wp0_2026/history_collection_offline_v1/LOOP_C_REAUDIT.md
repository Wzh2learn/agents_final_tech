# LOOP C RE-AUDIT — history_collection_offline_v1

> Task id: `history-offline-audit-20261017-r2`
> Role: Loop C independent reviewer. Mode: read-only focused re-audit of D1–D12 repairs and the collection gate.
> Scope: re-audit only. Independent software/qualification review, **not** human semantic gold.
> **Verdict: `CONDITIONAL`** — see §7.
> **Write access to `LOOP_C_REAUDIT.md` was denied; this is the full report for Loop D to transcribe.**

---

## 1. Anchor and scope

Prior report `LOOP_C_EXPOSURE_AND_SOFTWARE_AUDIT.md` (task `history-offline-audit-20261017`) returned **`CONDITIONAL`** with D1–D4 and D6 as must-close, D5/D7/D8/D9 as software-qualification blockers, D10–D12 as observations. Preserved unchanged; used as baseline.

Required inputs re-read (current versions): `EXPOSURE_AND_SPLIT_AUDIT.json` (98,157 lines), `SOURCE_CLUSTERS.json` (20,169), `SPLIT_PROPOSAL.json` (1,616), `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` (52), `OFFLINE_RETURN.md` (110), `tests/TEST_RECEIPT.json` (31), `tests/TEST_RECEIPT_GB10.json` (31), all eight `*.py` files, `tests/test_offline_v1.py` (163).

### Excluded actions

No reviewed file, old WP-2 artifact, frozen material, or raw datum was modified. No commit, no push, no memory write. No model/endpoint/judge/training call, service start, collection, or pilot.

**Cost of this re-audit: model 0, endpoint 0, judge 0, training 0, service starts 0, collection 0, pilot 0.** Read-only health probes: **0**.

Disclosed side effect: Python byte-compilation may refresh `__pycache__/`. No reviewed file content changed — verified by re-checking every bundle hash at audit end (§6.1).

---

## 2. Prior finding-by-finding closure

| ID | Sev | Prior defect | Status | Evidence |
|---|---|---|---|---|
| **D1** | M | `parse_numeric` rejected Unicode minus; 1,099 understated corpus | **CLOSED** | `offline_core.py:58` accepts U+2212/U+2013/U+2014/U+FF0D. Recomputed 1,149 / 177 / 165 / 12 exact (§3) |
| **D2** | M | `run_offline_episode` raised instead of `TOOL_ERROR` | **CLOSED** | `collection_chain.py:45-53`, `:134-143`. 11/11 invalid-plan probes return `TOOL_ERROR`, **zero** raises (§4.1) |
| **D3** | M | history clusters not materialized; identity undisclosed | **CLOSED** | `build_exposure_and_split_audit.py:96`; `OFFLINE_RETURN.md:51-52` states identity plainly (§3.3) |
| **D4** | M | freeze set 221 vs register 233 | **CLOSED** | register = 233 UIDs, canonical hash `d6c37842…` recomputed and matched (§3.4) |
| **D5** | m | receipt did not pin test file | **CLOSED** | `run_offline_tests.py:41-44`; both receipts pin `4397727d…` = on-disk (§5.2) |
| **D6** | m | GB10 claim unsupported, receipt unlabelled | **CLOSED** | host-labelled; **this audit host is that machine**, 11/11 reproduced first-hand (§5.3) |
| **D7** | m | `0.50` outside `THRESHOLDS`; rule omitted from return | **CLOSED** | `source_cluster_builder.py:22`, used `:91`; `OFFLINE_RETURN.md:38` (§3.2) |
| **D8** | m | `CRASH`/`COMPLETE` not exclusive; markers rewriteable | **CLOSED** | `raw_capture.py:28-33`, `:44-47`; six probes refuse correctly (§4.2) |
| **D9** | m | negative `estimated_tokens` bypassed cap | **CLOSED** | `raw_capture.py:67`; 9/9 rejected, caps exact (§4.3) |
| **D10** | o | 2,246 structural UIDs invite over-reading | **CLOSED** | `OFFLINE_RETURN.md:14`, `:54` both state zero structural tasks (§3.5) |
| **D11** | o | five literal UIDs lacked provenance comment | **CLOSED as to requirement; residual N-1** | comment at `exposure_classifier.py:59-61`, but citations wrong (§5.4) |
| **D12** | o | outputs/post-dated files untraceable | **CLOSED** | first audit preserved + referenced `:110`; all outputs pinned in bundle (§6.2) |

**All nine repair items D1–D9 closed.** D10, D12 closed. D11 closed as to requirement with residual traceability defect N-1.

---

## 3. Count verification — D1, D3, D4, D10

### 3.1 D1 Unicode-minus handling

`offline_core.py:56-64` now applies `re.sub(r"[−–—－]", "-", text)` (line 58) before the numeric match, alongside the pre-existing accounting-parentheses convention.

| Input | Result | Assessment |
|---|---:|---|
| `−1.25` (U+2212) | `-1.25` | correct |
| `–1.25` (U+2013) | `-1.25` | correct |
| `—1.25` (U+2014) | `-1.25` | correct |
| `－1.25` (U+FF0D) | `-1.25` | correct |
| `1,234.56` | `1234.56` | correct |
| `1.0.0` / `+2.5` / `12.5%` / `$1,000` / `a-b` | `None` | correctly rejected |
| `—` `–` `−` `－` `——` `(—)` `()` | `None` | **placeholder-safe** |

**Placeholder safety was the material risk and it is clean.** Corpus dash-family cells: **2,838** (U+2212 ×73, U+2013 ×493, U+2014 ×2,272). Em/en-dash in TAT-QA is overwhelmingly a *missing-value placeholder*, not a minus. Every placeholder-only form still returns `None`; no bare placeholder was misparsed as a number across all newly-parsed cells.

**Delta attribution** (independent variant parsers, same corpus):

| Parser variant | Contract tasks |
|---|---:|
| ASCII minus only, no parentheses | 904 |
| + dash substitution only | 947 |
| + parentheses only (pre-D1 behaviour) | **1,099** |
| dash + parentheses (current) | **1,149** |

The D1 repair added **only** the dash substitution; the parentheses convention is pre-existing and produced the original 1,099. **All 123 newly-parsed cells are genuine signed numbers** (`−2,563`, `–743`, `−137`, …) — zero placeholders. Largest single change `c83c3a82…` 6 → 15, matching the prior projection.

### 3.2 Corrected headline counts — all reproduce exactly

| Claimed | Artifact path | Recomputed | Status |
|---|---|---:|---|
| Raw records 2,479 | `source_clusters.raw_records` | 2,479 (2,201 train + 278 dev) | **MATCH** |
| Clusters 2,443 | `source_clusters.clusters` | 2,443 | **MATCH** |
| Contract tasks **1,149** | `source_clusters.contract_tasks` | **1,149** | **MATCH** |
| Eligible clusters **177** | `…eligible_clusters_with_ge2_tasks` | **177** | **MATCH** |
| Immediate future 0 | `…immediate_future_clusters` | 0 | **MATCH** |
| Pending future **165** | `…pending_program_review_future_clusters` | **165** | **MATCH** |
| Excluded future 12 | `…excluded_future_clusters` | 12 | **MATCH** |
| History after reservation 12 | `…history_clusters_after_future_reservation` | 12 | **MATCH** |

Exposure layers recomputed from task-root evidence: 2,246 / 170 / 42 / 21 / 0 — sum 2,479. **MATCH.**

`SOURCE_CLUSTERS.json` rebuilt independently: **entire JSON identical** to on-disk. Thresholds equal the code constant and the recorded block. `edge_reason_counts` unchanged: `paragraph_near_duplicate` 25, `paragraph_reuse_table_divergence` 15, `table_near_duplicate` 14, `table_reuse_paragraph_divergence` 8, `exact_table` 9, `joint_near_duplicate` 4.

### 3.3 D3 — history clusters materialized, identity disclosed

- `build_exposure_and_split_audit.py:96` emits a **materialized set**, not a subtraction.
- `source_clusters.history_cluster_ids` = 12 ids, independently reproduced: `cluster_0482, 0548, 0810, 0893, 0943, 1052, 1443, 1737, 1744, 1816, 1978, 2147`.
- Set equality with `excluded_future`: **True**. Composition 10 `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` + 2 `MODEL_OR_FEEDBACK_EXPOSURE`.
- `SPLIT_PROPOSAL.json.history` carries the **same 12**.
- `OFFLINE_RETURN.md:51-52` states the identity explicitly. The prior misreading is closed.

### 3.4 D4 — non-structural exposure freeze register

| Field | Claimed | Recomputed | Status |
|---|---:|---:|---|
| `uid_count` | 233 | 233 | **MATCH** |
| `canonical_sorted_uids_sha256` | `d6c37842dd6ebb1f8d512ca0ad3f0f94a1a6ba5e39c8fbeefe4b16c710724070` | identical | **MATCH** |
| `uids` | sorted | sorted, unique, identical list | **MATCH** |

Set relation: the 221-UID TQ-5 exclusion union is a **strict subset**; `register − exclusion_union` = exactly the 12 TQ-5 panel-selected UIDs. Freezing 233 closes the gap that would have left 12 model-exposed UIDs unfrozen. `OFFLINE_RETURN.md:94` names the 233-UID register.

### 3.5 D10 — zero structural tasks explicit

`OFFLINE_RETURN.md:14` (*"contributes 0 tasks under the current two-period/unit contract"*) and `:54` (*"contributes zero current-contract tasks"*) both explicit. `tasks_by_exposure_category` = `{STRUCTURAL_SCAN_ONLY: 0, PROGRAM_GENERATED…: 1071, METHOD_DEVELOPMENT…: 60, MODEL_OR_FEEDBACK…: 18}`, sum 1,149 — **MATCH**. Shape note correctly disclosed at `:54`: 176 of 177 eligible clusters are singletons; only `cluster_1973` is multi-member (2 records, 3 tasks).

### 3.6 Split determinism and disjointness

| Bucket | Count | Expected | Status |
|---|---:|---:|---|
| `future_test` | 8 | 8 | **MATCH** |
| `development` | 2 | 2 | **MATCH** |
| `history` | 12 | 12 | **MATCH** |
| `reserve` | 155 | 155 | **MATCH** |
| total | 177 | = eligible | **MATCH** |

- **Deterministic**: re-derived all four buckets from the audit + `seed = history-collection-offline-v1-split-20261017` via `sha256(seed:scope:cluster_id)` ascending (`prepare_collection_gate.py:21-22`). All four reproduce the file **exactly and in order**.
- **Disjoint**: 177 rows, **177 unique cluster_ids**, zero duplicates across all four buckets. Every row has ≥2 tasks.
- Accounting closes: future pool 165 = 8 + 2 + 155.

---

## 4. Software-contract verification — D2, D8, D9

### 4.1 D2 — invalid plans return `TOOL_ERROR`, never raise

11/11 probes through `run_offline_episode` — **zero raises**:

| Expression | `plan_status` | raised | `tool_result.status` | `error_detail` |
|---|---|---|---|---|
| `1/0` | `INVALID_PLAN` | NO | `TOOL_ERROR` | `ZeroDivisionError` |
| `1 +` | `INVALID_PLAN` | NO | `TOOL_ERROR` | `SyntaxError` |
| `2**3` | `INVALID_PLAN` | NO | `TOOL_ERROR` | `ValueError` |
| `""` / `"  "` | `INVALID_PLAN` | NO | `TOOL_ERROR` | `EMPTY_TOOL_EXPRESSION` |
| `abs(1)` / `__import__("os")` / `1 if 1 else 2` / `"a"` / `(1,2)` | `INVALID_PLAN` | NO | `TOOL_ERROR` | `ValueError` |

Unsupported `tool` and unsupported `requested_quantity` also yield `INVALID_PLAN` → `TOOL_ERROR` without raising. Exception type preserved in `error_detail`. Pinned by `tests/test_offline_v1.py:104-113`. **D2 closed.**

### 4.2 D8 — terminal states mutually exclusive, markers immutable

| Probe | Result | OK |
|---|---|---|
| `persist_response` after `mark_crash` | `RuntimeError: terminal crash state already recorded` | ✓ |
| `mark_crash` after `COMPLETE` | `RuntimeError: completed request cannot transition to crash` | ✓ |
| rewrite `response.json` | `FileExistsError: response overwrite prohibited` | ✓ |
| rewrite `CRASH` (twice) | `FileExistsError: crash marker overwrite prohibited` | ✓ |
| rewrite `COMPLETE` | `FileExistsError: complete marker overwrite prohibited` | ✓ |

On-disk marker sets: crashed = `{CRASH, request.json}`; completed = `{COMPLETE, request.json, response.json}`. **No contradictory terminal state reachable via the public API.** Covered by `tests/test_offline_v1.py:123-137`, now extended to both directions. **D8 closed.**

### 4.3 D9 — reservation validation

`raw_capture.py:67` requires a positive non-bool integer. 9/9 rejected with `ValueError`: `-5`, `0`, `-1`, `1.5`, `True`, `False`, `"10"`, `None`, `10.0`. Caps remain exact (exact-cap reserve of 10 succeeds; next raises `REQUEST_CAP_REACHED`; `reserve(11)` vs cap 10 raises `TOKEN_CAP_REACHED` before any increment). Covered by `tests/test_offline_v1.py:139-152`. **D9 closed.**

---

## 5. Test, receipt, provenance — D5, D6, D11

### 5.1 Independent read-only test run

Run with `python3 -m unittest discover -s tests -p "test_*.py" -v` (deliberately **not** `run_offline_tests.py`, which rewrites the receipt):

```
Ran 11 tests in 0.001s
OK
```

**11/11 PASS**, 0 failures / 0 errors / 0 skipped, Python 3.12.3. Assertions substantive and not weakened.

### 5.2 D5 — both receipts pin the test file

| Receipt | `test_hashes.test_offline_v1.py` | On-disk | Status |
|---|---|---|---|
| `TEST_RECEIPT.json` | `4397727d906b675a…` | `4397727d906b675a…` | **MATCH** |
| `TEST_RECEIPT_GB10.json` | `4397727d906b675a…` | `4397727d906b675a…` | **MATCH** |

All 8 implementation hashes match on-disk in both receipts. `prepare_collection_gate.py:104` also pins the test file in the bundle. **D5 closed.**

### 5.3 D6 — GB10 receipt host-labelled, and first-hand corroborated

`TEST_RECEIPT_GB10.json`: `host_label: "GB10"`, `platform: "Linux-6.17.0-1018-nvidia-aarch64-with-glibc2.39"`, `python_version: "3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0]"`.

**Stronger than the repair required.** The host this re-audit ran on *is* that machine — `platform.platform()` and `sys.version` return byte-identical strings to the receipt fields. My independent 11/11 run therefore **corroborates the GB10 leg first-hand** on the claimed host, platform, and interpreter. Per repository policy GB10 is authoritative; that leg is now independently supported.

### 5.4 D11 — comments present, citations inaccurate (N-1)

Comment at `exposure_classifier.py:59-61` names all five UIDs — requirement met. **The citations do not survive tracing:**

| Comment claims | Verified actual |
|---|---|
| *"WP2 S4B prompts/receipts for `3ab739eb`, `97176853`"* | Both **absent from all five S4B artifacts** (`loop_a_prompt_s4b.md`, `S4B_EXECUTION_REPORT.md`, `S4B_BRIDGE_PROBE_RECEIPT.json`, `S4B_STOP_RECEIPT.json`, `S4B_BRIDGE_PROTOCOL_RECEIPT.json`). They **do** appear in WP2 receipts: `WP2_SPLIT_DRYRUN_RECEIPT.json`, `wp2/PILOT_ELIGIBILITY_RECEIPT.json`, `wp2/SPLIT_RERUN_RECEIPT.json`, `wp2/ITEMS_V2_RECEIPT.json`. |
| *"TQ-4 candidate/model artifacts for `329e3ff5`, `d2bba753`, `44c7c9ef`"* | All three **absent from the entire `tq4_calibration_v1/**` tree**. Actually present one-each in **TQ-3** specs `tq3_execution_prep_v1/specs_rev1/Q02.json`/`Q03.json`/`Q04.json`, plus `LAYER1_RESULTS_v1.json`, `v4/V4_RESULTS_v1.json`, `v4/V4_HELDOUT_LABELS_FROZEN_v1.json`. |

**The classification is correct and conservatively evidenced:** all five UIDs appear in 4 files each under `research/positive_repair_20261011/runs/PR-EXP-03*/p1_run*.jsonl`. `MODEL_OR_FEEDBACK_EXPOSURE` and the 233-UID register are right; only the citation is wrong.

---

## 6. Hash chain, gate status, side effects

### 6.1 Hash chain — fully self-consistent

| Link | Status |
|---|---|
| 8 implementation hashes, both receipts vs disk | **16/16 MATCH** |
| local vs GB10: `fixture_sha256`, `implementation_hashes`, `test_hashes`, `tests_run`, `failures`, `errors`, `skipped`, `status` | **all SAME** (only host/platform/Python differ) |
| `bundle.resolved.implementation` (10 files incl. `tests/test_offline_v1.py`) vs disk | **10/10 MATCH** |
| `bundle.resolved.control.{local,gb10}_test_receipt_sha256` vs disk | **2/2 MATCH** |
| `bundle.resolved.source_and_split.{source_clusters,exposure_audit,split_proposal}_sha256` vs disk | **3/3 MATCH** |
| End-of-audit re-check of every bundle hash | **no drift** |

### 6.2 D12 — traceability

First audit preserved (401 lines, `CONDITIONAL`) and referenced at `OFFLINE_RETURN.md:110`. All four updated outputs pinned in the bundle and matching. Prior handoff phrase `developmental evaluation set qualified by scanning and isolated from this history/development material` preserved verbatim, exactly once, at `OFFLINE_RETURN.md:60`. **D12 closed.**

### 6.3 Collection gate — `NOT_READY_FOR_COLLECTION`, correctly listed

`status: NOT_READY_FOR_COLLECTION`. Unresolved: `loop_c_independent_review: PENDING`, `program_generated_reference_review: PENDING`, `final_future_and_history_split: PENDING_REVIEW`, `task_and_reference_manifest: NOT_MATERIALIZED`, `tokenizer_chat_template_service_binary_generation_parameters: NOT_BOUND`, `online_collection_runner_and_prompt_templates: NOT_IMPLEMENTED_OR_NOT_BOUND`, `beijing_window: NOT_AUTHORIZED`, `independent_software_review_result: PENDING`. All online/runtime/window gates present and correctly unresolved.

Control: `collection_request_cap: 54`, `collection_token_cap: 600000`, `retry_cap: 0`, `concurrency: 1`, `judge_calls: 0`, `training_calls: 0` — consistent with a single non-bundled collection and `OFFLINE_RETURN.md:101`.

### 6.4 Side-effect scan

Full AST import inventory across all 9 package `*.py` + `tests/test_offline_v1.py`:
`__future__, argparse, ast, collection_chain, collections, exposure_classifier, hashlib, json, math, offline_core, operator, os, pathlib, platform, raw_capture, re, source_cluster_builder, sys, tempfile, typing, unicodedata, unittest, uuid`

No `requests`/`urllib`/`http`/`socket`/`subprocess`/model SDK/DB driver/`torch`/training module. Only `os` use is `os.replace` at `raw_capture.py:54`. No `os.system`, no `eval`/`exec`. `EXPOSURE_AND_SPLIT_AUDIT.json.cost` records all four counters at 0.

**Confirmed: model 0, endpoint 0, judge 0, training 0, service 0, collection 0, pilot 0.**

---

## 7. Verdict and boundaries

### Verdict: **`CONDITIONAL`**

**The prior blocking set is fully closed.** Every must-close item (D1, D2, D3, D4, D6) and every software-qualification blocker (D5, D7, D8, D9) is repaired and verified first-hand — several stronger than required. D10 and D12 closed. The package is reproducible, internally consistent, free of side effects, and its gate correctly self-reports `NOT_READY_FOR_COLLECTION`.

`CONDITIONAL` rather than `ACCEPTED` only because two residual defects surfaced in this pass (N-1, N-2) — one a correctness defect in a reference-bearing parser. Neither changes any headline count, the split shape, or the freeze register; both must close before a **task/reference manifest** is materialized, which is already an open gate.

**Solid without further work:** all eight headline counts reproduce (§3.2); `SOURCE_CLUSTERS.json` identical on rebuild (§3.2); D1 correct across all four Unicode-minus variants and placeholder-safe over 2,838 dash cells (§3.1); 1,149 now reproducible *and* semantically sound; history materialized and identity disclosed (§3.3); 233-UID register + canonical hash correct (§3.4); split deterministic and disjoint across all four buckets (§3.6); chain preserves `TOOL_ERROR` end-to-end with no gold correction (§4.1); `CRASH`/`COMPLETE` exclusive and immutable, reservations validated, caps exact (§4.2–4.3); both receipts pin the test file and GB10 first-hand corroborated (§5.2–5.3); 11/11 on Python 3.12.3 (§5.1); zero side effects (§6.4).

**Why not `ACCEPTED`:**

| ID | Blocks acceptance because |
|---|---|
| **N-2** | `parse_numeric` double-negates accounting form `(−N)` → `+N` for 14 corpus cells that almost certainly denote `−N`. No count affected, but any future gold reference from `usable_rows[].value` carries a sign error. Same defect class as D1 — reproducible but wrong. All 14 became parseable only under the D1 fix. |
| **N-1** | D11 provenance comment cites artifact families where the UIDs do not appear (TQ-4 for three absent from the whole TQ-4 tree; S4B prompts for two absent from all S4B artifacts). A re-tracer reaches a dead end. |

**Why not `REJECTED`:** no evidence fabricated; `scientific_status: NOT_A_SCIENTIFIC_RESULT`; conservative direction preserved throughout (conflict merges, strongest-evidence precedence, `EXPOSURE_UNKNOWN → EXCLUDE`, `NOT_AUTHORIZED`, `NOT_READY_FOR_COLLECTION`); both defects repairable without altering TAT-QA semantics. The split decision — future eligibility **conditional**, collection **not authorized** — is correct and robust to both.

---

## 8. Software qualification boundary

**`SOFTWARE_PASS` for the offline contract is now SUPPORTED** — this reverses the prior caveat that the claim overstated what the episode chain delivers. The chain now delivers error preservation at the documented entry point across 11 error classes; the raw-capture state machine is closed under tested transitions; the budget ledger rejects every invalid reservation class; receipt integrity covers the test file; 11/11 assertions substantive and independently reproduced.

Stated so it cannot be over-read: **offline deterministic contract only.** Not online tool-chain qualification, not model-runtime qualification, not a scientific result. `BudgetLedger` and `AtomicRawStore` remain unintegrated with `collection_chain` — no budget → capture → chain integration exists, so `OFFLINE_RETURN.md` §4 bullets remain accurate as *component* claims, not a wired pipeline. The online runner is correctly `NOT_IMPLEMENTED_OR_NOT_BOUND`.

## 9. Future-task qualification boundary

**Remains `CONDITIONAL`** — unchanged in status, narrower in what blocks it.

- Numeric shape satisfied and robust: **0 immediate / 165 pending / 12 history**, with deterministic 8/2/155 allocation (§3.6). Held before and after the D1 fix.
- **Gate on the 165 pending clusters is open and correctly left open**: independent review of whether program-generated tasks/references entered any designer, actor, feedback, correction, or effect-analysis context (`OFFLINE_RETURN.md:56`). Not mine to close.
- Human semantic gold is not provided and is not provided here. **This re-audit is not human semantic gold.**
- **N-2 must close before any task/reference manifest is materialized.** The 1,149 count is safe; the *values* behind it are not yet safe to freeze.
- G-M remains `HOLD / NOT_IDENTIFIED` (`OFFLINE_RETURN.md:109`).
- If fewer than 8 clusters survive review, apply the fallback at `OFFLINE_RETURN.md:62` — TAT-QA history plus a separately qualified MultiHiertt same-contract future source. **SEC EDGAR acquisition remains unauthorized.**
- Old WP-2 trajectories remain prohibited from E/U experience contexts. Old panels and frozen materials unchanged.
- Disclaimer at `OFFLINE_RETURN.md:20` should be retained.

## 10. Residual findings

### N-1 — D11 provenance comment cites the wrong artifact families — **m** (traceability)

- Location: `exposure_classifier.py:59-61`.
- **FACT**: `329e3ff5`, `d2bba753`, `44c7c9ef` are absent from the entire `tq4_calibration_v1/**` tree, contradicting *"TQ-4 candidate/model artifacts"*. Present in `tq3_execution_prep_v1/specs_rev1/Q02|Q03|Q04.json` (one each), `LAYER1_RESULTS_v1.json`, `v4/V4_RESULTS_v1.json`, `v4/V4_HELDOUT_LABELS_FROZEN_v1.json`.
- **FACT**: `3ab739eb`, `97176853` absent from all five S4B artifacts, contradicting *"WP2 S4B prompts"*. Present in `WP2_SPLIT_DRYRUN_RECEIPT.json`, `wp2/PILOT_ELIGIBILITY_RECEIPT.json`, `wp2/SPLIT_RERUN_RECEIPT.json`, `wp2/ITEMS_V2_RECEIPT.json`.
- **FACT**: all five appear in 4 files each under `research/positive_repair_20261011/runs/PR-EXP-03*/p1_run*.jsonl`, so the label and the register are correct.
- **VALUE**: correct the citations; do not change the classification.

### N-2 — accounting form `(−N)` parses as `+N`; 14 corpus cells likely sign-flipped — **m** (correctness, future gold)

- Location: `offline_core.py:59-64`. The dash substitution runs **before** the parenthesis-negation check, so `(−21)` → `(-21)` → strip → `-21` → then negated again → **`+21`**.
- **FACT**: 14 corpus cells take this path: `(−21)` ×4, `(−6)` ×2, and one each of `(−0.06)`, `(−1.46)`, `(−51)`, `(−49)`, `(−16)`, `(−15)`, `(−79)`, `(−69)`.
- **FACT**: all 14 became parseable only under the D1 dash fix (previously `None`) — newly load-bearing.
- **VALUE**: in TAT-QA accounting notation `(−21)` denotes **−21**; the parenthesis and minus both mark negativity and do not cancel. All 14 likely carry a sign error.
- **IMPACT**: **none on any count** — `contract_task_count` counts parseable values, and these parse either way. Impact is on `usable_rows[].value`, the input a future gold reference uses for `delta_source = late_value − early_value`.
- **FIX DIRECTION**: if the inner text already carries a sign, do not negate again. Re-run `build_exposure_and_split_audit.py` and confirm 1,149 / 177 / 165 / 12 are unchanged — they should be.

### N-3 — `evaluate_expression("True")` → `1.0` — **o** (carried)

`collection_chain.py:25` admits `bool` via `isinstance(…, (int, float))`. Harmless (a constant evaluates to its numeric value; no operator or call reachable); AST whitelist still rejects `**`, `abs()`, `__import__`, conditionals, string constants. Pre-existing.

### N-4 — `_write_atomic` has no existence guard; orphan response state possible — **o** (state machine)

`raw_capture.py:50-54` relies on caller-side checks (`:28-33`, `:44-47`) — check-then-write, TOCTOU-racy under concurrency. Acceptable given `concurrency: 1`, worth stating as a precondition. Also `persist_response` writes `response.json` then `COMPLETE` (`:37-38`); a crash between them leaves a request with no terminal marker that can never transition — a narrow durability gap in an otherwise closed machine.

### N-5 — split self-check omits the reserve bucket — **o** (disclosure)

`SPLIT_PROPOSAL.json.checks.source_cluster_disjoint` (`prepare_collection_gate.py:78-81`) covers only `future + development + history` (22 rows), not `reserve`. I independently verified all four buckets disjoint (177 rows, 177 unique ids). Invariant holds; the self-check is weaker than the invariant.

### N-6 — local receipt is Python 3.9.10 on Windows — **o** (policy deviation, non-authoritative leg)

`tests/TEST_RECEIPT.json` records `python_version: 3.9.10`, `Windows-10-10.0.19045-SP0`, `host_label: LOCAL_WINDOWS`. Repository policy mandates Python 3.12. The **authoritative** GB10 leg is 3.12.3 and is independently corroborated (§5.3), so the deviation sits only on the non-authoritative leg. The receipt is correctly labelled local. I cannot corroborate the Windows host first-hand; I can and do corroborate the GB10 host.

### N-7 — `EXPOSURE_UNKNOWN` key still omitted from `category_counts_by_uid` — **o** (cosmetic, carried)

Absent rather than `EXPOSURE_UNKNOWN: 0`. `OFFLINE_RETURN.md:18` does state 0. Unchanged from the prior audit.

---

## 11. Is the next collection request sufficiently prepared for owner review?

**Yes — sufficient to go to the owner, with two additions to the unresolved list.**

Ready: the hash bundle is complete, internally consistent and hash-verified end to end (§6.1), and correctly self-reports `NOT_READY_FOR_COLLECTION`; every online/runtime/window gate the owner must decide is already listed (§6.3); the split is deterministic, disjoint and reproducible from the seed (§3.6), so the owner reviews a concrete 8/2/12/155 allocation; the freeze set is the correct 233 UIDs with a canonical hash (§3.4); budget controls match the "one new collection only, no bundled pilot" rule (`OFFLINE_RETURN.md:101`).

Add before it is complete:

1. **N-2** — record on the unresolved list, or fix first. The gate already says `task_and_reference_manifest: NOT_MATERIALIZED`; N-2 is exactly why that manifest must not be materialized until the sign convention is settled. Adding `parse_numeric_accounting_sign_convention: UNRESOLVED` would make the gate honest about this.
2. **N-1** — correct the citations, or list `provenance_comment_citations: INACCURATE`.

Neither blocks the owner from *reviewing* the request; both should be visible in the review package.

## 12. Unresolved items and decision handoff to Loop D

**Created here:** (1) N-2 accounting-sign convention — blocks task/reference manifest materialization. (2) N-1 provenance citations — blocks nothing numerical, blocks self-documenting traceability.

**Carried forward:** (3) whether association thresholds were fixed before results were inspected — still not determinable; nothing indicates post-hoc tuning; D7's centralization/disclosure ask is met. (4) Independent review of program-generated task/reference contamination of designer/actor/feedback/correction/effect-analysis contexts — the gate on the 165 pending clusters; correctly left open. (5) Human semantic gold — not provided here. (6) Whether unrecorded historical model access exists — disclaimer at `:20` should be retained. (7) G-M `HOLD / NOT_IDENTIFIED`. (8) Budget → capture → chain integration does not exist; components unqualified as a pipeline.

**Correctly left `NOT_AUTHORIZED`:** online collection, pilot, training, service start, source switch, public release. None occurred; none authorized.

**Handoff:**

- This report is advisory. **It does not authorize collection and does not change `NOT_AUTHORIZED`.**
- Treat the prior **D1–D4 and D6 set as closed** — the pre-collection freeze blockers named in the first audit are cleared. D5/D7/D8/D9 closed likewise, so `SOFTWARE_PASS for the offline contract only` (`OFFLINE_RETURN.md:86`) is no longer an overstatement (§8).
- Treat **N-2 as blocking for the task/reference manifest**, **N-1 as blocking for the freeze register's provenance trail**. Neither blocks the software-qualification claim.
- Loop D may proceed to owner review of the collection request preparation (§11), carrying N-1 and N-2 in the unresolved list.
- The architect's numeric shape — 12 history clusters and a potential future set of at least 8 — is satisfied under both pre- and post-D1 counts and is now deterministic and disjoint. If fewer than 8 clusters survive review, apply the fallback at `OFFLINE_RETURN.md:62`; **SEC EDGAR acquisition remains unauthorized.**
- **Preserve verbatim** `developmental evaluation set qualified by scanning and isolated from this history/development material` (`OFFLINE_RETURN.md:60`).
- Old WP-2 trajectories remain prohibited from E/U experience contexts. Old panels and frozen materials unchanged. The first audit report is preserved and must not be edited.

---

*Produced by the Loop C independent reviewer, task `history-offline-audit-20261017-r2`. Read-only focused re-audit. AI review is not human semantic gold.*
