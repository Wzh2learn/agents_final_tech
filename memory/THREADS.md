# Open Decisions And Blockers

Updated: 2026-10-28

当前短状态见 [STATE.md](STATE.md)，科研证据路由见 [Research Entry](../docs/research/README.md)。本表保留真实未决事项；完成或被后续证据更正的历史条目保留原文归档。

Loop D 已于 2026-10-28 接任并执行完本轮授权：Paper E 实质修订、Word/PDF 重渲染、逐页自审完成；唯一一次固定快照 C 已在 `08be0547` 上执行并处置，A/C 累计 29/29 用尽，本轮 A 为 0。科研生成/训练/判分仍为 0，外部动作仍待授权。

## 当前未决

| ID | 状态 | 待决内容与证据 |
|---|---|---|
| PHASE-B-VALIDITY | `CORRECTED_IN_D_ADDENDUM_STOP_RETAINED` | 父adapter未激活、集合代理指标和R无干净因果负结论已写入[D前提纠偏](../research/decision_residual_pivot_20261026_v1/D_PREMISE_CORRECTION.md)；原raw/计数保留，旧R/E不重开 |
| NATURAL-ERROR-COST-NO-GO | `OFFLINE_NO_GO_RETAINED_POST_CALIBRATION_NARROWED` | 旧507行代理no-go保留；后续P1公共actor/全24回归已交付，P2完成12题三臂真实校准。506仍不是独立完整语义参考，旧R/E不重开。见[D集成回执](../research/publication_proxy_calibration_20261026_v1/D_INTEGRATION_RETURN.md) |
| LOOP-D-PHASE-B-DISPATCH | `COMPLETED_CURRENT_R_E_STOPPED` | [Phase B 回执](../research/feedback_learning_phase_b_20261026_v1/PHASE_B_RETURN.md)：GB10 A/C 已执行，当前 R/E 候选停止；confirmation/second seed 按门未运行 |
| LEDGER-340 | `UNRECONCILED_KEEP_CONSERVATIVE_TOTAL` | [自审证据](../docs/governance/audit/loop_d_control_review/RECONCILIATION.json)：35个生成/评审事件加5个训练事件复算9,169,332，比聚合9,169,672少340；attempts均4,064；不释放差额、不改旧账 |
| UNIT-OBSERVABILITY | `UNOBSERVABLE_UNIT_CASE_EXCLUDED_FROM_INFERABLE_DENOMINATOR` | [A回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)已确认单位尺度不可见；仅可修引用题0/1，后续监督按可观测性资格核验 |
| ADAPTER-SEMANTICS | `SAFE_TAIL_AND_STRICT_SPLIT_VERIFIED_PHASE_A` | [A复算](../research/feedback_delivery_continuation_20261025_v1/PHASE_A_RECOMPUTE_V1.json)已阻止1)0→10反例，raw/strict/embedded分开；不把旧适配器继续写成现役实现，未来合同仍需C核验 |
| NEXT-C2-SUPERVISION | `SCORING_V3_CONFIRMED_DTM_EFFECT_UNIDENTIFIED` | [C审阅](../research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md)确认三类配对控制与纯重评；D/T/M有输出长度/截断混淆，M未获公平试验；typed UNKNOWN还存在exact-key冲突。修订卡需先核合同与参考，不能默认加长后24-call重跑 |
| NEXT-PHASE-BUDGET | `29_USED_NO_NEW_DISPATCH_OR_SCIENTIFIC_RUN` | A/C累计29/29；历史27次预留、24条raw和46,054 tokens保留。全局保守余额不是开跑许可；35请求卡输入/重试预算未闭合，需离线重写后再申请 |
| P2-CALIBRATION-NEXT | `QUESTION_ONLY_STOP_ACCEPTED_DEVELOPMENT_ONLY` | blank-type为12/19/5，question-only为31/5；mean信号真实可见，count/span依赖题面规则。停止冻结面板方法候选，不称通用answer-type推断或跨来源方法 |
| C2-FEEDBACK-REPAIR | `STOP_CURRENT_R_E_CANDIDATE_NOT_GENERAL_FEEDBACK_CLAIM` | [B2B 分析](../research/feedback_learning_phase_b_20261026_v1/b2b/B2B_DEVELOPMENT_ANALYSIS.json)与 [C 复核](../research/feedback_learning_phase_b_20261026_v1/audits/TASK_RESULT_C_B2B.json)支持当前实现停止；[事后复核](../docs/governance/audit/loop_d_control_review/PHASE_B_POST_RETURN_REVIEW.md)补充有效父模型与代理指标缺陷，不支持干净方法负结论或反馈学习普遍无效 |
| C3-DELIVERY-POLICY | `PRIOR_ERROR_POOL_REPLAY_NEUTRAL_RETRY_STRONG_LOCALIZATION_STOPPED` | [回放 C](../research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json) 中 original 60/72、neutral 62/72、localization 59/72；定位修订修对 3、破坏 4。24/24 task IDs 与 V4/V5 error pool 重合，只作开发回放，透明门控只以大面积弃答降低条件错误率 |
| PAPER-E-ROUTE | `SNCS_SUBSCRIPTION_CONDITIONAL_PRIMARY_ICAART_TIME_GATED` | [渠道复核](../research/natural_error_evidence_cost_20261026_v1/paper_e/ROUTE_REASSESSMENT_20261026.md)：ICAART实时官网不可用且前置条件未齐；Owner仍需最终确认，未投稿/付款/公开 |
| THESIS-REVIEW-DATE | `OCTOBER_2027_EXACT_DATE_UNKNOWN` | Owner 更正此前 2027 年 4 月信息；不得假设具体送审日为 10 月 31 日 |
| PAPER-E-SCOPE | `TWO_CASES_FOR_CURRENT_SUBMISSION` | 当前首投保持[主稿](../paper/saner_rene_manuscript_v1.md)两案例。FinQA 为89行/30 report clusters；UID 聚类与事后统计已同步，不追认事后分析为预注册 |
| PAPER-E-SUBMISSION | `FIGURES_REBUILT_TEXT_READY_DECLARATIONS_OPEN` | 三图已从 SVG 源重导出（去图内标题/副标题/脚注与重复 caption，裁到内容框，1200 dpi 线图 / 600 dpi 组合图），14 页重渲染并逐页自验，页哈希与派生 manifest 更新，旧图与原 manifest 保留历史身份。仍开放：声明占位、图内字号 5.7–8.2 pt 低于推荐值、文献标题大小写。C后修改未获独立复审 |
| DTM-MECHANISM-RERUN | `CARD_V2_CORRECTED_AWAITING_OWNER_BUDGET` | [决策卡v2](../research/word_scoring_new_family_20261027_v1/DTM_DECISION_CARD_20261028.md)已按[复核](../docs/governance/audit/loop_d_control_review/LOOP_D_POST_RETURN_REVIEW_20261028.md)原地更正：撤回因果与「单位未冻结」；`unit` 8/8 有值、3 条标签冲突使可分析面板收缩到 5；删除格式率停止判据；预算重开为 27 物理请求 / 67,824 token，重试入帽、D-long 取消。Owner只需接受硬帽与 5 条面板。生成仍 0 |
| WORKSPACE-INTEGRATION | `CONTINUE_EXISTING_INTEGRATION_WORKTREE_PRESERVE_123_FILES` | 负责人本地复核起点集成分支c33c14bf、主工作树main f0c246df；123个未跟踪文件原位保留。主树合并路径冲突不阻断集成分支修稿；本次未复核GB10，后续同步实测后再报 |
| HISTORICAL-CREDENTIAL-CARRIERS | `IGNORED_UNTRACKED_NO_LEAK_ESTABLISHED_NOT_A_BLOCKER` | 本次只核根.env未跟踪且被忽略，不读取内容或历史；先前“凭据形状”不能单独证明泄露，不要求轮换/迁移以完成科研交接。若将来有实际暴露证据再按证据处置，本轮未触碰 |
| PAPER-E-CONTINUATION | `D_SELF_VERIFIES_REMAINING_INTERNAL_WORK_NO_C_REDISPATCH` | C已审08be0547且29/29用尽。D继续已授权的图片/稿件内部修订和自验，保留未经再次独立复审边界。C规则文件改写事件保留恢复证据，不扩展基础设施工程 |
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
