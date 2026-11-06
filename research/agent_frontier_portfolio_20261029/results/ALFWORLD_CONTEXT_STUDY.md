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


<a id="teacher-supervision"></a>

## 2026-11-07闭合：教师与监督来源历史

以下为从现役纠正页移出的原文；其中累计账为对应批次当时快照，当前运行只读[现役学习与评价](ALFWORLD_CORRECTION_DATA.md)。

## 已完成：原十二个失败现场的固定教师对照

八题扩展批已全部返回：look_01、cool_02、heat_02、heat_04、heat_05成功，look_02、cool_03、look_04失败；270真POST、2,893,399tokens。与前四题合计，27B recent恢复8/12，共351 POST、3,817,330tokens；该批完成时专题累计1,804 POST、20,340,505tokens，不是项目全局账。所有失败与形成成本保留；cool_04等上下文门不证明任务无解，look_04还包括大量被环境拒绝的动作。

`teacher_pool_expansion_v1/RESULT.json` SHA `7925d7ea2114fd392dfe843a821488c97fc8bede79d53d6e5b7716aa72d85cde`；PID4095165已退出。教师的每个现场都从原source分支，不能当作先免费尝试别臂再回滚的部署收益。

离线导出位于`context_study_v1/recovery_supervision_v2/teacher_drop_recent_complete_v1`：8个任务/布局组、83个接受动作回合；`data_manifest.json` SHA `aea83b3319a3f90f5472a28bb0ba5990a64f6e0e92c519a21a717473d76fa44b`。这是同一环境的四类任务，不是8个独立来源。全部351次教师请求（含4条失败）计入形成账；1576项输入证据未改变。`qualification_v1.json` SHA `91e1417146965d98ed52316b6398e276135b4366e472973b9ca1a10357695ef4`还检验了真实双轮失败：固定Continue、同会话、27次tool结果对齐22个实际动作，正监督为0。

导出保留真实请求/SSE、公共content与tool_calls；被拒绝动作、工具反馈与最终文字不作为正监督，失败上下文不删除。每个当前动作completion仍须按实际请求编译token标签。已验证多轮chat候选不等于可直接投入旧单completion训练器。

CPU tokenizer已完成真实编译：83行/8组、3,582监督token，最长10,740，无排除或截断；逐个使用实际forwarded request和native SSE，历史消息及tool输出mask为-100，只当前助手动作completion＋单个im_end监督，尾部模板换行不计loss。HF模板前缀逐token相同；未加载权重、未调用CUDA或推理。`supervision_tokens_v1/teacher_drop_recent_qwen3_8b_v1/data_manifest.json` SHA `e12352162db845a61e14f337b722b17391262c08a953817c0316da388ebf124e`。数据量仍小，接受动作中也有冗余/探索，不能称逐步最优示范；训练比较须控制接口收益及来源不平衡。

## 已完成：从头执行的强教师与普通监督

`ordinary_teacher_v1/RESULT.json`已闭合：27B从真实reset执行原18题，成功16/18；265 POST、2,518,697tokens＝2,505,815输入＋12,882输出，usage缺失0，cache细分未知，episode用时合计2,003.724秒。clean_02、heat_01触输入上下文门而失败。RESULT SHA `e52b1c2d7b146b0f3884e8d65197691ee9e3cb83dd7d2ce4e1bc05e45f9ae085`，原PID4157942已退出；本专题累计2,069 POST/22,859,202tokens（不含更早项目账及研发Agent）。

同一12个原未完成任务上，直接教师从头完成11/12、160 POST；教师从学生现场恢复8/12、351 POST，尚未加学生形成费。clean_02只在恢复成功，cool_03/cool_04/look_02/look_04只在从头成功。两种起点、进度和上下文不同，这是配对开发诊断，不能归因为“重启/保留进度”的单独作用；也不能默认小模型失败后再接管更省。直接教师是必须保留的部署成本参照。

