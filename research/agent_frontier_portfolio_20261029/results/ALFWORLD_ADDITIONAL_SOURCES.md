# ALFWorld 新增训练来源

> 2026-11-08 | 只维护这批来源与原生资格；当前研究动作见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。旧7来源配方已停止，旧学习/恢复结果见[历史学习记录](ALFWORLD_CORRECTION_DATA.md)，不在本批重算。

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

## 下一步唯一动作

先冻结多任务真实执行与反馈采集协议，明确研究训练/开发来源角色、学生/教师、经验形成、强简单基线及有限预算；沿用这个POOL与现役actor接口，不新造runner。先获得新任务上的能力与策略选择空间，再决定学习，不因为新池可运行就扩旧R配方或训练选择器。当前尚无这12项的actor结果、纠正监督或训练行。
