# 第二篇：近邻与实验设计参照

> 2026-11-09 | 短导航；保留最接近的方法与比较要求。完整检索、来源日期和接口诊断见[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。不同条目的证据深度不一，摘要阅读不等于源码复现。

## 优先比较什么

| 近邻 | 已覆盖的方向 / 本项目应对齐的比较 |
| --- | --- |
| [SWE-ContextBench](https://arxiv.org/abs/2602.08316) | 真实问题间历史/摘要复用；对齐时序、修复及回归。已取Lite来源，未复现总体成绩。 |
| [RethinkSkill](https://arxiv.org/abs/2608.02636) | 成功/失败反馈、多轮候选与接受门；合法JSON不是方法复现。 |
| [Skill-V](https://arxiv.org/abs/2610.11781) / [SkillGLoW](https://arxiv.org/html/2609.02217v1) | 合同、范围、程序修订、历史回放与真实执行准入已有先例。 |
| [SkillApt](https://arxiv.org/abs/2609.26863) | 利用有无 skill 的配对结果学习复用选择；比较获取额外反馈的真实成本。 |
| [Skill-R1](https://arxiv.org/html/2605.09359v1) | 冻结actor、验证奖励训练编辑器；正文已核，未复现成绩。 |
| [SkillHEX §3.1/B.2](https://arxiv.org/html/2608.05628v1) | 可执行诊断、缓存重测与fresh执行；产物重测不等于重跑策略。 |
| [CIPO §3.3–3.4/App.B/D](https://arxiv.org/html/2610.04991v1) | 同前缀技能/原子分支、部分续做；world分支复原待核。 |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 固定仓库、有无skill、隐藏检查；区别自然issue与构造任务。 |
| [SkillFlow](https://arxiv.org/abs/2604.17308) | 完整历史、无历史和持续skill库对照；三臂本身非新贡献。 |
| [CFOE](https://arxiv.org/abs/2610.22984) / [CoEvoSkills](https://arxiv.org/abs/2604.01687) | 失败学习的迁移边界、验证器与经验共演化；要对齐已有反馈、额外执行和验证预算。 |
| [Useful Memories Become Faulty](https://arxiv.org/abs/2605.12978) | 连续抽象和更新导致条件/细节丢失；本项目应区分生成遗漏、工具读取截断与任务效果。 |

## 已接入到哪一步

RethinkSkill仅接口接通，未部署；[接入](../../docs/archive/2026-11-06_agent_research_context/related_work_candidate_design_20261105.md)、[诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)按需读。比较仍需修订、接受门及执行。

## 机制自审（2026-11-06）

**核查范围**：一手方法正文/附录，未完整复现代码；用来约束候选机制及对照。

- **CONFIRMED**：[Skill-V §3.3、B.5–B.6](https://arxiv.org/html/2610.11781v1)允许修订procedure，不只是rubric；保留语义约束并作历史证据回放。因此“会改步骤”不能单独作为区别。§3.4在episode开头选入技能。
- [SkillApt §3.2–3.6/附录B](https://arxiv.org/html/2609.26863v1)已有配对效用与LOAD/ABSTAIN；比较须对齐状态、工具和成本。保留改后world续做的差异待验证。
**比较要求**：keep/drop、短历史、目标重申及冲突规则，保持观察/动作一致；适配不冒充复现。

**当前参照**：[Sentry](https://arxiv.org/html/2610.02994v1)失败时暴露经验；[EMG](https://arxiv.org/html/2607.13884v3)成功/失败图匹配；[DGRR §3](https://arxiv.org/html/2608.10502v1)依赖失效/独立支持，须对齐故障标识；[Memento §3](https://arxiv.org/html/2611.00244v1)学习笔记折叠/回退。原文已核，成绩未复现；细节查[纠正记录](results/ALFWORLD_CORRECTION_DATA.md#方法重叠与下一验证)。

**R属强基线**：[STeP](https://arxiv.org/html/2505.20023v1)用教师纠正/partial masking；[Agent-R](https://arxiv.org/html/2501.11425v3)用自搜索拼接。O/R的6/12对8/12不识别新意或反馈因果；[数据/成本对齐](results/ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#recovery-literature)按需读。

检索规则见[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md#联网搜索路由)。

**机制核查**：[TrustMem](https://arxiv.org/html/2606.25161v1)、[LW2S](https://arxiv.org/html/2609.30734v1)、[AttriMem](https://arxiv.org/html/2607.21106v3)、[MemCalib](https://arxiv.org/html/2609.24259v1)、[Anti-Persistence](https://arxiv.org/html/2610.27406v1)覆盖转移奖励、组件信用及成本；局部编辑/交互loss本身不新。[MERIT](https://arxiv.org/html/2608.05906v1)用oracle，比较须对齐权限。

[JointCore §2–3](https://arxiv.org/html/2610.23266v1)搜索保留原行为的充分子集；[MemHarness §3](https://arxiv.org/html/2607.28272v1)重构经验并训练；[Value of Memory](https://arxiv.org/html/2610.31303v1)覆盖恢复成本和交互。[Forgetting Without Restarting](https://arxiv.org/html/2609.04875v1)提示历史/cache残留，不能声称精确遗忘。

[MGPO §2](https://arxiv.org/html/2609.37930v1)比较新旧记忆对当前/未来目标的边际效用；[CERL §3](https://arxiv.org/html/2606.05201v1)以同前缀保留/擦除/skip训练持久状态充分性；[CEDAR §3](https://arxiv.org/html/2608.27797v1)以已实现公开谓词、环境反例和DFA组合/LOOKUP修订控制器，非新DFA算法。均已读原文、未复现成绩；“预测状态/反例修订/加取证”均不足以单独成立新法。

理论边界：[Value-directed POMDP Compression](https://cs.uwaterloo.ca/~ppoupart/publications/compression/compression.pdf)已有保持决策质量的状态压缩（§3–4已读）；[MDPs with a State Sensing Cost](https://proceedings.mlr.press/v300/kapoor26a.html)已有付费感知与盲行动联合优化（仅一手摘要）。取证条件化记忆仍需具体算法与迁移证据，不能称新原理。

**最直接新增对标（§3原文已读，未复现）**：[OSL-MR](https://arxiv.org/html/2606.10616v1)已建模保留/重获延迟/陈旧风险，实际用gold evidence membership加权BCE及预算解码；[Context Compression Cost](https://arxiv.org/html/2608.16370v1)已诊断固定Agent的保留/摘要/oracle恢复及自然重新取证，区分可回读与历史依赖信息。问题划分和成本思想已有先例。

**候选取舍**：四格交互是回报的线性组合，普通联合Q可表达；仅加交互loss不足以新颖。主攻实际取证后、按续做后果学习局部经验修订，须与同数据/动作/可见反馈联合策略比较。[直接筛查](results/CODE_SOURCE_CORRECTIONS.md#direct-method)未形成可训练的新方法证据。

**联合学习直接对标**：[AiO-Mem §3](https://arxiv.org/html/2610.21147v1#S3)联合search/add/skip/stop与过程奖励；[CAMG §5/C.1/D.3](https://arxiv.org/html/2609.34422v1)训练文件记忆并干预清空/打乱。保持策略动作与反馈相同，不能通过削弱联合基线证明增量。原文已核，成绩未复现。

**局部修订近邻（11-09原文核查，未复现）**：[StateGraph §4.2–4.5](https://arxiv.org/html/2611.02912v1#S4)从历史发现依赖，用反事实问题验证后局部撤回并检查行动前提；“有依赖图/局部撤回”已被覆盖。[When Evidence Changes §4/6.2](https://arxiv.org/html/2610.03902v1#S6.SS2)比较局部修复与当前来源重读，发现节点重算少不保证全流程tokens少。我们的待验差异只能落在实际续做后果监督、局部编辑结构和同信息学习效率上；不能先宣布新原理。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
