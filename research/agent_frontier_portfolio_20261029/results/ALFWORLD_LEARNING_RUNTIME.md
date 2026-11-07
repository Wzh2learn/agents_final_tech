# 学习研究：闭合训练、运行与来源准备

> 2026-11-07按主题拆分；只在核查训练、部署、闭合成本或来源资格时加载。当前裁决和下一动作只读[现役学习记录](ALFWORLD_CORRECTION_DATA.md)。训练/部署旧片段来自拆分前 Git `685fcfd8`；后续结果和代码准备各节注明迁入来源，不改写旧数值。

<a id="learning-runtime-history"></a>

## 已闭合：同来源两臂真实训练

两臂用同HF8B基座、seed17、新q/v LoRA r8/alpha16/dropout0，各计划192次成功optimizer更新，来源均衡轮转且覆盖全部动作；普通计划1,135,199序列tokens/8,239监督tokens，纠正1,135,273/8,378。只称同来源/初始化/更新数；不把不同训练量写成完全等成本。现役计划为`learning_comparison_v1/plans/ordinary_v4`（manifest SHA `875243cbcab87d968789e76f34745ee3514c27e0ac65c470ab499b8ee90a8c09`）与`recovery_v4`（SHA `4be913090ed70584a52b7b7d832b3aecc3e87991221bb3665ca953ef274888c7`）。历史计划/源码/失败保留。`owned_window_v3`普通臂已192步保存并重载，tensor hash精确一致，实际1,135,199序列/8,239监督tokens、1579.43秒；receipt SHA `5d35669dabdd9a5a3ae2fea48b691f3bb3112628d42e2b7b945cc79573331068`。纠正臂亦完成192步保存/重载，实际1,135,273序列/8,378监督tokens、1600.13秒；receipt SHA `7d74ad33cf595935c5297fef5eb85547110c36d3c12e17d8643631aef9f085b8`。两臂合计384更新、2,270,472序列/16,617监督tokens。request SHA `69c07d8e1a6e63539a01b3d4ad85d69e7362a096c11b20cb2004287649fe66ff`。窗口已原样恢复owned18104（PID123887），共享35B/27B身份不变；4次健康GET、1次CUDA探测，窗口3237.58秒、科研生成0。窗口RESULT SHA `6f4ceae02bead9e5a424489492d60dee9dfc2c21160c947a6dfb2994adc2da46`。未加入canary生成，实际学习效果随后按环境won评价。

2026-11-07新评价窗口`learning_comparison_v1/hf_evaluation_v1/RUN_v1`在Popen后立即采集身份，启动瞬态被误判，0个task/POST；BF16实际已加载。原RESULT SHA `b8dfa6fda5c377049810e03915b7d4640552dc5ae5e33e11fd99cb452823039a`保留。D精确收回自有BF16 PID169132、原样恢复Q4为PID171257，保护35B/27B不变；`manual_restore_v1/RESULT.json` SHA `131747165d1ce410612065bd7d619fc17382a9c8ddde941902e6cc750fa9d251`，4次健康GET、0生成。v2把执行资格的稳定argv/cwd/exe与Popen子进程的清理所有权分开；D真实CPU exec过渡观察及5项测试通过，科学协议、任务和权重未改。随后RUN_v2开始实际评价，不能将本窗口工程失败算作学习负结果。

### 实际训练表示复核（2026-11-07）

独立只读核对V4排程实际覆盖的全部135个唯一训练行及原请求：ordinary为67行、7组、2,865唯一监督tokens，均从reset起步；recovery为68行、同7组、2,950唯一监督tokens，均来自drop_recent失败现场。两者训练system token hash一致；135行均只监督当前助手动作与EOS，历史及工具反馈为-100，未发现错误历史进入loss。`TRAINING_REPRESENTATION_CENSUS_V1.json`位于私有证据目录`evidence_packets_20261106`，SHA `2c3b1595109516d3eb05020abd5052ca746dc28b16bd3fab5f1fe1f050557a55`。

