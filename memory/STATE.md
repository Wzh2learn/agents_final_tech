# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；成对反例v1确认闭合，继续从实际恢复与死因改进训练规则；动作对齐为共同控制。
- **研究阶段**：开发64成对37/普通33；确认53成对30/普通30/均衡25，共同首轮30。DeepSeek35、修10/误改5。主比较持平，已有修复与保持部件继续保留。[确认与尸检](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#remaining53-confirmation-v1)。
- **实际运行 / 预算**：已结算FinQA本地4,600POST/19,495,081已知＋9未知预留294,912；六臂训练1,584更新/2,646显式前向/260,730监督tokens另账。校内累计5,225POST/51,855,529已知＋2,621,440预留，合54,476,969/10亿；新教师最多48POST/100万tokens，未计为实耗。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：源覆盖31/64、修5误改7，低于旧成对37；保留互补修复16/28，停止本版系数扩展。TAT32组/128题次e3d5d7af运行中；DeepSeek补做4个尚未恢复TRAIN现场，fd969910已冻结并等待TAT释放。后续从未用TRAIN扩样，各方法共享新增监督。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：源覆盖全部退出，完整包339f8b81双份1203文件；TAT监督2025906/tick15237494、CPU2031138/tick15284709，当前源覆盖接续2067244。教师2074153/tick15528372等待TAT，凭证仅进程内。boot b4166d98、32GiB保护、单模型顺序运行；其他WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
