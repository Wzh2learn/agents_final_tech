# ALFWorld：执行纠正与学习开发

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。目标是形成真实可执行的反馈监督，尚未训练或建立新方法贡献。

## 已完成：四现场的能力诊断

固定取三个自然未完成source（cool_01/cool_04/heat_03），加clean_02校准；后者不是新任务。补两条缺失8B drop_recent后，与27B在相同原source、公共目标/观察、最近3条accepted history及总cap比较，已有学生结果不重跑。教师不用专家动作、隐藏事实或参考计划。backend能力/实际计算不同，这不是等计算方法比较。

| 现场 | 8B won / POST | 27B won / POST | 27B新动作 / tokens |
| --- | --- | --- | --- |
| clean_02 | false / 10 | true / 16 | 15 / 128,280 |
| cool_01 | false / 12 | true / 12 | 10 / 80,968 |
| cool_04 | false / 63 | false / 47 | 46 / 681,234 |
| heat_03 | false / 71 | true / 6 | 5 / 33,449 |

27B成功恢复3/4，提供3个不同任务/布局的实际纠正候选；不是3个独立环境，也不是人工gold。成功轨迹仍须按真实tool结果、执行合法性、角色与来源检查后才能导出监督。cool_04的27B也触输入＋8192预留输出＋512余量的上下文门，不能称其任务不可解；它保留为失败和后续长轨迹分析，不混进成功监督。暂不围绕单例追加提示变体。

批次`context_study_v1/teacher_state_batch_v1/RESULT.json`为`ALL6_TEACHER_STATE_DIAGNOSTICS_RETURNED`，原PID4073951已退出。新6条共215真POST、2,863,108tokens＝2,853,227输入＋9,881输出；2条学生134 POST/1,939,177tokens，4条教师81 POST/923,931tokens。已知cached1,891,711仅来自学生输入；教师81次cache细分未知，不能填0。usage unknown为0；另3次本地预约未forward。

复用冻结独立审阅脚本的纯解析函数，逐条重读SSE/body SHA、输入绑定、原生终态和重放，四对prompt原文/caps/cohort/source相同；差异0。`TEACHER_STATES_RECOMPUTE_V1.json` SHA `1bf001d43834b4d9a691b151c7a76eca4bb74b6958c011b647d165708a4fee90`。它是确定性复算，不是新独立人工/统计审阅。

本批结束时本专题累计1,534真POST/17,447,106tokens，source形成只物理计一次；这不是项目全局账，研发Agent与更早形成/训练成本另账引用。没有新增训练、judge、付费科研API或生产写回。

两个增量私有薄包已在GB10和本机逐成员核验：`alfworld_simple_controls_v1_20261106.tar.gz`为3,080成员，SHA `7edfbc4635a5f175343dddb4721f6182e4efcb473c661cf15933d2c2479669a4`；`alfworld_teacher_states_v1_20261106.tar.gz`为1,241成员，SHA `52358c539c563e3e86a16a2be29ab8135bdd9c06267d87639d543ae7dd5d3bc4`。原source依赖[背景记录](ALFWORLD_CONTEXT_STUDY.md)所列18题包；这些不是完整runtime或公开artifact，不包含在途8题。原始命名保留批次开始日期，不因跨午夜改名。

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

## 当前动作：7组来源匹配的有界SFT开发

普通/纠正轨迹成功交集为7个任务/布局（普通67动作/2,865监督tokens，纠正68/2,950）。按双方成功取交集是common-support条件分析；唯一clean纠正任务被排除，因此训练只含heat/cool/look三类，不能称覆盖全部失败。配对记录`recovery_supervision_v2/ordinary_recovery_pairing_v1.json` SHA `dc0f6b6a6c464b53c16d708e51ee33d0ba61157bbe351f7e678f782d4eba5fcf`。全部形成与失败成本不因筛选删除。

两臂用同HF8B基座、seed17、新q/v LoRA r8/alpha16/dropout0，各192次成功optimizer更新，来源均衡轮转且覆盖全部动作；普通计划1,135,199序列tokens/8,239监督tokens，纠正1,135,273/8,378。只称同来源/初始化/更新数；不把不同训练量写成完全等成本。`learning_comparison_v1/plans/ordinary_v2` manifest SHA `ec4aa26b91041a316af0319e0704405d006a5d71e4195fd126c1b5c25bd3e2d4`；`recovery_v2` SHA `2b2364fa8a4c8dcfcae5ed327c2cce4503ee80a3a8fab88cac23180cfbce0217`。v1是未运行CPU草案，原样保留。训练前后不加入canary生成，实际学习效果随后按环境won评价。

仅D在持有本study队列及owned18104窗口时显式运行，窗口不代表整GPU独占；共享35B/27B保持常驻，结束须恢复owned8B原argv/cwd与健康。OOM保留失败、实际步数与未知项，不自动换模型/截样或改共享服务。4B不是前置。HF8B五shard共16,381,516,776bytes已完整绑定；`HF8B_MODEL_BINDING_V1.json` SHA `b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1`。它不证明与旧GGUF权重数值等价；部署比较要保持相同推理基座/量化与接口。

## 新布局与第二环境

