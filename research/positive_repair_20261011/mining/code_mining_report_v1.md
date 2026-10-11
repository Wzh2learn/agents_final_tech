# miner_code report — code-level mechanics and costs for Track-P candidate repairs (read-only)

**Meta.** Repo `D:\AIRcommend\JinRongAgents\agents_final_tech` (LOCAL @ `eae2688`), GB10 `/home/testuser/wzh/projects/agents_final_tech` @ `eae2688` (verified during mining). All below from code/JSON reading and read-only shell probes on GB10; zero model/endpoint/service calls, zero repo writes, no git mutations. Labels: FACT (verified in file:line) / INFERENCE (my reading) / UNVERIFIED (could not confirm).

**Identity note (process).** This child was bootstrapped with the ROOT's session summary instead of its own miner task (compaction mix-up). Identity verified via collaboration send-probe: I am `/root/miner_code`. Sibling `/root/miner_finqa` also bootstrapped with root context and initially behaved as root; it received a refocus message — a `followup_task` re-issue was needed (later delivered). `miner_stage_e` self-recovered and delivered already.

## Q1. Checkpoint aggregation / evaluation code

`scripts/eval_checkpoint_aggregate.py` — the "Algorithm 1" aggregator used across K2/Stage E:
- Leaf scoring via `LEAF_ROUTERS` keyed by source (`m1_regression` / `m2_deterministic` / `m2_judge` / `m2_number_faithfulness`); judge dims `0-5 -> *2` to 0-10; rates `*10`; binaries `10/0` (lines ~150-205).
- Missing-data policy: missing source artifact / unmapped router / `None` value -> `missing_score` + `degraded` flag, never silent zero (F-J1, lines 179-187). Per-leaf `missing_score` from `config/eval_checkpoint_trees.json` (parse-tree hinges default 0; qa-tree leaves 5; aggregator default 5.0).
- Aggregation: bottom-up weighted sibling-normalized mean (dfs, lines 216-239); `round(...,4)`; per-node subtree scores.
- Hinge gates: `HINGE_ROUTES = {overall_status_binary, pass_rate_contract, nf_pass_rate}` -> hinge leaves are `parse.doc.ok`, `qa.retrieval.source_required`, `qa.numeric.exact`, `qa.numeric.number_grounding`.
- STABLE rule: `leaf_ok >= 0.9 * n_leaves AND all hinge >= 7` (lines 253-259). Code observation (FACT, intent UNVERIFIED): the `stable` dict is assigned inside `for k in thresholds` and overwritten each pass, so with defaults `(5,7,8)` the persisted `stable` uses the LAST k=8 (counts `v > 8` strictly), while the module header/report text says ">=7" (lines 14-17, 295-299). Potential micro "deterministic contract" repair — verify intended semantics against K2 v0 before touching anything.
- CLI `--thresholds` default `5 7 8` (lines 314, 332); SR reported per threshold.

`scripts/eval_checkpoint_discrimination.py` — v1 deterministic mutant testbed (no endpoints):
- Builds mutant copies of the 4 eval artifacts under `<eval-dir>/_mutants/<id>/` (mutators lines 44-143): 9 mutants — M1 two rows FAIL; M2 `exact_numeric` contract fail; M3 `source_required` fail; M4 `refusal_expected` fail; M5 judge faithfulness 5->2; M6 citation 5->1.5; M7 NF 3 fails; M8 judge artifact deleted (missing_score path); M9 all rows FAIL.
- Per-mutant pass: target leaf drop >= `DROP_THRESHOLD = 2.0` (line 42), graded direction on rate leaves, locality (no non-target leaf moves > 1e-6), control zero-drift (lines 220-240); `ok = target hits AND graded hits AND no non-target moves` (stable/stable_flip recorded but NOT part of pass criteria, lines 231-233). Mutants deleted unless `--keep`.

`config/eval_checkpoint_trees.json` — 2 trees (parse/qa), 12 leaves total, weights 1-3, per-leaf `source`/`mapping`/`missing_score`; meta notes hinge nodes (parse_ok / exact_numeric / number_grounding) as hard gates.

## Q2. Controlled fault injections (three distinct arms)

