# Open Decisions And Blockers

> **2026-10-29 新增待办**：OpenCode/Qwen 已完成隔离合成任务，六次物理尝试及已知用量见[容器回执](../research/paper_e_deep_benchmark_20261029/CONTAINER_AGENT_EXPLORATION_RETURN.md)；自然来源、独立结果参考和可检验方法仍待完成。第二篇的 [SkillsBench 资格](../research/agent_frontier_portfolio_20261029/SKILLSBENCH_SOURCE_QUALIFICATION_AND_PLAN.md)仅为改造环境中的离线断言，不是官方 BenchFlow 或 agent 成效；继续核验原始版本、许可、变更和强简单基线，不重开已停止面板。

> **现役裁决（2026-10-29）**：本提示优先于下方历史条目。Paper E 三案例稿已完成 v3 内部修订，但仍待最终模板、完整独立审稿、作者与对外投稿事项；[v3 回执](../research/paper_e_manuscript_followup_20261028/V3_REVIEW_RETURN.md)、[统计复核](../research/paper_e_evidence_followup_20261028/INDEPENDENT_HOLM_REVIEW.md)。六系统不是预注册或独立数据确认。[投稿时间及条件备选](../research/paper_e_publication_route_20261028/PUBLICATION_PLAN_ZH.md)为当前路线，不预设主投已获批准。第二篇仍在[对标与资格筛选](../research/paper_e_evidence_followup_20261028/SECOND_PAPER_RELATED_WORK_20261028.md)。用户已接受现场参会。本机、GitHub、GB10 main 已快进接收集成分支；原本机副本及校验清单保存在 `D:/Documents/Loop_D_assets/git_sync_backup_20261029`。历史 worktree 已确认提交为 main 祖先，但含忽略文件或未提交改动，保留未删。GB10 `docs_lint` 有共享 skill 安装漂移和一条文档时效 warning；未核验生产服务。

下方条目保留历史来源和原文，遇到状态冲突以本段为准，不能重开已停止的候选。

Updated: 2026-10-28

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

Loop D 已于 2026-10-28 接任并执行完本轮授权：Paper E 实质修订、Word/PDF 重渲染、逐页自审完成；唯一一次固定快照 C 已在 `08be0547` 上执行并处置，A/C 累计 29/29 用尽，本轮 A 为 0。科研生成/训练/判分仍为 0，外部动作仍待授权。

## 当前未决

