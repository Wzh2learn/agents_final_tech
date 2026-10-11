# Loop C Post-Result Independent Audit — PR-EXP-03 (INTERVENTION_REPAIR)

You are the independent Loop C auditor. This is a POST-RESULT audit of one completed Track P experiment. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Judge strictly from this packet; missing evidence -> UNVERIFIED. Do not modify, re-run, or rescue the result. Labels: FACT / INFERENCE / UNVERIFIED.

## Round context (disclosed facts)
- Track P first wave: PR-EXP-03 INTERVENTION_REPAIR / PR-EXP-01 INTERVENTION_REPAIR / PR-EXP-04 GENERALIZATION_TEST / PR-EXP-07 ROBUSTNESS_ANTI_TAUTOLOGY. Only INTERVENTION_REPAIR positives may ever count toward the synthesis gate.
- Registered class for PR-EXP-03: INVALID.
- Disclosed incidents, NOT part of this experiment's scientific record: (i) two engineering dispatch layers (a1 INPUT_MISSING x4; a2 HASH_MISMATCH x4) were fail-closed infrastructure failures, zero scientific side effects, excluded from scientific classes; (ii) the prereg re-audit log lost its leading sections in capture (verdicts recovered from GLOBAL); (iii) the Loop D prereg/sanity-gate definitions may contain defects - examine critically.
- Registered INVALID came from the prereg sanity gate: reasons include "carrier monotonicity condition failed on all 216 carriers" and 2 undefined baseline field-hit cells (two held-out P1 tables with empty headers). Examine whether the sanity-gate non-monotonicity condition can fail vacuously for a constant-zero structural column on the frozen carriers (a definition artifact rather than a scientific finding), and whether the 2 undefined cells are a real data edge requiring handling. Descriptive complete-case numbers (new oracle 1973/2431 vs standalone baseline 0/2429) MUST NOT be treated as a positive while the classification and gate conditions are unsound.

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
--- BEGIN prereg v2 (PR-EXP-03) ---
# Prereg — PR-EXP-03: M-stage structural-oracle coverage repair (de-alias)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-03 | candidate: PR-03 | role: INTERVENTION_REPAIR
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> shared artifacts pinned in research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json

## 1. Hypothesis
A table-structure oracle defined from table/schema semantics and frozen before any topology-outcome observation recovers held-out structural failures that the existing field-hit-derived oracle misses, at comparable measurement cost, without constant-1-style or duplicate-catch artifacts.

## 2. Owner-fixed criteria (2026-10-11 human decision, section 3)
Primary question: held-out structural failures recovered where the existing oracle misses, comparable cost. Oracle from table/schema/execution semantics; no mutation labels; no held-out outcome; frozen before any M2-type result observation; held-out topology failures independent; old vs repaired oracle on the same population. Primary metrics: (1) held-out failure coverage delta; (2) stage/family diagnosability delta. Improvement only from SOURCE_LOCAL_RESPONSE -> not a repair positive. Merely-different oracle with no held-out diagnostic gain -> NULL.

## 3. Population
- P1 held-out topology failure set: deterministic adjacent-column transposition failures over held-out table UIDs. Selection rule (verbatim; pinned in the implementation contract): UIDs = ascending SHA-256(seed=20261011:namespace="pr03-topology":uid) over the frozen drift corpus table set (membership pinned by source-file hash + UID list hash); EXCLUSION REGISTRY = M-stage UIDs and N-stage UIDs extracted from research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json (extraction command recorded verbatim); exactly one adjacent column pair transposed per selected table, pair index by frozen per-table hash rule; values and row counts preserved; generator double-run byte-identical required.
- Ground truth for P1: stage_label="M", family_label="topology_transposition".
- P2 control: frozen 216-row carriers — untouched; only for the regression check; never for primary metrics.
- P3 M1 regression set: held-out M1-style cases (frozen selection rule).

## 4. Intervention and arms (frozen before P1 generation)
Structural oracle v2 at parse.table.regression: response = int(structural_signature(baseline) != structural_signature(injected)); structural_signature = (column_count, ordered positional header-token sequence under the pinned canonicalizer, row_count). No mutation labels; no held-out outcomes; fail-closed: undefined artifacts -> NOT_EVALUABLE cell.
Freeze order: (1) oracle implementation hash + verbatim rules; (2) P1 generation; (3) evaluation. No edits after P1 observation.
Arms (same frozen response rule): A0 no-op/identity (structural oracle must return 0 on every case); A1 value-only specificity (cell-value changes, structure preserved; must return 0); A2 P1 (expected 1); A3 frozen-carrier regression (M1 subset; expected 0).
Baseline oracles on the same population: (a) v1 aliased implementation (verbatim two-line extract from run_multileaf_formal.py:256-258 + file hash), (b) standalone field-hit oracle; unchanged.
Constant-1 control: documented that a constant-1 rule attains coverage=1 on P1 but fails A0/A1; POSITIVE therefore requires A0/A1 pass.

## 5. Metrics
Primary: (1) held-out failure coverage delta = coverage(new) − coverage(old) on P1 (raw numerators/denominators; cluster bootstrap CI over table UIDs, frozen seed); (2) stage/family diagnosability delta on the mixed held-out population = P1 ∪ frozen-rule subsample of carriers; macro-F1 via frozen nearest-centroid, LOCO over groups (table/document clusters, no source overlap); conclusion-level deltas only.
Secondary: disagreement rate; incremental unique catches; check-cost (§6); M1 regression; A0/A1 false-positive counts.
Attribution audit (operational; per contracts/SOURCE_LOCAL_RESPONSE_v1.md): pass = unique new catches AND A0/A1 clean AND constant-1 documented failure.

## 6. Cost and cost tolerance (defined)
Zero model/judge calls. Both oracles produce exactly 1 leaf response per case: check-count equality is the frozen cost tolerance (exact equality; no runtime-based claim). Freeze/audit overhead recorded in the cost ledger.

## 7. Outcome taxonomy (complete)
- POSITIVE: Δcov > 0 with CI lower > 0 AND Δdiag >= −0.02 (frozen materiality margin) AND A0/A1 pass AND no M1 regression AND attribution pass.
- DIAG_ONLY: Δcov <= 0 or CI includes 0, but Δdiag > +0.02 -> recorded as NULL with diag gain noted; NOT a repair positive.
- NULL: no material gain and no material loss (coverage nonpositive or CI includes 0; |Δdiag| <= 0.02).
- NEGATIVE: Δdiag < −0.02 (regardless of coverage).
- INVALID: sanity-gate failure, label access, post-freeze edits, UID overlap, cost inequivalence.
- NOT_EVALUABLE: P1 not executable/visible, or oracle semantics undefined on held-out artifacts. Never merged into NULL.
Sanity gate (defined): the structural column must differ from the field-hit column on >=1 held-out P1 case AND must not be a monotone function of field-hit on the frozen 216 rows; failure = INVALID (implementation defect), not a scientific outcome.

