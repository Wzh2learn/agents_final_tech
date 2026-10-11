You are the independent Loop C quality auditor for one bounded Stage E multi-leaf result. Do not modify any file, run training, call models, use the network, or change the scientific contract.

Audit scope:
- docs/research/multileaf_preresult_freeze_receipt_v1.md
- research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json
- research/stage_e_multileaf_20261010/run_multileaf_formal.py
- research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl
- research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl
- research/stage_e_multileaf_20261010/results/multileaf_permutation_null.json
- research/stage_e_multileaf_20261010/results/multileaf_bootstrap_intervals.json
- research/stage_e_multileaf_20261010/results/multileaf_formal_results.json
- research/stage_e_multileaf_20261010/results/independent_validation_receipt.json
- research/stage_e_multileaf_20261010/results/independent_contract_audit.json
- tests/test_multileaf_formal_contract.py

Acceptance criteria:
1. Verify that the pre-result receipt precedes result creation and its hashes match.
2. Independently recompute the 216-row confusion matrix, macro-F1, top-1 accuracy, response signatures, and result classification from raw prediction/paired artifacts. Do not trust the result summary.
3. Verify cluster-level leakage, repeated-measure accounting, stage contracts, tie handling, and the frozen primary metric/baseline definitions.
4. Recompute or spot-recompute permutation p-values and bootstrap intervals from stored null/replicate arrays.
5. Check whether the claim is correctly scoped to controlled M/R/N injections and does not claim hierarchy localization or natural-task generalization.
6. State the strongest failure scenario or reviewer attack that remains valid despite the perfect metrics.
7. Inspect code for row-order bugs, label leakage, denominator errors, metric inflation, or result-dependent decisions. Cite exact file and line or JSON field.
8. Only after completing 1-7, read docs/research/stage_e_multileaf_result_packet_v1.md and state whether it overclaims.

Output format:
- Independence declaration.
- Evidence table with command/file/field and observed value.
- Findings ordered by severity.
- Strongest remaining failure scenario.
- `VERDICT: ACCEPTED`, `VERDICT: CONDITIONAL`, or `VERDICT: REJECTED`.
- If conditional/rejected, list exact blocking evidence.

This is a read-only audit. Zero findings is allowed if supported.
