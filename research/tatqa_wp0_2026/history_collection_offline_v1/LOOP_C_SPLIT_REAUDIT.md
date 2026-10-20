# Loop C Focused Re-audit — Exposure-Qualified Split Revision

**Task id:** `history-split-reaudit-20261018-r1`
**Role:** Loop C independent reviewer
**Mode:** read-only focused re-audit of the revised future/development/history/reserve split
**Date:** 2026-10-18
**Artifact under review:** `SPLIT_PROPOSAL.json` revision 2
**Prior review:** `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` (r1 verdict `CONDITIONAL`)

---

## 0. Verdict

# `CONDITIONAL`

Revision 2 **is** a pure qualification-and-rank reselection. Against the categories recorded in `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md`, the reselection is mechanically exact — every one of the ten required checks on the selection mechanics reproduces bit-for-bit from independent recomputation.

One selected cluster is nonetheless **unsupported on the standard the prior review itself applied**:

> **`cluster_2314` is a WP2 dry-run `pilot`-role designated origin.** The prior review held `cluster_0584` and `cluster_1360` as `EXPOSURE_UNKNOWN` on exactly that designation boundary, and then stated in `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md:519-520` that the boundary is *unresolved* and that the conservative reading was applied "for the two future-pool members" only. `cluster_2314` was not a future-pool member at the time, so it was left clean. Revision 2 has now promoted it into the future 8.

Therefore the revised split **cannot be frozen for owner collection review as filed**. See §5.

---

## 1. Scope and method

Nothing in the task description, `OFFLINE_RETURN.md`, prior review verdicts, or commit messages was accepted as proof. Every claim below was reproduced mechanically before judgment.

Checks run (all read-only; zero model, endpoint, judge, canary, and training calls):

1. Independent reparse of the 165 per-cluster appendix records from `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` §7.
2. Independent recomputation of `sha256(seed:scope:cluster_id)` from the declared seed, from `EXPOSURE_AND_SPLIT_AUDIT.json.cluster_rows`, not from the proposal.
3. Independent rebuild of all five buckets and set/order comparison against `SPLIT_PROPOSAL.json`.
4. Independent rebuild of the *unfiltered* rank order to test the "removal + promotion only" claim.
5. Full read of `prepare_collection_gate.py`, `offline_core.py`, `run_offline_tests.py`, `tests/test_offline_v1.py`.
6. sha256 re-verification of every hash recorded in `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` and in both test receipts.
7. Inspection of `data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json` for the designation boundary.

Checks **not** run (declared, not silently omitted):

- No service start, data collection, model call, judge call, training, pilot, source switch, or data release.
- `run_offline_tests.py` was **not** executed: it writes `tests/TEST_RECEIPT.json` (`run_offline_tests.py:55-56`), which is a reviewed artifact this review is forbidden to modify. A direct `unittest` re-run was attempted and **required approval that was not granted**, so check 10 rests on hash pinning only (§4.9).
- No re-adjudication of the 12 `history` clusters, the 5 sub-threshold pending rows, or the 2211 `STRUCTURAL_SCAN_ONLY` clusters.
- No revision of `OFFLINE_RETURN.md`, `SPLIT_PROPOSAL.json`, the hash bundle, tests, implementation, prior reviews, raw data, or frozen material. This report is the only intended output.

---

## 2. Required check results

| # | Required check | Result |
|---|---|---|
| 1 | Reparse 165 records; verify category counts and conservative aggregation | **PASS** |
| 2 | Recompute rank key; verify revised order is first clean clusters | **PASS** |
| 3 | Only changes = removal of 3 + promotion under same rule | **PASS** |
| 4 | No future cluster unknown / exposed / method-dev / outside 165 | **PASS as filed — FAIL on substance** (§5) |
| 5 | Buckets pairwise disjoint; accounting closes to 177 | **PASS** |
| 6 | Future clusters ≥2 contract tasks; pending members `task_eligible: true` | **PASS** |
| 7 | Generator/tests free of hidden gold/answer/score/result/override selection | **PASS in generator — override found upstream** (§5) |
| 8 | Original unfiltered proposal and rejected IDs traceable in `.revision` | **PASS** |
| 9 | Hash bundle includes program review + current split hashes, `NOT_READY_FOR_COLLECTION` | **PASS** |
| 10 | Local and GB10 13/13 receipts pin current implementation and tests | **PASS** (hash pinning; no fresh run) |

