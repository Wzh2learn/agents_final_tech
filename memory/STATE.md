# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：独立提案/采纳候选已开训：31来源66个验证修复目标＋121回放，计划456更新/783前向，随后自动TRAIN96→采纳学习→DEV64。旧有效路由36/64保留；旧强制探针另发现425token工具前缀错配，新候选已统一输入整理。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#proposal-acceptance-v1)。
- **实际运行 / 预算**：本地FinQA5,429POST/22,911,630＋11未知360,448；校内5,510POST/53,214,738＋11未知2,883,584，合56,098,322/10亿。新增校内117POST/536,198，强制提案本地32POST/120,411，均无新增未知。角色头13,248、校内路由头1,000次CPU更新另计，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：跟进现有训练句柄，不重启；完成后跑真实提案和采纳出分。采纳校准含固定KEEP/全采纳两端，仅用TRAIN；当前旧父进程在ACCEPTANCE_TRAIN生成后需执行calibrate补全采纳选项，再做最终决策。DEV监督与新64隔离。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：proposal_acceptance_v1父3309591/20464326、训练子3309762/20464933已核存活。27B按单GPU规则卸载，当前8B训练，可用91.4GiB、保留32GiB保护；父流程结束恢复27B。旧批次均RETURNED，不重启，不混其他对话WIP。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
