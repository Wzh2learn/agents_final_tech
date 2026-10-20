# Loop C Independent Program-Reference Exposure Review

- **Task id:** `history-program-exposure-review-20261018-r1`
- **Role:** Loop C independent reviewer (bounded read-only evidence audit)
- **Review date:** 2026-10-18
- **Scope:** the 165 proposed future/development/reserve source clusters carrying `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW`
- **Decision object:** `research/tatqa_wp0_2026/history_collection_offline_v1/EXPOSURE_AND_SPLIT_AUDIT.json` + `SPLIT_PROPOSAL.json`
- **Verdict:** `CONDITIONAL`

This review qualifies **access/exposure evidence and task-contract eligibility only**. It is an AI evidence review.
It is **not human semantic gold**, and it **does not authorize online collection**.

---

## 0. Verdict

`CONDITIONAL`

Rationale in one line: 5 of the 8 proposed future clusters are positively supported as non-exposed and contract-valid;
1 is positively exposed and must be excluded; 2 sit on an unresolved designation boundary and are held as `EXPOSURE_UNKNOWN`.
The conservative qualified future count is **5**, which is below the required 8, so the future pool is not yet qualified.

---

## 1. Recomputed source and split counts

All headline figures were recomputed mechanically from the JSON before any other work. **No mismatch was found** against the figures in the task description.

| Claim in task description | Recomputed from JSON | Match |
|---|---|---|
| 165 clusters in `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` with >=2 contract-valid tasks | 170 cluster rows carry the category; 165 of them have `contract_task_count >= 2` | yes |
| proposed groups 8 future / 2 development / 155 reserve | `SPLIT_PROPOSAL.json` `future_test`=8, `development`=2, `reserve`=155; 8+2+155=165 | yes |
| 170 UIDs classified `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` | member-level count = 170; distinct UIDs in those 170 rows = 171 (see note) | yes at UID level |
| 233-UID non-structural exposure register | `uid_count`=233, `len(uids)`=233, all distinct | yes |
| register canonical hash `d6c37842dd6ebb1f8d512ca0ad3f0f94a1a6ba5e39c8fbeefe4b16c710724070` | sha256 of `json.dumps(sorted(uids), separators=(",", ":"))` reproduces the value exactly | yes |

**Note on 170 vs 171.** The category is assigned per member UID, then a cluster takes the max-ranked member category.
`cluster_1973` has two members: `cdbfc2e3-1082-4a25-9324-2f0ba9e684e5` (`PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW`, 3 contract tasks)
and `e8438d76-0352-403f-8393-7532cade7715` (`STRUCTURAL_SCAN_ONLY`, 0 contract tasks).
So 170 rows contain 171 distinct UIDs, of which exactly 170 carry the pending category. The task description's "170 UIDs" is correct at UID level.

Supporting counts also recomputed and internally consistent:

- `raw_records` = 2479; `clusters` = 2443; `eligible_clusters_with_ge2_tasks` = 177; `contract_tasks` = 1149.
- UID-level `category_counts_by_uid`: STRUCTURAL_SCAN_ONLY 2246, PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW 170, METHOD_DEVELOPMENT_OR_DIAGNOSTIC 42, MODEL_OR_FEEDBACK_EXPOSURE 21. Sum = 2479.
- `non_structural_exposure_register` = 170 + 42 + 21 = 233. Register hash recomputed and matched.
- `tasks_by_exposure_category`: pending 1071, method-dev 60, model/feedback 18, structural **0**. Sum = 1149.
- `eligible_clusters_by_exposure_category`: pending 165, method-dev 10, model/feedback 2. Sum = 177.
- `history_cluster_ids` (12) is set-identical to `SPLIT_PROPOSAL.json.history`, and to `excluded_future_clusters`.

Group disjointness and contract validity (all verified, all pass):

- every one of the 165 future/development/reserve clusters has `contract_task_count >= 2` and every pending member is `task_eligible: true` (0 failures);
- future / development / reserve / history are pairwise disjoint (0 overlaps; union 177 = 165 + 12);
- `future_test` + `development` + `reserve` is set-identical to the 165 eligible pending clusters.

---

## 2. How `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` is assigned

Traced in `exposure_classifier.py` and `build_exposure_and_split_audit.py`.

`build_evidence_sets()` builds four UID sets:

- `generated` = UIDs in `tq5_source_validation_v1/source_refs/origin_manifest.json.origins` union the `origin_id` values of `candidate_items_v2.json` items with the `tatqa_` prefix stripped.
- `diagnostic` = UIDs in `coordinator/pool_inventory.json` union `coordinator/case_provenance.json`.
- `model` = UIDs in `tq4_calibration_v1/panel_v2/natural/SELECTION_LOG.json.selected` union `tq5_source_validation_v1/panel/SELECTION_LOG.json.selected` union five hardcoded UIDs (three TQ-4 content-mapped, two WP2 opaque-mapped).
- `structural` = the entire raw UID set.

`classify_uid()` ranks `model` > `diagnostic` > `generated` > `structural` (RANK 4/3/2/1) and assigns the first matching set.
A UID is `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` exactly when it is in `generated` and in neither `model` nor `diagnostic`.

`build_exposure_and_split_audit.py` then marks a cluster eligible at `contract_task_count >= 2` and buckets
eligible pending clusters as `pending_program_review_future_clusters`.

**Structural property worth recording.** Because `structural = set(raw_uids)` covers every raw record, the `EXPOSURE_UNKNOWN` branch of
`classify_uid()` is unreachable for any UID present in the raw corpus. The classifier as written cannot emit `EXPOSURE_UNKNOWN`.
Therefore the absence of `EXPOSURE_UNKNOWN` in `EXPOSURE_AND_SPLIT_AUDIT.json` is **not** evidence that no unknown-exposure cases exist.
This review applies `EXPOSURE_UNKNOWN` manually.

**Scope limit of the classifier.** The classifier only consults TQ-4, TQ-5 and `coordinator` evidence. It does not consult
Stage-E multileaf artifacts, positive-repair (PR-EXP) artifacts, WP2 dry-run role assignments, or WP2 actor run artifacts
beyond the two hardcoded WP2 UIDs. Sections 4-5 show this gap is material.

---

## 3. Pinned candidate task/reference source and its consumers

Source identity (hashes as recorded in `EXPOSURE_AND_SPLIT_AUDIT.json.source_identity`):

- `data/research/tatqa_raw_2026/tatqa_dataset_train.json` sha256 `2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69`
- `data/research/tatqa_raw_2026/tatqa_dataset_dev.json` sha256 `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`
- `data/research/tatqa_wp0_2026/candidate_items_v2.json` sha256 `5f61f2a476c220f4ed4c159030490c6dfaabcea9778820abc89d3bed859738aa`

Artifacts that **contain generated tasks/references**:

