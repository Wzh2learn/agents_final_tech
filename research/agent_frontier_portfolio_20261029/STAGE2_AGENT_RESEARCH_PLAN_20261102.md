# 第二阶段：Agent 经验学习与变化适配

> 2026-11-10 | 唯一现役计划，原地更新。运行状态以宿主Goal控制面和用户最新指令为准，[STATE](../../memory/STATE.md)为快照；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇与硕士研究：Agent从执行/反馈形成经验，在变化后选择、验证和修订经验。11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；按11月底选方法、12月确认及正文、1月审阅倒排。Paper E与学位查STATE。

主攻变化环境中的经验适配。候选CCER比较有来源的经验单元在同一现场保留或移除的续做效果，以反馈决定局部更新；新颖性和有效性均未成立，首轮不先训练。近邻包括[EmbodiSkill](https://arxiv.org/abs/2605.10332v2)、[SkillApt](https://arxiv.org/abs/2609.26863v3)、[Skill-V](https://arxiv.org/abs/2610.11781)和[StateGraph](https://arxiv.org/abs/2611.02912)，须比较机制和方法；适配实现不冒称原法复现。

[旧五基线](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)已闭合，R是已有配方；SymPy直接动作与目标四臂看[方法现场](results/CODE_SOURCE_CORRECTIONS.md#direct-method)，不从历史准备句重复启动。

## 执行原则与后续顺序

1. **旧结果。** B6有通道/预算混淆；[ALF训练源](results/ALFWORLD_ADDITIONAL_SOURCES.md#progress-feedback18)4成功/14未完成，[两规则恢复14/14](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)，但规则与旧actor输入不同。此面板停止复杂选择器。
2. **代码资产。** [Sphinx8282→8127](results/CODE_SOURCE_CORRECTIONS.md#sphinx-新来源公开问题与实际运行11-09)源题模型及反馈修订均未通过；SymPy教师辅助、Django超时后的正向工件均不得当成完整自主成功。旧目标用于开发，不作新确认；134 valid_unseen保留。
3. **首轮。** 少量已曝光案例核经验来源和配对干预，再扩展至不同项目的4–6对开发任务；自主、教师辅助和参考补丁经验分开报告。旧[动态记录与动作分叉](results/ALFWORLD_ADDITIONAL_SOURCES.md#反馈后局部经验修订单现场开发)未形成有效训练标签；不在单题上堆变体。
4. **对照与裁决。** 比较无经验、完整经验、简单规则、同反馈自由修订与候选；有信号再消融依赖筛选和配对干预。各臂同等公开信息与总预算，计入形成、干预、修订、执行、验证成本。留出评分和任务不得用于选择经验；简单规则、同预算重试或直接取证解释收益时调整机制。小样本只作开发判断。

## 证据和写作要求

可写问题与设计；方法定稿需独立机制、两环境留出、强基线对照、完整成本、配对重复及消融。样本规模按开发方差确定。

冻结来源、输入与预算；actor不读未来gold或隐藏事实。原生环境判定成功，普通stop不等于成功；接口故障与未知结局另记。研发、形成、推理和训练分账，cache不重复相加，未知和旧差额保留；直接27B作成本对照。

## 按问题加载证据

| 要解决的具体问题 | 只加载这些材料 |
| --- | --- |
| 当前ALF恢复对照 | [来源与原生资格](results/ALFWORLD_ADDITIONAL_SOURCES.md#student-failure-recovery)。 |
| 当前代码纠正与目标 | [教师纠正及版本边界](results/CODE_SOURCE_CORRECTIONS.md#current)。 |
| SymPy新增候选 / 旧时序 | [集合语义复现](results/ALFWORLD_LEARNING_RUNTIME.md#sympy-intersection)；[旧时序](../../docs/archive/2026-11-06_agent_research_context/contextbench_sympy_20261104.md)。 |
| RethinkSkill与其他近邻 | [相关工作短页](IJCNN_RELATED_WORK_REFRESH_20261030.md) → 指定接口记录。 |
| 已结束环境与其他试验 | [历史主题目录](../../docs/archive/2026-11-06_agent_research_context/README.md)或[总索引](../../docs/INDEX.md)，只选一个主题；旧深链接在下方保留。 |
| 自动记录和工具前提 | [记录器](../../scripts/graph/research_auto_record.py)、[工具检查](../../scripts/graph/research_tool_runtime.py)、对应 runner；不改变业务服务。 |

## 维护规则

本页只留计划及路由，STATE留定位、THREADS留未决；原始证据不截断。联网与执行边界按[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)执行。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="两条并行问题线"></a>
<a id="输入格式变化的可视化工作流资格与开发2026-11-04"></a>
<a id="evoclaw-配置迁移公开反馈与独立合同2026-11-04"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="swe-skills-bench--aiohttp真实项目执行资格2026-11-04"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/aiohttp_development_20261104.md)

<a id="swe-skills-bench--sympy第二项目资格2026-11-04"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/sympy_skill_development_20261104.md)

<a id="swe-contextbench真实问题对与经验时间边界2026-11-04"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/contextbench_sympy_20261104.md)

<a id="升级后目标接续2026-11-05用户已恢复"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/sphinx_recovery_20261105.md)

<a id="任务组合和实验顺序"></a>
<a id="当前来源资格skillevolbench-的-api-重试族"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/skillflow_retry_qualification_20261104.md)

<a id="不同来源的连续办公任务开发2026-11-0304"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/office_workflow_20261103_04.md)

<a id="恢复研究requests-自然任务对2026-11-05"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/requests_development_20261105.md)

<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/astropy_pre_neat_20261105_06.md)
