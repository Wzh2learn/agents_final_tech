ROLE: Loop A / GB10 execution
RESEARCH QUESTION:
Can Paper E evidence be strengthened without re-analyzing the same M/R/N direct codebook or starting formal FinQA/PRM training?

INPUTS:
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/results/multileaf_formal_results.json
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/multileaf_mechanism_generalization_audit.json
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json
- /home/testuser/wzh/projects/agents_final_tech/research/finqa_independent_observation_scorer_v2.py
- /home/testuser/wzh/projects/agents_final_tech/tests/test_finqa_independent_observation_scorer_v2.py
- /home/testuser/wzh/projects/agents_final_tech/research/finqa_evidence_argument_resolver_v2.py
- /home/testuser/wzh/projects/agents_final_tech/tests/test_finqa_evidence_argument_resolver_v2.py
- Loop D input drafts stored under /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/loop_d_inputs/

ALLOWED ACTIONS:
1. Apply the supplied Loop D claim-boundary and Version-B wording to existing proposal/result-packet documents.
2. Generate Figure 3 from frozen ablation values and add it to the figure manifest.
3. Write a current six-gate FinQA v2 status document using the existing audits and candidate sample manifest.
4. Update the PRM formal-pilot proposal with the supplied power/resource/sample contract.
5. Run targeted unit tests for the independent observation scorer and evidence-argument resolver.
6. Run paper/submission validators, JSON parsing, docs lint and focused tests needed for evidence integrity.
7. Produce a machine-readable execution receipt with input/output hashes.

FORBIDDEN ACTIONS:
- Run a formal FinQA v2 experiment.
- Run PRM C0/C1/C2/C4 training.
- Modify frozen multi-leaf result JSON, old D3 artifacts or Stage E source evidence.
- Tune thresholds, predictors, mutation rules or sample selection after looking at results.
- Claim hierarchy localization, natural-failure localization or semantic process correctness.
- Change the independent scorer's measurement object from paired checkpoint observation reproduction.

OUTPUTS:
- Updated result packet and Version-B proposal with the exact claim boundary.
- Updated independent-scorer feasibility status: `PROTOTYPE_PASS_NOT_FROZEN`.
- Updated PRM proposal status: `PRM_FORMAL_PILOT_NOT_READY`.
- `docs/research/finqa_v2_gate_status_v1.md`.
- `docs/research/figures_multileaf/fig_multileaf_localization_ablation.png` and `.svg`.
- `docs/research/stage_e_version_b_figure_spec_v1.md`.
- `research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_receipt.json`.

STOP CONDITIONS:
- If any required input is absent, stop and report `INPUT_MISSING`.
- If the independent scorer cannot remain independent of the shared FinQA fault adapter, report `SCORER_NOT_INDEPENDENT`.
- If Figure 3 cannot be generated from frozen values without inventing data, report `FIGURE_DATA_MISSING`.
- If any validator fails, preserve the failure and do not relax assertions.

EVIDENCE CLASS:
PRIMARY = claim-boundary and frozen multi-leaf interpretation.
SECONDARY = FinQA gate status and PRM contract.
EXPLORATORY = Figure 3 and mechanism-feasibility summaries.
ENGINEERING = scorer/resolver implementation and validation receipts.
NEGATIVE = mechanism generalization not identified and formal pilot not ready.
