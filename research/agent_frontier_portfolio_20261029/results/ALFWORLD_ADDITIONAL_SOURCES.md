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

正式执行前两例的V2 native准备记录SHA `10cae464e8b79f17502e2666d5d491ad210f6433a04f00802e77087769b8cd7c`，当时无actor输出。旧两份准备因代码修复被V2替代，但原位保留；更早一次解释器失败亦保留。整批实际27次native准备，额外3次为预生成工程复核，不增加24次科学任务运行或POST帽。

C对四项具体阻断的限定复核通过，回执SHA `61c8393098cff6d3f9fff108d0c8e8174ebb9f82344499faac1f18cdd6b08a1d`；不代表真实采集效果。D release SHA `f741411031e706ff1938115cb885da91ff653efb34c95415c0d01c5a1f3ca6ca`绑定代码、两份manifest、协议、POOL与profile等固定文件，`--check-only`通过后启动。

**24/24已闭合**：末事件为`batch_completed`，原driver PID `1623227`已不存在，29个本批owned容器和24个执行world进程均已清理，模型资源锁可取得，既有8B进程未重启。首槽student为`attempt_v3`、teacher为`attempt_v2`，其余固定槽为`attempt_v1`；原始目录不重命名或覆盖。

私有运行路径和日志留在同一主题目录，不新增现役prompt。以下只报告TRAIN形成阶段；普通教师成功轨迹尚不是针对学生失败的合格纠正监督，不扩旧R配方。

### 完整闭合结果与失败类型

| 来源模型 | Clean成功 | Look成功 | 全部成功 | 实际转发POST | provider total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8B | 0/6 | 2/6 | 2/12 | 592 | 6,064,851 |
| 27B | 4/6 | 6/6 | 10/12 | 339 | 3,383,834 |

两模型面对相同12个来源；能力、精度和部署不同，不解释为学习增益。全批931实际POST，输入9,404,883、输出43,802、总计9,448,685 tokens；provider总usage未知0。8B已知缓存输入5,931,334，27B的339个响应缺缓存明细，因此**总体缓存量为null**，不能只用已知子集充当整体。研发Agent/工具额外费用未知，历史340-token差额仍独立保留。

29次OpenCode运行使用24个原生执行world；921次工具调用中403次被环境接受、518次返回invalid_action，后者未推进world。8B有5次普通续做及2次未执行的工具形状文本。第一条8B重复89次被拒的`put towel 1 in drawer 1`，其失败不能简单归因于经验不足。后续强基线须覆盖合法动作反馈和实际工具执行，接口收益与经验学习收益分开。

各episode墙时合计3,541.728秒，整批3,764.103秒，GPU-seconds未测。D逐槽重新读取raw闭合，C从931个实际SSE与原生轨迹独立复算一致；D闭合SHA `c017c9dfb02a8d27a7d837e2544ca47aef03d641df0c56e011b5aa0c2016b86f`，C复核SHA `cbedba3ee3260a1ca424d985a412427162008449a0ada3fa8d7b9209ada1fd44`。

完整私有包6365成员/29,229,655bytes，包含27次准备、24个执行现场和31份冻结输入映射；SHA `95a1ff1b31a422a9b73f934787d4f942ae646923e7aaaf21a7932d53c02d2e79`，manifest SHA `e52770ad04497d9485f33e3d4f7fe7599fbe7de594fb941cce02de4e9066efcb`。本机逐项字节核验通过，check SHA `b988b1b50e165fb374b5161ee316402827dbb4ffc5198df5f0704056d72e2a52`。旧版本代码与raw均已封存，后续代码演进不改写此批证据。

## 真实状态变化与部分进度：零模型开发控制

复用`clean_02`教师的实际成功前16步，清洗soapbar后由D执行合法动作暂存物体、回到原位置并保持空库存，构造开发接手点。它是一个已曝光TRAIN任务上的控制，不是自然失败现场或独立确认。原游戏、目标和seed不改，无中途reset；不读取隐藏facts/PDDL作为判断输入。

D在同一原生world中实际搬动物体，复用现有Episode/NativeBackend，不做实体改名或编辑观察。V2用无搬动的sham动作匹配计数：三个接手快照的观察、可用动作、score、done/won和action_count完全相同，均已消耗28个动作；库存反馈亦相同。

