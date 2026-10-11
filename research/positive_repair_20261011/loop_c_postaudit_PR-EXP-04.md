# Loop C Post-Result Independent Audit — PR-EXP-04 (GENERALIZATION_TEST)

You are the independent Loop C auditor. POST-RESULT audit of one completed Track P experiment. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Judge strictly from this packet; missing evidence -> UNVERIFIED. Do not modify, re-run, or rescue the result. Labels: FACT / INFERENCE / UNVERIFIED.

## Round context (disclosed facts)
- Track P first wave: PR-EXP-03/01 INTERVENTION_REPAIR, PR-EXP-04 GENERALIZATION_TEST (supporting-only; never counts toward the repair count), PR-EXP-07 ROBUSTNESS_ANTI_TAUTOLOGY.
- Registered class for PR-EXP-04: INVALID.
- Disclosed incidents, NOT scientific record: two engineering dispatch layers (a1 INPUT_MISSING x4; a2 HASH_MISMATCH x4) were fail-closed infrastructure failures with zero scientific side effects.
- SPECIAL: Registered INVALID came from a FROZEN_IMPLEMENTATION_FAILURE - KeyError: 'group_uid' at run_pr_exp_04.py:690 in build_scientific_result, raised AFTER generation and gates (preflight END_TO_END_PREFLIGHT_PASS; row/group gates PASS; harness equivalence 72/72 response vectors identical) and BEFORE metric evaluation; the agent refused post-generation source edits per freeze discipline; no rescue attempted (recorded). Judge whether INVALID is the correct class (vs MECHANISM_NOT_EVALUABLE), attribute the root cause (Loop A implementation bug vs Loop D contract), and state the minimal correct future action.
- Note: the descriptive machinery claims N1/N2 mechanisms were generated, gates passed, and the N1 harness-equivalence control passed; cross-mechanism metrics are NOT_COMPUTED. Do not treat anything as transfer evidence.

## Checklist (answer every item; cite packet fields)
1. Was the frozen prereg followed (population/intervention/baselines/metrics/taxonomy/stop rules; no threshold/rule hunting)?
2. Held-out independence (mechanism-disjoint + group-disjoint; UID overlap; freeze order)?
3. Any metric defined/modified after seeing results?
4. Measurement object consistent before/after?
5. Any source-local tautology in anything REPORTABLE from this packet?
6. Any label / stage / outcome leakage (incl. provenance fields, pairing, generation rules)?
7. Cost fairness (same-budget; zero model calls verified by packet)?
8. Are effect sizes / CIs recomputable from the packet as given? (state what you could and could not recompute)
9. Is the registered result classification reasonable and complete per the prereg taxonomy (POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE; NOT_EVALUABLE never merged into NULL)?
10. Manuscript role: should the SANER manuscript cite, bound, or decline this; any claim beyond evidence?

## Required output format
## INDEPENDENCE DECLARATION
## CHECKLIST
- C1..C10: one line each (FACT/INFERENCE/UNVERIFIED)
## FINDINGS (ordered by severity; cite packet fields)
## STRONGEST OBJECTION
## VERDICT: ENDORSE_CLASS | ENDORSE_WITH_NOTES | CHALLENGE_CLASS
## RECOMMENDED REGISTRY CLASS: (one of POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE)
## ROOT CAUSE ATTRIBUTION: (LOOP_A_IMPLEMENTATION_DEFECT | LOOP_D_CONTRACT_DEFECT | SCIENTIFIC_GATE | UNKNOWN) + one line
## RECOMMENDED MANUSCRIPT ROLE: (cite / bound / decline-cite / future-work) + one line
## RESIDUAL RISKS / NEXT ACTION
End with the literal line: POSTAUDIT_COMPLETE
--- BEGIN prereg v2 (PR-EXP-04) ---
# Prereg — PR-EXP-04: Cross-mechanism generalization (N1 vs N2)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-04 | candidate: PR-04 | role: GENERALIZATION_TEST (supporting evidence only; does NOT count toward the repair count)
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS

## 1. Hypothesis
The frozen stage-aligned signature for stage N generalizes across genuine mutation mechanisms: N1 operand-value perturbation vs N2 operator/coefficient perturbation. Tests whether instrumentation captures stage information beyond a single mutation fingerprint.

## 2. N2 requirements (all mandatory; else MECHANISM_NOT_EVALUABLE)
- genuine different mechanism (operator/coefficient/sign semantics change; not a string/parameter variant);
- deterministic;
- executor-owned downstream consequence (relation recomputed through the frozen reconciliation path);
- preregistered before any N2 result (this file);
- visibility/evaluability minimum gate: >= 2/3 of generated N2 injections produce >= 1 measurable response on the frozen 12-leaf surface under the frozen response rule AND >= 6 distinct held-out groups show response. Otherwise: MECHANISM_NOT_EVALUABLE (never a generalization failure);
- N2 selection rationale: determinism and executor ownership, NOT expected performance.

## 3. Population, groups, and split
- N1 rows: existing frozen N-stage carriers (unchanged; descriptive gate attrition reported).
- N2 rows: new deterministic N2 injections on held-out groups; generation rule frozen; UIDs disjoint from N1 groups; double-run byte-identical.
- "Group" (defined): stage-namespaced cluster as in the frozen freeze receipt (N:<uid>); for N2, groups = held-out table UIDs.
- mechanism-disjoint + group-disjoint; directions N1->N2 and N2->N1 (fit on one mechanism's groups; evaluate on the other's).
- Declarations: N1 and N2 are different populations by design; the visibility gate conditions N2 (N1 is frozen with its own observed 72/72 visibility; attrition reported for both); method-development history on N1 carriers is recorded as making the N2->N1 direction potentially optimistic.

## 4. Design and controls
Frozen nearest-centroid (tie=failure), LOCO on held-out groups; direct-codebook control mandatory; responsive-leaf-set overlap report mandatory; extraction frozen before N2 rows observed; no feature edits after observation.
- Feature surface ban: features may only use the frozen 12-leaf response surface + frozen contract-check outputs; provenance/mechanism-identifier features are forbidden (pinned in the implementation contract).
- Harness-equivalence control (mandatory): regenerate N1 rows through the N2 harness code path; require byte-identical response vectors vs frozen N1 rows; failure -> INVALID (harness confound not separable).

## 5. Primary metric and frozen baselines
macro-F1 / stage identification per direction; frozen baselines (numeric): chance top-1 = 1/3; uniform-class macro-F1 = 1/3; majority macro-F1 = 1/6; direct-codebook references from the frozen ablation (full 1.0 / direct 1.0 / non-direct 0.3333). Cluster bootstrap CIs.

## 6. Cost (added)
Zero model/judge calls; GB10 minutes; same-budget comparison = identical procedure both directions; freeze/audit overhead in the cost ledger.

## 7. Outcome taxonomy (complete, numeric)
Materiality margin m=0.05.
- SUPPORTED (supporting): both directions point >= 1/3 AND >= 1 direction CI-low > 1/3 AND direct-codebook control reported AND overlap report attached.
- NULL (fingerprint-bound): all directions |point − 1/3| <= m, or CI includes 1/3 without meeting SUPPORTED criteria. Documented; bounds the flagship claim.
- NEGATIVE: any direction point < 1/3 − m.
- NOT_EVALUABLE: N2 fails the visibility/evaluability gate (MECHANISM_NOT_EVALUABLE), or insufficient groups for a CI. Never merged into NULL.
- INVALID: leakage between mechanism sets; harness-equivalence failure; post-hoc tuning; prereg deviations.