| Artifact | What it holds | Process cost evidence |
|---|---|---|
| `data/research/tatqa_wp0_2026/origin_manifest.json` | 182 origins (UID + period/unit/usable_rows) | deterministic (`build_origins.py`) |
| `data/research/tatqa_wp0_2026/candidate_items_v1.json` | 60 candidate items | deterministic; `GENERATION_RECEIPT.json` |
| `data/research/tatqa_wp0_2026/candidate_items_v2.json` | 352 items over 176 origins, gold recomputed from table cells | deterministic; schema note: "not a model output or dataset annotation" |
| `data/research/drift_v0/input/tatqa_tables.json` + `output/injected_tables.json` | full-corpus 2479 tables; 95 tables / 118 deterministic injections | `output/report.json` seed 42, `determinism_sha256` recorded |
| `research/positive_repair_20261011/runs/PR-EXP-03*/p1_run1.jsonl`, `p1_run2.jsonl` | 2431 baseline/injected table pairs | `receipt.json.cost`: model_calls 0, judge_calls 0, network_calls 0; `p1_generation_manifest.json` `double_run_byte_identical: true` |

Workflows that **later read** those artifacts:

| Consumer | Reads | Cost evidence | Nature |
|---|---|---|---|
| `wp2/build_items_v2.py` -> `ITEMS_V2_RECEIPT.json` | origin_manifest, raw | deterministic | generation |
| `wp2/split_rerun_v1.py` -> `SPLIT_RERUN_RECEIPT.json`, `WP2_SPLIT_DRYRUN_RECEIPT.json` | origin_manifest | deterministic; role rule `sha256(seed:origin_id)`, content-blind | selection |
| `wp2/check_pilot_eligibility.py` -> `PILOT_ELIGIBILITY_RECEIPT.json` | candidate_items_v2 | `decision_boundary`: model_calls 0, judge_calls 0, endpoint_calls 0, `pilot_eligibility_only: true` | deterministic qualification |
| `wp2/run_wp2_episode_collection*.py` + `bridge_v2/` -> `s4b_run/`, `s4c_qual_run/` | candidate items via prompts | `ACTOR_ARTIFACT_VERIFICATION_RECEIPT.json`: actor `Qwen/Qwen3-8B`, real `prompt.txt` / `raw_response.txt` | **model request/response** |
| `stage_e_multileaf_20261010/run_multileaf_formal.py` -> `results/*` | `multileaf_preresult_sample_manifest.json` substrates | no model-call markers in runner; `multileaf_run_receipt.json` | **effect analysis** |
| `positive_repair_20261011/runs/PR-EXP-03/experiment.py` | multileaf freeze + p1_run corpus | `receipt.json.cost.model_calls = 0` | method-development analysis |
| TQ-3/TQ-4/TQ-5 `runs/*/request_ledger.jsonl` | TQ panel inputs | real request ledgers | **model request/response** |

---

## 4. Evidence search actually performed

Mechanical checks run (commands are reproduced in section 8):

1. Full literal-UID sweep of `research/` and `data/` for all 170 pending UIDs (`grep -r -o -E` over the UUID union), producing a UID -> artifact-path map.
2. Content mapping of **every** WP2 actor `prompt.txt` (7 files under `s4b_run/` and `s4c_qual_run/`) back to raw UIDs by table signature (third table row tuple).
3. Content mapping of TQ-4 `panel_v2/**` and TQ-5 `panel/**` JSON artifacts back to raw UIDs by table signature, plus literal-UID extraction.
4. Opaque-identifier sweep for `origin_` hex tokens across `research/` and `data/`.
5. Membership tests against bounded manifests: multileaf sample manifest (216 rows / stages M,N,R), WP2 dry-run roles (22 origins), drift injection map (118 entries / 95 UIDs), coordinator diagnostic sets, TQ-4/TQ-5 selection logs.
6. Cost/model-call inspection of the receipts of every candidate consuming workflow.

**Bounding manifests used as positive evidence of non-entry** (this is why non-exposure below is asserted positively rather than from absence of logs):

- WP2 actor population is **fully enumerated**: 7 `prompt.txt` across 8 attempt directories, all content-mapped. They map to exactly **two** raw UIDs: `3ab739eb-c0d7-44f5-9377-b8a02bafb361` and `97176853-a81e-422a-a8c1-e0542348d051`.
- Stage-E multileaf effect-analysis population is **fully enumerated**: 216 rows in `multileaf_preresult_sample_manifest.json`, 48 distinct TAT-QA `source_uid` values at stages M and N; R-stage clusters carry `source_uid: null` (opaque documents).
- TQ-4/TQ-5 model-selection population is **fully enumerated**: `SELECTION_LOG.json.selected` in both trees, plus panel input files content-mapped.
- WP2 role-assignment population is **fully enumerated**: 22 origins in `WP2_SPLIT_DRYRUN_RECEIPT.json.roles`, rule is content-blind `sha256(seed:origin_id)`.
- Drift injection population is **fully enumerated**: `injection_map.json.mapping`, 118 entries over 95 UIDs.

Opaque-ID mapping result: only two opaque identifiers exist in the bounded evidence, `origin_fbb782143f9a` and `origin_5c4e334806b6`,
in `wp2/S4B_BRIDGE_PROTOCOL_RECEIPT.json` / `S4B_BRIDGE_PROBE_RECEIPT.json`. They map to `3ab739eb-...` and `97176853-...` respectively,
both already `MODEL_OR_FEEDBACK_EXPOSURE`. **No future-8 UID is reachable through an opaque-ID mapping.**

The `diagnostic` evidence the classifier does read (`coordinator/pool_inventory.json` 59 rows, `case_provenance.json` 12 rows, 50 distinct UIDs)
contains **no** future-8 UID.

---

## 5. Special findings for the 8 proposed future clusters

| cluster | UID | contract tasks | proposed group | category assigned here | decisive evidence |
|---|---|---|---|---|---|
| `cluster_0306` | `20a028a0-5e02-4df0-99ba-ed59ab345e5a` | 9 | future_test | **PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE** | candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic |
| `cluster_0584` | `3e4f4b3e-0aa6-4e5f-9103-5f1155d27e75` | 11 | future_test | **EXPOSURE_UNKNOWN** | WP2 dryrun role `pilot_reserve`; designation-to-prompt pathway demonstrated in same pipeline; no past prompt hit |
| `cluster_0599` | `403e498a-59a2-4d4f-b560-a7ca853d6dc2` | 9 | future_test | **MODEL_OR_FEEDBACK_EXPOSURE** | multileaf M/N substrate; effect analysis at `results/multileaf_prediction_rows.jsonl`, `multileaf_paired_artifacts.jsonl`, `multileaf_formal_results.json` |
| `cluster_0615` | `41b215e5-024b-478e-bc05-5804ad02169a` | 5 | future_test | **PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE** | candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic |
| `cluster_0978` | `66b7c6dd-a4fc-48db-a226-6ecbb174aa77` | 2 | future_test | **PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE** | candidate_items_v1+v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic |
| `cluster_1340` | `8cbf706f-066a-46a3-a6aa-e5b1df0facd1` | 6 | future_test | **PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE** | candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic |
| `cluster_1360` | `8df5c241-c68c-427a-99af-30c44214199b` | 6 | future_test | **EXPOSURE_UNKNOWN** | WP2 dryrun role `pilot_reserve`; designation-to-prompt pathway demonstrated in same pipeline; no past prompt hit |
| `cluster_1724` | `b4129e1f-efcb-4157-9996-5389b83de63e` | 4 | future_test | **PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE** | candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic |

### 5.1 `cluster_0599` is positively exposed and must be excluded

UID `403e498a-59a2-4d4f-b560-a7ca853d6dc2` is one of the 48 M/N-stage `source_uid` values in
`research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json` (sample ids `N-403e498a-...-r8c1-1`, `-r7c3-2`, `-r8c2-3`).
Its table content was mutated as a controlled numeric-reconciliation injection
(`injection_operation: mutate_one_numeric_operand_while_preserving_labels_schema_and_identity_contract`,
`identity_expression: r6c1 + r7c1 + r8c1 + r9c1 = r10c1`) and then subjected to per-sample effect analysis:

- `results/multileaf_prediction_rows.jsonl` (216 rows: `predicted_stage`, `true_stage`, `correct`, `distance_margin`, full `response_vector` over 12 measurement leaves);
- `results/multileaf_paired_artifacts.jsonl` (`baseline_scores`, `injected_scores`, `contract_checks`, `response_vector`);
- `results/multileaf_formal_results.json` (confusion matrix, per-stage profiles, leakage audit), `multileaf_signature_ablation.json`, `multileaf_permutation_null.json`, `multileaf_bootstrap_intervals.json`;
- `results/independent_contract_audit.json` (per-sample pass/fail on the mutated identity).

Its UID also appears verbatim in method-development material: `runs/PR-EXP-03/implementation_contract.md`
("Verbatim M/N UID exclusion extraction command", 48-UID registry) and `loop_c_postaudit_PR-EXP-03.md`,
plus `research/stage_e_method_revision_20261009/multileaf_freeze.json` (9 occurrences),
`multileaf_preresult_sample_manifest.json` (9), `results/independent_contract_audit.json` (3) and
`research/causal_checkpoint_selection_mvp_20261011/smoke/dev_smoke_result.json`.

This is effect analysis of the content, which the evidence standard places in `MODEL_OR_FEEDBACK_EXPOSURE`, and independently
method-development/diagnostic use. Either reading excludes it from a new test. **`cluster_0599` is excluded.**

### 5.2 `cluster_0584` and `cluster_1360` are held `EXPOSURE_UNKNOWN`

UIDs `3e4f4b3e-0aa6-4e5f-9103-5f1155d27e75` and `8df5c241-c68c-427a-99af-30c44214199b` are `pilot_reserve` origins in
`data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json` (and the copies under `wp2/` and `tq5_source_validation_v1/source_refs/`),
and appear in `wp2/ITEMS_V2_RECEIPT.json`, `wp2/SPLIT_RERUN_RECEIPT.json` and `wp2/PILOT_ELIGIBILITY_RECEIPT.json`.

What is established positively:

- the role rule is content-blind (`sha256(seed:origin_id) ascending`), so content did not influence their selection;
- `PILOT_ELIGIBILITY_RECEIPT.json.decision_boundary` records model_calls 0 / judge_calls 0 / endpoint_calls 0, `pilot_eligibility_only: true`, `role_assignments_changed: false`;
- neither UID appears in any WP2 actor prompt (all 7 prompts content-mapped), nor in multileaf manifests, nor in TQ-4/TQ-5 panels, nor in `coordinator` diagnostic sets.

What is not established: in this same WP2 pipeline, role designation was followed by content consumption -- the `history`-role origins
`3ab739eb-...` and `97176853-...` were designated and then their table content entered real `Qwen/Qwen3-8B` prompts in `s4b_run/`.
These two clusters are therefore designated for imminent model consumption via a pathway this pipeline demonstrably executes.
Past use is not observed, but "designated and not yet used" is exactly the ambiguous case the standard reserves for `EXPOSURE_UNKNOWN`.
They are held **`EXPOSURE_UNKNOWN`** and excluded until resolved.

If a later reviewer establishes that WP2 role designation is strictly non-consuming and content-blind end to end, these two would move to
`PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE` and the conservative future count would rise from 5 to 7 -- still below 8.

### 5.3 The other five proposed future clusters are positively supported

`cluster_0306`, `cluster_0615`, `cluster_0978`, `cluster_1340`, `cluster_1724` have the clean profile:

- generated by bounded deterministic processes (`candidate_items_v2.json`, `origin_manifest.json`; `cluster_0978` also in `candidate_items_v1.json`);
- present in full-corpus structural/deterministic artifacts only (`drift_v0/input|output/tatqa_tables.json` pass-through, `PR-EXP-03 p1_run*.jsonl` full-corpus deterministic material);
- **not** in `drift_v0/output/injection_map.json` (their content was never mutated);
- **not** in any WP2 actor prompt (content-mapped), **not** in multileaf effect analysis, **not** in TQ-4/TQ-5 panels or selection logs, **not** in `coordinator` diagnostic sets, **not** in WP2 dry-run roles.

Each has `contract_task_count` >= 2 (9, 5, 2, 6, 4 respectively) and each pending member is `task_eligible: true`.
Category: `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`.

---

## 6. Excluded clusters and exact reasons

### 6.1 Excluded from the proposed future pool

| cluster | UID | reason |
|---|---|---|
| `cluster_0599` | `403e498a-59a2-4d4f-b560-a7ca853d6dc2` | `MODEL_OR_FEEDBACK_EXPOSURE` (effect analysis). Content was an M/N controlled-injection substrate in Stage-E multileaf; per-sample effect results in `multileaf_prediction_rows.jsonl` / `multileaf_paired_artifacts.jsonl` / `multileaf_formal_results.json`; UID named in PR-EXP-03 method-development contract and post-audit. |
| `cluster_0584` | `3e4f4b3e-0aa6-4e5f-9103-5f1155d27e75` | `EXPOSURE_UNKNOWN`. WP2 `pilot_reserve` designation with a demonstrated designation-to-prompt consumption pathway in the same pipeline; past prompt use not observed but boundary unresolved. |
| `cluster_1360` | `8df5c241-c68c-427a-99af-30c44214199b` | `EXPOSURE_UNKNOWN`. Same as `cluster_0584`. |

### 6.2 Excluded clusters elsewhere in the 165

`MODEL_OR_FEEDBACK_EXPOSURE` (effect analysis, Stage-E multileaf M/N substrates) -- 4 reserve clusters:

| cluster | UID | contract tasks | reason |
|---|---|---|---|
| `cluster_0789` | `538ada9e-1c28-447d-9ff7-b12995c2432d` | 6 | multileaf M/N injection substrate; per-sample effect analysis as in 5.1 |
| `cluster_0890` | `5e2b5b29-e0c9-4abb-935e-a3fc13d18285` | 7 | multileaf M/N injection substrate; per-sample effect analysis as in 5.1 |
| `cluster_0903` | `5f46a008-12b7-4c0d-b9e5-4b8e31cb0ba8` | 15 | multileaf M/N injection substrate; per-sample effect analysis as in 5.1 |
| `cluster_2344` | `f5511f3c-b02d-4142-aa16-0b87cd61690f` | 5 | multileaf M/N injection substrate; per-sample effect analysis as in 5.1 |

No development cluster is excluded. Both `cluster_1628` and `cluster_2060` are `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`.

### 6.3 Clusters outside the 165 (context only)