## 8. Implementation contract requirement
Before execution, Loop A materializes runs/PR-EXP-03/implementation_contract.md containing verbatim: drift-corpus membership rule (source path + sha256 + UID list hash), UID exclusion registry (extracted list + extraction command), pair-selection hash rule, oracle v2 source hash, baseline extract hashes, arm definitions, bootstrap seed, shared-surface hash check results. Missing items -> INPUT_MISSING stop.

## 9. Stop conditions
Any requirement violation; no threshold/oracle hunting; any scope change -> new prereg + re-audit. If any audit-v1 condition cannot be satisfied within this revision -> STOP_BRANCH.
--- BEGIN receipt.json ---
{
  "cost": {
    "check_count_attempted_equality": true,
    "check_counts": {
      "A0": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2431,
        "new_leaf_responses": 2431
      },
      "A1": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2431,
        "new_leaf_responses": 2431
      },
      "A3": {
        "attempted_equal": true,
        "baseline_leaf_responses": 72,
        "new_leaf_responses": 72
      },
      "P1": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2431,
        "new_leaf_responses": 2431
      },
      "mixed_diagnosability": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2503,
        "new_leaf_responses": 2503
      }
    },
    "database_calls": 0,
    "judge_calls": 0,
    "model_calls": 0,
    "network_calls": 0,
    "production_service_calls": 0,
    "runtime_seconds": 275.0,
    "training_runs": 0
  },
  "deviations": [],
  "end_utc": "2026-10-11T08:35:22Z",
  "environment": {
    "execution_label": "GB10",
    "hostname": "promaxgb10-0b48",
    "platform": "Linux-6.17.0-1018-nvidia-aarch64-with-glibc2.39",
    "python": "3.12.3"
  },
  "experiment_id": "PR-EXP-03",
  "fail_closed_note": "INVALID is determined by the preregistered sanity gate. Two undefined baseline field-hit cells independently prevent full-population diagnosability and attribution metrics; partial complete-case values are recorded and do not rescue the outcome.",
  "implementation_contract_sha256": "0d159746490b43c3c0209f7a4df6d6a1fbf7a666ed40d8eec4870b4a3e31db16",
  "input_hashes": {
    "baseline_runner": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
    "canonicalizer_implementation": "d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8",
    "canonicalizer_wrapper": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b",
    "drift_corpus_tables": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    "experiment_source": "d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3",
    "implementation_contract": "0d159746490b43c3c0209f7a4df6d6a1fbf7a666ed40d8eec4870b4a3e31db16",
    "injection_map_informational_not_used": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
    "multileaf_freeze": "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
    "multileaf_paired_artifacts": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
    "multileaf_prediction_rows_informational_not_used": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
    "multileaf_preresult_freeze_manifest": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
    "multileaf_sample_manifest": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
    "prereg": "f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250",
    "shared_surface_freeze": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    "source_local_term_sheet": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290"
  },
  "invalid_reasons": [
    "sanity_gate_failure"
  ],
  "outcome_label": "INVALID",
  "outcome_taxonomy": [
    "POSITIVE",
    "DIAG_ONLY",
    "NULL",
    "NEGATIVE",
    "INVALID",
    "NOT_EVALUABLE"
  ],
  "output_hashes": {
    "implementation_contract": "0d159746490b43c3c0209f7a4df6d6a1fbf7a666ed40d8eec4870b4a3e31db16",
    "metrics": "7eacf37b5b2666d0770ef21972964ddfbcc88cac030e30d576db790ef6f49650",
    "p1_generation_manifest": "ad941ade2dc735c8e454d27d28d7496889dc8696304847717716473735607b1f",
    "p1_run1": "8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69",
    "p1_run2": "8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69",
    "undefined_cells": "0972f895f51439c22a88ff20810d1e0e7e3022e082b0a699b6b45b638a9d875b"
  },
  "prereg_sha256": "f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250",
  "raw_metrics": {
    "attribution_audit": {
      "A0_A1_clean": true,
      "complete_case_denominator": 2429,
      "constant1_specificity_failure_documented": true,
      "reason": "full-population duplicate-catch test cannot be concluded with 2 undefined baseline cells",
      "status": "NOT_EVALUABLE",
      "undefined_count": 2,
      "unique_new_catches_vs_both_baselines_complete_cases": true,
      "unique_vs_standalone_numerator": 1973,
      "unique_vs_v1_alias_numerator": 1973
    },
    "constant1_control": {
      "A0_false_positive": {
        "ci95_wilson": [
          0.9984222961183868,
          1.0
        ],
        "denominator": 2431,
        "numerator": 2431,
        "rate": 1.0
      },
      "A1_false_positive": {
        "ci95_wilson": [
          0.9984222961183868,
          1.0
        ],
        "denominator": 2431,
        "numerator": 2431,
        "rate": 1.0
      },
      "P1_coverage": {
        "ci95_wilson": [
          0.9984222961183868,
          1.0
        ],
        "denominator": 2431,
        "numerator": 2431,
        "rate": 1.0
      },
      "specificity_failure_documented": true
    },
    "cost": {
      "check_count_attempted_equality": true,
      "check_counts": {
        "A0": {
          "attempted_equal": true,
          "baseline_leaf_responses": 2431,
          "new_leaf_responses": 2431
        },
        "A1": {
          "attempted_equal": true,
          "baseline_leaf_responses": 2431,
          "new_leaf_responses": 2431
        },
        "A3": {
          "attempted_equal": true,
          "baseline_leaf_responses": 72,
          "new_leaf_responses": 72
        },
        "P1": {
          "attempted_equal": true,
          "baseline_leaf_responses": 2431,
          "new_leaf_responses": 2431
        },
        "mixed_diagnosability": {
          "attempted_equal": true,
          "baseline_leaf_responses": 2503,
          "new_leaf_responses": 2503
        }
      },
      "database_calls": 0,
      "judge_calls": 0,
      "model_calls": 0,
      "network_calls": 0,
      "production_service_calls": 0,
      "runtime_claim": false,
      "training_runs": 0
    },
    "coverage": {
      "P1_new": {
        "ci95": [
          0.7955688919245218,
          0.8266482115799438
        ],
        "denominator": 2431,
        "intended_denominator": 2431,
        "numerator": 1973,
        "rate": 0.811600164541341,
        "status": "NEW_DEFINED_BASELINE_UNDEFINED_ON_2",
        "undefined_count": 2
      },
      "P1_standalone_field_hit_complete_cases": {
        "ci95": [
          0.0,
          0.0015790008867064649
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 0,
        "rate": 0.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "P1_v1_alias_complete_cases": {
        "ci95": [
          0.0,
          0.0015790008867064649
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 0,
        "rate": 0.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "delta_cluster_bootstrap_ci95_complete_cases": [
        0.7966241251543845,
        0.8275010292301359
      ],
      "delta_cluster_bootstrap_replicates": 10000,
      "delta_cluster_bootstrap_seed": 20261012,
      "delta_new_minus_v1_alias_complete_cases": 0.8122684232194318,
      "primary_status": "NOT_EVALUABLE",
      "reason": "baseline field-hit undefined on 2 held-out P1 artifacts"
    },
    "diagnosability": {
      "delta_diag_min_stage_family": {
        "ci95": [
          null,
          null
        ],
        "denominator": null,
        "intended_denominator": 2503,
        "numerator": null,
        "rate": null,
        "status": "NOT_EVALUABLE",
        "undefined_count": 2
      },
      "family_delta": {
        "ci95": [
          null,
          null
        ],
        "denominator": null,
        "intended_denominator": 2503,
        "numerator": null,
        "rate": null,
        "status": "NOT_EVALUABLE",
        "undefined_count": 2
      },
      "materiality_margin": -0.02,
      "mixed_population_complete_case_denominator": 2501,
      "mixed_population_intended_denominator": 2503,
      "reason": "mixed-population baseline field-hit is undefined on 2 P1 rows",
      "stage_delta": {
        "ci95": [
          null,
          null
        ],
        "denominator": null,
        "intended_denominator": 2503,
        "numerator": null,
        "rate": null,
        "status": "NOT_EVALUABLE",
        "undefined_count": 2
      },
      "status": "NOT_EVALUABLE",
      "undefined_count": 2
    },
    "population_inventory": {
      "P1_complete_case_denominator": 2429,
      "P1_intended_denominator": 2431,
      "P1_undefined_count": 2,
      "UID_overlap_count": 0,
      "all_uid_list_sha256": "b030d9df505eb406c00767947e6eab101a61a8f969c8e20550e68f3802be024a",
      "carrier_carrier_count": 216,
      "carrier_cluster_count": 72,
      "carrier_family_counts": {
        "mutate_one_numeric_operand_while_preserving_labels_schema_and_identity_contract": 24,
        "remove_required_source_blocks_from_retrieval_candidate_bundle": 24,
        "replace_one_header_token_with_out_of_vocabulary_token": 24
      },
      "carrier_stage_counts": {
        "M": 24,
        "N": 24,
        "R": 24
      },
      "carrier_subsample_count": 72,
      "carrier_subsample_sample_id_list_sha256": "e99f83f8f71337189a0fe44f151917acc39738bca515e841ab75249a4c5b1f90",
      "eligible_uid_count": 2431,
      "eligible_uid_list_sha256": "7a83aa01063be5bc10f5645236bd086771a2a16f9f2fa09b47dad782dedf8675",
      "excluded_uid_count": 48,
      "excluded_uid_list_sha256": "e511b6ed7ad40d0b336cdf49362af728b7301b6d696322bd3ede87b883ef99cd",
      "mixed_complete_case_denominator": 2501,
      "mixed_intended_denominator": 2503,
      "ordered_p1_uid_count": 2431,
      "ordered_p1_uid_list_sha256": "dc1315d6615d79f7891ee578d5571ba803fe440d00bb84ff168817a42aaafacc",
      "table_record_count": 2479,
      "unique_uid_count": 2479
    },
    "sanity_gate": {
      "P1_complete_case_denominator": 2429,
      "P1_intended_denominator": 2431,
      "P1_structural_differs_from_field_hit_complete_cases": 1973,
      "P1_undefined_count": 2,
      "carrier_denominator": 216,
      "carrier_structural_monotone_function_of_field_hit": true,
      "partial_status": false,
      "reason": "P1 existential difference observed on 1973 defined cases; carrier monotonicity condition failed on all 216 carriers; 2 P1 baseline cells remain undefined.",
      "status": "FAIL"
    },
    "secondary": {
      "A0_false_positive_new": {
        "ci95": [
          0.0,
          0.0015777038816131878
        ],
        "denominator": 2431,
        "intended_denominator": null,
        "numerator": 0,
        "rate": 0.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 0
      },
      "A0_false_positive_v1_alias_defined_cells": {
        "ci95": [
          0.0,
          0.0015790008867064649
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 0,
        "rate": 0.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "A1_false_positive_new": {
        "ci95": [
          0.0,
          0.0015777038816131878
        ],
        "denominator": 2431,
        "intended_denominator": null,
        "numerator": 0,
        "rate": 0.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 0
      },
      "A1_false_positive_v1_alias_defined_cells": {
        "ci95": [
          0.0,
          0.0015790008867064649
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 0,
        "rate": 0.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "A3_M1_regression_new": {
        "ci95": [
          0.9493488274035422,
          1.0
        ],
        "denominator": 72,
        "intended_denominator": null,
        "numerator": 72,
        "rate": 1.0,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 0
      },
      "disagreement_new_vs_standalone_complete_cases": {
        "ci95": [
          0.7962504520935175,
          0.8273002501110384
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 1973,
        "rate": 0.8122684232194318,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "disagreement_new_vs_v1_alias_complete_cases": {
        "ci95": [
          0.7962504520935175,
          0.8273002501110384
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 1973,
        "rate": 0.8122684232194318,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "unique_catch_vs_standalone_complete_cases": {
        "ci95": [
          0.7962504520935175,
          0.8273002501110384
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 1973,
        "rate": 0.8122684232194318,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      },
      "unique_catch_vs_v1_alias_complete_cases": {
        "ci95": [
          0.7962504520935175,
          0.8273002501110384
        ],
        "denominator": 2429,
        "intended_denominator": 2431,
        "numerator": 1973,
        "rate": 0.8122684232194318,
        "status": "COMPLETE_CASE_PARTIAL",
        "undefined_count": 2
      }
    }
  },
  "receipt_hash_note": "receipt_sha256 omitted because a file cannot contain its own stable hash",
  "shared_surface_hash_checks": {
    "canonicalizer_file": {
      "actual_hash_object": "def5161dd17fc14345d340879174ed01e0277626",
      "actual_rev_parse": "def5161dd17fc14345d340879174ed01e0277626",
      "expected_git_blob_sha1": "def5161dd17fc14345d340879174ed01e0277626",
      "identity_rule": "git_blob",
      "pass": true,
      "path": "scripts/m1_statement_parser.py",
      "raw_sha256_hosts": {
        "GB10": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b",
        "LOCAL": "f9f1bc92c9d2963b3f346c0557f2b6a59d22201277b2023400f6953c59ac4aee"
      },
      "raw_sha256_informational": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b"
    },
    "gb10_only_inputs[1]": {
      "actual_full_sha256": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
      "expected_prefix": "3e7e0568",
      "identity_rule": "sha256_prefix",
      "pass": true,
      "path": "data/research/drift_v0/input/tatqa_tables.json"
    },
    "gb10_only_inputs[2]": {
      "actual_full_sha256": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
      "expected_prefix": "d7612405",
      "identity_rule": "sha256_prefix",
      "pass": true,
      "path": "data/research/drift_v0/output/injection_map.json"
    },
    "multileaf_paired_artifacts": {
      "actual": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
      "expected": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
      "identity_rule": "raw_sha256",
      "pass": true,
      "path": "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl"
    },
    "multileaf_prediction_rows": {
      "actual": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
      "expected": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
      "identity_rule": "raw_sha256",
      "pass": true,
      "path": "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl"
    },
    "multileaf_preresult_freeze_manifest": {
      "actual": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
      "expected": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
      "identity_rule": "raw_sha256",
      "pass": true,
      "path": "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json"
    },
    "multileaf_response_rule_and_runner": {
      "actual": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
      "expected": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
      "identity_rule": "raw_sha256",
      "pass": true,
      "path": "research/stage_e_multileaf_20261010/run_multileaf_formal.py"
    },
    "source_local_term_sheet": {
      "actual": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
      "expected": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
      "identity_rule": "raw_sha256",
      "pass": true,
      "path": "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md"
    }
  },
  "source_freeze_checks": {
    "implementation_contract_sha256": "0d159746490b43c3c0209f7a4df6d6a1fbf7a666ed40d8eec4870b4a3e31db16",
    "source_hashes": {
      "config/eval_checkpoint_trees.json": {
        "actual": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
        "expected": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
        "pass": true
      },
      "data/research/drift_v0/input/tatqa_tables.json": {
        "actual": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
        "expected": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
        "pass": true
      },
      "data/research/drift_v0/output/injection_map.json": {
        "actual": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
        "expected": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
        "pass": true
      },
      "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md": {
        "actual": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
        "expected": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
        "pass": true
      },
      "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json": {
        "actual": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
        "expected": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
        "pass": true
      },
      "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md": {
        "actual": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
        "expected": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
        "pass": true
      },
      "research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md": {
        "actual": "f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250",
        "expected": "f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250",
        "pass": true
      },
      "research/positive_repair_20261011/runs/PR-EXP-03/experiment.py": {
        "actual": "d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3",
        "expected": "d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3",
        "pass": true
      },
      "research/stage_e_method_revision_20261009/multileaf_freeze.json": {
        "actual": "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
        "expected": "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
        "pass": true
      },
      "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json": {
        "actual": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
        "expected": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
        "pass": true
      },
      "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json": {
        "actual": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
        "expected": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
        "pass": true
      },
      "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl": {
        "actual": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
        "expected": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
        "pass": true
      },
      "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl": {
        "actual": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
        "expected": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
        "pass": true
      },
      "research/stage_e_multileaf_20261010/run_multileaf_formal.py": {
        "actual": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
        "expected": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
        "pass": true
      },
      "scripts/m1_statement_parser.py": {
        "actual": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b",
        "expected": "747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b",
        "pass": true
      },
      "src/biz/m1_statement_parser.py": {
        "actual": "d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8",
        "expected": "d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8",
        "pass": true
      }
    }
  },
  "start_utc": "2026-10-11T08:30:47Z",
  "unverified_items": [
    "full-population stage/family diagnosability delta",
    "full-population attribution duplicate-catch conclusion"
  ]
}

--- BEGIN metrics.json ---
{
  "attribution_audit": {
    "A0_A1_clean": true,
    "complete_case_denominator": 2429,
    "constant1_specificity_failure_documented": true,
    "reason": "full-population duplicate-catch test cannot be concluded with 2 undefined baseline cells",
    "status": "NOT_EVALUABLE",
    "undefined_count": 2,
    "unique_new_catches_vs_both_baselines_complete_cases": true,
    "unique_vs_standalone_numerator": 1973,
    "unique_vs_v1_alias_numerator": 1973
  },
  "constant1_control": {
    "A0_false_positive": {
      "ci95_wilson": [
        0.9984222961183868,
        1.0
      ],
      "denominator": 2431,
      "numerator": 2431,
      "rate": 1.0
    },
    "A1_false_positive": {
      "ci95_wilson": [
        0.9984222961183868,
        1.0
      ],
      "denominator": 2431,
      "numerator": 2431,
      "rate": 1.0
    },
    "P1_coverage": {
      "ci95_wilson": [
        0.9984222961183868,
        1.0
      ],
      "denominator": 2431,
      "numerator": 2431,
      "rate": 1.0
    },
    "specificity_failure_documented": true
  },
  "cost": {
    "check_count_attempted_equality": true,
    "check_counts": {
      "A0": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2431,
        "new_leaf_responses": 2431
      },
      "A1": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2431,
        "new_leaf_responses": 2431
      },
      "A3": {
        "attempted_equal": true,
        "baseline_leaf_responses": 72,
        "new_leaf_responses": 72
      },
      "P1": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2431,
        "new_leaf_responses": 2431
      },
      "mixed_diagnosability": {
        "attempted_equal": true,
        "baseline_leaf_responses": 2503,
        "new_leaf_responses": 2503
      }
    },
    "database_calls": 0,
    "judge_calls": 0,
    "model_calls": 0,
    "network_calls": 0,
    "production_service_calls": 0,
    "runtime_claim": false,
    "training_runs": 0
  },
  "coverage": {
    "P1_new": {
      "ci95": [
        0.7955688919245218,
        0.8266482115799438
      ],
      "denominator": 2431,
      "intended_denominator": 2431,
      "numerator": 1973,
      "rate": 0.811600164541341,
      "status": "NEW_DEFINED_BASELINE_UNDEFINED_ON_2",
      "undefined_count": 2
    },
    "P1_standalone_field_hit_complete_cases": {
      "ci95": [
        0.0,
        0.0015790008867064649
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 0,
      "rate": 0.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "P1_v1_alias_complete_cases": {
      "ci95": [
        0.0,
        0.0015790008867064649
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 0,
      "rate": 0.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "delta_cluster_bootstrap_ci95_complete_cases": [
      0.7966241251543845,
      0.8275010292301359
    ],
    "delta_cluster_bootstrap_replicates": 10000,
    "delta_cluster_bootstrap_seed": 20261012,
    "delta_new_minus_v1_alias_complete_cases": 0.8122684232194318,
    "primary_status": "NOT_EVALUABLE",
    "reason": "baseline field-hit undefined on 2 held-out P1 artifacts"
  },
  "diagnosability": {
    "delta_diag_min_stage_family": {
      "ci95": [
        null,
        null
      ],
      "denominator": null,
      "intended_denominator": 2503,
      "numerator": null,
      "rate": null,
      "status": "NOT_EVALUABLE",
      "undefined_count": 2
    },
    "family_delta": {
      "ci95": [
        null,
        null
      ],
      "denominator": null,
      "intended_denominator": 2503,
      "numerator": null,
      "rate": null,
      "status": "NOT_EVALUABLE",
      "undefined_count": 2
    },
    "materiality_margin": -0.02,
    "mixed_population_complete_case_denominator": 2501,
    "mixed_population_intended_denominator": 2503,
    "reason": "mixed-population baseline field-hit is undefined on 2 P1 rows",
    "stage_delta": {
      "ci95": [
        null,
        null
      ],
      "denominator": null,
      "intended_denominator": 2503,
      "numerator": null,
      "rate": null,
      "status": "NOT_EVALUABLE",
      "undefined_count": 2
    },
    "status": "NOT_EVALUABLE",
    "undefined_count": 2
  },
  "experiment_id": "PR-EXP-03",
  "generator": {
    "byte_identical": true,
    "row_count": 2431,
    "run1_sha256": "8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69",
    "run2_sha256": "8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69"
  },
  "outcome": {
    "invalid_reasons": [
      "sanity_gate_failure"
    ],
    "label": "INVALID",
    "reason": "Sanity gate failed: the structural carrier column is a monotone function of field-hit on all 216 frozen carriers; 2 additional baseline field-hit cells are undefined and leave diagnosability/attribution unverified.",
    "taxonomy": [
      "POSITIVE",
      "DIAG_ONLY",
      "NULL",
      "NEGATIVE",
      "INVALID",
      "NOT_EVALUABLE"
    ]
  },
  "population_inventory": {
    "P1_complete_case_denominator": 2429,
    "P1_intended_denominator": 2431,
    "P1_undefined_count": 2,
    "UID_overlap_count": 0,
    "all_uid_list_sha256": "b030d9df505eb406c00767947e6eab101a61a8f969c8e20550e68f3802be024a",
    "carrier_carrier_count": 216,
    "carrier_cluster_count": 72,
    "carrier_family_counts": {
      "mutate_one_numeric_operand_while_preserving_labels_schema_and_identity_contract": 24,
      "remove_required_source_blocks_from_retrieval_candidate_bundle": 24,
      "replace_one_header_token_with_out_of_vocabulary_token": 24
    },
    "carrier_stage_counts": {
      "M": 24,
      "N": 24,
      "R": 24
    },
    "carrier_subsample_count": 72,
    "carrier_subsample_sample_id_list_sha256": "e99f83f8f71337189a0fe44f151917acc39738bca515e841ab75249a4c5b1f90",
    "eligible_uid_count": 2431,
    "eligible_uid_list_sha256": "7a83aa01063be5bc10f5645236bd086771a2a16f9f2fa09b47dad782dedf8675",
    "excluded_uid_count": 48,
    "excluded_uid_list_sha256": "e511b6ed7ad40d0b336cdf49362af728b7301b6d696322bd3ede87b883ef99cd",
    "mixed_complete_case_denominator": 2501,
    "mixed_intended_denominator": 2503,
    "ordered_p1_uid_count": 2431,
    "ordered_p1_uid_list_sha256": "dc1315d6615d79f7891ee578d5571ba803fe440d00bb84ff168817a42aaafacc",
    "table_record_count": 2479,
    "unique_uid_count": 2479
  },
  "sanity_gate": {
    "P1_complete_case_denominator": 2429,
    "P1_intended_denominator": 2431,
    "P1_structural_differs_from_field_hit_complete_cases": 1973,
    "P1_undefined_count": 2,
    "carrier_denominator": 216,
    "carrier_structural_monotone_function_of_field_hit": true,
    "partial_status": false,
    "reason": "P1 existential difference observed on 1973 defined cases; carrier monotonicity condition failed on all 216 carriers; 2 P1 baseline cells remain undefined.",
    "status": "FAIL"
  },
  "secondary": {
    "A0_false_positive_new": {
      "ci95": [
        0.0,
        0.0015777038816131878
      ],
      "denominator": 2431,
      "intended_denominator": null,
      "numerator": 0,
      "rate": 0.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 0
    },
    "A0_false_positive_v1_alias_defined_cells": {
      "ci95": [
        0.0,
        0.0015790008867064649
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 0,
      "rate": 0.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "A1_false_positive_new": {
      "ci95": [
        0.0,
        0.0015777038816131878
      ],
      "denominator": 2431,
      "intended_denominator": null,
      "numerator": 0,
      "rate": 0.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 0
    },
    "A1_false_positive_v1_alias_defined_cells": {
      "ci95": [
        0.0,
        0.0015790008867064649
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 0,
      "rate": 0.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "A3_M1_regression_new": {
      "ci95": [
        0.9493488274035422,
        1.0
      ],
      "denominator": 72,
      "intended_denominator": null,
      "numerator": 72,
      "rate": 1.0,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 0
    },
    "disagreement_new_vs_standalone_complete_cases": {
      "ci95": [
        0.7962504520935175,
        0.8273002501110384
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 1973,
      "rate": 0.8122684232194318,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "disagreement_new_vs_v1_alias_complete_cases": {
      "ci95": [
        0.7962504520935175,
        0.8273002501110384
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 1973,
      "rate": 0.8122684232194318,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "unique_catch_vs_standalone_complete_cases": {
      "ci95": [
        0.7962504520935175,
        0.8273002501110384
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 1973,
      "rate": 0.8122684232194318,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    },
    "unique_catch_vs_v1_alias_complete_cases": {
      "ci95": [
        0.7962504520935175,
        0.8273002501110384
      ],
      "denominator": 2429,
      "intended_denominator": 2431,
      "numerator": 1973,
      "rate": 0.8122684232194318,
      "status": "COMPLETE_CASE_PARTIAL",
      "undefined_count": 2
    }
  }
}

--- BEGIN undefined_cells.json ---
[
  {
    "baseline_header": [
      "",
      "",
      "",
      ""
    ],
    "error": "ValueError: field-hit undefined",
    "pair": [
      2,
      3
    ],
    "uid": "05c38b31-a20d-49c7-b4da-9d5d9aac6e53"
  },
  {
    "baseline_header": [
      "",
      "",
      "",
      "",
      ""
    ],
    "error": "ValueError: field-hit undefined",
    "pair": [
      0,
      1
    ],
    "uid": "a2900cdd-d5d5-47fa-ad3e-751fc634ae91"
  }
]

--- BEGIN p1_generation_manifest.json ---
{
  "double_run_byte_identical": true,
  "experiment_id": "PR-EXP-03",
  "generated_at_utc": "2026-10-11T08:34:06Z",
  "row_count": 2431,
  "run1_sha256": "8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69",
  "run2_sha256": "8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69"
}

--- BEGIN implementation_contract.md ---
# PR-EXP-03 implementation contract (frozen before P1)

experiment_id = PR-EXP-03
PREREG_SHA256 = f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250
shared_surface_freeze = research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
implementation_freeze_order = source hashes -> this contract hash -> P1 generation -> evaluation
pre_result_authorization = Loop C recheck result states "PR-EXP-03 ... PASS"; residual_notes_v1 is binding
stop_semantics = missing verdict-relevant input -> INPUT_MISSING; shared/prereg/source mismatch -> HASH_MISMATCH or PREREG_MISMATCH; forbidden action required -> STOP; undefined oracle cell -> NOT_EVALUABLE cell; sanity-gate failure -> INVALID

## Verbatim SOURCE_HASH inventory

SOURCE_HASH research/positive_repair_20261011/runs/PR-EXP-03/experiment.py = d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3
SOURCE_HASH scripts/m1_statement_parser.py = 747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b
SOURCE_HASH src/biz/m1_statement_parser.py = d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8
SOURCE_HASH research/stage_e_multileaf_20261010/run_multileaf_formal.py = d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4
SOURCE_HASH research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json = 8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693
SOURCE_HASH research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json = 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163
SOURCE_HASH research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl = 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f
SOURCE_HASH research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl = 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06
SOURCE_HASH research/stage_e_method_revision_20261009/multileaf_freeze.json = 7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d
SOURCE_HASH data/research/drift_v0/input/tatqa_tables.json = 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302
SOURCE_HASH data/research/drift_v0/output/injection_map.json = d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e
SOURCE_HASH research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md = 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290
SOURCE_HASH research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json = d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4
SOURCE_HASH research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md = f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250
SOURCE_HASH research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md = a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569
SOURCE_HASH config/eval_checkpoint_trees.json = 0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25

## Enumerated verdict-relevant inventory

| Parameter | Verbatim rule or pinned value | Status / missing semantics |
|---|---|---|
| prereg | research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md; sha256 f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250 | mismatch -> PREREG_MISMATCH |
| shared freeze | research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json; sha256 d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4 | mismatch -> HASH_MISMATCH |
| SOURCE_LOCAL_RESPONSE operational test | PR-EXP-03: unique new catches vs both baselines; A0/A1 clean; constant-1 documented to fail specificity | missing -> INPUT_MISSING; prose is not substituted for operational test |
| drift membership | all records in data/research/drift_v0/input/tatqa_tables.json, each `uid` exactly once; sha256 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302 | missing/duplicate/malformed -> INPUT_MISSING |
| all drift UID list | sorted unique UIDs, UTF-8 one UID plus LF per line | list sha256 b030d9df505eb406c00767947e6eab101a61a8f969c8e20550e68f3802be024a; missing -> INPUT_MISSING |
| held-out UID list | drift UIDs minus M/N exclusion registry; structural eligibility requires a nonempty table and header row width >= 2 | 2431/2431 eligible; list sha256 7a83aa01063be5bc10f5645236bd086771a2a16f9f2fa09b47dad782dedf8675; missing -> INPUT_MISSING |
| P1 ordering and membership | every eligible held-out UID ordered ascending by hex SHA-256 of `20261011:namespace="pr03-topology":uid`; no result or label is read for selection | 2431 ordered UIDs; list sha256 7a83aa01063be5bc10f5645236bd086771a2a16f9f2fa09b47dad782dedf8675; no eligible UID -> NOT_EVALUABLE |
| exclusion registry | exact command and list below | missing/unextractable -> INPUT_MISSING; overlap with P1 -> INVALID |
| pair selection | exact rule below | undefined pair -> NOT_EVALUABLE |
| oracle v2 source | research/positive_repair_20261011/runs/PR-EXP-03/experiment.py; sha256 d75afca6004c0ad3d76ba1f00203aa27d863161ad528af532f4d40cf592f57e3 | mismatch -> HASH_MISMATCH |
| canonicalizer identity | exact git_blob and raw-sha256 results below | mismatch -> HASH_MISMATCH |
| baseline runner | research/stage_e_multileaf_20261010/run_multileaf_formal.py; sha256 d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 | mismatch -> HASH_MISMATCH |
| baseline extract | lines 256-258 inclusive; extract sha256 e4cdc5c2b59e97cb51cbb5d88dc8386c9a9e08da29d541d7dfcab62aa1a21298; 188 bytes | mismatch -> HASH_MISMATCH |
| carriers | multileaf_freeze sha256 7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d; sample manifest sha256 8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693; paired artifacts sha256 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f | mismatch/ID mismatch -> HASH_MISMATCH or INPUT_MISSING |
| carrier subsample | exact rule below | empty/missing class/group -> NOT_EVALUABLE |
| bootstrap | seed 20261012; 10000 replicates; exact derived-seed rules below | missing -> INPUT_MISSING |
| arms | exact definitions below | any undefined cell -> NOT_EVALUABLE cell |
| outcome taxonomy | exactly one of POSITIVE / DIAG_ONLY / NULL / NEGATIVE / INVALID / NOT_EVALUABLE per prereg section 7 | no rescue or relabeling |

The injection map is verified at full sha256 d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e but is not an input to P1 selection or evaluation. config/eval_checkpoint_trees.json is verified read-only and is not modified.

## Shared-surface hash check results (all pre-run PASS)

| Key | Identity rule | Expected | Actual | Result |
|---|---|---|---|---|
| multileaf_response_rule_and_runner | raw_sha256 | d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 | d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4 | PASS |
| multileaf_paired_artifacts | raw_sha256 | 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f | 39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f | PASS |
| multileaf_prediction_rows | raw_sha256 | 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06 | 37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06 | PASS |
| multileaf_preresult_freeze_manifest | raw_sha256 | 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163 | 15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163 | PASS |
| canonicalizer_file | git_blob | def5161dd17fc14345d340879174ed01e0277626 | rev-parse def5161dd17fc14345d340879174ed01e0277626; hash-object def5161dd17fc14345d340879174ed01e0277626 | PASS |
| source_local_term_sheet | raw_sha256 | 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290 | 4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290 | PASS |
| gb10_only_inputs[1] drift tables | sha256 prefix | 3e7e0568 | 3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302 | PASS |
| gb10_only_inputs[2] injection map | sha256 prefix | d7612405 | d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e | PASS |

Verified canonicalizer value required by residual_notes_v1: raw sha256 = 747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b (GB10 informational host value). The binding identity is git_blob = def5161dd17fc14345d340879174ed01e0277626, verified by both commands. The implementation source src/biz/m1_statement_parser.py is raw sha256 d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8 and git_blob 47e379bbe8e0a5c4d637123a2e4dda73b53f06f8 by both commands.

## Verbatim M/N UID exclusion extraction command

Command executed verbatim:

`python3 -c 'import json; x=json.load(open("research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json")); print("\n".join(sorted({r["source_uid"] for r in x["rows"] if r["stage"] in {"M","N"}})))'`

Extracted registry (48 UIDs; UTF-8 one UID plus LF list sha256 e511b6ed7ad40d0b336cdf49362af728b7301b6d696322bd3ede87b883ef99cd):

```text
1a153890-b70e-4746-947b-de2ff48027ce
1b6fe333-4e8b-468e-af0c-4de123fca154
2266f020-d5ef-4343-86d3-64f3fe883976
233252a6-3a26-489a-9e55-0b8fd9004c71
28f9a92f-7b79-4cd7-ae29-2b712e0856e5
2cb3ef36-9d41-4357-8b09-205ca457a263
403e498a-59a2-4d4f-b560-a7ca853d6dc2
43fac1ff-7968-4e7b-adcc-8a611b283ff2
481dd318-a69d-498e-aa28-869093371f0a
4c0023fe-f2df-49a5-babf-bc9bcf5367ba
4fa0f9f0-4665-4faa-89e8-7d0f208331d1
515a0a4c-fae0-4b03-96f1-2961eb823479
538ada9e-1c28-447d-9ff7-b12995c2432d
5728e846-a3da-4e10-b117-738cbbce305c
5db485cf-6c57-4869-8065-14e334b4b733
5e2b5b29-e0c9-4abb-935e-a3fc13d18285
5f46a008-12b7-4c0d-b9e5-4b8e31cb0ba8
6651cfa6-fe03-41a5-8713-32eb0e3b704a
68b8d514-802c-4ebc-a754-db4a3db7f9fd
6bf238a5-0a3e-492d-91f8-7f62d3b37fba
6e698627-eeee-46e3-b1b0-76dae40aa474
725f49da-9041-4f26-8b57-62427b0a3f92
736d8572-272b-4cab-8062-9012ec6e7fe9
736f65a8-7b6b-47bc-8c6a-3a2d641695bc
73a817fc-25df-494d-b0f2-79cfdab34076
7cea4c2f-f2a9-4a25-a459-6b193e821841
8692f92d-668a-452d-be7a-2b491ee27585
8da9eb14-c639-44f7-8730-2213d34f050d
8e4af07f-365e-4b40-b1b9-502b2fa50648
906decc3-1bc8-49a4-b0ff-a79d3ce5531f
98ac5f10-46c6-431d-b5a0-0463870a87af
9b1ab08e-2478-417c-9fcb-f654f88104ff
a0bd03e7-fbb5-447f-ad77-ecc116b1134a
a9bb6c15-8103-456a-b273-7b35b2eed202
aea2257f-c275-4c9f-a4fe-81b0b39693eb
b1164469-b658-4743-910a-9508c3b21b85
c0f66238-591a-4693-b2d2-fee0f6843420
d123906f-d70e-4313-9489-3e9f38347895
d66638f7-6e4a-464b-ad17-d2a51dad9b6d
de1c7388-c0ab-45d5-9c5a-259273d3f42c
e614befa-40ae-43c0-93b1-385899b6b181
e61fed25-0910-4ae5-ad68-8ba18dfcc8f9
ed31537b-9e9b-4645-ba47-3a2af77411f8
ef1bb586-08a6-4a28-b556-191841742424
f069afb6-f2a4-43fc-8908-9686b62cf714
f440390f-d988-4765-b573-273d5e351be2
f5511f3c-b02d-4142-aa16-0b87cd61690f
f77930d9-10f3-4ea3-8557-c6554fc9c823
```

## P1 generator and pair-selection rules

For each selected UID, `pair_index = int(SHA-256_hex("20261011:pr03-pair:" + uid), 16) mod (len(table[0]) - 1)`; pair = `[pair_index, pair_index + 1]`. Swap those adjacent positions in every row that contains both positions. The generator does not read stage/family/outcome labels to choose UIDs or pairs. It preserves every cell value, every row length, the row count, and the column count. Output serialization is UTF-8 JSON Lines with sorted keys and compact separators, one LF after each row. Generator run 1 and run 2 must be byte-identical; any mismatch is INVALID.

## Oracle v2 frozen semantics

`structural_signature(table) = (column_count, ordered positional header-token sequence, row_count)` where `column_count = max(len(row) for row in table)`, header token at position j is `normalize_header(table[0][j])` when j exists and `normalize_header(None) = ""` otherwise, and `row_count = len(table)`. Pinned canonicalizer semantics are the exact implementation at src/biz/m1_statement_parser.py lines 70-74: apply regex `[\\s\\u3000\\(\\)\\[\\]{}（）【】《》<>:：;；,，.。、/\\\\\\-—_~`'\"!！?？*]+`, remove matches, lowercase, with None -> empty string.

`response = int(structural_signature(baseline) != structural_signature(injected))`, emitted only at leaf `parse.table.regression`. The oracle receives table artifacts only; it never receives mutation labels, held-out outcomes, thresholds, or field-hit scores. For a carrier with no table (stage R), the defined unchanged execution artifact is `NO_TABLE = (0, (), 0)` for both baseline and injected, so response is 0. Any genuinely missing or malformed artifact is an undefined cell -> NOT_EVALUABLE cell, not 0.

## Frozen baseline extracts and implementations

Runner file hash: d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4.

Verbatim extract from run_multileaf_formal.py lines 256-258 inclusive (188 bytes; extract sha256 e4cdc5c2b59e97cb51cbb5d88dc8386c9a9e08da29d541d7dfcab62aa1a21298):

```python
    response = {leaf: 0 for leaf in leaves}
    response["parse.table.regression"] = int(mutated_hit < baseline_hit)
    response["parse.field.hit_rate"] = int(mutated_hit < baseline_hit)
```

The v1 aliased baseline selects `parse.table.regression` from that extract. The standalone field-hit baseline independently computes the unchanged formula from lines 248-254 and selects `parse.field.hit_rate`. Both use the same population and one leaf response per case. Both are compared to oracle v2 without alteration.

## Arms

- A0 no-op/identity: `structural_signature(table) != structural_signature(table)` on every P1 table; expected 0.
- A1 value-only specificity: select the non-header cell at flattened row-major index `int(SHA256("20261011:pr03-value-only:" + uid), 16) mod number_of_non_header_cells`; replace it with `__PR03_A1_VALUE__`, appending underscores only if needed to ensure a different string. Structure is preserved; expected 0.
- A2 P1: the frozen adjacent-column transposition; expected 1.
- A3 M1 regression: all 72 frozen M carrier rows; construct the injected table by changing only `source_object.cell` to `field_after`; expected 0.
- Constant-1 control: returns 1 on P1, A0, and A1; P1 coverage is 1 but A0/A1 false positives are both denominators, so specificity fails and it cannot support POSITIVE.

Carrier construction used for diagnostic evaluation: M changes only `source_object.cell` to `field_after`; N changes only `source_object.mutated_cell` to `value_after`; R has the defined unchanged NO_TABLE artifact. Source table JSON hashes are checked before construction.

## Mixed diagnosability population and classifier

Carrier subsample rule: group all 216 frozen carrier rows by `cluster_id`; within each group choose the row minimizing `(SHA-256_hex('20261011:namespace="pr03-carrier-subsample":' + cluster_id + ':' + sample_id), sample_id)`. This yields exactly one row per cluster and never changes carrier artifacts. Mixed population = all 2431 P1 rows plus this 72-row carrier subsample.

Ground truth is read only after freeze: P1 uses prereg-fixed `stage_label="M"` and `family_label="topology_transposition"`; carrier rows use the frozen manifest fields `stage` and `injection_operation`. LOCO group = `source_uid` for both P1 and carriers, so a shared source UID remains in one held-out group and there is no source overlap across folds.

Classifier is the frozen deterministic nearest-centroid rule: one scalar binary feature, Euclidean distance equivalent to absolute distance; leave one source_uid group out; train centroids on remaining groups; classes present in the full mixed population; tie -> `__TIE__` and scored incorrect. Macro-F1 uses the union of truth and prediction labels, including ties as prediction-only labels. Primary `Δdiag = min(Δstage_macro_F1, Δfamily_macro_F1)` against the v1 aliased baseline. Stage and family deltas are both reported at conclusion level only.

Coverage delta cluster bootstrap: resample P1 source_uid/table groups with replacement, 10000 replicates, seed 20261012, NumPy-free deterministic `random.Random`; percentile interval uses linear interpolation at 2.5% and 97.5%. Diagnosability cluster bootstrap: resample mixed source_uid groups with replacement, 10000 replicates; metric-specific seed is the integer represented by the first 16 hexadecimal digits of SHA-256 of `20261012:diag:stage_label` or `20261012:diag:family_label`; same percentile rule. Wilson 95% intervals are used for individual binary rates. Counts are raw exact numerators/denominators.

## Sanity, attribution, cost, and outcome gates

Sanity gate: on P1, oracle v2 must differ from standalone field-hit on at least one row; on all 216 frozen carriers, oracle v2 must not be a monotone binary function of standalone field-hit. A binary mapping is monotone when each field-hit value maps to at most one structural value and the two ordered outputs are nondecreasing or nonincreasing. Any failure -> INVALID.

Attribution pass = unique new catches against both baseline oracles AND A0/A1 structural false-positive counts are zero AND the constant-1 rule is documented to fail A0/A1 specificity. The SOURCE_LOCAL_RESPONSE prose does not override this per-experiment operational test.

Cost: exactly one leaf response per case for each oracle on P1, A0, A1, A3, and mixed diagnosability. Exact check-count equality is the only cost tolerance; no runtime performance claim. model_calls=0, judge_calls=0, training=0, network=0, database=0, production-service calls=0. Runtime is recorded only as cost ledger time.

Outcome priority after executable/defined gates: INVALID for sanity, UID overlap, double-run mismatch, cost inequivalence, label access before freeze, or post-freeze edit; NOT_EVALUABLE for missing/undefined P1 or oracle semantics; NEGATIVE if Δdiag < -0.02; POSITIVE only if coverage delta >0 with CI lower>0, Δdiag >= -0.02, A0/A1 pass, no A3 regression, and attribution pass; DIAG_ONLY only on the prereg's nonpositive/CI-inclusive coverage branch with Δdiag > +0.02; otherwise NULL. Exactly one canonical label is emitted.

## Binding residual addendum application

residual_notes_v1.md is read and incorporated before P1: canonicalizer verified sha256 recorded; SOURCE_LOCAL_RESPONSE pinned by sha256 and its PR-EXP-03 operational test is binding; full GB10 drift and injection-map hashes are recorded; the inventory above is exhaustive with INPUT_MISSING semantics; drift membership, UID list/exclusion registry, pair rule, oracle source, baseline extract hashes, arms, and bootstrap seed are enumerated. Frozen multileaf carriers, D3 inputs, drift outputs, config/eval_checkpoint_trees.json, tests, and frozen hashes remain read-only.

(NOTE: raw P1 rows are 2,431-line jsonl, run1=run2 sha256 8171a0a263f12f13591e5bbb934b6b830f79646d179c0ae0c1cbe234946e3a69; not embedded for size; per-row recomputation is limited to the aggregates above.)
--- END PACKET ---
