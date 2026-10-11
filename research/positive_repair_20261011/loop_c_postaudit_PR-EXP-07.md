# Loop C Post-Result Independent Audit — PR-EXP-07 (ROBUSTNESS_ANTI_TAUTOLOGY)

You are the independent Loop C auditor. This is a POST-RESULT audit of one completed Track P experiment. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Judge strictly from this packet; missing evidence -> UNVERIFIED. Do not modify, re-run, or rescue the result. Labels: FACT / INFERENCE / UNVERIFIED.

## Round context (disclosed facts)
- Track P first wave: PR-EXP-03 INTERVENTION_REPAIR / PR-EXP-01 INTERVENTION_REPAIR / PR-EXP-04 GENERALIZATION_TEST / PR-EXP-07 ROBUSTNESS_ANTI_TAUTOLOGY. Only INTERVENTION_REPAIR positives may ever count toward the synthesis gate.
- Registered class for PR-EXP-07: NOT_EVALUABLE.
- Disclosed incidents, NOT part of this experiment's scientific record: (i) two engineering dispatch layers (a1 INPUT_MISSING x4; a2 HASH_MISMATCH x4) were fail-closed infrastructure failures, zero scientific side effects, excluded from scientific classes; (ii) the prereg re-audit log lost its leading sections in capture (verdicts recovered from GLOBAL); (iii) the Loop D prereg/sanity-gate definitions may contain defects - examine critically.
- Registered NOT_EVALUABLE came from a contract pin defect: the frozen implementation contract required the paired-carrier field expected_first_affected_stage, but the frozen carrier schema exposes expected_first_stage; no unauthorized fallback was applied; 216/216 rows excluded and no scoring occurred. Blindness proofs PASS (swap-invariance 216/216, pairing PASS, leakage PASS, forbidden fields never accessed). Judge whether NOT_EVALUABLE is correct, attribute the root cause (Loop D contract pin), and state the minimal correct future action WITHOUT tuning the extractor to rescue results.

## Your checklist (answer every item; cite packet fields)
1. Was the frozen prereg followed (population/intervention/baselines/metrics/taxonomy/stop rules; no threshold or rule hunting)?
2. Was the held-out set kept independent (UID overlap, freeze order, split integrity)?
3. Was any metric defined or modified after seeing results (post-hoc)?
4. Is the measurement object consistent before/after (same construct, correctly declared non-comparabilities)?
5. Any source-local tautology in the reported effect (per contracts/SOURCE_LOCAL_RESPONSE semantics)?
6. Any label / stage / outcome leakage (incl. provenance fields, pairing order, generation rules)?
7. Is cost accounted fairly (same-budget comparison; zero model calls verified by packet)?
8. Are effect sizes / CIs recomputable from the packet as given? (state what you could and could not recompute; that is expected for a packet-only audit)
9. Is the registered result classification reasonable and complete per the prereg taxonomy (POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE; NOT_EVALUABLE never merged into NULL)?
10. Does the packet suggest any manuscript claim beyond the evidence (should the SANER Route A manuscript cite, declining-cite, or bound this)?

## Required output format
## INDEPENDENCE DECLARATION
## CHECKLIST
- C1..C10: one line each (FACT/INFERENCE/UNVERIFIED)
## FINDINGS (ordered by severity; cite packet fields)
## STRONGEST OBJECTION
## VERDICT: ENDORSE_CLASS | ENDORSE_WITH_NOTES | CHALLENGE_CLASS
## RECOMMENDED REGISTRY CLASS: (one of POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE)
## RECOMMENDED MANUSCRIPT ROLE: (cite / bound / decline-cite / future-work) + one-line reason
## RESIDUAL RISKS / NEXT ACTION
End with the literal line: POSTAUDIT_COMPLETE
--- BEGIN prereg v2 (PR-EXP-07) ---
# Prereg — PR-EXP-07: Label-blind re-extraction (anti-tautology robustness)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-07 | candidate: PR-07 | role: ROBUSTNESS_ANTI_TAUTOLOGY (supporting evidence only; NOT a repair count)
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> Objective: re-test the multi-leaf result after removing every possible label / contract-construction information channel. NOT a new positive method.

