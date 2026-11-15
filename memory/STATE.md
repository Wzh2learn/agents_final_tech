# Current State

> 2026-11-15 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；全负方向14/32对普通11/32；终止前移14/32、保持13/13。首决策系数对齐11/32未增益，停止此版本，保留两块正向。
- **研究阶段**：3参照及首决策规则训练/32执行已闭合；后者增加工具激活但保持9/13。先检验学习到的局部偏好能否筛选修正，见[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#initial-decision-v1)。
- **实际运行 / 预算**：FinQA闭合1,684POST/7,393,929已知＋2未知（65,536预留）。校内5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)；运维55,809另账。
- **下一交付**：复用32现场及已执行候选，固定零阈值比较局部偏好的训练增量与原始/整段置信；先离线小试，不新采教师、不扫权重。未执行；64确认报告仍封存。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：候选批次615892已结束，27B由守护633899恢复且GET核实就绪，32GiB保护；新试验未启动。已完成证据双份，其他对话/LoopB保留，按本批同步三端。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
