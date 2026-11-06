# 第二篇：近邻与实验设计参照

> 2026-11-06 | 短导航；保留最接近的方法与比较要求。完整检索、来源日期和接口诊断见[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。不同条目的证据深度不一，摘要阅读不等于源码复现。

## 优先比较什么

| 近邻 | 已覆盖的方向 / 本项目应对齐的比较 |
| --- | --- |
| [SWE-ContextBench](https://arxiv.org/abs/2602.08316) | 相关真实 GitHub 问题间的历史、摘要、记忆复用及成本；对齐可见信息、来源时序、问题修复和回归。项目已取得固定 Lite 来源，但没有复现作者总体成绩。 |
| [RethinkSkill](https://arxiv.org/abs/2608.02636) | 成功/失败反馈组合、多轮候选及训练/验证接受门；不能把一次合法 JSON 当完整方法复现。 |
| [Skill-V](https://arxiv.org/abs/2610.11781) | skill 合同、适用范围、历史回放与非回归；“附证据/按条件修订”本身已有先例。 |
| [SkillApt](https://arxiv.org/abs/2609.26863) | 利用有无 skill 的配对结果学习复用选择；比较获取额外反馈的真实成本。 |
| [Skill-R1](https://arxiv.org/html/2605.09359v1) | 冻结任务模型，以可验证奖励训练轻量skill编辑器，使用代内/代际优势；“用RL训练一个会改skill的小模型”本身已有覆盖。方法正文已核，未复现代码/成绩。 |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 固定真实仓库、有无 skill 和隐藏执行检查；构造需求、环境适配与自然 issue 必须区别报告。 |
| [SkillFlow](https://arxiv.org/abs/2604.17308) | 完整历史、无历史和持续 skill 库对照；这三臂的比较本身不是新贡献。 |
| [CFOE](https://arxiv.org/abs/2610.22984) / [CoEvoSkills](https://arxiv.org/abs/2604.01687) | 失败学习的迁移边界、验证器与经验共演化；要对齐已有反馈、额外执行和验证预算。 |
| [Useful Memories Become Faulty](https://arxiv.org/abs/2605.12978) | 连续抽象和更新导致条件/细节丢失；本项目应区分生成遗漏、工具读取截断与任务效果。 |

## 已接入到哪一步

RethinkSkill 固定源码 `8252445918ebebebce7adf9be843c90841e66810`（MIT）。早期适配把完整历史塞进自定义反馈，输入偏离原生接口；这几次接口失败不构成方法负结果。后按 `native.py:220–237` 的摘要字段构造反馈，1 POST / 2,447 reported tokens 的短调用通过官方候选与外层提案协议，但实际仅改变末尾换行，未部署、未产生实质技能更新。

缺失的答案/gold 未补造；历史源执行单独记账。下一次正式比较需语义合格的反馈、独立验证任务、接受/拒绝门及未曝光目标。接入细节按需读[原生修正与候选设计](../../docs/archive/2026-11-06_agent_research_context/related_work_candidate_design_20261105.md)，早期格式诊断见[接口记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)。

## 机制自审（2026-11-06）

**Mode / Boundary**：inquiry-methods的fact-check；本次读三篇一手HTML方法段及Skill-V附录，未做完整代码复现。核查对象是候选方法与已有工作的区别，同步推进实际实验。

- **CONFIRMED**：[Skill-V §3.3、B.5–B.6](https://arxiv.org/html/2610.11781v1)允许修订procedure，不只是rubric；保留语义约束并作历史证据回放。因此“会改步骤”不能单独作为区别。§3.4在episode开头选入技能。
- **CONFIRMED**：[SkillApt §3.2–3.6](https://arxiv.org/html/2609.26863v1)已覆盖配对效用与LOAD/ABSTAIN。SRA v1使用题面哈希和固定近邻估计，正确性相同的成本正/负例都标0.5；这不等于其一般问题定义排除了成本或更丰富状态。
- **CONFIRMED**：[Skill-R1 §3](https://arxiv.org/html/2605.09359v1)已覆盖用真实rollout奖励训练循环编辑器，不能只靠换成LoRA或代码任务宣称新方法。

**Recommendation / Conditions**：Skill-V历史门复评旧轨迹，并未描述接受前重跑旧任务；Skill-R1真实rollout评价新skill。强基线应含“历史证据门＋固定K次新旧任务重执行”（本项目适配，非原法完整复现）。联合选择载体、修订与验证投入须超过它及廉价规则；独立增量仍待实测。

**Risk / Exit / First action**：两项目隔离比较已完成，接续[当前自然任务](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)与可靠教师轨迹资格，收集不同来源的正/负效用。训练由实际监督决定；若普通SFT、历史或简单规则解释收益，调整机制。oracle选择与开发修复不计作泛化确认。

查新默认使用 Codex 宿主原生搜索，优先论文全文、官方代码/数据和模型卡；没有当前搜索工具时，由 D 取得带链接与版本的材料。不自动调用 DeepSeek/Qwen 搜索 CLI，不将宿主工具伪装成 GB10 可请求的 HTTP 服务。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[可执行候选：反馈与经验的适用性，而非又一个技能库 原记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
