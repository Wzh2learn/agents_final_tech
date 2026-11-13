# 纠正技能研究：跨批次归因与可复用信号

> 2026-11-13｜综合尸检；本轮新增模型/任务/训练0。已有正向学习、局部修复和成本信号；FCCL独立增量尚待验证。执行只查[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

<a id="cross-batch-autopsy"></a>
## 修正判断方式

**“有没有效果”“为什么有效”“是否超过近邻”分开回答。** 后两项未成立，不能抹掉第一项；整题失败不自动否定有效片段。原生分数保留，局部信号另记，不补计整题成功。停止对象限定为具体配置、实现或饱和面板。

本轮inquiry为first-principles。建立19份现役结果记录的定位，按机制复读相关章节及历史链接；不是重跑所有历史实验。下表最后一列包含研究推断，不冒充已识别因果。

## 历次结果与可用素材

| 实验族 / 原件 | 实际信号 | 归因与素材用途 |
|---|---|---|
| [8B纠正训练→12新布局](ALFWORLD_LEARNING_RUNTIME.md#trained-baselines) | 同BF16父模型F/O/R为4/12、6/12、8/12；R对O新增2题、未丢题，执行8,192,852→5,166,975tokens。 | **正向开发信号**：保留适配器与7组监督。训练配方有效信号与新算法贡献分开；内容/上下文因素仍未分离。 |
| [Astropy隔离四组](ASTROPY_ISOLATED_CONTROLS_20261106.md) | 四组均3/3目标＋132/132回归；普通历史19→10 POST、491,274→268,655tokens，普通skill未超过历史。 | **历史有用，压成skill未必更好**。可定位有效执行细节，不能把“没有新方法”写成“经验没收益”。单次结果待重复。 |
| [Astropy A4/A5恢复](CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-result) | A5动态/普通同为3/3＋132/132，71,472 vs99,200tokens；A4均0/3，最后请求均length。 | 保留A5条件性正向；A4有交付瓶颈。两现场合计动态多60,915tokens，不能只留好例，也不能用合计抹掉A5。 |
| [ALF恢复](ALFWORLD_CONTEXT_STUDY.md)及[full/recent](ALFWORLD_ADDITIONAL_SOURCES.md) | 旧heat原会话失败、新会话成功；clean02近期更省、03完整更省。 | 上下文条件效用候选；会话格式/历史/提示共变，不能单归因清空。逐题oracle只是上界。 |
| [早期SymPy加载](SYMPY_LATEX_TRANSFER_20261106.md)、[ALF通道](ALFWORLD_TEXT_AGENT_20261106.md) | 三经验正文未进实际请求；inline后溢出；旧8B动作仅在reasoning未执行。 | **机制未暴露**，不能作经验语义负例。用于修正送达、上下文与工具通道，保留失败费用。 |
| [旧Astropy可读依赖](ASTROPY_PROFILE_CONTROLS_20261106.md)、[参考辅助来源](MATPLOTLIB_QUALIFICATION_20261106.md) | 旧wheel可读面含未来修复，故不能当参考隐藏证据；另有明确标注的source参考补丁＋真实执行。 | **来源身份决定用途，不等于全作废**。污染旧成绩不作干净迁移结论；参考辅助可作教师材料并给强基线同信息，不能冒充Agent自主成功。 |
| [27B能力](CODE_SOURCE_CORRECTIONS.md#native27-capability)、Sphinx | 不推理档未编辑，低thinking档修好公开数组赋值但完整1/2；Sphinx多次读取不编辑，换工具仍未修好。 | 能力/动作落实瓶颈。不能一概归因4bit：旧分叉请求标识27B FP8，最新DeepSeek程序亦有逻辑错误；实际模型配置分批绑定。 |
| [绘图公开复现](CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)、[SymPy12481](FCCL_FORMATION.md#new-source-v2) | 三候选均解除原公开崩溃，较强辅助验收未过；12481为1/1＋7/7，额外两失败在base也存在。 | **整段失败中有真实修复**。公开行为、既定评分、新增退化分报，共同既有失败不算方法新增错误。 |
| [源内程序学习](FCCL_FORMATION.md#execution-fragment-v1)、[Django源](FCCL_FORMATION.md#formset-source-v1) | 参数溯源＋非空前提使公开控制6/9→9/9；Django纠正达3/3＋49/49。 | **真实更新闭环已有**，保留反例、守卫、绑定和程序。可由经典候选消除/普通修复解释，不等于没有可用学习部件。 |
| [Django新任务四组](FCCL_FORMATION.md#formset-target-v1) | 四份补丁全过2/2＋157/157；普通反馈6 POST/23,244tokens，候选12/107,282，且未试用原程序。 | 补丁正确、当前重绑定无收益、协议未完整落实分别记。触帽不改称代码失败；停止本版同题追提示。 |
| [ALF进度与文字修订](ALFWORLD_ADDITIONAL_SOURCES.md) | soapbar/soapbottle冲突已送达仍做错；heat任务指导成功、普通/固定skill失败；文字修订未改善已测续做。 | **信息未连到行动**。可执行纠正是合理研究对象；手写指导有额外领域信息，保留作强对照。 |
| [ALF14规则恢复](ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)、异步状态控制 | 领域规则14/14；两个async实现的相反取消选择被API状态规则覆盖。 | **本面板残差已解释**。冻结复杂选择器，规则作参照/回归；不外推所有任务，人工规则研发也非零成本。 |
| [tau2 v2/v3/反应式](#activation-v2) | v2避免重复充值却不修网络，普通编辑修网络却充4GB；v3旧流程阻塞；最新把正常Say回执误当充值写入。 | **局部正确效果＋范围/续行失配**。可学效果保留、参数和退出，不能全题0分丢掉互补片段；也不能称盲合并已成功。 |
| [形成/训练中断](CODE_SOURCE_CORRECTIONS.md)、[梯度试验](ALFWORLD_ADDITIONAL_SOURCES.md) | 规划耗完读取预算无计划；reasoning耗尽输出；4B接入OOM、8B梯度试验无可评估终版。 | 是交付/资源失败，未测到机制收益。O/R另一批已各完成192更新，不能混写成“从未训成”。 |

## 本轮挖出的三个重点

**纠正训练可能有摊销价值。** 新核36个receipt及72项receipt/manifest绑定，F/O/R仍为4/6/8题成功。此前已核来源组件＋本批执行：R为2,953,267＋5,166,975＝**8,120,242**，O为500,683＋8,192,852＝**8,693,535**tokens，R少573,293。此处未完整纳入训练/筛选/研发/硬件，不是全成本胜出；但不能因形成较贵便排除它。保留为正向学习参照。

**双方成功仍能提供效用候选。** 新核两组分叉30份请求/SSE、参数及原生日志hash：heat先取杯/先去炉灶都成功，24,234 vs47,984tokens；cool先去冰箱/先加热苹果都成功，131,971 vs116,726。按现有15%成本带作**本轮后验筛查**，heat为49.50%成本候选，cool的11.55%保留TIE；旧“没有成败偏好”不变。只一臂一次、自定义environment_step而非OpenCode，不推期望效用，不把整段信用全给首动作，不能跨题训练A/B字母。

**全题失败中的正确效果值得学习。** v2“只充2GB”和普通编辑“恢复网络”，Sphinx“隐藏类型但新增重复签名”，可产生“保持已实现效果、修正剩余问题”的监督。需实际执行验证，不用生成说明充当真值；当前盲合并只有局部探针，没有完整联合原生结果。

## 放宽开发门槛，保留事实标准

1. **分开发、扩样、论文结论。** 单题局部信号足以产生下一候选，重复与跨题放在扩样阶段；不先要求独立统计确认才准尝试。
2. **不要求每题每指标全胜。** 比较条件性成功率—成本和回归；无显著不等于无效，单次省token也不等于已证明省钱。一次负结果停实现，不关主问题。
3. **来源不必整段完美。** 失败轨迹中的真实有效片段可训练，连同失效条件、未解目标保存；Actor退出与环境/代码成功分报。单步纠正也能有价值，不强行多步求复杂。
4. **成本按实际部署计。** 全项目物理总账保留；方法比较分共同来源、额外形成/搜索/训练、执行，在明示N个后续任务下摊销。不重复收整笔历史研发，也不删失败形成费；token不等价计算/货币。
5. **资格只约束相应主张。** 源PR已合入目标base只对特定历史迁移主张必需，不是所有经验复用的必要条件。base/reference共有既有回归失败可在新协议单列、比较新增退化；参考辅助材料标为教师来源而非自动废弃。旧分数不回改。
6. **从真实失败生成候选，再配对取得监督。** 不必先在档案凑齐完美四格。g未触发时不评价未执行π；同信息、同预算和明确反例足以启动开发小试。

## 下一动作

优先从**已实现效果保留＋剩余纠正的局部续行**形成学习规则：用真实部分修复的前提、动作、效果和后继反馈生成局部更新；比较同信息普通整模块修订及类型/回执规则＋原策略。g/π作为诊断分解，不再设完美因子实验为前置；不重跑饱和面板或旧四组。

局部修订、执行程序、组链均有[近邻](../IJCNN_RELATED_WORK_REFRESH_20261030.md)。下一用具体更新与新任务收益判别增量，无须先声称通用新理论。训练适配器、普通历史与真实部分修复均是可用资源，方法仍随证据调整。

## 本轮证据范围

新核19份结果文档的定位/hash，36条训练迁移receipt/manifest及所存终态，Astropy两份completed和所存评分，分叉30份请求/SSE的hash/usage/参数及world日志hash。未重跑环境、未重核所有历史SSE/模型权重，未重新全面外查文献；其余为项目记录支持，不升级成本轮独立复现。

私有双端 `autopsy_reuse_20261113/RECHECK.json` SHA-256 `959566614a474dce648fe3b0ee6fc865e874f2e47d7f6d08b8c3cbd257aaf71b`；脚本同目录。GB10前缀 `/home/testuser/wzh/research_evidence/agent_learning_20261030/`，本机前缀 `D:/Documents/Loop_D_assets/agent_learning_20261106/`。校园累计仍**1,753请求/17,446,160已知＋8旧未知预留2,097,152**；本地历史调用不是该校园账。本轮0新增科研调用。

<a id="reactive-v1"></a>
## 最近先导与固定历史

[0954279f反应式完整记录](https://github.com/Wzh2learn/agents_final_tech/blob/0954279fdfe88414f730ad350dd3dbb256016f6c/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#reactive-v1)：三组原生均成功，唯一介入为回执误触发；执行464,898 vs同信息历史441,298tokens。当前关键词策略停扩，接口保留。149请求/1,450,383tokens已计；558载荷包SHA `6b308e7f8e3c8f7e08f992b4e3a7806815f18f1bb70c883f395df1818aa456ec`。

<a id="residual-option-v3"></a>
[v3完整记录](https://github.com/Wzh2learn/agents_final_tech/blob/0d09bc14dac2793c3bbafdecc7c5bafdea41aae2/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#residual-option-v3)：旧流程阻塞后继纠正，173请求/1,984,377tokens已计。

<a id="activation-v2"></a>
[v2激活/消融](https://github.com/Wzh2learn/agents_final_tech/blob/6a2b838236ff36b430e180b762091dbe453c10d7/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#activation-v2)：重复充值与网络恢复的互补失败，231请求/2,241,365tokens已计。

<a id="effect-conditioned-v2"></a>
[v2来源/数量反例](https://github.com/Wzh2learn/agents_final_tech/blob/f8cd77729665eb8cf8491ec78c716aa63c037b40/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#effect-conditioned-v2)及[v1](https://github.com/Wzh2learn/agents_final_tech/blob/7836c893c3926ea97f2d337b6790b097f63c59f7/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md)。原件未改；未投稿、付款、外部联系或生产操作。