1) Drift-v0 header arm (the 95 tables / 118 injections corpus).
- Injector `scripts/research/drift_inject.py`: six families `alias_variant, mixed_lang, unit_suffix, date_variant, ocr_similar, prefix_noise` (module docstring lines 3-31 + family dictionaries); header-row-only rewrites; seed 42 / ratio 0.3 defaults; byte-stable (unit test `tests/test_drift_inject.py` exists; determinism claim = docstring).
- Files: `data/research/drift_v0/input/tatqa_tables.json` sha256 `3e7e0568…` and `output/injection_map.json` sha256 `d7612405…` — present on GB10 repo checkout; ABSENT in LOCAL checkout (`data/research/` does not exist locally). FACT (verified both hosts).
- Visibility/absorption computed by `research/k2_table_discrimination_v2.py`: per injection `absorbed := (canonical found) and (mapped_to_in_inj == injected_text)`, `visible := not absorbed` (lines ~130-140) — i.e., the production `map_headers` (pure-rule, zero endpoint) still associates the corrupted token, making it observationally invisible ("silent absorption"); double-run zero-drift check of `map_headers` (line ~121); table-level degree `drop10 = (H_orig-H_inj)*10 >= 2` (~line 124); locality check (~lines 145-150); resumable checkpointed loop (~lines 250-260); per-family aggregation (~270-300); `meta.runtime_s` recorded.
- Cross-matcher detection arm `research/paper_d2_cross_matcher_det.py`: per-injection `absorption_silent | threshold_dilution` classification (~529-541) and gamma-grid visibility / all-gamma blind gate (~700-745) — this is the code behind "OCR-like blind under every threshold".

2) Multi-leaf controlled arm (216 injections). `research/stage_e_multileaf_20261010/run_multileaf_formal.py`:
- `check_m` (line 232): replace one header token (from freeze sample `field_after`); responses `parse.table.regression` and `parse.field.hit_rate` both `= int(mutated_hit < baseline_hit)` (lines 256-258) — the two leaves are byte-identical aliases (MVP audit F5 reproduced here). `check_r` (line 279): remove required evidence blocks from candidate bundle; `qa.retrieval.source_required = int(baseline_pass and not injected_pass)` (line 301). `check_n` (line 316): mutate one numeric operand; `parse.reconcile.equations = int(original_pass and not mutated_pass)` (line 341). Contract checks include table/question hash equality; 3 repeats per cluster (`materialize`, lines 350-380).

