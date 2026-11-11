# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active。inquiry：first-principles→minimal-experiment；专家8ab61632评审＋后续证据；新增CL-Bench原生SQL开发控制，模型/训练0。

## 目标与裁决

面向IJCNN 2027和硕士研究，复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**Agent怎样用真实反馈调整行动与经验适用范围，在任务/工具/环境变化后提高原生成功率，或以同等成功降低总成本？目标不绑定方法名；CCER/ECCE为工具，通用FCDR流程已停止作为独立贡献。

**当前判断：**通用FCDR与VBL重合；异步面板被简单规则覆盖。CL-Bench完整schema取证便宜，首个旧绑定差异仍被原生容差接受。预算选择尚无独立方法/收益证据。

**专家原则：**真实反馈→决策变化→任务/成本收益。送达、可靠性、采纳与能力分开；自测是线索，事后评分不算在线反馈。hash定位来源，不替代语义适用性判断；源码变化不使全部旧证据失效。保留研究问题、公平对照和可反驳条件；FCDR首推、一周六臂矩阵按新证据调整，48小时尸检不重做。完整方法阅读不等于复现。

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
2. **最新裁决。**[CL-Bench控制](results/CODE_SOURCE_CORRECTIONS.md#clbench-budget-screen)发现迁移有通知、完整schema只需1查询/2.3KB；Q101旧绑定仍满足原1%容差，Q109等价SQL可避10秒超时。不改评分，不当Agent结果；无学习调度器必要性证据。此前[行动控制](results/CODE_SOURCE_CORRECTIONS.md#action-state-controls)及[三臂](results/CODE_SOURCE_CORRECTIONS.md#async-decision-comparison-result)保持闭合。
3. **下一项交付。**先用普通Agent及当前元数据刷新定位真实决策断点，选原生评分能区分行动的开发题，来源须由Agent实际完成。复用请求/动作桥，先小批，不装完整新框架或六臂矩阵。候选须回答：简单策略还错在哪里？具体改变哪次行动？相对最近邻多了哪条规则/学习信号？无残差或只是改名就否决预算选择假设；不以继续读论文代替裁决。
4. **最小配对批次。**三问成立后，先比较普通恢复、最强简单策略、候选；统一模型、OpenCode、初态、公开信息/权限和总预算，形成与验证计费。调用前冻结具体请求/token/墙时帽及反证，按任务随机运行顺序。候选必须实际执行，不将回退当方法成功；D已知修法不注入。近邻按实际实现标注，出现信号再补完整矩阵。
5. **扩样与定稿。**开发信号在两个项目成立后，冻结机制再用未曝光任务、重复及消融检验；关闭探针选择、打乱反馈、同预算重试排除额外信息/尝试收益。按方差定规模，可靠监督后按需训练；12月中旬裁决IJCNN路线。

### 明确停止条件

- 原法/简单策略同效更省，或只改动作无任务/成本收益：停当前机制。
- 无适用反馈/竞争行动，或主要是能力不足：换问题，不追加提醒。
- 独立任务不复现或收益来自额外信息/尝试：收窄或转向。

每批报告假设、基线增量、全成本及下一动作。记录反馈采纳/适用回归，形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率：**只推进一个候选；每批裁决继续/转向/停止，附假设、基线增量、全成本和唯一下一动作。复用runner/结果页，维护只修阻断。无机制增量不训练，无任务/全成本收益不扩样；重大转向/新发现再定向请专家。按本计划接续；宿主Goal正文待同步，不暂停/重建Goal。

**待验证假设：**有限复验预算下，来源新鲜程度未必等于它对当前行动的影响；能否按可观察前提及开发态真实后继效用选择复验来源？须超出SkillApt的加载选择、OMCE路由与Bayesian Control取证。部署不取关键源标签、不免费遍历各臂，形成成本另计。近期公开新鲜度面板已被便宜规则覆盖，不能据此宣称该假设成立。

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
