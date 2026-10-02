# Current State

> Updated: 2026-10-03 | Scope: 承接 09-25 快照（SOURCE_GO 取证、三件运行器、步级线终止、小论文审稿链），新增两份导师向 DOCX 的 Office 视觉验收完成（3 处缺陷修复 + 回归测试） | Runtime: GB10 已连通并为唯一权威验收环境；未重启 daemon 与 :5050、未覆盖 production 脏件、未跑任何训练或业务实验

Current snapshot. Open decisions: [`THREADS.md`](THREADS.md); durable decisions:
[`DECISIONS.md`](DECISIONS.md); research entry: [`../docs/research/README.md`](../docs/research/README.md).
The pre-governance snapshot remains archived at [`archive/STATE_2026-09-22_pre_governance.md`](archive/STATE_2026-09-22_pre_governance.md).

## Current objective

围绕 Evaluate–Distill–Evolve 三阶段闭环推进科研主线（用户 2026-09-24 裁定：三阶段是目标主线，M 路线是阶段性过渡）。两份交付物按目标口径推进：小论文以**评估保底稿**为当前成稿口径（三阶段完整稿因数据门未开，按目标自带的自动切换条款走保底路线），大论文开题报告 + 初稿框架 + 前两章草稿均已成稿并经独立审计。

Phase 1a 动作包仍为 `DATA_NO_GO`，Phase 2 未启动，训练与模型端点窗口未开启。与 09-24 的差别在于：这不再是「尚未测量」，而是**已实测定位**——批准范围内没有单一命名空间可承载动作包（见 Research maturity 与 Pending user decisions）。任何阶段推进仍须逐门取得用户授权。

## Git state

- 三方对齐：local `main` = `origin/main` = GB10 production = `871aeb3d88064ed8a202da7ef4eedcd95d23b2e9`，ahead 0 / behind 0。
- 提交序列（09-25 快照以来）：STATE 快照刷新 `0fdd79b` → Office 缺陷修复 `3df1134` + 导师稿 DOCX 重建 `9b19167` → 视觉验收落档 `871aeb3`。全部逐路径 add，无 `-A`、无 `--amend`、无 `--no-verify`、无破坏性命令。
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
- Phase 1a：维持 `DATA_NO_GO`，成因已实测定位为四堵墙——W1 十簇填不满四层（dev 层实测 0 簇）、W2 注册表 `role_fit` 与协议 §4.1 均不给 Valentine gate/sealed、W3 动作流 K=10 对 250-500 UID 目标差 25-50 倍、W4 FinQA 无动作标签语义。门状态：SOURCE_GO 已过；SPLIT 仪器 READY 而动作包 SPLIT_GO **BLOCKED**；LABEL_GO 未启动（待 G-D）；POWER_GO / BASELINE_GO / MODEL_GO 未启动。
- 步级 checkpoint 重执行线：**已按其自身预注册停止条件终止**（两种百分号读法下 pct 形态保真度 0.0298 与 0.2233，均低于预设 0.5）。不得开 v3 继续试约定；唯一合法后续是新申报 FinQA 官方算子代码或文档（超出 D-C 范围，需用户批准），或放弃该路线并如实记录。
- FinQA **具备** table layer（7134 例 100% 带非空矩形表、首行全字符串、列数 2-11），故「缺表层」不是递延理由；缺的是官方表列 canonical 词汇。表层使样本可定义，但不提供样本所需的 gold。
- 专利公开状态未确认：不外发、不上 arXiv、不公开代码。

## Current repository-only delivery