## 1. Extractor blindness contract (provably enforced)
Inputs ONLY: the unordered pair {A,B} of paired raw observation states. Blind pairing: the PAIRING RULE is built from the frozen cluster structure only (which samples belong together is fixed by construction, never by response values); pair ORDER randomized by frozen seed; features computed as order-invariant (symmetric) functions; swap-invariance test required across all rows (feature(P) == feature(swap(P))).
Forbidden knowledge (structurally impossible): mutation family label; stage label; expected first stage; target checkpoint identity; gold outcome; sample namespace; generation code.
Label provenance (declared): decoded labels are injection-design stage labels fixed in the frozen freeze record before scoring; labels are never response-derived.
Freeze timing: extractor + feature sets frozen BY HASH BEFORE any feature-value observation (freeze first, then compute features, then evaluate). No post-hoc tuning; any edit -> new prereg.
Pairing-rule certification: record the pairing rule source + proof it reads no response values (code inspection note + hash).

## 2. Frozen feature sets and population
- Population: the frozen 216-row multi-leaf carriers (paths + hashes pinned in the implementation contract); LOCO groups = frozen cluster ids (rule referenced by hash from the freeze receipt).
- Feature sets frozen by hash: full label-blind set; direct-codebook subset (label-blind definition frozen); non-direct subset.
- NULL rule (binding): full <= direct -> NULL.

## 3. Primary metric and numeric criteria
macro-F1 / top-1 under frozen nearest-centroid + LOCO vs direct-codebook baseline vs chance (1/3).
Shuffled-label negative control (frozen seed) included.
Numeric "clearly above" (frozen): ROBUST requires (full point − direct point >= 0.05) AND (non-direct point >= 1/3 + 0.05).
Case taxonomy (complete): ROBUST (both criteria); NULL_DIRECT_CONCENTRATED (full > direct but non-direct <= chance margin); NULL (full <= direct); NULL_AT_CHANCE (full > direct but full ≈ chance within 0.05); NOT_EVALUABLE (undefined features / missing proof artifacts; row-level attrition accounting mandatory; never merged into NULL); INVALID (any leakage channel usable; swap-invariance or pairing proof fails).

## 4. Interpretation (owner-fixed)
- ROBUST -> robust supporting evidence.
- Degradation -> retain NULL/negative AND explicitly lower the original multi-leaf claim (recorded, never silent).

## 5. Required reports
- Quantified blind-vs-original delta on identical rows: Δ = full_labelblind_macroF1 − original_frozen_macroF1, reported with CI; explicitly declared non-comparable claim-wise (different measurement objects) while the numeric delta is recorded.
- Attrition table (rows per exclusion reason).