16条成功轨迹导出171个接受动作，CPU编译7,311监督tokens、最长18,180、无截断/排除。chat manifest SHA `b7cbec3a1660e20f293a08b5feae2470a28e024a10f4d50267ff6e20ce7f8bb6`；token manifest `supervision_tokens_v1/teacher_ordinary_reset_qwen3_8b_v1/data_manifest.json` SHA `3e070a3e713279405b0e23db6fcd38ac75f5e95c8991997b09cbc7d779cb3675`。两条失败成本均保留，普通监督无虚构collector或重放费。


新薄包`alfworld_teacher_complete_supervision_v2_20261107.tar.gz`（1,553成员，5,421,100bytes；SHA `5361d083bdeb7599efce2781667ae2903cc05ab93507b0445d23036dd7954bf2`）已在GB10、本机逐成员核验；manifest SHA `37997af7e5f5d5460315c078454b1eb94b7d8b8e314c78651e46362ca9117403`。依赖前述source/四诊断薄包；不含在途普通18题，也不是公开可再分发数据包。

<a id="learning-runtime-history"></a>

## 已闭合：同来源两臂真实训练

两臂用同HF8B基座、seed17、新q/v LoRA r8/alpha16/dropout0，各计划192次成功optimizer更新，来源均衡轮转且覆盖全部动作；普通计划1,135,199序列tokens/8,239监督tokens，纠正1,135,273/8,378。只称同来源/初始化/更新数；不把不同训练量写成完全等成本。现役计划为`learning_comparison_v1/plans/ordinary_v4`（manifest SHA `875243cbcab87d968789e76f34745ee3514c27e0ac65c470ab499b8ee90a8c09`）与`recovery_v4`（SHA `4be913090ed70584a52b7b7d832b3aecc3e87991221bb3665ca953ef274888c7`）。历史计划/源码/失败保留。`owned_window_v3`普通臂已192步保存并重载，tensor hash精确一致，实际1,135,199序列/8,239监督tokens、1579.43秒；receipt SHA `5d35669dabdd9a5a3ae2fea48b691f3bb3112628d42e2b7b945cc79573331068`。纠正臂亦完成192步保存/重载，实际1,135,273序列/8,378监督tokens、1600.13秒；receipt SHA `7d74ad33cf595935c5297fef5eb85547110c36d3c12e17d8643631aef9f085b8`。两臂合计384更新、2,270,472序列/16,617监督tokens。request SHA `69c07d8e1a6e63539a01b3d4ad85d69e7362a096c11b20cb2004287649fe66ff`。窗口已原样恢复owned18104（PID123887），共享35B/27B身份不变；4次健康GET、1次CUDA探测，窗口3237.58秒、科研生成0。窗口RESULT SHA `6f4ceae02bead9e5a424489492d60dee9dfc2c21160c947a6dfb2994adc2da46`。未加入canary生成，实际学习效果随后按环境won评价。

2026-11-07新评价窗口`learning_comparison_v1/hf_evaluation_v1/RUN_v1`在Popen后立即采集身份，启动瞬态被误判，0个task/POST；BF16实际已加载。原RESULT SHA `b8dfa6fda5c377049810e03915b7d4640552dc5ae5e33e11fd99cb452823039a`保留。D精确收回自有BF16 PID169132、原样恢复Q4为PID171257，保护35B/27B不变；`manual_restore_v1/RESULT.json` SHA `131747165d1ce410612065bd7d619fc17382a9c8ddde941902e6cc750fa9d251`，4次健康GET、0生成。v2把执行资格的稳定argv/cwd/exe与Popen子进程的清理所有权分开；D真实CPU exec过渡观察及5项测试通过，科学协议、任务和权重未改。随后RUN_v2开始实际评价，不能将本窗口工程失败算作学习负结果。

## 2026-11-07闭合：训练前工程现场