- `research/phase1a_data_contract.py` 实现 `phase1a-data-package-v2`：七个机械门 + 命名空间化 lineage UID/root/independence-cluster 隔离 + 严格 Q3 账本形状 + 显式统计字段 + 可选哈希绑定未来获取协议。只有两种结局：`DATA_NO_GO` 与 `READY_FOR_INDEPENDENT_ACCEPTANCE`；后者刻意不等于 `DATA_GO`、训练许可、GB10 验收或论文结果。
- `research/phase1a_learnability_baselines.py`（五基线）、`research/phase2_rule_gate_replay.py`（七臂 replay）、`research/paper_result_views.py`（Table 2 / Figure 4 视图，强制 `paper_result=false`）、以及 label_ledger 装配器 / feature ledger 派生器 / parser receipt 运行器均已在案并有合同测试。
- **本日新增三件运行器**：`research/phase1a_split_assign.py`（确定性、标签盲、零连接、哈希绑定 fail-closed 的分层仪器；治理编码——注册表 `role_fit` 未含 gate/sealed 时扣行并报 `LAYER_CAPACITY_BLOCKED_PILOT_ONLY`，须显式裁定 id 才填层；15 例合同测试）；`research/finqa_step_checkpoint_adapter.py`（预注册故障注入语料构建器，17 例测试）；`research/finqa_step_checkpoint_scorer.py`（按预注册 v2 的双读法检测器，含 v1 复现守卫与冻结值锚定，30 个测试函数）。
- 权威包 schema 与 GB10 程序见 `docs/experiments/2026-09-23_phase1a_data_no_go.md`；分层与容量见 `docs/datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md`；步级链路见 `docs/experiments/2026-09-25_finqa_step_checkpoint_corpus_v1.md`、`…_step_checkpoint_score_v1_results.md`、`…_step_checkpoint_score_v2_results.md`。

## Verification（GB10 权威，head `871aeb3`）

- 全量 pytest：**803 passed / 13 skipped / 1 deselected**（10-03 于 `871aeb3` 实测，rc=0）。计数按逐 head 实测对账：727（09-24 台账基线于 `3240a78`）+ 1（confidence_manifest 合同件）+ 15（分层运行器）= 743（实测于 `d079c05` / `4484fe6`）；+ 17（语料构建器）= 760（实测于 `47fa138`，即 conftest 修好跨文件 socket 守卫泄漏后复原的值）；+ 28（检测器 v1）= 788（实测于 `5bde74d`）；+ 2（audit_records 验收门）= 790（实测于 `c511bbd` / `12e5e39`）；+ 9（链路审计补的守卫负例与 seed 性质）= 799（实测于 `2377447`）；+ 4（导师稿 DOCX 渲染回归，`3df1134`）= **803**（实测于 `871aeb3`）。skipped 恒为 13、deselected 恒为 1（`tests/conftest.py` 默认排除 `integration`，`JINRONG_RUN_INTEGRATION=1` 才收集）。
- `tests/test_paper_claim_acceptance.py` 与渲染回归合计 13 passed（GB10，10-03；含 DOCX 与 MD 逐段逐格一致门）；`research/validate_paper_claims.py` PASS / 5 claims / **73 checks 全过** / errors 空（10-03 于 `871aeb3` 复跑，rc=0）。
- 三个链路测试文件合计 69 passed。
- `docs_lint` rc=0 / **0 fail / 4 warn**（10-03 于 `871aeb3` 实测；同一自然 Loop B 轮次的报告一致）：`docs/34*` 时效 1 条在基线内保留；另 3 条 `[2]` 时效 warn（`docs/32*`、`docs/33*`、`docs/m1_coldstart_candidates.md`，均 09-11 最后更新）自 09-26 起按 `STALE_DAYS=14` 自然越过阈值，非本批改动文件、非本批引入；本批未消警、未扩基线，按基线规则登记为待处置偏离（真实内容更新或用户批准准入）。+ `[5]` INFO 行（注册表标 DEPRECATED 且未分发，属预期）。
- `sync_skills --check` **PASS: 97**（C14 摘除 `verification-before-completion` 后的口径，98 → 97，`[5]` INFO 行为证）。
- 本机 `docs_lint` 的 `[4]` fail 是历次台账在案的已知假阳（本机 Codex skill 安装区与仓库不同步）。本日以 GB10 为权威，**未在本机重跑** `docs_lint`，因为重跑会改写 `logs/graph/docs_lint_report.json` 这一用户资产；该条因此是「已记录状态」而非本日新测结果。
- 端点与模型调用申报（决策 46 口径）：本批（10-03）只读探测为 `:5050/api/health/full` 的 GET 与 `tests/test_health_embeddings_count.py` 内 `_pg_ready()` 对 PG `:15432` 的探测（随全量 pytest 轮次发生）；`integration` 标记测试 1 deselected（`tests/conftest.py` 默认排除，`JINRONG_RUN_INTEGRATION=1` 才收集，符合 D2）。模型调用仅用于独立审稿与审计（离线 packet，不接业务端点），累计 **≤105 / 200** turns；本批 0 次模型调用，未 top-up。

