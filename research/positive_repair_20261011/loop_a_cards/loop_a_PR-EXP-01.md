# Loop A Assignment — PR-EXP-01 (SYNTHETIC_NULL_SUPPORT_REPAIR)
PREREG: research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md | sha256 41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3
ROLE: Loop A / GB10 execution. You execute ONE preregistered deterministic experiment under Track P. Nothing else.

CONTRACT (read first; binding):
- research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md  (THE scientific contract)
- research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
- research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md
- memory/CORE.md and memory/STATE.md for context (do not edit).

Project dir: /home/testuser/wzh/projects/agents_final_tech
Work dir (must NOT pre-exist): research/positive_repair_20261011/runs/PR-EXP-01/

PRE-RUN (mandatory, in order):
1) Verify every hash in shared_surface_freeze_v1.json; mismatch -> STOP, report HASH_MISMATCH.
2) Freeze your implementation BEFORE generating/observing anything: write runs/PR-EXP-01/implementation_contract.md with all items the prereg requires plus source hashes; then hash it.
3) Frozen artifacts READ-ONLY (multileaf carriers, D3 inputs, drift outputs, config, tests, frozen hashes).

FORBIDDEN: model/judge calls; training; services; databases; network; commit/push; editing the prereg; hunting; label misuse; changing shared surfaces. Negative/NULL/NOT_EVALUABLE results are valid; never fabricate or rescue.

OUTPUTS (runs/PR-EXP-01/): result JSON(s) + receipt.json exactly as the prereg requires (prereg_sha256, implementation_contract_sha256, start/end UTC, input/output hashes, raw numerators/denominators + CIs, exactly ONE canonical outcome label, cost with model_calls=0, unverified items, deviations). Valid JSON, no fences.
STOP CONDITIONS: INPUT_MISSING; PREREG_MISMATCH / HASH_MISMATCH; forbidden action required -> stop; prereg qualification gate failure -> NOT_EVALUABLE per prereg.

END: final message = status + receipt path + one-line summary.EXPERIMENT WORK (per prereg v2):
PHASE 0 (fail-closed qualification; runs BEFORE any scoring):
- Pin the scored surface verbatim (read the frozen contrastive scorer implementation; record path+hash+exact input expression) and the task-truth surface (downstream canonical artifacts).
- Implement the null edit DSL + generator AND an independent checker (no generator imports; AST check; separate file hash). Admitted edits must be NON-identity on the scored surface AND hash-identical on the task-truth surface. Panel = complete admitted set (no sampling).
- Empty admission or unverifiable identity -> STOP -> outcome NOT_EVALUABLE (no scoring, no claim).
PHASE 1 (only if Phase 0 admits a non-empty panel):
- Calibration nulls on calibration folds; threshold = smallest t with fraction(calibration scores > t) <= 0.05; freeze threshold hash BEFORE any harmful-side read.
- Held-out nulls: FPR <= 0.05 check. Then harmful side: TPR at the frozen operating point + paired cluster bootstrap CI.
- Bridge report: empirical clean-row score distribution + FPR at the frozen threshold (explicitly non-comparable synthetic-vs-empirical).
- Outcome labels per section 6 (single canonical string; NOT_EVALUABLE strictly separate from NULL).

BINDING ADDENDUM: read research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md and apply it inside your implementation contract before any run.

HASH-RULES UPDATE (2026-10-11T08:30Z): for canonicalizer_file use identity_rule=git_blob - verify git rev-parse HEAD:scripts/m1_statement_parser.py AND git hash-object scripts/m1_statement_parser.py both equal def5161dd17fc14345d340879174ed01e0277626; raw sha256 may differ by EOL (informational only). For identity_rule=raw_sha256 entries verify raw bytes. Record the verified identities in your implementation contract.