---

## 3. Check 1 — Reparse of the 165 per-cluster records

Independent regex reparse of the fenced block in `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` §7 (lines 253–438):

- member-level lines found: **165**; parsed: **165**; unparsed: **0**
- distinct clusters: **165** (exactly one pending member UID per cluster)
- member-level category counts: `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE` **158**, `EXPOSURE_UNKNOWN` **2**, `MODEL_OR_FEEDBACK_EXPOSURE` **5**
- cluster-level conservative aggregation (strongest-evidence / max-rank): **158 / 2 / 5** — identical, because no cluster in the appendix carries more than one pending member
- clusters with mixed pending-member categories: **none**
- `cluster_contract_tasks >= 2` for all 165; sum of `cluster_contract_tasks` = 1066

Non-clean clusters, with appendix group as filed in the review:

| cluster | category | appendix group | tasks |
|---|---|---|---|
| `cluster_0584` | `EXPOSURE_UNKNOWN` | future_test | 11 |
| `cluster_1360` | `EXPOSURE_UNKNOWN` | future_test | 6 |
| `cluster_0599` | `MODEL_OR_FEEDBACK_EXPOSURE` | future_test | 9 |
| `cluster_0789` | `MODEL_OR_FEEDBACK_EXPOSURE` | reserve | 6 |
| `cluster_0890` | `MODEL_OR_FEEDBACK_EXPOSURE` | reserve | 7 |
| `cluster_0903` | `MODEL_OR_FEEDBACK_EXPOSURE` | reserve | 15 |
| `cluster_2344` | `MODEL_OR_FEEDBACK_EXPOSURE` | reserve | 5 |

Counts match the claim in the revision reason string and the r1 verdict.

---

## 4. Checks 2, 3, 5, 6, 7, 8, 9, 10 — mechanical reproduction

### 4.1 Rank rule

Taken from `prepare_collection_gate.py:14,38-39`:

```
SEED     = "history-collection-offline-v1-split-20261017"
rank_key = sha256(SEED + ":" + scope + ":" + cluster_id)   hex, ascending
scope    = "future"  for the pending pool (and excluded)
scope    = "history" for the history pool
```

Because the key depends only on `(seed, scope, cluster_id)`, filtering the pool cannot change the relative order of surviving clusters. "Rank applied to the clean pool" and "unfiltered rank restricted to clean clusters" are therefore the same order — this is what makes revision 2 a pure reselection.

### 4.2 Recomputed buckets vs. `SPLIT_PROPOSAL.json`

Rebuilt independently from `EXPOSURE_AND_SPLIT_AUDIT.json.cluster_rows` (eligible = `contract_task_count >= 2`) plus the reparsed review categories:

| bucket | recomputed n | file n | **exact order match** |
|---|---|---|---|
| `future_test` | 8 | 8 | **YES** |
| `development` | 2 | 2 | **YES** |
| `history` | 12 | 12 | **YES** |
| `reserve` | 148 | 148 | **YES** |
| `excluded_pending_review` | 7 | 7 | **YES** |

Also verified:

- `pending(165) == review(165)` as **sets** (no review cluster outside the pending pool, none missing)
- all 5 buckets pairwise disjoint: 177 ids, 177 distinct
- union of the 5 buckets == the 177 eligible clusters exactly
- 8 + 2 + 12 + 148 + 7 = **177** — accounting closes
- eligible breakdown: 165 `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` + 10 `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` + 2 `MODEL_OR_FEEDBACK_EXPOSURE` = 177
- the 7 excluded are exactly the 7 non-clean reviewed clusters
- every one of the 158 clean clusters appears in exactly one of future/development/reserve

### 4.3 Check 3 — removal + promotion, nothing else

Unfiltered rank order of all 165 pending clusters (top 12):

```
1 cluster_1340   5 cluster_0584    9 cluster_1628
2 cluster_0306   6 cluster_0978   10 cluster_2060
3 cluster_0599   7 cluster_1724   11 cluster_2314
4 cluster_0615   8 cluster_1360   12 cluster_1642
```

