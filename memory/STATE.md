# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；从实际反馈学习纠正与保持。成对执行反例出现开发收益，继续识别其独立机制；动作对齐是共同控制。
- **研究阶段**：同64现场普通33、单侧29、成对37、半权重32；成对保留原33、修4、误改0，相对减权5胜0负。53确认未启用。[结果](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#paired-state-negatives-v1)。
- **实际运行 / 预算**：FinQA本地4,208POST/17,942,361已知＋9未知预留294,912；四臂训练1,056更新/1,764前向/173,820监督tokens另账。校内新增同64对照111POST/493,462，累计5,133POST/51,435,878已知＋2,621,440预留，合54,057,318/10亿。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：补相同147正目标、每状态等权SFT强基线；确认前统一比例输出说明。DeepSeek同64为38、修11/误改6，6例均输出尺度，不能据此称教师语义退化；DEV不回流TRAIN，53未启用。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：主结果f5a60b1b、减权1f87ea50、TRAIN教师642792ef、同64教师d509b63b均双份逐文件核SHA。训练/原生/CPU/校内对照均已退出；27B由1799521/tick13692020恢复ready，boot b4166d98、32GiB保护。保留其他WIP。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