| 构造条件 | 后续D已知位置的4步原生续做 | 最终native won | 总原生动作 |
| --- | --- | --- | ---: |
| 已清洗、未搬动 | 从原暂存处取回，放入目标cabinet | true | 32 |
| 已清洗、已搬动 | 从新暂存处取回，放入目标cabinet | true | 32 |
| 未清洗、未搬动 | 从原暂存处取回，放入目标cabinet | false | 32 |

续做均不再清洗。因此，在此任务上，位置事实可以变旧而清洗进度继续有效；同时，当前公开快照不能单独证明物体已清洗。后续位置由D知道，这些是功能见证，不是Agent策略成功率。干预、sham与见证动作全部计入成本，日志分段保留；不向未来actor提供干预动作、搬动真相或续做答案。

私有`state_change_development_v1/matched_control_v2/`：PROTOCOL SHA `2e8fe2d8761b4c5fe449a657e0731adf03820e74976e377b3e2a0424f1c01f00`，RESULT SHA `5a4652d3b1d700bd7c9c72e7a0810f15dfc0c2618cd0075d199bfe1d5f76d29f`。12项实际控制通过。V1与V2共6次world reset、177个原生动作、8.561秒墙时；模型/HTTP/训练均0。V1的81动作及未匹配计数现场原样保留，V2另外96动作，不覆盖或免费重算。

控制与已闭合教师来源的私有包已双端保留，142成员/246,404bytes，SHA `6b5b1eba86148716f78f0787a5f03128d3f2cec63a5151e3c6d1b92bbbf764c0`；manifest SHA `ec89248f136b72294204e9e9c0d39cf044d57ae76698d8cc52527362756b215b`。本机逐项字节核验，并独立从raw重算三个28步接手状态完全相同、32步终态true/true/false；不只读取RESULT的通过标志。包不含workspace、权重或依赖，既有native12资产包另存。

后续若进入模型实验，必须分开完整world重放轨迹与actor可见历史，并使用相同观察、合法动作、预算和干预代价。先比较固定保留/撤回、短历史、目标重申、笔记折叠、配对效用选择和简单冲突规则；只有反馈隐藏/打乱消融与新任务验证留下残差，才投入学习选择器。本控制说明问题可执行，尚不提供新方法或新理论。

## 运行中：27B checkpoint开发对照

私有`state_change_development_v1/actor_checkpoint_v1/D_MODEL_DEVELOPMENT_PLAN_V1.json` SHA `7c697126054b8a866cd2d12ff43cc667752cfcd18ea5e37eac558e3da1e266a2`，COHORT SHA `2bd0da21ffc55ad9773c41ddc2e8fed00863be7819edcbe5090d9f63256d04c8`。两种opaque现场与四种策略：完整历史、无旧历史、滚动近期历史、近期历史加目标重申。共同新会话，48 POST/900秒/72剩余原生步/32M bytes；8个开发episode最多384 POST，已按下述冻结release启动。

接入只重放完整28步，prompt只读21步公开历史和当前state28；隐蔽7步、条件名、新位置真相及D续做答案不进入模型。旧source合同不变；本批额外预算不从旧teacher POST余额冒算。新接口89 tests/282 subtests、私有闭合门15项和driver 10项CPU控制通过；它们不代表真实模型效果。

前两槽真实零生成预演均重放28步/29个状态逐条相等，当前状态28且剩余72步；实际task字节相同，SHA `9c39dd76f91e45edf39be275bd7a1a8a5880ef7846a2e090dbdb68efb4eba6c6`。PREPARED SHA `482e13d772c95ac95e859515411e15e97633b6370a71957ce60a399dbb01fb59`。C限定复核`LIMITED_PASS`，SHA `23140f2fdea31235dd94d603699701c5c26c2adcd2848f3e5f4f7deccbe41bc6`；余下六槽准备与全部模型行为仍待实际验证。

D release SHA `0db1e12f78b05d4145ae8a13361dff86d720cbfc9a06ee84c837e9ee3d82d61e`绑定67份文件，check-only通过；owned driver PID `1727745`/birth `1084497627`已启动，首槽已产生真实响应。逐槽核原生won、实际POST/usage/raw和清理后才续跑，异常停止未开始项，不自动重试。是否仍在运行只查实时进程和回执，不从本段推断。代码commit `30c80250`已同步本机/GitHub/GB10；私有准备文件保留于上述同一批目录。

此pilot只有一个曝光TRAIN任务，不作独立确认或训练。原生目标允许其他合格soapbar，不能为制造进度价值而限制actor必须使用soapbar2；最强固定策略若已解释结果，就简化或替换候选。后续扩独立任务并补摘要、配对效用与冲突规则后，才判断是否值得学习。
