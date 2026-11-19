# 第二篇：近邻、重合与实验判别

> 2026-11-18｜原始文献与既有代码对齐，英文论证见[现役正文](IJCNN_MANUSCRIPT.md)。已读机制不等于复现成绩；旧详表见Git bdb85edb/89ca0dbd，当前执行只读[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 当前裁决

现役方法是成对执行状态纠正＋共享教师多状态效用。增量落实为同一错误反例在恢复前后分配监督，以及固定教师轨迹跨实际本地状态复用标签；保持与纠正的分解、token负监督、后验接管及恢复收益均有先例。论文报告匹配对照与局部增益，纳入早53平局、新TAT退化及T₁恢复—保持取舍；旧提案器/首分叉调参不再作下一候选。

## 两项贡献的优先补强

1. **本地纠正先补恢复后单侧对照。** CCT 已用错答修复和正确保持共同训练，CARE 已通过可验证结果构造与正例接近的困难负例。本文的问题是，对同一条实际执行后仍错误的反例，在真实恢复前和恢复后都施加监督，能否比仅一侧监督更好地保住正确结果。现有恢复前单侧与成对结果支持继续拆解。先配对检查既有模型面对同题正确与错误起态时的原生恢复和错改，再补恢复后单侧训练，固定正例、反例、累计负监督权重与优化预算。若恢复后单侧已经达到成对效果，将贡献归于恢复后反例监督。 [CCT §6](https://aclanthology.org/2025.acl-long.203/) · [CARE](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_CARE_What_Fails_Contrastive_Anchored-REflection_for_Verifiable_Multimodal_Reasoning_CVPR_2026_paper.html)
2. **接管先区分监督复用和教师可恢复性。** CIR 已通过同状态的继续与干预分支学习恢复净收益，RASER 已学习何时追加检索。本文固定同题教师输出，将其与多个实际本地程序配对。训练缓存中，96 条教师轨迹得到 252 个视图，210 个视图采纳教师，42 个视图保留本地。45 个效用标签随视图改变的来源中，41 个在所有视图均采纳同一教师。这 41 个来源的效用标签差异由本地正确性变化解释。优先用同一批教师轨迹比较联合效用与分开预测本地正确、教师成功的基线，统一保护器、输入可见性与调用预算，单列本地错题上的教师成功区分及低预算净恢复。分析先用训练缓存与既有开发、前向结果，封存确认集维持原协议。 [CIR §3–4](https://arxiv.org/html/2610.00372) · [RASER](https://aclanthology.org/2026.findings-aacl.219.pdf) · [现有对照](results/IJCNN_EXPERIMENT_TABLES.md)

**下一版引言与方法归因。** 先说明已有研究分别处理了纠错／保持、有限预算介入和金融尺度后处理。本文的统一问题是在固定本地模型与教师预算下，怎样把已执行的进度转成可重复利用的训练监督。在 A 对照 CCT 的保持／修正训练与 CARE 的执行筛选难反例，明确本文比较真实恢复前后固定负监督的放置；在 B 净效用定义附近引用 CIR 的配对恢复收益，注明本文复用一条原快照教师轨迹来监督多个本地结果；在 C 对照 TAGOP 尺度预测和 Thokal 的确定性尺度规则，报告接管后两种学习适配器在新表打平，再把成对适配的优势限定到已有证据。详见[同模型排序](results/IJCNN_EXPERIMENT_TABLES.md#same-head-routing-readout)与[同算式尺度对照](results/IJCNN_EXPERIMENT_TABLES.md#matched-teacher-scale-adapters)。 [CCT §6](https://aclanthology.org/2025.acl-long.203.pdf) · [CARE](https://arxiv.org/html/2512.19554) · [CIR §3–4](https://arxiv.org/html/2610.00372) · [TAGOP §3.3](https://aclanthology.org/2021.acl-long.254.pdf) · [Thokal, FinNLP 2026](https://aclanthology.org/2026.finnlp-1.16/)。

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
