# Current State

> Updated: 2026-10-28 | Scope: post-return review; D continues internal Paper E work; no new scientific calls
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

Loop D已接任，Paper E转换与正文修复有实质进展：单一生产源`paper_e_revision_v2.md`、14页DOCX/PDF及派生manifest已交付。负责人本地重放源重建与结构/算术检查PASS（6步、4表、3图、24引用、28项算术），不替代重新目视或科学同行评审。C曾审`08be0547`并判CONDITIONAL，累计29/29；后续正文修订未经再次独立复审。三图与声明仍开放，尚非最终投稿包。

D可继续已授权内部图像修订、现成工具渲染和自验，不因C额度耗尽停止；不追加A/C。科研生成、训练、judge及外部动作保持未执行。下一步先闭环Paper E，再修离线实验卡；见[负责人复核](../docs/governance/audit/loop_d_control_review/LOOP_D_POST_RETURN_REVIEW_20261028.md)。

负责人本地复核起点：集成分支`integration/paper-e-word-20261028`为`c33c14bf`，主工作树main仍为`f0c246df`；123个未跟踪Word文件原位保留。当前修订继续在现成集成worktree，main路径冲突不阻断论文工作。本次未重核GB10，不能将本地文档更新写为三端已同步。



D/T/M旧面板仍受thinking、截断及不等长合同混淆，不能识别M效应。当前卡误读`unit_reference`；实际8条都有`unit`（3 percent、1 thousand、4 UNKNOWN），需逐题复核而非断言全缺。格式率持平不是停止方法的判据；35请求卡漏计部分输入和物理重试，尚不可开跑。历史推理输出已包含在output总量，不因缺细分重复追加。


接任前的28/28、5/7分叉、38/85文件分类及84/86历史hash结果保留为[前次复核](../docs/governance/audit/loop_d_control_review/NEW_LOOP_D_HANDOFF_REVIEW_20261028.json)的日期快照，不再作为“尚待接任/尚可派C”的现役状态。旧raw、清单、参考、评分与历史worktree均保留。

Phase A 复算确认：安全尾部适配后 copy 2/2、known edit 2/2；单位题没有可见 million/thousand 尺度，降为不可判定，唯一可修的引用题在 neutral/category/localization 下均 0/1。旧 generic adapter 的 `1)0→10` 语义污染反例已由 strict whole-JSON 和限定尾部规则阻止。详见 [Phase A 回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)与[复算](../research/feedback_delivery_continuation_20261025_v1/PHASE_A_RECOMPUTE_V1.json)。

此前 P0/A/C 负结果继续保留开发身份。Phase B 的R/E是真实训练后的实现失败；ordinary续训、答案正确率和干净方法负结果未被建立，不是新来源确认或feedback-derived learning。Paper E 投稿包较成熟，渠道仍为条件建议，Owner尚未批准外部动作。送审为2027年10月，具体日未知。

