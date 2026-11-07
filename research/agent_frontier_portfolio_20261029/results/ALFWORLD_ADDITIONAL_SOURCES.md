# ALFWorld 新增训练来源

> 2026-11-08 | 维护这批来源与真实采集；当前研究动作见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。旧7来源配方已停止，旧学习/恢复结果见[历史学习记录](ALFWORLD_CORRECTION_DATA.md)，不在本批重算。

## 为什么获取新来源

旧方法主要依赖7个来源；新Matplotlib任务的三臂都只搜索、未编辑，不能据此训练经验选择器。后续需要新增任务上的真实执行与反馈，先复用现有缓存和原生环境，保持来源与评价分离。此页不宣称新方法成立。

## 已冻结的候选

GB10私有根为`/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106/context_study_v1/learning_comparison_v1`。`NEXT_TRAIN_SOURCE_INVENTORY_V1.json` SHA `008b579626cbcdaffc5fd51f2f57157d9442ba0d9a2e0274894e0b26dc13851c`机械盘点已缓存官方ZIP：6,374份TRAIN JSON，3,553组有编译PDDL且game hash唯一，另2,821份缺PDDL。缓存与固定GitHub release元数据及原SHA一致，本轮无下载；不是重新在线认证。

按旧18、开发16、训练7、此前8及dev2、134保留候选等**已知索引**的身份/family/layout/gamehash排除2,131组，剩1,422组。未证明全项目未曝光或预训练隔离。类别余量为clean93/look194/simple586/two549，heat/cool为0；现有pool仅支持clean/heat/cool/look，未把simple/two改名混入。

按固定身份hash排序冻结clean6＋look6，12个布局各异，没有按成功选题。family是完整任务目录，layout来自场景后缀，不把同一轨迹切片当新来源。候选仅TRAIN；134个valid_unseen保留池未读取正文、未转训练。

## 原生资格：12/12通过

新私有根`next_train_source_v1`，SELECTION SHA `88c8e7d32771204f64846199c6022f94870a325129f3fdeb827bf1a17b46e477`。按精确member/hash只提取12对traj/game，不任意解包。复用现有`alfworld_task_pool.py --qualify-one`与动作桥，不新建runner或修改旧池。

冻结12例资格控制，各用既有seed17、100动作、120秒上限；不重抽、不替换失败，预算至多1,440秒资格运行。每例包含命名/复位检查及official expert与native轨迹对照，不将内部重复reset算独立任务。轨迹保留EVAL_ONLY，未授权作为训练行或actor输入。本阶段模型/HTTP/网络/容器/训练均为0。

原生资格证明任务与桥接可运行；场景/实体命名变化不等于环境动力学变化。后续须先冻结多任务执行/反馈比较，含强固定策略与预算，再决定真实采集或学习；不将合格POOL当作学习收益。

首次固定12例全部QUALIFIED_TRAIN_DEVELOPMENT，无重跑、替换或失败剔除。clean6例共94组逐步动作对照，look6例共99组，合计193组；每组包含official与native两侧执行。12例均复位非成功、同seed复位一致、命名扰动可重复、逐步公开观测/score/won/done一致，终态won/done=true、score=1。不外推为全部隐藏状态等价。

各资格回执墙时合计33.183秒、整批34.788秒；CPU user/system未测，不写成CPU/GPU-seconds。新增模型/HTTP/下载/容器/训练/服务操作均0。D逐条核193行对照、12份原始收据/trace hash，并实际通过现有适配器对全部12项的纯读取准入；没有重放。

| 私有工件（next_train_source_v1/） | SHA256 |
| --- | --- |
| RESULT.json | `6807a877abc0d52591c5c09ac7d2b66ced125d1ff651ea933f14b1caedfa98aa` |
| qualification.json | `a5eee732506dd58122fc11040e878b4e8ae462e557b72e9798922edff9568219` |
| POOL.json | `24a30747b87102a7dcfe2f92c666596285f72f7cc7b3a0c52f630acc5cd75023` |
| D_POOL_CHECK_V1.json | `3e8054818020d86a328827eb5a1d76a2500befc02d46226ddfe5246025ee9e44` |

114成员闭合私有包已双端逐项核验，631,027bytes，SHA `bd7d1646de2b388168c8e95fe8438d4c6ef00737f399334b82db6bdc9cd965e7`；manifest SHA `0959c086e4742562330f28d8e6e492164165110cc1f1ae8dd96181c9db6d8cbe`；本机check SHA `1133e1672ca8ae1cb11e5e49469a10c2c60a7ea736e49d83a930ad140ddf7bce`。原ZIP保留GB10固定缓存，包不含模型/依赖；源资产与专家参考受上述EVAL_ONLY边界约束。

## 真实执行采集

