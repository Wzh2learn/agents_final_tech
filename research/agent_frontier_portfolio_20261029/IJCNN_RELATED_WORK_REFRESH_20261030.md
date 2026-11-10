# 第二篇：近邻、重合与实验判别

> 2026-11-11。D定向读原文/公开工件，未复现原法。当前仅载入支配下一决策的近邻；完整旧表可用 `git show 747eac14:research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md` 按需恢复。

## 当前裁决

**尚无已验证新方法，Goal active。**VBL进一步覆盖通用前提恢复流程；预算择证只是待验证问题，不预认创新。当前结果与下一门见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 最直接的方法近邻

| 工作 | 原文已核机制 / 阅读范围 | 对本项目的约束 |
|---|---|---|
| [VBL](https://arxiv.org/html/2610.41564v1) | 11-11读§2、3.1–3.4/算法1：目标相关性与可执行性核验、失败分类、Push/Pop/重试/回溯；外部进度不回滚。 | 通用FCDR流程不能单作贡献；原法限单episode，不将其误称跨任务记忆学习。 |
| [StateWise](https://arxiv.org/html/2610.05241v1) | §3、4.2–4.4：记录干预定位前提，证据绑定作用域，持久修复并重规划。 | 前提/范围绑定已有直接近邻。 |
| [StateGraph](https://arxiv.org/html/2611.02912) | §3–4.5/算法1：支持依赖、反事实核验、强弱关系与替代支持下的保守撤回及行动约束。 | 图传播、局部撤回和不确定状态不新；共享前提须检验执行增量。 |
| [CounterMem](https://arxiv.org/html/2609.31874v1) | §3.2–3.3：≤4个具体局部编辑，同状态执行验证；跨任务选择复用/跳过。 | 用具体动作替换宽泛标签仍须超过其机制。 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | §3.1–3.4：可执行原子/技能接口，同前缀换粒度分支，结果差提供训练奖励。 | 可执行粒度与反事实分支已有先例，不等于原因表探针选择。 |
| [BiPACE](https://arxiv.org/html/2606.25556) | 11-11读§3.1–3.5：actor隐状态分组、同动作同伴估计Q−V，改变RL优势估计。 | 状态/动作分组与信用分配已有研究；不是自然语言原因表，未在本项目训练。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 同状态WITH/WITHOUT结果，条件边际效用及Load/Abstain。 | 配对干预与选择性复用已有近邻。 |
| [OMCE](https://arxiv.org/html/2611.01747v1) | 上下文bandit基于反馈学习经验形式路由与重试。 | 学习型经验路由不能改名为预算选择贡献。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | 轨迹诊断、保留有效部分、局部修订、执行效用接受门。 | 须超出该流程及普通改写。 |
| [Skill-V](https://arxiv.org/html/2610.11781v1) | 附录A/B.5–B.7：条件化回放非回归门；作者明确规则变化可使历史标签过期。 | 不能将原法简化为无条件遵守旧反馈。 |
| [Grounding Agent Memory](https://arxiv.org/html/2609.11060) | 11-11读§3.1–3.3/4：任务后只读环境propose–probe–commit，验证范围与漂移；任务/整理成本分报。 | 环境取证后写记忆不新；比较须计整理与使用总成本，不说原法未记整理费用。 |
| [Budgeted Verification](https://arxiv.org/html/2608.25553v1) | 11-11读§2–3/6及附录B；强制关键路径为oracle，非调度器。另核[OSF](https://osf.io/axsnm/)三包，未执行作者代码。 | Exp B为公开的前瞻设计，不能当已执行结果；其日期结构下最近两个活跃源覆盖关键路径，仅为分配覆盖筛查，非决策成功。 |
| [EFC](https://arxiv.org/html/2605.29682) | 分析反馈有效性、信息、冗余与后续决策保留。 | 反馈链分解仅作诊断，须有真实任务增益。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已核范围 / 实验约束 |
|---|---|
| [Teaching Agents to Code Reliably](https://arxiv.org/html/2610.03984) | §2.1–2.3：补丁/回退差分执行、覆盖与变体区分。复现优先须是强基线；提示基线不称完整TACR。 |
| [CodeT](https://arxiv.org/abs/2207.10397) | 仅核摘要：生成测试与多程序执行一致性选择。多候选×探针矩阵已有先例。 |
| [ErrorProbe](https://arxiv.org/html/2604.17658) | §4.3–4.4：执行核验错误假设，验证后写记忆；主要评估错误归因。假设＋探针＋记忆不新。 |
| [Contract Before Code](https://aclanthology.org/2026.realm-1.72/) | §2.3–4：失败编译为适用条件、探针及计划后果。探针＋前提检查已有近邻。 |
| [Bayesian Control for Coding Agents](https://aclanthology.org/2026.emnlp-main.1548/) | §3–5/A.6：正确性后验与成本驱动取证、修复、验证、停止；状态含预算和已查询critic。成本敏感取证本身不新。 |
| [VeriHarness](https://arxiv.org/abs/2607.14167) | 仅核摘要：原始反馈与位置/观测值/替代项，含prose/JSON对照。须排除额外信息与呈现收益。 |

## 其他近邻索引

上述固定旧表保留EvoMem/EvoArena、Repo2Skill-Evo、Recuris、VCE-Skill、EmbodiSkill、RADEG、STALE、ContinualSkillBench、OMCE、MemScope、AgentLoop及oracle审计的原文链接与已核范围；其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。未列入本页不代表失效或与本项目无关。

## 对本项目实验的直接约束

1. 反馈可靠性、送达、采纳与能力分开；通用流程不是新机制。
2. 统一任务、信息、工具与总预算，保留普通历史、状态规则、全重验及最近邻。
3. 预算择证须面对新鲜度优先、约束优先与直接重读基线，不能向候选暴露关键源标签。
4. 独立原生评分，形成/整理/取证/执行全成本；自写测试、AI检查、模式合法均不作任务成功。
5. 当前状态和授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)及[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
