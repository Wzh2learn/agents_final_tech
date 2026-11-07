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

后续素材盘点只查官方ZIP成员与opaque hash：`learning_comparison_v1/NEXT_SOURCE_INVENTORY_V1.json` SHA `c236da94b5ebf37a523e9b396f9ce06ad4f00192fea8925f4495f5c2234bcbb6`。已有134个官方valid_unseen JSON/PDDL交集、134个独特game payload，与原18/新16池的game hash无交集；尚未检查全项目曝光、原生运行或专家兼容，不是第二环境或确认结果。不改当前16题，也不把该池用于训练。

定向来源核对补齐了训练7组的14份普通/纠正manifest身份：与134候选的task UID、完整family、layout、game hash交集均为空，但去掉布局后仍共享3种目标模板、9个候选。报告`learning_comparison_v1/NEXT_SOURCE_TRAINING_OVERLAP_V1.json` SHA `fa1d19a265ef5314f329c63d68119959cbef4a81f9fe7c39431b7ad58e2adf06`；未重验训练行或全项目暴露。候选134个trial只含47个family和4个布局，类型与布局部分共线；后续须按组设计，不能按134个独立样本报告。

第二环境增量准备使用现有ContextBench Lite与Django/SymPy隔离依赖。元数据过滤剩21个关联候选目标（非全项目未曝光认证），按题目hash选得Django31051、SymPy9384/19006三目标及其较早来源；`ROOT/next_code_source_inventory_v1.json` SHA `114f22de08c94404909720ff950a61bbe0f0e39be4503bfe289616caf1c1081c`。上游`created_at`仅作排序，实际核GitHub源修复merge确为目标base祖先；`code_source_expansion_v1/ANCESTRY_CHECK_V1.json` SHA `c8412bc8d709509fa9336520dd4d19572c65f67dea571f8fa5a4ce6700143603`。源码准备阶段共下载3份官方commit归档：6次公开元数据HTTP＋3次源码HTTP、0模型/环境/训练；归档清单SHA `bc92d85748b67ea41fdfe67c85f169289429a526936c1d6d15bf021259d402d7`。CPU资格合同SHA `8b9d0977494184c8e61eeafde308143fdc4dc293bf401b8b8b9c541f1b3c6017`；先复现base/gold及全部已发布回归，再决定是否用作新开发任务，不把源码时序通过当任务修复资格。

已集成[统一CPU资格入口](../qualify_contextbench_pool.py)，首轮`QUALIFICATION_RUN_V1/receipt.json` SHA `6b43065ab2d70372d34258ad276b3a023b4aaffb16c65d6c79f28bf5511f3f14`返回NOT_QUALIFIED，但分题结果可用：SymPy9384的2个F2P全部base失败/gold通过，两侧320个PTP全部通过；Django31051在Python3.12缺distutils、未进入测试；SymPy19006的4个F2P成立，两侧PTP均46通过/2失败，首错为旧AST构造False常量的ValueError。后两者不当方法负结果，不豁免既存回归。最小修复复用已有冻结Python3.8给历史Django运行，同时区分pytest XFAIL/XPASS且仍拒绝non-pass资格；16tests/32subtests通过。`QUALIFICATION_RUN_V2`已闭合（receipt SHA `a3c7eef5d3b803dba02992d553d9858bf3e8385ace1d4c33435c750221044aa0`）：Django31051的12个F2P全部失败→通过、两侧25个PTP全通过；SymPy9384保留完整资格，19006仍未通过且不豁免两项。整体仍为NOT_QUALIFIED，不冒充三题全绿；仅两题进入开发EVAL_ONLY注册表`QUALIFIED_TARGETS_V1.json`（SHA `01493c013446b832b084aa914a578d4a0b0fe5b2645665792d59f43a7479da2f`），其较早经验源的后续资格见下段，真实轨迹尚未采集。两轮共24个实际测试容器、测试段墙时合计240.99秒、0模型，源码SHA `d05c12e757dae2d4c55261f62af89fb9ddec6830cbb6733dab9df3bdb23ffad8`；三题/源码/patch/标签不变，完整conda库树未冻结。它与六组实验仅并行占CPU，不发其他GPU请求；墙时不作为隔离硬件下的因果成本比较。本轮A临时worktree已合并并仅清理13个重建缓存，7个历史资产树保留，Agent上下文保留。

