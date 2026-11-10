# 代码来源：教师纠正与形成成本

> 状态: 维护中，Goal active | 更新: 2026-11-11 | 取代/被取代: 从ALFWORLD_CORRECTION_DATA按主题拆出代码来源；历史锚点保留。

<a id="fcdr-feedback-review"></a>
## FCDR首批：9条轨迹、9个反馈节点（11-11）

用户更新并恢复Goal后，只读核对SymPy两臂、Matplotlib三臂、Astropy隔离两臂和32K失败两臂；未重跑任务、测试、模型或训练。分类是D的开发判读，不是人工金标或因果效果。

| 节点 | 原始在线事件与后继动作 | 本批判断 |
| --- | --- | --- |
| S1/S2，SymPy来源卡raw行86/89 | `is_neq`未导入后补导入，`Q.neq`不存在后改`Q.ne` | 有正常恢复，最终1/3不表示反馈均未采纳 |
| M1/M2，Matplotlib完整卡行38、遮蔽卡行61 | 弃用警告后调整启动；自写errorbar测试遇RuntimeWarning后改测试处理 | 模型有响应。最终失败的`test__safe_first_finite_all_inf/all_nan`属事后评分，不能倒推在线送达 |
| A1/A2，Astropy隔离无历史行30/44 | 自测失败后改实现；mask断言失败后查实现、运行探针并改测试，最终独立合同通过 | 普通恢复有效。历史摘要臂少两轮本地测试失败；测试文件读取输出4,352字符对58,246字符，各因素作用未分离 |
| A3/A4/A5，Astropy32K完整行32/58、遮蔽行52 | 自测调用不存在的`NDDataRef.collapse`；另有生产代码None/unit异常。后继查相关实现，末7/8次操作无进一步编辑 | 可干预停滞节点；相关取证不等于未采纳反馈，尚未证实旧反馈越范围传播 |

**证据边界。** native harness仅留OpenCode事件流和采样元数据，没有完整模型HTTP消息/SSE。工具返回及具体后继修正支持在线使用观察，不等同逐请求载荷核验；新干预复用已有记录能力补足此项。静态回放不产生替代动作成绩。

**裁决与下一动作。** 节点定位闭合，不扩大尸检、不先训练。FCDR纯范围/版本标签不单独作方法。下一补齐`QUERY/PIVOT`：在测试/实现故障分歧处选公开探针，与普通恢复、失败清单/API核查及全量重测对照，定义不同决策后再释放小批预算。StateWise已涉及前提归因、范围绑定、重规划；VeriHarness要求区分修复信息与表示格式的作用，见[近邻](../IJCNN_RELATED_WORK_REFRESH_20261030.md)。

**私有材料。** `ROOT/fcdr_feedback_review_v1.json`含提取程序、行号、hash及判读，SHA `65c1b7f8f3c5f94213942b8546456655a7ff8e71bfc857c69541c67b94e0ac31`，只读重提取逐字节一致。ZIP共54项（manifest核53项）/527,267bytes，SHA `abcdcc8a2d81b36b50052ed3d21e326c440933ca33bed80b8063cb52c253f64c`，GB10与本机`D:/Documents/Loop_D_assets/agent_learning_20261106/fcdr_feedback_review_v1.zip`相同。它是节点材料，非完整环境/provider请求包；不入Git。新增科研请求/训练0，控制层阅读/搜索成本未并作0。

<a id="fcdr-recovery-pilot"></a>
### 最小恢复筛查合同（实现前冻结，DEV_ONLY）

**假设。** 在同一失败文件现场，按反馈类型、相关文件版本和未解决失败选择QUERY/PIVOT，能优于普通恢复及简单错误规则。先检验恢复组件，尚不主张方法新颖或跨任务学习。复用Astropy A4/A5：最后反馈之后无编辑，可用原失败work的Python改动重建现场；三臂均为新OpenCode会话、相同公开题面/经验/最后反馈和文件状态，不宣称恢复原完整对话。

**三臂。** 普通恢复提醒处理实际反馈；简单规则静态列出API核查、实现检查、修改后重测、无进展时用探针区分测试/实现故障；FCDR按未解决反馈、相关文件版本和近期诊断动态选择上述建议。三臂共享自测不是独立真值的说明，策略不加入隐藏测试、参考答案或手写修复代码；均允许模型自行取证与编辑。

**预算与判据。** 两个已曝光现场×三臂，固定35B＋同版OpenCode、seed7201/temperature0.2、64K/8192，每臂≤8 POST/300秒/6MB请求体，合计≤48实际POST；按固定seed随机运行顺序，不训练。记录完整实际模型请求及上游响应、恢复前后源码hash、动态干预和成本。评分复用原生3项原题、132项回归和公开issue probe，恢复原始测试后独立执行；自写测试不当终判。先离线检查状态重建、请求仅加策略消息而不改工具/历史、反馈分类与预算拒绝，再执行。持平或简单规则更优即停止本机制在本题追加；有信号再扩独立项目，两个现场不算两个独立任务。

**inquiry再判断（11-11，minimal-experiment）。** 已完整读外审1082行，复核StateWise §4.2–4.4、EFC预算匹配设计及SkillRevise接受门。三个待检验假设为可改变节点、超过普通恢复/规则的收益、跨项目全成本收益；本批只筛第二项。采纳反馈—决策干预主线，CCER降级；修正专家建议中的跳步：离线替代动作不等于真实收益，文件版本变化不证明旧事实错误，自写测试不独立但仍可作局部反馈。首轮先三臂，出现残差才扩完整基线，不把六组大矩阵作为启动前提。

**准备闭合。** GB10 Python3.12定向检查20 passed/exit0，含三策略接入真实派生harness的编译；均未访问模型。`ROOT/fcdr_recovery_pilot_v1/PLAN.json`已冻结6臂、随机顺序、共同现场和组件hash，SHA `44dfd2c73033daec257cdcf65c274855b9b70b9e9d684e594c140f48fe0ca584`。先运行一臂检查实际请求和干预送达，再续余臂；有接合故障即停、已开始但未闭合的运行不自动重启。当前原型是反馈清单与QUERY/PIVOT提示，不宣称已实现可靠前提归因或最优探针选择。

<a id="fcdr-recovery-result"></a>
### 六臂恢复结果（11-11，已执行）

三种策略在同一Astropy任务的两个曝光现场运行，均为35B＋OpenCode、64K/8192、seed7201、temperature0.2。前置原生结果A4为0/3、A5为2/3，回归均132/132。以下为恢复后的独立评分；两个现场不是两个独立任务。

| 现场 / 策略 | 实际POST | 原题通过 | 回归通过 | 恢复tokens |
| --- | ---: | ---: | ---: | ---: |
| A4 / 普通恢复 | 3 | 0/3 | 132/132 | 56,711 |
| A4 / 简单规则 | 3 | 0/3 | 132/132 | 48,364 |
| A4 / 动态反馈 | 7 | 0/3 | 132/132 | 145,354 |
| A5 / 普通恢复 | 6 | 3/3 | 132/132 | 99,200 |
| A5 / 简单规则 | 6 | 3/3 | 49/132 | 89,650 |
| A5 / 动态反馈 | 5 | 3/3 | 132/132 | 71,472 |

**实际改变判断的观察。** A5动态反馈与普通恢复均完成原合同，前者少1 POST、报告tokens少27.95%；轨迹少读一次测试文件，也未像普通臂追加整文件227项自测。三臂另在相同隔离环境恢复原始`test_nddata.py`做事后CPU复核，均219/219通过，不含actor追加的8项测试。它加强了这条局部成本信号，但没有增加独立任务或证明前提匹配机制。首次补充检查因只读目录的pytest缓存写入失败；原日志保留，按现有原生评分器统一加`no:cacheprovider`后复核，未改断言或新增warning豁免。

**失败尸检。** A5简单规则臂把双参数分支的`operation(self.data, operand.data)`改成只传`self.data`，本地8项自测过而83项既定回归失败；这是一条具体补丁的退化，不外推为规则方法普遍有害。A4三臂都在最后一次请求出现`finish_reason=length`、8192 completion主要为reasoning；动态臂虽编辑并复测，仍0/3。所有actor退出码均0，因此完成只按原生合同判定。动态控制器在首次读取任务后就触发PIVOT，它计算的是没有新执行诊断的请求轮数，不能据此声称识别了重复取证或已定位失效前提。

**成本与复核。** 本批30实际POST、510,751 provider总tokens＝477,614输入＋33,137输出；输入中361,431为cache-read、116,183为非缓存输入。30条provider usage与OpenCode逐臂完全对账，未知0，训练0；缓存不重复加入输入。A4/A5旧现场形成各24 POST、390,378/345,805 tokens，另有已存证来源形成成本；它们不是本批新费用，也不能在端到端收益里填0。上述27.95%是给定现场的恢复成本变化，不是来源形成至部署全流程节省；控制层阅读/搜索用量另列，未完整计量。

**裁决。** 保留A5正向开发信号；当前提示版本不扩样、不训练、不继续同题改文案。它在两现场合计比普通恢复多60,915 tokens，尚未识别独立方法。下一门是把“被反馈否定的前提→具体可执行探针→后继行动”写成可检验规则，对照普通恢复和直接重跑公开原例；范围标签、停滞提醒或假设验证本身须面对StateWise、ErrorProbe等近邻。先解决这项机制差异，再冻结不同项目的新批次；不重开全量尸检或增加框架层。

**复现材料。** 原型冻结于Git `36e9ea3a`。私有`ROOT/fcdr_recovery_pilot_v1/ANALYZE.py`核对实际请求、策略送达、初态文件、原生节点及SSE用量，输出SHA `a03506b7be0223fad5b1f839b80eee0b5cca0d93f5cc5c5c15b93851e32bed37`；补充复核RESULT SHA `ad7879cf8b8f9385c0e8e9287a21be7adbd9cba9e1f25836873e8ac6742cd112`。私有包`ROOT/fcdr_recovery_pilot_v1.zip`有284成员/283个manifest载荷、2,128,332bytes，SHA `54afc3eb00da4c22e127fee13102bd3d77123b5cefa8034ecac1aec4d93dcde6`；本机`D:/Documents/Loop_D_assets/agent_learning_20261106/fcdr_recovery_pilot_v1.zip`逐项hash相同。包含原始请求/SSE、评分、改变文件及复核代码，不含完整依赖镜像，不入Git。本机解包后以`python -X utf8 ANALYZE.py`独立重放，同得6臂/30 POST/510,751 tokens，零模型调用。

<a id="probe-choice-screen"></a>
### 取证是否改变修复选择（11-11，合同与停止结果）

inquiry模式为first-principles。本轮核到更直接近邻：CBC §2.3–4已将失败编译为适用条件、可执行探针和计划后果；Bayesian Control §3–5、A.6以候选正确性后验及观测成本选择检查、修复或停止。两者原文已读相应方法，未复现。后续不能仅把前置探针或成本控制改名为新方法；候选应明确比较的是不同修复前提对应的行动选择。

