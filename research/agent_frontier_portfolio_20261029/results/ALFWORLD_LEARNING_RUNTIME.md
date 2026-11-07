# ALFWorld：闭合训练与运行绑定

> 2026-11-07按主题拆分；只在核查模型坐标、训练、部署或私有镜像时加载。科学结果和下一动作只读[现役学习记录](ALFWORLD_CORRECTION_DATA.md)。原文来自拆分前 Git `685fcfd8` 的当前记录与背景记录，不改写旧数值。

<a id="learning-runtime-history"></a>

## 已闭合：同来源两臂真实训练

两臂用同HF8B基座、seed17、新q/v LoRA r8/alpha16/dropout0，各计划192次成功optimizer更新，来源均衡轮转且覆盖全部动作；普通计划1,135,199序列tokens/8,239监督tokens，纠正1,135,273/8,378。只称同来源/初始化/更新数；不把不同训练量写成完全等成本。现役计划为`learning_comparison_v1/plans/ordinary_v4`（manifest SHA `875243cbcab87d968789e76f34745ee3514c27e0ac65c470ab499b8ee90a8c09`）与`recovery_v4`（SHA `4be913090ed70584a52b7b7d832b3aecc3e87991221bb3665ca953ef274888c7`）。历史计划/源码/失败保留。`owned_window_v3`普通臂已192步保存并重载，tensor hash精确一致，实际1,135,199序列/8,239监督tokens、1579.43秒；receipt SHA `5d35669dabdd9a5a3ae2fea48b691f3bb3112628d42e2b7b945cc79573331068`。纠正臂亦完成192步保存/重载，实际1,135,273序列/8,378监督tokens、1600.13秒；receipt SHA `7d74ad33cf595935c5297fef5eb85547110c36d3c12e17d8643631aef9f085b8`。两臂合计384更新、2,270,472序列/16,617监督tokens。request SHA `69c07d8e1a6e63539a01b3d4ad85d69e7362a096c11b20cb2004287649fe66ff`。窗口已原样恢复owned18104（PID123887），共享35B/27B身份不变；4次健康GET、1次CUDA探测，窗口3237.58秒、科研生成0。窗口RESULT SHA `6f4ceae02bead9e5a424489492d60dee9dfc2c21160c947a6dfb2994adc2da46`。未加入canary生成，实际学习效果随后按环境won评价。

2026-11-07新评价窗口`learning_comparison_v1/hf_evaluation_v1/RUN_v1`在Popen后立即采集身份，启动瞬态被误判，0个task/POST；BF16实际已加载。原RESULT SHA `b8dfa6fda5c377049810e03915b7d4640552dc5ae5e33e11fd99cb452823039a`保留。D精确收回自有BF16 PID169132、原样恢复Q4为PID171257，保护35B/27B不变；`manual_restore_v1/RESULT.json` SHA `131747165d1ce410612065bd7d619fc17382a9c8ddde941902e6cc750fa9d251`，4次健康GET、0生成。v2把执行资格的稳定argv/cwd/exe与Popen子进程的清理所有权分开；D真实CPU exec过渡观察及5项测试通过，科学协议、任务和权重未改。随后RUN_v2开始实际评价，不能将本窗口工程失败算作学习负结果。

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
