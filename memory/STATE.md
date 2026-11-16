# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；从实际反馈学习纠正与保持，保留已有修复。主假设是恢复前后状态都使用执行反例；动作对齐是共同控制。
- **研究阶段**：同64题修复集合1→2→3→5严格包含，收益被误改抵消；已将原TRAIN反例绑定恢复前后状态，保留147条解释。三臂训练已启动，效果待回执；不扩本版投影。[现役执行](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#paired-state-negatives-v1)。
- **实际运行 / 预算**：FinQA累计3,952POST/16,943,529已知＋7未知预留229,376；本批另528更新/882显式前向/162额外梯度求值。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[成本](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。训练与HTTP分账。
- **下一交付**：等待普通、单侧与成对反例训练完成，继而同64现场做192原生复查。PLAN cd5c15b2/35a09272，每臂264更新/441前向/43,455监督tokens为计划数；70项/44子检查过、2跳过。若有净收益补匹配半权重消融，53仍保留。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：旧包保留，新准备2cd7e67c双份逐文件核SHA。监督1666180/tick12562263、训练1666296/tick12562673，boot b4166d98；27B已卸载，训练载入8B时余96.1GiB。单权重/32GiB保护，完成/失败后恢复27B，保留其他对话及LoopB。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
