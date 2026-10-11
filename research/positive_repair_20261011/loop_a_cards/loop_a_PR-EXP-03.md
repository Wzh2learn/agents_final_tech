# Loop A Assignment — PR-EXP-03 (structural-oracle coverage repair)
PREREG: research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md | sha256 f3398a329a12ef23e528eb41d0bd90c8b4c5cee807c3d2c76c5afd0ac753f250
ROLE: Loop A / GB10 execution. You execute ONE preregistered deterministic experiment under Track P. Nothing else.

CONTRACT (read first; binding):
- research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v2.md  (THE scientific contract; its sha256 is recorded in prerequisites below)
- research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
- research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md
- memory/CORE.md and memory/STATE.md for context (do not edit).

Project dir: /home/testuser/wzh/projects/agents_final_tech
Work dir (must NOT pre-exist): research/positive_repair_20261011/runs/PR-EXP-03/

PRE-RUN (mandatory, in order):
1) Verify every hash in shared_surface_freeze_v1.json against the working tree; mismatch -> STOP, report HASH_MISMATCH.
2) Freeze your implementation BEFORE generating/observing anything: write runs/PR-EXP-03/implementation_contract.md containing all items the prereg's implementation-contract section requires, plus your source-file hashes. Then hash it.
3) Frozen artifacts are READ-ONLY: multileaf carriers, D3 inputs, drift outputs, config/eval_checkpoint_trees.json, tests, frozen hashes.

FORBIDDEN: model/judge calls; training; production services; databases; network; commit/push; editing the prereg; threshold/threshold-rule hunting; reading mutation labels beyond the frozen generation rules; changing any shared surface.
Note: a negative/NULL/NOT_EVALUABLE result is a valid output; never fabricate or rescue.

OUTPUTS (in runs/PR-EXP-03/): result JSON(s) + receipt.json exactly as required by the prereg, including: experiment_id, prereg_sha256, implementation_contract_sha256, start/end UTC, input hashes, output hashes, raw numerators/denominators and CIs for every metric, exactly ONE canonical outcome label from the prereg taxonomy, cost (runtime; model_calls=0), unverified items, deviations (expect none). Receipt must be valid JSON (no markdown fences).
STOP CONDITIONS: input missing -> INPUT_MISSING; prereg/shared mismatch -> PREREG_MISMATCH / HASH_MISMATCH; any forbidden action required -> stop and report; prereg-defined qualification gate failure -> NOT_EVALUABLE per prereg.

END: final message = status + receipt path + one-line result summary.EXPERIMENT WORK (per prereg v2 sections 3-8):
1) Implement oracle v2 (structural signature: column_count + ordered positional header-token sequence under the pinned canonicalizer + row_count; response = signature-differs) and the frozen rule pins (drift-corpus membership; M/N UID exclusion registry extracted from multileaf_preresult_sample_manifest.json; per-table pair-selection hash rule; verbatim baseline extract from run_multileaf_formal.py:256-258 + file hash).
2) Freeze oracle implementation hash FIRST; then generate P1 (adjacent-column transpositions over held-out UIDs); generator double-run byte-identical required.
3) Evaluate arms A0 no-op (expect 0), A1 value-only specificity (expect 0), A2 P1 (expect 1), A3 M1 regression (expect 0); baselines: v1 aliased and standalone field-hit, same population; constant-1 documented control.
4) Metrics per section 5 (coverage delta + CI; diagnosability delta on mixed population; disagreement; unique catches; FP counts; attribution audit per contract) and outcome taxonomy per section 7 (one canonical label; sanity gate failure = INVALID).
5) Receipt per section 8 + common outputs.

BINDING ADDENDUM: read research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md and apply it inside your implementation contract before any run.

HASH-RULES UPDATE (2026-10-11T08:30Z): for canonicalizer_file use identity_rule=git_blob - verify git rev-parse HEAD:scripts/m1_statement_parser.py AND git hash-object scripts/m1_statement_parser.py both equal def5161dd17fc14345d340879174ed01e0277626; raw sha256 may differ by EOL (informational only). For identity_rule=raw_sha256 entries verify raw bytes. Record the verified identities in your implementation contract.
