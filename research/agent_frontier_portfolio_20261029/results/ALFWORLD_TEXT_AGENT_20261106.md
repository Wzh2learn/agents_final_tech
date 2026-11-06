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

27B成功轨迹提供了第二类真实源经验；下一步从现有官方归档先冻结未曝光train开发任务，再验证普通历史/skill、实体替换/条件化等强简单策略。当前尚无经验迁移结果。
