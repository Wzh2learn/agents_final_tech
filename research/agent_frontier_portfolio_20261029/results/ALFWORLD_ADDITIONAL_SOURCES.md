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
## 新18个开发源：资格完成，采集中

新增clean9/look9均来自TRAIN；UID、family、layout/group、game hash互异，排除旧18/16/运行池、新12、7训练源、2上游源及登记的保留身份。筛后有clean55条/11布局、look103条/10布局，按冻结身份hash取18，不按结果换样。数字布局不同不证明语义独立，完整外部/预训练曝光仍未知。

两份官方ZIP及36个选中成员实际hash相符；18/18专家控制通过，共247动作、串行48.59秒。核原生观察/score/done/won、reset合法动作、同seed重置/名称映射；D另逐项通过现役池读取器。资格阶段无模型、HTTP、训练或容器调用，不提供actor失败或学习成绩；专家轨迹只在私有评价侧。

私有根`progress_feedback_development_v1/native_pool_v1/`：`POOL.json` SHA `7fe85fb7564b1e0eba908e1279522a84fefce0dd61b80f2c75ad646ec992c6fe`，`qualification.json` SHA `581735ebf62a710c1a8819a8a50a3ac6f916b45129f62514ad3d149d5c9b874c`。双端包`progress_feedback18_native_qualified_v1_20261109.tar.gz`为305,768bytes/170文件，SHA `2ff52de6a5a1abdcdca89f9aca75e8270e8f1bbe07c1a4a779830545bdf7754e`；不含完整ZIP或模型。

**当前真实采集。** 同级`source_collection_v1/SOURCE_PLAN_V2.json` SHA `016a18104ff901a22b40b4f636c4f705a96a0511a7ad9bce47746a2094ba34a0`；执行器V2 SHA `719b34ada6bc7126d0f656057beb7f7a3ae8668b1ae5666b160135053d76f532`，D release SHA `2f7a8e6f54649316e1dffd80a57dfed033c9de2d6e5daa24f44959e360544fd9`。C固定快照核查后，D实跑22项CPU控制通过；它们不是模型/原生成绩。2026-11-09启动`RUN_V1`，controller PID2543943/birth1091452816，实际argv与`CONTROLLER_TICKET_V1.json`一致；观察超时先查此句柄，不另起批次。

F共同BF16无LoRA、全7普通历史、seed17/温度0.2、thinking关闭、32K/8192、required及原生终态门。首题实际wire已核，incoming auto与转发required分记，已出现原生接受动作；尚无批次成功率。固定18题、不替换失败，每题128 POST/100动作/64MB、actor阶段1800秒（不含prepare/preflight）；合计2304 POST/75,497,472tokens为预留上界，不是实际消耗。7080秒停止科研转清理、7200秒为含120秒恢复预留的目标，安全恢复可越目标并单列。未知usage/接口错停队列，已核cap可继续并保留真实won。闭合前不宣称已恢复Q4/解锁；不训练、教师或judge。

**用途限定。** 本批是source development，不是方法确认。零动作、纯接口失败和上下文耗尽不自动标为经验前提错误；下游另核非终态、公开动作/反馈、剩余动作，并区分仅导航与物体状态变化，之后才构造同前缀保留/撤回/修订对照。134 valid_unseen仍保留。

输入及发车绑定已双端归档：`progress_feedback18_source_inputs_v2_20261109.tar.gz`，472,697bytes/97文件，SHA `179f8f6960a9027fc240c17cb6253aa6649a596215fa3b3eb2adb6a699aaec18`；不含本批在途输出，闭合结果另核。

<a id="action-channel"></a>
## 首响应通道对照：不是任务成功

复用B6的01/03/05实际首请求，同BF16/解码，仅改`tool_choice: auto→required`。新3/3返回schema合规bash调用，旧3/3为无工具的stop；均无length。CLI形状正确，但01/03的动作不在各自源初始合法列表，05在；未执行任何工具或world，不能推定任务改善，也不将解码约束当纯因果工具。

新增3 POST：input24,009/output155，共24,164tokens，cached6,619为input子集；窗口51.38秒，训练/judge为0。C独立核请求、3 SSE、usage/schema/字节及公开reset；D另核Q4恢复身份、35/27和锁释放。当前私有`ACTION_CHANNEL_REQUIRED_V1/D_C_CLOSEOUT_V1.json` SHA `401c0c8d112a8f0d1fade3f316c634ed9337251843c868ce78c394ab070ba6ee`。双端包`action_channel3_closed_v1_20261109.tar.gz`为365,364bytes/102文件，SHA `ef5916660ab9d0d26ee0e713633460fedf64358e55dc54f05849427b6677d7c8`。

新协议以显式`action_channel=required`冻结执行采样，另记CBC构造采样；缺省/auto保留旧路径。required不替代`runtime_controls.native_terminal_stop=true`。使用新组件epoch，旧raw/评分不重算；真实episode见上方在途批次。[首响应CPU准备/解析](../action_channel_probe.py)不执行工具。

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