| step | result |
|---|---|
| unfiltered future 8 | `1340, 0306, 0599, 0615, 0584, 0978, 1724, 1360` |
| removed (non-clean) | `cluster_0584`, `cluster_0599`, `cluster_1360` — **exactly the 3 claimed** |
| kept | `1340, 0306, 0615, 0978, 1724` |
| promoted under the same rule | `1628`, `2060` (from development), `2314` (next clean in rank) |
| new development | `1642`, `2010` (next clean in rank) |
| reserve delta | removed `0789, 0890, 0903, 2344` (→ excluded), `2314, 1642, 2010` (→ future/dev); **added: none** |
| history | unchanged — set-equal to `EXPOSURE_AND_SPLIT_AUDIT.json.source_clusters.history_cluster_ids` |

The claim holds: **revision 2 is a pure qualification-and-rank reselection.** No cluster entered the future 8 other than by the documented rank advancing over clean clusters.

### 4.4 Check 5 — disjointness and 177

See §4.2. `SPLIT_PROPOSAL.json.checks.source_cluster_disjoint` is `true` and reproduces.

### 4.5 Check 6 — task counts and eligibility

| future cluster | `contract_task_count` | members | all `task_eligible` | uid matches audit |
|---|---|---|---|---|
| `cluster_1340` | 6 | 1 | true | yes |
| `cluster_0306` | 9 | 1 | true | yes |
| `cluster_0615` | 5 | 1 | true | yes |
| `cluster_0978` | 2 | 1 | true | yes |
| `cluster_1724` | 4 | 1 | true | yes |
| `cluster_1628` | 4 | 1 | true | yes |
| `cluster_2060` | 5 | 1 | true | yes |
| `cluster_2314` | 8 | 1 | true | yes |

All 8 have `contract_task_count >= 2`; every pending member is `task_eligible: true`. The only `task_eligible: false` member anywhere in the 177 eligible clusters is `e8438d76-0352-403f-8393-7532cade7715` in `cluster_1973` (`reason: no_unit_marker`, 0 tasks) — that cluster sits at `reserve[115]`, **not** in future.

### 4.6 Check 7 — hidden selection

`prepare_collection_gate.py` selection inputs, exhaustively:

- `row["contract_task_count"] >= 2` (line 98)
- `row["exposure"]["category"]` (lines 102, 106-109)
- `review[cluster_id]["category"] == "PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE"` (lines 114-120)
- `rank_key("future"|"history", cluster_id)` (lines 111, 121, 138, 142)

No task answers, reference values, gold, model results, scores, or effect estimates are read anywhere in the selection path. `offline_core.task_eligibility` (lines 98-127) reads only table structure: year headers, unit headers, and parseable numeric cells. A token scan of `build_exposure_and_split_audit.py`, `exposure_classifier.py`, `source_cluster_builder.py`, and `prepare_collection_gate.py` for gold/answer/score/effect/prediction/judge returns only `build_exposure_and_split_audit.py:192` — a cost-accounting field set to `0`. There are no hardcoded cluster IDs in the generator and no allowlist. The only writer of `SPLIT_PROPOSAL.json` is `prepare_collection_gate.py`.

`tests/test_offline_v1.py` contains no hardcoded future membership; `assertNotIn("cluster_0599", ...)` (line 35) is a negative qualification guard, not a selection override.

**However**, a pool-position-driven selective override exists one layer upstream, in the review's categorization itself. See §5.

### 4.7 Check 8 — traceability

`SPLIT_PROPOSAL.json.revision`:

| field | recorded | recomputed | match |
|---|---|---|---|
| `revision` | 2 | — | consistent |
| `prior_unfiltered_future_test_ids` | `1340, 0306, 0599, 0615, 0584, 0978, 1724, 1360` | identical | **YES** |
| `prior_unfiltered_development_ids` | `1628, 2060` | identical | **YES** |
| `rejected_from_prior_future_test` | `0584` `EXPOSURE_UNKNOWN`; `0599` `MODEL_OR_FEEDBACK_EXPOSURE`; `1360` `EXPOSURE_UNKNOWN` | identical | **YES** |

The original unfiltered future/development selection and all three rejected IDs are fully traceable. The prior unfiltered *reserve* membership is not stored verbatim, but is exactly reproducible from the declared seed and rule (reproduced here); the 12 history clusters remain recorded in `EXPOSURE_AND_SPLIT_AUDIT.json.source_clusters.history_cluster_ids`.

### 4.8 Check 9 — hash bundle

`PRE_COLLECTION_HASH_BUNDLE_DRAFT.json`:

