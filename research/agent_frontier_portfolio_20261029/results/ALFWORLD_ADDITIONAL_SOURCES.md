# ALFWorld 来源与恢复：当前证据

> 2026-11-09 | 只保留可复用结论与入口。完整过程已[归档](../../../docs/archive/2026-11-06_agent_research_context/alfworld_sources_through_20261108.md)，原始轨迹、预算和失败未改。下一动作只查[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 来源池与闭合采集

旧12个官方TRAIN任务，clean/look各6个、12个不同布局，按固定身份hash排序。已排除登记的训练/开发索引，不等于全项目或预训练隔离。旧“134个保留候选”实际是官方`valid_unseen`保留项，不是TRAIN；只读元数据，继续保留确认。原生资格12/12通过，专家轨迹不向actor提供。

| 从reset执行的来源模型 | Clean成功 | Look成功 | 总成功 | 实际POST | provider tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8B Q4学生 | 0/6 | 2/6 | 2/12 | 592 | 6,064,851 |
| 27B FP8教师 | 4/6 | 6/6 | 10/12 | 339 | 3,383,834 |

此24槽合计931 POST、9,448,685 tokens；27B缓存明细未知。教师从reset成功不自动成为针对学生失败的纠正。闭合工件位于私有`learning_comparison_v1/next_train_source_v1/source_collection_v1/`，以`D_SOURCE_COLLECTION_CLOSURE_V1.json`的逐槽实际路径为准：clean01学生attempt3、教师attempt2，其余attempt1，不能猜目录。

**离线自然错误筛查。** 本轮只读旧24槽原始工具反馈，重算921次工具调用＝403个公开状态返回＋518次`invalid_action`，与原采集账一致；学生/教师分别373/145次非法动作。只在已观察的公开合法命令内，筛`put ... in/on ...`的介词别名及`move ... to ...`→`put ... in/on ...`两条精确替换，均无唯一合法替代（0/518）；不把重复循环算独立样本。私有`trained_baseline_transfer_v1/D_NATURAL_ERROR_SCREEN_V1.py/.json`保存规则、逐槽统计及源码/原包SHA。这是事后适用性筛查，未执行修复、不推任务成功，也不否定其他规则；36槽F/O/R输入不变。

- POOL SHA256：`24a30747b87102a7dcfe2f92c666596285f72f7cc7b3a0c52f630acc5cd75023`。
- D闭合 SHA256：`c017c9dfb02a8d27a7d837e2544ca47aef03d641df0c56e011b5aa0c2016b86f`。
- 私有采集包SHA：`95a1ff1b31a422a9b73f934787d4f942ae646923e7aaaf21a7932d53c02d2e79`；成员、实际路径及账本见[完整采集记录](../../../docs/archive/2026-11-06_agent_research_context/alfworld_sources_through_20261108.md#完整闭合结果与失败类型)。

<a id="progress-feedback18"></a>
## 新18个开发源：采集已闭合

新增clean9/look9均来自TRAIN；UID、family、layout/group、game hash互异，排除旧18/16/运行池、新12、7训练源、2上游源及登记的保留身份。筛后有clean55条/11布局、look103条/10布局，按冻结身份hash取18，不按结果换样。数字布局不同不证明语义独立，完整外部/预训练曝光仍未知。

两份官方ZIP及36个选中成员实际hash相符；18/18专家控制通过，共247动作、串行48.59秒。核原生观察/score/done/won、reset合法动作、同seed重置/名称映射；D另逐项通过现役池读取器。资格阶段无模型、HTTP、训练或容器调用，不提供actor失败或学习成绩；专家轨迹只在私有评价侧。

私有根`progress_feedback_development_v1/native_pool_v1/`：`POOL.json` SHA `7fe85fb7564b1e0eba908e1279522a84fefce0dd61b80f2c75ad646ec992c6fe`，`qualification.json` SHA `581735ebf62a710c1a8819a8a50a3ac6f916b45129f62514ad3d149d5c9b874c`。双端包`progress_feedback18_native_qualified_v1_20261109.tar.gz`为305,768bytes/170文件，SHA `2ff52de6a5a1abdcdca89f9aca75e8270e8f1bbe07c1a4a779830545bdf7754e`；不含完整ZIP或模型。

**真实结果。** F共同BF16无LoRA、全7普通历史、seed17/温度0.2、thinking关闭、32K/8192、required及原生终态门，固定18题未换样：clean 1/9、look 3/9，共4/18成功。14个未完成均有物体相关动作、原生非终态、剩余38–93动作；13个触上下文帽，1个触128 POST帽。原世界已关闭，后续须重放并另设预算，不能称现存可续世界或14条合格纠正。

实际930 POST，input 14,506,473/output 55,860，总14,562,333；cache input 14,187,324为输入子集，非缓存319,149，未知usage为0。928个schema合规调用＝721次原生动作＋207次`invalid_action`，另2次8192-token length无工具，均在clean05；required不保证执行。14条末反馈均记录在actor输出/observed请求，其中12条完整末状态未进入最后实际转发请求，不能归因为模型看见后拒绝更新。无教师、训练或judge；旧形成账不重置。

D独立复算5,689 raw及92输入绑定，C另核18题/930 SSE与成本。36个原生world退出0，19个自有actor容器、controller/BF16子进程均已退出；Q4身份恢复、35/27未改、锁已释放。窗口4,858.64秒，低于7,200秒目标。`RUN_V1/RESULT.json` SHA `0ff420c3fa5999ede5af089b88307865a557057583f12a85ef2ed98fd26c36fb`；`D_C_SOURCE_CLOSEOUT_V1.json` SHA `1ad54b829069680bb0abcc60efb31cea1aec7d10938e78158768682c217502f3`。采集仅为TRAIN开发，不证明全7历史导致失败，也不构成方法增益；134 valid_unseen仍保留。

双端闭合包`progress_feedback18_source_closed_v1_20261109.tar.gz`，50,123,773bytes/6,098文件，SHA `7229867ec4a5f9cecbc752961785eb0f6f3073f7b1a1df1c9f383bcdc73eb2ab`，含全部raw绑定、逐成员清单及D/C核查；不复制workspace缓存/DB，原件保留。它依赖双端输入包`progress_feedback18_source_inputs_v2_20261109.tar.gz` SHA `179f8f6960a9027fc240c17cb6253aa6649a596215fa3b3eb2adb6a699aaec18`及上方资格包；计划/预算/执行器的完整绑定在包内，不再从历史启动句重开采集。

<a id="observability-controls"></a>
## 旧两题原生取证控制

仅复用已曝光clean02/look01，各三分支，不是六个独立任务。第一项固定查询与请求续做下，clean成功向量`[真,假,假]`、look`[假,真,假]`：相同投影历史/交接观察仍可因位置变化得到不同反馈；相同查询观察也可能未反映之前是否清洗/开灯。固定请求不保证全部合法，30个新请求中3个被拒；共153动作（含126重放）、7.21秒CPU、零模型。

第二项改为同一公开反馈搜索policy：旧位置优先，其余位置来自公开合法移动命令；找到后直接交付、不再clean/use。两族均`[真,真,假]`，6world/181合法动作（含重放）、6.06秒CPU、零模型。位置影响可被该搜索消除，但policy未读取进度见证，所以尚未证明这些见证必须存储。候选必须与“进度清单＋搜索”和“总是重新处理”比较；不能从物理进度重要直接推出记忆机制有效。

私有`progress_feedback_development_v1/observability_controls_v1/`保存两套计划/原始轨迹与D复算。第一项5个原始header的plan字段误为`domain`，数值与实际plan通过RESULT/raw hash间接绑定，D/C追加说明，未改旧raw；具体依赖修改argv的根因未核实。第二项6个header均正确。投影历史未实际送新actor，不证明隐藏状态等价、全查询不可观测或学习收益。

双端包`observability6_closed_v1_20261109.tar.gz` SHA `6144db07158c2889aa92beec30e3f27f5f2ce9a0055a16954d83ad2a66269297`；`observability_public_search6_closed_v1_20261109.tar.gz` SHA `ead2869129a0cbf8ea61facb6a28b816ce70d7ed674443deb949529933611326`。每包32文件，保留预算、限制及原始绑定。

<a id="simple-recovery"></a>
## 14个新失败现场：强规则已解

source18全部14个未获胜前缀，不挑题；同seed重放全部成功动作，逐步六键公开状态及交接状态匹配，保留外部进度。两臂共用公开目标语法、固定搜索、合法命令和实体绑定：A重新清洗/开灯再交付；B仅在对应实例有未被可见事件否定的成功见证时省略处理，无见证同A。不是LLM、学习方法或最优规划器。

| 规则 | 原生成功 | 新动作 | 重放动作 |
| --- | ---: | ---: | ---: |
| A 总是重做 | 14/14 | 194 | 688 |
| B 公开见证省略 | 14/14 | 190 | 688 |

只有look02/03/06/09的B各少一次`use desklamp 1`，其余10题逐动作一致。28world、1,760合法请求/动作＝1,376重放＋384新动作，最大单world95/100步，46.43秒CPU；无模型、HTTP、训练、容器或服务变动。原source形成成本另计，不能称整个流程零成本。

D逐项复算全部原始native/request轨迹；C另独立核28槽。规则使用整理的全部公开成功动作历史、过滤原invalid_action，并获得完整最终状态；不等于旧actor实际收到的上下文或计量，不能直接将旧4/18与此14/14作为同信息模型对比。没有读取隐藏事实、专家、score/won来选动作，done仅作停机门。

**裁决：停止在此面板训练复杂保留/撤回选择器。** 成功残差被领域规则解释，4动作差无需新算法；不推论一般记忆学习无价值。这28条可作标明规则来源的恢复资产，不能包装为教师反馈或学习收益。

私有`progress_feedback_development_v1/simple_recovery_controls_v1/`：`PLAN_V2.json` SHA `947409aa5eb7874bac2b666d1e0916d46013d1f4f21b9355637c7b193c477608`，`RESULT_V2.json` SHA `b204eef6a4955a1cdbdf85a181eda02fe973266cc45444c72ad984b8c38ca74e`，`D_CHECK_V2.json` SHA `4bc997b26ceb00178582f649287eb58bae85aabc47d7897540f1d5cc7ba78317`。V1仅准备未运行，保留原字节；V2发布前10项CPU/13项fake通过，D另实跑fake，实际world结果独立记录。

`C_CONTROL_CLOSEOUT_V2.json` SHA `8e8a7f0f289e730de86ea75397862f9183b2b5fa9cbc02394dd8f89fa51ae481`。双端包`simple_recovery28_closed_v2_20261109.tar.gz`，135,933bytes/72文件，SHA `241219f2925233d5e465967a6469c000fdc7273c218c41f3485fdf31b2f5e677`；输入source与game依赖沿上方两包解析。

<a id="action-channel"></a>
## 首响应通道对照：不是任务成功

复用B6的01/03/05实际首请求，同BF16/解码，仅改`tool_choice: auto→required`。新3/3返回schema合规bash调用，旧3/3为无工具的stop；均无length。CLI形状正确，但01/03的动作不在各自源初始合法列表，05在；未执行任何工具或world，不能推定任务改善，也不将解码约束当纯因果工具。

新增3 POST：input24,009/output155，共24,164tokens，cached6,619为input子集；窗口51.38秒，训练/judge为0。C独立核请求、3 SSE、usage/schema/字节及公开reset；D另核Q4恢复身份、35/27和锁释放。当前私有`ACTION_CHANNEL_REQUIRED_V1/D_C_CLOSEOUT_V1.json` SHA `401c0c8d112a8f0d1fade3f316c634ed9337251843c868ce78c394ab070ba6ee`。双端包`action_channel3_closed_v1_20261109.tar.gz`为365,364bytes/102文件，SHA `ef5916660ab9d0d26ee0e713633460fedf64358e55dc54f05849427b6677d7c8`。

新协议以显式`action_channel=required`冻结执行采样，另记CBC构造采样；缺省/auto保留旧路径。required不替代`runtime_controls.native_terminal_stop=true`。使用新组件epoch，旧raw/评分不重算；真实episode见上方18源闭合批次。[首响应CPU准备/解析](../action_channel_probe.py)不执行工具。

<a id="student-failure-recovery"></a>
## 四组真实学生失败恢复：已闭合

复用clean02、clean03的8B自然失败现场，由同27B接管，保留外部进度。来源world/模型seed17；恢复seed17、thinking=false、32K/8192、同目标提醒、无额外经验输入。完整/近期分别同时控制初始公开历史和后续滚动历史，因此结果不能归因于单独首次截短。

| 现场 / 策略 | 原生won | 新POST / 新动作 | 恢复input / output tokens | episode墙时 |
| --- | --- | ---: | ---: | ---: |
| clean02 / 完整 | 是 | 20 / 20 | 148,455 / 990 | 144.09秒 |
| clean02 / 近期 | 是 | 11 / 11 | 54,491 / 558 | 82.95秒 |
| clean03 / 近期 | 是 | 14 / 14 | 67,986 / 709 | 104.12秒 |
| clean03 / 完整 | 是 | 9 / 9 | 54,160 / 460 | 67.87秒 |

合计54 POST、327,809 tokens，未知总usage为0、27B缓存未知；无普通续跑。每槽原生成功后一次额外请求均在预留/转发前拦截，不作模型拒答。C独立核四槽、373项绑定和54份SSE，无阻断；其身份是AI独立复核。

**结论。** 两题出现成本交叉：02近期更省，03完整更省。完整合计204,065、近期123,744 tokens；事后逐题最省109,669，是比最佳固定策略低11.37%的上界，不是部署选择器成绩。原学生失败形成成本151,217计入后，两种流程为355,282 / 274,961，直接27B从reset为186,721；当前无完整流程优势。不同模型/cache下token和不代表等价算力或费用。两题、一seed的成功接续不证明学生学习或技能迁移。

恢复根为私有`next_train_source_v1/state_change_development_v1/student_failure_recovery_v1/`：

| 接续需要 | 工件 / SHA256 |
| --- | --- |
| 冻结计划 | `D_MODEL_DEVELOPMENT_PLAN_V1.json` / `b925b781db27dcfa9179ae98b28faea7a7e2e990d6f396be81a110783642177e` |
| 当前闭合裁决 | `D_C_CLOSEOUT_V1.json` / `bc3b21f644fe0ce0c92d776d743e4802d60ac5de1c3ca2cf7be5f4e3cad2b0bd`；旧D_RESULT保留“待C”的历史字段。 |
| 双端核验包 | `student_failure_recovery_closed_v1_20261108.tar.gz`，571成员 / 570文件，SHA `0fe123da481523a6ac68f3d783835ec8777a46dcb65f210302cc6a17f6e10193`。 |

包内代码是当时冻结版本；后续helper修订不应使旧证据被误判失效。原生公开状态重放一致不外推为全部隐藏状态等价。

## 反馈后局部经验修订：单现场开发

复用 clean02 的真实 8B 失败前缀与公开反馈；27B writer 将旧错误计划中 cloth 与当前 soapbar 目标的冲突写入一条修订记录，另一条记录保留。原计划来自真实历史动作的后验整理，不是已独立验证的在线记忆提取器。同一重放现场、27B、相同完整历史及其他设置下，普通历史与局部修订均原生成功，各新增 9 个动作；全部公开状态和动作序列一致。普通/修订续做分别为 37,648 / 37,027 tokens；修订生成另费 2,742，总计 39,769，较普通多 2,121。缓存未知，墙时分别 56.31 / 57.33 秒。一个已曝光现场不支持收益或泛化结论，尚未训练策略。

完整批次还包含先前无改动 writer 2,587 tokens 和多轮计数器故障前已转发的 3,085 tokens；共 21 次实际模型请求、83,089 tokens，未知 usage 为 0。原始 receipt 位于 GB10 私有 `context_study_v1/learning_comparison_v1/feedback_local_revision_alf_v3/RESULT.json`，SHA `7c609424a28b40f4855c89b3c9b491bcbfca29881efeb6af9e0c14692e3c9321`；两臂 receipt 分别 `83081a9998972c20c42d2137d666264c05216b95527cdbffd29b16329acbf14f` 和 `8a802c8d9b58d817a669cdf17402fb91e913932cba4c1507d520aaafbb9b2d0d`。两世界正常退出，故障和旧 raw 均保留。双端私有包`feedback_local_revision_alf_20261109.tar.gz`含217文件，SHA `57a7741d5e93d0be9fcb5a85ec66d1bc8ad896dec92ed4351a54f0493d015e8a`；仍依赖既有来源资产。

**clean03 第二现场。** 使用该题真实失败动作和公开反馈后验组织经验；15步公开前缀重放后，同27B、相同历史、仅一条记录不同的两臂均原生成功，各9次请求和9个新动作；路径不同。普通/修订续做分别45,004/44,060 tokens，writer额外3,803，修订总47,863、比普通多2,859。各臂墙时59.50/60.23秒，cache未知。本批19次实际请求、92,867 tokens，usage完整；两世界正常退出。单seed、两个开发现场合计均未显示任务成功或动作数收益；训练0，不能推断总体无效。`feedback_local_revision_clean03_v1/RESULT.json` SHA `26d02b6769754b41844986f7d77b9a8f674193d4bfedcb4e7883e94b4f5f2ba3`；双端私有包含166文件，SHA `482633cce8a49568069c9adbaebeb168e3fcc4dfedf5dbeb0f6b81a040c22bf6`，仍依赖旧来源资产。

**更强监督素材。** 旧 heat_03 的 8B 在加热动作被拒后声称任务完成，但公开终态为 won=false；同场景教师后来完成任务。两者可用来构造带公开依据的纠正标签；原陈述不是已写入经验库的记忆，任务失败也不证明由旧经验造成。旧 cool_01 的“没有可用 tomato”可能指手持物导致无法直接取得，不能无条件标假。均为已曝光开发来源。

**heat03 第三现场。** 从同一10步公开前缀重放，使用8B、同目标/反馈/历史，只改一条经验。普通与修订两臂各12次请求、12个合法动作后均未成功；都没有重新取目标杯、去微波炉或执行加热。普通臂探索多个炉具并拿面包，修订臂在两个炉具之间搬锅；是否受到修订影响未知。两臂分别86,665/86,066 tokens，writer额外5,204，修订总91,270、较普通多4,605；cache分别20,722/49,168，墙时受缓存与顺序影响。writer提到杯子“未加热”，公开反馈不能证实隐藏温度，故修订文本只记模型候选、不作训练真值。原生接口正常，停止于请求上限；单现场不能区分能力、计划和记忆贡献。

本次含旧计数器投影故障前1次已转发请求及5,769 tokens，累计26次请求/183,704 tokens；旧raw和故障均保留，world正常退出。`feedback_local_revision_heat03_v2/RESULT.json` SHA `23a9476adf3bb4f5ecd84786c2875998cf74837fd7045d9ecd360cdaa9f31f37`；双端私有包238文件，SHA `91bae9614e00fb43c09c53549ba9dc2c18d4a41d8e6d3994272d2947924b554d`，依赖旧来源资产。三个现场都没有形成可支持当前修订机制优于普通历史的结果；下一研究应先利用原生反馈构造可核验、与行动对应的监督，并与简单反馈规则和已训练R比较，不把未经核实的推断充当标签。

## 反馈位置梯度训练：中断的开发尝试

复用 7 个已曝光来源的 68 个教师接续动作，附来源任务中先前实际被拒绝的动作及当时反馈；教师实际请求外添加的上下文明确标为派生内容。被拒动作与后续教师动作不假设发生于同一状态，环境接受也不等于逐步最优。两臂同输入、教师标签和 8B LoRA 配置：普通臂使用标准交叉熵，候选臂在反向传播时提高反馈片段的位置权重，前向保持恒等。七组未包含保留确认集。

一次真实预检在同一输入上得到完全相同的 logits 和 loss，adapter 梯度 L2 差为 0.001816，反馈片段梯度非零；这只验证该输入的梯度机制，不是任务收益。真实训练原计划两臂各 192 更新；旧 `run_v1` 在模型加载前因缺失 import 退出，0 更新。修正后的 `run_v2` 两臂各完成 8 个 optimizer 更新，各计 59,147 输入及 352 监督 tokens；baseline 第9次 forward 已开始，是否完成未知。另每臂各一次预检前向/反向，不并入上述更新量。没有最终 adapter 或评测结果。

8B 加载期间 GB10 发生严重内存压力并出现 SSH 无响应；为保护其他服务，精确核对 PID 后终止本次训练。进程已退出，可用内存回升到约33 GiB，但15 GiB swap 仍接近占满；共享 8B/35B 进程和27B容器/监听存活，接口健康未测试。未观察到可证明的系统 OOM，不能把中断解释为方法失败。数据 manifest SHA `ad807a1b9267a2d409cea77c28284cea2d3ee0277faae472bc9a79fdcf2ac99f`，预检 SHA `ebc5739d0895cbb41a4d763f048faa2f41565e9df05bdc2aedf993e9de857ca1`，终止记录 SHA `aab5890f196712c48eb2fe4d247b6e8ecc85cfc03fa1aad4ab15596205be7e7d`。双端私有证据包 40 文件，SHA `cd261b1673e2b2accb5e7ab7341786bf66e9e59a41ff08aada6743afb8640c8e`，不含模型或旧来源资产。后续如用4B进行同模型配对，须独立核实资源上限，不能把4B候选与8B R直接当同模型因果对照。

**4B 受监控准备。** 现有 HF Qwen3-4B 权重约7.49 GiB，过去仅有两步训练/保存/重载记录。此次68行 CPU 重新分词最长10,546，低于模型配置的40,960位置上限；与8B编译的 input IDs、labels、反馈位置逐行相同。独立内存守护的四项CPU控制通过；真实4B训练设置启动前至少30 GiB可用内存、低于20 GiB停止本次自有进程，现约26 GiB而未启动：0权重加载、0更新、无真实梯度/保存重载结果。守护只是此次的风险控制，不构成模型能力或方法收益。CPU证明 SHA `efa9ef4a54bf41f0a2f647600de1df8b737707504ad4b9522b31b6ca5a36822b`；守护控制 SHA `4735a3c6432e859c54bc609ed7ff3de3e09a6c09ea333de364f60c7d13d67e09`。双端准备包34文件 SHA `2d18fa5d187abd3bcfc6e340e469a855f2d451569d917d4c516e0e193fc53cf0`，不含权重；监控异常与首次控制脚本错误均已保留。

## 尚未运行的扩样

`student_failure_expansion_v1`已冻结6来源×seed17/29×两历史策略的24份协议，真实文件读取准入20/24：clean05/06、look02/03/04。look01四份受现役reader的context-reserve拒绝范围限制，保留为压力来源；不是该数据无效。新模型、world、训练和目标root均未启动。

只有新student来源允许单值恢复seed17或29，协议、调用与cohort必须一致；原source/world仍17，其他旧来源规则不变。输入准备、纯读取准入、原生重放和模型运行分开记。当前先做[既有8B学习模型的新布局比较](ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)，不让上下文扩样取代学习证据。

## 早期记录定位

<a id="checkpoint-results"></a>
- [旧27B checkpoint开发对照](../../../docs/archive/2026-11-06_agent_research_context/alfworld_sources_through_20261108.md#checkpoint-results)。
<a id="multitask-context"></a>
- [三个任务的固定历史策略](../../../docs/archive/2026-11-06_agent_research_context/alfworld_sources_through_20261108.md#multitask-context)。
<a id="native-capability"></a>
- [合法动作接口与能力诊断](../../../docs/archive/2026-11-06_agent_research_context/alfworld_sources_through_20261108.md#native-capability)。

代码环境候选和时序查[代码纠正](CODE_SOURCE_CORRECTIONS.md#current)及[SymPy公开复现](ALFWORLD_LEARNING_RUNTIME.md#sympy-intersection)，不在此追加第二套代码日志。
