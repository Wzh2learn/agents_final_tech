# Current State

> 2026-11-17 | 项目维护记忆，只保留当前答案。任务入口见[研究导航](../docs/research/README.md)，未决见[THREADS](THREADS.md)。

- **Goal / FCCL**：active；结构化四算子生成器按止损停止，当前推进已授权的接管价值学习备选。原96来源模型DEV41、新57前向35/57，转固定方法确认；封存首分叉微调线，不打包或逐文件核SHA。
- **研究阶段**：DEV效用/风险41、单状态40。冻结新57来源：首轮31、普通/旧37均32；16接管效用35、风险/单状态33、随机35；7接管35/33/35/33。直接教师32、保护后37。局部收益迁移，固定混合40停止。[本批](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#forward-sources57-v1)。
- **实际运行 / 预算**：已结算本地FinQA5,913POST/24,796,155＋12未知393,216；校内5,862POST/54,846,953＋11未知2,883,584，合57,730,537/10亿。扩样新8校内POST/36,078，未知0；GPU累计5,117更新/9,130前向，HF427前向/641,160输入tokens。旧调用不重充，TAT不变。[完整账](../research/agent_frontier_portfolio_20261029/results/FINQA_CORRECTION_LEARNING.md#finqa-costs)。
- **下一交付**：confirmation64_v1父174666/23872327正在首轮采集；fd35576c先冻结原96三个模型、主18/次级8和12预算及比较族，再载入预约64题，训练重合0。顺序本地三臂→三HF头→公共教师→最终执行，不调模型或剔题。扩样40已停；确认64不再称未使用且始终不进训练。[短计划](../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。
- **历史资产**：[机制知识](../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)覆盖20结果页；代码/续行长过程已入[主题归档](../docs/archive/2026-11-06_agent_research_context/README.md)。旧结果/费用保留，按需读取。
- **导师 / Paper E**：稿件、开题与办理由独立对话维护，本Goal不复核其现役版本/提交状态。研究按问题、机制、形式化及假设再验证，不要求榜单最优。已知学校要求本人一作、北邮第一单位、方向相关；会议须召开并宣读/张贴。
- **行事规则**：D主责，按需复核；搜索/执行边界见[唯一入口](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。全局调度与跨机预算锁未实现。
- **Git与运行面**：扩样权重/短回执与57拆分已同步本机，raw留GB10。确认单父顺序执行、单模型/32GiB保护，各模型阶段退出后恢复27B；Key仅进程内。代码/短状态本批同步，数据/Key不入Git，其他对话WIP保留。

历史状态见[2026-11-06 快照](archive/STATE_2026-11-06_pre_context_neat.md)与[2026-09-22 治理前快照](archive/STATE_2026-09-22_pre_governance.md)，均不作现役待办。投稿、付款、公开、外部联系及生产操作仍按用户明确授权办理。
