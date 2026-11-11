# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active，用户已更新正文。inquiry：first-principles→minimal-experiment；完整读取专家8ab61632评审1082行，并按后续原生结果更新裁决。

## 目标与裁决

面向IJCNN 2027和硕士研究，复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**Agent怎样依据真实执行反馈修正当前决策，在任务/工具/环境变化后保留有用经验，提高原生成功率，或以同等成功降低全流程成本？先发现可识别机制，再做独立确认和论文；不绑定FCDR、CCER或某种训练。

**近期优先：**有限预算下，依据真实反馈及固定Agent的实际纠正能力，选择最值得重新核验的经验或证据。这是待检验候选；先明确一个简单策略尚未解决的决策节点，以及相对最近邻的可执行规则差异。

**当前判断：**尚无成立的新方法。新核AMV-Guard/ERRAND/ATR直接覆盖通用预算复验；[解析控制](results/CODE_SOURCE_CORRECTIONS.md#revalidation-neighbor-screen)表明联合行动选择也可由经典决策解释。旧饱和面板闭合；不据此启动新调度器或训练。

**专家建议的吸收与修正。**采纳“真实反馈→具体决策→任务/全成本收益”，不机械执行旧FCDR路线或六臂矩阵。反馈送达、可靠、适用、采纳、能力分开；自测可作线索，事后评分不算在线反馈。hash定位来源，不代替语义适用性；文件变化不使全部旧事实失效。离线行动分歧只定位干预，不能当成功。48小时尸检已闭合，不重复。

**每批运行前只答四问：**哪条已送达的真实反馈能改变哪个决策？最强简单策略为何还不够？新规则/学习信号与最近邻具体差在哪？什么原生结果或全成本观察会让本批继续、转向或停止？写在现有计划/回执，不另建框架。答不清则先定向解决这个问题，不扩任务、模块或训练；普通接续已解释收益的现场及时闭合。

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
2. **最新批次闭合。**[SQL Agent实测](results/CODE_SOURCE_CORRECTIONS.md#clbench-agent-pilot)：23 POST/204,060 tokens，来源未完成；失败轨迹不包装成成功技能。普通历史目标原生成功；刷新组终答正确但未提交，零模型统一提交控制通过。输入截断、提交适配另记，不能当记忆方法失败。一个曝光题对，不扩本题提示或预算选择器。
3. **来源补充已闭合。**[SymPy16988普通接续](results/CODE_SOURCE_CORRECTIONS.md#sympy-source-continuation)：原12 POST未编辑，额外普通新会话6 POST后既定2+72项通过；合计18 POST/200,436 tokens。符号条件的更广语义未解决，16953目标资格仍未过，不启动迁移或继续来源提示。
4. **下一项研究交付。**给出一个“复验能让固定Agent完成纠正”的具体决策节点及可执行机制；对照AMV局部停止值、Bayesian Control转换模型和普通条件化价值基线。条件化价值公式本身不是差异，不能只把拒绝代价换成Q网络。先完成上述四问，再冻结最小配对；重大增量不明时请专家定向核对，不再泛搜、重复尸检或追加成功来源。
5. **最小配对批次。**存在原生任务残差后，再比较普通恢复、最强简单策略、候选；普通历史/无经验按归因加入。同模型/OpenCode、初态、公开信息/权限及总预算，调用前冻结请求/token/墙时帽、顺序和反证。候选不拿隐藏关键源标签，不免费试各臂；输入/接口仅修必要项，回退不算方法成功。四个已知分布解析控制不算真实Agent或跨项目收益。
6. **确认与写作。**两个独立项目出现开发信号后，冻结机制，扩未曝光任务、重复和关键消融；用匹配近邻及同预算重试排除替代解释。训练仅在监督可靠且目标明确时开展，必须同数据/训练量比较并控制配对或反馈打乱。主结果、全成本和非退化齐备后写有效性结论；12月中旬裁决IJCNN路线。

### 明确停止条件

- 原法/简单策略同效更省，或只改动作无任务/成本收益：停当前机制。
- 无适用反馈/竞争行动，或主要是能力不足：换问题，不追加提醒。
- 独立任务不复现或收益来自额外信息/尝试：收窄或转向。

每批报告假设、基线增量、全成本及下一动作。记录反馈采纳/适用回归，形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率与退出：**一次一个候选，每批交付支持/推翻的假设、强基线增量、全成本及唯一下一动作。普通恢复/规则已解释收益就停该候选；只改行动未改善原生结果或成本，不升级贡献。复用runner和结果页，治理只修阻断；不默认调用子Agent。预算择证是近期待验证主线，不借饱和面板扩模块。重大转向或新发现再请专家定向复核，不把等待专家作为日常前置。

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
