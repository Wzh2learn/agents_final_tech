# ALFWorld：执行纠正与学习开发

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。两臂SFT已完成，frozen与普通SFT各16题闭合，纠正及历史臂继续比较，尚无新方法贡献。

四现场能力诊断与旧分账已移至[已关闭的先导实验](ALFWORLD_CONTEXT_STUDY.md#teacher-pilot)；本页保留当前结果和下一动作。

## 监督来源速览

27B从头执行16/18、从12个学生现场恢复8/12；两者成功交集只有7组（4heat/2cool/1look）。普通/纠正轨迹分别67/68个接受动作；失败和全部形成费保留。完整导出、token标签、来源hash和教师成本见[已闭合监督材料](ALFWORLD_CONTEXT_STUDY.md#teacher-supervision)，不再默认加载全过程。

## 当前动作：保留闭合结果，完成纠正与历史比较

普通/纠正轨迹成功交集为7个任务/布局（普通67动作/2,865监督tokens，纠正68/2,950）。按双方成功取交集是common-support条件分析；唯一clean纠正任务被排除，因此训练只含heat/cool/look三类，不能称覆盖全部失败。配对记录`recovery_supervision_v2/ordinary_recovery_pairing_v1.json` SHA `dc0f6b6a6c464b53c16d708e51ee33d0ba61157bbe351f7e678f782d4eba5fcf`。全部形成与失败成本不因筛选删除。

两臂使用同HF8B、seed17和新q/v LoRA r8/alpha16，各完成192次更新并保存/重载。合计2,270,472序列tokens、16,617监督tokens；普通/纠正训练用时1579.43/1600.13秒，监督tokens各8,239/8,378。同来源/初始化/更新数不等于完全等成本。原计划、实际receipt、旧工程失败和owned窗口恢复记录见[闭合训练](ALFWORLD_CONTEXT_STUDY.md#learning-runtime-history)。

仅D在持有本study队列及owned18104窗口时显式运行，窗口不代表整GPU独占；共享35B/27B保持常驻，结束须恢复owned8B原argv/cwd与健康。OOM保留失败、实际步数与未知项，不自动换模型/截样或改共享服务。4B不是前置。HF8B五shard共16,381,516,776bytes已完整绑定；`HF8B_MODEL_BINDING_V1.json` SHA `b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1`。

**部署判断已改变**：旧Q4 GGUF元数据标`awq-compatible-Instruct`，固定4层的8个非量化RMSnorm与HF均不等，8个q/k norm相等；72个量化块抽样的cosine高但相对误差大，不能直接认定HF LoRA的参数坐标兼容。诊断`gguf_conversion_v1/HF_GGUF_NORM_DIAGNOSTIC_V1.json` SHA `97a69526ac33d9fbe49ba97d320edbe35d2223b2732492aff7e7c5cb43253019`。不推断模型整体函数必不同，也不撤销旧模型的实际结果。改从绑定HF导出BF16 GGUF作为五臂共同父模型，并重跑新frozen对照；旧3/16不充当新父模型基线。默认旧profile和冻结actor/recovery保持不动，study增加显式私有runtime profile并绑定实际进程。父模型CPU导出已完成：399张量/8,190,735,360元素，145个norm全值及30个q/v标量精确核对；不声称全矩阵逐值比较。GGUF SHA `505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3`，16,388,044,256bytes，已封存只读；`gguf_conversion_v1/hf_parent_bf16_v1/EXECUTION_RECEIPT.json` SHA `85092e8d406f729fb3acbc51961bfd45d8561ee85d174ba76818606a6015b01e`，CPU135.15秒、生成0，原8B及共享服务不变。SentencePiece 0.2.1仅私有CPU工具依赖，不改项目venv。

普通适配器已CPU转GGUF：144个q/v A/B的F32形状/数值与PEFT精确一致，3833856参数有限且非零，72基础模块维度兼容；输出SHA `deaf4b1618cdc3664dab92d798c375f36ae2e9e6c87e787e9118277fa2bb805f`，receipt SHA `d2a1411c50f79138cd2012fccb78934721a6d7a87cc45d3220138db84871bfee`。工具为官方llama.cpp `954de248`的私有副本，不装入项目venv；Windows CRLF导出与上游blob另有逐文件映射，142份Python AST一致，不混用SHA。CPU文件资格不是实际加载或学习收益。

纠正适配器同样完成144个A/B张量与PEFT逐值核对，新BF16父模型72模块维度一致；GGUF SHA `560a86bd66d11fd2186a9ddff0130b8c4bc37a1fb148623a6faea831cc4b34ba`，receipt SHA `7c61a8a03a45954ed4168b175c6889783f3fe0e91ba0def3488911476cc46f9c`。两适配器均封存只读；两种适配器均已实际原生加载；学习收益待完整任务比较。

同7组普通教师轨迹另备`reference_history_v1/BANK.json`（SHA `eca70c91e604aa1c35304121760b062203bfecc0a92dd2225997ada6ec073870`）：67接受动作和1次实际invalid_action，公开文本合计13216bytes；不造thought、不含heldout。选择仅用公开goal类别、同类public_text hash首项，缺类固定fallback；clean无训练例。仅是同来源普通历史对照准备，不是完整ReAct复现、全量token匹配或已运行的ICL结果。

两次训练0步工程失败（初始化顺序与OOM）及定向文件缓存诊断见[闭合工程现场](ALFWORLD_CONTEXT_STUDY.md#learning-runtime-history)；没有把它们计作学习负结果。

独立数据复核读取361份原SSE和135配对训练行，无差异；只允许7组暴露任务上的有限学习开发，不是训练器或泛化审定。`learning_comparison_v1/independent_data_review_v1.json` SHA `2cf11cceebef3c06caeb07ebd7f6b7a04807fd930c9a6abd21757ebd132859b8`。训练源码/CPU loss与梯度检查另行验证，不将mock通过冒充真实GPU训练。

## 新布局与第二环境

另冻结16个development-heldout任务：clean/heat/cool/look各4，16布局/UID；排除原28个已知布局。`heldout_pool_v1/POOL.json` SHA `5f1eb3820881d797867c8348e71559a57d339a753bb88ef5b7bf70530095be00`，资格SHA `3ff9f90bb2a254f38db43817d73df84b42095a818554d19199161deace9b3e65`；官方expert/native控制16/16通过，CPU89.53秒，无替换。仍是官方train来源的本地开发留出，不是跨来源或正式确认；expert轨迹为EVAL_ONLY，禁止进入训练。原18配额因可用heat/cool合计8布局而需9不可行，先改四类各4并冻结元数据匹配规则，再运行控制；原阻断证据保留。

五臂共同使用同HF父模型/actor/cap，分别报告12个训练已见类型任务和4个未在本轮SFT出现的clean非退化检查，以及整体16题；普通历史只用同7组公开轨迹，额外输入与形成成本分账。协议`learning_comparison_v1/hf_evaluation_v1/PROTOCOL.json` SHA `fc19b701ff61ad00e4884d8bd891c2e68d36ae5b582a0a6113a89c2647fa1bde`；启动前清除复制的旧prefix/三臂字段，原draft保留。每臂fresh进程、只加载对应adapter，实际加载状态另核验。`hf_evaluation_v1/RUN_v2`已闭合，frozen16结果保留。普通LoRA真实加载正确（scale1），但读取器误拒服务新增的空`task_name/prompt_prefix`字段，在任何普通任务生成前停止；原Q4已自动恢复，shared35/27不变。R2 RESULT SHA `6188e2ea570a1dadea6109bd2b65ecda7310966e9ca658a1907b00797b49bbcd`。`hf_evaluation_v1/RUN_v3`已接续剩余64次（controller PID241627，源码SHA `4bd44ba612dc7f0645f6cb3925da4e70180104c20332f2c3825bcd8d1b52d472`），普通臂已实际转发。科学协议/权重/样本不变，按唯一root/receipt SHA统计，不重跑或重复加总这16题；完整学习比较尚未完成。首次启动竞态及来源见[工程现场](ALFWORLD_CONTEXT_STUDY.md#learning-runtime-history)。

HF共同父模型的frozen臂已闭合：**7/16 won，primary三类6/12，clean1/4**（heat1、cool2、look3、clean1）。746个请求预算记录中741次实际转发；10,184,855输入＋31,890输出＝10,216,745tokens，缓存输入9,994,186为输入子集。D逐条复算741份原SSE的hash/usage与原生终态及实际采样，0差异，无length结束；`hf_evaluation_v1/FROZEN_ARM_RESULT_V1.json` SHA `77f087dea66571529e5fc64b1be9772d48c217ee3691dda835459943e97fc644`。截至frozen臂闭合，本专题HTTP生成累计4,836 calls/55,985,482tokens（不含在途余四臂），训练/研发Agent另记，不是项目全账。旧Q4两接口的结果和来源保留于[闭合对照](ALFWORLD_CONTEXT_STUDY.md#old-parent-baselines)，不充当本共同父模型对照。

普通SFT臂16题亦闭合：**7/16 won**，633个预算请求中628次实际转发；7,806,812输入＋26,788输出＝7,833,600tokens，其中cached输入7,625,705为输入子集，usage/cache未知0。逐条原SSE、实际采样、共同父模型/ordinary adapter及native终态复算0差异；`hf_evaluation_v1/ORDINARY_ARM_RAW_CHECK_V1.json` SHA `63bce2cdce99ad0bac66f90e39d51761dfdcd01464111ae50d461e9278d59faf`。成功总数相同尚不代表完成同一组任务；纠正与历史臂继续运行，不从部分结果宣布学习收益。[闭合汇总器](../summarize_alfworld_learning.py)已33项测试通过，只在80条全部闭合后报告配对结果，冻结16条只计一次。

同16题的27B从头执行成本对照也已准备，`learning_comparison_v1/teacher_reference_v1/PROTOCOL.json` SHA `f458e77dc3098b29654b59486f2b1e5d4c38fe127c16579e8ee04ddd6c2c7e3a`。只完成CPU检查，未生成；须五臂80次闭合并恢复owned8B后，由D显式绑定closed结果再运行，不能与当前批次并发或把教师计作免费oracle。其输出仍EVAL_ONLY。

Django34570已完成新自然问题准备（私有`django34570_development_v1/summary.json` SHA `dd4046ba3b380103c967f7ee0b7d688188fa0b863e1bd8e4e47665c12d96bd28`）：base关键1项报错、gold1/1通过，两者回归13/13；M2M/GFK公开调用在base报AttributeError、gold正常。10次CPU容器含初次权限失败，均保留；gold/test补丁独立于actor源树。新[薄任务入口](../run_django34570_development.py)复用现有derive/计量/独立评分；GB10聚焦12测试/7 subtests通过、实际容器11项可读写边界检查通过，静态准备manifest SHA `43a5c6791d3ff2cfd422f50cf8eb8f6060a976250a0ff78466b07697f19b75d4`。v5已绑定当时恢复态，但actor启动因AF_UNIX路径过长在模型转发前失败；公开probe亦受源0600权限阻断，旧现场保留。最小修复为短自有socket及同hash的只读probe副本，冻结源不动；GB10复验33测试/29 subtests通过。入口已支持显式closed恢复回执，并保留原Q4 argv/cwd/权重与完整进程身份守卫；新`attempts/cpu_surface_v6`已静态准备（manifest SHA `ab040fba656d2ce553e7f257f7b49912aadfc1f6a0b7eb4dbbe9fa8ed95ab446`，0模型/服务动作）；等ALF窗口结束恢复后显式绑定再运行，尚未重跑actor。公开复现为空SQLite查询，不把13项测试算13任务。

后续素材盘点只查官方ZIP成员与opaque hash：`learning_comparison_v1/NEXT_SOURCE_INVENTORY_V1.json` SHA `c236da94b5ebf37a523e9b396f9ce06ad4f00192fea8925f4495f5c2234bcbb6`。已有134个官方valid_unseen JSON/PDDL交集、134个独特game payload，与原18/新16池的game hash无交集；尚未检查全项目曝光、原生运行或专家兼容，不是第二环境或确认结果。不改当前16题，也不把该池用于训练。

本批只检验从reset迁移。后续保留进度的恢复比较，应按固定规则使用冻结对照产生的、未won/未done且至少一个接受动作的真实失败前缀；同一现场比较各学习臂及原会话retry、短历史/目标重申等简单策略。此为待执行问题，不能用reset负结果替代，也不把这些EVAL_ONLY目标输出回流训练。

## 方法重叠与下一验证

Sentry已有失败触发与验证后入库，EMG已有失败/成功轨迹匹配提取知识，STeP已有教师纠正与partial masking；ACE/AgentFold/DGRR等也覆盖局部更新、折叠及依赖撤回。原文方法核对与其余近邻完整保留于[按需精读](ALFWORLD_CONTEXT_STUDY.md#mechanism-reading)。当前SFT是监督来源/能力对照，不是上述方法的新名字；独立贡献仍待实际比较。

## 本轮判读与训练对照取舍

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：教师恢复已有8组真实监督，共同HF父模型下frozen与普通SFT各7/16；UNVERIFIED：纠正监督是否比等源普通成功SFT更有迁移价值，或只是修复工具接口。Recommendation：完成有界训练对照，保留计划/示例等强简单方法。Conditions：接受动作不等于最优动作；同任务两类轨迹不算两个来源。Risk/exit：若简单goal/合法动作/循环控制已解释收益，停止复杂学习候选；保留形成与失败总成本，不让训练内存资格阻塞独立任务。First action：闭合现役五臂比较；恢复owned8B后执行已备第二环境，再测保留实际进度的恢复，不追加框架。

当前32个闭合baseline及对照材料已私有镜像：`alfworld_frozen_and_native_baselines_v1_20261107.tar.gz`，10746成员/27367833bytes，SHA `68023591e37f2624a810f5d66319bc417bb53c6515f5eab49af1c30bafa12d04`；双端逐成员核验。原监督薄包见上述历史段。另有闭合训练/部署薄包`alfworld_learning_and_deployment_v1_20261107.tar.gz`，87成员/57,243,487bytes，SHA `1459c7fe6dd7723502643ac40735b1dc2c0551d537da3c3e7444b6e134f63cdf`，双端逐成员核验；含两adapter、不含16GB共同父模型与在途评价raw。frozen16闭合薄包`alfworld_common_parent_frozen16_v1_20261107.tar.gz`（4130成员/24,264,221bytes）SHA `cc8c635f7d28d94b8d25551c8633641fbb19933525805d1d9a52cec5847e4cab`，双端逐成员核验；未复制仍在写入的恢复服务日志。所有包均非公开分发。
