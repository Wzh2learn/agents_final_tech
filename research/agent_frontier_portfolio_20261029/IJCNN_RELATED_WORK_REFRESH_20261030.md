# 第二篇：近邻与实验设计参照

> 2026-11-10 | 短导航；详细检索见[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。读原文不等于复现。

## 优先比较什么

| 近邻 | 已覆盖的方向 / 本项目应对齐的比较 |
| --- | --- |
| [MemSkill](https://arxiv.org/html/2602.02474v2) | 用反馈学习记忆操作及技能，已测ALFWorld。 |
| [SWE-ContextBench](https://arxiv.org/abs/2602.08316) | 真实问题间经验复用；Lite数据已取，成绩未复现。 |
| [RethinkSkill](https://arxiv.org/abs/2608.02636) | 成功/失败反馈、多轮候选与接受门；合法JSON不是方法复现。 |
| [ExecCritic](https://arxiv.org/html/2609.09133v1) / [/retro](https://arxiv.org/html/2610.34938v1) | 前者固定测试再修复；后者检验经验对后续任务的影响。 |
| [Environment-Probing](https://arxiv.org/html/2609.11060v1) / [Scope Before Persist](https://arxiv.org/html/2609.29144v1) | 前者用只读环境探测整理经验；后者用执行验证和作用域约束持久经验。均已覆盖，须比较。 |
| [Skill Inconsistency](https://arxiv.org/html/2610.18927v1) | 用修复前后配对执行区分静态缺陷与实际行为后果；非仅查是否读取。 |
| [SkillGLoW](https://arxiv.org/html/2609.02217v1) | 技能合同与执行准入已有先例；Skill-V与SkillApt见下。 |
| [Skill-R1](https://arxiv.org/html/2605.09359v1) | 冻结actor、验证奖励训练编辑器；正文已核，未复现成绩。 |
| [SkillHEX §3.1/B.2](https://arxiv.org/html/2608.05628v1) | 可执行诊断、缓存重测与fresh执行；产物重测不等于重跑策略。 |
| [CIPO §3.3–3.4/App.B/D](https://arxiv.org/html/2610.04991v1) | 同前缀技能/原子分支、部分续做；world分支复原待核。 |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 固定仓库、有无skill、隐藏检查；区别自然issue与构造任务。 |
| [SkillFlow](https://arxiv.org/abs/2604.17308) | 完整历史、无历史和持续skill库对照；三臂本身非新贡献。 |
| [CFOE](https://arxiv.org/abs/2610.22984) / [CoEvoSkills](https://arxiv.org/abs/2604.01687) | 失败经验迁移及验证器与经验共演化。 |
| [Useful Memories Become Faulty](https://arxiv.org/abs/2605.12978) | 连续抽象和更新导致条件/细节丢失；本项目应区分生成遗漏、工具读取截断与任务效果。 |

## 已接入到哪一步

RethinkSkill仅接通接口，未部署或复现；[接入](../../docs/archive/2026-11-06_agent_research_context/related_work_candidate_design_20261105.md)、[诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)按需读。

## 机制自审（2026-11-06）

**核查范围**：一手方法正文/附录，未完整复现代码；用来约束候选机制及对照。

- [Skill-V §3.3、B.5–B.6](https://arxiv.org/html/2610.11781v1)修订procedure并回放历史；§3.4于episode开头选技能。仅“修改步骤”不构成差异。
- [SkillApt §3.2–3.6/附录B](https://arxiv.org/html/2609.26863v1)已有配对效用与LOAD/ABSTAIN；修改后保留world续做的差异待验证。
**比较要求**：对齐状态、工具与成本，比较keep/drop、短历史、目标重申与冲突规则；适配不冒充复现。

**其他参照**：Sentry失败经验、EMG经验图、DGRR依赖失效、Memento笔记折叠，原文已核但成绩未复现；出处见[记录](results/ALFWORLD_CORRECTION_DATA.md#方法重叠与下一验证)。

**R属强基线**：[STeP](https://arxiv.org/html/2505.20023v1)教师纠正与partial masking；[Agent-R](https://arxiv.org/html/2501.11425v3)自搜索拼接。O/R不足以识别新意或反馈因果；见[成本](results/ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#recovery-literature)。

检索规则见[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md#联网搜索路由)。

**机制核查**：[TrustMem](https://arxiv.org/html/2606.25161v1)、[LW2S](https://arxiv.org/html/2609.30734v1)、[AttriMem](https://arxiv.org/html/2607.21106v3)、[MemCalib](https://arxiv.org/html/2609.24259v1)、[Anti-Persistence](https://arxiv.org/html/2610.27406v1)覆盖转移奖励、组件信用及成本；局部编辑/交互loss本身不新。[MERIT](https://arxiv.org/html/2608.05906v1)用oracle，比较须对齐权限。

[JointCore §2–3](https://arxiv.org/html/2610.23266v1)搜索保留原行为的充分子集；[MemHarness §3](https://arxiv.org/html/2607.28272v1)重构经验并训练；[Value of Memory](https://arxiv.org/html/2610.31303v1)覆盖恢复成本和交互。[Forgetting Without Restarting](https://arxiv.org/html/2609.04875v1)提示历史/cache残留，不能声称精确遗忘。

[MGPO §2](https://arxiv.org/html/2609.37930v1)比较新旧记忆对当前/未来目标的边际效用；[CERL §3](https://arxiv.org/html/2606.05201v1)以同前缀保留/擦除/skip训练持久状态充分性；[CEDAR §3](https://arxiv.org/html/2608.27797v1)以已实现公开谓词、环境反例和DFA组合/LOOKUP修订控制器，非新DFA算法。均已读原文、未复现成绩；“预测状态/反例修订/加取证”均不足以单独成立新法。

理论边界：[Value-directed POMDP Compression](https://cs.uwaterloo.ca/~ppoupart/publications/compression/compression.pdf)已有保持决策质量的状态压缩（§3–4已读）；[MDPs with a State Sensing Cost](https://proceedings.mlr.press/v300/kapoor26a.html)已有付费感知与盲行动联合优化（仅一手摘要）。取证条件化记忆仍需具体算法与迁移证据，不能称新原理。

**最直接新增对标（§3原文已读，未复现）**：[OSL-MR](https://arxiv.org/html/2606.10616v1)已建模保留/重获延迟/陈旧风险，实际用gold evidence membership加权BCE及预算解码；[Context Compression Cost](https://arxiv.org/html/2608.16370v1)已诊断固定Agent的保留/摘要/oracle恢复及自然重新取证，区分可回读与历史依赖信息。问题划分和成本思想已有先例。

**候选取舍**：四格交互可由普通联合Q表达；取证后经验修订须与同数据、动作和反馈的联合策略比较。[直接筛查](results/CODE_SOURCE_CORRECTIONS.md#direct-method)尚无可训练的新方法证据。

**联合学习直接对标**：[AiO-Mem §3](https://arxiv.org/html/2610.21147v1#S3)联合search/add/skip/stop与过程奖励；[CAMG §5/C.1/D.3](https://arxiv.org/html/2609.34422v1)训练文件记忆并干预清空/打乱。保持策略动作与反馈相同，不能通过削弱联合基线证明增量。原文已核，成绩未复现。

[TokenTune §3](https://arxiv.org/html/2501.18824v1)已用位置选择性反传＋LoRA；反馈加权不新，须对照等长随机位置与普通训练并计成本。

**局部修订近邻（11-09原文核查，未复现）**：[StateGraph §4.2–4.5](https://arxiv.org/html/2611.02912v1#S4)从历史发现依赖，用反事实问题验证后局部撤回并检查行动前提；“有依赖图/局部撤回”已被覆盖。[When Evidence Changes §4/6.2](https://arxiv.org/html/2610.03902v1#S6.SS2)比较局部修复与当前来源重读，发现节点重算少不保证全流程tokens少。我们的待验差异只能落在实际续做后果监督、局部编辑结构和同信息学习效率上；不能先宣布新原理。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
