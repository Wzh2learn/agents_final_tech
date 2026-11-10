# Astropy：统一资源配置下的经验强基线

## 2026-11-10 洁净来源采集合同（首次新生成前）

旧source的依赖暴露未来目标源码，不能作为新比较的洁净经验。复用已检查的v2隔离投影和本页source任务，执行一次真实source（Qwen3.6-35B-A3B Q4、seed7201、temperature 0.2、32K/8192、24 POST及900秒上限），先不运行目标、不训练。以原生问题和回归独立检查修复及Agent退出，保留完整轨迹和实际成本；失败或未知只记录，不反复堆提示。成功才从这次source形成经验，后续目标开发、配对干预与强基线另定同预算合同。此项仅形成来源素材，不是CCER方法效果或独立泛化确认；source和已曝光目标均非盲集。

**事后纠正**：发起新source时遗漏了[11-06已完成的隔离source及四臂](ASTROPY_ISOLATED_CONTROLS_20261106.md)。当时已有v2洁净source，重新采集并非必要；本次source及skill的14+1 POST、185,012+10,489 reported tokens（source缓存97,288已包含）如实另计。新source成功不能作为独立任务；不同上下文及配额也不支持旧新单变量因果比较。后续先检查全部同主题记录，再决定是否采集。

## 2026-11-10 经验片段配对筛查合同（新目标生成前）

洁净source成功并形成普通skill后，选已曝光的15082作机制开发：同一模型、初始目标、seed7201、temperature 0.2、32K/8192、24 POST/900秒，串行比较无经验、完整skill、仅将skill的`Task-Specific Choices`节替换为固定遮蔽标记。两个skill臂均用既有文件读取机制并核查实际读取；保留和遮蔽的其他文本须逐字一致。此节部分信息与其他段落重叠；长度与位置有变化，遮蔽差不是单条知识的无混淆因果估计。独立原题/回归只在actor退出后评分，不作挑选输入；原始skill及来源账不改。记录成功、读取、使用与生成成本，1次/臂仅开发；若全部成功或均失败，不据此断言方法有效或无效。后续自由修订、长度/位置对照和新任务另按结果安排。

**筛查结果**：新source为Agent exit0、原题及focus 1/1、回归179/179，completed SHA `30e6be6765259574cc0ea98b51c0e9392048540f78007b8be50b54818309f91c`；普通skill形成1 POST/10,489 tokens、SHA `794875de57ee3114f0575f09a9631313083c39894139ee40def900ad7e9419cf`。三目标臂均达到24 POST上限、Agent exit1，回归均132/132：

| 目标输入 | focus | 经验实际读取 | reported tokens / cache子集 | completed SHA-256 |
| --- | --- | --- | --- | --- |
| 无经验 | 1/3 | 不适用 | 313,348 / 240,078 | `ab97d192640e74e42fbe954557513956ee4ea0d2568e5a62454c3b96d2562456` |
| 完整skill | 0/3 | 34/34行 | 390,378 / 252,652 | `1dd789e5389b317ac5721ae169412b775121180f8ec160e1ff7aa00509914319` |
| 遮蔽一节skill | 2/3 | 27/27行 | 345,805 / 258,483 | `47381c7dd058e00dae2fae1f043471eae8d5f5e6c95277c5d990b189522fd526` |

三臂均未完成任务；raw与回执哈希复核一致。完整与遮蔽臂均发生真实源码编辑，但修改位置和失败细节不同；一次采样、改变文本长度及内容重叠均不支持单节的稳定因果作用。issue probe须看实际字段而非只看进程exit：无经验的有单位无mask情形得到全False数组；完整及遮蔽臂各有未消除异常。初轮不支持方法效果，不再在该目标追加调参；后续转向不同任务，并严格隔离评分。模型形成与三臂合计87 POST/1,245,032 reported tokens，其中缓存848,501为子集；研发Agent开销另计。本批原始记录留GB10私有`astropy_agent_20261105/attempts/ccer_*_20261110`，不以摘要代替raw。

> 2026-11-06 | 开发对照，代码在`9c92521b9e04164cf8cc1a4e95ee1f8ada1bcb1a`冻结；沿用[原source与旧profile](ASTROPY_PILOT_20261106.md)，不把两组差异解释为单一变量因果效应。原始source/经验均复用，没有重算形成成本。

## 检验的问题

旧组出现普通skill单次成功、普通历史末次输出length。新组统一增加资源并采用原值等价的安全历史，比较“有没有可复用证据”和“是否必须抽象成skill”；透明源补丁/真实结果摘要是强简单基线。

