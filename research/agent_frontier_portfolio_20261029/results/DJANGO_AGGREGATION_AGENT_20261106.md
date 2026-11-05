# Django：8B真实执行与经验迁移开发

> 2026-11-06 | 本页在首次模型执行前创建，原地维护本批合同与结果。前置[资格](DJANGO_AGGREGATION_PAIR_QUALIFICATION_20261106.md)已经跑通原题base/gold；它不是Agent成绩。Paper E不在本批修改。

## 问题与比较

在同一8B执行器、相同工具和预算下，从真实源任务形成的历史、实际补丁/反馈和普通skill，能否改善后续同类但发生版本变化的目标任务？先运行无历史source12589，再比较target34176的无历史、源历史、补丁/结果卡、普通skill。记录问题完成、回归、原题结果与总成本；若无历史已完成，比较实际成本和破坏，不能把更少POST自动视作更低成本。

source seed7201、target seed7202，temperature0.2，每episode48POST/1200秒/6MB累计请求体；8B context32768/output8192，单slot、禁止context shift、沿模型模板的thinking配置。普通skill由本批实际source形成，其模型、输入和额外调用单独记录；不得复用公开旧轨迹或以前已曝光source。失败source也可提供经验，但须如实绑定失败状态，不虚构已修复。独立新attempt保留raw、候选、评分、截断和拒绝，不自动覆盖/重跑。

此对及参考已暴露给研究者，属于开发；两任务不是两个独立来源。本轮不据一个目标认证普适学习方法或跨来源泛化。新方法仍需与最强普通载体、简单规则和公开近邻比较，适用的留出与重复按[现役计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)继续。

## 冻结环境与可读面

私有根`/home/testuser/wzh/research_evidence/agent_learning_20261030/django_aggregation_agent_20261106/`。

