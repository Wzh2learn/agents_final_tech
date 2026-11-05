# 第二阶段：Agent 经验学习与变化适配

> 2026-11-06 | 唯一现役执行计划，原地更新。长期问题见[研究组合](AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，对标见[相关工作](IJCNN_RELATED_WORK_REFRESH_20261030.md)。逐轮证据从本页按需加载，不全文追加到本页。

## 当前目标和次序

Goal active。主攻第二篇和硕士研究：Agent 从真实执行/反馈形成经验，并在任务、工具或环境变化后选择、验证和修订经验。IJCNN 2027 为目标窗口；Paper E 已交导师，等待反馈，ICINT 首投、ICDAR 顺序备投。

默认搜索与文档分层已更新，三端同步以Git实测为准。Astropy 普通 skill 臂已自然结束并归位；未为整理重跑或覆盖它。结果卡已结束且未完成完整修复。下一检查点是统一较大上下文/输出配额下的强基线比较，；Matplotlib原题/base/gold已完成资格，尚未运行Agent。详见当前批次合同与[新来源资格](results/MATPLOTLIB_QUALIFICATION_20261106.md)。

## 最新开发证据：Astropy

源 `14995` → 目标 `15082`；目标正文已公开提及源 PR，各臂共享此信息。独立原题、base/gold 和完整回归先完成资格验证；详见[批次结果与复放入口](results/ASTROPY_PILOT_20261106.md)。

| 条件 | 问题测试 | 回归 | POST / reported tokens | 执行状态 |
| --- | --- | --- | --- | --- |
| 源无历史 | 1/1 | 179/179 | 14 / 154,712 | 正常退出 |
| 目标无历史 | 0/3 | 132/132 | 15 / 246,557 | 正常退出；数值正确但 mask 契约未满足 |
| 目标普通历史 | 0/3 | 132/132 | 6 / 79,588 | 进程0但模型length终止；原题仍异常，长行被截断 |
| 目标普通 skill | 3/3 | 132/132 | 24 / 351,534 | 达请求上限、Agent exit1；独立产物和原题行为通过 |
| 目标结果卡 | 0/3 | 132/132 | 24 / 298,054 | 达请求上限；mask仍为全False |

普通 skill 形成另用 1 POST / 8,565 tokens；缓存读取包含在报告 tokens 中，不再相加。以上为一个已曝光任务对、单 seed；有正向开发线索，尚非方法或跨来源确认。混合 wheel 原生扩展及 NumPy ABI 警告在所有臂保留。普通历史源题行被截短，但源补丁完整读取；末次8192输出以length结束。skill32行完整读取。新批次统一更大配额并加入长行安全历史和源补丁摘要。

## 进入投稿稿制作的门槛

现在可同步写问题、相关工作与实验设计；锁定方法和结果须满足：①与最近方法的独立机制清楚；②至少两个独立项目来源的持有任务，来源隔离并重复验证；③超过无历史、普通历史/skill、简单修复及公开近邻中的最强者，或在效果相当时有明确总成本收益；④同预算对照与消融能解释收益，未修复/截断单列；⑤冻结确认后的区间、失败和复放可核查。确认样本量依据开发方差决定，统计单位是任务/来源而非测试条数。若简单方法解释收益，调整候选；不将旧工程故障计作方法证据。

## 实验合同

1. 冻结题面、源码、实际原题参考、模型/工具、seed、输入经验和预算，再比较；目标补丁/测试和未来 Git 历史不进入 Agent 工作区。
2. source 经验来自真实执行、最终产物与独立反馈；区分动作截断、摘要失真、工具未读到及下游行为。测试通过、正常退出、预算耗尽分别报告。
3. 比较无历史、普通历史/摘要、普通 skill、强简单规则和公开近邻。形成、检索、验证、执行及失败重试均记成本；先有残差再引入复杂方法。
4. 不同来源与变化类型可自主开发。重复/确认按具体科学问题和原始账本安排，开发证据不冒充未见来源；旧停止结论不外推为方向无效。
5. 新尝试使用显式 attempt 路径，保留旧 raw/评分与成本。跨机器预算锁尚未实现，不并发使用同一额度；已有输出不得覆盖。

## 按问题加载证据

| 要解决的具体问题 | 只加载这些材料 |
| --- | --- |
| 当前 Astropy 比较与下一臂 | [当前批次](results/ASTROPY_PILOT_20261106.md)，再按其中路径读取私有 completed/raw/冻结输入；不先扫全部历史。 |
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

保留已有深链接；每项直接指向对应证据，不扩充启动正文。

<a id="当前优先级2026-11-04"></a>
[原章节：当前优先级（2026-11-04）](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
[原章节：地震与板块工作流：下一组开发对照（2026-11-03）](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="两条并行问题线"></a>
[原章节：两条并行问题线](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="输入格式变化的可视化工作流资格与开发2026-11-04"></a>
[原章节：输入格式变化的可视化工作流：资格与开发（2026-11-04）](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="evoclaw-配置迁移公开反馈与独立合同2026-11-04"></a>
[原章节：EvoClaw 配置迁移：公开反馈与独立合同（2026-11-04）](../../docs/archive/2026-11-06_agent_research_context/workflow_development_20261103_04.md)

<a id="swe-skills-bench--aiohttp真实项目执行资格2026-11-04"></a>
[原章节：SWE-Skills-Bench / aiohttp：真实项目执行资格（2026-11-04）](../../docs/archive/2026-11-06_agent_research_context/aiohttp_development_20261104.md)

<a id="swe-skills-bench--sympy第二项目资格2026-11-04"></a>
[原章节：SWE-Skills-Bench / SymPy：第二项目资格（2026-11-04）](../../docs/archive/2026-11-06_agent_research_context/sympy_skill_development_20261104.md)

<a id="swe-contextbench真实问题对与经验时间边界2026-11-04"></a>
[原章节：SWE-ContextBench：真实问题对与经验时间边界（2026-11-04）](../../docs/archive/2026-11-06_agent_research_context/contextbench_sympy_20261104.md)

<a id="升级后目标接续2026-11-05用户已恢复"></a>
[原章节：升级后目标接续（2026-11-05，用户已恢复）](../../docs/archive/2026-11-06_agent_research_context/sphinx_recovery_20261105.md)

<a id="任务组合和实验顺序"></a>
[原章节：任务组合和实验顺序](../../docs/archive/2026-11-06_agent_research_context/skillflow_retry_qualification_20261104.md)

<a id="当前来源资格skillevolbench-的-api-重试族"></a>
[原章节：当前来源资格：SkillEvolBench 的 API 重试族](../../docs/archive/2026-11-06_agent_research_context/skillflow_retry_qualification_20261104.md)

<a id="不同来源的连续办公任务开发2026-11-0304"></a>
[原章节：不同来源的连续办公任务开发（2026-11-03—04）](../../docs/archive/2026-11-06_agent_research_context/office_workflow_20261103_04.md)

<a id="恢复研究requests-自然任务对2026-11-05"></a>
[原章节：恢复研究：Requests 自然任务对（2026-11-05）](../../docs/archive/2026-11-06_agent_research_context/requests_development_20261105.md)

<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
[原章节：工具修复、反馈接入与 Astropy 批次（2026-11-05）](results/ASTROPY_PILOT_20261106.md)

<a id="与-paper-e-并行"></a>
[原章节：与 Paper E 并行](../../docs/archive/2026-11-06_agent_research_context/astropy_pre_neat_20261105_06.md)
