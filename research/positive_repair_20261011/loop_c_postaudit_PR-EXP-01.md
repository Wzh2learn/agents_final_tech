# Loop C Post-Result Independent Audit — PR-EXP-01 (INTERVENTION_REPAIR)

You are the independent Loop C auditor. This is a POST-RESULT audit of one completed Track P experiment. Read-only, packet-only, report-only: no tools, no file reads, no network, no edits. Judge strictly from this packet; missing evidence -> UNVERIFIED. Do not modify, re-run, or rescue the result. Labels: FACT / INFERENCE / UNVERIFIED.

## Round context (disclosed facts)
- Track P first wave: PR-EXP-03 INTERVENTION_REPAIR / PR-EXP-01 INTERVENTION_REPAIR / PR-EXP-04 GENERALIZATION_TEST / PR-EXP-07 ROBUSTNESS_ANTI_TAUTOLOGY. Only INTERVENTION_REPAIR positives may ever count toward the synthesis gate.
- Registered class for PR-EXP-01: NOT_EVALUABLE.
- Disclosed incidents, NOT part of this experiment's scientific record: (i) two engineering dispatch layers (a1 INPUT_MISSING x4; a2 HASH_MISMATCH x4) were fail-closed infrastructure failures, zero scientific side effects, excluded from scientific classes; (ii) the prereg re-audit log lost its leading sections in capture (verdicts recovered from GLOBAL); (iii) the Loop D prereg/sanity-gate definitions may contain defects - examine critically.
- Registered NOT_EVALUABLE came from a fail-closed Phase 0 qualification: the independent checker reported unverifiable_identity (status FAIL) although the panel appeared non-empty (9,566 admitted of 37,900 candidate applications; panel_exact_complete_match true; AST generator-independence true) and the harmful side was never read (harmful_side_read=false, scoring_performed=false). Examine the checker logic/verdict fields critically: is NOT_EVALUABLE the correct scientific class per prereg sections 2/6, or is this an engineering/contract defect that must not be counted as a scientific NULL/NEGATIVE/INVALID?

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
--- BEGIN prereg v2 (PR-EXP-01) ---
# Prereg — PR-EXP-01: SYNTHETIC_NULL_SUPPORT_REPAIR

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-01 | candidate: PR-01 | role: INTERVENTION_REPAIR
> claim object: SYNTHETIC_NULL_SUPPORT_REPAIR — never "empirical clean-only matched-FPR repair"
> frozen: 2026-10-11 | authority: Human decision 2026-10-11; execution requires Loop C pre-result PASS and the null-semantics qualification below

## 1. Background (facts)
Clean-only matched-FPR operating point NOT_IDENTIFIABLE; 2,382 clean rows carry contrastive support exactly {0}; the frozen reanalysis doc names the remedy: nonzero clean support via a preregistered null-mutation panel.

## 2. Null-semantics qualification (fail-closed; surfaces defined)
- Scored surface: the exact raw observation surface consumed by the frozen contrastive score computation — pinned verbatim in the implementation contract by reading the frozen scorer implementation (path + hash + exact input expression).
- Task-truth surface: downstream canonical artifacts (post-canonicalization pipeline outputs) — identity (hash equality) required.
- Admitted edits must be NON-identity on the scored surface AND hash-identical on the task-truth surface. If no edits satisfy both under the frozen edit DSL -> NOT_EVALUABLE (panel empty), never NULL.
- Generator/checker independence: checker must not import the generator module (AST import check); separate file-hash lineage recorded; checker re-runs canonicalization + downstream pipeline and requires downstream hash equality.
- Panel completeness: panel = the complete admitted set under the frozen rule; no sampling, no outcome-based selection.

## 3. Populations and split
- Calibration nulls: admitted edits on calibration folds (frozen 5-fold table-UID rule inherited from the matched-FPR reanalysis namespace; rule text pinned verbatim in the implementation contract).
- Held-out nulls: disjoint folds.
- Harmful pairs: frozen 111 harmful pairs; NEVER used for threshold selection; read only after the operating point is frozen.

