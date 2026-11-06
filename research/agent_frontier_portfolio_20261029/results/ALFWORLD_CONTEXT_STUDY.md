# ALFWorld多任务上下文研究

> 2026-11-07 | 本主题原地接续；模型与原会话历史见[ALFWorld记录](ALFWORLD_TEXT_AGENT_20261106.md)。当前执行次序见[唯一短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。这不是论文确认结果。

<a id="current-multitask"></a>

## 专家评审后的18任务开发批（2026-11-06）

Goal已由用户明确恢复。主线使用既有8B/27B，不重启或等待4B。新增无日期[pool接口](../alfworld_task_pool.py)与[通用study](../alfworld_context_study.py)只服务这项实际扩样，复用固定CBC/bridge/relay/依赖，不改旧runner全局。pool位于`context_study_v1/pool`，POOL SHA `dea42177269e1c0bcb870641a68cc0aef2136ad7741bfe28da36de7c855819d2`，qualification SHA `600811f2cea740abc884af7f8a97db40ffd47ae189364c60a4478c6d6da85b19`。

18个官方train任务覆盖clean5/heat5/cool4/look4，18个不同layout，排除旧8题＋legacy2题的10个布局/任务UID。先按hash选择、固定经验分配和运行顺序，再运行18/18 native expert/实际bridge逐step一致资格（0模型、无替换，最长84步）；这不是模型成绩，也不证明预训练隔离。clean1/heat1源各9例，history/skill各9例，是真实冻结旧经验，不预贴有益/误导标签。

协议`context_study_v1/PROTOCOL.json` SHA `2fb92f35b20ae00e03183da837e92218240233180df9d3f9cf6d14383170843d`：原world总100动作；总128POST/1800秒/64m bytes，收集阶段32POST/600秒但world仍100。恢复四臂为经验保留/移除×完整/最近3条目标公共动作，各臂共有当前目标、公开state、模型/工具和剩余额度。完整仅指accepted world轨迹投影，不是原harness全部失败命令；当前state保留全部admissible。各阶段共享普通stop未won最多原session续做一次，单列首停和最终结果。真实collector和跨臂cohort冻结门拒绝fake、不同来源或协议，原形成成本只计一次。

冻结前C只读审阅核对来源/隔离/重放/预算门与18池metadata；其不覆盖后续统计推断。确定性focused验证22tests/99subtests；owned fake实际OpenCode→真实world→原session续做为3假POST/1look/1续做，真模型0，回执SHA `7ccc229c001161270c14ab471ab53ee7e6ad32995847b24c798a288a1c8b3a81`。初次fake在qualifier字段处提前拒forward，0真调用，旧raw与代码保留；不是模型负结果。

### 首两题的真实收集

按冻结顺序运行clean_01与clean_02，8B显式nativeFalse/seed17，未按结果换题。

| 任务 | 原生won | 首停won | 真POST | 实际新动作 | Provider tokens | Cached input子集 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| clean_01 | true | true | 8 | 7 | 81,431 | 69,878 |
| clean_02 | false | false | 32 | 25 | 354,434 | 339,634 |

clean_01无需恢复，不能据此断言经验有因果收益。clean_02在预设收集POST上限截尾，usage完整，原world非终态；它是budget-censored prefix，不称自然失败。两题新40真POST/435,865tokens，旧经验形成成本按原账引用，不在每臂重复加。receipt SHA依次为`70ea08da8393c3e4cecd13e04e807ee1766d837879c269baf8f697cf1d33c916`和`fd755318e5eb6f2f897cc271f1881658d9023495d22cc01d7ab66fe8759b6e24`。

初次恢复预检重放25步均相同后，仅在旧replay输出所需`public_prefix_sha256` metadata适配处出错，恢复真模型0；追加纯函数回归后在新attempt接续，旧形成不重跑，原cohort文件/hash不变。代码与原始失败在`initial_batch_v1/frozen_code`和私有旧attempt保留。恢复结果查`context_study_v1/initial_recovery_v1/RESULT.json`，四臂均从clean_02同一现场、同额剩余cap开始；不把此单一cohort认作方法增量或多任务确认。

### 首个恢复cohort与能力诊断：已返回

| clean_02同一25步前缀 | 原生won | 新动作 | 真POST | Provider tokens | 终止说明 |
| --- | --- | ---: | ---: | ---: | --- |
| 8B drop_recent | false | 7 | 10 | 60,639 | 普通stop后同session再继续一次，仍未成功 |
| 8B keep_full | false | 39 | 39 | 589,340 | input＋8192预留output＋512余量触上下文门 |
| 8B drop_full | false | 40 | 41 | 599,200 | 同上下文门 |
| 8B keep_recent | false | 41 | 42 | 596,064 | 同上下文门 |
| 27B drop_full | true | 23 | 24 | 271,073 | 事后能力诊断，普通首轮已成功 |

五次原生重放都逐项核对同一reset＋25步公共反馈，四个学生臂同一cohort/source hash；所有199个已保存请求均nativeFalse/seed17/max_tokens8192，实际196个forwarded模型请求有完整SSE usage，其余3个在本地上下文门拒绝，不能当模型调用。模型成功以won判，不以exit或最终文本判。所有实际首请求的完整task原文或SDK可逆编码均验证。

四种8B上下文条件在这个现场没有恢复成功；3臂受固定上下文资源合同限制，并非输出length截断。27B在相同公开信息、工具和剩余cap上成功，表明本例存在较强actor可完成的路径；它是事后能力诊断，不是记忆方法收益，也不证明所有学生失败只由模型能力造成。

本批实际196模型POST：两个collector40，四学生恢复132，教师诊断24。Provider总2,552,181tokens＝2,543,737输入＋8,444输出；已知cached输入2,183,533是输入子集，27B未报告cache细分，不能填0或把全部输入当同量新增计算。旧clean1/heat1经验形成成本按原manifest引用；本批来源收集仅物理计一次。无训练、judge、付费科研API或生产写回；研发Agent控制层成本另账，完整财务账单未知。

原始SSE逐条重读、body SHA、usage逐POST求和、真实payload参数、task交付和cohort/25步重放一致性复算见`context_study_v1/MULTITASK_RECOMPUTE_V1.json`，SHA `21d31cf7c6477234a63be2160306c9e6947bc25db02c35d6e540ba8284e9718b`。四臂与教师receipt哈希均列在该私有回执，不在启动文档重复。此首批仅2个目标/1个恢复cohort；后续18题结果另列，不扩张首批证据范围。

### 下一行动

扩独立前缀池后再比较恢复策略，并补从头不加载经验的强简单基线。学习选择器尚无正向必要性证据；目标重申、摘要与近邻按短计划推进。不围绕clean_02调参追求正例，也不等待4B。初批固定顺序不支持独立的墙时因果比较，后续确认需平衡顺序并按任务/来源分组。实际状态读对应batch的RESULT/driver。

### 工程验证与发布边界

GB10本轮focused四文件43passed/155subtests；本机docs lint0fail/3既有时效warn、上下文/链接检查与diff检查通过，变更18文件secret scan无真实凭据形状命中。skill-doctor0errors/134既有warnings，定向map0重复/0未解析。C8源已同步本机两个既有安装副本；GB10与Git发布终态另实测。没有重跑全仓pytest，不宣称旧FinQA fixture问题已修复。源码/协议的旧epoch保存在私有frozen_code及旧attempt，重放旧collector须用其快照，不以最新HEAD假充原运行源码。

## 18题收集已返回；接续多任务恢复

`context_study_v1/collection_sweep_v1/RESULT.json`已返回`ALL16_COLLECTIONS_RETURNED`；PID4020003已退出。它按冻结顺序完成其余16题，仅收集真实执行及未完成前缀，无替换、教师或训练。原控制器Q下`run_context_study_collection_sweep_v1.py`与ADMISSION保留，不能重启覆盖。该批360真POST、4,060,606tokens；合并初始两个collector为18题、400POST、4,496,471tokens。

独立零模型复核18个manifest/receipt、400份原始响应body/SSE usage、完整task/载体交付、原生won及282个动作，差异0；`COLLECTION_RECOMPUTE_V1.json` SHA `7112a26845d800074e9af2f47754b01a72d69911cc21ad9726c5903c954aeb16`。输入4,479,553，其中cached4,280,169；输出16,918；usage/cache未知均0，cached没有再加进总量。

| 目标类型 | 成功/任务数 | 自然未完成 | 调用上限截尾 |
| --- | ---: | ---: | ---: |
| clean | 4/5 | 0 | 1 |
| heat | 1/5 | 1 | 3 |
| cool | 0/4 | 2 | 2 |
| look | 1/4 | 0 | 3 |
| 合计 | 6/18 | 3 | 9 |

这不是经验增益估计：所有collector都加载预分配经验，没有从头无经验对照。任务、来源和载体分组也不是随机化因果结论。独立只读尸检发现cool_01拿着apple时反复寻找tomato，并两次heat apple；heat_01则按目标heat mug后完成。它们支持继续区分目标跟踪、持物/动作约束与历史信念，尚不能归因旧经验。

`context_study_v1/recovery_sweep_v1/RESULT.json`已返回`ALL12_RECOVERIES_RETURNED`，原owned PID4037300已退出，study lock可取；控制器Q下`run_context_study_recovery_sweep_v1.py`不重启。选取规则是在冻结顺序中对尚未测试的每个任务类型取首个合格未完成现场，即look_01、cool_01、heat_02；三题各跑原四臂，保留全部结果，不按恢复成败换题。原source不重跑、每题共用同一cohort，其他合同及arm_order不变。ADMISSION记录选择规则、source receipt、源码与driver SHA。

look_01四臂均won=true，cool_01与heat_02四臂均false；新增249真POST/3,376,233tokens，unknown usage为0，4臂在上下文门停止，其他未完成按实际普通stop等状态保留。结合旧clean_02，当前4个恢复现场的成功集合完全相同：只有look_01成功。删除经验、截短初始历史均未增加成功现场；不能据此归因旧经验，但本面板没有成功率上的策略选择空间。

独立逐响应SSE与receipt复算差异0；replay分别6/23/30行（source步数＋reset），全部equal，每题四臂的cohort/source/protocol一致。`RECOVERY_SWEEP_RECOMPUTE_V1.json` SHA `d80ab5b9f8404aeb95feff9aa74642d54c57541a26c972b30dc0118de1a9a209`。新249 POST的输入3,365,213（cached3,258,612）、输出11,020；另4次本地预约未forward，不算模型调用。224次重放控制动作另记。三个source的93 POST/978,264tokens已包含在18题collector账，不能再加进全批物理账。

| 四现场恢复汇总（source费用另计一次） | 成功/现场 | 真POST | Provider tokens |
| --- | ---: | ---: | ---: |
| drop_recent | 1/4 | 31 | 180,557 |
| keep_full | 1/4 | 136 | 2,128,168 |
| drop_full | 1/4 | 107 | 1,464,380 |
| keep_recent | 1/4 | 107 | 1,448,371 |

当前固定drop_recent以更低实际调用/输入成本达到相同观测won，复杂选择器暂无必要性证据；小样本和截尾限制仍在。这改变下一步：先检验两个强简单控制，不扩大选择器或重训actor。`collect_none`沿用同一冻结题面、模型、seed、32POST/600秒及统一续做，仅从头不加载旧经验；`goal_recent`在原drop_recent末尾只重复已有公共目标，不给步骤。前者和恢复臂分别分析，不把起点不同的成绩直接相减。新条件事后开发、非确认；待旧actor结束后再发布绑定新代码的运行。

### 强简单控制：22个episode已返回

新代码`34c7055d1bc53e6442d567b069f81067d86714ef`已在旧actor全部退出、lock可取后发布到本机/GB10/GitHub。GB10四文件focused为45passed/167subtests；对18个旧collector任务逐字节重建一致、18个none和4个goal公共输入零模型核对通过。独立静态审阅未见阻断，不替代模型结果。本机unittest的symlink项受Windows权限限制，实际完整验证以GB10为准；没有重跑全仓测试。

`context_study_v1/simple_controls_v1/RESULT.json`已返回`ALL22_SIMPLE_CONTROLS_RETURNED`，原PID4053364退出，不重启。控制器Q下`run_context_study_simple_controls_v1.py`保留。固定队列先clean_02/look_01/cool_01/heat_02的4个goal_recent，再按原顺序跑18个collect_none，无替换或调提示。原source只引用；新none从相同reset重开任务。ADMISSION绑定driver/hash、源码epoch、原18份source manifest/receipt及完整queue。每次none还核对与旧collector的caps、sampling/profile、assignment及reset原文一致。

普通带经验为6/18，无经验3/18；带经验新增成功clean_01、clean_03、clean_04、heat_01，同时look_01从无经验成功变为失败。另两题clean_05、look_03两条件均成功。它是同一开发seed下的双向现象，不支持一律清空；原baseline继承整个经验附加段（含公共提示与wrapper），尚未隔离语义内容与通用示例/提示作用。4个新增成功都来自history载体，唯一损失来自skill载体；事后“history则加载、skill则不加载”在本面板即可达到7/18并覆盖两条件成功并集，复杂初始选择器还需越过这个简单规则。

4个goal_recent仍仅look_01成功，73 POST/817,960tokens；原drop_recent同样1/4，为31 POST/180,557tokens。目标重申未增加本面板成功现场，停止继续改写该提示。22个控制合计514真POST/4,594,978tokens，usage unknown为0；其中18个none为441 POST/3,777,018tokens。全量独立SSE、完整输入、18对reset/caps/profile/sampling与4个goal replay复核差异0，`SIMPLE_CONTROLS_RECOMPUTE_V1.json` SHA `6b903f0f7897d4a6dce4a615e3d07772975ec08d21f45b933d5fecd70e1206b3`。新增输入4,569,506（cached4,395,991）、输出25,472，本地未forward预约0；27B后续不混入该账。

截至新控制开跑前，多任务主线累计805真POST/9,989,020tokens（含18个collector、16个学生恢复及1个27B诊断），这是本专题范围，不是整个项目总账。新22个控制另增记；无训练、judge、付费科研API或生产写回。上述旧批次全部终态，无须再等历史marker。

旧批完整私有证据薄包`alfworld_18_collections_four_recoveries_v1_20261106.tar.gz`已双端保存并逐成员核验：4,928成员、26,811,943字节，archive SHA `67e8d9c8d2c5f13ccc1ae3ab59ec02792dd7b7211af99990d8e892758fd72ed4`，manifest SHA `727fd9cd448751630212af1e19daa727d8f942798f4e6264c63d2231d61f7915`。不含workspace、私有game/专家原轨迹、缓存或权重；不是完整runtime，也不是公开artifact。它不包含后续simple_controls。

### 自然失败现场的教师恢复：已返回

`context_study_v1/teacher_state_batch_v1/RESULT.json`已返回`ALL6_TEACHER_STATE_DIAGNOSTICS_RETURNED`，原PID4073951已退出。固定三个自然未完成source加clean_02校准，补两条8B recent后测四条27B recent；学生0/4、教师3/4，剩一题触上下文门。新215真POST/2,863,108tokens，实际原生重放、相同公开prompt/caps及SSE复算差异0；`TEACHER_STATES_RECOMPUTE_V1.json` SHA `1bf001d43834b4d9a691b151c7a76eca4bb74b6958c011b647d165708a4fee90`。

三个成功是可执行纠正候选，不是学习增益；模型能力和实际计算不同。完整结果、账本以及新启动的8现场教师采集只在[现役纠正记录](ALFWORLD_CORRECTION_DATA.md)维护，不在本页追加采集日志。

进入本6诊断批前，本专题累计1,319真POST/14,583,998tokens，原source物理只计一次。Paper E与对外动作不在本批范围。

暂停时仅对核验argv后的当前owned controller发SIGTERM，handler会退出当前episode并保留receipt/未知usage，清理actor/relay/world；不停止模型服务。case中断不作为正常方法失败或合格收集样本。该锁只约束本study driver，不宣称跨机器全局预算锁。

初批发布回执（历史）：科研代码`d1566f021542ec319cb7aa3f4cc9fc561412df35`当时三端refs一致，本机clean、GB10保留Loop B日志修改。C8版本`509a50605e3c44d6f04c0cb89a6c6276b3c31dd8b757cb8d59896b711d3e18bb`当时两机器各两个既有安装副本一致；本轮没有再改skill。后续代码/文档发布与当前HEAD分开，以实际Git为准。

首批私有薄包SHA `b23fae27524bb5f6e1401a1316487bb9cea1d9b091cca684c4e705f28fb26bf9`，1,294成员；原会话控制包SHA `647a9de772f40ccc6f427de53c97121eddfb80e6d37253c4ae6b1423c1f1957a`，218成员，均双端逐成员核验。排除workspace、原game/专家轨迹与缓存；没有权重/凭据或公开artifact。它们不包含后续批次。


<a id="teacher-pilot"></a>
## 教师四现场能力诊断（闭合历史，2026-11-07）

固定取三个自然未完成source（cool_01/cool_04/heat_03），加clean_02校准；后者不是新任务。补两条缺失8B drop_recent后，与27B在相同原source、公共目标/观察、最近3条accepted history及总cap比较，已有学生结果不重跑。教师不用专家动作、隐藏事实或参考计划。backend能力/实际计算不同，这不是等计算方法比较。

| 现场 | 8B won / POST | 27B won / POST | 27B新动作 / tokens |
| --- | --- | --- | --- |
| clean_02 | false / 10 | true / 16 | 15 / 128,280 |
| cool_01 | false / 12 | true / 12 | 10 / 80,968 |
| cool_04 | false / 63 | false / 47 | 46 / 681,234 |
| heat_03 | false / 71 | true / 6 | 5 / 33,449 |

27B成功恢复3/4，提供3个不同任务/布局的实际纠正候选；不是3个独立环境，也不是人工gold。成功轨迹仍须按真实tool结果、执行合法性、角色与来源检查后才能导出监督。cool_04的27B也触输入＋8192预留输出＋512余量的上下文门，不能称其任务不可解；它保留为失败和后续长轨迹分析，不混进成功监督。暂不围绕单例追加提示变体。

批次`context_study_v1/teacher_state_batch_v1/RESULT.json`为`ALL6_TEACHER_STATE_DIAGNOSTICS_RETURNED`，原PID4073951已退出。新6条共215真POST、2,863,108tokens＝2,853,227输入＋9,881输出；2条学生134 POST/1,939,177tokens，4条教师81 POST/923,931tokens。已知cached1,891,711仅来自学生输入；教师81次cache细分未知，不能填0。usage unknown为0；另3次本地预约未forward。

复用冻结独立审阅脚本的纯解析函数，逐条重读SSE/body SHA、输入绑定、原生终态和重放，四对prompt原文/caps/cohort/source相同；差异0。`TEACHER_STATES_RECOMPUTE_V1.json` SHA `1bf001d43834b4d9a691b151c7a76eca4bb74b6958c011b647d165708a4fee90`。它是确定性复算，不是新独立人工/统计审阅。

本批结束时本专题累计1,534真POST/17,447,106tokens，source形成只物理计一次；这不是项目全局账，研发Agent与更早形成/训练成本另账引用。没有新增训练、judge、付费科研API或生产写回。

两个增量私有薄包已在GB10和本机逐成员核验：`alfworld_simple_controls_v1_20261106.tar.gz`为3,080成员，SHA `7edfbc4635a5f175343dddb4721f6182e4efcb473c661cf15933d2c2479669a4`；`alfworld_teacher_states_v1_20261106.tar.gz`为1,241成员，SHA `52358c539c563e3e86a16a2be29ab8135bdd9c06267d87639d543ae7dd5d3bc4`。原source依赖[背景记录](ALFWORLD_CONTEXT_STUDY.md)所列18题包；这些不是完整runtime或公开artifact，不包含在途8题。原始命名保留批次开始日期，不因跨午夜改名。