## 6. Cost / Stop
Zero model calls; deterministic; minutes of GB10 compute.
STOP: swap-invariance or pairing proof failure -> INVALID; then stop. No rescue tuning of the extractor.
--- BEGIN receipt.json ---
{
  "cost": {
    "database_calls": 0,
    "judge_calls": 0,
    "model_calls": 0,
    "network_requests": 0,
    "service_calls": 0,
    "training_runs": 0
  },
  "deviations": [],
  "end_utc": "2026-10-11T08:29:16.245091Z",
  "experiment_id": "PR-EXP-07",
  "implementation_contract_sha256": "f13a748fddd4f2aefb8fd28f921555caad84cb0563d582786a82dd5b3e73f4b3",
  "input_hashes": {
    "config/eval_checkpoint_trees.json": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "docs/research/multileaf_preresult_freeze_receipt_v1.md": "a167f770f5b2e42cca69579ec60efafd233c7e8ed742c7178f244dbc6c78eaf1",
    "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    "research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-07.md": "448fe0868fdfc427d88aef72f4094fc54610b3380cbb084ca93ddfef13563d3a",
    "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
    "research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log": "a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d",
    "research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md": "4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f",
    "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
    "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
    "research/stage_e_multileaf_20261010/results/multileaf_bootstrap_intervals.json": "0dbfebc34aebafbafcebdcb7c944668ea8c235a87fd692454536a4444a91887a",
    "research/stage_e_multileaf_20261010/results/multileaf_formal_results.json": "ae9cf1cf37e2742e3895ec2bd0e4cf0c150a18c927eb9a618f612782b3d9cbb0",
    "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
    "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
    "research/stage_e_multileaf_20261010/results/multileaf_run_receipt.json": "66ab58fa4847e6ee25567443310781628ee92bd952cfc3a469d323efd9c11956",
    "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json": "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d",
    "research/stage_e_multileaf_20261010/run_multileaf_formal.py": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
    "scripts/m1_statement_parser.py": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b"
  },
  "outcome_label": "NOT_EVALUABLE",
  "output_hashes": {
    "attrition.json": "7c94c1815cade08d2ad428edd726c22a02df116fb50ce3dab8f8e953eb9dacd7",
    "evaluate_pr_exp_07.py": "5f8310d0e86860915b55406b1a5eb82a94879f1ea2d73f6184780e84b0ce0dd1",
    "extraction_proof.json": "1260b648839edd150fcff6ded6de921d56c53c4f91a826e3e6f55753735b857b",
    "extractor.py": "8b136537189343f479506b9191908ce7d607805a29330b0890cf999c417e2d9c",
    "extract_features.py": "3419dba7f52497ba1c1fa721022a1b0a39d9e645c0b6afb0078dc2b105f0e2be",
    "feature_sets.json": "931f2a2a4c1cf37a39a0b3cd26b6387a9a322387cec3f0702c5fa9ff9aac7a45",
    "feature_values.jsonl": "763247c4b96a9ce07e2608f48fee36500be254f773fd8df2fc882c086c498408",
    "frozen_inputs.json": "6b69ecb36ccaf67682e0f62d7ba84acec422d89814ee27576402a3b24ee824ad",
    "implementation_contract.md": "f13a748fddd4f2aefb8fd28f921555caad84cb0563d582786a82dd5b3e73f4b3",
    "implementation_contract.sha256": "c0604de9969d1331ffaac97fb4f26e83ba47387e8fa09a94b186a6ecce76e1c2",
    "pairing_rule.json": "873f7ca3b26d2f88c52c20cb6063cca5b333e67da6187cb2f278bc0565d05b40",
    "result.json": "221332f8a74e82dadec6b55d911cba2516a3175437432e810a2ebdda50172984",
    "stop_event.json": "dbb4ba29041119c9d07ec73ac1e4e40d74c083463fcca6ec1fa49d2996c0f946",
    "swap_invariance_proof.json": "093bfc488e42bedee61583c94612cbfc950513c57f8f203532f381b4fec6da64"
  },
  "prereg_sha256": "4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f",
  "raw_metrics": {
    "ci95": null,
    "denominator": null,
    "not_evaluated": true,
    "numerator": null
  },
  "receipt_self_hash_note": "receipt.json self-hash is intentionally not embedded; it is verified externally after writing.",
  "shared_surface_identity": {
    "canonicalizer_git_blob_sha1": "def5161dd17fc14345d340879174ed01e0277626",
    "canonicalizer_identity_rule": "git_blob",
    "canonicalizer_raw_sha256": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b"
  },
  "start_time_basis": "Earliest generated feature artifact mtime; the frozen evaluator did not checkpoint a start timestamp before the schema stop.",
  "start_utc": "2026-10-11T08:27:31.173304Z",
  "status": "STOPPED_INPUT_MISSING",
  "stop_reason": "The frozen paired carrier lacks contract-pinned field expected_first_affected_stage; no fallback to expected_first_stage was applied.",
  "unverified_items": [
    "Label-provenance equality under the contract-pinned paired-carrier schema."
  ]
}

--- BEGIN result.json ---
{
  "attrition": {
    "expected_rows": 216,
    "excluded_rows": 216,
    "observed_source_rows": 216,
    "retained_rows": 0,
    "rows_by_exclusion_reason": {
      "cluster_missing": 0,
      "feature_row_missing": 0,
      "label_missing": 0,
      "label_provenance_field_schema_mismatch": 216,
      "missing_pair_member": 0,
      "nonfinite_feature": 0,
      "proof_missing": 0,
      "row_alignment_failure": 0
    }
  },
  "claim_lowering_note": null,
  "counts_toward_repair_count": false,
  "deviations": [],
  "experiment_id": "PR-EXP-07",
  "metrics": {
    "direct_codebook": null,
    "full": null,
    "non_direct": null,
    "not_evaluated": true,
    "original_frozen": null,
    "shuffled_label_control": null
  },
  "outcome_label": "NOT_EVALUABLE",
  "outcome_reason": "INPUT_MISSING: frozen paired-carrier schema lacks the contract-pinned label-provenance field expected_first_affected_stage; no fallback was authorized.",
  "population": {
    "clusters": 72,
    "evaluated_rows": 0,
    "expected_rows": 216,
    "observed_rows": 216
  },
  "proof_status": {
    "leakage": "PASS",
    "pairing": "PASS",
    "swap_invariance": "PASS"
  },
  "qualification_status": "NOT_EVALUABLE",
  "raw_metrics": {
    "ci95": null,
    "denominator": null,
    "not_evaluated": true,
    "numerator": null
  },
  "role": "ROBUSTNESS_ANTI_TAUTOLOGY_SUPPORTING_ONLY",
  "stop_event": "stop_event.json",
  "supporting_only": true,
  "taxonomy_priority": [
    "NOT_EVALUABLE",
    "INVALID",
    "ROBUST",
    "NULL",
    "NULL_AT_CHANCE",
    "NULL_DIRECT_CONCENTRATED"
  ],
  "unverified_items": [
    "Label provenance equality could not be checked under the contract-pinned schema because expected_first_affected_stage is absent from the paired carrier."
  ]
}