## 4. Threshold rule (frozen, incl. ties)
Threshold = the smallest t such that fraction(calibration-null scores > t) <= alpha, alpha=0.05; strict greater-than comparison; ties handled by the frozen "smallest t" rule (all candidate t drawn from the calibration-null score support). Rule hash-frozen before any harmful-side read.

## 5. Primary qualification and positive rule
- calibration null support > single point;
- threshold solely from calibration nulls;
- held-out null FPR <= alpha;
- THEN held-out harmful TPR at the frozen operating point (+ paired cluster bootstrap CI).
- POSITIVE = operating point becomes identifiable AND held-out null FPR contract satisfied. Identifiability status recorded as a result ATTRIBUTE, not a label.

## 6. Outcome labels (canonical, single string per run)
- POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE (exactly one).
- NULL: substantive run failing support or FPR contract (informative: bounds the remedy). 
- NOT_EVALUABLE: empty admission set, unverifiable identity, or unpinnable scored surface; never merged into NULL.
- INVALID: harmful-side involvement in selection; any post-freeze edit; relabeling as empirical clean-only repair.

## 7. Reporting boundary and bridge report
- Report the original 2,382-row identifiability result separately; never silently replace E2's population. All conclusions phrased as SYNTHETIC_NULL_SUPPORT_REPAIR.
- Bridge report (required): empirical clean-row score distribution + their FPR at the frozen threshold, labeled explicitly as a non-comparable empirical-vs-synthetic read.

## 8. Cost
Zero model calls; deterministic; calibration + held-out runs in minutes; same-budget comparison = same procedure on both null partitions.

