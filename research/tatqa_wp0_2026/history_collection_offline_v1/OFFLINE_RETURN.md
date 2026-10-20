# HISTORY_COLLECTION_OFFLINE_v1 RETURN

> Status: `OFFLINE_IMPLEMENTATION_PASS / REVISED_SPLIT_ACCEPTED / OWNER_REVIEW_READY / ONLINE_COLLECTION_NOT_AUTHORIZED`
> Cost: model 0, endpoint 0, judge 0, training 0, service starts 0.

## 1. Exposure correction

The previous `0 future tasks` interpretation is retracted. TQ-5 exclusion-list membership is a conservative TQ-5 isolation policy, not proof of model, diagnostic, or prompt exposure.

The new audit separates:

| exposure layer | UID count | new-test interpretation |
|---|---:|---|
| `STRUCTURAL_SCAN_ONLY` | 2,246 | low-exposure category, but contributes 0 tasks under the current two-period/unit contract |
| `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` | 170 | separate review required; not automatically excluded |
| `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` | 42 | exclude from new test |
| `MODEL_OR_FEEDBACK_EXPOSURE` | 21 | exclude from new test |
| `EXPOSURE_UNKNOWN` | 0 | would be excluded until resolved |

The layer counts sum to all 2,479 raw records. `STRUCTURAL_SCAN_ONLY` means recorded deterministic processing only; it is not a claim that no unrecorded historical access can ever exist.

## 2. Full source-association audit

- Raw records: 2,479.
- Conservative association edges: 39.
- Source-association clusters: 2,443.
- Report identity: unavailable in raw schema; no report-level independence claim is made.
- Normalization preserves minus signs, decimal points, digits, and punctuation.
- Table/paragraph/report reasons are retained separately.
- Table-reuse/paragraph-divergence and paragraph-reuse/table-divergence conflicts conservatively merge or isolate.

Frozen association thresholds:

- table near duplicate `>=0.95`;
- paragraph near duplicate `>=0.90`;
- joint near duplicate `table>=0.85 and paragraph>=0.75`;
- table-reuse conflict `table>=0.95 and paragraph<0.50`.
- paragraph-reuse conflict `paragraph>=0.90 and table<0.50`.

## 3. Task and split availability

- Contract-valid tasks: 1,149.
- Eligible clusters with at least two contract-valid tasks: 177.
- Eligible cluster distribution:
  - 165 `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW`;
  - 10 `METHOD_DEVELOPMENT_OR_DIAGNOSTIC`;
  - 2 `MODEL_OR_FEEDBACK_EXPOSURE`.
- Initial unfiltered proposal: 8 future clusters, of which Loop C found 5 clean, 2 `EXPOSURE_UNKNOWN`, and 1 model/effect-exposure contaminated.
- Program-reference review r1 initially found 158 `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`, 2 `EXPOSURE_UNKNOWN`, and 5 `MODEL_OR_FEEDBACK_EXPOSURE`.
- Split re-audit r2 found the WP2 dry-run role boundary was applied only to original future members. Revision 3 consistently holds all 19 WP2-designated pending clusters as `EXPOSURE_UNKNOWN`, leaving 141 clean, 19 unknown, and 5 exposed.
- Revised deterministic proposal after applying that qualification filter: 8 clean future, 2 clean development, 131 clean reserve, and 24 excluded pending-review clusters.
- Revised future clusters: `cluster_1340`, `cluster_0306`, `cluster_0615`, `cluster_0978`, `cluster_1724`, `cluster_1628`, `cluster_2060`, `cluster_1642`.
- Revised development clusters: `cluster_2010`, `cluster_2096`.
- All 24 excluded pending-review clusters are preserved with their effective category and evidence in `SPLIT_PROPOSAL.json`; none is silently dropped or replaced by threshold tuning.
- History clusters are the same 12 model/diagnostic-exposed clusters, materialized explicitly in `SPLIT_PROPOSAL.json`: `cluster_0482`, `cluster_0548`, `cluster_0810`, `cluster_0893`, `cluster_0943`, `cluster_1052`, `cluster_1443`, `cluster_1737`, `cluster_1744`, `cluster_1816`, `cluster_1978`, `cluster_2147`.
- The 12 history clusters are therefore not an additional group separate from the 12 excluded future clusters; they are those same exposed clusters reserved for new history collection.

