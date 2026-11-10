# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active。inquiry：first-principles→minimal-experiment；专家8ab61632评审＋后续实测，原地更新。

## 目标与裁决

面向IJCNN 2027和硕士研究，复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**Agent怎样用真实反馈调整行动与经验适用范围，在任务/工具/环境变化后提高原生成功率，或以同等成功降低总成本？FCDR是候选，CCER/ECCE为组件，目标不绑定名称。

**当前判断：**异步三臂未改善；停止自由原因表/粗行动标签版本。下一先核可执行行动定义与近邻增量，尚无自动机制收益。

**专家原则：**真实反馈→决策变化→任务/成本收益。送达、可靠性、采纳与能力分开；自测是线索，事后评分不算在线反馈。hash定位来源，不替代语义适用性判断；源码变化不使全部旧证据失效。48小时尸检已完成，不因更新Goal重开。

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
2. **最新对照。**[异步三臂×两seed](results/CODE_SOURCE_CORRECTIONS.md#async-decision-comparison-result)均5/6。两个规划未形成JSON；单请求交付控制虽成型，3假设全归同一宽泛行动，探针仍未执行。停止该形成版本，不将本批解读成选择公式被证伪或成功源迁移。
3. **下一项交付。**明确哪些不同的可执行操作会导致不同后果；核对CounterMem具体动作验证与CIPO可执行粒度的机制差异，筛出一项可单独验证的增量。单凭模型原因表/行动标签不给“无需取证”结论；差异已被覆盖则转向，不为异步同题追加提示版本。
4. **配对验证。**候选须实际执行后才比较。统一模型、OpenCode、初态、可用信息/权限和总预算，形成与验证计费；D已知修法不注入。普通恢复、复现优先强基线和近邻按实际实现标注。拒绝弱自测已有TACR；历史支持更新须面对Skill-V/StateWise/StateGraph。
5. **扩样与定稿。**开发信号在两个项目成立后，冻结机制再用未曝光任务、重复及消融检验；关闭探针选择、打乱反馈、同预算重试排除额外信息/尝试收益。按方差定规模，可靠监督后按需训练；12月中旬裁决IJCNN路线。

### 明确停止条件

- 原法/简单策略同效更省，或只改动作无任务/成本收益：停当前机制。
- 无适用反馈/竞争行动，或主要是能力不足：换问题，不追加提醒。
- 独立任务不复现或收益来自额外信息/尝试：收窄或转向。

每批报告假设、基线增量、全成本及下一动作。记录反馈采纳/适用回归，形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率：**一批一假设，先定预算、反证及结果将改变的决策；闭合即取舍。复用runner/结果页，不新建平行规划。维护只修当前阻断；重大转向/突破再请专家。宿主Goal仍有效；展示文案可删已完成的48小时段，以本计划接续，无须等待人工改字。

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