v2首次实跑在权重加载前返回`Invalid device argument`（0权重加载、0forward、0优化步，不是OOM或学习负结果）。根已在新进程精确复现：reset_peak不触发CUDA初始化，必须先mem_get_info；现已修正并以失败→通过回归验证。`owned_window_v1`结束已恢复8B原argv/cwd（PID16445），共享35B/27B身份未变；5次健康GET、1次CUDA内存探测、零模型生成。旧窗口与receipt保留，随后v3在CUDA初始化处报OOM，仍0权重加载/0forward/0步；`owned_window_v2`已恢复原8B（PID24359），共享服务未变，7次健康GET/1次CUDA探测。两次都不是学习负结果。定向释放已绑定HF8B文件的clean页缓存，实测MemFree增加约8.7GB而MemAvailable近似不变；v4仅在逐shard完整核验后作同类建议，并记录原始异常堆栈与阶段，不保证显存足够。不改共享模型，不让此支持项阻塞主线。

<a id="old-parent-baselines"></a>

## 已闭合：旧Q4底座与两种执行接口

冻结8B基线批次`heldout_frozen8b_v1`已闭合：原控制器PID29543已退出，Q下`run_context_study_heldout_frozen8b_v1.py`；代码epoch `62b197b8`，16题按冻结顺序全跑，stage ordinary_reset、无经验、无LoRA。评测protocol SHA `5af8c4579b8f14ed2fc3e2857b2928726b83a02c81e1b2b33ac81d4e18497aa2`。RESULT SHA `18e6873320b843a1256ba1b285e1036bb95fa62e866adaba24ae277fc5780c6c`：won为3/16（look2/4、cool1/4、clean0/4、heat0/4），755 POST、9,055,073输入＋33,410输出＝9,088,483tokens；其中缓存输入8,871,228是输入子集，不重复计费量。usage未知0。本专题累计2,824 POST/31,947,685tokens，不是项目全账；新16结果不进入训练或调SFT超参。

独立复核16份receipt/manifest和755份原SSE无差异；13失败按最终停止原因分3个POST上限、4个context门、6个普通stop（均已继续一次）。4个零工具错误失败仍处理错对象或漏清洗。侧车`heldout_frozen8b_v1/independent_review_v1.json` SHA `65c72e1a017aff2f7dc4c45cd738953be545995c8b4526315d954961060c008f`。这支持检验合法动作基线，不证明所有失败都由动作格式引起。

[直接策略](../alfworld_direct_policy.py)已在同16题实际跑完，服务端动态schema可用：native won为1/16（仅cool_03），比旧臂新增1题、丢失旧3题；7个context门、8个100动作耗尽的done-unwon、1个won。1271 POST/动作均在此前公开admissible列表，无非法动作；13,811,233输入＋9,819输出＝13,821,052tokens，缓存输入13,477,285为输入子集，unknown0。逐响应hash/usage、16个相同公共reset及独立native终态均复算通过。RESULT SHA `6f265b6a9416ffaef77e66823f61e4255fdb28fb661c4859fa3ed7084efee42b`；`COMPARISON_V1.json` SHA `f8f1d32b0724f6895955c94f3541bbcc64dd0fb9a7da7de2ed27c91ca172eaf9`。本专题生成累计4095 POST/45,768,737tokens，不含训练和研发Agent。