## Independent review status

- 小论文当前文本：双模型独立审稿第 3 轮 ACCEPT（实质修订后）→ 第 4 轮分歧（qwen 条件性 REVISE / deepseek ACCEPT，按更保守一侧执行全部 9 项）→ 第 5 轮双模型 **ACCEPT**，四条放行条件全部满足。
- 步级链路（暂存数据 → 论文所引数字）：独立审计 **PASS_WITH_NOTES**，无 HIGH；引用门判定「可以保留」，据此以 append-only 开启引用，范围严格限于边界量、必须带分母、两读法同时出现；detection 与 localization 数字仍在禁令内。
- 大论文三件（开题 / 前两章 / 骨架）：独立审计 **PASS_WITH_NOTES**，全部可执行 Finding 已闭合，仅余一项按审计人指示延后的范围性 Finding（既存批次数字不属本轮同步引入）。
- 纪律：生成者不自验；四份审稿 / 审计原件逐字落档；分歧以对照表记录、不合并结论、不代用户仲裁。

## Pending user decisions

1. **G-A..G-E**（见 `docs/datasets/2026-09-25_phase1a_split_design_and_layer_capacity.md` §8）：是否许 Valentine 承担 gate/sealed；小簇数下是否改秩分位分桶；是否批准新的最小下载增量以取得 ≥40 origin cluster 独立批次；Valentine 的 canonical 参考可否用 `target_table.csv` 表头；是否接受「动作包维持 DATA_NO_GO + RQ2 `NOT_IDENTIFIED` + 小论文按评估保底口径推进 + 146 列 Q3 复核作 exploratory」这一组合。
2. **V2-3 分叉**：是否新申报 FinQA 官方算子代码 / 文档（超 D-C 范围），或正式关闭步级重执行路线。
3. 仍沿用 2026-09-25 的 D-A=3 / D-B / D-C（已完成）/ D-D（仅范围设计）/ D-E（MIMO 维持现状另批）/ D-F（专利未确认前不外发）。

## Next gates

1. G-D 若批准：装配 Valentine 146 源列的 Q3 三载体复核输入包（R1 = qwen3.8-max，R2 = deepseek-v4-pro，裁决载体独立且不得由生成者担任），并强制任何载体不得见 `ground_truth.json`；源侧 gold 只用于事后收敛效度统计并披露其为来源自带元数据。
2. G-A / G-C 若批准：按裁定重跑分层仪器产出权威 layers，再走 label_ledger 装配 → feature ledger 派生 → 合同双跑 precheck（byte-identical、零 connect）→ 独立复核 → 重评 `DATA_NO_GO`。
3. 若均不批准：按 G-E 维持 `DATA_NO_GO` 与 RQ2 `NOT_IDENTIFIED`，小论文保持评估保底口径，大论文保持设计阶段表述，不以任何方式把目标写成结果。
4. Phase 2 正式 replay、4B smoke、8B 主训练、端点与服务变更、以及任何外发，仍各自需要独立授权。
5. 两份导师 DOCX 的 Office 视觉验收已于 2026-10-03 完成并 PASS（证据件 `docs/experiments/2026-10-03_office_visual_acceptance.md`；修复 `3df1134`、重建 `9b19167`）；仅余跨页表格未重复表头一项非阻断观察。另：`docs_lint` 的 3 条新增 `[2]` 时效 warn 需在后续治理批以真实内容更新或用户批准准入处理。