**首先验证一个前提。** Matplotlib24818公开题面只要求全NaN的`ax.errorbar`不崩溃，而既定2项评分要求辅助函数的NaN/Inf返回值。先在已有完整卡/无经验/遮蔽卡三个最终候选上执行原始公开复现，另记canvas draw及有限值控制；再对无经验候选仅回退`cbook.py`作对照。复用原harness的镜像、Python/依赖挂载与Agg环境，工作区只读、各CPU运行≤60秒，合计4容器、模型/训练0，不读参考修复、不改旧评分。若公开复现已通过，不继续该目标的同类恢复；区分公开行为与更强验收合同后再选择有实际行动分歧的任务。若仍失败，才以相应真实输出设计对照。这个检查不先裁定原评分无效。

**已执行的纠正。** 三个最终候选的原始全NaN复现、部分NaN和有限值控制均可调用并完成canvas draw；全NaN各保留2条RuntimeWarning。无经验候选仅恢复原始`cbook.py`后，原始全NaN复现重新出现StopIteration，另两控制通过。首个回退控制在观测结束后的辅助函数检查抛错而丢失JSON，原日志保留；移除该收尾检查后额外1个CPU容器取得完整控制记录，合计5容器、模型/训练0。结论限当前Python3.10/Agg/3.6.3依赖投影，旧0/2、61/61不变：应将“未修复目标”的笼统说法改为“公开崩溃已解除，辅助函数的较强验收尚未通过”，不裁定整个benchmark无效。

**下一候选的可执行定义（模型前冻结）。** 复用`decision_probes.py`，把模型提出的可能原因分组到具体修复动作。对候选探针比较观测前后的最小行动分类风险`1-max_a P(a)`，按其预计降低量/名义成本选择；所有原因都指向同一动作时不购买诊断。与区分原因的entropy目标、固定公开复现和普通恢复比较。此决策论量本身不是新理论，可能的增量只在实际反馈下修复动作的表示、取证选择与执行收益；模型预测矩阵不是真实反事实结果。

先在SymPy21203已有来源卡最终现场形成一次计划：同一35B＋OpenCode，64K/8192、temperature0.2、seed7201，单规划≤6 POST/300秒；显式请求关闭thinking并从SSE核实，禁止改源代码、看隐藏测试或独立评分。计划只用公开题面、已有经验及注明历史范围的最后工具输出，最多4行动/6假设/4探针，Python探针在原隔离面只读执行，名义成本统一1。无有效计划或没有可区分的行动时停止此选择器；若可用，再比较普通恢复、共享计划无预取证、固定公开探针、行动价值、entropy选择，等价输入合并，不把它们算独立样本。每修复臂≤8 POST/300秒，整批上限46实际POST，形成与探针成本另计；原生3项原题及124回归独立评分，不先训练，也不把此单曝光任务当跨项目确认。

**形成结果：停止修复矩阵。** 实际4 POST、29,559输入＋1,462输出＝31,021 tokens；4条provider usage与回执对齐。全部请求显式关闭thinking，SSE推理内容0字符，3次tool_calls＋1次stop，无length；1,428个SymPy Python文件逐项未变。模型列4个原因，却都指向同一宽泛修复A，行动价值选择器跳过，entropy会选P1；这只是模型预测表上的计算，不是实际收益。3项只读CPU执行：P1把集合传给JSON导致异常；P2/P3虽执行成功，输出常量标签均不在对应预测标签中。因此0/3形成可用于更新的观测合同，未执行修复臂、未训练，不追加同题prompt。该阶段不允许读源码，实际经验文件为0字节，输入含公开题面与注明历史范围的观察；不能据此认定模型不能修复、FCDR整体无效或选择器优于entropy。公开题面还把二元谓词推理列为未来工作，历史`None`不能直接标失败。

**本次inquiry裁决。** 专家主张的“反馈→具体决策→真实收益”作为主问题保留；固定方法名、48小时重做尸检和六组全矩阵不作为必经步骤。已完成节点与提醒原型筛查，当前缺口是执行证据支持的修复分歧。下一仅用既有真实补丁与原生结果定位一个可判别场景，再比较普通恢复/简单取证；没有分歧或独立机制差异就换假设或定向请专家。反馈来源/版本绑定用于控制混淆，不单独算算法贡献。

**存证。** Matplotlib公开复核共5次CPU容器（含首次未完整输出的对照），零模型；`ROOT/fcdr_probe_choice_v1.zip`双端SHA `d6e67c7e990d7bcf554a7763f5005cf87bdd9c757420a6e74076c7fc406f040e`。SymPy形成与3项CPU探针保存在`ROOT/fcdr_decision_probes_v1.zip`，SHA `db175029665b56bd9643ea8b95a31caefba249581544870d2d4fe713ebf6cb06`。本机均在`D:/Documents/Loop_D_assets/agent_learning_20261106/`；包含冻结代码/输入、请求/SSE及结果manifest，完整环境依赖仍引用旧私有资产，不入Git。本次复核与归位未新增模型调用或任务重跑。

