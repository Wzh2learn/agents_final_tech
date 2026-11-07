# ALFWorld：六组上下文与学习对照

> 2026-11-07 | 协议、修正链与逐臂闭合原文。当前进度及下一动作只读[现役学习与评价](ALFWORLD_CORRECTION_DATA.md)。各段按当时闭合次序保留，不把早期“仍运行”当最新状态；原始raw/账本未改。

从Git `5e0c7d5bcacccc47aba32b31ecbd9f1d406345fe` 的原现役页移入；规范换行后协议/逐臂段SHA `9bedffaabcc2012673831e8e68aaf810de9c8e3ca92e6c117593dd4821dba78b`，闭合成本段SHA `e94622fc930d576cf752c1c38d28860a4f49ab8c0edbb7770508d97350c6919e`。两段均逐字相同，后续完整批次结果另行追加。

<a id="setup-and-arm-records"></a>

## 下一批：六组而非重复训练

采用C协议审阅给出的96回合精简设计：O/R各做完整与持续last3工具回合，另含frozen_last3和all7_last3；同暴露16题、primary12和clean4不变，0继承旧episode、0新增训练。重点同时报告R-O两条件的差值、配对交互及R对两个简单短历史基线，不能只看交互或挑有利对照。last3保留全部系统/用户/来源历史锚，不是固定总token或3条world动作。`runtime_context_baselines_v1/PLAN_V2.json` SHA `49b44eaa69c623dc1c544925c779620039c7c00b39d77ea029b8cbbc859697be`；分析合同SHA `465faabb09a40cc9ad291ecbd9032e6fa08efec3bbebb58b09edb1e2a6b95dfc`。原128草案和原文字节修正链均保留，未实际运行。

新actor/taskpool代码导致旧pool精确代码绑定失效，未放松守卫或改旧receipt；同16资产在新根`pool_v2`真实重做16/16零模型expert/native控制，90.92秒，题目/UID/layout/game/traj及公开reset均与旧池一致，不计新样本。新POOL SHA `b922dd1a108754f31d862a56bd97eb4cee4e665be6b59279b4e8c7433a465b64`、qualification SHA `304e38e4b927f274bcf7e7b72f8071820dcde0e30da1e6cd8d3337f001adaaed`。新witness还对旧80份实际native记录全量解析匹配，SHA `e514868d57713f23e5d6a3e121cd6be99c4fc18dd346cee9519691747f579967`。

独立Terra/max预启动审阅发现并复现C1（共享身份异常挡住可安全尝试的原Q4恢复）和C2（cap/终态标志掩盖异常退出）。同一A续接修正：保护异常保留且独立恢复安全owned实例；137/-9拒绝；exit0/1都核raw SHA及顶层错误，只有匹配实际403/409拒绝证据才作为正常gate，普通工具错误反馈保留。V1/V2原回执均保留，同一C限定复核V3放行（SHA `7677c9d8dfd3ac9587487ef1746c38c5b59828c90246b0ebc3a5de0833c99661`），没有另起Agent重做实现。root远端实际133tests/380subtests通过；4个actor/pool组件未因审阅修正再变，未重做native资格。

代码已合并；driver SHA `ce8f29296929a120f293a107f6d8612d917aea4f76b426ee7dd619070c16ad7d`。旧源码和原五臂费用保持，ROOT闭合源码/C薄包已双端核验18成员，SHA `a10e86f96986a16c6ca6c027df9c75750158252239665083f8e4b9639c60a60a`。预启动检查为纯CPU/假数据及旧native档案核验，不证明实际409或方法效果。

