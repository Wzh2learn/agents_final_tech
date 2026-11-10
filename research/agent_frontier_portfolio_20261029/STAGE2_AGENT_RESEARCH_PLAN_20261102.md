# 第二阶段：Agent 经验学习与变化适配

> 更新：2026-11-11。Goal已由用户暂停；当前只同步成果并准备方法设计评估。下述近邻是文献核查笔记，不代表原法复现。

## 目标与裁决

面向 IJCNN 2027 和硕士研究，探索Agent在任务、工具或环境变化后，如何利用执行反馈调整经验并改善真实任务。复用GB10、OpenCode、本地模型与执行器；与Paper E独立。

**尚无已验证新方法。**配对干预、局部修订、进度/验收控制与上下文恢复均有近邻，具体重合待外部核验。本次Goal暂停来自用户指令，不能由旧计划自行恢复。

**专家任务：**据下表判断瓶颈，提出至多两个算法并推荐一个；给出与近邻/强基线的不同决策、可观测预测、48小时原型及一周反证实验。可改变研究切口，优先完成方法取舍。

候选要重新进入实验，必须同时满足：
1. 写出算法相对最接近方法/强规则的不同决策；参照[近邻笔记](IJCNN_RELATED_WORK_REFRESH_20261030.md)。
2. 来源真实成功、目标独立原生评分；按任务/项目分组留出，轨迹切片不算独立任务。
3. 匹配信息、模型、权限、重试及总预算，预先写反证条件。

无可检验差异就换问题，不以请求数量代替贡献。

## 现有证据尸检：不可合并成一种“坏经验”

| 现场 | 可支持的观察 | 不能支持的结论 | 定位 |
|---|---|---|---|
| ALFWorld `clean03` | 对象冲突已送达，8B仍选错；公开规则成功 | 复杂选择必要；记忆导致失败 | [来源记录](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery) |
| ALFWorld 局部修订 | `clean02/03` 两臂均成功、动作数持平；`heat03` 两臂均失败，修订另有形成成本 | 修订提高成功率或效率 | [实验汇总](results/ALFWORLD_ADDITIONAL_SOURCES.md) |
| Matplotlib 23562→27361 | 自写透明结果卡臂触发冻结回归；事后普通反馈重试与清单反馈都修复 | 卡片中的经验规则导致回归；清单优于普通反馈 | [隔离批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md) |
| Astropy 14995→15082 | 自建测试调用不存在的方法，反馈后未修复；上游回归不等于Agent引发 | 经验导致错误；适配有效 | [批次](results/ASTROPY_PROFILE_CONTROLS_20261106.md)、[源—目标](results/ASTROPY_ISOLATED_CONTROLS_20261106.md) |
| Sphinx #8282→#8127 | Agent 多轮收到任务失败反馈仍未编辑；教师提案也未解决原题 | 经验适配导致失败，或技能迁移已成功 | [纠正记录](results/CODE_SOURCE_CORRECTIONS.md#sphinx-新来源公开问题与实际运行11-09) |
| Matplotlib 24149→24818 | 35B＋OpenCode真实解决来源；完整卡/无经验/移除实现单元均目标0/2、回归61/61，三臂都采用None兜底 | 经验单元干预改善成功；共同错误由经验造成 | [NaN开发对照](results/CODE_SOURCE_CORRECTIONS.md#nan-transfer) |
| SymPy 21055→21203 | 来源1/1＋13/13；目标来源卡1/3、无经验0/3，回归均124/124、各24 POST封顶。含来源形成总tokens为817,915对807,711 | 目标完成；学习/修订有效；单题可估计泛化 | [最新结果](results/CODE_SOURCE_CORRECTIONS.md#sympy-21203-result) |

**尸检判断：**反馈质量、模型采纳和任务能力有不同断点，不能合并为一种“坏经验”训练标签。EFC、SkillApt/RADEG及STALE分别涉及反馈链、配对效用与过时记忆后的行为适配；分解本身仅作诊断。沿真实反馈→后续请求→动作→原生结果定位具体决策，再查最近邻；没有区别就改问题。

## 研究执行顺序

1. **证据：**核对raw、动作、反馈与评分；失败来源、泄漏或非独立评分不能进入确认集，曝光任务只作开发。
2. **算法：**从矛盾提出动作决策，核对最近邻、版本规则、完整重测和普通重试；给出可反证预测。
3. **开发：**小批匹配模型/工具/信息/预算，对照无经验、完整经验、强规则、普通修订/重试及最近邻；训练按需要。
4. **确认：**有信号后扩独立任务/环境；冻结留出集，记录目标成功、源回归、动作、失败和形成至验证全成本。

### 明确停止条件

- 简单规则、完整重测或普通重试达到相同效果且更省：停止复杂机制。
- 经验文字改变但动作/原生结果不变：停止当前机制。
- 增益只来自更多尝试、更多上下文、教师信息或工具权限：不归因给方法。
- 目标来源曝光、源经验失败或评分不独立：不进入确认集。
- 换独立任务/环境后优势消失：不宣称泛化；收窄或换题。

模型、harness、训练、经验形成及研发成本分账；POST为零不代表无计算，未知不填零。保留raw，以原生终态判断成功。运行/投稿/公开按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

## 按问题加载证据

| 问题 | 先读 |
|---|---|
| ALFWorld进度、反馈、简单规则 | [实验补充](results/ALFWORLD_ADDITIONAL_SOURCES.md) |
| 经验修订/测试反馈是否改变行为 | [Matplotlib批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)、[Astropy批次](results/ASTROPY_PROFILE_CONTROLS_20261106.md) |
| 代码任务来源、迁移与教师修复 | [代码纠正](results/CODE_SOURCE_CORRECTIONS.md)、[依赖扫描试验](DEPENDENCY_SCOPE_AGENT_PILOT_RETURN_20261031.md) |
| 方法新颖性与实验对照 | [近邻审计](IJCNN_RELATED_WORK_REFRESH_20261030.md) |
| 工具、预算与版本资格 | [项目入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)、[SkillsBench资格](SKILLSBENCH_SOURCE_QUALIFICATION_AND_PLAN.md) |

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
