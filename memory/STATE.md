# Current State

> 2026-11-08 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal active**：11-06用户恢复，控制面已核。主攻经验/反馈学习与变化适配，面向IJCNN及硕士论文；执行与证据路由见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **在途批次**：[8B F/O/R](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)新12题/36槽运行中。私有`trained_baseline_transfer_v1/OPERATOR_PROCESS_V1.json`绑定进程，`RUN_V1/STATE.json`查进度；禁止重复启动。look6/clean6分报；普通历史仅先备输入，当前窗口结束后执行。
- **方法状态**：研究保留实际进度时的经验保留、撤回与上下文重建。先核强固定策略和多任务选择空间，独立方法尚未成立；闭合结果按短计划链接读取。
- **Paper E**：用户已发老师，等反馈；[ICINT四页稿](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)为现役，ICDAR顺序备投，尚未投稿。学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。作者私有字段不入公开记忆。学位按2027年10月倒排。
- **搜索**：默认宿主原生搜索，无DeepSeek/Qwen自动回退；GB10禁网实验由D提供带来源材料，不假造搜索HTTP接口。推理模型与业务RAG不因此切换。
- **协作**：D主责，A/C按需隔离实现或固定快照复核，优先续用已有Agent。自动记录范围以runner为准，全局调度及跨机预算锁未实现；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。
- **Git与运行面**：三端仅main，18个归档标签及7棵历史树的提交均已集成；实际同步以HEAD/status为准。GB10 Loop B活动日志保留。当前科研锁独占18104，共同BF16替代原Q4，结束须恢复；共享35B/27B不动。私有raw、340-token差额和未知用量保留；Git一致不等于部署一致。

较长的旧状态已移入[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)；它是历史，不作为现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
