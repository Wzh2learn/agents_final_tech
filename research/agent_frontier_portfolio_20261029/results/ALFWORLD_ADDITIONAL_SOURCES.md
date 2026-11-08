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

<a id="checkpoint-results"></a>
## 已闭合：27B checkpoint开发对照

私有`state_change_development_v1/actor_checkpoint_v1/`保存冻结方案、八槽raw及闭合。PLAN SHA `7c697126054b8a866cd2d12ff43cc667752cfcd18ea5e37eac558e3da1e266a2`，release SHA `0db1e12f78b05d4145ae8a13361dff86d720cbfc9a06ee84c837e9ee3d82d61e`。一个曝光TRAIN任务、单seed、A未搬动/B已搬动；共同新会话，48 POST/900秒/72剩余原生步/32M bytes，八槽最多384 POST。不是两项独立任务或学习确认。

接入重放完整28步，模型只读21步公开历史和当前state28；隐蔽7步、条件名、新位置及D见证不进入模型。A/B首次实际请求消息字节相同；近期策略运行中保留3轮工具历史。全部8次准备及执行已实测；原预启动证据见Git `6e2ca3ec`和私有准备文件，未覆盖旧raw。89 tests/282 subtests、gate15项及driver10项是工程控制。

| 同任务上下文策略 | A：原生成功 / POST | B：原生成功 / POST | 两条件provider total tokens |
| --- | --- | --- | ---: |
| 完整历史 | true / 4 | true / 10 | 91,804 |
| 仅当前观察 | false / 48 | false / 48 | 722,162 |
| 滚动近期历史 | true / 7 | true / 16 | 115,482 |
| 目标重申＋近期历史 | true / 6 | true / 15 | 105,665 |

完整历史在本例均成功且请求及记录输入最少，**不据此训练复杂选择器**。无历史两臂虽已获得正确goal，却先拿/清洗cloth而非soapbar，之后反复尝试被拒动作；这不是已证实的动作语法缺陷，也未执行“放下cloth即可恢复”的反事实。B完整历史能按反馈寻找新位置，但又清洗了一次；其局部额外动作不能直接证明新方法空间。

全批154次真实转发/162次入口请求；差额为6次成功后的400终态拒绝、2次48-POST封顶403。154工具调用中68次推进world、86次invalid不推进；全部原始退出有对应原因。provider输入1,026,991、输出8,122、合计1,035,113 tokens，未知总usage调用0，cache全部未知。八次执行回放224步、八次预演另224步；episode墙时合计1,171.063秒，整批1,240.373秒。训练/judge/付费科研API为0，GPU-seconds及研发Agent额外用量未知；历史差额不并入。本表是新增阶段用量，来源形成成本仍见前节。

D逐槽重新读取gate/raw，RESULT SHA `58066ed38f2666e3e0e1831bfa48d6e661437ea1c7be68c3ecd8956998de06c4`；C独立核154份实际响应及动作，回执SHA `b76d9572297fcdbf55f7971e8a7e4ff8f5096afc3230253131c36c7b13f65a34`。driver `1727745`已gone，8个owned容器和16个native进程均清理，锁可取得、既有8B进程未变；收尾SHA `405c5fd3022f874a2da8a93fa30526921789cbf53bdc4c6174fdf7d83ed002e7`。

完整私有封存包`checkpoint_pilot_closed_v1_20261108.tar.gz`：1,197成员/2,781,463bytes，SHA `1aa5f9babc9609c7d742cd689435fb0da60e8692bac0d6dc0fd35846c5966e93`；本机逐项核1,196文件通过。包含执行代码、八槽闭合与新look控制，原12来源包另按SHA引用；后续代码升级不改变本批历史。

### 独立任务筛查与下一步

12条teacher来源纯文件筛查已收口，私有`NEXTDEV_SOURCE_SCREEN_V1.json` SHA `c9f947467ebef3b919f44f1115fba7f07e061812a4988e703200dfc75d864141`。除旧clean02外，clean03/05/06和look01/04共5项待原生验证；look05直接取杯即成功，不能照搬搬物模板。clean01/04是实际未完成来源，不伪装成构造成功前缀。

