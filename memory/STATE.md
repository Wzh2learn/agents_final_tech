# Current State

> 2026-11-15 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；旧首分叉仍有额外语义修复，终止前移有正确保持。最新收尾重写/条件投影两臂均4/32，已停止这版；回到原有效监督，只改状态输入。
- **研究阶段**：原目标统一状态学习v2训练中，随后三模型同提示比较。新64TRAIN源20成功、44失败；教师续做已准备并排队，见[现役实验](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#state-view-v2)。
- **实际运行 / 预算**：FinQA累计2,755POST/11,778,831已知＋7未知（229,376预留）；新源143POST/550,040、未知0。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[总账](../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#成本与证据定位)；训练/运维另账。
- **下一交付**：v2计划合192更新/322前向及96原生执行。之后复用恢复的27B续做44个TRAIN失败，另保留20成功现场；各方案共享新数据。教师上限528POST/4M本地tokens，校内0，尚未调用。TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：v2启动代码c8c472d8；监督1035837/tick7966848，教师等待1048806/tick8081010，boot b4166d98。当前单权重/32GiB保护，教师不并发加载。新源e5358889、v2准备c69ea8a2及教师准备4a529ade均双份；其他对话/LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
