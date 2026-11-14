# ALFWorld：执行纠正与学习开发

> 历史批次2026-11-06至08，2026-11-14整理路由。本页保留已闭合监督/学习记录，96＋32及8现场四臂均闭合，旧“下一批”不作待办。后续R训练正向见[训练资产](ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)，现役机制与暂停状态见[知识索引](CONTINUATION_PROGRAM.md#mechanism-knowledge)及短计划。

四现场诊断与旧分账见[先导实验](ALFWORLD_CONTEXT_STUDY.md#teacher-pilot)；本页旧“下一步”保留当时上下文，现役行动以短计划为准。

## 监督来源速览

27B从头执行16/18、从12个学生现场恢复8/12；两者成功交集只有7组（4heat/2cool/1look）。普通/纠正轨迹分别67/68个接受动作；失败和全部形成费保留。完整导出、token标签、来源hash和教师成本见[已闭合监督材料](ALFWORLD_CONTEXT_STUDY.md#teacher-supervision)，不再默认加载全过程。

实际135个训练行及原请求已全核：历史均不参与loss；O从reset学习，R从失败现场学习，后者起始user含3个环境动作，不能等同运行期last3工具轮次。因此O/R目前识别训练方案整体差异；表示及信息条件的拆分留待稳定收益出现后。证据见[训练表示复核](ALFWORLD_LEARNING_RUNTIME.md#实际训练表示复核2026-11-07)，不改在途合同。

## 已闭合：完整历史强基线与来源纠正

普通/纠正轨迹成功交集为7个任务/布局（普通67动作/2,865监督tokens，纠正68/2,950）。按双方成功取交集是common-support条件分析；唯一clean纠正任务被排除，因此训练只含heat/cool/look三类，不能称覆盖全部失败。配对记录`recovery_supervision_v2/ordinary_recovery_pairing_v1.json` SHA `dc0f6b6a6c464b53c16d708e51ee33d0ba61157bbe351f7e678f782d4eba5fcf`。全部形成与失败成本不因筛选删除。

两臂使用同HF8B、seed17和新q/v LoRA r8/alpha16，各完成192次更新并保存/重载。合计2,270,472序列tokens、16,617监督tokens；普通/纠正训练用时1579.43/1600.13秒，监督tokens各8,239/8,378。同来源/初始化/更新数不等于完全等成本。原计划、实际receipt、旧工程失败和owned窗口恢复记录见[闭合训练](ALFWORLD_LEARNING_RUNTIME.md#learning-runtime-history)。

仅D使用owned18104研究窗口，共享35B/27B保持常驻，结束恢复原8B argv/cwd与健康。五臂统一绑定HF导出的BF16父模型（SHA `505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3`）；旧AWQ-compatible Q4不直接套新LoRA，旧成绩不作本批对照。坐标诊断、HF/adapter哈希和CPU导出证明只查[运行绑定](ALFWORLD_LEARNING_RUNTIME.md#deployment-bindings)。

同7组普通教师轨迹另备`reference_history_v1/BANK.json`（SHA `eca70c91e604aa1c35304121760b062203bfecc0a92dd2225997ada6ec073870`）：67接受动作和1次实际invalid_action，公开文本合计13216bytes；不造thought、不含heldout。选择仅用公开goal类别、同类public_text hash首项，缺类固定fallback；clean无训练例。这是同来源普通历史对照，不是完整ReAct复现或全量token匹配。

两次训练0步工程失败（初始化顺序与OOM）及定向文件缓存诊断见[闭合工程现场](ALFWORLD_LEARNING_RUNTIME.md#learning-runtime-history)；没有把它们计作学习负结果。

独立数据复核读取361份原SSE和135配对训练行，无差异；只允许7组暴露任务上的有限学习开发，不是训练器或泛化审定。`learning_comparison_v1/independent_data_review_v1.json` SHA `2cf11cceebef3c06caeb07ebd7f6b7a04807fd930c9a6abd21757ebd132859b8`。训练源码/CPU loss与梯度检查另行验证，不将mock通过冒充真实GPU训练。

## 新布局与第二环境

另冻结16个development-heldout任务：clean/heat/cool/look各4，16布局/UID；排除原28个已知布局。`heldout_pool_v1/POOL.json` SHA `5f1eb3820881d797867c8348e71559a57d339a753bb88ef5b7bf70530095be00`，资格SHA `3ff9f90bb2a254f38db43817d73df84b42095a818554d19199161deace9b3e65`；官方expert/native控制16/16通过，CPU89.53秒，无替换。仍是官方train来源的本地开发留出，不是跨来源或正式确认；expert轨迹为EVAL_ONLY，禁止进入训练。原18配额因可用heat/cool合计8布局而需9不可行，先改四类各4并冻结元数据匹配规则，再运行控制；原阻断证据保留。

五臂共同使用同HF父模型/actor/cap，分别报告12个训练已见类型任务和4个未在本轮SFT出现的clean非退化检查，以及整体16题；普通历史只用同7组公开轨迹，额外输入与形成成本分账。协议`learning_comparison_v1/hf_evaluation_v1/PROTOCOL.json` SHA `fc19b701ff61ad00e4884d8bd891c2e68d36ae5b582a0a6113a89c2647fa1bde`；启动前清除复制的旧prefix/三臂字段，原draft保留。每臂fresh进程、只加载对应adapter，实际加载状态另核验。`hf_evaluation_v1/RUN_v2`已闭合，frozen16结果保留。普通LoRA真实加载正确（scale1），但读取器误拒服务新增的空`task_name/prompt_prefix`字段，在任何普通任务生成前停止；原Q4已自动恢复，shared35/27不变。R2 RESULT SHA `6188e2ea570a1dadea6109bd2b65ecda7310966e9ca658a1907b00797b49bbcd`。`hf_evaluation_v1/RUN_v3`现已闭合剩余64次，状态`ALL_FIVE_ARMS_RETURNED`（RESULT SHA `debfb559fd6a4dea85d9180b536b16c9a024b69edf5680fe92a1ce266c5dae68`）；原Q4恢复完整进程身份PID372039/start_ticks1075796960，shared35/27不变。科学协议/权重/样本不变，冻结16条只计一次。首次启动竞态及来源见[工程现场](ALFWORLD_LEARNING_RUNTIME.md#learning-runtime-history)。

### 五臂闭合结果与判读

同HF的F/O/R/all7/top1总完成为7/7/10/7/6（各16题），主比较为6/6/7/5/4（各12题）；R相对O主比较只增1/12，95%描述区间[-16.7,+33.3]pp。27B直接执行为14/16、主比较11/12；保留纠正学习的正向开发信号，继续检验短历史与实际恢复。五臂完整费用、逐raw核验、独立复核、终态后长尾、27B参照及Django34570的33POST未修复现场，已原文归入[闭合结果与成本](ALFWORLD_LEARNING_RUNTIME.md#five-arm-results)，不在当前入口重复加载。

后续素材盘点只查官方ZIP成员与opaque hash：`learning_comparison_v1/NEXT_SOURCE_INVENTORY_V1.json` SHA `c236da94b5ebf37a523e9b396f9ce06ad4f00192fea8925f4495f5c2234bcbb6`。已有134个官方valid_unseen JSON/PDDL交集、134个独特game payload，与原18/新16池的game hash无交集；尚未检查全项目曝光、原生运行或专家兼容，不是第二环境或确认结果。不改当前16题，也不把该池用于训练。

定向来源核对补齐了训练7组的14份普通/纠正manifest身份：与134候选的task UID、完整family、layout、game hash交集均为空，但去掉布局后仍共享3种目标模板、9个候选。报告`learning_comparison_v1/NEXT_SOURCE_TRAINING_OVERLAP_V1.json` SHA `fa1d19a265ef5314f329c63d68119959cbef4a81f9fe7c39431b7ad58e2adf06`；未重验训练行或全项目暴露。候选134个trial只含47个family和4个布局，类型与布局部分共线；后续须按组设计，不能按134个独立样本报告。

**代码来源已实际采集。** Django12453→31051、SymPy21055→9384两对通过时序、原版/参考和回归控制，隔离入口及实际评分控制亦已通过；目标保持EVAL_ONLY。使用[同一代码入口](../run_contextbench_source.py)和冻结V4输入，不另开同源运行。闭合的选择、环境、接口修复与CPU控制过程原文归入[代码来源准备](ALFWORLD_LEARNING_RUNTIME.md#code-source-controls)，只按问题加载。

私有`code_source_expansion_v1/source_collection_sequence_v1/`持有启动快照`LAUNCH.json`（SHA `f54cfea3df16e37f87423a1f83ea8929461e1a96c102c665d458063ef0e7d997`）；owner PID1173985/start1080064615，脚本SHA `37bd142ef8e0cdbe09e899ed80da9e2933cfaa1b733abedbe90d1f60c338c172`。它须等主进程PID748995/start1077529568退出、96条闭合且原服务恢复，才逐题调用既有runner；每题48POST/1200秒，最多96POST，无自动重试。接续先查该目录events/RESULT及进程身份，不把等待快照当采集完成。若用户暂停，须同时取消主进程与此队列，核实各自及owned子进程退出，不能只暂停Goal。复用C四轮限定检查共11次工具调用后放行；实际CPU反例及取消控制通过，不替代后续真实raw审计。脚本/启动/审阅材料已双端私有镜像，启动时来源请求为0。

**上述主进程/队列现已退出。** Django source实际48转发、49次本地尝试（第49次HARD_CAP拒绝，未送模型），原receipt保留`GENERATION_FAULT`、序列保留`STOPPED_FOR_REVIEW`。D重读48原SSE核input481,736/output2,601/total484,337tokens、无未知usage；cache字段48条未知。模型重复搜索，candidate.diff为空；既有评分完整，F2P0/1、P2P5/5，不是合格成功纠正来源，不外推反馈学习失败。未增加容器或重跑Django。D据此人工释放原有未使用的SymPy48POST，仍不超过来源阶段原96帽；决策SHA `c80db134350e28af252f4ab7856551f6875e6d2ebb74b74c5cde16d57dabd717`，`MANUAL_SYMPY_LAUNCH_V1.json` SHA `e5dfa193743cb52e1233a12029940c85d1e69f0699597ddda04a1cc1789e088a`，owner PID1232740/start1080540634。接续只核此源receipt与owner，不再启动旧队列；暂停时核身份并停止该owner及其container.cid记录的owned容器，保留共享模型。

**来源批已闭合，无在途模型请求。** SymPy同样48转发/49尝试，cap拒绝第49次，空补丁，原评分F2P0/1、P2P13/13；receipt SHA `57614a483a559af171b8cee6411b7c9e7a88ab1fea95f875fceb735155173b94`，上述manual owner亦已退出。其usage元数据为input624,225/output2,985/total627,210，原SSE尸检单独核验。两来源共96实际模型POST、98次本地尝试，total1,111,547tokens，原96模型帽全部用尽，没有预算重置。暂没有合格成功纠正；优先核角色/反馈，再考虑仅用source历史参考patch构造明确reference-assisted纠正，不动未来target gold、不把辅助来源冒充自主成功。

<a id="source-tool-contract"></a>
代码来源及教师纠正已按主题移至[独立记录](CODE_SOURCE_CORRECTIONS.md#current)；原段完整保留在该页历史部分。

[追加前缀加载器](../alfworld_recovery_source.py)显式绑定旧protocol/cohort/manifest/receipt/world哈希并分开新旧额度，联合聚焦38 tests/19 subtests通过。现已对8个合格失败前缀实际重放：322个接受动作及全部公开reset/逐步状态均相等，8个owned world均关闭，模型/训练0、环境段墙时合计23.35秒。5个heat/cool/look为主比较，3个clean作诊断；7成功与1零动作来源被拒绝。`additional_recovery_v1/NATIVE_REPLAY_RUN_V1/RESULT.json` SHA `32b93d6d436d973d9e2e7ed53d9db6e6d444aefe581589dfe3d9f5fcb8c2577f`；来源协议SHA `466815d7b75026d3605f88e3504a4c54502792878dd13b90e4697e3b57a567d4`。接受动作不保证有用进度；公开重放不证明全部隐藏状态等价。当时prepare尚未接入、未做学习恢复比较，未改在途96回合组件；后续隔离接入状态见下文。8个来源原本都是无经验ordinary_reset失败，不能改称旧skill失效现场。其完整/近期3步的单user提示实测为1,014–5,027 / 681–1,238 HF tokens（不含OpenCode额外输入）；`PROMPT_LENGTH_V1.json` SHA `72ae67c334ddf23a7dc8afd8a46cd6534b34558f134472acdbe6ea37bf72b8b5`，仅CPU计数。下一恢复阶段另给32 POST/600秒，world总100步、各现场尚余27–92步；旧形成费只计一次，不按每臂重收。

## 下一批：六组而非重复训练

同一暴露开发面板，16个任务/布局；primary12为heat/cool/look，clean4未在本轮SFT出现。零新增训练；各臂同父模型、种子及额度。完整协议、修正链、逐raw复算和旧回执只按需读[六组实验记录](ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#setup-and-arm-records)。

| 臂 | primary12 | clean4 | overall16 | 实际POST |
| --- | --- | --- | --- | --- |
| Frozen last3 | 2/12 | 1/4 | 3/16 | 1,312 |
| Ordinary last3 | 4/12 | 0/4 | 4/16 | 1,185 |
| Ordinary full | 5/12 | 1/4 | 6/16 | 640 |
| Recovery full | 7/12 | 4/4 | 11/16 | 387 |
| Recovery last3 | 4/12 | 3/4 | 7/16 | 1,059 |
| All7 history last3 | 4/12 | 2/4 | 6/16 | 935 |

完整历史R相对O主比较增2/12，95%描述区间[-8.33,+41.67]pp；短历史R/O/All7均4/12。交互为-16.67pp，区间[-41.67,+8.33]pp，尚未分离稳定学习增量或历史交互。R短历史7个成功均在R完整历史11个成功内，后者POST、总输入及noncached均更低；不据此训练选择器。旧96中All7只测last3，不能把该臂与Rfull直接当同窗口比较；完整历史补充已在下文闭合。冻结六对与成本见[全批闭合](ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#all96-results)；27B直接执行14/16及形成/训练费继续作参照，独立代码来源采集已接续。

**完整历史32条已闭合、复核及恢复。** 新F full为primary5/12、clean1/4、整体6/16；All7 full为5/12、2/4、7/16。旧R full为7/12、4/4、11/16，对两个匹配固定基线的primary差均+16.67pp、描述区间[0,41.67]；整体差分别+31.25/+25pp。保留了值得后续验证的点估计残差，不能由clean或整体替代primary结论，也未分离纯反馈内容。逐项结果、四组区间和费用见[完整历史对照](ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#full-baseline-extension)。新增1,022POST/13,184,363tokens，原始SSE/交付/原生末态及当前恢复身份均已核；C独立重算一致。PID1301996已退出，旧raw及源码快照已双端归档。

**8个保留现场四臂已闭合；以下保留启动合同。** 原隔离分支69bf6b00已并入main7af454e0，只复用既有study/controller。F/O/R均完整公开前缀、无额外经验；Frozen All7另给同7普通教师轨迹。共32条、独立上限1,024POST，各32POST/600秒/64M，world总100、按现场剩27–92步；primary5、clean3、整体8。98 tests/368 subtests及V2实际计划检查通过，C限定条件通过（SHA `8acd4d55b3d9264f338d1cb39dd72c7770220339f0a73481c1a9d79866057bf3`），旧数量文字已更正。计划SHA `64cd1bd4d6ae29ec3e1660b04de8f35c21610cfe52f965e36b40cef8b85d4984`；已绑定补充32闭合结果6966f16b的最新恢复身份。私有`additional_recovery_v1/RECOVERY_RUN_V1`原owner PID1379062/start_ticks1081725810已退出，launch SHA `afb24e3e9480b9a79513c16e745e6b85487f863b1f61ee7a43bafc7cc9a93a4a`；32条已闭合，R的唯一成功被All7覆盖，见[结果与停止裁决](ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#preserved-recovery-results)。临时树和已合并支线已删除，原7历史树保留。

八个ALF来源回执唯一去重：旧614POST、input9,250,602（cache子集9,105,499、noncached145,103）、output26,614、total9,277,216tokens，全部已计在原frozen16账，不能再次或按四臂重复追加。`RECOVERY_SOURCE_COST_V1.json` SHA `fc07268eb016af5bf5022839da5113710f3878174724aa9c0edc693ca4313364`。接入源码/协议/审阅/日志27成员薄包双端核验，SHA `4dc1f08fda481a639a02b2699b3ff1ad68535799e0e91e098f8e72f3d430e3c4`。这是旧失败条件池的恢复诊断，不是新任务确认或旧skill失效实验。

<a id="两项改变下一步的发现"></a>
## 机制线索与下一阶段准备

**代码来源的具体问题（执行前公开题面判读）**：Django12453→31051同涉序列化依赖，但前者公开建议反序列化事务，后者区分普通外键、自然键与循环依赖；SymPy21055→9384同为refine，前者参数简化，后者Piecewise分支条件。它们可检验相关旧经验的适用边界，不能只用关键词相同当可迁移证据。D-only私有`code_source_expansion_v1/SOURCE_PAIR_PUBLIC_MECHANISMS_V1.json` SHA `c04a7f8822f483b5a4caea53a4fdd6ecce684e32dc74ebb23a5cd9c99ae7f0d8`绑定公开题面与既定source输入；不含新结果。后续经验生成只能读source证据，不能读这份包含目标解释的笔记；无历史、普通摘要和不重复旧补丁检查仍作强简单对照。

**持续短历史需要与学习增量分开比较。** 旧drop_recent仅首次交接保留3条公共动作，之后OpenCode历史继续增长；闭合样例第74次转发仍含73个工具回合。新[纯投影器](../alfworld_context_projection.py)逐次保留所有系统/用户目标及最近3个完整工具回合，不造摘要；离线核对F/O的1379份闭合请求后，已接入Relay且在上述真实body核实生效。投影发生在采样合入后、body序列化/计费/记录前；六组结果闭合后再判断短历史能否解释学习差异。

**最终成功不保证每个接受动作适合作为正监督。** 同7组O67/R68动作的精确LCS合计36；其余差异不自动算错误。针对三条暴露训练轨迹，另做6个无模型native控制（固定源前缀与后继动作，事后诊断）：

| 训练现场 | 原R接受动作/结果 | 删除预选开头片段后 | 观察 |
| --- | --- | --- | --- |
| cool_02，目标pan | 19/won | 删前10步pot流程，9/won | 该片段不是此固定后继序列达标所必需 |
| heat_02，目标hot tomato | 13/won | 删开头cool，12/won | 此次cool可省略 |
| heat_05，目标cup，原持bowl | 6/won | 删放bowl，下一take cup报invalid_action | 此固定后继须先释放持物 |

六次原生reset/源前缀均逐步公开状态相等；共227接受动作，其中168为源重放、59为新探针，环境对照墙时24.21秒、模型/训练/judge调用0。RESULT位于`learning_comparison_v1/teacher_trace_counterfactual_v1/RUN_v1/RESULT.json`，SHA `32945e3f343f3fa25f196a737fe3d77b9b7484ae8391ff89866bb3788506821e`。只证明固定轨迹下这三处依赖，不证明全局最优、一般因果规则或过滤后学习收益。固定后继带有教师后验计划，删除验证不证明部署时无需相应信息；搜索/观察须保留或用真实actor续做复验。后续若试原生反事实监督mask，比较须含目标/持物规则、随机mask及普通混合rehearsal。46成员薄包已双端核验，SHA `6934a6cd1759de698a2f2d01d2b507ba70e3df194dc4aede8a1c5285465a6ddf`；不含在途历史输出。

**旧历史选择空间已复算。** 在闭合F/all7的同16题单次实现中，all7相对F修复clean_02/look_04，同时丢失look_01/heat_02；整体均7/16，事后逐题oracle并集9/16。主比较12题为F6、all7 5、oracle7；按公开goal类别事后取较好固定臂仍为6。故当前主面板的观测选择上界只多1/12，尚不值得据此训练复杂选择器。`hf_evaluation_v1/CLOSED_HISTORY_CHOICE_SPACE_V1.json` SHA `2c91f9dc747a53b1e307d2b0a1f52bdfc7e7ae0c518f809de1d8138bb046e1ed`；逐receipt hash已核。这是暴露开发的事后观察上界，不是稳定个体处理效应或可部署oracle，不用这些EVAL_ONLY目标输出训练。

**闭合短历史轨迹尸检。** 本机读取已核验包中16份world日志：979个接受动作，13个失败中9个至少2/3观察再次出现；全16条均无相邻同动作重复。观察键仅含observation/score/won及排序后的合法动作，排除计步/done；重复公开观察不证明隐藏状态相同或动作无用。clean_01在look/examine之间交替，cool_01反复往返fridge/diningtable，说明只查连续同动作会漏掉本批循环。私有`evidence_packets_20261106/frozen_short_trajectory_autopsy_v1.json` SHA `419b47505b0269573239b6b67862f1887c785d460554d4b351da3600697fb3fb`。这是下一恢复触发器的开发线索，不把它当截短的独立因果证明，不改在途臂。

**公开反馈触发器的开发回放。** 再核旧五臂80条及新frozen_last3 16条闭合轨迹（仍只有同16个任务/布局簇）：最近12次公开观察（含初始reset）中同一观察出现3次，覆盖23/56个最终失败、0/40个最终成功；连续3次同动作只覆盖1/56、0/40。固定第12步报警覆盖43/56失败，也在12/40个最终成功的原轨迹上报警。旧O/R完整历史中该循环信号分别出现于4/9和0/6个失败；R的6条失败仍有34–70步，包含持续搜索与错误处理操作，不能用“没有近期循环”替代成功。私有`public_feedback_signal_replay_v1.json` SHA `06f9cfd3e003a05553c6d5728422719e7c8c1da08141581b99d22d6ad2a25a64`。信号只用观察文本与排序合法动作，不读取隐藏state/gold；这是已暴露数据上的事后报警描述，未执行干预、未证明恢复效用，且不以这些EVAL_ONLY输出训练。它支持下一轮保留循环触发、固定步数与语义反馈三类简单对照，不把96条当96独立任务。

**六组分析入口已静态验收。** 复用[现有分析器](../summarize_alfworld_learning.py)新增显式runtime模式，不新建日期runner；冻结`1dd75aa8`仅改分析器/测试，GB10实跑57 tests通过。原C复核六方向、任务内交互、六臂共同抽样和未知cache，限定PASS；私有`SUMMARIZER_C_SCOPED_REVIEW_V1.json`记录其范围。D另用真实已闭合frozen_last3的16行重核新native见证及9,284个绑定，0差异，check SHA `a5f66037be4df9ad67a2dbb33b3904b33feb943a4102514d3e2046d74b1f42a1`。全96仍无终态RESULT，不生成真实总表；待完整批次、还原及成本闭合才出六对和交互描述区间。旧API保持，形成/训练费与本轮评测分账。审阅与触发器回放薄包3成员已双端核验，SHA `1a7b248f3a50cc1337f8038ffe881214fd3ce89936047095e414c8b3a7348a6a`。

**后续独立来源容量。** 对同两份已绑定官方ALF档案只查2233条四类任务元数据，不打开expert轨迹/新环境：已选布局并集44个，train尚余287题/33布局，但只有clean/look，heat/cool新布局为0；valid_unseen尚余93题，却仅FloorPlan10/308/424三组。因而本地快照不能再按四类各3个新布局扩成12个独立组；未见题目与未见布局必须分列，不能把93题当93独立房间。`learning_comparison_v1/NEXT_SOURCE_CAPACITY_V1.json` SHA `0e811b31062fdc59cc4f6345214a30c408b7092ae5298565eba93db2bf75d5e8`。先完成当前实际比较与两code来源，再以自然代码项目扩样；若复用已见ALF布局，须明确改为task-family迁移问题。现有代码元数据21对覆盖6项目；另核399条source/target的标准化问题与repo/base/patch/test身份，未发现原20个已声明ID的同问题别名命中或完整重复组，全部20ID均可核；这不认证全项目未曝光。`code_source_expansion_v1/METADATA_IDENTITY_AUDIT_V1.json` SHA `29a710f50f860382bec467aab8297ee2d964cebf557e6ce99a5d201fd9ea0783`。两份元数据JSON已镜像，0模型/环境/训练。

**跨项目下一波只完成时序核验。** 冻结另一4项目各1对的元数据选择（scikit-learn限定2020后以复用现代依赖，再按target hash选题），12次官方只读HTTP全部保留并复核方向：Matplotlib25332→25352、scikit-learn25638→25637、Sphinx8282→8127均源修复merge为目标base祖先；Seaborn3190→3203源修复晚于目标题且不在目标base中，按当前时序门拒绝，不改阈值找信号。前三对分别涉及pickle修复后的Grouper实现替换、nullable dtype从unique_labels到LabelBinarizer的扩展、overload类型提示到ellipsis引用解析；均只作问题关系，不宣称旧经验已有效/失效。dataset ID不总是上游PR号：后两target实际PR为25813/9104，依规范URL与commit核，不按ID猜。`code_source_expansion_v1/SECOND_WAVE_ANCESTRY_V1/RESULT.json` SHA `25d2264f52836d719897bca05f8dceb4b30f6024a90e2036fa1de47b5358a107`。14成员薄包已镜像，SHA `d8ab365f92f61d93dec5d1fd492e6eb7fd35f463d4da7d8027eb7bea63967de1`；本波0测试/环境/模型/训练，尚未下载新项目或开放actor。先实际采集现有两source，不把这3对时序通过当新经验/方法证据。


**Matplotlib新来源另按主题加载。** [新pair资格与真实采集](MATPLOTLIB_QUALIFICATION_20261106.md#new-source-pair)保留原缓存/V1–V3失败链及逐字迁移hash；不再把代码任务的详情默认装入本ALF记录。

## 方法重叠与下一验证

Sentry已有失败触发与验证后入库，EMG已有失败/成功轨迹匹配提取知识，STeP已有教师纠正与partial masking；ACE/AgentFold/DGRR等也覆盖局部更新、折叠及依赖撤回。原文方法核对与其余近邻完整保留于[按需精读](ALFWORLD_CONTEXT_STUDY.md#mechanism-reading)。当前SFT是监督来源/能力对照，不是上述方法的新名字；独立贡献仍待实际比较。另核[Memento](https://arxiv.org/html/2611.00244v1)在静态书籍QA中已有学习笔记/上下文重建，[SkillApt](https://arxiv.org/html/2609.26863v1)的一般形式已有状态、模型与成本条件效用；STeP混合普通/纠正监督，当前纯O/R小LoRA不是其复现。不能仅因某公开实现较窄而声称状态选择或混合纠正为新机制。

## 本轮判读与训练对照取舍

**记忆/上下文近邻补核（2026-11-07，方法与设置已读、代码成绩未复现）**：[MemGen §4–5](https://arxiv.org/html/2509.24704v1)以LoRA触发器和潜在记忆配合冻结reasoner，含ALFWorld与跨域评测；[AgeMem §3–4](https://arxiv.org/html/2601.01885v1)已用策略内工具学习长期/短期记忆操作，含ALFWorld等五任务；[CADOC §2–5](https://arxiv.org/html/2609.37012v1)已用可精确查回的Card及缓存重建成本调度批量编辑，并做固定轨迹和实际任务链评价。故不以学习上下文、换ALFWorld或发现缓存失效单独立贡献。若继续研究压缩，应加入“近期历史＋精确查回旧记录”对照，并计查回费；不改现96协议。私有`MEMORY_CONTEXT_NEIGHBORS_V1.json` SHA `795db6815fd35c272e408a08b3f0b588c2d3fa20ccee5c0be62b57380a30312b`保留比较范围。

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：8现场四臂均闭合，primary各0/5，R与All7只同一clean题成功；预定固定基线覆盖R全部成功。Recommendation：停止扩同7来源恢复配方，不在该池训练选择器；先增加独立任务与可执行纠正来源。UNVERIFIED：纯反馈内容效应、跨来源迁移及环境动力学变化。Conditions：旧reset开发信号单独保留；6次上下文守卫与动作/请求限制不抹除，不将八个旧失败现场解释为总体等效。

新增64条闭合raw薄包已在GB10与本机逐一核验14,052成员，SHA `0995fa01149373591fea14cea126a9112f229430f1a2e8558c554acb2ac2c9b0`（manifest SHA `9018cfabed3d9e2113080a7dc01cb36f0fda9acf2178a4594e3020ef0f6db733`）；与先前frozen16包共同覆盖80条，未复制仍写入的restore服务日志。历史baseline、训练/部署及frozen16薄包的镜像hash见[私有资产](ALFWORLD_LEARNING_RUNTIME.md#private-packets)，不复制在途服务日志。

代码资格私有包`code_development_qualification_v1_20261107.tar.gz`已双端逐成员核验76项，2,704,064bytes、SHA `267bf996950f25cadfddd2e7a5390d761ad6b8d36b074a98bc44d3a79f847532`；保留两轮原结果、命令、逐test状态、错误与注册表，未打包完整candidate/gold树，不是公开artifact。

后续两source与8个保留现场的闭合证据包`source_pairs_and_preserved_states_v1_20261107.tar.gz`已双端逐成员核验88项，17,256,211bytes、SHA `2eec08f3e78d52038472e8f62bd0d69b33676961fb1f3a42869b54742e487ae0`（manifest SHA `4a5647676e2cc8277ec6fc0c82cee27c5dcb624eb73bfd74c95d8409718118aa`）。本机另逐条核8个公开重放日志的322动作及回执hash；不含在途96回合或完整base/gold工作树，不作actor输入。

六组及补充32的原始包与费用见[闭合成本](ALFWORLD_RUNTIME_CONTEXT_COMPARISON.md#closed-costs)。全96完成时小计13,357 HTTP / 131,480,358tokens；加入补充32后已闭合小计14,379 / 144,664,721，仅新增1,022/13,184,363一次。在途恢复、代码来源、训练、研发Agent及历史差额另账，不是项目总成本。

source评分控制薄包已双端核验59项、18,178bytes，SHA `2e6a7066eed4486a240c42d7db9ddc4fc41a35741331f14d78f2d303758fb42e`；本机另核4份base/gold回执的完整标签、预期失败/通过及清理，check SHA `2a260602c18411b07f63eba05be1e1ceb96e04be1bc5598461ba52a2bd08d428`。不含work/baseline/gold树，未公开。