## 9. Stop conditions
Qualification failure or unverifiable identity -> STOP (NOT_EVALUABLE). If the scored surface cannot be pinned without changing the claim object -> STOP_BRANCH. No threshold hunting; any scope change -> new prereg + re-audit.
--- BEGIN receipt.json ---
{
  "claim_object": "SYNTHETIC_NULL_SUPPORT_REPAIR",
  "cost": {
    "database_calls": 0,
    "judge_calls": 0,
    "model_calls": 0,
    "network_calls": 0,
    "service_calls": 0,
    "training_runs": 0,
    "wall_seconds": 10.102562
  },
  "deviations": [],
  "end_utc": "2026-10-11T08:32:03.010155Z",
  "experiment_id": "PR-EXP-01",
  "harmful_semantic_read_utc": null,
  "implementation_contract_sha256": "b3447ddb17da3e81eceb5347bb8f28468c2fb66b4f751aa457e78ff37c51f9ab",
  "implementation_hashes": {
    "check_null_panel.py": "53a9cc017d0382869afe1ed019696d962d8d516e7343ae8373aad76616a02228",
    "generate_null_panel.py": "fbade41436b12724a1ca9ea7f58cf86cfa8d3fb01f87b1cacbedbb5b2093c0f8",
    "run_pr_exp_01.py": "f66dfbeeaded20ba9dfe243ec4d3769db32cb8e6b3a110415f9166aba5fccb10"
  },
  "input_hashes": {
    "config/eval_checkpoint_trees.json": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "data/research/drift_v0/input/tatqa_tables.json": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    "data/research/drift_v0/output/injection_map.json": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
    "research/paper_d3_matched_fpr_stage_a.py": "56f0c8519236f4420a63835bf95ea6c6853bb838d94527486519a3e9482d8f9f",
    "research/paper_t1_eval_baselines.py": "01772e84efb3f579a1146c7c0b0e76f42b1e77625eee1124f901ab03b4c29f79",
    "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    "research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-01.md": "424bc01707bdd9aa075196725b0f35b8aa1193f923e68bc07cebfbd0b4aa71e8",
    "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
    "research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log": "a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d",
    "research/positive_repair_20261011/prereg_freeze_manifest_v2.json": "b543953952c3af87b9db98f360b7d5b57d02a6dfe399cab8621c822b2b0dda5f",
    "research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md": "41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3",
    "research/positive_repair_20261011/round_receipt_v4_hashfix.json": "7c942208c92c49fa4e54a066e7ce479b8d23a130d2dd5fadf80a6eb4fd87aa26",
    "research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py": "f926c63d602db9ecbd2c64a8cdb0fff5850875a16ea88d386e905cc8bcb24489",
    "scripts/m1_statement_parser.py:git_blob": "def5161dd17fc14345d340879174ed01e0277626",
    "src/biz/m1_statement_parser.py": "d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8"
  },
  "outcome_label": "NOT_EVALUABLE",
  "output_hashes": {
    "generator_summary.json": "a76e2c2212f330d720e7322134b862bab114ec044a6dabffda02463433c8c073",
    "panel.jsonl": "2baa68e1600aae446fcf5ac825593f5993b1c7274e857bc9736522e0c8372cd7",
    "phase0_qualification.json": "3bb1092c641dec51caede00a34d9efc796541368dd3d552f690ea5eeb878c735",
    "result.json": "991a21ce67636ea01b6122a88caa327c62d79b5102e7e79ecb0552aa9a7d8011"
  },
  "phase_reached": "PHASE_0_STOP",
  "prereg_sha256": "41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3",
  "raw_metrics": {
    "bridge": "not applicable: no frozen threshold",
    "calibration": "not applicable: Phase 0 stopped before scoring",
    "generator_summary": {
      "admitted_count": 9566,
      "candidate_scope": "every cell of every usable non-injected source table × every DSL rule",
      "counts": {
        "admitted": 9566,
        "candidate_applications": 37900,
        "candidate_identity_at_rule": 12339,
        "clean_usable_tables": 2382,
        "excluded_injected_uid": 95,
        "excluded_no_canonical": 2,
        "rejected_task_truth_mismatch": 15995,
        "source_tables": 2479
      },
      "edit_dsl_rules": [
        "edge_space_prefix",
        "edge_space_suffix",
        "internal_single_space_removed",
        "case_swap"
      ],
      "injection_map_sha256": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
      "namespace": "PR-EXP-01_null_panel_generator_v1",
      "panel_completeness": "all and only candidate applications satisfying raw nonidentity and task-truth hash identity; no sampling",
      "panel_sha256": "2baa68e1600aae446fcf5ac825593f5993b1c7274e857bc9736522e0c8372cd7",
      "source_tables_sha256": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302"
    },
    "harmful": "not read",
    "heldout_null": "not applicable: Phase 0 stopped before scoring",
    "phase0": {
      "admission_failure_count": 15995,
      "admission_failures": [
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 4,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 4,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 4,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 5,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 5,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 5,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "00234411-6779-46a1-915a-d58e3e27716a"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "008149bc-f997-49d9-a981-f01f19579451"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "internal_single_space_removed",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "case_swap",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
        },
        {
          "index": 1,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
        },
        {
          "index": 2,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
        },
        {
          "index": 3,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_prefix",
          "uid": "00a5764e-8bb7-48f1-a4cb-bea0edf188b1"
        },
        {
          "index": 0,
          "kind": "truth_mismatch",
          "rule": "edge_space_suffix",
          "uid": "00a5764e-8bb7-48f1-a4cb-bea0edf188b1"
        }
      ],
      "admitted_count_observed": 9566,
      "admitted_count_recomputed": 9566,
      "ast_independence": {
        "generator_imports": [],
        "imports": [
          "__future__",
          "argparse",
          "ast",
          "biz.m1_statement_parser",
          "collections",
          "hashlib",
          "importlib.util",
          "json",
          "pathlib",
          "sys"
        ],
        "passes": true
      },
      "candidate_count_recomputed": 37900,
      "checker_path": "research/positive_repair_20261011/runs/PR-EXP-01/check_null_panel.py",
      "checker_sha256": "53a9cc017d0382869afe1ed019696d962d8d516e7343ae8373aad76616a02228",
      "duplicate_candidate_ids": 0,
      "empty_admission": false,
      "generator_path": "research/positive_repair_20261011/runs/PR-EXP-01/generate_null_panel.py",
      "generator_sha256": "fbade41436b12724a1ca9ea7f58cf86cfa8d3fb01f87b1cacbedbb5b2093c0f8",
      "namespace": "PR-EXP-01_independent_panel_checker_v1",
      "panel_exact_complete_match": true,
      "separate_file_hash_lineage": true,
      "status": "FAIL",
      "unverifiable_identity": true
    }
  },
  "start_utc": "2026-10-11T08:31:52.907590Z",
  "status": "NOT_EVALUABLE",
  "threshold_frozen_before_harmful_semantic_read": false,
  "threshold_frozen_utc": null,
  "unverified_items": [
    "No scoring or harmful-side claim is made because Phase 0 failed."
  ]
}