| item | recorded | recomputed | match |
|---|---|---|---|
| `status` | `NOT_READY_FOR_COLLECTION` | — | **YES** |
| `resolved.source_and_split.split_proposal_sha256` | `ef019a81…bdb52` | `ef019a81…bdb52` | **YES** |
| `resolved.source_and_split.program_exposure_review_sha256` | `85ac9f3f…733ff` | `85ac9f3f…733ff` | **YES** |
| `exposure_audit_sha256` | `29a793ca…46f` | identical | **YES** |
| `source_clusters_sha256` | `12bb9d0f…890e` | identical | **YES** |

All 10 `resolved.implementation` entries re-verified against disk — **all match**. Online gates remain open: `beijing_window: NOT_AUTHORIZED`, `online_collection_runner_and_prompt_templates: NOT_IMPLEMENTED_OR_NOT_BOUND`, `focused_split_review_result: PENDING`, `task_and_reference_manifest: NOT_MATERIALIZED`. `control` records `judge_calls: 0`, `training_calls: 0`, `retry_cap: 0`, `concurrency: 1`.

### 4.9 Check 10 — test receipts

| receipt | host | tests_run | failures | errors | skipped | status |
|---|---|---|---|---|---|---|
| `tests/TEST_RECEIPT.json` | `LOCAL_WINDOWS` | 13 | 0 | 0 | 0 | `PASS` |
| `tests/TEST_RECEIPT_GB10.json` | `GB10` | 13 | 0 | 0 | 0 | `PASS` |

**13/13 on both.** Every `implementation_hashes` entry (8 files), the `test_hashes` entry (`test_offline_v1.py`), and `fixture_sha256` in **both** receipts match the current files on disk byte-for-byte. The bundle pins both receipt hashes correctly (`4be8aa00…` local, `88987eec…` GB10). Bundle and receipts agree on all implementation hashes.

Both receipts are labelled by host; per repository rules GB10 is authoritative and the local receipt is labelled local. Note the local receipt was produced on Windows/Python 3.9.10, not the repository's Python 3.12 baseline (`LOCAL_WINDOWS`, `run_offline_tests.py --host-label`); the GB10 receipt is Python 3.12.3 aarch64.

---

## 5. Finding — `cluster_2314` is unsupported on the review's own standard

### 5.1 What the prior review established

`LOOP_C_PROGRAM_EXPOSURE_REVIEW.md:182-201` (§5.2) holds `cluster_0584` and `cluster_1360` as `EXPOSURE_UNKNOWN` because they are WP2 dry-run designated origins. The stated basis is threefold:

1. they hold a WP2 dry-run **role designation**;
2. in the same pipeline, designation **was** followed by content consumption — the `history`-role origins `3ab739eb-…` and `97176853-…` entered real `Qwen/Qwen3-8B` prompts in `s4b_run/`;
3. past prompt use is not observed for these two — and "designated and not yet used" is "exactly the ambiguous case the standard reserves for `EXPOSURE_UNKNOWN`" (line 197).

The review then concedes the point explicitly at lines 519-520:

> **6. WP2 role designation boundary.** Whether `pilot_reserve` / `pilot` designation constitutes exposure is not resolved by the available receipts. This review chose the conservative reading **for the two future-pool members** and documented the alternative in 5.2.

### 5.2 What the evidence actually shows

`data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json` assigns all 22 designated origins from a **single content-blind rank**, `sha256("wp2-split-dryrun-20261013:origin_id") ascending`, sliced `[0:8]=pilot, [8:16]=pilot_reserve, [16:18]=development, [18:22]=history`. Every designated origin is produced by the identical mechanism.

19 of those 22 sit in the 165 reviewed pending clusters. Their dispositions as filed:

| role | in the 165 | `EXPOSURE_UNKNOWN` | `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE` |
|---|---|---|---|
| `pilot` | 8 | **0** | **8** |
| `pilot_reserve` | 7 | 2 | 5 |
| `development` | 2 | 0 | 2 |
| `history` | 2 | 0 | 2 |
| **total** | **19** | **2** | **17** |

The two held-out clusters are the **only** two designated origins that sat in the original future pool. The five other `pilot_reserve` clusters (`cluster_0772`, `1098`, `1996`, `2005`, `2095`) carry the **same role from the same receipt** and were left clean. Both `history`-role clusters in the pool (`cluster_1474`, `1710`) were left clean even though `history` designation is the very case that demonstrably led to model consumption. And all eight `pilot` clusters — the primary designated consumption slice — were left clean.

