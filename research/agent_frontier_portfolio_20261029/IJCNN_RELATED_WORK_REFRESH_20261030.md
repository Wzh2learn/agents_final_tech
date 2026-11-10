# 第二篇：近邻、重合与实验判别

> 2026-11-11。D的文献笔记，未复现原法；外审须核验版本与具体重合。[历史笔记](../../docs/archive/2026-11-06_agent_research_context/README.md)。

## 当前裁决

**尚无已验证新方法，Goal active。**下表界定近邻，具体FCDR取舍见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 最直接的方法近邻

| 工作 | 已覆盖的机制（依原文） | 对本项目的约束 |
|---|---|---|
| [StateWise](https://arxiv.org/html/2610.05241v1) | 本轮补读§3、4.2–4.4：记录干预定位前提，核验后将证据绑定记录/作用域，持久修复并重规划。 | FCDR仅作前提/范围绑定已有近邻；原法未复现。 |
| [EmbodiSkill](https://arxiv.org/html/2605.10332) | 区分技能缺陷与执行失误；前者定向修订，后者保留有效指导。 | “修订或保留”与执行失误归因已覆盖。 |
| [EvoMem / EvoArena](https://arxiv.org/html/2606.13681) | 终端、软件及偏好变化任务；补丁式记忆演化，并测下游任务链表现。 | 版本化记忆、变化场景和下游成绩均已有先例。 |
| [Repo2Skill-Evo](https://arxiv.org/html/2608.21964) | 57个仓库、105次发布转换中的仓库技能维护。 | 真实发布迁移本身不新，须有独立算法差异。 |
| [Recuris](https://arxiv.org/abs/2608.24876) | 进度记忆、轨迹定位、局部修补、留出门控及失败后适配。匹配4次尝试比较53/87对51/87，p=0.774。 | 隔离适配与重试收益；机制和成绩均未复现。 |
| [VCE-Skill](https://arxiv.org/abs/2608.16544) | 从公开技能版本差异提炼经验，并与当前轨迹的更新提案融合。 | “从版本变化中学更新经验”不能单独作为方法。 |
| [CounterMem](https://arxiv.org/html/2609.31874v1) | 同状态反事实动作和适用条件记忆；学习使用/跳过并测有害误用。 | 配对执行和适用性选择已覆盖。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 同状态WITH/WITHOUT配对结果，条件边际效用与Load/Abstain。 | 配对干预与选择性复用有直接近邻。 |
| [RADEG](https://arxiv.org/html/2608.09168v1) | 同query技能增删替换，以rollout学效用门，再用verifier反馈更新。 | 局部干预＋反馈调整已覆盖。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | 轨迹诊断、保留有效部分、局部修订、执行效用接受门。 | 须超出该流程及其普通改写基线。 |
| [Skill-V](https://arxiv.org/html/2610.11781v1) | 版本化可证伪合同，结果驱动边界修订与历史回放。 | 边界更新/回归保护已有先例。 |
| [EFC](https://arxiv.org/html/2605.29682) | 计量反馈有效性、信息、冗余及后续决策保留。 | 反馈链分解本身仅作尸检。 |
| [STALE](https://arxiv.org/html/2605.06527v1) | 隐式冲突下测状态识别、旧前提抵抗与行为适配。 | 个人事实记忆场景不同，问题定义有重合。 |
| [ContinualSkillBench](https://arxiv.org/abs/2608.03874) | 顺序任务中普通历史平均可与显式skill维护相当。 | 保留普通历史强基线。 |
| [OMCE](https://arxiv.org/html/2611.01747v1) | 用上下文 bandit 基于反馈更新经验路由，并支持失败后重试。 | 在线反馈路由不是空白。 |
| [MemScope](https://arxiv.org/html/2610.21170) | 联合检查轨迹、运行时记忆和 provider 代码，定位并局部修改，再验证恢复/回归。 | 反馈定位＋局部修改＋验证已覆盖。 |
| [AgentLoop](https://arxiv.org/html/2609.33315) | 根据需求槽、证据和相邻轮稳定/低收益信号，决定继续、整合或停止。 | 通用进展/停滞控制已覆盖。 |
| [CORAL](https://arxiv.org/abs/2610.40350)、[Context compression](https://arxiv.org/abs/2609.29875)、[AgentRewind](https://arxiv.org/abs/2608.14380) | 分别研究经核实进度上的新推理episode、交互历史压缩、上下文与环境状态对齐恢复。 | ALFWorld新会话/轨迹投影观察不能单独证明新颖性。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已覆盖 / 实验启示 |
|---|---|
| [ExecCritic](https://arxiv.org/abs/2609.09133) | 独立生成并冻结测试后再修复；区分测试质量与修复效果。 |
| [Teaching Agents to Code Reliably](https://arxiv.org/html/2610.03984) | 已读§2.1–2.3：补丁/回退差分执行、改动行覆盖、候选/变体区分、加权轨迹和断言奖励。执行矩阵与覆盖门不能单独作创新；未复现。 |
| [CodeT](https://arxiv.org/abs/2207.10397) | 仅核原始摘要：生成测试与多程序执行一致性选择。多候选×探针矩阵已有先例。 |
| [ErrorProbe](https://arxiv.org/html/2604.17658) | 本轮读§4.3–4.4：工具执行核验错误假设，验证后写入经验记忆；主评估为错误归因，未复现。假设＋探针＋记忆本身不新。 |
| [Contract Before Code](https://aclanthology.org/2026.realm-1.72/) | REALM 2026；已读§2.3–4：失败编译为适用条件、可执行探针及计划后果，检索后运行前置门。探针＋前提检查已有直接近邻；未复现。 |
| [Bayesian Control for Coding Agents](https://aclanthology.org/2026.emnlp-main.1548/) | EMNLP 2026；已读§3–5/A.6：以候选正确性后验和成本决定取证、修复、验证或停止，状态含预算及已查询critic。成本敏感取证本身不新；未复现。 |
| [VeriHarness](https://arxiv.org/abs/2607.14167) | 本轮核摘要：比较原始反馈与位置/观测值/可行替代项，含prose/JSON对照。FCDR须排除额外修复信息及表示格式收益；实现未核。 |
| [Validation Evidence](https://arxiv.org/abs/2607.28871) | 缺陷/候选/金补丁重放测试以测反馈区分力；报告效应低于预设阈值。测试质量有直接近邻。 |
| [Auditing Feedback-Driven Evolution](https://arxiv.org/abs/2608.19626) | 用外部一致性、锁定任务和等密度 placebo 审计反馈驱动测试演化；单一 oracle 可能夸大收益。 |
| [Rethinking the Value of Agent-Generated Tests](https://arxiv.org/abs/2602.07900)、[Risks of LLM-Generated Regression Tests](https://arxiv.org/abs/2610.11835) | 写更多测试不等于更好反馈；自生成测试可能固化错误行为。反馈是否独立于补丁、是否改变动作、是否改善原生目标结果必须分别验证。 |

## 其他近邻索引

MemSkill、RethinkSkill、TAM、SkillShift、VibeMemBench、StateGraph及记忆压缩研究见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。

## 对本项目实验的直接约束

1. 反馈不可靠、抵达但未采纳、执行停滞须分开，见[尸检](STAGE2_AGENT_RESEARCH_PLAN_20261102.md#现有证据尸检不可合并成一种坏经验)；把这些环节拼成流程不等于新方法。
2. 匹配任务/信息/工具/总预算，对照普通历史、简单规则、全量重测、普通重试与最近邻；按算法选择适用项。
3. 冻结独立原生评分，报告动作、目标成功、源回归及形成至验证全成本；自写测试不作金标准。
4. 当前状态与运行授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)和[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
