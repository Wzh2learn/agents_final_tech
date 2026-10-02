# Current State

> Updated: 2026-10-03 | Scope: 草稿层两份交付物证据完成；投稿版与后续章节框架继续推进；G-A..G-E/V2-3 已同步；146 列 Q3 保持已装配未复核 | Runtime: GB10 权威；token 未轮换/未就绪，零模型调用，外发与后续实验继续受专利/预注册门控制

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions:
[`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md).
The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

围绕 Evaluate–Distill–Evolve 三阶段闭环推进科研主线（用户 2026-09-24 裁定：三阶段是目标主线，M 路线是阶段性过渡）。两份交付物按目标口径推进：小论文以**评估保底稿**为当前成稿口径（三阶段完整稿因数据门未开，按目标自带的自动切换条款走保底路线），大论文开题报告 + 初稿框架 + 前两章草稿均已成稿并经独立审计。

完成审计见 `docs/experiments/2026-10-03_goal_completion_audit.md`：草稿层两份交付物有机器验收、独立审稿/审计与 Office/边界证据；goal 保持 ACTIVE，继续准备小论文投稿版、大论文开题/前两章及后续章节框架。146 列 Q3、正式投稿、Phase 2/训练均不得冒充完成结果。

## Git state

- 三方对齐至审计基线 `ae344ae1c6fe4883ce19a047c94658d01f354cbe`，ahead 0 / behind 0；本快照/完成审计提交随后收尾。
- 后续提交链：零模型边界同步 `07d89a1` → Q3 理论/图表空槽 `6ea6209` → readiness 契约链接回归修复 `ae344ae`。全部逐路径 add，无 `-A`、无 `--amend`、无 `--no-verify`、无破坏性命令。
- GB10 production 脏件始终为固定五件（`config/schema_suggestions.json`、`logs/graph/docs_lint_report.json`、`logs/graph/governance_drift_latest.md`、`logs/graph/loop_b_last_status`、`logs/graph/verify-report.json`），每次 pull 前后逐条复核未被覆盖。
- 本机用户资产（`logs/graph/docs_lint_report.json`、`IMPLEMENTATION_PLAN.md`、`PROMPT.md`、`_d3b_dispatch.sh`）与 `side_handoff_20260829.md` 全程未 add、未 commit、未 stash、未 reset、未 clean。
- 受保护件未触碰：`docs/33*`、`docs/34*`、冻结测试、schema、`scripts/graph/frozen_hashes.txt`。
- Loop B：最近自然周期 2026-10-03 00:27:32 于 head `871aeb3` 记录 overall **PASS**，9 项检查全 PASS（`logs/graph/verify-report.json`）；本批未手工触发、未重置。

## GB10 boundary（已连通，取代 09-24 的「未连通」记载）

- SSH `jinrong-dev` 全天可用。GB10 是唯一权威运行 / 实验 / 验收环境；本机只做 git 同步、文本编辑与 commit/push，本机测试结果不作权威验收。
- 进程：`:5050` = PID 1868428，lstart 09-13 01:22:32（未重启）；Loop B daemon = PID **2835621**，lstart 09-24 14:14:59（用户授权 FLIP 改道重启后的进程）；10-03 复核两者 lstart 均未变。**旧任务卡所载 daemon PID 1816933 已不存在**，任何仍以该 PID 为准的检查都需更正。
- 端口：`:5050 / :8004 / :8006 / :8008 / :4096` 全部 LISTEN；`:5050/api/health/full` 实测 HTTP 200 / 0.127s，`overall=healthy`，pgvector ok（embeddings 137），llm_8004 ok，embedding ok。
- 资源门（决策 D4/D5 口径，本日实测）：磁盘 `/dev/nvme0n1p2` 3.6T 总量 / 814G 已用 / 2.7T 可用（24% 已用，满足「free ≥20% 且 ≥50GB」开工门）；内存 121G 总量 / available 31G（满足 ≥20G 开工门）/ used 74%（低于 85% 停止门）。
- `loop_b_flip_log.md` 由 `.gitignore:33`（`logs/graph/*`）收录并正常写入；`dispatch_log.md` 只承载 Loop D 台账，不再承载 Loop B 运行时记录。
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
- **Q3 复核包**：`research/valentine_q3_review_package.py` + 6 例合同测试已落地；GB10 双跑 10 pair / 146 source columns / 160 target headers，50+50+46 三块，包逐字节一致，`strace` 对 `ground_truth.json` open 命中 0。证据见 `docs/experiments/2026-10-03_ruling_gd_q3_package_and_goal_refresh.md`。
- 权威包 schema 与 GB10 程序见 `docs/experiments/2026-09-23_phase1a_data_no_go.md`；分层与容量见 `docs/datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md`；步级链路见 `docs/experiments/2026-09-25_finqa_step_checkpoint_corpus_v1.md`、`…_step_checkpoint_score_v1_results.md`、`…_step_checkpoint_score_v2_results.md`。

## Verification（GB10 权威，head `ae344ae`）

- 全量 pytest：**809 passed / 13 skipped / 1 deselected**（10-03 于 `ae344ae` 实测，rc=0）。审计过程中曾抓到 readiness 缺执行计划链接的 1 failed；只补链接、未改测试，随后目标用例 1 passed 与全量均恢复。
- `tests/test_paper_claim_acceptance.py` 与渲染回归合计 13 passed（GB10，10-03；含 DOCX 与 MD 逐段逐格一致门）；`research/validate_paper_claims.py` PASS / 5 claims / **73 checks 全过** / errors 空（10-03 于 `871aeb3` 复跑，rc=0）。
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

1. **GB10 qwen/deepseek key 已失效，token 按“未轮换 / 未就绪”处理**：新 key 安全配置、状态确认并获明确授权前不得派 R1/R2/裁决，不打印或记录 token。
2. G-A..G-E 与 V2-3 已裁定；D-E（MIMO 挂起）与 D-F（专利门）继续有效。

## Next gates

1. 只有新 key 安全配置、状态确认并获明确授权后，才派 R1 = qwen3.8-max、R2 = deepseek-v4-pro 与独立裁决；三者互异且非生成者，任何载体不得见 `ground_truth.json`。
2. 复核输出过既有 label_ledger 装配器与独立审计；源侧 gold 只在复核完成后作收敛效度统计，严格标 exploratory。
3. goal 保持 active：继续小论文投稿版、大论文开题/前两章与后续章节框架；ARR 10/12 为主窗口，WWW 10/18/10/25 为后备。146 列 review 如后续获准，只作 exploratory 补充证据。
4. Phase 2 正式 replay、4B smoke、8B 主训练、端点与服务变更、以及任何外发，仍各自需要独立授权。