look01已完成一次零模型匹配控制：题目为在desklamp下看报纸，真实来源前4步含开灯、发现异处报纸；公开历史7步，完整交接14步。灯开＋sham、灯开＋搬报纸到shelf1、未开灯＋同样搬动，三者六键公开交接完全相同。D同样3步取报纸回灯侧，原生终态为true/true/false；3world共51步、墙时2.057秒。D独立从原raw复算，不把功能见证当模型成功。协议SHA `7e226b2c1b82120d2981505928c53684df1a93fdb4142b8c1855d5dc41f87f44`，RESULT SHA `e7afb871f97c8c53781caa611be4d623bfae7001c0fd40c819390043f89579c3`，代码SHA `f94e606dc384b6ce636c1bab483ad4433f120faa33a30abb8245248bb01f689e`，同在`state_change_development_v1/look01_matched_v1/`。

下一步以两个自然失败来源和新look任务检验固定策略是否出现异质性，执行状态见下节。后续须补普通摘要、最新观察覆盖、配对效用及同信息的依赖修复/原子续做。原生目标允许其他合格物体，不能限制为指定个体来制造进度价值。

[DGRR §3/4/D](https://arxiv.org/html/2608.10502v1)已覆盖依赖失效和独立证据保留，也承认逻辑回滚不能撤销外部副作用；[CIPO §3.3–3.4/B/D](https://arxiv.org/html/2610.04991v1)已有同前缀技能/原子比较及部分结果续做。当前待检验的是旧观察当时正确而后过期、其他执行效果仍有效时，能否超过相同故障信息下的简单刷新和直接续做；不是将已有概念改名，也未证明两篇无法适配本场景。

<a id="multitask-context"></a>
## 已闭合：三个任务的固定策略比较

私有`state_change_development_v1/multitask_context_v1/`；PLAN SHA `772e8699525002d302f1602838c59a48ba6474870c5d8af550ca3e5e358f6160`。两个实际失败来源与一个D构造变化任务，均为已曝光TRAIN开发材料；不是跨benchmark或确认集。

| 来源 | 来源性质 | 完整world重放 / 可用公开历史 | actor新增动作帽 |
| --- | --- | ---: | ---: |
| clean01 | 原27B真实未完成末态 | 39 / 39 | 61 |
| clean04 | 原27B真实未完成末态 | 11 / 11 | 89 |
| look01 A/B | 开灯进度保留，报纸未搬/搬动 | 14 / 7 | 86 |

每个现场比较完整历史与目标重申＋滚动3轮近期历史，共8槽、3个独立任务布局。策略顺序按任务块交替，墙时只作描述；goal_recent初始也只呈现最近3条。完整历史指accepted公开动作/观察，不是原session、reasoning或全部旧invalid请求；新执行反馈照常提供。两类来源分别解释，不将“行为原先失败”和“原观察后来过期”互换。

明确V2合同仅在新输入启用：真实失败绑定原manifest/receipt/native/raw及已冻结D/C闭合，D构造控制绑定真实三分支，未伪造历史receipt或调用被新代码替代的旧source verify。旧V1验证器AST未变。GB10 117 tests/282 subtests通过，变量计数gate17项、driver11项CPU控制通过；三份真实预演共67步逐状态相等，look A/B task字节相同。PREPARED SHA `1741e8e7b1ba221f7f47cbd1dd91e26b6107e36b61ce1d94a46d04992457df91`；C限定准入SHA `2ee54bb68fb784c2f787066ec718a7ef7cda971e33c6b1822da80abb30859682`。

新批上限384次实际模型POST、16次OpenCode运行，单槽48POST/900秒/32M bytes；原生总上限100步，新增余量扣除实际前缀。8次预演与8次执行最多重放312步；训练/judge/付费科研API为0，不挪用旧批未消耗余额。逐槽闭合，未解释错误或零模型容量拒绝停止队列，不自动重试。

D release SHA `eaee3a3452ebc62d1fb203837ccc7f050d51e55af53bbc8360c2cb31660d5283`绑定678文件。首个实际SDK请求模板为7,028 input＋8,192 output预留＋512 margin，低于32,768上限；八槽实际首包均通过容量检查。代码commit `dcb50bee`，没有以零转发容量拒绝冒充方法失败。

| 任务与条件 | 完整历史：won / POST | 目标重申＋近期：won / POST |
| --- | --- | --- |
| clean01自然失败接续 | false / 48 | false / 48 |
| clean04自然失败接续 | false / 48 | false / 48 |
| look01 A：未搬报纸 | true / 4 | true / 5 |
| look01 B：报纸已搬 | true / 5 | true / 7 |

没有成功交叉；look中完整历史请求更少，两个自然任务均未恢复，**不据此训练选择器**。四失败槽共110次invalid_action，命令均不在当时公开admissible列表中；108次拒绝反馈确实进入下个实际请求，2次只进入封顶后的未转发入口。clean01也尝试cloth，并非只追towel；尚不能从轨迹单独归因于语义、工具或信息。

全批213实际POST/221入口请求，差额为4次成功终态拒绝和4次POST封顶；输入1,532,216、输出10,712、合计1,542,928 tokens，总usage未知0，cache全部未知。213工具调用中103次推进world、110次invalid不推进。8次执行重放156步、8次预演另156步；episode墙时合计1,551.727秒，整批1,614.996秒；训练/judge/付费科研API为0，GPU及研发Agent开销未知。

D fresh逐槽复算全8通过，RESULT SHA `b4c442933afa890bee9fb5829c5aab43908f3e17c5887c55c52d06b07899febd`；C独立核213份SSE/原生动作与A/B首包一致性，回执SHA `cb4c00dbaf11a5dbfa67dfd7855f78af66118775731400b4bc3ee9b45c715e06`。D第一次reader误用无transformers的系统Python，保留错误记录并以V2纠正，未修改科研raw。owned driver已gone，8容器/16原生进程退出、锁可取得、既有8B进程身份未变；收尾SHA `eab6ba77a7b29eb363925b292673760341eefd585333d4d9ef84298258ce2d53`。

私有封存包`multitask_context_closed_v1_20261108.tar.gz`共2,312成员/8,265,261bytes，SHA `d8d0fc2ceb90a8d7e5b6160feb94aa2afa48f567ca80989085bb20cd026e4763`；manifest SHA `db604d7782e95e48b53197c27d690f93d9980edd7ca84e5d059a1a7fc0084cfe`。本机已逐项核2,311文件，原路径与归档成员映射保留。包不含权重、依赖、全量数据压缩包或OpenCode数据库；来源旧包另按SHA引用，私有评测资产不提供给actor或公开分发。

随后只用clean01冻结前缀做一次原生function-tool/合法动作诊断，保持模型与环境进度。它同时改变系统提示、工具和controller包装，不能算学习收益或单一Bash因果。该诊断现已闭合，结果见下节；不再围绕旧例追加接口变体，转向实际代码来源采集及独立任务。

**自然失败仍可恢复的公开信息见证。** D仅据旧公开轨迹选择动作：它已记载cloth位置、手中towel的来源及合法归还命令。重放clean01的39步逐状态相等后，归还towel、取cloth、清洗并放入drawer，新增8步即native won=true，总47步、1.689秒、模型/HTTP/训练0。不是actor成绩或隐藏专家示范，见证suffix不加入待测actor输入；它只排除了该交接现场已经不可恢复的解释。协议SHA `b2691c0691552e7c68655b1c06efd5163e7f9ea3fdc72a3f77e921f98dae4778`，RESULT SHA `8c4b60a8f9508fe9155d99f04e0caeda44bf9fc721071abff95d2480ef867cb9`，raw SHA `f9f1e225c11d5b9c545d5268c0c3399c1995312b4071fcadc6c596d57e663045`。私有8文件包SHA `40537fef69bf56f7c26cf796406f1560b07066e5c1b552b2cc1ca48717d9bb97`，本机逐字节核过；旧模型失败不覆盖。

<a id="native-capability"></a>
### 原生动作接口诊断：合法仍不足以完成任务

新[原生入口](../alfworld_native_actor.py)只加独立模块，复用原动作桥、source验证、预算和SSE计量，未改上批15个绑定组件。模型仍27B/nonthinking/seed17、同39步公开前缀；旧full task只替换Bash调度说明，无D见证步骤。实际schema逐步枚举当前公开admissible动作。

V1漏存witness所需initial_reset，在任何请求前停止，原生重放39步照计。V2实际1POST返回完整合法工具调用，但旧parser误拒forced named tool的正常stop结束；未执行该动作，3,945tokens照计。[官方vLLM分支](https://github.com/vllm-project/vllm/blob/main/vllm/entrypoints/serve/utils/tool_calls_utils.py)与实际raw一致。两项确定性修复均保留旧root，35项CPU检查通过；V3显式只给剩余47POST，未以修复重置48帽。

V3共47次真实调用、47个合法原生动作，最终POST_CAP、world86、won=false：去countertop23次、去drawer22次、查看towel及去sink各1次，没有取走或清洗目标。已访问状态下，47份动作枚举均无take cloth或归还towel选项；这不说明其他状态不可归还，也不推翻前述8步公开恢复见证。结果说明**在这个已曝光现场，去掉非法动作并没有解决任务**；不据此推论模型永远不会恢复，亦不支持训练经验选择器。

三次合计48POST，输入455,048、输出1,514、总456,562tokens，usage未知0、cache未知；117步原生重放另加47步actor动作。episode墙时合计292.437秒，不含未完整计量的研发/审阅开销；训练/judge/付费科研API为0。三个owner及原生子进程已退出，接续代码source前锁已释放，未重启共享服务。

D闭合SHA `a99628142b475b53f028f55f81e6933a3f0c4ba450ab37fe17e23886fbea14da`；C独立核48个SSE/实际枚举/逐步回放及新旧提示边界，回执SHA `d594f8be6ceb2020779c37681dc324fdf25f534f0f315360525345719614cd19`。私有封存包420成员/492,835bytes，SHA `24e68cdbded5821562ad9c20a4bf4aa0c24b1ba7c5136b2c65db9d68f7e62b77`，本机逐项核419文件；旧source包另按SHA引用，未包含权重或依赖。

<a id="student-failure-recovery"></a>
### 新接入：8B自然失败现场，保留外部进度

12题来源中，clean02/03/05/06与look01/02/03/04是同初始任务下27B成功、8B失败；clean01/04两者均失败，look05/06两者均成功。27B的10条成功轨迹可作普通经验，但当时从reset独立执行，不是针对8B失败的纠正。两批旧上下文面板未出现双向成功交叉，不从它们训练选择器。

现有[checkpoint入口](../alfworld_checkpoint_source.py)只增`REAL_CLOSED_STUDENT8B_FAILURE`：严格绑定student8b路径/原profile、manifest/receipt、既有D/C闭合对应行、POOL/seed、原生终态和费用；恢复actor仍为27B，旧teacher来源门不放松。不新建runner或自动注入经验。GB10联合117项/239子测试通过；首次镜像缺一个原fixture的5项保留，补入后通过，D再完整核117项。首次接入helper SHA `7bf39c342be4b46cc2c7d63ae29a19904139140e0feed157e0527baa837bca9b`；原CPU报告SHA `35d124f66c57762cb1ea39edb9d1439b5264aeb96d8058e598ca420e3ce1f3d0`。

原接入当时仅做CPU验证，模型/原生world/容器均0；上述helper和117项是该阶段历史版本。随后显式绑定新student来源的正整数attempt，clean02使用新attempt3、clean03使用attempt1，保留旧输出。当时helper SHA `adf8c61cab8fc7895fa5bf5a58e787f3d3648efcbea79f4d4b3463669a0c0191`，该修订80项通过。

**真实重放已完成。** clean02来源manifest/receipt SHA为`8ef124042235694f0a881844a5e7bfe33e9673ea1675e6b91955630d09f22d7a` / `55ea6fdef9b246ee7559d766cad9dc1d66c56ac810a50f95c2bb5f611da4cb2c`，原10POST、8动作；clean03为`28eaae1d138822fd4aba7161041112e135bc79161fe392cdb3d71621b8bfd1e7` / `d8c1bf19abc4b575c68dc9dab6e8c7c4339a379a31371636b041d30669aba1a7`，原17POST、15动作。两个来源均won=false/done=false、usage完整。复用既有重放接口恢复23原动作、25公开状态（含reset），逐项相等，剩余额度92/85；两个自有world均退出，无新后缀动作、模型、HTTP或容器。原生墙时合计2.5165秒；这证明公开轨迹恢复一致，不代表隐藏状态普遍等价或恢复任务成功。

私有`student_failure_recovery_v1/NATIVE_REPLAY_V1/RESULT.json` SHA `0fdda0e9b4e375e504a74844ccdeba7923da7b78472fbbbd6b091184cd29a38e`；D逐项复核动作、公开状态和进程退出。双端逐字节核37成员资格包SHA `84cac74617e8925b58a20ba5be696515801d3864fe59137185621d71747619cb`，绑定当时c76代码快照；后续代码修订不改写它。

**恢复比较前的控制对齐。** 两条公开轨迹都曾操作与目标不符的物品，不能据此断言遗忘。因此新student来源的`drop_full`与`goal_recent`共用同一目标提醒，完整/近期历史及滚动窗口仍分别保留。旧teacher/constructed输出和普通stop最多续做一次的逻辑未改。study SHA `c154e8fd317e8042b2d9806d8f4ba09ec75f0332360e80877717c04a0e9de82c`，GB10联合132项/246子测试通过，D另一次重验通过。

**四槽预检通过，进入真实恢复。** 复用既有prepare/verify，四个预检world均退出，另计46个原动作重放；准备总墙时13.438秒，不将它写成纯原生/GPU时间。两题的提示在历史JSON外逐字相等，完整历史分别8/15条，近期均3条且等于完整历史末尾3条，目标提醒各一次。`PREPARE_V1/RESULT.json` SHA `bd4b05d94bc10da139a6a60bedd9e06bdc5a630b603dc6dbae6e3f19af3141a8`；此预检阶段模型/HTTP/训练/actor容器0。

私有`D_MODEL_DEVELOPMENT_PLAN_V1.json` SHA `b925b781db27dcfa9179ae98b28faea7a7e2e990d6f396be81a110783642177e`、`D_RUN_RELEASE_V1.json` SHA `563063390d0ebd752e894b9aeeef048d691acffa58c0fa8969d32ed6c47d8b49`。顺序clean02完整→近期、clean03近期→完整；同27B profile/seed17、关闭thinking、32K/8192，普通stop最多继续一次。逐槽48POST/900秒/32M收发bytes，四槽总帽192POST/3600 actor秒/128M bytes；实际进度保留，world剩余92/85。旧source费用只计一次，新执行重放另记。

`RUN_OPERATOR_V1.py`只调用既有study和owned-child执行原语；不自动推进下一槽。每槽先核raw、原生witness、费用与清理，D再释放下一槽；接口、未知总usage或清理异常停队，不自动重试。实时进程、结果和放行记录在`MODEL_RUN_V1/`；完整/近期还同时包含后续全历史/3个完整tool round滚动窗口差异，不能归因于单独首次截短。经验模式none，额外成功经验需另明输入与来源边界；本批只检验已曝光TRAIN上的历史策略，不作确认或学习收益。

### 四组结果与独立复核

| 自然失败现场 / 历史策略 | 原生成功 | 恢复POST / 新动作 | 恢复input / output tokens | episode墙时 |
| --- | --- | --- | --- | --- |
| clean02 / 完整 | 是 | 20 / 20 | 148,455 / 990 | 144.09秒 |
| clean02 / 近期 | 是 | 11 / 11 | 54,491 / 558 | 82.95秒 |
| clean03 / 近期 | 是 | 14 / 14 | 67,986 / 709 | 104.12秒 |
| clean03 / 完整 | 是 | 9 / 9 | 54,160 / 460 | 67.87秒 |

四组均无普通续跑；合计54预留/54转发、325,092 input＋2,717 output＝327,809 tokens，未知总usage0、27B缓存未知。episode墙时合计399.036秒，不作GPU计算量。另有四个execute world重放46个原动作；与四个preflight合计8个world、92个原动作重放及54个actor新动作，不重复计入provider tokens。训练、科研judge、付费科研API、生产调用均0；研发Agent费用未知并单列。

**改变的判断是存在开发性成本交叉。** 完整策略两题共204,065 tokens，近期共123,744；02近期更省、03完整更省。事后逐题选最省为109,669，比最佳固定近期少14,075（11.37%）；这是事后上界，不是部署选择器成绩。两题/一seed尚不足以证明稳定选择空间。它们提供2个自然学生失败现场上的4条27B成功接续轨迹，不是4个独立来源，也不证明学生学习或技能迁移。

**完整流程账不能省略。** 原8B失败形成共151,217 tokens，分别加计一次后，完整/近期流程为355,282 / 274,961，原同两题直接27B从reset为186,721。当前没有完整流程优势；不同模型和不全缓存意味着token和只能作用量账，不换算等价算力或费用。直接reset是能力/全流程基线，不能当作在实际失败world中回滚。

独立零继承上下文C核四槽、373项绑定及54份原始SSE，未发现阻断。原生成功后各有一次请求在预留/转发前被终态保护拦截，CLI exit1/API400与相应witness匹配，终态后额外转发0；不能算模型拒答。四个自有容器及所有查验进程已退出。C为AI独立复核，不作人工gold或全面统计审查。

私有`D_RESULT_V1.json` SHA `89c39fc67131055b7de6c2504b3c9aed9a60d825b33dad764f261aeee0ee5ddb`保留D当时“待C”状态；当前看`D_C_CLOSEOUT_V1.json` SHA `bc3b21f644fe0ce0c92d776d743e4802d60ac5de1c3ca2cf7be5f4e3cad2b0bd`及`C_REVIEW_V1.json` SHA `73ef2bae2f9f57a1a30dbbe56e70b8eb7c0ff16278ecfbd897f4971512543499`。571成员/570文件闭合包已双端逐字节核验，2,493,489 bytes，SHA `0fe123da481523a6ac68f3d783835ec8777a46dcb65f210302cc6a17f6e10193`，封存当前代码，不含权重和依赖；旧source包按SHA引用。

下一步扩其他TRAIN失败布局并重复生成seed，再测无历史/目标重申、普通摘要和便宜规则；只在超出最佳固定策略且能复现时训练选择机制。clean05/06、look01/02/03/04均有既有8B失败/27B reset成功记录；look01在上下文门结束，作为长上下文压力样本单列，不把已有构造状态当其自然失败重放。未曝光保留池继续不读。

**重复实验入口。** 仅新student来源的恢复协议增加单值seed17或29，协议/调用/两历史策略cohort严格同seed；原source和world仍17，旧角色仍17。当前helper SHA `acca84e7a6650d00d6e6e3981dc8d006207ecba1646b6d9a73efec3167c7d961`；GB10 CPU153项/246子测试通过，D已读完整日志并核候选字节，未改变原始normal/POST-cap准入。`BASE/student_failure_expansion_v1/SELECTION_AND_PROTOCOLS_V1.json`冻结六case×两seed共24份数据协议，SHA `d12689f7b71d12e21f4d501bfb8ec546e27bddcbe318a01fbfcd68e90e907130`；尚未实际读取准入、重放或释放模型，不把输入文件准备当新结果。

Django12589有修好原题却引入新回归的真实代码候选，可作第二环境开发资产。SQLite回归与任务专属PG语义探针分属完整评测合同；离线准备不访问PG，正式续做不能略过PG后宣称完整成功。旧35B来源与新27B接续应分标身份，旧题不作新确认。
