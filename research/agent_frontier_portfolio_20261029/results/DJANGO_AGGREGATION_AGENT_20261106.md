# Django：真实执行、反馈与教师经验资格

> 2026-11-06 | 本页在首次模型执行前创建，原地维护本批合同与结果。前置[资格](DJANGO_AGGREGATION_PAIR_QUALIFICATION_20261106.md)已经跑通原题base/gold；它不是Agent成绩。Paper E不在本批修改。

接续先只读[当前27B检查点](#current-27b-handoff)；此前各节是本批过程证据，按问题检索。

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

## 一次执行边界资格复验（运行前）

新attempt `scoped_candidate_retry_controls_8b_20261106`。沿用同一冻结候选、模型、预算、N→F顺序及各臂前空库重建，只向两个prompt共同补充：`instructions.txt`是只读题面，不修改/提权；Django源码在`/root/django/`可改；评测`/workspace/`按同一repo相对路径对应actor的`/root/`。不指定待改函数或修法，F仍只比N多实际诊断。单测确认新说明在两臂相同且未包含compiler文件名。这是一次执行资格复验，不与旧prompt结果作方法优越性比较；若仍无有效源码修订，不再扩提示，转强教师。

## 执行边界复验结果

代码`af92020d`，两臂均按合同退出且无代理拒绝。N开始修改真正源码，但将硬编码字段改名后仍保留错误的字符串格式化，关键测试与原题仍为TypeError，65项回归仍42 errors。它曾运行错误目录下的unittest，得到`Ran 0 tests ... OK`，不等于通过任务验证。

F真实修改了源码，但把新import插入`django/db/models/sql/query.py`尚未闭合的多行import内，第40行引入SyntaxError；独立关键测试、回归和原题probe均在import阶段退出，**没有执行到测试集合**。该结果不能记作65项测试失败。raw中27次对where.py提交同一不匹配原文的edit均报错；另2次源码edit成功，其中query.py修改造成上述语法错误。完整动作保留，不将其解释为一般反馈学习无效。

| 臂 | POST | 报告tokens（含缓存） | 缓存 | 未缓存输入 | 输出 | 自动计时秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 边界说明后N | 9 | 86,994 | 80,426 | 3,442 | 3,126 | 95.059 |
| 边界说明后F | 38 | 543,993 | 512,637 | 13,611 | 17,745 | 729.748 |

N completed SHA `af66b881ba82baf86992743cf208ef767f99c59bc2cfe9ec6a8df363086b4b4a`；F `a47c9ed1292de77a7720297cb4ea04092238e0f34640df2b7e4b926b865483a0`。新增47POST/630,987tokens；加此前源任务与N/F共65POST/807,614tokens。缓存、未缓存输入、输出分别741,665/39,949/26,000；环境、协调及评测另计，训练/额外judge仍0。失败首启的0POST单独保留。

79项raw/候选关键文件/回执/组件已双机保存为私有`evidence_packets_20261106/django_scoped_source_feedback_20261106.tar.gz`，本机同名文件位于`D:/Documents/Loop_D_assets/agent_learning_20261106/`；263,658bytes，包SHA `259e265483b25e8b7ec73aa91ff18d259bd310c416af66d3070402044bf2e6bc`，本机逐成员hash通过。首个打包选择误把`.components`目录当case，零模型失败；修正后仅创建一次成功包，未改raw。包不是完整依赖/模型发行物。

**裁决**：停止本候选的8B提示变体；8B仍可作为学生，不再用它未经验证的产物冒充成功教师经验。下一步调用既有35B研究后端，在同一冻结源题上从base重新实际执行，再以原题和恢复后的测试验证轨迹。这不是改变N/F结果，也不是受控模型规模比较。

## 强教师轨迹资格（运行前）

复用8004现有Qwen3.6-35B-A3B-Q4_K_M，只消费推理，不重启或改其配置。profile SHA `2b0d9ed7d9bc4b763a697bfbb52e69c208217567d3089af7eb2f7ce5544e7294`；权重SHA `4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d`。进程、监听、可执行文件及权重按只读校验器核对。另3次只读GET（models/props/slots）确认模型ID、4个slot各65,536上下文；这些不是生成或任务成功。

教师使用source `none`独立新attempt、48POST/1200秒/6MB，context65,536/output16,384为输入与输出共享上下文范围内的配置，不声称可用65,536输入另加16,384输出。沿既有模板thinking；未从进程确认context-shift关闭，后端共享负载及不同资源上限不支持纯模型大小归因。actor仅可读冻结base、同一Python3.8投影和专属PGsocket；统一说明只读题面/可写源码，仍不给参考补丁、隐藏测试或未来目标信息。每次启动前重建专属research_probe空库，退出后仍用新的独立评测库。

教师完整CLI零模型预检SHA `288a94d41ed90bc97d9c3857bb3b9a07fec57b0eefa98ba2fb53113867d9fb33`，派生harness `64fce2755305532e67893bee61fd87178e108556687355c28d4e22259ef7bbd8`；合成请求合同与实际Docker只读题面/可写工作区检查分别见`teacher_derive_preflight_20261106_v1/receipt.json`（`b516ed6ce5c8a12d7652d46073aa30dce9f30ebcc6e9b33891b7f5036d35d364`）、`teacher_mount_probe_20261106_v1/receipt.json`（`20496179298c1189d742967c81e42d11b7ff4c497a7d7bf7b8ec120cb666b6f3`）。代码`c8412373`已三端同步后，以`teacher_source_35b_20261106`启动；不改运行中绑定组件。GB10相关24项测试通过，非教师修复成绩。

通过关键测试、65项映射回归和真实PG原题，才可将其登记为本源任务的有效教师轨迹；失败则按实际错误区分源码修订、工具使用和环境，不用更多上下文自动解释为学习收益。成功后先冻结实际轨迹、反馈与形成成本，再决定学生迁移或学习数据资格；单一源题不启动训练或宣称新方法。

## 教师实际结果与补充验证合同

教师产物通过关键1/1、映射回归65/65，PG原题得到`[{"status":7,"total_count":1}]`。completed SHA `07533253b98b4a6c69564380989acda67cb42e8ec8a28e6fd68355647f7ac2b5`，raw SHA `eaff219394b8c5f41c9d8eed801c2ff7904a0fc407ea696e23f1130b8c1c4fc6`；48POST/1,378,852tokens（缓存1,245,583、未缓存输入108,553、输出24,716），624.926秒。第49次转发被本批POST门拒绝，Agent exit1；代码产物有效与调用闭环未完成分别报告，不计49次真实模型请求。新增1次只读slots GET核对请求output16,384仍在实际处理；本教师准备/观察合计4GET，不是生成。

源DRAFT `source_experience_teacher_v1/draft_manifest.json` SHA `f009780d6105c1baff0f42cbfde8ef9b8148752595ea56113fe5faf2b7b24eee`，57个真实工具动作，普通历史75,415bytes，补丁/反馈卡8,614bytes。实际改动为Subquery.get_group_by_cols统一返回`[self]`及新增测试草稿test_fix.py。后者在actor中尚未跑通；不把它作为验证测试或正确示范。学习输入须保留真实失败状态，不能据D侧通过编造actor已完成自验。

补丁较宽：它不再区分alias或external columns。**在传播或生成普通skill前**，追加一次零生成的SQLite `aggregation`和`expressions`完整目录检查；同命令比较冻结base、公开gold与教师候选，全部只读运行。这是见过补丁后的扩大资格验证，不改原65项分数，不作为预注册确认；若教师新增破坏而gold没有，则不能将该修法当可靠通用示范，先定位适用范围。

补充检查已完成：三者均收集219项、各跳过1项；base为1 error，gold无失败，教师为1 failure（`test_aggregation_subquery_annotation`，SQL中的SELECT计数3而原有合同要求2）。其余218项不是额外独立任务，不能按测试数扩大研究样本量。receipt SHA `2e58244265854ac2dacca9e4c0bca9850d93dcd7109e467717ea380737a8ebcc`，教师log `ed69458dd7aa3629ae5f298338f1dcb7352490f7833ad6c8af2f092f2ed6e9da`；失败函数在clean/base/gold同字节，block SHA `fc38abc5b718ac3f06b36e86a0aa83223542aa537bdee5e21691183a3b226c10`。这是真实回归，暂不生成成功skill或训练示范。

下一次`teacher_feedback_repair`从上述真实候选和同一教师profile继续，仍48POST/1200秒/6MB；提供其实际父源diff及公开回归失败，不给gold修法或目标信息。diff由已验证DRAFT无损恢复，避免新上下文不知前次删改；它包含真实失败测试草稿，不把它认证为正确示例。新attempt保留父源、DRAFT、候选快照和补充反馈hash；普通8B的N/F条件及历史身份不变。目的为取得经完整当前合同核验的纠正轨迹，不据单次教师续修认证反馈机制。仍以关键/65项回归/原题及上述219项检查决定是否适合作正向示范，记录调用门、失败及全部来源成本。

本次源轨迹、DRAFT、预检及扩大回归55项已双机保存为私有`evidence_packets_20261106/django_teacher_source_20261106.tar.gz`；本机同名文件仍在`D:/Documents/Loop_D_assets/agent_learning_20261106/`。252,498bytes，SHA `f69dca996a4850c2cb0068315bc32dae23ef03cbec7e4746bf67cf2985c7cac3`，全部成员hash核对通过；不包含完整依赖/模型，不作为独立发行包。

教师续修零模型CLI预检已通过，stdout SHA `f78d9f88e5e511a8093108308a66ad6c764e9cd9438720218c70e82b028bb65f`；父候选manifest `c5f03e13e072d76f5f0c95f6a8abc674f635b8a8b150acfda946af948415734b`，实际父diff `03ff09d618b00fd2ff03ea7f36bc70c201ca56c73af88d575c6b1db321004a08`。代码`591d5195`三端同步后启动`teacher_feedback_repair_35b_20261106`；29项定点测试通过，docs lint为0fail/3条既有提醒。不修改在途绑定组件；原题与扩大回归等待本次实际产物。

## 单项反馈续修结果与联合目标强基线

续修27POST/775,019tokens（缓存734,426、未缓存输入36,602、输出3,991），105.253秒、Agent exit0、无代理拒绝。completed SHA `d183d65bed9e7f6f525b5d5845510c57507f33898cf6aaad33e4fa9fee614e5f`，raw `fdbf6fb1cebea2387db879fd270f2f5689e4593f6fade8417a5a167a00b230ce`。模型完整恢复了原Subquery方法，79项原有aggregation测试在actor内通过；但独立关键测试再次失败、原题重新报`status`歧义，65项映射回归仍通过。原题probe进程exit0只是捕获异常后打印JSON，实际`observed.exception=ProgrammingError`；不能按进程码计作任务通过。

同命令重放219项扩大集合：base与续修均1 error、gold无失败，各skip1。receipt `c0da3f0f33fb1bd98bcef174d1e49c5af5dadc49ea2f19e366a5c4f0e1b65fa1`。消除了新回归但恢复原bug，尚无适合传播的完整正向示范。

下一强简单对照`teacher_joint_feedback_repair`仍从**同一个首次教师候选**开始，使用相同profile、父diff、公开失败和预算，仅再列出该候选已通过的关键/65项回归/原题观察，明确新修订须同时保持原题修复与原有行为。父原题语义通过由`expected_data=true`与无异常核验，不把exit0当正确；不给gold补丁、隐藏断言或目标题信息。它是见过单项反馈结果后设计的一次开发对照，不冒充预注册机制确认。若简单联合要求就解决问题，后续学习方法必须超过这个基线；若仍失败，本对不继续堆教师提示，保留失败并转其他来源或明确标注的参考辅助监督。

联合首启`teacher_joint_feedback_repair_35b_20261106`在第13次POST等待约300秒后收到`The operation timed out`，12个完整usage步骤，358.732秒、Agent exit1；0次源码编辑，不能裁决联合要求的语义效果。completed SHA `4e888fb10abd281f4752dbf4de0c77edf5b67e3122b880b6a90b9cffc05ea8d0`，raw `cf957f6d7a8fafce297e538713e50b280e0a98efce77e97ccad10242804386df`。已报告283,711tokens＝缓存249,263＋未缓存输入32,531＋输出1,917；末次调用未回usage，总量仍有未知，不记0或用下轮填补。初始产物保留原题通过/1项公开回归，扩大检查receipt `7ecb4936bc89729849efb158156c3ebd29f0201e3b9ded1f249e6001034eeb35`。

实测opencode配置的request timeout仍为300,000ms，虽然教师output上限已为16,384；隔离harness把教师客户端等待改为900,000ms，8B仍300,000，episode48POST/1200秒/6MB及模型、题面、反馈、候选均保持。追加1次只读slots GET确认旧调用已不在处理；教师准备/观察累计5GET。新attempt只作相同联合合同的传输修复重跑，不按首启推断方法无效；开始前核对题面hash及归一化harness仅timeout不同。补记录usage步骤与物理POST计数是否一致，避免把部分usage当完整总成本。

<a id="current-27b-handoff"></a>

### 最新执行：27B长连接计量事故与修复

`teacher27_source_20261106`已由D停止，仅停止自有actor `4ad7c3998cbf`，未重启共享模型。旧代理只解析连接首个请求，随后双向字节relay把HTTP keep-alive上的后续请求一并转发，绕过逐请求计数、采样绑定及字节门。完成记录虽然写`posts=1`，raw实际有156个完成usage步骤、157个step_start；至少156次完成推理，另一次开始是否到达模型/用量未知。已报告1,930,944 tokens为下界，不把旧1POST当真实总数。相对96POST限额至少超出60次。raw SHA `7bf0272ba9af60fbe92dc52b6e7376929eecefa91f36e49c17a9e8cb2c7da86f`、completed SHA `6c57ce4d8f15b25e726c81f7c8ac3a5a2a85a6e7ca83bad4d5c3e3b9cb29d30b`原样保留；另存operator_stop与对账，不覆写历史回执。该轮反复对不存在的`/root/django/tests`调用工具；原题未修、65项映射回归通过，不能解释为经验学习机制失败。

确定性复现：同一持久客户端发三请求，旧relay在限额2下返回`200/200/200`，新单响应relay为`200/200/403`；chunked SSE解码后body保持一致。新harness每次只转发一个HTTP响应并关闭客户端连接，下一请求必须重新过门；私有记录实际转发JSON body（不记auth/header），完成后核对POST、usage步骤、逐请求hash。已知计量无效的源不可升级为合格经验。此前8B/35B记录有逐POST/usage相符检查；35B联合第13次未完成用量继续单列，不能由本次vLLM缺陷反推旧记录全部失效。

下一步先用相同题面/采样/默认thinking做传输诊断，检查工具`NotFound`是否真的进入模型请求；若连续出现同一无效路径且无源码编辑，可停止诊断而非继续烧满余量。只有确认反馈完整后，才决定是否调整通用路径说明或per-request thinking。每次改变配置都另列，不用接口修复冒充方法收益。

**诊断完成与下一配置**：首个修复诊断在生成前因注入缩进片段不符退出，0模型；修正后`teacher27_transport_diag_v2_20261106`实际60次请求、55个step_finish、910,170已报告tokens，含压缩步骤，另5条请求用量未匹配，不能记0。D观察50余步骤仍反复检索/阅读、源码Python树逐文件未改后停止actor；这是事后开发判断，不是预注册方法停止。关键/原题未修、65项映射回归通过，不能推论27B总体能力或反馈学习无效。raw SHA `8ad4446218696b5761394eacc66c61ae4d04e03fdbc128a052c99bcfdff2bfbc`，completed `b0d8c0ac26320b1c9f6c13ee534756bcf03a8ef84463e8a23b35e64496915972`。已修正每步实际采样；旧事故轮后续采样未核，因此两轮不构成等采样因果对照。

下一次同题面/base/工具/seed/temperature/角色限额，只将27B每请求thinking从模板默认关闭改为`enable_thinking=true, reasoning_effort=low`；通过实际转发body核对，不改共享服务。额外保存解chunk后的SSE原文与provider usage，区分公开step tokens与实际HTTP总用量，避免压缩/失败请求漏算。POST与字节预留各有锁和独立请求index。`steps>POST`否定完整计量；`steps<POST`可能是内部/失败调用，须报告未知成本而非直接判作超帽。零模型实际derived-harness控制和远端相关定点测试已通过，真实执行尚待下一轮。

本轮152个私有工件已双机逐成员hash核对：`evidence_packets_20261106/django_27b_transport_diagnostics_20261106.tar.gz`，1,401,459bytes，SHA `c31f52d4cfc2d235ccb7380f455efaa559003b4d7d7e5d7eb9a652dcc880d846`。包含raw、回执、代码快照及27B权重hash清单，不含模型权重或runtime分发。本地在`D:/Documents/Loop_D_assets/agent_learning_20261106/`。原账本保留，旧1POST由附加对账明确失效。

独立窄审确认SymPy14774→19235的13份资格工件和clean源码均匹配hash，可复用既有Python3.8/SymPy依赖，但新建blocked-SymPy投影；不能直接执行旧19487→19484 runner。新对source题面自带修法、target引用前序，仍属带限定开发。以该对并行准备，避免把整条研究卡在Django单题。

## 当前接续：优先核验并使用27B

### 27B采集与学生迁移：运行前合同

**Mode / Boundary**：inquiry-methods的minimal-experiment，使用已核原题、base/gold、现有隔离harness及GB10本地模型。最影响决策的三个假设是：27B能提供同时满足原题与回归的轨迹；该经验可改善8B的变化任务；普通skill相对历史/补丁卡有收益。先实测第一个，再做迁移，不用工程检查替代后两项证据。

profile `qwen38_27b_model_profile_v1.json` SHA `9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279`；实际66个权重及必要配置/分词文件共30,889,968,808bytes，manifest SHA `c96a2de0131047513e5723d8db26c65f98113402a0eb328ae61e98e3682d9bd8`。首次流式hash37.729秒、完整重读37.804秒，校验receipt `4e928c882b025b542b2ce3c85643ba3c58961efa7ef2aba7d41cf4d9cb4ca68c`。这些固定磁盘内容与服务容器/模板身份，不声称测得GPU内权重hash。宿主PID命名空间不对应，绑定Docker PID/StartedAt并将host start ticks保持未知。

**Action / Budget**：`teacher27_source_20261106`从同一冻结source base开始，沿用35B首次源题的通用环境说明，不附gold、隐藏测试或未来目标；temp0.2/seed7201、实际32K共享上下文/output8192。为采集完整教师轨迹，D按用户本地资源授权将此新角色的运行余量设为96POST/2400秒/12MB、单请求900秒；不追改旧8B/35B的48POST/1200秒/6MB。上限用于可复放和资源观察，不是方法成败门，更不意味着全项目模型请求预算耗尽。

退出后同一次独立评测检查关键1项、映射回归65项、扩大aggregation/expressions219项（gold已有skip1）及PG原题语义。记录实际执行/跳过数，拒绝零测试或只凭probe exit0判断通过。base/gold零生成控制已得到预期否/是，receipt `11b8ef99fc16255733eb754934fcf57115320d165f82099dc77091d077f98f8a`。27B CLI预检stdout SHA `0149dbb6173f10e301a1fa94ed420df0a71481dabaea73631159a3854383ee14`；只是工程资格，不是27B修复成绩。

**Continue / Metrics**：记录真实源产物后，形成历史摘要、完整实际补丁/反馈卡与一次普通skill；凡失败/回归如实进入材料，不冒充成功示范。所有目标臂开始前固定同一来源manifest。学生8B用相同target34176、seed7202/0.2/32K/output8192与48POST/1200秒/6MB，比较无历史、历史、补丁卡、普通skill；无历史仅在D侧绑定来源、不把经验给actor。比较原题结果、关键/回归、实际读取、形成及执行总成本。四种载体的信息量不同，属于完整使用方案比较，不能直接归因于文本格式。

**Risks / Exit / Next**：此对属于已知参考的开发，数据量不支持方法认证。27B身份/接口、源任务效果、迁移效果分层判断；源失败则据实际问题调整轨迹形成或换来源，不将失败外推为反馈学习无效。若普通历史、廉价规则或公开方法解释收益，就把它们作为强基线，继续寻找机制差异。第一动作是冻结本代码、真实运行27B源任务；合格材料后立即开展学生目标比较，而非继续停留于盘点。

用户补充GB10已有Qwen3.8-27B。只读实测确认vllm-probe在8006服务`qwen38-27b-fp8`，max_model_len32,768、max_num_seqs32、前缀缓存开启、qwen3_xml工具解析、qwen3推理解析；沿用既有自定义模板，不凭模板文件名断言每次实际thinking状态。容器ID `4b7c8b76fd42c474f76c9ee53b13c90980dc9ddae7e62cd8201dc58cc79eadf3`，镜像 `sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f`。本次1个只读models GET、0生成、0服务改动；没有把DSpark辅助草稿模型当完整27B。

私有盘点`qwen38_27b_asset_inventory_20261106.json` SHA `f4ac7074a76134358c6c58e30dd860aa84c2d2398df229f9e5641e916771565c`，已绑定config、权重索引和实际模板hash；全权重SHA清单尚未在本盘点计算。官方[模型卡](https://huggingface.co/Qwen/Qwen3.8-27B)和[vLLM配方](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)说明其沿用qwen3_5架构，因此本地config使用该架构名不等于文件误标；外部说明不代替本机任务成绩。

**下一动作变更**：优先把既有27B服务接入隔离研究runner，以原题、映射及扩大回归核验教师质量；4B/8B保留学生/成本对照，35B保留历史与辅助角色。900秒客户端修订尚未做35B重跑，该重跑不再优先。27B当前仅资产核实，尚未运行本批真实任务；使用其32K实际上限，不把35B的64K配置套用，不为科研重启共享服务。Goal继续active。

并行SymPy14774→19235已完成零模型开发资格：source原题/焦点base失败→gold通过、回归114/114双通过；target原题/焦点亦base失败→gold通过，原144项回归有2项两臂共同的Python3.8 AST失败，冻结排除后其余142/142双通过。source题面直接给修改提示，target直接引用前序PR，适合开发性同项目适配，不作为独立发现或跨项目确认。FINAL_QUALIFICATION SHA `941e2cc1f44ddb77059d6feb6a51669b7e5cab39cb8456a832231b998ba974e7`，其引用的全部文件hash由D复核；3个官方metadata请求、2个源码下载、0生成/训练。原144项失败与排除依据保留。

两次教师续修、扩大检查、27B盘点与SymPy资格共104项已双机保存为私有`evidence_packets_20261106/django_teacher_repair_and_sympy_qualification_20261106.tar.gz`，本机仍在`D:/Documents/Loop_D_assets/agent_learning_20261106/`；268,578bytes，SHA `579c3fd024c6339ddf36aaed06454cdc5a0a060b3e6d45907657427d4d73972c`，全部成员hash核对通过。包内对账标出联合首启13POST/12 usage步骤，不是完整源码/模型发行包。此Django系列共153实际POST，已报告3,245,196tokens，另1个调用用量未知，不能当精确总量。

## 下一来源资产筛查

已下载的Relationship.parquet第81行原配对为SymPy14774→19235，经验/目标记录时间2018-06-05与2020-05-01、关联issue14768/19235；base分别`8fc63c2d71752389a44367b8ef4aba8a91af6a45`、`226b942f0748819d5d2d723b91591fed4975961c`。可借原SymPy Python3.8环境与资格工具，但新对仍须核原题、base/gold及source merge祖先，不能复用旧对成绩。

第70行scikit25638→25637也是数据原配对，但source experience_issue_url与target related_issue_url都指向issue25637，先暂停把它作独立迁移候选；尚不判定数据集违规。记录时间先后不等于merge/base祖先，也不等于来源隔离。关系表SHA `f59b1a0fd021c6608bd185f15113cbbd26f804c20494da6d4827adb9ea70edb5`，Lite Experience `7a21f37b8bc179c7db5beeb14e88ac538ba283455c776e6b2535bbfb6e3551b4`，Related Lite `1930b392f7beb17a0d87c2e79d1eb889af2c5996b23a003386651ba64a68b8f3`。本盘点0生成，资格结果单独记录。