--- BEGIN result.json ---
{
  "claim_object": "SYNTHETIC_NULL_SUPPORT_REPAIR",
  "experiment_id": "PR-EXP-01",
  "harmful_side_read": false,
  "original_clean_identifiability": {
    "population": "2,382 empirical clean rows",
    "reported_separately": true,
    "status": "NOT_IDENTIFIABLE",
    "support": [
      0
    ]
  },
  "outcome_label": "NOT_EVALUABLE",
  "phase0": {
    "admission_failure_count": 15995,
    "admission_failures": [
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 4,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 4,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 4,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 5,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 5,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 5,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "00234411-6779-46a1-915a-d58e3e27716a"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "008149bc-f997-49d9-a981-f01f19579451"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "internal_single_space_removed",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "case_swap",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
      },
      {
        "index": 1,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
      },
      {
        "index": 2,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
      },
      {
        "index": 3,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_prefix",
        "uid": "00a5764e-8bb7-48f1-a4cb-bea0edf188b1"
      },
      {
        "index": 0,
        "kind": "truth_mismatch",
        "rule": "edge_space_suffix",
        "uid": "00a5764e-8bb7-48f1-a4cb-bea0edf188b1"
      }
    ],
    "admitted_count_observed": 9566,
    "admitted_count_recomputed": 9566,
    "ast_independence": {
      "generator_imports": [],
      "imports": [
        "__future__",
        "argparse",
        "ast",
        "biz.m1_statement_parser",
        "collections",
        "hashlib",
        "importlib.util",
        "json",
        "pathlib",
        "sys"
      ],
      "passes": true
    },
    "candidate_count_recomputed": 37900,
    "checker_path": "research/positive_repair_20261011/runs/PR-EXP-01/check_null_panel.py",
    "checker_sha256": "53a9cc017d0382869afe1ed019696d962d8d516e7343ae8373aad76616a02228",
    "duplicate_candidate_ids": 0,
    "empty_admission": false,
    "generator_path": "research/positive_repair_20261011/runs/PR-EXP-01/generate_null_panel.py",
    "generator_sha256": "fbade41436b12724a1ca9ea7f58cf86cfa8d3fb01f87b1cacbedbb5b2093c0f8",
    "namespace": "PR-EXP-01_independent_panel_checker_v1",
    "panel_exact_complete_match": true,
    "separate_file_hash_lineage": true,
    "status": "FAIL",
    "unverifiable_identity": true
  },
  "reason": "Phase 0 qualification failed: empty admission or unverifiable identity",
  "scoring_performed": false
}

--- BEGIN phase0_qualification.json ---
{
  "admission_failure_count": 15995,
  "admission_failures": [
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "000abf67-dc6c-4c08-a922-70664fb01b4b"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0012a118-070e-43bf-a23c-19fe94cee4e9"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "001781c6-0e17-4fdd-b000-011e3ed66d6e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "001e29d7-77e9-4434-9a3d-f72ef640fa79"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 4,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 4,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 4,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 5,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 5,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 5,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "00234411-6779-46a1-915a-d58e3e27716a"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "0024d75d-53db-4d93-8d6f-c207ae3f2fe7"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "0027cf6e-f6e8-4d8b-b4ee-0b9f9aeb1f54"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "003a9449-5c23-446f-ae11-1d478c7f6719"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "0042d133-e5c2-4260-bc73-f8168cdf6001"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "004dd600-f3df-4212-8ef9-e3b16ced923e"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "008149bc-f997-49d9-a981-f01f19579451"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "00842ff1-169b-4246-9208-7cfef29a4363"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "internal_single_space_removed",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "case_swap",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "008eaf4e-4d70-496b-aa25-b842b05a3560"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
    },
    {
      "index": 1,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
    },
    {
      "index": 2,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
    },
    {
      "index": 3,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00a11cc5-dc80-4e56-baea-d12d74ca79f5"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_prefix",
      "uid": "00a5764e-8bb7-48f1-a4cb-bea0edf188b1"
    },
    {
      "index": 0,
      "kind": "truth_mismatch",
      "rule": "edge_space_suffix",
      "uid": "00a5764e-8bb7-48f1-a4cb-bea0edf188b1"
    }
  ],
  "admitted_count_observed": 9566,
  "admitted_count_recomputed": 9566,
  "ast_independence": {
    "generator_imports": [],
    "imports": [
      "__future__",
      "argparse",
      "ast",
      "biz.m1_statement_parser",
      "collections",
      "hashlib",
      "importlib.util",
      "json",
      "pathlib",
      "sys"
    ],
    "passes": true
  },
  "candidate_count_recomputed": 37900,
  "checker_path": "research/positive_repair_20261011/runs/PR-EXP-01/check_null_panel.py",
  "checker_sha256": "53a9cc017d0382869afe1ed019696d962d8d516e7343ae8373aad76616a02228",
  "duplicate_candidate_ids": 0,
  "empty_admission": false,
  "generator_path": "research/positive_repair_20261011/runs/PR-EXP-01/generate_null_panel.py",
  "generator_sha256": "fbade41436b12724a1ca9ea7f58cf86cfa8d3fb01f87b1cacbedbb5b2093c0f8",
  "namespace": "PR-EXP-01_independent_panel_checker_v1",
  "panel_exact_complete_match": true,
  "separate_file_hash_lineage": true,
  "status": "FAIL",
  "unverifiable_identity": true
}

