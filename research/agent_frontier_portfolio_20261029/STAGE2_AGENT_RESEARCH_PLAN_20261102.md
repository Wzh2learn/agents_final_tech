# 第二阶段：Agent 经验学习与变化适配

> 2026-11-08 | 唯一现役计划，原地更新。运行授权只查[STATE](../../memory/STATE.md)和用户最新指令；本页规划不恢复Goal。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，选方法时再读[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

## 目标与负责人取舍

主攻第二篇和硕士研究：Agent从真实执行/反馈形成经验，在任务、工具或环境变化后选择、验证和修订经验。IJCNN 2027为目标窗口；Paper E已交导师，等待反馈，ICINT首投、ICDAR顺序备投。2026-11-06核对的[IJCNN截止](https://ijcnn.org/2027/events/regular-papers-deadline)为2027-01-31；内部仍按11月底选择方法、12月确认及正文、1月审阅准备倒排。学位2027年10月送审。

**负责人取舍。** 稳定8B/27B上的多任务研究优先，4B为支持资产。D主责、A按需实作、C审冻结节点；同类任务续用子Agent，独立任务再新建。新执行位优先GPT-6.1 Terra/max；缓存与上下文续接分开核实。[专家复核](results/ALFWORLD_TEXT_AGENT_20261106.md#expert-review)保留依据。

主攻候选：**在保留实际任务进度的条件下，利用新反馈判断旧经验应保留、撤回还是重建为后续上下文。** 学习经验选择、笔记管理、教师纠正已有覆盖；候选独立机制尚未成立。若最佳固定策略解释收益，就简化策略或切换机制，不先建设复杂选择器。

当前已有[代码教师纠正](results/CODE_SOURCE_CORRECTIONS.md#current)，停止该题诊断。下一步真实重放[8B自然失败前缀](results/ALFWORLD_ADDITIONAL_SOURCES.md#student-failure-recovery)，先核clean02/03，再比较同27B恢复actor的完整/近期历史；source与actor身份分开。随后扩独立任务及经验保留/撤回/修订、摘要、观察刷新和原子续做，接口收益不算学习。

## 执行原则与后续顺序

1. **能力先行。** 按多任务实测选择机制actor，优先稳定27B；8B保留为低成本/学习对照，4B独立支持。沿用动作桥、原生won及请求证据，不重启共享服务。
2. **独立任务优先。** 冻约12–20个任务/布局的开发池，含有益/无关/误导经验；分组留出确认并记录来源共享。heat_2/clean_2只作曝光回归；切片、seed和测试条数不算独立样本，不给actor变化真值。
3. **先拆混杂。** 同一执行前缀/实际环境及新会话表示下，比较经验保留/移除 × 完整/固定近期目标历史，四臂共有目标、公开当前观察、工具、模型与剩余额度。补原会话retry、目标重申、摘要等强基线。短历史应含执行全程滚动截取，不能只首次交接截短。各臂统一“普通stop但未won最多再继续一次”，首停与最终结果分记。
4. **先测选择空间。** 配对开发rollout估方差，oracle只作上界；跨任务有稳定异质性再比较规则、轻量选择器及近邻，决定actor训练。测试只执行所选策略并计总成本；学习与确认隔离。固定短窗口追平就不扩复杂选择器。消融与详细边界见[复核记录](results/ALFWORLD_TEXT_AGENT_20261106.md#expert-review)。

第二环境优先复用已有隔离代码任务，以8B筛选非饱和题；35B容易题的多项测试不能冒充外部泛化。教师纠正状态选择、变化后重新验证经验保留为备选，主攻无稳定残差时再按[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)筛查。

## 证据和写作要求

现在可写问题、相关工作与设计；方法及结果定稿需：明确超出近邻的机制；至少两个独立环境/项目来源的留出验证；超过最强简单策略及匹配近邻，或同效果下有总成本收益；配对重复、按任务/来源分组区间、无害情形非退化及关键消融。确认规模根据开发方差确定，不以12–20例直接认证论文。

冻结题面、环境、来源时序、经验输入、评测与预算后再比较。actor可读面不含未来目标、gold/专家动作/隐藏事实；公开状态重放一致不外推为所有隐藏状态等价。原生won/独立语义检查决定成功，done或exit0不单独代表成功。接口、截断、未修复与方法结果分别记录，旧失败和原始账本不覆盖。

研发Agent、actor/教师、训练/进程内生成分账；输入/cached子集/输出/墙时分报，未知及历史差额保留。直接27B作成本基线；仅为实际实验抽取接口，不先重写框架。

## 按问题加载证据

| 要解决的具体问题 | 只加载这些材料 |
| --- | --- |
| 新ALF训练来源 | [来源与原生资格](results/ALFWORLD_ADDITIONAL_SOURCES.md)。 |
| Matplotlib 新pair及来源证据 | [新任务段落](results/MATPLOTLIB_QUALIFICATION_20261106.md#new-source-pair)；旧23562/27361的[隔离对照](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)仅按需读。 |
| Astropy新隔离比较 | [本批合同与结果](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)；[旧四臂及修正](results/ASTROPY_PROFILE_CONTROLS_20261106.md)单独保留，不混用source。 |
| SymPy新增候选 / 旧时序 | [集合语义复现](results/ALFWORLD_LEARNING_RUNTIME.md#sympy-intersection)；[旧时序](../../docs/archive/2026-11-06_agent_research_context/contextbench_sympy_20261104.md)。 |
| Django 读取、前置反馈和同候选续修 | [Django](../../docs/archive/2026-11-06_agent_research_context/contextbench_django_20261104_05.md) |
| Sphinx 失败状态与摘要/续写 | [Sphinx](../../docs/archive/2026-11-06_agent_research_context/sphinx_recovery_20261105.md) |
| Requests 参考冲突，为什么不继续 | [Requests](../../docs/archive/2026-11-06_agent_research_context/requests_development_20261105.md) |
| RethinkSkill 原生反馈和门控 | [相关工作短页](IJCNN_RELATED_WORK_REFRESH_20261030.md) → 该页指定的接口记录。 |
| 早期可视化、办公、重试或 skill 试验 | [历史主题目录](../../docs/archive/2026-11-06_agent_research_context/README.md)，先选一个主题。 |
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
