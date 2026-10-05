# Current State

> Updated: 2026-10-05T13:00:00+08:00 | Scope: Qwen3-8B model sync and both-model artifact readiness | Runtime: GB10 authoritative; local synthetic tests are DEV_ONLY / NON_AUTHORITATIVE

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions: [`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md). The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

围绕 Evaluate-Distill-Evolve 三阶段闭环推进科研主线。Goal 保持 ACTIVE。成熟 Stage E 保底稿有效；Stage D 仍为 `PILOT_ONLY`，`DATA_NO_GO` / `RQ2 NOT_IDENTIFIED` 保持；Q3 与 B0-B4 仍是 exploratory evidence。

## Model artifact status

- Execution authority is GB10-only. Local fixture runs are `DEV_ONLY / NON_AUTHORITATIVE`.
- Qwen3-4B and Qwen3-8B both passed GB10 real artifact validation and remain `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`.
- Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218` was downloaded through `hf-mirror.com` with `token_sent=false`, Xet disabled, and HF transfer disabled.
- Qwen3-8B evidence: 15/15 immutable identities (6 LFS SHA-256 + 9 Git blob SHA-1), 5 shard headers, 399 tensors, tokenizer/licence, clean manifest `e47b9aca...`, full manifest `6ba50550...`.
- Sync receipt: `docs/datasets/2026-10-05_qwen3_8b_sync_receipt_v1.json`, SHA-256 `684dfb9b...`.
- Artifact receipt: `docs/datasets/2026-10-05_qwen3_8b_artifact_validation_receipt_v1.json`, SHA-256 `8c35a447...`.
- GB10 readiness: `PASS_DRY_RUN_ONLY`, `smoke_model_revision_ready=true`, `student_model_revision_ready=true`, `model_revision_ready=true`, `missing_dependencies=[]`.
- `model_revision_ready=true` means immutable model/tokenizer artifacts are validated only. It is not MODEL_GO, TRAINING_GO, or a scientific result.
- Approved initial Stage D necessity criteria are now explicit and hash-bound: A2 coverage gain over B4 `>=0.05`, target exact non-inferiority margin `<=0.02`, maximum single-pair residual/gain share `<=0.50`, harmful-map risk upper `<=0.10` in primary/pair-invalid/salted, and positive A2-B4 coverage-delta lower bounds in primary/pair-invalid. A2 is not run; gain/target/gain-share/deltas are `NOT_ESTIMABLE`, while the salted risk upper `0.1250` fails.
- Route V target `>=40` clusters is approved at revision `5d5163f...`; the official tree supplies only 10 eligible clusters, eligible new clusters=0, gap=30. No exact new-directory annex exists and no download is possible without a new source/revision/file-scope annex.
- Phase 2 duplicate JSON-key prerequisite is `PASS_SOFTWARE_CONTRACT`: commit `60eaa27` uses `object_pairs_hook` + `parse_constant`, and GB10 `tests/test_phase2_rule_gate_replay.py` reports `22 passed`. Phase 2 remains `NOT_RUN`; this is not replay or Stage R evidence.
- No model weights were loaded and no training model was instantiated.

## Conditional execution authorization

The user conditionally authorized automatic S0/A0/A1/A2 only after both artifacts and SOURCE/LABEL/SPLIT/POWER/BASELINE/MODEL/SAFETY pass, Stage D has stable residual, A2 meets the frozen risk/coverage/target-exact criteria versus B4, controls are frozen, and execution is GB10 isolated with one heavy task. The model artifact condition is now satisfied; the scientific/residual/window conditions are not.

A3, Phase 2, new data/licence, formal submission, arXiv, code release, and external release still require separate authorization.

## Git state

- Verified prior baseline = `58496430a6bd3c1a5de45949471ed804a2f565fe`; model-sync batch commit is `5a16845`. Git history is authoritative for subsequent fixes.
- Preserve protected/user assets: `logs/graph/docs_lint_report.json`, `IMPLEMENTATION_PLAN.md`, `PROMPT.md`, `_d3b_dispatch.sh`.
- GB10 production dirty files remain the fixed five: `config/schema_suggestions.json`, `logs/graph/docs_lint_report.json`, `logs/graph/governance_drift_latest.md`, `logs/graph/loop_b_last_status`, `logs/graph/verify-report.json`.
- Do not touch `docs/33*`, `docs/34*`, frozen tests/schema, `scripts/graph/frozen_hashes.txt`, or TAT-DQA boundaries.

## Research boundaries

- Q3 corrected ledger remains `map_to=51 / skip=58 / hold=37`, `SEALED_WITH_VISIBILITY_EXCEPTIONS`; exploratory only.
- B0-B4 v2 remains exploratory. Stage D necessity remains `PILOT_ONLY`; dedicated-student necessity `NOT_ESTABLISHED`.
- Route V remains 10 eligible clusters against the 40-cluster target; gap 30. G-A/G-B remain unapproved; G-C does not authorize source/revision/file-scope expansion.
- V2-3 remains closed. B5 remains dormant / `NOT_RUN`.
- Stage R has mechanism evidence only; RQ4 has no end-to-end evidence.

## Next gates

1. Close the exact-source annex gap or formally retain `DATA_NO_GO`; do not claim the 40-cluster target is available at the current revision.
2. Recompute Stage D necessity and SOURCE/LABEL/SPLIT/POWER/BASELINE/SAFETY from real artifacts.
3. Run A2 only after the scientific gates and signed power receipt pass; use the approved necessity criteria without post-result changes.
4. Keep Phase 2 blocked until RQ2/RQ3 prerequisites and the approved execution window pass; duplicate JSON-key software readiness is already closed.
5. Only after every conditional gate passes may S0/A0/A1/A2 proceed automatically under the frozen controls.
6. A3, Phase 2, new data/licence, formal submission, arXiv, code release, and external release remain separately authorized.
