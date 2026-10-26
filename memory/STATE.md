# Current State

> Updated: 2026-10-26 | Scope: publication, thesis and bounded mechanism continuation
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

阶段B前提纠偏保留，旧R/E继续停止。新增6次A/C已完成：P1的5个ordinary frozen failures是4个真实模型语义错误+1个reference defect，gold-free规则修复4/4后残差为0；P2的507个table-text原题可复算前沿没有同时满足答案非劣与成本预算的challenger。最终`NO_GO_STOP_MODEL_STAGE`，未释放48-call探针、未训练、未确认。C终审另有两个未进入评分路径的matcher latent缺陷，只作为未来探针发布前阻断。

Phase A 复算确认：安全尾部适配后 copy 2/2、known edit 2/2；单位题没有可见 million/thousand 尺度，降为不可判定，唯一可修的引用题在 neutral/category/localization 下均 0/1。旧 generic adapter 的 `1)0→10` 语义污染反例已由 strict whole-JSON 和限定尾部规则阻止。详见 [Phase A 回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)与[复算](../research/feedback_delivery_continuation_20261025_v1/PHASE_A_RECOMPUTE_V1.json)。

此前 P0/A/C 负结果继续保留开发身份。Phase B 的R/E是真实训练后的实现失败；ordinary续训、答案正确率和干净方法负结果未被建立，不是新来源确认或feedback-derived learning。Paper E 投稿包较成熟，渠道仍为条件建议，Owner尚未批准外部动作。送审为2027年10月，具体日未知。

| 用途 | 当前权威入口 |
|---|---|
| 当前方法实验 | [PHASE_B_RETURN](../research/feedback_learning_phase_b_20261026_v1/PHASE_B_RETURN.md)、[B2B_ANALYSIS](../research/feedback_learning_phase_b_20261026_v1/b2b/B2B_DEVELOPMENT_ANALYSIS.json)、[C_AUDIT](../research/feedback_learning_phase_b_20261026_v1/audits/TASK_RESULT_C_B2B.json) |
| 修订算子诊断 | [REVISION_OPERATOR_RETURN](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_DIAGNOSTIC_RETURN.md)、[CONTROL](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V2_CONTROL_RESCORED.json)、[MECHANISM](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V3_MECHANISM.json) |
| Paper E 投稿路线 | [ROUTE_REASSESSMENT](../research/natural_error_evidence_cost_20261026_v1/paper_e/ROUTE_REASSESSMENT_20261026.md)：SNCS订阅条件主投，ICAART仅在截止前四项条件齐备时启用 |
| 当前科研基线与三张实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[GOVERNANCE_RETURN](../research/research_baseline_governance_20261023/GOVERNANCE_RETURN.md) |
| 唯一现役指令 | [LOOP_D_RESEARCH_PROMPT](../docs/research/LOOP_D_RESEARCH_PROMPT.md)：自然错误/取证成本阶段已执行并以no-go收口 |
| 事后有效性复核 | [POST_B_REVIEW](../docs/governance/audit/loop_d_control_review/PHASE_B_POST_RETURN_REVIEW.md)：主计数复算、有效父模型/合同与语义边界；本轮0科研生成/训练 |
| 最新科研回执 | [STAGE_RETURN](../research/natural_error_evidence_cost_20261026_v1/STAGE_RETURN.md)、[A_CLOSEOUT](../research/natural_error_evidence_cost_20261026_v1/a_closeout/A_CLOSEOUT_RESULT.json)、[C_FINAL](../research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_FINAL.json) |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 当前聚合记账 | [RESOURCE_LEDGER](../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：历史阶段4,064 accounting attempts / 9,169,672 tokens，不含独立Phase B；B另记188物理生成、137,770—139,306生成tokens、2次训练/319,948训练tokens；340旧差额保留，不假称全局对账 |
| 历史 Portfolio 账本 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- C1 / Paper E：`NARROW_AND_CONTINUE / PACKAGE_AUDIT_PASS`。唯一主稿维持两案例；12 页 ICAART PDF、24/24 引用、目标包审计与私有 artifact 完整性均通过。投稿路线须Owner确认；渠道建议不等于最终批准，正式动作前按官方重新核验。
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