该臂保留原目标/完整公共历史/权重/采样/caps及一次Continue，但同时去除OpenCode计划/工具结构并只准输出单动作JSON；结果不识别单独约束效应，也不代表强简单基线已经穷尽。不再修补此action-only臂。对照[ReAct §4](https://arxiv.org/html/2210.03629v3)及[官方ALFWorld入口](https://github.com/ysymyth/ReAct/blob/master/alfworld.ipynb)（2026-11-07已读，未复现成绩），后续保留同数据条件的计划/示例基线；不能把它们的收益改称新经验机制。原16题已属暴露开发数据，未进入SFT监督或超参选择。


<a id="mechanism-reading"></a>

## 2026-11-07按需：近邻机制原文核对

## 方法重叠与下一验证

[ACE §3](https://arxiv.org/html/2510.04618v1)已有带效用记录的条目、局部delta更新和保留历史知识；[AgentFold §3](https://arxiv.org/html/2510.24699v1)已有任务执行中的细粒度/深层上下文折叠和轨迹SFT。[STeP](https://arxiv.org/html/2505.20023v1)已有学生失败现场的教师纠正与partial masking。均已读方法正文，未复现成绩；局部改经验、继续外部进度或换LoRA都不足以构成独立贡献。

**Memento补核（2026-11-07）**：[§3.1–3.6](https://arxiv.org/html/2611.00244v1)以Qwen3-8B学习compaction notes：教师成功轨迹事后插入笔记做SFT，再按终答、笔记有效性及置信奖励做GRPO；训练只compact到新window，测试另支持fold/backtracking。其Book QA工具为search/view，回退的是阅读上下文。它已覆盖“学习记笔记/删历史/重建窗口”，不能只换为ALFWorld声称新机制；本文剩余待检验条件是已执行外部动作后的恢复及总成本，而非已证空白。下一恢复比较需保留普通摘要/近期历史/同额度reset等强控制；若均可解释收益，不扩大复杂记忆选择器。原文方法已读，代码与成绩未复现。

**STeP配置补核（2026-11-07）**：[§3.3–3.4及附录B](https://arxiv.org/html/2505.20023v1)在学生动作及环境反馈后由教师判断、反思并继续纠正；最终从基础模型混合普通与反思轨迹训练，mask错误步骤。文中708条反思轨迹涵盖三个环境，不是708条ALFWorld；训练采用batch32、lr3e-5、4 epochs。当前7组、纯普通/纯纠正LoRA是有限数据来源对照，尚未实现该混合训练和显式反思，不能当STeP复现或反证。若纠正臂损害原能力，先核混合rehearsal这一强基线及实际失败现场的恢复效果，再决定候选；不会仅凭从reset成绩停止所有恢复学习。

**2026-11-07原文新增核对**：[Dependency-Guided Rollback Repair §3](https://arxiv.org/html/2608.10502v1)已研究故障经验的后继失效、独立支持保留和选择性重放；其输入包含上游已诊断的故障memory，明确不能撤销不可逆外部副作用。因此“撤回前提及依赖、保留未受影响部分”也不是新机制。可比较的剩余条件是普通执行反馈下的诊断不确定性、实际外部进度及补偿成本，是否值得学习仍须实测。

[Invalidation Contracts §3/6.4](https://arxiv.org/html/2609.00243v1)提供服务端版本/差分与依赖失效，实验为作者构建API；[MERIT §3](https://arxiv.org/html/2608.05906v1)已有按错误类型检索正负修复记忆，但终态正确性用oracle反馈。这些是应对齐的近邻/信息条件，不因换环境就认定独立增量。当前失败并未证明需要复杂依赖机制；先比较精确目标绑定、循环保护、等预算摘要和相关局部更新适配。新增最直接对标（2026-11-07读方法正文，未复现成绩）：[Sentry §3](https://arxiv.org/html/2610.02994v1)已按运行中失败触发少量经验、验证局部恢复再入库；[EMG §4](https://arxiv.org/html/2607.13884v3)已对失败/成功轨迹做决策图匹配以提取纠正知识，并在ALFWorld/ScienceWorld评测；[VH-GPO §3](https://arxiv.org/html/2610.14000v1)已从学生现场做教师恢复、验证提前交还控制并学习。故“条件暴露失败经验”“从成功/失败差异抽技能”“短教师桥＋学生续做”也须作为对照，不能直接改名为新方法。优先对齐Sentry的反馈条件、EMG的监督来源和STeP的纠正训练；VH-GPO涉及额外搜索和RL，比较时不能省略其形成成本或称已完整复现。

普通/纠正监督学习是能力和训练对照，不预先宣称新方法。第二环境按[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)接续；不再训练已无成功选择空间的旧四臂选择器。