**Django既有迁移现场尸检（11-10，不重跑）**：GB10私有根`research_evidence/agent_learning_20261030/swe_contextbench_django_agent_20261104/`已有7次运行，261 POST、3,703,097已报tokens；14个receipt/raw文件的SHA清单为`8756638191e6d7eca7ec861f06f67d9a4de717f7fe5e609079477e6a85075d69`。来源`django-16910`无经验运行的目标测试2项失败、35项回归通过且无源码修改；但[`build_experience()`](../run_swe_contextbench_django_20261104.py#L305)只检查评分字段存在，没有要求来源目标测试通过，故后续经验不是“已验证成功经验”。目标`django-35356`的base本身以`FieldError`失败、17项回归通过。无经验/候选重试臂修改源码后仍失败，部分另有2项回归错误；source-history与generated-skill臂未改生产源码、保留base错误和17项回归通过，后者完整读完21/21行，前者仅读73/82行。7臂目标原题均未通过。它提示“错误类型、源码改动和回归退化”应与目标成功一起看；但来源失败、单目标单seed且条件输入不同，不能证明记忆保护或迁移方法有效。本配对停止，不再追加。

<a id="branch-scope-result"></a>
### 修复分歧与公开强基线（11-11，零模型实测）

**待判断前提。** A5三个补丁都通过219项原始`test_nddata.py`，简单规则补丁却在既定132项回归中失败83项。此前把219项当额外加强支持，解读过宽。本批冻结已有初始现场及三个补丁，对`_arithmetic_data`作执行跟踪，再跑公开无单位collapse与双参数add；随后恢复原始公开`test_ndarithmetic.py`，验证廉价整文件回归是否已足够。不改旧源码/评分，不增加Agent请求，不把这些已曝光候选算新任务。

| 冻结版本 | 原始NDData测试 | 其中算术函数调用 | 公开collapse / add | 原始算术文件回归 |
| --- | --- | ---: | --- | --- |
| A5初始现场 | 219/219 | 0 | 失败 / 通过 | 180/180 |
| 简单规则补丁 | 219/219 | 0 | 通过 / 失败 | 49/180 |
| 普通恢复补丁 | 219/219 | 0 | 通过 / 通过 | 本批未重跑，旧既定132/132 |
| 动态反馈补丁 | 219/219 | 0 | 通过 / 通过 | 180/180 |

两个公开操作均实际触发跟踪函数各一次，排除跟踪器完全失效。简单补丁在双参数分支把`operation(self.data, operand.data)`改为只传`self.data`；公开add得到TypeError。公开算术测试文件在三臂actor工作树的hash均与原始文件相同，运行不依赖隐藏评分或模型生成新测试；初始/动态补丁180通过各约0.28秒pytest时间，简单补丁131失败/49通过约3.27秒，容器墙时约1–4秒。跟踪运行额外开销不当成方法成本收益。

**裁决。** 存在真实行为分歧，但本面板已有廉价强简单基线。219项不调用编辑函数，不能加强本次算术修复结论；原3项原题/132回归成绩不变。停止在此面板扩复杂探针选择器，不把“更多测试/覆盖绑定”包装成方法。新核[Teaching Agents to Code Reliably](https://arxiv.org/html/2610.03984)§2.1–2.3已明确补丁/回退执行、改动行覆盖和区分候选；[CodeT](https://arxiv.org/abs/2207.10397)原始摘要已涉及多程序×测试的执行一致性。尚未复现两法。

**成本与存证。** 本批7个CPU容器，模型/训练0；控制层阅读与搜索另计。`ROOT/fcdr_branch_scope_v1/RESULT.json` SHA `2dffe06fe5b4e963fa0096d056d854922931c4d5d1b701197eab95eb6815afd8`；公开基线`BASELINE_RESULT.json` SHA `727e88c6d95761e02319510f482ffea4ab6ba2471d55cdf75fa95b919088c666`。私有ZIP有20成员，SHA `fe65b8e37930133950981e74ce7d00d0eca08c148c59d5397847a3829bc9b580`，镜像到本机`D:/Documents/Loop_D_assets/agent_learning_20261106/`；仅含脚本、合同、输出和hash，原工作树/依赖引用旧资产。下一是针对上述最近邻定向判别尚未覆盖的决策变量，不追加同题模型重试。

<a id="current"></a>
## 已验证来源资产

<a id="feedback-support-candidate"></a>
### 当前机制候选与公开来源筛选（11-11，未运行新Agent）

**原文支持的切口。** 补读[Skill-V](https://arxiv.org/html/2610.11781v1)附录A的Historical dependency和B.5–B.7：作者明确指出规则变化后，历史轨迹的行为标签可能过时。其回放门比较rubric预测与环境结果，已允许修订适用条件；同一观察池中的有效支持可以变化。因此不能假设原法一定阻止正确更新，或把按上下文分组回放省略出基线。[EvoMem](https://arxiv.org/html/2606.13681)§4.2–4.3已保存并检索非增量版本更新。两法未复现。

**候选操作，尚非已验证方法。** 输入旧反馈及其决策前提、当前实际反馈和可执行见证。先依据当前执行把旧反馈分为仍适用、已冲突、未知，并在提出经验修订前固定验证支持集；只更新已验证冲突的范围，保留其他范围的旧经验，未知时取证或回到普通恢复。旧事件仍保留其原环境下的结果，不反向改标签，也不能根据哪个候选表现好再挑验证记录。拟检验的是“验证依据怎样随变化更新”；其与Skill-V条件化回放、StateWise范围核验及EvoMem的独立差异仍须定向审阅。

**最小比较与反证。** 先找到真实成功来源及一个发生规则冲突、一个未变的现场，在同一Actor、OpenCode、信息/查询权限和总预算下比较普通修订、按当前上下文/版本筛选回放、候选支持更新；全量当前重验和时间衰减为后续强对照。若简单版本规则或原法适配同效更省，就停止本候选；若只有验证指标改善而原生任务及总成本不改善，也不算方法收益。当前还没有满足此实验的冻结来源与变更现场，不启动训练或大矩阵。

**本批实际取得的素材。** 官方代码元数据固定`Aiden0526/EvoArena@17983e68eeaa26e78575566836aa679ea6b6bf80`；其Terminal子目录README指向`wufeiwu/Terminal-Bench-Evo`，数据revision `18ecf86f67ad9208eccaf195c63ceb42f4095dc0`。在读取需求前按Python/数据工作流适配选择`cancel-async-tasks`与`multi-source-data-merger`两链，随后只读各base＋EVO1–4的10份公开instruction及4份task元数据，没有读测试或solution。前者显式增加失败取消约束、工具限制及模块路径变化；后者显式变更输入/输出路径、promote步骤和JSON→YAML，合并优先级保持。可作为版本规则的开发对照，不能把这些显式变化当作隐式反馈失效，更未获得新任务成功。数据卡为`license: other`，最终下游许可未核；本批不安装或执行上游代码、不转分发数据。

**存证与下一动作。** 私有`evoarena_contract_discovery_v1_posix.zip`共20成员/24,706bytes，双端SHA `689ebee8cfd4cfd3d4c19635887bc41b8bb3fdc4f0dc2f3c6cb67ef06e348f68`；本机`D:/Documents/Loop_D_assets/agent_learning_20261106/`、GB10 `ROOT/`。Discovery SHA `df6f1a22b0c00520d51a3a68b1d8c0b95cf05a32a107e35bac4aca313b1b90a5`。首包manifest的Windows路径分隔符与ZIP成员不符，失败包保留；最终包改POSIX键并逐项核验。模型、训练、环境安装及原生任务运行均0，控制层阅读/搜索另计。下一先请专家定向判别上述独立机制，并寻找真实、可执行的规则冲突；不因得到新基准名字就建adapter。

**2026-11-10 来源元数据筛查**：对Lite中Django不同PR的关系按`sha256(source_id|target_id)`排序，只读取任务ID、base与GitHub PR merge/compare元数据，不读目标题面或补丁。前七对的source PR merge相对目标base均为`behind`：14017→32450（3提交）、14608→11776（11,880）、16910→21204（734）、15252→32012（1,554）、13220→29838（2,400）、12284→30931（294）、14787→32260（710）。它们未通过当前“源PR合并为目标base祖先”的严格时间门，不用于声称源修复已存在的向前迁移；这不排除源问题在合并前已可被Agent解决。仅7对非全体统计，无模型调用；下一步继续查不同来源，不读取留出目标答案。

**可继续检查的自然任务链**：Matplotlib源PR [25332](https://github.com/matplotlib/matplotlib/pull/25332)已合并，原开发目标[25352](https://github.com/matplotlib/matplotlib/pull/25352)的base在其后；25352合并亦为候选`matplotlib__matplotlib-22482`的base祖先（compare ahead 4033、behind 0；目标对应PR [28430](https://github.com/matplotlib/matplotlib/pull/28430)）。初筛只查元数据，后续D已读[22482公开题面](https://github.com/matplotlib/matplotlib/issues/22482)，它关于含交互滑块的Figure序列化；25332来源则关于对齐标签后的weakref序列化。二者有自然任务联系，但报错并不相同，不能预设旧修复适用。目标原issue早于源PR，目标base在源修复之后，不能说问题发生时间也在之后。该目标仅用于开发，尚未核原生执行或目标金补丁，不是留出确认。25332是参考辅助源，25352的27B OpenCode三臂均搜索循环且无编辑，其失败反馈本身不能证明源经验失效。元数据回执SHA `d2c3c79539fedd04b3abee7f96a815bba1377f2a7811ecdc593fbfdd22afb78c`，位于下述Sphinx尸检私有目录。

**22482开发评分准备（模型调用前）**：按基准固定base `d347c3227f8de8a99aa327390fee619310452a96`、Matplotlib 3.9，复用现有ARM/Python3.10依赖和Agg容器；数据卡有1个原题节点、194个原有回归节点。先只做一次base/参考的隔离执行并报告节点缺失、跳过或环境不适配；参考与测试补丁只在评分侧，源经验明确标记参考辅助。原公开问题涉及Qt，Agg评分通过不能直接宣称复现Qt环境。资格有阻断就不启动目标Agent；通过后再比较无经验、完整来源和简单规则，具体运行前单独冻结。目标已被D阅读，不作盲确认。

**22482评分未通过准入**：base及参考均为目标1/1、回归193/194，目标节点不区分两者；共同回归失败为`test_lazy_auto_backend_selection`。另在隔离容器请求TkAgg并检查真实实例，两臂实际均回落`FigureCanvasAgg`，均可序列化按钮；原题Qt后端未复现。GB10宿主与容器均未发现`Xvfb`，未连接现有桌面或安装软件。因评分无法区分修复，暂停此目标Agent比较；这不是旧经验有效或无效的证据。CPU、零模型/训练，原始资格receipt SHA `a94b11cb8b1c48c1246a1b99262e5742458a44823822ccbc7c85cc2e0e24342b`，后端探针SHA `85a100eea237f708eabc1eaa51dd8edc5b72f6e60b225e960bffa5b1d3901adc`，均在GB10私有`matplotlib_22482_development_v1/`。下一来源优先选能在现有环境中区分原版与修复的任务。

**候选SymPy第二开发目标（生成前）**：数据集关系表把`21055`与`21203`关联；后者公开题面涉及等式查询接受假设，D已读题面开头，不作留出确认。目标base `7ba571cd2151d4975036f61d7745a260933fbbe3`相对源修复merge `4b03990bb9df237c110b8120ffe5ed94c610348c`为ahead 176/behind 0；只说明源码版本先后。复用既有Python3.8及源证据，先零模型检查目标base与参考的3个关键、124个回归节点，参考/test patch只在评分侧。来源21055是教师辅助并非自主Agent解决，资格通过后才决定是否做同预算模型＋OpenCode比较。

**21203原生评分可区分**：base关键0/3、参考3/3，双方124/124回归通过，节点均完整、无错误或缺失；四个容器均为CPU执行，模型/训练0。评分receipt SHA `c0a5a3046979c300149d36be9c8b7ccc79fbf31dab984b3f7c7c906c95c17d42`，见私有`ROOT/sympy_21203_development_v1/`。该结果证明本次评分合同可区分候选，不是Agent方法成绩；真实运行须只挂载`clean_base`、公开题面及选定来源，不暴露`scorer_only`。下一步优先运行无经验与已验证来源证据的OpenCode开发对照，来源和总成本分列。

**21203两臂执行前冻结**：相同目标base、Qwen3.8-27B FP8＋OpenCode原生工具、seed17、32K/8192、temperature 0.2，串行比较无历史与完整`21055`教师辅助修复记录；每臂上限32 POST/900秒/64MiB，停用自动压缩。两臂公共输入及源码一致，来源臂多2,863字节的真实源题、教师生成补丁及历史核验说明，故是有无来源信息筛查，不是等信息的格式因果对比。目标测试补丁和参考仅评分侧，CPU核查实际挂载与输入；后者不得提供给actor。私有`actor_pair_v1/PLAN.json` SHA `52e7317ff5f41efe190ae99323129d23a2462f653caf80dbb3051748ee8f7c9c`；无经验/source两臂manifest SHA分别`15a9a12b777eb488458a6fd512f15d2457bccd1c53af591e6048e0d37d3909c6` / `b494379df42c5ebc870b22e84933153a4ab91e63f11f71b8ca55b0439299d948`。训练0；形成成本及未完成结果另计，此题不作为盲确认。

**首个无经验臂运行故障**：实际14 POST，累计已知181,569 tokens＋第14次usage未知；13次工具操作为9次bash和4次read，没有编辑，目标0/3、回归124/124。服务返回`ContextOverflowError`：当前Qwen3.8服务实际上限32,768，而旧合同为输出预留8,192，输入达到至少24,577即被拒。末次请求已达约63KB，最大单次工具输出约12KB；不是方法优劣结果。receipt SHA `1af42e25d27a96f4e427645b490762bc4b1bd11bb399e22ad94f383a77a3f4a1`。已停发同配置来源臂；下一批需两臂共同调整上下文管理与输出上限，保留这次失败与费用，不能把旧臂与新臂混作配对。

**21203两臂新合同（生成前）**：使用同一既有32K服务，不重启共享模型；两臂共同将输出帽设4,096、启用OpenCode自动压缩，并给相同的定位后分段读取提示。压缩请求若不带工具，转发时省略空tools；其余请求仍限原生工具白名单。模型、目标、seed、来源差异、32 POST/900秒及评分合同不变；两臂均重新开始，旧臂不合并比较。配置/空tools/转发输出帽已做零模型检查，尚须核实实际wire和压缩行为。私有`actor_pair_v2_compaction/PLAN.json` SHA `65327dbabdc7808835c39d9648a3d1b218807bca0c94a40c7794290ee9a879d3`；两臂manifest SHA `c2aeb02d39c2c94af8eb6238799e9793b9d8b7a73d751a324e9874a54db50e66` / `e5a2a86f87e6333f19c31dd137c4044167753f53750fc7116bd4280018f39b56`。

**接入错误及修复**：上述v2转发元数据使用了运行器保留字段`kind`，写事件时抛`TypeError`；7次本地尝试均未转发模型、0 tokens。发现后只终止本次自有容器，清理成功；receipt SHA `cbe98c2912a04a9d82e0e0de8f9964b8a1a28d8a540c2c417a4e992f5ebad722`。已在新快照改名，并分别用无工具和原生工具请求实际调用既有`Relay.event`、检查4096输出帽；这次是运行器接入错误，不是模型/方法结果。v2现场保留，不覆盖。

修正后两臂仍按上述同一合同重新准备，CPU通过。私有`actor_pair_v3_compaction/PLAN.json` SHA `08a7a310252e0569e7ad87255112a019631122e809c18fc151c303ef7cfa1ce2`；无经验/source manifest SHA `a9f8d50d25f24441d703e003e925acd733ae480577443465d59f6a6b30c42bbc` / `adbcab506a509d224601492ff12a1e8b2cc55c52c488ac19251db3bdadcb4ebb`。准备阶段0模型；执行后另记实际成本与结果。

**21203真实配对结果与尸检。** 两臂均用Qwen3.8-27B＋OpenCode实际运行，分别转发32 POST、第33次由本地硬帽拒绝；均无文件改动，原题0/3、回归124/124，评分节点完整。无经验臂输入521,343、输出2,821，共524,164 tokens；来源臂已知输入605,564、输出3,099，共608,663 tokens，另有第26请求usage未知。两臂累计已知1,132,827 tokens＋1次未知，形成成本另计，不能把有来源信息当作等信息机制对照。receipt SHA分别为`a23ef682f1b47966a189a95050d10baa439994db249627431c8c2d0e8e82d80b`与`42d53b41482752fadf46a137d5dc960dc4e42fb44f291cf9c4499753a2e62e04`。

**定位线索与限制。** 两臂均读到`AssumptionsWrapper`调用，来源臂还读过`wrapper.py`，但两臂没有调用编辑工具。无经验臂40次bash、5次read，末段出现重复搜索；来源臂20次bash、11次read。来源臂第26次遇32K上下文溢出，随后产生无工具压缩请求并继续至额度帽；无经验臂32次转发均成功。工具输出被看到不等于模型理解或采用，无法把未编辑归咎于单一原因，也不能以此判定经验修订机制无效。公开PR #21235的merge相对目标base为ahead 32/behind 0，相关变更已进入目标源码；完整PR内容是否能从隔离环境中直接复原未验证。本开发题停止追加同类提示；下一步应对现有成功/失败轨迹比较“读到定位线索→形成改动→执行反馈”的断点，并选未暴露任务验证。

**跨轨迹诊断线索。** 既有Astropy洁净source成功轨迹在前11次工具操作中读取任务和源码，第12次调用`edit`，随后复现、再次编辑并运行pytest；上述SymPy两臂则在读到相关源码后继续检索而未编辑。它们属于不同项目、模型和任务，不能解释成某一提示或经验操作导致成功；可用来制定下一批前测：记录首次候选修改、候选执行反馈与修订，而非只统计读取或最终成功。原始Astropy见[隔离对照](ASTROPY_PROFILE_CONTROLS_20261106.md)，不新增模型调用。

**私有证据包。** 本轮Sphinx、Matplotlib与SymPy的原始请求、执行和评分日志打包用于复核，排除源码工作树、评分侧参考与补丁；GB10及本机同一包SHA-256 `046dd543f595a3daf2fbd5db0e79aaab76f77bf80dce2576c0a4df2bc3ceed66`，737个文件的清单哈希已逐项核验。它含研究原始内容，仅供私有复核，不是可独立重建环境的发布包，也不得挂入Agent输入。

当前读[FCDR节点](#fcdr-feedback-review)、[NaN干预](#nan-transfer)及[SymPy迁移](#sympy-21203-result)；旧教师/控制器保留作来源。带“生成前/执行前”的历史段落不构成新授权。

SymPy21055取得一条**教师辅助、经执行验证的代码纠正**。教师仅接收原公开问题、D定位的源码和实际公开复现反馈；未接收未来目标或gold。它是一条来源素材，不是学习方法或迁移收益的确认。

| 条件 | 实际结果 |
| --- | --- |
| nonthinking，1 POST | 正常stop，输出完整diff；原严格应用因hunk行数错误失败。 |
| 同一diff，Git --recount | 只重算hunk行数，不改生成程序文本；独立原题1/1、回归13/13通过。新增模型0。 |
| thinking，1 POST | 600秒超时，原SSE含16,355字符推理、无答案通道或finish；不是完成的能力对比。 |

重计数控制是在看到第一臂应用失败后选定的后验工程适配；原始失败、超时与raw均保留。原题/回归通过只支持该释放测试合同，未扩充为任意输入正确性。当前不追加同题思考模式重试。

实际两臂消息逐字节相同，只有enable_thinking不同；模型27B、seed17、temperature0.2、32k上下文与8192总输出相同。原始请求/通道/补丁/执行日志可定位；没有把候选代码写回模型服务或业务系统。

## 成本与执行边界

本阶段共3个物理POST：早先空tools被HTTP400拒绝1次，以及两臂各1次。仅nonthinking有完整provider用量：输入3,583、输出456、合计4,039；HTTP400与超时两请求usage未知，**阶段总量未知**，cache未知。旧source的48POST/465,678已知tokens另记一次，不按子臂重复收取。研发Agent用量未完整计量。

nonthinking生成64.885秒，thinking600.001秒；后验重计数及两组CPU评分合计5.616秒、2个评分容器。训练/judge/付费科研API为0。owner已退出、两个owned评分容器已实查不存在、资源锁已释放；共享模型服务未改动，断连后服务内部生成状态未探测。

首次直接CLI预检受旧校验器的全局模块清单影响；固定为stdin/importlib调用后，旧17组件与两个二进制严格一致，未改校验函数或历史manifest。无工具请求只省略空工具字段；传输层兼容检查85项GB10测试通过，原ALF工具合同hash不变。

## 证据定位

GB10私有根为`ROOT/code_source_expansion_v1/SOURCE_ACTOR_PREPARED_V2_BASH_FIX/sympy__sympy-21055/teacher_patch_v2`：

- 协议SHA `77d9a417e23cef5d7a6e3d23c9766ac172057d1d11cf447e073fc5bd190e928c`；准备manifest SHA `44af743dab01224bcb7085de6848dc65c9bd60596a6b9391d724908e877e062d`。
- 主结果false receipt SHA `519023796011a76195055f7b32dbe655ca01f7dee71233d80bb096d202773bed`；true receipt SHA `3234ee92c3c191c7b1987a03fb1ce334c4fdba68b8bb18fd394eeae39f1ac0fa`。
- 后验`recount_evaluation_v1/D_RESULT_V1.json` SHA `abcfd72d6cdce158bcdcd0c6ac2819721cc9ca20263d37fd36943c21d2fe802c`；D闭合SHA `e2ea0e06cf6d77dc40ee87756be218a3d5dc600cda1eb273cacdd88dba6de9b4`。
- 私有封存包`teacher_correction_closed_v1_20261108.tar.gz`，1,922成员/7,233,655bytes，SHA `f43b840d9591257792ae7ac705bccc98c4bd69928964022d2bc68615ba5507f2`；原HTTP400包SHA `da0ae15fdc46963e262bd0b2a9fe2148674de8d309ede19d24b56600fe88ecfd`。模型权重及依赖不在包内。

[单轮入口](../contextbench_teacher_patch.py)；[主线短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。纠正使用与后续目标必须继续隔离，不能把该已曝光source改称新确认。

## 后续代码版本边界

注册候选为21055→9384：源修复merge `4b03990bb9df237c110b8120ffe5ed94c610348c`是目标base `70cd4ffd093ac224fc0226c1be58f9163e2c800a`的祖先（ahead290/behind0）。既有compare索引SHA `c22b36b869f5b3d72827e1a352b15fa62585e6dccfd56297c97e812b669c97e6`，`ANCESTRY_CHECK_V1.json` SHA `c8412bc8d709509fa9336520dd4d19572c65f67dea571f8fa5a4ce6700143603`；本次仅核元数据与汇总，没有重查原始compare。这支持代码版本向前，不证明原issue提出时间或无曝光。目标维持DEVELOPMENT_EVAL_ONLY，本轮未运行它。9384与21309两条题面hash不同，但索引绑定同一上游PR21309与同一base，不能作为两项独立PR修复计数。集合候选16988→16953仍仅有公开行为/时序复现，未获actor资格。

**可复用的目标资格。** 21055的`refine/arg`与9384的`refine/Piecewise`同属假设化简问题。9384历史CPU资格已完成：原题base 0/2、gold 2/2，双方回归各320/320。本轮只读复验GB10现存`QUALIFICATION_RUN_V2/sympy__sympy-9384/clean_base`的1,883文件及公开题面，全部与原冻结SHA一致，没有重跑模型或资格测试。该目录是源码快照，不是Git checkout；Python3.8 ARM环境仍沿历史记录，未整体复验。私有`sympy_refine_transfer_v1/ASSET_STATUS_V1.json` SHA `906a6a1f28603b544097fc1dba6c8013490c754d3be200602bc33b55748be0d2`。已复用现有runner准备双臂隔离输入，gold/testpatch/资格父目录不进入actor；来源只能称教师辅助修复记录，尚无目标迁移结果，不再先重复已通过的资格。

**准备器已复用。** [现有目标驱动](../run_contextbench_target.py)新增SymPy显式分支：none与source_repair_record，固定绑定原教师失败、后验重计数及执行验证。实际执行复用既有SymPy评分器，不把修复记录称为普通成功轨迹。本机45项合成控制通过（导入替身及Windows UID适配）；GB10与ALF准备器合计97项/246个子控制通过，无替身。两臂实际CPU准备及D独立verify已完成，各1,883文件，0模型/HTTP/容器；gold/资格父目录/评分补丁不进actor挂载。私有`ROOT/sympy_refine_transfer_v1/TARGET_PROTOCOL_V1.json` SHA `698785a471942627e60b6dbeb30deb56fa66f5d7d955b21ba3dedd8984765884`及6份元数据已双端镜像；源/目标路径与manifest查同目录。普通none/修复记录两臂暂缓运行，作为新反馈机制第二环境的复用资产；尚无目标模型成绩。

## 取证条件研究：已核资产与简单对照

11-09只读复核后，保留两项开发来源，不重跑已有资格：上方SymPy21055→9384，以及[Django12589→34176](DJANGO_AGGREGATION_PAIR_QUALIFICATION_20261106.md)。Django的65项与219项SQLite测试指向同一退出后的候选目录、同镜像/runtime/只读挂载，后者发现一项回归；缺少两个时点的完整树hash，不能认证逐字节不变。测试扩大不等于外部环境改变，旧65项通过仍是真实局部证据；两次约1.061/0.874秒，也不支持直接把宽测试称为更贵。

Django源/目标base分别为`895f28f9cbed817c00ab68770433170d83132d90`/`016bead6a23989adec5c7ee6948db7ce2fc5e89b`；目标base/gold 0/6→6/6、双方回归166/166。PG原题探针是独立PG15环境，不能混作上述SQLite范围比较。原receipt与宽检查分别以私有`django_teacher_source_20261106.tar.gz`中的`07533253…f7ac2b5`/`2e582442…50febcc`定位，完整SHA沿资格记录解析。

上述两个历史时点的字节同一性仍未知；下方新增同一固定快照的复算，不追认旧时点。两项目仍属已曝光开发来源，目标与隐藏检查继续隔离。

<a id="joint-development"></a>
## 联合记忆与取证：开发现场

**新固定快照复算。** 私有`ROOT/django_aggregation_agent_20261106/memory_evidence_development_v1/CURRENT_REPLAY_V1/RESULT_V1.json` SHA `e549bc3b3b05744f4570c907d10f027afa59d1145af7989d68ba295e291d2968`：候选前后树hash均`55f42bf3…42009f1`，65/65通过、219项中1失败/1跳过，分别0.837/0.938秒。公开源投影6,192文件，树hash`b1fb79d5…548dd3c`；私有16行测试overlay只进入评分端。纯公开快照单测亦已重现`3 != 2`，不是只凭带overlay的旧日志给反馈。

**成功门同时保留原修复。** D复用旧测试恢复及固定SQLite环境，独立评1项原题、65项回归和219项宽检查；不接PG。原base未过原题，当前修复过原题但未过宽检查，两者65项均过。两组CPU控制支持评分器能区分“撤销旧修复”与“修复新回归”；最终门须三组全通过、宽检查保持既定1跳过，仅代表此SQLite合同。

**学习原型。** [数据合同](../joint_memory_program.py)只接受有限query ID，不执行模型文本；未知/超预算结果不做训练负例，同输入成功比较成本采用Pareto规则，形成成本另记。标量偏好loss是普通参考式，尚非可训练实现或方法贡献。

**四次真实提案。** 私有`ROOT/joint_memory_reacquisition_pilot_v1/RUN_V1/RESULT.json` SHA `a5fe01084594a5671e53b62268084e637bfdda77fa063182335e2e671c5cd107`，27B/非thinking，两类prompt各seed17/29：4 POST，输入5,594/输出900/合计6,494，usage齐全、cache未知。严格whole-JSON为0/4；仅去完整外围栏后的诊断中，两个joint为数组、两个summary仍为string。原始失败保留，不重复生成补格式。writer已见两份公开代码读取片段，因此空query不证明回读无用。

D另删除一条生产函数记录并实际读取67bytes代码，完成算子检查，未形成偏好。独立C四提案复核SHA `f6cad8fd26d51a1e87686b153f4ebe362ba5753f5c3446c49dec9759dac5cfff`。

**普通恢复已闭合。** `D_READER_RESULT_V1.json` SHA `654703efe405a11e92964073164f8df4afa72db9f630fb179f8fd5c056009db1`：27B/seed17，无memory/无预读，12实际POST、13次relay尝试（末次封顶拒绝），输入107,482/输出1,062/总108,544tokens，cache未知，151.086秒。20次bash均只读/搜索，无生产编辑；独立原题1/1、回归65/65通过，宽219仍1失败/1跳过。此前摘要的21次计数经C按raw更正为20次。`GENERATION_FAULT`源于封顶403；只说明本次有界控制未完成，不能断言模型无修复能力。

**四格已闭合。** 同一D整理六record，交叉保留/删除生产函数记录×是否预读67bytes；所有臂仍可自主读公开repo。同27B/seed17、各12POST/300秒/16MiB，使用[复用入口](../joint_memory_program_runtime.py)。实际结果：

| 记忆 / 预读 | POST | provider tokens | bash | 新编辑 / 恢复 |
| --- | --- | --- | --- | --- |
| 保留 / 无 | 12 | 87,001 | 17 | 0 / 0 |
| 删除 / 有 | 12 | 89,661 | 19 | 0 / 0 |
| 删除 / 无 | 12 | 132,663 | 23 | 0 / 0 |
| 保留 / 有 | 12 | 91,097 | 20 | 0 / 0 |

四臂均在第13次relay尝试被本地帽拒绝，原题1+65保持通过、219仍同一回归。五臂共99条命令只读/搜索，未跑测试或编辑。独立参考正控1+65+219全过（既定skip1），SHA `ebe010b53b99af08f80b9f4495b2513404da738cf305d88f01917a12591426d6`；参考从未进入actor，非方法收益。

批结果SHA `d8e46a6d416b23f5eb4aff7db0a517ed2768f7d9a380b0f147ffd8a58ed7ad5c`；D闭合`D_CLOSEOUT_V1.json` SHA `b87a0e67d2bb72d6e5c65525001a143bb9d89307109973f2ebca5493cd6cecc5`。连同普通控制及四writer共64实际POST、输入508,854/输出6,606/总515,460tokens，usage齐全、64条cache未知；5次本地拒绝不算模型生成。形成历史不重置，训练0；token是用量，非等价新增计算。owner已退出，5个actor容器均实查不存在。

C独立核全部60条reader SSE和此前4writer，复核请求/采样/账本、99条命令及评分日志，无阻断；`C_FACTORIAL_CLOSEOUT_V1.json` SHA `4762fa8d1c8c2f5fa45f93ecb2223079684ea61ffb2034a7bbbf7213a8a65b4e`已私有双端镜像。1/65/219是相互重叠的评分集合，不相加为独立样本。四格闭合包`joint_memory_factorial_closed_v1.tar.gz`双端290成员＋索引校验，2,821,797bytes，SHA `019b201291086dff9a246ef8442795f0c898456505793056d557e5ffb776d14f`；后写C复核以独立sidecar hash绑定，不改旧包。

**裁决**：停止此非thinking/12POST单例分支，没有恢复偏好或训练方法效用证据。删除改变长度/位置、预读改变交付时机；单来源/单seed后验开发不作因果确认。下一扩独立source，复用已核真实Agent工件与依赖；Matplotlib25332源及25352目标已有失败，不能当未运行来源。旧目标的执行阻断或饱和不冒充新确认。

已闭合提案/普通控制与公开source快照的私有包`joint_memory_development_closed_control_v1.tar.gz`已双端逐项校验：19,474,055bytes，6,369证据成员＋索引，SHA `eadc70b242754aa2fd8b6e705e33b194304483d7c728b8952c53305502c35ece`；排除在途四格、权重与依赖。新数据合同/运行器GB10定向19项及21个子控制通过；不代表方法或泛化成立。

**旧正向工件补入索引。** `ROOT/django_aggregation_agent_20261106/attempts/teacher27_thinking_low_source_20261106`已有27B thinking-low修复：`source__none__seed7201.completed.json` SHA `ec4b3a362e0d50004d4ef492b3bfc1812ae01bca4451a7c9d6d0a784a5dd0449`。其`query.py`修复通过PG原题及SQLite原题1、回归65、宽检查219（既定skip1）；actor本身2400秒超时，54POST、53次完整usage共891,947tokens，末次usage未知，不能记成正常完成episode。原始请求确认nested thinking=true/low，seed7201；与上方非thinking/seed17/12POST并非同预算因果对照。退出后反馈不证明actor已见；历史包SHA `9987712bd65327a953520d8b798d06b7393eec88ad5cc899560653e16f24fdd1`已双端保留，不为重获该资产重跑。

<a id="source-expansion"></a>
**独立问题扩样。** 私有`ROOT/joint_memory_source_pool_v1`按兼容版本/回归成本事先选4道Matplotlib来源题，非随机代表样本。26020的6个截短参数名经原生collect的49个唯一节点补全；V3 base为1项原题失败/48回归通过，gold为49通过，receipt SHA `8eaf5d38dd2c2c58b0695ff316de85dae4e83cc11cf078e57984babca8354a30`。22711完整执行2原题＋91回归：base两原题失败，gold两原题通过；双方回归90通过/同1项PDF跳过。仅在新development合同事后声明该已观测skip，原严格覆盖仍为不完整，另报`LIMITED_RUNTIME_SCOPE`；receipt SHA `fe2d8915bf1618f6392910974ec9329d4587598ade604a187bddb3757fa4fa86`。23913另有真实回归失败，不放行；24149转义选择器未解，不猜测。旧pair/target/默认门不改。

<a id="nan-transfer"></a>
**24149解阻与新开发合同（11-10，生成前）。** 定位到检查器对所有反斜杠一律拒绝；新增仅Matplotlib参数区的显式允许选项，路径、函数名及默认严格模式不变，GB10定向43测试/125子控制通过。原生collect得到832节点：原768个公布选择器中766个唯一匹配，另两个截短选择器各匹配两项；取全部匹配的并集去重后仍为1原题＋767回归，不任择其一。原版原题失败、参考通过；双方回归均697通过/68跳过/2失败，参考没有新增失败。此环境并非原发布回归全通过，不能称完整benchmark资格。CPU控制reference receipt SHA `57219506d48c0d119a21fa4c19c9d7a06b8d39d3f75ce515ce9018f0d01e61d9`；驱动漏写patch凭证造成的哈希异常保留，随后以反向check核实参考已应用，再完成评分，未重复应用或生成。

该轮仅做一次开发来源采集：Qwen3.6-35B-A3B＋OpenCode原生工具、seed7201/temperature0.2、64K上下文/8192输出、24 POST/900秒；复用同一隔离依赖和原版源码。Agent仅收公开source题面与源码，不给参考、评分补丁或未来目标。生成前声明的开发成功线为正常退出、原题通过、保持原697项通过，其余既有失败/跳过及全成本单列；不是完整发布测试通过或新方法成绩。

**24149真实Agent来源成功。** 19实际POST、77.059秒、正常退出；原题1/1通过，回归697通过/68跳过/2原有失败，原通过项无退化。实际6次read、7次bash、3次grep、1次glob、2次edit：在`cbook._safe_first_finite`捕获`StopIteration`并返回`None`，另加3个断言约定全NaN/Inf返回`None`。自写测试只验证其自身约定，尚未证明fallback适合其他调用方。OpenCode逐请求计数：非缓存input 17,634、cache-read 184,931、output 3,257、合计205,822；缓存是累计输入202,565的子集，训练0。私有`native_24149_escape_v1/source_agent_v1/RESULT.json`绑定actor receipt SHA `c483ca2eba29ee09341b6df85985b5b42ba13c1e00cdea0b8b54cfecbc848112`、独立评分SHA `b6c4c20183227dc3ba9c61e9086881220f7f32a0a76f564fe7961bbc3a0958e9`及raw SHA `966c942161fdf17e4e2a47828a270662b7ff61a94d336942e2b7a6325fbe8ae6`，已核对。最终参数标签边界测试为GB10 43项/126子检查通过。

**24818干预合同与实际结果。** 选择自然关联的`24818`（errorbar全NaN）作为开发目标；`18294`与它共用PR25547及base，只算一个独立目标。经验卡只由24149真实轨迹、代码差异和来源反馈确定性提取，不是完整raw历史；移除臂仅删实现diff单元，保留诊断、来源与执行结果。三臂同35B/OpenCode、seed7201/temperature0.2、64K/8192、24实际POST/900秒，预定顺序完整卡→无经验→移除卡。PLAN SHA `88b412d4f09725b5c2b3f42c3b80051b7c617690b4015d1ae97ca082f2973893`；仅评分侧补齐25个遗漏所属类的公布测试名，原失败控制保留；原版2失败/61通过，参考63通过。

| 24818开发臂 | 实际转发POST | 原生原题 / 回归通过 | OpenCode总tokens | 正常退出 |
| --- | ---: | --- | ---: | --- |
| 完整来源卡 | 15 | 0/2；61/61 | 160,417 | 是 |
| 无经验 | 22 | 0/2；61/61 | 319,064 | 是 |
| 移除实现单元 | 24 | 0/2；61/61 | 371,316 | 否，下一次请求被本地封顶拒绝 |

**裁决与死因。** 三臂均编辑了代码，最终都采用`None`兜底；完整卡实际被读取，但无经验臂也独立选择同一语义。完整卡和无经验臂的公开errorbar复现不再抛`StopIteration`；原生两测试另外要求全NaN/Inf时返回相应数值哨兵，故仍失败。自写测试把`None`写成预期，不能补足这一合同。此题没有检出经验单元移除的成功率收益，也不能把共同错误归因为旧经验；停止同题提示变体及训练。卡片长短不同、单目标/单seed只支持开发排除，不作统计泛化。后续应先取得不同项目的可靠来源与可区分反馈，而非在此题训练保留/撤回选择器。

**计量及证据闭合。** 目标共61实际POST/850,797 tokens，非缓存input 50,752、cache-read 790,280、output 9,765；加来源共80 POST/1,056,619 tokens、训练0。移除臂原RESULT的`posts=25`混入1次本地拒绝，复算为24转发＋1拒绝，原RESULT保留，修正见`DEVELOPMENT_AUDIT.json` SHA `708709bd70f5ccbbf2c5f6812f0679bf8feb942ebf7eadd87a4f4fdabea006f5`。每个raw、actor/评分receipt及评分日志已核hash并复核机器结果。私有包`native_24149_escape_v1_closed.tar.gz`共142文件/1,788,785 bytes，SHA `fd823e0e6f0d88515df10b156260f16b4ebd5748cdf08285b229eb878b5e7165`，本机`D:/Documents/Loop_D_assets/agent_learning_20261106/`与GB10 `ROOT/joint_memory_source_pool_v1/`逐成员hash一致；无源码树、gold/test patch或权重。

<a id="sympy-native35"></a>
**跨项目自主来源补齐。** 复用SymPy21055既有源码、依赖投影及原版/参考评分控制，仅做一次35B＋OpenCode原生工具来源采集，24 POST/600秒、64K/8192、seed7201；不提供D定位、教师补丁或目标。旧27B Bash-only失败和新配置不是单因素对照，且仍是已曝光开发题。PLAN SHA `e2e42fc4123d08fdc11a0b1b2e7e6d65c976d6e997002ed4ca784e3af657fb11`，私有`ROOT/code_source_expansion_v1/source_collection_sequence_v1/sympy21055_native35_v1/`；依赖槽别名准备异常在生成前修正并保留，新增资格容器0。

实际14 POST/72.470秒正常退出，原题1/1、回归13/13通过；Agent添加`refine_arg`，用`ask(Q.positive/negative(...), assumptions)`处理符号条件，并在handler表注册，附带实际测试。OpenCode非缓存input 21,452、cache-read 194,109、output 2,922，共218,483 tokens，训练0。actor receipt SHA `f304fcd1e0ab3a38253b9b41352792f569aaa86b20e3ee14c61abf4ec009c0e2`、评分SHA `b5caea4b6404662c4beffe119b4b49fc46a9da1991f66047be8c0f0d821aabd7`、raw SHA `ff3c60233565f19fce7c4216a63893619d5e767ca76e785ab65ad74632517ca4`。这将旧教师辅助资产补成一条实际自主来源，不增加独立任务计数。

**21203强配置开发对照：历史冻结合同（已执行）。** 复用已合格目标环境，不重复原版/参考控制；源经验只由上述真实source题面、生成diff及1＋13评分结果提取。两臂均35B＋OpenCode原生工具、64K/8192、seed7201/temperature0.2、24 POST/900秒，固定顺序来源卡→无经验。PLAN SHA `9a68bede1c6a2f5538367777dee26a647ffd88157e2b25f918340c9c14f88fef`，私有`ROOT/sympy_21203_development_v1/native35_real_source_v1/`。它与旧27B/教师来源/32K队列不同，不能归因为单独模型效应或源经验改善；两臂内部才可作有无该来源信息的开发比较。

<a id="sympy-21203-result"></a>
**21203实际结果与记录补齐（11-11，只读核对，未重跑）。** 此前文档滞留“执行前”，GB10的两臂RESULT、raw及actor/独立评分回执已经存在；本次核实其绑定均相符。完整来源卡臂通过`test_query.py::test_relational`，其余两原题失败；无经验臂三原题均失败。两臂各124项回归均完整通过，均未解决目标。

| 开发臂 | 转发POST / 本地封顶拒绝 | 原题 / 回归通过 | 非缓存输入 / 缓存读取 / 输出tokens | 总tokens | actor墙时 |
| --- | --- | --- | --- | ---: | ---: |
| 完整来源卡 | 24 / 1 | 1/3；124/124 | 99,510 / 492,934 / 6,988 | 599,432 | 197.747秒 |
| 无经验 | 24 / 1 | 0/3；124/124 | 84,676 / 717,285 / 5,750 | 807,711 | 167.011秒 |

每臂25次尝试中仅24次转发模型，最后一次为`DENIED_POST_LIMIT`；两臂agent退出码均1，不能按正常完成计。上述是目标运行的OpenCode累计用量，缓存是输入子集。计入一次来源形成的218,483 tokens，来源卡路线为817,915、无经验为807,711；来源成本另可报告跨任务摊销，但本次尚未测得稳定复用收益。两目标臂合计48实际POST/1,407,143 tokens，训练0。单曝光目标、单seed、固定顺序及来源信息量不同，只支持局部测试结果观察，不能确认学习/局部修订机制或泛化收益。

来源/无经验两份RESULT SHA依次为`e184dece159482da0662e090b3a187965aaf95318e27b0baaca68e66ed7551ab` / `1ef6411b8d5d7754cedbf7abb2a64617bf1d0482fc67ee3559546ebc30771a57`；actor回执SHA为`999b2636ca3a598478190b94b4a17504bd5db9fcfc649209ccfa228397145adf` / `7949fb1ad790452d3a44fa9d3ff7e5e8d48b728029ae73e6f4654ff3f5789926`，评分回执SHA为`32048d801e7d45e4c21e07a739c669a10f218dda210b963ff8dc4bcf45dae234` / `431cfe15012987efd713ed25f711d587af5392a1157675f869d35304cbe7b681`。原始文件保持不变；本次同步的是摘要与代码，不公开私有raw。

**运行器版本边界。** 本次一并收录两端同内容的`contextbench_source_bash_v3`：仅补充空搜索的退出状态与换查询说明，未在本轮运行模型检验效果。上述35B多工具运行以各自冻结runner/manifest为准，不能把当前文件当成历史实际执行版本。

复用原生Python3.10 ARM依赖/扩展投影，并非各commit完整重新编译；没有安装依赖或新增warning豁免。4次archive下载、原生base/gold/collection/config共10个容器（含一次collector缓存写入失败），科研模型0。首个V3驱动缺父目录，在Docker启动前失败，保留原记录后另启；不计模型请求。新source支持显式27B thinking-low与首个生产编辑后的preforward现场：256MiB/30,000文件/累计30秒上限，失败为UNKNOWN，READY只保证字节稳定。实测安装版OpenCode接受关闭自动压缩，config receipt SHA `fadde246299e555c681ff2b7c0ba8b33f44fac33771a100113a23efef44f2924`。

GB10主树新鲜联合测试197项/120子控制通过；不是原生模型结果。两个实际CPU准备已完成，manifest SHA分别`e6bf98c27e7d4d554e93970051505aa7f9cec5c64dfa826f2141aa08782058c8`、`5fb412bf17aa0c144ddcdbf5e7914bed56b57ab359a33bcbed25291f9eb18518`。后续只做至多两道新source采集，各48POST/1200秒/64MiB，固定seed17、32k/8192、串行运行；先完成固定快照复核，不重跑旧失败面板。它们仍属同项目开发来源，不是跨项目确认或训练方法证据。

**采集收口。** C限域复核SHA `997725c93a9bda0e330acdd0d1fd52ffa6c1cb9fc039c7ce937b17d0b96afe8c`后真实运行：26020为26POST/407,000tokens，1200秒超时，第27次本地deadline拒绝未转发；22711按用户要求转向直接方法实验而中断，为16POST/115,834已知tokens，末次usage未知。合计42实际POST/522,834已知tokens＋1未知；不重置或隐藏该失败成本。26020首编辑checkpoint READY；22711捕获达到30秒门为UNKNOWN，不作为合格现场。

独立评分原26020中途及最终工件，各为1原题失败、48回归中38通过/10失败，无缺失；两份回执SHA `d0f5f0851d06e2da1530da9a05cda1be715f710b209a652f5e9ba0c522055d88`、`74d18eada8e3f70e64a15e4da8e9360b8740abf6666cb87af26539f9a00d168a`。完整源码hash前后不变；计数相同不自动推断失败节点完全相同。停止来源扩跑及该现场的提示追加。

<a id="direct-method"></a>
## 直接方法实验：控制器显式选择

**提示式DEFER已停止。** 私有`substitution_mechanism_v1`从26020同一READY现场运行KEEP/DROP/DEFER，各27B非thinking/seed17、6POST/180秒；共18POST/173,350tokens，usage齐全。三臂均无新编辑，原题仍失败、回归38/48通过。恢复client均调用0次，但三臂均用原生sed/grep回读同一源码，不能写成“没有重新取证”。它没有形成有效替代对比，不训练、不追加同例预算。结果SHA `b12aca6b406a9fe90985f057beb401e91c0e3b015d1680660506c8a799f66c0b`。

**显式动作已取得真实监督。** 改用已经验证有能力的SymPy21055单轮修复；三臂同公开题目/反馈/27B非thinking/seed17，控制器实际保留/省略/读取源码，再由固定模型生成diff。统一使用事先确定的`git apply --recount`，不改变生成代码。原生评分复用既有1项原题＋13项回归，测试与参考均不进入模型。

| 控制器动作 | 观测 | provider tokens |
| --- | --- | ---: |
| KEEP完整源码 | 补丁可应用，原题1/1及回归13/13通过 | 4,039 |
| DROP源码 | 幻觉代码上下文，补丁在共同recount下仍无法应用；未进测试 | 959 |
| QUERY结构＋refine_abs | 补丁可应用，但新增未定义处理器，测试在导入/收集时失败 | 1,492 |
| QUERY结构＋refine_sign | 只替换近似等长的实际处理器片段；补丁无法应用，未进测试 | 1,762 |

四次实际POST共8,252tokens，usage齐全/cache未知。KEEP请求体与旧正控逐字节相同；两种QUERY只读修复前真实源码，未虚构尚不存在的refine_arg。SIGN是在前3次结果已知后选定的一次来源开发，不是独立确认。绑定见私有`sympy_substitution_v1/INPUT_MANIFEST.json` SHA `564fc36b20a1b1e6b665984823d6a36b57432d0282daa69f505191dea6cec56c`及对应release/receipt/raw；模型token不等于新增计算，query读取时间另记。

**自然版本/任务变化四臂已闭合。** 21055的真实修复记忆迁往9384后，NONE、MEMORY、QUERY、BOTH均未改变预算末源码；独立原生评分均为原题0/2、回归320/320。NONE在180秒超时、usage未知；其余三臂正常生成但补丁无法应用，分别1,489/3,395/4,080tokens。QUERY/BOTH读取当前两文件61,820bytes，只呈现11,004bytes局部结构，不能称完整源码。4实际POST、8,964已知tokens＋其中1条未知；8个评分容器移除，owner均退出，服务端取消未核实。绑定私有`sympy_transfer_utility_v1/BUDGET_ENDSTATE_RESULT_V1.json` SHA `eae9f92744fd00e9f660b5212e004772f03b7932a9711a4c5f0e7d830bc47ef6`。这检验跨任务经验复用，不是同任务执行中保留进度的确认。

**最后一个上下文控制已闭合。** 无旧经验、完整提供当前refine.py与piecewise.py，模板15,720input tokens，连8192输出及512余量共24,424，小于32,768，未截短。新900秒/8MiB预算不改旧180秒合同，旧超时NONE不作公平新预算对照。实际1POST，15,720输入＋713输出＝16,433tokens，正常stop；补丁在refine.py:316无法应用，末状态仍原题0/2、回归320/320。receipt SHA `eafe6b73725e8c93c3195b6a16cb55a8497f474227fa42f3bb505aead8ad83f8`。两文件完整不等于相关上下文充分：D只读冻结gold的文件头，6个被改文件均在assumptions引擎及core/relational.py，不含上述两文件；现有两个F2P对应satask/relational，公开Piecewise行为的覆盖未充分证明。题面版本/哈希未见串换，但不能据此断言任务合同错误或模型无能力。停止9384提示/预算追加，不拿此面板训练或裁决学习方法。

**方法取舍。** 21055完整源码成功、局部片段失败，说明取证内容需覆盖实际执行需求；9384没有形成有效方法监督。独立质疑指出，四格交互项是已有回报的线性组合，普通联合Q可表达它；新增交互loss不作为独立方法。主攻取证后的局部经验重构：按实际反馈，仅改动影响后续行动的经验条件/内容，保留无关经验和已发生的外部进度。训练在同前缀续做候选中，优先成功，再取最低实际修订/执行成本；不是按文本相似或一条裁判判断失效。部署只执行所选查询和修订。与同数据/动作/反馈的普通联合策略、全部保留/重读和简单失效规则比较，检验结构化局部修订的学习增量；并非仅提出新loss。候选未训练、未证明新颖或有效；134 valid_unseen保留。

**闭合证据同步。** 此处source采集、提示式对照及两组SymPy筛查合计69条已确认POST、729,833已知tokens，其中2条usage未知；不是全项目成本。私有`evidence_packets_20261106/joint_memory_method_screen_v1.tar.gz`有760成员/14,393,685bytes，SHA `2d054a3885c2a589e40b8f0d9afb3039330aef7443ea9b5a44f3db3ec06b781d`，GB10与本机包hash相同并逐成员核验760/760。排除源码ZIP、整树副本、依赖与合成扫描fixture，原始完整树仍在GB10；包不是独立完整运行环境。成员索引SHA `f6e2b0d68765e60bc497c18834f4fa0e294fddf2c334a9dc3f8ed6af4c15d749`，仅私有保留。

## Sphinx 新来源：公开问题与实际运行（11-09）

数据集源ID `sphinx-doc__sphinx-8282` 对应上游[修复PR #8282](https://github.com/sphinx-doc/sphinx/pull/8282)及[问题 #7785](https://github.com/sphinx-doc/sphinx/issues/7785)；目标ID `sphinx-doc__sphinx-8127` 对应[问题 #8127](https://github.com/sphinx-doc/sphinx/issues/8127)及[修复PR #9104](https://github.com/sphinx-doc/sphinx/pull/9104)。ID不全是issue编号。

物化公开时序对 Sphinx8282→8127 的固定源码/问题，金补丁与评分补丁只在评分侧。8282实测base原题1失败/回归16通过，gold原题1通过/回归16通过；8127的39个原始节点先因 `::context::` 标签在当前pytest下4次退出4，保留失败。依据base/gold各自原生收集到的一致41节点，将32个标签去除非测试源码节点 `::context::`、7个保留，全部唯一映射；映射后base原题1失败/回归38通过，gold原题1通过/回归38通过，无跳过。原标签及初始失败未改；私有映射SHA `d2eaf7a8e0f372ab0c21c6b771a5bed8c89a04191fa8693870acfc0822b75e2c`，评分资产双端包SHA `7a1799f59204f2a3afc544eceb08cbfe21b6fb8ba4ac7f3e396866e0f5488f15`。

复用现有计量Relay及隔离工作区，27B/OpenCode对8282实际24 POST、208,774 tokens，下一请求预算拒绝后退出1；最终源码与base逐文件相同，独立评分原题1失败/回归16通过。24个bash步骤均为读取/搜索，后段四次重复相同grep及反馈，且至少后3次实际请求含先前相同输出；未编辑或运行pytest。评分是actor退出后的反馈，当时并未收到；不能归因重复为唯一原因。旧运行未改，actor receipt SHA `2957d2dbb228530402b3fa3500f9003494a7135493d78f4e203f9cb279b5c7d7`，评分SHA `174866a42ca393c9defc96a66694322d62ea4ba4a81b1b0e880c99677fac2257`。后续已依据对应公开问题及已读源码尝试有界纠正，结果见下；金补丁未作为actor输入。

**公开复现与一次教师提案。** 按对应公开问题 #7785 的最小Sphinx示例实际构建，`autodoc_typehints='none'` 时重载函数仍出现类型提示；未用评分补丁。27B仅接公开复现输出及原Agent已读源码，一次POST消耗5,177输入/298输出 tokens，生成候选diff；原样应用因围栏/损坏hunk失败。事后仅去完整外围栏并用 `git apply --recount`，不改生成代码，候选可应用到隔离副本；评分原题仍1失败、16回归通过（SHA `444e025f0fb6916a54635381332b53fe67132ff5de9fbfa1334149bce6b089f6`）。评分显示部分函数类型提示消失，但类 `Bar` 仍有类型提示；此为事后评测反馈，教师此前未见。该候选可作为部分修复素材，不能称任务成功；与24 POST的OpenCode运行接口不同，不作方法收益对比。原样应用失败、机械适配与评分均保留。

**一次真实反馈后的修订。** 另给同一27B一次请求，输入首次候选、公开源码与明确标注的评分文字“函数示例已隐藏类型提示、Bar仍显示类型提示；原题失败、16回归通过”，不提供测试源码、金补丁或未来8127信息。此时源任务评分已用于开发，源原题不再是独立确认。新增1 POST/2,686 tokens，原样Git应用成功；独立评分仍原题1失败、16回归通过，类的类型提示消失但出现重复 `Bar(x, y)` 签名；该重复是模型输出后的评分观察。评分SHA `f66999bcd8f659b2170d5c911fd303c92bbeb8504b043160389f596fae0264b6`。累计OpenCode及两次教师请求26 POST/216,935已知tokens，未知usage 0；不额外重试，继续保留原始失败与修改。

两次提案的初次回执顶层 `attempts: 0` 与实际不符；嵌套计量及原始ledger均记录1次实际POST，累计26次按物理调用计。完整证据包双端SHA `c059639cceecbf7fc0734ffd096a9434b918a9b671808b6768ecc064c92d09c5`；其中含评分侧私有测试/参考材料，不提供给actor。

**2026-11-10 失败链尸检与受控点检。** 原27B/OpenCode轨迹有24次bash、21个不同命令，无编辑或测试；同一搜索及其输出在第17、18、22、24次出现，不能称四次连续。另一个SymPy源的同一复现命令和输出连续33次；Matplotlib目标三臂分别连续34、38、37次，后者52次bash对应48次模型请求，不把工具动作当独立任务。这些轨迹支持识别搜索停滞，但提前停止只省下后续无进展，尚未证明能恢复任务。

Sphinx教师第二次修订虽隐藏了类的类型标注，却逐个追加隐藏后的签名：原本`int`与`str`两种重载都显示成`Bar(x, y)`。本轮在私有评分副本做**事后人工控制**，同一初始候选和冻结测试：原候选原题0/1、回归16/16；只对类去重仍0/1，首个差异转到`Math.sum`；对函数、类、方法三个输出分别保持顺序去重后为1/1、回归16/16。在教师修订候选上运行原公开问题复现时，函数`foo(x)`重复2次；三个位置同时去重后为1次。原工件未改；仅支持此有限测试范围内的失败解释，不能当Agent自主修复或方法泛化。零模型/零训练，CPU隔离测试；私有`ROOT/sphinx_8282_8127_development_v1/autopsy_signature_dependency_v1/RESULT.json` SHA `3264ab4d033e251563126d767206939ba848bf6df405c988e6a3eef4e087beb3`，公开复现结果SHA `9293dec5d98a10b1747e6b9eb908d540c28be29ccf0e073b1a5d67f874cd526d`，代码与日志同目录。该源题的评分已经暴露，仅用于开发；后续用OpenCode加本地模型在其他任务上验证“修复局部时保留并复核关联约束”，与普通反馈修订及简单规则等信息对照。

**下一项有界开发合同（新模型调用前）**：先在上述已曝光的Sphinx源题，用相同真实部分修订工件、公开题面及原例前后输出，比较OpenCode＋Qwen3.8-27B普通自由修订与“已满足/未满足约束”结构化提示。两臂均提供相同的人工追加开发要求：隐藏类型标注后避免重复签名，及先前改动涉及的三个类名；不提供本轮人工去重代码或评分测试。相同seed17、temperature 0.2、32K/8192、24 POST/600秒/64MiB，依次独立运行，记录全部实际请求、源码变化与成本，退出后由独立评分副本恢复测试。两臂的公共反馈相同，提示形式和长度不同；结论仅为单源开发信号。若两臂均未改善或简单臂已完成，不继续围绕此题调提示；若形成信号，还需不同任务、简单规则、相同反馈、形成成本和相关方法验证，不能据此宣称新方法。源代码现成候选来自两次教师提案，带人工开发信息，不能称独立自主来源或预注册确认。

两臂隔离输入与仅源题挂载的CPU检查已准备，尚无新模型请求。私有`constraint_feedback_pilot_v1/PLAN.json` SHA `b50fe694e3ff5b114b93afbc3a2bd97cfe8509c8940d3cc7e1667ed41f5a7bac`；`PREPARED.json` SHA `6ee57ce5328352063e9a91ab3b5b587670d6a81ed7001d391552e7a0fa508ffc`；输入、驱动、模型配置及两臂manifest均绑定于其中。原候选与clean base逐文件比较仅生产源码1文件不同，私有评分补丁不进入actor挂载。

**实际结果（本地Qwen3.8-27B＋OpenCode）**：普通与结构化两臂各24个真实POST、最后第25次由本地硬帽拒绝，均无源码或测试改动；actor exit1，恢复测试后原题0/1、回归16/16。普通臂26次bash动作、24种不同命令；结构化臂29次bash、29种不同命令，均为读取/搜索：结构化臂的不进展不能简单说成重复同一命令。两臂实际请求的模型、seed、温度、thinking关闭、输出帽及唯一bash工具已核；最后转发请求分别保留25/28条tool消息，不能归因为工具反馈全部丢失。普通臂输入258,971/输出1,555＝260,526 tokens、自动计时224.94秒；结构化臂277,095/1,660＝278,755、238.83秒；合计48 POST/539,281 tokens，provider未报告缓存细分。正文公共部分一致，结构化提示另长165字符，不能把差异当严格单因素因果。receipt SHA分别`104921a411290fdbfd9a008f52cd70b5234424eed90d5c192637af5269af94ff`、`f94165ceace4ff7c487c6a8205fd085f1ed73123d37575855d603b30c4eb02ff`；raw、实际请求与独立评分留同私有目录。按合同停止在此题调提示；这否定本例的提示收益，不否定一般经验修订。

**运行面待分离**：本批沿用家庭环境actor的`tools={"*":false,"bash":true}`；实际wire只给bash，而OpenCode系统示例仍提到read/edit。此前Astropy 35B运行开放原生read/edit，模型和工具面共同变化，不可直接比较模型能力。bash说明已明确允许读写，过去有一次简单写入canary；系统示例是否影响实际修复仍是待检验假设。下一步先在隔离低成本控制里检验Qwen3.8-27B使用原生编辑工具的能力，再在不同任务上进行同模型、同预算的工具面对照；不能把工具资格当论文方法结果。

**原生工具资格合同（调用前）**：复用原OpenCode、27B模型、隔离容器及请求计量，仅在新私有副本启用bash/read/edit/write/glob/grep；事先放入一个无关测试文件，请Agent实际用edit更改并用read检查。最多4 POST/180秒，不接源题、目标测试或外网；核对实际工具调用、文件与费用。通过只说明该小任务能使用工具，不证明会修复真实问题；失败保留实际错误，不重复加预算。准备好后另记输入/驱动hash及结果。

**原生工具资格结果**：Qwen3.8-27B＋OpenCode依次调用read、edit、read，唯一测试文件内容按要求改变，actor正常退出；实际工具列表为bash/edit/glob/grep/read/write。4 POST，输入21,752/输出168＝21,920 tokens，缓存细分未知，耗时28.34秒。私有`native_tool_canary_v1/run/receipt.json` SHA `9dfbde138edd09d8b70a81146005b6e76995d2821e8cfbe6e44b51388bc8e5f5`。合成资格不能证明真实任务收益。

**单一运行面对照（新调用前）**：为检验工具面是否解释上述不编辑，复用完全相同Sphinx部分候选、普通反馈正文、模型、seed17、温度、thinking关闭和24 POST/600秒/64MiB，只将Bash-only改为经上面资格验证的原生工具组；原有Bash-only自由修订臂为对照。两组工具数量、描述与上下文长度共同变化，按工具面整体比较，不归因单个edit工具；顺序和模型缓存亦未随机化。独立恢复同一源题测试，记录真实工具与成本；仅此一个已曝光开发源，不作为跨任务方法证据，也不继续追加提示变体。

新原生工具臂在生成前已CPU准备，代码树与先前普通反馈臂逐文件相同，完整包装prompt哈希相同。私有`native_sphinx_control_v1/PLAN.json` SHA `0386f131cc4ac3a7ab0657f634c31f2026e8a05658ee604c10c71833bedf9910`、`PREPARED.json` SHA `a9c9699e2190e1f8b699c4973fd1cd7ba507e00e04b55e3ab825973453f42381`，隔离挂载及评分器边界不变。

**原生工具对照结果。** 真实OpenCode轨迹共24次工具动作：bash 16、read 7、grep 1，未调用edit/write、未运行测试、源码无差异；独立事后评分仍为原题0/1、回归16/16。实际24 POST，第25次请求由本地额度控制拒绝，原始回执`GENERATION_FAULT`里的403不是上游认证错误。输入335,327、输出1,307、合计336,634 tokens，缓存细分未知，actor约192秒；receipt SHA `c117053712485a597e293c50b12a0254d06a32cf6a199d0576b144ab42cc207a`，raw SHA `bfe3e354d965ed3bb554a0a9586752173ea7c04cd8622b38f162ee4baf717923`。它确实使用了新增的读取工具，但没有开始编辑；与Bash-only普通反馈臂在此样本均未解决，不能据此认定工具面不重要。轨迹另显示`git`命令不可用，之后仍继续搜索；其影响未隔离。小工具资格加三个真实臂合计76 POST、897,835 tokens（输入893,145、输出4,690），非项目总账。此题停止追加；下一步优先对照真实成功轨迹并扩不同来源，而非再换同题提示。

## 先前准备与故障记录（迁入原文）

以下为原页面代码来源段的完整历史文本；其中“下一步”指当时状态，当前裁决只看上文。

<a id="source-tool-contract"></a>

**两源尸检已核。** `SOURCE_EPISODES_AUTOPSY_V1.json` SHA `52b958f5b39914c37017824e356ba9d56555a9b37907d7f30ad26311ebdb5727`：A共7次工具，D再核324绑定与96原SSE，合计input1,105,961/output5,586/total1,111,547tokens一致；96条cache未报告。每题48动作均只读/搜索、无编辑或测试，47轮后继工具反馈逐字带回，首user题面完整。确认实际只开放bash，而其说明禁止读写/编辑并指向未开放工具；这是能力/说明合同冲突，未证明它导致循环，亦不把两次失败当纯模型能力或反馈学习结论。先做source专用的最小合同修正和隔离写入验证，不改ALF/生产工具面，不直接重跑整批；source参考辅助纠正为低成本后续选项。

**工具说明修正与真实写入控制通过。** source专用v2只在转发前深拷贝替换唯一bash的说明，保留schema/messages及其他字段，非法工具拒绝；不改ALF或生产面。GB10 Python3.12聚焦57项通过，C限定静态PASS（SHA `1b1859f5b29ec70f16f7b52a247d817cb7c0a83371e4e1c831f07f642b1d9580`）。独立4POST/120秒/2MiB控制实际2POST、25.77秒、56,724wire bytes，1次原生bash真实写入并读回28bytes；D复核19绑定、原SSE和容器清理。receipt SHA `b8e914788bcaccf6aab7cc4dd639787993095b1648e1c28b9d41dd733d73ecaa`，D复核SHA `f0f8d6924735941ba8a2626a9196b55ce075a4ab55eb05af58cd27d8ac5afe96`。新增input5,341/output153/total5,494tokens，cache未知，训练0；旧96帽未重置、SWE题未重跑。只确认此次通路，不归因旧循环或认证修复能力。

该控制薄包21成员已双端核验，SHA `37516f9214d85400d8e082f0de583d44708e808c76396790a64acb7e3e834048`。新临时树仅5个受控修改与28缓存；五文件/patch及Git基线655afb2e已私有镜像，代码包SHA `aedaff8004b7e01bb9210294ac18b179023163aa18ebccf86ad9dad55dd7b1d8`，D核17组件的快照或Git重建后只移除这棵新测试树，7个历史树保留；收尾SHA `c11a983e20cc4edc8f1434b78bf5e294bdaac22aff1873b573ec6bf01f5fe6d2`。C9在本机/GB10各两harness定向分发，LF SHA `a496be2764834b097c9defd174d6eccd803573d146faa760dd19b8263c776ef3`，未声称全技能库重验。

**Bash-v2的已曝光来源开发重试已闭合，未形成成功来源。** 仅SymPy21055，新根`code_source_expansion_v1/SOURCE_ACTOR_PREPARED_V2_BASH_FIX/sympy__sympy-21055/attempt_v1`，manifest SHA `c1cbc8bcca58d6a5d32ac9322b777773bb4d8bc476676a508ebbf304bbaf71ba`；runner SHA `b2377f352cc824100c70bfb3340c0c9b78e3722d777b2fe113ed75b695c6b86d`。原题/wrapper与旧源一致，工具说明为既定v2；source-only输入未读未来9384题面/gold。D另给48POST/1200秒/64MiB，不重置旧96POST账；release SHA `85f43117f351875eef8106c9525e742a36a968c0c74767c23a91e38aea132076`。owner `1925392`/birth `1085721038`及3个owned actor/评分容器均已退出，锁已释放；未并发ALF模型、未重启共享服务。

实际48模型POST/49尝试，末次为封顶拒绝而未转发；输入461,600、输出4,078、总465,678tokens，usage未知0、cache未知。actor墙时714.981秒，两个独立评分容器合计4.527秒；训练/judge/付费科研API为0。源问题F2P0/1、PTP13/13完整覆盖，代码差异为空；模型运行真实公开复现后，重复同一命令33次。原receipt保留GENERATION_FAULT，403仅表示正常预算封顶；未修复判断由独立评分支持，不当作已查明的工具/模型单因果。

D核全部48原SSE/实际工具合同/请求hash/封顶账及容器清理；closure SHA `f92f4bb287b216cfb8401e6862656df6139e13416496b2b65c673bc2481ffb1a`，原receipt SHA `5d9cc82cd7a069e2b39b47920fcafa844b27c49ab0ff9f8733f99786824144fe`。私有薄包183成员/742,006bytes，SHA `9dd91038692e93b97319dd3fbb33bfa15d3e0d905e4aa19fc6b3b97cc7cb8825`，本机逐项核182文件。源码/依赖沿用原资格资产，不用参考patch冒充Agent成功。

**历史设计（已执行，结果见[当前结果](#current)）：同输入单轮教师代码修复能力对照。** 同27B/seed17/32k上下文/8k总输出，非thinking与thinking各最多1POST，只有请求级思考开关不同。输入限本来源的公开题面、源码和真实执行反馈；D定位辅助不冒充完整自主Agent。输出补丁在隔离工作区检查并原生评分，严格保留reasoning/content、格式或长度失败、调用和形成成本。固定模板具有True分支，但旧source入口强制False且False计数器不能套用True；当时只准备薄衔接与CPU验证，尚无True实际请求或新训练。不继续同配置48轮重试；必要时比较明确标记的source-reference辅助基线。新增[SymPy集合候选](ALFWORLD_LEARNING_RUNTIME.md#sympy-intersection)仍仅作公开行为素材。

当时[单轮入口](../contextbench_teacher_patch.py)与49项CPU检查已完成，尚未prepare或生成；后续实际执行由页首结果取代此状态。真实分词初检将BatchEncoding的2个字段误作长度，旧证明保留为无效；修复后按一维整数token计数，False为3,583、True为3,619，加8,192输出与512余量均小于32,768。协议SHA `983a80057a21db5863bf08a7a3f9de2f438ff778ed815a6b8d0d6ac878adaf67`；实际CPU复核SHA `76e67530e5eb66e72080325bed3a9230aab8351d03f09555092270ca7202088b`，模型/环境/容器0。它是代码来源的能力诊断，不把它设为其他已合格ALF来源继续研究的统一前置。

报告保留两项byte差：每题wire计数比原SSE body多6,720bytes。冻结relay明确wire另计HTTP响应头，body文件不含头；单位不同，不据此判断token丢失或超帽。动态头原文未归档，未声称独立重建每字节。两源闭合私有包349成员/2,068,583bytes已双端核验，SHA `3d3ac3fa60fcc0ac078204f96113e43397863a0aa67eb6e2e7d44e6399c2de63`，本机check SHA `973a88f07660ea1d4efdf6b7cf2091d22090b9942b6bd861007b9c05514c8d8a`；尸检报告随后单独镜像，不重打原包。

[Current result](#current)