| 用途 | 当前权威入口 |
|---|---|
| 当前方法实验 | [A回执](../research/word_scoring_new_family_20261027_v1/A_RETURN.md)、[C审阅](../research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md)、[D收尾](../research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md) |
| 修订算子诊断 | [REVISION_OPERATOR_RETURN](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_DIAGNOSTIC_RETURN.md)、[CONTROL](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V2_CONTROL_RESCORED.json)、[MECHANISM](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V3_MECHANISM.json) |
| Paper E 投稿路线 | [REVISION_NOTES_20261028](../research/word_scoring_new_family_20261027_v1/paper_e_word/D_REVISION_NOTES_20261028.md)、[SNCS_GUIDELINE_CHECK_20261028](../research/word_scoring_new_family_20261027_v1/paper_e_word/SNCS_GUIDELINE_CHECK_20261028.md)、[C_RESPONSE_20261028](../research/word_scoring_new_family_20261027_v1/paper_e_word/C_RESPONSE_AND_DISPOSITION_20261028.md)：SNCS条件主投；正文与技术包已达可交作者办理，图像分辨率/图内标题与声明占位仍开放 |
| 当前科研基线与三张实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[GOVERNANCE_RETURN](../research/research_baseline_governance_20261023/GOVERNANCE_RETURN.md) |
| 唯一现役指令 | [LOOP_D_RESEARCH_PROMPT](../docs/research/LOOP_D_RESEARCH_PROMPT.md)：D继续内部修图与渲染，29/29不追加派发；先Paper E、后纠正离线实验卡，无新科研生成 |
| 事后有效性复核 | [POST_B_REVIEW](../docs/governance/audit/loop_d_control_review/PHASE_B_POST_RETURN_REVIEW.md)：主计数复算、有效父模型/合同与语义边界；本轮0科研生成/训练 |
| 最新科研回执 | [D_LOOP_RETURN_20261028](../research/word_scoring_new_family_20261027_v1/D_LOOP_RETURN_20261028.md)、[C_PAPER_E_V2_REVIEW](../research/word_scoring_new_family_20261027_v1/audits/C_PAPER_E_V2_REVIEW.md)、[DTM_DECISION_CARD](../research/word_scoring_new_family_20261027_v1/DTM_DECISION_CARD_20261028.md) |
| 新对话交接 | [D_CLOSEOUT_RETURN § 新对话交接](../research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md)：最少必读、Git/工作区、预算与授权边界 |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 当前方法账本 | [DIAGNOSTIC_SUMMARY](../research/word_scoring_new_family_20261027_v1/scoring_v3/results/DIAGNOSTIC_SUMMARY.json)：27次预留、24条raw、46,054 input+output、0训练；本轮新增0生成，仅对既有raw做分词分段测量([DTM_SEGMENT_SPLIT](../research/word_scoring_new_family_20261027_v1/validation/DTM_SEGMENT_SPLIT_20261028.json)) |
| 历史聚合记账 | [RESOURCE_LEDGER](../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：历史阶段4,064 accounting attempts / 9,169,672 tokens，不含独立Phase B；B另记188物理生成、137,770—139,306生成tokens、2次训练/319,948训练tokens；340旧差额保留，不假称全局对账 |
| 历史 Portfolio 账本 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- C1 / Paper E：`REVISED_AND_C_DISPOSED / TEXT_READY_ARTWORK_OPEN`。上一轮C列的正文缺陷（六步、表格/列表融合、表图编号、书目/引文）已全部关闭并有确定性复现；本轮C在冻结快照上仍判 `CONDITIONAL`，剩余阻断只有图像分辨率与图内标题，另加声明占位。正文修改发生在C快照之后，未获独立复审。
- C2/C3新表族诊断：`OUTPUT_BUDGET_CONFOUNDING_QUANTIFIED / CAUSAL_EFFECT_UNIDENTIFIED`。旧24条分段支持严重预算混淆，不能分离合同长度的因果效应；D4/T1/M0是接口提取结果。实际unit字段和冻结语义仍需核验，旧卡已标待修；typed UNKNOWN冲突是静态缺陷，不归因为旧失败。未授权新生成。
- 以下 G2、G3 与旧第三研究点条目保留为历史边界和复用素材，不承担现役 C1/C2/C3 贡献身份。
- G2：`METHOD_INCREMENT_NOT_IDENTIFIED / STOP_CURRENT_MECHANISM`。v3 已绑定实际模块并拒绝审计反例；alias-aware static + repo/behavior 与 consumption + behavior 均 6/6。一个自然 Qwen 候选为等价正确实现，无新错误机制。
- G3：`SIMPLE_RULE_SUFFICIENT / COMPLEX_PLANNER_PAUSED`。六对象真实动作中多个 simple baseline 均 6/6；单次 wall-clock 不支持稳定成本排序。
- 第三研究点：`NARROW_TO_STAGE_SEPARATED_EVIDENCE_RELIABILITY`。scope 的 30 对 35 probe 节省已由 exact cache + miss revalidation 完全解释；scope 面板停止扩样。
- G2 状态到行动：`CONTINUE_RQ_U_DEVELOPMENT_ONLY / NO_METHOD_GAIN`。plain/decision fact 为 2/8 对 3/8、action 均 1/8；当前 action 分布是 `1/6/1` 对 `1/5/2`。现有 bundle 会丢新事实，不能据此证明正确状态无法迁移到行动。
- G3 增量补查：`KEEP_RQ_A_WITH_HEADROOM / NO_POLICY_CLAIM`。oracle 只证明目标定义下的覆盖/成本空间；depth-2 `5/43` 与同预算随机相容，不能称弱可学习信号；模型接口仍是 `UNEVALUATED_NO_VALID_DECISION`。
- C2反馈学习：`IMPLEMENTATION_STOPPED / ORDINARY_CONTINUATION_NOT_SATISFIED / METHOD_NOT_ESTABLISHED`。训练切换到新child而非保持父计算；E0合法patch、R25/36集合匹配与N26/36不构成干净方法比较，R36/36仅embedded解析。下一步见唯一指令，旧raw/报告保留。
- C3 可靠交付：`NEUTRAL_RETRY_STRONG_BASELINE / LOCALIZATION_REPAIR_STOPPED`。先前 V4/V5 error-pool 回放上 original 60/72、neutral retry 62/72、localization 59/72；定位修订修对 3 个、破坏 4 个。该面板 24/24 与旧 error pool 重合，不能作新 family 确认；透明门控与有界修复仅以 33-34 次弃答换取较低条件错误率。
- FinRank：`STOP_ON_CURRENT_PANEL`，不重开 H/K；当前负结果不否定经验复用的一般可能性。
- MA-CERD：资源 membership 基线不等于依赖边传播；selective escalation 未验证，完整动作集合 exact match 与动作可接受性须区分，见[更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)。
- Adaptive V3：当前 authored fixtures 上 greedy 已足够，two-step 无正向配对收益；RPC capability 边界不等于操作系统沙箱。
- CodeUpdateArena：修正执行器后开发集与新 families 均为有界负结果，不重复同一 prose-update 实验。
- VersiCode：结果只涉及语法与 API 名称，不证明行为正确或信息表示优劣。
- PyMigBench/外部迁移：NtripBrowser 与 Partridge 两个真实迁移均显示行为测试边界；Partridge 进一步暴露旧依赖回退和合法 alias 的不同错误。仍不证明 hybrid oracle 普遍充分，也不进入 Paper E 两案例主张。

## 运行与历史

本轮 Git 和离线治理不是生产运行检查；运行约束仍见 [CORE.md](CORE.md)。未核实的生产问题、外部发送和审批事项保留在 [THREADS.md](THREADS.md)，不随文档归档自动关闭。

以下为不含独立Phase B的历史阶段累计：4,064 个 accounting attempts、536 次 physical HTTP、316 次本地批量 generate、9,169,672 accounting tokens，其中 judge 113 次。总量已含训练token；本次事件复算少340，原聚合账不改、差额待核。累计 14 次 LoRA SFT、3,495,424 training tokens、3,117.78 GPU-seconds。本轮修订诊断新增 20 attempts、8,060 prompt tokens、952 actual non-padding completion tokens；一次 runner 故障发生在生成前，计 0 attempts。付费 API 和生产 Memory 写回仍为零。

原 THREADS 完整快照保留在 [memory/archive/THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)。2026-10-19 收口前状态见 [历史状态](../docs/archive/2026-10-19_memory_state_history.md)；更早快照仍为 `memory/archive/STATE_2026-09-22_pre_governance.md`。
