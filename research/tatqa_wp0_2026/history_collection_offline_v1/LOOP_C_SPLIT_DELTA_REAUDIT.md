**Verdict: `ACCEPTED`** — r2 N-1 is **closed**; revision 3 **can be frozen** for owner collection review; online collection **remains unauthorized**.

---

# Loop C Delta Re-Audit — revision 3 WP2 designation closure

**Task id:** `history-split-delta-reaudit-20261018-r2`
**Role:** Loop C independent reviewer
**Mode:** read-only delta re-audit of `SPLIT_PROPOSAL.json` revision 3 against `LOOP_C_SPLIT_REAUDIT.md` N-1
**Date:** 2026-10-18
**Artifact under review:** `SPLIT_PROPOSAL.json` (revision 3) + `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json`

---

## 0. Verdict

# `ACCEPTED`

| | |
|---|---|
| **r2 N-1 (WP2 designation applied selectively)** | **CLOSED** |
| **Blocking discrepancies in revision 3** | **none** |
| **Can revision 3 be frozen for owner collection review?** | **YES** |
| **Online collection authorized?** | **NO — remains unauthorized** |
| **Human semantic gold?** | **NO — this is AI evidence review only** |

All ten revision-3 claims reproduce mechanically from raw inputs. Both advisory items (N-3 readability, N-4 test naming) are fixed as claimed. Four non-blocking observations (§5) are recorded for the owner; none affects the future 8, the development 2, or the closure accounting.

> **This AI review is not human semantic gold.** Every disposition below rests on mechanical file evidence and deterministic recomputation. No human annotated, judged, or adjudicated any UID or cluster here. Nothing in this report is a semantic gold label for task quality, reference correctness, or scientific validity.
>
> Consistent with `LOOP_C_SPLIT_REAUDIT.md` §7: the N-1 finding was a **consistency** finding about how one documented standard was applied. It did not establish that any cluster is in fact exposed. Revision 3 closes the *consistency* defect. It does not resolve the underlying WP2 designation boundary, which remains unresolved.
>
> **Online collection remains unauthorized.** This review performed zero model calls, zero judges, zero training, zero pilots, zero data collection, and zero service starts. `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` remains `NOT_READY_FOR_COLLECTION` with `beijing_window: NOT_AUTHORIZED` and `online_collection_runner_and_prompt_templates: NOT_IMPLEMENTED_OR_NOT_BOUND`.

---

## 1. Scope and method

Reviewed: `SPLIT_PROPOSAL.json` revision 3, `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json`, `prepare_collection_gate.py`, `tests/test_offline_v1.py`.

Cross-checked against raw evidence: `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` §7 appendix (r1), `LOOP_C_SPLIT_REAUDIT.md` (r2), `EXPOSURE_AND_SPLIT_AUDIT.json`, `SOURCE_CLUSTERS.json`, `data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json`.

**Independence.** Nothing in the task description, `OFFLINE_RETURN.md`, the revision `reason` string, prior verdicts, or commit messages was accepted as proof. The category map, the WP2 designation set, the adjusted counts, and the full rank were recomputed from raw inputs with a private parser and an independently re-implemented `sha256(seed:scope:cluster_id)` key. Project code was imported only to interrogate two named error paths (§4 N-4) and to run the generator against a scratch copy (§5 D-2).

**No reviewed file was modified.** `SPLIT_PROPOSAL.json` (`e0db478d…`), `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` (`935316b1…`), `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` (`85ac9f3f…`), `LOOP_C_SPLIT_REAUDIT.md` (`431bcaec…`), `EXPOSURE_AND_SPLIT_AUDIT.json` (`29a793ca…`), `SOURCE_CLUSTERS.json` (`12bb9d0f…`), `prepare_collection_gate.py` (`13c65640…`) and `tests/test_offline_v1.py` (`cf7526a6…`) were verified unchanged in both mtime and sha256 after the audit. All scratch work was confined to `/tmp` and has been removed.

---

## 2. The blocking finding and its authorized resolution

