# ALFWorld：执行纠正与学习开发

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。目标是形成真实可执行的反馈监督，尚未训练或建立新方法贡献。

四现场能力诊断与旧分账已移至[已关闭的先导实验](ALFWORLD_CONTEXT_STUDY.md#teacher-pilot)；本页保留当前结果和下一动作。

## 已完成：原十二个失败现场的固定教师对照

八题扩展批已全部返回：look_01、cool_02、heat_02、heat_04、heat_05成功，look_02、cool_03、look_04失败；270真POST、2,893,399tokens。与前四题合计，27B recent恢复8/12，共351 POST、3,817,330tokens；本专题总计1,804 POST、20,340,505tokens，不是项目全局账。所有失败与形成成本保留；cool_04等上下文门不证明任务无解，look_04还包括大量被环境拒绝的动作。

`teacher_pool_expansion_v1/RESULT.json` SHA `7925d7ea2114fd392dfe843a821488c97fc8bede79d53d6e5b7716aa72d85cde`；PID4095165已退出。教师的每个现场都从原source分支，不能当作先免费尝试别臂再回滚的部署收益。

离线导出位于`context_study_v1/recovery_supervision_v2/teacher_drop_recent_complete_v1`：8个任务/布局组、83个接受动作回合；`data_manifest.json` SHA `aea83b3319a3f90f5472a28bb0ba5990a64f6e0e92c519a21a717473d76fa44b`。这是同一环境的四类任务，不是8个独立来源。全部351次教师请求（含4条失败）计入形成账；1576项输入证据未改变。`qualification_v1.json` SHA `91e1417146965d98ed52316b6398e276135b4366e472973b9ca1a10357695ef4`还检验了真实双轮失败：固定Continue、同会话、27次tool结果对齐22个实际动作，正监督为0。

导出保留真实请求/SSE、公共content与tool_calls；被拒绝动作、工具反馈与最终文字不作为正监督，失败上下文不删除。每个当前动作completion仍须按实际请求编译token标签。已验证多轮chat候选不等于可直接投入旧单completion训练器。

CPU tokenizer已完成真实编译：83行/8组、3,582监督token，最长10,740，无排除或截断；逐个使用实际forwarded request和native SSE，历史消息及tool输出mask为-100，只当前助手动作completion＋单个im_end监督，尾部模板换行不计loss。HF模板前缀逐token相同；未加载权重、未调用CUDA或推理。`supervision_tokens_v1/teacher_drop_recent_qwen3_8b_v1/data_manifest.json` SHA `e12352162db845a61e14f337b722b17391262c08a953817c0316da388ebf124e`。数据量仍小，接受动作中也有冗余/探索，不能称逐步最优示范；训练比较须控制接口收益及来源不平衡。

## 已完成：从头执行的强教师与普通监督

`ordinary_teacher_v1/RESULT.json`已闭合：27B从真实reset执行原18题，成功16/18；265 POST、2,518,697tokens＝2,505,815输入＋12,882输出，usage缺失0，cache细分未知，episode用时合计2,003.724秒。clean_02、heat_01触输入上下文门而失败。RESULT SHA `e52b1c2d7b146b0f3884e8d65197691ee9e3cb83dd7d2ce4e1bc05e45f9ae085`，原PID4157942已退出；本专题累计2,069 POST/22,859,202tokens（不含更早项目账及研发Agent）。

同一12个原未完成任务上，直接教师从头完成11/12、160 POST；教师从学生现场恢复8/12、351 POST，尚未加学生形成费。clean_02只在恢复成功，cool_03/cool_04/look_02/look_04只在从头成功。两种起点、进度和上下文不同，这是配对开发诊断，不能归因为“重启/保留进度”的单独作用；也不能默认小模型失败后再接管更省。直接教师是必须保留的部署成本参照。

16条成功轨迹导出171个接受动作，CPU编译7,311监督tokens、最长18,180、无截断/排除。chat manifest SHA `b7cbec3a1660e20f293a08b5feae2470a28e024a10f4d50267ff6e20ce7f8bb6`；token manifest `supervision_tokens_v1/teacher_ordinary_reset_qwen3_8b_v1/data_manifest.json` SHA `3e070a3e713279405b0e23db6fcd38ac75f5e95c8991997b09cbc7d779cb3675`。两条失败成本均保留，普通监督无虚构collector或重放费。

## 当前动作：新布局基线先行，SFT作有界支持

普通/纠正轨迹成功交集为7个任务/布局（普通67动作/2,865监督tokens，纠正68/2,950）。按双方成功取交集是common-support条件分析；唯一clean纠正任务被排除，因此训练只含heat/cool/look三类，不能称覆盖全部失败。配对记录`recovery_supervision_v2/ordinary_recovery_pairing_v1.json` SHA `dc0f6b6a6c464b53c16d708e51ee33d0ba61157bbe351f7e678f782d4eba5fcf`。全部形成与失败成本不因筛选删除。

两臂用同HF8B基座、seed17、新q/v LoRA r8/alpha16/dropout0，各计划192次成功optimizer更新，来源均衡轮转且覆盖全部动作；普通计划1,135,199序列tokens/8,239监督tokens，纠正1,135,273/8,378。只称同来源/初始化/更新数；不把不同训练量写成完全等成本。现役计划为`learning_comparison_v1/plans/ordinary_v4`（manifest SHA `875243cbcab87d968789e76f34745ee3514c27e0ac65c470ab499b8ee90a8c09`）与`recovery_v4`（SHA `4be913090ed70584a52b7b7d832b3aecc3e87991221bb3665ca953ef274888c7`）。历史计划/源码/失败保留，全部采样与预算未变。`owned_window_v3`已开始实际运行：普通臂成功加载权重并产生有限loss/非零梯度更新，纠正臂排队；实际步数查各plan的`steps.jsonl`，以最终receipt为准。request SHA `69c07d8e1a6e63539a01b3d4ad85d69e7362a096c11b20cb2004287649fe66ff`。只暂停owned18104，结束原样恢复；共享35B/27B不变。训练前后不加入canary生成，实际学习效果随后按环境won评价。

仅D在持有本study队列及owned18104窗口时显式运行，窗口不代表整GPU独占；共享35B/27B保持常驻，结束须恢复owned8B原argv/cwd与健康。OOM保留失败、实际步数与未知项，不自动换模型/截样或改共享服务。4B不是前置。HF8B五shard共16,381,516,776bytes已完整绑定；`HF8B_MODEL_BINDING_V1.json` SHA `b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1`。它不证明与旧GGUF权重数值等价；部署比较要保持相同推理基座/量化与接口。

v2首次实跑在权重加载前返回`Invalid device argument`（0权重加载、0forward、0优化步，不是OOM或学习负结果）。根已在新进程精确复现：reset_peak不触发CUDA初始化，必须先mem_get_info；现已修正并以失败→通过回归验证。`owned_window_v1`结束已恢复8B原argv/cwd（PID16445），共享35B/27B身份未变；5次健康GET、1次CUDA内存探测、零模型生成。旧窗口与receipt保留，随后v3在CUDA初始化处报OOM，仍0权重加载/0forward/0步；`owned_window_v2`已恢复原8B（PID24359），共享服务未变，7次健康GET/1次CUDA探测。两次都不是学习负结果。定向释放已绑定HF8B文件的clean页缓存，实测MemFree增加约8.7GB而MemAvailable近似不变；v4仅在逐shard完整核验后作同类建议，并记录原始异常堆栈与阶段，不保证显存足够。不改共享模型，不让此支持项阻塞主线。

独立数据复核读取361份原SSE和135配对训练行，无差异；只允许7组暴露任务上的有限学习开发，不是训练器或泛化审定。`learning_comparison_v1/independent_data_review_v1.json` SHA `2cf11cceebef3c06caeb07ebd7f6b7a04807fd930c9a6abd21757ebd132859b8`。训练源码/CPU loss与梯度检查另行验证，不将mock通过冒充真实GPU训练。

## 新布局与第二环境

另冻结16个development-heldout任务：clean/heat/cool/look各4，16布局/UID；排除原28个已知布局。`heldout_pool_v1/POOL.json` SHA `5f1eb3820881d797867c8348e71559a57d339a753bb88ef5b7bf70530095be00`，资格SHA `3ff9f90bb2a254f38db43817d73df84b42095a818554d19199161deace9b3e65`；官方expert/native控制16/16通过，CPU89.53秒，无替换。仍是官方train来源的本地开发留出，不是跨来源或正式确认；expert轨迹为EVAL_ONLY，禁止进入训练。原18配额因可用heat/cool合计8布局而需9不可行，先改四类各4并冻结元数据匹配规则，再运行控制；原阻断证据保留。

未来三臂共同使用相同actor/输入/cap，分别报告12个训练已见类型任务和4个未在本轮SFT出现的clean非退化检查，以及整体16题；不凭环境资格宣称模型已评测。

冻结8B基线批次`heldout_frozen8b_v1`已闭合：原控制器PID29543已退出，Q下`run_context_study_heldout_frozen8b_v1.py`；代码epoch `62b197b8`，16题按冻结顺序全跑，stage ordinary_reset、无经验、无LoRA。评测protocol SHA `5af8c4579b8f14ed2fc3e2857b2928726b83a02c81e1b2b33ac81d4e18497aa2`。RESULT SHA `18e6873320b843a1256ba1b285e1036bb95fa62e866adaba24ae277fc5780c6c`：won为3/16（look2/4、cool1/4、clean0/4、heat0/4），755 POST、9,055,073输入＋33,410输出＝9,088,483tokens；其中缓存输入8,871,228是输入子集，不重复计费量。usage未知0。本专题累计2,824 POST/31,947,685tokens，不是项目全账；新16结果不进入训练或调SFT超参。

独立复核16份receipt/manifest和755份原SSE无差异；13失败按最终停止原因分3个POST上限、4个context门、6个普通stop（均已继续一次）。4个零工具错误失败仍处理错对象或漏清洗。侧车`heldout_frozen8b_v1/independent_review_v1.json` SHA `65c72e1a017aff2f7dc4c45cd738953be545995c8b4526315d954961060c008f`。这支持检验合法动作基线，不证明所有失败都由动作格式引起。

[直接策略](../alfworld_direct_policy.py)已在同16题实际跑完，服务端动态schema可用：native won为1/16（仅cool_03），比旧臂新增1题、丢失旧3题；7个context门、8个100动作耗尽的done-unwon、1个won。1271 POST/动作均在此前公开admissible列表，无非法动作；13,811,233输入＋9,819输出＝13,821,052tokens，缓存输入13,477,285为输入子集，unknown0。逐响应hash/usage、16个相同公共reset及独立native终态均复算通过。RESULT SHA `6f265b6a9416ffaef77e66823f61e4255fdb28fb661c4859fa3ed7084efee42b`；`COMPARISON_V1.json` SHA `f8f1d32b0724f6895955c94f3541bbcc64dd0fb9a7da7de2ed27c91ca172eaf9`。本专题生成累计4095 POST/45,768,737tokens，不含训练和研发Agent。

该臂保留原目标/完整公共历史/权重/采样/caps及一次Continue，但同时去除OpenCode计划/工具结构并只准输出单动作JSON；结果不识别单独约束效应，也不代表强简单基线已经穷尽。不再修补此action-only臂。对照[ReAct §4](https://arxiv.org/html/2210.03629v3)及[官方ALFWorld入口](https://github.com/ysymyth/ReAct/blob/master/alfworld.ipynb)（2026-11-07已读，未复现成绩），后续保留同数据条件的计划/示例基线；不能把它们的收益改称新经验机制。原16题已属暴露开发数据，未进入SFT监督或超参选择。

Django34570已完成新自然问题准备（私有`django34570_development_v1/summary.json` SHA `dd4046ba3b380103c967f7ee0b7d688188fa0b863e1bd8e4e47665c12d96bd28`）：base关键1项报错、gold1/1通过，两者回归13/13；M2M/GFK公开调用在base报AttributeError、gold正常。10次CPU容器含初次权限失败，均保留；gold/test补丁独立于actor源树。尚无模型运行，未来完整actor可读面未验收，公开复现当前为空SQLite查询，不把13项测试算13任务。

## 方法重叠与下一验证

[ACE §3](https://arxiv.org/html/2510.04618v1)已有带效用记录的条目、局部delta更新和保留历史知识；[AgentFold §3](https://arxiv.org/html/2510.24699v1)已有任务执行中的细粒度/深层上下文折叠和轨迹SFT。[STeP](https://arxiv.org/html/2505.20023v1)已有学生失败现场的教师纠正与partial masking。均已读方法正文，未复现成绩；局部改经验、继续外部进度或换LoRA都不足以构成独立贡献。

**2026-11-07原文新增核对**：[Dependency-Guided Rollback Repair §3](https://arxiv.org/html/2608.10502v1)已研究故障经验的后继失效、独立支持保留和选择性重放；其输入包含上游已诊断的故障memory，明确不能撤销不可逆外部副作用。因此“撤回前提及依赖、保留未受影响部分”也不是新机制。可比较的剩余条件是普通执行反馈下的诊断不确定性、实际外部进度及补偿成本，是否值得学习仍须实测。

[Invalidation Contracts §3/6.4](https://arxiv.org/html/2609.00243v1)提供服务端版本/差分与依赖失效，实验为作者构建API；[MERIT §3](https://arxiv.org/html/2608.05906v1)已有按错误类型检索正负修复记忆，但终态正确性用oracle反馈。这些是应对齐的近邻/信息条件，不因换环境就认定独立增量。当前失败并未证明需要复杂依赖机制；先比较精确目标绑定、循环保护、等预算摘要和相关局部更新适配。新增最直接对标（2026-11-07读方法正文，未复现成绩）：[Sentry §3](https://arxiv.org/html/2610.02994v1)已按运行中失败触发少量经验、验证局部恢复再入库；[EMG §4](https://arxiv.org/html/2607.13884v3)已对失败/成功轨迹做决策图匹配以提取纠正知识，并在ALFWorld/ScienceWorld评测；[VH-GPO §3](https://arxiv.org/html/2610.14000v1)已从学生现场做教师恢复、验证提前交还控制并学习。故“条件暴露失败经验”“从成功/失败差异抽技能”“短教师桥＋学生续做”也须作为对照，不能直接改名为新方法。优先对齐Sentry的反馈条件、EMG的监督来源和STeP的纠正训练；VH-GPO涉及额外搜索和RL，比较时不能省略其形成成本或称已完整复现。

普通/纠正监督学习是能力和训练对照，不预先宣称新方法。第二环境按[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)接续；不再训练已无成功选择空间的旧四臂选择器。

## 本轮判读与训练对照取舍

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：教师恢复已有8组真实监督，16新布局的OpenCode/native动作臂分别3/16和1/16；UNVERIFIED：纠正监督是否比等源普通成功SFT更有迁移价值，或只是修复工具接口。Recommendation：完成有界训练对照，保留计划/示例等强简单方法。Conditions：接受动作不等于最优动作；同任务两类轨迹不算两个来源。Risk/exit：若简单goal/合法动作/循环控制已解释收益，停止复杂学习候选；保留形成与失败总成本，不让训练内存资格阻塞独立任务。First action：监测两臂SFT及原服务恢复，核同推理基座/实际激活adapter后再评价；第二环境只补薄任务入口。

新薄包`alfworld_teacher_complete_supervision_v2_20261107.tar.gz`（1,553成员，5,421,100bytes；SHA `5361d083bdeb7599efce2781667ae2903cc05ab93507b0445d23036dd7954bf2`）已在GB10、本机逐成员核验；manifest SHA `37997af7e5f5d5460315c078454b1eb94b7d8b8e314c78651e46362ca9117403`。依赖前述source/四诊断薄包；不含在途普通18题，也不是公开可再分发数据包。