## 8. Stop conditions
Any requirement violation; no tuning to recover transfer. This experiment never counts toward the repair count.
--- BEGIN receipt.json ---
{
  "experiment_id": "PR-EXP-04",
  "status": "INVALID",
  "prereg_sha256": "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
  "implementation_contract_sha256": "0fe3d3ec47b4b0671753fe7f8b9ba9f9a3077923b8a644bae30bdd5918dbc529",
  "start_utc": "2026-10-11T08:33:15Z",
  "end_utc": "2026-10-11T08:35:42Z",
  "input_hashes": [
    {
      "path": "config/eval_checkpoint_trees.json",
      "identity_rule": "raw_sha256",
      "sha256": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
      "status": "PASS"
    },
    {
      "path": "data/research/drift_v0/input/tatqa_tables.json",
      "identity_rule": "raw_sha256",
      "sha256": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
      "status": "PASS"
    },
    {
      "path": "data/research/drift_v0/output/injection_map.json",
      "identity_rule": "raw_sha256",
      "sha256": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
      "status": "PASS"
    },
    {
      "path": "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md",
      "identity_rule": "raw_sha256",
      "sha256": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
      "status": "PASS"
    },
    {
      "path": "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json",
      "identity_rule": "raw_sha256",
      "sha256": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
      "status": "PASS"
    },
    {
      "path": "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md",
      "identity_rule": "raw_sha256",
      "sha256": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
      "status": "PASS"
    },
    {
      "path": "research/positive_repair_20261011/preregs/PR-EXP-04_prereg_v2.md",
      "identity_rule": "raw_sha256",
      "sha256": "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_method_revision_20261009/build_multileaf_freeze.py",
      "identity_rule": "raw_sha256",
      "sha256": "1c78a7349b989b3701f1820c70d3b0c784c0428455ddabe0e176ff292c0c27c1",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_method_revision_20261009/multileaf_freeze.json",
      "identity_rule": "raw_sha256",
      "sha256": "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/multileaf_mechanism_generalization_audit.json",
      "identity_rule": "raw_sha256",
      "sha256": "bd412df8d7d8f38b748b6a01c3fd90d070baf48287ee81983d1595c1b9def6ef",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json",
      "identity_rule": "raw_sha256",
      "sha256": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json",
      "identity_rule": "raw_sha256",
      "sha256": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl",
      "identity_rule": "raw_sha256",
      "sha256": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl",
      "identity_rule": "raw_sha256",
      "sha256": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json",
      "identity_rule": "raw_sha256",
      "sha256": "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d",
      "status": "PASS"
    },
    {
      "path": "research/stage_e_multileaf_20261010/run_multileaf_formal.py",
      "identity_rule": "raw_sha256",
      "sha256": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
      "status": "PASS"
    },
    {
      "path": "scripts/m1_statement_parser.py",
      "identity_rule": "git_blob",
      "sha256": "def5161dd17fc14345d340879174ed01e0277626",
      "git_rev_parse": "def5161dd17fc14345d340879174ed01e0277626",
      "git_hash_object": "def5161dd17fc14345d340879174ed01e0277626",
      "raw_sha256_informational": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b",
      "status": "PASS"
    }
  ],
  "output_hashes": [
    {
      "path": "implementation_contract.md",
      "sha256": "0fe3d3ec47b4b0671753fe7f8b9ba9f9a3077923b8a644bae30bdd5918dbc529"
    },
    {
      "path": "implementation_contract.sha256",
      "sha256": "c9d5c72650ff24a22888d0310ad6060caba46307a24786a6f11e62096ab066b7"
    },
    {
      "path": "n1_harness_equivalence.json",
      "sha256": "92a45d0ff1508df8f699180453de0961807ad05bc7c74e7a7e32e8ca0d860cb8"
    },
    {
      "path": "n2_generation_run1.jsonl",
      "sha256": "3266afb95be799fa8d32fba5ab5597f57cd5cae43ee6bc670199a7ffc6d5d8df"
    },
    {
      "path": "n2_generation_run2.jsonl",
      "sha256": "3266afb95be799fa8d32fba5ab5597f57cd5cae43ee6bc670199a7ffc6d5d8df"
    },
    {
      "path": "preflight_receipt.json",
      "sha256": "4810e16add4c3a103fdb707e4078423ba0c6c53f99d731cb326729e948de996f"
    },
    {
      "path": "result.json",
      "sha256": "1d3b5877fe6fab638d42d7cbfcda6e31448afb465d1e91b2abb357351ded4994"
    },
    {
      "path": "run_pr_exp_04.py",
      "sha256": "945f936e229b9df252a9e495c4de45c56a5da0f32ccd049bec4f2587ec63c8f3"
    },
    {
      "path": "validate_pr_exp_04.py",
      "sha256": "dad54b0a68399c50a2697161603cc6f37e888a7f3588d6b7768a9aa8b45ba93f"
    }
  ],
  "raw_metrics": {
    "n1_harness_equivalence": {
      "numerator": 72,
      "denominator": 72,
      "mismatches": 0,
      "fraction": 1.0,
      "ci95": [1.0, 1.0],
      "ci_reason": "DETERMINISTIC_EXACT_CONTROL"
    },
    "n2_double_run": {
      "numerator": 1,
      "denominator": 1,
      "fraction": 1.0,
      "ci95": [1.0, 1.0],
      "ci_reason": "DETERMINISTIC_EXACT_CONTROL",
      "rows_each_run": 72
    },
    "n1_visibility": {
      "visible_rows": 72,
      "total_rows": 72,
      "row_fraction": 1.0,
      "row_ci95_cluster_bootstrap": [1.0, 1.0],
      "responding_groups": 24,
      "total_groups": 24,
      "group_fraction": 1.0,
      "group_ci95_cluster_bootstrap": [1.0, 1.0]
    },
    "n2_visibility": {
      "visible_rows": 72,
      "total_rows": 72,
      "row_gate_required": 48,
      "row_fraction": 1.0,
      "row_ci95_cluster_bootstrap": [1.0, 1.0],
      "responding_groups": 24,
      "total_groups": 24,
      "group_gate_required": 6,
      "group_fraction": 1.0,
      "group_ci95_cluster_bootstrap": [1.0, 1.0],
      "gate_pass": true
    },
    "responsive_leaf_overlap": {
      "intersection_numerator": 1,
      "union_denominator": 1,
      "jaccard": 1.0,
      "ci95": null,
      "ci_reason": "NOT_APPLICABLE_DETERMINISTIC_SET_OVERLAP"
    },
    "n1_to_n2_full": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "n1_to_n2_direct_codebook": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "n2_to_n1_full": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "n2_to_n1_direct_codebook": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "baselines": {
      "chance_top1": 0.3333333333333333,
      "uniform_class_macro_f1": 0.3333333333333333,
      "majority_macro_f1": 0.1666666666666667,
      "frozen_ablation_full": 1.0,
      "frozen_ablation_direct": 1.0,
      "frozen_ablation_non_direct": 0.3333
    }
  },
  "canonical_outcome_label": "INVALID",
  "canonical_outcome_label_satisfied": true,
  "supporting_only": true,
  "counts_toward_repair_count": false,
  "preflight_verification_level": "END_TO_END_PREFLIGHT_PASS",
  "cost": {
    "runtime_seconds": 147.0,
    "model_calls": 0,
    "judge_calls": 0,
    "network_calls": 0,
    "database_calls": 0,
    "training_calls": 0,
    "production_service_calls": 0
  },
  "unverified_items": [
    "N1-to-N2 and N2-to-N1 macro-F1/top-1 points and cluster-bootstrap CIs were not computed.",
    "Direct-codebook cross-direction control metrics were not computed.",
    "Final mechanism UID-leakage audit and independent FORMAL_RUN_PASS validation were not completed."
  ],
  "deviations": [
    {
      "type": "FROZEN_IMPLEMENTATION_FAILURE",
      "stage": "formal_run_after_generation_and_gates",
      "exception": "KeyError: 'group_uid'",
      "location": "run_pr_exp_04.py:690 in build_scientific_result",
      "consequence": "Cross-mechanism evaluation and independent metric recomputation were not executed.",
      "rescue_attempted": false,
      "post_generation_source_edit": false
    }
  ],
  "stop_reason": "The frozen implementation raised KeyError before population leakage finalization or metric evaluation; editing after generation would violate the implementation freeze, so execution stopped as INVALID."
}