`LOOP_C_SPLIT_REAUDIT.md` N-1 held that the WP2 dry-run role designation had been applied **selectively by pool position**:

- r1 marked only `cluster_0584` and `cluster_1360` `EXPOSURE_UNKNOWN`;
- 17 other pending clusters carrying the same `WP2 dryrun role` evidence were left `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`;
- revision 2 then promoted `cluster_2314` into the future 8 despite its `pilot` designation.

The authorized conservative resolution is **Reading C**: every r1 appendix entry whose evidence records `WP2 dryrun role` is `EXPOSURE_UNKNOWN`, regardless of its original pool position.

### 2.1 Independent derivation of the designation set

Parsed `LOOP_C_PROGRAM_EXPOSURE_REVIEW.md` §7 with a private regex: **165 rows, 165 distinct `cluster_id`, 0 malformed.** Applying the Reading C predicate (`"WP2 dryrun role" in evidence`) yields **19 clusters**, each with its role string:

| # | cluster | r1 category | r1 `group=` | WP2 role | appendix line |
|---|---|---|---|---|---|
| 1 | `cluster_0013` | clean | reserve | `pilot` | 256 |
| 2 | `cluster_0489` | clean | reserve | `pilot` | 282 |
| 3 | `cluster_0584` | **EXPOSURE_UNKNOWN** | future_test | `pilot_reserve` | 283 |
| 4 | `cluster_0647` | clean | reserve | `development` | 288 |
| 5 | `cluster_0689` | clean | reserve | `pilot` | 292 |
| 6 | `cluster_0772` | clean | reserve | `pilot_reserve` | 295 |
| 7 | `cluster_0976` | clean | reserve | `pilot` | 314 |
| 8 | `cluster_1098` | clean | reserve | `pilot_reserve` | 322 |
| 9 | `cluster_1105` | clean | reserve | `pilot` | 323 |
| 10 | `cluster_1360` | **EXPOSURE_UNKNOWN** | future_test | `pilot_reserve` | 340 |
| 11 | `cluster_1369` | clean | reserve | `pilot` | 343 |
| 12 | `cluster_1474` | clean | reserve | `history` | 351 |
| 13 | `cluster_1710` | clean | reserve | `history` | 368 |
| 14 | `cluster_1996` | clean | reserve | `pilot_reserve` | 389 |
| 15 | `cluster_2005` | clean | reserve | `pilot_reserve` | 390 |
| 16 | `cluster_2095` | clean | reserve | `pilot_reserve` | 400 |
| 17 | `cluster_2178` | clean | reserve | `pilot` | 407 |
| 18 | `cluster_2224` | clean | reserve | `development` | 410 |
| 19 | `cluster_2314` | clean | reserve | **`pilot`** | 413 |

Derived independently: **2 already `EXPOSURE_UNKNOWN`** (`0584`, `1360`) and **17 clean before the boundary** — exactly the N-1 arithmetic.

### 2.2 Designation set cross-checked against the source receipt

The r1 evidence strings are themselves a claim. Cross-checked every uid against `data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json` (`rule: sha256(seed:origin_id) ascending; [0:8]=pilot, [8:16]=pilot_reserve, [16:18]=development, [18:22]=history`; `roles` = 22 designated origins): **19/19 role assignments agree exactly** with the r1 evidence strings. No mismatch, in either direction.

The receipt designates 22 origins; 3 are outside the r1 appendix. See §5 D-1.

---

## 3. Claim-by-claim verification

Raw r1 counts recomputed from the appendix: `{PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE: 158, EXPOSURE_UNKNOWN: 2, METHOD_DEVELOPMENT_OR_DIAGNOSTIC: 0, MODEL_OR_FEEDBACK_EXPOSURE: 5}` = 165.

Counts after applying Reading C to the 19 derived designations: `{141, 19, 0, 5}` = 165.

