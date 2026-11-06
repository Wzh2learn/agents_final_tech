# ALFWorld执行纠正：现役采集记录

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。目标是形成真实可执行的反馈监督，尚未训练或建立新方法贡献。

## 已完成：四现场的能力诊断

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

## 当前在途：补齐剩余八个原失败现场

- 批次：`context_study_v1/teacher_pool_expansion_v1`；owned PID4095165，控制器Q下`run_context_study_teacher_pool_v1.py`。Q为`/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106`。
- 固定队列：look_01、cool_02、look_02、heat_02、cool_03、look_04、heat_04、heat_05；均为原18题中尚未测27B recent的合格未完成source，无替换或按成功筛选。look_01虽已被学生恢复，仍保留以补全强模型基线。
- 沿用原protocol SHA `2fb92f35b20ae00e03183da837e92218240233180df9d3f9cf6d14383170843d`和科研代码epoch `34c7055d`；27B统一drop_recent/nativeFalse/seed17，其他合同不变。不重跑原collector，不训练actor或选择器。
- ADMISSION绑定全队列、source receipt、driver与components SHA。逐题events，最终RESULT；先核对应进程及终态，不因缺marker重复启动。已完成6诊断批不再等待。
- 暂停只向本批写STOP_REQUESTED并对核验argv的该PID发SIGTERM，保留当前receipt/未知usage，退出actor/relay/world；不停止模型服务。锁仅约束本study，不能冒充全局预算锁。

这轮用于补全原12个未完成现场的固定强模型基线及纠正候选。各恢复从共同原source分支，不能当作“先跑失败的恢复臂、再免费回滚给教师”的部署策略。真实形成、失败、重放与后续使用成本分别保留。

## 下一唯一优先工作

完整返回后，导出实际成功轨迹的可追溯监督候选，检查唯一任务/布局、工具错误与来源隔离，保留所有失败。先与普通成功轨迹、强固定策略及STeP等近邻对齐，再决定小规模学习实验；当前3个成功现场不够认证学习或泛化。4B接入是有时限的支持工作，不阻塞8B/27B的多任务研究。第二环境沿[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)接续；不再把四现场没有成功选择空间的旧选择器当成已成立方法。
