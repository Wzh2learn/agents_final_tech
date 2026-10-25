# Current State

> Updated: 2026-10-25 | Scope: publication, thesis and bounded mechanism continuation
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

2026-10-25 完成 P0 合同修正、同一候选反馈干预、oracle-assisted 机制诊断、24-family 固定模型交付回放和 Paper E 路由适配。可见定位/执行反馈均未修复开发面板的 16 个原错；普通中性重答在先前 V4/V5 error-pool 回放上为 62/72，优于原始 60/72 和定位修订 59/72。独立复核确认这 24 个任务全部与旧 error pool 重合，故不是新 family 确认。当前 O/R/E 因缺少反馈衍生且训练合格的纠正监督未训练。Paper E 为 ICAART 条件主投、SN Computer Science 顺序备投，送审按 2027 年 10 月倒排。详见 [本轮研究回执](../research/feedback_delivery_continuation_20261025_v1/RESEARCH_RETURN_20261025.md)。

| 用途 | 当前权威入口 |
|---|---|
| 当前方法实验 | [RESEARCH_RETURN_20261025](../research/feedback_delivery_continuation_20261025_v1/RESEARCH_RETURN_20261025.md)、[EXPERIMENT_A](../research/feedback_delivery_continuation_20261025_v1/SAME_CANDIDATE_FEEDBACK_A_FINAL.json)、[REPLAY_C](../research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json) |
| Paper E 投稿路线 | [PAPER_E_ROUTE_ADAPTATION](../research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_20261025.md)：ICAART 条件主投、SN Computer Science 顺序备投 |
| 当前科研基线与三张实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[GOVERNANCE_RETURN](../research/research_baseline_governance_20261023/GOVERNANCE_RETURN.md) |
| 新阶段方向与授权衔接 | [四项 Goals v2](../docs/research/LOOP_D_PUBLICATION_AND_THESIS_GOALS_V2_20261022.md)；当前为部分完成，G2 停止、G3 暂停、第三贡献进入有界开发 |
| 当前回执 | [RESEARCH_RETURN_20261025](../research/feedback_delivery_continuation_20261025_v1/RESEARCH_RETURN_20261025.md)；V5/V4/V3 回执为前序证据 |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 当前聚合记账 | [RESOURCE_LEDGER](../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：当前 Goal 4,044 attempts / 9,160,660 tokens；训练 token 单列 3,495,424 |
| 历史 Portfolio 账本 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- C1 / Paper E：`NARROW_AND_CONTINUE / PACKAGE_AUDIT_PASS`。唯一主稿维持两案例；12 页 ICAART PDF、24/24 引用、目标包审计与私有 artifact 完整性均通过。主投只在 2026-10-29 前授权、宣读/差旅与学校认可三个条件成立时使用。
- 以下 G2、G3 与旧第三研究点条目保留为历史边界和复用素材，不承担现役 C1/C2/C3 贡献身份。
- G2：`METHOD_INCREMENT_NOT_IDENTIFIED / STOP_CURRENT_MECHANISM`。v3 已绑定实际模块并拒绝审计反例；alias-aware static + repo/behavior 与 consumption + behavior 均 6/6。一个自然 Qwen 候选为等价正确实现，无新错误机制。
- G3：`SIMPLE_RULE_SUFFICIENT / COMPLEX_PLANNER_PAUSED`。六对象真实动作中多个 simple baseline 均 6/6；单次 wall-clock 不支持稳定成本排序。
- 第三研究点：`NARROW_TO_STAGE_SEPARATED_EVIDENCE_RELIABILITY`。scope 的 30 对 35 probe 节省已由 exact cache + miss revalidation 完全解释；scope 面板停止扩样。
- G2 状态到行动：`CONTINUE_RQ_U_DEVELOPMENT_ONLY / NO_METHOD_GAIN`。plain/decision fact 为 2/8 对 3/8、action 均 1/8；当前 action 分布是 `1/6/1` 对 `1/5/2`。现有 bundle 会丢新事实，不能据此证明正确状态无法迁移到行动。
- G3 增量补查：`KEEP_RQ_A_WITH_HEADROOM / NO_POLICY_CLAIM`。oracle 只证明目标定义下的覆盖/成本空间；depth-2 `5/43` 与同预算随机相容，不能称弱可学习信号；模型接口仍是 `UNEVALUATED_NO_VALID_DECISION`。
- C2 反馈学习：`VISIBLE_REPAIR_STOPPED / OE_NOT_TRAINED`。开发面板中 ordinary/neutral 56/72，localization 49/72、execution 40/72，三者 `wrong_to_correct=0`；oracle 类别可修 3/16，但破坏 54 个原对且格式完成率仅 13/72。无反馈衍生且训练合格的纠正监督，不把答案重加权命名为反馈学习。
- C3 可靠交付：`NEUTRAL_RETRY_STRONG_BASELINE / LOCALIZATION_REPAIR_STOPPED`。先前 V4/V5 error-pool 回放上 original 60/72、neutral retry 62/72、localization 59/72；定位修订修对 3 个、破坏 4 个。该面板 24/24 与旧 error pool 重合，不能作新 family 确认；透明门控与有界修复仅以 33-34 次弃答换取较低条件错误率。
- FinRank：`STOP_ON_CURRENT_PANEL`，不重开 H/K；当前负结果不否定经验复用的一般可能性。
- MA-CERD：资源 membership 基线不等于依赖边传播；selective escalation 未验证，完整动作集合 exact match 与动作可接受性须区分，见[更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)。
- Adaptive V3：当前 authored fixtures 上 greedy 已足够，two-step 无正向配对收益；RPC capability 边界不等于操作系统沙箱。
- CodeUpdateArena：修正执行器后开发集与新 families 均为有界负结果，不重复同一 prose-update 实验。
- VersiCode：结果只涉及语法与 API 名称，不证明行为正确或信息表示优劣。
- PyMigBench/外部迁移：NtripBrowser 与 Partridge 两个真实迁移均显示行为测试边界；Partridge 进一步暴露旧依赖回退和合法 alias 的不同错误。仍不证明 hybrid oracle 普遍充分，也不进入 Paper E 两案例主张。

## 运行与历史

本轮 Git 和离线治理不是生产运行检查；运行约束仍见 [CORE.md](CORE.md)。未核实的生产问题、外部发送和审批事项保留在 [THREADS.md](THREADS.md)，不随文档归档自动关闭。

当前 Goal 累计 3,396 个 accounting attempts、536 次 physical HTTP、251 次本地批量 generate、8,707,353 accounting tokens，其中 judge 113 次。累计 14 次 LoRA SFT、3,495,424 training tokens、3,117.78 GPU-seconds。V4/V5 新增 624 attempts、313,796 generation tokens、1,026,672 training tokens；语义检查与修复回放均为 0 模型请求。付费 API 和生产 Memory 写回仍为零。

原 THREADS 完整快照保留在 [memory/archive/THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)。2026-10-19 收口前状态见 [历史状态](../docs/archive/2026-10-19_memory_state_history.md)；更早快照仍为 `memory/archive/STATE_2026-09-22_pre_governance.md`。
