# 第二阶段：Agent 经验学习与变化适配

> 2026-11-09 | 唯一现役计划，原地更新。运行授权只查[STATE](../../memory/STATE.md)和用户最新指令；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇与硕士研究：Agent从执行/反馈形成经验，在变化后选择、验证和修订经验。11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；按11月底选方法、12月确认及正文、1月审阅倒排。Paper E与学位查STATE。

主攻[记忆与重新取证联合学习](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md#可检验的机制方向)：以实际“删除→补证→续做”比较训练，不再追加普通纠正SFT。与OSL-MR式保留＋同恢复器、普通联合训练及强简单策略对照；候选未成立。D/A/C按[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)执行；4B不作前置。

[五基线与四格](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)已闭合，R仍属已有配方。SymPy双臂[已准备](results/CODE_SOURCE_CORRECTIONS.md#current)，暂缓运行，供新机制第二环境复用；不为增加基线数量而单独扩跑。

## 执行原则与后续顺序

1. **旧四格闭合。** B6受通道/预算混淆，预测向量已更正；oracle5/6、R6/6不识别新机制。
2. **新来源闭合。** [18个TRAIN源](results/ALFWORLD_ADDITIONAL_SOURCES.md#progress-feedback18)4成功/14未完成、930 POST；末反馈12条未转发。world已关，前缀非纠正监督。
3. **规则反证。** [14现场](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)两规则均全恢复、新动作194/190；停止此面板复杂选择器。规则用整理后的公开历史，非与旧actor同输入。
4. **当前机制开发已闭合。** [Django](results/CODE_SOURCE_CORRECTIONS.md#joint-development)普通及四格均无编辑/恢复，停止此单例分支；64POST/515,460tokens含writer，无学习偏好。下一按独立问题扩样，复用已成功的代码Agent及既有依赖；旧Astropy/Matplotlib目标已饱和，SymPy目标有能力阻断，均只作开发资产。先核新source元数据/时间边界，再释放小批，不新建日期runner。134 valid_unseen及分组确认仍保留。

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

本页只留计划及路由，STATE留定位、THREADS留未决；闭合证据按主题保存。[上下文检查](../../scripts/graph/research_context_check.py)限制启动体量，原始证据不截断。联网、运行与外部边界按[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)执行。

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
