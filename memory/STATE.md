# Current State

> 2026-11-09 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal active**：11-06用户恢复，控制面已核。主攻经验/反馈学习与变化适配，面向IJCNN及硕士论文；执行与证据路由见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **当前执行**：[五种基线](../research/agent_frontier_portfolio_20261029/results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)已闭合。B-only六槽已释放，PID2438702/birth1090530234在GB10执行；最多768 POST，仅补缺格，不训练。旧H18进程已退出，禁止重启。
- **方法状态**：R是已有纠正学习基线；联合选择/主动采集亦有近邻。先识别反馈与经验组合的作用，再设计保留外部进度的修订机制，算法尚未定；路线见[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **Paper E**：用户已发老师，等反馈；[ICINT四页稿](../research/paper_e_publication_route_20261028/icint_latex/main.pdf)为现役，ICDAR顺序备投，尚未投稿。学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。作者私有字段不入公开记忆。学位按2027年10月倒排。
- **搜索**：默认宿主原生搜索，无DeepSeek/Qwen自动回退；GB10禁网实验由D提供带来源材料，不假造搜索HTTP接口。推理模型与业务RAG不因此切换。
- **协作**：D主责，A/C按需隔离实现或固定快照复核，优先续用已有Agent。自动记录范围以runner为准，全局调度及跨机预算锁未实现；见[架构](../docs/17_Graph_Engineering_多层Loop设计.md)。
- **Git与运行面**：三端仅main，18个归档标签及7棵历史树提交已集成；以HEAD/status实测。GB10 Loop B日志保留。B6占用自有18104 BF16窗口，结束须恢复Q4/释放锁；共享35B/27B不变。私有raw、340-token差额及未知用量保留。

较长的旧状态已移入[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)；它是历史，不作为现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
