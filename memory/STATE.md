# Current State

> Updated: 2026-10-22 | Scope: four-goal continuation after owner audit
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

V2 复核后的有限修补和科研判断已完成：Paper E 恢复全精度计算并形成可投包；G2 完成 actual-module/配对因果/三态修复，但 simple strong baseline 与消费方法均 6/6，当前机制停止扩展；G3 复杂 planner 暂停；第三贡献仅透明证据失效候选继续，scope 方法暂停。G4 已同步中文正文、导师一页稿和现役入口。详见 [V2 SPRINT_RETURN](../research/publication_thesis_goals_v1/revision_v2/SPRINT_RETURN.md)。

| 用途 | 当前权威入口 |
|---|---|
| 新阶段方向与授权衔接 | [四项 Goals v2](../docs/research/LOOP_D_PUBLICATION_AND_THESIS_GOALS_V2_20261022.md)；当前为部分完成，G2 停止、G3 暂停、第三贡献待正交资格 |
| 当前回执与独立审计 | [V2 SPRINT_RETURN](../research/publication_thesis_goals_v1/revision_v2/SPRINT_RETURN.md)、[Owner 独立审计](../research/publication_thesis_goals_v1/OWNER_INDEPENDENT_AUDIT_20261022.md)；[首轮 GOAL_RETURN](../research/publication_thesis_goals_v1/GOAL_RETURN.md) 为历史 |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 最新科研回执 | [Portfolio V2 GOAL_RETURN](../research/research_portfolio_v2/GOAL_RETURN.md)；成本为当时快照 |
| 当前聚合记账 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；含失败调用补记，历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- Paper E：`NARROW_AND_CONTINUE / INTERNAL_PACKAGE_READY`。唯一主稿维持两案例；9pt、11页 PDF、目标包审计、私有 artifact 与 GB10 clean reproduction 均完成，外部投稿动作待 Owner。
- G2：`METHOD_INCREMENT_NOT_IDENTIFIED / STOP_CURRENT_MECHANISM`。v3 已绑定实际模块并拒绝审计反例；alias-aware static + repo/behavior 与 consumption + behavior 均 6/6。一个自然 Qwen 候选为等价正确实现，无新错误机制。
- G3：`SIMPLE_RULE_SUFFICIENT / COMPLEX_PLANNER_PAUSED`。六对象真实动作中多个 simple baseline 均 6/6；单次 wall-clock 不支持稳定成本排序。
- 第三贡献：`TRANSPARENT_INVALIDATION_CONTINUE / SCOPE_METHOD_PAUSED`。全局证据复用有 2/5 误迁移，但 dependency-change invalidation 已 5/5；等待 dependency 不变、input regime 改变的正交案例。
- FinRank：`STOP_ON_CURRENT_PANEL`，不重开 H/K；当前负结果不否定经验复用的一般可能性。
- MA-CERD：资源 membership 基线不等于依赖边传播；selective escalation 未验证，完整动作集合 exact match 与动作可接受性须区分，见[更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)。
- Adaptive V3：当前 authored fixtures 上 greedy 已足够，two-step 无正向配对收益；RPC capability 边界不等于操作系统沙箱。
- CodeUpdateArena：修正执行器后开发集与新 families 均为有界负结果，不重复同一 prose-update 实验。
- VersiCode：结果只涉及语法与 API 名称，不证明行为正确或信息表示优劣。
- PyMigBench/外部迁移：NtripBrowser 与 Partridge 两个真实迁移均显示行为测试边界；Partridge 进一步暴露旧依赖回退和合法 alias 的不同错误。仍不证明 hybrid oracle 普遍充分，也不进入 Paper E 两案例主张。

## 运行与历史

本轮 Git 和离线治理不是生产运行检查；运行约束仍见 [CORE.md](CORE.md)。未核实的生产问题、外部发送和审批事项保留在 [THREADS.md](THREADS.md)，不随文档归档自动关闭。

V2 当前累计新增 1 个自然模型请求、1 次 physical HTTP、1,849 accounting tokens；judge、训练、付费 API 和生产 Memory 写回均为零。历史模型账本继续独立保留。

原 THREADS 完整快照保留在 [memory/archive/THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)。2026-10-19 收口前状态见 [历史状态](../docs/archive/2026-10-19_memory_state_history.md)；更早快照仍为 `memory/archive/STATE_2026-09-22_pre_governance.md`。