There is no per-cluster evidentiary difference behind the split. Compare the appendix evidence strings:

- `cluster_0584` (line 283) / `cluster_1360` (line 340) → `WP2 dryrun role pilot_reserve (…wp2_split_dryrun_receipt.json); designation->prompt pathway demonstrated in same pipeline; no past prompt hit`
- `cluster_0772` (line 295) / `cluster_2314` (line 413) → `WP2 dryrun role pilot_reserve|pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry`

Both describe the same designation from the same receipt. "No past prompt hit" is equally true of the clean ones; "no actor/design/effect entry" is untrue of a cluster that *is* a design entry. The difference is the narrative attached, not the facts.

### 5.3 Consequence for the revised split

`cluster_2314` (uid `f188de60-64eb-49cb-8b9d-a72f844357ef`) is `tatqa_f188de60-…` in the **`pilot`** role list — a stronger designation than the `pilot_reserve` designation that was deemed sufficient to exclude `cluster_0584` and `cluster_1360`. It is now `future_test[7]` in revision 2.

Under the review's own §5.2 rationale and §10.6 concession, `cluster_2314` should be `EXPOSURE_UNKNOWN`, or at minimum unresolved. It is not supported.

**Impact, recomputed under the unchanged rank:**

| reading | clean pool | future 8 | development |
|---|---|---|---|
| **A — as filed** | 158 | `1340, 0306, 0615, 0978, 1724, 1628, 2060,` **`2314`** | `1642, 2010` |
| **B — hold `cluster_2314` only** | 157 | `1340, 0306, 0615, 0978, 1724, 1628, 2060,` **`1642`** | `2010, 2096` |
| **C — hold all 17 designated** | 141 | `1340, 0306, 0615, 0978, 1724, 1628, 2060,` **`1642`** | `2010, 2096` |

Two useful properties:

- **`cluster_2314` is the only selected future cluster whose qualification depends on the boundary.** The other seven carry the §5.3 clean profile — `candidate_items_v2` deterministic generation with bounded non-entry against WP2 actor prompts, the multileaf manifest, TQ-4/TQ-5 panels, and coordinator diagnostics — and are clean under every reading.
- **The remedy is stable.** Readings B and C produce the same future 8, because no other designated origin ranks high enough to enter it. Dropping only `cluster_2314` or all designated origins changes nothing else.

Replacement candidates under the unchanged rule: `cluster_1642` (uid `ac6e77fe-…`, `contract_task_count` **2**, the minimum acceptable) and `cluster_2010` (5) / `cluster_2096` (7) for development. All three carry the §5.3 clean profile.

### 5.4 Check 7, restated

The generator contains no hidden selection. But the qualification layer it consumes encodes a **pool-position selective override**: the conservative reading was chosen "for the two future-pool members", so a cluster's category depended on where the *unfiltered* split had placed it rather than on its evidentiary profile. Revision 2 faithfully applies those categories and thereby inherits the inconsistency, promoting a cluster that the same standard would exclude.

---

## 6. Discrepancy register

| id | severity | location | discrepancy |
|---|---|---|---|
| **N-1** | **blocking** | `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md:283,340` vs `:413`; `:519-520`; `data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json` `.rule`, `.roles.pilot`; `SPLIT_PROPOSAL.json` `future_test[7].cluster_id` | `cluster_2314` is a WP2 `pilot`-role designated origin but is filed `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`, while `cluster_0584`/`cluster_1360` (`pilot_reserve`, a weaker designation) are `EXPOSURE_UNKNOWN` on that boundary. The boundary is declared unresolved and was applied only to future-pool members. `cluster_2314` is therefore unsupported in the future 8. |
| N-2 | advisory | `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` §7 `group=` column (12 rows) | Appendix `group=` labels describe the *unfiltered* split and are stale against revision 2: `0584/0599/1360` future_test→excluded; `0789/0890/0903/2344` reserve→excluded; `1628/2060` development→future_test; `2314` reserve→future_test; `1642/2010` reserve→development. Expected — that review documents r1 and is not to be revised — but any consumer matching on `group=` will disagree with the current split. |
| N-3 | advisory | `SPLIT_PROPOSAL.json` `future_test[*].exposure_category`, `development[*]`, `reserve[*]`, `excluded_pending_review[*]` | The top-level `exposure_category` is the *pre-review pool* category (`PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW`) and is identical for all 158 clean and all 7 excluded clusters. Qualification lives only in the nested `program_exposure_review.category`. A consumer reading `exposure_category` alone cannot distinguish clean from excluded. Not incorrect, but a real readability risk. |
| N-4 | advisory | `tests/test_offline_v1.py:44-62`; `prepare_collection_gate.py:69-80` | Test `test_program_exposure_review_contract_and_error_path` passes a fixture named `duplicate` but the `ValueError` it asserts comes from the `len(parsed) != 165` check at lines 79-80, not from duplicate detection. `parse_program_exposure_review_text` uses `setdefault` (line 69) and **merges** repeated `cluster_id` lines with conservative aggregation rather than rejecting them. Test name and covered behavior do not match. |
| N-5 | note | `run_offline_tests.py:55-56`; this review's check 10 | A fresh local test run was not performed: `run_offline_tests.py` overwrites a reviewed receipt, and a direct `unittest` invocation required approval that was not granted. Check 10 is satisfied by hash pinning only, not by re-execution. |
| N-6 | note | `tests/TEST_RECEIPT.json` `.host_label`, `.python_version` | The local receipt is `LOCAL_WINDOWS` / Python 3.9.10, not the repository's Python 3.12 baseline. Correctly labelled local; GB10 (Python 3.12.3 aarch64) remains authoritative. |