| # | Claim | Result | Mechanical evidence |
|---|---|---|---|
| **1** | Reading C applied to all 19; 17 previously clean reclassified | **PASS** | `revision.wp2_designated_cluster_ids` equals the independently derived set exactly (19/19). `wp2_category_reclassified_count: 17` equals derived clean-before = 17. All 19 appear in `excluded_pending_review` with `effective_exposure_category` and `program_exposure_review.category` both `EXPOSURE_UNKNOWN`, each carrying the appended `LOOP_C_SPLIT_REAUDIT N-1` evidence line. `category_before_wp2_boundary` is recorded on all 19: 17 × `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`, 2 × `EXPOSURE_UNKNOWN` (`0584`, `1360`). |
| **2** | raw 158/2/5, adjusted 141/19/5 | **PASS** | Recomputed raw `{158, 2, 0, 5}` and adjusted `{141, 19, 0, 5}` match `revision.program_review_raw_category_counts`, `checks.raw_review_category_counts` and `checks.adjusted_review_category_counts` field-for-field. |
| **3** | future `1340, 0306, 0615, 0978, 1724, 1628, 2060, 1642` | **PASS** | Independent re-rank of the clean pool under `sha256(seed:future:cluster_id)` ascending reproduces this list **in this exact order**. |
| **4** | development `2010, 2096` | **PASS** | Ranks 9–10 of the same clean-pool order: `cluster_2010`, `cluster_2096`. Order match. |
| **5** | 8 / 2 / 12 / 131 / 24, disjoint, closing to 177 | **PASS** | Sizes `(8, 2, 12, 131, 24)`, sum **177**, all 177 ids distinct. Eligible universe (`contract_task_count >= 2`) is exactly 177 = 165 pending + 12 history. Full ordered lists for all five buckets reproduce exactly, including all 131 reserve positions. |
| **6** | `cluster_2314` excluded as `EXPOSURE_UNKNOWN` | **PASS** | In `excluded_pending_review`, `effective_exposure_category: EXPOSURE_UNKNOWN`, `program_exposure_review.category: EXPOSURE_UNKNOWN`, evidence includes the N-1 line. Absent from future, development, and reserve. Independently in the WP2 set with role `pilot`. |
| **7** | every future cluster ≥2 contract-valid tasks, `task_eligible: true` | **PASS** | All 8 verified against `EXPOSURE_AND_SPLIT_AUDIT.json` member records: `contract_task_count` ∈ {6, 9, 5, 2, 4, 4, 5, 2}, every member `task_eligible: true`, `task_eligible_record_count` consistent. `cluster_1642` and `cluster_0978` sit at the documented minimum of 2. |
| **8** | unfiltered / rev 2 / rev 3 rejection traceability preserved | **PASS** | See §3.1. |
| **9** | no answer / gold / score / model result / effect estimate / manual allowlist in selection | **PASS** | Recursive key and value scan returns **no** hit. Top-level keys only `schema, status, seed, selection_rule, future_test, development, history, reserve, excluded_pending_review, revision, checks`. Bucket row keys only `cluster_id, contract_task_count, task_eligible_record_count, exposure_category, members, program_exposure_review, effective_exposure_category`. `program_exposure_review` keys only `cluster_id, category, category_before_wp2_boundary, uids, evidence`. `selection_rule` is purely deterministic. |
| **10** | bundle at `NOT_READY_FOR_COLLECTION`, online authorization absent | **PASS** | `status: NOT_READY_FOR_COLLECTION`, `owner_review_state: READY_WITH_UNRESOLVED_ONLINE_GATES`, `unresolved.beijing_window: NOT_AUTHORIZED`, `unresolved.online_collection_runner_and_prompt_templates: NOT_IMPLEMENTED_OR_NOT_BOUND`, `task_and_reference_manifest: NOT_MATERIALIZED`. `control` records `judge_calls: 0`, `training_calls: 0`, `retry_cap: 0`. Every resolved hash pin matches the bytes on disk (§5 D-2). |

### 3.1 Claim 8 detail — three-layer rejection traceability