3) K2 artifact-mutant arm (same file as Q1's second entry; M1-M9 mutants) — separate namespace from the drift arm; do not conflate the three arms in synthesis.

## Q3. Per-checkpoint signal tables (schemas, keys only)

- `logs/graph/eval/checkpoint_discrimination_tables_v2.json`: keys `{meta, properties, by_type, patent_crosswalk, tables, qa_arm}`; `by_type` = six families with `n_injections/n_visible/n_absorbed/visibility_rate/match_tiers`; `tables[]` = per-table `h_orig/h_inj/drop10/discriminated/zero_drift/locality_clean/locality_moves + injections[]`; `qa_arm` = endpoint-scored arm rows.
- `logs/graph/eval/t2_visibility_sensitivity.json`: keys `{meta, gates, g3_detail, e2_1_gamma_grid, e2_2_equivalence_correction, e2_3_strength_gradient, prereg_predicates, tables, injections, zero_endpoint, payload_sha256, sha256_scope}`; `injections[118]` fields incl. `absorbed_single, absorbed_full_injection, visible_frozen, mapping_keys_same_full, mapping_text_same_full, equivalent_mutation, visible_by_gamma, gradient`.
- `d1_mutant_validity_audit.json`, `d3_matched_fpr_stage_a.json`, `t1_eval_baseline_comparison.json`: `{meta, gates, payload, …}` (+`arm_a/arm_b/aggregation_isomorphism` in t1).
- Multi-leaf: `research/stage_e_multileaf_20261010/results/` — `multileaf_paired_artifacts.jsonl` (216 rows: `stage/cluster/year/contract_checks/baseline_scores/injected_scores/response_vector[12]`), `multileaf_prediction_rows.jsonl`, `multileaf_formal_results.json`, `multileaf_signature_ablation.json`, `multileaf_bootstrap_intervals.json`, `multileaf_permutation_null.json`, `multileaf_run_receipt.json`.
- Key limitation (FACT): frozen artifacts carry leaf-level values only — no intermediate/pipeline state hashes (paired artifacts schema shows this). Propagation-depth / first-visible-distance analyses are NOT computable from the frozen data; they need new-namespace instrumentation.

## Q4. Multi-leaf harness: rerun cost, knobs, determinism

- Constants: `PERMUTATION_SEED=20261011`, `BOOTSTRAP_SEED=20261012`, 10,000 + 10,000 replicates; `CLASSES=M/R/N`; `DIRECT_LEAVES` map; `TATQA_RAW=/home/testuser/wzh/datasets/tat-dqa/raw` (GB10-only, lines 32-37); tables input `data/research/drift_v0/input/tatqa_tables.json` (GB10).
- Guards: `verify_pre_result_freeze()` refuses on freeze/manifest/code/env/git mismatch (line 189); seed cross-checks (591-594); refuses pre-existing out-dir (599); leakage audit; per-table hash equality inside checks.
- Rerun compute (FACT): freeze captured `2026-10-10T01:01:51+08:00` -> results generated `2026-10-10T01:02:44+08:00` = ~53 s end-to-end on GB10 (216 rows + LOCO + 10k permutations + 10k bootstraps). Zero endpoints.
- Cluster selection (`research/stage_e_method_revision_20261009/build_multileaf_freeze.py`): `SEED=20261010`, `CLUSTERS_PER_STAGE=24`, `INJECTIONS_PER_CLUSTER=3`; selection = ascending SHA-256 of `seed:namespace:key`, label-blind ("no evaluator output or visibility result is read", line 501). M/N clusters from TAT-QA tables (N excludes M UIDs, line 477); R clusters from TAT-DQA QA records keyed `(source_split, document_id)` (230-258).
- Modified-config rerun (INFERENCE): compute is trivial, but the runner/manifest are hash-bound and out-dir must not pre-exist -> any config change requires a new prereg namespace + fresh audit, not a rerun-in-place. The real cost is protocol + audit, not FLOPs.

## Q5. Recorded runtimes (all zero-endpoint)

- k2 tables arm `meta.runtime_s=0.14` (checkpointed/resumable), t2 sensitivity `0.62`, t1 comparison `0.28`; d1/d3 carry no runtime field.
- Multi-leaf formal end-to-end ~53 s (above). Adjacent DEV_ONLY smoke (causal-MVP): `9 passed in 0.94s`.
- Not recorded (do not quote numbers): multileaf ablation script, independent validation script, discrimination testbed runtime. UNVERIFIED.

## Q6. Intervention implementation difficulty (files to touch)

- (a) Checkpoint-subset pruning / same-diagnosability-at-lower-cost: new analysis script over `multileaf_prediction_rows.jsonl` / reuse `analyze_multileaf_signature_ablation.py`. No frozen edits; cost ~hours; compute seconds. Caveat: high tautology risk vs the direct codebook (ablation already at 1.0); best framed as a cost-side result.
- (b) Observation placement variants: (b1) re-placement over existing 12-leaf responses (post-processing with `leaf_order` / `effective_leaf_weights`) = hours, no runner change; (b2) genuinely new placement node = trees config variant + new-namespace runner change = days.
- (c) Tri-state missing-evidence channel: `scripts/eval_checkpoint_aggregate.py` (missing/degraded handling lines 179-187, report, stable semantics) + `config/eval_checkpoint_trees.json` `missing_score`; changes the reporting object -> must predefine the reading; days.
- (d) Extra generic observation node at extraction: three touch points — trees config leaf + `LEAF_ROUTERS` + an artifact/evidence producer (or a frozen predicate in a new runner check for the controlled arm). Days; the project already has the anti-tautology contract pattern (MVP design doc Anti-Tautology: SOURCE_LOCAL vs DOWNSTREAM_CAUSAL) to borrow.
- (e) Judge -> deterministic verifier: reuse `scripts/m2_eval_deterministic.py` patterns; swap router/mapping for the 3 judge leaves. Caveat (FACT): on the frozen corpora judge leaves have zero nonzero responses (8/12 zero columns) — no effect can show there; needs a population where judges fire (new data / production eval records; policy care). Days.
- (f) Trace-completeness logging: extend the multi-leaf runner (new namespace) to emit per-stage input/output hashes + first-visible leaf index; enables the currently-impossible propagation-depth / silent-absorption quantification. Days; compute stays ~1 min.
- (bonus) Stable-k deterministic micro-repair: see Q1 quirk; very low cost; testable on the existing discrimination testbed; verify intent first.

## Q7. Held-out structures (as implemented)

- Multi-leaf: LOCO = "leave one stage-namespaced table/document/origin cluster out; all three repeated injections stay in the held-out fold" (freeze receipt); 72 clusters (24/stage); cluster ids `M:<uid>`, `R:<split>:<doc>`, `N:<uid>`.
- Drift arm: 88 table clusters (bootstrap); 5 deterministic table-UID folds (matched-FPR reanalysis); OCR-like = 13 injections over 11 clusters.
- Selection label-blind for the multi-leaf freeze (hash rule); drift map fixed (seed 42, ratio 0.3).

## Candidate-relevant candies (code-side, INFERENCE)

1. All re-runs are endpoint-free and sub-minute -> cheap replication; costs live in prereg + audit + executor changes, not compute.
2. Propagation/silent-absorption candidates need instrumentation (no intermediate states in frozen artifacts) — matches the result packet's "unexecuted" list.
3. The `parse.table.regression` == `parse.field.hit_rate` alias and the 8/12 zero-response columns are code-visible — repairs touching "non-direct leaves" start from a very thin information base.
4. Drift corpus + TAT-DQA raw are GB10-only; LOCAL analysis cannot rerun the drift arm.
5. The stable-k overwrite quirk is the only clear deterministic-contract candidate I found in the aggregation path; verify intent before proposing.

End of report. Read-only; no files modified; no endpoint calls.