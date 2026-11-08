# 第二阶段：Agent 经验学习与变化适配

> 2026-11-09 | 唯一现役计划，原地更新。运行授权只查[STATE](../../memory/STATE.md)和用户最新指令；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇与硕士研究：Agent从执行/反馈形成经验，在变化后选择、验证和修订经验。11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；按11月底选方法、12月确认及正文、1月审阅倒排。Paper E与学位查STATE。

主攻[组合反事实信用分配候选](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md#可检验的机制方向)：学习经验组合何时有用，而非再做普通纠正SFT。D/A/C按[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)执行；4B不作前置。

[五种开发基线](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)已闭合并复核：新12题F/O/R/all7/目标匹配分别4/6/8/4/4。R有开发优势但属于已有配方，不是新方法。新增H18为766 POST，Q4已恢复。SymPy普通复用双臂[已准备](results/CODE_SOURCE_CORRECTIONS.md#current)，暂缓运行，供新机制的第二环境验证复用。

## 执行原则与后续顺序

1. **最小识别。** look6已有无经验00、单轨迹A的10、all7的11；核实际输入后补其余六轨迹B的01，最多6新槽/768 POST。该后验开发试验只检验组合效应，尚未释放，不冒充动态撤回。[片段与四格原语](feedback_context_policy.py)已实现，CPU通过不代表机制成立。
2. **明确预测。** 比较`I=V11−V10−V01+V00`及逐题最佳组合。非零I和优于最佳固定策略的上界都需存在，再在新seed/独立布局重复；若仅是更多文本、目标类型或固定短历史解释效果，停止该具体候选。
3. **学习机制。** 有重复信号后，以同前缀续做监督联合效用，并比较随机/均匀补格与按决策价值补格。用相同数据/容量的普通联合MLP、独立片段效用、规则及近邻强适配定位增量；不把多数据、多算力或重复加权说成新信息。
4. **动态与迁移。** 扩至12–20个来源隔离任务现场，统一当前观察、目标、真实进度与预算；清理旧上下文再暴露所选片段。训练只用开发来源，测试仅执行所选策略；第二环境及未见组合验证后才定稿。heat_2/clean_2仍为曝光回归。

## 证据和写作要求

可写问题与设计，方法定稿需独立机制、两环境留出、超过强对照或同效果下的总成本收益，以及配对重复、分组区间、无害非退化和消融。规模按开发方差定，12–20例不认证论文。

冻结来源、输入与预算；actor不读未来gold/隐藏事实，公开重放不证明隐藏等价。原生won和独立语义决定成功，普通stop未成功也是失败；接口/未知结局另记。研发、形成、推理和训练分账，cache不重复相加，未知与旧差额保留；直接27B作成本对照。

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

本页只留目标、当前比较、下一动作和证据路由；闭合证据按主题保存。STATE只留定位，THREADS只留未决，不重复实验日志。[上下文检查](../../scripts/graph/research_context_check.py)限制单页与启动体量；超限先拆主题，原始证据不截断。联网、GB10能力及外部操作边界按[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)执行。

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
