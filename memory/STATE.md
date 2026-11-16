# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：可用27B路由仍 **36/64：恢复3、错改0、18调用**，同预算错误风险/固定随机也36。角色选择器三版DEV均33；新DeepSeek路由33/64、21调用、0恢复/0错改。8B强制非KEEP探针TRAIN32恢复0/错改9，停止这些版本。两教师同TRAIN各恢复7，合并覆盖11个不同现场，继续提炼这些成功补丁。[结果](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#campus-value-pilot)。
- **实际运行 / 预算**：本地FinQA5,429POST/22,911,630＋11未知360,448；校内5,510POST/53,214,738＋11未知2,883,584，合56,098,322/10亿。新增校内117POST/536,198，强制提案本地32POST/120,411，均无新增未知。角色头13,248、校内路由头1,000次CPU更新另计，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：将修复提案学习与KEEP/采纳学习分开：用真实成功补丁及错误子集训练提案器，另用恢复/错改效用学习采纳，保留原Actor与121组回放。不再靠强制解码或小选择器扫门槛；下一轮须实现/训练并原生出分。仅候选单臂，DEV监督与新64不入训练。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：角色三版、campus_v2及forced_v1均RETURNED，不重启。8B已卸载，27B守护3280515已恢复，8006健康200、可用74.4GiB、保留32GiB保护（1次GET，非推理）。原始证据留GB10，不混Paper E/开题/旧Goal WIP。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
