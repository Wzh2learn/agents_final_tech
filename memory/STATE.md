# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：效用与同模型风险均原生DEV41/64，旧37之上4语义恢复/0错改；共同教师池再现两组41。12接管效用40/风险39，保留低预算局部信号。当前单状态重复对照，同教师/来源/训练计算量，识别状态经验多样性，不再调分类门槛。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#shared-teacher-value-v1)。
- **实际运行 / 预算**：本地FinQA5,686POST/23,910,452＋12未知393,216；校内5,740POST/54,293,925＋11未知2,883,584，合57,177,509/10亿。风险新8校内POST/32,856，未知0；GPU434更新/894前向完成，HF另64前向/91,581tokens。14复用响应保留部署成本，不重复充账；单状态训练在途，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：跟进acquisition_single_state_v1父5022/子5132，不重启。单一cheap状态按原组大小重复，同96教师/121回放/434更新/894前向；完成后自动预测、恢复27B，再evaluate --variant single及matched --variant single，重合教师复用，缺失分支新增。Key仅进程内，新64隔离。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：效用/风险均闭合，权重与短回执已同步本机。当前单状态父5022/22545119、子5132/22545327，单8B权重、32GiB保护，结束后恢复27B。代码/短状态本批同步，raw/数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
