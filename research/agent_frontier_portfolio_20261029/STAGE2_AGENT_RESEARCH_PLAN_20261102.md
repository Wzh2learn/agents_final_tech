# 第二阶段：真实反馈如何改变 Agent 决策

> 2026-11-11。Goal active。inquiry：first-principles→minimal-experiment；专家8ab61632评审＋后续实测，原地更新。

## 目标与裁决

面向IJCNN 2027和硕士研究，复用GB10＋OpenCode＋本地模型；Paper E独立等导师反馈。

**主问题：**Agent怎样用真实反馈调整行动与经验适用范围，在任务/工具/环境变化后提高原生成功率，或以同等成功降低总成本？FCDR是候选，CCER/ECCE为组件，目标不绑定名称。

**当前判断：**旧提醒/探针未建立独立收益；历史反馈支持更新仍待检验。

**专家原则：**真实反馈→决策变化→任务/成本收益。送达、可靠性、采纳与能力分开；自测可作线索，事后评分不算在线反馈，源码变化不使旧证据全部过期。48小时尸检已完成。

## 现有证据尸检：不可合并成一种“坏经验”

| 现场 | 可支持的观察 | 不能支持的结论 | 定位 |
|---|---|---|---|
| ALFWorld | 规则14/14恢复 | 复杂选择必要 | [汇总](results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery) |
| Astropy 14995→15082 | 隔离四臂均完成；无历史/摘要19/10 POST，491,274/268,655 tokens | 端到端净收益；FCDR有效 | [隔离批次](results/ASTROPY_ISOLATED_CONTROLS_20261106.md) |
| Matplotlib 24149→24818 | 公开崩溃已修复；较强验收0/2 | 公开目标未修复；经验致错 | [复核](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen) |
| SymPy 21055→21203 | 来源成功；目标1/3对0/3 | 完成或迁移净收益 | [结果/全成本](results/CODE_SOURCE_CORRECTIONS.md#sympy-21203-result) |

均为曝光开发题。ALF教师未见事后追加的旧拒绝，7动作不能证明黑名单误用。

## 当前执行顺序

1. **旧循环关闭。**[尸检](results/CODE_SOURCE_CORRECTIONS.md#fcdr-feedback-review)、[六臂](results/CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-result)、[探针](results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)、[回归](results/CODE_SOURCE_CORRECTIONS.md#branch-scope-result)已闭合。保留A5恢复tokens少27.95%信号；219项未触及编辑函数。旧提示/选择器与ALF饱和面板不扩跑。
2. **先明确机制差异。**[支持更新候选](results/CODE_SOURCE_CORRECTIONS.md#feedback-support-candidate)须给出不同于普通恢复/条件化回放的具体行动及预期收益。Skill-V、StateWise与本次补核StateGraph已覆盖适用条件、范围及保守撤回，不能只增加图或标签。
3. **下一项交付。**找一个旧反馈与当前证据分歧的可执行现场，固定可见输入、范围和竞争行动；先检验普通恢复/状态版本规则是否已解决。迁移须有真实成功来源。两公开链只作显式变化开发对照。没有差异就改机制，不为凑样本建adapter。
4. **配对验证。**先三臂：普通恢复、最强简单策略、候选；按假设补历史/重试/最近邻。统一模型、harness、初态、信息、权限和总预算。修订前固定验证依据；额外取证计费。共享前提失效仍是假设，不默认跨经验传播。
5. **扩样与定稿。**两项目有一致信号后再做未曝光任务、重复及消融；关闭机制/打乱反馈/仅截短上下文排除替代解释。按方差定规模，可靠监督后按需训练；12月中旬裁决IJCNN路线。

### 明确停止条件

- 原法/简单策略同效更省，或只改动作无任务/成本收益：停当前机制。
- 无适用反馈/竞争行动，或主要是能力不足：换问题，不追加提醒。
- 独立任务不复现或收益来自额外信息/尝试：收窄或转向。

每批报告假设、基线增量、全成本及下一动作。记录反馈采纳/适用回归，形成/执行/训练/研发分账，缓存分列、未知不填零；开发/确认及评分参考隔离。运行按[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)授权。

**效率：**一批一假设，先写预算、反证及结果将改变的决策；闭合即取舍。复用runner/结果页，无新证据不重开检查。重大转向/突破请专家，不阻塞独立工作。宿主Goal仍有效，建议移除已完成的48小时阶段，人工编辑非前置。

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
