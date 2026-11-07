# ALFWorld：执行纠正与学习开发

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。两臂SFT已完成，三种模型臂各16题闭合，普通历史两臂继续比较，尚无新方法贡献。

四现场能力诊断与旧分账已移至[已关闭的先导实验](ALFWORLD_CONTEXT_STUDY.md#teacher-pilot)；本页保留当前结果和下一动作。

## 监督来源速览

27B从头执行16/18、从12个学生现场恢复8/12；两者成功交集只有7组（4heat/2cool/1look）。普通/纠正轨迹分别67/68个接受动作；失败和全部形成费保留。完整导出、token标签、来源hash和教师成本见[已闭合监督材料](ALFWORLD_CONTEXT_STUDY.md#teacher-supervision)，不再默认加载全过程。

## 当前动作：完成历史基线，再检验持续短历史

普通/纠正轨迹成功交集为7个任务/布局（普通67动作/2,865监督tokens，纠正68/2,950）。按双方成功取交集是common-support条件分析；唯一clean纠正任务被排除，因此训练只含heat/cool/look三类，不能称覆盖全部失败。配对记录`recovery_supervision_v2/ordinary_recovery_pairing_v1.json` SHA `dc0f6b6a6c464b53c16d708e51ee33d0ba61157bbe351f7e678f782d4eba5fcf`。全部形成与失败成本不因筛选删除。

两臂使用同HF8B、seed17和新q/v LoRA r8/alpha16，各完成192次更新并保存/重载。合计2,270,472序列tokens、16,617监督tokens；普通/纠正训练用时1579.43/1600.13秒，监督tokens各8,239/8,378。同来源/初始化/更新数不等于完全等成本。原计划、实际receipt、旧工程失败和owned窗口恢复记录见[闭合训练](ALFWORLD_LEARNING_RUNTIME.md#learning-runtime-history)。

仅D使用owned18104研究窗口，共享35B/27B保持常驻，结束恢复原8B argv/cwd与健康。五臂统一绑定HF导出的BF16父模型（SHA `505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3`）；旧AWQ-compatible Q4不直接套新LoRA，旧成绩不作本批对照。坐标诊断、HF/adapter哈希和CPU导出证明只查[运行绑定](ALFWORLD_LEARNING_RUNTIME.md#deployment-bindings)。

同7组普通教师轨迹另备`reference_history_v1/BANK.json`（SHA `eca70c91e604aa1c35304121760b062203bfecc0a92dd2225997ada6ec073870`）：67接受动作和1次实际invalid_action，公开文本合计13216bytes；不造thought、不含heldout。选择仅用公开goal类别、同类public_text hash首项，缺类固定fallback；clean无训练例。这是同来源普通历史对照，不是完整ReAct复现或全量token匹配；两臂完整ICL结果待闭合。

两次训练0步工程失败（初始化顺序与OOM）及定向文件缓存诊断见[闭合工程现场](ALFWORLD_LEARNING_RUNTIME.md#learning-runtime-history)；没有把它们计作学习负结果。

独立数据复核读取361份原SSE和135配对训练行，无差异；只允许7组暴露任务上的有限学习开发，不是训练器或泛化审定。`learning_comparison_v1/independent_data_review_v1.json` SHA `2cf11cceebef3c06caeb07ebd7f6b7a04807fd930c9a6abd21757ebd132859b8`。训练源码/CPU loss与梯度检查另行验证，不将mock通过冒充真实GPU训练。

## 新布局与第二环境

另冻结16个development-heldout任务：clean/heat/cool/look各4，16布局/UID；排除原28个已知布局。`heldout_pool_v1/POOL.json` SHA `5f1eb3820881d797867c8348e71559a57d339a753bb88ef5b7bf70530095be00`，资格SHA `3ff9f90bb2a254f38db43817d73df84b42095a818554d19199161deace9b3e65`；官方expert/native控制16/16通过，CPU89.53秒，无替换。仍是官方train来源的本地开发留出，不是跨来源或正式确认；expert轨迹为EVAL_ONLY，禁止进入训练。原18配额因可用heat/cool合计8布局而需9不可行，先改四类各4并冻结元数据匹配规则，再运行控制；原阻断证据保留。

五臂共同使用同HF父模型/actor/cap，分别报告12个训练已见类型任务和4个未在本轮SFT出现的clean非退化检查，以及整体16题；普通历史只用同7组公开轨迹，额外输入与形成成本分账。协议`learning_comparison_v1/hf_evaluation_v1/PROTOCOL.json` SHA `fc19b701ff61ad00e4884d8bd891c2e68d36ae5b582a0a6113a89c2647fa1bde`；启动前清除复制的旧prefix/三臂字段，原draft保留。每臂fresh进程、只加载对应adapter，实际加载状态另核验。`hf_evaluation_v1/RUN_v2`已闭合，frozen16结果保留。普通LoRA真实加载正确（scale1），但读取器误拒服务新增的空`task_name/prompt_prefix`字段，在任何普通任务生成前停止；原Q4已自动恢复，shared35/27不变。R2 RESULT SHA `6188e2ea570a1dadea6109bd2b65ecda7310966e9ca658a1907b00797b49bbcd`。`hf_evaluation_v1/RUN_v3`已接续剩余64次（controller PID241627，源码SHA `4bd44ba612dc7f0645f6cb3925da4e70180104c20332f2c3825bcd8d1b52d472`），普通臂已实际转发。科学协议/权重/样本不变，按唯一root/receipt SHA统计，不重跑或重复加总这16题；完整学习比较尚未完成。首次启动竞态及来源见[工程现场](ALFWORLD_LEARNING_RUNTIME.md#learning-runtime-history)。

HF共同父模型的frozen臂已闭合：**7/16 won，primary三类6/12，clean1/4**（heat1、cool2、look3、clean1）。746个请求预算记录中741次实际转发；10,184,855输入＋31,890输出＝10,216,745tokens，缓存输入9,994,186为输入子集。D逐条复算741份原SSE的hash/usage与原生终态及实际采样，0差异，无length结束；`hf_evaluation_v1/FROZEN_ARM_RESULT_V1.json` SHA `77f087dea66571529e5fc64b1be9772d48c217ee3691dda835459943e97fc644`。截至frozen臂闭合，本专题HTTP生成累计4,836 calls/55,985,482tokens（不含后续四臂），训练/研发Agent另记，不是项目全账。旧Q4两接口的结果和来源保留于[闭合对照](ALFWORLD_CONTEXT_STUDY.md#old-parent-baselines)，不充当本共同父模型对照。

普通SFT臂16题亦闭合：**7/16 won，primary6/12，clean1/4**，633个预算请求中628次实际转发；7,806,812输入＋26,788输出＝7,833,600tokens，其中cached输入7,625,705为输入子集，usage/cache未知0。逐条原SSE、实际采样、共同父模型/ordinary adapter及native终态复算0差异；`hf_evaluation_v1/ORDINARY_ARM_RAW_CHECK_V1.json` SHA `63bce2cdce99ad0bac66f90e39d51761dfdcd01464111ae50d461e9278d59faf`。F/O总数相同但成功集合不同；两种历史臂继续运行，最终比较按任务配对。[闭合汇总器](../summarize_alfworld_learning.py)已33项测试通过，只在80条全部闭合后报告配对结果，冻结16条只计一次。

纠正SFT已闭合：**10/16 won，primary7/12，clean3/4**。814个预算请求中807次实际转发；9,658,310输入＋34,115输出＝9,692,425tokens，cached输入9,438,233为输入子集，usage未知0。807份原SSE、采样、共同父模型/recovery adapter与native终态逐条复算0差异；801 tool_calls、6 stop、0 length。`hf_evaluation_v1/RECOVERY_ARM_RAW_CHECK_V1.json` SHA `5eef466664b8c34ca445a8f338ba148a812be7b070f217e0b597b02c803ce7df`。相对F为4新增/1丢失，相对O为5新增/2丢失；总数增3主要来自clean非退化切片，预定primary仅增1题。保留这项正向开发信号，不以总16替换primary12，待两历史对照闭合。

**环境完成与收尾成本分开。** F/O各7个won均正常退出；R10个won中仅6个正常退出，另4个达标后触预算/上下文门。逐tool JSON的完整六字段与native first-won匹配后，R在首次已实际转发成功反馈的请求T之后仍有346个实际POST、4,106,887tokens（cached输入4,060,867为子集）；F/O同口径均0。含T则R为355POST/4,175,209tokens，这是可证后缀费用及全部终态后量的保守下界，不从原账扣除。`hf_evaluation_v1/POST_TERMINAL_REQUEST_REVIEW_V1.json` SHA `935c8eff8591733167b394f18c063b3e3d16dc8cf3ecde5b14cfd0762765a131`。未来全臂一致加native done/won停止门，保留原生10胜与原始费用；工程停止门不算学习贡献。

同16题的27B从头执行成本对照也已准备，`learning_comparison_v1/teacher_reference_v1/PROTOCOL.json` SHA `f458e77dc3098b29654b59486f2b1e5d4c38fe127c16579e8ee04ddd6c2c7e3a`。只完成CPU检查，未生成；须五臂80次闭合并恢复owned8B后，由D显式绑定closed结果再运行，不能与当前批次并发或把教师计作免费oracle。其输出仍EVAL_ONLY。

Django34570已完成新自然问题准备（私有`django34570_development_v1/summary.json` SHA `dd4046ba3b380103c967f7ee0b7d688188fa0b863e1bd8e4e47665c12d96bd28`）：base关键1项报错、gold1/1通过，两者回归13/13；M2M/GFK公开调用在base报AttributeError、gold正常。10次CPU容器含初次权限失败，均保留；gold/test补丁独立于actor源树。新[薄任务入口](../run_django34570_development.py)复用现有derive/计量/独立评分；GB10聚焦12测试/7 subtests通过、实际容器11项可读写边界检查通过，静态准备manifest SHA `43a5c6791d3ff2cfd422f50cf8eb8f6060a976250a0ff78466b07697f19b75d4`。v5已绑定当时恢复态，但actor启动因AF_UNIX路径过长在模型转发前失败；公开probe亦受源0600权限阻断，旧现场保留。最小修复为短自有socket及同hash的只读probe副本，冻结源不动；GB10复验33测试/29 subtests通过。入口已支持显式closed恢复回执，并保留原Q4 argv/cwd/权重与完整进程身份守卫；新`attempts/cpu_surface_v6`已静态准备（manifest SHA `ab040fba656d2ce553e7f257f7b49912aadfc1f6a0b7eb4dbbe9fa8ed95ab446`，0模型/服务动作）；等ALF窗口结束恢复后显式绑定再运行，尚未重跑actor。公开复现为空SQLite查询，不把13项测试算13任务。

后续素材盘点只查官方ZIP成员与opaque hash：`learning_comparison_v1/NEXT_SOURCE_INVENTORY_V1.json` SHA `c236da94b5ebf37a523e9b396f9ce06ad4f00192fea8925f4495f5c2234bcbb6`。已有134个官方valid_unseen JSON/PDDL交集、134个独特game payload，与原18/新16池的game hash无交集；尚未检查全项目曝光、原生运行或专家兼容，不是第二环境或确认结果。不改当前16题，也不把该池用于训练。

本批只检验从reset迁移。后续恢复开发固定取frozen结束时未won/未done且至少一个接受动作的完整前缀，共8个现场；零动作cool_02单列reset诊断。接受动作不自动等于有效进度，不挑近成功片段。各臂重放同一公共现场，用额外且统一的接续额度（候选32POST/600秒，尚未冻结），不把原128POST耗尽写成仍有剩余；world仍总100动作，形成费只计一次。比较最强简单history/公共摘要、ordinary/recovery，并补同接续额度reset控制，以区分恢复特异性与一般能力。旧load_prefix只接受collect及同protocol，后续须显式绑定旧protocol/manifest/receipt/world SHA，不改原回执。此设计未启动，EVAL_ONLY目标输出不回流训练。

[追加前缀加载器](../alfworld_recovery_source.py)已离线实现，显式绑定旧protocol/cohort/manifest/receipt/world哈希并分开新旧额度；GB10联合聚焦38 tests/19 subtests通过。真实16条来源中8个失败前缀可加载，7成功与1零动作来源被拒绝。当前prepare尚未接入，未实际重放world或调用模型；本次不改运行中的组件。

## 两项改变下一步的发现

**持续短历史尚未比较。** 当前drop_recent仅首次交接保留3条公共动作，之后OpenCode历史继续增长；闭合样例第74次转发仍含73个工具回合。新[纯投影器](../alfworld_context_projection.py)逐次保留所有系统/用户目标及最近3个完整工具回合，不造摘要；已核对F/O的1379份闭合请求，目标/采样/tools均保留，尚未接入Relay或运行模型。GB10三模块聚焦50tests/43subtests通过。接入必须发生在采样合入后、body序列化/计费/记录前，不能只改forward的dict而仍发送旧packet。当前80次及已备teacher使用旧组件，先完成这些队列，再发布最小hook。

**最终成功不保证每个接受动作适合作为正监督。** 同7组O67/R68动作的精确LCS合计36；其余差异不自动算错误。针对三条暴露训练轨迹，另做6个无模型native控制（固定源前缀与后继动作，事后诊断）：

| 训练现场 | 原R接受动作/结果 | 删除预选开头片段后 | 观察 |
| --- | --- | --- | --- |
| cool_02，目标pan | 19/won | 删前10步pot流程，9/won | 该片段不是此固定后继序列达标所必需 |
| heat_02，目标hot tomato | 13/won | 删开头cool，12/won | 此次cool可省略 |
| heat_05，目标cup，原持bowl | 6/won | 删放bowl，下一take cup报invalid_action | 此固定后继须先释放持物 |

六次原生reset/源前缀均逐步公开状态相等；共227接受动作，其中168为源重放、59为新探针，环境对照墙时24.21秒、模型/训练/judge调用0。RESULT位于`learning_comparison_v1/teacher_trace_counterfactual_v1/RUN_v1/RESULT.json`，SHA `32945e3f343f3fa25f196a737fe3d77b9b7484ae8391ff89866bb3788506821e`。只证明固定轨迹下这三处依赖，不证明全局最优、一般因果规则或过滤后学习收益。固定后继带有教师后验计划，删除验证不证明部署时无需相应信息；搜索/观察须保留或用真实actor续做复验。后续若试原生反事实监督mask，比较须含目标/持物规则、随机mask及普通混合rehearsal。46成员薄包已双端核验，SHA `6934a6cd1759de698a2f2d01d2b507ba70e3df194dc4aede8a1c5285465a6ddf`；不含在途历史输出。

## 方法重叠与下一验证

Sentry已有失败触发与验证后入库，EMG已有失败/成功轨迹匹配提取知识，STeP已有教师纠正与partial masking；ACE/AgentFold/DGRR等也覆盖局部更新、折叠及依赖撤回。原文方法核对与其余近邻完整保留于[按需精读](ALFWORLD_CONTEXT_STUDY.md#mechanism-reading)。当前SFT是监督来源/能力对照，不是上述方法的新名字；独立贡献仍待实际比较。

## 本轮判读与训练对照取舍

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：同HF的F/O/R为7/7/10（各16题），primary为6/6/7（各12题）；UNVERIFIED：纠正监督是否比等源普通成功SFT更有迁移价值，或只是修复工具接口。Recommendation：完成有界训练对照，保留计划/示例等强简单方法。Conditions：接受动作不等于最优动作；同任务两类轨迹不算两个来源。Risk/exit：若简单goal/合法动作/循环控制已解释收益，停止复杂学习候选；保留形成与失败总成本，不让训练内存资格阻塞独立任务。First action：五臂闭合/owned8B恢复后，依次运行已备27B参照与Django基线；随后统一终态停止门并接入持续K3对照，再决定追加学习及8现场恢复。

历史baseline、训练/部署及frozen16薄包的镜像hash见[私有资产](ALFWORLD_LEARNING_RUNTIME.md#private-packets)，不复制在途服务日志。