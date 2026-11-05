> 历史快照归位于 2026-11-06。原文件 `research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md` 的连续片段；旧任务、结果与预算保持当时口径，不能作为当前授权。现状见[第二阶段计划](../../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 2. 候选 A：环境变化下的 Agent skill 适用性与可靠迁移（优先资格验证）

**问题与待证机制**：已有工作评估 skill 是否帮助解任务，却不能据此断言：当某个 skill 在旧版本工具上有效、但工具语义或接口发生自然演进时，Agent 能否只凭运行时可见证据识别其适用边界，并修正或避免错误使用。候选机制是将每条 skill 绑定可检查的适用条件和验证结果，在不满足条件时采用透明 fallback 或有限修复；不是声称“条件化 skill”首次提出。须在获取真实变更和复现 SkillLearnBench/SkillsBench 基线后重新查新颖性。

**资格/数据**：先钉住 SkillsBench v1.1 task 与 code license，再从公开仓库正式 release / commit 中选择 API、CLI 或软件依赖的历史改变，离线对照原 skill 所需执行合同；每族分离仓库/版本、避免把版本变体当独立样本。受控变更仅为机制探针，和自然变更结果分报。项目已有 NtripBrowser/Partridge 迁移和 PyMigBench 样本只作可执行资格/开发，不作未见新样本；其当前强基线已能解释旧面板，不重开旧方法结论。

**至少四臂**：无 skill / 原 skill（同长度）/ 静态版本或可见 metadata 规则 / 普通重试或验证器失败后重试 / 新的合同条件候选；资源允许则用官方适配技能或 SkillLearnBench 可复现流程。信息可见性和 token 预算匹配。结果通过目标系统行为测试＋合法 API/状态合同；oracle 合同仅用于评测，禁止作为 agent 提示泄漏。负作用、正确任务、UNKNOWN/过度拒绝、总 token、工具次数、GPU 秒和墙时分别统计。

**可证伪预测**：相同预算下，条件化候选在变更版本的真实任务族降低误用或提升可验证成功，同时在未变更时不过度弃答；若静态版本检测、无 skill、普通重试在匹配成功/风险/成本下追平，则方法停止，仅保留负结果。先约 3–5 个版本族做资格控制、再冻结 20–30 个未见族（具体数量以可获取数据和资源评估为准），报告 family 聚类区间，不把小样本当显著确证。

**论文潜力/风险**：对应热门技能进化与 agent 可靠性，与 Paper E 形成“度量—方法”联系；最大风险是任务由简单版本规则完全解决、skill 内容与测试相互泄漏或只在一个软件生态生效。可基于约束写机制性实证或新问题，但不能由小样本直接推出跨域普遍定理。

## 3. 候选 B：可验证预算分配：什么时候让更多 Agent 帮忙？

**问题**：对真实工具任务的中间状态，能否在观察开销计入后决定“继续单 agent、请求独立审阅、还是执行确定性测试”，使同预算下正确交付更高？要超越 General AgentBench、MultiAgentBench 和 Google 2026 的[规模研究](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)，必须明确新变量是可部署的中间状态/验证证据，而不是重复比较 agent 数量。

**候选数据**：SkillsBench/公开软件工程 benchmark 和可离线验证的结构化工具环境；校验许可证、可运行容器、源码与测试是否暴露。多 agent 实验应把共享上下文、检索、模型 calls、额外 verifier、串/并行墙时都记入预算；使用 OpenCode/Qwen 组成真实工具 agent，而不是把三次单轮回答算成多 agent。

**基线**：单 agent 等 token 延长、等预算多样采样＋同一个可部署选择器、固定验证顺序、确定性本地测试、随机审阅/固定规则；项目过去 exact-cache 已完全解释的收益不得复用为新发现。候选只用实际可见日志与资源，不用隐藏答案或 gold 预测难度。

**判据**：按未见任务族配对报告任务成功率、质量—成本 Pareto 曲线以及额外验证成本；两种以上任务结构、多次重复后若动态机制仍无法超过最强固定/随机方案或成本抵消，停止。训练是可选备选，须先确认可执行训练标签、分离任务族与不训练对照。预估首轮 3–5 天准备和 100–300 个 agent episode 是规划上界而非实测；并发和计算由实际 GB10 资源测定。

**风险**：管理系统本身造成收益、任务选择偏差和多重比较；小模型可能在基线任务失败而无可识别 headroom；未证明可推广。若无强基线残差，则降为经验结果而不是硬造学习算法。

## 4. 候选 C：不确定工具结果下的执行恢复与受控副作用

**问题**：模拟或真实可离线重放环境中，工具返回超时后，agent 是否能凭可见副作用证据选择重试、只读核实、补偿或 UNKNOWN，避免重复/遗漏？对标 UndoBench 的同阶段故障和幂等、以及 ToolRL-DR 的 transition 干扰；仅重复它们不构成创新。候选差异可检验“部分可见、跨工具组合的恢复合同”，但须核对其现有 8 域/36 族覆盖和最近后续研究。

**实验**：优先在隔离模拟 API/文件操作中按开发、未见工作流分组；冻结 ground-truth effect ledger，部署 agent 只能看到可公开的读取接口。强基线：普通 retry、只读查询+重试、server idempotency、回滚补偿、always abstain；不可声称具备线上支付/生产验证。量化 conditional recovery success、重复或丢失副作用、任务成功、不可恢复状态、成本。需要含至少 2 类故障时序和独立来源；如 server 幂等/只读查询简单可靠则停止候选。仅在此基础上才考虑训练小模型并比较 no-training 和普通 SFT。

## 5. 已完成的只读资格检查和下一步

- 补充真实历史源码的离线执行资格：参见 [Partridge qualification](../../../research/agent_frontier_portfolio_20261029/PARTRIDGE_NATURAL_VERSION_QUALIFICATION.md)。复制的两版在既有兼容性测试补丁下均为 42 passed；`__version__` 均为 `0.11.0`，仅版本号无法区分，但针对已知变更的简单静态检查可区分。没有找到其历史 `SKILL.md`，也未跑固定 skill/普通重试/模型；不能视为 skill 方法实验或残差。原项目旧面板强基线结论依然有效。
- GB10 上实际检查：`/home/testuser/.opencode/bin/opencode`、项目 `venv/bin/python`、`scripts/graph` 和 `/usr/bin/docker` 存在；Python 为 3.12.3。`nvidia-smi` 可见 `NVIDIA GB10`，该查询的总/空闲显存返回 N/A。`command -v opencode` 在非登录 SSH PATH 中未找到，但绝对路径存在。
- 这仅证明文件/命令存在：未检查 Docker 守护进程、未访问模型服务、未调用 OpenCode 或模型、未检验模型权重/许可证、没有进行 agent episode；不可称为 Agent 实验。不开启生产 `:5050` 或现有服务探针，不读取/打印密钥。
- GB10 旧项目两个开发来源的报告实际存在并计算 SHA-256：`research/publication_thesis_goals_v1/revision_v2/G2_V2_REPORT.md` 为 `51412f1059fef4b504d7787d18d1c369396ec7adfff9f5d8332eaf3ec8eb3ac2`；`research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/QUALIFICATION_RETURN.md` 为 `4d9d301957e1a516ecbc679562fad3d2b175f7a1fe2516475648de7c3488323b`。文件存在与哈希一致不代表复跑、环境可用或满足未见来源条件。
- 下一阶段先冻结 A/B/C 的选择、时间和次数上限，完成公开任务版本/许可/环境资格；任务在隔离工作区运行，原始观测和失败保留，禁止训练测试交叉泄漏。优先 A，B 为另一路候选，C 对照当前非常新的 UndoBench 后再裁决。依据真实残差调整顺序，不因“热”而忽略基线。
<!-- End of preserved historical segment. -->
