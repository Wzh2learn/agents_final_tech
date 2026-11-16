# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；从实际反馈学习纠正与保持，保留已有修复。主假设是恢复前后状态都使用执行反例；动作对齐是共同控制。
- **研究阶段**：恢复前后执行反例三臂训练已完成，正在同64现场做192次原生复查。成功状态反例损失初始偏低，需用半权重消融识别保持项作用；不扩本版投影。[现役执行](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#paired-state-negatives-v1)。
- **实际运行 / 预算**：已闭合FinQA仍3,952POST/16,943,529已知＋7未知预留229,376，新原生运行中待对账。新训练实耗792更新/1,323前向/130,365监督tokens，旧训练另存。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[成本](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：完成192原生复查和逐请求对账，按修复/误改/总成本比较。匹配半权重对照仅CPU准备（PLAN b972842d/082ed431），未训练；主批返回后按机制证据决定执行。53确认仍保留，70项/44子检查过、2跳过。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：准备2cd7e67c双份，训练RESULT 2ebc0463已闭合。监督1666180/tick12562263、原生1718101/tick13191386，boot b4166d98；训练1666296已退出，27B暂停。CPU后处理1675046/tick12655963待完成后复算归包。单权重/32GiB保护及自动恢复，保留其他对话及LoopB。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
