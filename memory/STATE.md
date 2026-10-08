# Current State

> Updated: 2026-10-08 | Scope: formal negative path B, Stage E advisor review, and governance neat closeout | Runtime: GB10 authoritative; local synthetic tests are DEV_ONLY / NON_AUTHORITATIVE

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions: [`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md). The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

当前 goal 的合法路径 B 已完成：正式记录 `DATA_NO_GO / RQ2 NOT_IDENTIFIED`，解释 Valentine 551 tasks 仅形成 8 个保守 origin components、无 native trajectory/checkpoint bridge，完整 Evaluate-Distill-Evolve 转为 future work；成熟 Stage E 小论文内部投稿版与大论文开题、第 1–2 章、第 3–8 章框架、Track B pilot、负结果边界和未来数据需求均已落盘。Stage E 现为 `ready for advisor review`；仅剩两个导师决策项：multi-leaf vs second dataflow、harmfulness 定义选择。此结论不等于确认性 RQ2/Stage D/Stage R/RQ4、正式外投或训练完成。

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
- Metadata-only RQ2 source screening covers all 10 registry sources: `0/10` directly provide the same-UID checkpoint + map/hold/skip action/target + independent correctness bridge. This is registry-scoped, not a global nonexistence claim; no new source was selected or downloaded.
- The user selected Route 2 (Valentine full benchmark + frozen process adapter). Its read-only structural audit found 551 complete pairs but only 8 conservative shared-origin components (<40), so the preregistered hard stop transitioned the work to the formal negative-result branch. No archive download/annex/full-benchmark adapter is authorized; the small paper remains Stage E fallback and full E-D-R is future work.
- Route V full benchmark DOCX narrative was refreshed and passed GB10 Office text/ZIP/PDF/page-4 visual checks; teacher-review Stage E DOCX remains unchanged.
- Current goal completion audit is `COMPLETE_FOR_FORMAL_NEGATIVE_PATH_B`; the earlier `NOT_COMPLETE_FOR_FULL_GOAL` audit remains historical evidence for the stricter confirmatory-only interpretation.
- Track B adapter pilot is sealed on GB10 at `/home/testuser/wzh/track_b_adapter_20261005_seal/`; 8/8 payload hashes pass and manifest hash is `dc388959150c98ffa7639108e1e80e306c346317b1cdced632ab66593960a04b`. It is exploratory within-origin evidence with `correctness_status=NOT_RUN`.
- Phase 2 duplicate JSON-key prerequisite is `PASS_SOFTWARE_CONTRACT`: commit `60eaa27` uses `object_pairs_hook` + `parse_constant`, and GB10 `tests/test_phase2_rule_gate_replay.py` reports `22 passed`. Phase 2 remains `NOT_RUN`; this is not replay or Stage R evidence.
- Paper/thesis evidence-state consistency was refreshed across 12 internal files: Q3 is now described as sealed exploratory evidence with corrected `51/58/37` and visibility exceptions; B0-B4 is exploratory v2; Stage E established numbers and claim boundaries were not changed.
- No model weights were loaded and no training model was instantiated.

## Conditional execution authorization

The user conditionally authorized automatic S0/A0/A1/A2 only after both artifacts and SOURCE/LABEL/SPLIT/POWER/BASELINE/MODEL/SAFETY pass, Stage D has stable residual, A2 meets the frozen risk/coverage/target-exact criteria versus B4, controls are frozen, and execution is GB10 isolated with one heavy task. The model artifact condition is now satisfied; the scientific/residual/window conditions are not.

A3, Phase 2, new data/licence, formal submission, arXiv, code release, and external release still require separate authorization.

## Git state

- Scientific/test source split: full pytest ran authoritatively at `f0764e714d21408a1a848ee0f327a22294eda73a` or an equivalent GB10 head; Stage E package claims, submission audit, focused tests and Office/PDF checks are bound through `62274ef1fa624912390d4f0a05828c038a938ccb`; the repository governance/self-check head is `8c0b248ddfe19c937e815003ac31db48a54bc091`.
- `652c9c6cadc2b62b731ee13ed34663562f88dc65` is an audit metadata-baseline correction only. `1d5a7ff8218fa9ec073cebcd81a0a39523d7c14b` is the documentation archive/link-repair/workspace-neat commit. Neither changes scientific results or running code.
- Current repository head is the current Git commit; verify it with `git rev-parse HEAD` on local/origin/GB10. The last pre-closeout synchronized head was `8c0b248ddfe19c937e815003ac31db48a54bc091`. Stage E package head: `62274ef1fa624912390d4f0a05828c038a938ccb`. Latest Stage E package validation: claims `74/74`, submission `10/10`, focused tests `22 passed`, Office/PDF visual PASS on 9 pages.
- Commits `c39b301..8c0b248` are governance docs/tools only; they do not alter frozen experiment numbers, preregistered criteria, claim boundaries, paper results, or production code.
- Pre-neat baseline remains `1d5a7ff8218fa9ec073cebcd81a0a39523d7c14b`; GB10 production dirty files remained the fixed five and were not overwritten.
- Legacy session residue is archived: `docs/archive/session_assets/2026-08-29/` holds `IMPLEMENTATION_PLAN.md` and `PROMPT.md`; `scripts/archive/_d3b_dispatch.sh` holds the old dispatch script. The local WSL `docs_lint_report.json` copy is preserved under ignored `logs/graph/archive/`; the tracked report path is restored to repository baseline and is not authoritative over GB10.
- GB10 protected production dirty files remain the fixed five; `logs/graph/dispatch_log.md` is an additional runtime ledger and is also left untouched: `config/schema_suggestions.json`, `logs/graph/docs_lint_report.json`, `logs/graph/governance_drift_latest.md`, `logs/graph/loop_b_last_status`, `logs/graph/verify-report.json`.
- Do not touch `docs/33*`, `docs/34*`, frozen tests/schema, `scripts/graph/frozen_hashes.txt`, or TAT-DQA boundaries.

## Governance self-check

- Four governance batches are committed and synchronized: `c39b301`, `3e57191`, `69f93c3`, `8c0b248`.
- GB10 focused governance tests: `14 passed`; tracked secret scan: clean; docs_lint on 2026-10-08: `0 fail / 6 warn`. The earlier `0 fail / 4 warn` package closeout remains historical evidence, not the current time-based warning count.
- `skill-doctor`: `0 errors / 139 warnings / 0 fixes`; warnings are existing catalog hygiene debt and were not auto-fixed.
- Guard source and tests are committed; global hook settings were not modified.
- OpenAlex metadata API configuration is external-only and validated with HTTP 200 on local and GB10; the key is not stored in the repository. Literature/dataset screening remains incomplete and is handed off as open work.
- `inquiry-methods` is added as one progressive-dispatch router for learning, research, problem-solving, fact-checking, and decisions; Loop A/C and task-card routing reference it without granting execution authority. `registry_check.py` and `loopkit_ledger.py` remain intentionally not imported.
## Research boundaries

- Q3 corrected ledger remains `map_to=51 / skip=58 / hold=37`, `SEALED_WITH_VISIBILITY_EXCEPTIONS`; exploratory only.
- B0-B4 v2 remains exploratory. Stage D necessity remains `PILOT_ONLY`; dedicated-student necessity `NOT_ESTABLISHED`.
- Route V remains 10 eligible clusters against the 40-cluster target; gap 30. G-A/G-B remain unapproved; G-C does not authorize source/revision/file-scope expansion.
- V2-3 remains closed. B5 remains dormant / `NOT_RUN`.
- Stage R has mechanism evidence only; RQ4 has no end-to-end evidence.


## Open decisions

1. Multi-leaf versus second dataflow as the next evidence priority.
2. Harmfulness definition: canonical, reader-referent, or parallel constructs. No choice is recorded yet.

## Next gates

1. The exact-source annex gap is formally retained as part of `DATA_NO_GO`; do not claim the 40-cluster target is available at the current revision.
2. Any future confirmatory attempt requires a new exact source/task-definition annex and all SOURCE/LABEL/SPLIT/POWER/BASELINE/MODEL/SAFETY gates; it is outside the completed path-B goal.
3. Recompute Stage D necessity and SOURCE/LABEL/SPLIT/POWER/BASELINE/SAFETY from real artifacts.
4. Run A2 only after the scientific gates and signed power receipt pass; use the approved necessity criteria without post-result changes.
5. Keep Phase 2 blocked until RQ2/RQ3 prerequisites and the approved execution window pass; duplicate JSON-key software readiness is already closed.
6. Continue paper/thesis work only by backfilling independently accepted evidence; keep Q3/B0-B4 outside Stage E main results until their evidence level changes.
7. Only after every conditional gate passes may S0/A0/A1/A2 proceed automatically under the frozen controls.
8. A3, Phase 2, new data/licence, formal submission, arXiv, code release, and external release remain separately authorized.
