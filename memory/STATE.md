# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；方法固定为恢复前后成对执行反例学习，已有开发支持，进入独立确认；动作对齐为共同控制。
- **研究阶段**：同64五臂开发闭合，成对37、保留33、修4、误改0；原117组剩余53确认已启动，固定方法与普通/均衡SFT，先运行共同首轮。[确认](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#remaining53-confirmation-v1)。
- **实际运行 / 预算**：FinQA本地4,272POST/18,195,242已知＋9未知预留294,912；五臂训练1,320更新/2,205前向/217,275监督tokens另账。校内累计5,133POST/51,435,878已知＋2,621,440预留，合54,057,318/10亿。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：完成53组共同首轮及三组相同现场接续，共212题次；固定λ0.1/ρ0.5及权重017833f6，不再调参。TAT原生评分回调待接；提示/原生评分保持，尺度仅诊断，DEV不回流TRAIN。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：确认PLAN585bacac、准备包3b3bd59f双份284文件核SHA。监督1905735/tick14466100、首轮1905831/tick14466307，CPU后处理1913451/tick14507006；boot b4166d98、32GiB保护，27B已卸载供学生独占，批次费未结算。契约源及四安装fe0b894d；保留其他WIP。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
