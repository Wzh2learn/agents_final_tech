# 第二篇：近邻、重合与实验判别

> 更新：2026-11-10。以下用于界定研究空间；读论文不等于复现。新近论文按一手原文核查，具体代码、数据及全部结果未独立复现。历史检索与长笔记见[研究归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。

## 当前裁决

**尚无通过新颖性门的方法。**经验局部修订、进度控制和外部状态验收均有直接近邻；换版本场景、经验格式或评测指标不构成新方法。暂停这些候选的模型实验。重开前须给出与近邻动作不同的具体轨迹、可核验结果、未曝光独立任务及超过强规则的可证伪预测。

## 最直接的方法近邻

| 工作 | 已覆盖的机制（依原文） | 对本项目的约束 |
|---|---|---|
| [StateWise](https://arxiv.org/html/2610.05241) | 记录级反事实定位、有效性核验、带来源的局部修复、修复后行动检查；150例及跨配置评估。 | 行动归因＋核验＋局部更新已重合；成绩未复现。 |
| [EvoMem / EvoArena](https://arxiv.org/html/2606.13681) | 终端、软件及偏好变化任务；补丁式记忆演化，并测下游任务链表现。 | 版本化记忆、变化场景和下游成绩均已有先例。 |
| [Repo2Skill-Evo](https://arxiv.org/html/2608.21964) | 57个仓库、105次发布转换中的仓库技能维护。 | 真实发布迁移本身不新，须有独立算法差异。 |
| [Recuris](https://arxiv.org/abs/2608.24876) | 进度记忆、轨迹定位、局部修补、留出门控及失败后适配。匹配4次尝试比较53/87对51/87，p=0.774。 | 隔离适配与重试收益；机制和成绩均未复现。 |
| [VCE-Skill](https://arxiv.org/abs/2608.16544) | 从公开技能版本差异提炼经验，并与当前轨迹的更新提案融合。 | “从版本变化中学更新经验”不能单独作为方法。 |
| [CounterMem](https://arxiv.org/html/2609.31874v1) | 同状态反事实动作和适用条件记忆；学习使用/跳过并测有害误用。 | 配对执行和适用性选择已覆盖。 |
| [OMCE](https://arxiv.org/html/2611.01747v1) | 用上下文 bandit 基于反馈更新经验路由，并支持失败后重试。 | 在线反馈路由不是空白。 |
| [MemScope](https://arxiv.org/html/2610.21170) | 联合检查轨迹、运行时记忆和 provider 代码，定位并局部修改，再验证恢复/回归。 | 反馈定位＋局部修改＋验证已覆盖。 |
| [AgentLoop](https://arxiv.org/html/2609.33315) | 根据需求槽、证据和相邻轮稳定/低收益信号，决定继续、整合或停止。 | 通用进展/停滞控制已覆盖。 |
| [TAM](https://arxiv.org/html/2610.37482)、[SkillShift](https://arxiv.org/html/2610.33528) | TAM保存已验证进度/局部操作供后续任务复用；SkillShift按环境可行性重排固定技能。 | 保留进度或变化时调整动作本身不是新贡献。 |
| [CORAL](https://arxiv.org/abs/2610.40350)、[Context compression](https://arxiv.org/abs/2609.29875)、[AgentRewind](https://arxiv.org/abs/2608.14380) | 分别研究经核实进度上的新推理episode、交互历史压缩、上下文与环境状态对齐恢复。 | ALFWorld新会话/轨迹投影观察不能单独证明新颖性。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已覆盖 / 实验启示 |
|---|---|
| [ExecCritic](https://arxiv.org/abs/2609.09133) | 独立生成并冻结测试后再修复；区分测试质量与修复效果。 |
| [Auditing Feedback-Driven Evolution](https://arxiv.org/abs/2608.19626) | 用外部一致性、锁定任务和等密度 placebo 审计反馈驱动测试演化；单一 oracle 可能夸大收益。 |
| [Progress Mirage](https://arxiv.org/abs/2607.25152) | 固定 Agent/工具，改变评估信息通道，以隔离的外部状态核验进展；作者报告自评会误认停滞或退化。 | 外部验收与自评偏差已覆盖；仅加验收门不新。 |
| [Rethinking the Value of Agent-Generated Tests](https://arxiv.org/abs/2602.07900)、[Risks of LLM-Generated Regression Tests](https://arxiv.org/abs/2610.11835) | 写更多测试不等于更好反馈；自生成测试可能固化错误行为。反馈是否独立于补丁、是否改变动作、是否改善原生目标结果必须分别验证。 |
| [Harness Design Study](https://arxiv.org/abs/2609.20804)、[Beyond the Model](https://arxiv.org/abs/2609.32459)、[PRISM](https://arxiv.org/abs/2609.05736) | 已有多模型、多基准 harness 对照及预算约束优化；本论文须把 harness 固定或做配对消融，不能把运行器差异归给记忆方法。 |

## 其他近邻索引

既有清单包括MemSkill、SkillApt、Skill-V、RethinkSkill、VibeMemBench、StateGraph、After the Fix、修复失败记忆及记忆压缩/成本研究；完整链接与历史判断见[研究归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。当前设计至少对照普通重试、修复后经验、scope/provenance核验、无改写历史和全流程成本。

## 对本项目实验的直接约束

1. 现有ALFWorld、Matplotlib、Astropy、Sphinx结果揭示了不同断点：信息送达但不改动作、自建测试不可靠、收到有效失败反馈仍停滞。它们不是同一训练标签；见[尸检计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md#现有证据尸检不可合并成一种坏经验)。
2. 若后续提出算法，必须与“无历史、完整历史、短历史/目标重申、版本/依赖规则、全量重测、普通反馈重试、最近邻方法”在相同任务、信息、工具和总成本下比较；根据算法实际目标选择其中适用近邻。
3. 评分须来自独立、冻结的原生检查；不把Agent自写测试当作金标准。报告后续动作、任务成功、源任务回归、无效更新和形成/检索/修订/验证成本。
4. 以上只约束设计，不等于实验已授权、方法已通过或论文结论已成立。当前方法状态以[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)与[科研入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)为准。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