`RUN_V2`在终态409重试时受控停止：clean_01上限失败、look_01原生成功，实际136POST/613,202tokens与原输出全部保留。400永久终止响应经真实OpenCode假接口及GB10聚焦136tests/389subtests验证；原Q4已恢复，35/27不变。接口事故、完整成本与双端私有镜像见[闭合运行记录](ALFWORLD_LEARNING_RUNTIME.md#terminal-retry-20261107)，不当作学习方法负结果。

现已从固定源码`8fcfc342`启动`runtime_context_baselines_v1/RUN_V3`（PID748995/start1077529568），使用新attempt14–19、0继承旧回合；同六臂/16题/权重/种子/caps及原统计对比。`PLAN_V3.json` SHA `3e7d9814c12a96fb1723977f252278b54527d61cd8f622330974710ad446a8d1`，分析合同SHA `f43382c981d691e123130b4d1a320cd447e920fa6a9bccd6ea1c71eced987f82`；明确记录旧2题结果已知，不是独立确认。新精确源码绑定的同16资产native/expert复验16/16、142.23秒、0模型；pool_v3 SHA `afe5d0deffa3380b34b39bbc398df10c774b51fd164a8cb4b88dbe632cb784ad`。同一C限定代码审阅无阻断，回执SHA `d8826d2f4ffa5f32f476916580093abd3407e445ef01780b7a0fcaeedc709557`。已实际核look_01在5动作/8POST后36.35秒自然收尾，新增1次终态拒绝即exit1，raw为400/Bad Request/isRetryable=false，native won保持；其receipt SHA `c4c84f79bc74aa810b21a484cf3d8cebb46fc18e33c506e96b80bc18e2b9044c`。全96结果尚待闭合。

**本批首臂已闭合，其他臂仍运行。** frozen_last3为3/16 won（主比较2/12、clean1/4），1,312实际POST；输入6,546,720、cached子集5,418,388、输出56,154tokens，非缓存输入1,128,332。旧frozen full为7/16、主比较6/12，输入10,184,855但非缓存仅190,669；控制器版本不同，不能把跨版本差全归因于截短。D已在本机对16条native终态和全部1,312份原SSE的hash/usage/cache重新核算，0差异；1,307 tool_calls、5 stop、0 length。独立check SHA `aa671380ea16f694c9afff9713be11d4ecf8975728cbb04b10a8fbde9ad39729`。闭合摘要`runtime_context_baselines_v1/FROZEN_LAST3_CLOSED_V1.json` SHA `94370c4da5763a9f497020391e2c5dc6f63c5c8db3b34cbf71f8f6ecd9391f38`。当前观察已不支持把持续last3默认视为更强、更省计算的策略；完整历史须保留作恢复对照，仍待O/R同协议对比和全批裁决。

**本批第二臂已闭合。** ordinary_last3为4/16 won（primary4/12、clean0/4）；与同批frozen_last3的3/16并列作补充描述，原六对R/O和交互仍待完整批次。配对新增cool_02/heat_02/heat_04，损失look_01/clean_02。其12条失败中9条触发此前的最近12观察三次重访信号，4条成功均未触发，连续三次同动作仍为0。实际1,185 POST；input5,866,422、cached子集4,795,157、noncached1,071,265、output50,103，total5,916,525tokens。1,181 tool_calls、4 stop、0 length；episode墙时合计6,497.96秒，不作隔离硬件下的因果耗时比较。D重读两完整短历史臂共2,497份原SSE并核native/hash/usage/cache，0差异；`FROZEN_ORDINARY_LAST3_CLOSED_V1.json` SHA `85bb2106295c53ba2753f4d2b855d0c170a501133da9176688c4c4e0063ce574`。新ordinary16原始包又在本机逐成员及SSE独立核验，本机check SHA `bf8b9137ecb81178e728443b039e0ecdc31c590fc570bdc5319404868445fb9d`。本次仅只读分析，完整历史与R臂继续原设置，不训练或改在途组件。

**普通完整历史臂已闭合。** ordinary_full为6/16 won（primary5/12、clean1/4），640实际及预算POST；input8,107,905、cached子集7,918,709、noncached189,196、output27,437，total8,135,342tokens。634 tool_calls、6 stop、0 length；455接受动作，episode墙时3,548.67秒。复用A核查4,004个输入绑定，D又独立核全部640份原SSE、16个native终态及费用，差异0；16题首个实际请求与ordinary_last3逐字节相同。A回执`ORDINARY_FULL_CLOSED_V1.json` SHA `de40ed42af5e034c2215221ef743de383d9c33ac475979589a32d033c0952c13`，D复算SHA `5e4968faaa9b13ce742fb0bf719908f3ecb8c144e9798f696334a6d1ee2b189f`。

这两条普通臂的描述性对照为full6/16、last3为4/16：full新增look_01/clean_02/cool_01，丢失cool_02。last3总tokens较低，但请求更多（1,185对640），noncached输入反而更多（1,071,265对189,196）；不能只按上下文长度推定费用或计算节省，也不能把缓存输入按新增计算等价计价。墙时非隔离硬件因果估计；该对照不替代冻结六对R/O及交互，R臂尚在途，未改设置或新增训练。

**纠正完整历史臂已闭合。** recovery_full为11/16 won（primary7/12、clean4/4），相对同批ordinary_full新增clean_01/look_02/look_04/clean_03/clean_04/cool_03，丢失heat_02；主比较增2/12，clean增3/4。387实际及预算POST；input4,321,152、cached子集4,158,864、noncached162,288、output16,614，total4,337,766tokens；387 tool_calls、0 stop、0 length，378接受动作，episode墙时1,759.74秒。A核2,489输入绑定，D独立核全部387份原SSE、16个native终态及费用，差异0；与普通完整历史16个首请求逐字节相同。A回执`RECOVERY_FULL_CLOSED_V1.json` SHA `0d397c696d85133e2c45896312a2a590c964bd89392f226818afb157e659d319`；D复算SHA `43136b101ac32d5a35d3d26336e896663c9a7736d304fdc32c1b9fc728d95b49`。这是当前开发面板的训练方案信号；短历史R和history臂继续，六对/交互区间仍等96条闭合。直接27B的14/16及形成/训练费用继续作成本参照，不单凭运行tokens判定部署更省。

**纠正短历史臂已闭合。** recovery_last3为7/16 won（primary4/12、clean3/4），与ordinary_last3主比较同为4/12，整体增加来自clean；逐题新增look_01/look_02/clean_02/look_04/clean_03/clean_04，丢失cool_02/heat_02/heat_04。R短历史成功集合是R完整历史成功集合的子集，后者另成功clean_01/cool_01/cool_03/heat_04。1,059实际及预算POST；input5,574,507、cached子集4,490,637、noncached1,083,870、output44,805，total5,619,312tokens；1,059 tool_calls、0 stop、0 length，906接受动作，episode墙时4,156.56秒。相对R完整历史，其总输入与noncached均更多；这是一组配对开发观察，墙时仍非隔离计算因果比较。

A核7,582个绑定及1,060份投影证明，1,059个实际body全部匹配，最多保留3个完整工具回合；D独立重读全部1,059份原SSE、16个native终态、请求body与固定事件前缀，差异0。16题首个观察请求与普通短历史/R完整历史逐字节相同。A回执`RECOVERY_LAST3_CLOSED_V1.json` SHA `9d7696fb7e0621682e464c52ca69ccc33cf49077bf3e42aca159c2c15eaf84fb`；D复算`RECOVERY_LAST3_ROOT_RECHECK_V1.json` SHA `cc42dffb04fb111dac40c0617ada6905388c6c3ac8f94c8629f88bfb2c53b854`。本次复用A续接核查5次工具调用；未改在途history臂，未新增训练或因果结论。

**五个闭合臂的任务类型分解（事后描述）。** D只读取上述固定事件前缀和已核category映射；每列恰为4个任务，仍只有同16个任务/布局，不是80个独立样本，没有新增显著性检验。

| 臂 | clean | cool | heat | look |
| --- | --- | --- | --- | --- |
| Frozen last3 | 1/4 | 0/4 | 0/4 | 2/4 |
| Ordinary last3 | 0/4 | 1/4 | 2/4 | 1/4 |
| Ordinary full | 1/4 | 1/4 | 2/4 | 2/4 |
| Recovery full | 4/4 | 2/4 | 1/4 | 4/4 |
| Recovery last3 | 3/4 | 0/4 | 0/4 | 4/4 |

R短历史的primary4/12全来自look，不能把整体7/16解释为普遍学会了加热/冷却。R完整历史在本面板保留R短历史全部成功，且POST、总输入和非缓存输入均更低，故不据这两臂训练复杂的上下文选择器；完整历史作为后续强固定对照。任务需要长期状态信息只是待检验解释，类型、搜索路线、训练方案与采样的作用尚未分离。history臂和冻结六对/交互仍待全批闭合。

<a id="all96-results"></a>

## 全96闭合与冻结分析

`RUN_V3/RESULT.json`状态`ALL96_RUNTIME_CONTEXT_RETURNED`，96/96、0继承、原Q4健康恢复，受保护35B/27B身份未变；SHA `b6bc426206ff395a8ee3e51e8da6f90accb2bfccc656fd14175cecd2b91d0012`。恢复后Q4为PID1220283/start1080455452，原主进程已退出，来源采集按既定队列接续。末臂history_all7_last3为6/16（primary4/12、clean2/4），全批矩阵已由冻结分析器验过原生终态与回执；末臂原SSE和C全批独立复核另行闭合，不把分析器运行等同所有复核完成。

冻结分析器SHA `1303a9a99ac79495cd4d6a9da06099ba05e2efb741c314eeaa9538c362c933cb`，输出`RUNTIME_COMPARISON_SUMMARY_V3.json` SHA `366147721fed8c9c158aa27576ba00408a58378b56dda3e8238b44d42537e31f`。PLAN与V2→V3分析链均绑定；按原16任务/布局分组，四类型各4，primary排除clean，所有臂共用分层bootstrap抽样索引，seed17、10,000次、linear百分位95%描述区间。全部对比保留，不按区间筛选；本面板已曝光且单seed，不作独立确认或显著性获胜认证。

| 预定对比 A−B | primary12差值pp [95%区间] | overall16差值pp [95%区间] |
| --- | --- | --- |
| R last3−O last3 | 0.00 [-25.00,25.00] | 18.75 [-6.25,37.50] |
| R full−O full | 16.67 [-8.33,41.67] | 31.25 [12.50,50.00] |
| R last3−F last3 | 16.67 [0.00,33.33] | 25.00 [6.25,43.75] |
| R last3−All7 last3 | 0.00 [-25.00,25.00] | 6.25 [-25.00,31.25] |
| R full−F last3 | 41.67 [16.67,66.67] | 50.00 [31.09,75.00] |
| R full−All7 last3 | 25.00 [0.00,50.00] | 31.25 [6.25,56.25] |

配对交互`(Rlast3−Olast3)−(Rfull−Ofull)`：primary -16.67pp [-41.67,8.33]、clean 0.00pp [-75.00,75.00]、overall -12.50pp [-37.50,12.50]。整体R/O full有正向开发信号，primary与交互仍不确定；不把clean的3/4增量改写为三种已见类型的普遍提升。R/O训练同时改变起始状态、表示与信息条件，不能仅归因于反馈内容。Rfull对F/All7 short也同时改变窗口，不能据此宣称超过最强匹配历史基线；补齐All7 full比增加新训练更能回答这一缺口，旧96保持原结论与事后顺序。

本批实际/预算POST均5,518；input39,280,968（含cached子集34,657,190，noncached4,623,778）、output235,792、total39,516,760tokens，unknown usage/cache均0；4,458接受动作，episode墙时合计28,717.75秒，研究窗口29,264.91秒。formation/training在通用汇总中保留UNKNOWN及来源引用，不能填0或当未发生；已知两次训练费用仍在现役页另账。七份固定闭合JSON已在本机逐hash镜像；本次分析/复制0新增模型请求，接续中的代码来源另账。

**独立复核闭合。** 复用C从固定96份receipt/native及5,518条响应usage元数据独立重算，六对与交互在三切片共21项结果均一致，26条done-unwon未混为成功。结论`PASS_WITH_SCIENTIFIC_LIMITATIONS`，回执`C_RUNTIME_CONTEXT_RESULTS_REVIEW_V3.json` SHA `2c7b80bfaf8a2ef22c6535b5646b2080b3698318fbb214fc312d8b9ad9706dab`；3次只读检查和1次独占写入，未重解析原SSE或探测实时服务。各臂SSE另由A/D复算，不把该C范围说成全面人工统计认证。

**末臂reference判据修正，无模型重跑。** A原`HISTORY_LAST3_CLOSED_V1.json` SHA `dd409e935281fcf55322dff5dfe81d93dce3b96d256b4dbb8d01529a3ac6e7fd`核native/935原SSE/投影均一致，但另记951个参考字串不匹配；后续`HISTORY_REFERENCE_RECHECK_V1.json` SHA `ae9b77acf4a90e73311ff7f872d290f954e2ac3d2186a28106bbbf6302e48abc`又将完整task逐字相等作为参考存在前提。D直接读取实际首user及转发body：user以JSON字符串成帧，`json.loads(...,strict=False)`后16首请求和935转发均包含完整all7载体UTF8原字节（SHA `d19c16440cc7d7cc6d77c07248a37b7fde2a3142e28db7a68255ae0cc31a662b`）。完整task差异来自当前公开观察JSON里的字面换行转义；所有96首user均满足解码后等于task中的字面反斜线n转LF，非all7缺失。此为既有表示的观察性核对，不改raw，也不证明表示在行为上中性。两份原报告保留；root复核SHA `add132ffb7e660cecb3ec38a6519f4eb78ab5d73641c1592ccb9692112b14603`，再核6,715绑定、935原SSE/native16/费用，0残留差异。

末臂实际935POST；input8,864,262、cached子集7,875,435、noncached988,827、output40,679、total8,904,941tokens；928 tool_calls、7 stop、0 length，800接受动作，episode墙时4,298.28秒。D决定先补F full和All7 full两臂32个事后开发回合，保持当前提示表示与控制器语义，补齐同窗口强基线；旧F full的控制器不同。其结果出来前不增训练，不将Rfull对短窗口对照的优势写成方法成立。

<a id="closed-costs"></a>

## 闭合成本与私有镜像

首臂闭合raw私有包已双端逐成员核验9,550项，34,584,157bytes、SHA `41be9737b82e03ff8378b56ae0e55c540f4f3407b849412e720b84ec590ab6f5`；只含frozen_last3闭合16条。source准备/审阅/内核控制薄包双端核验90项，3,106,501bytes、SHA `f6ab79c43decaf40b9379aa0592cac9dedfe45e6439e1cd8fc433612f6e671b3`；不含完整work/baseline/runtime。继承此前ALFWorld专题已闭合7,839HTTP/91,963,598tokens，只追加本首臂1,312 / 6,602,874，当时已闭合小计9,151 / 98,566,472；排除其余在途臂、训练和研发Agent，不是项目总账。

ordinary_last3闭合原始包双端核验8,656项、29,176,224bytes，SHA `97345e170747f8b7448fc8ac81585e08191620182a955d4abf74aa1ac81b39e4`，只加入该臂16条，不复制在途完整历史/R输出。小计再增加1,185 HTTP / 5,916,525tokens，当前ALF专题已闭合10,336 HTTP / 104,482,997tokens；再次解析先前frozen原SSE不重复记生成。仍非项目总账，训练、研发Agent、未闭合其余臂及历史差额单列。

ordinary_full闭合包双端核验4,201项、25,244,280bytes，SHA `e8ce840431faefde6c8b4a2b54c94e5bed131cc1eb5ca937be76d40bc72c580d`；本机check SHA `237067124940022bcf274d91a136d22f8c18f64014075413c62b89d1856d9f92`。只含已闭合普通完整历史16条及固定事件前缀，不含在途R输出。本专题仅增加该臂640 HTTP / 8,135,342tokens，已闭合小计10,976 HTTP / 112,618,339tokens；A只读核查4次工具调用，D复算0新增生成，研发Agent用量仍分账，不填0。

recovery_full闭合包双端核验2,677项、13,856,346bytes，SHA `1c0863f09895e5f9ab52e70e284ff6dc18678d31186f766fb4ba42f5d4f5124e`；本机check SHA `baf908eca7731400b0688d23c9574c3e440859eae49e72d8999537de5451470c`。只含闭合R完整历史16条及固定事件前缀，不含R短历史或history在途输出。本专题只增加该臂387 HTTP / 4,337,766tokens，已闭合小计11,363 HTTP / 116,956,105tokens；A含有界等待共6次工具调用，D复算0新增生成。全部仍为本专题闭合账，不含在途、训练及研发Agent，不是项目总成本。

recovery_last3闭合包双端逐成员核验7,769项、30,092,908bytes，SHA `a31167512a2e638c8f7ab87abf7d9e334b2f239258710cbed853380056bf422b`；manifest SHA `1329c863646a42a85db65b350b949a50975193a5b34ec9eef57dd4ea9703f95a`，本机check SHA `221e126ccfcfcb8fbb621ec57a4eeb9a234b7feddcdb44135c73a3592620d665`。仅含闭合R短历史16条、两份复核与固定事件前缀，不含在途history或服务日志。该臂新增1,059 HTTP / 5,619,312tokens，ALF专题已闭合小计12,422 HTTP / 122,575,417tokens；复制/再次解析不追加生成，训练/研发Agent及未知历史成本另账。

末臂及全96闭合包双端核验6,937成员、52,082,332bytes，SHA `4a69158f6d831853261732c74b24335896a6ac5da6981682d029f81a15301c1e`；manifest SHA `cf821fe0fb0f06518a733022181b40d09a2a859849cb15dead6fe4eb7ae0a36c`，本机check SHA `cd15d186d31766359cd66129b46ee69cc1bca8f6a3a6e7553a9995717e3a43ae`。含history16原始记录、原参考误报/后续复核、固定全96合同与回执及15份绑定Python源码快照（清单SHA `ab456b93cb5d6a79fc533b41b4dd07363b5c8f8100f4f25b8f16772522743f40`），不含其他臂重复raw、服务日志或权重；源码修改后以此快照及Git `89984349`复现旧代码，不能用新版本冒充原绑定。末臂仅追加935 HTTP / 8,904,941tokens，ALF专题闭合累计13,357 HTTP / 131,480,358tokens，来源阶段另账；复制与确定性复算不追加科学生成，研发Agent用量另账。

[返回现役学习与评价](ALFWORLD_CORRECTION_DATA.md)。