The 12 `history` clusters are already `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` (10) or `MODEL_OR_FEEDBACK_EXPOSURE` (2) in the audit and are
excluded by the audit itself. This review did not re-adjudicate them. Five pending rows with `contract_task_count < 2`
(`cluster_0055`, `cluster_1649`, `cluster_1683`, `cluster_1796`, `cluster_2298`) are not in the 165 and were not adjudicated for split placement.

---

## 7. Complete per-cluster appendix (all 165)

Machine-readable-style listing. Every future/development/reserve cluster appears exactly once, with every pending member UID,
its category under this review, and the evidence path supporting that category.

```
cluster_id=cluster_0002 | group=reserve | cluster_contract_tasks=4 | uid=0012a118-070e-43bf-a23c-19fe94cee4e9 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0003 | group=reserve | cluster_contract_tasks=5 | uid=001781c6-0e17-4fdd-b000-011e3ed66d6e | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0013 | group=reserve | cluster_contract_tasks=5 | uid=008eaf4e-4d70-496b-aa25-b842b05a3560 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_0022 | group=reserve | cluster_contract_tasks=4 | uid=0131320a-1ed4-470e-90f8-7a68e9c8c766 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0030 | group=reserve | cluster_contract_tasks=4 | uid=02a7787e-92f9-4a5a-9f95-c4c9ed0f7eff | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0090 | group=reserve | cluster_contract_tasks=10 | uid=0992660b-76ed-46a1-92eb-e91977f6f381 | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0093 | group=reserve | cluster_contract_tasks=7 | uid=09dfce79-6163-42a4-8fe6-a2eaf20c1435 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0117 | group=reserve | cluster_contract_tasks=4 | uid=0bf3d7a7-f26b-497b-babe-b2361f84f6fb | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0154 | group=reserve | cluster_contract_tasks=4 | uid=0f69ef4a-6d23-4e5e-9781-dbd44d5b99a0 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0172 | group=reserve | cluster_contract_tasks=7 | uid=10e46d24-413a-4fd1-9e96-56da277f6ba9 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0179 | group=reserve | cluster_contract_tasks=5 | uid=11ae619c-285a-4b82-854d-2bfd5d7ec141 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0193 | group=reserve | cluster_contract_tasks=15 | uid=13bb283b-4b9c-42b9-9b02-f1b2e1a87abf | uid_contract_tasks=15 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0211 | group=reserve | cluster_contract_tasks=14 | uid=163c5d6d-e301-4464-a640-8fdd33a8fa18 | uid_contract_tasks=14 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0239 | group=reserve | cluster_contract_tasks=3 | uid=195383eb-3e09-4aa3-9f60-89fcc4d7ed61 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0257 | group=reserve | cluster_contract_tasks=2 | uid=1b2ca134-09ae-4936-bc3d-453699823f6e | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0261 | group=reserve | cluster_contract_tasks=2 | uid=1b90541f-9a34-43a2-8fab-ebd84d49dbe0 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0299 | group=reserve | cluster_contract_tasks=3 | uid=1fee6a61-d243-4e8d-b8e1-f5662f104eb5 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0306 | group=future_test | cluster_contract_tasks=9 | uid=20a028a0-5e02-4df0-99ba-ed59ab345e5a | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0347 | group=reserve | cluster_contract_tasks=7 | uid=24198a1c-0f45-4c32-92ba-98c6cfde01fe | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0356 | group=reserve | cluster_contract_tasks=3 | uid=24ff90f9-79ee-4e0e-a1ec-1d94abe7bc8b | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0376 | group=reserve | cluster_contract_tasks=3 | uid=276d4eff-6476-4a1a-9e2c-188a80d79445 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0379 | group=reserve | cluster_contract_tasks=3 | uid=27c6ed38-b840-4835-935e-731a52d7b983 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0388 | group=reserve | cluster_contract_tasks=21 | uid=2889dd15-8bc7-48bd-aa31-dcc40efd67f7 | uid_contract_tasks=21 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0402 | group=reserve | cluster_contract_tasks=8 | uid=2975881e-3e71-435b-8500-56d668a50eb2 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0424 | group=reserve | cluster_contract_tasks=3 | uid=2bcc60e7-139f-43ee-9c91-dd58f868b113 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0458 | group=reserve | cluster_contract_tasks=5 | uid=2ff661fc-b6cc-4b50-ad7b-f1cbadd003d0 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0472 | group=reserve | cluster_contract_tasks=6 | uid=31b59507-dcb1-41cf-8752-e2bb17dd62db | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0480 | group=reserve | cluster_contract_tasks=9 | uid=32c45a53-b1b5-46b6-a519-8f7bbbddf93f | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0489 | group=reserve | cluster_contract_tasks=5 | uid=334d9b85-ec0c-4783-81d7-64259a410b16 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_0584 | group=future_test | cluster_contract_tasks=11 | uid=3e4f4b3e-0aa6-4e5f-9103-5f1155d27e75 | uid_contract_tasks=11 | category=EXPOSURE_UNKNOWN | evidence=WP2 dryrun role pilot_reserve (data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json); designation->prompt pathway demonstrated in same pipeline; no past prompt hit
cluster_id=cluster_0599 | group=future_test | cluster_contract_tasks=9 | uid=403e498a-59a2-4d4f-b560-a7ca853d6dc2 | uid_contract_tasks=9 | category=MODEL_OR_FEEDBACK_EXPOSURE | evidence=multileaf M/N substrate; effect analysis at research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl, multileaf_paired_artifacts.jsonl, multileaf_formal_results.json
cluster_id=cluster_0604 | group=reserve | cluster_contract_tasks=2 | uid=40a7da40-c983-486f-9c32-8a3559c757c6 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0615 | group=future_test | cluster_contract_tasks=5 | uid=41b215e5-024b-478e-bc05-5804ad02169a | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0629 | group=reserve | cluster_contract_tasks=3 | uid=43155e3f-2a04-47a3-8dee-0f8c63e028f1 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0647 | group=reserve | cluster_contract_tasks=7 | uid=4565ded8-5e2e-4cd7-beab-6da622434396 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role development (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_0654 | group=reserve | cluster_contract_tasks=9 | uid=460b737c-4b0c-4c5a-8f73-e5b3b8d42cec | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0664 | group=reserve | cluster_contract_tasks=5 | uid=46557a47-26a7-45f2-901d-3398aa4aabdb | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0673 | group=reserve | cluster_contract_tasks=4 | uid=4742afee-a8aa-456b-85ed-446f8fa8fe36 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0689 | group=reserve | cluster_contract_tasks=15 | uid=48eb64be-428f-429d-afd5-39cdbc4e4dde | uid_contract_tasks=15 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_0731 | group=reserve | cluster_contract_tasks=8 | uid=4ebf4ce6-2e2d-4146-850d-8c5450961dcc | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0734 | group=reserve | cluster_contract_tasks=10 | uid=4ecbff45-a2f1-42dd-ae23-491846321001 | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0772 | group=reserve | cluster_contract_tasks=2 | uid=51c8eba0-1876-42aa-afdb-d18741b2fe7b | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot_reserve (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_0777 | group=reserve | cluster_contract_tasks=7 | uid=5214bc24-1d07-42be-9b21-54d688d06c4c | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0781 | group=reserve | cluster_contract_tasks=5 | uid=52cebcac-ee1d-47e4-ba64-5fb783a58a5b | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0783 | group=reserve | cluster_contract_tasks=9 | uid=52d79de5-c56a-4c91-b47d-58fb05a109bf | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0784 | group=reserve | cluster_contract_tasks=4 | uid=532c14a5-b085-4383-9f4e-76b75969629e | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0789 | group=reserve | cluster_contract_tasks=6 | uid=538ada9e-1c28-447d-9ff7-b12995c2432d | uid_contract_tasks=6 | category=MODEL_OR_FEEDBACK_EXPOSURE | evidence=multileaf M/N substrate; effect analysis at research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl, multileaf_paired_artifacts.jsonl, multileaf_formal_results.json
cluster_id=cluster_0791 | group=reserve | cluster_contract_tasks=13 | uid=53eec737-630e-4915-afbb-8c20cdd01263 | uid_contract_tasks=13 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0840 | group=reserve | cluster_contract_tasks=8 | uid=58567520-c343-43fd-b803-bc078bb77c87 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0851 | group=reserve | cluster_contract_tasks=8 | uid=5999c164-eb8b-4eff-b432-bb688b8fa65f | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0875 | group=reserve | cluster_contract_tasks=10 | uid=5c088a56-074d-49d0-af03-68c2d6a4c346 | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0890 | group=reserve | cluster_contract_tasks=7 | uid=5e2b5b29-e0c9-4abb-935e-a3fc13d18285 | uid_contract_tasks=7 | category=MODEL_OR_FEEDBACK_EXPOSURE | evidence=multileaf M/N substrate; effect analysis at research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl, multileaf_paired_artifacts.jsonl, multileaf_formal_results.json
cluster_id=cluster_0895 | group=reserve | cluster_contract_tasks=5 | uid=5e94ca98-0b87-4ad5-a7ad-6bed5d3b4be2 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0903 | group=reserve | cluster_contract_tasks=15 | uid=5f46a008-12b7-4c0d-b9e5-4b8e31cb0ba8 | uid_contract_tasks=15 | category=MODEL_OR_FEEDBACK_EXPOSURE | evidence=multileaf M/N substrate; effect analysis at research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl, multileaf_paired_artifacts.jsonl, multileaf_formal_results.json
cluster_id=cluster_0916 | group=reserve | cluster_contract_tasks=5 | uid=6082d8ef-75ae-4c52-a26d-adc6f6ae58ac | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0921 | group=reserve | cluster_contract_tasks=2 | uid=61068531-0af5-41bd-b5ea-17bfb06c8358 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0923 | group=reserve | cluster_contract_tasks=9 | uid=610d99f0-250a-474a-b1bc-d791058d006c | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0931 | group=reserve | cluster_contract_tasks=8 | uid=62167bd9-5b0e-4942-bf9f-b19b1f1f284c | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0965 | group=reserve | cluster_contract_tasks=11 | uid=65cde743-18a6-418f-8f5a-000660a38cdf | uid_contract_tasks=11 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0970 | group=reserve | cluster_contract_tasks=6 | uid=66210694-acb9-4386-b71e-930cb2ba0da0 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0976 | group=reserve | cluster_contract_tasks=3 | uid=668a081b-e793-4d45-935d-816d2d7eba6d | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_0978 | group=future_test | cluster_contract_tasks=2 | uid=66b7c6dd-a4fc-48db-a226-6ecbb174aa77 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_0983 | group=reserve | cluster_contract_tasks=5 | uid=673707a3-c628-4ff7-be61-16ab9ff1eb7a | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1013 | group=reserve | cluster_contract_tasks=9 | uid=6aa15859-a841-47eb-ad04-a441599cf05c | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1014 | group=reserve | cluster_contract_tasks=4 | uid=6aae8dee-45af-4a09-9e09-8137d6eb3dc3 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1020 | group=reserve | cluster_contract_tasks=7 | uid=6b250bb5-2435-4e4a-b799-5bd331232a20 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1063 | group=reserve | cluster_contract_tasks=2 | uid=6f9e4e1d-c737-4a61-82e5-455457f37f40 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1097 | group=reserve | cluster_contract_tasks=2 | uid=72b79d03-72a0-42ec-8b86-eaec5b850e29 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1098 | group=reserve | cluster_contract_tasks=8 | uid=72bfa3fa-9acd-437f-b682-0199daed6aa7 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot_reserve (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_1105 | group=reserve | cluster_contract_tasks=3 | uid=735ba0a0-60c8-452f-96a2-c6fc50cce80d | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_1108 | group=reserve | cluster_contract_tasks=2 | uid=7378cf39-2abb-43cd-8b03-00ddc98f9fa5 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1118 | group=reserve | cluster_contract_tasks=6 | uid=74fd96c1-a5f0-42ea-b5ce-9fcf1b36d1d3 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1138 | group=reserve | cluster_contract_tasks=4 | uid=76ce05c3-8d33-4fd8-9c6e-73c9486a8a8d | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1142 | group=reserve | cluster_contract_tasks=2 | uid=77391fcc-be7b-4d28-81ab-072bc448c4e1 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1161 | group=reserve | cluster_contract_tasks=7 | uid=789bab55-3343-4512-b6b2-18ea66d8d79c | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1180 | group=reserve | cluster_contract_tasks=3 | uid=7ac100f5-8d0a-4fb1-ad1b-6e5eebb4d3fa | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1210 | group=reserve | cluster_contract_tasks=2 | uid=7f675606-2b0b-4ddf-9d0a-a46b3fb542c5 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1216 | group=reserve | cluster_contract_tasks=16 | uid=7ffd5216-30e1-4a4c-b548-b657d92df228 | uid_contract_tasks=16 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1222 | group=reserve | cluster_contract_tasks=2 | uid=805e19ed-e861-4da5-a412-3e8a85aff770 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1227 | group=reserve | cluster_contract_tasks=7 | uid=808ea5b8-f097-4094-a893-e3f4bbe56918 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1257 | group=reserve | cluster_contract_tasks=10 | uid=8363e1b1-8e3e-4009-8df4-24f591433791 | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1291 | group=reserve | cluster_contract_tasks=10 | uid=8749fc7b-19fb-4014-8eed-f96a05da50cf | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1300 | group=reserve | cluster_contract_tasks=3 | uid=88097457-b056-45fb-bb8d-9106df18df0d | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1323 | group=reserve | cluster_contract_tasks=10 | uid=8b2c7a63-0dc5-4a6f-83f1-6f9b27a8016c | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1340 | group=future_test | cluster_contract_tasks=6 | uid=8cbf706f-066a-46a3-a6aa-e5b1df0facd1 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1358 | group=reserve | cluster_contract_tasks=8 | uid=8dd62c68-2768-48e1-b28a-9c7169fff905 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1360 | group=future_test | cluster_contract_tasks=6 | uid=8df5c241-c68c-427a-99af-30c44214199b | uid_contract_tasks=6 | category=EXPOSURE_UNKNOWN | evidence=WP2 dryrun role pilot_reserve (data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json); designation->prompt pathway demonstrated in same pipeline; no past prompt hit
cluster_id=cluster_1361 | group=reserve | cluster_contract_tasks=4 | uid=8e0e12f7-ed7e-4a32-8a9e-7eeddc77f55d | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1366 | group=reserve | cluster_contract_tasks=7 | uid=8e9c46ac-9dd9-4436-9482-9a166d8ae6e8 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1369 | group=reserve | cluster_contract_tasks=4 | uid=8edfdb1c-3d22-496f-b6ba-f3ea45cf6151 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_1370 | group=reserve | cluster_contract_tasks=5 | uid=8ee550f6-e032-47dc-928b-078b62ee9aa1 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1448 | group=reserve | cluster_contract_tasks=4 | uid=97a0d99a-feef-41ed-baaa-960b59d23b89 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1451 | group=reserve | cluster_contract_tasks=6 | uid=97dfc73a-8916-4691-9eb9-87d3e258c8d1 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1458 | group=reserve | cluster_contract_tasks=5 | uid=988b4303-d440-4b20-97d9-40f6bb22c0ed | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1459 | group=reserve | cluster_contract_tasks=3 | uid=989a6b20-45e6-4430-9491-98c93361e184 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1471 | group=reserve | cluster_contract_tasks=15 | uid=9989ca79-5332-47be-a08e-85f2648cdde7 | uid_contract_tasks=15 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1473 | group=reserve | cluster_contract_tasks=10 | uid=99a0fe81-7855-45b6-b157-3f9439abf3ca | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1474 | group=reserve | cluster_contract_tasks=9 | uid=99a3fe4e-1302-42ff-b0ae-4bf7ef0b3934 | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role history (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_1476 | group=reserve | cluster_contract_tasks=3 | uid=99e73ea1-2dd6-478d-8fef-3a71122f6f83 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1479 | group=reserve | cluster_contract_tasks=12 | uid=9a214b31-4dad-417d-83aa-b54692b2a785 | uid_contract_tasks=12 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1487 | group=reserve | cluster_contract_tasks=3 | uid=9b0abd12-8d9e-48ba-9ac2-baacfa92e7eb | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1498 | group=reserve | cluster_contract_tasks=7 | uid=9c69cfbe-0c76-4cca-9eef-f41fee959c8a | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1502 | group=reserve | cluster_contract_tasks=2 | uid=9ca94048-91be-4546-b2bc-f10fc2a0d835 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1505 | group=reserve | cluster_contract_tasks=4 | uid=9d032108-437d-4368-908d-214aa2f26d0e | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1508 | group=reserve | cluster_contract_tasks=9 | uid=9d5adcb7-6bc0-4b86-b48e-fe9333bb6e7b | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1569 | group=reserve | cluster_contract_tasks=4 | uid=a3c80b34-7e97-44e3-a07e-5b6999e5113b | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1582 | group=reserve | cluster_contract_tasks=9 | uid=a5216555-06a1-4ec2-9afe-3db4e76b04a4 | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1588 | group=reserve | cluster_contract_tasks=2 | uid=a5fb7f90-4f37-460a-886e-13195f501f1b | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1598 | group=reserve | cluster_contract_tasks=9 | uid=a784a8e4-33a3-4f22-b338-ca218f76831c | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1604 | group=reserve | cluster_contract_tasks=8 | uid=a824b7af-61e8-4800-83c6-72e56e64a36d | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1628 | group=development | cluster_contract_tasks=4 | uid=ab59379f-ccca-409d-bc39-a48df76f6117 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1630 | group=reserve | cluster_contract_tasks=7 | uid=ab938d5a-cfe5-46b0-bc90-e4f0db462a9f | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1642 | group=reserve | cluster_contract_tasks=2 | uid=ac6e77fe-ba02-4764-9806-943cd8572e67 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1699 | group=reserve | cluster_contract_tasks=4 | uid=b19757bf-8a8a-428b-9dcc-8179595064ae | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1710 | group=reserve | cluster_contract_tasks=6 | uid=b2c8ac7d-6959-4874-b9f6-e6a53a1c6dc8 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role history (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_1724 | group=future_test | cluster_contract_tasks=4 | uid=b4129e1f-efcb-4157-9996-5389b83de63e | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1760 | group=reserve | cluster_contract_tasks=4 | uid=b6d52f9f-c989-4f47-9842-3d74c469d9cd | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1789 | group=reserve | cluster_contract_tasks=6 | uid=ba26cd64-e448-4ffb-bfaa-c6ad4760fba7 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1792 | group=reserve | cluster_contract_tasks=10 | uid=ba7ad32a-4f39-4eb3-a1ae-2aac19ca9325 | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1797 | group=reserve | cluster_contract_tasks=4 | uid=bb01e5d0-4524-497f-a45a-03804a6cb6ba | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1841 | group=reserve | cluster_contract_tasks=5 | uid=bf203086-ab57-4b6c-9ce6-34bf399ddd90 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1868 | group=reserve | cluster_contract_tasks=6 | uid=c18bb1bc-dc66-4586-989f-8bd13c0d77a4 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1875 | group=reserve | cluster_contract_tasks=7 | uid=c1e1d2be-ee4f-45c7-87d8-e8d218657bcb | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1880 | group=reserve | cluster_contract_tasks=2 | uid=c29582f8-d95d-480c-8daf-320273546471 | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1887 | group=reserve | cluster_contract_tasks=12 | uid=c3a02c86-f7f6-495c-8de2-a74c48f11905 | uid_contract_tasks=12 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1904 | group=reserve | cluster_contract_tasks=6 | uid=c501a508-4205-4046-a1b2-bc1d0baa25e3 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1912 | group=reserve | cluster_contract_tasks=6 | uid=c615ea13-a665-42ed-8e68-41ee7e3452b2 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1919 | group=reserve | cluster_contract_tasks=15 | uid=c7143215-25a8-44a2-b91f-4cbbfea16865 | uid_contract_tasks=15 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1925 | group=reserve | cluster_contract_tasks=15 | uid=c83c3a82-fb5e-403b-a73b-d3b1628092ef | uid_contract_tasks=15 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1929 | group=reserve | cluster_contract_tasks=3 | uid=c8be67ee-0783-4428-b9f0-0458f8725da6 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1934 | group=reserve | cluster_contract_tasks=8 | uid=c9ad526f-6bbf-4410-afbd-af41337b5067 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1950 | group=reserve | cluster_contract_tasks=3 | uid=cb626a5c-7b30-46ef-b0a7-971bc2196678 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1952 | group=reserve | cluster_contract_tasks=13 | uid=cb8b0774-53b1-4e33-9cf1-a7c1dac2f224 | uid_contract_tasks=13 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1973 | group=reserve | cluster_contract_tasks=3 | uid=cdbfc2e3-1082-4a25-9324-2f0ba9e684e5 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1981 | group=reserve | cluster_contract_tasks=13 | uid=ce8bc5c1-9b3b-458b-bd12-9d4e2ab4e2c9 | uid_contract_tasks=13 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_1996 | group=reserve | cluster_contract_tasks=4 | uid=cfe0ee38-48b2-46d2-8920-e423fc6c91ac | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot_reserve (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_2005 | group=reserve | cluster_contract_tasks=6 | uid=d15a82c3-024f-4e9c-a461-59e24bd95987 | uid_contract_tasks=6 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot_reserve (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_2007 | group=reserve | cluster_contract_tasks=8 | uid=d17ec6e0-0d83-453e-b9c9-aeb795802ef4 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2010 | group=reserve | cluster_contract_tasks=5 | uid=d21abb01-5bda-4a72-be49-e43a9d41c723 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2014 | group=reserve | cluster_contract_tasks=9 | uid=d258211e-01d6-477b-96f4-c059b7282c3e | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2015 | group=reserve | cluster_contract_tasks=9 | uid=d2647217-3696-4ec0-ad69-a3db3626c707 | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2044 | group=reserve | cluster_contract_tasks=3 | uid=d52fcb48-90fc-4a49-81f2-57065953f114 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2060 | group=development | cluster_contract_tasks=5 | uid=d7990183-3079-4e28-975b-bd60cafdcd1d | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2064 | group=reserve | cluster_contract_tasks=2 | uid=d7ec8bf0-ec91-4a6d-86a1-7bcc87bd37cc | uid_contract_tasks=2 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2070 | group=reserve | cluster_contract_tasks=11 | uid=d8662c4b-5f96-400b-8cd4-ff7b1f585bca | uid_contract_tasks=11 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2090 | group=reserve | cluster_contract_tasks=7 | uid=da915ccc-defe-40e3-9ade-04d76be09807 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2095 | group=reserve | cluster_contract_tasks=8 | uid=dace18a6-701f-49d4-a16d-078e5b62fc94 | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot_reserve (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_2096 | group=reserve | cluster_contract_tasks=7 | uid=daf81839-002f-40c2-8067-b4ad7eaf1517 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2111 | group=reserve | cluster_contract_tasks=9 | uid=dc50b42b-1520-49c0-a9ae-49249bcc9221 | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2120 | group=reserve | cluster_contract_tasks=5 | uid=dd9f455a-73fe-43a7-bde1-41e71bf18722 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2151 | group=reserve | cluster_contract_tasks=4 | uid=e0fb3736-71df-4e95-a40f-77ba0cce3487 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2159 | group=reserve | cluster_contract_tasks=5 | uid=e1754270-0867-4525-876e-5579322d3fa5 | uid_contract_tasks=5 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2174 | group=reserve | cluster_contract_tasks=9 | uid=e2d0f4f9-d15b-4537-bc7a-625729013ba4 | uid_contract_tasks=9 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2178 | group=reserve | cluster_contract_tasks=7 | uid=e316af95-270d-4107-99d4-6f52e4d61d38 | uid_contract_tasks=7 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_2196 | group=reserve | cluster_contract_tasks=3 | uid=e573a09b-3053-4c6e-9766-3cce1d2c087d | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2220 | group=reserve | cluster_contract_tasks=3 | uid=e78f8b29-6085-43de-b32f-be1a68641be3 | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2224 | group=reserve | cluster_contract_tasks=3 | uid=e8877535-8ade-4ba3-aae2-cd4db2b5c59c | uid_contract_tasks=3 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role development (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_2287 | group=reserve | cluster_contract_tasks=14 | uid=ee312f2a-0b31-4f27-838d-8244e5e46ce5 | uid_contract_tasks=14 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2290 | group=reserve | cluster_contract_tasks=16 | uid=ee496e48-bec3-45e2-b4d9-3986d90d98fe | uid_contract_tasks=16 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2314 | group=reserve | cluster_contract_tasks=8 | uid=f188de60-64eb-49cb-8b9d-a72f844357ef | uid_contract_tasks=8 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=WP2 dryrun role pilot (content-blind sha256 rule) + wp2/PILOT_ELIGIBILITY_RECEIPT.json deterministic qualification; no actor/design/effect entry
cluster_id=cluster_2328 | group=reserve | cluster_contract_tasks=10 | uid=f3bb2fbf-7b9c-43fc-a262-2e899947bf9e | uid_contract_tasks=10 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2336 | group=reserve | cluster_contract_tasks=4 | uid=f47d9a01-a25d-436c-a28b-7aa04e2df491 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2344 | group=reserve | cluster_contract_tasks=5 | uid=f5511f3c-b02d-4142-aa16-0b87cd61690f | uid_contract_tasks=5 | category=MODEL_OR_FEEDBACK_EXPOSURE | evidence=multileaf M/N substrate; effect analysis at research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl, multileaf_paired_artifacts.jsonl, multileaf_formal_results.json
cluster_id=cluster_2437 | group=reserve | cluster_contract_tasks=4 | uid=ff281ea5-25cf-4e1d-b7f5-f0dc51a40f25 | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
cluster_id=cluster_2442 | group=reserve | cluster_contract_tasks=4 | uid=ffc5e1e0-e7bf-4b8f-b60e-ace472695a1e | uid_contract_tasks=4 | category=PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | evidence=candidate_items_v2 deterministic generation; bounded non-entry vs WP2 actor prompts, multileaf manifest, TQ-4/TQ-5 panels, coordinator diagnostic
```