本批只检验从reset迁移。后续恢复开发固定取frozen结束时未won/未done且至少一个接受动作的完整前缀，共8个现场；零动作cool_02单列reset诊断。接受动作不自动等于有效进度，不挑近成功片段。各臂重放同一公共现场，用额外且统一的接续额度（候选32POST/600秒，尚未冻结），不把原128POST耗尽写成仍有剩余；world仍总100动作，形成费只计一次。比较最强简单history/公共摘要、ordinary/recovery，并补同接续额度reset控制，以区分恢复特异性与一般能力。旧load_prefix只接受collect及同protocol，后续须显式绑定旧protocol/manifest/receipt/world SHA，不改原回执。此设计未启动，EVAL_ONLY目标输出不回流训练。

**两对代码任务的经验来源已完成资格。** 仍复用同一A，不新建Agent：扩展入口以原Experience标签逐项绑定具体测试方法，未放宽旧三target资格。`SOURCE_CONTRACT_V1.json` SHA `8c48cb051323c396fb50d05994c3b0a67cacb92afb902e644c04faa336b57df7`；8个真实CPU容器、测试段15.26秒，Django12453的1个F2P失败→通过、两侧5个PTP通过；SymPy21055的1个F2P失败→通过、两侧13个PTP通过。D复核491个输入hash、原始测试日志及clean源码树；19 tests/47 subtests通过。`SOURCE_QUALIFICATION_RUN_V1/receipt.json` SHA `576dec0cc19d342d50c8ebfd65b90dde8c123ba7e1fd199545dde209ad638ab2`；两对注册表`QUALIFIED_SOURCE_TARGET_PAIRS_V1.json` SHA `de086acea81dcfae7bdc6e3276a05e7c8ff02e0c6ce38a989bb9f1560a39838f`。经验源为12453→31051、21055→9384，源码修复merge均为目标base祖先；新增2次官方source归档HTTP，扩展专题累计11次非模型HTTP。此为参考/测试资格，不是Agent成功经验；source真实轨迹待模型窗口释放后采集，目标仍为EVAL_ONLY，gold/隐藏测试不进actor。

[追加前缀加载器](../alfworld_recovery_source.py)显式绑定旧protocol/cohort/manifest/receipt/world哈希并分开新旧额度，联合聚焦38 tests/19 subtests通过。现已对8个合格失败前缀实际重放：322个接受动作及全部公开reset/逐步状态均相等，8个owned world均关闭，模型/训练0、环境段墙时合计23.35秒。5个heat/cool/look为主比较，3个clean作诊断；7成功与1零动作来源被拒绝。`additional_recovery_v1/NATIVE_REPLAY_RUN_V1/RESULT.json` SHA `32b93d6d436d973d9e2e7ed53d9db6e6d444aefe581589dfe3d9f5fcb8c2577f`；来源协议SHA `466815d7b75026d3605f88e3504a4c54502792878dd13b90e4697e3b57a567d4`。接受动作不保证有用进度；公开重放不证明全部隐藏状态等价。当前prepare未接入、未做学习恢复比较，不改在途96回合组件。下一恢复阶段另给32 POST/600秒，world总100步、各现场尚余27–92步；旧形成费只计一次，不按每臂重收。

## 下一批：六组而非重复训练

采用C协议审阅给出的96回合精简设计：O/R各做完整与持续last3工具回合，另含frozen_last3和all7_last3；同暴露16题、primary12和clean4不变，0继承旧episode、0新增训练。重点同时报告R-O两条件的差值、配对交互及R对两个简单短历史基线，不能只看交互或挑有利对照。last3保留全部系统/用户/来源历史锚，不是固定总token或3条world动作。`runtime_context_baselines_v1/PLAN_V2.json` SHA `49b44eaa69c623dc1c544925c779620039c7c00b39d77ea029b8cbbc859697be`；分析合同SHA `465faabb09a40cc9ad291ecbd9032e6fa08efec3bbebb58b09edb1e2a6b95dfc`。原128草案和原文字节修正链均保留，未实际运行。

新actor/taskpool代码导致旧pool精确代码绑定失效，未放松守卫或改旧receipt；同16资产在新根`pool_v2`真实重做16/16零模型expert/native控制，90.92秒，题目/UID/layout/game/traj及公开reset均与旧池一致，不计新样本。新POOL SHA `b922dd1a108754f31d862a56bd97eb4cee4e665be6b59279b4e8c7433a465b64`、qualification SHA `304e38e4b927f274bcf7e7b72f8071820dcde0e30da1e6cd8d3337f001adaaed`。新witness还对旧80份实际native记录全量解析匹配，SHA `e514868d57713f23e5d6a3e121cd6be99c4fc18dd346cee9519691747f579967`。