| layer | recorded fields | verification |
|---|---|---|
| **original unfiltered** | `prior_unfiltered_future_test_ids`, `prior_unfiltered_development_ids`, `rejected_from_prior_future_test` | Unfiltered future rank head `1340, 0306, 0599, 0615, 0584, 0978, 1724, 1360` and development pair `1628, 2060` both reproduce exactly from the independent re-rank of the *uncleaned* pool. The three rejections (`0584` → `EXPOSURE_UNKNOWN`, `0599` → `MODEL_OR_FEEDBACK_EXPOSURE`, `1360` → `EXPOSURE_UNKNOWN`) are exactly the non-clean members of that head, with correct adjusted categories. |
| **revision 2** | `superseded_revision_2_future_test_ids`, `rejected_from_revision_2_future_test` | The eight ids match `LOOP_C_SPLIT_REAUDIT.md` §5.3 Reading A verbatim (`1340, 0306, 0615, 0978, 1724, 1628, 2060,` **`2314`**). The single rejection `cluster_2314` → `EXPOSURE_UNKNOWN`, reason `LOOP_C_SPLIT_REAUDIT N-1`, is recorded with its cause. |
| **revision 3** | the five buckets + `excluded_pending_review[*].program_exposure_review` | All 24 excluded entries carry their non-clean category and evidence trail, including the appended N-1 line on the 19 WP2 entries. Partition is 19 `EXPOSURE_UNKNOWN` + 5 `MODEL_OR_FEEDBACK_EXPOSURE`. No clean cluster excluded; no non-clean cluster selected or held in reserve. |

---

## 4. Advisory fixes

| item | claim | result |
|---|---|---|
| **N-3 readability** | each non-history bucket exposes `effective_exposure_category` | **PASS** — present on 8/8 future, 2/2 development, 131/131 reserve, 24/24 excluded; zero missing, zero mismatched against `program_exposure_review.category`. History also carries it (12/12), not required by N-3. |
| **N-4 test naming** | N-4's test name now matches its count-error behavior | **PASS** — renamed `test_program_exposure_review_contract_and_error_path` → `test_program_exposure_review_contract_and_count_error_path`; old name absent. The asserted error path was executed directly: the `too_short` fixture raises `ValueError: expected 165 reviewed clusters, found 1`, i.e. from the `len(parsed) != 165` count check, **not** from duplicate detection. A repeated-`cluster_id` input does not raise on duplication — `parse_program_exposure_review_text` merges via `setdefault`. Name and covered behavior now agree. |

---

## 5. New observations (non-blocking)

| id | severity | finding |
|---|---|---|
| **D-1** | informational | **Three further WP2-designated origins sit outside the authorized Reading C scope.** The dry-run receipt designates 22 origins; 19 are the r1 appendix set treated above. The remaining three — `cluster_0548` (uid `3ab739eb…`, role `history`), `cluster_1443` (uid `97176853…`, role `history`), `cluster_1737` (uid `b538d340…`, role `pilot_reserve`) — are not appendix entries and therefore fall outside "every r1 appendix entry whose evidence records `WP2 dryrun role`". All three are already `future_test_state: EXCLUDE` on their own exposure category (`MODEL_OR_FEEDBACK_EXPOSURE`, `MODEL_OR_FEEDBACK_EXPOSURE`, `METHOD_DEVELOPMENT_OR_DIAGNOSTIC`) and land in the **history** bucket, which is the experience side and not a held-out evaluation set. **There is no under-application inside the 165**: every receipt-designated uid whose cluster is in the pending pool is in the WP2-19. Revision 3 correctly implements the authorized, appendix-scoped rule. *For the owner:* the designation boundary is appendix-scoped by construction. If it is ever widened to all designated origins regardless of pool, these three would need the same treatment — that would change history only, never the future 8. |
| **D-2** | advisory (pre-collection) | **`SPLIT_PROPOSAL.json` and `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` are stored with CRLF line endings; the generator writes LF.** Re-running `prepare_collection_gate.py` on a scratch copy reproduces the split **JSON-identical and line-for-line identical** (3590/3590 lines, zero differing lines) — the *only* difference is the newline convention (reviewed file larger by exactly 3589 CR bytes). All bundle hash pins match the reviewed bytes as filed (`split_proposal_sha256` `e0db478d…` = actual; `source_and_split`, `implementation` 10/10, `independent_review_reports` 5/5, both control receipts all match). However, a fresh generator run emits LF bytes with a different `split_proposal_sha256` (`1c230e00…`), so the bundle would **not** reproduce byte-identically from the generator. Integrity/tamper-evidence is intact (the pin matches what is on disk); only generator-level reproducibility of the pin is affected. `SOURCE_CLUSTERS.json` and `EXPOSURE_AND_SPLIT_AUDIT.json` are LF, so this is confined to the two artifacts written during revision 3. *Recommend:* normalize line endings, or record the pin convention, before the bundle is materialized. |
| **D-3** | note | **Revision-2 provenance strings are hardcoded literals** in `prepare_collection_gate.py` (`superseded_revision_2_future_test_ids`, `rejected_from_revision_2_future_test`) rather than derived. They are **accurate today** — cross-checked against `LOOP_C_SPLIT_REAUDIT.md` §5.3 — but would silently go stale if re-run against different inputs. Selection is unaffected: those literals only populate the `revision` provenance block and feed no filtering or ranking. |
| **D-4** | note | **Revision 2's development pair (`cluster_1642`, `cluster_2010`) is not stored verbatim** in the revision block; only its future 8 and its one rejection are. Same class of gap `LOOP_C_SPLIT_REAUDIT.md` §6 already accepted for the unfiltered reserve membership: not stored, but exactly reproducible from the declared seed and rule. All three *rejection* layers (the substance of claim 8) are preserved. |

