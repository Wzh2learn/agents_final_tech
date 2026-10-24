# Current State

> Updated: 2026-10-24 | Scope: publication, thesis and bounded mechanism continuation
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

2026-10-24 已完成首轮审计定点更正和自然 TAT-QA 真实训练比较。旧 tool-paired 指标已拆分，隐藏参考已从部署特征移除，任务单位和聚合收据已追加版本化更正。自然任务上普通 answer/execution SFT 是强基线；visible-program filter 显著更差，所有模型的相关变化适配均为 0。当前残余是等值别名导致的证据绑定错误，而不是格式或计算器执行本身。详见 [CORRECTION_RETURN](../research/feedback_learning_finance_20261024_v2/CORRECTION_RETURN.md) 与 [NATURAL_METHOD_RETURN](../research/natural_program_learning_20261024_v2/NATURAL_METHOD_RETURN.md)。

| 用途 | 当前权威入口 |
|---|---|
| 当前方法实验 | [CORRECTION_RETURN](../research/feedback_learning_finance_20261024_v2/CORRECTION_RETURN.md)、[NATURAL_METHOD_RETURN](../research/natural_program_learning_20261024_v2/NATURAL_METHOD_RETURN.md)、[ARM_COMPARISON](../research/natural_program_learning_20261024_v2/ARM_COMPARISON_V2.json) |
| 当前科研基线与三张实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[GOVERNANCE_RETURN](../research/research_baseline_governance_20261023/GOVERNANCE_RETURN.md) |
| 新阶段方向与授权衔接 | [四项 Goals v2](../docs/research/LOOP_D_PUBLICATION_AND_THESIS_GOALS_V2_20261022.md)；当前为部分完成，G2 停止、G3 暂停、第三贡献进入有界开发 |
| 当前回执 | [V5 RESEARCH_SPRINT_RETURN](../research/publication_thesis_goals_v1/revision_v5/RESEARCH_SPRINT_RETURN.md)；V4/V3/V2 回执为前序证据 |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 当前聚合记账 | [RESOURCE_LEDGER](../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：当前 Goal 2,412 attempts / 6,204,757 tokens；训练 token 单列 1,496,816 |
| 历史 Portfolio 账本 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- Paper E：`NARROW_AND_CONTINUE / INTERNAL_PACKAGE_READY`。唯一主稿维持两案例；9pt、11页 PDF、目标包审计、私有 artifact 与 GB10 clean reproduction 均完成，外部投稿动作待 Owner。
- G2：`METHOD_INCREMENT_NOT_IDENTIFIED / STOP_CURRENT_MECHANISM`。v3 已绑定实际模块并拒绝审计反例；alias-aware static + repo/behavior 与 consumption + behavior 均 6/6。一个自然 Qwen 候选为等价正确实现，无新错误机制。
- G3：`SIMPLE_RULE_SUFFICIENT / COMPLEX_PLANNER_PAUSED`。六对象真实动作中多个 simple baseline 均 6/6；单次 wall-clock 不支持稳定成本排序。
- 第三研究点：`NARROW_TO_STAGE_SEPARATED_EVIDENCE_RELIABILITY`。scope 的 30 对 35 probe 节省已由 exact cache + miss revalidation 完全解释；scope 面板停止扩样。
- G2 状态到行动：`CONTINUE_RQ_U_DEVELOPMENT_ONLY / NO_METHOD_GAIN`。plain/decision fact 为 2/8 对 3/8、action 均 1/8；当前 action 分布是 `1/6/1` 对 `1/5/2`。现有 bundle 会丢新事实，不能据此证明正确状态无法迁移到行动。
- G3 增量补查：`KEEP_RQ_A_WITH_HEADROOM / NO_POLICY_CLAIM`。oracle 只证明目标定义下的覆盖/成本空间；depth-2 `5/43` 与同预算随机相容，不能称弱可学习信号；模型接口仍是 `UNEVALUATED_NO_VALID_DECISION`。
- C2 反馈学习：`ORDINARY_SFT_STRONG_BASELINE / VISIBLE_FILTER_STOPPED`。自然任务上普通 answer/execution SFT 原题正确率 test 75.0%、external 79.2%；visible filter 为 54.2%/54.2%。相关变化适配均为 0，下一步只测试能区分等值别名的反馈。
- C3 可靠交付：`SIMPLE_DEPLOYMENT_RULE_SUFFICIENT_ON_CURRENT_OUTPUTS`。固定计算器和部署可见检查已经可运行；普通 SFT test 错误交付条件率 50.0%、external 46.5%，logistic policy 与强规则完全相同，停止复杂策略扩展。
- FinRank：`STOP_ON_CURRENT_PANEL`，不重开 H/K；当前负结果不否定经验复用的一般可能性。
- MA-CERD：资源 membership 基线不等于依赖边传播；selective escalation 未验证，完整动作集合 exact match 与动作可接受性须区分，见[更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)。
- Adaptive V3：当前 authored fixtures 上 greedy 已足够，two-step 无正向配对收益；RPC capability 边界不等于操作系统沙箱。
- CodeUpdateArena：修正执行器后开发集与新 families 均为有界负结果，不重复同一 prose-update 实验。
- VersiCode：结果只涉及语法与 API 名称，不证明行为正确或信息表示优劣。
- PyMigBench/外部迁移：NtripBrowser 与 Partridge 两个真实迁移均显示行为测试边界；Partridge 进一步暴露旧依赖回退和合法 alias 的不同错误。仍不证明 hybrid oracle 普遍充分，也不进入 Paper E 两案例主张。

## 运行与历史

本轮 Git 和离线治理不是生产运行检查；运行约束仍见 [CORE.md](CORE.md)。未核实的生产问题、外部发送和审批事项保留在 [THREADS.md](THREADS.md)，不随文档归档自动关闭。

当前 Goal 累计 2,412 个 accounting attempts、536 次 physical HTTP、183 次本地批量 generate、6,204,757 accounting tokens，其中 judge 113 次。累计 8 次 LoRA SFT、1,496,816 training tokens、1,350.38 GPU-seconds。付费 API 和生产 Memory 写回仍为零。两次中断评价分别按 128 attempts / 58,743 tokens 和 288 attempts / 275,581 tokens 上界保守入账；自然阶段的本地 1.2M 规划未计入训练与中断上界，实际阶段上界为 1,610,394 tokens，但未突破全局授权。

原 THREADS 完整快照保留在 [memory/archive/THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)。2026-10-19 收口前状态见 [历史状态](../docs/archive/2026-10-19_memory_state_history.md)；更早快照仍为 `memory/archive/STATE_2026-09-22_pre_governance.md`。