--- BEGIN stop_event.json ---
{
  "event": "INPUT_MISSING",
  "exception": "KeyError",
  "exception_detail": "expected_first_affected_stage",
  "observed_utc": "2026-10-11T08:28:13.127189Z",
  "source": "evaluate_pr_exp_07.py:232",
  "status": "STOPPED_BEFORE_EVALUATION",
  "unauthorized_fallback_applied": false
}

--- BEGIN swap_invariance_proof.json ---
{
  "comparison": "feature(P) == feature(swap(P)) exactly for every row",
  "failures": [],
  "rows_failed": 0,
  "rows_passed": 216,
  "rows_tested": 216,
  "status": "PASS"
}

--- BEGIN extraction_proof.json ---
{
  "extractor_input_contract": "exactly one unordered pair of observation-state mappings",
  "extractor_sha256": "8b136537189343f479506b9191908ce7d607805a29330b0890cf999c417e2d9c",
  "forbidden_fields_accessed": [],
  "order_counts": {
    "baseline_first": 113,
    "injected_first": 103
  },
  "pair_order_seed": 2026101107,
  "row_count": 216,
  "source_sha256": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
  "status": "PASS"
}

--- BEGIN attrition.json ---
{
  "expected_rows": 216,
  "excluded_rows": 216,
  "observed_source_rows": 216,
  "proof_missing_rows": 0,
  "retained_rows": 0,
  "rows_by_exclusion_reason": {
    "cluster_missing": 0,
    "feature_row_missing": 0,
    "label_missing": 0,
    "label_provenance_field_schema_mismatch": 216,
    "missing_pair_member": 0,
    "nonfinite_feature": 0,
    "proof_missing": 0,
    "row_alignment_failure": 0
  },
  "reason": "The frozen contract requires paired-carrier field expected_first_affected_stage; the carrier schema exposes expected_first_stage instead. The schema-mismatch fallback was not authorized and was not applied."
}

--- BEGIN pairing_rule.json ---
{
  "pair_membership": "Within one frozen multileaf_paired_artifacts.jsonl record, pair baseline_scores with injected_scores; no cross-record search, matching, or response-value selection is performed.",
  "pair_order_rule": "Process records in frozen file order; draw one bit per record from Python random.Random(2026101107) and reverse the two states exactly when the bit is 1.",
  "pair_order_seed": 2026101107,
  "proof": "extractor.extract accepts only a two-member sequence; extract_features.py accesses only baseline_scores and injected_scores before calling it. Pair membership is fixed by frozen materialization inside each record, while order is seed-driven and all seven per-leaf components are symmetric min/max/XOR/sum functions.",
  "response_value_read_during_pairing": false,
  "source_file": "research/stage_e_multileaf_20261010/run_multileaf_formal.py",
  "source_sha256": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4"
}

--- BEGIN feature_sets.json ---
{
  "components": [
    "presence_min",
    "presence_max",
    "presence_xor",
    "score_min",
    "score_max",
    "score_abs_diff",
    "score_sum"
  ],
  "direct_codebook": [
    "parse.field.hit_rate",
    "qa.retrieval.source_required",
    "parse.reconcile.equations"
  ],
  "full": [
    "parse.doc.ok",
    "parse.doc.throughput",
    "parse.table.regression",
    "parse.field.hit_rate",
    "parse.reconcile.equations",
    "qa.retrieval.source_required",
    "qa.faithfulness.judge",
    "qa.numeric.exact",
    "qa.numeric.number_grounding",
    "qa.citation.judge",
    "qa.refusal.judge",
    "qa.refusal.deterministic"
  ],
  "non_direct": [
    "parse.doc.ok",
    "parse.doc.throughput",
    "parse.table.regression",
    "qa.faithfulness.judge",
    "qa.numeric.exact",
    "qa.numeric.number_grounding",
    "qa.citation.judge",
    "qa.refusal.judge",
    "qa.refusal.deterministic"
  ],
  "score_scale": 10.0
}

