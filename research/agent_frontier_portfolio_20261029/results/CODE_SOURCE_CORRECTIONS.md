# 代码实验素材与失败经验索引

> 2026-11-14｜已闭合/暂停素材，当前Goal paused。完整原文已[归档](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md)，其中“Goal active”和旧下一步仅属历史。现役主线见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，机制关联见[知识索引](CONTINUATION_PROGRAM.md#mechanism-knowledge)。

## 可复用的内容

| 来源 | 实际结果与死因 | 后续用途 |
|---|---|---|
| Astropy A4/A5 | A5普通/动态同过3＋132，动态71,472对99,200tokens；A4均失败且末请求length，两现场合计动态更贵 | 条件性成本信号、有效mask/unit片段与交付瓶颈分别保留；完整合并修复仍是强参照 |
| Matplotlib投影路径 | 普通与清单都曾完成原题＋150回归；事后旧对象状态中eager getattr默认值抛错、显式分支可用 | 真实成功和失败修复对，学习状态条件与行为保留；单个旧对象不等于正式跨版本兼容保证 |
| Matplotlib NaN源/目标 | 源24149实际修复成功；24818完整卡/无经验/移除卡三臂均编辑为None兜底，完整卡和无经验解除公开StopIteration，但三臂原题0/2、回归61/61 | 局部修复确实发生，未满足全NaN/Inf返回数值哨兵的合同；保留有效片段与语义边界，不把原题未过改称无编辑 |
| SymPy | 16988普通接续在既定测试内成功；12481补丁过1＋7、另外两失败原版已存在；LaTeX目标存在经验未送达、上下文/能力问题 | 完整恢复、实际参数与普通接续作为数据和基线；原有失败不计作新增退化 |
| Sphinx | 强教师修订隐藏类型但引入重复签名；事后人工三个输出有序去重可通过；27B两臂多次读取未编辑 | 局部改动与关联约束素材；人工控制仅作原理/上界，不标为Agent学会或迁移成功 |
| Django | 27B有验收合格代码、Actor却触时限；后续不同源的普通反馈程序可执行，目标普通反馈同效更省 | 真实产物可供教师监督；正确补丁、自然完成、方法收益分开。复用评分与依赖，不重开生产DB |
| SQL/异步/取证 | SQL普通历史已解决，另一路长行/终答问题；异步相反决策被简单状态规则解释；取证候选未胜简单覆盖 | 接入反例与强简单基线；不扩复杂调度、原因表或只换价值分数 |
| 接口/来源 | 经验未入请求、默认thinking吞输出、wheel未来源码可见、测试映射/工件错误均已留原件 | 分类为未暴露/交付/来源错误；修接口不冒充方法，修正历史用途而不丢全部素材 |

## 暂停时新增的CPU现场

本轮暂停前选过Astropy14182与Matplotlib25079两个开发源，尚无新Agent请求或训练。Astropy原版原题失败/9回归过，参考10项过；最初日志解析漏掉pytest进度字符，已从同一旧log恢复，未重跑该控制。Matplotlib在base收集时遇已知pkg_resources warning，参考控制未跑。这是外围支持现场，不再作为金融主线的前置。

三次已执行CPU控制及原始错误、脚本、标签/补丁/日志已收为私有19载荷薄包，SHA d698362b774d1b6d4603d32af421a4987eec46b5f8af28ebbc2bf24bce78a770；完整源码/环境按原版本与archive hash定位，不转入Git。后续需要这些代码任务时才处理已知警告；当前不续跑。

## 本索引的使用方式

先从[机制知识](CONTINUATION_PROGRAM.md#mechanism-knowledge)选问题，再按下面旧锚点取一段原文/证据。不要默认读整份124KB历史，也不把源码资格、工具次数或自建测试当作方法完成。跨代码场景与LoRA迁移保留为大论文后续候选；Paper E/开题原文由独立对话维护。

## 兼容旧锚点

<a id="native27-capability"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#native27-capability)

<a id="fcdr-feedback-review"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#fcdr-feedback-review)

<a id="fcdr-recovery-pilot"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#fcdr-recovery-pilot)

<a id="fcdr-recovery-result"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#fcdr-recovery-result)

<a id="probe-choice-screen"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#probe-choice-screen)

<a id="branch-scope-result"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#branch-scope-result)

<a id="current"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#current)

<a id="feedback-support-candidate"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#feedback-support-candidate)

<a id="numpy-state-scope-screen"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#numpy-state-scope-screen)

<a id="async-feedback-decision-node"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#async-feedback-decision-node)

<a id="async-decision-comparison-result"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#async-decision-comparison-result)

<a id="clbench-budget-screen"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#clbench-budget-screen)

<a id="revalidation-neighbor-screen"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#revalidation-neighbor-screen)

<a id="repair-value-mechanism-screen"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#repair-value-mechanism-screen)

<a id="paid-paired-audit-prototype"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#paid-paired-audit-prototype)

<a id="paired-utility-native-pilot"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#paired-utility-native-pilot)

<a id="sympy-source-continuation"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sympy-source-continuation)

<a id="sympy-source-continuation-result"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sympy-source-continuation-result)

