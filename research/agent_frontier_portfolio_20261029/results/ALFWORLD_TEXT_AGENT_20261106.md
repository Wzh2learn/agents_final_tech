# ALFWorld：非代码执行经验与变化适配

> 2026-11-06 | 开发环境资格与真实actor入口。现役次序见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，本页不新建prompt或Goal。模型实验结果按原始回执更新。

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

下一批按实际动作/上下文需求冻结新预算，避免直接沿用旧48POST/6MB角色上限；旧结果不追改。先比较无经验、普通历史/skill与实体替换/条件化等强简单策略，再决定方法残差。当前尚无ALFWorld经验迁移结果。

## 经验迁移pilot的事前分工

在扩源池任何模型运行前，固定每类`_1`为source、`_2`为target；首批只采`clean_1`和`heat_1`的27B真实源，不根据成败替换来源。`experience_transfer_pilot_v1/CONTRACT.json` SHA `088fcc1b43f71f6c09f63168456b9c200ee1bb7352f55afd2db5443c6f36625e`。这是内部事前冻结，不追认独立时间戳预注册。

新角色预算为128POST/1800秒/100动作/64MB请求payload＋响应wire；上下文32K/output8192、seed17/temp0.2、27B显式关闭thinking。实际caps已传至relay/world并绑定manifest；旧默认仍保留。源只给真实模型观察/动作与终态反馈，专家/PDDL不进writer。普通历史、普通skill、透明goal条件摘要均在目标前冻结，成本分冷启动与既有经验使用；是否训练或加入新机制由实际监督和最强简单基线的残差决定。

pool/caps扩展代码SHA `2a95c969b9f327e7bcaeb4c6e885242c9344c544c4cfe99f08d5fdcdcec875a4`，20项GB10 tests/33subtests通过。`pool_actor_extension_v1/final_receipt.json` SHA `ffa24edd360967d9bf326e4a95f1ca93133ba91cd2a1351d82885d972a19ced7`；唯一新`teacher27b_clean1_caps128_preflight_v1`的inputs manifest SHA `2dc493fd8eb8e45b3acca73ddedd150c9d2f47e9646096e3e542aaaae044e2ce`，原生reset验证0动作/0模型、owned socket已清理，尚待D真实execute。预检不当作成功经验。