The source pool contains enough positively qualified clusters for a future set of 8. Revision 3 passed the delta re-audit and can be frozen for owner collection review. Most eligible clusters are singleton source records; `STRUCTURAL_SCAN_ONLY` contributes zero current-contract tasks.

1. keep the accepted revision 3 split immutable during any later collection application;
2. keep future test content out of experience selection and qualification;
3. retain the wording `developmental evaluation set qualified by scanning and isolated from this history/development material`.

The conservative WP2 designation boundary remains scientifically unresolved; revision 3 accepts the conservative reading consistently and does not claim those designations were actual exposures. MultiHiertt bulk acquisition and SEC EDGAR acquisition are not authorized.

## 4. Offline software qualification

Implemented under `history_collection_offline_v1/`:

- conservative source-cluster builder;
- evidence-layered exposure classifier;
- deterministic task/reference checker;
- plan -> actual calculator -> consume chain;
- unique request IDs and atomic raw response capture;
- overwrite refusal and crash markers;
- hard request/token budget stops;
- synthetic fixtures and regression tests.

Verification:

- Local tests: 14/14 PASS (`host_label=LOCAL_WINDOWS`).
- GB10 tests: 14/14 PASS (`host_label=GB10`, Python 3.12.3, Linux aarch64).
- Local receipt: `tests/TEST_RECEIPT.json`.
- GB10 receipt: `tests/TEST_RECEIPT_GB10.json`.
- Real audit output: `EXPOSURE_AND_SPLIT_AUDIT.json`.
- Full cluster graph: `SOURCE_CLUSTERS.json`.

This is `SOFTWARE_PASS` for the offline contract only. It is not online tool-chain qualification and not a scientific result.

Independent review status:

- First Loop C audit: `CONDITIONAL`; D1-D9 identified.
- Focused re-audit r2: `CONDITIONAL`; all D1-D9 repairs closed and verified, with D10/D12 closed.
- r2 residual N-2 is fixed: `(−N)` / `(-N)` remain negative instead of being double-inverted by the accounting-parentheses rule.
- r2 residual N-1 is fixed: model-exposure UIDs now carry a detailed provenance map distinguishing direct selection/prompt evidence from deterministic content mapping.
- Final focused re-audit r3: `ACCEPTED`; N-1/N-2 are closed.
- Program-reference exposure review r1: `CONDITIONAL`; the unfiltered future 8 is rejected.
- Revised split focused review r2: `CONDITIONAL`; reselection mechanics pass, while N-1 requires consistent treatment of WP2 dry-run role designations.
- Revision 3 delta review: `ACCEPTED`; split N-1 is closed and revision 3 can be frozen for owner collection review.
- Delta D-2 is fixed by explicit LF JSON output; D-4 is closed by storing revision 2's development pair. D-1 and D-3 remain disclosed notes.
- The current package proceeds to owner review with software N-1/N-2 and split N-1 resolved; online collection remains unauthorized.

## 5. Collection decision

**Online collection remains `NOT_AUTHORIZED`.**

Before requesting collection, freeze or bind:

1. source clusters and the 233-UID non-structural exposure register;
2. the delta-review-accepted 12 history and 8 future clusters;
3. task/reference/checker versions;
4. model, tokenizer, chat template, service binary and generation parameters;
5. runner, adapter, calculator, schema, prompt templates and raw-capture implementation;
6. budget ledger, stop rules, fixture receipts and independent software review.

The next request is for one new collection only. It must not bundle the 160-request pilot. The source/exposure side is qualified for owner review after revision, but the remaining task/runtime/execution-chain hashes and Beijing window are still open.

## 6. Boundaries

- Old WP-2 trajectories remain prohibited from E/U experience contexts.
- Old panels and frozen materials remain unchanged.
- No online probe, collection, pilot, training, memory write-back, source switch, or public release occurred.
- AI software review is not human semantic gold.
- G-M remains `HOLD / NOT_IDENTIFIED`.
- The first Loop C audit is preserved as `LOOP_C_EXPOSURE_AND_SOFTWARE_AUDIT.md` with verdict `CONDITIONAL`; its D1-D9 repairs were independently re-audited and closed before the final `ACCEPTED` r3 review.
