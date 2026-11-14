# Current State

> 2026-11-15 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；闭合监督解决循环，三组答案均1/4，调用约束无增量。当前验证执行错误分叉的负方向学习，与普通SFT/同位置正加权比较。
- **研究阶段**：优先深化恢复训练8/12对普通6/12、适配器平均及有效片段；[机制知识K01—K12](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)关联正向/局部/死因。当前没有已验证的金融领域新方法。
- **实际运行 / 预算**：FinQA已闭合本地285POST/1,261,784已知tokens＋1未知（预留32,768）；闭合三组96更新/192前向，旧88中断另账。校内累计5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)。运维另账。
- **下一交付**：同22行的普通SFT、同位置正加权与正负对比；新8报告公共首轮进行中，后全题复查。64更新/128前向已完成，上限384本地POST；看纠正、保持与完整成本。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：Docker/PG/OpenCode在线；监督PID216965运行，新批已卸载27B，权重互斥/32GiB守护。研究代码待本批同步；其他对话WIP、LoopB及历史worktree保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