**Verified non-issue.** `cluster_1973` (reserve) is the only cluster in the whole proposal with mixed member eligibility: one `task_eligible: true` member carrying 3 contract tasks plus one `STRUCTURAL_SCAN_ONLY` member with `task_eligible: false`, `reason: no_unit_marker`. It still satisfies "two or more contract-valid tasks with `task_eligible: true`", and `task_eligible_record_count: 1` records it correctly. Every other cluster in all five buckets has all members `task_eligible: true`. Not a discrepancy.

---

## 6. Answers to the review questions

**Is r2 N-1 closed?** **Yes.** The selective application is gone. Reading C is applied uniformly to all 19 WP2-designated appendix entries regardless of original pool position, the 17 previously clean entries are reclassified, `cluster_2314` is excluded as `EXPOSURE_UNKNOWN`, and the resulting future 8 is uniform under the standard. Every number in the revision-3 claim set reproduces from raw inputs.

**New discrepancies?** None blocking. Four non-blocking observations (§5): D-1 three designated origins outside the authorized appendix scope (already `EXCLUDE`, history side only), D-2 CRLF/LF pin reproducibility, D-3 hardcoded revision-2 provenance literals, D-4 revision-2 development pair not stored verbatim.

**Can revision 3 be frozen for owner collection review?** **Yes.** The selection is deterministic, content-blind, free of answers/gold/scores/effect estimates/manual allowlists, pairwise disjoint, and closes to 177. D-1 through D-4 should be read by the owner as review context; D-2 is worth resolving before the bundle is materialized into a real collection gate, not before review.

---

## 7. Standing statements

- **This AI review is not human semantic gold.** No human adjudicated any UID or cluster here. Nothing above is a semantic gold label for task quality, reference correctness, or scientific validity.
- **Online collection remains unauthorized.** Zero model calls, zero canaries, zero judges, zero training, zero pilots, zero new runs, zero data collected, zero services started. The only execution performed was local deterministic recomputation and one offline generator re-run against a `/tmp` scratch copy (since removed).
- **The WP2 designation boundary remains unresolved.** Revision 3 applies the authorized conservative reading consistently; it does not establish that any designated origin is in fact exposed, nor that the designation is non-consuming. If the boundary is later resolved in the other direction, the clean pool returns to 158 and the split wants re-derivation — a future-set change of the kind `LOOP_C_SPLIT_REAUDIT.md` §7.1 already scoped.
- **Local results are labelled local.** No GB10 runtime behavior is claimed or implied by this review.