--- BEGIN frozen_inputs.json ---
{
  "code_and_definitions": [
    {
      "path": "extractor.py",
      "sha256": "8b136537189343f479506b9191908ce7d607805a29330b0890cf999c417e2d9c"
    },
    {
      "path": "extract_features.py",
      "sha256": "3419dba7f52497ba1c1fa721022a1b0a39d9e645c0b6afb0078dc2b105f0e2be"
    },
    {
      "path": "evaluate_pr_exp_07.py",
      "sha256": "5f8310d0e86860915b55406b1a5eb82a94879f1ea2d73f6184780e84b0ce0dd1"
    },
    {
      "path": "feature_sets.json",
      "sha256": "931f2a2a4c1cf37a39a0b3cd26b6387a9a322387cec3f0702c5fa9ff9aac7a45"
    },
    {
      "path": "pairing_rule.json",
      "sha256": "873f7ca3b26d2f88c52c20cb6063cca5b333e67da6187cb2f278bc0565d05b40"
    }
  ],
  "implementation_contract_sha256": "f13a748fddd4f2aefb8fd28f921555caad84cb0563d582786a82dd5b3e73f4b3",
  "scientific_inputs": [
    {
      "path": "research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md",
      "sha256": "4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f"
    },
    {
      "path": "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json",
      "sha256": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4"
    },
    {
      "path": "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md",
      "sha256": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290"
    },
    {
      "path": "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md",
      "sha256": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569"
    },
    {
      "path": "research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-07.md",
      "sha256": "448fe0868fdfc427d88aef72f4094fc54610b3380cbb084ca93ddfef13563d3a"
    },
    {
      "path": "research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log",
      "sha256": "a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d"
    },
    {
      "path": "docs/research/multileaf_preresult_freeze_receipt_v1.md",
      "sha256": "a167f770f5b2e42cca69579ec60efafd233c7e8ed742c7178f244dbc6c78eaf1"
    },
    {
      "path": "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json",
      "sha256": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163"
    },
    {
      "path": "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json",
      "sha256": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693"
    },
    {
      "path": "research/stage_e_multileaf_20261010/run_multileaf_formal.py",
      "sha256": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4"
    },
    {
      "path": "config/eval_checkpoint_trees.json",
      "sha256": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl",
      "sha256": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl",
      "sha256": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_formal_results.json",
      "sha256": "ae9cf1cf37e2742e3895ec2bd0e4cf0c150a18c927eb9a618f612782b3d9cbb0"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_bootstrap_intervals.json",
      "sha256": "0dbfebc34aebafbafcebdcb7c944668ea8c235a87fd692454536a4444a91887a"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json",
      "sha256": "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_run_receipt.json",
      "sha256": "66ab58fa4847e6ee25567443310781628ee92bd952cfc3a469d323efd9c11956"
    }
  ]
}

--- BEGIN implementation_contract.md ---
# PR-EXP-07 Implementation Contract — frozen before feature-value observation

> experiment_id: `PR-EXP-07` | role: `ROBUSTNESS_ANTI_TAUTOLOGY` supporting evidence only; never a repair-count positive
> frozen_at_utc: `2026-10-11T08:24:52Z`
> prereg: `research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md`
> prereg_sha256: `4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f`
> qualification_gate: Loop C pre-result re-audit `PASS`; source `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log`, sha256 `a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d`
> freeze timing: extractor, evaluator, feature sets, pairing rule, seeds, classifier, metrics, taxonomy, and source hashes are fixed below before any experiment feature value was computed or observed. Key names and source-code structure were inspected; no response value, feature vector, shuffled-control value, or blind-vs-original metric was observed before this freeze.
> post-freeze rule: these files are read-only for this run. Any edit invalidates this contract and requires a new preregistration; no rescue tuning is allowed.

## 1. Goal, done conditions, exclusions, and stop conditions

