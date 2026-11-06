# ALFWorld多任务上下文研究

> 2026-11-06 | 本主题原地接续；模型与原会话历史见[ALFWorld记录](ALFWORLD_TEXT_AGENT_20261106.md)。当前执行次序见[唯一短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。这不是论文确认结果。

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

原始SSE逐条重读、body SHA、usage逐POST求和、真实payload参数、task交付和cohort/25步重放一致性复算见`context_study_v1/MULTITASK_RECOMPUTE_V1.json`，SHA `21d31cf7c6477234a63be2160306c9e6947bc25db02c35d6e540ba8284e9718b`。四臂与教师receipt哈希均列在该私有回执，不在启动文档重复。新原生数据目前仅2个目标/1个恢复cohort；其余16例尚未执行模型，不能称18题模型结果。

### 下一行动

沿冻结execution_order继续look_01、cool_01及其余任务，优先形成独立前缀池和真实成败分布，再扩大恢复比较。学习选择器尚无正向必要性证据。加入目标重申等强简单控制和部署近邻对照仍按短计划安排；不围绕clean_02继续调参追求正例，也不等待4B接入。初批固定顺序不支持独立的墙时因果比较，后续确认需平衡顺序并按任务/来源分组。当前运行状态读取对应batch的RESULT/driver；已结束初批无需等待marker。

### 工程验证与发布边界

GB10本轮focused四文件43passed/155subtests；本机docs lint0fail/3既有时效warn、上下文/链接检查与diff检查通过，变更18文件secret scan无真实凭据形状命中。skill-doctor0errors/134既有warnings，定向map0重复/0未解析。C8源已同步本机两个既有安装副本；GB10与Git发布终态另实测。没有重跑全仓pytest，不宣称旧FinQA fixture问题已修复。源码/协议的旧epoch保存在私有frozen_code及旧attempt，重放旧collector须用其快照，不以最新HEAD假充原运行源码。

## 当前接续：剩余16题的收集批

已启动`context_study_v1/collection_sweep_v1`，按冻结execution_order从look_01、cool_01继续其余16题；本批只收集真实执行及未完成前缀，不自动扩恢复臂或训练。实际输入、初始PID4020003、controller argv/hash、科研源码HEAD和case列表见`ADMISSION.json`；逐题结果追加`events.jsonl`，最终状态见`RESULT.json`。控制器为Q下`run_context_study_collection_sweep_v1.py`。RESULT存在即检查终态；尚无RESULT时先核ADMISSION对应进程与当前case，不重复启动。

暂停时仅对核验argv后的该owned controller发SIGTERM，handler会退出当前episode并保留receipt/未知usage，清理actor/relay/world；不停止模型服务。case中断不作为正常方法失败或合格收集样本。该锁只约束本study driver，不宣称跨机器全局预算锁。

科研代码已整合发布至`d1566f021542ec319cb7aa3f4cc9fc561412df35`，本机/GB10/GitHub refs实测一致；本机clean，GB10仅保留Loop B的`logs/graph/pytest_loopb.txt`外部修改。C8版本`509a50605e3c44d6f04c0cb89a6c6276b3c31dd8b757cb8d59896b711d3e18bb`在两机器各两个既有安装副本一致。后续文档提交不改本批科研代码epoch，当前HEAD以Git为准。

首批私有薄包SHA `b23fae27524bb5f6e1401a1316487bb9cea1d9b091cca684c4e705f28fb26bf9`，1,294成员；原会话控制包SHA `647a9de772f40ccc6f427de53c97121eddfb80e6d37253c4ae6b1423c1f1957a`，218成员，均双端逐成员核验。排除workspace、原game/专家轨迹与缓存；没有权重/凭据或公开artifact。新在途批不包含在该已冻结薄包中。
