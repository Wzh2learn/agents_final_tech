> 历史快照归位于 2026-11-06。原文件 `research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md` 的连续片段；旧任务、结果与预算保持当时口径，不能作为当前授权。现状见[第二阶段计划](../../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

# Agent 研究方向前瞻与论文候选（2026-10-29）

状态：文献初筛及开发性模型、真实工具 Agent 探针；不是系统综述、已确认创新或独立确认。目标是为学术硕士寻找可验证方法和可发表论文，金融文档不是限制，现有工程系统主要提供执行与评测基础设施。外部论文是否已正式接收只按对应来源说明，arXiv 论文按预印本处理；不能宣称未核查的研究空白。

2026-10-31：[PDF/Excel 跨任务探索](../../../research/agent_frontier_portfolio_20261029/PDF_EXCEL_TRANSFER_RETURN_20261031.md)完成三条真实工具 Agent 和事后简单对照。带经验组原检查 11/11，无经验组 7/11；无经验组已有正确的 15/15 删除与 20/20 修改，展平其嵌套输出后也为 11/11，且与带经验组结果相同。无模型的公开输入确定性基线也通过。该单实例支持分离事实与输出合同，不证明经验学习有因果收益；下一步仍是不同来源、多任务族的经验适用与反馈更新。

同日新增 [SkillLearnBench 来源与反馈合同发现](../../../research/agent_frontier_portfolio_20261029/FINANCIAL_FEEDBACK_CONTRACT_FINDING_20261031.md)：六个公开金融任务的 solution 存在相邻股票类别字符串拼接；在两个已暴露任务上，代码运行时计数与参考一致，而分开字符串的反事实会被原 pytest 拒绝。后者不是独立财务 gold，也没有进行 Agent 学习实验。它提供了“可执行任务规则与评价反馈冲突时如何学习”的候选场景，需同简易规则和普通历史比较。

进一步完成 [6 条真实 Agent 的反馈冲突探针](../../../research/agent_frontier_portfolio_20261029/FEEDBACK_CONFLICT_AGENT_PILOT_RETURN_20261031.md)：源任务产生真实冲突反馈，五条目标条件与无模型确定性基线均正确；目标轨迹中未观察到显式复核旧冲突的标记。这是一个简单、已暴露来源上的上下文比较，没有持久技能更新或可识别方法收益。

[企业检索任务反馈资格](../../../research/agent_frontier_portfolio_20261029/ENTERPRISE_FEEDBACK_QUALIFICATION_20261031.md)进一步用实际 pytest 正反控制验证了漏题、额外无关项和负数 token 通过原检查器的情况。它为有反馈但任务完成度不足的技能学习开发提供材料；仍需独立 q2 语义参考以及跨来源确认，不能把该检查器分数当最终 gold。

[依赖审计条件变化](../../../research/agent_frontier_portfolio_20261029/DEPENDENCY_SCOPE_SHIFT_QUALIFICATION_20261031.md)提供另一条更直接的开发序列：同一真实依赖文件在三个不同风险筛选条件下有不同发布参考，交叉套用不通过。原测试有同包多漏洞被覆盖的盲区；此资格阶段未运行 Agent，后续运行见下段。

后续[两次真实 Agent 开发试验](../../../research/agent_frontier_portfolio_20261029/DEPENDENCY_SCOPE_REPEAT_RETURN_20261031.md)已恢复离线环境并从实际失败反馈生成 skill：生成经验组两次交付三个目标身份，其他组被有限额度阻断；两次成功输出都伴随改写数据库副本时间。该现象提供经验可用性与可信性的具体研究机会，但仍属同源开发观察，原测试分别 8/8 与 7/8，需在更公平额度和新工作流上继续。

同日[统一扩大预算的事后复测](../../../research/agent_frontier_portfolio_20261029/DEPENDENCY_SCOPE_BUDGET_SENSITIVITY_RETURN_20261031.md)中，普通历史也交付 3/3 目标身份并通过原检查 8/8；生成 skill 为 3/3 与 7/8。两组都改写工作副本的数据库时间。旧的两个受限运行不能证明生成 skill 相对普通历史有独特收益，也不能把这次单例差异简单归因于预算。下一步围绕经验可信性、真实迁移和其他工作流寻找可区分的机制。

2026-11-01 的[两个公开项目迁移开发试验](../../../research/agent_frontier_portfolio_20261029/DEPENDENCY_CROSS_PROJECT_RETURN_20261101.md)显示：四记录项目中普通历史与生成 skill 都找全身份和指定来源分数，前者未发现留存的时间改写，后者改写了副本；空记录项目中生成 skill 虽输出正确空结果，轨迹使用了不适用于一般新任务的严重程度筛选。同任务的确定性工具规则也完成了筛选。当前应研究从经验中验证和修订有风险的局部建议，而非据此声称生成 skill 方法成立；更广泛的 Agent 经验、反馈、记忆与技能适配方向继续保留。

随后[来源见证及人工局部修订试验](../../../research/agent_frontier_portfolio_20261029/SKILL_VERIFICATION_RETURN_20261101.md)在两个已暴露项目上保留快照相对输出，并未发现留存的时间篡改副本；但空结果项目仍使用了旧严重程度过滤。该手工对照说明一个经验前提得到修订不代表其他前提已被验证，不是自动方法或泛化结论。下一步转向不同工作流、跨来源和同信息强基线，而不持续针对这份 skill 调参。

另完成[科研计算工作流资格](../../../research/agent_frontier_portfolio_20261029/DBSCAN_METRIC_SHIFT_QUALIFICATION_20261101.md)：固定参数改变聚类距离后，218/369 个图像的簇划分变化。两份发布参考在替代环境完成完整 Pareto 搜索并通过各自的 8 项自带测试；对 task 1 的事后白盒控制还发现测试可接受一个额外矛盾行。2026-11-02 的[后续真实 Agent 试验](../../../research/agent_frontier_portfolio_20261029/DBSCAN_AGENT_PILOT_RETURN_20261102.md)中，无历史、真实源历史与透明规则均完成目标任务；两任务共享数据及测试代码，不是方法收益或独立 benchmark 确认。

2026-10-30 补充：[跨任务经验迁移与元件匹配尸检](../../../research/agent_frontier_portfolio_20261029/CROSS_TASK_TRANSFER_RETURN_20261030.md)已运行三个真实制造任务 Agent 和四个无模型代码控制。观察到标识符切分、大小写及类别语义共同影响结果；原任务检查和单次轨迹不足以确认迁移收益。当前可复用的是带成本的轨迹与任务设计约束，不是已成立的方法。

后续工作、训练可选条件、强基线和 IJCNN 倒排见 [实验执行路线](../../../research/agent_frontier_portfolio_20261029/IJCNN_EXPERIMENT_PROGRAM_20261030.md)。

2026-10-30 新增 [IJCNN 近邻核查与下一实验候选](../../../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)，包括 Skill-V、SkillShift-Bench、SkillEvolBench、RSE-Bench、CFOE 和 SEAL 等：技能合同、环境适配、反馈噪声、非回归及从失败迁移均已有直接先例，须进一步全文比较和复现相应强基线。

## 2026-10-30：真实工具 Agent 的技能与执行预算探针

**后续接续**：[真实 dialogue-parser 反馈与验证器研究](../../../research/agent_frontier_portfolio_20261029/DIALOGUE_PILOT_RETURN_20261030.md)在新的任务上运行了 8 次 Agent episode。发现一次同起点修复中的真实文件权限阻断，并修复后重新执行；也发现原 verifier 可对缺少解析器的构造控制给出 35/35，以及对可达的 End 终点产生误拒。具体反馈与 neutral 两组在单案例中均通过新增解析烟测，原测试分别为 34/35 与 29/35，其中部分测试对图结构表示有争议。记录为候选问题和测量约束，不将它包装成反馈方法已成立。

**第二任务接续**：[prefix-cache 反馈修复](../../../research/agent_frontier_portfolio_20261029/PREFIX_FEEDBACK_RETURN_20261030.md)中，现成任务技能在同起点上通过 10/10 且在上游参考下 2,000 行一致；中性重试及可见合同诊断未达到该基线，诊断扩容后为 5/10。技能包含完整策略知识，不与短反馈视为信息等量；重复执行与 2,000 行复核均已实际运行。下一轮应研究新任务族上的知识/反馈选择与可靠迁移，而不把同任务手工 skill 的有效性当作新方法。

在 SkillsBench 开发任务 `tictoc-unnecessary-abort-detection` 上，将 OpenCode 与 GB10 本地 Qwen 组成可执行工具 Agent；相同任务分别提供 no-skill 和全部三份任务 skill。Docker 无网络、任务 verifier 不在 Agent 容器中；运行结束后在隔离环境执行原验证器。这里只是一个公开任务的开发探索，没有独立任务族、重复试验、source-isolated 测试，也没有经验学习或反馈更新。

首次各运行一次时本地模型传输超时，两个条件都未交付；[no-skill 原回执](../../../research/agent_frontier_portfolio_20261029/tictoc_timeout_no_skill_receipt_20261030.json)和 [all-skill 原回执](../../../research/agent_frontier_portfolio_20261029/tictoc_timeout_all_skill_receipt_20261030.json)分别有 4 和 2 个物理 POST。第二轮仅将服务及回合超时上限从 120/300 秒调整到 300/600 秒，其余请求上限等保持，使用 [可复现适配脚本](../../../research/agent_frontier_portfolio_20261029/run_tictoc_extended.py)，不是重写第一轮。

| 第二轮条件 | Agent | 独立输出验证 | 模型物理 POST | 墙时 |
|---|---|---|---:|---:|
| [no-skill](../../../research/agent_frontier_portfolio_20261029/tictoc_extended_no_skill_receipt_20261030.json) | 退出码 0，生成文件 | 3 项格式测试通过；任务语义评分 **0.05/1** | 5 | 125.3 秒 |
| [all-skill](../../../research/agent_frontier_portfolio_20261029/tictoc_extended_all_skill_receipt_20261030.json) | 触及 8 POST 上限，退出码 1，无输出文件 | 3 项格式测试失败；无可评价语义答案 | 8 | 227.2 秒 |

第二轮的已完成步骤分别报告 37,407 和 87,495 tokens（包含各自报告的缓存输入，不可重复相加）；原始实验日志保存在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/agent_tictoc_extended/`，首次实验日志保存在 `/home/testuser/wzh/research_evidence/agent_skill_method_20261029/`。首次超时请求的未返回 usage 为 UNKNOWN；本地 Qwen 直接模型反馈探针另有 9 次、8,818 reported tokens，不与此混为同一种调用。没有训练、付费 API 或生产 Memory 写回。

**可行动研究假设**：当经验或技能增加 Agent 上下文与推理步骤时，额外信息的潜在收益可能被执行预算、输出长度或错误反馈抵消。这个单任务结果不能区分技能内容、提示长度、工具使用与上限等因素；不能说 skill 导致性能下降。后续应在多个可执行任务上比较 no-skill、完整 skill、等长度无效文本、简短摘录和基于可见反馈的选择或修订，匹配输入及总预算并报告任务成功、合法输出、调用数、缓存、墙时；同时引入普通重试与随机选择。先做开发和运行合同校验，再使用未见来源/任务族开展独立确认，复查 SkillLearnBench、SkillsBench 及近邻文献是否已覆盖候选机制。

## 2026-10-30：IJCNN 目标及首次连续反馈开发运行

**目标**：第二篇独立研究以 [IJCNN 2027](https://ijcnn.org/2027/) 为目标，regular 截止 2027-01-31，通知 03-15，会议 06-14–18；首篇与第二篇须有独立问题、数据和贡献。IJCNN 主题涵盖基础模型、参数高效适配、持续学习、Agentic AI；一般免费篇幅 6 页，费用及超过 6 页的条件按当时 [官方作者须知](https://ijcnn.org/2027/authors/initial-author-instructions)核验。该方向仍为研究假设，不伪装为已成立方法。

**倒排**：2026-11-06 前打通真实任务可见反馈、输出合同和强基线；11 月中下旬对已筛选家族运行重复开发，对照模型历史、简单 ICL、检索、skill 和工具反馈；12 月上旬确定方法或转向另一候选，完成公开近邻复现与消融；12 月下旬至 2027 年 1 月进行来源隔离确认、多个种子和成本核算；1 月中旬写完整 6 页稿、审阅与修订，1 月 31 日前确定是否具备可投稿证据。时间点是工作目标，任务数据与硬件决定实际规模，不以进度代替科研结果。

**已执行最小探针**：[脚本](../../../research/agent_frontier_portfolio_20261029/run_sequential_feedback_pilot.py)、[摘要](../../../research/agent_frontier_portfolio_20261029/sequential_feedback_pilot_summary_20261030.json)、[逐次账本](../../../research/agent_frontier_portfolio_20261029/sequential_feedback_pilot_ledger_20261030.json)。固定 ContinualSkillBench finance stream 中 FinQA 题 5/25/26；GB10 本地 Qwen3.6-35B-A3B-Q4_K_M，独立与历史+前序正确/错误反馈两臂，每臂 3 次，temperature 0，输出 cap 1024，无 retry。该探针为**直接单轮模型接口、不是工具 Agent 或官方 benchmark 运行**，任务与旧来源曝光，模型预训练曝光未知。每次独立 JSON 合同合规；按上游 numeric helper 计分两臂均为 `[1,0,0]`。第一题两臂输入本来相同；不能把 1/3 作为反馈方法有效或无效。

**发生判断变化的观察**：两条错判涉及百分数合同。题 25 问百分比，独立臂输出 `65.6%`，参考为比例 `0.65644`；题 26 独立臂输出 `5.62%`，参考为 `0.05624`。上游 helper 删除 `%` 而不将百分数换成比例，且容差不考虑显示舍入。将显式百分数解释为比例后，它们接近参考，但具体正确性需按题目和精度合同独立核验；历史臂输出无 `%` 的 `65.6` 与 `5.6`，不得自动断定单位。第二题的上游 `incorrect` 反馈被第三题历史臂看到，因此这是可能存在的反馈污染，不能用它评估可信纠正学习。保持 raw 与原判分不变，新评分另版本并先做正负例。

**事后确定性诊断**：[数值格式诊断器](../../../research/agent_frontier_portfolio_20261029/numeric_semantic_diagnostic.py)按明确百分号、比例、十进制末位舍入区间和符号做有界分析，单位不明确保留 unresolved；本地与 GB10 的三组正反例测试均通过。[固定 raw 重评](../../../research/agent_frontier_portfolio_20261029/sequential_feedback_posthoc_diagnostic_20261030.json)中独立臂 3 项都与该舍入约定相容，历史臂 1 项相容、2 项为缺少百分号的 unresolved。它是为理解旧输出的事后诊断，依赖选定的四舍五入与单位假设，并非事前冻结 gold 或独立人工裁决，不能作为方法胜负。

**反馈标签反事实探针**：对先前历史臂题 25 的固定回答，维持同一前题、回答和目标题 26，仅将合成反馈设为 `incorrect` / `uncertain` / `correct`，[脚本](../../../research/agent_frontier_portfolio_20261029/run_feedback_label_probe.py)在 GB10 分别执行 1 次，结果为 `5.69` / `5.7` / `5.7`（均无明确百分号）；[账本](../../../research/agent_frontier_portfolio_20261029/feedback_label_pilot_ledger_20261030.json)共 3 次、4,010 reported tokens、0 retry。该探针由前轮观察后提出，不是独立确认；其输入不包含第一题历史，与前轮历史臂不是相同上下文。它说明此固定输入下反馈标签可以伴随输出变化，但单个确定性任务不能判断反馈机制的泛化、行动收益或答案准确性。实验没有训练或 tool-agent 调用，raw 和请求保存在 `/home/testuser/wzh/research_evidence/agent_learning_20261030/feedback_label_development_20261030_v1/`。

**成本与来源**：实际 6 次 HTTP、0 retry、0 judge、0 训练、0 付费 API；返回 usage 总计 4,808 tokens（含已报告缓存输入，不重复相加）；full request/response 在 `/home/testuser/wzh/research_evidence/agent_learning_20261030/sequential_feedback_development_20261030_v1/`。本研究使用公开 benchmark 题目的请求和结果，不写生产 Memory。下一步先制定百分数、单位和舍入的冻结参考并重评固定 raw，随后使用可执行工具任务和 source-disjoint 面板开展真实 agent 对照；实验条件由实况迭代，不把本次错误归因于模型或完整基准。

<!-- End of preserved historical segment. -->