12例全部作为TRAIN形成来源，不作验证或确认。每例由现有8B GGUF学生和27B FP8教师分别从相同原生初始现场执行；固定seed17、32K上下文、最多8192输出、关闭thinking，不输入旧经验、gold或expert轨迹。直接27B也作为成本基线；不同模型的能力差异不解释为学习收益。

私有`source_collection_v1/SOURCE_COLLECTION_PROTOCOL_V1.json` SHA `17597dbc116c7919b893645206eabc7201e4aaddd93ed9fe4325b820a8a7964e`；PLAN SHA `326e0287585825212d11c30e1d5891a2c43028f845e596d80787126c1e129c70`。固定24个任务运行，逐例最多96 POST、900秒、100环境动作、32,000,000模型收发bytes，合计最多2,304 POST；普通无错误stop最多同session继续一次，共享该例额度。只采集，不训练、不judge、不调用付费科研API；后续恢复预算未释放。

复用现役study并增加明确的`experience_mode=none`；未声明该模式的旧合同保持原准入。发现并修复首轮顶层接口error后仍可能续跑的问题：raw/hash保留，普通工具错误反馈不当作接口错误。GB10 focused为65 tests/282 subtests；私有逐例闭合门14项、批次取消/启动/绑定控制7项合成CPU检查通过，不把它们当真实模型成绩。

队列只在真实原生终态、逐轮raw/退出码、费用和清理证据闭合后进入下一例；137、UnknownError、未知调用账等阻断后续未运行例。已证明的终态/POST帽/上下文预算拒绝分别记录；原生`won`独立报告，cache明细缺失保留null。全批持有已有模型资源锁；取消先等待已拥有子进程退出，观察超时不冒充终止。私有gate SHA `390aecf9a39fdbbc325bd20edf1327289e5626f1d518195d6da5738ba8ccc921`，driver SHA `9bb2d9feb3065e649c431535f8cba568a34c5ebef5328c4fbfdc3012d2467dcf`。

正式执行前两例的V2 native准备记录SHA `10cae464e8b79f17502e2666d5d491ad210f6433a04f00802e77087769b8cd7c`，当时无actor输出。旧两份准备因代码修复被V2替代，但原位保留；更早一次解释器失败亦保留。启动前实际native准备5次，其中V2复核10.118秒；后续22例轮到时再准备，最多合计27次准备，额外3次属于预生成工程复核，不增加24次科学任务运行或POST帽。

C对四项具体阻断的限定复核通过，回执SHA `61c8393098cff6d3f9fff108d0c8e8174ebb9f82344499faac1f18cdd6b08a1d`；不代表真实采集效果。D release SHA `f741411031e706ff1938115cb885da91ff653efb34c95415c0d01c5a1f3ca6ca`绑定代码、两份manifest、协议、POOL与profile等固定文件，`--check-only`通过后启动。

**运行中**：GB10 owned driver PID `1623227`、birth ticks `1083656173`；以实时进程/回执为准，不从本行推断仍存活。首槽`nexttrain_clean_01/collect_none/student8b/attempt_v3`已产生实际请求与原生动作；teacher首槽为`attempt_v2`，其余固定槽为`attempt_v1`。每槽结果只在其closure与原始receipt闭合后计入，不能用进行中请求数报最终成本。

批次返回后按任务统计成功、失败、停止原因和形成成本，再决定保留进度的反馈比较。尚无本批纠正监督、训练行或方法增益，不扩旧R配方。私有运行路径和日志留在同一主题目录，不新增现役prompt。

### 首三条已闭合运行：开发观察

以下是批次未结束时的固定前缀，不代表12例总成绩。三条均通过实际raw/费用闭合，原生`won=false`；工具尝试与环境接受的动作不是同一计数。

| 任务 / 模型 | 实际模型POST | 接受的原生动作 | 返回invalid_action的工具调用 | provider total tokens |
| --- | ---: | ---: | ---: | ---: |
| clean_01 / 8B | 96 | 6 | 90 | 878,321 |
| clean_01 / 27B | 96 | 39 | 57 | 1,239,453 |
| clean_02 / 8B | 10 | 8 | 0 | 52,510 |

前两条用满POST帽。8B重复89次被拒的`put towel 1 in drawer 1`；27B也反复尝试被拒的`clean towel 1 with sink 1`与`use sink 1`。不能据此认定环境已执行这些动作。第三条有两轮普通续做、共8次真实工具调用，末尾输出了工具形状的普通文本而未实际执行；正常进程结束不代表任务完成。

这组观察要求后续强简单基线覆盖合法动作反馈与实际工具执行；相应工程或界面收益须与经验学习收益分开。整批仍按原固定名单/配置继续，不因看到结果就更换任务或给未运行臂追加提示；待全批返回再选择开发候选。
