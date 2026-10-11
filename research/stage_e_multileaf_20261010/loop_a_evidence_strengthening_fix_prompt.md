ROLE: Loop A / GB10 targeted repair after Loop C CONDITIONAL audit
RESEARCH QUESTION:
Can the blocking presentation, gate-snapshot, and numeric-token-identity findings from Loop C be closed without changing frozen scientific evidence or running any formal experiment?

INPUTS:
- /home/testuser/wzh/projects/agents_final_tech/docs/experiments/2026-10-10_loop_c_evidence_strengthening_audit.md if present; otherwise the verbatim audit in /home/testuser/wzh/loop_runs/paper-evidence-strengthening-c-20261010/c.log
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json
- /home/testuser/wzh/projects/agents_final_tech/docs/research/figures_multileaf/fig_multileaf_localization_ablation.png and .svg
- /home/testuser/wzh/projects/agents_final_tech/docs/research/stage_e_version_b_figure_spec_v1.md
- /home/testuser/wzh/projects/agents_final_tech/docs/research/stage_e_multileaf_result_packet_v1.md
- /home/testuser/wzh/projects/agents_final_tech/docs/research/stage_e_version_b_revision_proposal_v1.md
- /home/testuser/wzh/projects/agents_final_tech/docs/research/finqa_v2_gate_status_v1.md
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json
- /home/testuser/wzh/projects/agents_final_tech/research/finqa_evidence_argument_resolver_v2.py
- /home/testuser/wzh/projects/agents_final_tech/research/finqa_independent_observation_scorer_v2.py
- corresponding existing tests under /home/testuser/wzh/projects/agents_final_tech/tests

ALLOWED ACTIONS:
1. Correct Figure 3 and all proposal/result-packet wording so metric-specific baselines are explicit:
   - non-direct top-1 = 0.3333 equals chance top-1 = 0.3333;
   - non-direct macro-F1 = 0.3333 equals uniform-class macro-F1 = 0.3333 but is above the plotted majority macro-F1 baseline = 0.1667;
   - avoid the unqualified phrase "collapses to approximately chance" wherever it could refer to both metrics.
2. Regenerate Figure 3 only from the frozen ablation values; preserve the full/direct/non-direct values and make the two baselines metric-specific.
3. Keep the construct-sensitive scope clause wherever perfect full/direct-codebook bars or macro-F1 = 1.0 are shown.
4. Create a new non-destructive gate-reconciliation namespace that declares which older snapshots are stale, preserves their hashes, and gives one canonical six-gate table with `SCORER_GO` present. Do not edit frozen audit/manifest source JSON.
5. Create a new numeric-token canonicalization namespace shared by selection and causal-test logic, or an equivalent explicit reconciliation adapter. It must remove the `float` formatting versus `Decimal.normalize()` identity mismatch without rewriting old audit artifacts.
6. Add focused tests proving canonical token identity agreement and fail-closed ambiguity behavior.
7. Run the existing scorer/resolver tests plus new focused tests in the GB10 permissive environment and record exact counts.
8. Write a machine-readable repair receipt with input/output SHA-256 hashes, commands, test results, changed-file list and evidence classes.

FORBIDDEN ACTIONS:
- Run or rerun the M/R/N experiment.
- Run a formal FinQA v2 experiment.
- Run PRM C0/C1/C2/C4 training or any model training.
- Modify frozen multi-leaf results, frozen source evidence, old D3 artifacts, sample IDs, mutation rules, predictors or thresholds.
- Edit paper body/DOCX.
- Change the independent scorer measurement object from paired checkpoint observation reproduction.
- Claim semantic process correctness, hierarchy localization, natural-failure localization or mechanism generalization.
- Resolve the 627-versus-594 PRM accounting question by inventing an explanation; only label it `NOT YET RESOLVED`.

OUTPUTS:
- Updated Figure 3 PNG/SVG and figure spec with metric-specific baseline wording.
- Updated result packet and Version-B proposal only for the affected wording and scope clauses.
- `docs/research/finqa_v2_gate_reconciliation_v2.md` plus machine-readable companion.
- New numeric-token canonicalization code/test namespace and a concise reconciliation note.
- Exact test log and `research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_receipt.json`.
- A short status matrix for Loop C findings F2-F8, each marked CLOSED / PARTIAL / OPEN / NOT_YET_RESOLVED.

STOP CONDITIONS:
- If frozen ablation values cannot support corrected Figure 3 without new analysis, stop with `FIGURE_REPAIR_INPUT_MISSING`.
- If canonical token identity cannot be reconciled without changing frozen artifacts, stop with `TOKEN_IDENTITY_NEW_NAMESPACE_REQUIRED`.
- If any existing or new focused test fails, preserve the failure and report `REPAIR_VALIDATION_FAILED`.
- If a fix would require changing the paper body or rerunning experiments, stop and report `OUT_OF_SCOPE`.

EVIDENCE CLASS:
PRIMARY = corrected claim/metric boundary and preserved construct-sensitive scope.
SECONDARY = canonical gate reconciliation.
ENGINEERING = token canonicalization and test verification.
EXPLORATORY = figure presentation repair.
NEGATIVE = any item left OPEN or NOT_YET_RESOLVED.
