# PR03_SPILLOVER_AUDIT_v1.md

> date: 2026-10-11 | scope: does the PR-EXP-03 (v2/v3) defect lineage contaminate SANER Route A submission evidence? | method: read-only token/path/import sweep over every Track A asset + provenance verification of the multi-leaf headline numbers
> verdict: **PR03_SPILLOVER_AUDIT = PASS (CLEAN)**

## 1. The three defects and where they live
- A. Runtime shadowing bug (`a1_table = a1_table(...)` at line 480): unique to research/positive_repair_20261011/runs/PR-EXP-03/experiment.py (Track P round-1 run dir, GB10-only, untracked).
- B. `predict_loco` O(groups^2) + round-1 runtime/provenance mismatch: unique to the same Track P experiment (its pure-Python `predict_loco` and `diag_bootstrap`).
- C. Dead `field_hit` baseline (returns 1.0 for any non-empty header): unique to the same Track P experiment.

## 2. Sweep results
| Track A asset | A | B | C | Evidence |
|---|---|---|---|---|
| saner_rene_manuscript_v1.md | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | 0 hits for PR-EXP-03, PR-03, positive_repair, predict_loco, field_hit, a1_table, a3_fp, 1973, 0.8116, topology_transposition, structural oracle |
| saner_rene_manuscript_v1.tex | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | 0 hits for the same token set |
| compiled PDF | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | built only from the bundle .tex + bundle-local figures/bib |
| Figure 1-3 | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | render_saner_figures.py has 0 PR-03 tokens; fig3 numeric bindings resolve to multileaf_signature_ablation.json (sha 0518c5bf...) |
| Table 1 | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | numbers (95/95, 75/95, 20/95, 112/118, 85/118, 13/118) come from docs/research/stage_e_118_quantification_v1.md |
| Stage E 118 results | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | docs/research sweep: 0 hits |
| multi-leaf 216 results | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | see section 4 |
| direct-codebook ablation | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | analyze_multileaf_signature_ablation.py imports stdlib + numpy only |
| affine-equivalence result | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | docs/research/stage_e_matched_fpr_reanalysis_v1.md (0 hits) |
| matched-FPR reanalysis | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | same |
| FinQA autopsy | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | docs/research FinQA files (0 hits) |
| claim matrix | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | C1-C3 evidence paths are all Track A (stage E, multi-leaf, FinQA) |
| scope lock | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | docs sweep 0 hits |
| reference/result ledgers | NO_SPILLOVER | NO_SPILLOVER | NO_SPILLOVER | related-work and reference ledgers cite RENE/NIST only |

Additional sweeps: logs/graph/eval = 0 hits. paper/ = 2 hits, both benign internal docs (SANER_RENE_2027_REQUIREMENTS.md and BUILD_README.md mention the round folder path only), neither is manuscript evidence.

## 3. Name-collision note (NOT a dependency)
The multi-leaf pipeline has its OWN `predict_loco` (numpy, in run_multileaf_formal.py and analyze_multileaf_signature_ablation.py). It is a different function from PR-EXP-03's pure-Python `predict_loco`. Likewise, the manuscript's "field hit-rate" is the production checkpoint leaf measured in Stage E, not PR-EXP-03's `field_hit` helper. Token collision only: no shared code, data, or results.

## 4. Multi-leaf four-number provenance (independent chain)
- Numbers: full vector macro-F1 = 1.0; direct three-leaf codebook = 1.0; non-direct leaves only = 0.3333 (tie rate 0.6667); majority baseline = 0.1667 (derived 1/(2K), K=3); any-response scalar = 0.0.
- Producer script (ablation): research/stage_e_multileaf_20261010/analyze_multileaf_signature_ablation.py, sha256 bb420363e6747172ed0b991298a03224b8237fece9f90d557ca496961266640c (imports stdlib + numpy only).
- Result artifact (ablation): research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json, sha256 0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d (matches the figure manifest expectation).
- Formal chain (upstream of the ablation): run_multileaf_formal.py, sha256 d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 -> multileaf_prediction_rows.jsonl (216 rows), sha256 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06 -> multileaf_formal_results.json, sha256 ae9cf1cf37e2742e3895ec2bd0e4cf0c150a18c927eb9a618f612782b3d9cbb0. Bootstrap intervals: multileaf_bootstrap_intervals.json (sha256 0dbfebc3...); permutation null: multileaf_permutation_null.json (sha256 b988fba4...).
- Runtime provenance: multileaf_run_receipt.json (sha256 66ab58fa4847e6ee25567443310781628ee92bd952cfc3a469d323efd9c11956) binds the runner, predictions and result hashes and records completed_at 2026-10-10T01:02:44+08:00, status COMPLETE, result_status POSITIVE; the ablation JSON source block pins the prediction file path (GB10 runtime tree) + sha256 + rows=216. Full-chain hash equality (receipt = predictions = formal results = ablation source = figure manifest) re-verified by Loop D on 2026-10-11.
- Pre-result freeze: multileaf_preresult_freeze_manifest.json (sha256 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163) equals the pre_result_manifest_sha256 embedded in the formal results; the runner refuses to start on freeze mismatch. Prereg/freeze receipts: docs/research/stage_e_multileaf_preregistration_v1.md; docs/research/multileaf_preresult_freeze_receipt_v1.md; documented in docs/research/stage_e_multileaf_signature_ablation_v1.md.
- Classifier implementation: numpy nearest-centroid leave-one-cluster-out (per cluster: class centroids from the training folds; distance ties -> TIE, scored incorrect; margin = nearest-vs-second distance gap). Same algorithm in both scripts (runner line 403; ablation line 47); no third-party code.
- Baseline semantics: chance top-1 = 1/K = 0.3333; majority top-1 = 0.3333; majority macro-F1 = 0.1667 = 1/(2K) for the balanced three-class population; uniform-class macro-F1 = 1/3 (baseline block of multileaf_formal_results.json; the fig3 manifest derives the displayed 0.1667 from full_vector.confusion with K=3).
- Dependency on PR-EXP-03 lineage: NONE (no import, no string reference, distinct classifier implementation).
- Verdict: MULTI_LEAF_PROVENANCE_INDEPENDENT_OF_PR03 = **YES**.

## 5. Supersession
- research/positive_repair_20261011/runs_local_mirror/PR-EXP-03/metrics.json and receipt.json (round 1) are NOT reproducible by the delivered frozen implementation (the shadowing bug prevents `evaluate` from running; `predict_loco` makes the frozen diagnostic bootstrap infeasible; the recorded 275 s runtime is not attainable by that code).
- These files are marked SUPERSEDED_FOR_SCIENTIFIC_INTERPRETATION (see the marker file in that directory). History is retained, nothing is deleted, and they were never a manuscript evidence source and remain barred from being one.
- Registry: POSITIVE_REPAIR_REGISTRY_v1.json carries a pr03_lineage_supersession block binding the two artifacts by sha256 (mirror hashes equal the GB10 counterparts, verified 2026-10-11).

## 6. Verdict
- PR03_SPILLOVER_AUDIT = PASS (CLEAN).
- No manuscript number is affected. No Track A asset depends on the PR-03 lineage.
- SUBMISSION_DRAFT_COMPLETE remains YES. No blocking scientific issue. No manuscript file was touched by this audit.