--- BEGIN generator_summary.json ---
{
  "admitted_count": 9566,
  "candidate_scope": "every cell of every usable non-injected source table × every DSL rule",
  "counts": {
    "admitted": 9566,
    "candidate_applications": 37900,
    "candidate_identity_at_rule": 12339,
    "clean_usable_tables": 2382,
    "excluded_injected_uid": 95,
    "excluded_no_canonical": 2,
    "rejected_task_truth_mismatch": 15995,
    "source_tables": 2479
  },
  "edit_dsl_rules": [
    "edge_space_prefix",
    "edge_space_suffix",
    "internal_single_space_removed",
    "case_swap"
  ],
  "injection_map_sha256": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
  "namespace": "PR-EXP-01_null_panel_generator_v1",
  "panel_completeness": "all and only candidate applications satisfying raw nonidentity and task-truth hash identity; no sampling",
  "panel_sha256": "2baa68e1600aae446fcf5ac825593f5993b1c7274e857bc9736522e0c8372cd7",
  "source_tables_sha256": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302"
}

--- BEGIN implementation_contract.md ---
# PR-EXP-01 Implementation Contract — SYNTHETIC_NULL_SUPPORT_REPAIR

Frozen before panel generation and before any scoring. This contract applies the binding `residual_notes_v1` addendum and is the execution inventory for Loop A / GB10.

## 1. Goal, done conditions, exclusions, and stops

- Goal: execute exactly one deterministic Track P experiment, PR-EXP-01, under prereg v2.
- Done: Phase 0 either proves a complete non-empty admitted panel or stops `NOT_EVALUABLE`; if admitted, freeze a calibration-only threshold before semantic harmful-side access, evaluate held-out nulls, report harmful TPR with paired cluster bootstrap CI, produce the required empirical bridge, and emit exactly one canonical label in `result.json` plus `receipt.json`.
- Exclusions: no model/judge calls, training, services, databases, network, commit/push, prereg edits, threshold hunting, label misuse, shared-surface edits, or execution of any other experiment.
- Stop conditions: `INPUT_MISSING`, `PREREG_MISMATCH`, `HASH_MISMATCH`, unpinnable scored surface (`STOP_BRANCH`), empty/unverifiable Phase 0 admission (`NOT_EVALUABLE`), or any requirement for a forbidden action.
- Invalid conditions: harmful-side involvement in selection, any post-freeze source/implementation edit, or relabeling the claim as an empirical clean-only repair.

## 2. Authority and qualification gate

