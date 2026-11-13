# 第二篇：近邻、重合与实验判别

> 更新至2026-11-14。定向读方法，未复现原法；旧表见`bdb85edb`本文件blob，早期见`89ca0dbd`。

## 当前裁决

**FCCL主线：从执行反馈学习可复用纠正策略。** 尚无成立新方法。当前跨角色续行程序仅为候选；角色标签、可执行程序、配对执行和反馈更新本身已有，不以新载体替代增量。

11-14：固定差分停扩；当前检验原生反馈—纠正收益交互的生成策略更新。来源反转不等于方法收益。

## 最直接的方法近邻

| 工作 | 已核机制 | 当前必须解决的区别 |
|---|---|---|
| [REBEL](https://arxiv.org/abs/2404.16767) | 已核摘要/作者论文：以策略相对奖励回归做优化；相对奖励回归本身已有。 | 当前逐行项须按其已知骨架解释，并作同四格数据的强基线；跨上下文中心化不自动构成新算法。 |
| [InfoPO](https://arxiv.org/html/2603.00656) / [Embodied-Corrector](https://arxiv.org/html/2611.15651v1) | C核前者§4.1–4.2：真实/遮蔽反馈下动作LL差；D核后者§3.2：准确/自生成诊断的token概率差及OPD/NEPO。 | 反馈敏感性、诊断蒸馏已有。当前候选以原生四格结果监督生成更新；仍须同预算DPO/逐行回归验证。 |
| [UniSkill](https://arxiv.org/html/2610.10164v1) / [CaPE](https://aclanthology.org/2023.findings-acl.685/) | 分别读§3.3/实现及原文：前者以冻结actor在同题成败参考上的token归一似然增量差学习技能，并联合GRPO；后者用expert−anti-expert参数差。 | 成败对比与R−O算术已有；当前仅检验旧训练信号，条件更新及独立任务收益仍须另证。 |
| [PEAM v2](https://arxiv.org/html/2605.27762v2) | 读§3.1–3.4：同上下文失败/纠正对以BC＋DPO更新类别隔离LoRA，执行验证失败回退慢模型，按效用及失败统计触发巩固。 | 从失败学适配器、条件路由/回退已有；不把参数化记忆本身主张为独立创新。未复现代码/结果。 |
| [Agent-R](https://arxiv.org/html/2501.11425v1) / [STeP](https://arxiv.org/html/2505.20023v1) | 共享前缀纠正/MCTS及迭代SFT；教师反思轨迹、错误动作部分mask。 | 从失败续做/正确片段学习已有，须证明条件纠正的额外收益。 |
| [HASP](https://arxiv.org/html/2605.17734v2) / [官方代码](https://github.com/HolaYan/ExecutableSkills-HASP) | §2.1–2.3/D：触发/改写及corrective context注入，时机/模式/正确/费用后续结果四信号，RS/SFT；`2a0e859e`含配对重生成。 | 纠正、上下文和后续结果信用均已有。须具体区分学习机制，不能把交还提醒或宏效果命名当增量。 |
| [SkillCompiler](https://arxiv.org/html/2610.39508) / [SkillSmith](https://arxiv.org/html/2605.15215) / [TraceCompiler](https://arxiv.org/html/2608.02680) | 分别核§III、§3、§3：操作级编译/修订，边界接口与回退，轨迹去噪及有证据依赖。 | 程序化、混合执行和去除偶然先后已有；当前阶段化反馈目标仍须匹配编译/普通更新比较，不能仅凭组合主张新方法。 |
| [StateGraph](https://arxiv.org/html/2611.02912v1) | §4.3–4.5：反事实依赖核验、保留历史、失效前提触发动作重规划。 | 效果记账/改触发条件本身不足；[v2](results/CONTINUATION_PROGRAM.md#effect-conditioned-v2)须以实际规则和任务收益判别，不能只用一步动作反例。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | §3.1–3.4：诊断/原则绑定、执行锚点、保留约束、重执行、效用门；搜索继续自最新候选，返回最佳候选。 | 已覆盖有锚点的纠正；不能用中间零收益推断它无法越过。需同信息/候选/总成本适配比较。 |
| [AdaMEM](https://arxiv.org/html/2606.05684v1) | §3.1–3.2：动态策略记忆，成功/动作改变筛选；反事实动作不实际执行。 | 条件策略须由实际片段及续行后果支持，动作变化本身不是收益。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 条件化配对效用、Load/Abstain。 | 条件效用本身不新。作者公开包为guoshaung/SkillApt，`73db0b54`；旧404不能外推无代码。 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | §3.3–3.4/B：参数绑定，软中断返回部分轨迹/结果；首个可行粒度同前缀分叉、同策略续行，结果差辅助GRPO。 | 返回部分进度及续行结果监督已有；下一须检验不同学习规则，不把分叉或交还本身称新方法。 |
| [SkillMorph](https://arxiv.org/html/2610.11858v1) | §2/4：跨重复、任务和演化轮的动作覆盖定位，再关联技能中的指令/脚本编辑位置并协调修订；固定模型/harness、留出任务评估。 | 失败轨迹定位和执行证据驱动技能修订已有，不能说它只看文本或没有实际行为。 |
| [SCOPE](https://arxiv.org/html/2611.03116v1) | §3.1–3.4：从全局失败轨迹挖局部技能/失败经验，组链；同探索前沿教师/自干预，完整轨迹蒸馏。 | 挖失败、保留进度与拼局部成功已有；不能把当前两种失败的互补目标直接称新机制。 |
| [SkillCAT](https://arxiv.org/html/2606.13317v1) | CCE同题成败对找首次有意义分歧；AAE源副本重放，0→1/1→1优先，阈值后层级合并。 | 首分歧学习已有；整体0→0的互补修复可能被筛除，但盲合并是必要强基线。正文已读，代码未独立核查。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已核范围 / 实验约束 |
|---|---|
| [TACR](https://arxiv.org/html/2610.03984) / [Bayesian Control](https://aclanthology.org/2026.emnlp-main.1548/) | 差分执行/覆盖；修好与修坏转移、在线Beta均值（已核官方`2a3de1dc`）。普通差分诊断与条件转移须作强基线，提示适配不称原法复现。 |
| [Rethinking Self-Repair](https://arxiv.org/html/2611.06863v1) / [PracRepair](https://arxiv.org/html/2606.17612v1) | 固定指导/同预算重试；执行差异诊断和最多3轮修复。动态反馈或整理输入本身不是新机制；前者未测保留失败现场恢复。 |
| [World Model Predictive Paths](https://arxiv.org/abs/2610.28945) | 本轮仅核摘要：多候选动作、世界模型预测、MPPI式选择及双支经验记忆。正文/代码未核，不作完整比较；“预测后果再决策”本身不能当创新。WorldRepair原始PDF访问受验证页阻挡，方法差异仍待核。 |

## 其他近邻索引

[tau2原文](https://arxiv.org/html/2506.07982v1)§3已有双侧工具协作及官方进度流程。v1.0.1 `fc0055dc`已接入；[反应式先导](results/CONTINUATION_PROGRAM.md#reactive-v1)三组均成功，唯一自动介入把正确Say回执误当重复写。HASP式适配/一步执行不算独立方法。分支恢复双侧历史/DB；不同领域仍属同一benchmark。

`e920668f`保留WER/Skill-α的成败/反事实技能更新；`17d4885f`保留ReGAL程序库更新；`6a2b8382`保留CodePhage/Getafix/CEGIS/CESS、SkillComposer、ASPIRE。其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)，移出不表示失效。

## 对本项目实验的直接约束

1. 反馈可靠性、送达、采纳与能力分开；通用流程不是新机制。
2. 统一任务、信息、工具与总预算，保留普通历史、状态规则、全重验及最近邻。
3. 条件片段学习须面对普通反馈纠正、静态技能、简单接口/约束规则及匹配近邻；形成数据与模型预算一致，不用更多样本解释为独立机制。
4. 独立原生评分，形成/整理/取证/执行全成本；自写测试、AI检查、模式合法均不作任务成功。
5. 当前状态和授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)及[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
