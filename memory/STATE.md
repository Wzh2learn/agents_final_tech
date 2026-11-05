# Current State

> 2026-11-06 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal active**：用户已恢复第二阶段。主攻 Agent 从执行与反馈形成经验、在变化任务中选择与修订技能；面向 IJCNN 和硕士论文。长期方向见[研究组合](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)，当前执行只读[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **当前检查点**：隔离actor依赖修正已通过容器/控制复验。Matplotlib新source已完成，待形成经验并跑target四臂；按[当前批次](../research/agent_frontier_portfolio_20261029/results/MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)接续。Astropy旧四臂因wheel可读未来修复已降级，原数值与成本保留，不混入新比较。
- **方法状态**：已有多来源开发轨迹和失败分析；尚无跨来源稳定方法增量。RethinkSkill 原生摘要接入可生成合法提案，但该次实际只改末尾换行。来源、接口和历史结论通过短计划按需加载。
- **Paper E**：用户已发老师审阅，等待反馈。现役[ICINT 四页稿](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)，ICDAR 顺序备投；尚未正式投稿。学校要求本人一作、北邮第一单位、方向相关，会议须召开并宣读/张贴。作者信息已私有准备；不在公开记忆复制。硕士按 2027 年 10 月送审倒排。
- **搜索**：科研联网默认使用当前 Codex 宿主原生搜索；无自动 DeepSeek/Qwen 搜索回退。GB10 禁网实验由 D 提供带来源材料，不假造宿主搜索的 HTTP API。搜索切换不改变推理模型或业务 RAG。
- **执行面**：D 主责，A/C 仅按需承担隔离实现或固定快照复核；ContextBench 五类 runner 已有自动记录，但不等于全局调度或跨机器预算锁。架构见[Graph Loop](../docs/17_Graph_Engineering_多层Loop设计.md)。
- **同步与证据**：本机、GitHub、GB10 以实测 HEAD/status 为准，Git 同步不等于部署。GB10 私有 raw 和历史账本保留；Loop B 日志可能变化，不回滚。历史 340-token 差额及未知用量继续分账。7 个含独有忽略产物的历史 worktree 保留。

较长的旧状态已移入[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)；它是历史，不作为现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