重要区别：R原始user中保留的是起始现场最近3个已接受**环境动作**，随后教师原生assistant/tool历史继续增长；运行期last3则滚动保留3个完整**工具调用轮次**，二者不是同一操作。当前O/R检验训练方案整体差异，包含来源状态、可用信息及表示，不能单独归因为反馈内容。当前批次按冻结合同继续；若R出现稳定收益，再用表示及信息匹配对照拆分来源，不自动增加训练变体。

仅按公开目标检查135行中的heat/cool/clean正监督动作，普通无非目标处理动作，纠正有1个（目标hot tomato时执行cool tomato）；hot/heated、cold/cooled按对应动作解释。`TEACHER_GOAL_OPERATION_SCAN_V1.json` SHA `43e4c2143a141d3dc0311920e5d63cefba10b703e484fbf8d865e920f8e5da59`。这只是监督筛查线索，不证明该步有害、冗余或解释迁移失败；移动、搜索、开关等动作未判定必要性，不据此清洗数据或改变在途实验。

## 2026-11-07闭合：训练前工程现场

v2首次实跑在权重加载前返回`Invalid device argument`（0权重加载、0forward、0优化步，不是OOM或学习负结果）。根已在新进程精确复现：reset_peak不触发CUDA初始化，必须先mem_get_info；现已修正并以失败→通过回归验证。`owned_window_v1`结束已恢复8B原argv/cwd（PID16445），共享35B/27B身份未变；5次健康GET、1次CUDA内存探测、零模型生成。旧窗口与receipt保留，随后v3在CUDA初始化处报OOM，仍0权重加载/0forward/0步；`owned_window_v2`已恢复原8B（PID24359），共享服务未变，7次健康GET/1次CUDA探测。两次都不是学习负结果。定向释放已绑定HF8B文件的clean页缓存，实测MemFree增加约8.7GB而MemAvailable近似不变；v4仅在逐shard完整核验后作同类建议，并记录原始异常堆栈与阶段，不保证显存足够。不改共享模型，不让此支持项阻塞主线。

<a id="deployment-bindings"></a>

## 共同HF父模型与部署

仅D在持有本study队列及owned18104窗口时显式运行，窗口不代表整GPU独占；共享35B/27B保持常驻，结束须恢复owned8B原argv/cwd与健康。OOM保留失败、实际步数与未知项，不自动换模型/截样或改共享服务。4B不是前置。HF8B五shard共16,381,516,776bytes已完整绑定；`HF8B_MODEL_BINDING_V1.json` SHA `b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1`。

**部署判断已改变**：旧Q4 GGUF元数据标`awq-compatible-Instruct`，固定4层的8个非量化RMSnorm与HF均不等，8个q/k norm相等；72个量化块抽样的cosine高但相对误差大，不能直接认定HF LoRA的参数坐标兼容。诊断`gguf_conversion_v1/HF_GGUF_NORM_DIAGNOSTIC_V1.json` SHA `97a69526ac33d9fbe49ba97d320edbe35d2223b2732492aff7e7c5cb43253019`。不推断模型整体函数必不同，也不撤销旧模型的实际结果。改从绑定HF导出BF16 GGUF作为五臂共同父模型，并重跑新frozen对照；旧3/16不充当新父模型基线。默认旧profile和冻结actor/recovery保持不动，study增加显式私有runtime profile并绑定实际进程。父模型CPU导出已完成：399张量/8,190,735,360元素，145个norm全值及30个q/v标量精确核对；不声称全矩阵逐值比较。GGUF SHA `505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3`，16,388,044,256bytes，已封存只读；`gguf_conversion_v1/hf_parent_bf16_v1/EXECUTION_RECEIPT.json` SHA `85092e8d406f729fb3acbc51961bfd45d8561ee85d174ba76818606a6015b01e`，CPU135.15秒、生成0，原8B及共享服务不变。SentencePiece 0.2.1仅私有CPU工具依赖，不改项目venv。

普通适配器已CPU转GGUF：144个q/v A/B的F32形状/数值与PEFT精确一致，3833856参数有限且非零，72基础模块维度兼容；输出SHA `deaf4b1618cdc3664dab92d798c375f36ae2e9e6c87e787e9118277fa2bb805f`，receipt SHA `d2a1411c50f79138cd2012fccb78934721a6d7a87cc45d3220138db84871bfee`。工具为官方llama.cpp `954de248`的私有副本，不装入项目venv；Windows CRLF导出与上游blob另有逐文件映射，142份Python AST一致，不混用SHA。CPU文件资格不是实际加载或学习收益。

