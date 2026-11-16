# Current State

> 2026-11-16 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；保留执行反例纠正的语义收益，聚焦降低额外误改。保持约束两臂训练已完成，当前比较原生修复与错改。
- **研究阶段**：新64报告256执行闭合，首轮33、普通纠正34、候选33、原模型复查29。候选多修1题也多错改2题；保留局部语义收益，下一步比较减弱反例项与保持投影。旧42/接口结果不覆盖。[证据](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#test-execution-v1)。
- **实际运行 / 预算**：FinQA已结算3,824POST/16,441,365已知＋7未知预留229,376；本批训练528更新/882显式前向，当前原生调用待闭合增记。校内仍5,005POST/50,865,083已知＋2,621,440预留，见[成本](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。训练与HTTP分账。
- **下一交付**：两臂训练d0e64479已完成：同88组/147正目标，固定λ=0.05、λ=0.1加保持投影；128次开发执行7e7d3c97进行中。完成后`ANALYZE.py`全量复核，不加教师或扫系数；余53未启用，TAT-QA仅CPU准备。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：冻结代码4a5ee70e未变，训练包66d6579d双份。监督1502164/tick11279203、原生子进程1546046/tick11742948、boot b4166d98实跑；进度见私有`retention_projection_v1/PIPELINE_LIVE.json`及`native_v1/LIVE.json`。27B卸载、终态恢复；32GiB保护/单权重，保留其他对话及LoopB。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
