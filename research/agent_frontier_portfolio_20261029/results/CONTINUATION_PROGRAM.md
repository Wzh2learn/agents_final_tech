# 纠正学习：机制知识与经验索引

> 2026-11-16｜Goal active；这里解释已有证据怎样支持方案。当前计划见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，金融批次见[FinQA当前记录](FINQA_CORRECTION_LEARNING.md)，旧训练/能力见[专题](FEEDBACK_INTERACTION_LEARNING.md)。原始结果、失败及成本保留；历史过程按锚点读取。

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
| K13 金融训练：互补正向 | 旧8报告负方向2/8对普通/正加权1/8，匹配融合均3/8；新32报告全负14对普通11、3胜0负。终止前移也14，保持13/13、复查34POST，但失去3个语义恢复 | 保留怎样纠正和正确保持两块能力；语法门控回放仍更便宜。两条派生见K14/K15；关键对照已补齐见K16，下一步固定规则做确认 | 成败与费用见[当前机制](FINQA_CORRECTION_LEARNING.md#expanded-boundary-v1)。单seed开发，融合或混合样本本身不另称创新 |
| K14 首步剂量：激活不等于有效修正 | 同51行/日程/96更新，只统一首决策CE系数；工具激活从1/32到23/32，成功却14→11、保持13→9，恢复1个语义错 | 训练改动已连到执行，但全局剂量不能解决状态选择；停止本系数版本，保留负方向修复 | 不把系数和当梯度范数，不扫新权重；后续关键对照与确认，不要求每个派生都正向。[尸检](FINQA_CORRECTION_LEARNING.md#initial-decision-v1) |
| K15 局部置信：生成收益不等于接受奖励 | 同32现场，零阈值的参考相对首分叉仅13/32；原始局部14、整段12/13、公开规则14。96HF前向、0HTTP | 首分叉负方向仍改善生成，不能直接将模型差分当可靠接受信号；停止该门控，保留3胜0负的训练规则，并纳入已补齐的强对照K16 | 全32题/所有预设策略保留，黄金仅评分；不在dev调阈值，不把离线回放算新在线成功。[回放及费用](FINQA_CORRECTION_LEARNING.md#initial-decision-v1) |
| K16 同目标近邻：作用与保持分开看 | 同60正目标/暖启动/96更新，成功上下文14/32（保持11、恢复3），步骤偏好10（保持7、恢复3）；原负方向14（保持10、恢复4）。后者对普通3胜0负，对成功上下文3胜3负 | 更干净的条件也能改善保持；负方向仍有语义纠正，不因同分丢弃，也不把胜过普通当优于最强对照。四方案的新64报告检验已闭合，见K17；停止追加门控 | 本批134POST/572,707tokens；步骤偏好455前向含参考/拒例，原负方向192。单seed开发、非原文完整复现。[结果及成本](FINQA_CORRECTION_LEARNING.md#expanded-boundary-v1) |
| K17 新64报告：修复与错改抵消 | 普通/全负/成功上下文25/64、步骤偏好19；首轮/语法规则27。全负保持18、修复7，普通20/5；主比较4胜4负 | 继续深化语义修复，下一小试只改收尾条件：原30条皆跟在工具后，旧前移仅9条，部署却是新公开状态包；两组同目标/数据/日程检验条件错位 | 新64已曝光，不再作新规则独立确认；320执行/663POST，结果与原失败监督双份。不是整体方法收益。[完整验证及尸检](FINQA_CORRECTION_LEARNING.md#confirmation-primary-v1) |
| K18 收尾小试：目标不能只当结束信号 | 同51目标/两种收尾条件均4/32，低于旧14；原21条恢复解释被裸程序/值改写，每份数据的监督4,362→2,638，并共同重配首决策；两组投影比较无收益 | 旧解释含金融数量、单位和期间绑定；保留这些真实监督，下一只改坏/好状态的统一执行表示。目标删减/权重是否致退化仍待识别；不恢复已停首步权重扫描 | 新包32/32正常/可执行，不能归接口/OOM；131POST/547,254已知＋1未知，完整双份f4e0feee。[小试与尸检](FINQA_CORRECTION_LEARNING.md#terminal-state-v1) |
| K19 真实源扩样：可用资产 | 新64TRAIN源20成功；44失败经教师实际恢复40（39个可执行错、1无效程序），新增60个正向来源；未混入dev | 与旧30组合并训练，各方法共享。3个正常答错、1个POST上限未完成暂不入正监督，保留全部失败和费用；不把形成成功当方法成绩 | 源包e5358889、教师全结果28a7169b双份；教师100POST/496,680tokens。5个不同于参考的正确源程序仍保留。[教师形成与尸检](FINQA_CORRECTION_LEARNING.md#train-teacher-expansion-v1) |
| K20 统一状态下合并保持与纠正 | 同51目标/系数/更新，候选15/32、普通/保持参照14；均保持13/13。候选新增1个增长率语义修复，6个改写都来自原错误现场 | 保留规则、增加语义覆盖；另4个语义改写仍错，不能只提升启动率。1胜0负、区间含0，作开发信号。相对旧全负整策略多1题、推理tokens少25.5%；比语法门控仍贵 | 原生106POST/425,583tokens，全部正常/可执行；训练包3f4a6742、结果27ed19ec双份。单项增量看同条件15对14，不把整配方差异或形成成功全归给分叉。[结果与尸检](FINQA_CORRECTION_LEARNING.md#state-view-v2) |
| K21 扩样与训练材料一致性 | 40个新原生恢复中2组参考/题意冲突暂挂；88组主147正目标逐token一致，成功蒸馏176目标，多29必要提交动作 | 附加项每轮54组/156点，训练损失0.82291→0.01880，正向CE稍高；拟合取舍回到真实修复/错改，不以降loss替代收益 | 三臂792更新/1,410前向完成，d8a47ed2/8f1757ed双份；新42组原生已闭合，结果看K24。[完整材料](FINQA_CORRECTION_LEARNING.md#expanded-state-v1) |
| K22 首分叉表面位置与计算含义 | 156个有效点：82数字/符号、30含字母、44标点/边界；新116个反例中34个边界分别来自16个缺尾步骤、18个中间引用变化，均实际执行答错 | 首token是监督定位，不等于因果错误位置；边界符号也承载程序结构，不能按“标点”名称当无效格式信号删去。若后续有收益，再做匹配剂量的结构/字段消融 | CPU定位0模型调用，a62fdba4分类与f58910d9程序绑定双份；不以该描述代替原生增益。[材料与机制](FINQA_CORRECTION_LEARNING.md#expanded-state-v1) |
| K23 纠正的终点是实际返回结果 | 旧v2一次改正未被最后步骤引用的数字，返回值仍81,161,000；其余未成功分支涉及基期、合计范围及量的选择。新88个正确训练程序共206步，全部通向终值，无冗余步骤 | 不为当前正目标另建剪枝器；保留结构监督与完整解释，后续看新原生结果能否改善终值。局部改写不计为任务成功，也不将旧dev失败转入TRAIN | 37a2ad48结构统计、0506b251六例尸检双份，0模型调用。解释相对固定参考，未改标注或筛除评估题。[当前材料](FINQA_CORRECTION_LEARNING.md#expanded-state-v1) |
| K24 内容纠正与实际提交 | 旧42两臂同13、0工具调用；候选文字回放多修1题。首4次新接入照抄占位词，统一格式后同4次均实际执行 | 接口已接通，但接通不等于学习收益；保留语义信号和相反开发结果，不统一首token或删解释 | 旧主7a053f92/回放b04ccea4、接入578cdb30；ec1ea34d/fdb29f13双份。新64已闭合，见K25。[接入](FINQA_CORRECTION_LEARNING.md#terminal-interface-v1) |
| K25 新增修复与误改 | 新64首轮33、普通34、候选33、原模型复查29；候选修2/错改2，普通修1/错改0。候选新增修复及两误改均涉及数值期间/方向绑定 | 保留语义修复，只改反例更新的保持保护；固定半权重对比同任务成功状态投影，普通CE不动，不加教师或扫系数 | 全量44c55293/包52a32ff1双份；接入65/34通过、2跳过，训练d0e64479已启、128原生7e7d3c97随后执行。[结果](FINQA_CORRECTION_LEARNING.md#test-execution-v1)、[规则](FINQA_CORRECTION_METHOD.md#retention-branch-v1) |

<a id="mechanism-candidates"></a>
## 从知识提出可执行的候选

**优先候选：反馈与执行状态绑定的片段级纠正学习。** 输入为任务、当前可见证据、执行状态和真实反馈，输出为一段恢复操作及接续。首版以普通恢复SFT为基础，选一个规则改进，其他部件保持简单：

- M1 恢复片段监督：从实际错误现场定位有效恢复及正常接续，重点学习改变后续行为的片段。K01/K02/K05提供依据；用同一批失败轨迹比较普通恢复SFT、STeP式部分mask和新增规则，成功SFT另作参照。报告实际监督tokens/更新；需要时用等监督token对照分离采样量与位置效应。
- M2 条件对比：同类反馈在不同证据/状态下的可执行纠正不同，以实际续做结果形成正、负或无差别监督。K06/K08/K09提供素材；完整简单修复、普通反馈及相关近邻作对照，不把条件化或DPO本身当新发明。
- M3 能力保留与融合：利用普通成功经验保持正常行为，比较固定平均与一种具体保留/融合规则。K01/K03提供依据；不重新搜索静态R−O系数。

这三项是同一主线的机制来源。现役方案已收敛为K13的执行验证首分叉负方向＋恢复/收尾CE；M1的正加权与字段筛选作消融，M3的保持部件保留。具体规则、损失与完整训练对照以[金融记录](FINQA_CORRECTION_LEARNING.md#expanded-boundary-v1)为准。控制共同来源、学生与预算，不要求组合中的各组件原创。

11-14重读[STeP §3.4](https://arxiv.org/html/2505.20023v1#S3.SS4)及[Agent-R §3.1](https://arxiv.org/html/2501.11425v1#S3.SS1)：前者已屏蔽错误步骤并混合成功轨迹训练，后者已选择纠正转接点。首版可直接借鉴，新增规则需明确“边界怎样确定、权重怎样变化、为何改善执行”，而非仅改名为片段监督。最先排除的替代解释是合法动作与循环控制；反馈关闭/打乱在可解释条件内作消融，不把训练未覆盖的乱码输入当因果证据。

当前主集为FinQA，TAT-QA原始算术题作相关增强；取数、公式、单位/百分比及程序结构错误分别统计。训练可利用标注程序/答案构造恢复；测试时仅使用当前证据、工具执行或可见一致性反馈，隐藏答案只作最终评分。Paper E旧FinQA探针未重算下游结果，不能直接充当完整纠正学习样本。

工具返回错误与“程序合法但最终答案错”须分别统计；后者没有天然的在线错误标签。外挂可固定调用或基于公开信息触发；比较纠正内容时固定调用条件，若研究调用时机则另作消融，隐藏答案不能决定调用。整体Agent收益和给定失败现场恢复收益分别报告。形成/训练成本按使用量摊销，保留直接强模型执行参照。

## 金融资产怎样直接复用

| 已有资产 | 本轮查到的事实 | 恢复后的用途与边界 |
|---|---|---|
| FinQA原数据 | GB10暂存train/dev两文件已重新读hash并匹配[既有执行器绑定](../../finqa_causal_exposure_20261010/executor_contract_v1/finqa_executor_contract_v1.py)：6,251/883例，共7,134；没有新下载或模型调用 | 可优先评估主benchmark的失败采集与恢复监督；还需查既有曝光及报告级划分，不把历史曝光样本当独立确认 |
| FinQA终值执行器 | [既有决定](../../../docs/decisions/001-finqa-executor-scope.md)记录7,134例终值精确回放，但不支持旧qa.steps.res/answer的因果映射；本轮只读代码/历史记录，未重跑执行器 | 复用官方算子和终值执行，在新Agent任务命名空间评价实际程序/答案；无需为新主线重建旧D字段映射。旧0/89探针不当纠正样本 |
| TAT-QA原始问题与旧WP素材 | GB10 `data/research/tatqa_raw_2026/`两文件重读hash，匹配[既有WP记录](../../tatqa_wp0_2026/README.md)：train/dev为2,201/278条记录、5,543/718个算术问题，SHA前缀2df6e722/8da095a8。另有[许可记录](../../../docs/datasets/tatqa_licence_record_v1.md) | 可作第二相关集；旧WP60个期差题是派生任务。[原评估器](https://github.com/NExTplusplus/TAT-QA/blob/master/tatqa_metric.py)及[测试](https://github.com/NExTplusplus/TAT-QA/blob/master/tatqa_metric_test.py)已读：算术评分处理答案与scale，不能直接替用FinQA小数相等口径。冻结输出单位/官方评分后用原问句及表文执行，不重开TAT-DQA；本轮0模型调用 |

<a id="tatqa-related-prep-v1"></a>
**TAT-QA相关原始算术题：CPU准备完成，Agent未运行。** [组件](../tatqa_correction.py)复用既有数值执行器，公开输入仅保留原问句、完整表格及段落；工具保存程序和模型自报scale，只返回执行反馈。私有主机评分使用[固定上游870accc](https://github.com/NExTplusplus/TAT-QA/tree/870accc41953dcde885aabeb963d94aabdc0fbc3)未改代码的算术EM/F1，另记scale准确率；测试包含零值、符号、等价尺度和重复百分比换算。

GB10 `tatqa_correction_v1/related_dev_v1/PREPARATION.json` SHA 0d662423：在原始dev算术题中按固定UID哈希取32个不同表文上下文，不按答案值、scale或模型成绩筛题；尺度分布million/无/percent/thousand为12/4/7/9，最大任务文本6,704字节。这是相关开发集，不将表UID称公司/年份分组。当前仅组件与数据准备；待FinQA固定批次结束后，再接入既有episode的候选/评分回调，不额外建设runner。

本批GB10定点73项/40子测试通过，包含新组件5项、两个未改动的上游评分测试及既有66项；孤立工具的`subtract(2, 2)`仅作接口检查，不记原题成功。0模型POST/神经前向/训练更新。双份包`tatqa_related_preparation_20261115_v1.tgz`为834,633字节、SHA256 `97f8521cf1309204607cf04ab95a473c504c04b94ec29c7cf8ed33ea22c7ca15`，含32个公共输入、私有标签、原始dev文件、源码/测试、上游许可/代码及准备脚本。

知识库使用成本口径：执行tokens含缓存，不能直接等价钱或新增算力；另计教师/失败采集、经验形成、训练和使用。既有来源共享费用只记一次，缺失研发/硬件用量保留未知。与普通基法的比较先控制来源、学生与预算，训练内容和监督位置的变化可以是要研究的机制。

<a id="finqa-current"></a>
### FinQA当前记录（按需加载）

当前只读[FinQA机制、对照和形成源](FINQA_CORRECTION_LEARNING.md)；本页保留跨阶段知识，不重复逐轮实验。新8报告的纠正/保持、固定平均与20个来源的全部结果均在该页。


<a id="paired-decision-v1"></a>
<a id="semantic-edit-v1"></a>
旧链接接续：[形成/训练与原生执行](FINQA_CORRECTION_LEARNING.md#finqa-current)、[闭合监督对照](FINQA_CORRECTION_LEARNING.md#paired-decision-v1)、[错误分叉机制](FINQA_CORRECTION_LEARNING.md#semantic-edit-v1)。早期FinQA全过程保存在[11-15快照](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261115.md#finqa-current)，不作现役待办。

## 既有20份主题记录的用途

| 记录组（原20份结果页；金融新记录另列） | 保留位置与用途 |
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

## 先前整理的证据范围（启动FinQA前）

较早的零调用整理、暂停现场和旧来源清点已原文保存在[11-15历史快照](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261115.md)。它们是素材索引，不是当前执行许可或当前方法成绩。

## 兼容旧锚点

以下仅保留历史链接入口。旧上下文、候选及回执叙述查[原文快照](../../../docs/archive/2026-11-06_agent_research_context/continuation_through_20261115.md#兼容旧锚点)，当前实验查[FinQA记录](FINQA_CORRECTION_LEARNING.md)。

<a id="feedback-interaction-v1"></a>
<a id="feedback-policy-v1"></a>
<a id="feedback-residual-v2"></a>
<a id="fragment-continuation-v1"></a>
<a id="fragment-transfer-v1"></a>
<a id="binding-update-v1"></a>
<a id="deployment-timing-v1"></a>
<a id="feedback-transfer-v1"></a>
<a id="local-edits-v1"></a>
<a id="phase-v1"></a>
<a id="normalized-v1"></a>
<a id="witness-v1"></a>
<a id="expansion-v1"></a>
<a id="prefix-v1"></a>
<a id="effect-witness-v1"></a>
<a id="preservation-v1"></a>
<a id="cross-batch-autopsy"></a>
<a id="reactive-v1"></a>
<a id="residual-option-v3"></a>
<a id="activation-v2"></a>
<a id="effect-conditioned-v2"></a>
<a id="反馈交互学习已按主题分离"></a>
<a id="复用or训练两条新任务检验平均与差分"></a>
<a id="同现场续做普通继续已足够固定提醒未见增益"></a>
<a id="完整纠正片段两新任务八组闭合局部修复未带来总体增益"></a>
<a id="绑定修订两类互补独立一致性配方停止"></a>
<a id="部署时点12组保留条件收益停止扩跑"></a>
<a id="新任务五组成功保留与执行成本信号"></a>
<a id="源内自动反馈修订已闭合"></a>
<a id="早期阶段化原型"></a>
<a id="旧标准化十组保留条件差别及完整费用"></a>
<a id="原先导输入错误保留形成产物复用"></a>
<a id="旧四配置20组停止整流程接管保留局部价值"></a>
<a id="旧同一现场续做保留复用与路由收益"></a>
<a id="旧失败进一步变成条件纠正监督局部效果与执行归属"></a>
<a id="旧部分保留与控制流程修补已完成停止整节点冻结"></a>
<a id="修正判断方式"></a>
<a id="历次结果与可用素材"></a>
<a id="最值得挖的三类资产与复用收益"></a>
<a id="放宽开发门槛保留事实标准"></a>
<a id="尸检导出的方向"></a>
<a id="证据范围与当前状态"></a>
<a id="最近先导与固定历史"></a>