No other discrepancy was found. Checks 1, 2, 3, 5, 6, 8, 9 and the mechanics of 4, 7 and 10 reproduced exactly.

---

## 7. Freeze decision

**The revised split should not be frozen for owner collection review as filed.**

- Revision 2 **is** a pure qualification-and-rank reselection. The rank key, the seed, the scope, and the selection inputs are unchanged; the only filter added is the recorded review category. Every bucket reproduces exactly, the buckets are pairwise disjoint, and the accounting closes to 177 eligible clusters.
- But a future-set member (`cluster_2314`) is unsupported on the standard the prior review applied to exclude `cluster_0584` and `cluster_1360`. A future set that is not uniformly qualified cannot be frozen as a held-out evaluation set.

Two acceptable resolutions, both outside this review's authority to implement:

1. **Resolve the WP2 designation boundary first.** If a later reviewer establishes that dry-run role designation is strictly non-consuming and content-blind end to end, then `cluster_0584` and `cluster_1360` return to `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`, `cluster_2314` is fine where it is, and the split as filed stands — though the future set would then want re-derivation against a clean pool of 163 rather than 158.
2. **Apply the conservative reading consistently.** Hold `cluster_2314` as `EXPOSURE_UNKNOWN` and re-run the unchanged rule: future becomes `1340, 0306, 0615, 0978, 1724, 1628, 2060, 1642` with development `2010, 2096`. This is Reading B in §5.3 and is identical to Reading C, so the scope of the holding does not need to be decided to make the split well-defined.

Whichever path is taken, the resulting split should be re-verified against the same ten checks, and the `focused_split_review_result` key in `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` (currently `PENDING`) updated by an authorized party.

---

## 8. Standing statements

**This AI review is not human semantic gold.** Every disposition above rests on mechanical file evidence, deterministic recomputation, and data-flow tracing. No human annotated, judged, or adjudicated any UID or cluster here. Nothing in this report is a semantic gold label for task quality, reference correctness, or scientific validity. In particular, the N-1 finding is a **consistency** finding about how one documented standard was applied — it does not establish that `cluster_2314` is in fact exposed, only that it cannot be certified clean while the boundary remains unresolved and was applied selectively.

**Online collection remains unauthorized.** This review made zero model calls, endpoint calls, judge calls, canaries, and training calls. It started no service, collected no data, trained nothing, piloted nothing, authorized nothing, switched no source, and released no data. `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` remains `NOT_READY_FOR_COLLECTION` with `beijing_window: NOT_AUTHORIZED` and the online collection runner and prompt templates `NOT_IMPLEMENTED_OR_NOT_BOUND`. No collection may proceed on the basis of this report.

**Residual provenance limits carried forward from r1 (unchanged, out of scope here):** clusters are source-association clusters, not report-level independence units, so future-test leakage across reports cannot be excluded; `exposure_classifier.py` cannot emit `EXPOSURE_UNKNOWN` for UIDs present in the raw corpus; the PR-EXP-03 registry transcription defect remains open; item-level gold correctness of any generated task or reference was not verified by this or the prior review.
