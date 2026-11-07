# ALFWorld：执行纠正与学习开发

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。同父模型五臂80回合已闭合；纠正SFT有正向开发信号，27B直接执行参照已闭合，尚无独立方法贡献。

四现场能力诊断与旧分账已移至[已关闭的先导实验](ALFWORLD_CONTEXT_STUDY.md#teacher-pilot)；本页保留当前结果和下一动作。

## 监督来源速览

27B从头执行16/18、从12个学生现场恢复8/12；两者成功交集只有7组（4heat/2cool/1look）。普通/纠正轨迹分别67/68个接受动作；失败和全部形成费保留。完整导出、token标签、来源hash和教师成本见[已闭合监督材料](ALFWORLD_CONTEXT_STUDY.md#teacher-supervision)，不再默认加载全过程。

## 当前动作：六组新批次与代码任务资格

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

**代码经验来源已准备。** Django12453→31051、SymPy21055→9384两对通过时序、原版/参考和回归控制，隔离入口及实际评分控制亦已通过；source真实轨迹仍待主模型窗口，目标保持EVAL_ONLY。使用[同一代码入口](../run_contextbench_source.py)和冻结V4输入，不再扩接口。闭合的选择、环境、接口修复与CPU控制过程原文归入[代码来源准备](ALFWORLD_LEARNING_RUNTIME.md#code-source-controls)，只按问题加载。

[追加前缀加载器](../alfworld_recovery_source.py)显式绑定旧protocol/cohort/manifest/receipt/world哈希并分开新旧额度，联合聚焦38 tests/19 subtests通过。现已对8个合格失败前缀实际重放：322个接受动作及全部公开reset/逐步状态均相等，8个owned world均关闭，模型/训练0、环境段墙时合计23.35秒。5个heat/cool/look为主比较，3个clean作诊断；7成功与1零动作来源被拒绝。`additional_recovery_v1/NATIVE_REPLAY_RUN_V1/RESULT.json` SHA `32b93d6d436d973d9e2e7ed53d9db6e6d444aefe581589dfe3d9f5fcb8c2577f`；来源协议SHA `466815d7b75026d3605f88e3504a4c54502792878dd13b90e4697e3b57a567d4`。接受动作不保证有用进度；公开重放不证明全部隐藏状态等价。当前prepare未接入、未做学习恢复比较，不改在途96回合组件。8个来源原本都是无经验ordinary_reset失败，不能改称旧skill失效现场。其完整/近期3步的单user提示实测为1,014–5,027 / 681–1,238 HF tokens（不含OpenCode额外输入）；`PROMPT_LENGTH_V1.json` SHA `72ae67c334ddf23a7dc8afd8a46cd6534b34558f134472acdbe6ea37bf72b8b5`，仅CPU计数。下一恢复阶段另给32 POST/600秒，world总100步、各现场尚余27–92步；旧形成费只计一次，不按每臂重收。

## 下一批：六组而非重复训练

采用C协议审阅给出的96回合精简设计：O/R各做完整与持续last3工具回合，另含frozen_last3和all7_last3；同暴露16题、primary12和clean4不变，0继承旧episode、0新增训练。重点同时报告R-O两条件的差值、配对交互及R对两个简单短历史基线，不能只看交互或挑有利对照。last3保留全部系统/用户/来源历史锚，不是固定总token或3条world动作。`runtime_context_baselines_v1/PLAN_V2.json` SHA `49b44eaa69c623dc1c544925c779620039c7c00b39d77ea029b8cbbc859697be`；分析合同SHA `465faabb09a40cc9ad291ecbd9032e6fa08efec3bbebb58b09edb1e2a6b95dfc`。原128草案和原文字节修正链均保留，未实际运行。

新actor/taskpool代码导致旧pool精确代码绑定失效，未放松守卫或改旧receipt；同16资产在新根`pool_v2`真实重做16/16零模型expert/native控制，90.92秒，题目/UID/layout/game/traj及公开reset均与旧池一致，不计新样本。新POOL SHA `b922dd1a108754f31d862a56bd97eb4cee4e665be6b59279b4e8c7433a465b64`、qualification SHA `304e38e4b927f274bcf7e7b72f8071820dcde0e30da1e6cd8d3337f001adaaed`。新witness还对旧80份实际native记录全量解析匹配，SHA `e514868d57713f23e5d6a3e121cd6be99c4fc18dd346cee9519691747f579967`。

独立Terra/max预启动审阅发现并复现C1（共享身份异常挡住可安全尝试的原Q4恢复）和C2（cap/终态标志掩盖异常退出）。同一A续接修正：保护异常保留且独立恢复安全owned实例；137/-9拒绝；exit0/1都核raw SHA及顶层错误，只有匹配实际403/409拒绝证据才作为正常gate，普通工具错误反馈保留。V1/V2原回执均保留，同一C限定复核V3放行（SHA `7677c9d8dfd3ac9587487ef1746c38c5b59828c90246b0ebc3a5de0833c99661`），没有另起Agent重做实现。root远端实际133tests/380subtests通过；4个actor/pool组件未因审阅修正再变，未重做native资格。

代码已合并；driver SHA `ce8f29296929a120f293a107f6d8612d917aea4f76b426ee7dd619070c16ad7d`。旧源码和原五臂费用保持，ROOT闭合源码/C薄包已双端核验18成员，SHA `a10e86f96986a16c6ca6c027df9c75750158252239665083f8e4b9639c60a60a`。预启动检查为纯CPU/假数据及旧native档案核验，不证明实际409或方法效果。

`RUN_V2`在终态409重试时受控停止：clean_01上限失败、look_01原生成功，实际136POST/613,202tokens与原输出全部保留。400永久终止响应经真实OpenCode假接口及GB10聚焦136tests/389subtests验证；原Q4已恢复，35/27不变。接口事故、完整成本与双端私有镜像见[闭合运行记录](ALFWORLD_LEARNING_RUNTIME.md#terminal-retry-20261107)，不当作学习方法负结果。

现已从固定源码`8fcfc342`启动`runtime_context_baselines_v1/RUN_V3`（PID748995/start1077529568），使用新attempt14–19、0继承旧回合；同六臂/16题/权重/种子/caps及原统计对比。`PLAN_V3.json` SHA `3e7d9814c12a96fb1723977f252278b54527d61cd8f622330974710ad446a8d1`，分析合同SHA `f43382c981d691e123130b4d1a320cd447e920fa6a9bccd6ea1c71eced987f82`；明确记录旧2题结果已知，不是独立确认。新精确源码绑定的同16资产native/expert复验16/16、142.23秒、0模型；pool_v3 SHA `afe5d0deffa3380b34b39bbc398df10c774b51fd164a8cb4b88dbe632cb784ad`。同一C限定代码审阅无阻断，回执SHA `d8826d2f4ffa5f32f476916580093abd3407e445ef01780b7a0fcaeedc709557`。已实际核look_01在5动作/8POST后36.35秒自然收尾，新增1次终态拒绝即exit1，raw为400/Bad Request/isRetryable=false，native won保持；其receipt SHA `c4c84f79bc74aa810b21a484cf3d8cebb46fc18e33c506e96b80bc18e2b9044c`。全96结果尚待闭合。

**本批首臂已闭合，其他臂仍运行。** frozen_last3为3/16 won（主比较2/12、clean1/4），1,312实际POST；输入6,546,720、cached子集5,418,388、输出56,154tokens，非缓存输入1,128,332。旧frozen full为7/16、主比较6/12，输入10,184,855但非缓存仅190,669；控制器版本不同，不能把跨版本差全归因于截短。D已在本机对16条native终态和全部1,312份原SSE的hash/usage/cache重新核算，0差异；1,307 tool_calls、5 stop、0 length。独立check SHA `aa671380ea16f694c9afff9713be11d4ecf8975728cbb04b10a8fbde9ad39729`。闭合摘要`runtime_context_baselines_v1/FROZEN_LAST3_CLOSED_V1.json` SHA `94370c4da5763a9f497020391e2c5dc6f63c5c8db3b34cbf71f8f6ecd9391f38`。当前观察已不支持把持续last3默认视为更强、更省计算的策略；完整历史须保留作恢复对照，仍待O/R同协议对比和全批裁决。

**本批第二臂已闭合。** ordinary_last3为4/16 won（primary4/12、clean0/4）；与同批frozen_last3的3/16并列作补充描述，原六对R/O和交互仍待完整批次。配对新增cool_02/heat_02/heat_04，损失look_01/clean_02。其12条失败中9条触发此前的最近12观察三次重访信号，4条成功均未触发，连续三次同动作仍为0。实际1,185 POST；input5,866,422、cached子集4,795,157、noncached1,071,265、output50,103，total5,916,525tokens。1,181 tool_calls、4 stop、0 length；episode墙时合计6,497.96秒，不作隔离硬件下的因果耗时比较。D重读两完整短历史臂共2,497份原SSE并核native/hash/usage/cache，0差异；`FROZEN_ORDINARY_LAST3_CLOSED_V1.json` SHA `85bb2106295c53ba2753f4d2b855d0c170a501133da9176688c4c4e0063ce574`。新ordinary16原始包又在本机逐成员及SSE独立核验，本机check SHA `bf8b9137ecb81178e728443b039e0ecdc31c590fc570bdc5319404868445fb9d`。本次仅只读分析，完整历史与R臂继续原设置，不训练或改在途组件。

<a id="两项改变下一步的发现"></a>
## 机制线索与下一阶段准备

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

## 方法重叠与下一验证

Sentry已有失败触发与验证后入库，EMG已有失败/成功轨迹匹配提取知识，STeP已有教师纠正与partial masking；ACE/AgentFold/DGRR等也覆盖局部更新、折叠及依赖撤回。原文方法核对与其余近邻完整保留于[按需精读](ALFWORLD_CONTEXT_STUDY.md#mechanism-reading)。当前SFT是监督来源/能力对照，不是上述方法的新名字；独立贡献仍待实际比较。另核[Memento](https://arxiv.org/html/2611.00244v1)已有学习笔记/上下文重建，[SkillApt](https://arxiv.org/html/2609.26863v1)的一般形式已有状态、模型与成本条件效用；STeP混合普通/纠正监督，当前纯O/R小LoRA不是其复现。不能仅因某公开实现较窄而声称状态选择或混合纠正为新机制。

## 本轮判读与训练对照取舍

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：同HF的F/O/R/all7/top1为7/7/10/7/6（各16题），primary为6/6/7/5/4（各12题）；UNVERIFIED：纠正监督相对等源普通成功SFT的增益是否可重复，以及持续短历史能否解释它。Recommendation：先统一工程停止门、比较执行全程的K3与完整历史；若R仍有残差，再扩独立纠正来源并比较普通混合rehearsal、可见目标/持物规则和反馈衍生监督。Conditions：接受动作不等于最优动作；同任务两类轨迹不算两个来源。Risk/exit：若简单goal/合法动作/循环控制已解释收益，停止复杂学习候选；保留形成与失败总成本，不让训练内存资格阻塞独立任务。First action：六组last3对照闭合后，先以现有O/R权重比较同一保留现场的实际恢复，再决定新训练；已重放8现场、两对代码source/target资格均可复用。O/R必须同历史表示、目标、公共反馈及新增预算；reset参照不能在新增world步数不同的情况下充当状态特异性的因果对照。

新增64条闭合raw薄包已在GB10与本机逐一核验14,052成员，SHA `0995fa01149373591fea14cea126a9112f229430f1a2e8558c554acb2ac2c9b0`（manifest SHA `9018cfabed3d9e2113080a7dc01cb36f0fda9acf2178a4594e3020ef0f6db733`）；与先前frozen16包共同覆盖80条，未复制仍写入的restore服务日志。历史baseline、训练/部署及frozen16薄包的镜像hash见[私有资产](ALFWORLD_LEARNING_RUNTIME.md#private-packets)，不复制在途服务日志。

代码资格私有包`code_development_qualification_v1_20261107.tar.gz`已双端逐成员核验76项，2,704,064bytes、SHA `267bf996950f25cadfddd2e7a5390d761ad6b8d36b074a98bc44d3a79f847532`；保留两轮原结果、命令、逐test状态、错误与注册表，未打包完整candidate/gold树，不是公开artifact。

后续两source与8个保留现场的闭合证据包`source_pairs_and_preserved_states_v1_20261107.tar.gz`已双端逐成员核验88项，17,256,211bytes、SHA `2eec08f3e78d52038472e8f62bd0d69b33676961fb1f3a42869b54742e487ae0`（manifest SHA `4a5647676e2cc8277ec6fc0c82cee27c5dcb624eb73bfd74c95d8409718118aa`）。本机另逐条核8个公开重放日志的322动作及回执hash；不含在途96回合或完整base/gold工作树，不作actor输入。

首臂闭合raw私有包已双端逐成员核验9,550项，34,584,157bytes、SHA `41be9737b82e03ff8378b56ae0e55c540f4f3407b849412e720b84ec590ab6f5`；只含frozen_last3闭合16条。source准备/审阅/内核控制薄包双端核验90项，3,106,501bytes、SHA `f6ab79c43decaf40b9379aa0592cac9dedfe45e6439e1cd8fc433612f6e671b3`；不含完整work/baseline/runtime。继承此前ALFWorld专题已闭合7,839HTTP/91,963,598tokens，只追加本首臂1,312 / 6,602,874，当时已闭合小计9,151 / 98,566,472；排除其余在途臂、训练和研发Agent，不是项目总账。

ordinary_last3闭合原始包双端核验8,656项、29,176,224bytes，SHA `97345e170747f8b7448fc8ac81585e08191620182a955d4abf74aa1ac81b39e4`，只加入该臂16条，不复制在途完整历史/R输出。小计再增加1,185 HTTP / 5,916,525tokens，当前ALF专题已闭合10,336 HTTP / 104,482,997tokens；再次解析先前frozen原SSE不重复记生成。仍非项目总账，训练、研发Agent、未闭合其余臂及历史差额单列。

source评分控制薄包已双端核验59项、18,178bytes，SHA `2e6a7066eed4486a240c42d7db9ddc4fc41a35741331f14d78f2d303758fb42e`；本机另核4份base/gold回执的完整标签、预期失败/通过及清理，check SHA `2a260602c18411b07f63eba05be1e1ceb96e04be1bc5598461ba52a2bd08d428`。不含work/baseline/gold树，未公开。
