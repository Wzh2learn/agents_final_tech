# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；保留执行反例纠正的语义收益，聚焦降低额外误改。共用提交接口已接通，下一步检验保持状态约束的反例更新。
- **研究阶段**：新64报告256执行闭合，首轮33、普通纠正34、候选33、原模型复查29。候选多修1题也多错改2题；保留局部语义收益，下一步比较减弱反例项与保持投影。旧42/接口结果不覆盖。[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#test-execution-v1)。
- **实际运行 / 预算**：FinQA累计3,824POST/16,441,365已知＋7未知预留229,376；本批325/1,272,436、未知0。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[成本](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。训练/CPU回放另账，无在途实验。
- **下一交付**：训练接入65项/34子检查通过、2跳过；两臂88组/147正目标已冻结：固定λ=0.05，λ=0.1加保持投影。训练d0e64479、后续128开发执行7e7d3c97待启，不加教师或扫系数；余53组未启用，TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：新结果52a32ff1及两臂准备5b63c079双份；训练接入、测试和文档随本轮提交。27B守护1456281/tick10948506、boot b4166d98已ready，开训前核身份卸载，终态恢复。32GiB保护/单权重，其他对话及LoopB保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
