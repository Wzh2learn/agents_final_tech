# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；成对反例v1确认闭合，继续从实际恢复与死因改进训练规则；动作对齐为共同控制。
- **研究阶段**：开发64成对37/普通33；确认53成对30/普通30/均衡25，共同首轮30。DeepSeek35、修10/误改5。主比较持平，已有修复与保持部件继续保留。[确认与尸检](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#remaining53-confirmation-v1)。
- **实际运行 / 预算**：已结算FinQA本地4,536POST/19,243,406已知＋9未知预留294,912；当前六臂训练1,584更新/2,646显式前向/260,730监督tokens另账，新原生费待结算。校内累计5,225POST/51,855,529已知＋2,621,440预留，合54,476,969/10亿。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：源覆盖训练127aa32d完成、权重f96a0d34，正在做64 DEV；147正目标不变，两状态各补9分叉。TAT的32组/128题次已冻结e3d5d7af，排队接续并用官方EM/F1评分，准备包61421fdd双份212文件；不回流确认轨迹训练。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：源覆盖监督2008693/tick15063173、原生2029562/tick15279198、CPU2011926/tick15089249；TAT排队2025906/tick15237494、CPU2031138/tick15284709。boot b4166d98、32GiB保护，单模型顺序运行；源覆盖准备fa4f964e双份。旧证据及其他WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
