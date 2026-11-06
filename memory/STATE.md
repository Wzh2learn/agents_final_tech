# Current State

> 2026-11-07 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal active**：2026-11-06用户已明确继续，且Goal控制面恢复active。主攻 Agent 从执行与反馈形成经验、在变化任务中选择与修订技能；面向 IJCNN 和硕士论文。长期方向见[研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，当前执行只读[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **当前检查点**：16新布局两种执行基线已返回；同7组有限SFT在途，owned8B暂交训练窗口管理。只读[现役纠正记录](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_CORRECTION_DATA.md)；旧raw/失败和共享服务保留。
- **方法状态**：候选是在保留实际进度时，学习旧经验的保留、撤回或上下文重建；先测强固定策略与多任务选择空间，独立方法尚未成立。完整次序只在短计划维护。
- **Paper E**：用户已发老师审阅，等待反馈。现役[ICINT 四页稿](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)，ICDAR 顺序备投；尚未正式投稿。学校要求本人一作、北邮第一单位、方向相关，会议须召开并宣读/张贴。作者信息已私有准备；不在公开记忆复制。硕士按 2027 年 10 月送审倒排。
- **搜索**：科研联网默认使用当前 Codex 宿主原生搜索；无自动 DeepSeek/Qwen 搜索回退。GB10 禁网实验由 D 提供带来源材料，不假造宿主搜索的 HTTP API。搜索切换不改变推理模型或业务 RAG。
- **执行面**：D 主责，A/C 仅按需承担隔离实现或固定快照复核；已接入的ContextBench runner有自动记录，覆盖以具体批次为准，不等于全局调度或跨机器预算锁。架构见[Graph Loop](../docs/17_Graph_Engineering_多层Loop设计.md)。
- **同步与证据**：本机、GitHub、GB10 以实测 HEAD/status 为准，Git 同步不等于部署。GB10 私有 raw 和历史账本保留；Loop B 日志可能变化，不回滚。历史 340-token 差额及未知用量继续分账。7 个含独有忽略产物的历史 worktree 保留。

较长的旧状态已移入[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)；它是历史，不作为现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
