# ALFWorld：非代码执行经验与变化适配

> 2026-11-06 | 开发环境资格与真实actor入口。现役次序见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，本页不新建prompt或Goal。模型实验结果按原始回执更新。

接续先读[当前学习资格](#current-learning)，经验结果看[固定载体比较](#current-transfer)；其余按问题加载，不把历史控制当待办。

## 为什么增加这一来源

代码修复之外，用可执行家居任务检验经验中的实体、动作顺序和前置条件能否迁移。先建立无经验actor，再比较普通历史、普通skill及有证据的新候选；不把环境部署、专家成功或实体改名当成学习增量。对标SkillGLoW等已有ALFWorld研究，基准选择本身不是创新。

## 已核实的环境与边界

- 官方来源：[ALFWorld](https://github.com/alfworld/alfworld)，私有环境固定ALFWorld0.4.2、TextWorld1.7.0、fast-downward20.6.4、Jericho3.3.1。GB10为aarch64，未修改共享环境或业务服务。
- 原生TextWorld构建因Inform7无对应ARM编译器归档而失败；保留原始失败和下载记录。随后只适配构建阶段跳过Inform7，使用PDDL路线；76个运行时Python源文件与上游一致，原生ARM依赖可导入、`pip check`通过。这是PDDL-only构建兼容适配，不是完整未修改TextWorld复现。
- 显式train模式开发任务：Clean→Place与Heat→Place。官方手写专家分别10/7步，从reset未成功到终态won/done=true、score=1；未调用模型。seed17实体随机化可重复，改名105/171与92/166，不代表语义、布局或未见来源变化。
- actor只接收公共观察、合法动作列表及动作接口，不挂载PDDL、专家脚本、私有轨迹或评分数据。初始reset快照是缓存，不能当成后续当前观察。实际成功以环境终态为准，不以最终文字回答或工具调用次数替代。
- 动作桥已用真实环境和隔离Docker验证：只挂载client/socket/初始快照，私有游戏与日志不可读；非法请求及terminal后请求不改变状态。14项桥接控制通过；这不是OpenCode真实模型任务成功。

## 证据与成本

GB10私有根：`/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106`。

| 原始回执 | SHA-256 / 范围 |
| --- | --- |
| `logs/final_qualification_receipt.json` | `9a7a9af1fc5675fca295221c21d313f3e6f26525b701db0b157825fa3d6be703`；两游戏专家、构建和来源资格。 |
| `logs/artifact_sha256_manifest.json` | `1979faee8284686107cf7a875bbfb1386a03825a32337c2c78dc560cba3a0d24`；资格快照88项未变，唯一`logs/operations.jsonl`后续追加；其原11,531bytes前缀hash也已核对，原manifest不覆写。 |
| `bridge_controls_v1/final_bridge_receipt.json` | `916444d371cd76fa7171c3a4cd12aa0a256e12c8230df8ffc951333d953ded73`；两游戏原生动作与Docker隔离控制。 |
| 双端私有选定证据包 | `alfworld_qualification_bridge_metadata_20261106.tar.gz`，SHA `3896a0d3b4cac196487626520cccb5848b81131fffd8c64c065f2321361077c0`，157成员逐项核验；无完整资产、环境或候选树。 |

已计来源/资产归档184,045,609bytes；失败构建Inform7约23.2MB及pip元数据/构建隔离的未完整计量下载另列，不声称精确总流量。展开私有内容约479.6MB。ALFWorld/TextWorld为MIT，fast-downward为GPLv3，Jericho为GPLv2+；资产ZIP未附独立LICENSE，不据此推定可重新分发。

## 下一执行点

[动作桥](../../../scripts/graph/research_alfworld_bridge.py)与[actor](../run_alfworld_actor_20261106.py)已交付；GB10定点28tests/30subtests通过。owned fake服务的两backend控制各2假POST、1原生look，只验证接口；真实模型调用为0。最终零模型receipt SHA `49a6c62b9c1aa44163d56808694eee5154ca9458986768a32cd41e094a0d2e00`。

SymPy四臂结束后，按48POST/1200秒/100环境动作、请求payload＋响应wire合计6MB上限，串行执行同一Clean任务/seed17。原生合法动作列表对两模型都可见；这不等于最初ALFWorld论文设置。

| 真实无历史episode | 实际结果 | 请求与成本 | 冻结及终态 |
| --- | --- | --- | --- |
| 8B `ready_student8b_clean` | 39动作，主要逐柜搜索，尚未取到目标；response字节预算终止。docker exit0不能算成功。 | 41POST，574,066已知provider tokens＋1请求usage未知；259.86秒。 | manifest `a4d4df12ddd3f7040a2f6c0e527b2cc1aab4e51e4e788155e326a0e7749e90ee`；receipt `29389eb62d89dc9b114df35650c027b078013a8a4ab37518ed38a3a04c6a4bea`。 |
| 27B `ready_teacher27b_clean` | 15动作，实际取出、清洗、放到餐桌；环境won/done=true，score1。 | 17POST，142,565provider tokens，usage完整；127.16秒。 | manifest `96951fef5111c26acee6cef2512c5896d5edca0ee2431ec812b5994972fdae8c`；receipt `3ba6e08e4da9192b2a95e5d4d6ee780acb3a20cb3f88fcf6f4252abe13507b23`。 |

两个真实episode均已terminal、owned容器/桥接清理无错误；公共raw步骤分别41/17。实际合计58POST、716,631已知tokens＋1未知请求，模拟调用另列。以上是两种固定配置的单次开发观察，不是模型排名或经验收益。8B停止受工程字节门约束，后续可在新manifest中增大预算，旧结果不改。

27B成功轨迹提供了第二类真实源经验。真实两episode与明确标记的模拟控制已双端保存为`alfworld_real_actor_and_frozen_controls_20261106.tar.gz`，SHA `289ebffa29f8e852ad65c199bb6656ceebab46fc1a458ff9af236e663de2455e`，329成员逐项核验。

## 已冻结的下一开发池

只用现有官方归档，先固定哈希选样规则再跑专家，不根据上述模型成败挑题。clean/heat/cool/plain-place各2题，8个不同floorplan，整体排除旧布局2/19；8题均从reset未成功到专家终态won。专家动作数9/17/8/15/8/85/27/9，不能当最短路径或模型成绩。seed17改名及重复reset文本/合法命令可复现；这仍是train开发池，不是未见来源确认。没有新增模型、下载或依赖。

私有`source_expansion_v1/RECEIPT.json` SHA `2a126dd70bae97ca55d47546ff94afcb552d3690dd25c7890b5384981be35d29`，`FUTURE_POOL.json` SHA `1309000e4ec90fb40246f7fce235ed06fbc30f017bfe747f89aab1ebe1a3a426`，最终64项来源hash已复算。专家/PDDL只在D侧，未来actor_reset_views仅含公共观察及合法动作。

双端私有`alfworld_source_expansion_private_controls_20261106.tar.gz`，SHA `0f6f76c3f7aadb06d09257153c65b291cec90f90495e241b1cceaf583b228cf5`，65成员核验通过；含特权专家/PDDL控制，不能整包给actor或公开分发。

扩源时按实际动作/上下文需求冻结新预算，没有直接沿用旧48POST/6MB角色上限；旧结果不追改。当时尚无ALFWorld经验迁移结果，随后实际比较见[当前经验比较](#current-transfer)。

## 经验迁移pilot的事前分工

在扩源池任何模型运行前，固定每类`_1`为source、`_2`为target；首批只采`clean_1`和`heat_1`的27B真实源，不根据成败替换来源。`experience_transfer_pilot_v1/CONTRACT.json` SHA `088fcc1b43f71f6c09f63168456b9c200ee1bb7352f55afd2db5443c6f36625e`。这是内部事前冻结，不追认独立时间戳预注册。

新角色预算为128POST/1800秒/100动作/64MB请求payload＋响应wire；上下文32K/output8192、seed17/temp0.2、27B显式关闭thinking。实际caps已传至relay/world并绑定manifest；旧默认仍保留。源只给真实模型观察/动作与终态反馈，专家/PDDL不进writer。普通历史、普通skill、透明goal条件摘要均在目标前冻结，成本分冷启动与既有经验使用；是否训练或加入新机制由实际监督和最强简单基线的残差决定。

pool/caps扩展代码SHA `2a95c969b9f327e7bcaeb4c6e885242c9344c544c4cfe99f08d5fdcdcec875a4`，20项GB10 tests/33subtests通过。运行前`pool_actor_extension_v1/final_receipt.json` SHA `ffa24edd360967d9bf326e4a95f1ca93133ba91cd2a1351d82885d972a19ced7`；`teacher27b_clean1_caps128_preflight_v1`的inputs manifest SHA `2dc493fd8eb8e45b3acca73ddedd150c9d2f47e9646096e3e542aaaae044e2ce`，预检仅原生reset、0动作/0模型并清理socket。实际模型终态见下节，不以预检当成功经验。

### 首批真实源已完成

源/目标分工冻结后，D串行采集两条真实27B源，未更换题目：

| source | 实际结果 | 用量与终态receipt SHA-256 |
| --- | --- | --- |
| `clean_1` | 8动作、won/done=true | 9POST、47,390tokens，usage完整；`554da1ae3ae4ebcd78845ec3d9164ba49665999caa742af2c9a864e424cca3cf`。 |
| `heat_1` | 8动作、won/done=true | 9POST、53,736tokens，usage完整；`0d0d5f6d28ac848d03b59079269eacd87650327c8284b54cc140c9a7527b3749`。 |

两条均正常返回、cleanup无错误；合计18POST/101,126tokens。`heat_1`输入manifest SHA `983cc29d5c87c31aa85f91ff6a974cfd82b350b1dd1eed9070f540743ede4251`。私有`experience_transfer_pilot_v1/SOURCES.json`先于生成绑定两root，终态见`SOURCE_RESULTS.jsonl`。它们是可用真实经验，尚非迁移收益。接下来冻结公开历史、普通生成skill及透明goal条件摘要，再比较新布局的8B目标；expert/PDDL仍不进入任何载体。

目标运行前另加27B直接无历史对照，检验把形成经验的算力直接用于更强actor是否更划算；它与8B四条件分表，不混作同模型方法增量。事前增补在`DIRECT_TARGET_BASELINE_ADDENDUM_V1.json`，两目标/seed/运行cap同样冻结。形成和使用按模型分列，冷启动与既有经验视图均报告，不把不同模型的一个token当相同计算成本。

<a id="current-transfer"></a>

## 两源经验冻结与首个目标比较

[编译器](../prepare_alfworld_experience_20261106.py)只从真实source公开任务、raw text/tool的input/output/error与实际world反馈取材。保留完整source归档，不将PDDL/专家、pool全表或目标信息送进writer。两个source各一次27B编译，实际prompt长度与本地模板计数一致：clean 4,788＋730=5,518tokens，heat 6,692＋645=7,337tokens；合计2POST/12,855tokens，用量完整、cache详情未提供。输出原样作为普通skill基线，未人工改写建议或挑选最佳样本。

| source | 冻结manifest SHA-256 | 历史 / skill / 透明摘要大小 |
| --- | --- | --- |
| clean_1 | `5956067df1e59bb81c5a3f21bc7acd8fd60d21ca0df35b14fc2fb1ab854d4a11` | 13,535 / 2,715 / 1,096bytes |
| heat_1 | `8153681da13e84878488d27b0fead3e01b185f5f9bfbaef1cabec6d23b73a70f` | 18,672 / 2,335 / 1,060bytes |

各在`experience_transfer_pilot_v1/experiences/<source>/v1`。source采集＋编译实际20POST/113,981tokens；采集和形成只在物理账本计一次，目标边际与整条pipeline成本分列。两条源的131成员薄包与当时7个Git代码组件快照均已双端核验，包SHA `64c9fce404d4464e352c112f129a8598430c922a235adb0de05f25970f3d07b2`。

首个`clean_2`目标预检五臂均通过且0目标生成；冻结顺序为8B none→普通公开历史→普通生成skill→透明goal条件摘要，最后27B直接none。`clean2_cohort_v1/FROZEN_PLAN.json` SHA `8ccfe5fed4545f650338f4c266199dab4dfca08eae2a9809af22a0047427f2be`。它是单个开发目标，不能将五臂当五个任务。actor接入代码SHA `e42622cd6ca1334b07d4eb53544d8b222fc22b5d3bcd2f53585c9be239050030`，compiler SHA `14bc026e3f51877c2679989404af56e35a1c63fc2e3cfe4f5a6f3bfb95643d3d`；37项tests/56subtests通过。source形成写入门与目标后的只读验证分开，所有目标含none绑定同一F，none提示不含来源内容，其余须由真实首请求核实完整载体交付。

### 五臂终态与接口裁决

| 模型 / 条件 | native won | 实际动作 / POST | 已知provider tokens |
| --- | --- | --- | --- |
| 8B none | false | 47 / 51 | 692,784 |
| 8B 普通公开历史 | false | 3 / 4 | 41,424 |
| 8B 普通skill | false | 7 / 8 | 54,103 |
| 8B 透明摘要 | false | 3 / 4 | 22,844 |
| 27B直接none | true | 8 / 9 | 55,967 |

合计76POST/867,122tokens，usage完整、cleanup无错误，均未耗尽各自运行帽。四种8B末次SSE均finish=stop、final content空、没有native tool_calls，待执行的bash动作却在reasoning字段；不能把reasoning挪成动作。none已清洗kettle并到达shelf，但最后放置未执行。独立只读复核支持优先诊断8B思考/工具通道资格，不能用这一批认证经验无效或负迁移。

首请求核查还纠正了测量器：五臂SDK user均逐字等于双引号包裹task、内部双引号增加一层反斜线；逆变换后task原始bytes/SHA全部恢复。history/skill的`COMPLETE_CARRIER_MISSING`是raw substring误判，信息完整但为lossless quoting，不是原始字节直接交付。原receipt不重写，后续校验同时保留raw和整串等价归一化证据。controller显示误取`experience_exposure`，实际字段为`experience_delivery`，原显示null不作科学证据。

27B直接执行已提供可靠的强基线；首批8B经验方案没有可交付收益。随后做same-transport的8B none/attempt_v2，显式native thinking=false，其余条件不改。事前增补见`NATIVE_FALSE_DIAGNOSTIC_ADDENDUM_V1.json`；配置修复不计作新学习方法。

该诊断已结束，inputs manifest SHA `41b6d38ccfe89dd8ee61ad31d10e6ee17f139b4d28420a1501a72d98946acdc7`，root为`target_attempts/clean_2/student8b/none/attempt_v2`，结果写`wire_thinking_diagnostic_v1/NATIVE_FALSE_RESULT.json`。actor代码SHA `cbc4db7e5b1bf6927004eff833d0584f3db3a875efb00c13965523955ad90a76`，39tests/63subtests通过。保留argv输送；四个旧8B首请求在新默认配置下逐字重建相等，新flag只增加原生false。3次fake POST单列，0真实探针；旧receipt/F不改，SDK编码校正sidecar SHA `e4c3acfce655f5dedaa702523c0f179e2f3cc7a132e62c6df4c3dd1403da7246`。

### NativeFalse真实诊断与后续同配置比较

none/v2为62POST、903,356已知provider tokens、48合法动作/12次invalid action，won=false，usage完整、cleanup无错误；receipt SHA `f612abb5a50be31c17e869a88cc07c98f8bf929d24f9628404d45b4d6d04648a`。独立AI只读复核逐POST确认：62个实际forwarded payload均显式false，62份SSE的reasoning字符为0，60次native工具调用；这不把未报告的内部reasoning tokens填成0。末次是普通content声称会继续找kettle，随后stop，没有工具调用。实际拿错mug发生在压缩前，最后清洗的仍是mug，故本次是对象控制、规划和提前结束问题，已不同于v1推理通道动作未执行。侧车`NATIVE_FALSE_INDEPENDENT_AUDIT.json` SHA `ac0fa7fdd92048c8b3f96ab3fbfc34e5ea901ada9ada24a96258c43ca889f8f4`。

通道合格不要求无经验先成功。D冻结`clean2_nativefalse_cohort_v1/FROZEN_PLAN.json`（SHA `79d9436b8765e3cda18bb3b8bda91a8fed8e8ad40888a325036c4723a06f90cf`），复用none/v2、不再生成；其余三个条件用各自attempt_v2、同一source F/seed/上下文/caps/nativeFalse，核经验是否缩短搜索或减少目标偏移。它仍是一个已暴露开发目标，结果不能冒充来源隔离确认。

| clean_2 nativeFalse条件 | won | 动作 / POST | 已知provider tokens |
| --- | --- | --- | --- |
| none/v2（复用，不再次计物理调用） | false | 48 / 62 | 903,356 |
| 普通公开历史/v2 | false | 13 / 14 | 167,580 |
| 普通skill/v2 | false | 51 / 53 | 790,611 |
| 透明摘要/v2 | false | 51 / 53 | 777,752 |

四臂合计182POST/2,639,299tokens，usage完整；本次补齐三臂新增120POST/1,735,943tokens。历史臂把mug放到shelf并称其为kettle，实际world未成功；skill后段重复look后用普通文字给出下一动作；摘要未找到kettle即提前结束。载体均完整encoded交付，不能再解释为“未读到经验”。它们没有解决当前配置的对象绑定和规划失败，但这一个开发目标不否定经验学习领域。

第二个预先固定目标heat_2已冻结五臂再启动，plan SHA `3d4154d899cbf6c72254febff993053aeced191d6099ff3e45ea00ed2df3e03e`，先27B直接none、再8B nativeFalse的四种条件；source热任务F保持原字节。结果已收，见私有`heat2_nativefalse_cohort_v1/RESULTS.jsonl`。

| heat_2条件 | native won | 动作 / POST | 已知provider tokens |
| --- | --- | --- | --- |
| 27B直接none | true | 26 / 27 | 238,852 |
| 8B none | false | 29 / 128 | 2,020,135 |
| 8B普通公开历史 | false | 8 / 9 | 113,940 |
| 8B普通skill | true | 15 / 18 | 134,266 |
| 8B透明摘要 | false | 8 / 9 | 51,938 |

合计191POST/2,559,131tokens，usage完整、cleanup无错误。8B none耗尽POST帽；不等同其余提前停止。skill成功由实际take/heat/move egg 1及world won确认，完整历史与摘要则加热并放置potato 3而非目标egg。源是potato 2/sidetable，目标错误已适配ID和diningtable，只保留了错误物体类别，不能说整个源路径机械照搬。

正向结果的机制也不能夸大：skill先拿错potato 3，放错物体后仍won=false，随后利用公开观察中的egg 1继续，最终成功。history/summary在放错物体后的公开state与skill除action_count外全等（canonical SHA `06e3f1633a60d2600178b5d6416ac5f8f8e85e0857c6062df540687060eb27f5`），但停止；skill最初多一步移动及一次非法动作，不能称三臂前缀完全相同，也未据此证明内部完整状态相同。该差异支持研究反馈后的继续/恢复，不支持“skill从一开始正确绑定目标”或新方法成立。

两开发目标、各单seed下普通skill仅heat成功，无历史/历史/摘要均未成功，27B直接两题均成功。它提供了真实可复用的正向迁移轨迹与具体失败残差；下一用相同失败动作前缀恢复实际环境，比较fresh-session中性继续、仅终态合同提醒和教师接管，判断简单策略是否已解释恢复，再决定学习机制。整个pilot（两源＋编译、旧clean五臂、nativeFalse clean四臂、heat五臂；不含此前环境资格/初始calibration）物理合计469POST/6,179,533provider tokens，未重复计算复用的none/v2；不同模型token不视为等价算力。

heat独立AI只读审计侧车SHA `bf98101e3b75e58bc21bdb6a612a5c8ab38a1bb975d53a51da904710c8732cd7`核对上述终态/成本、实际forwarded nativeFalse、源writer只含公开经验、F早于target reservation及无特权读取；不替代未见任务确认。heat完整目标与新审计已双端逐项保存为907成员私有薄包，SHA `08bbec92fd22eb7a176df16fdd97d106666a4e6d6d9f58a5708d445b390f7425`。clean新三臂和独立nativeFalse审计的566成员包SHA `ac2d632b9ca5053dc316914716d6f4c5dbaf4ddfb70330b3cf8f60db302f9319`。

### 相同失败前缀的恢复对照

新增[恢复器](../run_alfworld_recovery_20261106.py)不修改CBC actor或原pilot合同。固定失败源manifest/receipt/world trace，真实reset后逐条重放已接受动作并比较每个公开state；非法工具请求不冒充world动作。两个backend给同一公开投影：原任务、完整历史动作/观察、完整当前state及admissible commands；不恢复原OpenCode对话，也不含PDDL/专家。preflight/mock不触模型；真实execute要求manifest SHA、独占reservation、实际模板token门，旧失败和source F不改。

heat history失败源8动作/9POST后未成功，两臂同额剩余119POST/1754秒/92个actor动作；world总动作帽100包括重放8步。旧9POST物理成本只计一次，重放控制动作/CPU另列。冻结`failure_recovery_v1/heat2_recovery_comparison_v1/FROZEN_PLAN.json` SHA `0746e46996c1539b825e8faa86a59ebce7e7e18fd12eb978624a5ddd9cf61707`，顺序8B neutral→27B neutral；只有8B neutral未成功时才另冻并运行8B terminal_guard。两臂actual roots为`failure_recovery_v1/heat2_history_v1/<backend>/attempt_v1`，均已结束，不重复执行。恢复器源码SHA `cad06ec2b6f9e144fea29c17061b9527d07b7df13ecbf5784fb0870d9a0ce8ca`；当前任务/layout显式排除未来确认。

| 相同真实失败状态的fresh-session | native won | 新动作 / POST | 新provider tokens | receipt SHA-256 |
| --- | --- | --- | --- | --- |
| 8B中性继续 | true | 9 / 18 | 117,535 | `16bb5056d370cc0ae2320d82454bed38911c27e20c2679d7937e3e9d837be193` |
| 27B教师接管 | true | 5 / 6 | 34,401 | `e7d3394b82f38d519de5262428032a0c2c38e6e2ac7cc8787dd947e18024deac` |

两臂逐步重放8个旧world动作后再行动；无errors/relay errors，usage完整。新增24POST/151,936tokens；8B中性已成功，按事前分支跳过terminal_guard。简单fresh-session能从该失败状态恢复，故原skill成功不能独占归因于其内容或新抽象机制；不等于否定skill从reset的开发正例，也不等于两种对话状态完全相同。教师接管已给出经过真实执行的纠正，旧“从reset成功不代表从学生失败状态纠正”的资格缺口在这一任务上补齐。

两个actor的纠正记录及8个精确代码组件冻结于`failure_recovery_v1/qualified_corrections_v1/FROZEN_MANIFEST.json`，SHA `06a6313b8d62709699dfe8e88b13e9736b24d3daccee22eaa98abeb56893b7c1`。它们属于同一已暴露任务/布局的一个来源组，不拆成两个独立训练/确认组。`qualified_world_correction=true`但`training_ready=false`：仍需assistant-only loss mask、匹配base/adapter推理接入及更多独立来源/留出评测。恢复器/原actor/编译器共52tests及83subtests通过；资格receipt SHA `1b2d3394a7ba66b9603328b9bd2ac7b9bba5b9d6f937eb6894bbcea9a45a2c80`。所有mock标明假请求且不授予真实纠正资格；未新训练。

<a id="current-learning"></a>

## 真实纠正到参数学习：当前资格阶段

该阶段检验数据、梯度和adapter保存/重载闭环，先不用单个任务认证学习收益。按research-driven-design区分部署行为、监督信号和配置耦合：沿用已有q/v LoRA基础，修正旧训练链对全部非padding token算loss的设置；训练和评测使用匹配BF16基座，不将4B新配置与旧8B GGUF的差别当学习收益。

[数据模块](../alfworld_correction_data_20261106.py)从已验收恢复case的provider请求与SSE组装样本，先核先前325成员清单（SHA `afdc84eb2a337a06be923cebe742debee8d92c08cab5645c5369eff639eab058`）。teacher-only为5条native工具响应与1条终结content，共6行/1来源组，长度4615–6514tokens、监督252tokens。完整system/user/tool上下文保留，只有当前assistant completion及真实EOS监督，EOS后换行/所有prompt均为-100；不将reasoning当答案，不截断。4B/8B tokenizer导出相同rows SHA `e098807a89bfab1b74f18e9e68bfcad0c6d296d0a578b14e13a3297fd959e2ee`，是同6条样本而非12条。4B/8B数据manifest SHA分别`5c59f64d041a7df04a6a5bcb53d9247ec607e86523bf54ea00a932ab16f46126`、`3806a26e64d3a141d96dc5093f98936b37bc690b38fc44d8c3cbaaac943d82e0`，数据资格11tests/13subtests通过；实际CPU回执SHA `ed4223d1a7ddbe1bfc450a5db7c0873916135a7b6b219b7eaa06a20c2ec6c211`。

独立AI复算已从锚定原始forwarded请求逐token验证6/6数组/边界/labels/EOS相符。导出row经sort_keys序列化后schema键顺序改变，仅用row内messages/tools重新render会少1token；目前数组正确，精确重建必须回读锚定raw。这是非阻断可复现缺陷，原导出不覆盖，后续新版本修复roundtrip。

[两步训练器](../run_alfworld_correction_learning_20261106.py)只取前两条teacher行作资格，fresh HF4B基座＋一个q/v rank8 adapter，无旧parent adapter；现有torch/PEFT，不走旧TRL自动重写labels。仅投影监督位置前一格的logits，保持标准causal shift与CE；tiny Qwen对照验证loss及梯度与完整masked CE一致，5tests/16subtests通过。完整HF4B七文件8.056GB已流式hash，绑定SHA `e74513f1fe22a2cb9198714738bb86b2f78c05eb0474b25e3759394b8a709823`。

训练前实测CUDA free11.2GB、host available约17.5GB，不叠加8B训练。D只临时释放owned8B:18104原PID3205480（profile归属research_django_aggregation），不触共享8004/8006；同一私有controller在finally用原argv/cwd恢复，并保留新PID/health GET数/共享进程身份。controller为`learning_qualification_v1/run_owned_training_v1.py`，状态只查`owned_training_window_v1/RESULT.json`及实际进程，不根据旧profile PID推测当前服务。

实际训练root=`learning_qualification_v1/attempt_v1`，manifest SHA `da55d9bbfc24ea0dd284d5291a5e3a14655160521f6717369310708e976b9fc7`，代码SHA `357b6daaf688ae0ce7c73ccee1787c01e03bdfd77583d7b3c920d2b15adca5fc`；data代码SHA `0b20b130fe8a3a8a05d610a542a45d8dd60b4491644e28b3740b8551d69ca4aa`。已结束，不重跑reserved根。完整代码在训练前单独快照；未来data代码修正不改本次身份，旧F/原始轨迹不改。

### 已完成的两步资格，不作方法确认

真实2optimizer steps完成，LoRA梯度有限且非零。序列tokens9557（已包含监督部分，不再加88）、监督tokens88；不是对全部6行完整训练。初始化零adapter与base的最大logit差0，训练后停用adapter与原base差0，训练adapter相对base差8.125，保存并重载adapter与训练态eval差0。它证明梯度及序列化连通，不证明准确率提升。receipt SHA `1df59e5c5870b40105ad5ac62f01dd00530433aaa47d2081d222c2637b5f78fe`，状态`QUALIFIED_TRAINING_GRAPH_AND_IN_PROCESS_RELOAD`。

2次in-process greedy生成共9136prompt＋98completion tokens，HTTP模型请求0，judge0；同一个暴露训练prompt上，base和adapter均给出`take egg 1 from diningtable 1`的可解析工具文本，未执行world动作，不能当2条任务成功或heldout成绩。PyTorch峰值allocated10,121,544,192bytes/reserved10,917,773,312bytes，未新下载/安装。

controller已用原argv/cwd恢复8B为PID3853089，`/health`通过（5次readiness GET，0模型POST），共享35B原进程及27B容器身份均未变；完整结果见`owned_training_window_v1/RESULT.json`。旧profile中的PID3205480是原冻结采样身份，不覆写；当前进程身份看该lifecycle侧车及实际进程。原始训练输出、失败与代码快照保留。独立mask审计SHA `c4d8faa191de7d2c54f30d0af8b63b6bf38115060a76fe39ea5d6dd7098199c9`另确认无未来工具反馈泄漏及1token序列化顺序问题的边界。

下一修复新导出版本的顺序往返；无需为序列化修复重训本次已验证数组。随后为同一BF16 base/adapter接真实OpenCode/world执行，再扩来源隔离的纠正监督。当前仍是训练资格，独立学习机制、heldout收益与第二篇方法贡献尚待实验。

下一步从真实失败状态重放公开动作，比较8B中性续做和27B纠正接管，以实际world成功验收纠正监督，而非继续改skill措辞。只读核实已找到本地HF Qwen3-8B BF16五分片16.38GB、4B三分片8.04GB及既有PEFT/TRL单卡链；这只是资产资格，未核完整权重hash、未新训练。旧trainer对全部非padding token算loss，后续必须显式核assistant mask和adapter回接评测，不能直接把“训练跑完”算学习收益。

旧五臂、两源冻结载体/编译raw、none/v2及两版精确代码快照已打私有薄包，SHA `0dc93c35005a90b1091fc8b62ff725ce010f72cdc26ab2e7ee3b957e39ee5145`，789成员双端逐项验证；不含actor workspace/runtime或全量游戏。独立新侧车及在途三臂另行保存，不改原包。