| Item | Path | Verified identity |
|---|---|---|
| Scientific contract | `research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md` | sha256 `41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3` |
| Prereg freeze | `research/positive_repair_20261011/prereg_freeze_manifest_v2.json` | sha256 `b543953952c3af87b9db98f360b7d5b57d02a6dfe399cab8621c822b2b0dda5f` |
| Loop C pre-result re-audit | `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log` | sha256 `a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d`; PR-EXP-01 `PASS`, authorization present |
| Shared-surface freeze | `research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json` | current raw sha256 `d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4`; all entries verified before this contract |
| Hash-fix authority | `research/positive_repair_20261011/round_receipt_v4_hashfix.json` | sha256 `7c942208c92c49fa4e54a066e7ce479b8d23a130d2dd5fadf80a6eb4fd87aa26` |
| SOURCE_LOCAL_RESPONSE | `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md` | raw sha256 `4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290` |
| Binding residual notes | `research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md` | raw sha256 `a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569` |
| Loop A card | `research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-01.md` | raw sha256 `424bc01707bdd9aa075196725b0f35b8aa1193f923e68bc07cebfbd0b4aa71e8` |

Per experiment, `SOURCE_LOCAL_RESPONSE` is restricted exactly as frozen: claim object is only `SYNTHETIC_NULL_SUPPORT_REPAIR`, and source-local language is not used. The residual-note requirements—verified canonicalizer value, source-term-sheet hash, full GB10 input hashes, enumerated inventory, `INPUT_MISSING` semantics, and PR-EXP-01 edit-DSL/admission/fold/scored-surface pinning—are incorporated below.

## 3. Hash-checked verdict-relevant inventory

Any absent file or identity mismatch is `INPUT_MISSING`/`HASH_MISMATCH` and stops before scoring.

### 3.1 Shared and pre-threshold sources

| Parameter | Path | Identity |
|---|---|---|
| Frozen clean scorer | `research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py` | raw sha256 `f926c63d602db9ecbd2c64a8cdb0fff5850875a16ea88d386e905cc8bcb24489` |
| D3 contrastive implementation | `research/paper_d3_matched_fpr_stage_a.py` | raw sha256 `56f0c8519236f4420a63835bf95ea6c6853bb838d94527486519a3e9482d8f9f` |
| Tree aggregation implementation | `research/paper_t1_eval_baselines.py` | raw sha256 `01772e84efb3f579a1146c7c0b0e76f42b1e77625eee1124f901ab03b4c29f79` |
| Canonicalizer wrapper | `scripts/m1_statement_parser.py` | `identity_rule=git_blob`; `git rev-parse HEAD:...` = `def5161dd17fc14345d340879174ed01e0277626`; `git hash-object ...` = same; verified raw sha256 `747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b` (GB10 informational) |
| Canonicalizer implementation | `src/biz/m1_statement_parser.py` | raw sha256 `d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8` |
| Frozen tree | `config/eval_checkpoint_trees.json` | raw sha256 `0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25` |
| Drift corpus tables (GB10-only) | `data/research/drift_v0/input/tatqa_tables.json` | full raw sha256 `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` |
| Injection map (GB10-only) | `data/research/drift_v0/output/injection_map.json` | full raw sha256 `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e` |

### 3.2 Harmful-side sources, semantically opened only after threshold freeze

Hash pinning here is an inventory identity; semantic row parsing and harmful reproduction are deferred until `threshold_freeze.json` exists, is sha256-sidecar bound, and is read-only.

| Parameter | Path | raw sha256 |
|---|---|---|
| Injected corpus | `data/research/drift_v0/output/injected_tables.json` | `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9` |
| D1 labels/scores carrier | `logs/graph/eval/d1_mutant_validity_audit.json` | `ef1d46ed9ca1ae3832f35d2796b3a51be34c912897d68b40d73c9413d8651a2b` |
| D2 deterministic carrier | `logs/graph/eval/d2_cross_matcher_det.json` | `7bb268e5da19590c9f58e71e293c3b66e4e5071f53932b41792ec8fb0ea1f146` |
| D2 embedding carrier | `logs/graph/eval/d2_cross_matcher_embed.json` | `ed3d3905e42c41ab71d4dfacc64a3609de2dd12d5e20cf9b5b363a90d29d4bbf` |
| W2 E16 carrier | `logs/graph/eval/_w2_e16_section.json` | `d02057eda97618fd57e9051babf45bf0faab3e5ba923c68cb39cafa07d6e2757` |
| Frozen D3 output carrier | `logs/graph/eval/d3_matched_fpr_stage_a.json` | `3318ac178a0c3317ce18d69663b942e289c2668f4b604082606a549172f2ab10` |