## 固定配置与结果

同一目标题面、源码、模型Qwen3.6-35B-A3B Q4_K_M、离线工具、冻结3项问题/132项回归；seed7202、context65536、output16384、每臂最多48转发POST/1500秒、代理请求体总额6MB。按none→补丁结果→安全历史→普通skill顺序串行运行。源沿用seed7201；参考和测试只在独立事后评分副本应用。

| 目标输入 | 关键测试 / 回归 | 转发POST | 总tokens（含缓存） | 未缓存输入 / 输出 | 运行秒 |
| --- | --- | ---: | ---: | ---: | ---: |
| 无历史 | 3/3、132/132 | 19 | 677,365 | 66,051 / 7,363 | 280.64 |
| 实际源补丁＋源结果 | 3/3、132/132 | 16 | 454,616 | 73,270 / 10,436 | 283.08 |
| 长行安全的完整历史 | 3/3、132/132 | 12 | 325,435 | 33,264 / 4,006 | 103.20 |
| 普通生成skill | 3/3、132/132 | 19 | 409,368 | 63,061 / 7,295 | 191.26 |

四臂均Agent exit0，原题两例均为正确data、mask None、正确unit。三个经验文件均在一次read中逐字完整进入工具输出：补丁结果36/36、安全历史241/241、普通skill32/32。没有额外判断模型。总tokens包含缓存，不能直接等同GPU计算量：补丁摘要的总tokens比无历史少，但未缓存输入/输出更多、实际用时并未减少。

## 科研裁决

**后续可读面审计降级（在下一次目标生成前发现）**：actor只读挂载的`/deps/astropy/nddata/mixins/ndarithmetic.py`来自5.3.2 wheel，包含目标gold的两处未来修复（`hasattr(operand, "data")`和`getattr(operand, "mask", None)`）。`/root`源码优先导入并不能阻止直接读取`/deps`。四臂raw的tool input中未发现依赖路径、`sys.path`、`inspect.getfile`等显式命中，但这不能排除间接访问。上述实测数值与成本保留；它们不再作为参考隐藏的干净迁移证据。旧source也使用此依赖面，后续应在隔离依赖和解释器可读目录后，重新形成source经验并复验，不能仅换target挂载后沿用旧source。

1. **旧的“skill独自成功”不是稳定方法增量**：新配置下无历史也完整修复；由于seed、context/output和请求配额共同变化，不能只归因于输出帽。
2. **完整历史是必须保留的强简单基线**：此单次运行同时更少请求、更少未缓存输入/输出和更短用时；依赖可读面污染使效果比较仍待洁净复验。不把生成skill当作方法收益的默认来源。
3. **本组不同输入条件下观察到成本差异**：该次结果没有表明复杂技能抽象优于完整历史。下一步在不同项目的自然source/target中重复对照，再判断来源约束、动作时适用性或学习型编译是否仍有残差。

本组一个已曝光任务、每臂一次；3个参数化测试不是3个独立任务。较长历史的格式、预算与seed变化均须如实区分，耗时也受缓存、运行次序和共享机器影响，不报告为总体稳定节省。

## 隔离修正与后续复验

新[actor依赖投影](../../../scripts/graph/research_actor_dependencies.py)单独复制解释器/标准库和第三方依赖，不把原完整环境挂给actor；排除精确`astropy`项目目录及其metadata，保留`astropy_iers_data`。现役私有`astropy_agent_20261105/actor_dependencies_v2`共3442文件，manifest SHA `32fd788dae461e4eca1f792c9f9e569c70bac9ee7d0befb3335848f98efe1aed`。v1保留；v2仅增加同字节的`python3`入口，防止它落到image的不同版本解释器，其他投影文件逐项一致。运行器在前后验证固定hash，并拒绝started/completed/harness未绑定这一可读面的旧source；不是仅给旧target换路径后继续。

零模型容器检查：source/target可从冻结源码导入并使用NumPy、离线rg；`/deps/astropy`和`/extra/lib/python3.10/site-packages`均不存在。相同隔离依赖下再次执行base/gold控制：source关键测试0/1→1/1、两臂179/179回归；target关键测试0/3→3/3、两臂132/132回归。原资格目录只读挂载，未改历史资格或原始数据。