Category totals over the 165 clusters:

| category | clusters |
|---|---|
| EXPOSURE_UNKNOWN | 2 |
| MODEL_OR_FEEDBACK_EXPOSURE | 5 |
| PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | 158 |
| **total** | **165** |

By proposed group:

| group | PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE | EXPOSURE_UNKNOWN | MODEL_OR_FEEDBACK_EXPOSURE | total |
|---|---|---|---|---|
| future_test | 5 | 2 | 1 | 8 |
| development | 2 | 0 | 0 | 2 |
| reserve | 151 | 0 | 4 | 155 |

---

## 8. Commands and checks actually run

Run (all read-only against evidence; no service, model, judge, or training call was made):

1. `python3` JSON recomputation of `EXPOSURE_AND_SPLIT_AUDIT.json`: top-level keys, `source_clusters`, `exposure_model.category_counts_by_uid`, member-level category counts, pending-row filter at `contract_task_count >= 2`, distinct-UID counts.
2. `python3` sha256 recomputation of `non_structural_exposure_register.uids` under three canonicalizations; matched the claimed `d6c37842dd6ebb1f8d512ca0ad3f0f94a1a6ba5e39c8fbeefe4b16c710724070` (`json.dumps(sorted(uids), separators=(",", ":"))`).
3. `python3` recomputation of `SPLIT_PROPOSAL.json` group sizes, pairwise disjointness, union size, and set-equality against pending-eligible clusters and `history_cluster_ids`.
4. Full read of `exposure_classifier.py` and `build_exposure_and_split_audit.py` (source-level trace of category assignment).
5. Full read of `source_cluster_builder.py` `record_id()` / `report_identity()` (UID is `record["table"]["uid"]`; `report_identity_available: false`).
6. `find` / `ls` enumeration of `tatqa_wp0_2026/`, `wp2/`, `tq4_calibration_v1/`, `tq5_source_validation_v1/` trees.
7. `grep -r -o -E` over `research/` + `data/` for the union of all 170 pending UUIDs (single pass, then per-future-8 confirmation).
8. `python3` table-signature content mapping of all 7 WP2 actor `prompt.txt` files to raw UIDs.
9. `python3` table-signature content mapping of TQ-4 `panel_v2/**` and TQ-5 `panel/**` JSON to raw UIDs + literal-UID extraction.
10. `python3` regex sweep for opaque `origin_` hex tokens across `research/` + `data/`.
11. `python3` membership tests: multileaf sample manifest M/N set, WP2 dry-run roles, drift `injection_map.json`, `coordinator/pool_inventory.json` + `case_provenance.json`, TQ-4/TQ-5 `SELECTION_LOG.json.selected`.
12. Recomputation of the PR-EXP-03 "48 UIDs" registry from `multileaf_preresult_sample_manifest.json` using the contract's verbatim command, and set-diff against the registry printed in `implementation_contract.md`.
13. Cost/model-call inspection: `PR-EXP-03/receipt.json`, `multileaf_run_receipt.json`, `PILOT_ELIGIBILITY_RECEIPT.json.decision_boundary`, `ACTOR_ARTIFACT_VERIFICATION_RECEIPT.json`, marker scan of `experiment.py` / `run_multileaf_formal.py` / `check_pilot_eligibility.py`.
14. `python3` enumeration of every WP2 `attempts/` directory and `ACTOR_CALL_LEDGER.json` attempts (8 logical actor requests).

