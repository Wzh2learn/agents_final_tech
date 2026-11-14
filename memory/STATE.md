# Current State

> 2026-11-15 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；三组训练及4报告复查已闭合，字段加权未增加正确题。DeepSeek同题无参考3/4，8B首轮1/4；下一验证纠正—收尾的成对监督。
- **研究阶段**：优先深化恢复训练8/12对普通6/12、适配器平均及有效片段；[机制知识K01—K12](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)关联正向/局部/死因。当前没有已验证的金融领域新方法。
- **实际运行 / 预算**：FinQA本地261POST/1,164,822已知tokens＋1未知（预留32,768）；本轮96更新与旧88中断分账。校内累计5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)。运维另账。
- **下一交付**：11条真实恢复已编译22条纠正/收尾样本；比较同数据/初始化/更新预算的token平均与决策阶段平均。先做4旧报告开发回归，再扩独立报告；不把正常收尾与答案正确混成一个指标。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：GB10评估已返回；Docker/PG/OpenCode在线，27B按用户要求恢复，35B卸载。权重互斥/32GiB守护；下轮训练须先卸载27B。研究代码待汇总后同步；其他对话WIP、LoopB及历史worktree保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