BEIR第三案例评分合同、前后对照和复现命令已在2e7cc0f8修正；官方二进制对照、汇总舍入口径、图1重排及会议稿仍待执行。具体见[唯一科研指令](../docs/research/LOOP_D_RESEARCH_PROMPT.md)最新阶段，旧raw/结果保留。

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| PHASE-B-VALIDITY | `CORRECTED_IN_D_ADDENDUM_STOP_RETAINED` | 父adapter未激活、集合代理指标和R无干净因果负结论已写入[D前提纠偏](../research/decision_residual_pivot_20261026_v1/D_PREMISE_CORRECTION.md)；原raw/计数保留，旧R/E不重开 |
| NATURAL-ERROR-COST-NO-GO | `OFFLINE_NO_GO_RETAINED_POST_CALIBRATION_NARROWED` | 旧507行代理no-go保留；后续P1公共actor/全24回归已交付，P2完成12题三臂真实校准。506仍不是独立完整语义参考，旧R/E不重开。见[D集成回执](../research/publication_proxy_calibration_20261026_v1/D_INTEGRATION_RETURN.md) |
| LOOP-D-PHASE-B-DISPATCH | `COMPLETED_CURRENT_R_E_STOPPED` | [Phase B 回执](../research/feedback_learning_phase_b_20261026_v1/PHASE_B_RETURN.md)：GB10 A/C 已执行，当前 R/E 候选停止；confirmation/second seed 按门未运行 |
| LEDGER-340 | `UNRECONCILED_KEEP_CONSERVATIVE_TOTAL` | [自审证据](../docs/governance/audit/loop_d_control_review/RECONCILIATION.json)：35个生成/评审事件加5个训练事件复算9,169,332，比聚合9,169,672少340；attempts均4,064；不释放差额、不改旧账 |
| UNIT-OBSERVABILITY | `UNOBSERVABLE_UNIT_CASE_EXCLUDED_FROM_INFERABLE_DENOMINATOR` | [A回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)已确认单位尺度不可见；仅可修引用题0/1，后续监督按可观测性资格核验 |
| ADAPTER-SEMANTICS | `SAFE_TAIL_AND_STRICT_SPLIT_VERIFIED_PHASE_A` | [A复算](../research/feedback_delivery_continuation_20261025_v1/PHASE_A_RECOMPUTE_V1.json)已阻止1)0→10反例，raw/strict/embedded分开；不把旧适配器继续写成现役实现，未来合同仍需C核验 |
| NEXT-C2-SUPERVISION | `SCORING_V3_CONFIRMED_DTM_EFFECT_UNIDENTIFIED` | [C审阅](../research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md)确认三类配对控制与纯重评；D/T/M有输出长度/截断混淆，M未获公平试验；typed UNKNOWN还存在exact-key冲突。修订卡需先核合同与参考，不能默认加长后24-call重跑 |
| NEXT-PHASE-BUDGET | `PAPER_E_128_ATTEMPTS_1M_TOKENS_ON_FORWARD` | Owner转发后Paper E本地生成/judge硬帽128物理尝试与100万输入+输出tokens，含失败重试；先核父账本和余额，保留历史差额，DTM重跑不包含 |
| P2-CALIBRATION-NEXT | `QUESTION_ONLY_STOP_ACCEPTED_DEVELOPMENT_ONLY` | blank-type为12/19/5，question-only为31/5；mean信号真实可见，count/span依赖题面规则。停止冻结面板方法候选，不称通用answer-type推断或跨来源方法 |
| C2-FEEDBACK-REPAIR | `STOP_CURRENT_R_E_CANDIDATE_NOT_GENERAL_FEEDBACK_CLAIM` | [B2B 分析](../research/feedback_learning_phase_b_20261026_v1/b2b/B2B_DEVELOPMENT_ANALYSIS.json)与 [C 复核](../research/feedback_learning_phase_b_20261026_v1/audits/TASK_RESULT_C_B2B.json)支持当前实现停止；[事后复核](../docs/governance/audit/loop_d_control_review/PHASE_B_POST_RETURN_REVIEW.md)补充有效父模型与代理指标缺陷，不支持干净方法负结论或反馈学习普遍无效 |
| C3-DELIVERY-POLICY | `PRIOR_ERROR_POOL_REPLAY_NEUTRAL_RETRY_STRONG_LOCALIZATION_STOPPED` | [回放 C](../research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json) 中 original 60/72、neutral 62/72、localization 59/72；定位修订修对 3、破坏 4。24/24 task IDs 与 V4/V5 error pool 重合，只作开发回放，透明门控只以大面积弃答降低条件错误率 |
| PAPER-E-ROUTE | `EARLIER_CONFERENCE_SEARCH_IJCNN_BACKUP` | Owner偏好早会、正式出版、费用合理和远程展示；筛选更早可投会议，IJCNN 2027为备选，SNCS期刊顺序备选。学校是否认可预录、注册费及准确送审日需核实 |
| THESIS-REVIEW-DATE | `OCTOBER_2027_EXACT_DATE_UNKNOWN` | Owner 更正此前 2027 年 4 月信息；不得假设具体送审日为 10 月 31 日 |
| PAPER-E-SCOPE | `TWO_CASES_EXISTING_THIRD_IF_QUALIFIED` | 当前两案例保留；经冻结合同与可复现验证的独立公开案例可纳入，更新全部主张和摘要，不能将开发性/后验观察冒充确认 |
| PAPER-E-SUBMISSION | `IJCNN_PAGE_LIMIT_BLOCKS / SNCS_PRIMARY` | 匿名双栏 IJCNN 稿实测 13 页，超免费上限 7 页、超收费上限 3 页，付费也不能投；需另写真正 6 页精简稿。主投 SN Computer Science；IJCNN/FLAIRS 为有条件备选。官方 trec_eval 10.0-rc3 已实际运行，18,690 值一致 |
| DTM-MECHANISM-RERUN | `CORRECTED_CARD_DEFERRED` | D已修正字段/参考/预算，5条可分析样本仅开发；本轮优先Paper E，不释放D/T/M重跑预算 |
| WORKSPACE-INTEGRATION | `CONTINUE_EXISTING_INTEGRATION_WORKTREE_PRESERVE_123_FILES` | 负责人本地复核起点集成分支c33c14bf、主工作树main f0c246df；123个未跟踪文件原位保留。主树合并路径冲突不阻断集成分支修稿；本次未复核GB10，后续同步实测后再报 |
| HISTORICAL-CREDENTIAL-CARRIERS | `IGNORED_UNTRACKED_NO_LEAK_ESTABLISHED_NOT_A_BLOCKER` | 本次只核根.env未跟踪且被忽略，不读取内容或历史；先前“凭据形状”不能单独证明泄露，不要求轮换/迁移以完成科研交接。若将来有实际暴露证据再按证据处置，本轮未触碰 |
| PAPER-E-CONTINUATION | `PUBLIC_EVALUATION_AND_DECISION_IMPACT_PLANNED` | Owner转发后执行公开体系验证与审计前后对照，使用强基线、正反例和成本；A/C29/29，不再派发。结果尚未运行 |
| THESIS-DOC-CONTINUITY | `CONTINUE_PAPER_E_METHOD_EFFECT_UNIDENTIFIED` | 2027年10月送审日未定；Paper E两案例继续，C2/C3仍候选。旧raw/负结果保留，不把格式工程、治理和同一机制拆成三个创新点 |
| OWNER_EXTERNAL_ACTIONS | `AUTHOR_DECLARATIONS_ROUTE_AND_EXTERNAL_ACTIONS` | 作者/北邮单位/通讯、资助/利益冲突、作者贡献、AI披露最终确认、专利/artifact许可与公开、渠道和正式投稿及适用费用/学校认定。新科研预算另行接受；不再把内部图像重导出、字段核验列为Owner许可 |
| LEGACY-DATA-TRAINING | `HISTORICAL_NO_GO_RETAINED_NEW_STUDIES_AUTHORIZED` | Owner 新授权允许合格新数据上的小规模 LoRA/SFT 等研究；旧 Phase 1a `DATA_NO_GO`、RQ2 `NOT_IDENTIFIED` 及已停止面板的证据缺陷不解除，不洗掉旧训练/数据判定。本轮范围以唯一指令和Owner转发为准；历史广泛授权不恢复停止面板 |
| SKILL-METADATA-DEBT | `KNOWN_WARNINGS_AND_SOURCE_CONTRACT_UPDATE_NOT_DISTRIBUTED` | 历史skill-doctor为0 errors/141 warnings；本次仅补录版本化prompt契约，未同步机器安装。集成worktree为稀疏checkout，本地docs_lint的source missing/安装比较不是完整跨机分发验收；不阻断论文实作 |

