# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；用户已恢复并授权Step1/2。主攻证据绑定的结构化程序修复，仅rebind_operand、scale_output、prepend_step、KEEP四算子；接管效用路由为强备选，封存首分叉微调线。轻量探索：单候选对缓存普通33，DEV64净增至少3题再补确认，不打包或逐文件核SHA。
- **研究阶段**：共享教师状态效用候选原生DEV41/64，较普通33净增8，较旧37恢复4/错改0，均为语义修复。共同旧教师池回放学习40/风险39/固定随机40；保留正向结果，当前只训练同8B同数据的风险对照。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#shared-teacher-value-v1)。
- **实际运行 / 预算**：本地FinQA5,686POST/23,910,452＋12未知393,216；校内5,732POST/54,261,069＋11未知2,883,584，合57,144,653/10亿。新原生DEV40校内POST/187,515，未知0；效用GPU434更新/894前向已完成，另64次HF效用前向和200次CPU对照更新，风险训练在途另记，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：跟进acquisition_risk_control_v1父4149876/子4149995，不重启。相同96来源252视图＋121回放，只学本地错误风险，完成后冻结18个接管任务，再运行evaluate --variant risk做原生对照。Key仅隐藏输入进程内，DEV监督与新64继续隔离。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：效用训练/预测/原生评测已结束，41模型权重及短回执同步本机。风险对照父4149876/22115166、子4149995/22115572已核存活；单8B权重、32GiB保护，结束后恢复27B。代码/短状态本批同步，raw/数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
