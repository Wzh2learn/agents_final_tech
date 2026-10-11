# Loop A Assignment — PR-EXP-04 (cross-mechanism generalization N1 vs N2)
PREREG: research/positive_repair_20261011/preregs/PR-EXP-04_prereg_v2.md | sha256 c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038
ROLE: Loop A / GB10 execution. You execute ONE preregistered deterministic experiment under Track P. Nothing else.

CONTRACT (read first; binding):
- research/positive_repair_20261011/preregs/PR-EXP-04_prereg_v2.md  (THE scientific contract; its sha256 is recorded in prerequisites below)
- research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
- research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md
- memory/CORE.md and memory/STATE.md for context (do not edit).

Project dir: /home/testuser/wzh/projects/agents_final_tech
Work dir (must NOT pre-exist): research/positive_repair_20261011/runs/PR-EXP-04/

PRE-RUN (mandatory, in order):
1) Verify every hash in shared_surface_freeze_v1.json against the working tree; mismatch -> STOP, report HASH_MISMATCH.
2) Freeze your implementation BEFORE generating/observing anything: write runs/PR-EXP-04/implementation_contract.md containing all items the prereg's implementation-contract section requires, plus your source-file hashes. Then hash it.
3) Frozen artifacts are READ-ONLY: multileaf carriers, D3 inputs, drift outputs, config/eval_checkpoint_trees.json, tests, frozen hashes.

FORBIDDEN: model/judge calls; training; production services; databases; network; commit/push; editing the prereg; threshold/threshold-rule hunting; reading mutation labels beyond the frozen generation rules; changing any shared surface.
Note: a negative/NULL/NOT_EVALUABLE result is a valid output; never fabricate or rescue.

OUTPUTS (in runs/PR-EXP-04/): result JSON(s) + receipt.json exactly as required by the prereg, including: experiment_id, prereg_sha256, implementation_contract_sha256, start/end UTC, input hashes, output hashes, raw numerators/denominators and CIs for every metric, exactly ONE canonical outcome label from the prereg taxonomy, cost (runtime; model_calls=0), unverified items, deviations (expect none). Receipt must be valid JSON (no markdown fences).
STOP CONDITIONS: input missing -> INPUT_MISSING; prereg/shared mismatch -> PREREG_MISMATCH / HASH_MISMATCH; any forbidden action required -> stop and report; prereg-defined qualification gate failure -> NOT_EVALUABLE per prereg.

END: final message = status + receipt path + one-line result summary.EXPERIMENT WORK (per prereg v2 sections 2-7):
1) Implement N2 (deterministic operator/coefficient/sign perturbation; executor-owned downstream consequence via the frozen reconciliation path); generation rule frozen; N2 UIDs disjoint from N1 groups; double-run byte-identical.
2) Harness-equivalence control (mandatory): regenerate N1 rows through the N2 harness code path; require byte-identical response vectors vs frozen N1 rows; failure = INVALID.
3) Visibility/evaluability gate: >=2/3 of N2 injections produce >=1 measurable response on the frozen 12-leaf surface AND >=6 distinct held-out groups respond; else MECHANISM_NOT_EVALUABLE (NOT_EVALUABLE, never merged into NULL).
4) Cross-mechanism evaluation N1->N2 and N2->N1 under the frozen nearest-centroid + LOCO; direct-codebook control; responsive-leaf overlap report; frozen numeric baselines per section 5.
5) Outcome taxonomy per section 7 (m=0.05 margin; one canonical label; supporting-only — this experiment never counts toward the repair count).

BINDING ADDENDUM: read research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md and apply it inside your implementation contract before any run.

HASH-RULES UPDATE (2026-10-11T08:30Z): for canonicalizer_file use identity_rule=git_blob - verify git rev-parse HEAD:scripts/m1_statement_parser.py AND git hash-object scripts/m1_statement_parser.py both equal def5161dd17fc14345d340879174ed01e0277626; raw sha256 may differ by EOL (informational only). For identity_rule=raw_sha256 entries verify raw bytes. Record the verified identities in your implementation contract.