### 3.3 Frozen implementation lineage

| File | sha256 |
|---|---|
| `generate_null_panel.py` | `fbade41436b12724a1ca9ea7f58cf86cfa8d3fb01f87b1cacbedbb5b2093c0f8` |
| `check_null_panel.py` | `53a9cc017d0382869afe1ed019696d962d8d516e7343ae8373aad76616a02228` |
| `run_pr_exp_01.py` | `f66dfbeeaded20ba9dfe243ec4d3769db32cb8e6b3a110415f9166aba5fccb10` |

The three files parse as Python AST before freeze. The checker's own AST import inventory contains no module containing `generate_null_panel`; it has a separate file hash and does not import the generator.

## 4. Scored surface pinned verbatim

The frozen clean implementation is `research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py` at the pinned hash above. Its exact raw observation input and score expression are:

```python
header = d3.header_of(table["table"][0])
canonical = d3.unique_canonical(header, mp)
h, _ = d3.hit_rate(header, canonical, mp)
h_repeat = d3.hit_rate(header, canonical, mp)[0]
flat = round((h - h_repeat) * 10.0, 6)
root = d3.root_of(tb, h)
layered = round(root - d3.root_of(tb, h_repeat), 6)
```

The corresponding frozen two-observation expression is in `research/paper_d3_matched_fpr_stage_a.py` at the pinned hash:

```python
inj_hdr = header_of(corp["by_uid"][uid][0])
oh = orig_header(inj_hdr, corp["entries"][uid])
cans = unique_canonical(oh, mp)
h_o, m_o = hit_rate(oh, cans, mp)
h_f, m_f = hit_rate(inj_hdr, cans, mp)
comb10 = round((h_o - h_f) * 10.0, 6)
```

For this null panel, the scored surface is exactly the two raw row-zero header lists `[str(c) if c is not None else "" for c in table["table"][0]]`: `source_header` is `oh` and `edited_header` is the second observation. The frozen score is instantiated as:

```python
canonical = d3.unique_canonical(source_header, mp)
h_original, _ = d3.hit_rate(source_header, canonical, mp)
h_edited, _ = d3.hit_rate(edited_header, canonical, mp)
flat = round((h_original - h_edited) * 10.0, 6)
layered = round(d3.root_of(tb, h_original) - d3.root_of(tb, h_edited), 6)
```

The raw lists—not normalized keys or downstream artifacts—are the scored surface. Admission requires their canonical JSON hashes to differ.

## 5. Task-truth surface pinned exactly

For each raw header independently, the checker and generator re-run the frozen canonicalizer and downstream mapping and hash this post-canonicalization artifact:

```python
canonical_raw = d3.unique_canonical(header, mp)
fields = [mp.SchemaField(std, [std]) for std in canonical_raw]
schema_table = mp.SchemaTable(..., fields=fields)
mapping, unmapped = mp.map_headers(header, schema_table)
task_truth = {
  "canonical_normalized_keys": [mp.normalize_header(cell) for cell in canonical_raw],
  "canonical_count": len(canonical_raw),
  "mapped_standard_values_in_header_order": [mapping.get(cell) for cell in header],
  "unmapped_normalized_counts": sorted normalized-count pairs from unmapped,
}
```

Admission requires byte-identical canonical-JSON hashes of `task_truth(source_header)` and `task_truth(edited_header)`.

## 6. Null edit DSL, generator, checker, and complete panel

Candidate universe: every cell of every usable clean table, crossed with every rule below, in rule order. A table is usable when its UID is absent from the frozen injection map and `d3.unique_canonical(source_header, mp)` is non-empty.

1. `edge_space_prefix`: replace cell text `x` with `" " + x`.
2. `edge_space_suffix`: replace cell text `x` with `x + " "`.
3. `internal_single_space_removed`: if ASCII space exists, remove its first occurrence; otherwise no candidate.
4. `case_swap`: replace cell text `x` with `x.swapcase()`.

