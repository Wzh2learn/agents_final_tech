# Current State

> 2026-11-15 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；全负方向14/32对普通11/32；终止前移也14/32，保住13/13但少3个语义恢复。保留两块正向，研究纠正触发。
- **研究阶段**：终止位置192更新/322前向、64执行已核对，正确保持及请求减半有效，尚未超过语法门控回放；见[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#expanded-boundary-v1)。
- **实际运行 / 预算**：FinQA闭合1,624POST/7,140,661已知＋2未知（65,536预留）；新候选另记LIVE。校内5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)；运维55,809另账。
- **下一交付**：裸8B首轮0/32、给定源现场纠正13/32、盲27B首轮12/32已核；首决策系数对齐正在训练，同DATA/目标量、96更新/161前向，随后同32现场执行。64确认报告未启用。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：3参照完成，旧监督就绪超时保留；新监督615892/训练615989，读`initial_decision_v1/PIPELINE_LIVE.json`。27B已按权重锁卸载，批后恢复；32GiB守护，其他对话/LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