Checks **not** run (declared, not silently omitted):

- No service start, model call, judge call, canary, training run, or data collection. Cost of this review: zero model/endpoint/judge/training calls.
- No re-execution of `build_exposure_and_split_audit.py`, `build_items_v2.py`, or any generation script; existing artifacts were read as pinned.
- No recomputation of the sha256 of `SOURCE_CLUSTERS.json` against `outputs.source_clusters_sha256`.
- No adjudication of the 12 `history` clusters, of the 5 sub-threshold pending rows, or of the 2211 `STRUCTURAL_SCAN_ONLY` clusters.
- No exploration of SEC EDGAR, MultiHiertt, public web search, or unrelated repository threads (`finqa_*`, `harness_rsi_v1`, `pso/`).
  A literal-UID sweep did cover those paths; none of the 170 pending UIDs occurs there, so they were left unexamined as out of scope.
- No human semantic gold judgment, and no re-grading of any task or reference answer.

---

## 9. Conservative qualified future count

Applying `EXPOSURE_UNKNOWN` conservatively to the proposed future pool of 8:

| cluster | disposition |
|---|---|
| `cluster_0306` | qualified (`PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE`) |
| `cluster_0615` | qualified |
| `cluster_0978` | qualified |
| `cluster_1340` | qualified |
| `cluster_1724` | qualified |
| `cluster_0584` | not qualified (`EXPOSURE_UNKNOWN`) |
| `cluster_1360` | not qualified (`EXPOSURE_UNKNOWN`) |
| `cluster_0599` | not qualified (`MODEL_OR_FEEDBACK_EXPOSURE`) |

