# 第二阶段：Agent 经验学习与变化适配

> 2026-11-06 | 唯一现役执行计划，原地更新。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，对标见[相关工作](IJCNN_RELATED_WORK_REFRESH_20261030.md)。逐轮证据从本页按需加载，不全文追加到本页。

## 当前目标和次序

Goal active。主攻第二篇和硕士研究：Agent 从真实执行/反馈形成经验，并在任务、工具或环境变化后选择、验证和修订经验。IJCNN 2027 为目标窗口；Paper E 已交导师，等待反馈，ICINT 首投、ICDAR 顺序备投。

2026-11-06核对[IJCNN官方截止](https://ijcnn.org/2027/events/regular-papers-deadline)仍为2027-01-31。内部倒排：11月中旬建立新任务/模型基线，11月底选择有证据的方法；12月独立确认与正文，1月审阅及投稿准备。未达到方法门槛则调整任务或机制，不为赶窗口认证弱证据。

当前执行[ALFWorld clean_2五臂](results/ALFWORLD_TEXT_AGENT_20261106.md#current-transfer)：两源载体已冻结，先核在途/receipt再接续，不重跑reserved根。[SymPy](results/SYMPY_LATEX_TRANSFER_20261106.md)此配置已收口；[Django](results/DJANGO_AGGREGATION_AGENT_20261106.md#current-27b-handoff)源可复用但完整历史超当前writer32K。新方法仍须超过最强普通载体与公开近邻。

## 最新开发证据

`Matplotlib23562→27361`[隔离批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)：无历史/历史/skill均通过关键与完整回归，结果卡出现1项回归；skill少POST但本次token/用时无优势。含source与形成124POST/2,789,460tokens。

`Astropy14995→15082`[隔离批次](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)：四臂关键3/3、回归132/132、原题实际data/mask/unit相符；普通历史目标未缓存输入输出41,264tokens，对无历史83,758，本次94对212秒。skill未超过历史。含source与形成84POST/2,298,659tokens。每任务一次，两个项目不能给出稳定选择规律；两批结果卡信息不同。完整raw与hash按批次加载，[旧四臂](results/ASTROPY_PROFILE_CONTROLS_20261106.md)保留。

## 进入投稿稿制作的门槛

Matplotlib/Astropy的35B无历史接近上限，本批转向8B/27B与非代码变化任务。训练可与经验编译并行推进：从学生真实低效/失败状态重放，由教师产生纠正并实际执行验收，形成反馈监督，再与普通SFT、rehearsal及固定规则比较。反事实rollout本身已有先例；判断学习增量须分离更强教师、额外信息与新机制，来源隔离且不使用确认目标训练。

Django12589→34176使用新采源经验，公开旧轨迹含未来目标题号，不能替代；原题/数据库资格见[本对记录](results/DJANGO_AGGREGATION_PAIR_QUALIFICATION_20261106.md)，不使用业务DB。SymPy14774→19235题面自带修法/前序引用，属开发；目标原144回归有2项共同Python3.8失败，排除后142通过。scikit25638→25637关联同issue，不作独立迁移。

[小模型资格](results/QWEN4B_TOOL_QUALIFICATION_20261106.md)只定位工具与能力，不永久否定4B；当前用8B作学生、27B采真实源经验。先看四臂实际补丁、回归、经验读取和完整成本，再决定较强actor诊断、内容消融或新方法。SkillGLoW已覆盖guard与fresh准入，SkillHEX/CIPO已覆盖执行反馈与反事实rollout；下一候选必须超过[这些近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)，不能把普通摘要换名为创新。

现在可同步写问题、相关工作与实验设计；锁定方法和结果须满足：①与最近方法的独立机制清楚；②至少两个独立项目来源的留出任务，来源隔离并重复验证；③超过无历史、普通历史/skill、简单修复及公开近邻中的最强者，或在效果相当时有明确总成本收益；④同预算对照与消融能解释收益，未修复/截断单列；⑤冻结确认后的区间、失败和复放可核查。确认样本量依据开发方差决定，统计单位是任务/来源而非测试条数。若简单方法解释收益，调整候选；不将旧工程故障计作方法证据。

## 实验合同

1. 冻结题面、源码、实际原题参考、模型/工具、seed、输入经验和预算，再比较；检查全部actor可读挂载而非仅import路径，项目wheel源码、目标补丁/测试和未来Git不进入可读面。
2. source 经验来自真实执行、最终产物与独立反馈；区分动作截断、摘要失真、工具未读到及下游行为。测试通过、正常退出、预算耗尽分别报告。
3. 比较无历史、普通历史/摘要、普通 skill、强简单规则和公开近邻。形成、检索、验证、执行及失败重试均记成本；先有残差再引入复杂方法。
4. 不同来源与变化类型可自主开发。重复/确认按具体科学问题和原始账本安排，开发证据不冒充未见来源；旧停止结论不外推为方向无效。
5. 新尝试使用显式 attempt 路径，保留旧 raw/评分与成本。跨机器预算锁尚未实现，不并发使用同一额度；已有输出不得覆盖。

## 按问题加载证据

| 要解决的具体问题 | 只加载这些材料 |
| --- | --- |
| 当前 Matplotlib 目标对照 | [当前批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)，再按其中路径读取私有completed/raw/冻结输入；不先扫全部历史。 |
| Astropy新隔离比较 | [本批合同与结果](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)；[旧四臂及修正](results/ASTROPY_PROFILE_CONTROLS_20261106.md)单独保留，不混用source。 |
| 真实任务时序 / SymPy | [来源和 SymPy](../../docs/archive/2026-11-06_agent_research_context/contextbench_sympy_20261104.md) |
| Django 读取、前置反馈和同候选续修 | [Django](../../docs/archive/2026-11-06_agent_research_context/contextbench_django_20261104_05.md) |
| Sphinx 失败状态与摘要/续写 | [Sphinx](../../docs/archive/2026-11-06_agent_research_context/sphinx_recovery_20261105.md) |
| Requests 参考冲突，为什么不继续 | [Requests](../../docs/archive/2026-11-06_agent_research_context/requests_development_20261105.md) |
| RethinkSkill 原生反馈和门控 | [相关工作短页](IJCNN_RELATED_WORK_REFRESH_20261030.md) → 该页指定的接口记录。 |
| 早期可视化、办公、重试或 skill 试验 | [历史主题目录](../../docs/archive/2026-11-06_agent_research_context/README.md)，先选一个主题。 |
| 自动记录和工具前提 | [记录器](../../scripts/graph/research_auto_record.py)、[工具检查](../../scripts/graph/research_tool_runtime.py)、对应 runner；不改变业务服务。 |

## 维护规则

本页只保留目标、当前比较、下一动作和证据路由；已结束批次进入有来源的短任务记录。结果不同时复制进 STATE、THREADS 和长期组合。STATE 只留恢复定位，THREADS 只留未决，相关工作只留近邻。单文件与总启动体量由[上下文检查](../../scripts/graph/research_context_check.py)验证，超限先拆主题，不截断原始证据。

科研联网默认 Codex 宿主原生搜索；GB10 隔离 Agent 不直接继承此工具，也不回退到旧 DeepSeek/Qwen 搜索。生产、对外提交、公开与付款继续按现有明确授权处理。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="两条并行问题线"></a>
<a id="输入格式变化的可视化工作流资格与开发2026-11-04"></a>
<a id="evoclaw-配置迁移公开反馈与独立合同2026-11-04"></a>
[当前优先级（2026-11-04） 等原章节](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="swe-skills-bench--aiohttp真实项目执行资格2026-11-04"></a>
[SWE-Skills-Bench / aiohttp：真实项目执行资格（2026-11-04） 原记录](../../docs/archive/2026-11-06_agent_research_context/aiohttp_development_20261104.md)

<a id="swe-skills-bench--sympy第二项目资格2026-11-04"></a>
[SWE-Skills-Bench / SymPy：第二项目资格（2026-11-04） 原记录](../../docs/archive/2026-11-06_agent_research_context/sympy_skill_development_20261104.md)

<a id="swe-contextbench真实问题对与经验时间边界2026-11-04"></a>
[SWE-ContextBench：真实问题对与经验时间边界（2026-11-04） 原记录](../../docs/archive/2026-11-06_agent_research_context/contextbench_sympy_20261104.md)

<a id="升级后目标接续2026-11-05用户已恢复"></a>
[升级后目标接续（2026-11-05，用户已恢复） 原记录](../../docs/archive/2026-11-06_agent_research_context/sphinx_recovery_20261105.md)

<a id="任务组合和实验顺序"></a>
<a id="当前来源资格skillevolbench-的-api-重试族"></a>
[任务组合和实验顺序 等原章节](../../docs/archive/2026-11-06_agent_research_context/skillflow_retry_qualification_20261104.md)

<a id="不同来源的连续办公任务开发2026-11-0304"></a>
[不同来源的连续办公任务开发（2026-11-03—04） 原记录](../../docs/archive/2026-11-06_agent_research_context/office_workflow_20261103_04.md)

<a id="恢复研究requests-自然任务对2026-11-05"></a>
[恢复研究：Requests 自然任务对（2026-11-05） 原记录](../../docs/archive/2026-11-06_agent_research_context/requests_development_20261105.md)

<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[工具修复、反馈接入与 Astropy 批次（2026-11-05） 等原章节](../../docs/archive/2026-11-06_agent_research_context/astropy_pre_neat_20261105_06.md)
