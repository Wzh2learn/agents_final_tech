# Current State

> 2026-11-08 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal active**：11-06用户恢复，控制面active。主攻经验/反馈学习与变化下技能适配，面向IJCNN和硕士论文。执行读[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，长期取舍读[研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)。
- **检查点**：[四组27B恢复](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_ADDITIONAL_SOURCES.md#student-failure-recovery)已闭合；下一批[8B F/O/R](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)12题/36槽输入已冻结，经C科学输入复核及GB10完整parser检查，尚未运行。look6与clean6分报，优越性裁决前须补同面板普通历史。[代码纠正](../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#current)已闭合。
- **方法状态**：候选是在保留实际进度时，学习旧经验的保留、撤回或上下文重建；先测强固定策略与多任务选择空间，独立方法尚未成立。完整次序只在短计划维护。
- **Paper E**：用户已发老师审阅，等待反馈。现役[ICINT 四页稿](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)，ICDAR 顺序备投；尚未正式投稿。学校要求本人一作、北邮第一单位、方向相关，会议须召开并宣读/张贴。作者信息已私有准备；不在公开记忆复制。硕士按 2027 年 10 月送审倒排。
- **搜索**：科研联网默认使用当前 Codex 宿主原生搜索；无自动 DeepSeek/Qwen 搜索回退。GB10 禁网实验由 D 提供带来源材料，不假造宿主搜索的 HTTP API。搜索切换不改变推理模型或业务 RAG。
- **执行面**：D 主责，A/C 仅按需承担隔离实现或固定快照复核；已接入的ContextBench runner有自动记录，覆盖以具体批次为准，不等于全局调度或跨机器预算锁。架构见[Graph Loop](../docs/17_Graph_Engineering_多层Loop设计.md)。
- **同步与证据**：SSH已恢复，三端main已重新对齐，以最后实测HEAD/status为准；GB10仅Loop B日志有修改，未覆盖。已核旧8B恢复身份匹配、共享35B/27B未变、科研锁空闲。只留main和18个归档标签，7棵历史worktree保留。私有raw、340-token差额和未知用量不改，Git同步不等于部署。

较长的旧状态已移入[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)；它是历史，不作为现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
