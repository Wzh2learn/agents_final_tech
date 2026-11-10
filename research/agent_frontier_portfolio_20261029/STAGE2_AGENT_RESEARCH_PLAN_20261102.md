# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active；尸检与两轮原型筛查已闭合。本次inquiry：first-principles→minimal-experiment；专家基准8ab61632，结合其后实测更新。

## 目标与裁决

面向IJCNN 2027和硕士研究，探索Agent如何利用真实反馈调整行动与经验，适应任务、工具或环境变化。复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**真实反馈能否帮助Agent识别失效的决策前提，选取必要的新证据并调整行动，从而提高任务成功或降低总成本？FCDR是当前候选，名称和算法可换；CCER为工具组件，ECCE不独立立项。

**当前判断：**旧提醒与探针选择未形成独立收益。近期候选转为“当前执行证据如何更新历史反馈的有效范围”，作用于经验更新的验证依据；机制独立性与实际收益待检验。

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

1. **旧筛查闭合。**[尸检](results/CODE_SOURCE_CORRECTIONS.md#fcdr-feedback-review)、[六臂](results/CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-result)、[计划形成](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)与[公开回归](results/CODE_SOURCE_CORRECTIONS.md#branch-scope-result)不重跑。保留A5恢复成本少27.95%的局部信号；219项不触及编辑函数，不能加强算术修复。停止旧提示/选择器扩样。
2. **候选操作。**[当前执行证据→历史反馈支持集](results/CODE_SOURCE_CORRECTIONS.md#feedback-support-candidate)：定位旧反馈依赖的前提，用当前真实见证分为仍适用/已冲突/未知；在提出经验修订前固定其验证支持集，更新冲突范围并保留其他范围的旧经验，未知时重新取证或回到普通恢复。禁止根据候选结果挑选有利的验证记录；不改历史真值。
3. **独立性与强反例。**Skill-V已支持适用条件及历史回放，EvoMem已有版本历史，StateWise已有事实核验。必须比较按上下文/版本分组的回放、时间衰减、普通修订、全量当前重验及适用近邻。版本规则或原法适配同效更省，就停止此候选；不把新增标签当贡献。
4. **数据与下一动作。**已核[两条公开版本链](results/CODE_SOURCE_CORRECTIONS.md#feedback-support-candidate)，仅含显式要求变化，未运行Agent；可作开发对照，不证明隐式反馈失效。下一定向复核上述机制差异，并找确有规则冲突且有真实成功来源的现场，先做同状态三策略配对；没有这种现场不建新adapter或大矩阵。可请专家审候选，答复不作为全部科研的阻塞。
5. **扩样与写作。**统一模型/OpenCode、状态、权限和总预算，先看原生成功/全成本，再扩不同项目的两seed与随机顺序。至少两项目有一致信号后做未曝光任务及消融，按方差定规模；12月中旬裁决IJCNN路线，可靠监督出现后按需训练。

### 明确停止条件

- 无适用在线反馈、无可改变节点：停止当前FCDR版本；不反复加prompt或资格分支。
- 规则/普通恢复同效更省，或只改动作却无成功/成本收益：停止或修订机制。
- 收益来自额外信息/尝试/权限，或独立任务不复现：收窄或换题，不包装为方法增量。

每批报告假设、增量、全成本和下一动作。主看成功/成本，另记反馈采纳及适用回归。形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。工程服务当前实验，重大转向可请专家。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率约束：**一批一假设，在现有记录写清机制、强基线、预算和反证；闭合即决定继续/修改/停止。不重做旧48小时尸检，不扩规则已解决面板，不追加框架。现有Goal覆盖此迭代，不以手动修改目标正文为前置。

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