旧 `MIGRATION-ORACLE-DESIGN`、`REVALIDATION-POLICY-DESIGN`、`G2-STATE-ACTION`、`G3-INCREMENTAL-EVIDENCE` 和 `NEXT-STATE-ACTION-EXPERIMENT` 已降为历史研究线，现役入口统一使用 C1 测量、C2 学习、C3 交付；原始证据和停止结论不改写。

## 未复核的历史运行与外部事项

本轮未连接生产后端复验。下列事项继续保留，归档不表示解决；完整描述、日期和原始状态见[旧 THREADS 全文](archive/THREADS_2026-10-21_pre_workspace_governance.md)。

| 事项 | 本轮状态 | 原文检索线索 |
|---|---|---|
| PostgreSQL 空闲连接、Loop B/kiosk 并发写、orphan/sidecar session、历史性能风险 | `NOT_REVALIDATED` | `PG`、`idle`、`schema_suggestions`、`orphan`、`sidecar` |
| M1 元数据缺失与 OCR/坐标边界 | `NOT_REVALIDATED` | `110/137`、`product_name`、`coord_table` |
| 导师/客户实际发送、旧投稿日期、专利与公开权限 | `NOT_CONFIRMED_THIS_PASS` | `发送`、`NLPCC`、`CCIR`、`专利`、`权限` |
| 其他历史 pending、known risk、待审批事项 | `RETAIN_ORIGINAL_STATUS` | 以原文状态为准；新证据出现后再逐项裁决 |

## 已收口或被更正条目的去向

- 2026-10-27：GB10 陈旧 A/C CLI transcript 已归档，50 条 OpenCode QA/eval
  sidecar session 已清理；备份和清场回执见
  [D收尾](../research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md)。
  `loop_runs` 证据、Loop B、服务 tmux 和 Claude memory 均保留。

- 2026-10-26：阶段B真实训练、B2B接口修复和独立C复核已完成；当前 R/E 停止，C 的四项范围披露已由 D 采纳。340 token旧差额未解释，继续单独保留。

- GOV-20261021 已完成：独有材料保全、九个历史独有提交合并、旧工作树退役、三端 main 对齐；范围、恢复入口和离线验收见[治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md)。
- 原 `memory/THREADS.md` 全文通过 `git mv` 原样保留为 [THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)，SHA256 为 `63246e3e23aaa7445c30bdaefee672d34f57e2cf3770edb64f87e3f84d9f516d`。快照内相对链接沿用原文件位于 `memory/THREADS.md` 时的基址，不重写历史正文。
- MA-CERD 的旧 dependency-propagation 与 handling 解释由[日期更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)取代；原始分数和实验回执不改。
- 旧 Goal “待转发”、Paper E “修订未落实”及 wide-evidence 源绑定阻塞已有后续执行或更正，不再作为现役待办；Paper E 的外部投稿事项仍开放。
- 旧 24 题统一人工门禁已有 AI 开发性裁决与后续资格判断；AI review 不等于人工 Gold。FinRank 当前面板已停止，不再以旧人工门禁要求重开。
- 747-record 与更早账本继续独立保存；当前 Portfolio V2 成本仅以[聚合账本](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)及其可重放更正为准。
- FinRank H/K、TAT-DQA 及各训练/数据门禁、同一 CodeUpdateArena prose-update 臂和已饱和 authored fixtures 的停止或授权边界继续有效。归档不产生新的运行许可。