--- BEGIN result.json ---
{
  "experiment_id": "PR-EXP-04",
  "namespace": "PR_EXP_04_CROSS_MECHANISM_N1_N2",
  "status": "INVALID",
  "result_status": "INVALID",
  "start_utc": "2026-10-11T08:33:15Z",
  "end_utc": "2026-10-11T08:34:20Z",
  "prereg_sha256": "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
  "implementation_contract_sha256": "0fe3d3ec47b4b0671753fe7f8b9ba9f9a3077923b8a644bae30bdd5918dbc529",
  "preflight_verification_level": "END_TO_END_PREFLIGHT_PASS",
  "input_hashes": {
    "config/eval_checkpoint_trees.json": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "data/research/drift_v0/input/tatqa_tables.json": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    "data/research/drift_v0/output/injection_map.json": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
    "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
    "research/positive_repair_20261011/preregs/PR-EXP-04_prereg_v2.md": "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
    "research/stage_e_method_revision_20261009/build_multileaf_freeze.py": "1c78a7349b989b3701f1820c70d3b0c784c0428455ddabe0e176ff292c0c27c1",
    "research/stage_e_method_revision_20261009/multileaf_freeze.json": "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
    "research/stage_e_multileaf_20261010/multileaf_mechanism_generalization_audit.json": "bd412df8d7d8f38b748b6a01c3fd90d070baf48287ee81983d1595c1b9def6ef",
    "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
    "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
    "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
    "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
    "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json": "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d",
    "research/stage_e_multileaf_20261010/run_multileaf_formal.py": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4"
  },
  "canonicalizer_identity": {
    "identity_rule": "git_blob",
    "expected": "def5161dd17fc14345d340879174ed01e0277626",
    "git_rev_parse": "def5161dd17fc14345d340879174ed01e0277626",
    "git_hash_object": "def5161dd17fc14345d340879174ed01e0277626",
    "raw_sha256_informational": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b",
    "status": "PASS"
  },
  "controls": {
    "n1_harness_equivalence": {
      "matched_rows": 72,
      "denominator": 72,
      "mismatched_rows": 0,
      "byte_identical": true,
      "fraction": 1.0,
      "ci95": [1.0, 1.0],
      "ci_reason": "DETERMINISTIC_EXACT_CONTROL",
      "n1_equivalence_json_sha256": "92a45d0ff1508df8f699180453de0961807ad05bc7c74e7a7e32e8ca0d860cb8"
    },
    "n2_double_run": {
      "identical_runs": 1,
      "denominator": 1,
      "rows_run1": 72,
      "rows_run2": 72,
      "byte_identical": true,
      "run1_sha256": "3266afb95be799fa8d32fba5ab5597f57cd5cae43ee6bc670199a7ffc6d5d8df",
      "run2_sha256": "3266afb95be799fa8d32fba5ab5597f57cd5cae43ee6bc670199a7ffc6d5d8df",
      "fraction": 1.0,
      "ci95": [1.0, 1.0],
      "ci_reason": "DETERMINISTIC_EXACT_CONTROL"
    },
    "uid_disjointness": {
      "status": "NOT_FINALIZED_AFTER_EXECUTION_FAILURE",
      "ci95": null,
      "ci_reason": "NOT_COMPUTED"
    }
  },
  "gates": {
    "n1_descriptive_visibility": {
      "visible_rows": 72,
      "total_rows": 72,
      "fraction": 1.0,
      "row_ci95_cluster_bootstrap": [1.0, 1.0],
      "responding_groups": 24,
      "total_groups": 24,
      "group_fraction": 1.0,
      "group_ci95_cluster_bootstrap": [1.0, 1.0],
      "bootstrap_seed": 20261012,
      "bootstrap_replicates": 10000
    },
    "n2_visibility": {
      "visible_rows": 72,
      "total_rows": 72,
      "row_gate_numerator_required": 48,
      "row_gate_denominator": 72,
      "fraction": 1.0,
      "row_ci95_cluster_bootstrap": [1.0, 1.0],
      "responding_groups": 24,
      "total_groups": 24,
      "group_gate_numerator_required": 6,
      "group_gate_denominator": 24,
      "group_fraction": 1.0,
      "group_ci95_cluster_bootstrap": [1.0, 1.0],
      "bootstrap_seed": 20261012,
      "bootstrap_replicates": 10000,
      "row_gate_pass": true,
      "group_gate_pass": true,
      "pass": true
    },
    "n1_attrition": {
      "generated": 72,
      "retained": 72,
      "attrition": 0
    },
    "n2_attrition": {
      "selected_groups": 24,
      "generated_rows": 72,
      "retained_rows": 72,
      "attrition": 0
    }
  },
  "responsive_leaf_overlap": {
    "n1_responsive_leaves": ["parse.reconcile.equations"],
    "n2_responsive_leaves": ["parse.reconcile.equations"],
    "intersection": ["parse.reconcile.equations"],
    "union": ["parse.reconcile.equations"],
    "intersection_numerator": 1,
    "union_denominator": 1,
    "jaccard": 1.0,
    "ci95": null,
    "ci_reason": "NOT_APPLICABLE_DETERMINISTIC_SET_OVERLAP"
  },
  "evaluation": {
    "n1_to_n2_full": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "n1_to_n2_direct_codebook": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "n2_to_n1_full": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    },
    "n2_to_n1_direct_codebook": {
      "status": "NOT_COMPUTED",
      "macro_f1": null,
      "macro_f1_ci95": null,
      "top1_accuracy": null,
      "top1_ci95": null,
      "reason": "FROZEN_IMPLEMENTATION_FAILURE_BEFORE_METRIC_EVALUATION"
    }
  },
  "baselines": {
    "chance_top1": 0.3333333333333333,
    "uniform_class_macro_f1": 0.3333333333333333,
    "majority_macro_f1": 0.1666666666666667,
    "frozen_ablation_direct_codebook_reference": {
      "full": 1.0,
      "direct": 1.0,
      "non_direct": 0.3333
    }
  },
  "canonical_outcome_label": "INVALID",
  "canonical_outcome_label_satisfied": true,
  "supporting_only": true,
  "counts_toward_repair_count": false,
  "deviations": [
    {
      "type": "FROZEN_IMPLEMENTATION_FAILURE",
      "stage": "formal_run_after_generation_and_gates",
      "exception": "KeyError: 'group_uid'",
      "location": "run_pr_exp_04.py:690 in build_scientific_result",
      "consequence": "Cross-mechanism evaluation and independent metric recomputation were not executed.",
      "rescue_attempted": false,
      "post_generation_source_edit": false
    }
  ],
  "stop_reason": "The frozen implementation raised KeyError before population leakage finalization or metric evaluation; editing after generation would violate the implementation freeze, so execution stopped as INVALID.",
  "unverified_items": [
    "N1-to-N2 and N2-to-N1 macro-F1/top-1 points and cluster-bootstrap CIs were not computed.",
    "Direct-codebook cross-direction control metrics were not computed.",
    "Final mechanism UID-leakage audit and independent FORMAL_RUN_PASS validation were not completed."
  ]
}

