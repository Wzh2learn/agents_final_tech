# 第二阶段：Agent 经验学习与变化适配

> 2026-11-10 | 唯一现役计划，原地更新。运行状态以宿主Goal控制面和用户最新指令为准，[STATE](../../memory/STATE.md)为快照；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇与硕士研究：Agent从执行/反馈形成经验，在变化后选择、验证和修订经验。11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；按11月底选方法、12月确认及正文、1月审阅倒排。Paper E与学位查STATE。

主攻变化环境中的经验适配，但不预设方法成立。11-10近邻核对表明：[Recuris](https://arxiv.org/html/2608.24876)覆盖任务进度工作记忆、执行轨迹定位、经验局部修补、留出门控及失败后同题适配；Terminal-Bench匹配4次尝试时，适配53/87、冻结记忆重试51/87（7胜/5负，McNemar p=0.774），说明其总提升主要不能归给学习。[VCE-Skill](https://arxiv.org/html/2608.16544)覆盖公共技能版本差异的经验提炼及其与当前轨迹修改的自适应融合。[CounterMem](https://arxiv.org/html/2609.31874v1)、[OMCE](https://arxiv.org/html/2611.01747v1)、[MemScope](https://arxiv.org/html/2610.21170)、[Remember, Verify, or Ask?](https://arxiv.org/html/2608.19564v2)、[TAM](https://arxiv.org/html/2610.37482)、[SkillShift](https://arxiv.org/html/2610.33528)、[Skill-V](https://arxiv.org/html/2610.11781v1)及[多轮技能反馈演化研究](https://arxiv.org/html/2608.02636v1)也分别覆盖反事实适用性、在线更新/路由、局部修补、复用时核验、进度记录和环境变化适配。宽泛的“真实反馈＋局部经验修订＋保留进度”不再是可主张的新方法。

**当前没有通过新颖性门的方法候选；暂停该方向的模型实验。**保留的窄边界是：真实软件/API版本变化发生在任务执行中时，能否依据行为依赖而非仅版本标签，选择性重验或更新经验，同时保留不可回滚的任务进度。该交叉点目前只是应用场景，尚无算法定义或新颖性证据。现有素材也未组成合格验证集：SkillsBench所选任务是静态S3FIFO任务，Partridge是已曝光commit对且未找到历史skill；CSV/JSON/TSV任务属于合成格式变化；依赖扫描经验来源任务未成功，而确定性程序已通过源/目标7/7与8/8。其余代码迁移任务已曝光或来源资格不足。重开实验前，必须写出具体任务轨迹，说明候选算法相对Recuris、VCE-Skill、CounterMem、OMCE、MemScope及版本检查/全量回归等简单基线会作出什么不同决定，并找到未曝光、可独立评分的真实迁移任务；否则淘汰该候选、调整研究问题，不以增加模型调用补新颖性。详见[SkillsBench资格](SKILLSBENCH_SOURCE_QUALIFICATION_AND_PLAN.md)、[依赖扫描现场](DEPENDENCY_SCOPE_AGENT_PILOT_RETURN_20261031.md)及[格式变化记录](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)。

[旧五基线](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)已闭合，R是已有配方；SymPy直接动作与目标四臂看[方法现场](results/CODE_SOURCE_CORRECTIONS.md#direct-method)，不从历史准备句重复启动。

## 执行原则与后续顺序

1. **旧结果。** B6有通道/预算混淆；[ALF训练源](results/ALFWORLD_ADDITIONAL_SOURCES.md#progress-feedback18)4成功/14未完成，[两规则恢复14/14](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)，但规则与旧actor输入不同。此面板停止复杂选择器。
2. **代码资产。** [Sphinx8282→8127](results/CODE_SOURCE_CORRECTIONS.md#sphinx-新来源公开问题与实际运行11-09)源题模型及反馈修订均未通过；SymPy教师辅助、Django超时后的正向工件均不得当成完整自主成功。旧目标用于开发，不作新确认；134 valid_unseen保留。
3. **值得复用来设计新实验的现场，不是方法成绩。** ALFWorld同一任务的8步公开轨迹可重建相同进度，但“旧会话续做未成功/新会话轨迹投影后成功”同时改变了上下文、历史表示与模型条件；Matplotlib目标上不准确的结果卡引出回归，普通反馈与清单式反馈后来都修好了；依赖扫描迁移中生成经验臂通过既有目标检查，但来源任务未完成，确定性程序也通过源任务7/7和目标任务8/8。另有Astropy14995→15082：成功来源后的四个目标条件都完成，普通历史目标臂为10 POST/268,655 reported tokens、无历史为19 POST/491,274；单目标、固定顺序且成本口径含缓存，支持把经验成本/目标收益列为正向开发信号，不证明因果或净成本优势。详见[Astropy现场](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)。Sphinx已曝光源题上，普通/结构化反馈各24 POST均无编辑；扩大工具面后仍无编辑，原题未通过。该链显示重复搜索和执行停滞，但不支持“旧经验导致错误”的归因；按[尸检记录](results/CODE_SOURCE_CORRECTIONS.md)停止同题提示、工具面续试。按因果相关性区分，clean03是最明确的“正确的当前对象不匹配记录已送达但未改变动作”现场，然而同题纯规则成功，复杂机制没有必要性证据；Matplotlib回归出现在经验卡臂，但卡片未包含实际修复规则，不能归因于经验；Sphinx主要是搜索/编辑停滞，SymPy主要是相关源码覆盖不足。现有失败并非同一机制，不能合并成一个“旧经验导致失败”的训练标签。
4. **先收窄，再调用模型。** Matplotlib24149→24818与SymPy21055→21203已有成功来源及实际目标运行，但目标都未显示经验收益，均仅作开发负结果；Django16910→35356来源失败、目标环境也有回归错误；SymPy9384重复探针已停止。[尸检记录](results/CODE_SOURCE_CORRECTIONS.md)。不重跑这些题。只读筛出现有材料里未曝光、评分可区分、来源成功且目标执行中会产生真实反馈的任务；不满足条件的样本不进入迁移实验。当前第一道门是方法差异，不是任务数。
5. **方法成立后才冻结判别合同。** 若新候选通过新颖性门，至少比较：同一进度无经验、完整旧经验、Recuris式失败后局部记忆演化、VCE-Skill式版本经验辅助、CounterMem式反事实适用性、OMCE式在线路由更新、最佳简单版本/依赖规则、全量重测及候选机制；若可行，核对公开基线实现并保持模型、工具、证据与总预算一致。运行前冻结任务来源、评分和失败条件；报告目标任务成功、源任务回归、进度保留和形成/修订/执行/验证全成本。留出评分不参与更新或挑选。4–6个独立目标只用于机制筛查，不能作为论文确认证据。
6. **裁决。** 如果静态修复经验、简单规则或直接重新取证达到相同效果，停止复杂更新机制；如果更新只改善文本、不改变后续动作或任务结果，也停止。即使开发实验有信号，仍需独立任务/环境、留出评分、配对重复和针对性消融后才能定方法。

## 当前最有信息量的失败样本

Astropy #14995→#15082 是**上游项目**明确记录的回归链：上游 #14995 将 `operand is None` 改为 `operand.mask is None`，后续 #15082 明确指出这移除了无 mask 对象的 collapse 行为。但我们自己的来源 Agent **没有**重现这个破坏性替换：原始编辑记录保留 `elif operand is None`，只新增 `elif operand is not None and operand.mask is None`。所以它不是“Agent 生成的经验导致后续回归”的直接样本。

11-10目标三臂仍都在24 POST上限内未完成。尸检显示完整skill臂自建测试调用不存在的 `NDDataRef.collapse`，其后测试反馈没有带来新编辑；遮蔽臂也是测试失败后停在读取/搜索；无经验臂的末次 `pytest | head` 没有保留最终汇总。该批最多说明测试反馈到有效修复之间有断点，不支持经验有害、局部修订有效或泛化。详见[Astropy批次](results/ASTROPY_PROFILE_CONTROLS_20261106.md)及上游 [#14995](https://github.com/astropy/astropy/pull/14995) / [#15082](https://github.com/astropy/astropy/pull/15082)。

**Matplotlib 23562→27361是更强但仍不充分的开发线索**：旧目标批中透明结果卡臂出现了`get_path()`无条件返回`_original_path`的改动，并触发冻结图像回归（149/150）；无历史、来源历史和生成skill臂通过（150/150）。透明卡记录来源问题/结果/修改路径，并未给出目标修复规则；单任务单seed及不同载体信息使“经验造成回归”仍未被因果识别。随后普通真实反馈复跑与清单反馈都修好了回归，故“跑独立回归、交还失败信息、普通重试”是强且已成功的基线，清单没有已证实增益。完整边界见[Matplotlib隔离批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)。

**Matplotlib反馈来源线索的裁决**：这条已曝光单任务只显示一次与结果卡相关的冻结回归信号，普通反馈复跑即可修复；它没有证明某条经验导致回归，也未形成区别于强基线的操作机制。自写测试价值、错误测试固化和oracle反馈审计已有直接近邻，因此该线索不作为当前方法候选，也不重跑该目标。它只保留为设计经验：候选机制必须证明它改变了实际决策和任务结果，而不只是重写经验文本。当前研究仍只检查上述真实软件/API变化边界；若现有资产找不到未曝光且具独立评分的源—目标对，则转向新问题，不追加同类模型运行。

## 证据和写作要求

可写问题与设计；方法定稿需独立机制、两环境留出、强基线对照、完整成本、配对重复及消融。样本规模按开发方差确定。

冻结来源、输入与预算；actor不读未来gold或隐藏事实。原生环境判定成功，普通stop不等于成功；接口故障与未知结局另记。研发、形成、推理和训练分账，cache不重复相加，未知和旧差额保留；直接27B作成本对照。

## 按问题加载证据

| 要解决的具体问题 | 只加载这些材料 |
| --- | --- |
| 当前ALF恢复对照 | [来源与原生资格](results/ALFWORLD_ADDITIONAL_SOURCES.md#student-failure-recovery)。 |
| 任务进度与会话上下文是否可分离 | [ALFWorld续做尸检](results/ALFWORLD_ADDITIONAL_SOURCES.md#student-failure-recovery)。 |
| 经验误导与目标反馈修订 | [Matplotlib原题/回归结果](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)；[依赖扫描迁移](DEPENDENCY_SCOPE_AGENT_PILOT_RETURN_20261031.md)。 |
| 已有正向成本信号 | [Astropy源—目标四臂](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)；只作开发结果，不当独立确认。 |
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