**Conservative qualified future count: 5.**

Upper bound if the two `EXPOSURE_UNKNOWN` clusters are later resolved clean: **7**.

### Do at least 8 clusters survive?

**No.** The proposed future pool contains exactly 8 clusters. One is positively exposed (`cluster_0599`), so at most 7 of the
proposed set can ever qualify; under the conservative application of `EXPOSURE_UNKNOWN`, 5 qualify. Both figures are below the required 8.
Reserve contains 151 `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE` clusters that are contract-valid and disjoint, so a replacement future pool
of size 8 is plausibly constructible -- but that would be a new split proposal, which this review is explicitly not permitted to make.

Therefore: `CONDITIONAL` (not `FUTURE_POOL_QUALIFIED`, not `INSUFFICIENT_EVIDENCE`).

---

## 10. Unresolved provenance and report-identity limits

1. **No report-level independence.** `EXPOSURE_AND_SPLIT_AUDIT.json.unresolved` and `normalization_and_association.report_identity_available: false`
   record that raw records carry no report ID. Clusters are source-association clusters (exact/near-duplicate table and paragraph edges),
   not report-level independence units. Future-test leakage across reports cannot be excluded on this evidence.
2. **PR-EXP-03 registry transcription defect.** The "Extracted registry (48 UIDs)" block in
   `research/positive_repair_20261011/runs/PR-EXP-03/implementation_contract.md` does not exactly match the set produced by its own
   verbatim extraction command. The contract lists `1b6fe333-4e8b-468e-af0c-4de123fca154`;
   `multileaf_preresult_sample_manifest.json` yields `1b6fe334-3e8b-468e-af0c-4de123fca154`. Intersection 47/48.
   The contract's stated list sha256 `e511b6ed...` also does not reproduce under `sha256("\n".join(list) + "\n")`.
   Neither UID is in the 165, so this does not change any disposition here, but the report-identity claim in that contract is not self-consistent.
