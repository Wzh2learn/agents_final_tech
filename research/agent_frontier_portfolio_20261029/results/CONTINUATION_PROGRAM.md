# 纠正学习：机制知识与经验索引

> 2026-11-14｜吸收最近三轮完整讨论；Goal paused。这里解释已有证据怎样支持方案，当前计划见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，最新具体训练/能力见[专题](FEEDBACK_INTERACTION_LEARNING.md)。原始结果、失败及成本保留；历史过程按锚点读取。

<a id="mechanism-knowledge"></a>
## 一条研究主线，三个知识来源阶段

**从真实执行成败提炼有效恢复片段，学习与当前反馈和执行状态匹配的小型纠正能力，在金融文档/表文问答任务上提高完成率或减少无效执行。** 强模型真实接续可提供监督；小模型/LoRA既可增强原Actor，也可作按需调用的外挂。前两阶段为纠正训练提供内容、条件和结束位置，第三阶段已有最直接的模型收益。

| 阶段 | 已有经验 | 如何进入方案 |
|---|---|---|
| 经验使用 | 历史有条件节费；更长或文字更准确未必改变行动 | 保留能决定下一步的证据、参数和当前条件，作为纠正输入；不预设先做复杂记忆选择器 |
| 可执行纠正 | 失败整题含有效片段；旧整流程易错在绑定、重入、参数和交还 | 提取完整恢复片段及触发/结束监督，保留成功局部与失败边界 |
| 训练与融合 | 恢复训练与普通训练有真实差别；简单平均有进一步成本信号 | 以已有恢复SFT作起点，选择片段监督/条件对比/正常能力保留中的一项改进 |

推进顺序为正向深化→机制假设→参考已有工作完善→同条件对照/消融。允许组合和优化已有方法，不要求所有组件原创或所有benchmark领先。小样本能启动候选；结论强度随验证增加。选定范围内的预定结果完整报告，不能只留有利题。

## 已有证据—机制—可借鉴部件

标签含义：正向=任务/成本有开发信号；局部=中间行为有效；无增量=当前实现未胜必要基线；未暴露=没有测到该机制。每行均给出下一可用知识，不把所有失败合并为无效。

