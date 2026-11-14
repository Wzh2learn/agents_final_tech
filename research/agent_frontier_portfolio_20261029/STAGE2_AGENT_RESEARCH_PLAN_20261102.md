# 第二阶段：反馈条件化的可复用纠正技能学习

> 2026-11-14。[能力与纠正入口](results/FEEDBACK_INTERACTION_LEARNING.md#capability-entry-v1)已闭合：DeepSeek＋OpenCode解决Astropy并通过179项回归；8B基础/逐行/耦合三组即使拿到源码和报错仍无修改。停止该8B配方扩训，主目标不变。

## 目标与保留资产

从真实执行反馈学习可复用的纠正条件、内容、参数、续行与退出，以新任务原生成功、回归及形成＋执行成本裁决。FCCL为工作名；配对执行服务监督，不以审计或新载体代替学习贡献。运行只用公开信息，隐藏状态/评分不入Actor。Paper E/开题由独立对话维护。

- [已有8B训练](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)：R/O/F为8/12、6/12、4/12，R多2题未丢题，较O少36.93%执行tokens；不是本轮新机制的确认。
- [R/平均探针](results/CONTINUATION_PROGRAM.md#feedback-residual-v2)在两条新ALF任务均2/2，平均较R少19.72%执行tokens；固定差分1/2已停。保留适配器、实际纠正段及费用，不从零重训。
- [Astropy历史](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)与[同现场复用](results/CONTINUATION_PROGRAM.md#prefix-v1)条件成本线索保留；旧整流程接管、源内闭环、旧四组及饱和面板不重跑。

## 本轮裁决

[四格来源](results/FEEDBACK_INTERACTION_LEARNING.md#feedback-interaction-v1)来自同一曝光Astropy15082的两个状态，两条局部修复有条件充分性；完整合并修复亦成功，不能据此证明复杂选择必需。沿用逐行相对奖励回归再加残差耦合，仅为候选实现，没有独立新理论声明。

[真实训练与冷启动](results/FEEDBACK_INTERACTION_LEARNING.md#feedback-policy-v1)：BC、DPO、逐行回归、耦合各24步，同四条完整纠正片段与梯度量级，共96更新/408forward。两个曝光开发任务×六组均在16请求内0/2，无生产修改；原始失败、保存候选重评及来源费用保留。

[本批能力诊断](results/FEEDBACK_INTERACTION_LEARNING.md#capability-entry-v1)：校内DeepSeek两题各12请求，Astropy14995原题1/1＋179/179回归，Matplotlib23562原题0/2＋136/136回归。两Actor都达帽退出，原生补丁成功单列。没有把模型、provider和请求帽的变化当作纯模型规模因果效应。

[匹配纠正入口](results/FEEDBACK_INTERACTION_LEARNING.md#capability-entry-v1)：各组同公开源码与真实报错，8B基础/逐行/耦合两题各4请求，三组均0/2；24次都用于grep，没有生产修改。原始请求证实源码、错误和实际工具反馈均已送达。短预算仍限制结论，但没有证据支持扩大该配方或搜系数。

## 唯一下一交付

1. **使用已验证能力的Actor。** 校内DeepSeek＋现有OpenCode为主要机制验证路径；本地模型的训练/迁移研究保留，不再把8B代码冷启动当成必经门槛。新增Astropy实际成功纠正片段可作真实经验来源，参考gold不进入Agent。
2. **回到同模型的方法比较。** 在既有非参数纠正接口中，检验从成功/失败反馈更新的条件化纠正片段能否改善新目标；比较无经验、普通历史/反馈、完整简单修复及匹配近邻，形成/使用信息和总预算对齐。先固定新任务、学习规则与运行帽，不重复Astropy15082旧四格，也不把教师更强、源码窗口或格式改动当作新方法。若无增益，停止该具体机制并重新设计。
3. **论文目标不缩小。** 稳定收益后扩到至少两项目4—6独立任务，来源隔离留出、必要重复与消融；12月中旬IJCNN评估点保留。未完成：独立方法收益、跨任务泛化、完整强近邻及总流程成本优势。

## 成本与同步

[校内总账](results/FCCL_FORMATION.md#成本与证据定位)已4,993请求/50,815,217已知＋10未知预留2,621,440，合53,436,657/10亿。本批新增校园24/151,776、本地入口24/147,273；旧本地192/1,349,640与训练forward另列，不重复计，cache/reasoning为子集。研发D/C用量未完整核对。

校内116与入口186载荷包均双端逐项验hash；原训练46与冷启动787载荷包保持。GB10 VPN恢复后SSH正常，批次已结束，自有18104释放；其他对话、LoopB及7历史worktree不动。只同步本批代码、结果和现役状态，不追加全库治理。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[旧探索归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。