- Goal: re-extract the frozen 216-row multi-leaf population from unordered raw observation-state pairs without exposing label or construction fields to the extractor, then evaluate the frozen three feature sets under nearest-centroid LOCO.
- Done conditions: exact row preservation; all-row swap proof; pairing/leakage proof; full/direct/non-direct metrics; shuffled-label control; identical-row blind-vs-original delta with CI; attrition table; exactly one canonical outcome label; receipt with input/output hashes, zero endpoint cost, unverified items, and deviations.
- Exclusions: no model/judge calls, training, services, databases, network, commit/push, prereg edits, shared-surface edits, hunting, label misuse, production probes, or repair-count accounting.
- Stop conditions: `INPUT_MISSING`; `PREREG_MISMATCH` or `HASH_MISMATCH`; forbidden action; qualification failure -> `NOT_EVALUABLE`; leakage, pairing, or swap proof failure -> `INVALID`. Negative/NULL/`NOT_EVALUABLE` results are valid and must not be rescued.
- Partial-delivery note: acknowledged as non-blocking bookkeeping only. Missing verdict-relevant inputs or proofs remain fail-closed (`INPUT_MISSING` or `NOT_EVALUABLE`) and are never silently converted to NULL.

## 2. Shared-surface hash verification completed before execution

All entries of `research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json` were verified in manifest insertion order before this contract was created:

