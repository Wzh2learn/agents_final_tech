# 代码来源：教师纠正与形成成本

> 状态: 活跃 | 更新: 2026-11-09 | 取代/被取代: 从ALFWORLD_CORRECTION_DATA按主题拆出代码来源；历史锚点保留。

<a id="current"></a>
## 已验证来源资产

**2026-11-10 来源元数据筛查**：对Lite中Django不同PR的关系按`sha256(source_id|target_id)`排序，只读取任务ID、base与GitHub PR merge/compare元数据，不读目标题面或补丁。前七对的source PR merge相对目标base均为`behind`：14017→32450（3提交）、14608→11776（11,880）、16910→21204（734）、15252→32012（1,554）、13220→29838（2,400）、12284→30931（294）、14787→32260（710）。它们未通过当前“源PR合并为目标base祖先”的严格时间门，不用于声称源修复已存在的向前迁移；这不排除源问题在合并前已可被Agent解决。仅7对非全体统计，无模型调用；下一步继续查不同来源，不读取留出目标答案。

**可继续检查的自然任务链**：Matplotlib源PR [25332](https://github.com/matplotlib/matplotlib/pull/25332)已合并，原开发目标[25352](https://github.com/matplotlib/matplotlib/pull/25352)的base在其后；25352合并亦为后续候选`matplotlib__matplotlib-22482`的base祖先（compare ahead 4033、behind 0；目标对应PR [28430](https://github.com/matplotlib/matplotlib/pull/28430)）。本轮仅查ID、base和PR元数据，未读新目标题面/补丁；尚未确认其历史曝光、执行环境或任务适配性，不是留出确认结果。25332是参考辅助源，25352的27B OpenCode三臂均搜索循环且无编辑，其失败反馈本身不能证明源经验失效。后续应先核这条链能否提供可操作反馈，再与同反馈简单规则及无经验比较。元数据回执SHA `d2c3c79539fedd04b3abee7f96a815bba1377f2a7811ecdc593fbfdd22afb78c`，位于下述Sphinx尸检私有目录。

当前方法实验与下一动作直接读[显式控制器对照](#direct-method)；下列原始教师资产与旧四格保留作来源，不作为当前训练成绩。

SymPy21055取得一条**教师辅助、经执行验证的代码纠正**。教师仅接收原公开问题、D定位的源码和实际公开复现反馈；未接收未来目标或gold。它是一条来源素材，不是学习方法或迁移收益的确认。

| 条件 | 实际结果 |
| --- | --- |
| nonthinking，1 POST | 正常stop，输出完整diff；原严格应用因hunk行数错误失败。 |
| 同一diff，Git --recount | 只重算hunk行数，不改生成程序文本；独立原题1/1、回归13/13通过。新增模型0。 |
| thinking，1 POST | 600秒超时，原SSE含16,355字符推理、无答案通道或finish；不是完成的能力对比。 |

重计数控制是在看到第一臂应用失败后选定的后验工程适配；原始失败、超时与raw均保留。原题/回归通过只支持该释放测试合同，未扩充为任意输入正确性。当前不追加同题思考模式重试。

实际两臂消息逐字节相同，只有enable_thinking不同；模型27B、seed17、temperature0.2、32k上下文与8192总输出相同。原始请求/通道/补丁/执行日志可定位；没有把候选代码写回模型服务或业务系统。

## 成本与执行边界

本阶段共3个物理POST：早先空tools被HTTP400拒绝1次，以及两臂各1次。仅nonthinking有完整provider用量：输入3,583、输出456、合计4,039；HTTP400与超时两请求usage未知，**阶段总量未知**，cache未知。旧source的48POST/465,678已知tokens另记一次，不按子臂重复收取。研发Agent用量未完整计量。

nonthinking生成64.885秒，thinking600.001秒；后验重计数及两组CPU评分合计5.616秒、2个评分容器。训练/judge/付费科研API为0。owner已退出、两个owned评分容器已实查不存在、资源锁已释放；共享模型服务未改动，断连后服务内部生成状态未探测。

首次直接CLI预检受旧校验器的全局模块清单影响；固定为stdin/importlib调用后，旧17组件与两个二进制严格一致，未改校验函数或历史manifest。无工具请求只省略空工具字段；传输层兼容检查85项GB10测试通过，原ALF工具合同hash不变。

## 证据定位

GB10私有根为`ROOT/code_source_expansion_v1/SOURCE_ACTOR_PREPARED_V2_BASH_FIX/sympy__sympy-21055/teacher_patch_v2`：

- 协议SHA `77d9a417e23cef5d7a6e3d23c9766ac172057d1d11cf447e073fc5bd190e928c`；准备manifest SHA `44af743dab01224bcb7085de6848dc65c9bd60596a6b9391d724908e877e062d`。
- 主结果false receipt SHA `519023796011a76195055f7b32dbe655ca01f7dee71233d80bb096d202773bed`；true receipt SHA `3234ee92c3c191c7b1987a03fb1ce334c4fdba68b8bb18fd394eeae39f1ac0fa`。
- 后验`recount_evaluation_v1/D_RESULT_V1.json` SHA `abcfd72d6cdce158bcdcd0c6ac2819721cc9ca20263d37fd36943c21d2fe802c`；D闭合SHA `e2ea0e06cf6d77dc40ee87756be218a3d5dc600cda1eb273cacdd88dba6de9b4`。
- 私有封存包`teacher_correction_closed_v1_20261108.tar.gz`，1,922成员/7,233,655bytes，SHA `f43b840d9591257792ae7ac705bccc98c4bd69928964022d2bc68615ba5507f2`；原HTTP400包SHA `da0ae15fdc46963e262bd0b2a9fe2148674de8d309ede19d24b56600fe88ecfd`。模型权重及依赖不在包内。

[单轮入口](../contextbench_teacher_patch.py)；[主线短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。纠正使用与后续目标必须继续隔离，不能把该已曝光source改称新确认。

## 后续代码版本边界

注册候选为21055→9384：源修复merge `4b03990bb9df237c110b8120ffe5ed94c610348c`是目标base `70cd4ffd093ac224fc0226c1be58f9163e2c800a`的祖先（ahead290/behind0）。既有compare索引SHA `c22b36b869f5b3d72827e1a352b15fa62585e6dccfd56297c97e812b669c97e6`，`ANCESTRY_CHECK_V1.json` SHA `c8412bc8d709509fa9336520dd4d19572c65f67dea571f8fa5a4ce6700143603`；本次仅核元数据与汇总，没有重查原始compare。这支持代码版本向前，不证明原issue提出时间或无曝光。目标维持DEVELOPMENT_EVAL_ONLY，本轮未运行它。9384与21309两条题面hash不同，但索引绑定同一上游PR21309与同一base，不能作为两项独立PR修复计数。集合候选16988→16953仍仅有公开行为/时序复现，未获actor资格。

**可复用的目标资格。** 21055的`refine/arg`与9384的`refine/Piecewise`同属假设化简问题。9384历史CPU资格已完成：原题base 0/2、gold 2/2，双方回归各320/320。本轮只读复验GB10现存`QUALIFICATION_RUN_V2/sympy__sympy-9384/clean_base`的1,883文件及公开题面，全部与原冻结SHA一致，没有重跑模型或资格测试。该目录是源码快照，不是Git checkout；Python3.8 ARM环境仍沿历史记录，未整体复验。私有`sympy_refine_transfer_v1/ASSET_STATUS_V1.json` SHA `906a6a1f28603b544097fc1dba6c8013490c754d3be200602bc33b55748be0d2`。已复用现有runner准备双臂隔离输入，gold/testpatch/资格父目录不进入actor；来源只能称教师辅助修复记录，尚无目标迁移结果，不再先重复已通过的资格。

**准备器已复用。** [现有目标驱动](../run_contextbench_target.py)新增SymPy显式分支：none与source_repair_record，固定绑定原教师失败、后验重计数及执行验证。实际执行复用既有SymPy评分器，不把修复记录称为普通成功轨迹。本机45项合成控制通过（导入替身及Windows UID适配）；GB10与ALF准备器合计97项/246个子控制通过，无替身。两臂实际CPU准备及D独立verify已完成，各1,883文件，0模型/HTTP/容器；gold/资格父目录/评分补丁不进actor挂载。私有`ROOT/sympy_refine_transfer_v1/TARGET_PROTOCOL_V1.json` SHA `698785a471942627e60b6dbeb30deb56fa66f5d7d955b21ba3dedd8984765884`及6份元数据已双端镜像；源/目标路径与manifest查同目录。普通none/修复记录两臂暂缓运行，作为新反馈机制第二环境的复用资产；尚无目标模型成绩。

## 取证条件研究：已核资产与简单对照

11-09只读复核后，保留两项开发来源，不重跑已有资格：上方SymPy21055→9384，以及[Django12589→34176](DJANGO_AGGREGATION_PAIR_QUALIFICATION_20261106.md)。Django的65项与219项SQLite测试指向同一退出后的候选目录、同镜像/runtime/只读挂载，后者发现一项回归；缺少两个时点的完整树hash，不能认证逐字节不变。测试扩大不等于外部环境改变，旧65项通过仍是真实局部证据；两次约1.061/0.874秒，也不支持直接把宽测试称为更贵。

Django源/目标base分别为`895f28f9cbed817c00ab68770433170d83132d90`/`016bead6a23989adec5c7ee6948db7ce2fc5e89b`；目标base/gold 0/6→6/6、双方回归166/166。PG原题探针是独立PG15环境，不能混作上述SQLite范围比较。原receipt与宽检查分别以私有`django_teacher_source_20261106.tar.gz`中的`07533253…f7ac2b5`/`2e582442…50febcc`定位，完整SHA沿资格记录解析。

上述两个历史时点的字节同一性仍未知；下方新增同一固定快照的复算，不追认旧时点。两项目仍属已曝光开发来源，目标与隐藏检查继续隔离。

<a id="joint-development"></a>
## 联合记忆与取证：开发现场

**新固定快照复算。** 私有`ROOT/django_aggregation_agent_20261106/memory_evidence_development_v1/CURRENT_REPLAY_V1/RESULT_V1.json` SHA `e549bc3b3b05744f4570c907d10f027afa59d1145af7989d68ba295e291d2968`：候选前后树hash均`55f42bf3…42009f1`，65/65通过、219项中1失败/1跳过，分别0.837/0.938秒。公开源投影6,192文件，树hash`b1fb79d5…548dd3c`；私有16行测试overlay只进入评分端。纯公开快照单测亦已重现`3 != 2`，不是只凭带overlay的旧日志给反馈。

**成功门同时保留原修复。** D复用旧测试恢复及固定SQLite环境，独立评1项原题、65项回归和219项宽检查；不接PG。原base未过原题，当前修复过原题但未过宽检查，两者65项均过。两组CPU控制支持评分器能区分“撤销旧修复”与“修复新回归”；最终门须三组全通过、宽检查保持既定1跳过，仅代表此SQLite合同。

**学习原型。** [数据合同](../joint_memory_program.py)只接受有限query ID，不执行模型文本；未知/超预算结果不做训练负例，同输入成功比较成本采用Pareto规则，形成成本另记。标量偏好loss是普通参考式，尚非可训练实现或方法贡献。

**四次真实提案。** 私有`ROOT/joint_memory_reacquisition_pilot_v1/RUN_V1/RESULT.json` SHA `a5fe01084594a5671e53b62268084e637bfdda77fa063182335e2e671c5cd107`，27B/非thinking，两类prompt各seed17/29：4 POST，输入5,594/输出900/合计6,494，usage齐全、cache未知。严格whole-JSON为0/4；仅去完整外围栏后的诊断中，两个joint为数组、两个summary仍为string。原始失败保留，不重复生成补格式。writer已见两份公开代码读取片段，因此空query不证明回读无用。

D另删除一条生产函数记录并实际读取67bytes代码，完成算子检查，未形成偏好。独立C四提案复核SHA `f6cad8fd26d51a1e87686b153f4ebe362ba5753f5c3446c49dec9759dac5cfff`。

**普通恢复已闭合。** `D_READER_RESULT_V1.json` SHA `654703efe405a11e92964073164f8df4afa72db9f630fb179f8fd5c056009db1`：27B/seed17，无memory/无预读，12实际POST、13次relay尝试（末次封顶拒绝），输入107,482/输出1,062/总108,544tokens，cache未知，151.086秒。20次bash均只读/搜索，无生产编辑；独立原题1/1、回归65/65通过，宽219仍1失败/1跳过。此前摘要的21次计数经C按raw更正为20次。`GENERATION_FAULT`源于封顶403；只说明本次有界控制未完成，不能断言模型无修复能力。

**四格已闭合。** 同一D整理六record，交叉保留/删除生产函数记录×是否预读67bytes；所有臂仍可自主读公开repo。同27B/seed17、各12POST/300秒/16MiB，使用[复用入口](../joint_memory_program_runtime.py)。实际结果：

| 记忆 / 预读 | POST | provider tokens | bash | 新编辑 / 恢复 |
| --- | --- | --- | --- | --- |
| 保留 / 无 | 12 | 87,001 | 17 | 0 / 0 |
| 删除 / 有 | 12 | 89,661 | 19 | 0 / 0 |
| 删除 / 无 | 12 | 132,663 | 23 | 0 / 0 |
| 保留 / 有 | 12 | 91,097 | 20 | 0 / 0 |

四臂均在第13次relay尝试被本地帽拒绝，原题1+65保持通过、219仍同一回归。五臂共99条命令只读/搜索，未跑测试或编辑。独立参考正控1+65+219全过（既定skip1），SHA `ebe010b53b99af08f80b9f4495b2513404da738cf305d88f01917a12591426d6`；参考从未进入actor，非方法收益。

批结果SHA `d8e46a6d416b23f5eb4aff7db0a517ed2768f7d9a380b0f147ffd8a58ed7ad5c`；D闭合`D_CLOSEOUT_V1.json` SHA `b87a0e67d2bb72d6e5c65525001a143bb9d89307109973f2ebca5493cd6cecc5`。连同普通控制及四writer共64实际POST、输入508,854/输出6,606/总515,460tokens，usage齐全、64条cache未知；5次本地拒绝不算模型生成。形成历史不重置，训练0；token是用量，非等价新增计算。owner已退出，5个actor容器均实查不存在。

C独立核全部60条reader SSE和此前4writer，复核请求/采样/账本、99条命令及评分日志，无阻断；`C_FACTORIAL_CLOSEOUT_V1.json` SHA `4762fa8d1c8c2f5fa45f93ecb2223079684ea61ffb2034a7bbbf7213a8a65b4e`已私有双端镜像。1/65/219是相互重叠的评分集合，不相加为独立样本。四格闭合包`joint_memory_factorial_closed_v1.tar.gz`双端290成员＋索引校验，2,821,797bytes，SHA `019b201291086dff9a246ef8442795f0c898456505793056d557e5ffb776d14f`；后写C复核以独立sidecar hash绑定，不改旧包。

**裁决**：停止此非thinking/12POST单例分支，没有恢复偏好或训练方法效用证据。删除改变长度/位置、预读改变交付时机；单来源/单seed后验开发不作因果确认。下一扩独立source，复用已核真实Agent工件与依赖；Matplotlib25332源及25352目标已有失败，不能当未运行来源。旧目标的执行阻断或饱和不冒充新确认。

已闭合提案/普通控制与公开source快照的私有包`joint_memory_development_closed_control_v1.tar.gz`已双端逐项校验：19,474,055bytes，6,369证据成员＋索引，SHA `eadc70b242754aa2fd8b6e705e33b194304483d7c728b8952c53305502c35ece`；排除在途四格、权重与依赖。新数据合同/运行器GB10定向19项及21个子控制通过；不代表方法或泛化成立。

**旧正向工件补入索引。** `ROOT/django_aggregation_agent_20261106/attempts/teacher27_thinking_low_source_20261106`已有27B thinking-low修复：`source__none__seed7201.completed.json` SHA `ec4b3a362e0d50004d4ef492b3bfc1812ae01bca4451a7c9d6d0a784a5dd0449`。其`query.py`修复通过PG原题及SQLite原题1、回归65、宽检查219（既定skip1）；actor本身2400秒超时，54POST、53次完整usage共891,947tokens，末次usage未知，不能记成正常完成episode。原始请求确认nested thinking=true/low，seed7201；与上方非thinking/seed17/12POST并非同预算因果对照。退出后反馈不证明actor已见；历史包SHA `9987712bd65327a953520d8b798d06b7393eec88ad5cc899560653e16f24fdd1`已双端保留，不为重获该资产重跑。

<a id="source-expansion"></a>
**独立问题扩样。** 私有`ROOT/joint_memory_source_pool_v1`按兼容版本/回归成本事先选4道Matplotlib来源题，非随机代表样本。26020的6个截短参数名经原生collect的49个唯一节点补全；V3 base为1项原题失败/48回归通过，gold为49通过，receipt SHA `8eaf5d38dd2c2c58b0695ff316de85dae4e83cc11cf078e57984babca8354a30`。22711完整执行2原题＋91回归：base两原题失败，gold两原题通过；双方回归90通过/同1项PDF跳过。仅在新development合同事后声明该已观测skip，原严格覆盖仍为不完整，另报`LIMITED_RUNTIME_SCOPE`；receipt SHA `fe2d8915bf1618f6392910974ec9329d4587598ade604a187bddb3757fa4fa86`。23913另有真实回归失败，不放行；24149转义选择器未解，不猜测。旧pair/target/默认门不改。

复用原生Python3.10 ARM依赖/扩展投影，并非各commit完整重新编译；没有安装依赖或新增warning豁免。4次archive下载、原生base/gold/collection/config共10个容器（含一次collector缓存写入失败），科研模型0。首个V3驱动缺父目录，在Docker启动前失败，保留原记录后另启；不计模型请求。新source支持显式27B thinking-low与首个生产编辑后的preforward现场：256MiB/30,000文件/累计30秒上限，失败为UNKNOWN，READY只保证字节稳定。实测安装版OpenCode接受关闭自动压缩，config receipt SHA `fadde246299e555c681ff2b7c0ba8b33f44fac33771a100113a23efef44f2924`。

GB10主树新鲜联合测试197项/120子控制通过；不是原生模型结果。两个实际CPU准备已完成，manifest SHA分别`e6bf98c27e7d4d554e93970051505aa7f9cec5c64dfa826f2141aa08782058c8`、`5fb412bf17aa0c144ddcdbf5e7914bed56b57ab359a33bcbed25291f9eb18518`。后续只做至多两道新source采集，各48POST/1200秒/64MiB，固定seed17、32k/8192、串行运行；先完成固定快照复核，不重跑旧失败面板。它们仍属同项目开发来源，不是跨项目确认或训练方法证据。

**采集收口。** C限域复核SHA `997725c93a9bda0e330acdd0d1fd52ffa6c1cb9fc039c7ce937b17d0b96afe8c`后真实运行：26020为26POST/407,000tokens，1200秒超时，第27次本地deadline拒绝未转发；22711按用户要求转向直接方法实验而中断，为16POST/115,834已知tokens，末次usage未知。合计42实际POST/522,834已知tokens＋1未知；不重置或隐藏该失败成本。26020首编辑checkpoint READY；22711捕获达到30秒门为UNKNOWN，不作为合格现场。

独立评分原26020中途及最终工件，各为1原题失败、48回归中38通过/10失败，无缺失；两份回执SHA `d0f5f0851d06e2da1530da9a05cda1be715f710b209a652f5e9ba0c522055d88`、`74d18eada8e3f70e64a15e4da8e9360b8740abf6666cb87af26539f9a00d168a`。完整源码hash前后不变；计数相同不自动推断失败节点完全相同。停止来源扩跑及该现场的提示追加。

<a id="direct-method"></a>
## 直接方法实验：控制器显式选择

**提示式DEFER已停止。** 私有`substitution_mechanism_v1`从26020同一READY现场运行KEEP/DROP/DEFER，各27B非thinking/seed17、6POST/180秒；共18POST/173,350tokens，usage齐全。三臂均无新编辑，原题仍失败、回归38/48通过。恢复client均调用0次，但三臂均用原生sed/grep回读同一源码，不能写成“没有重新取证”。它没有形成有效替代对比，不训练、不追加同例预算。结果SHA `b12aca6b406a9fe90985f057beb401e91c0e3b015d1680660506c8a799f66c0b`。

**显式动作已取得真实监督。** 改用已经验证有能力的SymPy21055单轮修复；三臂同公开题目/反馈/27B非thinking/seed17，控制器实际保留/省略/读取源码，再由固定模型生成diff。统一使用事先确定的`git apply --recount`，不改变生成代码。原生评分复用既有1项原题＋13项回归，测试与参考均不进入模型。

| 控制器动作 | 观测 | provider tokens |
| --- | --- | ---: |
| KEEP完整源码 | 补丁可应用，原题1/1及回归13/13通过 | 4,039 |
| DROP源码 | 幻觉代码上下文，补丁在共同recount下仍无法应用；未进测试 | 959 |
| QUERY结构＋refine_abs | 补丁可应用，但新增未定义处理器，测试在导入/收集时失败 | 1,492 |
| QUERY结构＋refine_sign | 只替换近似等长的实际处理器片段；补丁无法应用，未进测试 | 1,762 |

四次实际POST共8,252tokens，usage齐全/cache未知。KEEP请求体与旧正控逐字节相同；两种QUERY只读修复前真实源码，未虚构尚不存在的refine_arg。SIGN是在前3次结果已知后选定的一次来源开发，不是独立确认。绑定见私有`sympy_substitution_v1/INPUT_MANIFEST.json` SHA `564fc36b20a1b1e6b665984823d6a36b57432d0282daa69f505191dea6cec56c`及对应release/receipt/raw；模型token不等于新增计算，query读取时间另记。

**自然版本/任务变化四臂已闭合。** 21055的真实修复记忆迁往9384后，NONE、MEMORY、QUERY、BOTH均未改变预算末源码；独立原生评分均为原题0/2、回归320/320。NONE在180秒超时、usage未知；其余三臂正常生成但补丁无法应用，分别1,489/3,395/4,080tokens。QUERY/BOTH读取当前两文件61,820bytes，只呈现11,004bytes局部结构，不能称完整源码。4实际POST、8,964已知tokens＋其中1条未知；8个评分容器移除，owner均退出，服务端取消未核实。绑定私有`sympy_transfer_utility_v1/BUDGET_ENDSTATE_RESULT_V1.json` SHA `eae9f92744fd00e9f660b5212e004772f03b7932a9711a4c5f0e7d830bc47ef6`。这检验跨任务经验复用，不是同任务执行中保留进度的确认。

**最后一个上下文控制已闭合。** 无旧经验、完整提供当前refine.py与piecewise.py，模板15,720input tokens，连8192输出及512余量共24,424，小于32,768，未截短。新900秒/8MiB预算不改旧180秒合同，旧超时NONE不作公平新预算对照。实际1POST，15,720输入＋713输出＝16,433tokens，正常stop；补丁在refine.py:316无法应用，末状态仍原题0/2、回归320/320。receipt SHA `eafe6b73725e8c93c3195b6a16cb55a8497f474227fa42f3bb505aead8ad83f8`。两文件完整不等于相关上下文充分：D只读冻结gold的文件头，6个被改文件均在assumptions引擎及core/relational.py，不含上述两文件；现有两个F2P对应satask/relational，公开Piecewise行为的覆盖未充分证明。题面版本/哈希未见串换，但不能据此断言任务合同错误或模型无能力。停止9384提示/预算追加，不拿此面板训练或裁决学习方法。

**方法取舍。** 21055完整源码成功、局部片段失败，说明取证内容需覆盖实际执行需求；9384没有形成有效方法监督。独立质疑指出，四格交互项是已有回报的线性组合，普通联合Q可表达它；新增交互loss不作为独立方法。主攻取证后的局部经验重构：按实际反馈，仅改动影响后续行动的经验条件/内容，保留无关经验和已发生的外部进度。训练在同前缀续做候选中，优先成功，再取最低实际修订/执行成本；不是按文本相似或一条裁判判断失效。部署只执行所选查询和修订。与同数据/动作/反馈的普通联合策略、全部保留/重读和简单失效规则比较，检验结构化局部修订的学习增量；并非仅提出新loss。候选未训练、未证明新颖或有效；134 valid_unseen保留。

**闭合证据同步。** 此处source采集、提示式对照及两组SymPy筛查合计69条已确认POST、729,833已知tokens，其中2条usage未知；不是全项目成本。私有`evidence_packets_20261106/joint_memory_method_screen_v1.tar.gz`有760成员/14,393,685bytes，SHA `2d054a3885c2a589e40b8f0d9afb3039330aef7443ea9b5a44f3db3ec06b781d`，GB10与本机包hash相同并逐成员核验760/760。排除源码ZIP、整树副本、依赖与合成扫描fixture，原始完整树仍在GB10；包不是独立完整运行环境。成员索引SHA `f6e2b0d68765e60bc497c18834f4fa0e294fddf2c334a9dc3f8ed6af4c15d749`，仅私有保留。

## Sphinx 新来源：公开问题与实际运行（11-09）

数据集源ID `sphinx-doc__sphinx-8282` 对应上游[修复PR #8282](https://github.com/sphinx-doc/sphinx/pull/8282)及[问题 #7785](https://github.com/sphinx-doc/sphinx/issues/7785)；目标ID `sphinx-doc__sphinx-8127` 对应[问题 #8127](https://github.com/sphinx-doc/sphinx/issues/8127)及[修复PR #9104](https://github.com/sphinx-doc/sphinx/pull/9104)。ID不全是issue编号。

物化公开时序对 Sphinx8282→8127 的固定源码/问题，金补丁与评分补丁只在评分侧。8282实测base原题1失败/回归16通过，gold原题1通过/回归16通过；8127的39个原始节点先因 `::context::` 标签在当前pytest下4次退出4，保留失败。依据base/gold各自原生收集到的一致41节点，将32个标签去除非测试源码节点 `::context::`、7个保留，全部唯一映射；映射后base原题1失败/回归38通过，gold原题1通过/回归38通过，无跳过。原标签及初始失败未改；私有映射SHA `d2eaf7a8e0f372ab0c21c6b771a5bed8c89a04191fa8693870acfc0822b75e2c`，评分资产双端包SHA `7a1799f59204f2a3afc544eceb08cbfe21b6fb8ba4ac7f3e396866e0f5488f15`。

复用现有计量Relay及隔离工作区，27B/OpenCode对8282实际24 POST、208,774 tokens，下一请求预算拒绝后退出1；最终源码与base逐文件相同，独立评分原题1失败/回归16通过。24个bash步骤均为读取/搜索，后段四次重复相同grep及反馈，且至少后3次实际请求含先前相同输出；未编辑或运行pytest。评分是actor退出后的反馈，当时并未收到；不能归因重复为唯一原因。旧运行未改，actor receipt SHA `2957d2dbb228530402b3fa3500f9003494a7135493d78f4e203f9cb279b5c7d7`，评分SHA `174866a42ca393c9defc96a66694322d62ea4ba4a81b1b0e880c99677fac2257`。后续已依据对应公开问题及已读源码尝试有界纠正，结果见下；金补丁未作为actor输入。

**公开复现与一次教师提案。** 按对应公开问题 #7785 的最小Sphinx示例实际构建，`autodoc_typehints='none'` 时重载函数仍出现类型提示；未用评分补丁。27B仅接公开复现输出及原Agent已读源码，一次POST消耗5,177输入/298输出 tokens，生成候选diff；原样应用因围栏/损坏hunk失败。事后仅去完整外围栏并用 `git apply --recount`，不改生成代码，候选可应用到隔离副本；评分原题仍1失败、16回归通过（SHA `444e025f0fb6916a54635381332b53fe67132ff5de9fbfa1334149bce6b089f6`）。评分显示部分函数类型提示消失，但类 `Bar` 仍有类型提示；此为事后评测反馈，教师此前未见。该候选可作为部分修复素材，不能称任务成功；与24 POST的OpenCode运行接口不同，不作方法收益对比。原样应用失败、机械适配与评分均保留。

**一次真实反馈后的修订。** 另给同一27B一次请求，输入首次候选、公开源码与明确标注的评分文字“函数示例已隐藏类型提示、Bar仍显示类型提示；原题失败、16回归通过”，不提供测试源码、金补丁或未来8127信息。此时源任务评分已用于开发，源原题不再是独立确认。新增1 POST/2,686 tokens，原样Git应用成功；独立评分仍原题1失败、16回归通过，类的类型提示消失但出现重复 `Bar(x, y)` 签名；该重复是模型输出后的评分观察。评分SHA `f66999bcd8f659b2170d5c911fd303c92bbeb8504b043160389f596fae0264b6`。累计OpenCode及两次教师请求26 POST/216,935已知tokens，未知usage 0；不额外重试，继续保留原始失败与修改。

两次提案的初次回执顶层 `attempts: 0` 与实际不符；嵌套计量及原始ledger均记录1次实际POST，累计26次按物理调用计。完整证据包双端SHA `c059639cceecbf7fc0734ffd096a9434b918a9b671808b6768ecc064c92d09c5`；其中含评分侧私有测试/参考材料，不提供给actor。

**2026-11-10 失败链尸检与受控点检。** 原27B/OpenCode轨迹有24次bash、21个不同命令，无编辑或测试；同一搜索及其输出在第17、18、22、24次出现，不能称四次连续。另一个SymPy源的同一复现命令和输出连续33次；Matplotlib目标三臂分别连续34、38、37次，后者52次bash对应48次模型请求，不把工具动作当独立任务。这些轨迹支持识别搜索停滞，但提前停止只省下后续无进展，尚未证明能恢复任务。

Sphinx教师第二次修订虽隐藏了类的类型标注，却逐个追加隐藏后的签名：原本`int`与`str`两种重载都显示成`Bar(x, y)`。本轮在私有评分副本做**事后人工控制**，同一初始候选和冻结测试：原候选原题0/1、回归16/16；只对类去重仍0/1，首个差异转到`Math.sum`；对函数、类、方法三个输出分别保持顺序去重后为1/1、回归16/16。在教师修订候选上运行原公开问题复现时，函数`foo(x)`重复2次；三个位置同时去重后为1次。原工件未改；仅支持此有限测试范围内的失败解释，不能当Agent自主修复或方法泛化。零模型/零训练，CPU隔离测试；私有`ROOT/sphinx_8282_8127_development_v1/autopsy_signature_dependency_v1/RESULT.json` SHA `3264ab4d033e251563126d767206939ba848bf6df405c988e6a3eef4e087beb3`，公开复现结果SHA `9293dec5d98a10b1747e6b9eb908d540c28be29ccf0e073b1a5d67f874cd526d`，代码与日志同目录。该源题的评分已经暴露，仅用于开发；后续用OpenCode加本地模型在其他任务上验证“修复局部时保留并复核关联约束”，与普通反馈修订及简单规则等信息对照。

**下一项有界开发合同（新模型调用前）**：先在上述已曝光的Sphinx源题，用相同真实部分修订工件、公开题面及原例前后输出，比较OpenCode＋Qwen3.8-27B普通自由修订与“已满足/未满足约束”结构化提示。两臂均提供相同的人工追加开发要求：隐藏类型标注后避免重复签名，及先前改动涉及的三个类名；不提供本轮人工去重代码或评分测试。相同seed17、temperature 0.2、32K/8192、24 POST/600秒/64MiB，依次独立运行，记录全部实际请求、源码变化与成本，退出后由独立评分副本恢复测试。两臂的公共反馈相同，提示形式和长度不同；结论仅为单源开发信号。若两臂均未改善或简单臂已完成，不继续围绕此题调提示；若形成信号，还需不同任务、简单规则、相同反馈、形成成本和相关方法验证，不能据此宣称新方法。源代码现成候选来自两次教师提案，带人工开发信息，不能称独立自主来源或预注册确认。

两臂隔离输入与仅源题挂载的CPU检查已准备，尚无新模型请求。私有`constraint_feedback_pilot_v1/PLAN.json` SHA `b50fe694e3ff5b114b93afbc3a2bd97cfe8509c8940d3cc7e1667ed41f5a7bac`；`PREPARED.json` SHA `6ee57ce5328352063e9a91ab3b5b587670d6a81ed7001d391552e7a0fa508ffc`；输入、驱动、模型配置及两臂manifest均绑定于其中。原候选与clean base逐文件比较仅生产源码1文件不同，私有评分补丁不进入actor挂载。

## 先前准备与故障记录（迁入原文）

以下为原页面代码来源段的完整历史文本；其中“下一步”指当时状态，当前裁决只看上文。

<a id="source-tool-contract"></a>

**两源尸检已核。** `SOURCE_EPISODES_AUTOPSY_V1.json` SHA `52b958f5b39914c37017824e356ba9d56555a9b37907d7f30ad26311ebdb5727`：A共7次工具，D再核324绑定与96原SSE，合计input1,105,961/output5,586/total1,111,547tokens一致；96条cache未报告。每题48动作均只读/搜索、无编辑或测试，47轮后继工具反馈逐字带回，首user题面完整。确认实际只开放bash，而其说明禁止读写/编辑并指向未开放工具；这是能力/说明合同冲突，未证明它导致循环，亦不把两次失败当纯模型能力或反馈学习结论。先做source专用的最小合同修正和隔离写入验证，不改ALF/生产工具面，不直接重跑整批；source参考辅助纠正为低成本后续选项。

**工具说明修正与真实写入控制通过。** source专用v2只在转发前深拷贝替换唯一bash的说明，保留schema/messages及其他字段，非法工具拒绝；不改ALF或生产面。GB10 Python3.12聚焦57项通过，C限定静态PASS（SHA `1b1859f5b29ec70f16f7b52a247d817cb7c0a83371e4e1c831f07f642b1d9580`）。独立4POST/120秒/2MiB控制实际2POST、25.77秒、56,724wire bytes，1次原生bash真实写入并读回28bytes；D复核19绑定、原SSE和容器清理。receipt SHA `b8e914788bcaccf6aab7cc4dd639787993095b1648e1c28b9d41dd733d73ecaa`，D复核SHA `f0f8d6924735941ba8a2626a9196b55ce075a4ab55eb05af58cd27d8ac5afe96`。新增input5,341/output153/total5,494tokens，cache未知，训练0；旧96帽未重置、SWE题未重跑。只确认此次通路，不归因旧循环或认证修复能力。

该控制薄包21成员已双端核验，SHA `37516f9214d85400d8e082f0de583d44708e808c76396790a64acb7e3e834048`。新临时树仅5个受控修改与28缓存；五文件/patch及Git基线655afb2e已私有镜像，代码包SHA `aedaff8004b7e01bb9210294ac18b179023163aa18ebccf86ad9dad55dd7b1d8`，D核17组件的快照或Git重建后只移除这棵新测试树，7个历史树保留；收尾SHA `c11a983e20cc4edc8f1434b78bf5e294bdaac22aff1873b573ec6bf01f5fe6d2`。C9在本机/GB10各两harness定向分发，LF SHA `a496be2764834b097c9defd174d6eccd803573d146faa760dd19b8263c776ef3`，未声称全技能库重验。

**Bash-v2的已曝光来源开发重试已闭合，未形成成功来源。** 仅SymPy21055，新根`code_source_expansion_v1/SOURCE_ACTOR_PREPARED_V2_BASH_FIX/sympy__sympy-21055/attempt_v1`，manifest SHA `c1cbc8bcca58d6a5d32ac9322b777773bb4d8bc476676a508ebbf304bbaf71ba`；runner SHA `b2377f352cc824100c70bfb3340c0c9b78e3722d777b2fe113ed75b695c6b86d`。原题/wrapper与旧源一致，工具说明为既定v2；source-only输入未读未来9384题面/gold。D另给48POST/1200秒/64MiB，不重置旧96POST账；release SHA `85f43117f351875eef8106c9525e742a36a968c0c74767c23a91e38aea132076`。owner `1925392`/birth `1085721038`及3个owned actor/评分容器均已退出，锁已释放；未并发ALF模型、未重启共享服务。

实际48模型POST/49尝试，末次为封顶拒绝而未转发；输入461,600、输出4,078、总465,678tokens，usage未知0、cache未知。actor墙时714.981秒，两个独立评分容器合计4.527秒；训练/judge/付费科研API为0。源问题F2P0/1、PTP13/13完整覆盖，代码差异为空；模型运行真实公开复现后，重复同一命令33次。原receipt保留GENERATION_FAULT，403仅表示正常预算封顶；未修复判断由独立评分支持，不当作已查明的工具/模型单因果。

D核全部48原SSE/实际工具合同/请求hash/封顶账及容器清理；closure SHA `f92f4bb287b216cfb8401e6862656df6139e13416496b2b65c673bc2481ffb1a`，原receipt SHA `5d9cc82cd7a069e2b39b47920fcafa844b27c49ab0ff9f8733f99786824144fe`。私有薄包183成员/742,006bytes，SHA `9dd91038692e93b97319dd3fbb33bfa15d3e0d905e4aa19fc6b3b97cc7cb8825`，本机逐项核182文件。源码/依赖沿用原资格资产，不用参考patch冒充Agent成功。

**历史设计（已执行，结果见[当前结果](#current)）：同输入单轮教师代码修复能力对照。** 同27B/seed17/32k上下文/8k总输出，非thinking与thinking各最多1POST，只有请求级思考开关不同。输入限本来源的公开题面、源码和真实执行反馈；D定位辅助不冒充完整自主Agent。输出补丁在隔离工作区检查并原生评分，严格保留reasoning/content、格式或长度失败、调用和形成成本。固定模板具有True分支，但旧source入口强制False且False计数器不能套用True；当时只准备薄衔接与CPU验证，尚无True实际请求或新训练。不继续同配置48轮重试；必要时比较明确标记的source-reference辅助基线。新增[SymPy集合候选](ALFWORLD_LEARNING_RUNTIME.md#sympy-intersection)仍仅作公开行为素材。

当时[单轮入口](../contextbench_teacher_patch.py)与49项CPU检查已完成，尚未prepare或生成；后续实际执行由页首结果取代此状态。真实分词初检将BatchEncoding的2个字段误作长度，旧证明保留为无效；修复后按一维整数token计数，False为3,583、True为3,619，加8,192输出与512余量均小于32,768。协议SHA `983a80057a21db5863bf08a7a3f9de2f438ff778ed815a6b8d0d6ac878adaf67`；实际CPU复核SHA `76e67530e5eb66e72080325bed3a9230aab8351d03f09555092270ca7202088b`，模型/环境/容器0。它是代码来源的能力诊断，不把它设为其他已合格ALF来源继续研究的统一前置。

报告保留两项byte差：每题wire计数比原SSE body多6,720bytes。冻结relay明确wire另计HTTP响应头，body文件不含头；单位不同，不据此判断token丢失或超帽。动态头原文未归档，未声称独立重建每字节。两源闭合私有包349成员/2,068,583bytes已双端核验，SHA `3d3ac3fa60fcc0ac078204f96113e43397863a0aa67eb6e2e7d44e6399c2de63`，本机check SHA `973a88f07660ea1d4efdf6b7cf2091d22090b9942b6bd861007b9c05514c8d8a`；尸检报告随后单独镜像，不重打原包。

[Current result](#current)