3. **Classifier cannot emit `EXPOSURE_UNKNOWN`.** As shown in section 2, `structural = set(raw_uids)` makes the `EXPOSURE_UNKNOWN` branch
   unreachable. Any downstream consumer treating "no `EXPOSURE_UNKNOWN` rows" as a clean bill of health is mistaken.
4. **Classifier evidence scope is narrower than actual consumption.** The classifier reads only TQ-4, TQ-5 and `coordinator`. It does not
   read Stage-E multileaf, positive-repair, WP2 dry-run roles, or WP2 actor runs (beyond 5 hardcoded UIDs).
   5 of the 165 clusters are exposed through exactly those un-read paths.
5. **`cluster_1973` mixed membership.** One pending UID plus one `STRUCTURAL_SCAN_ONLY` UID in a single cluster; the cluster inherits the
   pending category by rank. Its pending member has 3 contract tasks so the cluster is correctly in the 165, but the cluster is not homogeneous.
6. **WP2 role designation boundary.** Whether `pilot_reserve` / `pilot` designation constitutes exposure is not resolved by the available
   receipts. This review chose the conservative reading for the two future-pool members and documented the alternative in 5.2.
7. **This review did not verify item-level gold correctness** of any generated task/reference. Contract validity here means the audit's
   `task_eligibility` contract (`task_eligible: true`, `contract_task_count >= 2`) and nothing about answer correctness.

---

## 11. Standing statements

**This is an AI evidence review, not human semantic gold.** Every category assignment above rests on mechanical file evidence and
deterministic data-flow tracing. No human annotated, judged, or adjudicated any UID or cluster in this review, and nothing here should be
read as a semantic gold label for task quality, reference correctness, or scientific validity.

**Online collection remains not authorized by this review.** This review was read-only. It did not authorize collection, start any service,
make any model/endpoint/judge call, run any scientific model, train, pilot, switch source, or release data. Model calls, endpoint calls,
judge calls and training calls performed by this review: **0 / 0 / 0 / 0**. Any online collection requires separate explicit authorization
and a further gate; `SPLIT_PROPOSAL.json` status remains `DRAFT_PENDING_LOOP_C_PROGRAM_REVIEW`.

---

*End of review. Single report file; no second summary file created. Reviewed artifacts, raw data, WP-2 files, frozen materials, scores,
and prior review reports were not modified.*