现役v2三解释器别名、两个环境和8个base/gold控制均实跑通过，`actor_isolation_check_20261106/astropy_environment_v2/receipt.json` SHA `a1f63adf3dd850337d9ac481da091c1cf684daa565eeecb8d56061f0f5532a0f`。较早v1私有`actor_isolation_check_20261106/astropy_environment_receipt.json` SHA `3e56f3fae8cf78491bf442a7622dc7ba2b7b3b7dae96660715217975ade6a0cf`；`astropy_controls/receipt.json` SHA `5faa13f2ce8dfa22e67b3163b3e51bce467b4be18e75d6eda771fe7ff2cb7d6c`。这是运行隔离与控制复验，不是新的Agent方法结果。洁净source及target比较须使用新attempt，尚未执行。

## 成本与证据

本组新增**66转发POST /1,866,784 reported tokens**，其中缓存1,602,038已包含；未缓存输入235,646、输出29,100。0训练、0judge。全部已终态，未出现预算拒绝；旧source14POST/154,712tokens（138.67秒）和skill形成1POST/8,565tokens（17.34秒）沿原账，只计一次。

部署比较须区分：已有历史的增量使用成本，以及专门采集source经验的完整成本；不能只报下游省时而隐去形成代价。本次target计时来自自动sidecar，未把重复缓存token当新生成计价。

私有根：`/home/testuser/wzh/research_evidence/agent_learning_20261030/astropy_agent_20261105/attempts/profile_controls_20261106/`。

| completed前缀 | SHA-256 |
| --- | --- |
| target__none__seed7202 | `3958090632c273b37f132ac055929b05b66d2811a1433d70ef80ec1cc494d5d2` |
| target__feedback_card__seed7202 | `55c38deb1c55b74e0924bef38fc9be66f5bf8c2ab5085e5ed35d6f74ba0253fe` |
| target__source_history__seed7202 | `a0c2febea5d437905f0da988764822190b064e981b0ba635df1e829bc644ca7b` |
| target__generated_skill__seed7202 | `e06a46ed714e5636c68b848fc7964e94110c64ff09587fee2b65c7803a884c53` |

按前缀读取`.completed.json`、`.auto_record.json`、`.evidence_check.json`、`raw.jsonl`及独立评分日志。源码、输入和实际采样字段绑定；这类检查不是独立方法评审。一次Windows CRLF shell传输在运行前解析失败，修正传输后首次执行，没有覆盖或重复模型episode。

## 保留的事前合同与零模型接入记录

以下内容从原批次记录连续迁入；在本组首次生成前已位于Git `9c92521b`，不是看到新组结果后重写成功线。

**下一批事前合同（在旧结果后设计，新的运行前冻结）**：复用该次真实源，不重新生成源或skill。固定新attempt、seed7202及同一模型/工具/参考；统一实验端context65536、output16384、每臂48转发POST/1500秒，服务实际上限只读核对为65536，不重启服务。新一轮比较：无历史、原始对象等值的长行安全历史、原普通skill、确定性的完整源补丁＋真实结果。每条input hash和来源先绑定。至多4臂192次转发；不把该设置与旧8192/24臂直接解释为单一变量因果实验。

长行安全历史必须能逐值重建原对象，不补造新反馈；补丁摘要必须来自完整实际源diff与独立结果，不加入目标参考或推断修复指令。新组用于排除简单证据组织及预算解释，随后决定重复、公开近邻和新项目资格。目标均为已曝光开发任务；原source形成费用只在原批次记一次，新增目标费用单记。


新输入profile已零模型生成，根在`astropy_agent_20261105/attempts/profile_controls_20261106/source_experience/`；manifest SHA-256 `5cf3474b13d2030715e171ffaceb31dca340b3073ad1195e8a726d945f71a2b0`。长行安全历史SHA `9d6e8847b64dc5a073f906962d38532aa451c5455e012534e66eda9ea1624663`，源补丁/结果摘要SHA `3739e9999f1cefcd7b5f821d3782eda81cec3b18d2566d74c2694a9f20f3c8c4`；普通skill沿原hash。新target顺序固定为none→源补丁结果→长行安全历史→普通skill，seed7202；source沿用原seed7201，只在原批次记账。

[输入准备器](../prepare_astropy_evidence_profiles_20261106.py)校验源raw/评分/完整diff，拒绝跨来源错误绑定、刷新hash后向摘要追加的无来源文本及覆盖已有profile。修改后的runner默认4种target派生与旧harness逐字节相同；新seed实际进入代理payload、路径和配置，新增上下文/输出/请求及墙时设置在零模型控制中核对。代码验证、原值roundtrip及参数检查12项通过，8项准备器测试通过；首个私有验证目录存在一次导入旧模块导致的测试失败，第二目录显式加载新模块后通过，未冒充科学结果。证据在`astropy_agent_20261105/implementation_check2_20261106/implementation_receipt.json`。原记录和旧执行上限不追溯修改。
