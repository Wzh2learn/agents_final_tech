# HISTORY_COLLECTION_DESIGN_v1 RETURN

> Status: `DESIGN_PACKAGE_COMPLETE / CONDITIONAL_COLLECTION_RECOMMENDATION / NOT_A_SCIENTIFIC_PASS`
> Model/endpoint/judge/training calls in this phase: 0.

## 1. Question answered

**Is this application package sufficient to request approval for one new bounded real-history collection?**

**Recommendation: `CONDITIONAL_HISTORY_COLLECTION_ONLY`; bind a future task source first if the collection is intended for immediate evaluation.**

The package fixes the source, task class, real-experience chain, feedback visibility, comparison semantics, model pin, budget shape, and stop rules. It is sufficient to put one collection decision in front of the next gate. It is **not** sufficient to start requests today: source-cluster/exposure closure and the new tool-chain hash bundle must be frozen before the first request.

This is not a recommendation for pilot, method research, or scientific PASS. Under the current TAT-QA/WP-0 task contract there are zero unexposed future-pilot clusters, so collection should not be spent merely to create data that cannot be evaluated.

## 2. Qualification results

| item | result | evidence / gap |
|---|---|---|
| Source family | `PASS` | TAT-QA fixed; SEC EDGAR excluded |
| Upstream revision | `PASS` | `870accc41953dcde885aabeb963d94aabdc0fbc3` |
| Raw identity | `PASS_ON_GB10` | train/dev hashes match the architect's re-verification |
| Licence | `PASS` | CC BY 4.0; attribution and derivative note required |
| Task class | `PASS_DESIGN` | explicit row, two periods, signed difference, explicit unit conversion |
| Record-level pool | `PASS` | 182 origins; 176 with >=2 usable rows; 352 draft v2 items; 316 eligibility-passing items |
| Report/source clusters | `PARTIAL_FOR_HISTORY` | proposed rule yields 182 singleton components on the history-candidate manifest; raw schema still has no report ID |
| Near-duplicate isolation | `PASS_FOR_DESIGN_RECOMPUTATION` | 160 clean components after WP-2 exclusions; 154 have >=2 rows; persistent replay builder still required |
| Exposure exclusion | `PASS_FOR_RECORDED_SOURCES` | 22 WP2 role origins, Q02-Q04 source UIDs, opaque WP2 refs and TQ panels mapped; 221-UID union reproduced from pinned sources and hashed |
| Historical experience pool | `NOT_ESTABLISHED` | old WP-2 traces are prohibited from U/E |
| Feedback rights | `DESIGN_READY` | conservative visible/hidden fields fixed in `COLLECTION_DESIGN.md` |
| Model identity | `PARTIAL` | Qwen3.6 artifact hash fixed; runtime/template/tokenizer/service/tool hashes still required |
| Two-stage tool chain | `NOT_QUALIFIED` | plan -> real tool -> consume chain is specified but not implemented |
| Budget | `DRAFT_READY` | collection cap 54 requests / 600k tokens; not activated |
| Human semantic review | `UNRESOLVED` | not required for bounded contract tasks; required for later natural semantic claims |
| Future independent task pool | `FAIL_CURRENT_CONTRACT` | 2,246 unexposed raw records remain, but 0 satisfy the two-period/unit/usable-row task contract |

## 3. Conservative source availability

- Current record-level candidate manifest: 182 origins.
- With at least two usable rows: 176 origins.
- Known old WP-2 role origins: 22.
- Conservative record-level remainder after those roles: 160 origins; 154 have at least two usable rows.
- Proposed source-cluster recomputation: 182 singleton components total; 160 history-candidate components after WP-2 role exclusions; 154 have at least two usable rows.
- Recorded TQ exclusion union: 221 UIDs, canonical sorted-UID sha256 `416bdf247a242ded47b7edc32e5a39554547f9715bdf683685bf2df3d8d674f3`.
- Collection target: 12 source clusters, one task each.
- Record-level volume and the proposed component rule are sufficient for the 12-cluster history-collection target only. The 182-record manifest is a TQ-5 exclusion source and cannot be a new unseen pilot set.
- After the 221-UID union and 12 TQ-5 selected UIDs, 2,246 raw records remain outside recorded TQ exposure. This is not an independent-cluster count.
- WP-0 task-eligibility recomputation on those 2,246 records yields 0 eligible records and therefore 0 future-pilot source clusters.

## 4. Minimum engineering changes before collection

1. Persist and replay the deterministic source-cluster builder used for the design recomputation.
2. Materialize the reproduced 221-UID exposure register and cluster-disjoint history/development/future-test split.
3. Build a new isolated collection runner; do not modify or resume the old WP-2 runner.
4. Bind model, tokenizer, chat template, service binary, generation parameters, calculator, checker, and adapter hashes.
5. Add unique request IDs, atomic raw capture, and overwrite protection.
6. Implement independent reference recomputation and explicit `REFERENCE_UNSCORABLE` handling.
7. Validate the protocol only with labelled engineering fixtures.
8. Freeze the collection manifest, exact Beijing-time window, and 54-request accounting before the first scientific request.

No implementation is included in this package.

## 5. AUTHORIZATION boundary

Recommended approval wording:

> Before spending collection requests, bind either (a) a different future independent task source with at least 8 eligible source clusters or (b) an explicitly approved revised task scope. If the owner accepts cross-source evaluation, authorize one new TAT-QA history-collection run of at most 54 two-stage requests and 600k tokens only after the exact exposure register and the complete plan-tool-consume hash bundle are frozen and independently checked. This authorization excludes pilot, U/E comparison, judge calls, training, online memory write-back, future-test reuse of the 182-record manifest, and all use of old WP-2 trajectories as experience.

If any pre-request condition remains unresolved, the collection does not start.

## 6. STOP_CONDITIONS before collection

- fewer than 12 eligible history source clusters remain after the final exact exposure register and near-duplicate exclusion;
- any future-test split would reuse the 182-record TQ-5 exclusion source or another exposed cluster;
- future-test cluster independence cannot be preserved;
- no future independent task source or revised scope is bound before collection;
- old WP-2 trajectories would be needed to fill the pool;
- feedback/rights fields cannot be produced from actually executed history;
- model/runtime/tool/checker identity differs from the frozen bundle;
- raw capture cannot guarantee request-response correspondence;
- exact window or budget accounting is not bound.

Normal model errors and failed corrections do not top up the sample. Infrastructure/raw/parse-chain failures stop the collection and preserve all evidence.

## 7. Final disposition

- Collection request: **conditionally worth approving only with a future evaluation source/scope decision**.
- Immediate execution: **not authorized**.
- Pilot: **not authorized**.
- G-M: `HOLD / NOT_IDENTIFIED`.
- Scientific conclusion: `NONE`.