| ID / 阶段 | 观察事实与结果 | 机制推断及可用于方案的内容 | 比较或边界 / 证据 |
|---|---|---|---|
| K01 训练：正向，优先 | 同8B父模型，F/O/R为4/12、6/12、8/12；R对O新增2题、未丢题，执行tokens8,192,852→5,166,975（−36.93%） | 从模型实际失败状态训练恢复接续；保留现成LoRA与7组监督，优先提炼恢复窗口和有效续行 | O/R各192更新，监督8,239/8,378tokens，内容/上下文不同；不是单纯更多更新，也未识别独立新算法。[训练与全36槽尸检](ALFWORLD_LEARNING_RUNTIME.md#paired-autopsy) |
| K02 训练：局部机制 | O/R非法反馈412→13；clean263→11，clean成功却均2/6 | 合法动作学习已生效，下一残差是目标相关恢复、继续搜索和退出；可区分“合法”与“有用”的监督 | R在8题更省、4题更贵，72.12%节省来自两题新增成功；不能只统计非法率。[同源记录](ALFWORLD_LEARNING_RUNTIME.md#paired-autopsy) |
| K03 融合：正向线索 | 两新任务R/平均均2/2，平均90,850→72,938tokens（−19.72%）；R−O为1/2，部分动作只成普通文字 | 保留普通执行能力与纠正能力，固定平均是可复用强参照；可提正常能力保留/条件融合改进 | 两题、0新优化；平均/差分有效rank16而R为rank8，不能单归因能力保留。已有算术与短路失败不算创新/节费。[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#feedback-residual-v2) |
| K04 使用：正向 | Astropy目标均成功；普通历史reported tokens491,274→268,655（−45.31%），普通skill553,232 | 经验价值取决于是否保留决策所需证据；用于设计紧凑但可执行的纠正输入 | 一目标一次；reported含cache，形成费另算，不能直接称省钱。[四臂记录](ASTROPY_ISOLATED_CONTROLS_20261106.md) |
| K05 使用/行动：局部 | soapbar冲突写入进度仍操作错误物；两处文字修订与普通均9动作成功，计writer后更贵；旧heat新会话恢复而原会话失败 | 正确诊断须接到动作；研究输入与执行闭环，文字摘要不能替代恢复片段；保留上下文条件效用 | 会话/历史/提示共变，不能只归因清空。[新增来源](ALFWORLD_ADDITIONAL_SOURCES.md)、[上下文](ALFWORLD_CONTEXT_STUDY.md) |
| K06 片段：局部 | tau2失败程序各保留充值/网络恢复等正确效果；62段仅5个非零宏效果；完整旧节点会冻结错误解释和退出 | 全题0分中提取局部有效片段；学习参数、重入和结束位置，避免重复执行有副作用动作 | 不能把中性段当负例，也不能把用户动作全归给Actor。[失败效果](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#effect-witness-v1) |
| K07 片段复用：条件正向 | 同前缀历史/回跳关/开均成功，473,214/290,287/269,054tokens；另两题自动反馈更新较Actor少20.69%执行tokens | 学会何时调用短片段、何时交还，局部自动化有节费价值；用于设计外挂的触发/终止 | 扩样程序3/4而Actor4/4、总体更贵；另一批片段比Actor贵27%。新保护未触发，不能把收益归给它。[同现场](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#prefix-v1)、[扩样](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#expansion-v1) |
| K08 编译更新：源内有效 | SymPy运行见证＋参数溯源、非空前提使公开控制6/9→9/9；Django普通反馈形成可执行修复 | 可复用的参数绑定、前提归纳、反例更新与可执行片段工具；允许用经典方法作方案基础 | Django目标普通反馈6请求/23,244，重绑定12/107,282，无增量；先改一条实际不足。[来源闭环](FCCL_FORMATION.md#execution-fragment-v1) |
| K09 适用条件：局部 | Astropy两个源码状态对mask/unit单修复收益矩阵为[[1,0],[0,1]]，但完整合并修复两状态都成功 | 条件监督素材可保留，研究需面对“统一完整修复”强参照；不能据交叉矩阵就宣布复杂选择必要 | 一曝光问题、D提取片段，不是自主发现或两独立任务。[四格](FEEDBACK_INTERACTION_LEARNING.md#feedback-interaction-v1) |
| K10 模型/入口：未见学习收益 | BC/DPO/逐行/耦合真实训练后，两个代码任务六组均0/2无编辑；直接给源码报错的8B三组也0/2。DeepSeek修一题＋179回归 | 训练入口、任务难度与模型能力共同匹配；代码负结果不否定K01，金融主线选学生可执行的任务 | 固定请求帽；只停当前配方，强模型成功不是方法收益。[训练/能力](FEEDBACK_INTERACTION_LEARNING.md) |
| K11 简单策略：本面板无残差 | 14个历史失败现场两规则均14/14；同现场普通继续与提醒均2/2 | 规则与普通接续进入强基线；方法可在其他错误族发挥，不在已饱和面板训练复杂选择器 | 规则的信息面不同于早期Actor，不能把历史分数直接做同信息比较。[规则](ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)、[接续](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#fragment-continuation-v1) |
| K12 旧失效：未暴露 | 经验未进入请求、长行截断、动作只在reasoning、原wheel含未来修复、4B接入OOM、训练无最终可评估adapter | 区分传输/交付/来源问题与语义方法失败；有效局部、接口修正和已完成O/R训练均保留 | 缺口标明用途，不伪补成功/费用；不增加每轮资格层。[代码素材](CODE_SOURCE_CORRECTIONS.md)、[ALF运行](ALFWORLD_TEXT_AGENT_20261106.md) |

<a id="mechanism-candidates"></a>
## 从知识提出可执行的候选

**优先候选：反馈与执行状态绑定的片段级纠正学习。** 输入为任务、当前可见证据、执行状态和真实反馈，输出为一段恢复操作及接续。首版以普通恢复SFT为基础，选一个规则改进，其他部件保持简单：

- M1 恢复片段监督：从实际错误现场定位有效恢复及正常接续，重点学习改变后续行为的片段。K01/K02/K05提供依据；用同一批失败轨迹比较普通恢复SFT、STeP式部分mask和新增规则，成功SFT另作参照。报告实际监督tokens/更新；需要时用等监督token对照分离采样量与位置效应。
- M2 条件对比：同类反馈在不同证据/状态下的可执行纠正不同，以实际续做结果形成正、负或无差别监督。K06/K08/K09提供素材；完整简单修复、普通反馈及相关近邻作对照，不把条件化或DPO本身当新发明。
- M3 能力保留与融合：利用普通成功经验保持正常行为，比较固定平均与一种具体保留/融合规则。K01/K03提供依据；不重新搜索静态R−O系数。

这三项是同一主线的机制来源。首版暂优先M1的恢复片段定位/加权，与完整教师接续的普通恢复SFT比较；M2/M3为扩展，融合需对齐有效rank/scale。结束/交还先用简单规则。训练内容差异可作为机制，控制共同来源划分、学生与预算，不要求各方法逐token相同。组合改进可以成为贡献，用关闭新增规则的消融说明具体作用。

11-14重读[STeP §3.4](https://arxiv.org/html/2505.20023v1#S3.SS4)及[Agent-R §3.1](https://arxiv.org/html/2501.11425v1#S3.SS1)：前者已屏蔽错误步骤并混合成功轨迹训练，后者已选择纠正转接点。首版可直接借鉴，新增规则需明确“边界怎样确定、权重怎样变化、为何改善执行”，而非仅改名为片段监督。最先排除的替代解释是合法动作与循环控制；反馈关闭/打乱在可解释条件内作消融，不把训练未覆盖的乱码输入当因果证据。

金融任务中的取数、单位换算、公式/工具执行和答案接续是候选错误类型，不冒充已运行结果。主benchmark在FinQA/TAT-QA中核资产后选择，第二相关集为增强。训练可利用标注程序/答案构造恢复；测试时仅使用当前证据、工具执行或可见一致性反馈，隐藏答案只作最终评分。Paper E旧FinQA探针未重算下游结果，不能直接充当完整纠正学习样本。

工具返回错误与“程序合法但最终答案错”须分别统计；后者没有天然的在线错误标签。外挂可固定调用或基于公开信息触发；比较纠正内容时固定调用条件，若研究调用时机则另作消融，隐藏答案不能决定调用。整体Agent收益和给定失败现场恢复收益分别报告。形成/训练成本按使用量摊销，保留直接强模型执行参照。

## 金融资产怎样直接复用

| 已有资产 | 本轮查到的事实 | 恢复后的用途与边界 |
|---|---|---|
| FinQA原数据 | GB10暂存train/dev两文件已重新读hash并匹配[既有执行器绑定](../../finqa_causal_exposure_20261010/executor_contract_v1/finqa_executor_contract_v1.py)：6,251/883例，共7,134；没有新下载或模型调用 | 可优先评估主benchmark的失败采集与恢复监督；还需查既有曝光及报告级划分，不把历史曝光样本当独立确认 |
| FinQA终值执行器 | [既有决定](../../../docs/decisions/001-finqa-executor-scope.md)记录7,134例终值精确回放，但不支持旧qa.steps.res/answer的因果映射；本轮只读代码/历史记录，未重跑执行器 | 复用官方算子和终值执行，在新Agent任务命名空间评价实际程序/答案；无需为新主线重建旧D字段映射。旧0/89探针不当纠正样本 |
| TAT-QA与Paper E表格素材 | 已有[许可记录](../../../docs/datasets/tatqa_licence_record_v1.md)与表格来源；本轮未重新哈希完整原数据 | 候选主集或相关集，用于证据/表文绑定及泛化；不重开冻结TAT-DQA实验。原始数据、过程反馈和派生表头任务分别标明 |

知识库使用成本口径：执行tokens含缓存，不能直接等价钱或新增算力；另计教师/失败采集、经验形成、训练和使用。既有来源共享费用只记一次，缺失研发/硬件用量保留未知。与普通基法的比较先控制来源、学生与预算，训练内容和监督位置的变化可以是要研究的机制。

## 20份主题记录的用途清点

| 记录组（完整枚举当前20份结果页） | 保留位置与用途 |
|---|---|
| ALFWORLD_LEARNING_RUNTIME；CONTINUATION_PROGRAM | 当前训练资产和机制知识；优先K01—K03 |
| ALFWORLD_CORRECTION_DATA；ALFWORLD_RUNTIME_CONTEXT_COMPARISON | 监督形成、96＋32及恢复对照历史；不按旧“下一批”执行 |
| ALFWORLD_ADDITIONAL_SOURCES；ALFWORLD_CONTEXT_STUDY；ALFWORLD_TEXT_AGENT | 历史现场、规则、上下文与通道；K05/K11/K12，按锚点加载 |
| ASTROPY_PILOT；ASTROPY_PROFILE_CONTROLS；ASTROPY_ISOLATED_CONTROLS | 区分旧可读面/污染边界和隔离结果；K04，不合并不同信息干预 |
| MATPLOTLIB_QUALIFICATION；MATPLOTLIB_ISOLATED_CONTROLS | 原生控制与真实修复/回归；源误修和旧对象状态供条件监督 |
| DJANGO_AGGREGATION_PAIR_QUALIFICATION；DJANGO_AGGREGATION_AGENT | base/reference与实际产物分开；有合格产物不等于自然完成 |
| SYMPY_LATEX_TRANSFER；CODE_SOURCE_CORRECTIONS | 源成功、迁移失败、接口与源码修复；K08/K12，当前只保留素材 |
| QWEN4B_TOOL_QUALIFICATION；SCHOOL_MODEL_CAPABILITY | 模型/接口能力，不作方法效果；不将4B接入设主线前置 |
| FCCL_FORMATION；FEEDBACK_INTERACTION_LEARNING | 来源及校园唯一总账；闭合候选训练/能力结果，保留但不继续扩训 |

早期地震/股票/办公、aiohttp、Requests、Sphinx及其他来源通过[历史主题索引](../../../docs/archive/2026-11-06_agent_research_context/README.md)保留。材料按“当时发生什么—哪些有效—失败条件—机制推断—可改规则—必要对照—下一辨别”关联；知识用于方案、训练样本与消融，不新增数据库或自动反思层。

## 本次整理的证据范围

机械盘点科研目录319份md/py/json/jsonl、20份结果页；主题结论按上表归位。36槽原生结果、36份receipt/manifest与11,694项绑定本轮离线匹配，4/6/8成功及成本相符；既有成对尸检hash匹配。能力116和入口186载荷包重新逐项验hash。未重跑任何模型、训练、环境或原生测试；并非所有历史raw的全量独立重演。

本次审稿人视角复核与机械核验均由D完成，无新增独立C或外部专家审阅。机制仍为候选，现役计划与暂停状态见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。完整过程/成本快照见[历史原文](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md)。

### 11-14追加自问：从目标反推，再核事实

模式为 first-principles → fact-check；读取当前计划、训练/尸检记录，并重核上述两篇原文。只分析与修正文档，未复现原法、未新增科研运行；其他对话工件和历史原文不变。

| 自问 | 证据判断与修正 |
|---|---|
| 是否又在做审计框架？ | VALUE：交付是学到纠正能力并改善金融任务；日志/核验只支持验证，不作为方法贡献。 |
| 正向是否已说明机制？ | FACT：R配方有单seed任务/成本收益；INFERENCE：失败接续值得深化。未分离内容/上下文/合法动作效应，继续从这里设计，不丢弃收益。 |
| 首个候选是否已具体？ | UNVERIFIED：M1还需明确一条边界或权重规则。恢复后先用少量开发轨迹完成定义，和普通恢复/部分mask比较；不直接扩训。 |
| 换到金融领域就一定有效？ | UNVERIFIED：原数据与执行器可复用，效果尚未验证。先选一个可运行主集，公共反馈与隐藏评分分开；不要求跨领域全胜。 |
| 新旧待办是否冲突？ | FACT：近邻表原有“四格/逐行仍待验证”已改为历史闭合，不会再当当前队列。 |
| 何时停止具体变体？ | 风险是收益仅由廉价规则或额外信息解释；同效更贵则停该变体，保留有效基础与素材。若成功率/成本取舍改善，完整报告后继续。 |

下一步仍为恢复后的一项具体学习改进＋金融主集小开发验证；本轮完成的是自问与核查，没有产生新的方法有效性结果。

## 兼容旧锚点

旧链接仍可找到原批次；以下跳转不产生当前待办。

<a id="feedback-interaction-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#feedback-interaction-v1)

<a id="feedback-policy-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#feedback-policy-v1)

<a id="feedback-residual-v2"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#feedback-residual-v2)

<a id="fragment-continuation-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#fragment-continuation-v1)

<a id="fragment-transfer-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#fragment-transfer-v1)

<a id="binding-update-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#binding-update-v1)

<a id="deployment-timing-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#deployment-timing-v1)

<a id="feedback-transfer-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#feedback-transfer-v1)

<a id="local-edits-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#local-edits-v1)

<a id="phase-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#phase-v1)

<a id="normalized-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#normalized-v1)

<a id="witness-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#witness-v1)

<a id="expansion-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#expansion-v1)

<a id="prefix-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#prefix-v1)

<a id="effect-witness-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#effect-witness-v1)

<a id="preservation-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#preservation-v1)

<a id="cross-batch-autopsy"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#cross-batch-autopsy)

<a id="reactive-v1"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#reactive-v1)

<a id="residual-option-v3"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#residual-option-v3)

<a id="activation-v2"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#activation-v2)

<a id="effect-conditioned-v2"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#effect-conditioned-v2)

<a id="反馈交互学习已按主题分离"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#反馈交互学习已按主题分离)

<a id="复用or训练两条新任务检验平均与差分"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#复用or训练两条新任务检验平均与差分)

<a id="同现场续做普通继续已足够固定提醒未见增益"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#同现场续做普通继续已足够固定提醒未见增益)

<a id="完整纠正片段两新任务八组闭合局部修复未带来总体增益"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#完整纠正片段两新任务八组闭合局部修复未带来总体增益)

<a id="绑定修订两类互补独立一致性配方停止"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#绑定修订两类互补独立一致性配方停止)

<a id="部署时点12组保留条件收益停止扩跑"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#部署时点12组保留条件收益停止扩跑)

<a id="新任务五组成功保留与执行成本信号"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#新任务五组成功保留与执行成本信号)

<a id="源内自动反馈修订已闭合"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#源内自动反馈修订已闭合)

<a id="早期阶段化原型"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#早期阶段化原型)

<a id="旧标准化十组保留条件差别及完整费用"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#旧标准化十组保留条件差别及完整费用)

<a id="原先导输入错误保留形成产物复用"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#原先导输入错误保留形成产物复用)

<a id="旧四配置20组停止整流程接管保留局部价值"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#旧四配置20组停止整流程接管保留局部价值)

<a id="旧同一现场续做保留复用与路由收益"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#旧同一现场续做保留复用与路由收益)

<a id="旧失败进一步变成条件纠正监督局部效果与执行归属"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#旧失败进一步变成条件纠正监督局部效果与执行归属)

<a id="旧部分保留与控制流程修补已完成停止整节点冻结"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#旧部分保留与控制流程修补已完成停止整节点冻结)

<a id="修正判断方式"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#修正判断方式)

<a id="历次结果与可用素材"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#历次结果与可用素材)

<a id="最值得挖的三类资产与复用收益"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#最值得挖的三类资产与复用收益)

<a id="放宽开发门槛保留事实标准"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#放宽开发门槛保留事实标准)

<a id="尸检导出的方向"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#尸检导出的方向)

<a id="证据范围与当前状态"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#证据范围与当前状态)

<a id="最近先导与固定历史"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261114.md#最近先导与固定历史)
