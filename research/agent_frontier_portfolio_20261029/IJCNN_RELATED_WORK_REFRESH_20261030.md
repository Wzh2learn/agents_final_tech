# 第二篇：近邻、重合与实验判别

> 2026-11-17｜已读机制不等于复现成绩。旧详表见Git bdb85edb/89ca0dbd。当前执行只读[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 当前裁决

从执行反馈学习可复用纠正能力；优先金融主集上的具体改进。近邻用于借鉴与对照，不要求全部组件原创或跨领域领先。旧固定差分/首分叉配方停扩；下一候选分开学习修复提案和KEEP/采纳，只选实际采用的最近机制比较。

## 最直接的方法近邻

| 工作 | 已核机制 | 当前用途 |
|---|---|---|
| [RouteLLM](https://arxiv.org/html/2406.18665v4) | 11-17核正文：问题到强弱胜率，含因果LM分类器 | 对照问题级路由；大模型分类器本身不作新机制 |
| [AutoMix](https://arxiv.org/html/2310.12963v5) / [GenGate](https://aclanthology.org/2026.emnlp-main.2071.pdf) | 11-17核正文：回答后验证/接管；动作概率训练门控 | 当前风险臂只适配后验判断，不称完整原法复现 |
| [RASER](https://aclanthology.org/2026.findings-aacl.219.pdf) / [DARS](https://arxiv.org/html/2606.06924v2) | 11-17核正文：恢复收益路由；重复采样监督 | 检验执行进度、共享教师标注效率；恢复价值和多观测不作首创 |
| [SCoRe](https://arxiv.org/html/2409.12917v1) | §4–5：离线SFT可偏向不修改；自身分布两阶段RL与改善奖励 | 对照KEEP坍缩及增量奖励；本项目全KEEP尚未证明同因 |
| [LEVER](https://arxiv.org/abs/2302.08468) | 问题/程序/执行结果验证，结合生成概率和等结果聚合重排 | 补丁价值须与此类正确性验证适配比较，检验相对原程序的增量和联合编辑信用 |
| [SSR](https://arxiv.org/html/2610.05976v1) | 11-17读§2–3：冻结生成器、同骨干LoRA采纳门；首穿越监督、同前缀排序及结果RL | 生成/采纳分离已有；检验同状态候选区分，不能只学题目难度。本项目拟用确定性程序结果与剩余修复，需实证差异 |
| [MOTIVE](https://arxiv.org/html/2610.07018v1) | 11-17读§2–3：多视角正确性监督、可靠性校准及accept/rethink；VLM共享骨干 | 可靠性学习和按需重思已有；参考校准与验证能力分析，保持本轮金融程序范围 |
| [Agent-R](https://arxiv.org/html/2501.11425v1) / [STeP](https://arxiv.org/html/2505.20023v1) | 11-14重核§3.1/§3.4：选择纠正转接点；教师反思、错误mask及成功轨迹混训 | 直接借鉴，比较普通纠正与具体片段/条件规则 |
| [PEAM v2](https://arxiv.org/html/2605.27762v2) | §3.1–3.4：失败/纠正对BC+DPO、隔离LoRA、执行失败回退、效用巩固 | 失败适配和条件回退已有；未复现代码/成绩 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 条件化WITH/WITHOUT效用、Load/Abstain | 条件效用已有；公开包guoshaung/SkillApt，73db0b54，旧404不代表无代码 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | §3.1–3.4：诊断/原则绑定、执行锚点、保留约束、重执行及效用门 | 同信息/候选/成本适配；自最新候选续搜并返回最佳，不能以中间零收益推断无法越过 |
| [HASP](https://arxiv.org/html/2605.17734v2) / [代码](https://github.com/HolaYan/ExecutableSkills-HASP) | §2.1–2.3/D：触发/改写、corrective context、四信号RS/SFT；2a0e859e含配对重生成 | 纠正上下文和后续结果信用已有，改进须落到具体规则 |

## 历史机制近邻：按需展开

| 机制 / 来源 | 已核内容与使用边界 |
|---|---|
| [REBEL](https://arxiv.org/abs/2404.16767) | 策略相对奖励回归；旧逐行配方已闭合，再用时作为骨架对照 |
| [InfoPO](https://arxiv.org/html/2603.00656) / [Embodied-Corrector](https://arxiv.org/html/2611.15651v1) | 历史核§4.1–4.2/§3.2：真实/遮蔽反馈及诊断下动作概率差；旧四格/DPO停扩 |
| [UniSkill](https://arxiv.org/html/2610.10164v1) / [CaPE](https://aclanthology.org/2023.findings-acl.685/) | 成败参考似然差+GRPO、expert−anti-expert参数差；固定R−O停扩 |
| [SkillCompiler](https://arxiv.org/html/2610.39508) / [SkillSmith](https://arxiv.org/html/2605.15215) / [TraceCompiler](https://arxiv.org/html/2608.02680) | 分别核§III/§3/§3：操作编译/修订、边界回退、轨迹去噪与依赖；程序化组合不是独立增量 |
| [StateGraph](https://arxiv.org/html/2611.02912v1) | §4.3–4.5：依赖核验、历史与失效重规划；[旧v2](results/CONTINUATION_PROGRAM.md#effect-conditioned-v2)仅历史 |
| [AdaMEM](https://arxiv.org/html/2606.05684v1) | §3.1–3.2：成功/动作改变筛选动态策略记忆，反事实动作未实际执行；区分动作改变和任务收益 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | §3.3–3.4/B：参数绑定、部分进度返回、同前缀分叉续行与结果差GRPO；交还和分叉已有 |
| [SkillMorph](https://arxiv.org/html/2610.11858v1) | §2/4：跨轮动作覆盖定位技能编辑、协调修订，固定模型/harness及留出评估；已看实际行为 |
| [SCOPE](https://arxiv.org/html/2611.03116v1) | §3.1–3.4：失败轨迹挖局部技能/经验、组链、同前沿干预与完整蒸馏；局部成功拼接已有 |
| [SkillCAT](https://arxiv.org/html/2606.13317v1) | 同题成败分歧、源副本回放、0→1/1→1及层级合并；盲合并作基线，代码未独立核查 |

## 反馈与测试 oracle 的近邻

| 来源 | 已核范围 / 约束 |
|---|---|
| [TACR](https://arxiv.org/html/2610.03984) / [Bayesian Control](https://aclanthology.org/2026.emnlp-main.1548/) | 差分执行/覆盖、修好修坏转移、Beta均值；核官方2a3de1dc。普通诊断/条件转移为强基线 |
| [Rethinking Self-Repair](https://arxiv.org/html/2611.06863v1) / [PracRepair](https://arxiv.org/html/2606.17612v1) | 固定指导/同预算重试、执行差异及至多3轮修复；整理反馈本身不是新机制 |
| [World Model Predictive Paths](https://arxiv.org/abs/2610.28945) | 仅摘要：候选动作、世界模型、MPPI选择及双支记忆。正文/代码未核；WorldRepair原PDF受验证页阻挡 |

## 其他近邻索引

[tau2](https://arxiv.org/html/2506.07982v1)§3已有双侧工具协作/进度；v1.0.1 fc0055dc已接入。[反应式先导](results/CONTINUATION_PROGRAM.md#reactive-v1)三组成功，自动介入曾误判正确Say；不同领域仍是同benchmark。

Git e920668f保留WER/Skill-α，17d4885f保留ReGAL，6a2b8382保留CodePhage/Getafix/CEGIS/CESS、SkillComposer、ASPIRE；其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。

## 对本项目实验的直接约束

同任务、公开信息、工具和预算比较普通纠正/规则及最近机制；按失败来源分组，训练子集不当独立确认。原生结果区分恢复与错改，形成/训练/执行及未知成本保留。提示适配不称完整复现，合法格式或AI检查不作任务成功；全表重跑不是启动门槛。

Token对比：[CRINGE](https://aclanthology.org/2023.acl-long.493/)、[UniSDv3](https://arxiv.org/html/2605.06597v3)；[首分叉历史](results/FINQA_CORRECTION_METHOD.md#branch-neighbors)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
