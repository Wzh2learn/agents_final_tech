# 第二阶段：Agent 经验学习与变化适配

> 2026-11-09 | 唯一现役计划，原地更新。运行授权只查[STATE](../../memory/STATE.md)和用户最新指令；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇与硕士研究：Agent从执行/反馈形成经验，在变化后选择、验证和修订经验。11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；按11月底选方法、12月确认及正文、1月审阅倒排。Paper E与学位查STATE。

多任务优先，4B为支持资产。D/A/C与子Agent规则见[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)，依据见[专家复核](results/ALFWORLD_TEXT_AGENT_20261106.md#expert-review)。

主攻候选：**保留实际进度，利用反馈选择旧经验的保留、撤回或上下文重建。** 经验选择、笔记管理、纠正训练均已有近邻，R只作适配强基线；停止追加普通纠正SFT变体，先明确可区分近邻的机制与反证实验。最佳固定策略或近邻强适配解释收益时简化或切换，尚无独特普适机制的证据。

当前[F/O/R新布局](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)12题/36槽**闭合并独立复核**：look主比较F/O/R为4/6、4/6、6/6；all12为4、6、8，R保留为强开发基线，非独立确认。H18槽已启动：all7历史12槽、目标类型匹配6槽，clean-none复用F并照计策略费用，不加训练；按STATE票据观察，闭合核费用和Q4恢复。[代码纠正](results/CODE_SOURCE_CORRECTIONS.md#current)准备合格SymPy双臂输入，不重跑同题资格。之后推进保留实际进度的上下文机制拆分与独立来源扩样。

## 执行原则与后续顺序

1. **能力。** 按多任务实测选actor，27B供稳定机制/教师，8B供学习对照，4B不作前置。复用动作桥、原生won与请求证据，不重启共享服务。
2. **样本。** 约12–20个独立任务/布局用于开发，含有益/无关/误导经验；按来源留出。heat_2/clean_2只作曝光回归，切片/seed/测试条数不算独立任务，不给actor变化真值。
3. **混杂拆分。** 同执行前缀、环境进度与新会话表示，比较经验保留/移除 × 完整/近期历史；共有目标、当前公开观察、工具、模型与剩余额度。补原会话retry、目标重申、摘要；近期需全程滚动。普通stop未won时统一最多继续一次，首停与最终结果分记。
4. **选择空间。** 配对重复估方差，oracle只作上界；稳定跨任务异质性出现后再训练选择器/actor并对比近邻。测试只执行所选策略，学习与确认隔离；固定短窗口追平则简化。机制消融见专家复核。

第二环境复用隔离代码的非饱和题，35B容易题的测试数不代表泛化。主攻无残差时，再按[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)评估教师纠正状态选择或经验重验证。

## 证据和写作要求

可先写问题、近邻和设计。方法/结果定稿需超出近邻的机制、至少两个独立环境/项目来源留出验证，超过强简单策略及匹配近邻或同效果下有总成本收益；配对重复、来源分组区间、无害非退化与消融。确认规模按开发方差定，12–20例不直接认证论文。

先冻题面、环境、来源时序、输入、评测、预算。actor不读未来目标、gold/专家动作/隐藏事实；公开重放相等不代表隐藏状态相等。成功以原生won/独立语义为准，done/exit0不足；接口/截断与方法结果分记，原始失败与账本不覆盖。

研发Agent、actor/教师、训练/进程内生成分账；input/cached子集/output/墙时分报，未知与差额保留。直接27B作成本基线；只按实验需求抽接口。

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
[原章节](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

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
[原章节](../../docs/archive/2026-11-06_agent_research_context/skillflow_retry_qualification_20261104.md)

<a id="不同来源的连续办公任务开发2026-11-0304"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/office_workflow_20261103_04.md)

<a id="恢复研究requests-自然任务对2026-11-05"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/requests_development_20261105.md)

<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[原章节](../../docs/archive/2026-11-06_agent_research_context/astropy_pre_neat_20261105_06.md)
