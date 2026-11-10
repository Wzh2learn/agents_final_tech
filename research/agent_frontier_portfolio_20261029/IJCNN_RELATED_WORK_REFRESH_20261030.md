# 第二篇：近邻与实验设计参照

> 2026-11-10 | 短导航；详细检索见[历史目录](../../docs/archive/2026-11-06_agent_research_context/README.md)。读原文不等于复现。11-10新增近邻仅用于收紧创新边界，未复现其结果。

## 优先比较什么

| 近邻 | 已覆盖的方向 / 本项目应对齐的比较 |
| --- | --- |
| [VibeMemBench](https://arxiv.org/abs/2609.23570) | 111个真实仓库目标、冻结且执行验证的跨任务经验、配对memory-off；其已有经验转移与检索系统比较。只做静态转移不足以构成差异；原文未做目标执行中基于新反馈的经验更新。 |
| [After the Fix](https://arxiv.org/abs/2609.34603) | 直接比较同一失败来源在接受修复前/后的经验迁移，并设独立执行起点；3,300次运行覆盖ThinkingBox及APEX的state/text两类handoff。已覆盖“修复后的来源经验是否更能迁移”；必须分开看修复前后差（C−U）与修复经验相对无经验差（C−B-only），因为修复可能只是恢复无经验基线已有的成功。state/text同时改变多项因素，不能视为状态继承的单因素实验，且结果依任务族而异。 |
| [CounterMem](https://arxiv.org/html/2609.31874v1) | 最直接覆盖反事实记忆构造：失败动作后从同一状态副本测试替代，保存已验证的动作对照、结果与适用条件，并训练选择使用或跳过；还在“相似请求但旧修正会出错”的look-alike条件下测量harmful use。留出任务中记忆与选择策略冻结；作者把变化后检测/停用陈旧记录列为后续方向。故“反事实修正＋适用条件＋误用评估”不能单独作为新方法；剩余差异若只是在同一任务中在线改写/停用并保留进度，属于对其明确后续方向的直接延伸，仍需证明有独立机制。 |
| [OMCE](https://arxiv.org/html/2611.01747v1) | 11-01提交；用上下文bandit依据反馈跨任务更新路由策略与经验库，在DIRECT、EPISODE、GUIDE、DISTILL间选择，并在失败attempt后允许同题注入新经验重试。故“在线反馈学习何时用经验、选哪类经验、何时归纳”已直接覆盖；论文未以真实外部部分进度持续演化为研究对象，但只把路由/更新搬进同一任务仍不足以构成贡献。 |
| [MemScope](https://arxiv.org/html/2610.21170) | 10-15提交；Patch Agent联合检查原始成功/失败轨迹、运行时记忆和provider代码，定位后对记忆架构作局部原位修改，保留运行时记忆并记录后续恢复/回归；报告了GAIA、xBench及ALFWorld unseen结果。故“执行证据定位记忆问题＋局部修订＋后续验证”已被直接覆盖。其主要更新对象是provider代码，按任务段更新；与内容级同一活任务例外仍有实现差别，但单靠这一区别不足以构成论文方法。 |
| [Recuris](https://arxiv.org/abs/2608.24876) | 工作记忆跟踪任务进度；结构化轨迹定位失效的记忆组件；Meta-Agent局部修补并经留出任务门控。孤立任务模式用隐藏验证器反馈后重试。Terminal-Bench 2.1中，同为4次尝试时，适配为53/87、冻结记忆重试为51/87（7胜/5负，McNemar p=0.774）；主提升主要来自增加重试次数。故“保留进度＋反馈定位＋局部经验修订＋验证门”已直接覆盖，且必须把学习收益与重试预算分开。其报告不是受控真实软件版本迁移，是否有可检验差异仍待核。 |
| [VCE-Skill](https://arxiv.org/abs/2608.16544) | 把公开技能版本差异蒸馏为可迁移更新经验，再与当前轨迹提出的修改自适应融合；报告跨技能演化及跨模型迁移收益。故“从技能版本变化中学习更新经验”本身已被直接覆盖。它研究的是公共技能版本历史作为演化先验；与真实项目运行中依赖/API版本变化的在线适配是否构成差异，仍需按其完整任务设置核对，不能只靠场景命名主张新意。 |
| [Remember, Verify, or Ask?](https://arxiv.org/html/2608.19564v2) | 10-12版本定义复用时四种处理：持久化、仅当前上下文使用、外部核验、向用户澄清，并用evidence-flip对照评估；但只评分动作选择，不实际执行存储/核验或下游任务。故“临时使用 vs 持久提交/先核验”的决策标签已被覆盖；真正的运行时收益仍需实际执行和对照，不能只评分类别。 |
| [Task Advancement Memory (TAM)](https://arxiv.org/html/2610.37482) | 任务执行中维护已验证进度与剩余目标，并从失败任务中的局部成功操作学习后续可复用操作；任务结束后才把操作提供给后续任务。故“保留当前进度并从局部反馈学习经验”已被直接覆盖。 |
| [SkillShift-Bench](https://arxiv.org/html/2610.33528) | 在环境变化下做测试时动作适配；其MPCR在固定技能库上依当前页面可行性重排候选，经验本身不更新。故只在执行中因反馈改变动作选择不够新。 |
| [From Interaction Traces to Persistent Skills](https://arxiv.org/html/2609.04869) | 计算机使用Agent依据轨迹和评估反馈增删修订持久技能；执行期间冻结技能快照，更新在下一轮生效。覆盖跨轮在线演化，但未覆盖同一运行中更新并续接外部进度。 |
| [What Does a Repair Agent Gain from Remembering Its Failure?](https://arxiv.org/abs/2610.41433) | 75个BugsInPy缺陷、181次失败重试；普通重试是强基线，反思不优于其转录，显著性未过Holm。研究同一缺陷重试，提醒我们区分失败重试与成功经验跨变化迁移。 |
| [Can LLM Agents Learn to Test? / AdaptiTest](https://arxiv.org/abs/2611.05873) | 11-04提交；直接覆盖经验适用范围、轨迹来源、确认/复核/撤回生命周期。评估限于只读GUI工作流，所列变更是UI变化而非已确认回归；部分维护合同也未由归档实现端到端落实。故“给经验加scope、provenance和stale状态”不能单独作为新方法。 |
| [Agent Skills Can Be Harmful](https://arxiv.org/abs/2608.11888) | 对307个skill诱发失败/成本回退做差分归因，比较无skill或语义匹配参照；要求本项目用同一目标、同反馈的配对对照，不能从单臂失败归因经验。其研究静态载入skill，不覆盖跨变化的经验修订。 |
| [Rethinking the Value of Agent-Generated Tests](https://arxiv.org/abs/2602.07900) | 分析5,000次SWE-bench Verified运行，并对4个模型操纵是否写新测试；测试写入频次与成功任务区分有限，提示操纵没有显著改变各模型解决数，但改变了部分调用/token成本。故“让Agent多写测试”或“反馈更充分”本身不是方法；需检验测试反馈是否改变后续修复行为及独立任务结果。 |
| [On the Risks of using LLM-Generated Tests for Regression Testing](https://arxiv.org/abs/2610.11835) | 对145个SciPy/Qiskit/pandas PR研究LLM生成回归测试；报告8%–17%测试会固化错误行为，且可在后续版本中持续通过。直接支持自写测试需与独立行为合同区分，但该工作研究测试随软件演化的风险，不研究Agent跨任务经验更新策略。 |
| [Auditing Feedback-Driven Evolution under the Oracle Problem](https://arxiv.org/abs/2608.19626) | 用开发、锁定外部及留出任务和密度匹配placebo，审计反馈驱动测试生成；单参考oracle可夸大所谓演化收益。它直接覆盖“执行反馈不等于可靠监督”，因此本项目若研究反馈来源，必须用独立评分与等成本placebo分离真实反馈收益；原文研究的是测试生成，不是持久经验的局部修订。 |
| [SkillApt](https://arxiv.org/abs/2609.26863) | 同状态WITH/WITHOUT配对执行学习LOAD/ABSTAIN；附录已有54次软件Agent受控运行，但作者明确不把它称为在线轨迹学习或自主适配。不能把配对证据或选择保留/弃用当作新机制。 |
| [MemSkill](https://arxiv.org/html/2602.02474v2) | 用反馈学习记忆操作及技能，已测ALFWorld。 |
| [SWE-ContextBench](https://arxiv.org/abs/2602.08316) | 真实问题间经验复用；Lite数据已取，成绩未复现。 |
| [RethinkSkill](https://arxiv.org/abs/2608.02636) | 成功/失败反馈、多轮候选与接受门；合法JSON不是方法复现。 |
| [ExecCritic](https://arxiv.org/html/2609.09133v1) / [/retro](https://arxiv.org/html/2610.34938v1) | 前者固定测试再修复；后者检验经验对后续任务的影响。 |
| [Environment-Probing](https://arxiv.org/html/2609.11060v1) / [Scope Before Persist](https://arxiv.org/html/2609.29144v1) | 前者用只读环境探测整理经验；后者用执行验证和作用域约束持久经验。均已覆盖，须比较。 |
| [Skill Inconsistency](https://arxiv.org/html/2610.18927v1) | 用修复前后配对执行区分静态缺陷与实际行为后果；非仅查是否读取。 |
| [SkillGLoW](https://arxiv.org/html/2609.02217v1) | 技能合同与执行准入已有先例；Skill-V与SkillApt见下。 |
| [Skill-R1](https://arxiv.org/html/2605.09359v1) | 冻结actor、验证奖励训练编辑器；正文已核，未复现成绩。 |
| [SkillHEX §3.1/B.2](https://arxiv.org/html/2608.05628v1) | 可执行诊断、缓存重测与fresh执行；产物重测不等于重跑策略。 |
| [CIPO §3.3–3.4/App.B/D](https://arxiv.org/html/2610.04991v1) | 同前缀技能/原子分支、部分续做；world分支复原待核。 |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 固定仓库、有无skill、隐藏检查；区别自然issue与构造任务。 |
| [SkillFlow](https://arxiv.org/abs/2604.17308) | 完整历史、无历史和持续skill库对照；三臂本身非新贡献。 |
| [CFOE](https://arxiv.org/abs/2610.22984) / [CoEvoSkills](https://arxiv.org/abs/2604.01687) | 失败经验迁移及验证器与经验共演化。 |
| [Useful Memories Become Faulty](https://arxiv.org/abs/2605.12978) | 连续抽象可能使经验变差；episodic-only控制不弱于自动整理。比较必须包含原始历史/轨迹和不改写控制，不能预设抽象或局部整理有益。 |

## 已接入到哪一步

RethinkSkill仅接通接口，未部署或复现；[接入](../../docs/archive/2026-11-06_agent_research_context/related_work_candidate_design_20261105.md)、[诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)按需读。

## 机制自审（2026-11-06）

**核查范围**：一手方法正文/附录，未完整复现代码；用来约束候选机制及对照。

- [Skill-V §3.3、B.5–B.6](https://arxiv.org/html/2610.11781v1)修订procedure并回放历史；§3.4于episode开头选技能。仅“修改步骤”不构成差异。
- [SkillApt §3.2–3.6/附录B](https://arxiv.org/html/2609.26863v1)已有配对效用与LOAD/ABSTAIN；修改后保留world续做的差异待验证。
**比较要求**：对齐状态、工具与成本，比较keep/drop、短历史、目标重申与冲突规则；适配不冒充复现。

**其他参照**：Sentry失败经验、EMG经验图、DGRR依赖失效、Memento笔记折叠，原文已核但成绩未复现；出处见[记录](results/ALFWORLD_CORRECTION_DATA.md#方法重叠与下一验证)。

**R属强基线**：[STeP](https://arxiv.org/html/2505.20023v1)教师纠正与partial masking；[Agent-R](https://arxiv.org/html/2501.11425v3)自搜索拼接。O/R不足以识别新意或反馈因果；见[成本](results/ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#recovery-literature)。

检索规则见[唯一入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md#联网搜索路由)。

**机制核查**：[TrustMem](https://arxiv.org/html/2606.25161v1)、[LW2S](https://arxiv.org/html/2609.30734v1)、[AttriMem](https://arxiv.org/html/2607.21106v3)、[MemCalib](https://arxiv.org/html/2609.24259v1)、[Anti-Persistence](https://arxiv.org/html/2610.27406v1)覆盖转移奖励、组件信用及成本；局部编辑/交互loss本身不新。[MERIT](https://arxiv.org/html/2608.05906v1)用oracle，比较须对齐权限。

[JointCore §2–3](https://arxiv.org/html/2610.23266v1)搜索保留原行为的充分子集；[MemHarness §3](https://arxiv.org/html/2607.28272v1)重构经验并训练；[Value of Memory](https://arxiv.org/html/2610.31303v1)覆盖恢复成本和交互。[Forgetting Without Restarting](https://arxiv.org/html/2609.04875v1)提示历史/cache残留，不能声称精确遗忘。

[MGPO §2](https://arxiv.org/html/2609.37930v1)比较新旧记忆对当前/未来目标的边际效用；[CERL §3](https://arxiv.org/html/2606.05201v1)以同前缀保留/擦除/skip训练持久状态充分性；[CEDAR §3](https://arxiv.org/html/2608.27797v1)以已实现公开谓词、环境反例和DFA组合/LOOKUP修订控制器，非新DFA算法。均已读原文、未复现成绩；“预测状态/反例修订/加取证”均不足以单独成立新法。

理论边界：[Value-directed POMDP Compression](https://cs.uwaterloo.ca/~ppoupart/publications/compression/compression.pdf)已有保持决策质量的状态压缩（§3–4已读）；[MDPs with a State Sensing Cost](https://proceedings.mlr.press/v300/kapoor26a.html)已有付费感知与盲行动联合优化（仅一手摘要）。取证条件化记忆仍需具体算法与迁移证据，不能称新原理。

**最直接新增对标（§3原文已读，未复现）**：[OSL-MR](https://arxiv.org/html/2606.10616v1)已建模保留/重获延迟/陈旧风险，实际用gold evidence membership加权BCE及预算解码；[Context Compression Cost](https://arxiv.org/html/2608.16370v1)已诊断固定Agent的保留/摘要/oracle恢复及自然重新取证，区分可回读与历史依赖信息。问题划分和成本思想已有先例。

**候选取舍**：四格交互可由普通联合Q表达；取证后经验修订须与同数据、动作和反馈的联合策略比较。[直接筛查](results/CODE_SOURCE_CORRECTIONS.md#direct-method)尚无可训练的新方法证据。

[Executed Counterfactual §2/D.5](https://arxiv.org/html/2611.05650v1)已提出固定现场的历史干预设计，并区分文件hash与实测恢复一致性；该设计未执行。单凭同前缀分支不能构成新意，仍须验证局部经验更新的实际收益。

**联合学习直接对标**：[AiO-Mem §3](https://arxiv.org/html/2610.21147v1#S3)联合search/add/skip/stop与过程奖励；[CAMG §5/C.1/D.3](https://arxiv.org/html/2609.34422v1)训练文件记忆并干预清空/打乱。保持策略动作与反馈相同，不能通过削弱联合基线证明增量。原文已核，成绩未复现。

[TokenTune §3](https://arxiv.org/html/2501.18824v1)已用位置选择性反传＋LoRA；反馈加权不新，须对照等长随机位置与普通训练并计成本。

**局部修订近邻（11-09原文核查，未复现）**：[StateGraph §4.2–4.5](https://arxiv.org/html/2611.02912v1#S4)从历史发现依赖，用反事实问题验证后局部撤回并检查行动前提；“有依赖图/局部撤回”已被覆盖。[When Evidence Changes §4/6.2](https://arxiv.org/html/2610.03902v1#S6.SS2)比较局部修复与当前来源重读，发现节点重算少不保证全流程tokens少。我们的待验差异只能落在实际续做后果监督、局部编辑结构和同信息学习效率上；不能先宣布新原理。

**11-10候选边界重审**：前一版“目标任务进行中、更新经验并保留进度”仍过宽。[Recuris](https://arxiv.org/html/2608.24876)已直接覆盖工作记忆进度、轨迹定位、局部经验修补、留出门控及失败后同题适配；其Terminal-Bench匹配4次尝试对照中，适配53/87、冻结记忆重试51/87（7胜/5负，McNemar p=0.774），说明不能把重试带来的总提升算成学习收益。[VCE-Skill](https://arxiv.org/abs/2608.16544)已覆盖从公共技能版本差异提炼更新经验并融合当前轨迹提案。[CounterMem](https://arxiv.org/html/2609.31874v1)、[OMCE](https://arxiv.org/html/2611.01747v1)、[MemScope](https://arxiv.org/html/2610.21170)、[Remember, Verify, or Ask?](https://arxiv.org/html/2608.19564v2)、[TAM](https://arxiv.org/html/2610.37482)、[SkillShift](https://arxiv.org/html/2610.33528)、[Skill-V](https://arxiv.org/html/2610.11781v1)及[多轮技能反馈演化研究](https://arxiv.org/html/2608.02636v1)已分别覆盖反事实适用性、在线路由/更新、证据驱动局部修补、复用时核验/暂存、进度记忆、变化时动作适配及技能修订。**因此“真实反馈＋经验局部修订＋保留进度”当前没有通过新颖性门，不再作为既定方法推进。**剩余可检查的窄边界是：真实软件/API版本变化发生在任务执行中时，如何用行为依赖而非仅版本标签，选择需要重新验证或局部更新的经验，同时保留不可回滚的任务进度。但这目前只是场景差异，尚不是方法。只有给出会在具体轨迹上区别于上述方法及版本检查/全量重测等简单规则的明确决策算法，并找到未曝光、可独立评分的真实迁移样本，才考虑小规模开发实验；否则淘汰该候选并调整研究问题，不再靠增加运行数补新颖性。

**样本边界核对**：Astropy #14995→#15082确是上游明确记录的回归链，但来源 Agent 的原始diff保留了 `operand is None` 分支，没有复现上游破坏性替换；因此不能把该链写成Agent经验造成回归。候选机制若要重开，必须找到Agent自身成功改动被后续独立行为证据反证的实例，并与直接读当前代码、普通重试和回归测试区分。

**反馈来源线索（Matplotlib 23562→27361，开发样本）**：来源Agent修复`Poly3DCollection.get_facecolors()`的pre-draw异常；其透明卡只含来源问题、结果及修改路径，生成skill则另含由Agent自写测试支撑的初始化约定。目标是`PathPatch3D.get_path()`在tight layout中的状态问题。旧四臂中仅透明卡臂出现`get_path()`无条件返回`_original_path`并触发冻结`test_arc_pathpatch[png]`回归（149/150）；无历史、来源历史、生成skill臂均为150/150。单目标单seed且载体信息不同，只能记作与透明卡相关的开发性有害使用信号，不能归因于某条经验规则。事后将同一回归信息交给Agent，普通反馈复跑和清单反馈均修复；普通反馈已足以成功，尚无新方法增益。原始卡与目标轨迹已在[Matplotlib隔离批次](results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)；候选问题仅是：如何使经验更新区分Agent自建、可能与自身补丁共因的测试证据与独立行为证据，并在普通“跑冻结回归＋反馈后重试”之上产生可测收益。该问题同时受[Agent生成测试价值研究](https://arxiv.org/abs/2602.07900)、[生成回归测试风险研究](https://arxiv.org/abs/2610.11835)和[反馈演化oracle审计](https://arxiv.org/abs/2608.19626)强约束，现阶段仍不是通过新颖性门的方法。

## 旧章节链接

按原始主题分组保留深链接；点击后只读对应历史片段。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[原记录](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
