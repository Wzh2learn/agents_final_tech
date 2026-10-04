# Current State

## 2026-10-04 Q3 result and B5 addendum (append-only)

- User confirmed Q3 review by three independent experts (R1/R2/ADJ). This supersedes the intermediate statement that one expert served as both R1 and R2. Local checkout head observed as `d62420e`; this update performed no git operation and did not re-verify origin/GB10 alignment.
- Exploratory Q3 summary: 146/146 adjudicated labels; R1/R2 exact agreement 119/146 (81.51%); action Cohen's kappa approximately 0.727; 41/41 target exact agreement when both chose `map_to`; 27 disagreements all at the action boundary; final `map_to=52 / skip=58 / hold=36`.
- Raw R1/R2/ADJ outputs, adjudication ledger, final label ledger, gold-isolation receipt, and hashes remain to be sealed. These numbers are recorded as a user-confirmed expert-output summary, not as a complete artifact audit.
- Evidence boundary unchanged: exploratory learnability evidence only. It does not lift `RQ2 NOT_IDENTIFIED / DATA_NO_GO`, and must not be written as Stage D closure, RQ2 confirmation, training evidence, or RQ4 closure. The 146 columns contain only 10 lineage/table-pair clusters.
- B5 candidate registered as `Jev-like typed-decision baseline`, status `PROPOSED_EXPLORATORY / NOT_RUN`. Input is strictly `source_header + canonical headers + LABEL semantics`; action is selected first, then target only for `map_to`. B5 does not replace or modify frozen B0-B4. `open-alternative-jev` and `jevos-v2` remain unverified candidates and must not be installed or run before licence, provenance, version, dependency, and output-capability checks.
- Next order: seal the three expert outputs and hashes, run the existing B0-B4 exploratory probe, then audit and decide whether to run B5 as a single frozen zero-shot probe. Any tuning or calibration must use a table/lineage-UID group-aware split.
- 2026-10-04 full delivery: the 10-file expert package is stored at `logs/graph/q3_raw_seal_20261004/` and GB10 `/home/testuser/wzh/q3_raw_seal_20261004/inbox/q3_raw_seal_20261004/`. All 9 manifest hashes match. R1/R2/ADJ/final synthesis was mechanically verified: 119/146 agreement, 27 ADJ rows, kappa 0.7265, zero derivation errors; corrected ledger is `map_to=51 / skip=58 / hold=37` with only line 61 changed to `hold|null`. Status is `SEALED_WITH_VISIBILITY_EXCEPTIONS` / `seal_complete=true`; R1 saw lineage/table grouping and R2/ADJ lack separately signed visibility receipts.
> Updated: 2026-10-04 | Scope: 两份科研交付物最终完成审计通过；D-B licence_record 核验保持；MIMO 状态 READY_FOR_CONFIG_ONLY | Runtime: GB10 权威；零模型、零下载、零服务重启，API key 只在一次性进程环境加载

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions:
[`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md).
The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

围绕 Evaluate–Distill–Evolve 三阶段闭环推进科研主线（用户 2026-09-24 裁定：三阶段是目标主线，M 路线是阶段性过渡）。两份交付物按目标口径推进：小论文以**评估保底稿**为当前成稿口径（三阶段完整稿因数据门未开，按目标自带的自动切换条款走保底路线），大论文开题报告 + 初稿框架 + 前两章草稿均已成稿并经独立审计。

完成审计见 `docs/experiments/2026-10-03_goal_completion_audit.md`：草稿层两份交付物有机器验收、独立审稿/审计与 Office/边界证据；goal 保持 ACTIVE，继续准备小论文投稿版、大论文开题/前两章及后续章节框架。146 列 Q3、正式投稿、Phase 2/训练均不得冒充完成结果。

最终完成审计见 `docs/experiments/2026-10-04_goal_final_completion_audit.md`：按当前 goal 口径两份可交付成果均已达成；正式投稿、Q3 exploratory review、Phase 2/训练保留为后续授权/探索项，不冒充完成结果。
大白话完成度解释见 `docs/experiments/2026-10-04_goal_completion_plain_language.md`：内部科研交付完成不等于正式投稿或全项目所有后续实验完成。

当前执行重点：小论文投稿材料与大论文章节继续零模型推进；D-B licence_record 已正式接受，但仅覆盖 FinQA LICENSE、FinQA README、Valentine LICENSE 三件，不解除 `DATA_NO_GO`、不扩大下载或用途。

## Git state

- 当前 head = `f2adaf1be13cd641ca0993c8e2d20a16ad717cfc`；local / origin / GB10 对齐，ahead 0 / behind 0。
- 当前提交链：D-B licence_record `0a8ffbe` → 状态同步 `c26ae04` → 接受证据 `d83078e` → 可复现性声明 `af441ee` → 后续章节证据指针 `7d776b1` → 匿名投稿预览 `10dc253` → tracked 对账测试修正 `3f82d68` → 投稿包审计 `6e01b40`/`1ae9517`/`4cd0713` → SP-C5 证据锚点 `695b796`/`61abf0c` → reviewer 风险登记 `e34b3ea` → Related Work 矩阵 `1a13223` → RR-01 推导与派生重建 `7e91eea`/`de8bafe`/`6812d3c` → goal requirement matrix `e0a626e` → 语言/术语审计 `08b231f` → RQ2–RQ4 执行矩阵 `b72d06a`。全部逐路径 add，无 `-A`、无 `--amend`、无 `--no-verify`。
- GB10 production 脏件始终为固定五件（`config/schema_suggestions.json`、`logs/graph/docs_lint_report.json`、`logs/graph/governance_drift_latest.md`、`logs/graph/loop_b_last_status`、`logs/graph/verify-report.json`），每次 pull 前后逐条复核未被覆盖。
- 本机用户资产（`logs/graph/docs_lint_report.json`、`IMPLEMENTATION_PLAN.md`、`PROMPT.md`、`_d3b_dispatch.sh`）与 `side_handoff_20260829.md` 全程未 add、未 commit、未 stash、未 reset、未 clean。
- 受保护件未触碰：`docs/33*`、`docs/34*`、冻结测试、schema、`scripts/graph/frozen_hashes.txt`。
- Loop B：最近自然 PASS 覆盖 head `6ea62091c`；后续 `ae344ae`、`dc72a24`、`4591273`、`7e2a241`、`00bb53d`、`d1c82df`、`35e77d1`、`7dfb426`、`1c4ffaf`、`10dfbbd` 未被 PASS 覆盖。自然周期另于 `5f82efb` 记录 **FAIL**：唯一失败 `qa_canary`（`adv_cross_doc` 的 `source_required` 因 `sources empty`，1/2），其余 8 项 PASS；最终收尾 `2219fbc` 尚未被自然周期覆盖。本批未手工触发、未重置。

## GB10 boundary（已连通，取代 09-24 的「未连通」记载）

- SSH `jinrong-dev` 全天可用。GB10 是唯一权威运行 / 实验 / 验收环境；本机只做 git 同步、文本编辑与 commit/push，本机测试结果不作权威验收。
- 进程：`:5050` = PID 1868428，lstart 09-13 01:22:32（未重启）；Loop B daemon = PID **2835621**，lstart 09-24 14:14:59（用户授权 FLIP 改道重启后的进程）；10-03 复核两者 lstart 均未变。**旧任务卡所载 daemon PID 1816933 已不存在**，任何仍以该 PID 为准的检查都需更正。
- 端口：`:5050 / :8004 / :8006 / :8008 / :4096` 全部 LISTEN；`:5050/api/health/full` 实测 HTTP 200 / 0.127s，`overall=healthy`，pgvector ok（embeddings 137），llm_8004 ok，embedding ok。
- 资源门（决策 D4/D5 口径，本日实测）：磁盘 `/dev/nvme0n1p2` 3.6T 总量 / 814G 已用 / 2.7T 可用（24% 已用，满足「free ≥20% 且 ≥50GB」开工门）；内存 121G 总量 / available 31G（满足 ≥20G 开工门）/ used 74%（低于 85% 停止门）。
- `loop_b_flip_log.md` 由 `.gitignore:33`（`logs/graph/*`）收录并正常写入；`dispatch_log.md` 只承载 Loop D 台账，不再承载 Loop B 运行时记录。
- MIMO 路由只改 GB10 配置，不派发模型：Codex `/home/testuser/.codex/config.toml` = `mimo-v2.6-flash` / `https://token-plan-cn.xiaomimimo.com/v1`；Claude Code `/home/testuser/.claude/settings.json` = `mimo-v2.6-pro` / `https://token-plan-cn.xiaomimimo.com/anthropic`。两处语法/加载检查 PASS；secret 由既有安全通道承载，未读取、未打印、未写入 Git。
- MIMO 状态：`READY_FOR_CONFIG_ONLY`。`/home/testuser/.config/mimo-token-plan.env` 权限 600，已安全加载到一次性进程环境并通过 key 长度/格式检查；不派发模型、不跑 R1/R2/ADJ、不启动 Phase 2/训练。
- 仓外暂存：`~/wzh/phase1a_staging_20260925/`（FinQA train/dev + Valentine 10 个 NYC 目录 + LICENSE + bench.py；`sha256_manifest.txt` 共 64 行）。派生产物在 `/tmp/step_ckpt_20260925/` 与 `/tmp/repro_20260925/`。数据体与派生产物一律不入 Git。

## Research maturity

- Stage E（评估）：成熟评估子稿，95 表 / 118 注入，主张有界；当前文本经双模型独立审稿第 5 轮 **ACCEPT**，零 blocking。
- Stage D（蒸馏）：无训练后学生结果，既有零样本矩阵不是蒸馏证据。**新增实测边界**：RQ2 记 `NOT_IDENTIFIED`，因为「同一母池同时具备 checkpoint 证据 + Q3 动作/目标标签 + Q3 结果」的同样本桥在批准范围内不存在。
- Stage R（规则进化）：拒绝与碰撞机制证据存在；稳定净收益与长期回滚证据不存在。
- Phase 1a：按 G-A/B/C/E 裁定维持 `DATA_NO_GO`；Valentine 不承担 gate/sealed、阈值分桶不改、本批不扩下载。G-D 只批准 `target_table.csv` 表头作 canonical 参考并开 exploratory Q3 复核，不解 LABEL_GO/SPLIT_GO/POWER_GO/BASELINE_GO/MODEL_GO。
- 步级 checkpoint 重执行线：V2-3 已关闭；按预注册停止条件归档为边界结论（pct 保真度 0.0298 / 0.2233 < 0.5），不开 v3、不申报 FinQA 官方算子代码/文档。
- FinQA **具备** table layer（7134 例 100% 带非空矩形表、首行全字符串、列数 2-11），故「缺表层」不是递延理由；缺的是官方表列 canonical 词汇。表层使样本可定义，但不提供样本所需的 gold。
- 专利公开状态未确认：不外发、不上 arXiv、不公开代码。

## Current repository-only delivery

- `research/phase1a_data_contract.py` 实现 `phase1a-data-package-v2`：七个机械门 + 命名空间化 lineage UID/root/independence-cluster 隔离 + 严格 Q3 账本形状 + 显式统计字段 + 可选哈希绑定未来获取协议。只有两种结局：`DATA_NO_GO` 与 `READY_FOR_INDEPENDENT_ACCEPTANCE`；后者刻意不等于 `DATA_GO`、训练许可、GB10 验收或论文结果。
- `research/phase1a_learnability_baselines.py`（五基线）、`research/phase2_rule_gate_replay.py`（七臂 replay）、`research/paper_result_views.py`（Table 2 / Figure 4 视图，强制 `paper_result=false`）、以及 label_ledger 装配器 / feature ledger 派生器 / parser receipt 运行器均已在案并有合同测试。
- **本日新增三件运行器**：`research/phase1a_split_assign.py`（确定性、标签盲、零连接、哈希绑定 fail-closed 的分层仪器；治理编码——注册表 `role_fit` 未含 gate/sealed 时扣行并报 `LAYER_CAPACITY_BLOCKED_PILOT_ONLY`，须显式裁定 id 才填层；15 例合同测试）；`research/finqa_step_checkpoint_adapter.py`（预注册故障注入语料构建器，17 例测试）；`research/finqa_step_checkpoint_scorer.py`（按预注册 v2 的双读法检测器，含 v1 复现守卫与冻结值锚定，30 个测试函数）。
- **Q3 复核包**：`research/valentine_q3_review_package.py` + 16 例合同测试已落地；hardening 后输入只接受 10 pair × 3 allowlist 文件，输出目录 fail-closed 且不再删除旧内容。旧包 10 pair / 146 source columns / 160 target headers 仍为 hardening 前不可变历史产物。三位独立专家的 exploratory R1/R2/ADJ 结果已由用户确认，原始输出/hash 待封存；详见 `docs/experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md`。
- **Q3 复核包**：`research/valentine_q3_review_package.py` + 16 例合同测试已落地；hardening 后输入只接受 10 pair × 3 allowlist 文件，输出目录 fail-closed 且不再删除旧内容。旧包 10 pair / 146 source columns / 160 target headers 仍为 hardening 前不可变历史产物。三位独立专家的 exploratory R1/R2/ADJ 结果已由用户确认，原始输出/hash 待封存；详见 `docs/experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md`。
- **D-B licence_record**：`docs/datasets/phase1a_licence_record_v1.json` 已正式接受，`accepted_by=Wzh`、`accepted_at=2026-10-03T17:01:42Z`、permitted_uses 仅四项；covered hashes 仅限 FinQA LICENSE / FinQA README / Valentine LICENSE。该记录不是 package-wide 授权，不解除 `DATA_NO_GO`。证据见 `docs/experiments/2026-10-04_db_licence_record_acceptance.md`。
- **投稿/章节零模型材料**：`paper/reproducibility_statement_arr_www_v1.md` 区分可公开候选与不外发材料；`paper/thesis_manuscript_scaffold_v1.md` 新增第 3-8 章证据指针，Q3/Phase 2/训练空槽保持未完成。
- **匿名投稿预览**：`paper/submission_draft_arr_www_anonymous_v0.md` + 内部 `paper/submission_redaction_map_v1.json` 已生成，11 处机械脱敏、claim tokens 全保留、禁词 0；不是 camera-ready，不外发。
- **投稿包审计**：`research/audit_submission_package.py` + `paper/submission_package_audit_v1.json` 已落地，机械 10/10 PASS，但 `submission_status=PENDING_EXTERNAL_ITEMS`；venue/作者/专利/camera-ready/Q3 review 均未完成。
- **Goal requirement matrix**：2026-10-04 补充审计确认草稿层两份交付物 PROVEN；Q3 review 与投稿外部件仍为完成前置，goal 保持 ACTIVE。
- **SP-C5 evidence 锚点**：已补入 FinQA process structure 实测件，闭合 round5 N-2；`validate_paper_claims` 由 73 增至 74，acceptance report 已重生成，实验数字不变。
- **Reviewer 风险登记**：`paper/submission_review_risk_register_v1.md` 区分 controlled/closed/tracked/pending-external；当前无新 manuscript blocking issue，外部 submission blocker 保持 open。
- **RR-01 已闭合**：主稿 §5.2 补 single-varying-leaf 仿射分数推导，明确 `[0,0]` 是退化支持集而非一般等价定理；DOCX、匿名预览、redaction map、审计 hash 已同步。
- **Related Work 贡献矩阵**：`paper/related_work_contribution_matrix_v1.md` 固定四簇代表工作、本文差异边界，并将 KD/agent distillation 限定为 future work。
- **投稿语言审计**：`paper/submission_language_audit_v1.md` 未发现 AI 套话、无依据强主张或术语漂移；不改主稿。
- **RQ2–RQ4 执行矩阵**：`paper/thesis_rq2_rq4_execution_matrix_v1.md` 固化第 5–6 章的臂、指标、门序、确认性族与禁止写法，所有实验槽位保持空。
- 权威包 schema 与 GB10 程序见 `docs/experiments/2026-09-23_phase1a_data_no_go.md`；分层与容量见 `docs/datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md`；步级链路见 `docs/experiments/2026-09-25_finqa_step_checkpoint_corpus_v1.md`、`…_step_checkpoint_score_v1_results.md`、`…_step_checkpoint_score_v2_results.md`。

## Verification（GB10 权威，全量 head `6812d3c`；文档/章节收口 `b72d06a`）

- 全量 pytest：**832 passed / 13 skipped / 1 deselected**（10-04 于 `6812d3c` 实测，rc=0）。相对 829 增量 3 条为投稿包审计合同测试；tracked preview 测试自身 KeyError 已修，不改生成器。
- `research/validate_paper_claims.py` PASS / 5 claims / **74 checks 全过** / errors 空（10-04 于 `6812d3c` 复跑，rc=0）。
- 文档/投稿/章节后续 head `af441ee`、`7d776b1`、`b72d06a` 定点复核分别为 22、22、20 passed；claims 74/74、docs_lint 0 fail / 4 warn。
- 三个链路测试文件合计 69 passed。
- `docs_lint` rc=0 / **0 fail / 4 warn**；四条已按用户裁定逐条纳入 `logs/graph/docs_lint_warn_baseline.md`，机器比对 `SET_EQUAL=True, 4/4`。未回改正文、未消警、未改 lint 逻辑；真实内容更新留后续治理批。+ `[5]` INFO 行（注册表标 DEPRECATED 且未分发，属预期）。
- `sync_skills --check` **PASS: 97**（C14 摘除 `verification-before-completion` 后的口径，98 → 97，`[5]` INFO 行为证）。
- 本机 `docs_lint` 的 `[4]` fail 是历次台账在案的已知假阳（本机 Codex skill 安装区与仓库不同步）。本日以 GB10 为权威，**未在本机重跑** `docs_lint`，因为重跑会改写 `logs/graph/docs_lint_report.json` 这一用户资产；该条因此是「已记录状态」而非本日新测结果。
- 端点与模型调用申报（决策 46 口径）：本批（10-03）只读探测为 `:5050/api/health/full` 的 GET 与 `tests/test_health_embeddings_count.py` 内 `_pg_ready()` 对 PG `:15432` 的探测（随全量 pytest 轮次发生）；`integration` 标记测试 1 deselected（`tests/conftest.py` 默认排除，`JINRONG_RUN_INTEGRATION=1` 才收集，符合 D2）。模型调用仅用于独立审稿与审计（离线 packet，不接业务端点），累计 **≤105 / 200** turns；本批 0 次模型调用，未 top-up。

## Independent review status

- 小论文当前文本：双模型独立审稿第 3 轮 ACCEPT（实质修订后）→ 第 4 轮分歧（qwen 条件性 REVISE / deepseek ACCEPT，按更保守一侧执行全部 9 项）→ 第 5 轮双模型 **ACCEPT**，四条放行条件全部满足。
- 步级链路（暂存数据 → 论文所引数字）：独立审计 **PASS_WITH_NOTES**，无 HIGH；引用门判定「可以保留」，据此以 append-only 开启引用，范围严格限于边界量、必须带分母、两读法同时出现；detection 与 localization 数字仍在禁令内。
- 大论文三件（开题 / 前两章 / 骨架）：独立审计 **PASS_WITH_NOTES**，全部可执行 Finding 已闭合，仅余一项按审计人指示延后的范围性 Finding（既存批次数字不属本轮同步引入）。
- 纪律：生成者不自验；四份审稿 / 审计原件逐字落档；分歧以对照表记录、不合并结论、不代用户仲裁。

## Pending user confirmation

1. **MIMO 状态 = READY_FOR_CONFIG_ONLY**：API key 已安全加载到一次性进程环境；本轮 Q3 由三位独立外部专家完成，不等于 MIMO 模型派发。B5、Phase 2、训练仍待另行授权，不打印或记录 token。
2. G-A..G-E 与 V2-3 已裁定；MIMO 仅完成路由配置、不调用模型；D-F（专利门）继续有效。

## Next gates

1. 封存三位独立专家的 R1/R2/ADJ 输出、最终 label ledger、visibility receipt 与 hash，并过既有 label_ledger 装配器和独立审计；任何后续载体不得见 `ground_truth.json`。
2. 复核输出过既有 label_ledger 装配器与独立审计；源侧 gold 只在复核完成后作收敛效度统计，严格标 exploratory。
3. goal 保持 active：继续小论文投稿版、大论文开题/前两章与后续章节框架；ARR 10/12 为主窗口，WWW 10/18/10/25 为后备。146 列 Q3 只作 exploratory learnability evidence；下一步是 B0-B4 与 B5 go/no-go，不自动进入训练。
4. Phase 2 正式 replay、4B smoke、8B 主训练、端点与服务变更、以及任何外发，仍各自需要独立授权。

## 2026-10-04 research edge batch（append-only）

- 当前批准基线 = `f2adaf1be13cd641ca0993c8e2d20a16ad717cfc`；本批实际工作起点 = `e44c3c3d3922bc8b3c6f11d6a7cd50526ad6ebc0`。上文仍写 f2adaf1 的 Git 行是前批快照，本段为当前更正，不回改历史。
- 新增 `docs/datasets/2026-10-04_rq2_identification_and_acquisition_card.md`：RQ2 同样本 identification 与 Route V/F 数据、许可、split、power 申报，状态 `DECISION_APPLICATION / NO_EXECUTION`。
- 新增 `docs/experiments/2026-10-04_q3_b0_b4_execution_plan.md`：Q3 专家摘要状态注记与 B0-B4 执行合同；Q3 raw 未封存，B0-B4 `NOT_RUN`。
- 边界不变：`DATA_NO_GO`、`RQ2 NOT_IDENTIFIED`；146 列已有用户确认的 exploratory 摘要但 raw 未封存；MIMO `READY_FOR_CONFIG_ONLY`、V2-3 关闭、G-A/G-B/G-C 不批准。零模型、零下载、不启动 Phase 1a/2/训练、不外发。

## 2026-10-04 boundary clarification and blocker closure (append-only)

- Goal remains ACTIVE; Stage E fallback remains valid; RQ2 stays NOT_IDENTIFIED / DATA_NO_GO; Q3 remains exploratory learnability evidence only.
- Q3 raw artifacts are still MISSING in the checked local and GB10 scopes: R1 output, R2 output, ADJ output, final label ledger, expert visibility/gold-isolation receipt, and output manifest/hash. Empty input templates and historical /tmp/r1.json,/tmp/r2.json are explicitly not sealed raw outputs.
- Three invalid action references remain pending user disposition: turn 12 record_match, turn 13 revoke_match, turn 31 batch_record_match in City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments all reference mgp_curb_pri_boro. Options are reference-level quarantine or whole-pair INVALID; no option has been selected.
- B0-B4 exploratory split protocol is DRAFT_NOT_FROZEN / NOT_RUN at docs/datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md. The frozen runner is not run because proposal_train.dev=0.
- B5 remains PROPOSED_EXPLORATORY / NOT_RUN. Offline audit found no local source checkout, licence, version, dependency, import, or typed-output evidence for open-alternative-jev / jevos-v2.
- Stage R, RQ4, training, formal submission, external release, arXiv, and public code remain incomplete or prohibited.

## 2026-10-04 ruling landing (append-only)

- Raw originals delivery target is /home/testuser/wzh/q3_raw_seal_20261004/inbox/ (created empty, mode 700), with exact GB10 paths preferred. No reconstruction from summary.
- Invalid action references: Option A reference quarantine is primary for turn 12/13/31 with invalid_action_reference_count=3; Option B whole-pair INVALID is mandatory sensitivity. Preserve the 146-column summary and report a 9-cluster / 130-column sensitivity subset.
- B0-B4: LOO is primary, salted split is sensitivity; bootstrap 2000 and seeds [42,43,44] are exploratory uncertainty only. Protocol is user-selected but not frozen/running.
- B5 remains dormant / NOT_RUN; metadata-only audit is the maximum next step and execution needs separate authorization.

## 2026-10-04 Q3 raw seal correction (append-only)

- Raw audit package is sealed at logs/graph/q3_raw_seal_20261004/ and GB10 /home/testuser/wzh/q3_raw_seal_20261004/inbox/q3_raw_seal_20261004/; 10 files, 9/9 manifest hashes, secret scan 0.
- Authoritative corrected ledger SHA256 cf339cef8b7065dad05f574a1400415a7bff64b78b66e1db38f74143cc49ccb6; corrected counts map_to=51 / skip=58 / hold=37. The earlier 52/58/36 is pre-correction only.
- Evidence level is ARTIFACT_CLOSED_WITH_VISIBILITY_EXCEPTIONS: R1 saw lineage/table grouping; R2/ADJ lack separately signed visibility receipts.

## 2026-10-04 B0-B4 exploratory v2 result (append-only)

- Option A/B process variants passed on real staging: primary 10 pairs / 146 columns / 3 quarantined references; sensitivity 9 pairs / 130 columns / the same 3 references.
- Frozen B0-B4 v2 ran on GB10 with zero model calls. Primary B4 action macro-F1=0.71699, harmful-map rate=0.06164, coverage=0.26027; B3=0.57188 / 0.17808 / 0.32877. Pair-invalid B4=0.70931 / 0.06154 / 0.25385. Salted B4=0.69150 / 0.10526 / 0.31579 on only 2 test pairs / 19 columns.
- B4 is the current simple baseline to beat. A dedicated student is `NOT_ESTABLISHED` as necessary; no go/no-go threshold was approved and no training is authorized.
- The first probe run is invalidated by a salted B4 alignment bug; `freeze_v2` and `*_v2` outputs are the only valid exploratory evidence. Double-run diff rc=0/0/0.
- DATA_NO_GO / RQ2 NOT_IDENTIFIED / B5 dormant / no Phase 2 / no training boundaries remain.