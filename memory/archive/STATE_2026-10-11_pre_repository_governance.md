# Current State

> Updated: 2026-10-08 | Scope: formal negative path B, Stage E advisor review, and governance neat closeout | Runtime: GB10 authoritative; local synthetic tests are DEV_ONLY / NON_AUTHORITATIVE

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions: [`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md). The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

当前 goal 的合法路径 B 已完成：正式记录 `DATA_NO_GO / RQ2 NOT_IDENTIFIED`，解释 Valentine 551 tasks 仅形成 8 个保守 origin components、无 native trajectory/checkpoint bridge，完整 Evaluate-Distill-Evolve 转为 future work；成熟 Stage E 小论文内部投稿版与大论文开题、第 1–2 章、第 3–8 章框架、Track B pilot、负结果边界和未来数据需求均已落盘。Stage E 现为 `ready for advisor review`；仅剩两个导师决策项：multi-leaf vs second dataflow、harmfulness 定义选择。此结论不等于确认性 RQ2/Stage D/Stage R/RQ4、正式外投或训练完成。

- [2026-10-08] Stage E metadata-only source audit and 12-section inquiry/experiment-design report are complete as `DESIGN_ONLY_NOT_AUTHORIZED`; 94 HTTP attempts over 72 URLs exceeded the 80-attempt budget by 14 and are transparently recorded. Zero model/service/database/download/training calls occurred; `DATA_NO_GO / RQ2 NOT_IDENTIFIED` remains active and commit is `NOT_AUTHORIZED`.

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


## Current decisions

1. Paper E Version A is `QUANTIFICATION_READY`; Version B remains a proposal until user review.
2. Multi-leaf v1 is `POSITIVE` only for the constructed M/R/N codebook; v2 and Stage D training require separate authorization.

## Next gates

1. FinQA v2: freeze causal E1 evidence-to-argument join, exact IDs, label-blind extractor and role/split scope.
2. PRM formal pilot: close train payload, data licence, native token matching, powered split and MODEL_GO/TRAINING_GO.
3. Agent Distillation remains `NOT_SUITABLE_FOR_C2_C4` until terminal negatives and independent semantic process evidence exist.
4. Harmfulness definition remains open; do not change frozen Stage E labels.
5. External release, formal submission, Phase 2 and Stage R remain separately authorized.

## Overnight research graph loop (2026-10-10)

- Paper E matched-FPR/OCR claim boundary corrected across MD/DOCX/manifest/readiness/submission derivatives; frozen results unchanged.
- Multi-leaf formal run: `POSITIVE`, 216/216 contracts retained, macro-F1/top-1 `1.0`; direct-codebook ablation is also `1.0` and narrows the claim.
- PRM C2/C4 dry-run: `VALIDATED_NON_TRAINING`; reference smoke: `PIPELINE_CLOSED`, formal pilot `NO-GO`.
- Agent Distillation: `DATA_CAPABLE_LICENCE_PENDING_NOT_PILOT_READY`; TCV smoke 1926/1928 rows, execution proxy 1792/1928.
- Math-Shepherd-style rollout labels: constructed on 4 prefixes, 2/4 hard-positive and 2/4 human agreement; reference only.
- Verification: full pytest `880 passed / 13 skipped / 1 deselected`; docs lint `0 fail / 6 existing warnings`; paper claims `79/79`; submission `10/10`.

## Configuration and session neat status (2026-10-09)
- Loop A execution/diagnostic profiles and Loop C Claude Code route now use the approved Xiaomi mimo-v2.6 routes. Old deepseek profile and qwen Loop C wording are historical only.
- Codex history sessions were archived reversibly; OpenCode session deletion and attached tmux closure remain pending explicit cleanup confirmation.
- Config backups are retained outside Git; no credentials were copied into repository files.


- Final neat verification: GB10 full pytest 876 passed / 13 skipped / 1 deselected; docs_lint PASS with 6 existing warnings; skill-doctor 0 errors / 139 warnings; skill-map 114 skills / 1 duplicate / 27 unresolved; Codex archive 150 reversible. OpenCode session trimming and tmux closure remain pending confirmation.

- [2026-10-10 12:48 CST] FinQA v2 pre-result freeze Loop A is complete under `finqa-v2-preresult-freeze-a-20261010`: 216 candidates, 215 retained after one ambiguous N join was excluded before split, 72 group-disjoint clusters assigned as 27/15/30 groups by stage with exact 9/5/10 role quotas, 215 scorer bindings are bound but unexecuted, 19 focused tests passed, and formal FinQA v2 evaluator/model/training/endpoint counts are all zero. Status is `READY_FOR_LOOP_C_INDEPENDENT_REVIEW_NOT_EXECUTION`; no commit or push.
- [2026-10-10 14:49 CST] FinQA v2 statistical analysis-plan freeze Loop A is complete under `finqa-v2-analysis-freeze-a-20261010`: the Markdown/JSON plan, 16-file hash manifest and self-hashed receipt bind the 89-sample/30-cluster evaluation population, exact V/D/O definitions, 10,000 cluster bootstraps at seed 20261017, NOT_USED permutation, and fixed failure/result-class rules. Prior-freeze hash mismatches are 0; formal scorer outputs are 0 before and after plan creation; focused tests are 19 passed; no commit or push.
- [2026-10-10] FinQA v2 formal Loop A is `FORMAL_RUN_INVALID`: all 60 frozen hash checks and all 645 nested paired-artifact checks passed, focused tests passed `19/19`, and the authorized scorer failed closed on `89/89` evaluation pairs with `artifact_sha256_mismatch` because the raw manifest and normalized payload hashes differ. All 89 rows and 30 clusters remain retained with `V/D/O=null`; 0 estimands and 0 of 10,000 planned bootstraps were run, permutation remains `NOT_USED`, and `A_RECOMMENDED_CLASS=SECOND_FLOW_INVALID`. Fresh independent output verification passed; no endpoint, model, database, training, PRM, Stage D, or Paper E work occurred, and no commit or push.
- [2026-10-10 17:53 CST] The minimal binding-v2 rerun gate is now satisfied by the independent Loop C report (`SCORER_BINDING_GO = PASS`, `VERDICT: PASS`) and fresh preflight reconfirmed 12 old-run hashes, 7 frozen-input hashes, the 994-row mapping, and the exact 89-sample/30-cluster population; focused tests passed `19 + 10`. The authorized rerun then stopped fail-closed at `BINDING_TRACE_MISMATCH` on `89/89` evaluation records, with 0 scorer successes. `results_binding_v2_rerun/` preserves 89 null V/D/O rows, 56 non-computable scientific estimand slots, 0 of 10,000 bootstrap attempts, hash-bound logs/receipt, and `A_RECOMMENDED_CLASS=SECOND_FLOW_INVALID`. Status is `FORMAL_RUN_INVALID / SECOND_FLOW_INVALID`; estimands and bootstrap were not run, no scientific class is accepted, and Loop C independent post-run recomputation is required before any scientific acceptance.

## Historical objective context (2026-10-08)

No third FinQA formal scientific rerun is authorized. Active work is `RUNTIME_BINDING_INTEGRATION_QUALIFICATION`: binding-v3 reports `89/89` runtime bindings, `420/420` evaluation traces, zero silent defaults and zero scientific outputs, pending independent Loop C review. Governance authority and preflight rules are now in `docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md` and `docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`. `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN` remains `NO` until the v3 C audit and `END_TO_END_PREFLIGHT_PASS` are materialized.


No third FinQA formal scientific rerun is authorized. Active work is `RUNTIME_BINDING_INTEGRATION_QUALIFICATION`: binding-v3 reports `89/89` runtime bindings, `420/420` evaluation traces, zero silent defaults and zero scientific outputs, pending independent Loop C review. Governance authority and preflight rules are in `docs/governance/GRAPH_LOOP_AUTHORITY_MAP_V1.md` and `docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`. `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN` remains `NO` until the v3 C audit and `END_TO_END_PREFLIGHT_PASS` are materialized.

## Current governance status (2026-10-11)

SANER `PRIMARY_ROUTE=A` is frozen. Route B is `READ_ONLY_48H_QUALIFICATION / NO / STOP_BRANCH`. FinQA formal-v3 is `SECOND_FLOW_MIXED` with accepted interpretation `MEASUREMENT_OBJECT_MISMATCH`; it is not protocol-blindness evidence. Repository governance is `FAIL / STOP_GIT_SYNC` pending the recordkeeping and scope-lock corrections identified by Loop C.