No sampling, label use, score use, harmful read, or favorable selection is allowed. The generator enumerates the full Cartesian candidate universe. The independent checker recomputes it without importing the generator, compares the exact ordered admission list and duplicate count, and requires both `raw_nonidentity=true` and `task_truth_identity=true` for every row. Panel = all and only admitted records. Empty admission, any checker mismatch, AST independence failure, or unverifiable identity stops without scoring as `NOT_EVALUABLE`.

## 7. Fold rule and partitions

Inherited fold text from `stage_e_matched_fpr_reanalysis.py`, verbatim:

```python
fold = {uid: i % N_FOLDS for i, uid in enumerate(sorted({row["uid"] for row in clean} | {row["uid"] for row in harmful}))}
```

D3 S-1 text, verbatim: `sorted(uid) index % 5; 表为最小单元, 同表 clean 版与全部 mutation 同 fold（本语料 clean 表与注入表 uid 不相交, 天然满足 S-1）`.

`N_FOLDS=5`. The union equals the sorted source-table UID universe. Frozen implementation split, declared before panel generation: calibration folds `{0,1,2}`; held-out folds `{3,4}`. Both partitions use the identical score function. Empty calibration or held-out partition after non-empty admission stops `NOT_EVALUABLE`.

## 8. Threshold, harmful ordering, metrics, and bootstrap

- Alpha `0.05`; candidate thresholds are only calibration-null score support.
- Threshold is the smallest `t` satisfying `fraction(calibration score > t) <= 0.05`; comparison is strict `>`; no interpolation and no harmful/held-out selection.
- Compute flat and layered thresholds independently under the same frozen rule.
- Write `threshold_freeze.json`, its sha256 sidecar, and chmod it read-only before held-out reporting and before any semantic harmful-side open.
- Held-out null FPR uses strict `>`; report raw numerator/denominator, rate, and 95% exact Clopper–Pearson CI.
- Only after threshold freeze: verify all harmful-source hashes, run deterministic `d3.g1_reproduce`, require `all_pass=true`, filter frozen classes `H|HI`, and require denominator `111`.
- Harmful TPR uses strict `>` at each frozen threshold; report numerator/denominator.
- Paired cluster bootstrap: resample sorted table UIDs with replacement, retain every harmful row in each sampled cluster, `N_BOOT=2000`, seed `20260830`, percentile CI at 2.5/97.5 using the frozen linear interpolation; report flat, layered, and paired difference CIs.
- Threshold selection never reads harmful rows. Harmful rows are descriptive after the threshold file is immutable.

## 9. Bridge, outcome, cost, and receipt rules

- Original result remains separate: 2,382 empirical clean rows, support `{0}`, `NOT_IDENTIFIABLE`; it is never replaced.
- Bridge recomputes the original empirical clean-row flat/layered distribution and strict-`>` FPR at the frozen synthetic thresholds, with exact CIs, explicitly labeled `non-comparable empirical-vs-synthetic read`.
- `POSITIVE` only if calibration support is greater than a single point, a threshold exists, and held-out FPR is `<=0.05` for both channels. Identifiability is an attribute, not a synonym for the label.
- `NULL` is the substantive label if support or held-out FPR contract fails.
- `NOT_EVALUABLE` is strictly limited to empty admission, unverifiable identity, or unpinnable/empty qualification surfaces; it is never `NULL`.
- `INVALID` covers forbidden selection, post-freeze edit, source mismatch during execution, or empirical-clean relabeling.
- `NEGATIVE` has no frozen decision criterion in prereg v2 and is therefore not invented or used.
- Cost ledger must show `model_calls=0`, `judge_calls=0`, training/service/database/network counts `0`.
- `receipt.json` must contain prereg and implementation-contract hashes, UTC start/end, input/output hashes, raw numerators/denominators and CIs, exactly one label, cost, unverified items, and deviations. Valid JSON only.

## 10. Frozen-artifact handling

After this contract and its sha256 sidecar are written, the contract, sidecar, generator, checker, runner, and all pre-existing frozen carriers are read-only for this run. Only files under `runs/PR-EXP-01/` created as experiment outputs may be written. Any attempted edit to a frozen source, implementation, prereg, carrier, config, test, or frozen hash is `INVALID` and stops.

--- END PACKET ---
