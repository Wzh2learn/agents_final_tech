# Dialogue parser: feedback, repair and verifier development study

日期：2026-10-30。状态：**真实 Agent 开发性机制观察，非跨任务确认、非已成立论文方法。** 同一 SkillsBench v1.1 任务、同一 GB10 Qwen3.6-35B-A3B 与 OpenCode、相同公开输入，在线生成期间无外网、无隐藏 verifier；测试在独立容器内事后运行。使用项目适配 runner，不声称官方 harness 复现。研究设计在[实验卡](archive/plans/DIALOGUE_AGENT_PILOT_PLAN_20261030.md)，逐次资源与 raw hash 在[账本](dialogue_pilot_summary_20261030.json)。

数据固定：SkillsBench checkout `b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af`；上游 `dialogue-parser/task.md` SHA-256 `d14e9102a433abcdb7cbab8a02e082b698fb87eb50fd9e8bc95c2ebb8d9cc1ab`；原 `verifier/test_outputs.py` SHA-256 `d0effcfa8ba898260bce69ba8a0c4852f4959a83e9130cc69c13847f0f05b01c`。这能固定检查对象，但不排除公开题目曾在模型训练中出现。

## 实际结果

| 独立运行 | 原任务测试 | 本次新增合成解析烟测 | Agent / 资源 | 解读 |
|---|---|---|---|---|
| 初始 no skill | 34 通过 / 1 失败 | FAIL：缺 choice node | 触及 8 次请求上限，8 POST | 写出文件但其解析器没有在小例中返回 choice 类型。 |
| 初始全部 skill | 27 通过 / 8 失败 | PASS | 触及 8 次请求上限，8 POST | 烟测通过不代表真实脚本解析或技能整体有效；两组信息量也不相等。 |
| 修复权限后的 neutral，16 请求上限 | 29 / 6 | PASS | 正常退出，11 POST | 普通重试改写了解析器；多项原测试变差，其中有些断言偏好直接边结构，不能未经裁决全部当作真实语义错误。 |
| 修复权限后的具体反馈，16 请求上限 | 34 / 1 | PASS | 正常退出，11 POST | 原 `shape` 检查通过；唯一失败是 reachability 测试未将终点 End 入队。标准 BFS 检查原输出 205 个节点全部可达，含 End。 |

具体反馈是从初始 no-skill 原测试的失败断言提取的“choice nodes 应可视化为 diamond”；neutral 仅知道未通过所有检查。两臂都以同一初始 `solution.py`、`dialogue.json`、`dialogue.dot` 的 SHA-256 拷贝作为起点，在同一运行限制下独立执行；反馈内容经过人工选择，本研究没有把原测试代码直接提供给 Agent。事后只读核对具体反馈组的 JSON 和简单 DOT 声明：58 个 choice 节点均标为 diamond，无非 choice 节点被标为 diamond；该解析不覆盖完整 DOT 语法。Agent 只能在实际能够取得同类反馈的任务中复现这个信息条件。本轮看到的是**同一个开发案例中局部反馈可能帮助修复**，且普通重试也改善了基础烟测；不足以说明反馈学习、跨任务技能迁移或统计优势。

**被废止的四次修复对照**：前两个 8 请求、后两个 16 请求运行曾报告仍是 34/35，但复核原始轨迹发现具体反馈组两次写入 `/app/solution.py` 均 `PermissionDenied`。原因是宿主机复制文件为宿主用户所有、模式 0644，而容器去除了 DAC override 能力；生成前条件阻止了 Agent 更改初始文件。因此这四次只能作为运行故障证据，不能比较反馈效果。经独立容器复现文件 mode 0666 可写后，才进行上表末两行；成本全部保留，不抹除。

## 验证器本身的反例

1. 原 `test_outputs.py` 中 shape 检查只查 DOT 文本是否出现 `shape=diamond`，不检查节点类型是否匹配；原测试未检查 `solution.py` 是否存在或调用 `parse_script`。在**单独复制的构造控制**中，保留初始静态 JSON，将 DOT 的默认所有节点设为 diamond，并完全不提供 `solution.py`；原 35 项测试仍 `35 passed`。这不是某个实际 Agent 生成的结果，也不说明 benchmark 其他任务存在同样问题。复算用 [控制构造脚本](prepare_dialogue_verifier_control.py) 和源码的独立测试容器；原输入 `dialogue.json` SHA-256 `281b570d6c1db20f5f48eb78145c80f0c00e684a03a500b0ea52415c8c178756`，控制 DOT SHA-256 `dc4cec7577e7ced72143d28faf71a5c75482c577d926b07a9e4efde5fe8857b6`。一次只读容器重放先因缺少可写 `/tmp` 失败，加入 tmpfs 后重放 35/35；第一次工作副本也独立得到 35/35。
2. 原 reachability 测试的 BFS 对目标 `End` 明确跳过入队，但随后在全部节点中判定不可达；只要输出同时包含 `End` 节点，它即可能被该测试误判。具体反馈组的输出中 End 存在且从 Start 可达，标准 BFS 证实 `unreachable=[]`。这说明该断言与其“所有节点可达”意图不一致，不说明其他测试或整个数据集无效。
3. 新增 [确定性烟测](dialogue_semantic_smoke.py) 调用实际 `parse_script`，检查一个新的小型选择脚本中 choice 类型、文本和目标，另提供标准 BFS 和有界 DOT/JSON 节点身份对照；[5 组单元测试](test_dialogue_semantic_smoke.py)覆盖合法、缺 choice、缺目标、终点可达及错误节点形状。它是观察后构造的小例和诊断工具，**不是全覆盖独立 gold、正式模型评级或上游测试的通用替代品**。在只读、无网络容器中，初始 no-skill 为 `missing_choice_node`；构造控制为 `missing_solution_file`；初始 all-skill 和两组权限修复后的 Agent 输出均通过该小例。

## 成本与材料

8 次物理 Agent episode 合计 **82 POST**，已返回 step usage 合计 **1,132,954 tokens（含已报告缓存输入）**；计入了 4 次权限错误运行的 44 POST。各次调用、时间和原始输出 hash 见账本。真实模型 provider 未返回的 usage 如存在只能记 UNKNOWN；没有训练、付费 API 或生产 Memory 写回。文件权限修正前还有一次 runner 源片段计数检查失败，发生在任何模型请求之前；一次只读 verifier 重放缺 `/tmp` 也不产生模型调用。

原始 prompt/tool events、stderr、verifier 和工作文件保留 GB10：`/home/testuser/wzh/research_evidence/agent_learning_20261030/agent_tictoc_extended/dialogue-parser__*` 和 `.../dialogue_repair/dialogue-parser__*`；[汇总脚本](summarize_dialogue_pilot.py)从逐次 receipt 和 verifier 重算。两条权限修复后试验的初始化 hash 相同；它们在已观察面板上的自适应结论不应转述为预注册确认。

## 下一步研究选择

将可执行任务的**反馈可信性、局部修复和回归控制**作为候选问题：验证失败信息如何通过普通重试、定点修复、以及有可见复核的候选机制改变行动与原有正确行为；对照自查、同预算重复、明确编辑提示、可部署的单测与回滚。优先独立、可复验的任务族，事前固定原始环境、时间、工具与质量/成本口径，并对 feedback/reference 缺陷做正反控制。SkillLearnBench 已研究外部反馈与技能学习，必须继续对照其公开基线和最新近邻；现阶段没有提出已证实的新方法，也不在原一个面板上做泛化宣称。
