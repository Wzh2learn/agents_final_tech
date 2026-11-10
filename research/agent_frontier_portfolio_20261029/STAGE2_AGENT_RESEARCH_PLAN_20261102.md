# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active；节点核对闭合，下一为恢复干预筛查。inquiry：minimal-experiment；专家基准8ab61632。

## 目标与裁决

面向IJCNN 2027和硕士研究，探索Agent如何利用真实反馈调整行动与经验，适应任务、工具或环境变化。复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**真实反馈能否帮助Agent识别失效的决策前提，选取必要的新证据并调整行动，从而提高任务成功或降低总成本？FCDR是当前候选，名称和算法可换；CCER为工具组件，ECCE不独立立项。

**待检验三点：**A反馈后存在可改变的决策；B干预优于普通恢复及规则；C收益跨任务且覆盖全成本。首批支持A的筛查价值，未证实范围误用；B/C须实际执行。

专家建议按此吸收：先证实反馈改变了什么，再检验是否值得复用。范围标签、依赖图和测试门已有[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)；当前重点是区分性取证如何改善修复。静态回放不产生收益，文件变化只触发重新核验，自测仍可提供局部反馈。

## 现有证据尸检：不可合并成一种“坏经验”

| 现场 | 可支持的观察 | 不能支持的结论 | 定位 |
|---|---|---|---|
| ALFWorld `clean03` | 对象冲突已送达，8B仍选错；公开规则成功 | 复杂选择必要；记忆导致失败 | [来源记录](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery) |
| ALFWorld 局部修订 | `clean02/03` 两臂均成功、动作数持平；`heat03` 两臂均失败，修订另有形成成本 | 修订提高成功率或效率 | [实验汇总](results/ALFWORLD_ADDITIONAL_SOURCES.md) |
| Matplotlib 23562→27361 | 自写透明结果卡臂触发冻结回归；事后普通反馈重试与清单反馈都修复 | 卡片中的经验规则导致回归；清单优于普通反馈 | [隔离批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md) |
| Astropy 14995→15082 | 隔离四臂均完成；无历史/历史摘要目标19/10 POST、491,274/268,655 tokens。另一配置自测调用不存在方法，不能混作单因素对照 | 已有端到端净收益；FCDR有效 | [隔离四臂](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)、[另一配置](results/ASTROPY_PROFILE_CONTROLS_20261106.md) |
| Sphinx #8282→#8127 | Agent 多轮收到任务失败反馈仍未编辑；教师提案也未解决原题 | 经验适配导致失败，或技能迁移已成功 | [纠正记录](results/CODE_SOURCE_CORRECTIONS.md#sphinx-新来源公开问题与实际运行11-09) |
| Matplotlib 24149→24818 | 35B＋OpenCode真实解决来源；完整卡/无经验/移除实现单元均目标0/2、回归61/61，三臂都采用None兜底 | 经验单元干预改善成功；共同错误由经验造成 | [NaN开发对照](results/CODE_SOURCE_CORRECTIONS.md#nan-transfer) |
| SymPy 21055→21203 | 来源1/1＋13/13；目标来源卡1/3、无经验0/3，回归均124/124、各24 POST封顶。含来源形成总tokens为817,915对807,711 | 目标完成；学习/修订有效；单题可估计泛化 | [最新结果](results/CODE_SOURCE_CORRECTIONS.md#sympy-21203-result) |

**判读边界：**均为曝光开发题；Astropy优势限已有来源的目标成本。ALF教师68动作未看到事后追加的旧拒绝，7条动作不能证明永久黑名单错误。反馈质量、采纳、能力分开；静态轨迹只能定位干预点，替代动作收益须实际验证。

## 当前执行顺序

1. **尸检完成，不重开48小时整理。**[9轨迹/9节点](results/CODE_SOURCE_CORRECTIONS.md#fcdr-feedback-review)定位普通恢复与Astropy停滞；未见已证实的范围误用。
2. **最小筛查。**[合同](results/CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-pilot)：Astropy两个曝光现场×普通恢复/简单规则/动态反馈三臂，≤48 POST。原型17项GB10离线检查通过，真实harness接合待检；未运行模型。它目前提示QUERY/PIVOT，尚非完整前提匹配或最优探针算法。有修复/成本信号才进入下一步，持平即停止本题追加。
3. **跨项目机制检验。**在已具真实成功来源的项目递进比较，冻结两个seed、随机顺序；模型/OpenCode、公开信息、权限、状态和总预算一致。补无经验、完整历史、同预算重试及适用近邻；简化适配不称原法复现。
4. **确认与写作。**约一周作开发取舍；至少两个项目有信号，再扩未曝光目标并消融取证、范围与提醒，按方差定规模。12月中旬决定IJCNN路线；方法与结果成形后写作。可靠监督出现后按需训练，无残差及时换机制。

### 明确停止条件

- 无适用在线反馈、无可改变节点：停止当前FCDR版本；不反复加prompt或资格分支。
- 规则/普通恢复同效更省，或只改动作却无成功/成本收益：停止或修订机制。
- 收益来自额外信息/尝试/权限，或独立任务不复现：收窄或换题，不包装为方法增量。

每批报告假设、增量、全成本和下一动作。主看成功/成本，另记反馈采纳及适用回归。形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。工程服务当前实验，重大转向可请专家。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

## 按问题加载证据

| 问题 | 先读 |
|---|---|
| ALFWorld进度、反馈、简单规则 | [实验补充](results/ALFWORLD_ADDITIONAL_SOURCES.md) |
| 经验修订/测试反馈是否改变行为 | [Matplotlib批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)、[Astropy批次](results/ASTROPY_PROFILE_CONTROLS_20261106.md) |
| 代码任务来源、迁移与教师修复 | [代码纠正](results/CODE_SOURCE_CORRECTIONS.md)、[依赖扫描试验](DEPENDENCY_SCOPE_AGENT_PILOT_RETURN_20261031.md) |
| 方法新颖性与实验对照 | [近邻审计](IJCNN_RELATED_WORK_REFRESH_20261030.md) |

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