纠正适配器同样完成144个A/B张量与PEFT逐值核对，新BF16父模型72模块维度一致；GGUF SHA `560a86bd66d11fd2186a9ddff0130b8c4bc37a1fb148623a6faea831cc4b34ba`，receipt SHA `7c61a8a03a45954ed4168b175c6889783f3fe0e91ba0def3488911476cc46f9c`。两适配器均封存只读；两种适配器均已实际原生加载；学习收益待完整任务比较。

<a id="private-packets"></a>

## 闭合私有镜像

当前32个闭合baseline及对照材料已私有镜像：`alfworld_frozen_and_native_baselines_v1_20261107.tar.gz`，10746成员/27367833bytes，SHA `68023591e37f2624a810f5d66319bc417bb53c6515f5eab49af1c30bafa12d04`；双端逐成员核验。原监督薄包见上述历史段。另有闭合训练/部署薄包`alfworld_learning_and_deployment_v1_20261107.tar.gz`，87成员/57,243,487bytes，SHA `1459c7fe6dd7723502643ac40735b1dc2c0551d537da3c3e7444b6e134f63cdf`，双端逐成员核验；含两adapter、不含16GB共同父模型与在途评价raw。frozen16闭合薄包`alfworld_common_parent_frozen16_v1_20261107.tar.gz`（4130成员/24,264,221bytes）SHA `cc8c635f7d28d94b8d25551c8633641fbb19933525805d1d9a52cec5847e4cab`，双端逐成员核验；未复制仍在写入的恢复服务日志。所有包均非公开分发。


<a id="terminal-retry-20261107"></a>

## 已闭合：终态409重试及永久终止修复

以下事故原记录从当前纠正记录移入（来源commit `8fcfc342`）；原始raw与账本不覆盖。

main `8200764f`启动的`RUN_V2`现已受控停止。首回合clean_01在128实际POST上限失败；第69次实际body确认从68个工具回合保留3个，目标、8192输出、seed17/temperature0.2及nativeFalse保留。次回合look_01实际5动作、8POST即native won，但终态返回409后客户端继续发相同请求，新增10次拒绝按2/4/8/16/32/64/128/256/512秒指数退避，模型转发始终为8。D核原PID682492/出生票/完整argv，通过pidfd发SIGTERM走原清理路径，没有因SSH超时重启或在运行中改源码。`RUN_V2/RESULT.json` SHA `a6d6c3f8a5d7bd65640805a8506c9526d8c75736521bd20b4f2bd524e5157811`：`STOPPED_RESTORE_REQUIRED`但实际restored_healthy=true，原Q4恢复PID718236/start1077364320，35/27身份不变，无清理异常。

原两回合原生结果均保留，不作为完整六组方法比较。新增136真实POST，607,566输入＋5,636输出＝613,202tokens，cached输入532,586为输入子集，usage未知0；第二回合receipt因受控中断记FAILED而won=true，两者不混同。事故记录SHA `6e46a52d59f59a0329ded6256996a7317df5f52c1a46e5145ff7f771a28102fa`。从五臂/27B后的专题累计追加本136次，为7,839 HTTP/91,963,598生成tokens，仍不含训练、研发Agent及Django。

同一C续做真实OpenCode1.18.3＋原GUEST桥＋断网假relay验证：409产生2次相同假请求（按约定清理，不算自然退出），400/410/403均1请求后自然exit1。原响应字节、命令、raw及清理核验见`TERMINAL_HTTP_PROBE_V1/VERIFICATION.json` SHA `424d49a6318e9213fed8f0c5662a55d4ccfeadf0d0a7ca639ca70f002e269694`；0模型/0world。现役终态改400 Bad Request，仍要求真实终态见证；无见证400、旧409或未知错误均拒绝。原403预算门不变。恢复入口新增显式closed回执以绑定新Q4进程，恢复旧版SHA校验后`POSIX_FADV_DONTNEED`建议（不保证驱逐，不据此归因SSH异常）；GB10实际136 tests/389 subtests通过。后续使用新输出根和精确源码绑定，科学设计、权重、种子、caps不因这两题调优。


