# Current State

> Updated: 2026-10-22 | Scope: four-goal continuation after owner audit
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

四项 Goals v2 已推进到本次研究冲刺证据出口：Paper E 实际 ICAART 包修复并内部就绪；G2 在新真实 Partridge 迁移上取得行为测试盲区与等价实现误拒证据；G3 接入真实 pytest/wall-clock 后支持简单固定规则、停止复杂策略候选；G4 五份现役文件已衔接。详见 [V2 SPRINT_RETURN](../research/publication_thesis_goals_v1/revision_v2/SPRINT_RETURN.md)。

| 用途 | 当前权威入口 |
|---|---|
| 新阶段方向与授权衔接 | [四项 Goals v2](../docs/research/LOOP_D_PUBLICATION_AND_THESIS_GOALS_V2_20261022.md)；有限真实研究冲刺已到证据出口，G2/G3 仍为候选 |
| 当前回执与独立审计 | [V2 SPRINT_RETURN](../research/publication_thesis_goals_v1/revision_v2/SPRINT_RETURN.md)、[Owner 独立审计](../research/publication_thesis_goals_v1/OWNER_INDEPENDENT_AUDIT_20261022.md)；[首轮 GOAL_RETURN](../research/publication_thesis_goals_v1/GOAL_RETURN.md) 为历史 |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 最新科研回执 | [Portfolio V2 GOAL_RETURN](../research/research_portfolio_v2/GOAL_RETURN.md)；成本为当时快照 |
| 当前聚合记账 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；含失败调用补记，历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- Paper E：`NARROW_AND_CONTINUE / INTERNAL_PACKAGE_READY`。唯一主稿维持两案例；9pt、11页 PDF、目标包审计、私有 artifact 与 GB10 clean reproduction 均完成，外部投稿动作待 Owner。
- G2：`CONTINUE_NARROWED_CANDIDATE`。Partridge parent/gold 与两个真实仓库控制已执行；行为-only 会误放行旧依赖回退，literal static 会误拒 alias，结果消费 + 行为是当前简单充分规则。
- G3：`SIMPLE_FIXED_RULE_SUFFICIENT / COMPLEX_POLICY_STOP_FOR_NOW`。四对象真实成本中 runtime+行为 4/4、约7.26秒；不支持学习型或复杂自适应 planner。G2/G3均未成立学位创新。
- FinRank：`STOP_ON_CURRENT_PANEL`，不重开 H/K；当前负结果不否定经验复用的一般可能性。
- MA-CERD：资源 membership 基线不等于依赖边传播；selective escalation 未验证，完整动作集合 exact match 与动作可接受性须区分，见[更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)。
- Adaptive V3：当前 authored fixtures 上 greedy 已足够，two-step 无正向配对收益；RPC capability 边界不等于操作系统沙箱。
- CodeUpdateArena：修正执行器后开发集与新 families 均为有界负结果，不重复同一 prose-update 实验。
- VersiCode：结果只涉及语法与 API 名称，不证明行为正确或信息表示优劣。
- PyMigBench/外部迁移：NtripBrowser 与 Partridge 两个真实迁移均显示行为测试边界；Partridge 进一步暴露旧依赖回退和合法 alias 的不同错误。仍不证明 hybrid oracle 普遍充分，也不进入 Paper E 两案例主张。

## 运行与历史

本轮 Git 和离线治理不是生产运行检查；运行约束仍见 [CORE.md](CORE.md)。未核实的生产问题、外部发送和审批事项保留在 [THREADS.md](THREADS.md)，不随文档归档自动关闭。

V2 本轮模型、judge、训练调用为零；官方模板、公开源、确定性 verifier 和真实 pytest 在离线/GB10 执行。历史模型账本继续独立保留。

原 THREADS 完整快照保留在 [memory/archive/THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)。2026-10-19 收口前状态见 [历史状态](../docs/archive/2026-10-19_memory_state_history.md)；更早快照仍为 `memory/archive/STATE_2026-09-22_pre_governance.md`。
