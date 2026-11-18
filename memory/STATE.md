# Current State

> 2026-11-18 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active。四状态完整反馈与仅静态程序两臂在GB10串行验证。训练视图252条，旧N的171条分成双对79、双错92；另恢复68、错改13。仅用固定DEV64、前向57和既有教师回执，封存确认64隔离。
- **研究阶段**：确认64：首轮/普通34、旧成对39；主18接管效用42、风险43、单状态/随机41。效用相对普通8胜0负，相对风险1胜2负；多状态仍有局部收益，不能把风险43替换成主方法。DEV41与新57的35保留。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#confirmation64-v1)。
- **实际运行 / 预算**：FinQA本地6,310POST/26,149,988＋76未知2,490,368；TAT累计508POST/1,844,964＋2未知65,536。校内6,216POST/56,362,677＋11未知2,883,584，合59,246,261/10亿。本轮两臂只在GB10训练和读出，完成后按实际更新/前向结算。[账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：报两臂条件恢复AUC与固定预算结果，再用旧TAT主9的分流诊断冻结新48题协议。[英文正文v1](../research/agent_frontier_portfolio_20261029/IJCNN_MANUSCRIPT.md)和[总表](../research/agent_frontier_portfolio_20261029/results/IJCNN_EXPERIMENT_TABLES.md)保留原主结果。[计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：GB10串行训练由1015746管理，四状态回执位于已有证据根的acquisition_four_state_v1，独占GPU并保留32GiB余量。27B服务在训练后恢复。TAT48已完成公开样本准备，披露规则待冻结。短回执同步本机，raw留GB10，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