修复后的真实look_01回合在5动作/8模型POST后36.35秒自然收尾，额外1次终态请求返回400、isRetryable=false，原生won保持；这是接口修复，不是方法收益。完整96新批次只在[当前纠正记录](ALFWORLD_CORRECTION_DATA.md)维护。

私有包`runtime_terminal_incident_and_next_sources_v1_20261107.tar.gz`已镜像本机：27,328,912bytes/1,130成员，SHA `b2b3eda06aaf0c4baec49449e3af2788f15c7f0791a2e263f7cfc85a9209fbec`，双端逐成员hash通过；含闭合两回合、接口probe、下一批固定协议及新代码任务源码/元数据，未打包在途RUN_V3。另从本机镜像独立重算全部136份实际SSE的hash/usage/终止原因，0差异、0 length；本机`runtime_terminal_incident_raw_sse_local_check_v1_20261107.json` SHA `3bad7182329ae35a382448c60591ecf1ffcc40d1b64c67945d721a6aea4ceff1`。私有包不是公开分发材料。


<a id="five-arm-results"></a>

## 已闭合：五臂、27B参照与Django单题

> 从现役纠正记录原文移入；这是已闭合证据，当前运行只查[现役学习](ALFWORLD_CORRECTION_DATA.md)。

HF共同父模型的frozen臂已闭合：**7/16 won，primary三类6/12，clean1/4**（heat1、cool2、look3、clean1）。746个请求预算记录中741次实际转发；10,184,855输入＋31,890输出＝10,216,745tokens，缓存输入9,994,186为输入子集。D逐条复算741份原SSE的hash/usage与原生终态及实际采样，0差异，无length结束；`hf_evaluation_v1/FROZEN_ARM_RESULT_V1.json` SHA `77f087dea66571529e5fc64b1be9772d48c217ee3691dda835459943e97fc644`。截至frozen臂闭合，本专题HTTP生成累计4,836 calls/55,985,482tokens（不含后续四臂），训练/研发Agent另记，不是项目全账。旧Q4两接口的结果和来源保留于[闭合对照](ALFWORLD_CONTEXT_STUDY.md#old-parent-baselines)，不充当本共同父模型对照。

普通SFT臂16题亦闭合：**7/16 won，primary6/12，clean1/4**，633个预算请求中628次实际转发；7,806,812输入＋26,788输出＝7,833,600tokens，其中cached输入7,625,705为输入子集，usage/cache未知0。逐条原SSE、实际采样、共同父模型/ordinary adapter及native终态复算0差异；`hf_evaluation_v1/ORDINARY_ARM_RAW_CHECK_V1.json` SHA `63bce2cdce99ad0bac66f90e39d51761dfdcd01464111ae50d461e9278d59faf`。F/O总数相同但成功集合不同；历史两臂已闭合，五臂按相同任务/布局配对。[闭合汇总器](../summarize_alfworld_learning.py)已33项测试通过，已在80条全部闭合后生成描述性汇总，冻结16条只计一次。

纠正SFT已闭合：**10/16 won，primary7/12，clean3/4**。814个预算请求中807次实际转发；9,658,310输入＋34,115输出＝9,692,425tokens，cached输入9,438,233为输入子集，usage未知0。807份原SSE、采样、共同父模型/recovery adapter与native终态逐条复算0差异；801 tool_calls、6 stop、0 length。`hf_evaluation_v1/RECOVERY_ARM_RAW_CHECK_V1.json` SHA `5eef466664b8c34ca445a8f338ba148a812be7b070f217e0b597b02c803ce7df`。相对F为4新增/1丢失，相对O为5新增/2丢失；总数增3主要来自clean非退化切片，预定primary仅增1题。保留这项正向开发信号，不以总16替换primary12，完整历史比较见下表。

### 五臂闭合结果与判读

| 臂 | 主比较heat/cool/look | clean非退化切片 | 总计 | 实际POST | 输入 / cached子集 / 输出tokens |
| --- | --- | --- | --- | --- | --- |
| Frozen F | 6/12 | 1/4 | 7/16 | 741 | 10,184,855 / 9,994,186 / 31,890 |
| Ordinary SFT O | 6/12 | 1/4 | 7/16 | 628 | 7,806,812 / 7,625,705 / 26,788 |
| Recovery SFT R | 7/12 | 3/4 | 10/16 | 807 | 9,658,310 / 9,438,233 / 34,115 |
| 普通历史all7 | 5/12 | 2/4 | 7/16 | 344 | 4,740,345 / 4,539,009 / 16,143 |
| 普通历史top1 | 4/12 | 2/4 | 6/16 | 748 | 9,425,043 / 9,212,441 / 32,599 |

汇总`hf_evaluation_v1/DESCRIPTIVE_SUMMARY_V1.json` SHA `d7b14e0fbe80550850d94442d9427e0c873cf8d5d692e76be09042b8944ecf77`。五臂80个唯一回合，共3,268实际POST、41,815,365输入＋141,535输出＝41,956,900tokens；cached输入40,809,574是输入子集，usage未知0。继承冻结16条为741POST/10,216,745tokens；新增64条为2,527POST/31,740,155tokens，不再叠加RUN_v2总账。从前述截至frozen的专题账只追加这64条，则本专题截至五臂闭合为7,363HTTP调用/87,725,637tokens，排除在途27B、训练与研发Agent，仍非项目全账。训练与教师形成另计。对应非缓存输入F/O/R/all7/top1为190,669/181,107/220,077/201,336/212,602；all7总输入与调用较少不等于非缓存计算也最低。两历史臂1,092份实际SSE逐条复算hash/usage/采样，0差异，无length终止；`HISTORY_ARMS_RAW_CHECK_V1.json` SHA `77d28b0a525dd9610a916de2865cfc0e7aa741c5e0a5ae8dce471085370ca98d`。

R相对F/O主比较只多1/12，配对分层布局bootstrap的95%描述区间为[-16.7,+33.3]pp；总体多3/16，区间[-6.25,+43.75]pp。相对all7主比较多2/12，区间[0,+41.7]pp。all7总成功数与F/O相同且实际token更低，不能仅按成功数忽略强简单方法的成本；不同成功集合也不能视为策略等价。所有区间为同一暴露开发面板的事后描述，非确认检验；不以clean的增益替换primary，也不选最有利对照宣布胜出。固定快照C独立重算80个原生终态、唯一root/费用/实际首请求与历史交付及20项区间，0差异；`C_CLOSED_COHORT_REVIEW_V1.json` SHA `117093a03776ed6f0184ed7d0cd1421bf65db62c4c6ea081cbbb136cca320347`，D回读并核780输入hash稳定。C仅另抽3份SSE，其余全量原SSE复算为上述分臂审查，不冒称C重读全部3,268份。历史臂通用delivery中的NONE只是任务内交付的元数据局限；32/32冻结历史块及80/80首次实际请求均完整。下一步先补持续短历史对照，并统一终态后的成本控制，再决定学习增强。

**环境完成与收尾成本分开。** F/O各7个won均正常退出；R10个won中仅6个正常退出，另4个达标后触预算/上下文门。逐tool JSON的完整六字段与native first-won匹配后，R在首次已实际转发成功反馈的请求T之后仍有346个实际POST、4,106,887tokens（cached输入4,060,867为子集）；F/O同口径均0。含T则R为355POST/4,175,209tokens，这是可证后缀费用及全部终态后量的保守下界，不从原账扣除。`hf_evaluation_v1/POST_TERMINAL_REQUEST_REVIEW_V1.json` SHA `935c8eff8591733167b394f18c063b3e3d16dc8cf3ecde5b14cfd0762765a131`。未来全臂一致加native done/won停止门，保留原生10胜与原始费用；工程停止门不算学习贡献。

同16题的27B直接执行参照已闭合：**14/16 won，primary11/12，clean3/4**；340实际POST、342预算请求，3,607,940输入＋16,819输出＝3,624,759tokens，控制器墙时2792.55秒，训练/服务重启0。逐条340份原SSE、采样、初始题面/reset、native终态与回执复核0差异，326 tool_calls/14 stop/0 length。usage未知0，但全部340次没有provider cached-input字段，缓存未知，不填0或将全部input称为非缓存。`teacher_reference_v1/RUN_v1/RESULT.json` SHA `469aeba85a1ce50863948a90fe85a9f0fb20de247f111940e8efe7ef8d3c0a81`；`DIRECT_TEACHER_RAW_CHECK_V1.json` SHA `6bcd093ef298a9c55b00427c16001767c40b57657b4021b1c6977c78ab0fb07d`。协议SHA `f458e77dc3098b29654b59486f2b1e5d4c38fe127c16579e8ee04ddd6c2c7e3a`，同公开题面/reset/cap，既有27B部署、无免费oracle，输出EVAL_ONLY。强模型更高完成数和更少实际调用是本面板的部署参照；不同模型/cache未知及旧R终态长尾下，不直接换算同等计算或端到端经济优势。

截至该参照闭合，ALFWorld专题继承账只追加340次/3,624,759tokens，变为7,703HTTP调用/91,350,396tokens；不含训练、研发Agent或下述Django。研发子Agent缓存/费用不由这份科研调用账证明。

Django34570已完成新自然问题准备（私有`django34570_development_v1/summary.json` SHA `dd4046ba3b380103c967f7ee0b7d688188fa0b863e1bd8e4e47665c12d96bd28`）：base关键1项报错、gold1/1通过，两者回归13/13；M2M/GFK公开调用在base报AttributeError、gold正常。10次CPU容器含初次权限失败，均保留；gold/test补丁独立于actor源树。新[薄任务入口](../run_django34570_development.py)复用现有derive/计量/独立评分；GB10聚焦12测试/7 subtests通过、实际容器11项可读写边界检查通过，静态准备manifest SHA `43a5c6791d3ff2cfd422f50cf8eb8f6060a976250a0ff78466b07697f19b75d4`。v5已绑定当时恢复态，但actor启动因AF_UNIX路径过长在模型转发前失败；公开probe亦受源0600权限阻断，旧现场保留。最小修复为短自有socket及同hash的只读probe副本，冻结源不动；GB10复验33测试/29 subtests通过。入口已支持显式closed恢复回执，并保留原Q4 argv/cwd/权重与完整进程身份守卫；新`attempts/cpu_surface_v6`已静态准备（manifest SHA `ab040fba656d2ce553e7f257f7b49912aadfc1f6a0b7eb4dbbe9fa8ed95ab446`，0模型/服务动作）；已按五臂closed恢复回执绑定同一原Q4 PID372039并实际执行。v6结果`GENERATION_RECORDED`（SHA `8ffc1c3065268d79b4651980a1396c6d081d9fcf812095390d661e1b9fc20110`）：33实际/预算POST、588,426已报告tokens、89.07秒，已完整计量；独立F2P失败、PTP13/13、公开M2M/GFK复现失败，fixed=false。actor正常退出却最后询问是否继续，候选相对起点0改动/0删除/0非缓存新增；`CANDIDATE_DELTA_V1.json` SHA `8f6be481e3822dd5e396688a8f822d30a88989cf3d9519f4af976fb5098c81e5`。这是可运行、未解决的一道新代码开发问题，尚无经验/学习比较，也不是反馈学习负结果；公开复现为空SQLite查询，不把13项测试算13任务。

<a id="code-source-controls"></a>
## 代码经验来源：闭合的资格与接口准备

> 从当前学习记录原文迁入；实际source采集现状仍读该记录，不以本节历史等待状态作为现役待办。迁移文本规范换行后SHA-256：`0eecd1070768f1bddcc02df439e05c965ff60f2d4374eaa98fa901164596ffbb`。

本节`ROOT`为`/home/testuser/wzh/research_evidence/agent_learning_20261030`；未加前缀的source资格/准备回执位于`ROOT/code_source_expansion_v1/`。迁入前快照为Git `b682eafd`。

第二环境增量准备使用现有ContextBench Lite与Django/SymPy隔离依赖。元数据过滤剩21个关联候选目标（非全项目未曝光认证），按题目hash选得Django31051、SymPy9384/19006三目标及其较早来源；`ROOT/next_code_source_inventory_v1.json` SHA `114f22de08c94404909720ff950a61bbe0f0e39be4503bfe289616caf1c1081c`。上游`created_at`仅作排序，实际核GitHub源修复merge确为目标base祖先；`code_source_expansion_v1/ANCESTRY_CHECK_V1.json` SHA `c8412bc8d709509fa9336520dd4d19572c65f67dea571f8fa5a4ce6700143603`。源码准备阶段共下载3份官方commit归档：6次公开元数据HTTP＋3次源码HTTP、0模型/环境/训练；归档清单SHA `bc92d85748b67ea41fdfe67c85f169289429a526936c1d6d15bf021259d402d7`。CPU资格合同SHA `8b9d0977494184c8e61eeafde308143fdc4dc293bf401b8b8b9c541f1b3c6017`；先复现base/gold及全部已发布回归，再决定是否用作新开发任务，不把源码时序通过当任务修复资格。

已集成[统一CPU资格入口](../qualify_contextbench_pool.py)，首轮`QUALIFICATION_RUN_V1/receipt.json` SHA `6b43065ab2d70372d34258ad276b3a023b4aaffb16c65d6c79f28bf5511f3f14`返回NOT_QUALIFIED，但分题结果可用：SymPy9384的2个F2P全部base失败/gold通过，两侧320个PTP全部通过；Django31051在Python3.12缺distutils、未进入测试；SymPy19006的4个F2P成立，两侧PTP均46通过/2失败，首错为旧AST构造False常量的ValueError。后两者不当方法负结果，不豁免既存回归。最小修复复用已有冻结Python3.8给历史Django运行，同时区分pytest XFAIL/XPASS且仍拒绝non-pass资格；16tests/32subtests通过。`QUALIFICATION_RUN_V2`已闭合（receipt SHA `a3c7eef5d3b803dba02992d553d9858bf3e8385ace1d4c33435c750221044aa0`）：Django31051的12个F2P全部失败→通过、两侧25个PTP全通过；SymPy9384保留完整资格，19006仍未通过且不豁免两项。整体仍为NOT_QUALIFIED，不冒充三题全绿；仅两题进入开发EVAL_ONLY注册表`QUALIFIED_TARGETS_V1.json`（SHA `01493c013446b832b084aa914a578d4a0b0fe5b2645665792d59f43a7479da2f`），其较早经验源的后续资格见下段，真实轨迹尚未采集。两轮共24个实际测试容器、测试段墙时合计240.99秒、0模型，源码SHA `d05c12e757dae2d4c55261f62af89fb9ddec6830cbb6733dab9df3bdb23ffad8`；三题/源码/patch/标签不变，完整conda库树未冻结。它与六组实验仅并行占CPU，不发其他GPU请求；墙时不作为隔离硬件下的因果成本比较。本轮A临时worktree已合并并仅清理13个重建缓存，7个历史资产树保留，Agent上下文保留。

本批只检验从reset迁移。后续恢复开发固定取frozen结束时未won/未done且至少一个接受动作的完整前缀，共8个现场；零动作cool_02单列reset诊断。接受动作不自动等于有效进度，不挑近成功片段。各臂重放同一公共现场，用额外且统一的接续额度（候选32POST/600秒，尚未冻结），不把原128POST耗尽写成仍有剩余；world仍总100动作，形成费只计一次。比较最强简单history/公共摘要、ordinary/recovery，并补同接续额度reset控制，以区分恢复特异性与一般能力。旧load_prefix只接受collect及同protocol，后续须显式绑定旧protocol/manifest/receipt/world SHA，不改原回执。此设计未启动，EVAL_ONLY目标输出不回流训练。

**两对代码任务的经验来源已完成资格。** 仍复用同一A，不新建Agent：扩展入口以原Experience标签逐项绑定具体测试方法，未放宽旧三target资格。`SOURCE_CONTRACT_V1.json` SHA `8c48cb051323c396fb50d05994c3b0a67cacb92afb902e644c04faa336b57df7`；8个真实CPU容器、测试段15.26秒，Django12453的1个F2P失败→通过、两侧5个PTP通过；SymPy21055的1个F2P失败→通过、两侧13个PTP通过。D复核491个输入hash、原始测试日志及clean源码树；19 tests/47 subtests通过。`SOURCE_QUALIFICATION_RUN_V1/receipt.json` SHA `576dec0cc19d342d50c8ebfd65b90dde8c123ba7e1fd199545dde209ad638ab2`；两对注册表`QUALIFIED_SOURCE_TARGET_PAIRS_V1.json` SHA `de086acea81dcfae7bdc6e3276a05e7c8ff02e0c6ce38a989bb9f1560a39838f`。经验源为12453→31051、21055→9384，源码修复merge均为目标base祖先；新增2次官方source归档HTTP，扩展专题累计11次非模型HTTP。此为参考/测试资格，不是Agent成功经验；source真实轨迹待模型窗口释放后采集，目标仍为EVAL_ONLY，gold/隐藏测试不进actor。

**通用代码source入口已准备，实际经验尚未采集。** 新[单一入口](../run_contextbench_source.py)供两个source复用，直接导入稳定传输/隔离依赖/评分组件，不再复制日期runner或提取旧AST代码。最新源码`f63e4a0e`；D实跑62 tests/47 subtests通过。C固定快照找到并复现晚连接越过关闭，再限定复核原子关停和5秒单次发送界；D另以真实内核socketpair阻塞写验证约5.01秒收尾、部分发送仍unknown，真实模型0。C审到`0f0e30cc`，后续Docker缺失对象小写兼容由D检查及真实容器核验。

两个真实资产V4 CPU prepare与frozen verify均通过；`SOURCE_ACTOR_PREPARE_D_V4.json` SHA `ebece8b1aabd89d3050800709ae42a5f13c33fd872838994ccf4eee1e65ab1ec`，Django/SymPy manifest分别`7fdcc03db7adda119d77b012b31120ca774fdcffb8352e158c0b6e07262a1ee5` / `7d639a0c1983ec9a1c547419efbba8c75846d7c9f9ed6139db5d0e4a0091a37a`。原公开题面与包装提示分hash，Django自带作者建议diff原样保留；actor Py3.8/依赖与资格逐文件相等（47/415）。实际Django容器的导入、OpenCode1.18.3、可写代码、只读题面及私有评分不可见均通过；首次正常自动删除被大小写误报，原回执保留且精确CID确认已不存在。新scorer控制在可用内存3,240,075,264bytes低于4GiB时正确DEFERRED，未启动测试容器；SymPy表面及base/gold评分均待资源释放后在新控制根续做。`SOURCE_PREPARATION_RETURN_V1.json` SHA `6409af4cdc0ee494148f72c0d844a89cfdcc377cbdf3d49fe442387339352304`。本轮仅2个Django表面容器、source模型/训练0；V1–V3静态准备保留未执行，不作为经验。

**资源允许后已补完CPU控制。** 新根`SOURCE_SCORER_CONTROLS_V2/RESULT.json` SHA `7718efabe51be0ebedde1030652ba19af912f6f1c738bf19a6ba0ec7eac37ff7`：8个实际测试容器、30.48秒；两source均原版F2P失败、参考F2P通过、两侧PTP全通过。SymPy实际隔离表面亦PASS（Py3.8.20、项目从/workspace导入、OpenCode1.18.3、代码可写/输入只读、私有证据不可见），精确CID自动删除。汇总`SOURCE_PREPARATION_RETURN_V2.json` SHA `530dd81deae03ea69d95ec14cee9d51925f047c6d74d385c33e1a4e80d5390fd`。本次新增1表面＋8测试容器，source模型/训练仍0；旧低内存DEFERRED保留。下一步仅待主模型窗口释放后采集真实source轨迹，不能把参考控制通过当Agent经验。

[回到现役学习记录](ALFWORLD_CORRECTION_DATA.md)。