<a id="clbench-agent-pilot"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#clbench-agent-pilot)

<a id="action-state-controls"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#action-state-controls)

<a id="joint-development"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#joint-development)

<a id="source-expansion"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#source-expansion)

<a id="nan-transfer"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#nan-transfer)

<a id="sympy-native35"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sympy-native35)

<a id="sympy-21203-result"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sympy-21203-result)

<a id="direct-method"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#direct-method)

<a id="source-tool-contract"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#source-tool-contract)

<a id="school-gateway"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#school-gateway)

<a id="27b真实修复能力与评分范围11-11已闭合"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#27b真实修复能力与评分范围11-11已闭合)

<a id="fcdr首批9条轨迹9个反馈节点11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#fcdr首批9条轨迹9个反馈节点11-11)

<a id="最小恢复筛查合同实现前冻结dev_only"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#最小恢复筛查合同实现前冻结dev_only)

<a id="六臂恢复结果11-11已执行"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#六臂恢复结果11-11已执行)

<a id="取证是否改变修复选择11-11合同与停止结果"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#取证是否改变修复选择11-11合同与停止结果)

<a id="修复分歧与公开强基线11-11零模型实测"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#修复分歧与公开强基线11-11零模型实测)

<a id="已验证来源资产"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#已验证来源资产)

<a id="当前机制候选与公开来源筛选11-11未运行新agent"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#当前机制候选与公开来源筛选11-11未运行新agent)

<a id="同版本真实规则变化numpy开发控制11-11已闭合"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#同版本真实规则变化numpy开发控制11-11已闭合)

<a id="新异步任务反馈已改变代码错误决策前提仍可定位11-11开发批次闭合"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#新异步任务反馈已改变代码错误决策前提仍可定位11-11开发批次闭合)

<a id="异步三臂对照形成未落实停止粗行动标签版本11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#异步三臂对照形成未落实停止粗行动标签版本11-11)

<a id="cl-bench原生sql控制预算与判别力先回到实际接口11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#cl-bench原生sql控制预算与判别力先回到实际接口11-11)

<a id="预算复验方法筛查直接近邻与联合行动解析控制11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#预算复验方法筛查直接近邻与联合行动解析控制11-11)

<a id="机制复核可纠正性进入强基线不能只换一个价值分数11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#机制复核可纠正性进入强基线不能只换一个价值分数11-11)

<a id="有偿配对效用复验最小研发合同11-11尚未验证方法收益"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#有偿配对效用复验最小研发合同11-11尚未验证方法收益)

<a id="新原生节点源历史无历史与同信息顺序控制11-11已闭合"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#新原生节点源历史无历史与同信息顺序控制11-11已闭合)

<a id="sympy16988来源与普通接续测试合同内成功不是新方法11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sympy16988来源与普通接续测试合同内成功不是新方法11-11)

<a id="sql真实agent普通历史成功提交差异不能算方法收益11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sql真实agent普通历史成功提交差异不能算方法收益11-11)

<a id="行动定义与近邻裁决简单状态规则覆盖本面板11-11"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#行动定义与近邻裁决简单状态规则覆盖本面板11-11)

<a id="成本与执行边界"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#成本与执行边界)

<a id="证据定位"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#证据定位)

<a id="后续代码版本边界"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#后续代码版本边界)

<a id="取证条件研究已核资产与简单对照"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#取证条件研究已核资产与简单对照)

<a id="联合记忆与取证开发现场"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#联合记忆与取证开发现场)

<a id="直接方法实验控制器显式选择"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#直接方法实验控制器显式选择)

<a id="sphinx-新来源公开问题与实际运行11-09"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#sphinx-新来源公开问题与实际运行11-09)

<a id="先前准备与故障记录迁入原文"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#先前准备与故障记录迁入原文)

<a id="校内模型接入与代码能力"></a>
[原批次](../../../docs/archive/2026-11-06_agent_research_context/code_sources_through_20261114.md#校内模型接入与代码能力)
