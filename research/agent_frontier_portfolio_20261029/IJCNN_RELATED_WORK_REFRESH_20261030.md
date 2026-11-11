# 第二篇：近邻、重合与实验判别

> 2026-11-11。D定向读原文，未复现原法。活表只留近期参照；上版完整表固定在`faa3a12b`的本文件Git blob，更早大表在`747eac14`，按需恢复。

## 当前裁决

**尚无已验证新方法，Goal active。**AMV-Guard、ERRAND与ATR直接覆盖通用预算复验/行动范围；联合行动选择亦有经典决策参照。下一只审“复验后的实际Agent接续价值”能否产生机制增量，见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 最直接的方法近邻

| 工作 | 原文已核机制 / 阅读范围 | 对本项目的约束 |
|---|---|---|
| [AMV-Guard](https://arxiv.org/html/2610.31446v1) | §2.3–3.3/4/F：前提提取、校准、单步VOI及两步补充；外层重规划共用预算。 | 行动条件化复验已覆盖；Gate终端为Proceed/Abstain。匿名源码读取403，未复现。 |
| [ERRAND](https://arxiv.org/html/2609.29545v1) | §3.1–3.4/B.3/E.6/9：漂移信念、单峰VOI、工资门、就近批检和免费回执。 | 预算定价/多级取证不新；论文声明匿名补充包，未获其实现。 |
| [ATR](https://arxiv.org/html/2609.08015v1) | §2–4/算法1：类型前提、变更反向索引、四响应、目标CAS。 | 版本变化不等于决策失效已有原型；开发者编写验证器，非真实LLM评测。 |
| [StateWise](https://arxiv.org/html/2610.05241v1) | §3、4.2–4.4：记录干预定位前提，证据绑定作用域，持久修复并重规划。 | 前提/范围绑定已有直接近邻。 |
| [StateGraph](https://arxiv.org/html/2611.02912) | §3–4.5/算法1：支持依赖、反事实核验、强弱关系与替代支持下的保守撤回及行动约束。 | 图传播、局部撤回和不确定状态不新；共享前提须检验执行增量。 |
| [CounterMem](https://arxiv.org/html/2609.31874v1) | §3.2–3.3：≤4个具体局部编辑，同状态执行验证；跨任务选择复用/跳过。 | 用具体动作替换宽泛标签仍须超过其机制。 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | §3.1–3.4：可执行原子/技能接口，同前缀换粒度分支，结果差提供训练奖励。 | 可执行粒度与反事实分支已有先例，不等于原因表探针选择。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 同状态WITH/WITHOUT结果，条件边际效用及Load/Abstain。 | 配对干预与选择性复用已有近邻。 |
| [OMCE](https://arxiv.org/html/2611.01747v1) | 上下文bandit基于反馈学习经验形式路由与重试。 | 学习型经验路由不能改名为预算选择贡献。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | 轨迹诊断、保留有效部分、局部修订、执行效用接受门。 | 须超出该流程及普通改写。 |
| [Skill-V](https://arxiv.org/html/2610.11781v1) | §3合同初始化及附录A/B：交互史提出可观察条件，版本化更新、回放非回归门；历史标签可过期。 | 自动提出可执行条件及反馈修订也已有近邻。 |
| [CL-Bench](https://arxiv.org/html/2606.05661v1) | §3.1/4/附录A.4及代码5f8c50eb、两官方DB；[本项目原生helper控制](results/CODE_SOURCE_CORRECTIONS.md#clbench-budget-screen)。 | 非完整复现；当前迁移有通知、schema一查询、1%容差接受Q101旧绑定，不能凭事实变化生成失败标签。 |
| [EFC](https://arxiv.org/html/2605.29682) | 分析反馈有效性、信息、冗余与后续决策保留。 | 反馈链分解仅作诊断，须有真实任务增益。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已核范围 / 实验约束 |
|---|---|
| [Teaching Agents to Code Reliably](https://arxiv.org/html/2610.03984) | §2.1–2.3：补丁/回退差分执行、覆盖与变体区分。复现优先须是强基线；提示基线不称完整TACR。 |
| [Bayesian Control for Coding Agents](https://aclanthology.org/2026.emnlp-main.1548/) | §3–5/A.6：正确性后验与成本驱动取证、修复、验证、停止；状态含预算和已查询critic。成本敏感取证本身不新。 |
| [VeriHarness](https://arxiv.org/abs/2607.14167) | 仅核摘要：原始反馈与位置/观测值/替代项，含prose/JSON对照。须排除额外信息与呈现收益。 |

## 其他近邻索引

上述旧blob保留VBL、BiPACE、Grounding/SkillGLoW、Budgeted Verification、CodeT、ErrorProbe、CBC及更早近邻；其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。不在活表不代表失效。

## 对本项目实验的直接约束

1. 反馈可靠性、送达、采纳与能力分开；通用流程不是新机制。
2. 统一任务、信息、工具与总预算，保留普通历史、状态规则、全重验及最近邻。
3. 预算择证须面对新鲜度/约束/直接重读及AMV、ERRAND；若学接续价值，须补条件化价值强基线，不能只换大网络或加数据。
4. 独立原生评分，形成/整理/取证/执行全成本；自写测试、AI检查、模式合法均不作任务成功。
5. 当前状态和授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)及[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
