# 第二篇：近邻与实验设计参照

> 2026-11-09 | 短导航；保留最接近的方法与比较要求。完整检索、来源日期和接口诊断见[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。不同条目的证据深度不一，摘要阅读不等于源码复现。

## 优先比较什么

| 近邻 | 已覆盖的方向 / 本项目应对齐的比较 |
| --- | --- |
| [SWE-ContextBench](https://arxiv.org/abs/2602.08316) | 真实问题间历史/摘要复用；对齐时序、修复及回归。已取Lite来源，未复现总体成绩。 |
| [RethinkSkill](https://arxiv.org/abs/2608.02636) | 成功/失败反馈、多轮候选与接受门；合法JSON不是方法复现。 |
| [Skill-V](https://arxiv.org/abs/2610.11781) | skill 合同、适用范围、历史回放与非回归；“附证据/按条件修订”本身已有先例。 |
| [SkillApt](https://arxiv.org/abs/2609.26863) | 利用有无 skill 的配对结果学习复用选择；比较获取额外反馈的真实成本。 |
| [Skill-R1](https://arxiv.org/html/2605.09359v1) | 冻结actor、可验证奖励训练skill编辑器及代内/代际优势；正文已核，未复现成绩。 |
| [SkillGLoW §3.3–3.4](https://arxiv.org/html/2609.02217v1) | 适用条件/程序/失败模式、退化后的scope guards、真实执行准入及冻结迁移均已覆盖；这些不能作为新意。 |
| [SkillHEX §3.1/B.2](https://arxiv.org/html/2608.05628v1) | 假设转可执行诊断、缓存产物重测与新技能fresh执行；重测旧产物不同于改变环境后重跑策略。 |
| [CIPO §3.3–3.4/App.B/D](https://arxiv.org/html/2610.04991v1) | 同前缀技能/原子反事实、部分结果续做已覆盖；须比较原子续做，可变world分支复原实现仍需核。 |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 固定仓库、有无skill、隐藏检查；区别自然issue与构造任务。 |
| [SkillFlow](https://arxiv.org/abs/2604.17308) | 完整历史、无历史和持续skill库对照；三臂本身非新贡献。 |
| [CFOE](https://arxiv.org/abs/2610.22984) / [CoEvoSkills](https://arxiv.org/abs/2604.01687) | 失败学习的迁移边界、验证器与经验共演化；要对齐已有反馈、额外执行和验证预算。 |
| [Useful Memories Become Faulty](https://arxiv.org/abs/2605.12978) | 连续抽象和更新导致条件/细节丢失；本项目应区分生成遗漏、工具读取截断与任务效果。 |

## 已接入到哪一步

RethinkSkill原生接口已接通，提案未部署，不作方法负结果。[源码与接入](../../docs/archive/2026-11-06_agent_research_context/related_work_candidate_design_20261105.md)、[诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)按需读；正式比较仍需修订、接受门及后续执行。表中机制核查不等于成绩复现。

## 机制自审（2026-11-06）

**核查范围**：一手方法正文/附录，未完整复现代码；用来约束候选机制及对照。

- **CONFIRMED**：[Skill-V §3.3、B.5–B.6](https://arxiv.org/html/2610.11781v1)允许修订procedure，不只是rubric；保留语义约束并作历史证据回放。因此“会改步骤”不能单独作为区别。§3.4在episode开头选入技能。
- **11-08复核**：[SkillApt §3.2–3.6/附录B](https://arxiv.org/html/2609.26863v1)已有WITH/WITHOUT配对效用及LOAD/ABSTAIN；SRA v1以题面hash表征状态，等正确率成本正/负例均标0.5。同前置状态修复与工具隔离已覆盖；未见执行中撤回经验、保留改后world续做的对照。一般定义不排除成本/丰富状态，须比较同输入强适配版。
- **CONFIRMED**：[Skill-R1 §3](https://arxiv.org/html/2605.09359v1)已覆盖用真实rollout奖励训练循环编辑器，不能只靠换成LoRA或代码任务宣称新方法。

**比较要求**：keep/drop、短历史、目标重申、笔记折叠、配对效用及冲突规则；同观察/动作/合同。打乱反馈后优势不降，撤回反馈因果解释。适配不冒充复现。

**当前参照**：[Sentry](https://arxiv.org/html/2610.02994v1)失败时暴露经验；[EMG](https://arxiv.org/html/2607.13884v3)成功/失败图匹配；[DGRR §3](https://arxiv.org/html/2608.10502v1)依赖失效/独立支持，须对齐故障标识；[Memento §3](https://arxiv.org/html/2611.00244v1)学习笔记折叠/回退。原文已核，成绩未复现；细节查[纠正记录](results/ALFWORLD_CORRECTION_DATA.md#方法重叠与下一验证)。

**R属强基线**：[STeP](https://arxiv.org/html/2505.20023v1)用教师纠正/partial masking；[Agent-R](https://arxiv.org/html/2501.11425v3)用自搜索拼接。O/R的6/12对8/12不识别新意或反馈因果；[数据/成本对齐](results/ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#recovery-literature)按需读。

检索规则见[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md#联网搜索路由)。

**11-09机制拆解**：[TrustMem §3](https://arxiv.org/html/2606.25161v1)已有转移覆盖/保留/忠实度奖励和同状态偏好；[LW2S](https://arxiv.org/html/2609.30734v1)已有组件skip信用分配。局部修订、交互loss和主动学习本身不足以认证新意。

本轮补查最直接重叠：[JointCore §2–3](https://arxiv.org/html/2610.23266v1)以群删除搜索保留完整记忆行为的充分子集，允许冗余/联合必要性；它不等于以真实续做成功为目标。[MemHarness §3](https://arxiv.org/html/2607.28272v1)已按状态批判/重构经验，GRPO训练且评测ALFWorld/WebShop。[Value of Memory](https://arxiv.org/html/2610.31303v1)已有恢复/修订成本和组件交互理论，不能再声称首先提出价值框架。

**取舍**：非零交互不保证选择收益。聚焦不回滚外部进度的见证保留/重新取证，须超过强适配及同数据简单模型。[Forgetting Without Restarting](https://arxiv.org/html/2609.04875v1)提示历史/cache残留，不声称精确遗忘；见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md#可检验的机制方向)。

[MERIT §3](https://arxiv.org/html/2608.05906v1)以oracle确认修复、已观测失败及错型检索积累经验；部署比较须对齐oracle可用性。非执行/超预算是真实效用损失，但不足以反证经验前提；区分两类标签仍只是估计对象划分，候选修订必须胜过不可变bank＋弃用及同信息修复。

**11-09方法正文**：[AttriMem](https://arxiv.org/html/2607.21106v3)用记忆遮罩贡献奖励；[MemCalib](https://arxiv.org/html/2609.24259v1)用原子过用/欠用及反事实信用；[Anti-Persistence](https://arxiv.org/html/2610.27406v1)用成本bandit选择合成。因此细粒度奖励或按需改写非独立新意。

[MGPO §2](https://arxiv.org/html/2609.37930v1)比较新旧记忆对当前/未来目标的边际效用；[CERL §3](https://arxiv.org/html/2606.05201v1)以同前缀保留/擦除/skip训练持久状态充分性；[CEDAR §3](https://arxiv.org/html/2608.27797v1)以已实现公开谓词、环境反例和DFA组合/LOOKUP修订控制器，非新DFA算法。均已读原文、未复现成绩；“预测状态/反例修订/加取证”均不足以单独成立新法。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
