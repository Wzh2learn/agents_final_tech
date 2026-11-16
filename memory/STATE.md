# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；成对反例v1确认闭合，继续从实际恢复与死因改进训练规则；动作对齐为共同控制。
- **研究阶段**：开发64成对37/普通33；确认53成对30/普通30/均衡25，共同首轮30。DeepSeek35、修10/误改5。主比较持平，已有修复与保持部件继续保留。[确认与尸检](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#remaining53-confirmation-v1)。
- **实际运行 / 预算**：FinQA本地4,664POST/19,738,584已知＋9未知预留294,912；TAT另228POST/824,488＋2未知65,536。校内5,261POST/52,037,133已知＋10未知2,621,440，合54,658,573/10亿。六臂训练完成账1,584更新/2,646前向/260,730监督tokens；新双臂运行中，不将预计量记实耗。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：同121组/195目标普通SFT已完成363更新、成对训练中；随后固定64 DEV共128题次。TRAIN尸检36/398反例点有正确续写，已备见证移除/等数量随机对照，未训练或排队；先收本批。原53不回流，TAT语法迁移另查。[规则](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_METHOD.md#prefix-witness-controls-v1)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：监督2143213/tick16007434、训练2143322/tick16007840、CPU2146003/tick16034739；boot b4166d98、32GiB保护。实跑≥431更新/697前向，普通臂363已完成。STUDY96c68bce、DATA bc05abf4；准备e6f6c622及形成becd8185双份。前缀CPU准备cd430187双份9文件；教师已退出，其他WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