另冻结16个development-heldout任务：clean/heat/cool/look各4，16布局/UID；排除原28个已知布局。`heldout_pool_v1/POOL.json` SHA `5f1eb3820881d797867c8348e71559a57d339a753bb88ef5b7bf70530095be00`，资格SHA `3ff9f90bb2a254f38db43817d73df84b42095a818554d19199161deace9b3e65`；官方expert/native控制16/16通过，CPU89.53秒，无替换。仍是官方train来源的本地开发留出，不是跨来源或正式确认；expert轨迹为EVAL_ONLY，禁止进入训练。原18配额因可用heat/cool合计8布局而需9不可行，先改四类各4并冻结元数据匹配规则，再运行控制；原阻断证据保留。

未来三臂共同使用相同actor/输入/cap，分别报告12个训练已见类型任务和4个未在本轮SFT出现的clean非退化检查，以及整体16题；不凭环境资格宣称模型已评测。

Django34570已完成新自然问题准备（私有`django34570_development_v1/summary.json` SHA `dd4046ba3b380103c967f7ee0b7d688188fa0b863e1bd8e4e47665c12d96bd28`）：base关键1项报错、gold1/1通过，两者回归13/13；M2M/GFK公开调用在base报AttributeError、gold正常。10次CPU容器含初次权限失败，均保留；gold/test补丁独立于actor源树。尚无模型运行，未来完整actor可读面未验收，公开复现当前为空SQLite查询，不把13项测试算13任务。

## 方法重叠与下一验证

[ACE §3](https://arxiv.org/html/2510.04618v1)已有带效用记录的条目、局部delta更新和保留历史知识；[AgentFold §3](https://arxiv.org/html/2510.24699v1)已有任务执行中的细粒度/深层上下文折叠和轨迹SFT。[STeP](https://arxiv.org/html/2505.20023v1)已有学生失败现场的教师纠正与partial masking。均已读方法正文，未复现成绩；局部改经验、继续外部进度或换LoRA都不足以构成独立贡献。

**2026-11-07原文新增核对**：[Dependency-Guided Rollback Repair §3](https://arxiv.org/html/2608.10502v1)已研究故障经验的后继失效、独立支持保留和选择性重放；其输入包含上游已诊断的故障memory，明确不能撤销不可逆外部副作用。因此“撤回前提及依赖、保留未受影响部分”也不是新机制。可比较的剩余条件是普通执行反馈下的诊断不确定性、实际外部进度及补偿成本，是否值得学习仍须实测。

[Invalidation Contracts §3/6.4](https://arxiv.org/html/2609.00243v1)提供服务端版本/差分与依赖失效，实验为作者构建API；[MERIT §3](https://arxiv.org/html/2608.05906v1)已有按错误类型检索正负修复记忆，但终态正确性用oracle反馈。这些是应对齐的近邻/信息条件，不因换环境就认定独立增量。当前失败并未证明需要复杂依赖机制；先比较精确目标绑定、循环保护、等预算摘要和相关局部更新适配。新增最直接对标（2026-11-07读方法正文，未复现成绩）：[Sentry §3](https://arxiv.org/html/2610.02994v1)已按运行中失败触发少量经验、验证局部恢复再入库；[EMG §4](https://arxiv.org/html/2607.13884v3)已对失败/成功轨迹做决策图匹配以提取纠正知识，并在ALFWorld/ScienceWorld评测；[VH-GPO §3](https://arxiv.org/html/2610.14000v1)已从学生现场做教师恢复、验证提前交还控制并学习。故“条件暴露失败经验”“从成功/失败差异抽技能”“短教师桥＋学生续做”也须作为对照，不能直接改名为新方法。优先对齐Sentry的反馈条件、EMG的监督来源和STeP的纠正训练；VH-GPO涉及额外搜索和RL，比较时不能省略其形成成本或称已完整复现。

普通/纠正监督学习是能力和训练对照，不预先宣称新方法。第二环境按[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)接续；不再训练已无成功选择空间的旧四臂选择器。

## 本轮判读与训练对照取舍

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：教师恢复已有8组真实监督；UNVERIFIED：它是否比等源普通成功SFT更有迁移价值，或只是修复工具接口。Recommendation：先完成直接教师/普通成功池与逐completion标签；在交集任务上匹配基座、来源权重、有效监督token、步数与评测接口，再做小规模学习开发。Conditions：接受动作不等于最优动作；同任务两类轨迹不算两个来源。Risk/exit：若无稳定独立任务增益或简单goal/合法动作/循环控制已解释收益，停止复杂学习候选，保留数据与负结果；不为等所有环境/模型资格而延迟有界开发。First action：完成独立数据复核后，显式运行两臂有限SFT，再在冻结新布局上比较。

新薄包`alfworld_teacher_complete_supervision_v2_20261107.tar.gz`（1,553成员，5,421,100bytes；SHA `5361d083bdeb7599efce2781667ae2903cc05ab93507b0445d23036dd7954bf2`）已在GB10、本机逐成员核验；manifest SHA `37997af7e5f5d5460315c078454b1eb94b7d8b8e314c78651e46362ca9117403`。依赖前述source/四诊断薄包；不含在途普通18题，也不是公开可再分发数据包。
