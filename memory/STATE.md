# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；从实际反馈学习纠正与保持。成对执行反例出现开发收益，继续识别其独立机制；动作对齐是共同控制。
- **研究阶段**：同64现场完整复核：普通33、单侧29、成对37；成对保留原33、修4、误改0，14次改写全在原错题。正在训练匹配半权重消融；53确认未启用。[结果](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#paired-state-negatives-v1)。
- **实际运行 / 预算**：FinQA本地已闭合4,144POST/17,694,799已知＋8未知预留262,144；新三臂792更新/1,323前向/130,365监督tokens另账。DeepSeek新教师17POST/77,333已知，校内累计5,022POST/50,942,416已知＋2,621,440预留。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：半权重同设消融b972842d/082ed431已启动，264更新＋64原生；区分成功状态反例与单纯减权。DeepSeek8个TRAIN盲续做已3/8成功，独立经验不并入当前训练；70项/44子检查过、2跳过。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：主结果f5a60b1b、半权重准备969bd12f、教师642792ef均双份核SHA。旧主批/教师进程已退出。当前监督1764074/tick13407255、训练1764190/tick13407664、CPU1765410/tick13417374，boot b4166d98；27B暂停，单权重/32GiB保护及结束恢复，保留其他WIP。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
