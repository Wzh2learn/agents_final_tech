# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active；尸检与两轮原型筛查已闭合。本次inquiry：first-principles→minimal-experiment；专家基准8ab61632，结合其后实测更新。

## 目标与裁决

面向IJCNN 2027和硕士研究，探索Agent如何利用真实反馈调整行动与经验，适应任务、工具或环境变化。复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**真实反馈能否帮助Agent识别失效的决策前提，选取必要的新证据并调整行动，从而提高任务成功或降低总成本？FCDR是当前候选，名称和算法可换；CCER为工具组件，ECCE不独立立项。

**当前判断：**已定位可干预节点，但提醒式恢复整体未胜普通恢复；自由生成的取证计划也未形成可用的行动分歧。下一轮应发现可执行的机制差异，跨任务收益和全成本优势仍待验证。

专家建议按此吸收：先证实反馈改变了哪个决策，再检验是否改善任务。范围绑定、可执行探针和成本控制已有[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。反馈送达、有效性、采纳及任务能力分开；自测可作线索，源码变化不自动使所有证据过期。静态回放只定位，实际续做才验证收益。

## 现有证据尸检：不可合并成一种“坏经验”

| 现场 | 可支持的观察 | 不能支持的结论 | 定位 |
|---|---|---|---|
| ALFWorld | 规则14/14恢复；局部修订未显示收益 | 复杂选择必要 | [汇总](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery) |
| Astropy 14995→15082 | 隔离四臂均完成；无历史/摘要19/10 POST，491,274/268,655 tokens | 端到端净收益；FCDR有效 | [隔离批次](results/ASTROPY_ISOLATED_CONTROLS_20261106.md) |
| Matplotlib 24149→24818 | 三臂均消除公开NaN崩溃；辅助函数较强验收仍0/2，回归61/61 | 公开问题未修复；经验导致失败；全部验收通过 | [公开复核](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)、[旧评分](results/CODE_SOURCE_CORRECTIONS.md#nan-transfer) |
| SymPy 21055→21203 | 来源成功；目标1/3对0/3，回归均124/124；含来源817,915对807,711 tokens | 目标完成；迁移净收益 | [结果](results/CODE_SOURCE_CORRECTIONS.md#sympy-21203-result) |

**判读边界：**均为曝光开发题，Astropy优势限目标成本。ALF教师未见事后追加的旧拒绝，7动作不能证明黑名单误用。其他失败源与配置差异按下方索引读取。

## 当前执行顺序

1. **尸检完成，不重开48小时整理。**[9轨迹/9节点](results/CODE_SOURCE_CORRECTIONS.md#fcdr-feedback-review)定位普通恢复与Astropy停滞；未见已证实的范围误用。
2. **筛查已执行。**[六臂结果](results/CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-result)：30 POST/510,751 tokens。A5动态反馈同成功、目标恢复tokens少27.95%，事后原生219项均过；A4三臂均推理截断、原题未过。合计未胜普通恢复，停止此提示版本扩样，保留局部信号。
3. **取证形成筛查也已停止。**[SymPy计划](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)4 POST/31,021 tokens：4原因同指1行动，3探针无有效预测—观测对应；未运行修复臂。形成阶段禁止读源码且经验文件为空，不能外推为Agent修复能力失败。选择器代码保留为实验组件。
4. **下一项只做机制判别。**最多一个工作日，复用已有真实补丁及执行结果，找一处不同修复路径及其适用条件，明确一个公开观测会怎样改变选择。比较普通恢复、最强简单取证和候选机制，并写清与最近邻的操作差异；不能用模型编写的预测表代替执行证据。找不到分歧或独立差异，就换假设或定向请专家，不再同题补prompt。
5. **小批实测→扩样→写作。**机制可执行后，用同一模型/OpenCode、初始状态、权限和总预算做配对续做，计入取证与形成成本。先检验成功/成本，再在不同项目固定两个seed、随机顺序，补历史、无经验、同预算重试及适用近邻。至少两个项目出现一致信号后扩未曝光任务与消融；按方差定规模。12月中旬决定IJCNN路线，可靠监督出现后按需训练。

### 明确停止条件

- 无适用在线反馈、无可改变节点：停止当前FCDR版本；不反复加prompt或资格分支。
- 规则/普通恢复同效更省，或只改动作却无成功/成本收益：停止或修订机制。
- 收益来自额外信息/尝试/权限，或独立任务不复现：收窄或换题，不包装为方法增量。

每批报告假设、增量、全成本和下一动作。主看成功/成本，另记反馈采纳及适用回归。形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。工程服务当前实验，重大转向可请专家。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率约束：**一批一假设，在现有记录写清机制、强基线、预算和反证；闭合即决定继续/修改/停止。不重做尸检，不扩规则已解决面板，不追加框架。本次仅复核与整理，零新模型运行。宿主Goal旧48小时阶段已完成，正文待用户替换。

## 按问题加载证据

| 问题 | 先读 |
|---|---|
| ALFWorld进度、反馈、简单规则 | [实验补充](results/ALFWORLD_ADDITIONAL_SOURCES.md) |
| 经验修订/测试反馈是否改变行为 | [Matplotlib批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)、[Astropy批次](results/ASTROPY_PROFILE_CONTROLS_20261106.md) |
| 代码任务来源、迁移与教师修复 | [代码纠正](results/CODE_SOURCE_CORRECTIONS.md)、[依赖扫描试验](DEPENDENCY_SCOPE_AGENT_PILOT_RETURN_20261031.md) |
| 方法新颖性与实验对照 | [近邻审计](IJCNN_RELATED_WORK_REFRESH_20261030.md) |

## 维护与兼容链接

只维护本计划中的当前裁决和下一门；STATE 记状态，THREADS 记未决，原始证据留在结果文件。详细旧探索已归档，按需读取[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="两条并行问题线"></a>
<a id="输入格式变化的可视化工作流资格与开发2026-11-04"></a>
<a id="evoclaw-配置迁移公开反馈与独立合同2026-11-04"></a>
<a id="swe-skills-bench--aiohttp真实项目执行资格2026-11-04"></a>
<a id="swe-skills-bench--sympy第二项目资格2026-11-04"></a>
<a id="swe-contextbench真实问题对与经验时间边界2026-11-04"></a>
<a id="升级后目标接续2026-11-05用户已恢复"></a>
<a id="任务组合和实验顺序"></a>
<a id="当前来源资格skillevolbench-的-api-重试族"></a>
<a id="不同来源的连续办公任务开发2026-11-0304"></a>
<a id="恢复研究requests-自然任务对2026-11-05"></a>
<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[旧探索归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。