| Surface | Identity rule | Pinned identity | Verified identity |
|---|---|---|---|
| `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | raw_sha256 | `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4` | same |
| `research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl` | raw_sha256 | `39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f` | same |
| `research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl` | raw_sha256 | `37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06` | same |
| `research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json` | raw_sha256 | `15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163` | same |
| `scripts/m1_statement_parser.py` | git_blob | `def5161dd17fc14345d340879174ed01e0277626` | `git rev-parse HEAD:scripts/m1_statement_parser.py` = `def5161dd17fc14345d340879174ed01e0277626`; `git hash-object scripts/m1_statement_parser.py` = `def5161dd17fc14345d340879174ed01e0277626` |
| `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md` | raw_sha256 | `4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290` | same |

Canonicalizer informational raw SHA-256 on this host: `747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b` (matches the pinned GB10 informational value). Raw SHA-256 is not the canonical identity under the 2026-10-11T08:30Z rule; the two git-blob identities above are binding.

## 3. Enumerated verdict-relevant inventory with fail-closed semantics

Any missing path, hash mismatch, schema mismatch, or unpinned item below is `INPUT_MISSING` and stops before scientific evaluation.

### Contract and qualification sources

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 1 | Preregistration v2 | `research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md` | `4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f` |
| 2 | Shared freeze | `research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json` | `d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4` |
| 3 | SOURCE_LOCAL_RESPONSE term sheet | `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md` | `4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290` |
| 4 | Binding residual addendum | `research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md` | `a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569` |
| 5 | Loop A assignment card | `research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-07.md` | `448fe0868fdfc427d88aef72f4094fc54610b3380cbb084ca93ddfef13563d3a` |
| 6 | Loop C pre-result PASS re-audit | `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log` | `a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d` |
| 7 | Recheck packet header | `research/positive_repair_20261011/recheck_packet_header.md` | `1f89dc8215b171ae0189757c0dcdd90caccfd245a3e75d72228dbe19392b7768` |

### Population, pairing, grouping, and label provenance

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 8 | Freeze receipt / cluster and fold rule | `docs/research/multileaf_preresult_freeze_receipt_v1.md` | `a167f770f5b2e42cca69579ec60efafd233c7e8ed742c7178f244dbc6c78eaf1` |
| 9 | Freeze manifest | `research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json` | `15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163` |
| 10 | Sample manifest / design-label source | `research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json` | `8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693` |
| 11 | Formal runner / pairing source | `research/stage_e_multileaf_20261010/run_multileaf_formal.py` | `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4` |
| 12 | Frozen leaf order source | `config/eval_checkpoint_trees.json` | `0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25` |

- Population: exactly 216 frozen carrier rows, 72 frozen clusters, three classes, three injections per cluster. Expected rows/clusters are part of the qualification gate.
- LOCO groups: `cluster_id` exactly as frozen in the paired carrier and freeze receipt; all rows for one cluster stay together. The cluster/LOCO rule is the receipt text above, referenced by hash.
- Label decoding map: `M -> M`, `R -> R`, `N -> N`, decoded only from the injection-design `stage` field after feature extraction. The evaluator asserts equality with `expected_first_affected_stage`; labels are never response-derived.
- Forbidden extractor knowledge: mutation family, stage, expected first stage, target checkpoint, gold outcome, sample namespace, sample ID, generation code, response vector, or contract checks.
- GB10-only drift/injection-map inputs: not applicable to PR-EXP-07; this run consumes the frozen multi-leaf carriers only.

### Frozen extractor, feature sets, and proof artifacts

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 13 | Label-blind extractor | `research/positive_repair_20261011/runs/PR-EXP-07/extractor.py` | `8b136537189343f479506b9191908ce7d607805a29330b0890cf999c417e2d9c` |
| 14 | Pair loader / seed rule | `research/positive_repair_20261011/runs/PR-EXP-07/extract_features.py` | `3419dba7f52497ba1c1fa721022a1b0a39d9e645c0b6afb0078dc2b105f0e2be` |
| 15 | Frozen evaluator | `research/positive_repair_20261011/runs/PR-EXP-07/evaluate_pr_exp_07.py` | `5f8310d0e86860915b55406b1a5eb82a94879f1ea2d73f6184780e84b0ce0dd1` |
| 16 | Feature-set definition | `research/positive_repair_20261011/runs/PR-EXP-07/feature_sets.json` | `931f2a2a4c1cf37a39a0b3cd26b6387a9a322387cec3f0702c5fa9ff9aac7a45` |
| 17 | Pairing-rule source and proof | `research/positive_repair_20261011/runs/PR-EXP-07/pairing_rule.json` | `873f7ca3b26d2f88c52c20cb6063cca5b333e67da6187cb2f278bc0565d05b40` |

Pairing-rule certification:

- Pair membership: within one already-frozen carrier record, pair `baseline_scores` with `injected_scores`. The formal materialization fixed those two states together for the same frozen sample/cluster before scoring; no cross-record matching or value-based search occurs.
- Pair order: frozen file order, one bit per record from `random.Random(2026101107)`; reverse exactly when the bit is 1. Seed `2026101107` is frozen.
- Code-inspection proof: `extractor.extract` accepts only a two-member sequence of observation-state mappings. `extract_features.py` accesses only `baseline_scores` and `injected_scores` before that call. The extractor does not import the formal runner and contains no forbidden label/contract fields. Pairing is therefore independent of response values.
- Swap proof: for every one of the 216 rows, `feature(P) == feature(swap(P))` exactly. Failure on any row is `INVALID`; no partial success substitutes for the all-row gate.

Feature vector: 12 frozen leaves in frozen tree order x 7 symmetric components = 84 dimensions:

`presence_min`, `presence_max`, `presence_xor`, `score_min`, `score_max`, `score_abs_diff`, `score_sum`.

Scores are divided by the frozen scale `10.0`; missing leaves are represented only through zero presence/score components. Each per-leaf component is computed with symmetric min/max/XOR/sum operations, so pair reversal cannot change it.

Frozen feature sets:

- Full: all 12 leaves, 84 dimensions, sha256 of definition `931f2a2a4c1cf37a39a0b3cd26b6387a9a322387cec3f0702c5fa9ff9aac7a45`.
- Direct-codebook subset: `parse.field.hit_rate`, `qa.retrieval.source_required`, `parse.reconcile.equations`; 21 dimensions; definition is fixed by the freeze manifest before feature observation, not by response values.
- Non-direct subset: the complementary nine leaves; 63 dimensions; same definition hash.

### Carrier and original-result inputs

| # | Parameter/artifact | Path | SHA-256 |
|---:|---|---|---|
| 18 | Paired raw-state carriers | `research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl` | `39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f` |
| 19 | Original prediction rows / identical-row anchor | `research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl` | `37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06` |
| 20 | Original frozen formal result | `research/stage_e_multileaf_20261010/results/multileaf_formal_results.json` | `ae9cf1cf37e2742e3895ec2bd0e4cf0c150a18c927eb9a618f612782b3d9cbb0` |
| 21 | Original bootstrap intervals | `research/stage_e_multileaf_20261010/results/multileaf_bootstrap_intervals.json` | `0dbfebc34aebafbafcebdcb7c944668ea8c235a87fd692454536a4444a91887a` |
| 22 | Original direct/non-direct ablation evidence | `research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json` | `0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d` |
| 23 | Original run receipt | `research/stage_e_multileaf_20261010/results/multileaf_run_receipt.json` | `66ab58fa4847e6ee25567443310781628ee92bd952cfc3a469d323efd9c11956` |

## 4. Frozen evaluation

- Classifier: deterministic Euclidean nearest-centroid, class serialization order `M,R,N`, leave exactly one frozen `cluster_id` out, all repeated injections for that cluster in the held-out fold.
- Tie rule: `np.isclose(..., rtol=0.0, atol=1e-12)`; any distance tie becomes `__TIE__` and scores incorrect.
- Primary point metrics: macro-F1 and top-1 accuracy. Raw outputs include per-class TP/FP/FN and F1 numerator/denominator, plus top-1 correct/total and confusion matrices.
- Chance: `1/3` for both reported chance references. Direct-codebook baseline is the frozen direct subset evaluated by the same LOCO classifier.
- Shuffled-label negative control: permute the 72 cluster labels as a multiset with `random.Random(2026101108)`, assign permuted labels back by frozen cluster, fit/score the full set against those permuted design labels. Seed `2026101108` is frozen.
- Bootstrap: 10,000 cluster resamples, seed `20261012`, percentile 2.5/97.5 CI. The blind-vs-original delta uses paired resamples of the same clusters and identical 216 rows for label-blind and original predictions.
- Original comparison: `delta = full_labelblind_macroF1 - original_frozen_macroF1`, with paired cluster-bootstrap CI. It is explicitly `NON_COMPARABLE_CLAIM_WISE`: the numeric delta is reported only because rows are identical; measurement objects differ.

## 5. SOURCE_LOCAL_RESPONSE operational binding

For PR-EXP-07, the binding operational test from `SOURCE_LOCAL_RESPONSE_v1.md` is applied rather than the over-inclusive prose definition: `full <= direct` is NULL, and ROBUST additionally requires the non-direct subset to clear `1/3 + 0.05`. A direct/source-local-concentrated gain cannot be narrated as robust or counted as a repair positive.

## 6. Frozen numeric criteria and total/disjoint taxonomy

Primary comparison point is macro-F1. `m = 0.05`, chance margin boundary `1/3 + 0.05 = 0.3833333333333333`.

Ordering is fixed as follows:

1. `NOT_EVALUABLE` first for undefined/missing feature rows, missing proof artifacts, qualification failure, or a residual region not covered by the prereg's four terminal cases; row-level attrition is mandatory.
2. `INVALID` second if any extractor leakage token is accessible, pairing proof fails, or any-row swap invariance fails.
3. `ROBUST` iff `full - direct >= 0.05` and `non_direct >= 1/3 + 0.05`.
4. `NULL` iff `full <= direct`.
5. `NULL_AT_CHANCE` iff `full > direct` and `abs(full - 1/3) <= 0.05`.
6. `NULL_DIRECT_CONCENTRATED` iff `full > direct`, full is outside the chance band, and `non_direct <= 1/3 + 0.05`.

This ordered rule is evaluated until one and only one label is assigned; each outcome record must land in exactly one bucket. Exactly one canonical outcome string is emitted. `NOT_EVALUABLE` is never merged into NULL.

Interpretation:

- `ROBUST` is supporting evidence only and never increases the repair count.
- Any degradation or NULL-family result retains a negative/NULL claim and emits an explicit claim-lowering note; it is never silent.

## 7. Attrition and outputs

Row-level attrition table must report expected/observed/retained/excluded rows plus counts for: missing pair member, non-finite feature, feature row missing, label missing, cluster missing, row alignment failure, and proof missing. Zero-count reasons remain explicit.

Required outputs under `research/positive_repair_20261011/runs/PR-EXP-07/`:

- `feature_values.jsonl`
- `extraction_proof.json`
- `swap_invariance_proof.json`
- `attrition.json`
- `result.json`
- `receipt.json`

`receipt.json` must contain: experiment ID; exactly one `outcome_label`; `prereg_sha256`; `implementation_contract_sha256`; start/end UTC; input and output SHA-256 maps; raw numerators/denominators and CIs; `model_calls=0` and all other endpoint counts zero; `unverified_items`; and `deviations`.

## 8. Deviations and unverified posture

- Planned deviations: none.
- Planned unverified items: none.
- If an actual deviation or unverified item arises, it must be recorded truthfully in `receipt.json`; it may not be hidden or used to rescue the result.

--- END PACKET ---
