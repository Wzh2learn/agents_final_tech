# 第二篇：近邻与实验设计参照

> 2026-11-08 | 短导航；保留最接近的方法与比较要求。完整检索、来源日期和接口诊断见[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。不同条目的证据深度不一，摘要阅读不等于源码复现。

## 优先比较什么

| 近邻 | 已覆盖的方向 / 本项目应对齐的比较 |
| --- | --- |
| [SWE-ContextBench](https://arxiv.org/abs/2602.08316) | 相关真实 GitHub 问题间的历史、摘要、记忆复用及成本；对齐可见信息、来源时序、问题修复和回归。项目已取得固定 Lite 来源，但没有复现作者总体成绩。 |
| [RethinkSkill](https://arxiv.org/abs/2608.02636) | 成功/失败反馈组合、多轮候选及训练/验证接受门；不能把一次合法 JSON 当完整方法复现。 |
| [Skill-V](https://arxiv.org/abs/2610.11781) | skill 合同、适用范围、历史回放与非回归；“附证据/按条件修订”本身已有先例。 |
| [SkillApt](https://arxiv.org/abs/2609.26863) | 利用有无 skill 的配对结果学习复用选择；比较获取额外反馈的真实成本。 |
| [Skill-R1](https://arxiv.org/html/2605.09359v1) | 冻结任务模型，以可验证奖励训练轻量skill编辑器，使用代内/代际优势；“用RL训练一个会改skill的小模型”本身已有覆盖。方法正文已核，未复现代码/成绩。 |
| [SkillGLoW §3.3–3.4](https://arxiv.org/html/2609.02217v1) | 适用条件/程序/失败模式、退化后的scope guards、真实执行准入及冻结迁移均已覆盖；这些不能作为新意。 |
| [SkillHEX §3.1/B.2](https://arxiv.org/html/2608.05628v1) | 假设转可执行诊断、缓存产物重测与新技能fresh执行；重测旧产物不同于改变环境后重跑策略。 |
| [CIPO §3.3–3.4/App.B/D](https://arxiv.org/html/2610.04991v1) | 同前缀技能/原子反事实、部分结果续做已覆盖；须比较原子续做，可变world分支复原实现仍需核。 |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 固定真实仓库、有无 skill 和隐藏执行检查；构造需求、环境适配与自然 issue 必须区别报告。 |
| [SkillFlow](https://arxiv.org/abs/2604.17308) | 完整历史、无历史和持续 skill 库对照；这三臂的比较本身不是新贡献。 |
| [CFOE](https://arxiv.org/abs/2610.22984) / [CoEvoSkills](https://arxiv.org/abs/2604.01687) | 失败学习的迁移边界、验证器与经验共演化；要对齐已有反馈、额外执行和验证预算。 |
| [Useful Memories Become Faulty](https://arxiv.org/abs/2605.12978) | 连续抽象和更新导致条件/细节丢失；本项目应区分生成遗漏、工具读取截断与任务效果。 |

## 已接入到哪一步

RethinkSkill源码 `8252445918ebebebce7adf9be843c90841e66810`（MIT）：原生摘要接口1POST/2,447tokens得到合法但只添换行的提案，未部署；早期字段错配不算方法负结果。[接入与设计](../../docs/archive/2026-11-06_agent_research_context/related_work_candidate_design_20261105.md)、[早期诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)按需读。正式比较仍需真实修订、接受门和后续任务；新查三篇只核主文/附录机制，未复现官方实现。

## 机制自审（2026-11-06）

**Mode / Boundary**：inquiry-methods的fact-check；本次读三篇一手HTML方法段及Skill-V附录，未做完整代码复现。核查对象是候选方法与已有工作的区别，同步推进实际实验。

- **CONFIRMED**：[Skill-V §3.3、B.5–B.6](https://arxiv.org/html/2610.11781v1)允许修订procedure，不只是rubric；保留语义约束并作历史证据回放。因此“会改步骤”不能单独作为区别。§3.4在episode开头选入技能。
- **11-08复核**：[SkillApt §3.2–3.6/附录B](https://arxiv.org/html/2609.26863v1)已有WITH/WITHOUT配对效用及LOAD/ABSTAIN；SRA v1以题面hash表征状态，等正确率成本正/负例均标0.5。同前置状态修复与工具隔离已覆盖；未见执行中撤回经验、保留改后world续做的对照。一般定义不排除成本/丰富状态，须比较同输入强适配版。
- **CONFIRMED**：[Skill-R1 §3](https://arxiv.org/html/2605.09359v1)已覆盖用真实rollout奖励训练循环编辑器，不能只靠换成LoRA或代码任务宣称新方法。

**比较要求**：固定keep/drop、滚动短历史、目标重申、Memento式笔记折叠、配对效用选择及简单冲突guard；同当前观察/合法动作/工具合同。隐藏或打乱反馈后优势不降，就撤回反馈因果解释。适配不冒充原法复现。

**当前直接对标**：[STeP](https://arxiv.org/html/2505.20023v1)纠正训练、[Sentry](https://arxiv.org/html/2610.02994v1)失败时经验暴露、[EMG](https://arxiv.org/html/2607.13884v3)成功/失败图匹配；[DGRR §3/4/D](https://arxiv.org/html/2608.10502v1)已有依赖失效与独立证据保留，须对齐故障标识并比较最新观察覆盖；[Memento §3.2–3.6/4.2.2](https://arxiv.org/html/2611.00244v1)学习静态书籍QA笔记及窗口压缩/回退。原文已核，未复现成绩。更多重叠与假设见[纠正记录](results/ALFWORLD_CORRECTION_DATA.md#方法重叠与下一验证)，执行查[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

2026-11-08复核：[Agent-R §3/4.4](https://arxiv.org/html/2501.11425v3)是自生成搜索/轨迹拼接，已有失败中间前缀续做；不能概括为STeP式强教师接管。具体比较见[运行对标](results/ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#recovery-literature)。

检索规则见[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md#联网搜索路由)。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[可执行候选：反馈与经验的适用性，而非又一个技能库 原记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