--- BEGIN preflight_receipt.json ---
{
  "analysis_plan": {
    "bootstrap_replicates": 10000,
    "bootstrap_seed": 20261012,
    "ci_method": "95% percentile cluster bootstrap",
    "classifier": "frozen nearest-centroid with Euclidean distance and tie=failure",
    "direct_control": "same classifier restricted to M/R/N direct leaves",
    "directions": [
      "N1_to_N2",
      "N2_to_N1"
    ],
    "estimands": [
      "macro_f1",
      "top1_accuracy"
    ],
    "exclusions": "fail-closed on missing input/hash/class/group",
    "loco": "remove target cluster from source population before centroid fitting",
    "permutation": "NOT_USED"
  },
  "commands": [
    "python3 research/positive_repair_20261011/runs/PR-EXP-04/run_pr_exp_04.py preflight"
  ],
  "completed_utc": "2026-10-11T08:33:15Z",
  "environment": {
    "numpy": "2.4.3",
    "platform": "Linux-6.17.0-1018-nvidia-aarch64-with-glibc2.39",
    "python": "3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0]"
  },
  "experiment_id": "PR-EXP-04",
  "hash_domain": {
    "canonicalizer_runtime": "git_blob",
    "raw_provenance": "raw_sha256",
    "verified_records": 17
  },
  "implementation_contract_sha256": "0fe3d3ec47b4b0671753fe7f8b9ba9f9a3077923b8a644bae30bdd5918dbc529",
  "integration_trace": {
    "leaf_count": 12,
    "n1_class_counts": {
      "M": 72,
      "N": 72,
      "R": 72
    },
    "n1_paired_rows": 216,
    "n1_regeneration_rows": 72,
    "n1_response_matrix_sha256": "13edbaa827f8410072bb6072be59efa2fd434829f2545e9e151f270d7068d221",
    "n2_class_counts": {
      "M": 72,
      "N": 72,
      "R": 72
    },
    "n2_double_run_byte_identical": true,
    "n2_generated_rows": 72,
    "n2_groups": 24,
    "n2_population_rows": 216,
    "n2_response_matrix_sha256": "5fe3d9d1da57990c214ab39aef09921f11f7801da89384f91e2594399d437649"
  },
  "model_calls": 0,
  "prereg_sha256": "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
  "previous_run_immutability": {
    "shared_hash_mismatches": 0,
    "status": "PASS"
  },
  "runtime_interface": {
    "missing_values_raise": true,
    "required_metadata": [
      "experiment_id",
      "prereg_sha256",
      "implementation_contract_sha256",
      "start_utc",
      "end_utc",
      "input_hashes",
      "output_hashes",
      "raw_metrics",
      "canonical_outcome_label",
      "cost",
      "unverified_items",
      "deviations"
    ],
    "silent_defaults": false
  },
  "sample_group_identity": {
    "leaf_count": 12,
    "n1_class_counts": {
      "M": 72,
      "N": 72,
      "R": 72
    },
    "n1_paired_rows": 216,
    "n1_regeneration_rows": 72,
    "n1_response_matrix_sha256": "13edbaa827f8410072bb6072be59efa2fd434829f2545e9e151f270d7068d221",
    "n2_class_counts": {
      "M": 72,
      "N": 72,
      "R": 72
    },
    "n2_double_run_byte_identical": true,
    "n2_generated_rows": 72,
    "n2_groups": 24,
    "n2_population_rows": 216,
    "n2_response_matrix_sha256": "5fe3d9d1da57990c214ab39aef09921f11f7801da89384f91e2594399d437649"
  },
  "scorer_binding": {
    "checkpoint_trees_sha256": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "measurement_object": "frozen 12-leaf response vector plus frozen contract checks",
    "runner_sha256": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
    "shared_fault_adapter": false,
    "stage_e_aggregation_changed": false
  },
  "split_determinism": {
    "cross_role_uid_overlap": "checked during formal execution; preflight construction uses the frozen exclusion rule",
    "replay_byte_identical": true,
    "rule": "ascending SHA-256 over frozen seed:namespace:key",
    "seed": 20261011
  },
  "started_utc": "2026-10-11T08:33:15Z",
  "test_output_hashes": {
    "py_compile_command": "python3 -m py_compile research/positive_repair_20261011/runs/PR-EXP-04/run_pr_exp_04.py research/positive_repair_20261011/runs/PR-EXP-04/validate_pr_exp_04.py",
    "py_compile_exit_code": 0,
    "py_compile_stdout_stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "verification_level": "END_TO_END_PREFLIGHT_PASS",
  "zero_output_scan": {
    "independent_validation_exists": false,
    "receipt_json_exists": false,
    "result_json_exists": false,
    "scientific_outputs_absent": true
  }
}

--- BEGIN n1_harness_equivalence.json ---
{
  "byte_identical_response_vectors": true,
  "expected_rows": 72,
  "frozen_n1_response_bytes_sha256": "7ada4e20c6271bb18c50cc2b14ebe409bef983664962975f727113ee62bd9dc0",
  "frozen_rows": 72,
  "matched_rows": 72,
  "mismatched_rows": 0,
  "mismatches": [],
  "regenerated_bytes_sha256": "90a84b0e2924db8904591b278868d3720116bbcefeb3f8dce63d0a9289405dfe",
  "regenerated_rows": 72
}

--- BEGIN run_pr_exp_04.py ---
#!/usr/bin/env python3
"""Deterministic PR-EXP-04 preflight, execution, and receipt finalization."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
RUN_DIR = Path(__file__).resolve().parent
TASK = ROOT / "research/positive_repair_20261011"
STAGE_E = ROOT / "research/stage_e_multileaf_20261010"
METHOD = ROOT / "research/stage_e_method_revision_20261009"

PREREG = TASK / "preregs/PR-EXP-04_prereg_v2.md"
SHARED_FREEZE = TASK / "contracts/shared_surface_freeze_v1.json"
SOURCE_TERM = TASK / "contracts/SOURCE_LOCAL_RESPONSE_v1.md"
RESIDUAL_NOTES = TASK / "loop_a_cards/residual_notes_v1.md"
LOOP_CARD = TASK / "loop_a_cards/loop_a_PR-EXP-04.md"
CONTRACT = RUN_DIR / "implementation_contract.md"
CONTRACT_HASH = RUN_DIR / "implementation_contract.sha256"
PREFLIGHT = RUN_DIR / "preflight_receipt.json"
VALIDATION = RUN_DIR / "independent_validation.json"
RESULT = RUN_DIR / "result.json"
RECEIPT = RUN_DIR / "receipt.json"

RUNNER = STAGE_E / "run_multileaf_formal.py"
FREEZE_GENERATOR = METHOD / "build_multileaf_freeze.py"
MULTILEAF_FREEZE = METHOD / "multileaf_freeze.json"
SAMPLE_MANIFEST = STAGE_E / "multileaf_preresult_sample_manifest.json"
PRE_FREEZE_MANIFEST = STAGE_E / "multileaf_preresult_freeze_manifest.json"
PAIRED = STAGE_E / "results/multileaf_paired_artifacts.jsonl"
PREDICTIONS = STAGE_E / "results/multileaf_prediction_rows.jsonl"
ABLATION = STAGE_E / "results/multileaf_signature_ablation.json"
MECHANISM_AUDIT = STAGE_E / "multileaf_mechanism_generalization_audit.json"
TABLES = ROOT / "data/research/drift_v0/input/tatqa_tables.json"
INJECTION_MAP = ROOT / "data/research/drift_v0/output/injection_map.json"
CHECKPOINT_TREES = ROOT / "config/eval_checkpoint_trees.json"
CANONICALIZER = ROOT / "scripts/m1_statement_parser.py"

EXPECTED_RAW_HASHES = {
    str(PREREG.relative_to(ROOT)): "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
    str(SHARED_FREEZE.relative_to(ROOT)): "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    str(SOURCE_TERM.relative_to(ROOT)): "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    str(RESIDUAL_NOTES.relative_to(ROOT)): "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
    str(RUNNER.relative_to(ROOT)): "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
    str(PAIRED.relative_to(ROOT)): "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
    str(PREDICTIONS.relative_to(ROOT)): "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
    str(PRE_FREEZE_MANIFEST.relative_to(ROOT)): "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
    str(SOURCE_TERM.relative_to(ROOT)): "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    str(TABLES.relative_to(ROOT)): "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    str(INJECTION_MAP.relative_to(ROOT)): "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
    str(CHECKPOINT_TREES.relative_to(ROOT)): "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    str(MULTILEAF_FREEZE.relative_to(ROOT)): "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
    str(SAMPLE_MANIFEST.relative_to(ROOT)): "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
    str(FREEZE_GENERATOR.relative_to(ROOT)): "1c78a7349b989b3701f1820c70d3b0c784c0428455ddabe0e176ff292c0c27c1",
    str(ABLATION.relative_to(ROOT)): "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d",
    str(MECHANISM_AUDIT.relative_to(ROOT)): "bd412df8d7d8f38b748b6a01c3fd90d070baf48287ee81983d1595c1b9def6ef",
}
CANONICALIZER_GIT_BLOB = "def5161dd17fc14345d340879174ed01e0277626"

CLASSES = ("M", "R", "N")
TIE_LABEL = "__TIE__"
DIRECT_LEAVES = {
    "M": "parse.field.hit_rate",
    "R": "qa.retrieval.source_required",
    "N": "parse.reconcile.equations",
}
SEED = 20261011
N2_GROUPS = 24
N2_ROWS_PER_GROUP = 3
BOOTSTRAP_SEED = 20261012
BOOTSTRAP_REPLICATES = 10_000
EPS = 1e-12
MARGIN = 0.05
CHANCE_TOP1 = 1.0 / 3.0
UNIFORM_MACRO_F1 = 1.0 / 3.0
MAJORITY_MACRO_F1 = 1.0 / 6.0


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_bytes(jsonl_bytes(rows))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_module(path: Path, name: str) -> Any:
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_hashes() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative, expected in EXPECTED_RAW_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"INPUT_MISSING: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"HASH_MISMATCH: {relative} expected={expected} actual={actual}")
        records.append({"path": relative, "identity_rule": "raw_sha256", "expected": expected, "actual": actual, "status": "PASS"})

    relative = str(CANONICALIZER.relative_to(ROOT))
    revision = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative}"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    blob = subprocess.run(
        ["git", "hash-object", relative], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    if revision != CANONICALIZER_GIT_BLOB or blob != CANONICALIZER_GIT_BLOB:
        raise RuntimeError(f"HASH_MISMATCH: canonicalizer git_blob revision={revision} blob={blob}")
    records.append({
        "path": relative,
        "identity_rule": "git_blob",
        "expected": CANONICALIZER_GIT_BLOB,
        "revision": revision,
        "worktree_blob": blob,
        "raw_sha256_informational": sha256_file(CANONICALIZER),
        "status": "PASS",
    })
    return records


def contract_payload() -> dict[str, Any]:
    if not CONTRACT.is_file() or not CONTRACT_HASH.is_file():
        raise RuntimeError("INPUT_MISSING: implementation contract or contract hash")
    declared = CONTRACT_HASH.read_text(encoding="utf-8").strip().split()[0]
    actual = sha256_file(CONTRACT)
    if declared != actual:
        raise RuntimeError(f"HASH_MISMATCH: implementation_contract expected={declared} actual={actual}")
    text = CONTRACT.read_text(encoding="utf-8")
    marker_start = "BEGIN_IMPLEMENTATION_CONTRACT_JSON"
    marker_end = "END_IMPLEMENTATION_CONTRACT_JSON"
    if marker_start not in text or marker_end not in text:
        raise RuntimeError("INPUT_MISSING: machine-readable implementation contract block")
    payload = json.loads(text.split(marker_start, 1)[1].split(marker_end, 1)[0].strip())
    for relative, expected in EXPECTED_RAW_HASHES.items():
        recorded = payload.get("input_hashes", {}).get(relative)
        if recorded != expected:
            raise RuntimeError(f"PREREG_MISMATCH: contract input hash differs for {relative}")
    script_hashes = payload.get("source_hashes", {})
    for path in (Path(__file__), RUN_DIR / "validate_pr_exp_04.py"):
        recorded = script_hashes.get(str(path.relative_to(ROOT)))
        actual = sha256_file(path)
        if recorded != actual:
            raise RuntimeError(f"HASH_MISMATCH: contract source hash differs for {path}")
    payload["_sha256"] = declared
    return payload


def stable_rank(namespace: str, key: str) -> str:
    return sha256_bytes(f"{SEED}:{namespace}:{key}".encode("utf-8"))


def identity_passes(identity: dict[str, Any], table: list[list[Any]], replacements: dict[tuple[int, int], float]) -> bool:
    return bool(runner.identity_passes(identity, table, replacements))


runner = load_module(RUNNER, "pr_exp04_frozen_runner")
generator = load_module(FREEZE_GENERATOR, "pr_exp04_frozen_generator")


def ordered_leaves() -> list[str]:
    tree = json.loads(CHECKPOINT_TREES.read_text(encoding="utf-8"))
    leaves = runner.leaf_order(tree)
    if len(leaves) != 12 or len(set(leaves)) != 12:
        raise RuntimeError(f"INPUT_MISSING: expected frozen 12-leaf surface, got {len(leaves)}")
    return leaves


def table_index() -> dict[str, list[list[Any]]]:
    payload = json.loads(TABLES.read_text(encoding="utf-8"))
    return {str(record["uid"]): record["table"] for record in payload}


def evaluate_sample(
    sample: dict[str, Any],
    table: list[list[Any]],
    leaves: list[str],
    mechanism: str,
) -> dict[str, Any]:
    source = sample["source_object"]
    identity = source["identity"]
    relation_transform = sample.get("relation_transform", "none")
    row, col = int(source["mutated_cell"]["row"]), int(source["mutated_cell"]["col"])
    raw_value = runner.parse_number(table[row][col])
    value_before = float(sample["value_before"])
    value_after = float(sample["value_after"])

    evaluated_identity = json.loads(json.dumps(identity))
    if relation_transform == "operator_drop":
        evaluated_identity["lhs_cells"] = [
            cell for cell in evaluated_identity["lhs_cells"]
            if not (int(cell["row"]) == row and int(cell["col"]) == col)
        ]
    elif relation_transform == "coefficient_duplicate":
        selected = next(
            cell for cell in evaluated_identity["lhs_cells"]
            if int(cell["row"]) == row and int(cell["col"]) == col
        )
        evaluated_identity["lhs_cells"] = [*evaluated_identity["lhs_cells"], json.loads(json.dumps(selected))]
    elif relation_transform not in {"none", "sign_flip"}:
        raise RuntimeError(f"unknown relation transform: {relation_transform}")

    replacements = {} if value_after == value_before else {(row, col): value_after}
    original_pass = identity_passes(identity, table, {})
    mutated_pass = identity_passes(evaluated_identity, table, replacements)
    source_hash = generator.json_hash(table) == source["table_sha256"]
    value_before_matches = raw_value is not None and abs(raw_value - value_before) <= runner.EPS
    value_changed = abs(value_after - value_before) > 0.01
    relation_changed = canonical_json(evaluated_identity) != canonical_json(identity)
    checks = {
        "source_hash": source_hash,
        "value_before_matches": value_before_matches,
        "value_changed": value_changed,
        "shape_unchanged": True,
        "original_identity_pass": original_pass,
        "mutated_identity_fail": not mutated_pass,
        "relation_changed_for_operator_or_coefficient": (
            relation_changed if relation_transform in {"operator_drop", "coefficient_duplicate"} else True
        ),
        "single_mechanism_edit": int(value_changed) + int(relation_changed) == 1,
    }
    response = {leaf: 0 for leaf in leaves}
    response[DIRECT_LEAVES["N"]] = int(original_pass and not mutated_pass)
    checks["direct_leaf_response"] = response[DIRECT_LEAVES["N"]] == 1
    return {
        "sample_id": sample["sample_id"],
        "stage": "N",
        "mechanism": mechanism,
        "group_uid": str(source["uid"]),
        "cluster_id": sample["cluster_id"],
        "repeat_within_cluster": int(sample["repeat_within_cluster"]),
        "relation_transform": relation_transform,
        "contract_checks": checks,
        "contract_pass": all(checks.values()),
        "baseline_scores": {DIRECT_LEAVES["N"]: 10.0 if original_pass else 0.0},
        "injected_scores": {DIRECT_LEAVES["N"]: 10.0 if mutated_pass else 0.0},
        "response_vector": response,
    }


def regenerate_n1(leaves: list[str], tables: dict[str, list[list[Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    freeze = json.loads(MULTILEAF_FREEZE.read_text(encoding="utf-8"))
    frozen_rows = [row for row in read_jsonl(PAIRED) if row["stage"] == "N"]
    by_id = {row["sample_id"]: row for row in frozen_rows}
    regenerated: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for sample in freeze["samples"]["N"]:
        row = evaluate_sample(sample, tables[sample["source_object"]["uid"]], leaves, "N1")
        regenerated.append(row)
        frozen = by_id.get(row["sample_id"])
        frozen_bytes = None if frozen is None else canonical_json(frozen["response_vector"]).encode("utf-8")
        regenerated_bytes = canonical_json(row["response_vector"]).encode("utf-8")
        if frozen_bytes != regenerated_bytes:
            mismatches.append({
                "sample_id": row["sample_id"],
                "frozen_sha256": None if frozen_bytes is None else sha256_bytes(frozen_bytes),
                "regenerated_sha256": sha256_bytes(regenerated_bytes),
            })
    report = {
        "expected_rows": 72,
        "regenerated_rows": len(regenerated),
        "frozen_rows": len(frozen_rows),
        "byte_identical_response_vectors": len(regenerated) == len(frozen_rows) == 72 and not mismatches,
        "matched_rows": 72 - len(mismatches),
        "mismatched_rows": len(mismatches),
        "mismatches": mismatches,
        "regenerated_bytes_sha256": sha256_bytes(jsonl_bytes(regenerated)),
        "frozen_n1_response_bytes_sha256": sha256_bytes(
            b"".join(canonical_json(row["response_vector"]).encode("utf-8") + b"\n" for row in frozen_rows)
        ),
    }
    return regenerated, report


def excluded_table_uids() -> set[str]:
    manifest = json.loads(SAMPLE_MANIFEST.read_text(encoding="utf-8"))
    frozen = {
        str(row["source_uid"])
        for row in manifest["rows"]
        if row.get("source_uid") is not None
    }
    injection = json.loads(INJECTION_MAP.read_text(encoding="utf-8"))
    mapped = {str(item["uid"]) for item in injection["mapping"]}
    return frozen | mapped


def eligible_n2_groups(tables: dict[str, list[list[Any]]]) -> list[dict[str, Any]]:
    excluded = excluded_table_uids()
    candidates: list[dict[str, Any]] = []
    for uid, table in tables.items():
        if uid in excluded:
            continue
        identities = generator.find_numeric_identities(table)
        if not identities:
            continue
        operands: dict[tuple[int, int], dict[str, Any]] = {}
        for identity in identities:
            for cell in identity["lhs_cells"]:
                row, col = int(cell["row"]), int(cell["col"])
                value = runner.parse_number(table[row][col])
                if value is None or abs(value - float(cell["value"])) > 0.01 or abs(value) <= 0.02:
                    continue
                operands.setdefault((row, col), {"cell": cell, "identity": identity})
        if len(operands) >= N2_ROWS_PER_GROUP:
            candidates.append({"uid": uid, "table": table, "identities": identities, "operands": operands})
    candidates.sort(key=lambda item: stable_rank("pr-exp-04-n2-cluster", item["uid"]))
    return candidates


def generate_n2(leaves: list[str], tables: dict[str, list[list[Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = eligible_n2_groups(tables)
    selected = candidates[:N2_GROUPS]
    rows: list[dict[str, Any]] = []
    transforms = ("operator_drop", "coefficient_duplicate", "sign_flip")
    for candidate in selected:
        uid = candidate["uid"]
        ordered = sorted(
            candidate["operands"].items(),
            key=lambda item: stable_rank(
                "pr-exp-04-n2-operand",
                f"{uid}:{item[0][0]}:{item[0][1]}:{canonical_json(item[1]['identity'])}",
            ),
        )[:N2_ROWS_PER_GROUP]
        for repeat, ((row, col, ), record) in enumerate(ordered, start=1):
            transform = transforms[repeat - 1]
            identity = record["identity"]
            value = float(record["cell"]["value"])
            value_after = -value if transform == "sign_flip" else value
            sample = {
                "sample_id": f"N2-{uid}-r{row}c{col}-{repeat}",
                "cluster_id": f"N2:{uid}",
                "repeat_within_cluster": repeat,
                "relation_transform": transform,
                "value_before": value,
                "value_after": value_after,
                "source_object": {
                    "uid": uid,
                    "table_sha256": generator.json_hash(candidate["table"]),
                    "identity": identity,
                    "mutated_cell": {"row": row, "col": col},
                },
            }
            rows.append(evaluate_sample(sample, candidate["table"], leaves, "N2"))
    metadata = {
        "eligible_groups": len(candidates),
        "selected_groups": len(selected),
        "expected_groups": N2_GROUPS,
        "generated_rows": len(rows),
        "expected_rows": N2_GROUPS * N2_ROWS_PER_GROUP,
        "selected_group_uids": [candidate["uid"] for candidate in selected],
        "excluded_frozen_or_drift_uid_count": len(excluded_table_uids()),
        "generation_rule": {
            "namespace": "pr-exp-04-n2-cluster / pr-exp-04-n2-operand",
            "seed": SEED,
            "transforms_in_repeat_order": list(transforms),
            "eligibility": (
                "UID absent from frozen M/N table UIDs and drift injection-map UIDs; "
                "at least one frozen row/column total identity; at least three distinct LHS cells "
                "whose parsed magnitude is >0.02 and matches the frozen identity cell value within 0.01"
            ),
        },
    }
    return rows, metadata


def visibility(rows: list[dict[str, Any]]) -> dict[str, Any]:
    group_values: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        group_values[row["group_uid"]].append(int(sum(row["response_vector"].values()) > 0))
    visible = sum(sum(values) for values in group_values.values())
    total = sum(len(values) for values in group_values.values())
    responding_groups = sum(any(values) for values in group_values.values())
    group_count = len(group_values)
    threshold_rows = math.ceil((2.0 / 3.0) * total) if total else None
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    group_ids = sorted(group_values)
    row_bootstrap = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    group_bootstrap = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    group_binary = np.asarray([int(any(group_values[group])) for group in group_ids], dtype=float)
    for index in range(BOOTSTRAP_REPLICATES):
        sampled = rng.choice(len(group_ids), size=len(group_ids), replace=True)
        numerator = sum(sum(group_values[group_ids[position]]) for position in sampled)
        denominator = sum(len(group_values[group_ids[position]]) for position in sampled)
        row_bootstrap[index] = numerator / denominator if denominator else 0.0
        group_bootstrap[index] = float(group_binary[sampled].mean())
    return {
        "visible_rows": visible,
        "total_rows": total,
        "visible_fraction": visible / total if total else 0.0,
        "visible_fraction_ci95_cluster_bootstrap": [
            round(float(np.quantile(row_bootstrap, 0.025)), 6),
            round(float(np.quantile(row_bootstrap, 0.975)), 6),
        ],
        "row_gate_numerator_required": threshold_rows,
        "row_gate_denominator": total,
        "responding_groups": responding_groups,
        "total_groups": group_count,
        "responding_group_fraction": responding_groups / group_count if group_count else 0.0,
        "responding_group_fraction_ci95_cluster_bootstrap": [
            round(float(np.quantile(group_bootstrap, 0.025)), 6),
            round(float(np.quantile(group_bootstrap, 0.975)), 6),
        ],
        "group_gate_numerator_required": 6,
        "group_gate_denominator": group_count,
        "row_gate_pass": threshold_rows is not None and visible >= threshold_rows,
        "group_gate_pass": responding_groups >= 6,
        "pass": bool(threshold_rows is not None and visible >= threshold_rows and responding_groups >= 6),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
    }


def row_key(row: dict[str, Any], leaves: list[str]) -> dict[str, Any]:
    return {
        "sample_id": row["sample_id"],
        "cluster_id": row["cluster_id"],
        "stage": row["stage"],
        "mechanism": row["mechanism"],
        "response_vector": {leaf: int(row["response_vector"][leaf]) for leaf in leaves},
    }


def macro_components(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    per_class: dict[str, Any] = {}
    f1_values: list[float] = []
    for label in CLASSES:
        tp = int(np.sum((y_true == label) & (y_pred == label)))
        fp = int(np.sum((y_true != label) & (y_pred == label)))
        fn = int(np.sum((y_true == label) & (y_pred != label)))
        numerator = 2 * tp
        denominator = 2 * tp + fp + fn
        f1 = 0.0 if denominator == 0 else numerator / denominator
        per_class[label] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "f1_numerator": numerator,
            "f1_denominator": denominator,
            "f1": f1,
        }
        f1_values.append(f1)
    return {
        "per_class": per_class,
        "macro_f1_sum_numerator": sum(f1_values),
        "macro_f1_class_denominator": len(CLASSES),
        "macro_f1": float(np.mean(f1_values)),
    }


def predict_cross(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    leaves: list[str],
    feature_indices: list[int],
) -> tuple[np.ndarray, np.ndarray, int]:
    source_x = np.asarray([[row["response_vector"][leaves[index]] for index in feature_indices] for row in source_rows], dtype=float)
    source_y = np.asarray([row["stage"] for row in source_rows], dtype=object)
    source_clusters = np.asarray([row["cluster_id"] for row in source_rows], dtype=object)
    target_x = np.asarray([[row["response_vector"][leaves[index]] for index in feature_indices] for row in target_rows], dtype=float)
    target_clusters = np.asarray([row["cluster_id"] for row in target_rows], dtype=object)
    predictions = np.empty(len(target_x), dtype=object)
    margins = np.empty(len(target_x), dtype=float)
    for target_index, cluster in enumerate(target_clusters):
        train_mask = source_clusters != cluster
        if not np.all([np.any(train_mask & (source_y == label)) for label in CLASSES]):
            raise RuntimeError(f"missing training class after LOCO for cluster {cluster}")
        centroids = np.vstack([source_x[train_mask & (source_y == label)].mean(axis=0) for label in CLASSES])
        distances = np.sqrt(((target_x[target_index][None, :] - centroids) ** 2).sum(axis=1))
        minimum = float(distances.min())
        tied = np.isclose(distances, minimum, rtol=0.0, atol=EPS)
        if int(tied.sum()) > 1:
            predictions[target_index] = TIE_LABEL
            margins[target_index] = 0.0
        else:
            predictions[target_index] = CLASSES[int(np.argmin(distances))]
            ordered = np.sort(distances)
            margins[target_index] = float(ordered[1] - ordered[0])
    return predictions, margins, int(np.sum(predictions == TIE_LABEL))


def bootstrap_ci(
    target_rows: list[dict[str, Any]],
    y_pred: np.ndarray,
) -> dict[str, list[float]]:
    y_true = np.asarray([row["stage"] for row in target_rows], dtype=object)
    clusters = np.asarray([row["cluster_id"] for row in target_rows], dtype=object)
    unique = np.unique(clusters)
    indices = {cluster: np.flatnonzero(clusters == cluster) for cluster in unique}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    macro = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    top = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for index in range(BOOTSTRAP_REPLICATES):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        selected = np.concatenate([indices[cluster] for cluster in sampled])
        macro[index] = macro_components(y_true[selected], y_pred[selected])["macro_f1"]
        top[index] = float(np.mean(y_true[selected] == y_pred[selected]))
    return {
        "macro_f1_ci95_cluster_bootstrap": [
            round(float(np.quantile(macro, 0.025)), 6),
            round(float(np.quantile(macro, 0.975)), 6),
        ],
        "top1_ci95_cluster_bootstrap": [
            round(float(np.quantile(top, 0.025)), 6),
            round(float(np.quantile(top, 0.975)), 6),
        ],
    }


def metric_block(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    leaves: list[str],
    feature_indices: list[int],
) -> dict[str, Any]:
    predictions, margins, tie_count = predict_cross(source_rows, target_rows, leaves, feature_indices)
    y_true = np.asarray([row["stage"] for row in target_rows], dtype=object)
    components = macro_components(y_true, predictions)
    correct = int(np.sum(y_true == predictions))
    total = len(y_true)
    confusion = {
        true: {pred: int(np.sum((y_true == true) & (predictions == pred))) for pred in (*CLASSES, TIE_LABEL)}
        for true in CLASSES
    }
    ci = bootstrap_ci(target_rows, predictions)
    return {
        "rows": total,
        "groups": len({row["cluster_id"] for row in target_rows}),
        "macro_f1": components,
        "top1_accuracy": {
            "correct": correct,
            "denominator": total,
            "point": correct / total if total else 0.0,
        },
        "confusion": confusion,
        "tie_count": tie_count,
        "tie_rate": {"numerator": tie_count, "denominator": total, "point": tie_count / total if total else 0.0},
        **ci,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "feature_leaf_count": len(feature_indices),
        "feature_leaves": [leaves[index] for index in feature_indices],
        "distance_margins_min": float(margins.min()) if len(margins) else None,
        "distance_margins_max": float(margins.max()) if len(margins) else None,
    }


def overlap_block(n1_rows: list[dict[str, Any]], n2_rows: list[dict[str, Any]], leaves: list[str]) -> dict[str, Any]:
    def responsive(rows: list[dict[str, Any]]) -> list[str]:
        return [
            leaf for leaf in leaves
            if sum(int(row["response_vector"][leaf]) for row in rows) > 0
        ]
    n1_set = set(responsive(n1_rows))
    n2_set = set(responsive(n2_rows))
    intersection = sorted(n1_set & n2_set)
    union = sorted(n1_set | n2_set)
    return {
        "n1_responsive_leaves": sorted(n1_set),
        "n2_responsive_leaves": sorted(n2_set),
        "intersection": intersection,
        "union": union,
        "intersection_numerator": len(intersection),
        "union_denominator": len(union),
        "jaccard": len(intersection) / len(union) if union else 1.0,
        "ci95": None,
        "ci_reason": "NOT_APPLICABLE_DETERMINISTIC_SET_OVERLAP",
        "response_counts_n1": {leaf: sum(int(row["response_vector"][leaf]) for row in n1_rows) for leaf in leaves},
        "response_counts_n2": {leaf: sum(int(row["response_vector"][leaf]) for row in n2_rows) for leaf in leaves},
    }


def classify(result: dict[str, Any]) -> tuple[str, list[str]]:
    deviations = list(result.get("deviations", []))
    harness_ok = result["controls"]["n1_harness_equivalence"]["byte_identical_response_vectors"]
    deterministic_ok = result["controls"]["n2_double_run"]["byte_identical"]
    leakage_ok = result["controls"]["leakage_audit"]["pass"]
    if deviations or not harness_ok or not deterministic_ok or not leakage_ok:
        return "INVALID", deviations
    if not result["gates"]["visibility"]["pass"] or result["controls"]["insufficient_groups_for_ci"]:
        return "NOT_EVALUABLE", deviations
    full_points = [
        result["evaluation"]["n1_to_n2"]["full_surface"]["macro_f1"]["macro_f1"],
        result["evaluation"]["n2_to_n1"]["full_surface"]["macro_f1"]["macro_f1"],
    ]
    if any(point < CHANCE_TOP1 - MARGIN for point in full_points):
        return "NEGATIVE", deviations
    cis = [
        result["evaluation"]["n1_to_n2"]["full_surface"]["macro_f1_ci95_cluster_bootstrap"],
        result["evaluation"]["n2_to_n1"]["full_surface"]["macro_f1_ci95_cluster_bootstrap"],
    ]
    supported = (
        all(point >= UNIFORM_MACRO_F1 for point in full_points)
        and any(ci[0] > UNIFORM_MACRO_F1 for ci in cis)
        and result["controls"]["direct_codebook_reported"]
        and result["controls"]["responsive_leaf_overlap_reported"]
    )
    return ("SUPPORTED" if supported else "NULL"), deviations


def assemble_populations(n1_paired: list[dict[str, Any]], n2_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    n1 = [dict(row, mechanism="N1") for row in n1_paired]
    anchors = [dict(row, mechanism="N1") for row in n1_paired if row["stage"] in {"M", "R"}]
    n2 = anchors + n2_rows
    return n1, n2


def population_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage = Counter(row["stage"] for row in rows)
    return {
        "rows": len(rows),
        "groups": len({row["cluster_id"] for row in rows}),
        "class_counts": {label: int(by_stage[label]) for label in CLASSES},
        "mechanism_counts": dict(Counter(row["mechanism"] for row in rows)),
    }


def build_scientific_result() -> dict[str, Any]:
    hash_records = verify_hashes()
    contract = contract_payload()
    leaves = ordered_leaves()
    tables = table_index()
    n1_regen, equivalence = regenerate_n1(leaves, tables)
    if not equivalence["byte_identical_response_vectors"]:
        raise RuntimeError("INVALID: N1 harness-equivalence failure")
    n1_paired = read_jsonl(PAIRED)
    n2_rows_a, metadata_a = generate_n2(leaves, tables)
    n2_rows_b, metadata_b = generate_n2(leaves, tables)
    bytes_a = jsonl_bytes(n2_rows_a)
    bytes_b = jsonl_bytes(n2_rows_b)
    double_run = {
        "byte_identical": bytes_a == bytes_b and canonical_json(metadata_a) == canonical_json(metadata_b),
        "run1_sha256": sha256_bytes(bytes_a),
        "run2_sha256": sha256_bytes(bytes_b),
        "metadata_sha256": sha256_bytes(canonical_json(metadata_a).encode("utf-8")),
        "metadata": metadata_a,
    }
    if not double_run["byte_identical"]:
        raise RuntimeError("INVALID: N2 double-run mismatch")
    write_jsonl(RUN_DIR / "n2_generation_run1.jsonl", n2_rows_a)
    write_jsonl(RUN_DIR / "n2_generation_run2.jsonl", n2_rows_b)
    write_json(RUN_DIR / "n1_harness_equivalence.json", equivalence)

    n1_population, n2_population = assemble_populations(n1_paired, n2_rows_a)
    n1_n_rows = [row for row in n1_population if row["stage"] == "N"]
    n2_n_rows = [row for row in n2_population if row["stage"] == "N"]
    n1_uids = {row["group_uid"] for row in n1_n_rows}
    n2_uids = {row["group_uid"] for row in n2_n_rows}
    frozen_uids = excluded_table_uids()
    counts_n1 = population_counts(n1_population)
    counts_n2 = population_counts(n2_population)
    class_count_ok = all(
        counts_n1["class_counts"][label] == counts_n2["class_counts"][label] == 72
        for label in CLASSES
    )
    leakage = {
        "n1_n2_uid_intersection": sorted(n1_uids & n2_uids),
        "n1_n2_uid_intersection_count": len(n1_uids & n2_uids),
        "n2_vs_excluded_frozen_or_drift_uid_intersection": sorted(n2_uids & frozen_uids),
        "n2_vs_excluded_frozen_or_drift_uid_intersection_count": len(n2_uids & frozen_uids),
        "n1_class_counts": counts_n1["class_counts"],
        "n2_class_counts": counts_n2["class_counts"],
        "class_counts_balanced_72_each": class_count_ok,
        "shared_M_R_stage_anchor_rows": sum(row["stage"] in {"M", "R"} for row in n1_population),
        "shared_anchor_loco_rule": "For every target cluster, that cluster is removed from the source population before centroids are fit.",
        "mechanism_feature_ban": (
            "Features may only use the frozen 12-leaf response surface + frozen contract-check outputs; "
            "provenance/mechanism-identifier features are forbidden."
        ),
        "mechanism_identifiers_excluded_from_features": True,
        "pass": (
            len(n1_uids & n2_uids) == 0
            and len(n2_uids & frozen_uids) == 0
        ),
    }
    visibility_n2 = visibility(n2_rows_a)
    n1_visibility = visibility(n1_n_rows)
    direct_indices = [leaves.index(DIRECT_LEAVES[label]) for label in CLASSES]
    all_indices = list(range(len(leaves)))
    evaluation = {
        "n1_to_n2": {
            "source_population": counts_n1,
            "target_population": counts_n2,
            "full_surface": metric_block(n1_population, n2_population, leaves, all_indices),
            "direct_codebook": metric_block(n1_population, n2_population, leaves, direct_indices),
        },
        "n2_to_n1": {
            "source_population": counts_n2,
            "target_population": counts_n1,
            "full_surface": metric_block(n2_population, n1_population, leaves, all_indices),
            "direct_codebook": metric_block(n2_population, n1_population, leaves, direct_indices),
        },
    }
    overlap = overlap_block(n1_n_rows, n2_n_rows, leaves)
    result: dict[str, Any] = {
        "experiment_id": "PR-EXP-04",
        "namespace": "PR_EXP_04_CROSS_MECHANISM_N1_N2",
        "generated_at_utc": now_utc(),
        "prereg_sha256": EXPECTED_RAW_HASHES[str(PREREG.relative_to(ROOT))],
        "implementation_contract_sha256": contract["_sha256"],
        "preflight_verification_level": json.loads(PREFLIGHT.read_text(encoding="utf-8"))["verification_level"],
        "hash_verification": hash_records,
        "frozen_surface": {
            "leaf_count": len(leaves),
            "leaves": leaves,
            "direct_codebook": DIRECT_LEAVES,
        },
        "population_contract": {
            "n1": counts_n1,
            "n2": counts_n2,
            "n1_unchanged": len(n1_population) == 216,
            "n2_construction": "Frozen M/R stage anchors plus 72 new N2 rows on 24 disjoint held-out table UIDs.",
            "shared_anchor_disclosure": (
                "M/R rows are common stage anchors because only the N mechanism changes; "
                "LOCO removes every target cluster from source fitting."
            ),
            "n2_to_n1_optimism_declaration": (
                "Method-development history on N1 carriers makes N2->N1 potentially optimistic."
            ),
        },
        "controls": {
            "n1_harness_equivalence": equivalence,
            "n2_double_run": double_run,
            "leakage_audit": leakage,
            "direct_codebook_reported": True,
            "responsive_leaf_overlap_reported": True,
            "insufficient_groups_for_ci": (
                len({row["group_uid"] for row in n1_n_rows}) < 6
                or len({row["group_uid"] for row in n2_n_rows}) < 6
            ),
            "post_hoc_tuning": False,
            "shared_generation_harness_confound": (
                "N1 and N2 response extraction share the frozen reconciliation harness; "
                "harness equivalence controls implementation confounding but cannot rule out harness-specific visibility."
            ),
        },
        "gates": {
            "n1_descriptive_visibility": n1_visibility,
            "visibility": visibility_n2,
            "n1_attrition": {"generated": 72, "retained": 72, "attrition": 0},
            "n2_attrition": {
                "eligible_groups": metadata_a["eligible_groups"],
                "selected_groups": metadata_a["selected_groups"],
                "generated_rows": metadata_a["generated_rows"],
                "retained_rows": len(n2_rows_a),
                "attrition": metadata_a["generated_rows"] - len(n2_rows_a),
            },
        },
        "evaluation": evaluation,
        "responsive_leaf_overlap": overlap,
        "baselines": {
            "chance_top1": CHANCE_TOP1,
            "uniform_class_macro_f1": UNIFORM_MACRO_F1,
            "majority_macro_f1": MAJORITY_MACRO_F1,
            "frozen_ablation_direct_codebook_reference": {"full": 1.0, "direct": 1.0, "non_direct": 0.3333},
        },
        "source_local_operational_test": {
            "binding": (
                "PR-EXP-04 fingerprint-bound NULL branch + direct-codebook control + "
                "responsive-leaf overlap report operationalize source-locality."
            ),
            "fingerprint_bound_branch_reported": True,
            "duplicate_catch_analysis": "NOT_APPLICABLE_NO_NEW_ORACLE_CHANNEL",
            "specificity_no_op_arms": "NOT_APPLICABLE_NO_NEW_ORACLE_CHANNEL",
            "constant_one_rule": "NOT_APPLICABLE_NO_NEW_ORACLE_CHANNEL",
        },
        "deviations": [],
        "supporting_only": True,
        "counts_toward_repair_count": False,
    }
    label, deviations = classify(result)
    result["canonical_outcome_label"] = label
    result["canonical_outcome_label_satisfied"] = label in {"SUPPORTED", "NULL", "NEGATIVE", "NOT_EVALUABLE", "INVALID"}
    result["deviations"] = deviations
    result["result_status"] = "COMPLETE" if label in {"SUPPORTED", "NULL", "NEGATIVE"} else label
    write_json(RESULT, result)
    write_json(RUN_DIR / "execution_metadata.json", {
        "formal_started_at_utc": result["generated_at_utc"],
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "model_calls": 0,
        "network_calls": 0,
        "database_calls": 0,
        "training_calls": 0,
        "production_service_calls": 0,
    })
    return result


def preflight() -> dict[str, Any]:
    started = now_utc()
    hash_records = verify_hashes()
    contract = contract_payload()
    if RESULT.exists() or RECEIPT.exists() or VALIDATION.exists():
        raise RuntimeError("INVALID: scientific output exists before preflight")
    leaves = ordered_leaves()
    tables = table_index()
    n1_rows, equivalence = regenerate_n1(leaves, tables)
    n2_a, meta_a = generate_n2(leaves, tables)
    n2_b, meta_b = generate_n2(leaves, tables)
    if not equivalence["byte_identical_response_vectors"] or jsonl_bytes(n2_a) != jsonl_bytes(n2_b):
        raise RuntimeError("END_TO_END_PREFLIGHT_FAIL: integration identity failure")
    n1_population, n2_population = assemble_populations(read_jsonl(PAIRED), n2_a)
    integration = {
        "n1_paired_rows": len(n1_population),
        "n2_population_rows": len(n2_population),
        "n2_generated_rows": len(n2_a),
        "n2_groups": meta_a["selected_groups"],
        "leaf_count": len(leaves),
        "n1_class_counts": population_counts(n1_population)["class_counts"],
        "n2_class_counts": population_counts(n2_population)["class_counts"],
        "n1_response_matrix_sha256": sha256_bytes(
            jsonl_bytes([row_key(row, leaves) for row in n1_population])
        ),
        "n2_response_matrix_sha256": sha256_bytes(
            jsonl_bytes([row_key(row, leaves) for row in n2_population])
        ),
        "n1_regeneration_rows": len(n1_rows),
        "n2_double_run_byte_identical": jsonl_bytes(n2_a) == jsonl_bytes(n2_b),
    }
    payload = {
        "experiment_id": "PR-EXP-04",
        "verification_level": "END_TO_END_PREFLIGHT_PASS",
        "started_utc": started,
        "completed_utc": now_utc(),
        "prereg_sha256": EXPECTED_RAW_HASHES[str(PREREG.relative_to(ROOT))],
        "implementation_contract_sha256": contract["_sha256"],
        "hash_domain": {
            "raw_provenance": "raw_sha256",
            "canonicalizer_runtime": "git_blob",
            "verified_records": len(hash_records),
        },
        "runtime_interface": {
            "required_metadata": [
                "experiment_id", "prereg_sha256", "implementation_contract_sha256",
                "start_utc", "end_utc", "input_hashes", "output_hashes",
                "raw_metrics", "canonical_outcome_label", "cost",
                "unverified_items", "deviations",
            ],
            "missing_values_raise": True,
            "silent_defaults": False,
        },
        "sample_group_identity": integration,
        "split_determinism": {
            "seed": SEED,
            "rule": "ascending SHA-256 over frozen seed:namespace:key",
            "replay_byte_identical": integration["n2_double_run_byte_identical"],
            "cross_role_uid_overlap": "checked during formal execution; preflight construction uses the frozen exclusion rule",
        },
        "scorer_binding": {
            "runner_sha256": EXPECTED_RAW_HASHES[str(RUNNER.relative_to(ROOT))],
            "checkpoint_trees_sha256": EXPECTED_RAW_HASHES[str(CHECKPOINT_TREES.relative_to(ROOT))],
            "measurement_object": "frozen 12-leaf response vector plus frozen contract checks",
            "shared_fault_adapter": False,
            "stage_e_aggregation_changed": False,
        },
        "analysis_plan": {
            "estimands": ["macro_f1", "top1_accuracy"],
            "directions": ["N1_to_N2", "N2_to_N1"],
            "classifier": "frozen nearest-centroid with Euclidean distance and tie=failure",
            "loco": "remove target cluster from source population before centroid fitting",
            "direct_control": "same classifier restricted to M/R/N direct leaves",
            "exclusions": "fail-closed on missing input/hash/class/group",
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "ci_method": "95% percentile cluster bootstrap",
            "permutation": "NOT_USED",
        },
        "integration_trace": integration,
        "zero_output_scan": {
            "result_json_exists": RESULT.exists(),
            "receipt_json_exists": RECEIPT.exists(),
            "independent_validation_exists": VALIDATION.exists(),
            "scientific_outputs_absent": not (RESULT.exists() or RECEIPT.exists() or VALIDATION.exists()),
        },
        "previous_run_immutability": {"shared_hash_mismatches": 0, "status": "PASS"},
        "commands": [
            "python3 research/positive_repair_20261011/runs/PR-EXP-04/run_pr_exp_04.py preflight",
        ],
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "test_output_hashes": {
            "py_compile_command": (
                "python3 -m py_compile "
                "research/positive_repair_20261011/runs/PR-EXP-04/run_pr_exp_04.py "
                "research/positive_repair_20261011/runs/PR-EXP-04/validate_pr_exp_04.py"
            ),
            "py_compile_exit_code": 0,
            "py_compile_stdout_stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        },
        "model_calls": 0,
    }
    if not payload["zero_output_scan"]["scientific_outputs_absent"]:
        raise RuntimeError("END_TO_END_PREFLIGHT_FAIL: zero-output scan failed")
    write_json(PREFLIGHT, payload)
    return payload


def finalize_receipt() -> dict[str, Any]:
    if not VALIDATION.is_file():
        raise RuntimeError("INPUT_MISSING: independent validation receipt")
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS":
        raise RuntimeError("INVALID: independent validation did not pass")
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    preflight_payload = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    contract_hash = CONTRACT_HASH.read_text(encoding="utf-8").strip().split()[0]
    end = now_utc()
    start = preflight_payload["started_utc"]
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    output_paths = sorted(
        path for path in RUN_DIR.iterdir()
        if path.is_file() and path.name not in {"receipt.json"}
    )
    payload = {
        "experiment_id": "PR-EXP-04",
        "status": "COMPLETE",
        "prereg_sha256": EXPECTED_RAW_HASHES[str(PREREG.relative_to(ROOT))],
        "implementation_contract_sha256": contract_hash,
        "start_utc": start,
        "end_utc": end,
        "input_hashes": [
            {"path": path, "identity_rule": record["identity_rule"], "sha256": record["expected"], "status": "PASS"}
            for record in result["hash_verification"]
            for path in [record["path"]]
        ],
        "output_hashes": [
            {"path": path.name, "sha256": sha256_file(path)}
            for path in output_paths
        ],
        "raw_metrics": {
            "n1_harness_equivalence": result["controls"]["n1_harness_equivalence"],
            "n2_double_run": result["controls"]["n2_double_run"],
            "visibility_gate": result["gates"]["visibility"],
            "n1_to_n2_full": result["evaluation"]["n1_to_n2"]["full_surface"],
            "n1_to_n2_direct": result["evaluation"]["n1_to_n2"]["direct_codebook"],
            "n2_to_n1_full": result["evaluation"]["n2_to_n1"]["full_surface"],
            "n2_to_n1_direct": result["evaluation"]["n2_to_n1"]["direct_codebook"],
            "responsive_leaf_overlap": result["responsive_leaf_overlap"],
            "baselines": result["baselines"],
        },
        "canonical_outcome_label": result["canonical_outcome_label"],
        "canonical_outcome_label_satisfied": result["canonical_outcome_label_satisfied"],
        "supporting_only": True,
        "counts_toward_repair_count": False,
        "cost": {
            "runtime_seconds": round((end_dt - start_dt).total_seconds(), 3),
            "model_calls": 0,
            "judge_calls": 0,
            "network_calls": 0,
            "database_calls": 0,
            "training_calls": 0,
            "production_service_calls": 0,
        },
        "preflight_verification_level": preflight_payload["verification_level"],
        "independent_validation_sha256": sha256_file(VALIDATION),
        "unverified_items": [
            "No external Loop C recomputation was authorized or performed in this execution.",
            "No production-service, database, model, judge, network, training, commit, or push probe was performed.",
        ],
        "deviations": result["deviations"],
        "stop_reason": None,
    }
    if len({label for label in [payload["canonical_outcome_label"]]}) != 1:
        raise RuntimeError("INVALID: canonical outcome label is not unique")
    if payload["canonical_outcome_label"] not in {"SUPPORTED", "NULL", "NEGATIVE", "NOT_EVALUABLE", "INVALID"}:
        raise RuntimeError("INVALID: non-canonical outcome label")
    write_json(RECEIPT, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "run", "finalize"))
    args = parser.parse_args()
    if args.mode == "preflight":
        payload = preflight()
        print(json.dumps({"verification_level": payload["verification_level"], "zero_outputs": True}, sort_keys=True))
    elif args.mode == "run":
        payload = build_scientific_result()
        print(json.dumps({
            "result_status": payload["result_status"],
            "canonical_outcome_label": payload["canonical_outcome_label"],
            "visibility_pass": payload["gates"]["visibility"]["pass"],
        }, sort_keys=True))
    else:
        payload = finalize_receipt()
        print(json.dumps({
            "status": payload["status"],
            "canonical_outcome_label": payload["canonical_outcome_label"],
            "receipt": str(RECEIPT),
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

--- END PACKET ---
