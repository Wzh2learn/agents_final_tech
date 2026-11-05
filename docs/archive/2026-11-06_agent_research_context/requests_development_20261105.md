> 历史快照归位于 2026-11-06。原文件 `research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md` 的连续片段；旧任务、结果与预算保持当时口径，不能作为当前授权。现状见[第二阶段计划](../../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 恢复研究：Requests 自然任务对（2026-11-05）

用户确认升级框架后恢复科研 Goal。当前开发问题是：真实执行结果能否被经验准确保留，并在相关后续任务中产生实际帮助；同信息的普通历史、简单尾部保留和确定性反馈摘要作为强基线。此前 Sphinx/Django/SymPy 已暴露且各有能力或接口混淆，本轮不将其继续充作未见确认。

新自然任务对为 `psf__requests-3362` → `psf__requests-3481`。源 PR 已在目标基线前合并，目标 hints 提及源 PR；Agent 只获得问题正文及无 Git 历史的当前源码，不提供 hints、参考补丁和未发布到基线的测试补丁。两任务 source/target 基线分别固定 `36453b95b13079296776d11b09cab2567ea3e703`、`b2f6173a3833153f57d9e3baa6728c5cc46c0b29`。研究者已读取任务与测试用于资格验证，因此是新的开发来源，不能称研究者盲验。

[资格脚本](../../../research/agent_frontier_portfolio_20261029/qualify_swe_contextbench_requests_20261105.py)在 GB10 ARM 的隔离 Python 3.8 环境、固定镜像中完成 source base/gold 关键测试 `0/1`、`1/1` 和 target `0/2`、`2/2`。完整回归为 source `73/75`、target `65/67`：两项外网黑洞超时测试在禁网环境的 base/gold 同样失败。原始完整记录保留；预先冻结排除后，独立重跑的 source 两臂 `73/73`、target 两臂 `65/65`。另显式映射3条误记的嵌套类节点，IPv6参数通过完整收集后精确nodeid选择，缺失节点会使评测失败。资格总回执 SHA-256 `54ea5ffc639201ff5b19ff87e7066eef7f86cdc8f35ce8354393aadfb03eda0e`，GB10 私有根 `research_evidence/agent_learning_20261030/requests_qualification_20261105_v3/`；时序摘要 SHA-256 `8fa30986065f96c13f4466fa916644d945b103c2d4635accae16b4d0f4266d08`。上游 Requests 源码 Apache-2.0，任务数据按其来源单独记录。

[Agent 运行器](../../../research/agent_frontier_portfolio_20261029/run_swe_contextbench_requests_20261105.py)复用既有 OpenCode/Qwen 隔离 harness，新增显式 `attempt-id` 的独立输出根，不覆盖旧尝试、也不用改 seed 隐藏重试；接入原始产物、反馈、成本 sidecar 和证据图。先执行 source 与 target 无历史开发基线，各最多24次POST、900秒；同模型、seed 7201、temperature 0.2。参考和隐藏测试仅在结束后进入独立评测容器；回归只报告上述冻结可执行子集。实际任务有成功与失败区分后，源经验仅使用本轮真实源轨迹/反馈，比较普通历史、普通skill和确定性反馈摘要，再决定公开候选能否形成合法且公平的对照。当前不预设方法收益。

本轮真实运行先得到 source 无历史 `24 POST / 233,763 tokens`（含缓存129,506），Agent 因请求上限退出1，但恢复原始测试后的源问题 `1/1`、冻结回归 `73/73`。源普通skill只用已存源历史独立生成，`1 POST / 10,820 tokens`、正常stop；源历史、透明结果卡和skill均在首次目标调用前冻结，freeze SHA-256 `70920a45ff7d4b22d3e89c08ce905e32a4f57f6cc32180269dcf3cd30f79f27c`。

| 目标开发臂 | 参考问题测试 / 可执行回归子集 | 实际POST / 报告token（含缓存） | 结束与读取 |
| --- | --- | --- | --- |
| 无历史 | `0/2` / `65/65` | `23 / 233,297`（缓存178,347） | Agent正常退出0，实际修改了vendored urllib3 |
| 源历史 | `0/2` / `65/65` | `24 / 380,154`（缓存332,857） | 请求达帽退出1；read工具完整读取280/280行 |
| 普通skill、透明结果卡 | 未执行 | `0` | 题面/环境/参考合同不一致，停止此对上的后续模型比较 |

上述三条Agent轨迹的自动证据绑定检查均在私有目录执行，原始回执保留；source completion SHA-256 `4d3e0e29e6c5f08a10b2344f1129084949878995264d80043ab023e5e5a43f74`，target none `7bad941a5be810fc95b72ff93b5abcd7f1102bcb69d57db473c3fac21842a3bc`，target source_history `53cd06d4b48073baa568059046b10c89f2b75089718ab4573cf51a3b428fd2e9`。目前只能说两目标候选未通过该冻结参考合同；原题是流式读取时的`_fp.fp.readline`崩溃，而这两项gold测试检查未设置/非法encoding时的即时异常。无历史候选实际对vendored urllib3增加空文件对象guard，不能据gold未过就断言没有实现原题修复。已安排独立、零模型的本地流式HTTP复核，分别记录原题行为和参考合同；保留旧评分，不据此调整已冻结skill。

[原题行为复核](../../../research/agent_frontier_portfolio_20261029/probe_requests_streaming_20261105.py)在本地真实httpbin `/stream/20` 响应外包装HTTP/1.1 chunked传输，在禁外网容器中分别执行四个已冻结候选。未手动指定encoding时，base与无历史候选均输出20行bytes且无异常，gold抛TypeError而没有输出，源历史候选抛AttributeError而没有输出；显式设UTF-8时四者均输出20行str。因此原题要求、返回数据类型和gold的即时异常合同不能合并计分。原报告使用Requests2.11.0/Python2.7，冻结目标源码自报3.0.0，本次环境是Python3.8；不能据此否定原报告，也不能把20行bytes算作Unicode解码正确。该探针在看到目标结果后设计，仅是当前本地条件的机制复核；一次源历史候选在此条件出现读取失败是保留的开发观察，尚非稳定的负迁移结论。

探针完整回执 SHA-256 `d8645e9e1eb328f585f47b703ff9c28f5f16a710a06054e329176cc8df25fae6`，私有路径 `requests_streaming_probe_20261105/receipt.json`；原始issue佐证 SHA-256 `71342d360875d405d0a1dd9db24ed42ea0a7dfa8457b9a8ada8cba8d75763b5a`。保留原gold评分和全部候选，不再扩大该任务对；后续新来源资格先核对题面、实际base故障和参考行为的一致性，再花模型预算。源任务仍提供一次有独立测试支持的实际修复轨迹，可作为经验形成开发材料。三个已执行episode的自动绑定检查各通过10项文件哈希；同episode重复执行的负控制在生成前被拒绝，没有新增模型请求。

本次恢复阶段截至上述运行累计 `74` 次转发模型POST、`916,873`报告tokens，其中缓存`692,502`已包含在总量；另2次被代理拒绝的超帽请求没有转发。该小计包含三条Agent、一次源skill生成和前述两次RethinkSkill接口诊断；无训练、judge或生产Memory写回，不与历史旧账直接合并。

<!-- End of preserved historical segment. -->
