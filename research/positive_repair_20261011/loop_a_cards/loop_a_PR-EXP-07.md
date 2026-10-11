# Loop A Assignment — PR-EXP-07 (label-blind re-extraction; anti-tautology robustness)
PREREG: research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md | sha256 4724e53ebaf86633384f1955e5182bd7c5b886994603b59a6146c45ce6426d5f
ROLE: Loop A / GB10 execution. You execute ONE preregistered deterministic experiment under Track P. Nothing else.

CONTRACT (read first; binding):
- research/positive_repair_20261011/preregs/PR-EXP-07_prereg_v2.md  (THE scientific contract)
- research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json
- research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md
- memory/CORE.md and memory/STATE.md for context (do not edit).

Project dir: /home/testuser/wzh/projects/agents_final_tech
Work dir (must NOT pre-exist): research/positive_repair_20261011/runs/PR-EXP-07/

PRE-RUN (mandatory, in order):
1) Verify every hash in shared_surface_freeze_v1.json; mismatch -> STOP, report HASH_MISMATCH.
2) Freeze your implementation BEFORE generating/observing anything: write runs/PR-EXP-07/implementation_contract.md with all items the prereg requires plus source hashes; then hash it.
3) Frozen artifacts READ-ONLY (multileaf carriers, D3 inputs, drift outputs, config, tests, frozen hashes).

FORBIDDEN: model/judge calls; training; services; databases; network; commit/push; editing the prereg; hunting; label misuse; changing shared surfaces. Negative/NULL/NOT_EVALUABLE results are valid; never fabricate or rescue.

OUTPUTS (runs/PR-EXP-07/): result JSON(s) + receipt.json exactly as the prereg requires (prereg_sha256, implementation_contract_sha256, start/end UTC, input/output hashes, raw numerators/denominators + CIs, exactly ONE canonical outcome label, cost with model_calls=0, unverified items, deviations). Valid JSON, no fences.
STOP CONDITIONS: INPUT_MISSING; PREREG_MISMATCH / HASH_MISMATCH; forbidden action required -> stop; prereg qualification gate failure -> NOT_EVALUABLE per prereg.

END: final message = status + receipt path + one-line summary.EXPERIMENT WORK (per prereg v2):
1) Implement the label-blind extractor: inputs ONLY the unordered pair {A,B}; pairing rule built from frozen cluster structure (record source + proof it reads no response values); pair order randomized by frozen seed; features order-invariant; swap-invariance test across ALL rows (feature(P) == feature(swap(P))).
2) Freeze extractor + feature sets (full / direct-codebook subset / non-direct subset) BY HASH BEFORE any feature-value observation; then compute features; then evaluate.
3) Evaluation: frozen nearest-centroid + LOCO; direct-codebook baseline; chance (1/3); shuffled-label negative control (frozen seed); numeric criteria per section 3 (ROBUST margins 0.05; NULL_DIRECT_CONCENTRATED; NULL; NULL_AT_CHANCE; NOT_EVALUABLE with row-level attrition; INVALID on any leakage/swap proof failure).
4) Reports: quantified blind-vs-original delta on identical rows (Δ = full_labelblind − original_frozen, with CI; declared non-comparable claim-wise); attrition table.
5) Supporting-only role; never counts toward the repair count. Degradation -> NULL/negative AND recorded claim-lowering note (never silent).

BINDING ADDENDUM: read research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md and apply it inside your implementation contract before any run.

HASH-RULES UPDATE (2026-10-11T08:30Z): for canonicalizer_file use identity_rule=git_blob - verify git rev-parse HEAD:scripts/m1_statement_parser.py AND git hash-object scripts/m1_statement_parser.py both equal def5161dd17fc14345d340879174ed01e0277626; raw sha256 may differ by EOL (informational only). For identity_rule=raw_sha256 entries verify raw bytes. Record the verified identities in your implementation contract.