| 输入 | SHA-256 / 配置 |
| --- | --- |
| source依赖投影v1 manifest | `387f9d8f11bb154c3b5cb77fd94dd5bb7cd898bf7e6383dabad43052a6ad4483`，Python3.8；完整评测暴露缺依赖，未用于模型执行 |
| source依赖投影v2 manifest | `f76dc69ba650e61c49a81611392dabf15b65c5d67b7c8fc0ae03bac10c10c16c`，保留旧投影，加入原环境已有typing_extensions/pytz |
| target依赖投影manifest | `196a1cfb4cb2d98fddb66ac56bed81ee90868b8e608fc15055b0e051f8a33efc`，Python3.10 |
| 模型profile | `acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0`，独立loopback18104 |
| 8B GGUF | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` |
| PG socket manifest | `5a47eae155b38533536563543deb2b2e12e938ba95be81509894b60f97ad35c5` |

actor使用冻结base源码、无Django安装包/原site-packages的独立runtime及依赖投影；不挂未来Git、参考补丁、隐藏测试或外部研究目录。模型通过受限UDS代理，仅转发本批18104。source PostgreSQL仅使用新建专属容器的Unix socket，actor和DB均`--network none`，无TCP监听/宿主映射，不连接业务DB。无密码的local trust只在该独占socket范围内使用，不是通用安全认证。目标用SQLite，不承接源数据库状态。

Python、Django源码导入和source跨容器socket查询在零模型预检中实际通过，`actor_environment_preflight.json`保留stdout/hash。PG版本本批已用SQL实测15.17，是原题11的适配。只读挂载socket仍可连接；源码与依赖均与固定manifest核对。评测在actor退出后独立副本恢复冻结测试；原题probe仅改连接环境、不改SQL与期望，并消除源actor残留数据库状态。

## 工程诊断与成本

两次PG初始启动因镜像初始化脚本固定使用标准socket目录而失败；退出码、日志和两个失败回执保留。绑定标准`/var/run/postgresql`后第三次启动成功，未发生模型调用。该新环境仅有1次模型health GET，0生成；先前小模型资格7POST/44,800tokens归[独立资格批次](QWEN4B_TOOL_QUALIFICATION_20261106.md)，不算本批方法结果。

更完整的gold预检发现，顶层`import django`通过不能保证测试路径可运行：source的asgiref需要`typing_extensions.ParamSpec`，隔离后原环境的隐式依赖消失。v1失败记录保留，v2仅从原Python3.8环境补typing_extensions与Django3.1所需pytz，不恢复整个site-packages；新投影仍排除Django安装源码。target完整路径另核。准备阶段问题不计作Agent任务失败。

首次生成前的检查点是实现并验证新runner，再提交固定代码运行真实source。以下继续记录实际结果和判断变化。运行期间不改已启动harness及其绑定组件，不把预检或候选生成当方法成立。

## 运行器资格（首次生成前）

[新runner](../run_django_aggregation_agent_20261106.py)与[合同测试](../../../tests/test_django_aggregation_runner.py)已核对。远端8项定点测试通过（含Python3.8投影）；无历史source/target已接入自动记录、完整外层/组件快照和退出后独立评测。经验冻结与skill形成接口尚未实现，非none条件明确拒绝，不能把预定四臂写成已执行。

完整合成gold控制：source关键1/1、可映射回归65/65与新PG评测库原题均通过，target关键6/6、回归166/166与SQLite原题均通过。`preflight_django_runner_20261106_v2/receipt.json` SHA `878d825dac2758bc74ce079cac759daa005643435081cf473ed2f6ae43cf4a36`。随后base控制保持原题/关键失败、回归通过，实际合成请求验证18104模型及7201/7202种子转发；v3 receipt SHA `7c710cf5530ea7a5c27651c83885f4f448156e977725cd9ae8e861ba0005fb01`。这两批均0科研生成，非模型成功样本。

第一次实际启动`initial_8b_20261106`在Docker阶段退出125：继承harness还需空的`attempt/runtime`挂载目录，合成评测绕过actor启动而漏检该前提。该attempt的raw为空、0POST/0tokens，candidate保持base，不能计作模型任务失败；completed SHA `242bf45a1625154919a389b8063c5f2fb447666a92649a2a180540210b83a8c1`与stderr保留。修复显式创建空目录并拒绝symlink/隐藏内容，新增测试先失败后通过；真实重启使用新attempt，不覆盖第一次现场。

## 首次真实源任务结果

代码`2b01d3d8`，attempt `runtime_ready_8b_20261106`。实际8POST，采样记录确认8B/.2/7201/output8192均正确；Agent exit0、无proxy拒绝，60.663秒。报告76,496tokens＝缓存64,321＋未缓存输入10,315＋输出1,860。训练、额外judge和付费科研API为0。

这些是本episode的模型/执行用量，环境构建、评测CPU及D/子Agent平台开销另计；目前不以76,496tokens声称完整端到端科研成本。

独立恢复测试后，关键0/1；65项回归有42 errors（23项无错误），原题probe在构造SQL时触发`TypeError`、未产生结构化结果。这是实际候选错误，不是初始Docker故障：模型将`GROUP BY %s`硬编码为带反引号的status，随后原代码仍执行字符串格式化，引入`TypeError: not all arguments converted during string formatting`；反引号也不符合本任务PostgreSQL语法。

raw显示Agent读取题面、glob/grep、编辑与调用不存在的git，没有读取compiler文件或运行任务测试，最终请求用户许可运行测试。不能据此断言“诊断利用失败”，因为本episode没有收到退出后独立反馈。completed SHA `2283c62a7fd88aa308707a8188ad02d02890a7fce38e9a7c9e4a15c96aac7508`，raw SHA `bd9a10cbc06ded3e5f6e0f85bc521d4640e9acbe1024c3bbc087205583f31c33`；实际源码与完整组件快照均保留。

**下一判断**：暂不把错补丁直接传播到四个目标臂。先从完全相同的实际候选、同模型/工具/预算出发，比较普通续修与真实测试反馈续修；两者共享完成修复及测试的执行要求，反馈臂只增加本候选的真实错误，不给参考补丁或目标信息。若普通重试追平，反馈不能被认证为独立增量；若均失败，区分实际能力与执行策略，再考虑强教师形成可验证纠正轨迹。当前经验整理仅保留真实失败，不把它写为成功修复。

失败经验DRAFT已由[整理器](../prepare_django_aggregation_experience_20261106.py)实际形成，私有同attempt的`source_experience_draft_v1/draft_manifest.json` SHA `cd2691418f8b5714539f4470d6e8126f21ca6da4f9007320bde09b18191abefd`。绑定raw、7个实际动作摘要、完整实际diff、组件快照及独立错误；未生成skill、未做最终freeze。历史动作按600/800字符截取，字段与diff采用可无损重组的短行，不称完整原始对话。4项故障/篡改测试通过；DRAFT不是已验证技能，也未写入生产Memory。

## 等起点续修合同

N/F均从实际source work的同一6,192文件快照开始，排除原instructions/config/caches，不复制退出后含隐藏测试的评测副本。快照manifest SHA `cc2bb44e58e1db598beef71acf12c73ce2b06443139521b94a6df1cfe551dd0f`。相同题面后均增加自主完成内部修复与实际测试的要求；F仅再附本候选的真实错误、数量及最后两个Django应用栈帧，不含测试断言、人工修法或目标信息。N是强简单续修对照，不是复刻首次原始prompt。

每臂均使用原模型/.2/7201/32768/8192/48POST/1200秒/6MB，串行N→F；每次启动前由D核验同一专属PG归属并清空重建`research_probe`，保存reset回执，目标库/业务库均不操作。退出后原题仍在各自新建独立评测库中运行。首次source成本为共同前置成本，不能用新增续修调用掩盖它；此处比较是一次源修复诊断，不是目标泛化确认。

两臂CLI零模型预检和错误draft哈希负例已通过，`repair_preflight_20261106_v1/receipt.json` SHA `6f6ad9b81981984e8e9eb51d0a9d6a4b3628a2fceaf654fcf0e2d2d30054c5e8`。三组定点测试本机15项通过；源代码提交后实跑。技能生成器已接入显式单次生成/最终freeze校验，但当前仅DRAFT，target技能臂仍未释放。

## N/F实际结果与判断变化

代码`ecf5c0c5`，attempt `candidate_retry_controls_8b_20261106`。每臂的专属PG空库reset与退出后eval库create/drop均有单独回执；没有访问业务库。两组均Agent exit0、0 proxy拒绝；关键仍失败，65项回归仍42 errors，原题probe仍为格式化TypeError，实际compiler.py SHA均保持`f6769134fcc917d6531584aa68987732f9a3d7fdfdbde2c7a147c692dbee6a89`。

| 臂 | POST | 报告tokens（含缓存） | 缓存 | 未缓存输入 | 输出 | 自动计时秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 普通续修N | 5 | 41,371 | 35,894 | 3,966 | 1,511 | 46.307 |
| 测试反馈续修F | 5 | 58,760 | 48,387 | 8,615 | 1,758 | 59.366 |

N completed SHA `5bb1ad9a9f411981a0c202b0687f39bbdf40f6e7d2a931fa8641e94fe25f2bd6`，F `a874ebe426efb13f8f066341c851b900b657ed491d7c4af261f4bd696d6bf282`。本批初始真实source加N/F共18POST/176,627tokens（缓存148,602、未缓存输入22,896、输出5,129），训练与额外judge仍0；工程/协调开销另计。

raw支持更具体的解释：N读完46行题面后尝试编辑`/root/instructions.txt`；F完整读到90行（含真实应用栈）后也选中该文件，并尝试chmod。两次edit的实际错误均为`PermissionDenied: FileSystem.writeFile (/root/instructions.txt)`，F的chmod亦被拒。它们没有进入真正的仓库源码修订。原source曾成功修改compiler，故不能把只读题面误解为整个源码目录不可写；也不能将此次结果外推为一般反馈学习无效。

**后续裁决**：保留8B为学习/执行候选，当前不直接将其失败经验生成器当可靠教师。先给所有新对照统一的强简单执行合同：明确题面只读、仓库源码可改、应用栈路径与actor路径的对应，实际测试并禁止将题面当待修改程序。该合同是环境说明，不计作新方法；只做一次有边界的N/F资格复验，不反复堆提示。若仍无合法有效修订，使用更强教师的真实执行＋反馈生成经原题与回归验证的轨迹，再决定学习/技能迁移。目标任务仍未运行，未冻结成功skill，尚无新方法增量。

162项raw/回执/组件快照/DRAFT/DB重置与预检工件已双机归位：本机`D:/Documents/Loop_D_assets/agent_learning_20261106/django_source_feedback_controls_20261106.tar.gz`，GB10私有`evidence_packets_20261106/django_source_feedback_controls/`；537,025bytes，SHA `0d9ab8f2f3f43b6b98b9ade832a2554665504eab2d111cde69b08b38b67a0723`。本机逐成员hash与完整包hash均核对相符。包不含完整源码/运行依赖/模型权重/live socket，非独立复现发行包，不入Git。