独立Terra/max预启动审阅发现并复现C1（共享身份异常挡住可安全尝试的原Q4恢复）和C2（cap/终态标志掩盖异常退出）。同一A续接修正：保护异常保留且独立恢复安全owned实例；137/-9拒绝；exit0/1都核raw SHA及顶层错误，只有匹配实际403/409拒绝证据才作为正常gate，普通工具错误反馈保留。V1/V2原回执均保留，同一C限定复核V3放行（SHA `7677c9d8dfd3ac9587487ef1746c38c5b59828c90246b0ebc3a5de0833c99661`），没有另起Agent重做实现。root远端实际133tests/380subtests通过；4个actor/pool组件未因审阅修正再变，未重做native资格。

代码已合并；driver SHA `ce8f29296929a120f293a107f6d8612d917aea4f76b426ee7dd619070c16ad7d`。旧源码和原五臂费用保持，ROOT闭合源码/C薄包已双端核验18成员，SHA `a10e86f96986a16c6ca6c027df9c75750158252239665083f8e4b9639c60a60a`。预启动检查为纯CPU/假数据及旧native档案核验，不证明实际409或方法效果。

`RUN_V2`在终态409重试时受控停止：clean_01上限失败、look_01原生成功，实际136POST/613,202tokens与原输出全部保留。400永久终止响应经真实OpenCode假接口及GB10聚焦136tests/389subtests验证；原Q4已恢复，35/27不变。接口事故、完整成本与双端私有镜像见[闭合运行记录](ALFWORLD_LEARNING_RUNTIME.md#terminal-retry-20261107)，不当作学习方法负结果。

现已从固定源码`8fcfc342`启动`runtime_context_baselines_v1/RUN_V3`（PID748995/start1077529568），使用新attempt14–19、0继承旧回合；同六臂/16题/权重/种子/caps及原统计对比。`PLAN_V3.json` SHA `3e7d9814c12a96fb1723977f252278b54527d61cd8f622330974710ad446a8d1`，分析合同SHA `f43382c981d691e123130b4d1a320cd447e920fa6a9bccd6ea1c71eced987f82`；明确记录旧2题结果已知，不是独立确认。新精确源码绑定的同16资产native/expert复验16/16、142.23秒、0模型；pool_v3 SHA `afe5d0deffa3380b34b39bbc398df10c774b51fd164a8cb4b88dbe632cb784ad`。同一C限定代码审阅无阻断，回执SHA `d8826d2f4ffa5f32f476916580093abd3407e445ef01780b7a0fcaeedc709557`。已实际核look_01在5动作/8POST后36.35秒自然收尾，新增1次终态拒绝即exit1，raw为400/Bad Request/isRetryable=false，native won保持；其receipt SHA `c4c84f79bc74aa810b21a484cf3d8cebb46fc18e33c506e96b80bc18e2b9044c`。全96结果尚待闭合。

## 两项改变下一步的发现

**持续短历史需要与学习增量分开比较。** 旧drop_recent仅首次交接保留3条公共动作，之后OpenCode历史继续增长；闭合样例第74次转发仍含73个工具回合。新[纯投影器](../alfworld_context_projection.py)逐次保留所有系统/用户目标及最近3个完整工具回合，不造摘要；离线核对F/O的1379份闭合请求后，已接入Relay且在上述真实body核实生效。投影发生在采样合入后、body序列化/计费/记录前；六组结果闭合后再判断短历史能否解释学习差异。

**最终成功不保证每个接受动作适合作为正监督。** 同7组O67/R68动作的精确LCS合计36；其余差异不自动算错误。针对三条暴露训练轨迹，另做6个无模型native控制（固定源前缀与后继动作，事后诊断）：

| 训练现场 | 原R接受动作/结果 | 删除预选开头片段后 | 观察 |
| --- | --- | --- | --- |
| cool_02，目标pan | 19/won | 删前10步pot流程，9/won | 该片段不是此固定后继序列达标所必需 |
| heat_02，目标hot tomato | 13/won | 删开头cool，12/won | 此次cool可省略 |
| heat_05，目标cup，原持bowl | 6/won | 删放bowl，下一take cup报invalid_action | 此固定后继须先释放持物 |

六次原生reset/源前缀均逐步公开状态相等；共227接受动作，其中168为源重放、59为新探针，环境对照墙时24.21秒、模型/训练/judge调用0。RESULT位于`learning_comparison_v1/teacher_trace_counterfactual_v1/RUN_v1/RESULT.json`，SHA `32945e3f343f3fa25f196a737fe3d77b9b7484ae8391ff89866bb3788506821e`。只证明固定轨迹下这三处依赖，不证明全局最优、一般因果规则或过滤后学习收益。固定后继带有教师后验计划，删除验证不证明部署时无需相应信息；搜索/观察须保留或用真实actor续做复验。后续若试原生反事实监督mask，比较须含目标/持物规则、随机mask及普通混合rehearsal。46成员薄包已双端核验，SHA `6934a6cd1759de698a2f2d01d2b507ba70e3df194dc4aede8a1c5285465a6ddf`；不含在途历史输出。

## 方法重叠与下一验证

Sentry已有失败触发与验证后入库，EMG已有失败/成功轨迹匹配提取知识，STeP已有教师纠正与partial masking；ACE/AgentFold/DGRR等也覆盖局部更新、折叠及依赖撤回。原文方法核对与其余近邻完整保留于[按需精读](ALFWORLD_CONTEXT_STUDY.md#mechanism-reading)。当前SFT是监督来源/能力对照，不是上述方法的新名字；独立贡献仍待实际比较。另核[Memento](https://arxiv.org/html/2611.00244v1)已有学习笔记/上下文重建，[SkillApt](https://arxiv.org/html/2609.26863v1)的一般形式已有状态、模型与成本条件效用；STeP混合普通/纠正监督，当前纯O/R小LoRA不是其复现。不能仅因某公开实现较窄而声称状态选择或混合纠正为新机制。

## 本轮判读与训练对照取舍

Mode为inquiry-methods / minimal-experiment，结合research-driven-design。FACT：同HF的F/O/R/all7/top1为7/7/10/7/6（各16题），primary为6/6/7/5/4（各12题）；UNVERIFIED：纠正监督相对等源普通成功SFT的增益是否可重复，以及持续短历史能否解释它。Recommendation：先统一工程停止门、比较执行全程的K3与完整历史；若R仍有残差，再扩独立纠正来源并比较普通混合rehearsal、可见目标/持物规则和反馈衍生监督。Conditions：接受动作不等于最优动作；同任务两类轨迹不算两个来源。Risk/exit：若简单goal/合法动作/循环控制已解释收益，停止复杂学习候选；保留形成与失败总成本，不让训练内存资格阻塞独立任务。First action：六组last3对照闭合后，先以现有O/R权重比较同一保留现场的实际恢复，再决定新训练；已重放8现场、两对代码source/target资格均可复用。O/R必须同历史表示、目标、公共反馈及新增预算；reset参照不能在新增world步数不同的情况下充当状态特异性的因果对照。

新增64条闭合raw薄包已在GB10与本机逐一核验14,052成员，SHA `0995fa01149373591fea14cea126a9112f229430f1a2e8558c554acb2ac2c9b0`（manifest SHA `9018cfabed3d9e2113080a7dc01cb36f0fda9acf2178a4594e3020ef0f6db733`）；与先前frozen16包共同覆盖80条，未复制仍写入的restore服务日志。历史baseline、训练/部署及frozen16薄包的镜像hash见[私有资产](ALFWORLD_LEARNING_RUNTIME.md#private-packets)，不复制在途服务日志。

代码资格私有包`code_development_qualification_v1_20261107.tar.gz`已双端逐成员核验76项，2,704,064bytes、SHA `267bf996950f25cadfddd2e7a5390d761ad6b8d36b074a98bc44d3a79f847532`；保留两轮原结果、命令、逐test状态、错误与注册表，未打包完整candidate/gold树，不是公开artifact。

后续两source与8个保留现场的闭合证据包`source_pairs_and_preserved_states_v1_20261107.tar.gz`已双端逐成员核验88项，17,256,211bytes、SHA `2eec08f3e78d52038472e8f62bd0d69b33676961fb1f3a42869b54742e487ae0`（manifest SHA `4a5647676e2cc8277ec6fc0c82cee27c5dcb624eb73bfd74c95d8409718118aa`）。本机另逐条核8个公开重放日志的322动作及回执hash；不含在途96回合或完整base/gold工作树，不作actor输入。
