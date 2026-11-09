# 第二阶段：Agent 经验学习与变化适配

> 2026-11-09 | 唯一现役计划，原地更新。运行授权只查[STATE](../../memory/STATE.md)和用户最新指令；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇与硕士研究：Agent从执行/反馈形成经验，在变化后选择、验证和修订经验。11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；按11月底选方法、12月确认及正文、1月审阅倒排。Paper E与学位查STATE。

主攻[取证后的局部经验重构](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md#可检验的机制方向)：当前证据先返回，再决定保留、撤回或替换哪条经验。以实际续做效果训练，与同数据/动作/反馈的普通联合策略及强简单规则比较；不把增加交互loss当创新。候选未成立。D/A/C按[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)执行；4B不作前置。

[旧五基线](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)已闭合，R是已有配方；SymPy直接动作与目标四臂看[方法现场](results/CODE_SOURCE_CORRECTIONS.md#direct-method)，不从历史准备句重复启动。

## 执行原则与后续顺序

1. **旧四格闭合。** B6受通道/预算混淆，预测向量已更正；oracle5/6、R6/6不识别新机制。
2. **ALF闭合。** [18个TRAIN源](results/ALFWORLD_ADDITIONAL_SOURCES.md#progress-feedback18)4成功/14未完成；world已关，前缀非纠正监督。
3. **规则反证。** [两规则恢复14/14](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)，停止此面板复杂选择器；输入与旧actor不同。
4. **采集已收口。** [26020/22711](results/CODE_SOURCE_CORRECTIONS.md#source-expansion)共42实际POST；前者超时且代码未修对，后者按用户重心调整提前停止。复用已存真实现场/成功工件，不追加来源资格；134 valid_unseen保留。
5. **方法实验。** [开发现场](results/ALFWORLD_ADDITIONAL_SOURCES.md#反馈后局部经验修订单现场开发)：条件经验、动态进度记录未改善；两个任务同前缀行动分叉均成功、费用顺序相反，不能伪造成功/失败标签。旧反馈梯度训练中断且监督不匹配。下一步在相同取证和反馈后比较保留/局部修订的实际续做，再与同信息普通策略和规则对照；确认池继续保留。

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
