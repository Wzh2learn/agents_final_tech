# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active，用户已更新正文。inquiry：first-principles→minimal-experiment；完整读取专家8ab61632评审1082行，并按后续原生结果更新裁决。

## 目标与裁决

面向IJCNN 2027和硕士研究，复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**Agent怎样依据真实执行反馈修正当前决策，在任务/工具/环境变化后保留有用经验，提高原生成功率，或以同等成功降低全流程成本？先发现可识别机制，再做独立确认和论文；不绑定FCDR、CCER或某种训练。

**近期优先：**有限预算下，依据真实反馈及固定Agent的实际纠正能力，选择最值得重新核验的经验或证据。这是待检验候选；先明确一个简单策略尚未解决的决策节点，以及相对最近邻的可执行规则差异。

**当前判断：**[27B真实修复](results/CODE_SOURCE_CORRECTIONS.md#native27-capability)完成公开数组赋值问题，完整原生1/2、回归3/3；已找到可执行路径，非方法收益。16946三臂失败已闭合，EVSI仅参考。下一请专家定向指导形式化、算法增量及最小前后对照，尚无成立新方法或在途外审。

**inquiry裁决。**规则已解决ALF旧面板，普通历史在Astropy有成本信号，代码失败不全是坏经验。主攻反馈改变有价值决策，不预设修订有效；待证主动选证能否超过同预算简单策略。尸检闭合，自测作线索，事后评分不作在线反馈。

**每批只答四问：**反馈改变哪个具体决策？最强简单策略还剩什么未解？与最近邻的执行规则差在哪？什么原生结果或全成本观察决定继续、转向或停止？写在既有回执。方法有明确增量即可验证，不等新通用理论；原型和数学检查不替代实测。

## 现有证据尸检：不可合并成一种“坏经验”

| 现场 | 可支持的观察 | 不能支持的结论 | 定位 |
|---|---|---|---|
| ALFWorld | 规则14/14恢复 | 复杂选择必要 | [汇总](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery) |
| Astropy 14995→15082 | 隔离四臂均完成；无历史/摘要19/10 POST，491,274/268,655 tokens | 端到端净收益；FCDR有效 | [隔离批次](results/ASTROPY_ISOLATED_CONTROLS_20261106.md) |
| Matplotlib 24149→24818 | 公开崩溃已修复；较强验收0/2 | 公开目标未修复；经验致错 | [复核](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen) |
| SymPy 21055→21203 | 来源成功；目标1/3对0/3 | 完成或迁移净收益 | [结果/全成本](results/CODE_SOURCE_CORRECTIONS.md#sympy-21203-result) |

均为曝光开发题。ALF教师未见事后追加的旧拒绝，7动作不能证明黑名单误用。

## 当前执行顺序

1. **已闭合。**[尸检](results/CODE_SOURCE_CORRECTIONS.md#fcdr-feedback-review)、[六臂](results/CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-result)、[探针](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)、[回归](results/CODE_SOURCE_CORRECTIONS.md#branch-scope-result)、[NumPy](results/CODE_SOURCE_CORRECTIONS.md#numpy-state-scope-screen)。A5局部成本信号保留；219项未触及编辑函数，NumPy重验便宜。饱和面板不扩跑。
2. **普通基线现场已闭合。**[SQL](results/CODE_SOURCE_CORRECTIONS.md#clbench-agent-pilot)与[SymPy16988](results/CODE_SOURCE_CORRECTIONS.md#sympy-source-continuation-result)已保留普通历史/接续、全成本及接口/语义边界。失败来源不包装为成功，16953不合格目标不迁移，不扩本题提示或来源。
3. **候选与唯一下一动作。**27B能力诊断闭合，不再加同题配置；共同失败不造偏好，同参考修复不计独立迁移。给专家的候选问题为：普通执行已有事实反馈时，按预算只购买最有价值的缺失对照，并处理选择偏差。尚未实现或验证增量；SkillApt已有配对更新，ERRAND已有免费观察及付费复验，须明确相对它们的不同执行规则。
4. **最小配对批次。**四问成立后，共享可购池/学习器，比等全成本并补等配对数；未购买标签不可读取。保留普通恢复、固定开发指导＋同预算重试及无经验/历史。同模型/OpenCode、初态、信息/权限，先冻结请求/token/墙时帽、顺序、预期复用次数来源及反证；执行成本报价与实际成本分报。原型只在同作用域建模，跨变化泛化未证。
5. **确认与写作。**两个独立项目出现开发信号后，冻结机制，扩未曝光任务、重复和关键消融；用匹配近邻排除替代解释。可靠监督及收益明确后再训练，同数据/训练量并做反馈打乱。主结果、全成本和非退化齐备后写有效性结论；12月中旬裁决IJCNN。

### 明确停止条件

- 原法/简单策略同效更省，或只改动作无任务/成本收益：停当前机制。
- 无适用反馈/竞争行动，或主要是能力不足：换问题，不追加提醒。
- 独立任务不复现或收益来自额外信息/尝试：收窄或转向。

每批报告假设、基线增量、全成本及下一动作。记录反馈采纳/适用回归，形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率与退出：**一次一个候选，先明确决策节点/规则增量，再冻结请求、token、墙时帽。先强简单比较，按需近邻/消融；复用runner与记录，治理只修阻断。用户拟暂停科研并优先开题，状态以Goal为准；本轮先收拢后请专家，不另开批次。

## 导师指导与开题交接（11-11，用户转述）

Paper E老师先审后提交；开题报告和答辩由独立对话优先完成。研究点先明确问题、机制、形式化、假设及算法步骤，再用实验验证；不要求超过benchmark最优，但须对照无方法、最强简单策略及匹配近邻。选有解释力的结果组织叙事，保留影响判断的失败，避免事后挑选当确认。

有限预算选证先定义公开状态/反馈、经验适用性、候选核验、更新规则及目标成功—总成本约束；这是问题形式化，尚非成立算法或理论贡献。当前关键是核验结果如何改变后继行动，及为何比直接重读、随机取证或固定规则更有效。开题可提出待检验方法，现有结果作动机/开发证据；不把三个计划点写成三个已完成创新。GB10教学资料答辩后再沉淀。

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
